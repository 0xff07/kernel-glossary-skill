# System resume flow

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

System resume on an Intel Meteor Lake laptop running Sound Open Firmware reverses the suspend teardown by rebuilding the audio stack from the bottom, where each layer can only come up once the one beneath it is live, so the PCI core enters the SOF device through [`snd_sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L364) and [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163), which drives the DSP back to [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) through [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) and [`hda_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L860), reloads and runs firmware with [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78), restarts the SoundWire bus with [`intel_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L715) and [`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170), re-attaches the [`rt722-sdca`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) codec through [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879) and [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208), replays the codec register cache with [`regcache_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396), resumes the ASoC card through [`snd_soc_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L797) and [`soc_resume_deferred()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L755), and leaves each parked stream for userspace to restart with [`snd_pcm_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852).

```
    Resume ordering up the audio stack (Intel MTL SOF)
    ──────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ 1. Controller / DSP to D0                                │
    │    snd_sof_resume → sof_resume → hda_dsp_resume          │
    │    HDA controller init, links powered, DSP cores up      │
    │    snd_sof_boot_dsp_firmware  →  firmware reloaded       │
    │    set_up pipelines re-instantiated on the DSP           │
    └────────────────────────────┬─────────────────────────────┘
                                 │ DSP in D0, IPC live
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ 2. SoundWire re-enumerate / clock restart                │
    │    intel_resume → sdw_intel_start_bus → intel_start_bus  │
    │    sdw_clear_slave_status → all peripherals UNATTACHED   │
    │    attach_dwork → sdw_handle_slave_status                │
    │    rt722 update_status → ATTACHED → regcache_sync        │
    └────────────────────────────┬─────────────────────────────┘
                                 │ codecs re-attached, regs restored
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ 3. ASoC card resume                                      │
    │    snd_soc_resume → soc_resume_deferred (work)           │
    │    component->resume, DAPM stream RESUME replayed        │
    │    suspended PCMs left ready (state SUSPENDED)           │
    └────────────────────────────┬─────────────────────────────┘
                                 │ graph restored
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ 4. Userspace restarts each stream                        │
    │    snd_pcm_resume (INFO_RESUME) or prepare + start       │
    │    pipelines/widgets rebuilt per-PCM at hw_params        │
    └──────────────────────────────────────────────────────────┘
```

## SUMMARY

Resume runs across four cooperating layers and the SOF PM callback is the entry point. The PCI bus core invokes the resume function named in [`EXPORT_NS_DEV_PM_OPS(sof_pci_pm, ...)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L158), which is [`snd_sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L364), and it forwards to [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) with `runtime_resume` false. [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) returns early when [`first_boot`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L582) records that the DSP was never started, otherwise it powers the DSP up with [`snd_sof_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L230), which on Meteor Lake dispatches to [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) through the [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) function pointer struct that [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) copies in. Once the DSP reaches [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47), [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) calls [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78), which reloads the firmware image with [`snd_sof_load_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L474), runs it with [`snd_sof_run_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L109), and re-instantiates topology pipelines through the [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) op when one is set.

The SoundWire manager is a separate auxiliary device with its own PM table [`intel_pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L848), whose system resume callback is [`intel_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L715) and whose runtime callback is [`intel_resume_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L771). [`intel_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L715) powers the link with [`sdw_intel_link_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L198), forces every peripheral to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) through [`sdw_clear_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L2023), then restarts the bus with [`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170). On Meteor Lake that op is [`intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L12), which schedules [`cdns_check_attached_status_dwork()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L999), reads the Cadence slave-status register, and hands the array to [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879). That re-attaches each peripheral and calls the codec [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) callback [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208), which re-runs [`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525) and arms the register cache with [`regcache_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L603), and the codec device resume callback [`rt722_sdca_dev_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L500) then replays it with [`regcache_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396).

The ASoC card resumes through [`snd_soc_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L797), which only schedules [`deferred_resume_work`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc.h#L1086) so the PM thread can return before slow codec restoration finishes. The worker [`soc_resume_deferred()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L755) raises the card to [`SNDRV_CTL_POWER_D2`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1114), runs [`snd_soc_component_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L291) on each suspended component, replays the graph with [`soc_dapm_suspend_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638) under [`SND_SOC_DAPM_STREAM_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L381), unmutes the active DACs, and drops the card to [`SNDRV_CTL_POWER_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1112) so userspace can touch the device again. A PCM left in [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) is not auto-restarted by the kernel; userspace issues [`snd_pcm_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852) when the runtime advertises [`SNDRV_PCM_INFO_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L286), or otherwise re-prepares and restarts, and the DSP pipeline for that stream is rebuilt per-PCM at hw_params time by [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762).

## SPECIFICATIONS

System power-state transitions for the controller follow the ACPI Specification global-system-state model, with the PCI device returning to D0 on resume. The SoundWire bus restart, clock-stop exit, and peripheral re-enumeration follow the MIPI SoundWire Specification. The DSP firmware boot and the IPC handshake on resume are defined by the Sound Open Firmware project rather than a published hardware standard. The register-cache replay, the deferred-work model, and the PCM resume action are Linux kernel software constructs described here from the kernel source.

## LINUX KERNEL

### SOF PM callbacks and DSP power (sof/pm.c, sof/ops.h)

- [`'\<snd_sof_resume\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L364): system resume entry, calls [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) with `runtime_resume` false; wired by [`SYSTEM_SLEEP_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L161)
- [`'\<snd_sof_runtime_resume\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L358): runtime resume entry, calls [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) with `runtime_resume` true
- [`'\<sof_resume\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163): the shared body, powers the DSP to D0, then boots firmware and restores pipelines
- [`'\<snd_sof_boot_dsp_firmware\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78): loads and runs firmware, restores pipelines via the topology op, replays the DSP context
- [`'\<snd_sof_dsp_resume\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L230): function pointer wrapper dispatching to the platform [`resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L299) op
- [`'\<snd_sof_dsp_runtime_resume\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L247): wrapper dispatching to the platform [`runtime_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L301) op
- [`'\<snd_sof_load_firmware\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L474): wrapper calling the platform [`load_firmware`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op
- [`'\<snd_sof_run_firmware\>':'sound/soc/sof/loader.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L109): releases the DSP from reset and waits for the firmware-ready IPC
- [`'\<snd_sof_dsp_hw_params_upon_resume\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L271): wrapper calling the platform [`set_hw_params_upon_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L303) op
- [`'\<snd_sof_dsp_set_power_state\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L287): records the new [`struct sof_dsp_power_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L85) after a transition

### Intel HDA DSP resume (sof/intel/hda-dsp.c, hda-common-ops.c, mtl.c)

- [`'\<hda_dsp_resume\>':'sound/soc/sof/intel/hda-dsp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901): the [`resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L299) op, re-powers the HDA controller and links and targets [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47)
- [`'\<hda_dsp_runtime_resume\>':'sound/soc/sof/intel/hda-dsp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L954): the [`runtime_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L301) op
- [`'\<hda_resume\>':'sound/soc/sof/intel/hda-dsp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L860): resets and starts the HDA controller via [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186)
- [`'\<hda_dsp_set_hw_params_upon_resume\>':'sound/soc/sof/intel/hda-dsp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1155): the [`set_hw_params_upon_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L303) op, frees stale DAI resources before re-setup
- [`'\<hda_bus_ml_resume\>':'sound/soc/sof/intel/hda-mlink.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L906): powers up the multi-link segments that were active before suspend
- [`'sof_hda_common_ops':'sound/soc/sof/intel/hda-common-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17): the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) template binding [`.resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L93) to [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901)
- [`'\<sof_mtl_set_ops\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702): copies [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) into the Meteor Lake device ops

### Topology re-instantiation on the DSP (ipc4-topology.c, sof-audio.c)

- [`'set_up_all_pipelines':'sound/soc/sof/sof-audio.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237): the [`struct sof_ipc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L221) op called from [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78); set for IPC3, left NULL for IPC4
- [`'ipc4_tplg_ops':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3973): the Meteor Lake topology function pointer struct, with [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3985) set but no all-pipelines setup op
- [`'\<sof_ipc4_tear_down_all_pipelines\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829): frees every stream at suspend so the kernel and firmware widget state stay in sync; also takes the verify path
- [`'\<sof_widget_list_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762): builds the pipeline widget list for one PCM, called from [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116)
- [`'\<sof_widget_setup\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251): instantiates one widget on the DSP through the [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) op
- [`'\<sof_ipc4_widget_setup\>':'sound/soc/sof/ipc4-topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103): the IPC4 [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) op sending the module-instantiate IPC

### SoundWire link, bus restart, slave re-attach (intel_auxdevice.c, intel_bus_common.c, bus.c, cadence_master.c)

- [`'\<intel_resume\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L715): the manager system resume callback, powers the link and restarts the bus
- [`'\<intel_resume_runtime\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L771): the manager runtime resume callback, branching on the clock-stop quirks
- [`'intel_pm':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L848): the [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) table binding both resume paths
- [`'\<sdw_intel_link_power_up\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L198): inline dispatcher for the link-power-up op
- [`'\<sdw_intel_start_bus\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170): inline dispatcher for the bus-restart op
- [`'\<intel_start_bus\>':'drivers/soundwire/intel_bus_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L12): soft-resets and re-inits the Cadence IP, then schedules the attach work
- [`'\<sdw_clear_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L2023): forces every assigned peripheral to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) and stores the re-init reason
- [`'\<sdw_handle_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879): programs device numbers and drives the per-peripheral re-attach state machine
- [`'\<sdw_update_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854): invokes the codec [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) callback
- [`'\<sdw_initialize_slave\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1417): re-programs the peripheral's interrupt masks and bus parameters on re-attach
- [`'\<cdns_check_attached_status_dwork\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L999): reads [`CDNS_MCP_SLAVE_STAT`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L109) and calls [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879)

### Codec re-attach and regcache restore (rt722-sdca-sdw.c, rt722-sdca.c, regcache.c)

- [`'\<rt722_sdca_update_status\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208): the [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op, clears [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) on detach and re-runs init on [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96)
- [`'\<rt722_sdca_io_init\>':'sound/soc/codecs/rt722-sdca.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525): exits cache-only mode and, when not first init, marks the cache dirty for the next sync
- [`'\<rt722_sdca_dev_resume\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L500): the codec device PM resume callback, waits for re-enumeration then runs [`regcache_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396)
- [`'\<regcache_sync\>':'drivers/base/regmap/regcache.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396): writes every register the cache marked dirty back to the device
- [`'\<regcache_mark_dirty\>':'drivers/base/regmap/regcache.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L603): flags the whole cache so the following [`regcache_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396) restores it

### ASoC card resume (soc-core.c, soc-component.c, soc-dapm.c, soc-card.c)

- [`'\<snd_soc_resume\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L797): the card resume callback, selects default pins and schedules the deferred worker
- [`'\<soc_resume_deferred\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L755): the work item restoring components, replaying DAPM, and unmuting DACs
- [`'\<snd_soc_component_resume\>':'sound/soc/soc-component.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L291): runs the component [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L81) op and clears [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215)
- [`'\<soc_dapm_suspend_resume\>':'sound/soc/soc-core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638): walks each runtime and posts the stream event to [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620)
- [`'\<snd_soc_dapm_sync\>':'sound/soc/soc-dapm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005): re-runs the bias and power walk after endpoints are marked dirty
- [`'\<snd_soc_card_resume_pre\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L120) / [`'\<snd_soc_card_resume_post\>':'sound/soc/soc-card.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-card.c#L130): the machine driver resume hooks around the component restore

### PCM suspend-state recovery (pcm_native.c)

- [`'\<snd_pcm_resume\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852): the [`SNDRV_PCM_IOCTL_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L699) handler, runs the resume action under the stream lock
- [`'snd_pcm_action_resume':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1845): the [`struct action_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1230) binding the four resume phases
- [`'\<snd_pcm_pre_resume\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1802): rejects a stream not in [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) or lacking [`SNDRV_PCM_INFO_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L286)
- [`'\<snd_pcm_do_resume\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1814): issues [`SNDRV_PCM_TRIGGER_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L103) when the stream was running before suspend
- [`'\<snd_pcm_post_resume\>':'sound/core/pcm_native.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1836): restores the pre-suspend state from [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365)

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle whose transport must be re-established after the bus restarts
- [`Documentation/driver-api/soundwire/summary.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/summary.rst): the SoundWire bus model, manager and peripheral roles, and enumeration
- [`Documentation/sound/soc/dapm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dapm.rst): Dynamic Audio Power Management, the graph replayed on resume
- [`Documentation/sound/soc/pops-clicks.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/pops-clicks.rst): the DAC mute sequencing the resume worker applies
- [`Documentation/power/runtime_pm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/runtime_pm.rst): the runtime and system PM callback model the SOF and SoundWire device tables plug into

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The resume sequence is a chain of function pointer struct ops, one per layer, and each is reached through a wrapper that confirms the op is present before calling it. The PCI core enters the SOF device through the [`SYSTEM_SLEEP_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L161) resume slot, the SOF core reaches the platform through [`snd_sof_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L230), the topology layer through the [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) and [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) ops, the SoundWire manager through [`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170), the codec through its [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op, and the ASoC component through its [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L81) op.

| Stage | Order | Entry op | Concrete callee on Intel MTL SOF |
|-------|-------|----------|----------------------------------|
| PCI PM | 1 | [`SYSTEM_SLEEP_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L161) resume | [`snd_sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L364) |
| SOF DSP | 2 | [`snd_sof_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L230) | [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) |
| SOF firmware | 3 | [`snd_sof_load_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L474) | platform [`load_firmware`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op |
| SOF topology | 4 (per PCM) | [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) | [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) |
| SoundWire manager | 5 | [`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170) | [`intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L12) |
| SoundWire codec | 6 | [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) | [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) |
| ASoC component | 7 | [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L81) | codec component [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L81) op |
| ALSA PCM | 8 | [`snd_pcm_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852) | substream [`trigger`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L64) RESUME |

## DETAILS

### The PM callback enters the SOF device

On an Intel Meteor Lake machine the DSP is a PCI function, and its driver registers the PM table [`sof_pci_pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L158) with its system sleep callbacks bound by macro:

```c
/* sound/soc/sof/sof-pci-dev.c:158 */
EXPORT_NS_DEV_PM_OPS(sof_pci_pm, SND_SOC_SOF_PCI_DEV) = {
	.prepare = sof_pci_prepare,
	.complete = sof_pci_complete,
	SYSTEM_SLEEP_PM_OPS(snd_sof_suspend, snd_sof_resume)
	RUNTIME_PM_OPS(snd_sof_runtime_suspend, snd_sof_runtime_resume,
		       NULL)
};
```

When the PCI core resumes the device it calls the function named in the [`SYSTEM_SLEEP_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L161) resume slot, [`snd_sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L364), which forwards to the shared body with the runtime flag clear:

```c
/* sound/soc/sof/pm.c:364 */
int snd_sof_resume(struct device *dev)
{
	return sof_resume(dev, false);
}
```

The runtime PM entry [`snd_sof_runtime_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L358) calls the same body with the flag set, so one function handles both wake paths and differs only in which platform op it selects.

### sof_resume powers the DSP and re-boots firmware

[`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) is the pivot of the SOF layer. It does nothing when no resume op is set, and it returns immediately when [`first_boot`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L582) records that the DSP was never started, otherwise it powers the DSP up and falls through to [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78):

```c
/* sound/soc/sof/pm.c:163 */
static int sof_resume(struct device *dev, bool runtime_resume)
{
	struct snd_sof_dev *sdev = dev_get_drvdata(dev);
	u32 old_state = sdev->dsp_power_state.state;
	bool on_demand_boot;
	int ret;

	/* do nothing if dsp resume callbacks are not set */
	if (!runtime_resume && !sof_ops(sdev)->resume)
		return 0;

	if (runtime_resume && !sof_ops(sdev)->runtime_resume)
		return 0;

	/* DSP was never successfully started, nothing to resume */
	if (sdev->first_boot)
		return 0;

	/*
	 * if the runtime_resume flag is set, call the runtime_resume routine
	 * or else call the system resume routine
	 */
	if (runtime_resume)
		ret = snd_sof_dsp_runtime_resume(sdev);
	else
		ret = snd_sof_dsp_resume(sdev);
	if (ret < 0) {
		dev_err(sdev->dev,
			"error: failed to power up DSP after resume\n");
		return ret;
	}
	...
	return snd_sof_boot_dsp_firmware(sdev);
}
```

Two short-circuits sit between the power-up and the firmware boot. When the platform supports the low-power D0 substate and [`old_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) was already [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47), the firmware never stopped and [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163) only resumes trace and returns, and when [`on_demand_dsp_boot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L163) is set it moves the state to [`SOF_FW_BOOT_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L36) and defers the boot to the first stream. On a full system resume neither holds, so the call reaches [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78).

[`snd_sof_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L230) is the function pointer wrapper. It calls the platform [`resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L299) op when present and returns 0 otherwise:

```c
/* sound/soc/sof/ops.h:230 */
/* power management */
static inline int snd_sof_dsp_resume(struct snd_sof_dev *sdev)
{
	if (sof_ops(sdev)->resume)
		return sof_ops(sdev)->resume(sdev);

	return 0;
}
```

On Meteor Lake the [`resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L299) op resolves to [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) because [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) copies the shared template into the device ops:

```c
/* sound/soc/sof/intel/mtl.c:702 */
int sof_mtl_set_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *dsp_ops)
{
	...
	memcpy(dsp_ops, &sof_hda_common_ops, sizeof(struct snd_sof_dsp_ops));
	...
}
```

The template binds the power-management slots, so [`.resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L93), [`.runtime_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L95), and [`.set_hw_params_upon_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L97) point at the HDA DSP functions:

```c
/* sound/soc/sof/intel/hda-common-ops.c:91 */
	/* PM */
	.suspend		= hda_dsp_suspend,
	.resume			= hda_dsp_resume,
	.runtime_suspend	= hda_dsp_runtime_suspend,
	.runtime_resume		= hda_dsp_runtime_resume,
	.runtime_idle		= hda_dsp_runtime_idle,
	.set_hw_params_upon_resume = hda_dsp_set_hw_params_upon_resume,
```

### hda_dsp_resume re-powers the controller and links

[`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) has two paths. When the DSP is still in [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) it restores the multi-link segments, the command-IO buffers, and the PCI state and returns, and otherwise it re-initialises the HDA controller from scratch and targets D0:

```c
/* sound/soc/sof/intel/hda-dsp.c:901 */
int hda_dsp_resume(struct snd_sof_dev *sdev)
{
	struct sof_intel_hda_dev *hda = sdev->pdata->hw_pdata;
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct pci_dev *pci = to_pci_dev(sdev->dev);
	const struct sof_dsp_power_state target_state = {
		.state = SOF_DSP_PM_D0,
		.substate = SOF_HDA_DSP_PM_D0I0,
	};
	int ret;

	/* resume from D0I3 */
	if (sdev->dsp_power_state.state == SOF_DSP_PM_D0) {
		ret = hda_bus_ml_resume(bus);
		...
		/* set up CORB/RIRB buffers if was on before suspend */
		hda_codec_resume_cmd_io(sdev);
		...
		/* restore and disable the system wakeup */
		pci_restore_state(pci);
		disable_irq_wake(pci->irq);
		return 0;
	}

	/* init hda controller. DSP cores will be powered up during fw boot */
	ret = hda_resume(sdev, false);
	if (ret < 0)
		return ret;

	return snd_sof_dsp_set_power_state(sdev, &target_state);
}
```

The cold path runs [`hda_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L860), which powers the i915 display codec while the link reset runs, clears the PCI TCSEL bits, and resets and starts the controller with [`hda_dsp_ctrl_init_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L186):

```c
/* sound/soc/sof/intel/hda-dsp.c:860 */
static int hda_resume(struct snd_sof_dev *sdev, bool runtime_resume)
{
	int ret;

	/* display codec must be powered before link reset */
	hda_codec_i915_display_power(sdev, true);

	/*
	 * clear TCSEL to clear playback on some HD Audio
	 * codecs. PCI TCSEL is defined in the Intel manuals.
	 */
	snd_sof_pci_update_bits(sdev, PCI_TCSEL, 0x07, 0);

	/* reset and start hda controller */
	ret = hda_dsp_ctrl_init_chip(sdev, false);
	if (ret < 0) {
		dev_err(sdev->dev,
			"error: failed to start controller after resume\n");
		goto cleanup;
	}
	...
cleanup:
	/* display codec can powered off after controller init */
	hda_codec_i915_display_power(sdev, false);

	return 0;
}
```

According to the comment in [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901), "DSP cores will be powered up during fw boot", so the cores stay off until [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78) runs. With the controller up, [`snd_sof_dsp_set_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L287) records the new [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) state in [`dsp_power_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L572). The companion [`set_hw_params_upon_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L303) op [`hda_dsp_set_hw_params_upon_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1155) frees any stale host-DMA DAI resources so a stream that restarts after resume re-allocates them cleanly:

```c
/* sound/soc/sof/intel/hda-dsp.c:1155 */
int hda_dsp_set_hw_params_upon_resume(struct snd_sof_dev *sdev)
{
	int ret;

	/* make sure all DAI resources are freed */
	ret = hda_dsp_dais_suspend(sdev);
	if (ret < 0)
		dev_warn(sdev->dev, "%s: failure in hda_dsp_dais_suspend\n", __func__);

	return ret;
}
```

### Firmware reload and topology re-instantiation

Back in [`sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L163), [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78) reloads and runs the firmware, then restores pipelines through the topology op when one is set:

```c
/* sound/soc/sof/pm.c:78 */
int snd_sof_boot_dsp_firmware(struct snd_sof_dev *sdev)
{
	const struct sof_ipc_pm_ops *pm_ops = sof_ipc_get_ops(sdev, pm);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	int ret;
	...
	/* load the firmware */
	ret = snd_sof_load_firmware(sdev);
	...
	sof_set_fw_state(sdev, SOF_FW_BOOT_IN_PROGRESS);

	/*
	 * Boot the firmware. The FW boot status will be modified
	 * in snd_sof_run_firmware() depending on the outcome.
	 */
	ret = snd_sof_run_firmware(sdev);
	...
	/* restore pipelines */
	if (tplg_ops && tplg_ops->set_up_all_pipelines) {
		ret = tplg_ops->set_up_all_pipelines(sdev, false);
		if (ret < 0) {
			dev_err(sdev->dev, "%s: failed to restore pipeline: %d\n",
				__func__, ret);
			goto setup_fail;
		}
	}
	...
	/* notify DSP of system resume */
	if (pm_ops && pm_ops->ctx_restore) {
		ret = pm_ops->ctx_restore(sdev);
		...
	}
	...
}
```

[`snd_sof_load_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L474) is the thin wrapper that calls the platform loader op, and [`snd_sof_run_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L109) releases the cores from reset and blocks on the firmware-ready IPC:

```c
/* sound/soc/sof/ops.h:474 */
/* Firmware loading */
static inline int snd_sof_load_firmware(struct snd_sof_dev *sdev)
{
	dev_dbg(sdev->dev, "loading firmware\n");

	return sof_ops(sdev)->load_firmware(sdev);
}
```

The `tplg_ops->set_up_all_pipelines` call is conditional, and that condition is where Meteor Lake diverges from the older IPC3 platforms. The IPC4 topology function pointer struct sets a tear-down op but no all-pipelines setup op:

```c
/* sound/soc/sof/ipc4-topology.c:3973 */
const struct sof_ipc_tplg_ops ipc4_tplg_ops = {
	.widget = tplg_ipc4_widget_ops,
	.token_list = ipc4_token_list,
	.control_setup = sof_ipc4_control_setup,
	.control = &tplg_ipc4_control_ops,
	.widget_setup = sof_ipc4_widget_setup,
	.widget_free = sof_ipc4_widget_free,
	.route_setup = sof_ipc4_route_setup,
	.route_free = sof_ipc4_route_free,
	.dai_config = sof_ipc4_dai_config,
	.parse_manifest = sof_ipc4_parse_manifest,
	.dai_get_param = sof_ipc4_dai_get_param,
	.tear_down_all_pipelines = sof_ipc4_tear_down_all_pipelines,
	.link_setup = sof_ipc4_link_setup,
	.host_config = sof_ipc4_host_config,
};
```

Because [`set_up_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L237) is NULL for IPC4, [`snd_sof_boot_dsp_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L78) skips that block on Meteor Lake, and the firmware comes up with no pipelines instantiated. The matching suspend op [`sof_ipc4_tear_down_all_pipelines()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3829) freed every stream before suspend so the kernel and firmware widget state matched, which is why resume starts from a clean slate. According to the comment in its body, that teardown handles the corner case where freeing was skipped at suspend, and the same op is reachable on the firmware-verify path through the `verify` argument:

```c
/* sound/soc/sof/ipc4-topology.c:3829 */
static int sof_ipc4_tear_down_all_pipelines(struct snd_sof_dev *sdev, bool verify)
{
	/*
	 * This function is called during system suspend, we need to make sure
	 * that all streams have been freed up.
	 * Freeing might have been skipped when xrun happened just at the start
	 * of the suspend and it sent a SNDRV_PCM_TRIGGER_STOP to the active
	 * stream. This will call sof_pcm_stream_free() with
	 * free_widget_list = false which will leave the kernel and firmware out
	 * of sync during suspend/resume.
	 *
	 * This will also make sure that paused streams handled correctly.
	 */

	return sof_pcm_free_all_streams(sdev);
}
```

On Meteor Lake the DSP pipeline and its widgets for a given stream are therefore re-instantiated per-PCM when the stream restarts, each stream rebuilt on its own rather than in bulk at resume. [`sof_pcm_hw_params()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116) builds the widget list with [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762):

```c
/* sound/soc/sof/pcm.c:361 */
	ret = sof_widget_list_setup(sdev, spcm, params, platform_params, dir);
```

[`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762) walks the stream's widget list and instantiates each one with [`sof_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L251), which calls the [`widget_setup`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L230) op, [`sof_ipc4_widget_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-topology.c#L3103) on this platform, sending the module-instantiate IPC to the freshly booted firmware. It returns early when the list is absent or already built:

```c
/* sound/soc/sof/sof-audio.c:762 */
int sof_widget_list_setup(struct snd_sof_dev *sdev, struct snd_sof_pcm *spcm,
			  struct snd_pcm_hw_params *fe_params,
			  struct snd_sof_platform_stream_params *platform_params,
			  int dir)
{
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	struct snd_soc_dapm_widget_list *list = spcm->stream[dir].list;
	struct snd_soc_dapm_widget *widget;
	int i, ret;

	/* nothing to set up or setup has been already done */
	if (!list || spcm->setup_done[dir])
		return 0;

	/* Set up is used to send the IPC to the DSP to create the widget */
	ret = sof_walk_widgets_in_order(sdev, spcm, fe_params, platform_params,
					dir, SOF_WIDGET_SETUP);
	...
}
```

Whether that builder runs in bulk at resume or per stream turns on the IPC version, IPC3 restoring every pipeline in one call and IPC4 booting bare so each stream rebuilds at hw_params:

```
    Pipeline restore path selected by IPC version (set_up_all_pipelines)
    ────────────────────────────────────────────────────────────────────

    tplg op set_up_all_pipelines    snd_sof_boot_dsp_firmware does
    ────────────────────────────    ─────────────────────────────────
    IPC3   set (non-NULL)           call it once: bulk-restore every
                                    pipeline at resume
    IPC4   NULL (ipc4_tplg_ops)     skip the block; firmware boots
                                    with no pipelines

    IPC4 frees all streams at suspend (sof_ipc4_tear_down_all_pipelines)
    so each stream is rebuilt later, per-PCM at hw_params time:
      sof_pcm_hw_params ▶ sof_widget_list_setup ▶ sof_widget_setup
```

### SoundWire link power-up and bus restart

The SoundWire manager is a separate auxiliary device, and its resume is independent of the DSP resume above. Its PM table binds both wake paths:

```c
/* drivers/soundwire/intel_auxdevice.c:848 */
static const struct dev_pm_ops intel_pm = {
	SET_SYSTEM_SLEEP_PM_OPS(intel_suspend, intel_resume)
	SET_RUNTIME_PM_OPS(intel_suspend_runtime, intel_resume_runtime, NULL)
};
```

[`intel_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L715) powers the link, marks every peripheral unattached, and restarts the bus:

```c
/* drivers/soundwire/intel_auxdevice.c:715 */
static int __maybe_unused intel_resume(struct device *dev)
{
	struct sdw_cdns *cdns = dev_get_drvdata(dev);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_bus *bus = &cdns->bus;
	int ret;

	if (bus->prop.hw_disabled || !sdw->startup_done) {
		dev_dbg(dev, "SoundWire master %d is disabled or not-started, ignoring\n",
			bus->link_id);
		return 0;
	}

	ret = sdw_intel_link_power_up(sdw);
	if (ret) {
		dev_err(dev, "%s failed: %d\n", __func__, ret);
		return ret;
	}

	/*
	 * make sure all Slaves are tagged as UNATTACHED and provide
	 * reason for reinitialization
	 */
	sdw_clear_slave_status(bus, SDW_UNATTACH_REQUEST_MASTER_RESET);

	ret = sdw_intel_start_bus(sdw);
	if (ret < 0) {
		dev_err(dev, "cannot start bus during resume\n");
		sdw_intel_link_power_down(sdw);
		return ret;
	}
	...
}
```

[`sdw_clear_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L2023) walks the assigned peripherals and resets each one to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95), recording the re-init reason for the runtime resume path to consult later:

```c
/* drivers/soundwire/bus.c:2023 */
void sdw_clear_slave_status(struct sdw_bus *bus, u32 request)
{
	struct sdw_slave *slave;
	int i;

	/* Check all non-zero devices */
	for (i = 1; i <= SDW_MAX_DEVICES; i++) {
		...
		if (slave->status != SDW_SLAVE_UNATTACHED) {
			sdw_modify_slave_status(slave, SDW_SLAVE_UNATTACHED);
			slave->first_interrupt_done = false;
			sdw_update_slave_status(slave, SDW_SLAVE_UNATTACHED);
		}

		/* keep track of request, used in pm_runtime resume */
		slave->unattach_request = request;
	}
}
```

[`sdw_intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L170) is the inline dispatcher, which on Meteor Lake reaches [`intel_start_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L12). That function soft-resets the Cadence IP, re-enables interrupts, exits reset, and schedules the delayed attach check:

```c
/* drivers/soundwire/intel_bus_common.c:12 */
int intel_start_bus(struct sdw_intel *sdw)
{
	struct device *dev = sdw->cdns.dev;
	struct sdw_cdns *cdns = &sdw->cdns;
	struct sdw_bus *bus = &cdns->bus;
	int ret;

	ret = sdw_cdns_soft_reset(cdns);
	...
	ret = sdw_cdns_enable_interrupt(cdns, true);
	...
	ret = sdw_cdns_exit_reset(cdns);
	...
	schedule_delayed_work(&cdns->attach_dwork,
			      msecs_to_jiffies(SDW_INTEL_DELAYED_ENUMERATION_MS));

	return 0;
}
```

### Slave re-attach drives the codec back to ATTACHED

The scheduled work [`cdns_check_attached_status_dwork()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L999) reads the Cadence slave-status register, builds a per-device status array, and hands it to [`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879):

```c
/* drivers/soundwire/cadence_master.c:999 */
static void cdns_check_attached_status_dwork(struct work_struct *work)
{
	struct sdw_cdns *cdns =
		container_of(work, struct sdw_cdns, attach_dwork.work);
	enum sdw_slave_status status[SDW_MAX_DEVICES + 1];
	u32 val;
	int ret;
	int i;

	val = cdns_readl(cdns, CDNS_MCP_SLAVE_STAT);

	for (i = 0; i <= SDW_MAX_DEVICES; i++) {
		status[i] = val & 0x3;
		if (status[i])
			dev_dbg(cdns->dev, "Peripheral %d status: %d\n", i, status[i]);
		val >>= 2;
	}

	mutex_lock(&cdns->status_update_lock);
	ret = sdw_handle_slave_status(&cdns->bus, status);
	mutex_unlock(&cdns->status_update_lock);
	...
}
```

[`sdw_handle_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1879) first programs device numbers for any peripheral reporting on device 0, then walks each assigned peripheral. For one that moved to [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96) it updates the cached status, re-initialises the peripheral with [`sdw_initialize_slave()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1417), and then notifies the driver:

```c
/* drivers/soundwire/bus.c:1968 */
		case SDW_SLAVE_ATTACHED:
			if (slave->status == SDW_SLAVE_ATTACHED)
				break;

			prev_status = slave->status;
			sdw_modify_slave_status(slave, SDW_SLAVE_ATTACHED);

			if (prev_status == SDW_SLAVE_ALERT)
				break;

			attached_initializing = true;

			ret = sdw_initialize_slave(slave);
			...
			break;
		}

		ret = sdw_update_slave_status(slave, status[i]);
```

[`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854) invokes the codec [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op. For the Realtek RT722 SDCA codec that is [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208), which clears its init flag on detach, re-arms the jack-detection interrupt masks, and re-runs initialisation when the peripheral reports [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:208 */
static int rt722_sdca_update_status(struct sdw_slave *slave,
				enum sdw_slave_status status)
{
	struct rt722_sdca_priv *rt722 = dev_get_drvdata(&slave->dev);

	if (status == SDW_SLAVE_UNATTACHED)
		rt722->hw_init = false;

	if (status == SDW_SLAVE_ATTACHED) {
		if (rt722->hs_jack) {
		/*
		 * Due to the SCP_SDCA_INTMASK will be cleared by any reset, and then
		 * if the device attached again, we will need to set the setting back.
		 * It could avoid losing the jack detection interrupt.
		 * This also could sync with the cache value as the rt722_sdca_jack_init set.
		 */
			sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK1,
				SDW_SCP_SDCA_INTMASK_SDCA_0);
			sdw_write_no_pm(rt722->slave, SDW_SCP_SDCA_INTMASK2,
				SDW_SCP_SDCA_INTMASK_SDCA_8);
		}
	}

	/*
	 * Perform initialization only if slave status is present and
	 * hw_init flag is false
	 */
	if (rt722->hw_init || status != SDW_SLAVE_ATTACHED)
		return 0;

	/* perform I/O transfers required for Slave initialization */
	return rt722_sdca_io_init(&slave->dev, slave);
}
```

The bus walk reaches that callback only after driving each peripheral from UNATTACHED to ATTACHED, re-initializing the device first unless its previous state was ALERT:

```
    Per-peripheral re-attach state machine (sdw_handle_slave_status)
    ────────────────────────────────────────────────────────────────

      device 0 reporting            assigned peripheral i: status[i]
      program dev number            read from CDNS MCP_SLAVE_STAT bits
              │                                   │
              └─────────────────┬─────────────────┘
                                ▼
                     SDW_SLAVE_UNATTACHED
                                │
                                ▼   status becomes ATTACHED
                     SDW_SLAVE_ATTACHED
                       │             │
         prev == ALERT │             │ prev != ALERT
                       ▼             ▼
                   skip init    sdw_initialize_slave
                       │             │
                       └──────┬──────┘
                              ▼
                   sdw_update_slave_status ▶ codec update_status
```

### Register cache restore on the codec

[`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.c#L1525) takes the regmap out of cache-only mode and, on a re-attach where [`first_hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L24) is already set, marks the whole cache dirty with [`regcache_mark_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L603) so the values cached before suspend are queued for restoration:

```c
/* sound/soc/codecs/rt722-sdca.c:1525 */
int rt722_sdca_io_init(struct device *dev, struct sdw_slave *slave)
{
	struct rt722_sdca_priv *rt722 = dev_get_drvdata(dev);
	unsigned int val;

	rt722->disable_irq = false;

	if (rt722->hw_init)
		return 0;

	regcache_cache_only(rt722->regmap, false);
	if (rt722->first_hw_init) {
		regcache_cache_bypass(rt722->regmap, true);
	} else {
		...
	}
	...
	if (rt722->first_hw_init) {
		regcache_cache_bypass(rt722->regmap, false);
		regcache_mark_dirty(rt722->regmap);
	} else
		rt722->first_hw_init = true;

	/* Mark Slave initialization complete */
	rt722->hw_init = true;
	...
}
```

The dirty cache is replayed one step later, from the codec device PM resume callback [`rt722_sdca_dev_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L500). It waits for the re-enumeration to complete, drops the regmap out of cache-only mode, and calls [`regcache_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396):

```c
/* sound/soc/codecs/rt722-sdca-sdw.c:520 */
	time = wait_for_completion_timeout(&slave->initialization_complete,
				msecs_to_jiffies(RT722_PROBE_TIMEOUT));
	if (!time) {
		dev_err(&slave->dev, "Initialization not complete, timed out\n");
		sdw_show_ping_status(slave->bus, true);

		return -ETIMEDOUT;
	}

regmap_sync:
	slave->unattach_request = 0;
	regcache_cache_only(rt722->regmap, false);
	regcache_sync(rt722->regmap);
	return 0;
}
```

[`regcache_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396) writes every register the cache marked dirty back to the device, so the codec wakes with the gains, routing, and jack-detection settings it held before suspend rather than its hardware defaults.

```
    Register cache restore spans two codec PM callbacks
    ─────────────────────────────────────────────────────

    rt722_sdca_io_init            rt722_sdca_dev_resume
    (on SDW_SLAVE_ATTACHED)       (codec device PM resume)
    ┌─────────────────────────┐   ┌─────────────────────────┐
    │ regcache_cache_only     │   │ wait_for_completion     │
    │   (regmap, false)       │   │   (initialization_done) │
    │ first_hw_init set:      │   │ regcache_cache_only     │
    │   regcache_mark_dirty   │   │   (regmap, false)       │
    │   (whole cache queued)  │   │ regcache_sync           │
    └────────────┬────────────┘   └────────────▲────────────┘
                 │  cache marked dirty here,    │
                 └──────────────────────────────┘
                    replayed one callback later
```

### ASoC card resume schedules a deferred worker

The ASoC card resumes through [`snd_soc_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L797). It restores nothing inline; it selects the default pin state for active components and schedules the deferred worker so the PM thread can return while slow codec restoration happens out of line:

```c
/* sound/soc/soc-core.c:797 */
/* powers up audio subsystem after a suspend */
int snd_soc_resume(struct device *dev)
{
	struct snd_soc_card *card = dev_get_drvdata(dev);
	struct snd_soc_component *component;

	/* If the card is not initialized yet there is nothing to do */
	if (!snd_soc_card_is_instantiated(card))
		return 0;

	/* activate pins from sleep state */
	for_each_card_components(card, component)
		if (snd_soc_component_active(component))
			pinctrl_pm_select_default_state(component->dev);

	dev_dbg(dev, "ASoC: Scheduling resume work\n");
	if (!schedule_work(&card->deferred_resume_work))
		dev_err(dev, "ASoC: resume work item may be lost\n");

	return 0;
}
```

According to the comment in [`soc_resume_deferred()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L755), the card power state is still [`SNDRV_CTL_POWER_D2`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1114) after the worker raises it "so that DAPM starts enabling things". The worker restores each suspended component, replays the DAPM graph, unmutes the active DACs, and finally drops the card to [`SNDRV_CTL_POWER_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1112):

```c
/* sound/soc/soc-core.c:755 */
static void soc_resume_deferred(struct work_struct *work)
{
	struct snd_soc_card *card =
			container_of(work, struct snd_soc_card,
				     deferred_resume_work);
	struct snd_soc_component *component;
	...
	/* Bring us up into D2 so that DAPM starts enabling things */
	snd_power_change_state(card->snd_card, SNDRV_CTL_POWER_D2);

	snd_soc_card_resume_pre(card);

	for_each_card_components(card, component) {
		if (snd_soc_component_is_suspended(component))
			snd_soc_component_resume(component);
	}

	soc_dapm_suspend_resume(card, SND_SOC_DAPM_STREAM_RESUME);

	/* unmute any active DACs */
	soc_playback_digital_mute(card, 0);

	snd_soc_card_resume_post(card);
	...
	/* Recheck all endpoints too, their state is affected by suspend */
	snd_soc_dapm_mark_endpoints_dirty(card);
	snd_soc_dapm_sync(snd_soc_card_to_dapm(card));

	/* userspace can access us now we are back as we were before */
	snd_power_change_state(card->snd_card, SNDRV_CTL_POWER_D0);
}
```

[`snd_soc_component_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-component.c#L291) runs the component [`resume`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L81) op and clears the [`suspended`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L215) flag set at suspend time:

```c
/* sound/soc/soc-component.c:291 */
void snd_soc_component_resume(struct snd_soc_component *component)
{
	if (component->driver->resume)
		component->driver->resume(component);
	component->suspended = 0;
}
```

[`soc_dapm_suspend_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L638) replays the power graph by posting a stream event to every runtime in both directions:

```c
/* sound/soc/soc-core.c:638 */
static void soc_dapm_suspend_resume(struct snd_soc_card *card, int event)
{
	struct snd_soc_pcm_runtime *rtd;
	int stream;

	for_each_card_rtds(card, rtd) {

		if (rtd->dai_link->ignore_suspend)
			continue;

		for_each_pcm_streams(stream)
			snd_soc_dapm_stream_event(rtd, stream, event);
	}
}
```

With the event [`SND_SOC_DAPM_STREAM_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dapm.h#L381), [`snd_soc_dapm_stream_event()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L4620) re-powers the widgets that belong to streams that were active before suspend, and the closing [`snd_soc_dapm_sync()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-dapm.c#L3005) settles the bias levels after every endpoint is re-evaluated.

### A suspended PCM is recovered by userspace

The kernel does not silently re-arm a parked stream. At suspend, an active PCM was moved to [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) with its previous state saved. After the card is back at [`SNDRV_CTL_POWER_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L1112), userspace recovers the stream. When the runtime advertises [`SNDRV_PCM_INFO_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L286) it issues [`snd_pcm_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1852), which runs the resume action:

```c
/* sound/core/pcm_native.c:1852 */
static int snd_pcm_resume(struct snd_pcm_substream *substream)
{
	return snd_pcm_action_lock_irq(&snd_pcm_action_resume, substream,
				       ACTION_ARG_IGNORE);
}
```

The action is the four-phase [`snd_pcm_action_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1845) descriptor:

```c
/* sound/core/pcm_native.c:1845 */
static const struct action_ops snd_pcm_action_resume = {
	.pre_action = snd_pcm_pre_resume,
	.do_action = snd_pcm_do_resume,
	.undo_action = snd_pcm_undo_resume,
	.post_action = snd_pcm_post_resume
};
```

[`snd_pcm_pre_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1802) is the gate. It returns `-EBADFD` for a stream not in [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314) and `-ENOSYS` when the hardware does not advertise [`SNDRV_PCM_INFO_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L286):

```c
/* sound/core/pcm_native.c:1802 */
static int snd_pcm_pre_resume(struct snd_pcm_substream *substream,
			      snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (runtime->state != SNDRV_PCM_STATE_SUSPENDED)
		return -EBADFD;
	if (!(runtime->info & SNDRV_PCM_INFO_RESUME))
		return -ENOSYS;
	runtime->trigger_master = substream;
	return 0;
}
```

[`snd_pcm_do_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1814) issues [`SNDRV_PCM_TRIGGER_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L103) only when the stream was running before suspend, and [`snd_pcm_post_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/core/pcm_native.c#L1836) restores the saved [`suspended_state`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/pcm.h#L365):

```c
/* sound/core/pcm_native.c:1814 */
static int snd_pcm_do_resume(struct snd_pcm_substream *substream,
			     snd_pcm_state_t state)
{
	struct snd_pcm_runtime *runtime = substream->runtime;
	if (runtime->trigger_master != substream)
		return 0;
	/* DMA not running previously? */
	if (runtime->suspended_state != SNDRV_PCM_STATE_RUNNING &&
	    (runtime->suspended_state != SNDRV_PCM_STATE_DRAINING ||
	     substream->stream != SNDRV_PCM_STREAM_PLAYBACK))
		return 0;
	return substream->ops->trigger(substream, SNDRV_PCM_TRIGGER_RESUME);
}
```

When [`SNDRV_PCM_INFO_RESUME`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L286) is not set, userspace instead reacts to the `-EPIPE`/`-ESTRPIPE` it sees on the next I/O call by re-preparing the stream and restarting it, which re-runs hw_params and brings the per-PCM DSP pipeline back through [`sof_widget_list_setup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L762). Either way, the controller, DSP, SoundWire bus, codecs, and DAPM graph are already live by the time the stream restarts, which is why the ordering runs from the controller up to the streams.

```
    A suspended PCM is restarted by userspace
    ─────────────────────────────────────────

    state at suspend:  SNDRV_PCM_STATE_SUSPENDED  (prior state saved)
                                  │
                                  ▼  userspace snd_pcm_resume
                       snd_pcm_action_resume phases
       ┌──────────────┬───────────────────┬──────────────────┐
       │ pre_resume   │ do_resume         │ post_resume      │
       │ require      │ if prior state    │ restore saved    │
       │ SUSPENDED +  │ RUNNING/DRAINING: │ suspended_state  │
       │ INFO_RESUME  │ TRIGGER_RESUME    │                  │
       └──────┬───────┴───────────────────┴──────────────────┘
              │ not SUSPENDED ▶ -EBADFD ; no INFO_RESUME ▶ -ENOSYS
              ▼
       no INFO_RESUME: userspace re-prepares + restarts instead
```

### Four-stage bottom-up resume ordering of the audio stack

Resume proceeds bottom-up across four stages, the controller and DSP back to D0 through [`snd_sof_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L364), the SoundWire bus restart and peripheral re-attach through [`intel_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L714) up to [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) and [`regcache_sync()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/regmap/regcache.c#L396), the ASoC card restore through [`snd_soc_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L798), and finally userspace restarting each stream parked at [`SNDRV_PCM_STATE_SUSPENDED`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/asound.h#L314).

```
    Resume ordering up the audio stack (Intel MTL SOF)
    ──────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ 1. Controller / DSP to D0                                │
    │    snd_sof_resume → sof_resume → hda_dsp_resume          │
    │    HDA controller init, links powered, DSP cores up      │
    │    snd_sof_load_firmware  →  firmware reloaded           │
    │    set_up pipelines re-instantiated on the DSP           │
    └────────────────────────────┬─────────────────────────────┘
                                 │ DSP in D0, IPC live
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ 2. SoundWire re-enumerate / clock restart                │
    │    intel_resume → sdw_intel_start_bus                    │
    │    sdw_clear_slave_status → all peripherals UNATTACHED   │
    │    attach_dwork → sdw_handle_slave_status                │
    │    rt722 update_status → ATTACHED → regcache_sync        │
    └────────────────────────────┬─────────────────────────────┘
                                 │ codecs re-attached, regs restored
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ 3. ASoC card resume                                      │
    │    snd_soc_resume → soc_resume_deferred (work)           │
    │    component->resume, DAPM stream RESUME replayed        │
    │    suspended PCMs left ready (state SUSPENDED)           │
    └────────────────────────────┬─────────────────────────────┘
                                 │ graph restored
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ 4. Userspace restarts each stream                        │
    │    snd_pcm_resume (INFO_RESUME) or prepare + start       │
    │    pipelines/widgets rebuilt per-PCM at hw_params        │
    └──────────────────────────────────────────────────────────┘
```
