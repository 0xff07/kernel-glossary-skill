# SoundWire bank switching

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A SoundWire bus keeps two copies of every transport and channel-configuration register, bank 0 and bank 1, with only one bank active at a time, and a stream reconfiguration writes the new layout into the idle bank then flips the active bank at a frame boundary so the change applies on one frame with no torn samples. The live bank is recorded per bus in [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) as [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), each an [`enum sdw_reg_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539) value, and the flip is carried out by [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845), which runs the manager [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) callback, programs [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) (0x60) or [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218) (0x70) through the static [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742), and then runs the manager [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) callback. On an Intel x86-64 ACPI platform (LNL or MTL with an rt722-sdca codec) the two callbacks resolve to the host-controller hooks [`intel_pre_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L243) and [`intel_post_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L257), which arm and fire the multi-link hardware sync. The deferred frame-control write completes through the bus [`defer_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) holder, a [`struct sdw_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826), and [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817) waits on it.

```
    SoundWire channel-config register banks (one Slave/Master view)
    ───────────────────────────────────────────────────────────────

                 bank 0                            bank 1
    ┌───────────────────────────┐     ┌───────────────────────────┐
    │ SCP_FrameCtrl_B0  (0x60)  │     │ SCP_FrameCtrl_B1  (0x70)  │
    │ DPn_ChannelEn_B0  (..20)  │     │ DPn_ChannelEn_B1  (..30)  │
    │ DPn_SampleCtrl_B0 (..22)  │     │ DPn_SampleCtrl_B1 (..32)  │
    │ DPn_OffsetCtrl_B0 (..24)  │     │ DPn_OffsetCtrl_B1 (..34)  │
    └───────────────────────────┘     └───────────────────────────┘
                ▲                                   ▲
       curr_bank = 0                       next_bank = 1
       (live, driving frames)              (being programmed)

                 next-frame switch (write to SCP_FrameCtrl_Bx,
                 ssp_sync = true): hardware adopts the new bank
                 at the next frame boundary, atomically
                                  │
                                  ▼
                 curr_bank = 1                       next_bank = 0
                 (now live)                          (now idle)

    bank 1 register address = bank 0 address + SDW_BANK1_OFFSET (0x10)
```

## SUMMARY

SoundWire defines its transport and channel-enable registers in two banks so a stream reconfiguration never disturbs the audio currently in flight. The bus programs the new frame shape (columns and rows) and the new per-port channel mask into the inactive bank, leaves the live bank untouched, and then issues one frame-control write that the Slaves and the manager apply together at the next frame boundary. After that boundary the inactive bank is the active bank and the old active bank is free for the next change. The kernel models the two banks per bus in [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), whose [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) are each one of [`SDW_BANK0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539) and [`SDW_BANK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539) from [`enum sdw_reg_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539), held inside the per-bus [`params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) member of [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014). The invariant recorded in the [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) comment is that [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) is always the complement of [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593).

The switch runs from one place. [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) walks every manager runtime attached to the stream, calls the manager [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op, performs the per-manager [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742), and then in a second pass calls the manager [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op and waits for the hardware-synchronized flip through [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817). [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742) builds a broadcast write of the frame shape to [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) or [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218) depending on [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), marks the message [`ssp_sync`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L71) so the controller emits it at the Stream Synchronization Point, and either defers the message on a multi-link bus or sends it synchronously on a single link. The per-port channel masks were written earlier into the inactive bank by [`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317) using [`SDW_DPN_CHANNELEN_B0(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) or [`SDW_DPN_CHANNELEN_B1(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268). After a successful flip, [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) are toggled so the next reconfiguration targets the now-idle bank.

The four stream state transitions that change the channel layout each end with a bank switch. [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533), [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619), [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707), and [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) each program the inactive bank and then call [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) from their internal helpers. Those four ops are the callers of the bank mechanism this page describes; the mechanism itself is the two register banks, the frame-control trigger, the deferred completion, the multi-link sync, and the banked register map. The [`multi_link`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) flag on [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and the [`hw_sync_min_links`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) threshold decide whether the flip is hardware-synchronized across several SoundWire segments, in which case the deferred frame-control write completes through the bus [`defer_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) completion under the [`bank_switch_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) deadline, which [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) defaults to [`DEFAULT_BANK_SWITCH_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L7) (3000) when it is unset.

## SPECIFICATIONS

The MIPI SoundWire specification defines the dual-bank model for transport and data-port registers, the SCP_FrameCtrl banked register that carries the row and column frame shape, the per-data-port DPn_ChannelEn banked register, and the next-frame mechanism that adopts the alternate bank at a frame boundary. The specification is membership-gated and is not linked here. This page describes only the Linux kernel implementation of that model and the named SCP and DPn banked registers as defined by their kernel macros in [`include/linux/soundwire/sdw_registers.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h), where bank 1 is bank 0 plus [`SDW_BANK1_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L22) (0x10) and each data port DPn is reached at a stride of [`SDW_DPN_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L21) (0x100).

## LINUX KERNEL

### Bank state types (include/linux/soundwire/sdw.h)

- [`'\<enum sdw_reg_bank\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539): the two register banks, [`SDW_BANK0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539) and [`SDW_BANK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539)
- [`'\<struct sdw_bus_params\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593): per-bus configuration holding [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), and the active [`col`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593)/[`row`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) frame shape
- [`'\<struct sdw_bus\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014): the bus instance carrying [`params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) callbacks, the [`multi_link`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) flag, [`hw_sync_min_links`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), [`bank_switch_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), and [`defer_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)
- [`'\<struct sdw_master_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861): the manager function pointer struct supplying [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861), [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861), and [`xfer_msg_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861)
- [`'\<struct sdw_defer\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826): the deferred-message holder with the [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826) completion the hardware sync waits on
- [`'\<enum sdw_stream_state\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926): the stream states whose transitions ([`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926)) each end in a bank switch
- [`'\<enum sdw_command_response\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L129): the command response the deferred transfer maps to a return code, with [`SDW_CMD_OK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L129) and [`SDW_CMD_IGNORED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L129) treated as success

### Banked register macros (include/linux/soundwire/sdw_registers.h)

- [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) / [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218): the bank 0 (0x60) and bank 1 (0x70) frame-control registers carrying the column and row index, the destination of the bank-flip write
- [`SDW_SCP_NEXTFRAME_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L219) / [`SDW_SCP_NEXTFRAME_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L220): the companion banked registers (0x61, 0x71) for the upcoming frame shape
- [`SDW_DPN_CHANNELEN_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) / [`SDW_DPN_CHANNELEN_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268): the per-port channel-enable registers (0x20 and 0x30 within the port block), written into the inactive bank before the flip
- [`SDW_BANK1_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L22): the 0x10 offset that separates a bank 1 SCP register from its bank 0 counterpart
- [`SDW_DPN_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L21): the 0x100 per-data-port stride that the DPn macros multiply by the port number
- [`SDW_BROADCAST_DEV_NUM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L30): device number 15, the broadcast target of the frame-control write so every peripheral flips together
- [`DEFAULT_BANK_SWITCH_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L7): 3000, the default deadline copied into [`bank_switch_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)

### Bank switch core (drivers/soundwire/stream.c)

- [`'\<do_bank_switch\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845): orchestrates the switch across all managers of a stream, running [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861), [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742), [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861), and [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817)
- [`'\<sdw_bank_switch\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742): builds and sends the broadcast frame-control write to [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217)/[`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218); toggles [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593)/[`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) on the single-link path
- [`'\<sdw_ml_sync_bank_switch\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817): for the multi-link path, waits on [`defer_msg.complete`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826) under [`bank_switch_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and toggles the bank state once the hardware reports the flip
- [`'\<sdw_enable_disable_slave_ports\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317): writes the per-port channel mask into the inactive bank's [`SDW_DPN_CHANNELEN_B0(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) or [`SDW_DPN_CHANNELEN_B1(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268)
- [`'\<sdw_enable_disable_ports\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389): walks the Slave and Master ports of a manager runtime, calling [`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317) per Slave port
- [`'\<sdw_program_params\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661): programs transport and port parameters into the alternate bank before the switch
- [`'\<sdw_find_col_index\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L35) / [`'\<sdw_find_row_index\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L49): translate the active column and row counts into the index encoding written to SCP_FrameCtrl

### Stream lifecycle callers (drivers/soundwire/stream.c)

- [`'\<sdw_prepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) / [`'\<_sdw_prepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453): program the new frame shape on the alternate bank, then [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845), then prepare ports on the new clock
- [`'\<sdw_enable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) / [`'\<_sdw_enable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576): enable ports on the alternate bank, then [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) to make the channels live
- [`'\<sdw_disable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) / [`'\<_sdw_disable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651): disable ports on the alternate bank, then [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845), then disable the now-previous bank too
- [`'\<sdw_deprepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) / [`'\<_sdw_deprepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1738): deprepare ports, recompute bandwidth, then [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845)

### Message transport (drivers/soundwire/bus.c, cadence_master.c)

- [`'\<sdw_transfer\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L295): synchronous frame-control write on the single-link path
- [`'\<sdw_transfer_defer\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L347) / [`'\<do_transfer_defer\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L253): deferred frame-control write on the multi-link path; arms [`defer_msg.complete`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826) via [`init_completion()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/completion.h#L84) and calls the manager [`xfer_msg_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op
- [`'\<sdw_fill_msg\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L362): populates the [`struct sdw_msg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L63) the frame-control write uses, with [`SDW_BROADCAST_DEV_NUM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L30) (15) as the device number
- [`'\<cdns_xfer_msg_defer\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L797): the Cadence IP [`xfer_msg_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op that submits the single deferred frame-control message to the controller

### Intel x86 ACPI manager hooks (drivers/soundwire)

- [`'\<intel_pre_bank_switch\>':'drivers/soundwire/intel_bus_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L243): the [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op for Intel controllers; arms the multi-link sync with [`sdw_intel_sync_arm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L225)
- [`'\<intel_post_bank_switch\>':'drivers/soundwire/intel_bus_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L257): the [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op; fires the synchronized flip with [`sdw_intel_sync_go_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L231) when [`sdw_intel_sync_check_cmdsync_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L245) reports a pending CMDSYNC
- [`'\<generic_pre_bank_switch\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L105) / [`'\<generic_post_bank_switch\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L113): the [`struct sdw_master_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) entries registered in [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281), forwarding to the per-generation [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L231) bank-switch hooks
- [`'\<sdw_intel_sync_arm\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L225) / [`'\<sdw_intel_sync_go_unlocked\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L231): the per-generation dispatch wrappers that arm a link and write SYNCGO into the controller SHIM

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the stream state machine, where prepare, enable, disable, and deprepare each program the alternate bank and then switch banks so the new values take effect
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus overview, the manager and peripheral roles, and the frame structure of columns and rows
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the bus and message locks the bank switch takes while deferring the multi-link frame-control write
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): how a failed transfer during reconfiguration is unwound

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## REGISTERS

The banked registers occupy a fixed layout. Bank 1 is bank 0 plus [`SDW_BANK1_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L22) (0x10) for the SCP registers, and each data port DPn is reached at a stride of [`SDW_DPN_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L21) (0x100) from the port number, with the bank 0 and bank 1 channel-enable registers offset 0x10 apart inside the port block. The SCP_FrameCtrl register is one byte that packs two index fields, so it is drawn to scale below as a single-byte register.

```
    SCP_FrameCtrl_Bx byte (write that triggers the bank flip)
    ─────────────────────────────────────────────────────────

    bit    7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┐
    DW0   │row_index│ col │
          │  (7:3)  │(2:0)│
          └─┴─┴─┴─┴─┴─┴─┴─┘

    col_index = sdw_find_col_index(bus->params.col)   (bits 2:0)
    row_index = sdw_find_row_index(bus->params.row)   (bits 7:3)
    wbuf[0]   = col_index | (row_index << 3)
    written with ssp_sync = true to SDW_SCP_FRAMECTRL_B0 (0x60)
    or SDW_SCP_FRAMECTRL_B1 (0x70) so the bank flips at a frame boundary
```

The two banks present the same register set at two address ranges.

```
    Banked SCP and DPn registers (per Slave/Master register map)
    ─────────────────────────────────────────────────────────────

    bank 0                       bank 1                  next-frame role
    ───────────────────────────  ──────────────────────  ───────────────
    SCP_FrameCtrl_B0   (0x60)    SCP_FrameCtrl_B1 (0x70)  frame shape +
                                                          bank-flip trigger
    SCP_NextFrame_B0   (0x61)    SCP_NextFrame_B1 (0x71)  next-frame shape
    DPn_ChannelEn_B0 (n*0x100    DPn_ChannelEn_B1 (n*..   active channel
                      + 0x20)                    + 0x30)  mask per port

    SCP_FrameCtrl_Bx encodes (col_index | (row_index << 3))
    bank 1 SCP address = bank 0 address + SDW_BANK1_OFFSET (0x10)
    DPn block base = SDW_DPN_SIZE (0x100) * port number
```

The frame-control write is the trigger. [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742) selects [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218) (0x70) when [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) is [`SDW_BANK1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539) and [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) (0x60) otherwise, so the write that programs the new frame shape into the alternate bank is also the write whose [`ssp_sync`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L71) timing makes that bank active. [`SDW_SCP_NEXTFRAME_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L219) (0x61) and [`SDW_SCP_NEXTFRAME_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L220) are the companion banked registers that carry the upcoming frame shape. The channel masks are written separately into the inactive bank, where [`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317) targets [`SDW_DPN_CHANNELEN_B1(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268) when [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) is set and [`SDW_DPN_CHANNELEN_B0(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) otherwise.

| Register | Bank 0 | Bank 1 | Macro |
|----------|--------|--------|-------|
| SCP_FrameCtrl | 0x60 | 0x70 | [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) / [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218) |
| SCP_NextFrame | 0x61 | 0x71 | [`SDW_SCP_NEXTFRAME_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L219) / [`SDW_SCP_NEXTFRAME_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L220) |
| DPn_ChannelEn | n*0x100 + 0x20 | n*0x100 + 0x30 | [`SDW_DPN_CHANNELEN_B0(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) / [`SDW_DPN_CHANNELEN_B1(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268) |

## DETAILS

### The two banks and the bank state

A SoundWire peripheral and the manager each keep two copies of the transport and channel-enable registers. Bank 0 starts at the base address and bank 1 sits [`SDW_BANK1_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L22) above it for the SCP frame-control register, while each data port's bank 1 channel-enable register sits 0x10 above its bank 0 counterpart inside a [`SDW_DPN_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L21)-stride port block:

```c
/* include/linux/soundwire/sdw_registers.h:21 */
#define SDW_DPN_SIZE				0x100
#define SDW_BANK1_OFFSET			0x10
```

```c
/* include/linux/soundwire/sdw_registers.h:217 */
/* Banked Registers */
#define SDW_SCP_FRAMECTRL_B0			0x60
#define SDW_SCP_FRAMECTRL_B1			(0x60 + SDW_BANK1_OFFSET)
#define SDW_SCP_NEXTFRAME_B0			0x61
#define SDW_SCP_NEXTFRAME_B1			(0x61 + SDW_BANK1_OFFSET)
```

```c
/* include/linux/soundwire/sdw_registers.h:267 */
#define SDW_DPN_CHANNELEN_B0(n)			(0x20 + SDW_DPN_SIZE * (n))
#define SDW_DPN_CHANNELEN_B1(n)			(0x30 + SDW_DPN_SIZE * (n))
```

Which bank is live is tracked per bus in [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593). The two fields [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) are each an [`enum sdw_reg_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L539), and the struct comment records the invariant that [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) is always set to the complement of [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593):

```c
/* include/linux/soundwire/sdw.h:593 */
/**
 * struct sdw_bus_params: Structure holding bus configuration
 *
 * @curr_bank: Current bank in use (BANK0/BANK1)
 * @next_bank: Next bank to use (BANK0/BANK1). next_bank will always be
 * set to !curr_bank
 * @max_dr_freq: Maximum double rate clock frequency supported, in Hz
 * @curr_dr_freq: Current double rate clock frequency, in Hz
 * @bandwidth: Current bandwidth
 * @col: Active columns
 * @row: Active rows
 * @s_data_mode: NORMAL, STATIC or PRBS mode for all Slave ports
 * @m_data_mode: NORMAL, STATIC or PRBS mode for all Master ports. ...
 */
struct sdw_bus_params {
	enum sdw_reg_bank curr_bank;
	enum sdw_reg_bank next_bank;
	unsigned int max_dr_freq;
	unsigned int curr_dr_freq;
	unsigned int bandwidth;
	unsigned int col;
	unsigned int row;
	int s_data_mode;
	int m_data_mode;
};
```

```c
/* include/linux/soundwire/sdw.h:539 */
/**
 * sdw_reg_bank - SoundWire register banks
 * @SDW_BANK0: Soundwire register bank 0
 * @SDW_BANK1: Soundwire register bank 1
 */
enum sdw_reg_bank {
	SDW_BANK0,
	SDW_BANK1,
};
```

These [`params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) are embedded in [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), alongside the manager [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), the [`defer_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) deferred-message holder, the [`multi_link`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) flag, the [`hw_sync_min_links`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) threshold, and the [`bank_switch_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014):

```c
/* include/linux/soundwire/sdw.h:1014 */
struct sdw_bus {
	struct device *dev;
	struct sdw_master_device *md;
	...
	struct sdw_defer defer_msg;
	struct sdw_bus_params params;
	...
	const struct sdw_master_ops *ops;
	const struct sdw_master_port_ops *port_ops;
	struct sdw_master_prop prop;
	void *vendor_specific_prop;
	int hw_sync_min_links;
	...
	u32 bank_switch_timeout;
	...
	bool multi_link;
	unsigned int lane_used_bandwidth[SDW_MAX_LANES];
};
```

Two of these members open into their own boxes, params holding the current and next bank (next is the complement of current) and defer_msg holding the deferred message and its completion:

```
    struct sdw_bus embeds the bank state (boxes are structs)
    ──────────────────────────────────────────────────────────

    ┌───────────────────────────┐
    │ struct sdw_bus            │
    │   params                  │
    │   defer_msg               │
    │   ops                     │
    │   multi_link              │
    │   hw_sync_min_links       │
    │   bank_switch_timeout     │
    └───────────────────────────┘
                  │ params                      │ defer_msg
                  ▼                             ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │ struct sdw_bus_params     │   │ struct sdw_defer          │
    │   curr_bank               │   │   msg     (sdw_msg *)     │
    │   next_bank  =!curr_bank  │   │   length                  │
    │   col                     │   │   complete (completion)   │
    │   row                     │   └───────────────────────────┘
    └───────────────────────────┘

    curr_bank / next_bank : enum sdw_reg_bank (SDW_BANK0, SDW_BANK1)
```

### do_bank_switch orchestrates the two passes

[`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) is the single point that performs a switch for a whole stream, and it runs two passes over the manager runtimes in the stream's master list. The first pass takes [`msg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) for multi-link buses that cross at least [`hw_sync_min_links`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) segments, runs the manager [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op, and then performs the per-manager [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742):

```c
/* drivers/soundwire/stream.c:845 */
static int do_bank_switch(struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt;
	const struct sdw_master_ops *ops;
	struct sdw_bus *bus;
	bool multi_link = false;
	int m_rt_count;
	int ret = 0;

	m_rt_count = stream->m_rt_count;

	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;
		ops = bus->ops;

		if (bus->multi_link && m_rt_count >= bus->hw_sync_min_links) {
			multi_link = true;
			mutex_lock(&bus->msg_lock);
		}

		/* Pre-bank switch */
		if (ops->pre_bank_switch) {
			ret = ops->pre_bank_switch(bus);
			if (ret < 0) {
				dev_err(bus->dev,
					"Pre bank switch op failed: %d\n", ret);
				goto msg_unlock;
			}
		}

		/*
		 * Perform Bank switch operation.
		 * For multi link cases, the actual bank switch is
		 * synchronized across all Masters and happens later as a
		 * part of post_bank_switch ops.
		 */
		ret = sdw_bank_switch(bus, m_rt_count);
		if (ret < 0) {
			dev_err(bus->dev, "Bank switch failed: %d\n", ret);
			goto error;
		}
	}
	...
}
```

According to the comment on the second loop, the bank switch "is triggered by the post_bank_switch for the first Master in the list and for the other Masters the post_bank_switch() should return doing nothing". The second pass therefore runs the manager [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op, defaults [`bank_switch_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) to [`DEFAULT_BANK_SWITCH_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L7) when unset, and waits for the flip with [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817):

```c
/* drivers/soundwire/stream.c:894 */
	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;
		ops = bus->ops;

		/* Post-bank switch */
		if (ops->post_bank_switch) {
			ret = ops->post_bank_switch(bus);
			if (ret < 0) {
				dev_err(bus->dev,
					"Post bank switch op failed: %d\n",
					ret);
				goto error;
			}
		} else if (multi_link) {
			dev_err(bus->dev,
				"Post bank switch ops not implemented\n");
			ret = -EINVAL;
			goto error;
		}

		/* Set the bank switch timeout to default, if not set */
		if (!bus->bank_switch_timeout)
			bus->bank_switch_timeout = DEFAULT_BANK_SWITCH_TIMEOUT;

		/* Check if bank switch was successful */
		ret = sdw_ml_sync_bank_switch(bus, multi_link);
		if (ret < 0) {
			dev_err(bus->dev,
				"multi link bank switch failed: %d\n", ret);
			goto error;
		}

		if (multi_link)
			mutex_unlock(&bus->msg_lock);
	}

	return ret;
```

The default deadline is a 3000 jiffy timeout:

```c
/* drivers/soundwire/bus.h:7 */
#define DEFAULT_BANK_SWITCH_TIMEOUT 3000
```

That timeout caps the multi-link sync wait in the second pass, with the two runs over the manager list shown side by side, single-link buses toggling the bank on the first write and multi-link buses toggling after the completion wakes:

```
    do_bank_switch(): two passes over the stream's manager list
    ─────────────────────────────────────────────────────────────
    (each pass loops every manager M0..Mk; msg_lock held for multi-link)

    ┌──────────────────────────┐     ┌──────────────────────────┐
    │ Pass 1 (each manager):   │     │ Pass 2 (each manager):   │
    │   pre_bank_switch        │ ──▶ │   post_bank_switch       │
    │   sdw_bank_switch        │     │   sdw_ml_sync_bank_switch│
    └──────────────────────────┘     └──────────────────────────┘

    where curr_bank / next_bank actually toggle:
      single-link : in Pass 1, sdw_bank_switch sends the write
                    synchronously and toggles at once
      multi-link  : in Pass 2, post_bank_switch fires SYNCGO, the
                    completion wakes, then the bank state toggles
```

### sdw_bank_switch writes SCP_FrameCtrl into the inactive bank

[`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742) builds the frame-control write. It converts the active column and row counts to their index encoding with [`sdw_find_col_index()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L35) and [`sdw_find_row_index()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L49), packs them as `col_index | (row_index << 3)`, and selects the destination register from [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), choosing [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218) when the next bank is bank 1 and [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) otherwise:

```c
/* drivers/soundwire/stream.c:742 */
static int sdw_bank_switch(struct sdw_bus *bus, int m_rt_count)
{
	int col_index, row_index;
	bool multi_link;
	struct sdw_msg *wr_msg;
	u8 *wbuf;
	int ret;
	u16 addr;

	wr_msg = kzalloc_obj(*wr_msg);
	if (!wr_msg)
		return -ENOMEM;

	wbuf = kzalloc_obj(*wbuf);
	if (!wbuf) {
		ret = -ENOMEM;
		goto error_1;
	}

	/* Get row and column index to program register */
	col_index = sdw_find_col_index(bus->params.col);
	row_index = sdw_find_row_index(bus->params.row);
	wbuf[0] = col_index | (row_index << 3);

	if (bus->params.next_bank)
		addr = SDW_SCP_FRAMECTRL_B1;
	else
		addr = SDW_SCP_FRAMECTRL_B0;

	sdw_fill_msg(wr_msg, NULL, addr, 1, SDW_BROADCAST_DEV_NUM,
		     SDW_MSG_FLAG_WRITE, wbuf);
	wr_msg->ssp_sync = true;
	...
}
```

The write is built with [`sdw_fill_msg()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L362) against [`SDW_BROADCAST_DEV_NUM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L30) so every peripheral on the link adopts the new bank together, and [`wr_msg->ssp_sync`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L71) is set so the controller emits the command at the Stream Synchronization Point, the frame boundary at which the bank flip takes effect. According to the comment on the [`ssp_sync`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L71) field of [`struct sdw_msg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L63), the message is sent "at SSP (Stream Synchronization Point)":

```c
/* drivers/soundwire/bus.h:63 */
/**
 * struct sdw_msg - Message structure
 * @addr: Register address accessed in the Slave
 * @len: number of messages
 * @dev_num: Slave device number
 * @addr_page1: SCP address page 1 Slave register
 * @addr_page2: SCP address page 2 Slave register
 * @flags: transfer flags, indicate if xfer is read or write
 * @buf: message data buffer
 * @ssp_sync: Send message at SSP (Stream Synchronization Point)
 * @page: address requires paging
 */
struct sdw_msg {
	u16 addr;
	u16 len;
	u8 dev_num;
	u8 addr_page1;
	u8 addr_page2;
	u8 flags;
	u8 *buf;
	bool ssp_sync;
	bool page;
};
```

The tail of [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742) chooses the transport based on whether hardware synchronization is required. A multi-link bus that crosses at least [`hw_sync_min_links`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) segments defers the write through [`sdw_transfer_defer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L347) and leaves the bank state alone; a single-link bus sends synchronously with [`sdw_transfer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L295), frees the message, and toggles [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) immediately:

```c
/* drivers/soundwire/stream.c:776 */
	/*
	 * Set the multi_link flag only when both the hardware supports
	 * and hardware-based sync is required
	 */
	multi_link = bus->multi_link && (m_rt_count >= bus->hw_sync_min_links);

	if (multi_link)
		ret = sdw_transfer_defer(bus, wr_msg);
	else
		ret = sdw_transfer(bus, wr_msg);

	if (ret < 0 && ret != -ENODATA) {
		dev_err(bus->dev, "Slave frame_ctrl reg write failed\n");
		goto error;
	}

	if (!multi_link) {
		kfree(wbuf);
		kfree(wr_msg);
		bus->defer_msg.msg = NULL;
		bus->params.curr_bank = !bus->params.curr_bank;
		bus->params.next_bank = !bus->params.next_bank;
	}

	return 0;
```

On the single-link path the toggle of [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) happens here because [`sdw_transfer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L295) has already completed the synchronous write and the flip has occurred. On the multi-link path the toggle is deferred to [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817), which runs only after the hardware confirms the synchronized flip.

```
    Building the frame-control write in sdw_bank_switch()
    ───────────────────────────────────────────────────────

    bus->params.col ──▶ sdw_find_col_index ──▶ col_index ─┐
    bus->params.row ──▶ sdw_find_row_index ──▶ row_index ─┤
                                                          ▼
                          wbuf[0] = col_index, (row_index << 3) ─┐
                                                                 │
    next_bank == SDW_BANK1 ──▶ addr = SDW_SCP_FRAMECTRL_B1 ─┐    │
    next_bank == SDW_BANK0 ──▶ addr = SDW_SCP_FRAMECTRL_B0 ─┤    │
                                                            ▼    ▼
                                            ┌────────────────────────┐
                                            │ sdw_fill_msg(addr,wbuf)│
                                            │   dev_num = BROADCAST  │
                                            │   ssp_sync = true      │
                                            └────────────┬───────────┘
                                                         ▼
                              sdw_transfer  or  sdw_transfer_defer
```

### sdw_ml_sync_bank_switch waits for the hardware-synchronized flip

When several SoundWire segments must flip on the same frame, the frame-control write is deferred and the actual flip is triggered by the manager [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op. [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817) then waits on the [`defer_msg.complete`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826) completion for up to [`bank_switch_timeout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), and only after the wait succeeds does it toggle [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and free the deferred message:

```c
/* drivers/soundwire/stream.c:817 */
static int sdw_ml_sync_bank_switch(struct sdw_bus *bus, bool multi_link)
{
	unsigned long time_left;

	if (!multi_link)
		return 0;

	/* Wait for completion of transfer */
	time_left = wait_for_completion_timeout(&bus->defer_msg.complete,
						bus->bank_switch_timeout);

	if (!time_left) {
		dev_err(bus->dev, "Controller Timed out on bank switch\n");
		return -ETIMEDOUT;
	}

	bus->params.curr_bank = !bus->params.curr_bank;
	bus->params.next_bank = !bus->params.next_bank;

	if (bus->defer_msg.msg) {
		kfree(bus->defer_msg.msg->buf);
		kfree(bus->defer_msg.msg);
		bus->defer_msg.msg = NULL;
	}

	return 0;
}
```

The completion the wait blocks on is the [`complete`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826) member of [`struct sdw_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826), the deferred-message holder embedded in the bus as [`defer_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014):

```c
/* include/linux/soundwire/sdw.h:826 */
/**
 * struct sdw_defer - SDW deferred message
 * @complete: message completion
 * @msg: SDW message
 * @length: message length
 */
struct sdw_defer {
	struct sdw_msg *msg;
	int length;
	struct completion complete;
};
```

[`do_transfer_defer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L253) initializes that completion with [`init_completion()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/completion.h#L84) before invoking the manager [`xfer_msg_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op, so the controller interrupt that finishes the deferred frame-control write completes it and releases [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817). [`sdw_transfer_defer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L347) first checks that the manager supplies an [`xfer_msg_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) callback, then calls [`do_transfer_defer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L253):

```c
/* drivers/soundwire/bus.c:347 */
int sdw_transfer_defer(struct sdw_bus *bus, struct sdw_msg *msg)
{
	int ret;

	if (!bus->ops->xfer_msg_defer)
		return -ENOTSUPP;

	ret = do_transfer_defer(bus, msg);
	if (ret != 0 && ret != -ENODATA)
		dev_err(bus->dev, "Defer trf on Slave %d failed:%d\n",
			msg->dev_num, ret);

	return ret;
}
```

```c
/* drivers/soundwire/bus.c:253 */
static inline int do_transfer_defer(struct sdw_bus *bus,
				    struct sdw_msg *msg)
{
	struct sdw_defer *defer = &bus->defer_msg;
	int retry = bus->prop.err_threshold;
	enum sdw_command_response resp;
	int ret = 0, i;

	defer->msg = msg;
	defer->length = msg->len;
	init_completion(&defer->complete);

	for (i = 0; i <= retry; i++) {
		resp = bus->ops->xfer_msg_defer(bus);
		ret = find_response_code(resp);
		/* if cmd is ok or ignored return */
		if (ret == 0 || ret == -ENODATA)
			return ret;
	}

	return ret;
}
```

On a Cadence-based Intel controller the [`xfer_msg_defer`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) op is [`cdns_xfer_msg_defer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L797), which reads the single deferred [`struct sdw_msg`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L63) back out of [`bus->defer_msg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and submits it to the controller as an asynchronous command, returning an [`enum sdw_command_response`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L129) that [`do_transfer_defer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L253) folds into a return code:

```c
/* drivers/soundwire/cadence_master.c:797 */
enum sdw_command_response
cdns_xfer_msg_defer(struct sdw_bus *bus)
{
	struct sdw_cdns *cdns = bus_to_cdns(bus);
	struct sdw_defer *defer = &bus->defer_msg;
	struct sdw_msg *msg = defer->msg;
	int cmd = 0, ret;

	/* for defer only 1 message is supported */
	if (msg->len > 1)
		return -ENOTSUPP;

	ret = cdns_prep_msg(cdns, msg, &cmd);
	if (ret)
		return SDW_CMD_FAIL_OTHER;

	return _cdns_xfer_msg(cdns, msg, cmd, 0, msg->len, true);
}
```

That submit hands the command to the controller while the bus thread blocks on the completion, the controller firing SYNCGO at the frame boundary and signaling back so the wait returns and both bank fields toggle:

```
    Deferred frame-control completion handshake (time goes down)
    ──────────────────────────────────────────────────────────────

      bus thread                       controller / IRQ
      ──────────                       ────────────────
          │
   do_transfer_defer:                           │
     init_completion(&defer->complete)          │
     xfer_msg_defer ───── submit cmd ──────────▶│
          │                                     │
   sdw_ml_sync_bank_switch:                     │  SYNCGO fires,
     wait_for_completion_timeout                │  frame boundary
          │  (blocked, ≤ bank_switch_timeout)   │
          │◀────────── complete(&defer->complete)
          ▼
     curr_bank = !curr_bank
     next_bank = !next_bank
     kfree(defer_msg.msg)
```

### The channel mask is written into the inactive bank first

Before any frame-control write, the new per-port channel layout is programmed into the bank that is not yet live. [`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317) selects the channel-enable register of the alternate bank from [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), choosing [`SDW_DPN_CHANNELEN_B1(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268) when the next bank is bank 1 and [`SDW_DPN_CHANNELEN_B0(n)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) otherwise, and writes the port's [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126). According to the comment on the function, it "only sets the enable/disable bits in the relevant bank, the actual enable/disable is done with a bank switch":

```c
/* drivers/soundwire/stream.c:317 */
static int sdw_enable_disable_slave_ports(struct sdw_bus *bus,
					  struct sdw_slave_runtime *s_rt,
					  struct sdw_port_runtime *p_rt,
					  bool en)
{
	struct sdw_transport_params *t_params = &p_rt->transport_params;
	u32 addr;
	int ret;

	if (bus->params.next_bank)
		addr = SDW_DPN_CHANNELEN_B1(p_rt->num);
	else
		addr = SDW_DPN_CHANNELEN_B0(p_rt->num);

	/*
	 * Since bus doesn't support sharing a port across two streams,
	 * it is safe to reset this register
	 */
	if (en)
		ret = sdw_write_no_pm(s_rt->slave, addr, p_rt->ch_mask);
	else
		ret = sdw_write_no_pm(s_rt->slave, addr, 0x0);
	...
}
```

[`sdw_enable_disable_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389) drives this for every Slave and Master port of a manager runtime, and the transport parameters for those ports are programmed into the same alternate bank by [`sdw_program_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661). Because the channel mask and the transport parameters land in the inactive bank, the live bank keeps driving the current channel layout untouched until the frame-control write flips the active bank.

```c
/* drivers/soundwire/stream.c:389 */
static int sdw_enable_disable_ports(struct sdw_master_runtime *m_rt, bool en)
{
	struct sdw_port_runtime *s_port, *m_port;
	struct sdw_slave_runtime *s_rt;
	int ret = 0;

	/* Enable/Disable Slave port(s) */
	list_for_each_entry(s_rt, &m_rt->slave_rt_list, m_rt_node) {
		list_for_each_entry(s_port, &s_rt->port_list, port_node) {
			ret = sdw_enable_disable_slave_ports(m_rt->bus, s_rt,
							     s_port, en);
			if (ret < 0)
				return ret;
		}
	}

	/* Enable/Disable Master port(s) */
	list_for_each_entry(m_port, &m_rt->port_list, port_node) {
		ret = sdw_enable_disable_master_ports(m_rt, m_port, en);
		if (ret < 0)
			return ret;
	}

	return 0;
}
```

That per-port walk is phase one, writing each channel mask into the idle bank while the live bank keeps the old layout, and phase two flips the active bank with the frame-control write so the masks go live at once:

```
    Channel mask lands in the inactive bank, then the flip activates it
    ─────────────────────────────────────────────────────────────────────
    (phase 1 only sets bits in the idle bank; phase 2 makes them live)

    Phase 1  sdw_enable_disable_ports(m_rt, en)
    ───────  per Slave port ─▶ sdw_enable_disable_slave_ports:
                                 next_bank set ─▶ SDW_DPN_CHANNELEN_B1(n)
                                 next_bank 0   ─▶ SDW_DPN_CHANNELEN_B0(n)
                                 write ch_mask (en) or 0  ─┐
             per Master port ─▶ sdw_enable_disable_master_ports
                                                           │
                          live bank keeps driving the old  │ writes touch
                          channel layout, untouched        │ the IDLE bank
                                                           ▼
    Phase 2  do_bank_switch ─▶ SCP_FrameCtrl write at SSP flips the
    ───────  active bank, so the new channel mask becomes live at once
```

### Enable calls into the bank switch

The four stream transition ops are the callers of the bank mechanism. [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) is the public entry that moves a stream into [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926). It takes the bus lock, checks the current state, and delegates to [`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576):

```c
/* drivers/soundwire/stream.c:1619 */
int sdw_enable_stream(struct sdw_stream_runtime *stream)
{
	int ret;

	if (!stream) {
		pr_err("SoundWire: Handle not found for stream\n");
		return -EINVAL;
	}

	sdw_acquire_bus_lock(stream);

	if (stream->state == SDW_STREAM_ENABLED) {
		ret = 0;
		goto state_err;
	}
	...
	ret = _sdw_enable_stream(stream);

state_err:
	sdw_release_bus_lock(stream);
	return ret;
}
```

[`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576) programs the parameters and enables the ports on the alternate bank for every manager, then calls [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) to bring the newly enabled channels into service at the next frame boundary, and only then records the [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) state:

```c
/* drivers/soundwire/stream.c:1576 */
static int _sdw_enable_stream(struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt;
	struct sdw_bus *bus;
	int ret;

	/* Enable Master(s) and Slave(s) port(s) associated with stream */
	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;

		/* Program params */
		ret = sdw_program_params(bus, false);
		if (ret < 0) {
			dev_err(bus->dev, "%s: Program params failed: %d\n", __func__, ret);
			return ret;
		}

		/* Enable port(s) */
		ret = sdw_enable_disable_ports(m_rt, true);
		if (ret < 0) {
			dev_err(bus->dev,
				"Enable port(s) failed ret: %d\n", ret);
			return ret;
		}
	}

	ret = do_bank_switch(stream);
	if (ret < 0) {
		pr_err("%s: do_bank_switch failed: %d\n", __func__, ret);
		return ret;
	}

	stream->state = SDW_STREAM_ENABLED;
	return 0;
}
```

### Prepare, disable, and deprepare each call into the bank switch

The same shape repeats for the other three transition points. [`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453) recomputes the bus bandwidth, programs the new frame shape into the alternate bank with [`sdw_program_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661), then calls [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) before preparing the ports on the new clock:

```c
/* drivers/soundwire/stream.c:1499 */
	ret = do_bank_switch(stream);
	if (ret < 0) {
		pr_err("%s: do_bank_switch failed: %d\n", __func__, ret);
		goto restore_params;
	}

	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;

		/* Prepare port(s) on the new clock configuration */
		ret = sdw_prep_deprep_ports(m_rt, true);
		...
	}

	stream->state = SDW_STREAM_PREPARED;
```

[`_sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651) disables the ports on the alternate bank, sets the stream to [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), reprograms the parameters, calls [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845), and then disables the ports on the now-previous bank as well so neither bank is left enabling the channels:

```c
/* drivers/soundwire/stream.c:1679 */
	ret = do_bank_switch(stream);
	if (ret < 0) {
		pr_err("%s: do_bank_switch failed: %d\n", __func__, ret);
		return ret;
	}

	/* make sure alternate bank (previous current) is also disabled */
	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		struct sdw_bus *bus = m_rt->bus;

		/* Disable port(s) */
		ret = sdw_enable_disable_ports(m_rt, false);
		if (ret < 0) {
			dev_err(bus->dev, "Disable port(s) failed: %d\n", ret);
			return ret;
		}
	}

	return 0;
```

[`_sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1738) marks the stream [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), deprepares the ports, releases the bandwidth, reprograms the parameters into the alternate bank, and returns the result of [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) directly:

```c
/* drivers/soundwire/stream.c:1800 */
		/* Program params */
		ret = sdw_program_params(bus, false);
		if (ret < 0) {
			dev_err(bus->dev, "%s: Program params failed: %d\n", __func__, ret);
			stream->state = state;
			return ret;
		}
	}

	return do_bank_switch(stream);
}
```

This deprepare op is the last of the four, each moving the stream to its own state (prepared, enabled, disabled, deprepared) and all converging on the one switch that flips the freshly programmed bank:

```
    Four stream transitions, each ending in do_bank_switch
    ────────────────────────────────────────────────────────
    (every op programs the inactive bank, then flips it)

       _sdw_prepare_stream   ─▶ SDW_STREAM_PREPARED   ─┐
       _sdw_enable_stream    ─▶ SDW_STREAM_ENABLED    ─┤
       _sdw_disable_stream   ─▶ SDW_STREAM_DISABLED   ─┼─▶ do_bank_switch()
       _sdw_deprepare_stream ─▶ SDW_STREAM_DEPREPARED ─┘
```

### Intel x86 ACPI manager hooks arm and fire the multi-link sync

On an Intel LNL or MTL platform enumerated through ACPI, the SoundWire host controller registers its manager [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) as [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281), so the [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) and [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) callbacks point at [`generic_pre_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L105) and [`generic_post_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L113), which forward to the per-generation [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L231) and thus to [`intel_pre_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L243) and [`intel_post_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L257):

```c
/* drivers/soundwire/intel_auxdevice.c:105 */
static int generic_pre_bank_switch(struct sdw_bus *bus)
{
	struct sdw_cdns *cdns = bus_to_cdns(bus);
	struct sdw_intel *sdw = cdns_to_intel(cdns);

	return sdw->link_res->hw_ops->pre_bank_switch(sdw);
}

static int generic_post_bank_switch(struct sdw_bus *bus)
{
	struct sdw_cdns *cdns = bus_to_cdns(bus);
	struct sdw_intel *sdw = cdns_to_intel(cdns);

	return sdw->link_res->hw_ops->post_bank_switch(sdw);
}
```

[`intel_pre_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L243) runs only when the bus reports [`multi_link`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and arms the synchronization with [`sdw_intel_sync_arm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L225), which marks this link as participating in the next synchronized flip:

```c
/* drivers/soundwire/intel_bus_common.c:243 */
int intel_pre_bank_switch(struct sdw_intel *sdw)
{
	struct sdw_cdns *cdns = &sdw->cdns;
	struct sdw_bus *bus = &cdns->bus;

	/* Write to register only for multi-link */
	if (!bus->multi_link)
		return 0;

	sdw_intel_sync_arm(sdw);

	return 0;
}
```

[`intel_post_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L257) is the callback that triggers the flip across the armed links. It takes the shared SHIM lock, and according to its comment it sets the SYNCGO bit "only if CMDSYNC bit is set for any Master", so [`sdw_intel_sync_check_cmdsync_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L245) gates the call to [`sdw_intel_sync_go_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L231). The first manager in the list whose CMDSYNC is set issues the SYNCGO that releases all the deferred frame-control writes on the same frame, and the later managers find CMDSYNC clear and do nothing:

```c
/* drivers/soundwire/intel_bus_common.c:257 */
int intel_post_bank_switch(struct sdw_intel *sdw)
{
	struct sdw_cdns *cdns = &sdw->cdns;
	struct sdw_bus *bus = &cdns->bus;
	int ret = 0;

	/* Write to register only for multi-link */
	if (!bus->multi_link)
		return 0;

	mutex_lock(sdw->link_res->shim_lock);

	/*
	 * post_bank_switch() ops is called from the bus in loop for
	 * all the Masters in the steam with the expectation that
	 * we trigger the bankswitch for the only first Master in the list
	 * and do nothing for the other Masters
	 *
	 * So, set the SYNCGO bit only if CMDSYNC bit is set for any Master.
	 */
	if (sdw_intel_sync_check_cmdsync_unlocked(sdw))
		ret = sdw_intel_sync_go_unlocked(sdw);

	mutex_unlock(sdw->link_res->shim_lock);

	if (ret < 0)
		dev_err(sdw->cdns.dev, "Post bank switch failed: %d\n", ret);

	return ret;
}
```

[`sdw_intel_sync_go_unlocked()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L231) dispatches to the per-generation hardware op that writes SYNCGO into the controller's SHIM, the register action that makes all the armed links adopt their alternate banks on one frame:

```c
/* drivers/soundwire/intel.h:231 */
static inline int sdw_intel_sync_go_unlocked(struct sdw_intel *sdw)
{
	if (SDW_INTEL_CHECK_OPS(sdw, sync_go_unlocked))
		return SDW_INTEL_OPS(sdw, sync_go_unlocked)(sdw);
	return -ENOTSUPP;
}
```

The deferred write submitted by [`sdw_transfer_defer()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L347) thus completes only after [`intel_post_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L257) fires SYNCGO, the controller interrupt completes [`defer_msg.complete`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L826), and [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817) wakes up to toggle the bank state, so the new channel layout becomes live across every link at one frame boundary.

```
    Multi-link synchronized flip: arm every link, fire SYNCGO once
    ───────────────────────────────────────────────────────────────

                  Link 0      Link 1      Link 2
              ┌────────┐  ┌────────┐  ┌────────┐
    pre_bank_ │ CMDSYNC│  │ CMDSYNC│  │ CMDSYNC│   sync_arm() sets
     switch   │  armed │  │  armed │  │  armed │   each link's bit
              └────┬───┘  └────┬───┘  └────┬───┘
                   └───────────┼───────────┘
    post_bank_switch           ▼
     (first armed       ┌────────────┐
      link only)        │   SYNCGO   │   one SHIM write
                        └──────┬─────┘
                               ▼
          all armed links adopt the alternate bank on one frame;
          the controller IRQ completes defer_msg.complete, and
          sdw_ml_sync_bank_switch() toggles curr_bank / next_bank
```
