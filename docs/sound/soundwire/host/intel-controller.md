# Intel SoundWire controller

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

On an x86-64 Intel platform the SoundWire links are blocks inside the audio DSP, and the SOF (Sound Open Firmware) driver brings the controller up by scanning ACPI for the SoundWire node, copying the firmware-reported link mask into a [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), and handing it to [`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333), a thin wrapper over [`sdw_intel_probe_controller()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L156); that controller probe loops over every set bit in [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) and creates one auxiliary device per enabled link through [`intel_link_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L32), so the controller is not one device but a set of per-link auxiliary devices sharing a single [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303). Each aux device binds to the auxiliary driver [`sdw_intel_drv`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L860), whose probe [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) allocates a [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) wrapping a Cadence IP master [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124), sets [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029) to [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281), and adds the SoundWire bus with [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42); a later [`intel_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377) powers the link and registers the CPU DAIs through [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024).

```
    SOF audio DSP (sound/soc/sof/intel/hda.c)
    ┌──────────────────────────────────────────────────────────┐
    │  struct sdw_intel_res res                                │
    │  res.hw_ops = &sdw_intel_lnl_hw_ops  (ACE 2.x)           │
    │  res.link_mask  res.count   sdw_intel_probe(&res)        │
    └──────────────────────────────────────┬───────────────────┘
                                           │ one aux device per set link bit
              ┌──────────┬─────────────────┼─────────────────┐
              ▼          ▼                 ▼                 ▼
         ┌─────────┐ ┌─────────┐      ┌─────────┐       ┌─────────┐
         │ link.0  │ │ link.1  │      │ link.2  │       │ link.3  │
         │ auxdev  │ │ auxdev  │      │ auxdev  │       │ auxdev  │
         └────┬────┘ └─────────┘      └─────────┘       └─────────┘
              │  intel_link_probe / intel_link_startup
              ▼
         struct sdw_intel        ┌── struct sdw_cdns  (Cadence IP master)
         ┌────────────────────┐  │   ┌────────────────────────────┐
         │ cdns ──────────────┼──┘   │ struct sdw_bus bus         │
         │ link_res           │      │ pcm  (PDI capability)      │
         │ instance           │      │ dai_runtime_array          │
         └────────────────────┘      └─────────────┬──────────────┘
                                                   │ intel_register_dai
                                                   ▼
                                     SDWn PinM CPU DAIs  (ASoC component)
```

## SUMMARY

The Intel SoundWire controller is the integration layer that turns the SoundWire IP inside an Intel audio DSP into a SoundWire bus per link and a set of ASoC CPU DAIs. Bring-up runs in three software stages. The SOF driver supplies the resource description and triggers bring-up, the controller init code in [`intel_init.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c) creates one auxiliary device per enabled link, and the per-link auxiliary driver in [`intel_auxdevice.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c) wraps a Cadence IP master and adds its bus.

Discovery happens before any device is created. [`sdw_intel_acpi_scan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L180) walks the ACPI namespace under the HDAS scope to find the SoundWire (SNDW) device, then [`sdw_intel_scan_controller()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L56) reads the `mipi-sdw-manager-list` or `mipi-sdw-master-count` firmware property to learn how many links exist and which the BIOS enables, filling a [`struct sdw_intel_acpi_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241) with the [`handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241), [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241), and [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241). SOF caches that in its private data through [`hda_sdw_acpi_scan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L137) and copies it into the resource at probe time.

The entry point is [`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333), called from [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159) in the SOF Intel HDA code. It forwards to [`sdw_intel_probe_controller()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L156), which allocates a [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) and its [`ldev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) pointer array, then for every bit set in [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) calls [`intel_link_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L32) to init and add one [`struct sdw_intel_link_dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11) named `soundwire_intel.link.N`. The link-specific resources (register base, SHIM base, IP offset, [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31)) are written into the embedded [`struct sdw_intel_link_res`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31). Adding the device triggers a match against [`sdw_intel_drv`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L860), registered with [`module_auxiliary_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L286).

The auxiliary driver probe [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) allocates a [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) whose first member is a [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124), wires the Cadence IP register pointers from the link resources, runs [`sdw_cdns_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1817), sets the bus ops to [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281) and [`bus->compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1037) to [`sdw_compute_params()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/generic_bandwidth_allocation.c#L666), and calls [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) to register the SoundWire master and enumerate its peripherals from ACPI. The enumeration that [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) performs, reading the `_ADR` of each ACPI child and registering a [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) on the bus, is the subject of the SoundWire bus and device model page and is not re-derived here.

After the DSP firmware is loaded, [`sdw_intel_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L346) is called and forwards to [`sdw_intel_startup_controller()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L284), which walks the same set of enabled links and calls [`intel_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377) on each aux device. That function powers the SHIM and controller through [`sdw_intel_link_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L198), registers DAIs through [`sdw_intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157), and starts the bus through [`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170). Each of those is an inline dispatcher that reaches the per-version function pointer struct through the [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135) macro, dereferencing [`link_res->hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31). On Meteor Lake and Lunar Lake (ACE 2.x) that struct is [`sdw_intel_lnl_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109), whose [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) member is [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024). The body of that DAI registration, the PDI (Physical Data Interface) capability read, and the ACE 2.x hw_ops are owned by the Intel CPU DAI page; this page stops at the [`sdw_intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157) handoff.

## SPECIFICATIONS

The SoundWire bus is defined by the MIPI Alliance SoundWire (Serial Low-power Inter-chip Media Bus) specification, which the kernel SoundWire core implements; that specification is membership-gated and is described here only from the kernel source. The SoundWire master block licensed into the Intel audio DSP is the Cadence SoundWire IP, wrapped by [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) and reached through [`sdw_cdns_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1817); its register layout is encoded in the offset macros in [`include/linux/soundwire/sdw_intel.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h) and [`cadence_master.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h). The auxiliary device model that carries each link is a Linux kernel software construct with no hardware specification, defined in [`include/linux/auxiliary_bus.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h). The firmware-side description of which links exist is reported through ACPI on x86-64, read by [`sdw_intel_scan_controller()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L56) from the `mipi-sdw-manager-list` and `mipi-sdw-master-count` device properties.

## LINUX KERNEL

### Controller init and per-link aux devices (intel_init.c)

- [`'\<sdw_intel_probe\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333): exported entry point called by SOF; forwards its [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) to the controller probe and returns a [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303)
- [`'\<sdw_intel_probe_controller\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L156): allocate the [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) and the [`ldev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) array, create one aux device per set bit in [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303), and collect the enumerated peripherals into [`peripherals`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303)
- [`'\<intel_link_dev_register\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L32): allocate a [`struct sdw_intel_link_dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11), fill its embedded [`struct sdw_intel_link_res`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31), then run [`auxiliary_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L220) and [`auxiliary_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L222) for one link
- [`'\<intel_link_dev_unregister\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L113): [`auxiliary_device_delete()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L223) then [`auxiliary_device_uninit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L221), the two-step teardown of one link
- [`'\<intel_link_dev_release\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L23): the aux-device `release` callback that frees the [`struct sdw_intel_link_dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11) once the last reference drops
- [`'\<sdw_intel_startup\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L346): exported startup, called after the DSP is powered; forwards to the controller startup
- [`'\<sdw_intel_startup_controller\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L284): walk the enabled links and call [`intel_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377) for each aux device
- [`'\<sdw_intel_process_wakeen_event\>':'drivers/soundwire/intel_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L379): walk the links to service an in-band wake reported by the SHIM, calling [`intel_link_process_wakeen_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L508) per link

### Per-link auxiliary driver (intel_auxdevice.c)

- [`'sdw_intel_drv':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L860): the [`struct auxiliary_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L189) bound to every `soundwire_intel.link` aux device; registered with [`module_auxiliary_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L286)
- [`'intel_link_id_table':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L854): the [`struct auxiliary_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L968) table matching the `soundwire_intel.link` name
- [`'\<intel_link_probe\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301): allocate [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75), wire the Cadence IP pointers, check the hardware link count, set [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029) to [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281), and call [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42)
- [`'\<intel_link_startup\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377): power the link, register DAIs, enable runtime PM, and start the bus
- [`'\<intel_link_remove\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L489): tear the link down and call [`sdw_bus_master_delete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L196)
- [`'sdw_intel_ops':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281): the [`struct sdw_master_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) the SoundWire core uses to read properties and transfer command/control messages on the link
- [`'\<intel_link_process_wakeen_event\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L508): per-link half of the wake handling, resuming the master after an in-band wake

### Context and resource types

- [`'\<struct sdw_intel\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75): the per-link controller object; first member is the Cadence context [`cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75), so [`cdns_to_intel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L127) recovers it from a Cadence pointer
- [`'\<struct sdw_intel_link_res\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31): the link resources the controller fills, including [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31), the [`registers`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) and [`shim`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) bases, the [`ip_offset`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31), and the [`cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) back pointer
- [`'\<struct sdw_intel_ctx\>':'include/linux/soundwire/sdw_intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303): the controller context returned to SOF; holds the [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303), the [`ldev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) array, the [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303), the [`link_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303), and the enumerated [`peripherals`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303)
- [`'\<struct sdw_intel_res\>':'include/linux/soundwire/sdw_intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342): the resource description SOF populates, including [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), [`mmio_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), [`handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), and the [`ext`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) flag distinguishing ACE 2.x
- [`'\<struct sdw_intel_acpi_info\>':'include/linux/soundwire/sdw_intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241): the ACPI-scan result with the controller [`handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241), the [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241), and the BIOS-enabled [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241)
- [`'\<struct sdw_intel_link_dev\>':'drivers/soundwire/intel_auxdevice.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11): a [`struct auxiliary_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L142) with the [`struct sdw_intel_link_res`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) inlined behind it
- [`'\<struct sdw_intel_hw_ops\>':'include/linux/soundwire/sdw_intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415): the version-specific function pointer struct selected per platform; ACE 2.x uses [`sdw_intel_lnl_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109)
- [`'\<struct sdw_peripherals\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L488): the flat array of every [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) enumerated across all enabled links, built at the end of the controller probe

### Dispatch and bus helpers (intel.h, bus.c)

- [`'\<sdw_intel_register_dai\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157): inline dispatcher that runs the [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) op through [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135)
- [`'\<sdw_intel_link_power_up\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L198) / [`'\<sdw_intel_start_bus\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170): inline dispatchers for the [`link_power_up`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) and [`start_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) ops
- [`'\<sdw_intel_get_link_count\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L252): read the hardware link count, returning 4 on generations without the op
- [`'\<SDW_INTEL_OPS\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135) / [`'\<SDW_INTEL_CHECK_OPS\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L133): macros that reach and null-check [`link_res->hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31)
- [`'\<cdns_to_intel\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L127): [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) wrapper from the Cadence context to the enclosing [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75)
- [`'\<sdw_bus_master_add\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42): SoundWire core call that registers the [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698), reads master properties, seeds the device-number bitmap, and creates the peripheral devices from firmware
- [`'\<sdw_master_device_add\>':'drivers/soundwire/master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/master.c#L127): register the controller's Linux device and set [`bus->dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`bus->md`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014)
- [`'\<sdw_compute_params\>':'drivers/soundwire/generic_bandwidth_allocation.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/generic_bandwidth_allocation.c#L666): the generic bandwidth allocator the Intel link sets as [`bus->compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1037)

### Cadence IP master and register offsets (cadence_master.*, sdw_intel.h)

- [`'\<struct sdw_cdns\>':'drivers/soundwire/cadence_master.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124): the Cadence driver context, holding the [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) [`bus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124), the [`registers`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) base, the [`ip_offset`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124), the [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) PDI streams, and the [`dai_runtime_array`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124)
- [`'\<sdw_cdns_probe\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1817): init the Cadence completion, port ops, status work, and attach work
- [`SDW_IP_BASE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L122): per-link Cadence IP register base `0x00030100 + 0x8000 * link`, used on the ACE 2.x path
- [`SDW_SHIM2_GENERIC_BASE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L121) / [`SDW_SHIM2_VS_BASE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L123): per-link SHIM2 generic and vendor-specific bases for ACE 2.x
- [`SDW_CADENCE_MCP_IP_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L18): the `0x4000` offset to the MCP IP register window, written into [`cdns->ip_offset`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) on ACE 2.x

### SOF integration and ACPI scan (sound/soc/sof/intel/hda.c, sound/hda/core/intel-sdw-acpi.c)

- [`'\<hda_sdw_acpi_scan\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L137): resolve the DSP's ACPI handle and call [`sdw_intel_acpi_scan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L180), saving the result for the probe step
- [`'\<hda_sdw_probe\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159): build the [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), choose the [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) by hardware version, and call [`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333)
- [`'\<hda_sdw_startup\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L231): call [`sdw_intel_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L346) once the audio DSP is up
- [`'\<sdw_intel_acpi_scan\>':'sound/hda/core/intel-sdw-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L180): walk the namespace under the HDAS scope to find the SNDW device, then run [`sdw_intel_scan_controller()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L56)
- [`'\<sdw_intel_scan_controller\>':'sound/hda/core/intel-sdw-acpi.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L56): read the firmware link-count and link-mask properties and fill the [`struct sdw_intel_acpi_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241)

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus model, the master/slave roles, and the dev_id and link_id scoping a controller exposes
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the CPU DAI joins as the master endpoint from its hw_params op
- [`Documentation/driver-api/soundwire/locking.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/locking.rst): the bus and message locking the Cadence master and the shared SHIM registers rely on
- [`Documentation/driver-api/soundwire/error_handling.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/error_handling.rst): how command/control errors on the link are reported, relevant to the [`err_threshold`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1031) the Intel link forces to zero
- [`Documentation/firmware-guide/acpi/enumeration.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/firmware-guide/acpi/enumeration.rst): how a bus device is described and enumerated from the ACPI namespace on x86

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The SOF driver communicates with the Intel SoundWire controller through three exported functions and one resource struct, and the controller in turn communicates with each link through the per-version [`struct sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) function pointer struct. The boundary is narrow so that the same SOF code drives every SoundWire-capable Intel DSP regardless of the audio-controller-engine (ACE) version. The objects below have one creator each, so a reader can follow a link from the firmware scan to a live aux device and then to its Cadence master and bus.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct sdw_intel_acpi_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241) | filled by [`sdw_intel_scan_controller()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L56) | embedded in SOF private data |
| [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) | stack-built by [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159) | one [`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333) call |
| [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) | [`sdw_intel_probe_controller()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L156) | from probe to controller removal |
| [`struct sdw_intel_link_dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11) | [`intel_link_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L32) | one enabled link |
| [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) | [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) | the aux device (devm) |
| [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) | embedded in [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124), set up by [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) | the link |

### sdw_intel_probe and sdw_intel_startup

[`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333) takes a fully-populated [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) and returns a [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) that SOF stores opaquely. The split between probe (device creation) and startup (power-on and bus start) exists because the SoundWire IP cannot be brought up until the audio DSP firmware is loaded and running, which happens between the two calls. [`sdw_intel_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L346) takes the same context back and starts every link.

### SDW_INTEL_OPS dispatch

Inside a link, every hardware action is reached through [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135), guarded by [`SDW_INTEL_CHECK_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L133), so the link code never names an ACE-version function directly. A new hardware generation supplies a new [`struct sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) and SOF points [`res.hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) at it; the dispatchers in [`intel.h`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h) then route to it with no change to the auxiliary driver.

### sdw_master_ops and the SoundWire bus

The SoundWire core reaches the Cadence master through [`sdw_intel_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L281), a [`struct sdw_master_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L861) set on [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029) in [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301). This is the interface for reading master properties and transferring command/control messages, distinct from the [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) that drive power and synchronization.

## DETAILS

### SOF discovers the controller in ACPI

Discovery runs before any device is created. [`hda_sdw_acpi_scan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L137) resolves the DSP's ACPI handle with [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) and passes it to [`sdw_intel_acpi_scan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L180), saving the result in SOF's private data for the later probe step:

```c
/* sound/soc/sof/intel/hda.c:137 */
static int hda_sdw_acpi_scan(struct snd_sof_dev *sdev)
{
	u32 interface_mask = hda_get_interface_mask(sdev);
	struct sof_intel_hda_dev *hdev;
	acpi_handle handle;
	int ret;

	if (!(interface_mask & BIT(SOF_DAI_INTEL_ALH)))
		return -EINVAL;

	handle = ACPI_HANDLE(sdev->dev);

	/* save ACPI info for the probe step */
	hdev = sdev->pdata->hw_pdata;

	ret = sdw_intel_acpi_scan(handle, &hdev->info);
	if (ret < 0)
		return -EINVAL;

	return 0;
}
```

[`sdw_intel_acpi_scan()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L180) walks the namespace from the HDAS scope to a maximum depth of 2 to locate the SNDW device, because the SoundWire node may be either a child or a grandchild of HDAS. The per-node callback matches the SoundWire controller by the high `_ADR` bits, and the walk stops once it is found:

```c
/* sound/hda/core/intel-sdw-acpi.c:180 */
int sdw_intel_acpi_scan(acpi_handle parent_handle,
			struct sdw_intel_acpi_info *info)
{
	acpi_status status;

	info->handle = NULL;
	/*
	 * In the HDAS ACPI scope, 'SNDW' may be either the child of
	 * 'HDAS' or the grandchild of 'HDAS'. So let's go through
	 * the ACPI from 'HDAS' at max depth of 2 to find the 'SNDW'
	 * device.
	 */
	status = acpi_walk_namespace(ACPI_TYPE_DEVICE,
				     parent_handle, 2,
				     sdw_intel_acpi_cb,
				     NULL, info, NULL);
	if (ACPI_FAILURE(status) || info->handle == NULL)
		return -ENODEV;

	return sdw_intel_scan_controller(info);
}
```

Once the controller handle is known, [`sdw_intel_scan_controller()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/intel-sdw-acpi.c#L56) reads the link inventory from firmware properties on the SoundWire node, preferring the `mipi-sdw-manager-list` bitmask and falling back to `mipi-sdw-master-count`. According to the comment, the hardware link count cannot be checked at this point because the SoundWire IP is not yet powered, so the scan trusts the firmware properties and defers the hardware check to startup:

```c
/* sound/hda/core/intel-sdw-acpi.c:56 */
static int
sdw_intel_scan_controller(struct sdw_intel_acpi_info *info)
{
	struct acpi_device *adev = acpi_fetch_acpi_dev(info->handle);
	struct fwnode_handle *fwnode;
	unsigned long list;
	unsigned int i;
	u32 count;
	u32 tmp;
	int ret;
	...
	fwnode = acpi_fwnode_handle(adev);
	...
	ret = fwnode_property_read_u32(fwnode, "mipi-sdw-manager-list", &tmp);
	if (ret) {
		ret = fwnode_property_read_u32(fwnode, "mipi-sdw-master-count", &count);
		...
		list = GENMASK(count - 1, 0);
	} else {
		list = tmp;
		count = hweight32(list);
	}
	...
	info->count = count;
	info->link_mask = 0;

	for_each_set_bit(i, &list, SDW_INTEL_MAX_LINKS) {
		if (ctrl_link_mask && !(ctrl_link_mask & BIT(i))) {
			...
			continue;
		}
		if (!is_link_enabled(fwnode, i)) {
			...
			continue;
		}
		info->link_mask |= BIT(i);
	}

	return 0;
}
```

The resulting [`struct sdw_intel_acpi_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L241) carries only the three values the controller probe needs, the controller handle plus the count and the BIOS-enabled mask:

```c
/* include/linux/soundwire/sdw_intel.h:241 */
struct sdw_intel_acpi_info {
	acpi_handle handle;
	int count;
	u32 link_mask;
};
```

### SOF builds the resource description and starts the controller

The integration begins in the SOF Intel HDA driver. [`hda_sdw_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L159) zeroes a [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) on its stack, selects the function pointer struct by hardware version, copies the firmware-reported link count and mask out of the saved scan result, and calls [`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333):

```c
/* sound/soc/sof/intel/hda.c:159 */
static int hda_sdw_probe(struct snd_sof_dev *sdev)
{
	const struct sof_intel_dsp_desc *chip;
	struct sof_intel_hda_dev *hdev;
	struct sdw_intel_res res;
	void *sdw;

	hdev = sdev->pdata->hw_pdata;

	memset(&res, 0, sizeof(res));

	chip = get_chip_info(sdev->pdata);
	if (chip->hw_ip_version < SOF_INTEL_ACE_2_0) {
		res.mmio_base = sdev->bar[HDA_DSP_BAR];
		res.hw_ops = &sdw_intel_cnl_hw_ops;
		res.shim_base = hdev->desc->sdw_shim_base;
		res.alh_base = hdev->desc->sdw_alh_base;
		res.ext = false;
		res.ops = &sdw_callback;
	} else {
		/*
		 * retrieve eml_lock needed to protect shared registers
		 * in the HDaudio multi-link areas
		 */
		res.eml_lock = hdac_bus_eml_get_mutex(sof_to_bus(sdev), true,
						      AZX_REG_ML_LEPTR_ID_SDW);
		if (!res.eml_lock)
			return -ENODEV;

		res.mmio_base = sdev->bar[HDA_DSP_HDA_BAR];
		/*
		 * the SHIM and SoundWire register offsets are link-specific
		 * and will be determined when adding auxiliary devices
		 */
		res.hw_ops = &sdw_intel_lnl_hw_ops;
		res.ext = true;
		res.ops = &sdw_ace2x_callback;

		/* ACE3+ supports microphone privacy */
		if (chip->hw_ip_version >= SOF_INTEL_ACE_3_0)
			res.mic_privacy = true;
	}
	res.irq = sdev->ipc_irq;
	res.handle = hdev->info.handle;
	res.parent = sdev->dev;
	...
	/* we could filter links here if needed, e.g for quirks */
	res.count = hdev->info.count;
	res.link_mask = hdev->info.link_mask;

	sdw = sdw_intel_probe(&res);
	if (!sdw) {
		dev_err(sdev->dev, "error: SoundWire probe failed\n");
		return -EINVAL;
	}

	/* save context */
	hdev->sdw = sdw;

	return 0;
}
```

According to the comment on the ACE 2.x branch, the SHIM and SoundWire register offsets are link-specific and will be determined when adding auxiliary devices, so for Meteor Lake and Lunar Lake SOF passes only the single [`mmio_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) and the [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) pointer, and the controller computes the per-link bases later. The [`handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), and [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) come straight from the ACPI scan result in [`hdev->info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h). The returned pointer is cached opaquely in [`hdev->sdw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h); it is actually a [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303).

The resource struct SOF fills is the full global description of the controller, with the [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) abstraction, the [`mmio_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), the ACPI [`handle`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), the [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342), and the [`ext`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) flag that selects the ACE 2.x base-address layout:

```c
/* include/linux/soundwire/sdw_intel.h:342 */
struct sdw_intel_res {
	const struct sdw_intel_hw_ops *hw_ops;
	int count;
	void __iomem *mmio_base;
	int irq;
	acpi_handle handle;
	struct device *parent;
	const struct sdw_intel_ops *ops;
	struct device *dev;
	u32 link_mask;
	u32 clock_stop_quirks;
	u32 shim_base;
	u32 alh_base;
	bool ext;
	bool mic_privacy;
	struct hdac_bus *hbus;
	struct mutex *eml_lock;
};
```

The startup half runs later, after the DSP firmware is up, and simply forwards the saved context:

```c
/* sound/soc/sof/intel/hda.c:231 */
int hda_sdw_startup(struct snd_sof_dev *sdev)
{
	struct sof_intel_hda_dev *hdev;
	...
	if (!hdev->sdw)
		return 0;
	...
	return sdw_intel_startup(hdev->sdw);
}
```

### sdw_intel_probe and sdw_intel_startup are thin wrappers

Neither exported entry point does work directly; each forwards to a static function in the same file, which keeps the exported symbol stable while the implementation behind it can change:

```c
/* drivers/soundwire/intel_init.c:333 */
struct sdw_intel_ctx
*sdw_intel_probe(struct sdw_intel_res *res)
{
	return sdw_intel_probe_controller(res);
}
```

```c
/* drivers/soundwire/intel_init.c:346 */
int sdw_intel_startup(struct sdw_intel_ctx *ctx)
{
	return sdw_intel_startup_controller(ctx);
}
```

### The controller creates one auxiliary device per link

[`sdw_intel_probe_controller()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L156) is where the controller takes shape. It fetches the ACPI device from the handle, allocates the [`struct sdw_intel_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) and its [`ldev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) pointer array, copies the SHIM and ALH bases, and then loops over the [`count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) links creating one aux device for each bit set in [`link_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303):

```c
/* drivers/soundwire/intel_init.c:156 */
static struct sdw_intel_ctx
*sdw_intel_probe_controller(struct sdw_intel_res *res)
{
	struct sdw_intel_link_res *link;
	struct sdw_intel_link_dev *ldev;
	struct sdw_intel_ctx *ctx;
	struct acpi_device *adev;
	...
	u32 link_mask;
	int num_slaves = 0;
	int count;
	int i;

	if (!res)
		return NULL;

	adev = acpi_fetch_acpi_dev(res->handle);
	if (!adev)
		return NULL;
	...
	count = res->count;
	dev_dbg(&adev->dev, "Creating %d SDW Link devices\n", count);
	...
	ctx->mmio_base = res->mmio_base;
	ctx->shim_base = res->shim_base;
	ctx->alh_base = res->alh_base;
	ctx->link_mask = res->link_mask;
	ctx->handle = res->handle;
	mutex_init(&ctx->shim_lock);

	link_mask = ctx->link_mask;

	INIT_LIST_HEAD(&ctx->link_list);

	for (i = 0; i < count; i++) {
		if (!(link_mask & BIT(i)))
			continue;

		/*
		 * init and add a device for each link
		 *
		 * The name of the device will be soundwire_intel.link.[i],
		 * with the "soundwire_intel" module prefix automatically added
		 * by the auxiliary bus core.
		 */
		ldev = intel_link_dev_register(res,
					       ctx,
					       acpi_fwnode_handle(adev),
					       "link",
					       i);
		if (IS_ERR(ldev))
			goto err;

		link = &ldev->link_res;
		link->cdns = auxiliary_get_drvdata(&ldev->auxdev);
		...
		list_add_tail(&link->list, &ctx->link_list);
		bus = &link->cdns->bus;
		/* Calculate number of slaves */
		list_for_each(node, &bus->slaves)
			num_slaves++;
	}
	...
	return ctx;
```

According to the comment in the loop, the name of each device is `soundwire_intel.link.[i]`, with the `soundwire_intel` module prefix automatically added by the auxiliary bus core. Because [`intel_link_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L32) both initializes and adds the aux device, the matching auxiliary driver has already probed by the time the call returns, so [`link->cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) can be read straight back with [`auxiliary_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L200) (the Cadence pointer [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) set), and the loop can immediately count the peripherals the bus enumerated by walking [`bus->slaves`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014). After the loop, a second pass copies every peripheral across all links into a flat [`struct sdw_peripherals`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L488) array hung off [`ctx->peripherals`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303).

The context the probe returns is the controller's only persistent state, and it owns the per-link device array rather than a single device:

```c
/* include/linux/soundwire/sdw_intel.h:303 */
struct sdw_intel_ctx {
	int count;
	void __iomem *mmio_base;
	u32 link_mask;
	acpi_handle handle;
	struct sdw_intel_link_dev **ldev;
	struct list_head link_list;
	struct mutex shim_lock; /* lock for access to shared SHIM registers */
	u32 shim_mask;
	u32 shim_base;
	u32 alh_base;
	struct sdw_peripherals *peripherals;
};
```

The [`ldev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303) array is indexed by link id, with a NULL slot for every disabled link, so the startup and wake passes can reuse the same `link_mask & BIT(i)` test to skip holes. According to the comment in the probe, the number of links is small, so an indexed array is simpler than a list for tracking which links are present.

### intel_link_dev_register fills the link resources and adds the device

For each enabled link, [`intel_link_dev_register()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L32) allocates a [`struct sdw_intel_link_dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11), sets the aux-device name, id, parent, and release callback, records the pointer in [`ctx->ldev[link_id]`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L303), and then fills the embedded [`struct sdw_intel_link_res`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) with the per-link register windows. The ACE 2.x path is the [`res->ext`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) branch, which derives the link IP base, the IP offset, and the two SHIM2 windows from the link id:

```c
/* drivers/soundwire/intel_init.c:32 */
static struct sdw_intel_link_dev *intel_link_dev_register(struct sdw_intel_res *res,
							  struct sdw_intel_ctx *ctx,
							  struct fwnode_handle *fwnode,
							  const char *name,
							  int link_id)
{
	struct sdw_intel_link_dev *ldev;
	struct sdw_intel_link_res *link;
	struct auxiliary_device *auxdev;
	int ret;

	ldev = kzalloc_obj(*ldev);
	if (!ldev)
		return ERR_PTR(-ENOMEM);

	auxdev = &ldev->auxdev;
	auxdev->name = name;
	auxdev->dev.parent = res->parent;
	auxdev->dev.fwnode = fwnode;
	auxdev->dev.release = intel_link_dev_release;

	/* we don't use an IDA since we already have a link ID */
	auxdev->id = link_id;
	...
	ctx->ldev[link_id] = ldev;

	/* Add link information used in the driver probe */
	link = &ldev->link_res;
	link->hw_ops = res->hw_ops;
	link->mmio_base = res->mmio_base;
	if (!res->ext) {
		link->registers = res->mmio_base + SDW_LINK_BASE
			+ (SDW_LINK_SIZE * link_id);
		link->ip_offset = 0;
		link->shim = res->mmio_base + res->shim_base;
		link->alh = res->mmio_base + res->alh_base;
		link->shim_lock = &ctx->shim_lock;
	} else {
		link->registers = res->mmio_base + SDW_IP_BASE(link_id);
		link->ip_offset = SDW_CADENCE_MCP_IP_OFFSET;
		link->shim = res->mmio_base +  SDW_SHIM2_GENERIC_BASE(link_id);
		link->shim_vs = res->mmio_base + SDW_SHIM2_VS_BASE(link_id);
		link->shim_lock = res->eml_lock;
		link->mic_privacy = res->mic_privacy;
	}

	link->ops = res->ops;
	link->dev = res->dev;
	...
	link->shim_mask = &ctx->shim_mask;
	link->link_mask = ctx->link_mask;

	link->hbus = res->hbus;

	/* now follow the two-step init/add sequence */
	ret = auxiliary_device_init(auxdev);
	...
	ret = auxiliary_device_add(&ldev->auxdev);
	...
	return ldev;
}
```

The two base macros for ACE 2.x stride by `0x8000` per link, so each link gets a disjoint register window without any per-link table. [`SDW_IP_BASE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L122) places the Cadence IP registers and [`SDW_SHIM2_GENERIC_BASE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L121) the SHIM2 generic block:

```c
/* include/linux/soundwire/sdw_intel.h:121 */
#define SDW_SHIM2_GENERIC_BASE(x)	(0x00030000 + 0x8000 * (x))
#define SDW_IP_BASE(x)			(0x00030100 + 0x8000 * (x))
#define SDW_SHIM2_VS_BASE(x)		(0x00036000 + 0x8000 * (x))
```

According to the comment, the function follows the two-step init/add sequence the auxiliary bus requires. [`auxiliary_device_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L220) performs the [`device_initialize()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/core.c#L3156) and validates the struct, and [`auxiliary_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L222) sets the device name and places it on the bus, which is what triggers the driver match against [`sdw_intel_drv`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L860). Each link's [`hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) is copied from the resource, so every link descends from the same SOF-chosen ACE 2.x function pointer struct.

The structure the function fills is a [`struct auxiliary_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L142) with the link resources inlined directly behind it, so a [`container_of()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/container_of.h#L19) from the aux device reaches the resources:

```c
/* drivers/soundwire/intel_auxdevice.h:11 */
struct sdw_intel_link_dev {
	struct auxiliary_device auxdev;
	struct sdw_intel_link_res link_res;
};
```

The link resources hold the hardware window and the function pointer struct, and the [`cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31) back pointer the controller loop reads once the aux device probes:

```c
/* drivers/soundwire/intel.h:31 */
struct sdw_intel_link_res {
	const struct sdw_intel_hw_ops *hw_ops;

	void __iomem *mmio_base; /* not strictly needed, useful for debug */
	void __iomem *registers;
	u32 ip_offset;
	void __iomem *shim;
	void __iomem *shim_vs;
	void __iomem *alh;
	int irq;
	const struct sdw_intel_ops *ops;
	struct device *dev;
	struct mutex *shim_lock; /* protect shared registers */
	u32 *shim_mask;
	u32 clock_stop_quirks;
	bool mic_privacy;
	u32 link_mask;
	struct sdw_cdns *cdns;
	struct list_head list;
	struct hdac_bus *hbus;
};
```

On the ext branch each window field takes its own base macro keyed to the link id, the SHIM and IP windows striding 0x8000 apart and ip_offset a fixed 0x4000 reach into the MCP IP:

```
    ACE 2.x per-link register windows  (res->ext branch)
    ─────────────────────────────────────────────────────

    mmio_base + a per-link base; each link x strides by 0x8000

    ┌───────────────────────────────────────────────────────────┐
    │ link_res field   base macro (offset for link x)           │
    ├───────────────────────────────────────────────────────────┤
    │ shim             SDW_SHIM2_GENERIC_BASE  0x30000+0x8000*x │
    │ registers        SDW_IP_BASE             0x30100+0x8000*x │
    │ shim_vs          SDW_SHIM2_VS_BASE       0x36000+0x8000*x │
    └───────────────────────────────────────────────────────────┘

    ip_offset = SDW_CADENCE_MCP_IP_OFFSET (0x4000) into the MCP IP
```

### The auxiliary driver binds the per-link aux device

The driver that every `soundwire_intel.link` aux device binds to names the probe, the remove, and a PM block, and its [`id_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L189) matches the `soundwire_intel.link` name:

```c
/* drivers/soundwire/intel_auxdevice.c:854 */
static const struct auxiliary_device_id intel_link_id_table[] = {
	{ .name = "soundwire_intel.link" },
	{},
};
MODULE_DEVICE_TABLE(auxiliary, intel_link_id_table);

static struct auxiliary_driver sdw_intel_drv = {
	.probe = intel_link_probe,
	.remove = intel_link_remove,
	.driver = {
		/* auxiliary_driver_register() sets .name to be the modname */
		.pm = &intel_pm,
	},
	.id_table = intel_link_id_table
};
module_auxiliary_driver(sdw_intel_drv);
```

[`module_auxiliary_driver()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L286) expands to the module init/exit that registers and unregisters the driver. Because the registering side (the controller in [`intel_init.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c)) and the binding side (this driver) are built into the same module, the per-link aux device is created and consumed within one driver load.

### intel_link_probe wraps a Cadence IP master

[`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) is the per-link constructor. It allocates a [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/devres.c#L692), takes the address of its first member as the [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124), copies the link resources into the Cadence IP register pointers, checks the firmware link count against hardware with [`sdw_intel_get_link_count()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L252), runs [`sdw_cdns_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1817), sets the bus ops and the bandwidth allocator, and then registers the SoundWire master:

```c
/* drivers/soundwire/intel_auxdevice.c:301 */
static int intel_link_probe(struct auxiliary_device *auxdev,
			    const struct auxiliary_device_id *aux_dev_id)

{
	struct device *dev = &auxdev->dev;
	struct sdw_intel_link_dev *ldev = auxiliary_dev_to_sdw_intel_link_dev(auxdev);
	struct sdw_intel *sdw;
	struct sdw_cdns *cdns;
	struct sdw_bus *bus;
	int ret;

	sdw = devm_kzalloc(dev, sizeof(*sdw), GFP_KERNEL);
	if (!sdw)
		return -ENOMEM;

	cdns = &sdw->cdns;
	bus = &cdns->bus;

	sdw->instance = auxdev->id;
	sdw->link_res = &ldev->link_res;
	cdns->dev = dev;
	cdns->registers = sdw->link_res->registers;
	cdns->ip_offset = sdw->link_res->ip_offset;
	cdns->instance = sdw->instance;
	cdns->msg_count = 0;

	/* single controller for all SoundWire links */
	bus->controller_id = 0;

	bus->link_id = auxdev->id;
	bus->clk_stop_timeout = 1;

	/*
	 * paranoia check: make sure ACPI-reported number of links is aligned with
	 * hardware capabilities.
	 */
	ret = sdw_intel_get_link_count(sdw);
	if (ret < 0) {
		dev_err(dev, "%s: sdw_intel_get_link_count failed: %d\n", __func__, ret);
		return ret;
	}
	if (ret <= sdw->instance) {
		dev_err(dev, "%s: invalid link id %d, link count %d\n", __func__, auxdev->id, ret);
		return -EINVAL;
	}

	sdw_cdns_probe(cdns);

	/* Set ops */
	bus->ops = &sdw_intel_ops;

	/* set driver data, accessed by snd_soc_dai_get_drvdata() */
	auxiliary_set_drvdata(auxdev, cdns);

	/* use generic bandwidth allocation algorithm */
	sdw->cdns.bus.compute_params = sdw_compute_params;

	ret = sdw_bus_master_add(bus, dev, dev->fwnode);
	if (ret) {
		dev_err(dev, "sdw_bus_master_add fail: %d\n", ret);
		return ret;
	}
	...
	/*
	 * Ignore BIOS err_threshold, it's a really bad idea when dealing
	 * with multiple hardware synchronized links
	 */
	bus->prop.err_threshold = 0;

	return 0;
}
```

According to the comment, there is a single controller for all SoundWire links, so every link sets [`bus->controller_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1034) to 0 while its [`bus->link_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1035) is the aux device id. The paranoia check rejects a link id the hardware does not actually expose, with [`sdw_intel_get_link_count()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L252) returning the hardware count from the [`get_link_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) op or a default of 4. The driver data set with [`auxiliary_set_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L205) is the Cadence context, which is what the controller loop reads back and what the CPU DAI ops later recover through [`snd_soc_dai_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L542). [`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) registers the [`struct sdw_master_device`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L698), reads the master properties through [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029), and creates the SoundWire peripheral devices from the ACPI firmware on x86-64.

[`sdw_bus_master_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L42) checks that the link supplied both ops tables before doing anything else, which is why [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) sets [`bus->ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029) and [`bus->compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1037) before calling it:

```c
/* drivers/soundwire/bus.c:42 */
	ret = sdw_master_device_add(bus, parent, fwnode);
	...
	if (!bus->ops) {
		dev_err(bus->dev, "SoundWire Bus ops are not set\n");
		return -EINVAL;
	}

	if (!bus->compute_params) {
		dev_err(bus->dev,
			"Bandwidth allocation not configured, compute_params no set\n");
		return -EINVAL;
	}
	...
	if (IS_ENABLED(CONFIG_ACPI) && ACPI_HANDLE(bus->dev))
		ret = sdw_acpi_find_slaves(bus);
	else if (IS_ENABLED(CONFIG_OF) && bus->dev->of_node)
		ret = sdw_of_find_slaves(bus);
	else
		ret = -ENOTSUPP; /* No ACPI/DT so error out */
```

On an Intel x86-64 platform the [`ACPI_HANDLE()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/acpi.h#L61) branch is taken and [`sdw_acpi_find_slaves()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/slave.c#L211) walks the controller's ACPI children to enumerate the peripherals on this link. The detailed decode of each peripheral's `_ADR` and the registration of its [`struct sdw_slave`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) on [`sdw_bus_type`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus_type.c#L187) belong to the SoundWire bus and device model page.

The [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) places the Cadence context as its first member, so the [`cdns_to_intel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L127) macro recovers the enclosing object from a Cadence pointer with a zero offset:

```c
/* drivers/soundwire/intel.h:75 */
struct sdw_intel {
	struct sdw_cdns cdns;
	int instance;
	struct sdw_intel_link_res *link_res;
	bool startup_done;
	struct sdw_intel_bpt bpt_ctx;
#ifdef CONFIG_DEBUG_FS
	struct dentry *debugfs;
#endif
};
```

```c
/* drivers/soundwire/intel.h:127 */
#define cdns_to_intel(_cdns) container_of(_cdns, struct sdw_intel, cdns)
```

The [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) it contains is the Cadence IP master context, carrying the SoundWire bus object, the register window, the PCM PDI streams, and the per-DAI runtime array:

```c
/* drivers/soundwire/cadence_master.h:124 */
struct sdw_cdns {
	struct device *dev;
	struct sdw_bus bus;
	unsigned int instance;

	u32 ip_offset;
	...
	struct sdw_cdns_streams pcm;
	...
	void __iomem *registers;

	bool link_up;
	unsigned int msg_count;
	...
	struct sdw_cdns_dai_runtime **dai_runtime_array;

	struct mutex status_update_lock; /* add mutual exclusion to sdw_handle_slave_status() */
};
```

The bus the Cadence context embeds is the per-link [`struct sdw_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014), whose fields [`intel_link_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L301) sets before handing it to the core. The [`controller_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1034), [`link_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1035), [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1029), and [`compute_params`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1037) members are the ones the Intel link writes, and [`sdw_master_device_add()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/master.c#L127) fills in [`dev`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014) and [`md`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L1014):

```c
/* include/linux/soundwire/sdw.h:1014 */
struct sdw_bus {
	struct device *dev;
	struct sdw_master_device *md;
	struct lock_class_key bus_lock_key;
	struct mutex bus_lock;
	struct ida slave_ida;
	struct list_head slaves;
	struct lock_class_key msg_lock_key;
	struct mutex msg_lock;
	struct list_head m_rt_list;
	...
	const struct sdw_master_ops *ops;
	const struct sdw_master_port_ops *port_ops;
	struct sdw_master_prop prop;
	...
	int controller_id;
	unsigned int link_id;
	int id;
	int (*compute_params)(struct sdw_bus *bus, struct sdw_stream_runtime *stream);
	DECLARE_BITMAP(assigned, SDW_MAX_DEVICES);
	...
	bool multi_link;
	unsigned int lane_used_bandwidth[SDW_MAX_LANES];
};
```

The bus lives inside that Cadence context, which is itself the first member of the link object at offset 0, so recovering the link object from a Cadence pointer is a zero-offset step:

```
    struct sdw_intel embeds the Cadence master (first member, offset 0)
    ──────────────────────────────────────────────────────────────────

    ┌─ struct sdw_intel ───────────────────────────────────┐
    │ cdns  (first member, offset 0)                       │
    │ ┌─ struct sdw_cdns ──────────────────────────────┐   │
    │ │ bus   struct sdw_bus  (per-link SoundWire bus) │   │
    │ │ registers   ip_offset   instance               │   │
    │ │ pcm  (PDI streams)    dai_runtime_array        │   │
    │ └────────────────────────────────────────────────┘   │
    │ instance   link_res   startup_done   bpt_ctx         │
    └──────────────────────────────────────────────────────┘

    cdns_to_intel(cdns) = container_of(cdns, struct sdw_intel, cdns)
    recovers the outer struct from a Cadence pointer
```

### intel_link_startup powers the link and hands off to DAI registration

After probe has created the bus, the startup pass powers the link and creates its DAIs. [`sdw_intel_startup_controller()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L284) walks the same set of enabled links and calls [`intel_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377) on each aux device, then takes a runtime-PM reference on links without a clock-stop quirk so the parent PCI device stays awake:

```c
/* drivers/soundwire/intel_init.c:284 */
static int
sdw_intel_startup_controller(struct sdw_intel_ctx *ctx)
{
	struct acpi_device *adev = acpi_fetch_acpi_dev(ctx->handle);
	struct sdw_intel_link_dev *ldev;
	u32 link_mask;
	int i;
	...
	link_mask = ctx->link_mask;

	/* Startup SDW Master devices */
	for (i = 0; i < ctx->count; i++) {
		if (!(link_mask & BIT(i)))
			continue;

		ldev = ctx->ldev[i];

		intel_link_startup(&ldev->auxdev);
		...
	}

	return 0;
}
```

[`intel_link_startup()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L377) recovers the Cadence context with [`auxiliary_get_drvdata()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L200) and the enclosing [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) with [`cdns_to_intel()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L127), powers the SHIM and controller through [`sdw_intel_link_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L198), registers the DAIs through [`sdw_intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157), and finally starts the bus through [`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170):

```c
/* drivers/soundwire/intel_auxdevice.c:377 */
int intel_link_startup(struct auxiliary_device *auxdev)
{
	struct device *dev = &auxdev->dev;
	struct sdw_cdns *cdns = auxiliary_get_drvdata(auxdev);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_bus *bus = &cdns->bus;
	...
	bus->multi_link = multi_link;

	/* Initialize shim, controller */
	ret = sdw_intel_link_power_up(sdw);
	if (ret)
		goto err_init;

	/* Register DAIs */
	ret = sdw_intel_register_dai(sdw);
	if (ret) {
		dev_err(dev, "DAI registration failed: %d\n", ret);
		goto err_power_up;
	}

	sdw_intel_debugfs_init(sdw);
	...
	/* start bus */
	ret = sdw_intel_start_bus(sdw);
	if (ret) {
		dev_err(dev, "bus start failed: %d\n", ret);
		goto err_pm_runtime;
	}
	...
	sdw->startup_done = true;
	return 0;
	...
}
```

The DAI registration call is an inline dispatcher that defers the work to the per-version op. It checks the op is present and routes to it through [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135):

```c
/* drivers/soundwire/intel.h:157 */
static inline int sdw_intel_register_dai(struct sdw_intel *sdw)
{
	if (SDW_INTEL_CHECK_OPS(sdw, register_dai))
		return SDW_INTEL_OPS(sdw, register_dai)(sdw);
	return -ENOTSUPP;
}
```

The two macros reach the function pointer struct off the link resources. [`SDW_INTEL_CHECK_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L133) null-checks every pointer on the path and [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135) dereferences the chosen member:

```c
/* drivers/soundwire/intel.h:133 */
#define SDW_INTEL_CHECK_OPS(sdw, cb)	((sdw) && (sdw)->link_res && (sdw)->link_res->hw_ops && \
					 (sdw)->link_res->hw_ops->cb)
#define SDW_INTEL_OPS(sdw, cb)		((sdw)->link_res->hw_ops->cb)
```

[`sdw_intel_link_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L198) and [`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170) have the same body shape, each guarding and dereferencing a different member of the function pointer struct, so the auxiliary driver never names an ACE-version function directly and a new generation is wired in by supplying a new [`struct sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415).

```
    intel_link_startup(): per-link power-up sequence
    ───────────────────────────────────────────────

    ┌──────────────────────────────┐
    │ sdw_intel_link_power_up(sdw) │   power SHIM + controller
    └──────────────────────────────┘
                    ▼
    ┌──────────────────────────────┐
    │ sdw_intel_register_dai(sdw)  │   build CPU DAIs (PDI)
    └──────────────────────────────┘
                    ▼
    ┌──────────────────────────────┐
    │ sdw_intel_debugfs_init(sdw)  │   debugfs nodes
    └──────────────────────────────┘
                    ▼
    ┌──────────────────────────────┐
    │ sdw_intel_start_bus(sdw)     │   start the SoundWire bus
    └──────────────────────────────┘

    each call routes through SDW_INTEL_OPS to link_res->hw_ops
    (ACE 2.x = sdw_intel_lnl_hw_ops); startup_done = true at end
```

### sdw_intel_lnl_hw_ops selects the ACE 2.x callbacks and hands off DAI registration

The function pointer struct SOF chose for Meteor Lake and Lunar Lake is [`sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415), the version-specific table every dispatcher reaches through [`link_res->hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L31). Its members are the per-link operations, each taking the [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) of one link:

```c
/* include/linux/soundwire/sdw_intel.h:415 */
struct sdw_intel_hw_ops {
	void (*debugfs_init)(struct sdw_intel *sdw);
	void (*debugfs_exit)(struct sdw_intel *sdw);

	int (*get_link_count)(struct sdw_intel *sdw);

	int (*register_dai)(struct sdw_intel *sdw);

	void (*check_clock_stop)(struct sdw_intel *sdw);
	int (*start_bus)(struct sdw_intel *sdw);
	...
	int (*link_power_up)(struct sdw_intel *sdw);
	int (*link_power_down)(struct sdw_intel *sdw);
	...
};
```

For ACE 2.x the concrete table is [`sdw_intel_lnl_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109) in [`intel_ace2x.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c), exported under the `SOUNDWIRE_INTEL` namespace for SOF to reference by name. Its [`register_dai`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) member is [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024), and its [`link_power_up`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) and [`start_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) members are the power-on and bus-start callbacks the startup pass runs:

```c
/* drivers/soundwire/intel_ace2x.c:1109 */
const struct sdw_intel_hw_ops sdw_intel_lnl_hw_ops = {
	.debugfs_init = intel_ace2x_debugfs_init,
	.debugfs_exit = intel_ace2x_debugfs_exit,

	.get_link_count = intel_get_link_count,

	.register_dai = intel_register_dai,

	.check_clock_stop = intel_check_clock_stop,
	.start_bus = intel_start_bus,
	...
	.link_power_up = intel_link_power_up,
	.link_power_down = intel_link_power_down,
	...
};
EXPORT_SYMBOL_NS(sdw_intel_lnl_hw_ops, "SOUNDWIRE_INTEL");
```

The [`sdw_intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L157) dispatch is the boundary of this page. It routes to [`intel_register_dai()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1024), which reads the Cadence PCM PDI capability, builds one [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) named `SDWn PinM` per PDI, and registers the array as an ASoC component, so the SoundWire link's CPU DAIs join the sound card. That DAI body, the PDI capability read, and the [`intel_pcm_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L919) the DAIs use are covered by the Intel SoundWire CPU DAI page.

```
    sdw_intel_lnl_hw_ops: ACE 2.x dispatch table
    ────────────────────────────────────────────

    sdw_intel_hw_ops member  ──▶  ACE 2.x function
    ┌──────────────────┬──────────────────────────┐
    │ get_link_count   │ intel_get_link_count     │
    │ register_dai     │ intel_register_dai       │
    │ check_clock_stop │ intel_check_clock_stop   │
    │ start_bus        │ intel_start_bus          │
    │ link_power_up    │ intel_link_power_up      │
    │ link_power_down  │ intel_link_power_down    │
    │ debugfs_init     │ intel_ace2x_debugfs_init │
    └──────────────────┴──────────────────────────┘

    SDW_INTEL_OPS(sdw, member) reaches each via link_res->hw_ops
    register_dai is the boundary to the Intel CPU DAI page
```

### Removal and wake reuse the per-link walk

Teardown mirrors bring-up. [`intel_link_remove()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L489) recovers the Cadence context, tears down debugfs and the Cadence interrupt when the link is not disabled, and calls [`sdw_bus_master_delete()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L196) to remove the bus and its peripherals:

```c
/* drivers/soundwire/intel_auxdevice.c:489 */
static void intel_link_remove(struct auxiliary_device *auxdev)
{
	struct sdw_cdns *cdns = auxiliary_get_drvdata(auxdev);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_bus *bus = &cdns->bus;
	...
	if (!bus->prop.hw_disabled) {
		sdw_intel_debugfs_exit(sdw);
		cancel_delayed_work_sync(&cdns->attach_dwork);
		sdw_cdns_enable_interrupt(cdns, false);
	}
	sdw_bus_master_delete(bus);
}
```

The controller-level [`struct sdw_intel_link_dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11) is freed by the matching two-step teardown [`intel_link_dev_unregister()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L113), which runs [`auxiliary_device_delete()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L223) then [`auxiliary_device_uninit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxiliary_bus.h#L221); the final free of the [`struct sdw_intel_link_dev`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.h#L11) happens in [`intel_link_dev_release()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L23) once the last reference drops. An in-band wake reported by the SHIM follows the same per-link walk: [`sdw_intel_process_wakeen_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L379) iterates the enabled links and calls [`intel_link_process_wakeen_event()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L508), which checks the wake source through [`sdw_intel_shim_check_wake()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L212) and resumes the master so its peripherals re-enumerate.

### From SOF resource to per-link Cadence master and CPU DAIs

The SOF audio DSP hands one [`struct sdw_intel_res`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L342) to [`sdw_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_init.c#L333), which creates one auxiliary device per enabled link, each binding to a [`struct sdw_intel`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L75) that wraps a [`struct sdw_cdns`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.h#L124) Cadence IP master whose PDI capability becomes the link's ASoC CPU DAIs.

```
    SOF audio DSP (sound/soc/sof/intel/hda.c)
    ┌──────────────────────────────────────────────────────────┐
    │  struct sdw_intel_res res                                │
    │  res.hw_ops = &sdw_intel_lnl_hw_ops  (ACE 2.x)           │
    │  res.link_mask, res.count   sdw_intel_probe(&res)        │
    └──────────────────────────────────────┬───────────────────┘
                                           │ one aux device per link
              ┌──────────┬─────────────────┼─────────────────┐
              ▼          ▼                 ▼                 ▼
         ┌─────────┐ ┌─────────┐      ┌─────────┐       ┌─────────┐
         │ link.0  │ │ link.1  │      │ link.2  │       │ link.3  │
         │ auxdev  │ │ auxdev  │      │ auxdev  │       │ auxdev  │
         └────┬────┘ └─────────┘      └─────────┘       └─────────┘
              │  intel_link_probe / intel_link_startup
              ▼
         struct sdw_intel        ┌── struct sdw_cdns  (Cadence IP master)
         ┌────────────────────┐  │   ┌────────────────────────────┐
         │ cdns ──────────────┼──┘   │ struct sdw_bus bus         │
         │ link_res           │      │ pcm  (PDI capability)      │
         │ instance           │      │ dai_runtime_array          │
         └────────────────────┘      └─────────────┬──────────────┘
                                                   │ intel_register_dai
                                                   ▼
                                     SDWn PinM CPU DAIs  (ASoC component)
```
