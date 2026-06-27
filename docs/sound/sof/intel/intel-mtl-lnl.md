# SOF Intel Meteor Lake and Lunar Lake

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Sound Open Firmware drives the audio DSP of an Intel SoC through one platform-agnostic core object, [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and binds it to a given silicon generation through two const objects the core reaches from [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), a hardware map [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) holding the register offsets, core count, IPC doorbell, and an [`enum sof_intel_hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L14) tag, and a function pointer struct [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) that abstracts DSP boot, register IO, IPC send, and the PCM and DAI callbacks; Meteor Lake declares [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760) tagged [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) and builds its ops in [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) by copying [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) and overriding the IPC, shutdown, firmware-run, and core-power callbacks, while Lunar Lake declares [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164) tagged [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) and in [`sof_lnl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L103) inherits the Meteor Lake build before patching the probe, remove, post-firmware-run, and resume callbacks, with [`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190) handing the matched descriptor to the core through [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630).

```
    generic SOF core (no platform constants of its own)
    ┌────────────────────────────────────────────────────────────┐
    │  struct snd_sof_dev                                        │
    │    pdata ─▶ snd_sof_pdata.desc ─▶ sof_dev_desc             │
    │    bar[], ipc, fw_state, dsp_power_state                   │
    └───────────────────────┬────────────────────────────────────┘
                            │ reads at probe
                ┌───────────┴─────────────────┐
                ▼                              ▼
    sof_dev_desc.chip_info          sof_dev_desc.ops
    struct sof_intel_dsp_desc       struct snd_sof_dsp_ops
    ┌───────────────────────┐       ┌───────────────────────┐
    │ cores_num             │       │ probe / run / shutdown│
    │ ipc_req / ipc_ack     │       │ block_read / write    │
    │ rom_status_reg        │       │ send_msg / irq_thread │
    │ ssp_count / ssp_base  │       │ core_get / core_put   │
    │ sdw_shim_base         │       │ resume / runtime_res. │
    │ hw_ip_version         │       │ drv[] (DAI drivers)   │
    └───────────┬───────────┘       └───────────▲───────────┘
                │                                │ built by ops_init
    ┌───────────┴───────────┐       ┌────────────┴──────────┐
    │ MTL: mtl_chip_info    │       │ MTL: sof_mtl_set_ops  │
    │      ACE_1_0          │       │   memcpy(common_ops)  │
    │ ARL-S: arl_s_chip_info│       │   + override IPC/core │
    │      ACE_1_0          │       │ LNL: sof_lnl_set_ops  │
    │ LNL: lnl_chip_info    │       │   calls MTL set, then │
    │      ACE_2_0          │       │   override probe/PM   │
    └───────────────────────┘       └───────────────────────┘
```

## SUMMARY

The SOF core is one driver that supports every Intel DSP generation by deferring all platform detail to a pair of const objects reachable from [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128). The [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) member points at a [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) that records the fixed hardware facts of the platform, the DSP core count in [`cores_num`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L174), the IPC request and acknowledge register offsets and their busy and done masks in [`ipc_req`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L177) and [`ipc_ack`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173), the boot ROM status register in [`rom_status_reg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L182), the SSP count and base in [`ssp_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L184) and [`ssp_base_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L185), the SoundWire shim and ALH bases in [`sdw_shim_base`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L186) and [`sdw_alh_base`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L187), and the audio DSP IP generation in the [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) tag of [`enum sof_intel_hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L14). The [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) member points at a [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) function pointer struct that abstracts the DSP HW architecture and the IO busses between host and DSP, grouping the [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L169) and [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L172) callbacks, the DSP boot callback [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L175), the block IO accessors [`block_read`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L200) and [`block_write`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L203), the IPC callback [`send_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L220), the power-management callbacks, and the [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) array of audio DAI drivers.

Meteor Lake declares [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760) with three cores and a [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) of [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23), and a near-identical [`arl_s_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L789) covers Arrow Lake S with two cores and the same IP version. Its ops are assembled by [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702), which copies the whole shared [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) with one [`memcpy()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fortify-string.h#L688) and then replaces the IPC doorbell thread with [`mtl_ipc_irq_thread()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L558), the IPC send with [`mtl_ipc_send_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L99), the [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L172) with [`hda_dsp_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1148), and the per-core power callbacks with [`mtl_dsp_core_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L672) and [`mtl_dsp_core_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L685). Lunar Lake declares [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164) with five cores, the Lunar Lake ROM status register [`LNL_DSP_REG_HFDSC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.h#L12), and a [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) of [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24). Its ops are assembled by [`sof_lnl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L103), which calls [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) first and then overrides [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L169), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L170), [`post_fw_run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L290), [`resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L299), and [`runtime_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L301) with Lunar Lake variants that offload the DMIC and SSP back ends to the DSP. The SSP and DMIC back-end DAI ops are gated on the IP version inside [`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) and [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723), so only an ACE 2.0 platform such as Lunar Lake receives [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) and [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) on its back-end DAIs.

The PCI binding is one [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) per platform. [`mtl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31) names [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760) and the [`sof_mtl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26) callback, [`lnl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L31) names [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164) and [`sof_lnl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L26), and both descriptors sit in a [`struct pci_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L44) table the PCI core matches. The matched probe runs [`hda_pci_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L978), which forwards to [`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190) to copy the descriptor into a fresh [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) and call [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630), where the core allocates [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and later runs the platform [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) to populate its ops.

## SPECIFICATIONS

The [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) core and its platform descriptors are Linux kernel software constructs and have no standalone hardware specification. The audio DSP they drive is part of an Intel SoC reached over the HD Audio PCI function on x86-64 ACPI platforms, and the host controller register interface those drivers program is defined by the Intel High Definition Audio Specification. The DSP IPC protocol and the firmware image format the [`mtl_ipc_send_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L99) doorbell and the loader callbacks implement are defined by the Sound Open Firmware project rather than by a public hardware specification.

## LINUX KERNEL

### Generic core types (sof-priv.h, sof.h)

- [`'\<struct snd_sof_dev\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547): the platform-agnostic device-level object the core allocates; holds the [`bar`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) BAR pointers, the [`ipc_lock`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and [`hw_lock`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) spinlocks, the [`fw_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) firmware-boot state, the [`dsp_power_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and the [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) back pointer through which the platform descriptor is reached
- [`'\<struct snd_sof_dsp_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165): the function pointer struct abstracting the DSP HW architecture; groups [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L169)/[`remove`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L170)/[`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L172), the DSP boot [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L175), block IO, IPC [`send_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L220), firmware load, PCM callbacks, PM, and the [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) DAI array
- [`'\<struct snd_sof_pdata\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75): the platform data the bus probe fills; carries the [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) descriptor pointer, the file-path overrides, the resolved machine, and the [`hw_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) private block
- [`'\<struct sof_dev_desc\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128): the per-platform descriptor naming the [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) function pointer struct, the [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) callback, the machine lists, and the default firmware, library, and topology paths

### Intel hardware descriptor (intel/shim.h)

- [`'\<struct sof_intel_dsp_desc\>':'sound/soc/sof/intel/shim.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173): the Intel DSP hardware descriptor recording [`cores_num`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L174), the IPC request/ack offsets and masks, [`rom_status_reg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L182) and [`rom_init_timeout`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173), [`ssp_count`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L184)/[`ssp_base_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L185), the SoundWire [`sdw_shim_base`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L186) and [`sdw_alh_base`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L187), the [`d0i3_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L188), and the SoundWire and interrupt helper callbacks
- [`'\<enum sof_intel_hw_ip_version\>':'sound/soc/sof/intel/shim.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L14): the audio DSP IP generation tag; the values this page uses are [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) (Meteor Lake) and [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) (Lunar Lake)
- [`'\<get_chip_info\>':'sound/soc/sof/intel/shim.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213): the inline returning [`pdata->desc->chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) cast to [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173), used wherever Intel code needs the [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191)

### Meteor Lake descriptor and ops (intel/mtl.c)

- [`'mtl_chip_info':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760): the Meteor Lake [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) instance with three cores and [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23)
- [`'arl_s_chip_info':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L789): the Arrow Lake S instance, two cores, otherwise the same register layout and [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23)
- [`'\<sof_mtl_set_ops\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702): copy [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17), then override the shutdown, doorbell, IPC, debug, firmware-run, and core-power callbacks and call [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745)
- [`'\<mtl_ipc_send_msg\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L99): write the message to the mailbox and ring the host-to-DSP doorbell by setting [`MTL_DSP_REG_HFIPCXIDR_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.h#L42) in [`MTL_DSP_REG_HFIPCXIDR`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.h#L41)
- [`'\<mtl_ipc_irq_thread\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L558): the threaded IPC handler [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) installs as [`irq_thread`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L217); handles the reply done bit, the DSP-initiated message, and any delayed TX
- [`'\<mtl_dsp_core_get\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L672) / [`'\<mtl_dsp_core_put\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L685): power a DSP core up or down, special-casing [`SOF_DSP_PRIMARY_CORE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L80) through [`mtl_dsp_core_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L355) and delegating secondary cores to the IPC pm op
- [`'\<mtl_dsp_post_fw_run\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L301): the Meteor Lake [`post_fw_run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L290); start the SoundWire links on first boot and enable the SoundWire interrupt

### Lunar Lake descriptor and ops (intel/lnl.c)

- [`'lnl_chip_info':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164): the Lunar Lake [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) instance with five cores, [`LNL_DSP_REG_HFDSC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.h#L12) as the ROM status register, and [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24)
- [`'\<sof_lnl_set_ops\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L103): call [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702), then override [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L169), [`remove`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L170), [`post_fw_run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L290), [`resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L299), and [`runtime_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L301) with the Lunar Lake variants
- [`'\<lnl_hda_dsp_probe\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L41) / [`'\<lnl_hda_dsp_remove\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L52): wrap [`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) and the common remove, toggling the DMIC/SSP offload through [`hdac_bus_offload_dmic_ssp()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L24)
- [`'\<lnl_dsp_post_fw_run\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L86): the Lunar Lake [`post_fw_run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L290); enables IMR boot on first boot without the SoundWire startup the Meteor Lake version performs
- [`'\<lnl_hda_dsp_resume\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L64) / [`'\<lnl_hda_dsp_runtime_resume\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L75): wrap [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) and [`hda_dsp_runtime_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L954) and re-enable the DMIC/SSP offload after the DSP comes back
- [`'\<lnl_dsp_check_sdw_irq\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L131): the [`check_sdw_irq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) the Lunar Lake descriptor installs, using the embedded multi-link table
- [`'\<lnl_dsp_disable_interrupts\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L139): the [`disable_interrupts`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L201) the descriptor installs
- [`'\<lnl_sdw_check_wakeen_irq\>':'sound/soc/sof/intel/lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L146): the [`check_sdw_wakeen_irq`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L195) the descriptor installs, reading the global HDAudio STATESTS

### Shared HDA ops and DAI op binding (intel/hda-common-ops.c, intel/hda-dai.c)

- [`'sof_hda_common_ops':'sound/soc/sof/intel/hda-common-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17): the shared SKL+ HDAudio [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) both platforms copy as their starting point, supplying [`block_read`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L200), [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L175), the PCM callbacks, the PM callbacks, and the [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) DAI array
- [`'\<hda_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745): attach [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354) to the iDisp, Analog, and Digital DAIs, then call [`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) and [`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723)
- [`'\<ssp_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) / [`'\<dmic_set_dai_drv_ops\>':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723): install [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) and [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) on the SSP and DMIC back-end DAIs, gated on [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) at or above [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24)
- [`'hda_dai_ops':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354): the SoundWire and HDAudio back-end DAI function pointer struct attached to the iDisp/Analog/Digital link DAIs on both platforms
- [`'skl_dai':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L917): the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array of [`SOF_SKL_NUM_DAIS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L424) entries both platforms point [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) at

### PCI binding and probe (intel/pci-mtl.c, intel/pci-lnl.c, sof-pci-dev.c, core.c)

- [`'mtl_desc':'sound/soc/sof/intel/pci-mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31): the Meteor Lake [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) naming [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760), [`sof_mtl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26), and the IPC4 firmware paths
- [`'lnl_desc':'sound/soc/sof/intel/pci-lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L31): the Lunar Lake [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) naming [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164), [`sof_lnl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L26), and the [`on_demand_dsp_boot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) flag
- [`'\<sof_mtl_ops_init\>':'sound/soc/sof/intel/pci-mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26) / [`'\<sof_lnl_ops_init\>':'sound/soc/sof/intel/pci-lnl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L26): the [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) callbacks that fill the static per-module ops struct by calling the set-ops function
- [`'\<sof_pci_probe\>':'sound/soc/sof/sof-pci-dev.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190): allocate a [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75), copy the matched descriptor into [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75), apply the file-path overrides, and call [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630)
- [`'\<hda_pci_intel_probe\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L978): the [`struct pci_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h#L1019) probe both modules register, which forwards to [`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190)
- [`'\<snd_sof_device_probe\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630): allocate [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), record the [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), select the IPC ops with [`sof_init_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630), and continue the probe that runs the platform [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the ASoC platform component model under which the SOF DSP registers its PCM and DAI drivers
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC architecture overview that frames the codec, platform, and machine split a SOF card binds
- [`Documentation/sound/soc/dai.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dai.rst): the Digital Audio Interface concept the [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L917) entries implement
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end and back-end DAI model the SSP, DMIC, and SoundWire back-end DAIs use
- [`Documentation/driver-api/soundwire/stream.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/driver-api/soundwire/stream.rst): the SoundWire stream lifecycle the Lunar Lake back-end DAI ops drive

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [Sound Open Firmware on the Linux kernel ASoC tree](https://github.com/thesofproject/linux)
- [ALSA System on Chip (ASoC) section, ALSA project wiki](https://www.alsa-project.org/wiki/ASoC)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The platform layer presents two interfaces to the generic core, a data interface and a behaviour interface, both reached through [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128). The data interface is [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), a const [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) the core reads for fixed register offsets and the IP version. The behaviour interface is [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), a [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) the core calls for every action that touches hardware. Both descriptors live for the lifetime of the module, the [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) as a read-only constant and the per-module ops struct as static storage the [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) callback fills once.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760) / [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164) | static const initializer in the module | module load to unload |
| [`mtl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31) / [`lnl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L31) | static const initializer; reached via [`pci_device_id.driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L44) | module load to unload |
| filled per-module ops struct | [`sof_mtl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26) / [`sof_lnl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L26) calling the set-ops function | static; written once at probe |
| [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) | [`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190) (devm) | the PCI device |
| [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) | [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630) (devm) | the PCI device |

The table below maps the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) fields the two builders set and the value each platform supplies. A field marked inherited is the value [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) left in place that [`sof_lnl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L103) did not override.

| ops field | Meteor Lake source | Lunar Lake source |
|-----------|--------------------|--------------------|
| [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L169) | [`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) (from common) | [`lnl_hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L41) (offloads DMIC/SSP) |
| [`remove`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L170) | [`hda_dsp_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) (from common) | [`lnl_hda_dsp_remove()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L52) |
| [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L175) | [`hda_dsp_cl_boot_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-loader.c#L339) (from common) | inherited |
| [`block_read`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L200) / [`block_write`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L203) | [`sof_block_read()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/iomem-utils.c#L115) (from common) | inherited |
| [`send_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L220) | [`mtl_ipc_send_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L99) | inherited from MTL |
| [`irq_thread`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L217) | [`mtl_ipc_irq_thread()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L558) | inherited from MTL |
| [`shutdown`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L172) | [`hda_dsp_shutdown()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L1148) | inherited from MTL |
| [`core_get`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L178) / [`core_put`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L179) | [`mtl_dsp_core_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L672) / [`mtl_dsp_core_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L685) | inherited from MTL |
| [`post_fw_run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L290) | [`mtl_dsp_post_fw_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L301) | [`lnl_dsp_post_fw_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L86) |
| [`resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L299) / [`runtime_resume`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L301) | [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) (from common) | [`lnl_hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L64) / [`lnl_hda_dsp_runtime_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L75) |
| [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) (DAI array) | [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L917), [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354) only | [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L917) plus [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) and [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486) |

## DETAILS

### The descriptor pair and the core that reads it

The generic [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) holds no platform constants of its own. Every platform fact is reached by following [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) to the [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) and then [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) to the [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), which carries the two interface pointers, [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) and [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), and the [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) callback that builds the second:

```c
/* include/sound/sof.h:128 */
struct sof_dev_desc {
	/* list of machines using this configuration */
	struct snd_soc_acpi_mach *machines;
	struct snd_sof_of_mach *of_machines;

	/* alternate list of machines using this configuration */
	struct snd_soc_acpi_mach *alt_machines;

	bool use_acpi_target_states;
	...
	/* chip information for dsp */
	const void *chip_info;
	...
	const struct snd_sof_dsp_ops *ops;
	int (*ops_init)(struct snd_sof_dev *sdev);
	void (*ops_free)(struct snd_sof_dev *sdev);
};
```

The [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) member is typed `const void *` because the descriptor is shared across every SOF backend, and the Intel side casts it to [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173). That struct is the read-only hardware map the Intel code consults for register offsets, the doorbell layout, and the IP version:

```c
/* sound/soc/sof/intel/shim.h:173 */
struct sof_intel_dsp_desc {
	int cores_num;
	int host_managed_cores_mask;
	int init_core_mask; /* cores available after fw boot */
	int ipc_req;
	int ipc_req_mask;
	int ipc_ack;
	int ipc_ack_mask;
	int ipc_ctl;
	int rom_status_reg;
	int rom_init_timeout;
	int ssp_count;			/* ssp count of the platform */
	int ssp_base_offset;		/* base address of the SSPs */
	u32 sdw_shim_base;
	u32 sdw_alh_base;
	u32 d0i3_offset;
	u32 quirks;
	const char *platform;
	enum sof_intel_hw_ip_version hw_ip_version;
	int (*read_sdw_lcount)(struct snd_sof_dev *sdev);
	void (*enable_sdw_irq)(struct snd_sof_dev *sdev, bool enable);
	bool (*check_sdw_irq)(struct snd_sof_dev *sdev);
	bool (*check_sdw_wakeen_irq)(struct snd_sof_dev *sdev);
	void (*sdw_process_wakeen)(struct snd_sof_dev *sdev);
	bool (*check_ipc_irq)(struct snd_sof_dev *sdev);
	bool (*check_mic_privacy_irq)(struct snd_sof_dev *sdev, bool alt, int elid);
	void (*process_mic_privacy)(struct snd_sof_dev *sdev, bool alt, int elid);
	int (*power_down_dsp)(struct snd_sof_dev *sdev);
	int (*disable_interrupts)(struct snd_sof_dev *sdev);
	int (*cl_init)(struct snd_sof_dev *sdev, int stream_tag, bool imr_boot);
};
```

Intel code reaches this struct through one inline, [`get_chip_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213), which performs exactly the [`desc->chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) dereference and cast:

```c
/* sound/soc/sof/intel/shim.h:213 */
static inline const struct sof_intel_dsp_desc *get_chip_info(struct snd_sof_pdata *pdata)
{
	const struct sof_dev_desc *desc = pdata->desc;

	return desc->chip_info;
}
```

The [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) field is an [`enum sof_intel_hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L14), an ordered list of the Intel audio DSP IP generations where each comment names the SoC family the value covers:

```c
/* sound/soc/sof/intel/shim.h:14 */
enum sof_intel_hw_ip_version {
	SOF_INTEL_TANGIER,
	SOF_INTEL_BAYTRAIL,
	SOF_INTEL_BROADWELL,
	SOF_INTEL_CAVS_1_5,	/* SkyLake, KabyLake, AmberLake */
	SOF_INTEL_CAVS_1_5_PLUS,/* ApolloLake, GeminiLake */
	SOF_INTEL_CAVS_1_8,	/* CannonLake, CometLake, CoffeeLake */
	SOF_INTEL_CAVS_2_0,	/* IceLake, JasperLake */
	SOF_INTEL_CAVS_2_5,	/* TigerLake, AlderLake */
	SOF_INTEL_ACE_1_0,	/* MeteorLake */
	SOF_INTEL_ACE_2_0,	/* LunarLake */
	SOF_INTEL_ACE_3_0,	/* PantherLake */
	SOF_INTEL_ACE_4_0,	/* NovaLake */
};
```

Because the values are ordered, a comparison such as [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) at or above [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) selects Lunar Lake and later while excluding Meteor Lake, which the DAI op binding below relies on.

```
    enum sof_intel_hw_ip_version (ordered, low ─▶ high)
    ──────────────────────────────────────────────────────

      SOF_INTEL_TANGIER
      SOF_INTEL_BAYTRAIL
      SOF_INTEL_BROADWELL
      SOF_INTEL_CAVS_1_5        SkyLake, KabyLake, AmberLake
      SOF_INTEL_CAVS_1_5_PLUS   ApolloLake, GeminiLake
      SOF_INTEL_CAVS_1_8        CannonLake, CometLake, CoffeeLake
      SOF_INTEL_CAVS_2_0        IceLake, JasperLake
      SOF_INTEL_CAVS_2_5        TigerLake, AlderLake
      SOF_INTEL_ACE_1_0         MeteorLake    ◀── mtl_chip_info
    ───────────────────────────────────────────  >= ACE_2_0 cut
      SOF_INTEL_ACE_2_0         LunarLake     ◀── lnl_chip_info
      SOF_INTEL_ACE_3_0         PantherLake
      SOF_INTEL_ACE_4_0         NovaLake

    chip->hw_ip_version >= SOF_INTEL_ACE_2_0 selects LunarLake and later,
    so SSP / DMIC back-end ops attach on LNL but not on MTL
```

### The function pointer struct the core drives

The behaviour interface is [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), described by its own comment as the abstraction of the DSP HW architecture and the IO busses between the host CPU and the DSP. The core calls these callbacks for the DSP boot, the register and block IO, the IPC send, the PCM stream operations, and power management. Each callback is annotated mandatory or optional:

```c
/* sound/soc/sof/sof-priv.h:165 */
struct snd_sof_dsp_ops {

	/* probe/remove/shutdown */
	int (*probe_early)(struct snd_sof_dev *sof_dev); /* optional */
	int (*probe)(struct snd_sof_dev *sof_dev); /* mandatory */
	void (*remove)(struct snd_sof_dev *sof_dev); /* optional */
	void (*remove_late)(struct snd_sof_dev *sof_dev); /* optional */
	int (*shutdown)(struct snd_sof_dev *sof_dev); /* optional */

	/* DSP core boot / reset */
	int (*run)(struct snd_sof_dev *sof_dev); /* mandatory */
	...
	/* DSP core get/put */
	int (*core_get)(struct snd_sof_dev *sof_dev, int core); /* optional */
	int (*core_put)(struct snd_sof_dev *sof_dev, int core); /* optional */
	...
	/* memcpy IO */
	int (*block_read)(struct snd_sof_dev *sof_dev,
			  enum snd_sof_fw_blk_type type, u32 offset,
			  void *dest, size_t size); /* mandatory */
	int (*block_write)(struct snd_sof_dev *sof_dev,
			   enum snd_sof_fw_blk_type type, u32 offset,
			   void *src, size_t size); /* mandatory */
	...
	/* ipc */
	irqreturn_t (*irq_thread)(int irq, void *context); /* optional */
	...
	int (*send_msg)(struct snd_sof_dev *sof_dev,
			struct snd_sof_ipc_msg *msg); /* mandatory */
	...
	/* host read DSP stream data */
	int (*post_fw_run)(struct snd_sof_dev *sof_dev); /* optional */
	...
	/* DSP PM */
	int (*resume)(struct snd_sof_dev *sof_dev); /* optional */
	int (*runtime_resume)(struct snd_sof_dev *sof_dev); /* optional */
	...
	/* DAI ops */
	struct snd_soc_dai_driver *drv;
	int num_drv;
	...
};
```

The [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L351) members are the bridge from the SOF DSP layer to the ASoC layer. They hold the [`struct snd_soc_dai_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) array the SOF component registers, and the per-DAI [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) pointers inside that array are what the platform builder patches per IP version through [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745).

### Meteor Lake builds its ops by copy then override

The Meteor Lake ops are not written field by field. [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) starts from the shared [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) with a single [`memcpy()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fortify-string.h#L688) and then replaces only the callbacks where Meteor Lake differs from the generic SKL+ HDAudio behaviour:

```c
/* sound/soc/sof/intel/mtl.c:702 */
int sof_mtl_set_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *dsp_ops)
{
	struct sof_ipc4_fw_data *ipc4_data;

	/* common defaults */
	memcpy(dsp_ops, &sof_hda_common_ops, sizeof(struct snd_sof_dsp_ops));

	/* shutdown */
	dsp_ops->shutdown = hda_dsp_shutdown;

	/* doorbell */
	dsp_ops->irq_thread = mtl_ipc_irq_thread;

	/* ipc */
	dsp_ops->send_msg = mtl_ipc_send_msg;
	dsp_ops->get_mailbox_offset = mtl_dsp_ipc_get_mailbox_offset;
	dsp_ops->get_window_offset = mtl_dsp_ipc_get_window_offset;
	...
	/* pre/post fw run */
	dsp_ops->pre_fw_run = mtl_dsp_pre_fw_run;
	dsp_ops->post_fw_run = mtl_dsp_post_fw_run;
	...
	/* dsp core get/put */
	dsp_ops->core_get = mtl_dsp_core_get;
	dsp_ops->core_put = mtl_dsp_core_put;
	...
	dsp_ops->set_power_state = hda_dsp_set_power_state_ipc4;

	/* set DAI ops */
	hda_set_dai_drv_ops(sdev, dsp_ops);

	return 0;
}
```

The shared [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) it copies supplies the mandatory callbacks that do not change between SKL-generation platforms, the [`block_read`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L200) and [`block_write`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L203) memcpy IO, the [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L175) firmware boot, the PCM callbacks, the PM callbacks, and the [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) DAI array:

```c
/* sound/soc/sof/intel/hda-common-ops.c:17 */
const struct snd_sof_dsp_ops sof_hda_common_ops = {
	/* probe/remove/shutdown */
	.probe_early	= hda_dsp_probe_early,
	.probe		= hda_dsp_probe,
	.remove		= hda_dsp_remove,
	.remove_late	= hda_dsp_remove_late,

	/* Register IO uses direct mmio */

	/* Block IO */
	.block_read	= sof_block_read,
	.block_write	= sof_block_write,
	...
	/* firmware run */
	.run = hda_dsp_cl_boot_firmware,
	...
	/* DAI drivers */
	.drv		= skl_dai,
	.num_drv	= SOF_SKL_NUM_DAIS,
	...
	/* PM */
	.suspend		= hda_dsp_suspend,
	.resume			= hda_dsp_resume,
	.runtime_suspend	= hda_dsp_runtime_suspend,
	.runtime_resume		= hda_dsp_runtime_resume,
	.runtime_idle		= hda_dsp_runtime_idle,
	...
};
EXPORT_SYMBOL_NS(sof_hda_common_ops, "SND_SOC_SOF_INTEL_HDA_GENERIC");
```

The IPC send Meteor Lake installs, [`mtl_ipc_send_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L99), writes the payload into the host mailbox and then rings the doorbell by setting [`MTL_DSP_REG_HFIPCXIDR_BUSY`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.h#L42) in the request register whose offset the descriptor stored in [`ipc_req`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L177):

```c
/* sound/soc/sof/intel/mtl.c:99 */
static int mtl_ipc_send_msg(struct snd_sof_dev *sdev, struct snd_sof_ipc_msg *msg)
{
	struct sof_intel_hda_dev *hdev = sdev->pdata->hw_pdata;
	struct sof_ipc4_msg *msg_data = msg->msg_data;

	if (hda_ipc4_tx_is_busy(sdev)) {
		hdev->delayed_ipc_tx_msg = msg;
		return 0;
	}

	hdev->delayed_ipc_tx_msg = NULL;

	/* send the message via mailbox */
	if (msg_data->data_size)
		sof_mailbox_write(sdev, sdev->host_box.offset, msg_data->data_ptr,
				  msg_data->data_size);

	snd_sof_dsp_write(sdev, HDA_DSP_BAR, MTL_DSP_REG_HFIPCXIDDY,
			  msg_data->extension);
	snd_sof_dsp_write(sdev, HDA_DSP_BAR, MTL_DSP_REG_HFIPCXIDR,
			  msg_data->primary | MTL_DSP_REG_HFIPCXIDR_BUSY);

	hda_dsp_ipc4_schedule_d0i3_work(hdev, msg);

	return 0;
}
```

The register written here, [`MTL_DSP_REG_HFIPCXIDR`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.h#L41), is the same offset the descriptor records in [`ipc_req`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L177), which is how the data interface and the behaviour interface stay consistent, the descriptor names the offset and the op uses it. The reply path is located in [`mtl_ipc_irq_thread()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L558), the threaded handler installed in [`irq_thread`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L217); it reads the acknowledge and target doorbell registers and, when the done bit is set, flushes any [`delayed_ipc_tx_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L99) the send op had queued while the doorbell was busy:

```c
/* sound/soc/sof/intel/mtl.c:558 */
static irqreturn_t mtl_ipc_irq_thread(int irq, void *context)
{
	struct sof_ipc4_msg notification_data = {{ 0 }};
	struct snd_sof_dev *sdev = context;
	bool ack_received = false;
	bool ipc_irq = false;
	u32 hipcida;
	u32 hipctdr;

	hipcida = snd_sof_dsp_read(sdev, HDA_DSP_BAR, MTL_DSP_REG_HFIPCXIDA);
	hipctdr = snd_sof_dsp_read(sdev, HDA_DSP_BAR, MTL_DSP_REG_HFIPCXTDR);

	/* reply message from DSP */
	if (hipcida & MTL_DSP_REG_HFIPCXIDA_DONE) {
		/* DSP received the message */
		snd_sof_dsp_update_bits(sdev, HDA_DSP_BAR, MTL_DSP_REG_HFIPCXCTL,
					MTL_DSP_REG_HFIPCXCTL_DONE, 0);

		mtl_ipc_dsp_done(sdev);

		ipc_irq = true;
		ack_received = true;
	}
	...
	if (ack_received) {
		struct sof_intel_hda_dev *hdev = sdev->pdata->hw_pdata;

		if (hdev->delayed_ipc_tx_msg)
			mtl_ipc_send_msg(sdev, hdev->delayed_ipc_tx_msg);
	}

	return IRQ_HANDLED;
}
```

The per-core power callback [`mtl_dsp_core_get()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L672) shows the same split between a direct register sequence and the IPC pm op. The primary core is powered by [`mtl_dsp_core_power_up()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L355) while a secondary core is delegated to the IPC pm op [`set_core_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L672):

```c
/* sound/soc/sof/intel/mtl.c:672 */
static int mtl_dsp_core_get(struct snd_sof_dev *sdev, int core)
{
	const struct sof_ipc_pm_ops *pm_ops = sdev->ipc->ops->pm;

	if (core == SOF_DSP_PRIMARY_CORE)
		return mtl_dsp_core_power_up(sdev, SOF_DSP_PRIMARY_CORE);

	if (pm_ops->set_core_state)
		return pm_ops->set_core_state(sdev, core, true);

	return 0;
}
```

[`mtl_dsp_core_put()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L685) reverses the sequence in the opposite order. A secondary core is dropped through the IPC pm op first, and only the primary core falls through to [`mtl_dsp_core_power_down()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L396):

```c
/* sound/soc/sof/intel/mtl.c:685 */
static int mtl_dsp_core_put(struct snd_sof_dev *sdev, int core)
{
	const struct sof_ipc_pm_ops *pm_ops = sdev->ipc->ops->pm;
	int ret;

	if (pm_ops->set_core_state) {
		ret = pm_ops->set_core_state(sdev, core, false);
		if (ret < 0)
			return ret;
	}

	if (core == SOF_DSP_PRIMARY_CORE)
		return mtl_dsp_core_power_down(sdev, SOF_DSP_PRIMARY_CORE);

	return 0;
}
```

The descriptor that pairs with these ops is [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760). It names three cores, the Meteor Lake IPC and ROM-status register offsets, the SSP count and base, the ACE SoundWire shim and ALH bases, and the [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) IP version:

```c
/* sound/soc/sof/intel/mtl.c:760 */
const struct sof_intel_dsp_desc mtl_chip_info = {
	.cores_num = 3,
	.init_core_mask = BIT(0),
	.host_managed_cores_mask = BIT(0),
	.ipc_req = MTL_DSP_REG_HFIPCXIDR,
	.ipc_req_mask = MTL_DSP_REG_HFIPCXIDR_BUSY,
	.ipc_ack = MTL_DSP_REG_HFIPCXIDA,
	.ipc_ack_mask = MTL_DSP_REG_HFIPCXIDA_DONE,
	.ipc_ctl = MTL_DSP_REG_HFIPCXCTL,
	.rom_status_reg = MTL_DSP_REG_HFFLGPXQWY,
	.rom_init_timeout	= 300,
	.ssp_count = MTL_SSP_COUNT,
	.ssp_base_offset = CNL_SSP_BASE_OFFSET,
	.sdw_shim_base = SDW_SHIM_BASE_ACE,
	.sdw_alh_base = SDW_ALH_BASE_ACE,
	.d0i3_offset = MTL_HDA_VS_D0I3C,
	.read_sdw_lcount =  hda_sdw_check_lcount_common,
	.enable_sdw_irq = mtl_enable_sdw_irq,
	.check_sdw_irq = mtl_dsp_check_sdw_irq,
	.check_sdw_wakeen_irq = hda_sdw_check_wakeen_irq_common,
	.sdw_process_wakeen = hda_sdw_process_wakeen_common,
	.check_ipc_irq = mtl_dsp_check_ipc_irq,
	.cl_init = mtl_dsp_cl_init,
	.power_down_dsp = mtl_power_down_dsp,
	.disable_interrupts = mtl_dsp_disable_interrupts,
	.hw_ip_version = SOF_INTEL_ACE_1_0,
	.platform = "mtl",
};
```

The sibling [`arl_s_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L789) for Arrow Lake S is the same descriptor with [`cores_num`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L174) set to 2 and [`platform`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) set to "arl", and it keeps the same [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23) version, so it reuses [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) unchanged.

```
    MTL host ◀▶ DSP IPC doorbell (mtl_ipc_send_msg / mtl_ipc_irq_thread)
    ───────────────────────────────────────────────────────────────────────

    host ─▶ DSP   send: mtl_ipc_send_msg
    ┌─────────────────────────────────────────────────────────────┐
    │ sof_mailbox_write(host_box.offset, payload)                 │
    │ HFIPCXIDDY  ◀── msg extension                               │
    │ HFIPCXIDR   ◀── primary, set HFIPCXIDR_BUSY  (rings bell)   │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    DSP ─▶ host   reply: mtl_ipc_irq_thread
    ┌─────────────────────────────────────────────────────────────┐
    │ read HFIPCXIDA ;  read HFIPCXTDR                            │
    │ if HFIPCXIDA has HFIPCXIDA_DONE :                           │
    │    clear HFIPCXCTL_DONE in HFIPCXCTL ;  flush delayed TX    │
    └─────────────────────────────────────────────────────────────┘

    descriptor offsets:  ipc_req = HFIPCXIDR    ipc_ack = HFIPCXIDA
                         ipc_ctl = HFIPCXCTL    ipc_req_mask = HFIPCXIDR_BUSY
```

### Lunar Lake extends the Meteor Lake set

Lunar Lake does not copy the common ops directly. [`sof_lnl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L103) calls [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) to inherit the entire Meteor Lake build, including the MTL IPC send and core-power callbacks, and then overrides the handful of callbacks where ACE 2.0 diverges, the probe and remove that offload DMIC and SSP to the DSP, the post-firmware-run, and the two resume paths:

```c
/* sound/soc/sof/intel/lnl.c:103 */
int sof_lnl_set_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *dsp_ops)
{
	int ret;

	ret = sof_mtl_set_ops(sdev, dsp_ops);
	if (ret)
		return ret;

	/* probe/remove */
	if (!sdev->dspless_mode_selected) {
		dsp_ops->probe = lnl_hda_dsp_probe;
		dsp_ops->remove = lnl_hda_dsp_remove;
	}

	/* post fw run */
	dsp_ops->post_fw_run = lnl_dsp_post_fw_run;

	/* PM */
	if (!sdev->dspless_mode_selected) {
		dsp_ops->resume = lnl_hda_dsp_resume;
		dsp_ops->runtime_resume = lnl_hda_dsp_runtime_resume;
	}

	return 0;
}
EXPORT_SYMBOL_NS(sof_lnl_set_ops, "SND_SOC_SOF_INTEL_LNL");
```

Each Lunar Lake override is a thin wrapper that runs the common HDAudio body and then toggles the DMIC/SSP offload through [`hdac_bus_offload_dmic_ssp()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L24), a static helper that programs the HDAudio bus to route the DMIC and SSP back ends to the DSP. The probe override wraps [`hda_dsp_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L793) and enables the offload:

```c
/* sound/soc/sof/intel/lnl.c:41 */
static int lnl_hda_dsp_probe(struct snd_sof_dev *sdev)
{
	int ret;

	ret = hda_dsp_probe(sdev);
	if (ret < 0)
		return ret;

	return hdac_bus_offload_dmic_ssp(sof_to_bus(sdev), true);
}
```

The resume overrides mirror the probe. [`lnl_hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L64) runs [`hda_dsp_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L901) and re-enables the offload, and [`lnl_hda_dsp_runtime_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L75) does the same around [`hda_dsp_runtime_resume()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dsp.c#L954), so the DMIC and SSP stay routed to the DSP across a power cycle:

```c
/* sound/soc/sof/intel/lnl.c:64 */
static int lnl_hda_dsp_resume(struct snd_sof_dev *sdev)
{
	int ret;

	ret = hda_dsp_resume(sdev);
	if (ret < 0)
		return ret;

	return hdac_bus_offload_dmic_ssp(sof_to_bus(sdev), true);
}
```

The post-firmware-run override is where the two generations diverge in firmware setup rather than offload. [`mtl_dsp_post_fw_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L301) starts the SoundWire links with [`hda_sdw_startup()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L301) on first boot and unconditionally enables the SoundWire interrupt, while [`lnl_dsp_post_fw_run()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L86) only arms IMR boot and leaves the SoundWire startup to the Lunar Lake link layer:

```c
/* sound/soc/sof/intel/lnl.c:86 */
static int lnl_dsp_post_fw_run(struct snd_sof_dev *sdev)
{
	if (sdev->first_boot) {
		struct sof_intel_hda_dev *hda = sdev->pdata->hw_pdata;

		/* Check if IMR boot is usable */
		if (!sof_debug_check_flag(SOF_DBG_IGNORE_D3_PERSISTENT)) {
			hda->imrboot_supported = true;
			debugfs_create_bool("skip_imr_boot",
					    0644, sdev->debugfs_root,
					    &hda->skip_imr_boot);
		}
	}

	return 0;
}
```

The descriptor that pairs with the Lunar Lake ops is [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164). It records five cores, the Lunar Lake ROM status register [`LNL_DSP_REG_HFDSC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.h#L12), Lunar Lake SoundWire and interrupt helpers, and the [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) IP version:

```c
/* sound/soc/sof/intel/lnl.c:164 */
const struct sof_intel_dsp_desc lnl_chip_info = {
	.cores_num = 5,
	.init_core_mask = BIT(0),
	.host_managed_cores_mask = BIT(0),
	.ipc_req = MTL_DSP_REG_HFIPCXIDR,
	.ipc_req_mask = MTL_DSP_REG_HFIPCXIDR_BUSY,
	.ipc_ack = MTL_DSP_REG_HFIPCXIDA,
	.ipc_ack_mask = MTL_DSP_REG_HFIPCXIDA_DONE,
	.ipc_ctl = MTL_DSP_REG_HFIPCXCTL,
	.rom_status_reg = LNL_DSP_REG_HFDSC,
	.rom_init_timeout = 300,
	.ssp_count = MTL_SSP_COUNT,
	.d0i3_offset = MTL_HDA_VS_D0I3C,
	.read_sdw_lcount =  hda_sdw_check_lcount_ext,
	.check_sdw_irq = lnl_dsp_check_sdw_irq,
	.check_sdw_wakeen_irq = lnl_sdw_check_wakeen_irq,
	.sdw_process_wakeen = hda_sdw_process_wakeen_common,
	.check_ipc_irq = mtl_dsp_check_ipc_irq,
	.cl_init = mtl_dsp_cl_init,
	.power_down_dsp = mtl_power_down_dsp,
	.disable_interrupts = lnl_dsp_disable_interrupts,
	.hw_ip_version = SOF_INTEL_ACE_2_0,
	.platform = "lnl",
};
```

The Lunar Lake descriptor reuses the Meteor Lake IPC and doorbell register offsets ([`ipc_req`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L177) is the same [`MTL_DSP_REG_HFIPCXIDR`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.h#L41)), which is why the inherited [`mtl_ipc_send_msg()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L99) and [`mtl_ipc_irq_thread()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L558) work unchanged on Lunar Lake. It swaps in [`LNL_DSP_REG_HFDSC`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.h#L12) for the ROM status register, [`hda_sdw_check_lcount_ext`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164) for the SoundWire link count, and the three Lunar Lake interrupt helpers [`lnl_dsp_check_sdw_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L131), [`lnl_sdw_check_wakeen_irq()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L146), and [`lnl_dsp_disable_interrupts()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L139) that use the embedded multi-link table instead of the legacy SoundWire shim path.

```
    mtl_chip_info vs lnl_chip_info  (same struct sof_intel_dsp_desc)
    ───────────────────────────────────────────────────────────────────

    field                  mtl_chip_info          lnl_chip_info
    ────────────────────   ────────────────────   ────────────────────
    cores_num              3                      5
    rom_status_reg         MTL_..._HFFLGPXQWY     LNL_DSP_REG_HFDSC
    read_sdw_lcount        ..._check_lcount_com   ..._check_lcount_ext
    check_sdw_irq          mtl_dsp_check_sdw_irq  lnl_dsp_check_sdw_irq
    check_sdw_wakeen_irq   hda_sdw_..._common     lnl_sdw_check_wakeen
    disable_interrupts     mtl_dsp_disable_int    lnl_dsp_disable_int
    hw_ip_version          SOF_INTEL_ACE_1_0      SOF_INTEL_ACE_2_0
    platform               "mtl"                  "lnl"

    identical in both: ipc_req / ipc_ack / ipc_ctl = MTL_DSP_REG_HFIPCX*,
    the ipc masks, ssp_count = MTL_SSP_COUNT, d0i3 = MTL_HDA_VS_D0I3C
```

### The DAI op binding gates SSP and DMIC on the IP version

The last step of every [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) call is [`hda_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L745), which walks the [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) array and attaches the per-DAI ops. The iDisp, Analog, and Digital HDAudio DAIs always get [`hda_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L354), then the SSP and DMIC binding runs:

```c
/* sound/soc/sof/intel/hda-dai.c:745 */
void hda_set_dai_drv_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *ops)
{
	int i;

	for (i = 0; i < ops->num_drv; i++) {
#if IS_ENABLED(CONFIG_SND_SOC_SOF_HDA_AUDIO_CODEC)
		if (strstr(ops->drv[i].name, "iDisp") ||
		    strstr(ops->drv[i].name, "Analog") ||
		    strstr(ops->drv[i].name, "Digital"))
			ops->drv[i].ops = &hda_dai_ops;
#endif
	}

	ssp_set_dai_drv_ops(sdev, ops);
	dmic_set_dai_drv_ops(sdev, ops);
	...
}
```

[`ssp_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L708) is where the IP version decides the outcome. It reads the descriptor through [`get_chip_info()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L213) and only attaches [`ssp_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L479) when [`hw_ip_version`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L191) is at or above [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24):

```c
/* sound/soc/sof/intel/hda-dai.c:708 */
static void ssp_set_dai_drv_ops(struct snd_sof_dev *sdev, struct snd_sof_dsp_ops *ops)
{
	const struct sof_intel_dsp_desc *chip;
	int i;

	chip = get_chip_info(sdev->pdata);

	if (chip->hw_ip_version >= SOF_INTEL_ACE_2_0) {
		for (i = 0; i < ops->num_drv; i++) {
			if (strstr(ops->drv[i].name, "SSP"))
				ops->drv[i].ops = &ssp_dai_ops;
		}
	}
}
```

[`dmic_set_dai_drv_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L723) applies the identical gate to the DMIC DAIs with [`dmic_dai_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L486). Because [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760) carries [`SOF_INTEL_ACE_1_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L23), the comparison fails on Meteor Lake and its SSP and DMIC DAIs keep the default ASoC ops, while [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164) carries [`SOF_INTEL_ACE_2_0`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L24) and its SSP and DMIC DAIs receive the back-end ops that drive the DSP-offloaded path. The same [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L350) array [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L917) is shared by both platforms; only the per-DAI [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-dai.h#L403) pointers differ after this binding runs.

```
    Per-DAI ops binding by hw_ip_version (hda_set_dai_drv_ops)
    ──────────────────────────────────────────────────────────────

    DAI name match    MTL (ACE_1_0)         LNL (ACE_2_0)
    ───────────────   ───────────────────   ───────────────────
    iDisp             hda_dai_ops           hda_dai_ops
    Analog            hda_dai_ops           hda_dai_ops
    Digital           hda_dai_ops           hda_dai_ops
    SSP               default ASoC ops      ssp_dai_ops
    DMIC              default ASoC ops      dmic_dai_ops

    gate: ssp_set / dmic_set attach the back-end ops only when
          chip->hw_ip_version >= SOF_INTEL_ACE_2_0
    one shared skl_dai[] array ; only drv[i].ops pointers differ
```

### The PCI descriptor names the chip info and the ops builder

The two interfaces are tied together in one [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) per platform. [`mtl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L31) points [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) at [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760), [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) at the per-module ops struct, and [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) at [`sof_mtl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26):

```c
/* sound/soc/sof/intel/pci-mtl.c:31 */
static const struct sof_dev_desc mtl_desc = {
	.use_acpi_target_states	= true,
	.machines               = snd_soc_acpi_intel_mtl_machines,
	.alt_machines		= snd_soc_acpi_intel_mtl_sdw_machines,
	...
	.chip_info = &mtl_chip_info,
	.ipc_supported_mask	= BIT(SOF_IPC_TYPE_4),
	.ipc_default		= SOF_IPC_TYPE_4,
	.dspless_mode_supported	= true,		/* Only supported for HDaudio */
	...
	.ops = &sof_mtl_ops,
	.ops_init = sof_mtl_ops_init,
	.ops_free = hda_ops_free,
};
```

[`lnl_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L31) is the same shape with [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) pointing at [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164), [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) at [`sof_lnl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L26), and the extra [`on_demand_dsp_boot`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) flag that lets Lunar Lake leave the DSP unbooted until a stream needs it:

```c
/* sound/soc/sof/intel/pci-lnl.c:31 */
static const struct sof_dev_desc lnl_desc = {
	.use_acpi_target_states	= true,
	.machines               = snd_soc_acpi_intel_lnl_machines,
	.alt_machines		= snd_soc_acpi_intel_lnl_sdw_machines,
	...
	.chip_info		= &lnl_chip_info,
	.ipc_supported_mask	= BIT(SOF_IPC_TYPE_4),
	.ipc_default		= SOF_IPC_TYPE_4,
	.dspless_mode_supported	= true,
	.on_demand_dsp_boot	= true,
	...
	.ops = &sof_lnl_ops,
	.ops_init = sof_lnl_ops_init,
};
```

The [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) callback is the only place the set-ops function is named. [`sof_mtl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26) passes the module's static [`sof_mtl_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-mtl.c#L26) storage to [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) so the copy-then-override runs against real storage rather than the read-only descriptor:

```c
/* sound/soc/sof/intel/pci-mtl.c:26 */
static int sof_mtl_ops_init(struct snd_sof_dev *sdev)
{
	return sof_mtl_set_ops(sdev, &sof_mtl_ops);
}
```

[`sof_lnl_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L26) is the Lunar Lake mirror, calling [`sof_lnl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L103) against the [`sof_lnl_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/pci-lnl.c#L26) storage.

### From PCI match to the populated ops

The PCI core matches the descriptor through the [`driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L44) of the [`struct pci_device_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L44) table and runs the [`struct pci_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pci.h#L1019) probe [`hda_pci_intel_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L978), which forwards to [`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190). That function recovers the descriptor from the matched [`pci_id->driver_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mod_devicetable.h#L44), allocates a [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75), stores the descriptor in [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75), and calls [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630):

```c
/* sound/soc/sof/sof-pci-dev.c:190 */
int sof_pci_probe(struct pci_dev *pci, const struct pci_device_id *pci_id)
{
	struct sof_loadable_file_profile *path_override;
	struct device *dev = &pci->dev;
	const struct sof_dev_desc *desc =
		(const struct sof_dev_desc *)pci_id->driver_data;
	struct snd_sof_pdata *sof_pdata;
	int ret;
	...
	if (!desc->ops) {
		dev_err(dev, "error: no matching PCI descriptor ops\n");
		return -ENODEV;
	}

	sof_pdata = devm_kzalloc(dev, sizeof(*sof_pdata), GFP_KERNEL);
	if (!sof_pdata)
		return -ENOMEM;
	...
	sof_pdata->desc = desc;
	sof_pdata->dev = dev;
	...
	/* call sof helper for DSP hardware probe */
	return snd_sof_device_probe(dev, sof_pdata);
}
```

[`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630) is where the generic [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) comes into existence. It allocates the device, records the [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) so the descriptor stays reachable, selects the IPC ops with [`sof_init_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630), and then continues the probe that eventually runs the platform [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) to fill the per-module ops struct:

```c
/* sound/soc/sof/core.c:630 */
int snd_sof_device_probe(struct device *dev, struct snd_sof_pdata *plat_data)
{
	struct snd_sof_dev *sdev;
	int ret;

	sdev = devm_kzalloc(dev, sizeof(*sdev), GFP_KERNEL);
	if (!sdev)
		return -ENOMEM;

	/* initialize sof device */
	sdev->dev = dev;

	/* initialize default DSP power state */
	sdev->dsp_power_state.state = SOF_DSP_PM_D0;

	sdev->pdata = plat_data;
	sdev->first_boot = true;
	dev_set_drvdata(dev, sdev);
	...
	/* Initialize sof_ops based on the initial selected IPC version */
	ret = sof_init_sof_ops(sdev);
	if (ret)
		return ret;
	...
	return sof_probe_continue(sdev);
}
```

By the time the probe completes, the generic [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) holds a [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) whose [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) names the platform [`chip_info`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) and an [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) pointer the [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) callback has populated with the Meteor Lake or Lunar Lake bodies, so every later core call lands in the right platform function without the core ever naming a platform.

### The descriptor pair the platform-agnostic core reads at probe

This figure shows the platform-agnostic [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) reading the two const objects its descriptor names at probe, the hardware descriptor [`struct sof_intel_dsp_desc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/shim.h#L173) built per platform as [`mtl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L760) or [`lnl_chip_info`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L164), and the function pointer struct [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) assembled by [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) and extended by [`sof_lnl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/lnl.c#L103).

```
    generic SOF core (platform-agnostic)
    ┌───────────────────────────────────────────────────────────┐
    │  struct snd_sof_dev                                       │
    │    pdata ─▶ snd_sof_pdata.desc ─▶ sof_dev_desc            │
    │    bar[], ipc, fw_state, dsp_power_state                  │
    └───────────────────────┬───────────────────────────────────┘
                            │ reads at probe
                ┌───────────┴─────────────────┐
                ▼                             ▼
    sof_dev_desc.chip_info        sof_dev_desc.ops
    struct sof_intel_dsp_desc     struct snd_sof_dsp_ops
    ┌───────────────────────┐     ┌───────────────────────┐
    │ cores_num             │     │ probe / run / reset   │
    │ ipc_req / ipc_ack     │     │ block_read / write    │
    │ rom_status_reg        │     │ send_msg              │
    │ ssp_count / ssp_base  │     │ suspend / resume      │
    │ hw_ip_version         │     │ drv[] (DAI drivers)   │
    └───────────┬───────────┘     └───────────▲───────────┘
                │                             │ built by
    ┌───────────┴───────────┐     ┌───────────┴───────────┐
    │ MTL: mtl_chip_info    │     │ MTL: sof_mtl_set_ops  │
    │      ACE_1_0          │     │ LNL: sof_lnl_set_ops  │
    │ LNL: lnl_chip_info    │     │   (extends MTL set)   │
    │      ACE_2_0          │     └───────────────────────┘
    └───────────────────────┘
```
