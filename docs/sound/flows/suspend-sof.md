# System suspend flow (SOF DSP and SoundWire)

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

After the ASoC sound card suspend has muted the DACs, driven every PCM to suspended, and dropped DAPM bias toward off, the SOF PCI device suspends through [`sof_pci_pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L158) whose system-sleep entry [`snd_sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370) calls [`sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L229), which computes the DSP D-state with [`snd_sof_dsp_power_target()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L26), saves the firmware context through the [`ctx_save`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L452) IPC op, and powers the audio DSP to [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50) through [`hda_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1010) and [`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780), after which the SoundWire master auxiliary device suspends through [`intel_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628) which stops the bus through [`sdw_intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L191) and [`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205) into the Cadence clock stop [`sdw_cdns_clock_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1683), and the RT722 codec lands at [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) through [`sdw_clear_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L2023) and [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208).

```
    SOF DSP and SoundWire suspend descent (Intel MTL SOF)
    ─────────────────────────────────────────────────────

    (preceding stage: ASoC card suspend, snd_soc_suspend)
                                   │  PCMs SUSPENDED, DAPM bias off
                                   ▼
    SOF PCI device     dev_pm_ops sof_pci_pm  SYSTEM_SLEEP suspend
    ┌──────────────────────────────────────────────────────────┐
    │ snd_sof_suspend() ─▶ sof_suspend(dev, false)             │
    │   target = snd_sof_dsp_power_target()  ─▶ SOF_DSP_PM_D3   │
    │   tear_down_all_pipelines (DSP was D0)                    │
    │   snd_sof_dsp_hw_params_upon_resume()   arm replay        │
    │   pm_ops->ctx_save()    firmware context saved            │
    │   snd_sof_dsp_suspend() ─▶ hda_dsp_suspend()             │
    └──────────────────────────────┬───────────────────────────┘
                                   ▼
    HDA DSP power-down   hda_suspend()  (target_state == D3)
    ┌───────────────────────────────────────────────────────────┐
    │   chip->disable_interrupts()   DSP IRQ off                │
    │   hda_bus_ml_suspend()   HDA multi-links powered down     │
    │   chip->power_down_dsp()   DSP cores off                  │
    │   hda_dsp_ctrl_stop_chip()   controller stream engine off │
    │   hda_dsp_ctrl_link_reset(true)   link reset, PCI D3      │
    └──────────────────────────────┬────────────────────────────┘
                                   ▼
    SoundWire master aux device  dev_pm_ops intel_pm  suspend
    ┌──────────────────────────────────────────────────────────┐
    │ intel_suspend() ─▶ sdw_intel_stop_bus(sdw, false)        │
    │   intel_stop_bus() ─▶ sdw_cdns_clock_stop()  (if quirk)  │
    │   sdw_cdns_enable_interrupt(false)   Cadence IRQ off      │
    │   sdw_intel_link_power_down()   SHIM/link down            │
    └──────────────────────────────┬────────────────────────────┘
                                   ▼
    SoundWire codec detach   (driven when the bus is brought back)
    ┌──────────────────────────────────────────────────────────┐
    │ sdw_clear_slave_status(bus, MASTER_RESET)                │
    │   sdw_modify_slave_status() ─▶ SDW_SLAVE_UNATTACHED      │
    │   sdw_update_slave_status() ─▶ rt722_sdca_update_status  │
    │   rt722->hw_init = false   (re-init on next attach)       │
    └───────────────────────────────────────────────────────────┘
```

## SUMMARY

This page traces the lower half of a system-wide suspend on an Intel Meteor Lake platform whose audio is driven by Sound Open Firmware over the HDA controller, with SoundWire codecs such as the Realtek RT722. The PM core suspends devices in reverse dependency order, so the ASoC sound card suspends first and the SOF DSP device, the SoundWire master, and the HDA controller suspend after it. The ASoC/PCM/DAPM descent that runs first is the preceding stage, entered through [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654); this page picks up at the SOF PCI device callback and follows the DSP power-down, the SoundWire bus stop, and the codec detach.

The SOF PCI device is bound to [`sof_pci_pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L158), whose system-sleep suspend is [`snd_sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370), a thin call into [`sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L229) with the runtime flag clear. That function computes the target DSP state with [`snd_sof_dsp_power_target()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L26), tears down the running pipelines through the [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) topology op when the DSP was at [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47), arms stream replay for resume through [`snd_sof_dsp_hw_params_upon_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L271), saves the firmware context through the [`ctx_save`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L452) IPC op, and powers the DSP down through [`snd_sof_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L238), which on Meteor Lake dispatches to [`hda_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1010). The DSP D-state is recorded through [`snd_sof_dsp_set_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L287), and on a leaving-D0 transition the firmware boot state is reset to [`SOF_FW_BOOT_NOT_STARTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L40).

[`hda_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1010) cancels the opportunistic D0i3 work and, for an S3 or deeper target, runs [`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780), which disables DSP interrupts through the chip [`disable_interrupts`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L201) op, powers down the HDA multi-links through [`hda_bus_ml_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L925), powers down the DSP cores through the chip [`power_down_dsp`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L200) op, stops the controller stream engine through [`hda_dsp_ctrl_stop_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L275), and resets the controller through [`hda_dsp_ctrl_link_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L30) before the PCI device is left in D3.

The SoundWire master is an auxiliary device bound to [`intel_pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L848) whose [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L850) entry is [`intel_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628). When the master is not already runtime-suspended it stops the bus through [`sdw_intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L191), which dispatches to [`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205), and the clock-stop request reaches [`sdw_cdns_clock_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1683) on the Cadence master before [`sdw_cdns_enable_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1202) masks the Cadence interrupt and [`sdw_intel_link_power_down()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L205) powers the link down. The codec is detached when the bus is brought back up, where [`sdw_clear_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L2023) drives every assigned slave to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) through [`sdw_modify_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L928) and calls each codec's [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op through [`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854), reaching [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) on the RT722.

## SPECIFICATIONS

The DSP power-down and SoundWire bus stop form a Linux kernel software sequence and have no single hardware specification. The DSP D-states the SOF path targets follow the Intel High Definition Audio controller and Audio DSP power-management model, and the platform sleep states they map onto ([`ACPI_STATE_S0`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h), [`ACPI_STATE_S3`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h), [`ACPI_STATE_S4`](https://elixir.bootlin.com/linux/v7.0/source/include/acpi/actypes.h)) are defined by the ACPI Specification system-state model that [`acpi_target_system_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c) reports and that [`snd_sof_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L376) maps into [`system_suspend_target`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L577). The SoundWire bus clock-stop mode the master enters, and the slave attachment-status model the codec follows, are defined by the MIPI Alliance SoundWire (Serial Low-power Inter-chip Media Bus) specification, which is membership-gated and is described here only from the kernel source. The HDA controller register model the controller-off step programs (GCTL reset, interrupt control, stream descriptors) is defined by the Intel High Definition Audio Specification. The firmware image format, the topology binary, and the IPC4 context-save message are defined by the Sound Open Firmware project rather than by a ratified standard, and the project documentation is public.

## LINUX KERNEL

### PM callback entry points (sof-pci-dev.c, intel_auxdevice.c, pm.h)

- [`'\<struct dev_pm_ops\>':'include/linux/pm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288): the per-device function pointer struct the PM core dispatches through; its [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288), [`freeze`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288), and [`poweroff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) members are the system-sleep suspend entries
- [`'sof_pci_pm':'sound/soc/sof/sof-pci-dev.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L158): the SOF PCI device PM table, declared with [`EXPORT_NS_DEV_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L401) and referenced by the Meteor Lake PCI driver through [`pm_ptr(&sof_pci_pm)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L138); its [`SYSTEM_SLEEP_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L314) entry is [`snd_sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370)
- [`'intel_pm':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L848): the SoundWire master auxiliary device PM table set on [`sdw_intel_drv.driver.pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L865); its [`SET_SYSTEM_SLEEP_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h) entry is [`intel_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628)

### SOF suspend (sof/pm.c, sof/ops.h)

- [`'\<snd_sof_suspend\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370): the system-sleep entry; calls [`sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L229) with the runtime flag clear
- [`'\<sof_suspend\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L229): tear down pipelines, arm resume replay, save firmware context, and power the DSP down to the target state
- [`'\<snd_sof_prepare\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L376): the [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L159) callback that runs first, mapping [`acpi_target_system_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c) into [`system_suspend_target`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L577) when the descriptor sets [`use_acpi_target_states`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L32)
- [`'\<snd_sof_dsp_power_target\>':'sound/soc/sof/pm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L26): map [`system_suspend_target`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L577) to a DSP D-state, returning [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50) for S3 and deeper
- [`'\<snd_sof_dsp_hw_params_upon_resume\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L271): run the platform [`set_hw_params_upon_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op so streams replay their parameters on resume
- [`'\<snd_sof_dsp_suspend\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L238): call the platform [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op, which on Intel HDA platforms is [`hda_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1010)
- [`'\<snd_sof_dsp_set_power_state\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L287): record the new [`struct sof_dsp_power_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L85) under the [`power_state_access`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L574) mutex
- [`'\<snd_sof_stream_suspend_ignored\>':'sound/soc/sof/sof-audio.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L894): report whether any PCM set [`suspend_ignored`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h), the S0ix criterion for keeping the DSP in [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47)
- [`'\<struct sof_ipc_pm_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L451): the IPC-version PM function pointer struct whose [`ctx_save`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L452) op checkpoints the firmware before power is removed

### SOF Intel HDA DSP power-down (sof/intel/hda-dsp.c, hda-ctrl.c, hda-mlink.c)

- [`'\<hda_dsp_suspend\>':'sound/soc/sof/intel/hda-dsp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1010): cancel pending D0i3 work, then either prepare S0ix (for [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47)) or run [`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780) and record the D3 state
- [`'\<hda_suspend\>':'sound/soc/sof/intel/hda-dsp.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780): disable DSP interrupts, power down HDA links, power down the DSP cores, stop the controller, and reset the link
- [`'\<hda_bus_ml_suspend\>':'sound/soc/sof/intel/hda-mlink.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L925): power down each non-alternate HDA multi-link through [`snd_hdac_ext_bus_link_power_down()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/controller.c#L227)
- [`'\<hda_dsp_ctrl_stop_chip\>':'sound/soc/sof/intel/hda-ctrl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L275): disable per-stream and controller interrupts, clear stream and wake status, stop the command IO, and clear [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340)
- [`'\<hda_dsp_ctrl_link_reset\>':'sound/soc/sof/intel/hda-ctrl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L30): drive the controller into or out of reset through the GCTL register and wait for the state to settle
- [`'\<hda_codec_jack_wake_enable\>':'sound/soc/sof/intel/hda-codec.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L76): set the controller WAKEEN bits for HDA codecs with jack connectors before power-down
- [`'\<struct sof_dsp_power_state\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L85): the recorded DSP power state, a [`state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L85) D-number plus a platform [`substate`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L85)
- [`'\<enum sof_dsp_power_states\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L46): [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) through [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50)
- [`'\<enum sof_system_suspend_state\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L91): [`SOF_SUSPEND_NONE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L92), [`SOF_SUSPEND_S0IX`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L93), [`SOF_SUSPEND_S3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L94), [`SOF_SUSPEND_S4`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L95), [`SOF_SUSPEND_S5`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L96)

### SoundWire master suspend and clock stop (intel_auxdevice.c, intel_bus_common.c, cadence_master.c)

- [`'\<intel_suspend\>':'drivers/soundwire/intel_auxdevice.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628): disable runtime PM and, when the master is not already runtime-suspended, stop the bus through [`sdw_intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L191)
- [`'\<sdw_intel_stop_bus\>':'drivers/soundwire/intel.h'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L191): dispatch to the platform [`stop_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) op through [`SDW_INTEL_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L135), which on Meteor Lake is [`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205)
- [`'\<intel_stop_bus\>':'drivers/soundwire/intel_bus_common.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205): optionally run [`sdw_cdns_clock_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1683), disable Cadence interrupts through [`sdw_cdns_enable_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1202), and power the link down through [`sdw_intel_link_power_down()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L205)
- [`'\<sdw_cdns_clock_stop\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1683): mask slave interrupts, prepare attached slaves through [`sdw_bus_prep_clk_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1055), and enter clock-stop mode through [`sdw_bus_clk_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1155)
- [`'\<sdw_cdns_enable_interrupt\>':'drivers/soundwire/cadence_master.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1202): clear and mask the Cadence master interrupt sources, cancelling queued status work
- [`'sdw_intel_lnl_hw_ops':'drivers/soundwire/intel_ace2x.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109): the ACE 2.x [`struct sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) whose [`stop_bus`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1121) is [`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205)

### SoundWire codec detach and status (bus.c, codecs/rt722-sdca-sdw.c)

- [`'\<sdw_clear_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L2023): for every assigned slave not already detached, set [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) through [`sdw_modify_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L928) and notify the codec through [`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854)
- [`'\<sdw_modify_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L928): take the bus lock, reinit the enumeration completions on a transition to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95), and write the new [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665)
- [`'\<sdw_update_slave_status\>':'drivers/soundwire/bus.c'`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854): call the bound codec driver's [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op under the per-slave lock when the slave was probed
- [`'\<rt722_sdca_update_status\>':'sound/soc/codecs/rt722-sdca-sdw.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208): the RT722 [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op; clears [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) on [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) so the next attach re-initializes the device
- [`'\<struct sdw_slave_ops\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616): the SoundWire slave driver callbacks; its [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) member is the codec's status observer
- [`'\<enum sdw_slave_status\>':'include/linux/soundwire/sdw.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94): [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95), [`SDW_SLAVE_ATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L96), [`SDW_SLAVE_ALERT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L97)

## KERNEL DOCUMENTATION

- [`Documentation/driver-api/pm/devices.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/pm/devices.rst): the device PM model and the [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) callback phases the SOF and SoundWire suspends are dispatched through
- [`Documentation/power/runtime_pm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/power/runtime_pm.rst): the runtime PM interaction the SoundWire master suspend checks before stopping the bus
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream and bus lifecycle whose clock-stop entry the master suspend reaches
- [`Documentation/sound/hd-audio/intel-multi-link.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/hd-audio/intel-multi-link.rst): the HDAudio multi-link block whose links [`hda_bus_ml_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L925) powers down

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [SOF architecture overview](https://thesofproject.github.io/latest/introduction/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The descent this page covers crosses two device PM tables and ends at a bus-driven codec callback. Each table is a [`struct dev_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L288) whose suspend member the PM core invokes when it reaches that device in the reverse-dependency walk, after the preceding ASoC card suspend has already run. The SOF table powers the DSP down and resets the HDA controller in one callback, and the SoundWire master table stops the bus; the codec detach is not a PM callback of its own but a status notification the master drives. The table below maps each stage to the table, the suspend entry, and the state its objects land in.

| Stage | PM table | suspend entry | resulting state |
|-------|----------|---------------|-----------------|
| SOF DSP (PCI) | [`sof_pci_pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L158) | [`snd_sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370) | DSP [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50), firmware [`SOF_FW_BOOT_NOT_STARTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L40) |
| HDA controller | folded into [`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780) | (reset path) | stream engine stopped, controller reset, PCI D3 |
| SoundWire master | [`intel_pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L848) | [`intel_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628) | bus clock-stopped, link powered down |
| SoundWire codec | bus-driven via [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) | [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) | [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) |

The SOF [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L159) callback [`snd_sof_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L376) runs before the SOF suspend entry and selects the target sleep state, so by the time [`sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L229) reads [`system_suspend_target`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L577) the choice between [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) and [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50) is already constrained. The SoundWire master reaches its concrete stop routine through the per-version [`struct sdw_intel_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415), which on Meteor Lake is [`sdw_intel_lnl_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109), so the auxiliary driver never names an ACE-version function directly.

## DETAILS

### The two PM tables this descent enters

The PM core suspends devices in reverse of the order it resumed them, so a child suspends before its parent and a consumer before its supplier. The ASoC sound card is a child of the SOF DSP that supplies its DAIs, and the SoundWire codecs are children of the SoundWire master that the SOF device parents. The ASoC card therefore suspends first through [`snd_soc_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-core.c#L654) (the preceding stage), and this page resumes the trace at the SOF DSP device, then the SoundWire master and its codecs, then the HDA controller hardware that [`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780) resets at the bottom of the SOF path.

The SOF PCI device names [`sof_pci_pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L158), declared once in the shared PCI device code and pointed at by the Meteor Lake driver through [`pm_ptr()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L473). The [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L159) and [`complete`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L160) callbacks bracket the sleep, and the [`SYSTEM_SLEEP_PM_OPS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pm.h#L314) macro wires [`snd_sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370) as the suspend entry:

```c
/* sound/soc/sof/sof-pci-dev.c:158 */
EXPORT_NS_DEV_PM_OPS(sof_pci_pm, SND_SOC_SOF_PCI_DEV) = {
	.prepare = snd_sof_prepare,
	.complete = snd_sof_complete,
	SYSTEM_SLEEP_PM_OPS(snd_sof_suspend, snd_sof_resume)
	RUNTIME_PM_OPS(snd_sof_runtime_suspend, snd_sof_runtime_resume,
		       snd_sof_runtime_idle)
};
```

The Meteor Lake PCI driver points its [`pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L138) field at that table:

```c
/* sound/soc/sof/intel/pci-mtl.c:130 */
static struct pci_driver snd_sof_pci_intel_mtl_driver = {
	.name = "sof-audio-pci-intel-mtl",
	.id_table = sof_pci_ids,
	.probe = hda_pci_intel_probe,
	.remove = sof_pci_remove,
	.shutdown = sof_pci_shutdown,
	.driver = {
		.pm = pm_ptr(&sof_pci_pm),
	},
};
```

The SoundWire master is an auxiliary device whose driver names [`intel_pm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L848), and its system-sleep suspend is [`intel_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628):

```c
/* drivers/soundwire/intel_auxdevice.c:848 */
static const struct dev_pm_ops intel_pm = {
	.prepare = intel_pm_prepare,
	SET_SYSTEM_SLEEP_PM_OPS(intel_suspend, intel_resume)
	SET_RUNTIME_PM_OPS(intel_suspend_runtime, intel_resume_runtime, NULL)
};
```

The PM core walks these two tables in reverse-dependency order, the SOF PCI table first and the SoundWire master table after, each routing its suspend slot to the body that powers its own half down:

```
    The two struct dev_pm_ops tables this descent dispatches through
    ────────────────────────────────────────────────────────────────

    SOF PCI device (PCI)             SoundWire master (aux device)
    struct dev_pm_ops sof_pci_pm     struct dev_pm_ops intel_pm
    ┌──────────────────────────────┐ ┌──────────────────────────────┐
    │ .prepare  = snd_sof_prepare  │ │ .prepare  = intel_pm_prepare │
    │ .complete = snd_sof_complete │ │                              │
    │ SYSTEM_SLEEP_PM_OPS:         │ │ SET_SYSTEM_SLEEP_PM_OPS:     │
    │   .suspend = snd_sof_suspend │ │   .suspend = intel_suspend   │
    │   .resume  = snd_sof_resume  │ │   .resume  = intel_resume    │
    │ RUNTIME_PM_OPS: ...          │ │ SET_RUNTIME_PM_OPS: ...      │
    └──────────────┬───────────────┘ └──────────────┬───────────────┘
                   │ .suspend                       │ .suspend
                   ▼                                ▼
        sof_suspend(dev, false)           intel_suspend(dev)
        DSP ─▶ SOF_DSP_PM_D3,             bus stop, link down,
        HDA controller reset, D3          codec ─▶ UNATTACHED

    PM core invokes .suspend in reverse-dependency order:
    SOF PCI device first, then the SoundWire master aux device
```

### snd_sof_suspend defers to sof_suspend with the runtime flag clear

[`snd_sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L370) is the SOF system-sleep entry, and it is a thin wrapper that calls the shared [`sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L229) with the runtime flag clear, so the same function body handles both system suspend and runtime suspend with the boolean selecting which platform op runs at the bottom:

```c
/* sound/soc/sof/pm.c:370 */
int snd_sof_suspend(struct device *dev)
{
	return sof_suspend(dev, false);
}
```

Before this runs, the SOF [`prepare`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L159) callback [`snd_sof_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L376) has set the target sleep state. On a Meteor Lake device whose descriptor sets [`use_acpi_target_states`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L32), it reads [`acpi_target_system_state()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/acpi/sleep.c) and maps the ACPI sleep state onto [`system_suspend_target`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L577):

```c
/* sound/soc/sof/pm.c:376 */
int snd_sof_prepare(struct device *dev)
{
	struct snd_sof_dev *sdev = dev_get_drvdata(dev);
	const struct sof_dev_desc *desc = sdev->pdata->desc;

	/* will suspend to S3 by default */
	sdev->system_suspend_target = SOF_SUSPEND_S3;
	...
	if (!desc->use_acpi_target_states)
		return 0;

#if defined(CONFIG_ACPI)
	switch (acpi_target_system_state()) {
	case ACPI_STATE_S0:
		sdev->system_suspend_target = SOF_SUSPEND_S0IX;
		break;
	case ACPI_STATE_S1:
	case ACPI_STATE_S2:
	case ACPI_STATE_S3:
		sdev->system_suspend_target = SOF_SUSPEND_S3;
		break;
	case ACPI_STATE_S4:
		sdev->system_suspend_target = SOF_SUSPEND_S4;
		break;
	case ACPI_STATE_S5:
		sdev->system_suspend_target = SOF_SUSPEND_S5;
		break;
	default:
		break;
	}
#endif

	return 0;
}
```

That switch maps each reported ACPI state onto a suspend target, S0 alone giving S0IX while S1 through S3 fold to S3 and the deeper states pass straight through:

```
    snd_sof_prepare: ACPI sleep state ─▶ system_suspend_target
    ──────────────────────────────────────────────────────────

    acpi_target_system_state()        sdev->system_suspend_target
    ┌─────────────────────────┬──────────────────────────────────┐
    │ (no use_acpi_target..)  │ SOF_SUSPEND_S3   (default)       │
    ├─────────────────────────┼──────────────────────────────────┤
    │ ACPI_STATE_S0           │ SOF_SUSPEND_S0IX                 │
    │ ACPI_STATE_S1           │ SOF_SUSPEND_S3                   │
    │ ACPI_STATE_S2           │ SOF_SUSPEND_S3                   │
    │ ACPI_STATE_S3           │ SOF_SUSPEND_S3                   │
    │ ACPI_STATE_S4           │ SOF_SUSPEND_S4                   │
    │ ACPI_STATE_S5           │ SOF_SUSPEND_S5                   │
    └─────────────────────────┴──────────────────────────────────┘

    set only when desc->use_acpi_target_states; read later by
    snd_sof_dsp_power_target() to pick the DSP D-state
```

### sof_suspend computes the target state, saves context, and powers down

[`sof_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L229) opens by computing the target DSP state with [`snd_sof_dsp_power_target()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L26) and recording the old state, returns early if no platform suspend op exists, then, if the DSP was at [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47), tears down all running pipelines through the [`tear_down_all_pipelines`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) topology op:

```c
/* sound/soc/sof/pm.c:229 */
static int sof_suspend(struct device *dev, bool runtime_suspend)
{
	struct snd_sof_dev *sdev = dev_get_drvdata(dev);
	const struct sof_ipc_pm_ops *pm_ops = sof_ipc_get_ops(sdev, pm);
	const struct sof_ipc_tplg_ops *tplg_ops = sof_ipc_get_ops(sdev, tplg);
	pm_message_t pm_state;
	u32 target_state = snd_sof_dsp_power_target(sdev);
	u32 old_state = sdev->dsp_power_state.state;
	int ret;

	/* do nothing if dsp suspend callback is not set */
	if (!runtime_suspend && !sof_ops(sdev)->suspend)
		return 0;

	if (runtime_suspend && !sof_ops(sdev)->runtime_suspend)
		return 0;

	/* we need to tear down pipelines only if the DSP hardware is
	 * active, which happens for PCI devices. if the device is
	 * suspended, it is brought back to full power and then
	 * suspended again
	 */
	if (tplg_ops && tplg_ops->tear_down_all_pipelines && (old_state == SOF_DSP_PM_D0))
		tplg_ops->tear_down_all_pipelines(sdev, false);

	if (sdev->fw_state != SOF_FW_BOOT_COMPLETE)
		goto suspend;
```

[`snd_sof_dsp_power_target()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L26) is the mapping from platform sleep state to DSP D-state. For S3, S4, or S5 it returns [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50); for S0ix it returns [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) only when a stream asked to ignore suspend, otherwise [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50):

```c
/* sound/soc/sof/pm.c:26 */
static u32 snd_sof_dsp_power_target(struct snd_sof_dev *sdev)
{
	u32 target_dsp_state;

	switch (sdev->system_suspend_target) {
	case SOF_SUSPEND_S5:
	case SOF_SUSPEND_S4:
		/* DSP should be in D3 if the system is suspending to S3+ */
	case SOF_SUSPEND_S3:
		/* DSP should be in D3 if the system is suspending to S3 */
		target_dsp_state = SOF_DSP_PM_D3;
		break;
	case SOF_SUSPEND_S0IX:
		/*
		 * Currently, the only criterion for retaining the DSP in D0
		 * is that there are streams that ignored the suspend trigger.
		 * Additional criteria such Soundwire clock-stop mode and
		 * device suspend latency considerations will be added later.
		 */
		if (snd_sof_stream_suspend_ignored(sdev))
			target_dsp_state = SOF_DSP_PM_D0;
		else
			target_dsp_state = SOF_DSP_PM_D3;
		break;
	default:
		/* This case would be during runtime suspend */
		target_dsp_state = SOF_DSP_PM_D3;
		break;
	}

	return target_dsp_state;
}
```

The S0ix criterion is read from [`snd_sof_stream_suspend_ignored()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.c#L894), which scans the PCM list for any stream that set [`suspend_ignored`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h):

```c
/* sound/soc/sof/sof-audio.c:894 */
bool snd_sof_stream_suspend_ignored(struct snd_sof_dev *sdev)
{
	struct snd_sof_pcm *spcm;

	list_for_each_entry(spcm, &sdev->pcm_list, list) {
		if (spcm->stream[SNDRV_PCM_STREAM_PLAYBACK].suspend_ignored ||
		    spcm->stream[SNDRV_PCM_STREAM_CAPTURE].suspend_ignored)
			return true;
	}

	return false;
}
```

For a full S3 suspend the function then arms stream replay, saves firmware context, and powers the DSP down. The replay-arming runs only on the non-runtime path, and the context save is skipped when the DSP is entering D0:

```c
/* sound/soc/sof/pm.c:229 (replay arm and context save) */
	/* prepare for streams to be resumed properly upon resume */
	if (!runtime_suspend) {
		ret = snd_sof_dsp_hw_params_upon_resume(sdev);
		if (ret < 0) {
			dev_err(sdev->dev,
				"error: setting hw_params flag during suspend %d\n",
				ret);
			return ret;
		}
	}

	pm_state.event = target_state;
	...
	/* Skip to platform-specific suspend if DSP is entering D0 */
	if (target_state == SOF_DSP_PM_D0)
		goto suspend;
	...
	/* notify DSP of upcoming power down */
	if (pm_ops && pm_ops->ctx_save) {
		ret = pm_ops->ctx_save(sdev);
		if (ret == -EBUSY || ret == -EAGAIN) {
			/*
			 * runtime PM has logic to handle -EBUSY/-EAGAIN so
			 * pass these errors up
			 */
			dev_err(sdev->dev, "ctx_save IPC error during suspend: %d\n", ret);
			return ret;
		} else if (ret < 0) {
			/* FW in unexpected state, continue to power down */
			dev_warn(sdev->dev, "ctx_save IPC error: %d, proceeding with suspend\n",
				 ret);
		}
	}
```

[`snd_sof_dsp_hw_params_upon_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L271) runs the platform [`set_hw_params_upon_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op so each suspended stream re-sends its parameters when the DSP comes back, and the [`ctx_save`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L452) member of the [`struct sof_ipc_pm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L451) tells the firmware to checkpoint its state before power is removed:

```c
/* sound/soc/sof/ops.h:271 */
static inline int snd_sof_dsp_hw_params_upon_resume(struct snd_sof_dev *sdev)
{
	if (sof_ops(sdev)->set_hw_params_upon_resume)
		return sof_ops(sdev)->set_hw_params_upon_resume(sdev);
	return 0;
}
```

At the `suspend:` label the function calls the platform power-down op and then resets the firmware boot state, since the DSP is leaving D0:

```c
/* sound/soc/sof/pm.c:229 (suspend tail) */
suspend:

	/* return if the DSP was not probed successfully */
	if (sdev->fw_state == SOF_FW_BOOT_NOT_STARTED)
		return 0;

	/* platform-specific suspend */
	if (runtime_suspend)
		ret = snd_sof_dsp_runtime_suspend(sdev);
	else
		ret = snd_sof_dsp_suspend(sdev, target_state);
	if (ret < 0)
		dev_err(sdev->dev,
			"error: failed to power down DSP during suspend %d\n",
			ret);

	/* Do not reset FW state if DSP is in D0 */
	if (target_state == SOF_DSP_PM_D0)
		return ret;

	/* reset FW state */
	sof_set_fw_state(sdev, SOF_FW_BOOT_NOT_STARTED);
	sdev->enabled_cores_mask = 0;

	return ret;
}
```

[`snd_sof_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L238) dispatches to the platform [`suspend`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op, which on every Intel HDA platform including Meteor Lake is [`hda_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1010):

```c
/* sound/soc/sof/ops.h:238 */
static inline int snd_sof_dsp_suspend(struct snd_sof_dev *sdev,
				      u32 target_state)
{
	if (sof_ops(sdev)->suspend)
		return sof_ops(sdev)->suspend(sdev, target_state);

	return 0;
}
```

The target that wrapper forwards comes from a second mapping, S3 and deeper giving D3 and S0ix holding D0 only when a stream asked to ignore the suspend:

```
    snd_sof_dsp_power_target: suspend target ─▶ DSP D-state
    ────────────────────────────────────────────────────────

    system_suspend_target       target_dsp_state
    ┌────────────────────┬─────────────────────────────────────┐
    │ SOF_SUSPEND_S3     │ SOF_DSP_PM_D3                       │
    │ SOF_SUSPEND_S4     │ SOF_DSP_PM_D3                       │
    │ SOF_SUSPEND_S5     │ SOF_DSP_PM_D3                       │
    │ SOF_SUSPEND_S0IX   │ SOF_DSP_PM_D0  if stream_suspend_   │
    │                    │                    ignored()        │
    │                    │ SOF_DSP_PM_D3  otherwise            │
    │ default (runtime)  │ SOF_DSP_PM_D3                       │
    └────────────────────┴─────────────────────────────────────┘

    snd_sof_stream_suspend_ignored() scans pcm_list for any
    stream with suspend_ignored set (the only D0 criterion)
```

### snd_sof_dsp_power_target reads the target D-state into the recorded state

The target D-state is recorded for the whole device through [`snd_sof_dsp_set_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L287), which guards [`dsp_power_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L572) with the [`power_state_access`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L574) mutex:

```c
/* sound/soc/sof/ops.h:287 */
static inline int
snd_sof_dsp_set_power_state(struct snd_sof_dev *sdev,
			    const struct sof_dsp_power_state *target_state)
{
	guard(mutex)(&sdev->power_state_access);

	if (sof_ops(sdev)->set_power_state)
		return sof_ops(sdev)->set_power_state(sdev, target_state);

	return 0;
}
```

The recorded state is a [`struct sof_dsp_power_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L85), a D-number plus a platform substate, and the D-number is one of [`enum sof_dsp_power_states`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L46):

```c
/* sound/soc/sof/sof-priv.h:85 */
struct sof_dsp_power_state {
	u32 state;
	u32 substate; /* platform-specific */
};
```

```c
/* include/sound/sof.h:46 */
enum sof_dsp_power_states {
	SOF_DSP_PM_D0,
	SOF_DSP_PM_D1,
	SOF_DSP_PM_D2,
	SOF_DSP_PM_D3,
};
```

The platform sleep state that fed [`snd_sof_dsp_power_target()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L26) is one of [`enum sof_system_suspend_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L91), which [`snd_sof_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pm.c#L376) sets and a full S3 maps to [`SOF_SUSPEND_S3`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L94):

```c
/* sound/soc/sof/sof-priv.h:91 */
enum sof_system_suspend_state {
	SOF_SUSPEND_NONE = 0,
	SOF_SUSPEND_S0IX,
	SOF_SUSPEND_S3,
	SOF_SUSPEND_S4,
	SOF_SUSPEND_S5,
};
```

The setter records the chosen D-state in this two-field record, the first field taking one of the D-numbers and the substate carrying the Meteor Lake D0i3 marker:

```
    Recorded DSP power state (under power_state_access mutex)
    ──────────────────────────────────────────────────────────

    struct sof_dsp_power_state         sdev->dsp_power_state
    ┌──────────────────────────────┐
    │ u32 state                    │──┐  one of enum sof_dsp_power_states
    │ u32 substate  (platform)     │  │  ┌──────────────────────────┐
    └──────────────────────────────┘  └─▶│ SOF_DSP_PM_D0   (= 0)    │
                                         │ SOF_DSP_PM_D1            │
    substate on MTL D0 path:             │ SOF_DSP_PM_D2            │
      SOF_HDA_DSP_PM_D0I3, else 0        │ SOF_DSP_PM_D3   (target) │
                                         └──────────────────────────┘

    set by snd_sof_dsp_set_power_state(); a leaving-D0 transition
    also resets fw_state to SOF_FW_BOOT_NOT_STARTED
```

### hda_dsp_suspend branches on the target and runs hda_suspend for D3

[`hda_dsp_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1010) first cancels any opportunistic D0i3 work, then branches on the target. For an S0ix target of [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) it records the D0i3 substate, stops the command DMA, powers down the HDA links through [`hda_bus_ml_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L925), and arms the IPC wake. For a full suspend it runs [`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780) and records the D3 state through [`snd_sof_dsp_set_power_state()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L287):

```c
/* sound/soc/sof/intel/hda-dsp.c:1010 */
int hda_dsp_suspend(struct snd_sof_dev *sdev, u32 target_state)
{
	struct sof_intel_hda_dev *hda = sdev->pdata->hw_pdata;
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct pci_dev *pci = to_pci_dev(sdev->dev);
	const struct sof_dsp_power_state target_dsp_state = {
		.state = target_state,
		.substate = target_state == SOF_DSP_PM_D0 ?
				SOF_HDA_DSP_PM_D0I3 : 0,
	};
	int ret;

	if (!sdev->dspless_mode_selected) {
		/* cancel any attempt for DSP D0I3 */
		cancel_delayed_work_sync(&hda->d0i3_work);

		/* Cancel the microphone privacy work if mic privacy is active */
		if (hda->mic_privacy.active)
			cancel_work_sync(&hda->mic_privacy.work);
	}

	if (target_state == SOF_DSP_PM_D0) {
		...
		return 0;
	}

	/* stop hda controller and power dsp off */
	ret = hda_suspend(sdev, false);
	if (ret < 0) {
		dev_err(bus->dev, "error: suspending dsp\n");
		return ret;
	}

	return snd_sof_dsp_set_power_state(sdev, &target_dsp_state);
}
```

### hda_suspend powers the DSP off and resets the HDA controller

[`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780) is where the DSP cores, the HDA links, and the controller all stop. The chip descriptor on this path is the Meteor Lake [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760), reached through the SOF private [`hw_pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165). It disables DSP interrupts through the chip [`disable_interrupts`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L201) op, enables the codec jack wake through [`hda_codec_jack_wake_enable()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-codec.c#L76), powers down the multi-links, powers down the DSP cores through the chip [`power_down_dsp`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L200) op, stops the HDA controller stream engine through [`hda_dsp_ctrl_stop_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L275), and resets the link through [`hda_dsp_ctrl_link_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L30):

```c
/* sound/soc/sof/intel/hda-dsp.c:780 */
static int hda_suspend(struct snd_sof_dev *sdev, bool runtime_suspend)
{
	struct sof_intel_hda_dev *hda = sdev->pdata->hw_pdata;
	const struct sof_intel_dsp_desc *chip = hda->desc;
	struct hdac_bus *bus = sof_to_bus(sdev);
	bool imr_lost = false;
	int ret, j;
	...
	ret = chip->disable_interrupts(sdev);
	if (ret < 0)
		return ret;

	/* make sure that no irq handler is pending before shutdown */
	synchronize_irq(sdev->ipc_irq);

	hda_codec_jack_wake_enable(sdev, runtime_suspend);

	/* power down all hda links */
	hda_bus_ml_suspend(bus);

	if (sdev->dspless_mode_selected)
		goto skip_dsp;

	ret = chip->power_down_dsp(sdev);
	if (ret < 0) {
		dev_err(sdev->dev, "failed to power down DSP during suspend\n");
		return ret;
	}

	/* reset ref counts for all cores */
	for (j = 0; j < chip->cores_num; j++)
		sdev->dsp_core_ref_count[j] = 0;

	/* disable ppcap interrupt */
	hda_dsp_ctrl_ppcap_enable(sdev, false);
	hda_dsp_ctrl_ppcap_int_enable(sdev, false);
skip_dsp:

	/* disable hda bus irq and streams */
	hda_dsp_ctrl_stop_chip(sdev);

	/* disable LP retention mode */
	snd_sof_pci_update_bits(sdev, PCI_PGCTL,
				PCI_PGCTL_LSRMD_MASK, PCI_PGCTL_LSRMD_MASK);

	/* reset controller */
	ret = hda_dsp_ctrl_link_reset(sdev, true);
	if (ret < 0) {
		dev_err(sdev->dev,
			"error: failed to reset controller during suspend\n");
		return ret;
	}

	/* display codec can powered off after link reset */
	hda_codec_i915_display_power(sdev, false);

	return 0;
}
```

On Meteor Lake the chip descriptor supplies [`mtl_power_down_dsp()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L427) and [`mtl_dsp_disable_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L665) as those ops, reports [`cores_num`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L174) as 3, and reports [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h) as its [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191):

```c
/* sound/soc/sof/intel/mtl.c:760 */
const struct sof_intel_dsp_desc mtl_chip_info = {
	.cores_num = 3,
	...
	.power_down_dsp = mtl_power_down_dsp,
	.disable_interrupts = mtl_dsp_disable_interrupts,
	.hw_ip_version = SOF_INTEL_ACE_1_0,
	.platform = "mtl",
};
```

[`hda_bus_ml_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-mlink.c#L925) walks the HDA link list and powers down each non-alternate link through [`snd_hdac_ext_bus_link_power_down()`](https://elixir.bootlin.com/linux/v7.0/source/sound/hda/core/ext/controller.c#L227):

```c
/* sound/soc/sof/intel/hda-mlink.c:925 */
int hda_bus_ml_suspend(struct hdac_bus *bus)
{
	struct hdac_ext_link *hlink;
	int ret;

	list_for_each_entry(hlink, &bus->hlink_list, list) {
		struct hdac_ext2_link *h2link = hdac_ext_link_to_ext2(hlink);

		if (!h2link->alt) {
			ret = snd_hdac_ext_bus_link_power_down(hlink);
			if (ret < 0)
				return ret;
		}
	}
	return 0;
}
```

[`hda_dsp_ctrl_stop_chip()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L275) disables every stream descriptor interrupt, clears the controller interrupt enables, clears the stream and wake status, stops the command IO, and clears [`chip_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/hdaudio.h#L340) so the next bring-up re-initialises the controller:

```c
/* sound/soc/sof/intel/hda-ctrl.c:275 */
void hda_dsp_ctrl_stop_chip(struct snd_sof_dev *sdev)
{
	struct hdac_bus *bus = sof_to_bus(sdev);
	struct hdac_stream *stream;
	int sd_offset;

	if (!bus->chip_init)
		return;

	/* disable interrupts in stream descriptor */
	list_for_each_entry(stream, &bus->stream_list, list) {
		sd_offset = SOF_STREAM_SD_OFFSET(stream);
		snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR,
					sd_offset +
					SOF_HDA_ADSP_REG_SD_CTL,
					SOF_HDA_CL_DMA_SD_INT_MASK,
					0);
	}

	/* disable SIE for all streams */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR, SOF_HDA_INTCTL,
				SOF_HDA_INT_ALL_STREAM,	0);

	/* disable controller CIE and GIE */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR, SOF_HDA_INTCTL,
				SOF_HDA_INT_CTRL_EN | SOF_HDA_INT_GLOBAL_EN,
				0);
	...
	hda_codec_stop_cmd_io(sdev);
	...
	bus->chip_init = false;
}
```

[`hda_dsp_ctrl_link_reset()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-ctrl.c#L30) drives the GCTL reset bit and waits for the controller to enter or exit reset; the suspend path passes `reset == true` to enter reset, which is the last register write before the PCI device is parked in D3:

```c
/* sound/soc/sof/intel/hda-ctrl.c:30 */
int hda_dsp_ctrl_link_reset(struct snd_sof_dev *sdev, bool reset)
{
	unsigned long timeout;
	u32 gctl = 0;
	u32 val;

	/* 0 to enter reset and 1 to exit reset */
	val = reset ? 0 : SOF_HDA_GCTL_RESET;

	/* enter/exit HDA controller reset */
	snd_sof_dsp_update_bits(sdev, HDA_DSP_HDA_BAR, SOF_HDA_GCTL,
				SOF_HDA_GCTL_RESET, val);

	/* wait to enter/exit reset */
	timeout = jiffies + msecs_to_jiffies(HDA_DSP_CTRL_RESET_TIMEOUT);
	while (time_before(jiffies, timeout)) {
		gctl = snd_sof_dsp_read(sdev, HDA_DSP_HDA_BAR, SOF_HDA_GCTL);
		if ((gctl & SOF_HDA_GCTL_RESET) == val)
			return 0;
		usleep_range(500, 1000);
	}

	/* enter/exit reset failed */
	dev_err(sdev->dev, "error: failed to %s HDA controller gctl 0x%x\n",
		reset ? "reset" : "ready", gctl);
	return -EIO;
}
```

### intel_suspend stops the SoundWire bus

The SoundWire master auxiliary device suspends after the SOF device. [`intel_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L628) returns immediately for a disabled or never-started master, disables runtime PM to keep it from racing with the code below, and then has two cases. If the master is already runtime-suspended it only re-arms the shim wake; otherwise it stops the bus through [`sdw_intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L191):

```c
/* drivers/soundwire/intel_auxdevice.c:628 */
static int __maybe_unused intel_suspend(struct device *dev)
{
	struct sdw_cdns *cdns = dev_get_drvdata(dev);
	struct sdw_intel *sdw = cdns_to_intel(cdns);
	struct sdw_bus *bus = &cdns->bus;
	u32 clock_stop_quirks;
	int ret;

	if (bus->prop.hw_disabled || !sdw->startup_done) {
		dev_dbg(dev, "SoundWire master %d is disabled or not-started, ignoring\n",
			bus->link_id);
		return 0;
	}

	/* Prevent runtime PM from racing with the code below. */
	pm_runtime_disable(dev);

	if (pm_runtime_status_suspended(dev)) {
		dev_dbg(dev, "pm_runtime status: suspended\n");

		clock_stop_quirks = sdw->link_res->clock_stop_quirks;
		...
		return 0;
	}

	ret = sdw_intel_stop_bus(sdw, false);
	if (ret < 0) {
		dev_err(dev, "%s: cannot stop bus: %d\n", __func__, ret);
		return ret;
	}

	return 0;
}
```

[`sdw_intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L191) dispatches through the platform op table to the concrete stop routine, guarded by [`SDW_INTEL_CHECK_OPS`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L133) so a generation without the op returns `-ENOTSUPP`:

```c
/* drivers/soundwire/intel.h:191 */
static inline int sdw_intel_stop_bus(struct sdw_intel *sdw, bool clock_stop)
{
	if (SDW_INTEL_CHECK_OPS(sdw, stop_bus))
		return SDW_INTEL_OPS(sdw, stop_bus)(sdw, clock_stop);
	return -ENOTSUPP;
}
```

On Meteor Lake the [`stop_bus`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw_intel.h#L415) op is wired to [`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205) through the ACE 2.x op table [`sdw_intel_lnl_hw_ops`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_ace2x.c#L1109):

```c
/* drivers/soundwire/intel_ace2x.c:1109 */
const struct sdw_intel_hw_ops sdw_intel_lnl_hw_ops = {
	...
	.stop_bus = intel_stop_bus,
	...
	.link_power_down = intel_link_power_down,
	...
};
```

[`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205) cancels the attach work, runs the Cadence clock stop when the caller asked for it, disables Cadence interrupts through [`sdw_cdns_enable_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1202), powers the link down through [`sdw_intel_link_power_down()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel.h#L205), and arms or disarms the shim wake based on whether the clock was stopped. The system-sleep entry calls it with `clock_stop == false`, so the clock-stop branch is skipped unless a platform quirk later requests it:

```c
/* drivers/soundwire/intel_bus_common.c:205 */
int intel_stop_bus(struct sdw_intel *sdw, bool clock_stop)
{
	struct device *dev = sdw->cdns.dev;
	struct sdw_cdns *cdns = &sdw->cdns;
	bool wake_enable = false;
	int ret;

	cancel_delayed_work_sync(&cdns->attach_dwork);

	if (clock_stop) {
		ret = sdw_cdns_clock_stop(cdns, true);
		if (ret < 0)
			dev_err(dev, "%s: cannot stop clock: %d\n", __func__, ret);
		else
			wake_enable = true;
	}

	ret = sdw_cdns_enable_interrupt(cdns, false);
	if (ret < 0) {
		dev_err(dev, "%s: cannot disable interrupts: %d\n", __func__, ret);
		return ret;
	}

	ret = sdw_intel_link_power_down(sdw);
	if (ret) {
		dev_err(dev, "%s: Link power down failed: %d\n", __func__, ret);
		return ret;
	}

	sdw_intel_shim_wake(sdw, wake_enable);

	return 0;
}
```

### sdw_cdns_clock_stop brings the Cadence master into clock-stop mode

When the platform clock-stop quirks call for it, [`sdw_cdns_clock_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1683) brings the Cadence master into clock-stop mode. It masks the slave interrupts first so it does not have to handle a slave detaching mid-stop, optionally blocks wakes, prepares the attached slaves through [`sdw_bus_prep_clk_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1055), enters clock stop through [`sdw_bus_clk_stop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1155), and waits for the master status bit to confirm. According to the comment, masking the slave interrupts before entering clock stop "helps avoid having to deal with e.g. a Slave becoming UNATTACHED while the clock is being stopped":

```c
/* drivers/soundwire/cadence_master.c:1683 */
int sdw_cdns_clock_stop(struct sdw_cdns *cdns, bool block_wake)
{
	bool slave_present = false;
	struct sdw_slave *slave;
	int ret;

	sdw_cdns_check_self_clearing_bits(cdns, __func__, false, 0);

	/* Check suspend status */
	if (sdw_cdns_is_clock_stop(cdns)) {
		dev_dbg(cdns->dev, "Clock is already stopped\n");
		return 0;
	}

	/*
	 * Before entering clock stop we mask the Slave
	 * interrupts. This helps avoid having to deal with e.g. a
	 * Slave becoming UNATTACHED while the clock is being stopped
	 */
	cdns_enable_slave_interrupts(cdns, false);
	...
	list_for_each_entry(slave, &cdns->bus.slaves, node) {
		if (slave->status == SDW_SLAVE_ATTACHED ||
		    slave->status == SDW_SLAVE_ALERT) {
			slave_present = true;
			break;
		}
	}
	...
	/* Prepare slaves for clock stop */
	if (slave_present) {
		ret = sdw_bus_prep_clk_stop(&cdns->bus);
		if (ret < 0 && ret != -ENODATA) {
			dev_err(cdns->dev, "prepare clock stop failed %d\n", ret);
			return ret;
		}
	}

	/*
	 * Enter clock stop mode and only report errors if there are
	 * Slave devices present (ALERT or ATTACHED)
	 */
	ret = sdw_bus_clk_stop(&cdns->bus);
	if (ret < 0 && slave_present && ret != -ENODATA) {
		dev_err(cdns->dev, "bus clock stop failed %d\n", ret);
		return ret;
	}

	ret = cdns_set_wait(cdns, CDNS_MCP_STAT,
			    CDNS_MCP_STAT_CLK_STOP,
			    CDNS_MCP_STAT_CLK_STOP);
	if (ret < 0)
		dev_err(cdns->dev, "Clock stop failed %d\n", ret);

	return ret;
}
```

[`sdw_cdns_enable_interrupt()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/cadence_master.c#L1202) is then called with `state == false` from [`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205) to mask the master interrupt sources and cancel any queued status work, so no status-change interrupt fires while the link is down:

```c
/* drivers/soundwire/cadence_master.c:1202 */
int sdw_cdns_enable_interrupt(struct sdw_cdns *cdns, bool state)
{
	u32 slave_intmask0 = 0;
	u32 slave_intmask1 = 0;
	u32 mask = 0;

	if (!state)
		goto update_masks;
	...
update_masks:
	...
	cdns->interrupt_enabled = state;
	...
	if (!state)
		cancel_work_sync(&cdns->work);

	cdns_writel(cdns, CDNS_MCP_SLAVE_INTMASK0, slave_intmask0);
	cdns_writel(cdns, CDNS_MCP_SLAVE_INTMASK1, slave_intmask1);
	cdns_writel(cdns, CDNS_MCP_INTMASK, mask);

	return 0;
}
```

The clock-stop helper runs its own ordered steps, masking the slave interrupts before it prepares the attached peripherals, broadcasts the stop, and waits on the master status bit:

```
    sdw_cdns_clock_stop(): ordered entry into clock-stop mode
    ──────────────────────────────────────────────────────────

    ┌──────────────────────────────────────────────────────────┐
    │ sdw_cdns_is_clock_stop() ?  ─▶ already stopped, return 0 │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ cdns_enable_slave_interrupts(false)   mask Slave IRQ     │
    │   (avoids a Slave going UNATTACHED mid clock-stop)       │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ scan bus.slaves: ATTACHED or ALERT ?  ─▶ slave_present   │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼  (if slave_present)
    ┌──────────────────────────────────────────────────────────┐
    │ sdw_bus_prep_clk_stop()        prepare attached Slaves   │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ sdw_bus_clk_stop()             broadcast clock-stop      │
    └────────────────────────────┬─────────────────────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────────┐
    │ cdns_set_wait(CDNS_MCP_STAT, CDNS_MCP_STAT_CLK_STOP)     │
    │   wait for the master STAT bit to confirm                │
    └──────────────────────────────────────────────────────────┘
```

### The codec lands at SDW_SLAVE_UNATTACHED

The codec's attachment state is the part of the SoundWire stack the codec driver observes through its [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op. The transition to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) is driven by [`sdw_clear_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L2023), which the Intel master calls from the resume side, at [`intel_resume()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L715) and [`intel_resume_runtime()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_auxdevice.c#L771), so that every slave is treated as detached after the bus was stopped, forcing re-enumeration when the link comes back. It walks the assigned devices and, for any slave not already at [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95), modifies the recorded status and notifies the codec:

```c
/* drivers/soundwire/bus.c:2023 */
void sdw_clear_slave_status(struct sdw_bus *bus, u32 request)
{
	struct sdw_slave *slave;
	int i;

	/* Check all non-zero devices */
	for (i = 1; i <= SDW_MAX_DEVICES; i++) {
		mutex_lock(&bus->bus_lock);
		if (test_bit(i, bus->assigned) == false) {
			mutex_unlock(&bus->bus_lock);
			continue;
		}
		mutex_unlock(&bus->bus_lock);

		slave = sdw_get_slave(bus, i);
		if (!slave)
			continue;

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

[`sdw_modify_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L928) is the recorded-status write. On a transition to [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) it reinitialises the enumeration and initialisation completions so a later attach waits for fresh enumeration, then stores the new [`status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L665) under the bus lock:

```c
/* drivers/soundwire/bus.c:928 */
static void sdw_modify_slave_status(struct sdw_slave *slave,
				    enum sdw_slave_status status)
{
	struct sdw_bus *bus = slave->bus;

	mutex_lock(&bus->bus_lock);
	...
	if (status == SDW_SLAVE_UNATTACHED) {
		dev_dbg(&slave->dev,
			"initializing enumeration and init completion for Slave %d\n",
			slave->dev_num);

		reinit_completion(&slave->enumeration_complete);
		reinit_completion(&slave->initialization_complete);

	} else if ((status == SDW_SLAVE_ATTACHED) &&
		   (slave->status == SDW_SLAVE_UNATTACHED)) {
		...
		complete_all(&slave->enumeration_complete);
	}
	slave->status = status;
	mutex_unlock(&bus->bus_lock);
}
```

[`sdw_update_slave_status()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/bus.c#L1854) is the call into the codec driver. It takes the per-slave lock and, if the slave was probed, calls the bound driver's [`update_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L620) op (a member of [`struct sdw_slave_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L616)) with the new status:

```c
/* drivers/soundwire/bus.c:1854 */
static int sdw_update_slave_status(struct sdw_slave *slave,
				   enum sdw_slave_status status)
{
	int ret = 0;

	mutex_lock(&slave->sdw_dev_lock);

	if (slave->probed) {
		struct device *dev = &slave->dev;
		struct sdw_driver *drv = drv_to_sdw_driver(dev->driver);

		if (drv->ops && drv->ops->update_status)
			ret = drv->ops->update_status(slave, status);
	}

	mutex_unlock(&slave->sdw_dev_lock);

	return ret;
}
```

For the Realtek RT722, [`rt722_sdca_update_status()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L208) is that op. On [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) it clears the codec's [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) flag, which forces a full I/O re-initialization through [`rt722_sdca_io_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca-sdw.c#L239) the next time the device reattaches:

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

The [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) flag the op clears is a field of the RT722 private state, the gate that the attach path reads to decide whether a fresh I/O init is needed:

```c
/* sound/soc/codecs/rt722-sdca.h:18 */
struct  rt722_sdca_priv {
	struct regmap *regmap;
	struct snd_soc_component *component;
	struct sdw_slave *slave;
	struct sdw_bus_params params;
	bool hw_init;
	bool first_hw_init;
	...
};
```

The status the codec observes is one value of [`enum sdw_slave_status`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L94), where [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) is value 0:

```c
/* include/linux/soundwire/sdw.h:94 */
enum sdw_slave_status {
	SDW_SLAVE_UNATTACHED = 0,
	SDW_SLAVE_ATTACHED = 1,
	SDW_SLAVE_ALERT = 2,
	SDW_SLAVE_RESERVED = 3,
};
```

After the codec is marked unattached and the bus clock is stopped, the link is powered down in [`intel_stop_bus()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/soundwire/intel_bus_common.c#L205) and the HDA controller has already been reset and parked at PCI D3 by the [`hda_suspend()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L780) path, leaving the DSP-and-SoundWire half of the audio stack quiesced. Each object now sits in its defined low-power landing state. The DSP is at [`SOF_DSP_PM_D3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L50) with its firmware state reset to [`SOF_FW_BOOT_NOT_STARTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L40), the HDA controller is reset in D3, the SoundWire link is powered down, and the RT722 codec is at [`SDW_SLAVE_UNATTACHED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/soundwire/sdw.h#L95) with [`hw_init`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/codecs/rt722-sdca.h#L23) cleared so the next attach re-initialises it.

```
    SoundWire slave status the codec observes (enum sdw_slave_status)
    ─────────────────────────────────────────────────────────────────

         ┌──────────────────────┐      detach forced on bus stop
         │ SDW_SLAVE_ATTACHED   │ ─────────────┐
         │  (= 1)               │              │ sdw_clear_slave_status
         └──────────────────────┘              │ (MASTER_RESET)
         ┌──────────────────────┐              ▼
         │ SDW_SLAVE_ALERT      │ ───▶ ┌──────────────────────────┐
         │  (= 2)               │      │ SDW_SLAVE_UNATTACHED     │
         └──────────────────────┘      │  (= 0)                   │
                                       └────────────┬─────────────┘
    each transition runs:                           │ update_status op
      sdw_modify_slave_status  reinit enum/init      ▼
        completions, store status         rt722_sdca_update_status:
      sdw_update_slave_status  ─▶ driver     rt722->hw_init = false
        update_status op                   (forces rt722_sdca_io_init
                                            on the next ATTACHED)
```
