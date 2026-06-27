# SoundWire stream transitions

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A configured SoundWire stream reaches the wire through four exported operations, [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533), [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619), [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707), and [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812), each of which takes the bus lock with [`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419), checks that the [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) of the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) is a legal predecessor, and hands off to an inner worker ([`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453), [`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576), [`_sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651), [`_sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1738)) that walks the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) and drives the bus with [`sdw_program_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661), the channel-prepare helper [`sdw_prep_deprep_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581), the channel-enable helper [`sdw_enable_disable_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389), and a final [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) that flips the alternate register bank live. On an x86-64 ACPI Intel SoundWire card the [`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031), [`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050), and [`asoc_sdw_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133) machine ops in [`sound/soc/sdw_utils/soc_sdw_utils.c`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c) call the four transitions for a stream whose peripheral is the Realtek rt722-sdca codec.

```
    The four transitions and the bus operations each performs
    ─────────────────────────────────────────────────────────

    state in       entry op (bus action over the wire)            state out
    ──────────────────────────────────────────────────────────────────────
                   sdw_prepare_stream()
    CONFIGURED ──▶ ┌──────────────────────────────────────────┐──▶ PREPARED
    DEPREPARED     │ compute bandwidth + compute_params()     │
    DISABLED       │ sdw_program_params(bus, prepare=true)    │
                   │   DPn transport regs on alternate bank   │
                   │ do_bank_switch()  (flip to new clock)    │
                   │ sdw_prep_deprep_ports(prep=true)         │
                   │   DPn_PrepareCtrl, wait PrepareStatus    │
                   └──────────────────────────────────────────┘

                   sdw_enable_stream()
    PREPARED ────▶ ┌──────────────────────────────────────────┐──▶ ENABLED
    DISABLED       │ sdw_program_params(bus, prepare=false)   │     (audio
                   │ sdw_enable_disable_ports(en=true)        │      flows)
                   │   DPn_ChannelEn = ch_mask (alt bank)     │
                   │ do_bank_switch()  (channels go live)     │
                   └──────────────────────────────────────────┘

                   sdw_disable_stream()
    ENABLED ─────▶ ┌──────────────────────────────────────────┐──▶ DISABLED
                   │ sdw_enable_disable_ports(en=false)       │
                   │   DPn_ChannelEn = 0 (alt bank)           │
                   │ sdw_program_params(bus, prepare=false)   │
                   │ do_bank_switch()  (channels stop)        │
                   │ sdw_enable_disable_ports(en=false) again │
                   └──────────────────────────────────────────┘

                   sdw_deprepare_stream()
    PREPARED ────▶ ┌──────────────────────────────────────────┐──▶ DEPREPARED
    DISABLED       │ sdw_prep_deprep_ports(prep=false)        │
                   │ release bandwidth + compute_params()     │
                   │ sdw_program_params(bus, prepare=false)   │
                   │ do_bank_switch()                         │
                   └──────────────────────────────────────────┘

    every op holds bus_lock for the whole transition; do_bank_switch()
    writes SCP_FrameCtrl on the broadcast device so the new bank takes
    effect at a frame boundary, with no audible artifact.
```

## SUMMARY

The four transitions share one outer shape and differ only in the bus work their inner worker performs. [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) guards the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) against [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932), and [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), and when the predecessor is [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) it passes `update_params = false` so [`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453) re-applies the cached parameters without recomputing bandwidth, the path taken on an underflow or resume. The worker walks every [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) on the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961), optionally raises [`bus->params.bandwidth`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and runs [`bus->compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), programs transport registers on the inactive bank with [`sdw_program_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661), flips the bank with [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845), and only then sets the data-port channel-prepare bits with [`sdw_prep_deprep_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581) before setting [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929).

[`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) guards [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) and [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), and [`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576) reprograms the parameters, sets the channel-enable bit for every port with [`sdw_enable_disable_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389), and switches banks so the channels go live together at a frame boundary, leaving [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930). [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) guards [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930), and [`_sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651) clears the channel-enable bit, marks [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) before the reprogram so the stream is excluded from bit allocation, reprograms, switches banks, then clears the enable bit a second time on what is now the alternate bank. [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) guards [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) and [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), and [`_sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1738) sets [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) first, clears the channel-prepare bits with [`sdw_prep_deprep_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581), subtracts the stream bandwidth, recomputes, reprograms, and switches banks one last time.

Underneath, [`sdw_program_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661) writes the bus-clock scale register and walks [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) calling [`sdw_program_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L280) per runtime, the port helpers split into a slave side ([`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317), [`sdw_prep_deprep_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L441)) that writes peripheral registers directly and a manager side ([`sdw_enable_disable_master_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L348)) that goes through the [`struct sdw_master_port_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806), and [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) runs [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861), the broadcast frame-control write in [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742), and [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861).

## SPECIFICATIONS

The transition mechanics are a Linux kernel layer over the MIPI Alliance SoundWire bus, and this page describes the kernel implementation. The register writes the transitions issue follow the SoundWire data-port model. The channel-prepare and channel-enable state of a data port is held in banked registers, one copy per bank, so the manager programs the inactive bank while the active bank keeps the link running, then makes the new configuration current with a single broadcast write to the frame-control register at a frame boundary. The SoundWire specification is membership-gated and is not linked here. The per-register addresses the kernel uses are given as macros in [`include/linux/soundwire/sdw_registers.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h), where the bank-0 and bank-1 copies of each register sit [`SDW_BANK1_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L22) apart for the SCP registers and one half of [`SDW_DPN_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L21) apart for the per-port channel-enable register. The SDCA clock-scaling registers the rt722-sdca codec honors are defined by the MIPI SoundWire Device Class for Audio (SDCA) Specification, also membership-gated and not linked.

## LINUX KERNEL

### The four transition entry points (stream.c)

- [`'\<sdw_prepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533): take [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), guard [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) / [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) / [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), choose `update_params`, and call [`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453)
- [`'\<sdw_enable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619): guard [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) / [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) and call [`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576)
- [`'\<sdw_disable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707): guard [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) and call [`_sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651)
- [`'\<sdw_deprepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812): guard [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) / [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) and call [`_sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1738)

### The inner workers (stream.c)

- [`'\<_sdw_prepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453): per manager runtime, raise [`bus->params.bandwidth`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), run [`bus->compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), call [`sdw_program_params(bus, true)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661), then [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) and [`sdw_prep_deprep_ports(m_rt, true)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581); on error restores the saved [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593)
- [`'\<_sdw_enable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576): per manager runtime, [`sdw_program_params(bus, false)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661) and [`sdw_enable_disable_ports(m_rt, true)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389), then [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845)
- [`'\<_sdw_disable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651): [`sdw_enable_disable_ports(m_rt, false)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389), set [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), reprogram, [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845), then disable ports again on the alternate bank
- [`'\<_sdw_deprepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1738): set [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932), [`sdw_prep_deprep_ports(m_rt, false)`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581), subtract bandwidth, [`bus->compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), reprogram, [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845)

### Parameter programming (stream.c, sdw_registers.h)

- [`'\<sdw_program_params\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661): write [`SDW_SCP_BUSCLOCK_SCALE_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L222) / [`SDW_SCP_BUSCLOCK_SCALE_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L223) per SDCA peripheral, then per runtime on [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) call [`sdw_program_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L280) and [`sdw_notify_config()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L615)
- [`'\<sdw_program_port_params\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L280): per port, [`sdw_program_slave_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L129) for the peripheral and [`sdw_program_master_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L252) for the manager
- [`'\<sdw_program_slave_port_params\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L129): write [`SDW_DPN_PORTCTRL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L243), [`SDW_DPN_BLOCKCTRL1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L244), and the banked sample/offset registers from a [`struct sdw_transport_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L769)
- [`'\<sdw_program_master_port_params\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L252): call [`dpn_set_port_transport_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) and [`dpn_set_port_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) of the [`struct sdw_master_port_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806)
- [`'\<sdw_notify_config\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L615): call the [`set_bus_conf`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) manager op and the peripheral driver's [`bus_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) op with the new [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593)

### Port prepare and enable helpers (stream.c, sdw_registers.h)

- [`'\<sdw_prep_deprep_ports\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581): dispatch port channel-prepare to [`sdw_prep_deprep_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L441) and [`sdw_prep_deprep_master_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L546)
- [`'\<sdw_prep_deprep_slave_ports\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L441): write [`SDW_DPN_PREPARECTRL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L246), wait on [`port_ready[]`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L677), and poll [`SDW_DPN_PREPARESTATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L245) for peripherals without the simple channel-prepare state machine
- [`'\<sdw_enable_disable_ports\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389): dispatch channel-enable to [`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317) and [`sdw_enable_disable_master_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L348)
- [`'\<sdw_enable_disable_slave_ports\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317): write the peripheral [`SDW_DPN_CHANNELEN_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) / [`SDW_DPN_CHANNELEN_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268) register on the inactive bank to [`p_rt->ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) or 0
- [`'\<sdw_enable_disable_master_ports\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L348): fill a [`struct sdw_enable_ch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L789) and call the [`dpn_port_enable_ch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) manager op

### Bank switch (stream.c, sdw_registers.h)

- [`'\<do_bank_switch\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845): per manager runtime run [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) and [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742), then [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) and [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817); internals are documented separately
- [`'\<sdw_bank_switch\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742): broadcast-write [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) / [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218) with [`ssp_sync`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L71) set, and swap [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) / [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593)
- [`'\<sdw_ml_sync_bank_switch\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817): for a hardware-synced multi-link stream, wait on [`bus->defer_msg.complete`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1024) within [`DEFAULT_BANK_SWITCH_TIMEOUT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L7), then swap the banks

### Serialization and runtime types (stream.c, bus.h, sdw.h)

- [`'\<sdw_acquire_bus_lock\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419): take [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) for every manager runtime in [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961)
- [`'\<sdw_release_bus_lock\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1441): drop [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) in reverse order
- [`'\<struct sdw_master_runtime\>':'drivers/soundwire/bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166): the per-manager-per-stream runtime the workers walk, with [`bus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), [`ch_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), and the [`stream_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) link onto [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961)
- [`'\<struct sdw_port_runtime\>':'drivers/soundwire/bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126): one data port, carrying [`num`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126), [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126), [`transport_params`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126), and [`lane`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126)
- [`'\<struct sdw_bus_params\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593): the live bus configuration, with [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), [`bandwidth`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593), and the active row/column
- [`'\<struct sdw_enable_ch\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L789): the manager channel-enable descriptor, with [`port_num`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L789), [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L789), [`enable`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L789)
- [`'\<struct sdw_prepare_ch\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L555): the manager channel-prepare descriptor, with [`num`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L555), [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L555), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L555), [`bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L555)
- [`'\<struct sdw_master_port_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806): the manager data-port callbacks [`dpn_set_port_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806), [`dpn_set_port_transport_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806), and [`dpn_port_enable_ch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806)

### x86-64 machine callers and the rt722-sdca codec (soc_sdw_utils.c, sof_sdw.c, rt722-sdca.c)

- [`'\<asoc_sdw_prepare\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031): the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) machine op, reads the stream off the first CPU DAI and calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533)
- [`'\<asoc_sdw_trigger\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050): the [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) machine op, calls [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) on START/RESUME/PAUSE_RELEASE and [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) on STOP/SUSPEND/PAUSE_PUSH
- [`'\<asoc_sdw_hw_free\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133): the [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) machine op, calls [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812)
- [`'\<asoc_sdw_hw_params\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1090): the [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) machine op, sets each codec [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1217) but does not itself call a transition
- [`'sdw_ops':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865): the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) that wires [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) to the three transition callers on every SoundWire DAI link
- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): the codec [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op that selects the data port and channel mask and joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), the peripheral whose ports the transitions later prepare and enable

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the prepare/enable/disable/deprepare API contract, the per-state bus operations, and the multi-step stream state machine the transitions drive
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`msg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) ordering [`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419) and [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) follow
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): how a failed transition unwinds, including the [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) restore in [`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453)
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the manager and peripheral roles and the banked data-port register model the bank switch relies on

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

The four transition operations are plain exported functions reached directly, and a machine driver calls them in a fixed order over a stream's life. Each maps from one [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) to the next and performs one characteristic bus action, with [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845) ending each transition so the change takes effect at a frame boundary. The object the state field belongs to and the full enum are described on the stream-lifecycle page; this table names only the entry and exit states.

| Transition | Entry state(s) | Bus action over the wire | Exit state |
|------------|----------------|--------------------------|------------|
| [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) | [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926), [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932), [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) | program transport params on the inactive bank, bank switch, set the channel-prepare bit | [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) |
| [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) | [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929), [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) | set the channel-enable bit on the inactive bank, bank switch | [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) |
| [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) | [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) | clear the channel-enable bit, reprogram, bank switch, clear again on the alternate bank | [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) |
| [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) | [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929), [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) | clear the channel-prepare bit, release bandwidth, reprogram, bank switch | [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) |

### sdw_prepare_stream

[`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) is the machine driver's [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) step. It moves a stream out of [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) on a fresh start, or re-enters from [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) and [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) on a restart, and ends in [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929). Re-entry from [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) signals an underflow or resume, so the bandwidth is re-applied rather than recomputed.

### sdw_enable_stream

[`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) is the START half of the machine [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623). It moves [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) to [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930), the state in which the link carries audio. The channel-enable bits are written on the inactive bank and become active only at the bank switch, so the channels of every port on the stream start together.

### sdw_disable_stream

[`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) is the STOP half of the machine [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623). It moves [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) to [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931). [`_sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651) sets the state to [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) before the reprogram so the stream is dropped from the next bandwidth calculation, and disables the ports on both banks so neither the current nor the alternate bank keeps the channels live.

### sdw_deprepare_stream

[`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) is the machine [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) step. It accepts [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) and [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) and ends in [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932), the state from which the stream may be released or prepared again. It clears the channel-prepare bits and gives back the bandwidth the stream held, so a later stream can claim the freed rows and columns.

## DETAILS

### The outer entry point: lock, guard, dispatch

The four entry points are one template. [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) rejects a NULL handle, takes the bus lock with [`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419), treats an already-[`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) stream as a no-op, checks the predecessor [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961), decides whether to recompute the bandwidth, calls [`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453), and drops the lock at the shared `state_err` label:

```c
/* drivers/soundwire/stream.c:1533 */
int sdw_prepare_stream(struct sdw_stream_runtime *stream)
{
	bool update_params = true;
	int ret;

	if (!stream) {
		pr_err("SoundWire: Handle not found for stream\n");
		return -EINVAL;
	}

	sdw_acquire_bus_lock(stream);

	if (stream->state == SDW_STREAM_PREPARED) {
		ret = 0;
		goto state_err;
	}

	if (stream->state != SDW_STREAM_CONFIGURED &&
	    stream->state != SDW_STREAM_DEPREPARED &&
	    stream->state != SDW_STREAM_DISABLED) {
		pr_err("%s: %s: inconsistent state state %d\n",
		       __func__, stream->name, stream->state);
		ret = -EINVAL;
		goto state_err;
	}

	/*
	 * when the stream is DISABLED, this means sdw_prepare_stream()
	 * is called as a result of an underflow or a resume operation.
	 * In this case, the bus parameters shall not be recomputed, but
	 * still need to be re-applied
	 */
	if (stream->state == SDW_STREAM_DISABLED)
		update_params = false;

	ret = _sdw_prepare_stream(stream, update_params);

state_err:
	sdw_release_bus_lock(stream);
	return ret;
}
```

According to the comment, a call from [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) "is called as a result of an underflow or a resume operation", and in that case "the bus parameters shall not be recomputed, but still need to be re-applied", which is why `update_params` is cleared for that predecessor alone. The other three entry points drop the `update_params` argument but keep the rest of the shape. [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) guards two predecessors and calls [`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576):

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

	if (stream->state != SDW_STREAM_PREPARED &&
	    stream->state != SDW_STREAM_DISABLED) {
		pr_err("%s: %s: inconsistent state state %d\n",
		       __func__, stream->name, stream->state);
		ret = -EINVAL;
		goto state_err;
	}

	ret = _sdw_enable_stream(stream);

state_err:
	sdw_release_bus_lock(stream);
	return ret;
}
```

[`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) accepts only [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930), and [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) accepts [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931); each then calls its inner worker under the same lock and label.

### _sdw_prepare_stream: bandwidth, params, bank switch, then prepare

[`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453) does the bus work in three passes over the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961). The first pass, per [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), copies the live [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) so it can be restored on failure, rejects an asynchronous clock ratio, and when `update_params` is set adds this stream's rate times channel count times sample width to [`bus->params.bandwidth`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and runs the platform [`compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) allocator before programming the transport registers:

```c
/* drivers/soundwire/stream.c:1453 */
static int _sdw_prepare_stream(struct sdw_stream_runtime *stream,
			       bool update_params)
{
	struct sdw_master_runtime *m_rt;
	struct sdw_bus *bus;
	struct sdw_master_prop *prop;
	struct sdw_bus_params params;
	int ret;

	/* Prepare  Master(s) and Slave(s) port(s) associated with stream */
	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;
		prop = &bus->prop;
		memcpy(&params, &bus->params, sizeof(params));

		/* TODO: Support Asynchronous mode */
		if ((prop->max_clk_freq % stream->params.rate) != 0) {
			dev_err(bus->dev, "Async mode not supported\n");
			return -EINVAL;
		}

		if (update_params) {
			/* Increment cumulative bus bandwidth */
			/* TODO: Update this during Device-Device support */
			bus->params.bandwidth += m_rt->stream->params.rate *
				m_rt->ch_count * m_rt->stream->params.bps;

			/* Compute params */
			if (bus->compute_params) {
				ret = bus->compute_params(bus, stream);
				if (ret < 0) {
					dev_err(bus->dev, "Compute params failed: %d\n",
						ret);
					goto restore_params;
				}
			}
		}

		/* Program params */
		ret = sdw_program_params(bus, true);
		if (ret < 0) {
			dev_err(bus->dev, "Program params failed: %d\n", ret);
			goto restore_params;
		}
	}
```

After every manager runtime has its parameters on the inactive bank, the worker switches banks once for the whole stream, then runs a second pass that calls [`sdw_prep_deprep_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581) so the channel-prepare bit is set on the clock configuration that is now current, and finally sets [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929):

```c
/* drivers/soundwire/stream.c:1453 */
	ret = do_bank_switch(stream);
	if (ret < 0) {
		pr_err("%s: do_bank_switch failed: %d\n", __func__, ret);
		goto restore_params;
	}

	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;

		/* Prepare port(s) on the new clock configuration */
		ret = sdw_prep_deprep_ports(m_rt, true);
		if (ret < 0) {
			dev_err(bus->dev, "Prepare port(s) failed ret = %d\n",
				ret);
			goto restore_params;
		}
	}

	stream->state = SDW_STREAM_PREPARED;

	return ret;

restore_params:
	memcpy(&bus->params, &params, sizeof(params));
	return ret;
}
```

The `restore_params` tail copies the saved [`struct sdw_bus_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) back over [`bus->params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), so a failure anywhere leaves the bus describing the configuration that was actually running.

```
    _sdw_prepare_stream(): three passes over master_list
    ─────────────────────────────────────────────────────────────

    Pass 1 (per m_rt)         flip            Pass 2 (per m_rt)
    ┌─────────────────────┐                   ┌─────────────────────┐
    │ memcpy save params  │                   │ sdw_prep_deprep_    │
    │ if update_params:   │   ┌───────────┐   │   ports(prep=true)  │
    │   bandwidth +=      │──▶│do_bank_   │──▶│ DPn_PrepareCtrl on  │
    │   compute_params()  │   │  switch() │   │  the now-live clock │
    │ sdw_program_params( │   └───────────┘   └──────────┬──────────┘
    │   bus, prepare=true)│                              │
    │  DPn regs, alt bank │                              ▼
    └─────────────────────┘                   state = SDW_STREAM_PREPARED

    on any error ▶ restore_params: memcpy saved sdw_bus_params back
```

### _sdw_enable_stream: reprogram, set channel-enable, bank switch

[`_sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1576) is the shortest worker. Per manager runtime it reprograms the parameters with `prepare = false`, then sets the data-port channel-enable bit with [`sdw_enable_disable_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389), and after the loop switches banks so every port's channels become active at the same frame:

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

### _sdw_disable_stream: clear channel-enable on both banks

[`_sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1651) clears the channel-enable bit on the inactive bank in its first loop, then sets the state to [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) before reprogramming so the disabled stream is excluded from the bit allocation the reprogram performs:

```c
/* drivers/soundwire/stream.c:1651 */
static int _sdw_disable_stream(struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt;
	int ret;

	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		struct sdw_bus *bus = m_rt->bus;

		/* Disable port(s) */
		ret = sdw_enable_disable_ports(m_rt, false);
		if (ret < 0) {
			dev_err(bus->dev, "Disable port(s) failed: %d\n", ret);
			return ret;
		}
	}
	stream->state = SDW_STREAM_DISABLED;

	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		struct sdw_bus *bus = m_rt->bus;

		/* Program params */
		ret = sdw_program_params(bus, false);
		if (ret < 0) {
			dev_err(bus->dev, "%s: Program params failed: %d\n", __func__, ret);
			return ret;
		}
	}
```

After the bank switch the worker runs a third loop that disables the ports again. According to the comment, this is to "make sure alternate bank (previous current) is also disabled", so the bank that was active when the disable started no longer carries the channels either:

```c
/* drivers/soundwire/stream.c:1651 */
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
}
```

The disable worker clears the channel-enable on both banks around one flip, the first loop on the inactive bank and the third on the bank that was live when the call began:

```
    _sdw_disable_stream(): disable on BOTH banks around one flip
    ─────────────────────────────────────────────────────────────

    Loop 1 (alt bank)        Loop 2              Loop 3 (now-alt bank)
    ┌────────────────────┐  ┌────────────────┐  ┌────────────────────┐
    │ sdw_enable_disable │  │ state =        │  │ sdw_enable_disable │
    │  _ports(en=false)  │  │  SDW_STREAM_   │  │  _ports(en=false)  │
    │ CHANNELEN = 0      │─▶│   DISABLED     │─▶│ CHANNELEN = 0 on   │
    │ on inactive bank   │  │ sdw_program_   │  │  the bank that was │
    │                    │  │  params(false) │  │  current at entry  │
    └────────────────────┘  └───────┬────────┘  └────────────────────┘
                                    │
                            do_bank_switch()  (flip happens here)

    state set to DISABLED before reprogram so the stream is dropped
    from bit allocation; both banks end with the channels cleared
```

### _sdw_deprepare_stream: clear prepare, release bandwidth, bank switch

[`_sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1738) sets [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) at the top. According to the comment, this is so the stream "is not taken into account for bit allocation" during the recompute that follows. Per manager runtime it clears the channel-prepare bit with [`sdw_prep_deprep_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581), subtracts the bandwidth this stream held (accounting for any multi-lane ports through [`bus->lane_used_bandwidth[]`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)), recomputes, reprograms, and ends with a bank switch:

```c
/* drivers/soundwire/stream.c:1738 */
static int _sdw_deprepare_stream(struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt;
	struct sdw_port_runtime *p_rt;
	unsigned int multi_lane_bandwidth;
	unsigned int bandwidth;
	struct sdw_bus *bus;
	int state = stream->state;
	int ret = 0;

	/*
	 * first mark the state as DEPREPARED so that it is not taken into account
	 * for bit allocation
	 */
	stream->state = SDW_STREAM_DEPREPARED;

	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;
		/* De-prepare port(s) */
		ret = sdw_prep_deprep_ports(m_rt, false);
		if (ret < 0) {
			dev_err(bus->dev,
				"De-prepare port(s) failed: %d\n", ret);
			stream->state = state;
			return ret;
		}

		multi_lane_bandwidth = 0;

		list_for_each_entry(p_rt, &m_rt->port_list, port_node) {
			if (!p_rt->lane)
				continue;

			bandwidth = m_rt->stream->params.rate * hweight32(p_rt->ch_mask) *
				    m_rt->stream->params.bps;
			multi_lane_bandwidth += bandwidth;
			bus->lane_used_bandwidth[p_rt->lane] -= bandwidth;
			if (!bus->lane_used_bandwidth[p_rt->lane])
				p_rt->lane = 0;
		}
		/* TODO: Update this during Device-Device support */
		bandwidth = m_rt->stream->params.rate * m_rt->ch_count * m_rt->stream->params.bps;
		bus->params.bandwidth -= bandwidth - multi_lane_bandwidth;

		/* Compute params */
		if (bus->compute_params) {
			ret = bus->compute_params(bus, stream);
			if (ret < 0) {
				dev_err(bus->dev, "Compute params failed: %d\n",
					ret);
				stream->state = state;
				return ret;
			}
		}

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

On any error before the final bank switch the worker restores the entry state saved in `state`, so a half-completed de-prepare does not leave the stream stuck in [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) without the matching register state.

### sdw_program_params writes the bus-clock scale, then per-runtime port params

[`sdw_program_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661) is the shared programming step the prepare, enable, disable, and de-prepare workers all call. It first walks [`bus->slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014); if every peripheral complies with SDCA, as checked by [`is_clock_scaling_supported_by_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L815), it writes the bus-clock scale register for the inactive bank, [`SDW_SCP_BUSCLOCK_SCALE_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L222) or [`SDW_SCP_BUSCLOCK_SCALE_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L223), with the index from [`sdw_slave_get_scale_index()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1288):

```c
/* drivers/soundwire/stream.c:661 */
static int sdw_program_params(struct sdw_bus *bus, bool prepare)
{
	struct sdw_master_runtime *m_rt;
	struct sdw_slave *slave;
	int ret = 0;
	u32 addr1;

	/* Check if all Peripherals comply with SDCA */
	list_for_each_entry(slave, &bus->slaves, node) {
		if (!slave->dev_num_sticky)
			continue;
		if (!is_clock_scaling_supported_by_slave(slave)) {
			dev_dbg(&slave->dev, "The Peripheral doesn't comply with SDCA\n");
			goto manager_runtime;
		}
	}

	if (bus->params.next_bank)
		addr1 = SDW_SCP_BUSCLOCK_SCALE_B1;
	else
		addr1 = SDW_SCP_BUSCLOCK_SCALE_B0;
	...
manager_runtime:
	list_for_each_entry(m_rt, &bus->m_rt_list, bus_node) {

		/*
		 * this loop walks through all master runtimes for a
		 * bus, but the ports can only be configured while
		 * explicitly preparing a stream or handling an
		 * already-prepared stream otherwise.
		 */
		if (!prepare &&
		    m_rt->stream->state == SDW_STREAM_CONFIGURED)
			continue;

		ret = sdw_program_port_params(m_rt);
		if (ret < 0) {
			dev_err(bus->dev,
				"Program transport params failed: %d\n", ret);
			return ret;
		}

		ret = sdw_notify_config(m_rt);
		if (ret < 0) {
			dev_err(bus->dev,
				"Notify bus config failed: %d\n", ret);
			return ret;
		}

		/* Enable port(s) on alternate bank for all active streams */
		if (m_rt->stream->state != SDW_STREAM_ENABLED)
			continue;

		ret = sdw_enable_disable_ports(m_rt, true);
		if (ret < 0) {
			dev_err(bus->dev, "Enable channel failed: %d\n", ret);
			return ret;
		}
	}

	return ret;
}
```

The `manager_runtime` loop walks every runtime on [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), covering all streams on the bus rather than only the one being transitioned. The `prepare` flag and the per-runtime [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) decide what runs. A still-[`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) runtime is skipped unless this call is the explicit prepare, [`sdw_program_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L280) and [`sdw_notify_config()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L615) run for each programmed runtime, and a runtime already in [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) has its ports re-enabled on the inactive bank so an already-running stream keeps its channels across the bank flip. [`sdw_program_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L280) splits the work between the peripheral and the manager:

```c
/* drivers/soundwire/stream.c:280 */
static int sdw_program_port_params(struct sdw_master_runtime *m_rt)
{
	struct sdw_slave_runtime *s_rt;
	struct sdw_bus *bus = m_rt->bus;
	struct sdw_port_runtime *p_rt;
	int ret = 0;

	/* Program transport & port parameters for Slave(s) */
	list_for_each_entry(s_rt, &m_rt->slave_rt_list, m_rt_node) {
		list_for_each_entry(p_rt, &s_rt->port_list, port_node) {
			ret = sdw_program_slave_port_params(bus, s_rt, p_rt);
			if (ret < 0)
				return ret;
		}
	}

	/* Program transport & port parameters for Master(s) */
	list_for_each_entry(p_rt, &m_rt->port_list, port_node) {
		ret = sdw_program_master_port_params(bus, p_rt);
		if (ret < 0)
			return ret;
	}

	return 0;
}
```

The peripheral path [`sdw_program_slave_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L129) writes the per-port registers directly with [`sdw_write_no_pm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L526), selecting the banked address for the inactive bank from [`bus->params.next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and reading the geometry out of the port's [`struct sdw_transport_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L769):

```c
/* drivers/soundwire/stream.c:129 */
	addr1 = SDW_DPN_PORTCTRL(t_params->port_num);
	addr2 = SDW_DPN_BLOCKCTRL1(t_params->port_num);

	if (bus->params.next_bank) {
		addr3 = SDW_DPN_SAMPLECTRL1_B1(t_params->port_num);
		addr4 = SDW_DPN_OFFSETCTRL1_B1(t_params->port_num);
		addr5 = SDW_DPN_BLOCKCTRL2_B1(t_params->port_num);
		addr6 = SDW_DPN_LANECTRL_B1(t_params->port_num);

	} else {
		addr3 = SDW_DPN_SAMPLECTRL1_B0(t_params->port_num);
		addr4 = SDW_DPN_OFFSETCTRL1_B0(t_params->port_num);
		addr5 = SDW_DPN_BLOCKCTRL2_B0(t_params->port_num);
		addr6 = SDW_DPN_LANECTRL_B0(t_params->port_num);
	}

	/* Program DPN_PortCtrl register */
	wbuf = FIELD_PREP(SDW_DPN_PORTCTRL_DATAMODE, p_params->data_mode);
	wbuf |= FIELD_PREP(SDW_DPN_PORTCTRL_FLOWMODE, p_params->flow_mode);

	ret = sdw_update_no_pm(s_rt->slave, addr1, 0xF, wbuf);
```

The manager path [`sdw_program_master_port_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L252) does not touch registers directly. It calls the [`dpn_set_port_transport_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) and [`dpn_set_port_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) callbacks of the [`struct sdw_master_port_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806), since the manager's data ports are located in the controller IP rather than on the wire:

```c
/* drivers/soundwire/stream.c:252 */
static int sdw_program_master_port_params(struct sdw_bus *bus,
					  struct sdw_port_runtime *p_rt)
{
	int ret;
	...
	ret = bus->port_ops->dpn_set_port_transport_params(bus,
					&p_rt->transport_params,
					bus->params.next_bank);
	if (ret < 0)
		return ret;

	return bus->port_ops->dpn_set_port_params(bus,
						  &p_rt->port_params,
						  bus->params.next_bank);
}
```

The shared programming step writes the bus-clock scale on the inactive bank when every peripheral supports SDCA, then walks each runtime to program its peripheral and manager ports:

```
    sdw_program_params(): bus-clock scale, then per-runtime fan-out
    ─────────────────────────────────────────────────────────────────

    sdw_program_params(bus, prepare)
        │
        ├─ all Peripherals SDCA?  ─▶  SDW_SCP_BUSCLOCK_SCALE_B0 / _B1
        │                              (selected by next_bank)
        ▼
    per m_rt on bus->m_rt_list
        │
        ├─▶ sdw_program_port_params(m_rt)
        │       ├─ Slave ports  ─▶ sdw_program_slave_port_params()
        │       │                    (writes peripheral regs directly)
        │       └─ Master ports ─▶ sdw_program_master_port_params()
        │                            (dpn_set_port_* ops)
        └─▶ sdw_notify_config(m_rt)

    Slave transport regs, addr chosen by next_bank:
    ┌──────────────────────┬──────────────────────────────────────┐
    │ DPN_PortCtrl         │ SDW_DPN_PORTCTRL(n)     (not banked) │
    │ DPN_BlockCtrl1       │ SDW_DPN_BLOCKCTRL1(n)   (not banked) │
    │ DPN_SampleCtrl1_Bx   │ SDW_DPN_SAMPLECTRL1_B0/B1(n)         │
    │ DPN_OffsetCtrl1_Bx   │ SDW_DPN_OFFSETCTRL1_B0/B1(n)         │
    │ DPN_BlockCtrl2_Bx    │ SDW_DPN_BLOCKCTRL2_B0/B1(n)          │
    │ DPN_LaneCtrl_Bx      │ SDW_DPN_LANECTRL_B0/B1(n)            │
    └──────────────────────┴──────────────────────────────────────┘
```

### Channel-prepare: sdw_prep_deprep_ports and the slave register write

[`sdw_prep_deprep_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L581), called from the prepare and de-prepare workers, walks the slave runtimes and then the manager ports, dispatching each to its side-specific helper:

```c
/* drivers/soundwire/stream.c:581 */
static int sdw_prep_deprep_ports(struct sdw_master_runtime *m_rt, bool prep)
{
	struct sdw_slave_runtime *s_rt;
	struct sdw_port_runtime *p_rt;
	int ret = 0;

	/* Prepare/De-prepare Slave port(s) */
	list_for_each_entry(s_rt, &m_rt->slave_rt_list, m_rt_node) {
		list_for_each_entry(p_rt, &s_rt->port_list, port_node) {
			ret = sdw_prep_deprep_slave_ports(m_rt->bus, s_rt,
							  p_rt, prep);
			if (ret < 0)
				return ret;
		}
	}

	/* Prepare/De-prepare Master port(s) */
	list_for_each_entry(p_rt, &m_rt->port_list, port_node) {
		ret = sdw_prep_deprep_master_ports(m_rt, p_rt, prep);
		if (ret < 0)
			return ret;
	}

	return ret;
}
```

The manager side [`sdw_prep_deprep_master_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L546) calls the [`dpn_port_prep`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) callback of the [`struct sdw_master_port_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) with a [`struct sdw_prepare_ch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L555) carrying [`bus->params.next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593). For the rt722-sdca codec, the peripheral side [`sdw_prep_deprep_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L441) drives the data-port channel-prepare state machine. When the peripheral does not implement the simple channel-prepare state machine, the helper writes the channel mask into [`SDW_DPN_PREPARECTRL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L246), waits on the per-port [`port_ready[]`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L677) completion that the peripheral's interrupt handler signals, and confirms the bits cleared by reading [`SDW_DPN_PREPARESTATUS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L245):

```c
/* drivers/soundwire/stream.c:441 */
	/* Prepare Slave port implementing CP_SM */
	if (!simple_ch_prep_sm) {
		addr = SDW_DPN_PREPARECTRL(p_rt->num);

		if (prep)
			ret = sdw_write_no_pm(s_rt->slave, addr, p_rt->ch_mask);
		else
			ret = sdw_write_no_pm(s_rt->slave, addr, 0x0);

		if (ret < 0) {
			dev_err(&s_rt->slave->dev,
				"Slave prep_ctrl reg write failed\n");
			return ret;
		}

		/* Wait for completion on port ready */
		port_ready = &s_rt->slave->port_ready[prep_ch.num];
		wait_for_completion_timeout(port_ready,
			msecs_to_jiffies(ch_prep_timeout));

		val = sdw_read_no_pm(s_rt->slave, SDW_DPN_PREPARESTATUS(p_rt->num));
		if ((val < 0) || (val & p_rt->ch_mask)) {
			ret = (val < 0) ? val : -ETIMEDOUT;
			dev_err(&s_rt->slave->dev,
				"Chn prep failed for port %d: %d\n", prep_ch.num, ret);
			return ret;
		}
	}
```

Before and after that register write the helper calls [`sdw_do_port_prep()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L415) with [`SDW_OPS_PORT_PRE_PREP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L571) and [`SDW_OPS_PORT_POST_PREP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L573), so the codec driver's [`port_prep`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) callback runs around the prepare.

```
    sdw_prep_deprep_slave_ports(): channel-prepare handshake
    ─────────────────────────────────────────────────────────────

    sdw_do_port_prep(SDW_OPS_PORT_PRE_PREP)   ◀ codec port_prep
        │
        ▼
    write SDW_DPN_PREPARECTRL(num)
        prep=true  ▶ ch_mask        prep=false ▶ 0x0
        │
        ▼
    wait_for_completion_timeout(port_ready[num])   ◀ peripheral IRQ
        │
        ▼
    read SDW_DPN_PREPARESTATUS(num)
        (val & ch_mask) != 0  ▶  -ETIMEDOUT
        │
        ▼
    sdw_do_port_prep(SDW_OPS_PORT_POST_PREP)  ◀ codec port_prep
```

### Channel-enable: sdw_enable_disable_ports and the banked register

[`sdw_enable_disable_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L389), called from the enable and disable workers and from the active-stream tail of [`sdw_program_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L661), walks the same two lists and dispatches to the slave and manager channel-enable helpers:

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

The peripheral side [`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317) writes the banked channel-enable register, [`SDW_DPN_CHANNELEN_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) or [`SDW_DPN_CHANNELEN_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L268), to the channel mask on enable and to 0 on disable. According to the comment, the register is on the inactive bank, so "This function only sets the enable/disable bits in the relevant bank, the actual enable/disable is done with a bank switch":

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
	return ret;
}
```

The manager side [`sdw_enable_disable_master_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L348) fills a [`struct sdw_enable_ch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L789) and calls the [`dpn_port_enable_ch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806) callback of the [`struct sdw_master_port_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L806), passing [`bus->params.next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) so the controller programs the same inactive bank:

```c
/* drivers/soundwire/stream.c:348 */
static int sdw_enable_disable_master_ports(struct sdw_master_runtime *m_rt,
					   struct sdw_port_runtime *p_rt,
					   bool en)
{
	struct sdw_transport_params *t_params = &p_rt->transport_params;
	struct sdw_bus *bus = m_rt->bus;
	struct sdw_enable_ch enable_ch;
	int ret;

	enable_ch.port_num = p_rt->num;
	enable_ch.ch_mask = p_rt->ch_mask;
	enable_ch.enable = en;

	/* Perform Master port channel(s) enable/disable */
	if (bus->port_ops->dpn_port_enable_ch) {
		ret = bus->port_ops->dpn_port_enable_ch(bus,
							&enable_ch,
							bus->params.next_bank);
		...
	} else {
		dev_err(bus->dev,
			"dpn_port_enable_ch not supported, %s failed\n",
			str_enable_disable(en));
		return -EINVAL;
	}

	return 0;
}
```

### do_bank_switch ends every transition

Each worker ends in [`do_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L845), which makes the registers programmed on the inactive bank current. It runs the manager's [`pre_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) callback, then [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742) per manager runtime, then [`post_bank_switch`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861), taking [`msg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) when the stream spans enough links to need hardware-synchronized bank switching:

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
			...
		}

		ret = sdw_bank_switch(bus, m_rt_count);
		if (ret < 0) {
			dev_err(bus->dev, "Bank switch failed: %d\n", ret);
			goto error;
		}
	}
	...
}
```

The register write that actually flips the bank is in [`sdw_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L742). It builds a broadcast message to the frame-control register for the inactive bank, [`SDW_SCP_FRAMECTRL_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L217) or [`SDW_SCP_FRAMECTRL_B1`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L218), sets [`ssp_sync`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L71) so the change lands at a frame boundary, and for a single-link stream swaps [`curr_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) and [`next_bank`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L593) immediately after the transfer:

```c
/* drivers/soundwire/stream.c:742 */
	if (bus->params.next_bank)
		addr = SDW_SCP_FRAMECTRL_B1;
	else
		addr = SDW_SCP_FRAMECTRL_B0;

	sdw_fill_msg(wr_msg, NULL, addr, 1, SDW_BROADCAST_DEV_NUM,
		     SDW_MSG_FLAG_WRITE, wbuf);
	wr_msg->ssp_sync = true;
	...
	if (!multi_link) {
		kfree(wbuf);
		kfree(wr_msg);
		bus->defer_msg.msg = NULL;
		bus->params.curr_bank = !bus->params.curr_bank;
		bus->params.next_bank = !bus->params.next_bank;
	}
```

The full mechanics of the broadcast write, the deferred multi-link transfer, and the [`sdw_ml_sync_bank_switch()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L817) wait are documented on the bank-switch page; here the relevant point is that every one of the four transitions ends with this same flip, so each set of register writes the worker stages on the inactive bank becomes live atomically.

### The x86-64 machine callers wire the transitions to ASoC

On an Intel SoundWire card the four transitions are driven from the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) the [`sof_sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865) machine driver attaches to every SoundWire DAI link, which points the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623), and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hooks at the [`sound/soc/sdw_utils/`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c) helpers:

```c
/* sound/soc/intel/boards/sof_sdw.c:865 */
static const struct snd_soc_ops sdw_ops = {
	.startup = asoc_sdw_startup,
	.prepare = asoc_sdw_prepare,
	.trigger = asoc_sdw_trigger,
	.hw_params = asoc_sdw_hw_params,
	.hw_free = asoc_sdw_hw_free,
	.shutdown = asoc_sdw_shutdown,
};
```

[`asoc_sdw_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031) reads the stream handle off the first CPU DAI with [`snd_soc_dai_get_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L579) and calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) on it:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1031 */
int asoc_sdw_prepare(struct snd_pcm_substream *substream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sdw_stream_runtime *sdw_stream;
	struct snd_soc_dai *dai;

	/* Find stream from first CPU DAI */
	dai = snd_soc_rtd_to_cpu(rtd, 0);

	sdw_stream = snd_soc_dai_get_stream(dai, substream->stream);
	if (IS_ERR(sdw_stream)) {
		dev_err(rtd->dev, "no stream found for DAI %s\n", dai->name);
		return PTR_ERR(sdw_stream);
	}

	return sdw_prepare_stream(sdw_stream);
}
```

[`asoc_sdw_trigger()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050) maps the ALSA PCM trigger command onto the enable and disable transitions, calling [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) for the start group and [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) for the stop group:

```c
/* sound/soc/sdw_utils/soc_sdw_utils.c:1050 */
	switch (cmd) {
	case SNDRV_PCM_TRIGGER_START:
	case SNDRV_PCM_TRIGGER_PAUSE_RELEASE:
	case SNDRV_PCM_TRIGGER_RESUME:
		ret = sdw_enable_stream(sdw_stream);
		break;

	case SNDRV_PCM_TRIGGER_PAUSE_PUSH:
	case SNDRV_PCM_TRIGGER_SUSPEND:
	case SNDRV_PCM_TRIGGER_STOP:
		ret = sdw_disable_stream(sdw_stream);
		break;
	default:
		ret = -EINVAL;
		break;
	}
```

[`asoc_sdw_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133) closes the cycle by calling [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) on the same handle, so the bandwidth the prepare claimed is given back when the PCM frees its hardware.

### The rt722-sdca codec supplies the ports the transitions drive

The peripheral whose data ports these transitions prepare and enable is the rt722-sdca codec. Its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116) runs before the prepare and picks the data port number and channel mask from the DAI id and the stream direction, then joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117). That add creates the [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) and the [`struct sdw_port_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) the later workers walk:

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK) {
		direction = SDW_DATA_DIR_RX;
		if (dai->id == RT722_AIF1)
			port = 1;
		else if (dai->id == RT722_AIF2)
			port = 3;
		else
			return -EINVAL;
	} else {
		direction = SDW_DATA_DIR_TX;
		if (dai->id == RT722_AIF1)
			port = 2;
		else if (dai->id == RT722_AIF3)
			port = 6;
		else
			return -EINVAL;
	}
	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = direction;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = port;

	retval = sdw_stream_add_slave(rt722->slave, &stream_config,
					&port_config, 1, sdw_stream);
```

According to the comment in the body, port 1 carries headphone playback and port 2 the headset-mic capture on [`RT722_AIF1`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L226), port 3 the speaker on [`RT722_AIF2`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L227), and port 6 the digital-mic capture on [`RT722_AIF3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L228). The [`port_config.ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893) computed here becomes the [`p_rt->ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L126) that [`sdw_enable_disable_slave_ports()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L317) writes into the codec's channel-enable register when [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) runs, and the same port number selects the [`SDW_DPN_PREPARECTRL`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L246) and [`SDW_DPN_CHANNELEN_B0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_registers.h#L267) addresses the prepare and enable helpers compute.

```
    rt722_sdca_pcm_hw_params(): stream + DAI id select the data port
    ─────────────────────────────────────────────────────────────────

    direction          DAI id        port   carries
    ────────────────────────────────────────────────────────
    PLAYBACK (RX)      RT722_AIF1      1     headphone playback
    PLAYBACK (RX)      RT722_AIF2      3     speaker
    CAPTURE  (TX)      RT722_AIF1      2     headset-mic capture
    CAPTURE  (TX)      RT722_AIF3      6     digital-mic capture

    ch_mask = GENMASK(num_channels - 1, 0)
    sdw_stream_add_slave() builds the sdw_port_runtime the workers walk
```
