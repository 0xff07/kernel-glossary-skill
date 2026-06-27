# Fixed Events

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

ACPI fixed events are the platform events whose status and enable bits sit at spec-mandated positions inside the PM1 event register grouping, so OSPM services them through direct register access with zero AML involvement. The kernel enumerates them as five indices ([`ACPI_EVENT_PMTIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L721), [`ACPI_EVENT_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L722), [`ACPI_EVENT_POWER_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L723), [`ACPI_EVENT_SLEEP_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L724), [`ACPI_EVENT_RTC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L725)) into the [`acpi_gbl_fixed_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L168) table, which pairs each index with its PM1 status and enable bit masks. On every SCI, [`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167) reads both PM1 halves, ANDs status against enable, and routes each active event through [`acpi_ev_fixed_event_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L236) to the one handler recorded in [`acpi_gbl_fixed_event_handlers`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L243). Linux installs those handlers from vendor-neutral drivers, with [`acpi_button_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L532) claiming the fixed power and sleep buttons and [`acpi_rtc_event_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L783) claiming the RTC alarm, all through [`acpi_install_fixed_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L584).

```
    PM1x_STS status half (RW1C; PM1a and PM1b values ORed on read)
    ──────────────────────────────────────────────────────────────

    bit:   15    14  13:11   10     9     8    7:6    5     4    3:1    0
        ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
        │ WAK │ PCIE│ rsvd│ RTC │ SLP │ PWR │ rsvd│ GBL │  BM │ rsvd│ TMR │
        │ STS │ WAKE│     │ STS │ BTN │ BTN │     │ STS │ STS │     │ STS │
        │     │ STS │     │     │ STS │ STS │     │     │     │     │     │
        └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

    TMR_STS     bit 0   ACPI_BITREG_TIMER_STATUS        ACPI_EVENT_PMTIMER
    BM_STS      bit 4   ACPI_BITREG_BUS_MASTER_STATUS   (status only)
    GBL_STS     bit 5   ACPI_BITREG_GLOBAL_LOCK_STATUS  ACPI_EVENT_GLOBAL
    PWRBTN_STS  bit 8   ACPI_BITREG_POWER_BUTTON_STATUS ACPI_EVENT_POWER_BUTTON
    SLPBTN_STS  bit 9   ACPI_BITREG_SLEEP_BUTTON_STATUS ACPI_EVENT_SLEEP_BUTTON
    RTC_STS     bit 10  ACPI_BITREG_RT_CLOCK_STATUS     ACPI_EVENT_RTC
    PCIEXP_WAKE bit 14  ACPI_BITREG_PCIEXP_WAKE_STATUS  (status only)
    WAK_STS     bit 15  ACPI_BITREG_WAKE_STATUS         (status only)

    PM1x_EN enable half (R/W; writes mirrored to PM1a and PM1b)
    ───────────────────────────────────────────────────────────

    bit:   15    14  13:11   10     9     8    7:6    5    4:1    0
        ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
        │ rsvd│ PCIE│ rsvd│ RTC │ SLP │ PWR │ rsvd│ GBL │ rsvd│ TMR │
        │     │ WAKE│     │  EN │ BTN │ BTN │     │  EN │     │  EN │
        │     │ DIS │     │     │  EN │  EN │     │     │     │     │
        └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

    TMR_EN          bit 0   ACPI_BITREG_TIMER_ENABLE         arms TMR_STS
    GBL_EN          bit 5   ACPI_BITREG_GLOBAL_LOCK_ENABLE   arms GBL_STS
    PWRBTN_EN       bit 8   ACPI_BITREG_POWER_BUTTON_ENABLE  arms PWRBTN_STS
    SLPBTN_EN       bit 9   ACPI_BITREG_SLEEP_BUTTON_ENABLE  arms SLPBTN_STS
    RTC_EN          bit 10  ACPI_BITREG_RT_CLOCK_ENABLE      arms RTC_STS
    PCIEXP_WAKE_DIS bit 14  ACPI_BITREG_PCIEXP_WAKE_DISABLE  inverted polarity

    (the SCI asserts while any STS bit AND its EN partner are both 1;
     BM_STS and WAK_STS lack EN partners and are polled, never SCI sources)
```

## SUMMARY

The ACPI specification splits platform hardware into fixed and generic feature sets, and fixed events form the event half of the fixed feature set (section 4.8.2 of the specification, represented in the kernel by the [`ACPI_EVENT_PMTIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L721) through [`ACPI_EVENT_RTC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L725) index space of size [`ACPI_NUM_FIXED_EVENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L727)). The PM1 event grouping consists of a required PM1a block and an optional PM1b block, each split into a status half and an enable half, and ACPICA materializes the four halves at FADT parse time when [`acpi_tb_setup_fadt_registers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L639) carves [`acpi_gbl_xpm1a_status`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L36), [`acpi_gbl_xpm1a_enable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L37), [`acpi_gbl_xpm1b_status`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L39) and [`acpi_gbl_xpm1b_enable`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L40) out of the FADT event block addresses. Reads through [`acpi_hw_register_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L488) OR the A and B halves together via [`acpi_hw_read_multiple()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L714), which is legal because the specification keeps bit positions identical across the two blocks.

Runtime handling is a two-stage pipeline inside [`drivers/acpi/acpica/evevent.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c). [`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167) runs from the SCI interrupt path, fetches [`ACPI_REGISTER_PM1_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L987) and [`ACPI_REGISTER_PM1_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L988), and walks the [`struct acpi_fixed_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L531) table testing both masks per event. [`acpi_ev_fixed_event_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L236) then performs the spec-required write-1-to-clear acknowledgement through [`acpi_write_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L214) and invokes the [`acpi_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1055) callback registered in [`acpi_gbl_fixed_event_handlers`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L243), disabling the event when the slot is empty so an unclaimed event stops interrupting. The public surface ([`acpi_install_fixed_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L584), [`acpi_remove_fixed_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L653), [`acpi_enable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L142), [`acpi_disable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L205), [`acpi_clear_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L265), [`acpi_get_event_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L309)) is consumed inside the tree by [`drivers/acpi/button.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c) for the fixed buttons, by [`drivers/rtc/rtc-cmos.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c) for the RTC alarm, by [`acpi_suspend_enter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L598) for post-resume power button accounting, and by [`drivers/acpi/sysfs.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c) for the per-event counters under `/sys/firmware/acpi/interrupts/`.

## SPECIFICATIONS

- ACPI Specification, section 4.8.2: Fixed Hardware Features
- ACPI Specification, section 4.8.3.1: PM1 Event Grouping
- ACPI Specification, section 4.8.3.1.1: PM1 Status Registers
- ACPI Specification, section 4.8.3.1.2: PM1 Enable Registers
- ACPI Specification, section 5.6.2: Types of ACPI Events
- ACPI Specification, section 5.6.3: Fixed Event Handling

## LINUX KERNEL

### Event index space

- [`'\<ACPI_EVENT_PMTIMER\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L721): index 0, PM timer carry (TMR_STS)
- [`'\<ACPI_EVENT_GLOBAL\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L722): index 1, Global Lock release (GBL_STS)
- [`'\<ACPI_EVENT_POWER_BUTTON\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L723): index 2, fixed power button (PWRBTN_STS)
- [`'\<ACPI_EVENT_SLEEP_BUTTON\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L724): index 3, fixed sleep button (SLPBTN_STS)
- [`'\<ACPI_EVENT_RTC\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L725): index 4, RTC alarm (RTC_STS)
- [`'\<ACPI_NUM_FIXED_EVENTS\>':'include/acpi/actypes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L727): table size, [`ACPI_EVENT_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L726) + 1

### ACPICA tables and types

- [`'\<struct acpi_fixed_event_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L531): per-event quadruple of status/enable bit-register IDs and bit masks
- [`'\<struct acpi_fixed_event_handler\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L526): handler pointer plus opaque context for one event
- [`acpi_gbl_fixed_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L168): the five-entry constant table binding event indices to PM1 bits
- [`acpi_gbl_fixed_event_handlers`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L243): the mutable dispatch table, one [`struct acpi_fixed_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L526) slot per event
- [`acpi_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1055): handler typedef, `u32 (*)(void *context)`
- [`acpi_fixed_event_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L260): per-event interrupt counter incremented at detect time

### Detection and dispatch (ACPICA core)

- [`'\<acpi_ev_initialize_events\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L34): boot entry that initializes fixed events, then GPEs
- [`'\<acpi_ev_fixed_event_initialize\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L126): clears all handler slots and writes 0 to every enable bit
- [`'\<acpi_ev_fixed_event_detect\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167): SCI-time scan of PM1 status AND enable
- [`'\<acpi_ev_fixed_event_dispatch\>':'drivers/acpi/acpica/evevent.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L236): write-1-to-clear acknowledgement plus handler invocation

### Public event API

- [`'\<acpi_install_fixed_event_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L584): records the handler, clears stale status, enables the event
- [`'\<acpi_remove_fixed_event_handler\>':'drivers/acpi/acpica/evxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L653): disables the event, then empties the handler slot
- [`'\<acpi_enable_event\>':'drivers/acpi/acpica/evxfevnt.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L142): writes [`ACPI_ENABLE_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L897) to the enable bit and reads it back
- [`'\<acpi_disable_event\>':'drivers/acpi/acpica/evxfevnt.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L205): writes [`ACPI_DISABLE_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L898) to the enable bit and reads it back
- [`'\<acpi_clear_event\>':'drivers/acpi/acpica/evxfevnt.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L265): writes [`ACPI_CLEAR_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L893) to the status bit
- [`'\<acpi_get_event_status\>':'drivers/acpi/acpica/evxfevnt.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L309): returns [`ACPI_EVENT_FLAG_STATUS_SET`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L752) style flags for one event

### Register access path

- [`'\<acpi_read_bit_register\>':'drivers/acpi/acpica/hwxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L153): reads a parent PM register and normalizes one field to bit 0
- [`'\<acpi_write_bit_register\>':'drivers/acpi/acpica/hwxface.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L214): read-modify-write for enable/control bits, pure W1C write for PM1 status bits
- [`'\<acpi_hw_get_bit_register_info\>':'drivers/acpi/acpica/hwregs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L426): maps an `ACPI_BITREG_*` ID to its [`struct acpi_bit_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L950) entry
- [`'\<struct acpi_bit_register_info\>':'drivers/acpi/acpica/aclocal.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L950): parent register ID, bit position, access mask
- [`acpi_gbl_bit_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L100): the [`ACPI_NUM_BITREG`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L889)-entry table behind both bit-register functions
- [`'\<acpi_hw_register_read\>':'drivers/acpi/acpica/hwregs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L488): whole-register read that multiplexes PM1 A/B halves
- [`'\<acpi_hw_read_multiple\>':'drivers/acpi/acpica/hwregs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L714): ORs the PM1a and PM1b values into one logical register
- [`'\<acpi_tb_setup_fadt_registers\>':'drivers/acpi/acpica/tbfadt.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L639): splits each FADT event block into status and enable GAS structures via [`fadt_pm_info_table`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L118)

### Linux consumers

- [`'\<acpi_bus_scan_fixed\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2792): creates button devices when the FADT advertises fixed-hardware buttons
- [`'\<acpi_bus_add_fixed_device_object\>':'drivers/acpi/scan.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2783): allocates the [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) for one fixed button
- [`ACPI_BUTTON_HID_POWERF`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L24): synthetic HID `LNXPWRBN` assigned by [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388); [`ACPI_BUTTON_HID_SLEEPF`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L25) is the `LNXSLPBN` sibling
- [`'\<acpi_button_probe\>':'drivers/acpi/button.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L532): installs [`acpi_button_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L481) as the fixed-event handler for both button types
- [`'\<acpi_button_event\>':'drivers/acpi/button.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L481): interrupt-level handler that defers to [`acpi_button_notify_run()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L476) via [`acpi_os_execute()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/osl.c#L1092)
- [`'\<rtc_handler\>':'drivers/rtc/rtc-cmos.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L747): RTC fixed-event handler reporting the alarm and rearming wakeup state
- [`'\<acpi_rtc_event_setup\>':'drivers/rtc/rtc-cmos.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L783): installs [`rtc_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L747) and parks the event disabled
- [`'\<acpi_suspend_enter\>':'drivers/acpi/sleep.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L598): polls and clears PWRBTN_STS right after S3 resume
- [`'\<fixed_event_count\>':'drivers/acpi/sysfs.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L625): sysfs counter bump fed by [`acpi_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L637) through [`acpi_install_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L534)

## KERNEL DOCUMENTATION

- [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi): documents the `ff_pwr_btn`, `ff_slp_btn`, `ff_rt_clk`, `ff_pmtimer` and `ff_gbl_lock` fixed-event counter files under `/sys/firmware/acpi/interrupts/`
- [`Documentation/power/suspend-and-interrupts.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/suspend-and-interrupts.rst): interrupt handling across suspend/resume, the phase in which wake-armed fixed events fire

## OTHER SOURCES

- [PM1 Event Grouping, ACPI Specification 6.5, section 4.8.3.1](https://uefi.org/specs/ACPI/6.5/04_ACPI_Hardware_Specification.html#pm1-event-grouping)
- [Fixed Event Handling, ACPI Specification 6.5, section 5.6.3](https://uefi.org/specs/ACPI/6.5/05_ACPI_Software_Programming_Model.html#fixed-event-handling)

## REGISTERS

### PM1_STS (status half of the PM1 event grouping, RW1C)

The status half occupies the first `PM1_EVT_LEN/2` bytes of each event block named by [`acpi_gbl_FADT.xpm1a_event_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L245) and the optional [`acpi_gbl_FADT.xpm1b_event_block`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L246). Every defined bit is sticky and write-1-to-clear, which ACPICA encodes as the special PM1 status branch of [`acpi_write_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L214). Each bit is addressed kernel-side by an `ACPI_BITREG_*` ID whose position and mask come from [`acpi_gbl_bit_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L100).

| Bit | Spec field | Access | Bit-register ID | Mask constant | Fixed event |
|-----|------------|--------|-----------------|---------------|-------------|
| 0 | `TMR_STS` | RW1C | [`ACPI_BITREG_TIMER_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L858) | [`ACPI_BITMASK_TIMER_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L997) | [`ACPI_EVENT_PMTIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L721) |
| 4 | `BM_STS` | RW1C | [`ACPI_BITREG_BUS_MASTER_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L859) | [`ACPI_BITMASK_BUS_MASTER_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L998) | (status only) |
| 5 | `GBL_STS` | RW1C | [`ACPI_BITREG_GLOBAL_LOCK_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L860) | [`ACPI_BITMASK_GLOBAL_LOCK_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L999) | [`ACPI_EVENT_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L722) |
| 8 | `PWRBTN_STS` | RW1C | [`ACPI_BITREG_POWER_BUTTON_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L861) | [`ACPI_BITMASK_POWER_BUTTON_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1000) | [`ACPI_EVENT_POWER_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L723) |
| 9 | `SLPBTN_STS` | RW1C | [`ACPI_BITREG_SLEEP_BUTTON_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L862) | [`ACPI_BITMASK_SLEEP_BUTTON_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1001) | [`ACPI_EVENT_SLEEP_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L724) |
| 10 | `RTC_STS` | RW1C | [`ACPI_BITREG_RT_CLOCK_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L863) | [`ACPI_BITMASK_RT_CLOCK_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1002) | [`ACPI_EVENT_RTC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L725) |
| 14 | `PCIEXP_WAKE_STS` | RW1C | [`ACPI_BITREG_PCIEXP_WAKE_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L865) | [`ACPI_BITMASK_PCIEXP_WAKE_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1003) | (status only) |
| 15 | `WAK_STS` | RW1C | [`ACPI_BITREG_WAKE_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L864) | [`ACPI_BITMASK_WAKE_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1004) | (status only) |

`BM_STS` and `WAK_STS` lack enable partners, so they are informational bits that software polls, and only the five rows with a fixed-event column entry participate in [`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167). The sleep entry paths clear them ahead of suspend, with [`acpi_enter_sleep_state_s4bios()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxfsleep.c#L127) writing [`ACPI_BITREG_WAKE_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L864) individually before [`acpi_hw_clear_acpi_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L382) wipes the whole register through [`ACPI_BITMASK_ALL_FIXED_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1006).

### PM1_EN (enable half of the PM1 event grouping, R/W)

The enable half follows the status half inside the same event block, at offset `PM1_EVT_LEN/2`. An SCI is generated while a status bit and its enable bit are simultaneously 1, so writing the enable bit to 0 silences the event source without losing the latched status.

| Bit | Spec field | Access | Bit-register ID | Mask constant | Arms |
|-----|------------|--------|-----------------|---------------|------|
| 0 | `TMR_EN` | R/W | [`ACPI_BITREG_TIMER_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L869) | [`ACPI_BITMASK_TIMER_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1016) | `TMR_STS` |
| 5 | `GBL_EN` | R/W | [`ACPI_BITREG_GLOBAL_LOCK_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L870) | [`ACPI_BITMASK_GLOBAL_LOCK_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1017) | `GBL_STS` |
| 8 | `PWRBTN_EN` | R/W | [`ACPI_BITREG_POWER_BUTTON_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L871) | [`ACPI_BITMASK_POWER_BUTTON_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1018) | `PWRBTN_STS` |
| 9 | `SLPBTN_EN` | R/W | [`ACPI_BITREG_SLEEP_BUTTON_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L872) | [`ACPI_BITMASK_SLEEP_BUTTON_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1019) | `SLPBTN_STS` |
| 10 | `RTC_EN` | R/W | [`ACPI_BITREG_RT_CLOCK_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L873) | [`ACPI_BITMASK_RT_CLOCK_ENABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1020) | `RTC_STS` |
| 14 | `PCIEXP_WAKE_DIS` | R/W | [`ACPI_BITREG_PCIEXP_WAKE_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L874) | [`ACPI_BITMASK_PCIEXP_WAKE_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1021) | `PCIEXP_WAKE_STS`, inverted |

The bit positions behind each ID live in the [`ACPI_BITPOSITION_TIMER_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1033) through [`ACPI_BITPOSITION_PCIEXP_WAKE_DISABLE`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1047) constants, and `PCIEXP_WAKE_DIS` carries disable polarity (1 blocks the wake event), which is why it is named with a `_DISABLE` suffix instead of `_ENABLE`.

## DETAILS

### Boot path from acpi_enable_subsystem to disabled events

Fixed events come to life during [`acpi_enable_subsystem()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utxfinit.c#L110), which Linux reaches from [`acpi_subsystem_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1360) and [`acpi_bus_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/bus.c#L1390). Event setup runs before the SCI handler is installed, which the in-tree comment justifies directly.

```c
/* drivers/acpi/acpica/utxfinit.c:166 */
	if (!(flags & ACPI_NO_EVENT_INIT)) {
		ACPI_DEBUG_PRINT((ACPI_DB_EXEC,
				  "[Init] Initializing ACPI events\n"));

		status = acpi_ev_initialize_events();
		if (ACPI_FAILURE(status)) {
			return_ACPI_STATUS(status);
		}
	}
```

[`acpi_ev_initialize_events()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L34) bails out on hardware-reduced platforms (the [`acpi_gbl_reduced_hardware`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpixf.h#L214) test) because such platforms implement zero fixed hardware, then initializes fixed events ahead of GPEs.

```c
/* drivers/acpi/acpica/evevent.c:34 */
acpi_status acpi_ev_initialize_events(void)
{
	acpi_status status;

	ACPI_FUNCTION_TRACE(ev_initialize_events);

	/* If Hardware Reduced flag is set, there are no fixed events */

	if (acpi_gbl_reduced_hardware) {
		return_ACPI_STATUS(AE_OK);
	}

	/*
	 * Initialize the Fixed and General Purpose Events. This is done prior to
	 * enabling SCIs to prevent interrupts from occurring before the handlers
	 * are installed.
	 */
	status = acpi_ev_fixed_event_initialize();
	if (ACPI_FAILURE(status)) {
		ACPI_EXCEPTION((AE_INFO, status,
				"Unable to initialize fixed events"));
		return_ACPI_STATUS(status);
	}
	...
	return_ACPI_STATUS(status);
}
```

According to the comment "This is done prior to enabling SCIs to prevent interrupts from occurring before the handlers are installed", the ordering guarantees that the first SCI ever taken finds a consistent dispatch table. [`acpi_ev_fixed_event_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L126) then walks all [`ACPI_NUM_FIXED_EVENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L727) slots, empties [`acpi_gbl_fixed_event_handlers`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L243), and writes [`ACPI_DISABLE_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L898) (the value 0) into every enable bit through [`acpi_write_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L214).

```c
/* drivers/acpi/acpica/evevent.c:126 */
static acpi_status acpi_ev_fixed_event_initialize(void)
{
	u32 i;
	acpi_status status;

	/*
	 * Initialize the structure that keeps track of fixed event handlers and
	 * disable all of the fixed events.
	 */
	for (i = 0; i < ACPI_NUM_FIXED_EVENTS; i++) {
		acpi_gbl_fixed_event_handlers[i].handler = NULL;
		acpi_gbl_fixed_event_handlers[i].context = NULL;

		/* Disable the fixed event */

		if (acpi_gbl_fixed_event_info[i].enable_register_id != 0xFF) {
			status =
			    acpi_write_bit_register(acpi_gbl_fixed_event_info
						    [i].enable_register_id,
						    ACPI_DISABLE_EVENT);
			if (ACPI_FAILURE(status)) {
				return (status);
			}
		}
	}

	return (AE_OK);
}
```

The `0xFF` guard skips table entries lacking an enable register, and every entry in the v7.0 table carries a real enable ID, so all five events start their life disabled until a driver installs a handler.

### The pairing table acpi_gbl_fixed_event_info

Two small structs carry the entire fixed-event state. [`struct acpi_fixed_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L526) is the mutable dispatch slot and [`struct acpi_fixed_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L531) is the constant register binding.

```c
/* drivers/acpi/acpica/aclocal.h:524 */
/* Information about each particular fixed event */

struct acpi_fixed_event_handler {
	acpi_event_handler handler;	/* Address of handler. */
	void *context;		/* Context to be passed to handler */
};

struct acpi_fixed_event_info {
	u8 status_register_id;
	u8 enable_register_id;
	u16 status_bit_mask;
	u16 enable_bit_mask;
};
```

[`acpi_gbl_fixed_event_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L168) instantiates one quadruple per event index, pairing the `ACPI_BITREG_*` IDs (used for single-bit writes) with the raw `ACPI_BITMASK_*` masks (used for whole-register tests at detect time).

```c
/* drivers/acpi/acpica/utglobal.c:168 */
struct acpi_fixed_event_info acpi_gbl_fixed_event_info[ACPI_NUM_FIXED_EVENTS] = {
	/* ACPI_EVENT_PMTIMER       */ {ACPI_BITREG_TIMER_STATUS,
					ACPI_BITREG_TIMER_ENABLE,
					ACPI_BITMASK_TIMER_STATUS,
					ACPI_BITMASK_TIMER_ENABLE},
	/* ACPI_EVENT_GLOBAL        */ {ACPI_BITREG_GLOBAL_LOCK_STATUS,
					ACPI_BITREG_GLOBAL_LOCK_ENABLE,
					ACPI_BITMASK_GLOBAL_LOCK_STATUS,
					ACPI_BITMASK_GLOBAL_LOCK_ENABLE},
	/* ACPI_EVENT_POWER_BUTTON  */ {ACPI_BITREG_POWER_BUTTON_STATUS,
					ACPI_BITREG_POWER_BUTTON_ENABLE,
					ACPI_BITMASK_POWER_BUTTON_STATUS,
					ACPI_BITMASK_POWER_BUTTON_ENABLE},
	/* ACPI_EVENT_SLEEP_BUTTON  */ {ACPI_BITREG_SLEEP_BUTTON_STATUS,
					ACPI_BITREG_SLEEP_BUTTON_ENABLE,
					ACPI_BITMASK_SLEEP_BUTTON_STATUS,
					ACPI_BITMASK_SLEEP_BUTTON_ENABLE},
	/* ACPI_EVENT_RTC           */ {ACPI_BITREG_RT_CLOCK_STATUS,
					ACPI_BITREG_RT_CLOCK_ENABLE,
					ACPI_BITMASK_RT_CLOCK_STATUS,
					ACPI_BITMASK_RT_CLOCK_ENABLE},
};
```

The masks place [`ACPI_EVENT_PMTIMER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L721) on bit 0, [`ACPI_EVENT_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L722) on bit 5, [`ACPI_EVENT_POWER_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L723) on bit 8, [`ACPI_EVENT_SLEEP_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L724) on bit 9 and [`ACPI_EVENT_RTC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L725) on bit 10, matching the spec tables for PM1 status (section 4.8.3.1.1) and PM1 enable (section 4.8.3.1.2) bit for bit.

### PM1 A/B halves resolved at FADT parse time

The PM1 event grouping permits the platform to split one logical register pair across two chips, PM1a and PM1b, with identical bit layouts. ACPICA resolves the four physical halves once, at table-parse time, driven by [`fadt_pm_info_table`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L118).

```c
/* drivers/acpi/acpica/tbfadt.c:109 */
/* Table used to split Event Blocks into separate status/enable registers */

typedef struct acpi_fadt_pm_info {
	struct acpi_generic_address *target;
	u16 source;
	u8 register_num;

} acpi_fadt_pm_info;

static struct acpi_fadt_pm_info fadt_pm_info_table[] = {
	{&acpi_gbl_xpm1a_status,
	 ACPI_FADT_OFFSET(xpm1a_event_block),
	 0},

	{&acpi_gbl_xpm1a_enable,
	 ACPI_FADT_OFFSET(xpm1a_event_block),
	 1},

	{&acpi_gbl_xpm1b_status,
	 ACPI_FADT_OFFSET(xpm1b_event_block),
	 0},

	{&acpi_gbl_xpm1b_enable,
	 ACPI_FADT_OFFSET(xpm1b_event_block),
	 1}
};
```

[`acpi_tb_setup_fadt_registers()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/tbfadt.c#L639) iterates that table and computes each half's [`struct acpi_generic_address`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L90) as `block address + register_num * (pm1_event_length / 2)`, which encodes the spec rule that the status half occupies the first half of the block and the enable half the second.

```c
/* drivers/acpi/acpica/tbfadt.c:639 */
static void acpi_tb_setup_fadt_registers(void)
{
	struct acpi_generic_address *target64;
	...
	/*
	 * Calculate separate GAS structs for the PM1x (A/B) Status and Enable
	 * registers. These addresses do not appear (directly) in the FADT, so it
	 * is useful to pre-calculate them from the PM1 Event Block definitions.
	 *
	 * The PM event blocks are split into two register blocks, first is the
	 * PM Status Register block, followed immediately by the PM Enable
	 * Register block. Each is of length (pm1_event_length/2)
	 *
	 * Note: The PM1A event block is required by the ACPI specification.
	 * However, the PM1B event block is optional and is rarely, if ever,
	 * used.
	 */

	for (i = 0; i < ACPI_FADT_PM_INFO_ENTRIES; i++) {
		source64 =
		    ACPI_ADD_PTR(struct acpi_generic_address, &acpi_gbl_FADT,
				 fadt_pm_info_table[i].source);

		if (source64->address) {
			acpi_tb_init_generic_address(fadt_pm_info_table[i].
						     target, source64->space_id,
						     pm1_register_byte_width,
						     source64->address +
						     (fadt_pm_info_table[i].
						      register_num *
						      pm1_register_byte_width),
						     "PmRegisters", 0);
		}
	}
```

At read time [`acpi_hw_register_read()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L488) selects the pre-computed half pair for the requested logical register ID.

```c
/* drivers/acpi/acpica/hwregs.c:496 */
	switch (register_id) {
	case ACPI_REGISTER_PM1_STATUS:	/* PM1 A/B: 16-bit access each */

		status = acpi_hw_read_multiple(&value,
					       &acpi_gbl_xpm1a_status,
					       &acpi_gbl_xpm1b_status);
		break;

	case ACPI_REGISTER_PM1_ENABLE:	/* PM1 A/B: 16-bit access each */

		status = acpi_hw_read_multiple(&value,
					       &acpi_gbl_xpm1a_enable,
					       &acpi_gbl_xpm1b_enable);
		break;
```

[`acpi_hw_read_multiple()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L714) merges the two halves by ORing, and its comment quotes the spec clause that makes the OR safe.

```c
/* drivers/acpi/acpica/hwregs.c:741 */
	/*
	 * OR the two return values together. No shifting or masking is necessary,
	 * because of how the PM1 registers are defined in the ACPI specification:
	 *
	 * "Although the bits can be split between the two register blocks (each
	 * register block has a unique pointer within the FADT), the bit positions
	 * are maintained. The register block with unimplemented bits (that is,
	 * those implemented in the other register block) always returns zeros,
	 * and writes have no side effects"
	 */
	*value = (value_a | value_b);
	return (AE_OK);
```

### Detection on every SCI

The SCI interrupt handler in [`drivers/acpi/acpica/evsci.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evsci.c) checks fixed events first on every interrupt, so the caller side of the detect function is the top of the ACPI interrupt path.

```c
/* drivers/acpi/acpica/evsci.c:88 */
	/*
	 * Fixed Events:
	 * Check for and dispatch any Fixed Events that have occurred
	 */
	interrupt_handled |= acpi_ev_fixed_event_detect();
```

[`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167) reads the merged status and enable registers once, then evaluates each event's two masks against the cached values.

```c
/* drivers/acpi/acpica/evevent.c:167 */
u32 acpi_ev_fixed_event_detect(void)
{
	u32 int_status = ACPI_INTERRUPT_NOT_HANDLED;
	u32 fixed_status;
	u32 fixed_enable;
	u32 i;
	acpi_status status;

	ACPI_FUNCTION_NAME(ev_fixed_event_detect);

	/*
	 * Read the fixed feature status and enable registers, as all the cases
	 * depend on their values. Ignore errors here.
	 */
	status = acpi_hw_register_read(ACPI_REGISTER_PM1_STATUS, &fixed_status);
	status |=
	    acpi_hw_register_read(ACPI_REGISTER_PM1_ENABLE, &fixed_enable);
	if (ACPI_FAILURE(status)) {
		return (int_status);
	}
	...
	/*
	 * Check for all possible Fixed Events and dispatch those that are active
	 */
	for (i = 0; i < ACPI_NUM_FIXED_EVENTS; i++) {

		/* Both the status and enable bits must be on for this event */

		if ((fixed_status & acpi_gbl_fixed_event_info[i].
		     status_bit_mask)
		    && (fixed_enable & acpi_gbl_fixed_event_info[i].
			enable_bit_mask)) {
			/*
			 * Found an active (signalled) event. Invoke global event
			 * handler if present.
			 */
			acpi_fixed_event_count[i]++;
			if (acpi_gbl_global_event_handler) {
				acpi_gbl_global_event_handler
				    (ACPI_EVENT_TYPE_FIXED, NULL, i,
				     acpi_gbl_global_event_handler_context);
			}

			int_status |= acpi_ev_fixed_event_dispatch(i);
		}
	}

	return (int_status);
}
```

The status AND enable test implements the spec's SCI assertion condition in software, so a latched status whose enable bit is 0 stays parked in the register until something clears or enables it. For every active event the function bumps [`acpi_fixed_event_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L260), calls the optional [`acpi_gbl_global_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L241) hook with [`ACPI_EVENT_TYPE_FIXED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1051) (the hook Linux uses for sysfs statistics), and accumulates the [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145) bit from dispatch.

### Dispatch clears status before invoking the handler

[`acpi_ev_fixed_event_dispatch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L236) performs the per-event acknowledgement and hand-off, in that order.

```c
/* drivers/acpi/acpica/evevent.c:236 */
static u32 acpi_ev_fixed_event_dispatch(u32 event)
{

	ACPI_FUNCTION_ENTRY();

	/* Clear the status bit */

	(void)acpi_write_bit_register(acpi_gbl_fixed_event_info[event].
				      status_register_id, ACPI_CLEAR_STATUS);

	/*
	 * Make sure that a handler exists. If not, report an error
	 * and disable the event to prevent further interrupts.
	 */
	if (!acpi_gbl_fixed_event_handlers[event].handler) {
		(void)acpi_write_bit_register(acpi_gbl_fixed_event_info[event].
					      enable_register_id,
					      ACPI_DISABLE_EVENT);

		ACPI_ERROR((AE_INFO,
			    "No installed handler for fixed event - %s (%u), disabling",
			    acpi_ut_get_event_name(event), event));

		return (ACPI_INTERRUPT_NOT_HANDLED);
	}

	/* Invoke the Fixed Event handler */

	return ((acpi_gbl_fixed_event_handlers[event].
		 handler) (acpi_gbl_fixed_event_handlers[event].context));
}
```

Writing [`ACPI_CLEAR_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L893) (the value 1) through [`acpi_write_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L214) re-arms the RW1C latch before the handler runs, so a button press arriving during handler execution latches a fresh status bit and produces another SCI. The handler-missing branch writes [`ACPI_DISABLE_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L898) into the enable bit and returns [`ACPI_INTERRUPT_NOT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1144), which keeps a handlerless event from pinning the level-triggered SCI forever. The handler itself runs at ACPI interrupt level and must return [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145), the convention every in-tree handler follows.

### Installation through acpi_install_fixed_event_handler

[`acpi_install_fixed_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L584) serializes against [`ACPI_MTX_EVENTS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L49), refuses to stack handlers, and orders the state changes so the event is enabled only after the handler pointer is visible.

```c
/* drivers/acpi/acpica/evxface.c:583 */
acpi_status
acpi_install_fixed_event_handler(u32 event,
				 acpi_event_handler handler, void *context)
{
	acpi_status status;
	...
	/* Do not allow multiple handlers */

	if (acpi_gbl_fixed_event_handlers[event].handler) {
		status = AE_ALREADY_EXISTS;
		goto cleanup;
	}

	/* Install the handler before enabling the event */

	acpi_gbl_fixed_event_handlers[event].handler = handler;
	acpi_gbl_fixed_event_handlers[event].context = context;

	status = acpi_clear_event(event);
	if (ACPI_SUCCESS(status))
		status = acpi_enable_event(event, 0);
	if (ACPI_FAILURE(status)) {
		...
		/* Remove the handler */

		acpi_gbl_fixed_event_handlers[event].handler = NULL;
		acpi_gbl_fixed_event_handlers[event].context = NULL;
	}
	...
}
```

The [`acpi_clear_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L265) call ahead of [`acpi_enable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L142) discards a status bit that latched while the event was unowned, which prevents an immediate spurious dispatch the instant the enable bit goes to 1. [`acpi_enable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L142) itself writes the enable bit and verifies the hardware accepted it by reading it back through [`acpi_read_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L153).

```c
/* drivers/acpi/acpica/evxfevnt.c:142 */
acpi_status acpi_enable_event(u32 event, u32 flags)
{
	acpi_status status = AE_OK;
	u32 value;
	...
	/*
	 * Enable the requested fixed event (by writing a one to the enable
	 * register bit)
	 */
	status =
	    acpi_write_bit_register(acpi_gbl_fixed_event_info[event].
				    enable_register_id, ACPI_ENABLE_EVENT);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Make sure that the hardware responded */

	status =
	    acpi_read_bit_register(acpi_gbl_fixed_event_info[event].
				   enable_register_id, &value);
	...
	if (value != 1) {
		ACPI_ERROR((AE_INFO,
			    "Could not enable %s event",
			    acpi_ut_get_event_name(event)));
		return_ACPI_STATUS(AE_NO_HARDWARE_RESPONSE);
	}

	return_ACPI_STATUS(status);
}
```

[`acpi_disable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L205) mirrors the same write-then-verify pattern with [`ACPI_DISABLE_EVENT`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L898), and [`acpi_clear_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L265) is a single status-side write with zero verification, because a W1C bit reads back 0 immediately after a successful clear anyway.

```c
/* drivers/acpi/acpica/evxfevnt.c:265 */
acpi_status acpi_clear_event(u32 event)
{
	acpi_status status = AE_OK;
	...
	/*
	 * Clear the requested fixed event (By writing a one to the status
	 * register bit)
	 */
	status =
	    acpi_write_bit_register(acpi_gbl_fixed_event_info[event].
				    status_register_id, ACPI_CLEAR_STATUS);

	return_ACPI_STATUS(status);
}
```

[`acpi_remove_fixed_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L653) reverses the installation order, disabling first and emptying the slot afterwards, and it empties the slot even when the disable write failed.

```c
/* drivers/acpi/acpica/evxface.c:652 */
acpi_status
acpi_remove_fixed_event_handler(u32 event, acpi_event_handler handler)
{
	acpi_status status = AE_OK;
	...
	/* Disable the event before removing the handler */

	status = acpi_disable_event(event, 0);

	/* Always Remove the handler */

	acpi_gbl_fixed_event_handlers[event].handler = NULL;
	acpi_gbl_fixed_event_handlers[event].context = NULL;
	...
}
```

All four register-touching functions return [`AE_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acexcep.h#L60) untouched on hardware-reduced platforms because the registers they would touch are absent there.

### Bit-register normalization in hwxface.c

Each `ACPI_BITREG_*` ID indexes [`acpi_gbl_bit_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/utglobal.c#L100), a table of [`struct acpi_bit_register_info`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L950) entries naming the parent register, the bit position and the access mask.

```c
/* drivers/acpi/acpica/aclocal.h:950 */
struct acpi_bit_register_info {
	u8 parent_register;
	u8 bit_position;
	u16 access_bit_mask;
};
```

```c
/* drivers/acpi/acpica/utglobal.c:100 */
struct acpi_bit_register_info acpi_gbl_bit_register_info[ACPI_NUM_BITREG] = {
	/* Name                                     Parent Register             Register Bit Position                   Register Bit Mask       */

	/* ACPI_BITREG_TIMER_STATUS         */ {ACPI_REGISTER_PM1_STATUS,
						ACPI_BITPOSITION_TIMER_STATUS,
						ACPI_BITMASK_TIMER_STATUS},
	/* ACPI_BITREG_BUS_MASTER_STATUS    */ {ACPI_REGISTER_PM1_STATUS,
						ACPI_BITPOSITION_BUS_MASTER_STATUS,
						ACPI_BITMASK_BUS_MASTER_STATUS},
	...
	/* ACPI_BITREG_WAKE_STATUS          */ {ACPI_REGISTER_PM1_STATUS,
						ACPI_BITPOSITION_WAKE_STATUS,
						ACPI_BITMASK_WAKE_STATUS},
	/* ACPI_BITREG_PCIEXP_WAKE_STATUS   */ {ACPI_REGISTER_PM1_STATUS,
						ACPI_BITPOSITION_PCIEXP_WAKE_STATUS,
						ACPI_BITMASK_PCIEXP_WAKE_STATUS},

	/* ACPI_BITREG_TIMER_ENABLE         */ {ACPI_REGISTER_PM1_ENABLE,
						ACPI_BITPOSITION_TIMER_ENABLE,
						ACPI_BITMASK_TIMER_ENABLE},
	...
	/* ACPI_BITREG_PCIEXP_WAKE_DISABLE  */ {ACPI_REGISTER_PM1_ENABLE,
						ACPI_BITPOSITION_PCIEXP_WAKE_DISABLE,
						ACPI_BITMASK_PCIEXP_WAKE_DISABLE},
	...
};
```

[`acpi_read_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L153) resolves the ID through [`acpi_hw_get_bit_register_info()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L426), reads the whole parent register, and shifts the masked field down to bit 0, which is why callers compare against plain 0 and 1.

```c
/* drivers/acpi/acpica/hwxface.c:153 */
acpi_status acpi_read_bit_register(u32 register_id, u32 *return_value)
{
	struct acpi_bit_register_info *bit_reg_info;
	u32 register_value;
	u32 value;
	acpi_status status;
	...
	bit_reg_info = acpi_hw_get_bit_register_info(register_id);
	if (!bit_reg_info) {
		return_ACPI_STATUS(AE_BAD_PARAMETER);
	}

	/* Read the entire parent register */

	status = acpi_hw_register_read(bit_reg_info->parent_register,
				       &register_value);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	/* Normalize the value that was read, mask off other bits */

	value = ((register_value & bit_reg_info->access_bit_mask)
		 >> bit_reg_info->bit_position);
	...
	*return_value = value;
	return_ACPI_STATUS(AE_OK);
}
```

[`acpi_write_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L214) takes the global hardware lock and branches on the parent register, because PM1 status demands write-1-to-clear semantics while the other parents demand read-modify-write through [`acpi_hw_register_write()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L591).

```c
/* drivers/acpi/acpica/hwxface.c:260 */
	} else {
		/*
		 * 2) Case for PM1 Status
		 *
		 * The Status register is different from the rest. Clear an event
		 * by writing 1, writing 0 has no effect. So, the only relevant
		 * information is the single bit we're interested in, all others
		 * should be written as 0 so they will be left unchanged.
		 */
		register_value = ACPI_REGISTER_PREPARE_BITS(value,
							    bit_reg_info->
							    bit_position,
							    bit_reg_info->
							    access_bit_mask);

		/* No need to write the register if value is all zeros */

		if (register_value) {
			status =
			    acpi_hw_register_write(ACPI_REGISTER_PM1_STATUS,
						   register_value);
		}
	}
```

According to the comment "Clear an event by writing 1, writing 0 has no effect", the PM1 status branch writes the lone target bit and zeros everywhere else, so acknowledging one event leaves the other latched status bits untouched. A read-modify-write here would clear every latched event in the register, which is exactly the bug the branch exists to avoid.

The opposite extreme also exists. [`acpi_hw_clear_acpi_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwregs.c#L382), which the legacy sleep entry path [`acpi_hw_legacy_sleep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwsleep.c#L30) runs before programming the sleep type, blasts [`ACPI_BITMASK_ALL_FIXED_STATUS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/aclocal.h#L1006) into the status register so the machine enters the sleep state with every fixed-event latch (the enable-less `WAK_STS` and `BM_STS` included) wiped.

```c
/* drivers/acpi/acpica/hwregs.c:382 */
acpi_status acpi_hw_clear_acpi_status(void)
{
	acpi_status status;
	acpi_cpu_flags lock_flags = 0;
	...
	lock_flags = acpi_os_acquire_raw_lock(acpi_gbl_hardware_lock);

	/* Clear the fixed events in PM1 A/B */

	status = acpi_hw_register_write(ACPI_REGISTER_PM1_STATUS,
					ACPI_BITMASK_ALL_FIXED_STATUS);

	acpi_os_release_raw_lock(acpi_gbl_hardware_lock, lock_flags);
	...
}
```

### Fixed buttons surface as LNXPWRBN and LNXSLPBN platform devices

The FADT flags [`ACPI_FADT_POWER_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L280) and [`ACPI_FADT_SLEEP_BUTTON`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actbl.h#L281) advertise control-method buttons when set, so a clear flag means the platform implements the fixed-hardware variant and [`acpi_bus_scan_fixed()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L2792) fabricates a device node for it.

```c
/* drivers/acpi/scan.c:2783 */
static void acpi_bus_add_fixed_device_object(enum acpi_bus_device_type type)
{
	struct acpi_device *adev = NULL;

	acpi_add_single_object(&adev, NULL, type, false);
	if (adev)
		acpi_default_enumeration(adev);
}

static void acpi_bus_scan_fixed(void)
{
	if (!(acpi_gbl_FADT.flags & ACPI_FADT_POWER_BUTTON))
		acpi_bus_add_fixed_device_object(ACPI_BUS_TYPE_POWER_BUTTON);

	if (!(acpi_gbl_FADT.flags & ACPI_FADT_SLEEP_BUTTON))
		acpi_bus_add_fixed_device_object(ACPI_BUS_TYPE_SLEEP_BUTTON);
}
```

The fabricated [`struct acpi_device`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_bus.h#L471) has no namespace handle, so [`acpi_set_pnp_ids()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/scan.c#L1388) assigns it a synthetic Linux HID that the button driver matches on.

```c
/* drivers/acpi/scan.c:1463 */
	case ACPI_BUS_TYPE_POWER_BUTTON:
		acpi_add_id(pnp, ACPI_BUTTON_HID_POWERF);
		break;
	case ACPI_BUS_TYPE_SLEEP_BUTTON:
		acpi_add_id(pnp, ACPI_BUTTON_HID_SLEEPF);
		break;
```

[`ACPI_BUTTON_HID_POWERF`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L24) expands to the string `LNXPWRBN` and [`ACPI_BUTTON_HID_SLEEPF`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpi_drivers.h#L25) to `LNXSLPBN`, both listed in the driver's [`button_device_ids`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L61) match table next to the control-method HIDs `PNP0C0C` and `PNP0C0E`. [`acpi_button_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L532) tells the two models apart by `device->device_type` and installs the fixed-event handler only for the fixed-hardware case, falling back to an ACPI notify handler otherwise.

```c
/* drivers/acpi/button.c:532 */
static int acpi_button_probe(struct platform_device *pdev)
{
	struct acpi_device *device = ACPI_COMPANION(&pdev->dev);
	...
	switch (device->device_type) {
	case ACPI_BUS_TYPE_POWER_BUTTON:
		status = acpi_install_fixed_event_handler(ACPI_EVENT_POWER_BUTTON,
							  acpi_button_event,
							  button);
		break;
	case ACPI_BUS_TYPE_SLEEP_BUTTON:
		status = acpi_install_fixed_event_handler(ACPI_EVENT_SLEEP_BUTTON,
							  acpi_button_event,
							  button);
		break;
	default:
		status = acpi_install_notify_handler(device->handle,
						     ACPI_ALL_NOTIFY, handler,
						     button);
		break;
	}
```

[`acpi_button_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L481) is a textbook [`acpi_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1055) implementation; it runs at ACPI interrupt level, punts the real work to the [`OSL_NOTIFY_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/acpiosxf.h#L22) workqueue, and reports the event consumed.

```c
/* drivers/acpi/button.c:476 */
static void acpi_button_notify_run(void *data)
{
	acpi_button_notify(NULL, ACPI_BUTTON_NOTIFY_STATUS, data);
}

static u32 acpi_button_event(void *data)
{
	acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_button_notify_run, data);
	return ACPI_INTERRUPT_HANDLED;
}
```

The deferred [`acpi_button_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L440) then registers a wakeup event via [`acpi_pm_wakeup_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/device_pm.c#L523) and emits `KEY_POWER` or `KEY_SLEEP` through the input subsystem, so userspace sees a fixed-hardware button press exactly like a control-method one. On the teardown side, [`acpi_button_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/button.c#L673) undoes the registration with the matching event constants.

```c
/* drivers/acpi/button.c:678 */
	switch (adev->device_type) {
	case ACPI_BUS_TYPE_POWER_BUTTON:
		acpi_remove_fixed_event_handler(ACPI_EVENT_POWER_BUTTON,
						acpi_button_event);
		break;
	case ACPI_BUS_TYPE_SLEEP_BUTTON:
		acpi_remove_fixed_event_handler(ACPI_EVENT_SLEEP_BUTTON,
						acpi_button_event);
		break;
```

### The CMOS RTC driver gates RTC_EN around alarms

[`drivers/rtc/rtc-cmos.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c) owns [`ACPI_EVENT_RTC`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L725) and demonstrates the full lifecycle of a fixed event around system sleep. [`acpi_rtc_event_setup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L783) installs the handler at probe time and immediately parks the event disabled.

```c
/* drivers/rtc/rtc-cmos.c:783 */
static void acpi_rtc_event_setup(struct device *dev)
{
	if (acpi_disabled)
		return;

	acpi_install_fixed_event_handler(ACPI_EVENT_RTC, rtc_handler, dev);
	/*
	 * After the RTC handler is installed, the Fixed_RTC event should
	 * be disabled. Only when the RTC alarm is set will it be enabled.
	 */
	acpi_clear_event(ACPI_EVENT_RTC);
	acpi_disable_event(ACPI_EVENT_RTC, 0);
}
```

According to the comment "Only when the RTC alarm is set will it be enabled", the enable bit tracks alarm state rather than driver lifetime, so [`rtc_wake_on()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L805) and [`rtc_wake_off()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L811) flip RTC_EN exactly when an alarm is armed or torn down.

```c
/* drivers/rtc/rtc-cmos.c:805 */
static void rtc_wake_on(struct device *dev)
{
	acpi_clear_event(ACPI_EVENT_RTC);
	acpi_enable_event(ACPI_EVENT_RTC, 0);
}

static void rtc_wake_off(struct device *dev)
{
	acpi_disable_event(ACPI_EVENT_RTC, 0);
}
```

When the alarm fires, [`rtc_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/rtc/rtc-cmos.c#L747) reports the wakeup, acknowledges the latch with [`acpi_clear_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L265), disarms RTC_EN with [`acpi_disable_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L205) (an RTC alarm is one-shot), and returns [`ACPI_INTERRUPT_HANDLED`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L1145).

```c
/* drivers/rtc/rtc-cmos.c:747 */
static u32 rtc_handler(void *context)
{
	struct device *dev = context;
	struct cmos_rtc *cmos = dev_get_drvdata(dev);
	...
	pm_wakeup_hard_event(dev);
	acpi_clear_event(ACPI_EVENT_RTC);
	acpi_disable_event(ACPI_EVENT_RTC, 0);
	return ACPI_INTERRUPT_HANDLED;
}
```

### Resume consumes a pending PWRBTN_STS

[`acpi_suspend_enter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c#L598) shows the polling side of the API. Right after an S3 resume it asks [`acpi_get_event_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L309) whether the power button latched during the sleep window, clears the bit with [`acpi_clear_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L265), and remembers the fact for a later wakeup-event report.

```c
/* drivers/acpi/sleep.c:598 */
static int acpi_suspend_enter(suspend_state_t pm_state)
{
	acpi_status status = AE_OK;
	u32 acpi_state = acpi_target_sleep_state;
	...
	/* ACPI 3.0 specs (P62) says that it's the responsibility
	 * of the OSPM to clear the status bit [ implying that the
	 * POWER_BUTTON event should not reach userspace ]
	 *
	 * However, we do generate a small hint for userspace in the form of
	 * a wakeup event. We flag this condition for now and generate the
	 * event later, as we're currently too early in resume to be able to
	 * generate wakeup events.
	 */
	if (ACPI_SUCCESS(status) && (acpi_state == ACPI_STATE_S3)) {
		acpi_event_status pwr_btn_status = ACPI_EVENT_FLAG_DISABLED;

		acpi_get_event_status(ACPI_EVENT_POWER_BUTTON, &pwr_btn_status);

		if (pwr_btn_status & ACPI_EVENT_FLAG_STATUS_SET) {
			acpi_clear_event(ACPI_EVENT_POWER_BUTTON);
			/* Flag for later */
			pwr_btn_event_pending = true;
		}
	}
```

[`acpi_get_event_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L309) composes its answer from three sources, setting [`ACPI_EVENT_FLAG_HAS_HANDLER`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L754) from the [`acpi_gbl_fixed_event_handlers`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L243) slot and [`ACPI_EVENT_FLAG_ENABLE_SET`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L753) plus [`ACPI_EVENT_FLAG_STATUS_SET`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h#L752) from two [`acpi_read_bit_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/hwxface.c#L153) calls on the event's enable and status IDs.

```c
/* drivers/acpi/acpica/evxfevnt.c:309 */
acpi_status acpi_get_event_status(u32 event, acpi_event_status * event_status)
{
	acpi_status status;
	acpi_event_status local_event_status = 0;
	u32 in_byte;
	...
	/* Fixed event currently can be dispatched? */

	if (acpi_gbl_fixed_event_handlers[event].handler) {
		local_event_status |= ACPI_EVENT_FLAG_HAS_HANDLER;
	}

	/* Fixed event currently enabled? */

	status =
	    acpi_read_bit_register(acpi_gbl_fixed_event_info[event].
				   enable_register_id, &in_byte);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	if (in_byte) {
		local_event_status |=
		    (ACPI_EVENT_FLAG_ENABLED | ACPI_EVENT_FLAG_ENABLE_SET);
	}

	/* Fixed event currently active? */

	status =
	    acpi_read_bit_register(acpi_gbl_fixed_event_info[event].
				   status_register_id, &in_byte);
	if (ACPI_FAILURE(status)) {
		return_ACPI_STATUS(status);
	}

	if (in_byte) {
		local_event_status |= ACPI_EVENT_FLAG_STATUS_SET;
	}

	(*event_status) = local_event_status;
	return_ACPI_STATUS(AE_OK);
}
```

### Per-event counters under /sys/firmware/acpi/interrupts

Linux registers [`acpi_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L637) into the [`acpi_gbl_global_event_handler`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L241) hook seen earlier in the detect loop, so every dispatched fixed event also increments a sysfs counter.

```c
/* drivers/acpi/sysfs.c:625 */
static void fixed_event_count(u32 event_number)
{
	if (!all_counters)
		return;

	if (event_number < ACPI_NUM_FIXED_EVENTS)
		all_counters[num_gpes + event_number].count++;
	else
		all_counters[num_gpes + ACPI_NUM_FIXED_EVENTS +
			     COUNT_ERROR].count++;
}

static void acpi_global_event_handler(u32 event_type, acpi_handle device,
	u32 event_number, void *context)
{
	if (event_type == ACPI_EVENT_TYPE_GPE) {
		gpe_count(event_number);
		pr_debug("GPE event 0x%02x\n", event_number);
	} else if (event_type == ACPI_EVENT_TYPE_FIXED) {
		fixed_event_count(event_number);
		pr_debug("Fixed event 0x%02x\n", event_number);
	} else {
		pr_debug("Other event 0x%02x\n", event_number);
	}
}
```

[`acpi_irq_stats_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L856) performs the registration through [`acpi_install_global_event_handler()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxface.c#L534) and names one attribute file per event index using the same `ACPI_EVENT_*` constants.

```c
/* drivers/acpi/sysfs.c:889 */
		else if (i == num_gpes + ACPI_EVENT_PMTIMER)
			sprintf(buffer, "ff_pmtimer");
		else if (i == num_gpes + ACPI_EVENT_GLOBAL)
			sprintf(buffer, "ff_gbl_lock");
		else if (i == num_gpes + ACPI_EVENT_POWER_BUTTON)
			sprintf(buffer, "ff_pwr_btn");
		else if (i == num_gpes + ACPI_EVENT_SLEEP_BUTTON)
			sprintf(buffer, "ff_slp_btn");
		else if (i == num_gpes + ACPI_EVENT_RTC)
			sprintf(buffer, "ff_rt_clk");
```

The files are writable, and [`counter_set()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L732) turns the strings `enable`, `disable` and `clear` into the corresponding public API calls, which makes `/sys/firmware/acpi/interrupts/ff_rt_clk` a userspace remote control for the event's PM1 bits.

```c
/* drivers/acpi/sysfs.c:780 */
	} else if (index < num_gpes + ACPI_NUM_FIXED_EVENTS) {
		int event = index - num_gpes;
		if (!strcmp(buf, "disable\n") &&
		    (status & ACPI_EVENT_FLAG_ENABLE_SET))
			result = acpi_disable_event(event, ACPI_NOT_ISR);
		else if (!strcmp(buf, "enable\n") &&
			 !(status & ACPI_EVENT_FLAG_ENABLE_SET))
			result = acpi_enable_event(event, ACPI_NOT_ISR);
		else if (!strcmp(buf, "clear\n") &&
			 (status & ACPI_EVENT_FLAG_STATUS_SET))
			result = acpi_clear_event(event);
		else if (!kstrtoul(buf, 0, &tmp))
			all_counters[index].count = tmp;
		else
			result = -EINVAL;
	}
```

[`counter_show()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L675) reads back each event's live state through [`acpi_get_event_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evxfevnt.c#L309) (via its [`get_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sysfs.c#L651) helper) and renders the `EN`, `STS`, `enabled` and `masked` columns documented in [`Documentation/ABI/testing/sysfs-firmware-acpi`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/ABI/testing/sysfs-firmware-acpi), while the counter values themselves come from the [`acpi_fixed_event_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/acglobal.h#L260) increments performed inside [`acpi_ev_fixed_event_detect()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/acpica/evevent.c#L167).
