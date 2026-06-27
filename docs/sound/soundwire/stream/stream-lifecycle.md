# SoundWire stream lifecycle

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

A SoundWire stream is the logical audio channel that one or more peripherals and their bus manager share across a SoundWire link, and the kernel tracks it with one [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) whose [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L964) field advances through seven values from allocation to release. [`sdw_alloc_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874) creates the runtime in [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L927), the codec and manager join through [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) and [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991) which build the master/slave runtime tree and set [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928), and the four transition entry points [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533), [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619), [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707), and [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) drive the state field to [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929), [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930), [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), and [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932). On an x86-64 ACPI machine the Realtek RT722 SDCA codec joins and leaves the stream from its DAI [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) and [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) ops while the [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865) machine driver runs the alloc, prepare, enable, disable, deprepare, and release steps from its [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) hooks, and [`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419) serializes every transition against other streams on the same bus.

```
    SoundWire stream state machine (enum sdw_stream_state)
    ──────────────────────────────────────────────────────

      sdw_alloc_stream()
            │
            ▼
    ┌────────────────┐
    │   ALLOCATED    │  state = 0, master_list empty
    └───────┬────────┘
            │  sdw_stream_add_slave() / sdw_stream_add_master()
            ▼
    ┌────────────────┐
    │   CONFIGURED   │  state = 1, master/slave runtimes + ports linked
    └───────┬────────┘
            │  sdw_prepare_stream()    (port prepare + bank switch)
            ▼
    ┌────────────────┐
    │    PREPARED    │  state = 2
    └───────┬────────┘
            │  sdw_enable_stream()     (channel enable + bank switch)
            ▼
    ┌────────────────┐
    │    ENABLED     │  state = 3  ◀── link carries audio
    └───────┬────────┘
            │  sdw_disable_stream()    (channel disable + bank switch)
            ▼
    ┌────────────────┐
    │    DISABLED    │  state = 4
    └───────┬────────┘
            │  sdw_deprepare_stream()  (port de-prepare + bank switch)
            ▼
    ┌────────────────┐
    │   DEPREPARED   │  state = 5
    └───────┬────────┘
            │  sdw_stream_remove_master()  (master_list emptied)
            ▼
    ┌────────────────┐
    │    RELEASED    │  state = 6, runtime freed by sdw_release_stream()
    └────────────────┘

    re-entry edges (underflow / resume / restart):
      DISABLED   ──sdw_prepare_stream()────▶ PREPARED
      DISABLED   ──sdw_enable_stream()─────▶ ENABLED
      DISABLED   ──sdw_deprepare_stream()──▶ DEPREPARED
      DEPREPARED ──sdw_prepare_stream()────▶ PREPARED
```

## SUMMARY

The SoundWire core represents one audio stream with a single [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961). [`sdw_alloc_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874) allocates it with [`kzalloc_obj()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L1039), records the name, initializes the empty [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) head, and sets [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L964) to [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L927). The codec adds itself with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), which allocates a [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) through [`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224) and a [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) through [`sdw_slave_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129), configures the ports from a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) and a [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893), and advances the stream to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928) on the first slave add. [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991) does the equivalent for the bus manager, reusing the manager runtime the slave add already created and incrementing [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966) when it allocates a fresh one.

The four transition entry points share one shape. Each acquires the bus lock with [`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419), returns success early if the stream already holds the target state, rejects any state that is not a legal predecessor, calls an inner `_sdw_*_stream()` worker that walks the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) doing the bus programming, and releases the lock with [`sdw_release_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1441). [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) accepts [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928), [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932), or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) and sets [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929); [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) accepts [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) and sets [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930); [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) accepts only [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) and sets [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931); and [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) accepts [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) and sets [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932). The bodies of those four ops (transport programming, channel prepare and enable, and bank switching) are documented in the sibling stream-transitions page; this page treats them as the edges that move the state field. Teardown runs in the reverse order: [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228) frees the per-codec runtime, [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078) frees the manager runtime and sets [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) once the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) empties, and [`sdw_release_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1976) frees the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) itself.

## SPECIFICATIONS

The [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) state machine is a Linux kernel software construct layered on the MIPI Alliance SoundWire bus. The seven [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) values, the legal transitions between them, and the alloc/add/prepare/enable/disable/deprepare/release contract are defined by the kernel in [`include/linux/soundwire/sdw.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h) and [`drivers/soundwire/stream.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c), as a software construct above any register-level standard. The transport and port operations the transition functions program (data-port channel-prepare and channel-enable bits, frame-shape and active-bank registers) and the SDCA control model the RT722 codec drives are described by the MIPI SoundWire and SDCA specifications, which are membership-gated and not reproduced here; the page describes the state model entirely from kernel source. According to the comment on [`enum sdw_stream_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L160), "spec doesn't define this, but is used in implementation", so the PCM, PDM, and BPT classification carried in [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L965) is a kernel-internal distinction rather than a bus-level one.

## LINUX KERNEL

### Stream runtime object and state (sdw.h)

- [`'\<struct sdw_stream_runtime\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961): the per-stream runtime carrying the [`name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L962), the negotiated [`params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L963), the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L964), the [`type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L965), the [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966), and the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) of manager runtimes
- [`'\<enum sdw_stream_state\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926): the seven states [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L927) (0), [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928) (1), [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) (2), [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) (3), [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) (4), [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) (5), [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) (6)
- [`'\<enum sdw_stream_type\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L160): [`SDW_STREAM_PCM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L161), [`SDW_STREAM_PDM`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L162), [`SDW_STREAM_BPT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L163)
- [`'\<struct sdw_stream_params\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L943): the negotiated [`rate`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L944), [`ch_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L945), and [`bps`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L946) cached on the runtime
- [`'\<struct sdw_stream_config\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907): the per-direction config (`frame_rate`, `ch_count`, `bps`, `direction`, `type`) a DAI fills in before adding itself to the stream
- [`'\<struct sdw_port_config\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893): the data-port [`num`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L900) and channel [`ch_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L901)

### Per-stream runtime tree types (bus.h)

- [`'\<struct sdw_master_runtime\>':'drivers/soundwire/bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166): one per manager per stream, holding the [`bus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), the [`stream`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) back pointer, the [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), the manager [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), the [`stream_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) that links it onto the stream's [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967), and the [`bus_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) that links it onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1023)
- [`'\<struct sdw_slave_runtime\>':'drivers/soundwire/bus.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145): one per peripheral per stream, holding the [`slave`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), the [`direction`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), the [`ch_count`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), the [`port_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145), and the [`m_rt_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) onto the manager runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166)

### Allocation and release (stream.c)

- [`'\<sdw_alloc_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874): allocate the runtime, init [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967), set [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L927); called once per stream
- [`'\<sdw_release_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1976): [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L513) the runtime; called once per stream
- [`'\<sdw_startup_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1899): name and allocate the stream for a [`struct snd_pcm_substream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L464), then store it on every DAI via [`set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1844)
- [`'\<sdw_shutdown_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1943): retrieve the stream from the first CPU DAI, free its name, and call [`sdw_release_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1976)
- [`'\<set_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1844): store the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) pointer on every DAI of a runtime through [`snd_soc_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559)

### Membership: add and remove runtimes (stream.c)

- [`'\<sdw_stream_add_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117): under [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018), allocate the manager and slave runtimes if absent, allocate and configure the slave ports, and set [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928) on the first slave add
- [`'\<sdw_stream_add_master\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991): allocate the manager runtime if absent (reuse it when the slave add already created it), configure its ports, and increment [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966)
- [`'\<sdw_stream_remove_slave\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228): free the slave ports and the slave runtime under [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018)
- [`'\<sdw_stream_remove_master\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078): free the manager ports and runtime, decrement [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966), and set [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) once [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) is empty
- [`'\<sdw_master_rt_alloc\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224): allocate a [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), insert it onto [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) in bus-id order, and link it onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1023)
- [`'\<sdw_slave_rt_alloc\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129): allocate a [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) and link it onto the manager runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166)

### State-transition entry points and serialization (stream.c)

- [`'\<sdw_prepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533): guard from [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928), [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932), or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), then drive to [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) (body covered in the stream-transitions page)
- [`'\<sdw_enable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619): guard from [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), then drive to [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930)
- [`'\<sdw_disable_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707): guard from [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930), then drive to [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931)
- [`'\<sdw_deprepare_stream\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812): guard from [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), then drive to [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932)
- [`'\<sdw_acquire_bus_lock\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419): take the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018) mutex of every manager runtime in [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967)
- [`'\<sdw_release_bus_lock\>':'drivers/soundwire/stream.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1441): drop the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018) mutexes in reverse order

### x86-64 machine and RT722 codec glue (sdw_utils, sof_sdw, rt722-sdca)

- [`'sdw_ops':'sound/soc/intel/boards/sof_sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865): the [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) the Intel SOF SoundWire machine driver attaches to every SoundWire DAI link, wiring [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L624), [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L628), [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L629), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L627), and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L625) to the `asoc_sdw_*` wrappers
- [`'\<asoc_sdw_startup\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1025): the machine [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L624) op, calls [`sdw_startup_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1899)
- [`'\<asoc_sdw_prepare\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1031): the machine [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L628) op, calls [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533)
- [`'\<asoc_sdw_trigger\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1050): the machine [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L629) op, calls [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) on START/PAUSE_RELEASE/RESUME and [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) on STOP/PAUSE_PUSH/SUSPEND
- [`'\<asoc_sdw_hw_free\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133): the machine [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L627) op, calls [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812)
- [`'\<asoc_sdw_shutdown\>':'sound/soc/sdw_utils/soc_sdw_utils.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1152): the machine [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L625) op, calls [`sdw_shutdown_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1943)
- [`'rt722_sdca_ops':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246): the RT722 [`struct snd_soc_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L269) wiring [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326), [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328), and [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308)
- [`'\<rt722_sdca_set_sdw_stream\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102): the codec [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op, stores the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) handle in the DAI DMA-data slot
- [`'\<rt722_sdca_pcm_hw_params\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116): the codec [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op, joins the codec to the stream with [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117)
- [`'\<rt722_sdca_pcm_hw_free\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226): the codec [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) op, removes the codec with [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228)

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the stream concept, the state machine, the master/slave/port runtime objects, and the alloc/add/prepare/enable/disable/deprepare/remove/release API contract
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018) and [`msg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1022) ordering the transition functions follow
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): how a failed transition unwinds and how the stream returns to a consistent state
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the bus overview, the manager and peripheral roles, and the data-port model the runtime tree mirrors
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end split the SoundWire DAI link sits behind on an Intel SOF card

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## CALLBACKS

The four state-transition functions are not a function pointer struct of their own; they are exported functions a machine driver calls in a fixed order, one per state edge. On an Intel SOF SoundWire card the order is fixed by the [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865) machine [`struct snd_soc_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L623) and the RT722 codec's [`rt722_sdca_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1246) DAI ops, which together map each ALSA PCM operation to the SoundWire call that runs and the [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) it sets.

| PCM operation | machine / codec op | SoundWire call | resulting state |
|---------------|--------------------|----------------|-----------------|
| `open()` | machine [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L624) | [`sdw_startup_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1899) | [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L927) |
| `SNDRV_PCM_IOCTL_HW_PARAMS` | codec [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) | [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) | [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928) |
| `SNDRV_PCM_IOCTL_PREPARE` | machine [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L628) | [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) | [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) |
| `SNDRV_PCM_IOCTL_START` | machine [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L629) (START) | [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) | [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930) |
| `SNDRV_PCM_IOCTL_DROP` | machine [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L629) (STOP) | [`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) | [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) |
| `SNDRV_PCM_IOCTL_HW_FREE` | machine [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L627) | [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) | [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932) |
| `SNDRV_PCM_IOCTL_HW_FREE` | codec [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) | [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228) | (per-codec runtime freed) |
| `close()` | machine [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L625) | [`sdw_shutdown_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1943) | [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) |

The state set in the last column is the value the [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) holds after the row's call returns, and the RELEASED row reflects [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078) setting [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) when the last manager runtime leaves, just before [`sdw_release_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1976) frees the object. The bus reaches the manager and peripheral hardware through two function pointer structs, [`struct sdw_master_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) and [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616). The RT722 codec fills [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616) with [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) in its [`rt722_sdca_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L410); the transition bodies that invoke those callbacks are documented in the stream-transitions page.

## DETAILS

### The stream runtime and its state field

The whole lifecycle is the [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L964) field of one [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) advancing through [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926). The runtime holds a name, the negotiated [`struct sdw_stream_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L943), the current state, the stream type, a count of manager runtimes, and the list head that links every manager runtime carrying this stream:

```c
/* include/linux/soundwire/sdw.h:961 */
struct sdw_stream_runtime {
	const char *name;
	struct sdw_stream_params params;
	enum sdw_stream_state state;
	enum sdw_stream_type type;
	int m_rt_count;
	struct list_head master_list;
};
```

The state values are dense and ordered, which lets the transition guards compare the current [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L964) against named predecessors rather than tracking a bitmask:

```c
/* include/linux/soundwire/sdw.h:926 */
enum sdw_stream_state {
	SDW_STREAM_ALLOCATED = 0,
	SDW_STREAM_CONFIGURED = 1,
	SDW_STREAM_PREPARED = 2,
	SDW_STREAM_ENABLED = 3,
	SDW_STREAM_DISABLED = 4,
	SDW_STREAM_DEPREPARED = 5,
	SDW_STREAM_RELEASED = 6,
};
```

The list head is the root of the runtime tree the membership calls build. Each [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) on [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) holds one manager's view of the stream, threads onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1023) through [`bus_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166), and owns the peripherals on that link through [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166):

```c
/* drivers/soundwire/bus.h:166 */
struct sdw_master_runtime {
	struct sdw_bus *bus;
	struct sdw_stream_runtime *stream;
	enum sdw_data_direction direction;
	unsigned int ch_count;
	struct list_head slave_rt_list;
	struct list_head port_list;
	struct list_head stream_node;
	struct list_head bus_node;
};
```

Each [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) is one peripheral's participation in the stream, linked onto its manager runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) by [`m_rt_node`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145):

```c
/* drivers/soundwire/bus.h:145 */
struct sdw_slave_runtime {
	struct sdw_slave *slave;
	enum sdw_data_direction direction;
	unsigned int ch_count;
	struct list_head m_rt_node;
	struct list_head port_list;
};
```

### Allocation sets ALLOCATED

[`sdw_alloc_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874) is the only producer of a [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961). It zero-allocates the object, copies the caller's name, initializes the empty [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967), sets [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L927), clears [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966), and records the stream type:

```c
/* drivers/soundwire/stream.c:1874 */
struct sdw_stream_runtime *sdw_alloc_stream(const char *stream_name, enum sdw_stream_type type)
{
	struct sdw_stream_runtime *stream;

	stream = kzalloc_obj(*stream);
	if (!stream)
		return NULL;

	stream->name = stream_name;
	INIT_LIST_HEAD(&stream->master_list);
	stream->state = SDW_STREAM_ALLOCATED;
	stream->m_rt_count = 0;
	stream->type = type;

	return stream;
}
```

According to the comment on [`sdw_alloc_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874), it "should be called only once per stream" and is "Typically invoked from ALSA/ASoC machine/platform driver". On an x86-64 ACPI SOF card the call comes from [`sdw_startup_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1899), which the [`sdw_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/intel/boards/sof_sdw.c#L865) machine driver wires as the DAI-link [`startup`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L624) op through the [`asoc_sdw_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1025) wrapper. It names the stream for the substream direction, allocates it as a PCM stream, and stores the handle on every DAI through [`set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1844):

```c
/* drivers/soundwire/stream.c:1899 */
int sdw_startup_stream(void *sdw_substream)
{
	struct snd_pcm_substream *substream = sdw_substream;
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sdw_stream_runtime *sdw_stream;
	char *name;
	int ret;

	if (substream->stream == SNDRV_PCM_STREAM_PLAYBACK)
		name = kasprintf(GFP_KERNEL, "%s-Playback", substream->name);
	else
		name = kasprintf(GFP_KERNEL, "%s-Capture", substream->name);

	if (!name)
		return -ENOMEM;

	sdw_stream = sdw_alloc_stream(name, SDW_STREAM_PCM);
	if (!sdw_stream) {
		dev_err(rtd->dev, "alloc stream failed for substream DAI %s\n", substream->name);
		ret = -ENOMEM;
		goto error;
	}

	ret = set_stream(substream, sdw_stream);
	if (ret < 0)
		goto release_stream;
	return 0;

release_stream:
	sdw_release_stream(sdw_stream);
	set_stream(substream, NULL);
error:
	kfree(name);
	return ret;
}
```

[`set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1844) loops over every DAI of the runtime and calls [`snd_soc_dai_set_stream()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L559), which invokes the codec [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op so the codec keeps its own copy of the handle:

```c
/* drivers/soundwire/stream.c:1844 */
static int set_stream(struct snd_pcm_substream *substream,
		      struct sdw_stream_runtime *sdw_stream)
{
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct snd_soc_dai *dai;
	int ret = 0;
	int i;

	/* Set stream pointer on all DAIs */
	for_each_rtd_dais(rtd, i, dai) {
		ret = snd_soc_dai_set_stream(dai, sdw_stream, substream->stream);
		if (ret < 0) {
			dev_err(rtd->dev, "failed to set stream pointer on dai %s\n", dai->name);
			break;
		}
	}

	return ret;
}
```

For the RT722 codec the [`set_stream`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L308) op is [`rt722_sdca_set_sdw_stream()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1102), which stashes the handle in the per-direction DMA-data slot of the DAI so its [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op can find it later:

```c
/* sound/soc/codecs/rt722-sdca.c:1102 */
static int rt722_sdca_set_sdw_stream(struct snd_soc_dai *dai, void *sdw_stream,
				int direction)
{
	snd_soc_dai_dma_data_set(dai, direction, sdw_stream);

	return 0;
}
```

### Adding the first slave sets CONFIGURED and builds the runtime tree

The stream moves from [`SDW_STREAM_ALLOCATED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L927) to [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928) when the first peripheral joins. The RT722 codec joins from its DAI [`hw_params`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L326) op [`rt722_sdca_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1116), which reads back the stored handle, fills a [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) from the negotiated rate, channel count, and sample width, picks the data port from the DAI id and direction, and calls [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117):

```c
/* sound/soc/codecs/rt722-sdca.c:1116 */
static int rt722_sdca_pcm_hw_params(struct snd_pcm_substream *substream,
				struct snd_pcm_hw_params *params,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_config stream_config;
	struct sdw_port_config port_config;
	enum sdw_data_direction direction;
	struct sdw_stream_runtime *sdw_stream;
	int retval, port, num_channels;
	unsigned int sampling_rate;

	sdw_stream = snd_soc_dai_get_dma_data(dai, substream);

	if (!sdw_stream)
		return -EINVAL;

	if (!rt722->slave)
		return -EINVAL;
	...
	stream_config.frame_rate = params_rate(params);
	stream_config.ch_count = params_channels(params);
	stream_config.bps = snd_pcm_format_width(params_format(params));
	stream_config.direction = direction;

	num_channels = params_channels(params);
	port_config.ch_mask = GENMASK(num_channels - 1, 0);
	port_config.num = port;

	retval = sdw_stream_add_slave(rt722->slave, &stream_config,
					&port_config, 1, sdw_stream);
	if (retval) {
		dev_err(dai->dev, "%s: Unable to configure port\n", __func__);
		return retval;
	}
	...
}
```

The [`struct sdw_stream_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L907) and [`struct sdw_port_config`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L893) the codec fills are the inputs every peripheral hands the core; the first carries the per-direction PCM parameters, the second names the data port and its channel mask:

```c
/* include/linux/soundwire/sdw.h:907 */
struct sdw_stream_config {
	unsigned int frame_rate;
	unsigned int ch_count;
	unsigned int bps;
	enum sdw_data_direction direction;
	enum sdw_stream_type type;
};

/* include/linux/soundwire/sdw.h:893 */
struct sdw_port_config {
	unsigned int num;
	unsigned int ch_mask;
};
```

[`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) takes the bus lock for the whole add. It finds or allocates a [`struct sdw_master_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166) for this stream on the slave's bus through [`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224), allocates a [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) through [`sdw_slave_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129) and its ports, configures both the manager and slave transport parameters, and on the first slave add sets [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928):

```c
/* drivers/soundwire/stream.c:2117 */
int sdw_stream_add_slave(struct sdw_slave *slave,
			 struct sdw_stream_config *stream_config,
			 const struct sdw_port_config *port_config,
			 unsigned int num_ports,
			 struct sdw_stream_runtime *stream)
{
	struct sdw_slave_runtime *s_rt;
	struct sdw_master_runtime *m_rt;
	bool alloc_master_rt = false;
	bool alloc_slave_rt = false;

	int ret;

	mutex_lock(&slave->bus->bus_lock);

	/*
	 * check if Master is already allocated, if so skip allocation
	 * and go to configuration
	 */
	m_rt = sdw_master_rt_find(slave->bus, stream);
	if (!m_rt) {
		/*
		 * If this API is invoked by Slave first then m_rt is not valid.
		 * So, allocate m_rt and add Slave to it.
		 */
		m_rt = sdw_master_rt_alloc(slave->bus, stream);
		...
		alloc_master_rt = true;
	}

	s_rt = sdw_slave_rt_find(slave, stream);
	if (!s_rt) {
		s_rt = sdw_slave_rt_alloc(slave, m_rt);
		...
		alloc_slave_rt = true;
	}
	...
	ret = sdw_slave_port_config(slave, s_rt, port_config,
				    stream->type == SDW_STREAM_BPT);
	if (ret)
		goto unlock;

	/*
	 * Change stream state to CONFIGURED on first Slave add.
	 * Bus is not aware of number of Slave(s) in a stream at this
	 * point so cannot depend on all Slave(s) to be added in order to
	 * change stream state to CONFIGURED.
	 */
	stream->state = SDW_STREAM_CONFIGURED;
	goto unlock;
	...
unlock:
	mutex_unlock(&slave->bus->bus_lock);
	return ret;
}
```

According to the comment in the body, the bus "is not aware of number of Slave(s) in a stream at this point so cannot depend on all Slave(s) to be added in order to change stream state to CONFIGURED", so the transition happens on the first add and stays put as later peripherals join. The `alloc_master_rt` and `alloc_slave_rt` flags record which objects this call created so the `alloc_error` tail frees only those; the comment there notes that freeing the manager runtime "will call sdw_slave_rt_free() internally", which is why the two cleanups sit in an `else if`.

[`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224) is what links the manager runtime into both lists. It inserts onto the stream's [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) in ascending bus-id order, then appends onto [`bus->m_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1023):

```c
/* drivers/soundwire/stream.c:1224 */
	m_rt = kzalloc_obj(*m_rt);
	if (!m_rt)
		return NULL;

	/* Initialization of Master runtime handle */
	INIT_LIST_HEAD(&m_rt->port_list);
	INIT_LIST_HEAD(&m_rt->slave_rt_list);

	/*
	 * Add in order of bus id so that when taking the bus_lock
	 * of multiple buses they will always be taken in the same
	 * order to prevent a mutex deadlock.
	 */
	insert_after = &stream->master_list;
	list_for_each_entry_reverse(walk_m_rt, &stream->master_list, stream_node) {
		if (walk_m_rt->bus->id < bus->id) {
			insert_after = &walk_m_rt->stream_node;
			break;
		}
	}
	list_add(&m_rt->stream_node, insert_after);

	list_add_tail(&m_rt->bus_node, &bus->m_rt_list);

	m_rt->bus = bus;
	m_rt->stream = stream;
```

According to the comment, the bus-id ordering exists "so that when taking the bus_lock of multiple buses they will always be taken in the same order to prevent a mutex deadlock". This is the ordering [`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419) later relies on. [`sdw_slave_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1129) is the simpler counterpart, hanging a fresh slave runtime off the manager runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166):

```c
/* drivers/soundwire/stream.c:1129 */
static struct sdw_slave_runtime
*sdw_slave_rt_alloc(struct sdw_slave *slave,
		    struct sdw_master_runtime *m_rt)
{
	struct sdw_slave_runtime *s_rt;

	s_rt = kzalloc_obj(*s_rt);
	if (!s_rt)
		return NULL;

	INIT_LIST_HEAD(&s_rt->port_list);
	s_rt->slave = slave;

	list_add_tail(&s_rt->m_rt_node, &m_rt->slave_rt_list);

	return s_rt;
}
```

The two alloc helpers build this tree under the stream runtime, the manager runtimes hanging off master_list and each one carrying the peripheral runtimes on its slave_rt_list:

```
    Per-stream runtime tree (one sdw_stream_runtime and its lists)
    ──────────────────────────────────────────────────────────────

    ┌──────────────────────────────────┐
    │ struct sdw_stream_runtime        │  state, type, m_rt_count
    └─────────────────┬────────────────┘
                      │  master_list (stream_node), one per manager
                      ▼
    ┌──────────────────────────────────┐
    │ struct sdw_master_runtime        │  bus, ch_count
    │   port_list  ▶ manager ports     │
    └─────────────────┬────────────────┘
                      │  slave_rt_list (m_rt_node), one per device
                      ▼
    ┌──────────────────────────────────┐
    │ struct sdw_slave_runtime         │  slave, ch_count
    │   port_list  ▶ peripheral ports  │
    └──────────────────────────────────┘

    each sdw_master_runtime also links onto bus->m_rt_list via bus_node
```

### Adding the manager increments m_rt_count

The bus manager is added with [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991). On the Intel SOF SoundWire path the manager runtime is usually already present from the slave add, so [`sdw_master_rt_find()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1201) returns it and the call reuses it; only when it allocates a fresh manager runtime and its ports does it increment [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966), which the bank-switch logic later reads to decide whether a flip must be hardware-synchronized across links:

```c
/* drivers/soundwire/stream.c:1991 */
int sdw_stream_add_master(struct sdw_bus *bus,
			  struct sdw_stream_config *stream_config,
			  const struct sdw_port_config *port_config,
			  unsigned int num_ports,
			  struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt;
	bool alloc_master_rt = false;
	int ret;

	mutex_lock(&bus->bus_lock);
	...
	m_rt = sdw_master_rt_find(bus, stream);
	if (!m_rt) {
		m_rt = sdw_master_rt_alloc(bus, stream);
		...
		alloc_master_rt = true;
	}

	if (!sdw_master_port_allocated(m_rt)) {
		ret = sdw_master_port_alloc(m_rt, num_ports);
		if (ret)
			goto alloc_error;

		stream->m_rt_count++;
	}
	...
unlock:
	mutex_unlock(&bus->bus_lock);
	return ret;
}
```

According to the comment at the top of the allocation branch, the call checks "if Master is already allocated (e.g. as a result of Slave adding it first), if so skip allocation and go to configuration", so on a single-codec link the manager add does configuration only. The guard above the allocation refuses a second manager on a bus whose [`multi_link`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1046) flag is clear once [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966) is already above zero.

### The transition shape: lock, guard, inner worker, unlock

The four state-transition entry points share one shape, and [`sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1533) shows it. It acquires the bus lock for every manager runtime, returns success early if the stream already holds the target state, rejects any state that is not a legal predecessor, and otherwise calls the inner [`_sdw_prepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1453) worker (whose port-prepare and bank-switch body the stream-transitions page covers) before releasing the lock:

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

The legal predecessors are [`SDW_STREAM_CONFIGURED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L928), [`SDW_STREAM_DEPREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L932), and [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), which is what gives the state machine its re-entry edges from a stopped stream back to PREPARED. According to the comment in the body, when the stream is [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931) the prepare "is called as a result of an underflow or a resume operation", so it re-applies the bus parameters without recomputing the bandwidth. The other three entry points reject different predecessor sets but share the lock, early-return, guard, worker, unlock skeleton. [`sdw_enable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1619) accepts [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931):

```c
/* drivers/soundwire/stream.c:1619 */
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
```

[`sdw_disable_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1707) is the strictest, accepting only [`SDW_STREAM_ENABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L930), since a stream can be disabled only from the running state:

```c
/* drivers/soundwire/stream.c:1707 */
	if (stream->state == SDW_STREAM_DISABLED) {
		ret = 0;
		goto state_err;
	}

	if (stream->state != SDW_STREAM_ENABLED) {
		pr_err("%s: %s: inconsistent state state %d\n",
		       __func__, stream->name, stream->state);
		ret = -EINVAL;
		goto state_err;
	}

	ret = _sdw_disable_stream(stream);
```

[`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812) accepts [`SDW_STREAM_PREPARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L929) or [`SDW_STREAM_DISABLED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L931), so a stream that was prepared but never started can be torn down without passing through ENABLED:

```c
/* drivers/soundwire/stream.c:1812 */
	if (stream->state == SDW_STREAM_DEPREPARED) {
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

	ret = _sdw_deprepare_stream(stream);
```

Taken together the four guards define the legal edges: ALLOCATED reaches CONFIGURED only through an add call, CONFIGURED reaches PREPARED, PREPARED reaches ENABLED or DEPREPARED, ENABLED reaches DISABLED, DISABLED reaches PREPARED or ENABLED or DEPREPARED, and DEPREPARED reaches PREPARED. The repeated DISABLED-as-predecessor in prepare, enable, and deprepare lets a stopped stream restart, resume after suspend, or tear down from the same state.

```
    Transition guards: accepted predecessor states ──▶ exit state
    ─────────────────────────────────────────────────────────────

    entry point             accepted "from" state(s)      exit state
    ┌─────────────────────┬──────────────────────────┬──────────────┐
    │ sdw_prepare_stream  │ CONFIGURED DEPREPARED    │ PREPARED     │
    │                     │ DISABLED                 │              │
    ├─────────────────────┼──────────────────────────┼──────────────┤
    │ sdw_enable_stream   │ PREPARED  DISABLED       │ ENABLED      │
    ├─────────────────────┼──────────────────────────┼──────────────┤
    │ sdw_disable_stream  │ ENABLED                  │ DISABLED     │
    ├─────────────────────┼──────────────────────────┼──────────────┤
    │ sdw_deprepare_stream│ PREPARED  DISABLED       │ DEPREPARED   │
    └─────────────────────┴──────────────────────────┴──────────────┘

    DISABLED recurs as a "from" state in prepare / enable / deprepare:
    a stopped stream may restart, resume, or tear down from there.
```

### bus_lock serializes a transition against other streams

[`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419) walks the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967) and takes the [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018) mutex of each manager runtime's bus, so a transition that spans several links holds every relevant bus lock for its whole duration:

```c
/* drivers/soundwire/stream.c:1419 */
static void sdw_acquire_bus_lock(struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt;
	struct sdw_bus *bus;

	/* Iterate for all Master(s) in Master list */
	list_for_each_entry(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;

		mutex_lock(&bus->bus_lock);
	}
}
```

[`sdw_release_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1441) drops them with [`list_for_each_entry_reverse()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L792) so the release order mirrors the acquire order, and because [`sdw_master_rt_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1224) inserted the runtimes in ascending bus-id order, every multi-link stream takes its bus locks in the same order and cannot deadlock against another:

```c
/* drivers/soundwire/stream.c:1441 */
static void sdw_release_bus_lock(struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt;
	struct sdw_bus *bus;

	/* Iterate for all Master(s) in Master list */
	list_for_each_entry_reverse(m_rt, &stream->master_list, stream_node) {
		bus = m_rt->bus;
		mutex_unlock(&bus->bus_lock);
	}
}
```

According to the comment on [`sdw_acquire_bus_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1419), the function "is called from SoundWire stream ops and is expected that a global lock is held before acquiring bus_lock". Holding [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018) across the transition keeps a second stream on the same link from reprogramming transport parameters underneath the first, because the bandwidth recomputation and the bank registers the transition bodies touch are bus-global. The same [`bus_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1018) guards the membership calls: [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117), [`sdw_stream_add_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1991), [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228), and [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078) each take it directly through [`mutex_lock()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/locking/mutex.c#L285) on the single bus they touch rather than through the multi-bus walk, so a membership change and a transition cannot interleave on one link.

```
    bus_lock ordering over master_list (ascending bus id, no deadlock)
    ──────────────────────────────────────────────────────────────────

    master_list is kept sorted by bus id, so every stream locks the
    same buses in the same order.

    acquire (sdw_acquire_bus_lock, forward walk)
        bus id 0  ──▶  bus id 1  ──▶  bus id 2   lock lock lock
    ┌──────────────────────────────────────────────────────────┐
    │              transition body runs holding all bus_locks  │
    └──────────────────────────────────────────────────────────┘
    release (sdw_release_bus_lock, reverse walk)
        bus id 2  ──▶  bus id 1  ──▶  bus id 0   unlock unlock unlock
```

### Removing the slave, then the master, sets RELEASED

When the substream is freed, the RT722 codec leaves the stream from its DAI [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L328) op [`rt722_sdca_pcm_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1226), which reads the stored handle and calls [`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228):

```c
/* sound/soc/codecs/rt722-sdca.c:1226 */
static int rt722_sdca_pcm_hw_free(struct snd_pcm_substream *substream,
				struct snd_soc_dai *dai)
{
	struct snd_soc_component *component = dai->component;
	struct rt722_sdca_priv *rt722 = snd_soc_component_get_drvdata(component);
	struct sdw_stream_runtime *sdw_stream =
		snd_soc_dai_get_dma_data(dai, substream);

	if (!rt722->slave)
		return -EINVAL;

	sdw_stream_remove_slave(rt722->slave, sdw_stream);
	return 0;
}
```

[`sdw_stream_remove_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2228) frees the slave ports and the slave runtime under the bus lock, the inverse of what [`sdw_stream_add_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2117) allocated. It does not change [`state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L964); the per-codec teardown only unlinks one [`struct sdw_slave_runtime`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L145) from its manager runtime's [`slave_rt_list`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.h#L166):

```c
/* drivers/soundwire/stream.c:2228 */
int sdw_stream_remove_slave(struct sdw_slave *slave,
			    struct sdw_stream_runtime *stream)
{
	mutex_lock(&slave->bus->bus_lock);

	sdw_slave_port_free(slave, stream);
	sdw_slave_rt_free(slave, stream);

	mutex_unlock(&slave->bus->bus_lock);

	return 0;
}
```

The state field reaches [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) in [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078). It walks the [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967), frees the manager ports and runtime for the matching bus, decrements [`m_rt_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L966), and sets [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) once the list is empty:

```c
/* drivers/soundwire/stream.c:2078 */
int sdw_stream_remove_master(struct sdw_bus *bus,
			     struct sdw_stream_runtime *stream)
{
	struct sdw_master_runtime *m_rt, *_m_rt;

	mutex_lock(&bus->bus_lock);

	list_for_each_entry_safe(m_rt, _m_rt,
				 &stream->master_list, stream_node) {
		if (m_rt->bus != bus)
			continue;

		sdw_master_port_free(m_rt);
		sdw_master_rt_free(m_rt, stream);
		stream->m_rt_count--;
	}

	if (list_empty(&stream->master_list))
		stream->state = SDW_STREAM_RELEASED;

	mutex_unlock(&bus->bus_lock);

	return 0;
}
```

The list-empty test is why [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) is set by the manager removal rather than the slave removal. A multi-link stream has one manager runtime per bus, so the state advances to RELEASED only after the final [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078) empties [`master_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L967). The deprepare that precedes teardown runs from the machine [`hw_free`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L627) op [`asoc_sdw_hw_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sdw_utils/soc_sdw_utils.c#L1133), which finds the stream from the first CPU DAI and calls [`sdw_deprepare_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1812). Finally [`sdw_shutdown_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1943), the machine [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L625) op, reads the handle back from the first CPU DAI, frees its name, and calls [`sdw_release_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1976):

```c
/* drivers/soundwire/stream.c:1943 */
void sdw_shutdown_stream(void *sdw_substream)
{
	struct snd_pcm_substream *substream = sdw_substream;
	struct snd_soc_pcm_runtime *rtd = snd_soc_substream_to_rtd(substream);
	struct sdw_stream_runtime *sdw_stream;
	struct snd_soc_dai *dai;

	/* Find stream from first CPU DAI */
	dai = snd_soc_rtd_to_cpu(rtd, 0);

	sdw_stream = snd_soc_dai_get_stream(dai, substream->stream);

	if (IS_ERR(sdw_stream)) {
		dev_err(rtd->dev, "no stream found for DAI %s\n", dai->name);
		return;
	}

	/* release memory */
	kfree(sdw_stream->name);
	sdw_release_stream(sdw_stream);

	/* clear DAI data */
	set_stream(substream, NULL);
}
```

[`sdw_release_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1976) is the only consumer of the object [`sdw_alloc_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874) produced, and it frees it outright:

```c
/* drivers/soundwire/stream.c:1976 */
void sdw_release_stream(struct sdw_stream_runtime *stream)
{
	kfree(stream);
}
```

According to the comment on [`sdw_release_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1976), it "should be called only once per stream", which matches the once-per-stream allocation in [`sdw_alloc_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874) and closes the lifecycle. The [`SDW_STREAM_RELEASED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L933) value [`sdw_stream_remove_master()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L2078) wrote is the last state the runtime holds before [`kfree()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L513) reclaims it, so RELEASED is observable only on the brief window between the final manager removal and the release.

### State sequence and re-entry edges of the stream runtime

The [`enum sdw_stream_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L926) field of a [`struct sdw_stream_runtime`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L961) advances from [`sdw_alloc_stream()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/stream.c#L1874) through the configure, prepare, enable, disable, and de-prepare transitions to release, with underrun and resume paths re-entering from DISABLED or DEPREPARED.

```
    SoundWire stream state machine (enum sdw_stream_state)
    ──────────────────────────────────────────────────────

      sdw_alloc_stream()
            ▼
    ┌────────────────┐
    │   ALLOCATED    │  state = 0, master_list empty
    └───────┬────────┘
            ▼  sdw_stream_add_slave() / sdw_stream_add_master()
    ┌────────────────┐
    │   CONFIGURED   │  state = 1, runtimes + ports linked
    └───────┬────────┘
            ▼  sdw_prepare_stream()  (port prepare + bank switch)
    ┌────────────────┐
    │    PREPARED    │  state = 2
    └───────┬────────┘
            ▼  sdw_enable_stream()   (channel enable + bank switch)
    ┌────────────────┐
    │    ENABLED     │  state = 3  ◀── running stream
    └───────┬────────┘
            ▼  sdw_disable_stream()  (channel disable + bank switch)
    ┌────────────────┐
    │    DISABLED    │  state = 4
    └───────┬────────┘
            ▼  sdw_deprepare_stream()  (port de-prepare + bank switch)
    ┌────────────────┐
    │   DEPREPARED   │  state = 5
    └───────┬────────┘
            ▼  sdw_release_stream()
    ┌────────────────┐
    │    RELEASED    │  state = 6, runtime freed
    └────────────────┘

    re-entry edges (underrun / resume / restart):
      DISABLED   ──sdw_prepare_stream()──▶ PREPARED
      DISABLED   ──sdw_enable_stream()───▶ ENABLED
      DEPREPARED ──sdw_prepare_stream()──▶ PREPARED
```
