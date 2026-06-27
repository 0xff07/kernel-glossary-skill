# SOF device architecture

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Sound Open Firmware (SOF) drives an audio DSP from open firmware, and the kernel side is built around one per-device object, [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), allocated once by [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630); it is the join point between the ASoC core above it, the DSP hardware below it, and the firmware reached over an inter-processor message channel, embedding the ASoC platform component descriptor [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) that SOF fills and registers, carrying the topology object lists ([`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547)) that the topology file fills at runtime, and holding the two abstractions every hardware difference funnels through, the DSP hardware ops reached by the [`sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21) macro and the generic IPC channel [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547). On an x86-64 ACPI Meteor Lake machine the DSP is the audio engine inside the Intel HDAudio controller, its message protocol is IPC4, and its [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) starts from the SKL+ HDAudio-generic base [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17).

```
    ASoC core (sound/soc/soc-core.c)
            │  devm_snd_soc_register_component(&sdev->plat_drv, ...)
            ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  struct snd_sof_dev          (sound/soc/sof/sof-priv.h:547)  │
    │  ┌────────────────────────────────────────────────────────┐  │
    │  │ dev, pdata ─▶ snd_sof_pdata ─▶ sof_dev_desc.ops        │  │
    │  │ plat_drv  (struct snd_soc_component_driver, filled)    │  │
    │  │ component (struct snd_soc_component *, bound at probe) │  │
    │  │ basefw    (struct sof_firmware, base image)            │  │
    │  └────────────────────────────────────────────────────────┘  │
    │                                                              │
    │   topology object lists (filled from the .tplg file)         │
    │   ┌──────────┬────────────┬──────────────┬──────────┬──────┐ │
    │   │ pcm_list │widget_list │ pipeline_list│ dai_list │route │ │
    │   └──────────┴────────────┴──────────────┴──────────┴──────┘ │
    │                                                              │
    │   ops ───── sof_ops() ─────▶  struct snd_sof_dsp_ops         │
    │   ipc ─────────────────────▶  struct snd_sof_ipc ─▶ ops      │
    └───────────────┬──────────────────────────────┬───────────────┘
                    │ block_write, run, send_msg   │ tx_msg (IPC3/IPC4)
                    ▼                              ▼
            DSP hardware (HDA-gen)            DSP firmware (SOF)
```

## SUMMARY

SOF binds an audio DSP into ALSA by registering one ASoC platform component and then loading firmware and a topology file into the DSP behind it. Every per-device fact is held in [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), which [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630) allocates with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48), wires to its [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and through that to the platform descriptor [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), and initialises the seven topology lists and the locks before any DSP access. The probe splits in two. [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630) does the part that must not run in a workqueue and then either schedules [`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) on a work item or calls it inline, and [`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) probes the DSP through [`sof_init_environment()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L368), builds the platform component with [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823), inits IPC, loads and boots firmware, then registers the component with [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29).

Two abstractions keep the core free of hardware detail. The DSP hardware ops are a [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) function pointer struct that a platform points at from its descriptor's [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) field, so the core reaches register IO, firmware load, boot, and PCM DMA through [`sof_ops(sdev)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21) without naming a chip. The inter-processor messaging is a [`struct snd_sof_ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523) whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523) is a [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) chosen at [`snd_sof_ipc_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc.c#L145) by the firmware's message-protocol version, [`ipc3_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc3.c#L1142) for IPC3 or [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912) for IPC4. The component's ASoC probe callback [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759) then loads the topology file with [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494), which parses the firmware blob and fills the [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) so the DSP graph appears to userspace as ALSA PCM devices and controls. The body of the Meteor Lake and Lunar Lake ops fill is covered by the sibling Intel MTL/LNL dsp_ops page; the PCM op bodies are covered by the PCM ops page, the ASoC component build by the component page, and the IPC4 PCM backend by the IPC4 PCM page. This page stops at the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) surface and the probe sequence.

## SPECIFICATIONS

The [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) object is a Linux kernel software construct and has no standalone hardware specification. The DSP it drives on an x86-64 ACPI machine is the audio DSP embedded in an Intel High Definition Audio controller, whose host-side register and stream model is defined by the Intel High Definition Audio Specification. The firmware image format, the topology binary, and the IPC3 and IPC4 message protocols are defined by the Sound Open Firmware project rather than by a ratified standard, and the project documentation is public, so the message types and the topology schema can be read from the SOF documentation listed under OTHER SOURCES. The firmware-side description of which DSP is present, including the Meteor Lake HDAudio controller, is reported through ACPI on x86-64, read by the platform glue in [`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190) and the descriptor it selects.

## LINUX KERNEL

### The device object and its platform binding (sof-priv.h, include/sound/sof.h)

- [`'\<struct snd_sof_dev\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547): the per-device object; embeds [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), the topology lists, [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`basefw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and the [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) back pointer to the platform descriptor
- [`'\<struct snd_sof_pdata\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75): platform data passed into probe; carries the [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) descriptor, the [`machine`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) match, the firmware and topology filename overrides, and the selected [`ipc_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75)
- [`'\<struct sof_dev_desc\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128): per-platform descriptor; its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) field is the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) the core reaches through [`sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21), the optional [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) fills it at runtime, and [`ipc_supported_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) advertises IPC3/IPC4 support
- [`'\<struct sof_firmware\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L148): the base firmware image, a [`struct firmware`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/firmware.h#L13) plus a [`payload_offset`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L148) past the extended manifest, held in [`basefw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547)
- [`'\<enum sof_fw_state\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L33): the firmware boot state stored in [`fw_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), advancing through [`SOF_FW_BOOT_NOT_STARTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L34), [`SOF_FW_BOOT_PREPARE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L36), [`SOF_FW_BOOT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L37), and [`SOF_FW_BOOT_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L41)
- [`'\<enum sof_ipc_type\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L54): the message-protocol family, [`SOF_IPC_TYPE_3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L55) or [`SOF_IPC_TYPE_4`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L56), selecting the [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503)
- [`'\<enum sof_dsp_power_states\>':'include/sound/sof.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L46): DSP power state, initialised to [`SOF_DSP_PM_D0`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L47) at probe

### Probe and lifecycle (core.c)

- [`'\<snd_sof_device_probe\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630): allocate the [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), init the lists and locks, select the ops version with [`sof_init_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L345), run the early probe, then dispatch [`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) inline or on a work item
- [`'\<sof_probe_continue\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454): the rest of probe; runs [`sof_init_environment()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L368), builds the platform component, inits IPC, loads and boots firmware, then registers the ASoC component and the machine driver, with a labelled error-unwind tail
- [`'\<sof_init_environment\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L368): probe the DSP hardware via [`snd_sof_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L49), run [`sof_machine_check()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L206), select the IPC type and file paths, and re-init ops if the IPC type changed
- [`'\<sof_init_sof_ops\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L345): check the descriptor's [`ipc_supported_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), record the chosen [`ipc_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) and topology filename, then call [`validate_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L317)
- [`'\<validate_sof_ops\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L317): run the platform's [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) through [`sof_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L24) and check that every mandatory [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) callback ([`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), [`block_read`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), [`block_write`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), [`send_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), [`load_firmware`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165), [`ipc_msg_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165)) is present
- [`'\<sof_machine_check\>':'sound/soc/sof/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L206): select the ASoC machine driver through [`snd_sof_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L563), or fall back to the nocodec machine

### DSP hardware abstraction (sof-priv.h, ops.h)

- [`'\<struct snd_sof_dsp_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165): the DSP hardware abstraction function pointer struct; groups probe/boot, register and block IO, mailbox IO, the IPC send, firmware load, PCM DMA, PM, and the embedded DAI driver array [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165)
- [`'sof_ops':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21): the macro that resolves to `sdev->pdata->desc->ops`, the single point through which the core reaches every DSP op
- [`'\<snd_sof_probe\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L49) / [`'\<snd_sof_probe_early\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L41): wrappers that call the mandatory [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) and optional [`probe_early`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) ops
- [`'\<snd_sof_load_firmware\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L474): wrapper that calls the [`load_firmware`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op
- [`'\<snd_sof_machine_register\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L548) / [`'\<snd_sof_machine_select\>':'sound/soc/sof/ops.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L563): wrappers that call the optional [`machine_register`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) and [`machine_select`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) ops

### IPC abstraction (sof-priv.h, ipc.c)

- [`'\<struct snd_sof_ipc\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523): the generic IPC channel held in [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547); carries the [`tx_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523), the [`max_payload_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523), the pending [`struct snd_sof_ipc_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L412), and the version [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523)
- [`'\<struct sof_ipc_ops\>':'sound/soc/sof/sof-priv.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503): the IPC-version function pointer struct; groups [`tx_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), [`set_get_data`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), [`get_reply`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), [`rx_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), and the [`tplg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), [`pm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), [`fw_loader`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) sub-ops
- [`'\<snd_sof_ipc_init\>':'sound/soc/sof/ipc.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc.c#L145): allocate the [`struct snd_sof_ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523), pick [`ipc3_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc3.c#L1142) or [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912) by [`ipc_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75), and reject a version whose mandatory message, firmware-loader, PCM, or topology ops are missing
- [`'ipc3_ops':'sound/soc/sof/ipc3.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc3.c#L1142) / [`'ipc4_ops':'sound/soc/sof/ipc4.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912): the two concrete [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) instances; Meteor Lake selects [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912)

### Component, firmware boot, and topology (pcm.c, loader.c, topology.c)

- [`'\<snd_sof_new_platform_drv\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823): fill the embedded [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) component descriptor with the SOF PCM callbacks and the [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759) probe hook
- [`'\<sof_pcm_probe\>':'sound/soc/sof/pcm.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759): the component probe callback; binds [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), builds the topology filename, and calls [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494)
- [`'\<snd_sof_run_firmware\>':'sound/soc/sof/loader.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L109): boot the DSP via the [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op, wait on [`boot_wait`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) for the firmware-ready handshake, then run the post-boot op
- [`'\<snd_sof_load_firmware_raw\>':'sound/soc/sof/loader.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L17): the [`load_firmware`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op used by the HDA-generation ops; reads the firmware file into [`basefw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and parses its extended manifest
- [`'\<snd_sof_load_topology\>':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494): request the topology firmware blob and hand it to [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) with [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305), populating the topology lists
- [`'sof_tplg_ops':'sound/soc/sof/topology.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305): the [`struct snd_soc_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-topology.h#L108) SOF supplies to the ASoC topology loader

### Intel HDA-generation worked example (intel/)

- [`'sof_hda_common_ops':'sound/soc/sof/intel/hda-common-ops.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17): the SKL+ HDAudio-generic base [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) that the Meteor Lake fill copies and overrides
- [`'\<sof_mtl_set_ops\>':'sound/soc/sof/intel/mtl.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702): the Meteor Lake [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) helper, filled per platform and detailed on the sibling Intel MTL/LNL dsp_ops page; it copies [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) into the descriptor's ops and applies MTL overrides
- [`'\<hda_machine_select\>':'sound/soc/sof/intel/hda.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489): the [`machine_select`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op that matches an ACPI machine entry to the discovered HDAudio codecs
- [`'skl_dai':'sound/soc/sof/intel/hda-dai.c'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788): the DAI driver array the HDA ops point [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) at, registered as the component's DAIs
- [`'\<SOF_SKL_NUM_DAIS\>':'sound/soc/sof/intel/hda.h'`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L424): the count of entries in [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788), stored in [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165)

## KERNEL DOCUMENTATION

- [`Documentation/sound/soc/platform.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/platform.rst): the ASoC platform component model that SOF registers its DSP as
- [`Documentation/sound/soc/overview.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/overview.rst): the ASoC component, DAI, and machine layering SOF plugs the DSP into
- [`Documentation/sound/soc/dpcm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/sound/soc/dpcm.rst): Dynamic PCM, the front-end/back-end model the SOF topology builds from its pipeline and PCM lists

## OTHER SOURCES

- [Sound Open Firmware project documentation](https://thesofproject.github.io/latest/index.html)
- [SOF architecture overview](https://thesofproject.github.io/latest/introduction/index.html)
- [SOF IPC documentation](https://thesofproject.github.io/latest/introduction/ipc/index.html)
- [Audio with embedded Linux training](https://bootlin.com/doc/training/audio/audio-slides.pdf) by Bootlin, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## INTERFACES

The interface a platform implements to bring up a SOF DSP is the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) function pointer struct, declared in or filled from the platform's [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) and reached only through the [`sof_ops(sdev)`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21) macro. Each op is annotated mandatory or optional in the struct definition, and [`validate_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L317) rejects a platform that leaves a mandatory one NULL. The objects below have one creator each, so a reader can follow a link from the platform descriptor through the device object to the live IPC channel and the registered component.

| Object | Created by | Lifetime |
|--------|-----------|----------|
| [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) | [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48) in [`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630) | the DSP device (devm) |
| [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) | the bus glue ([`sof_pci_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-pci-dev.c#L190)) | passed into probe |
| [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) | static per platform, or filled by [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) | the device |
| [`struct snd_sof_ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523) | [`snd_sof_ipc_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc.c#L145) | the device (devm) |
| [`struct snd_soc_component_driver`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L67) [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) | [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) | embedded in [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) |
| [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) | [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) | the device (devm) |

### probe, probe_early, and run

[`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) is mandatory and brings up the DSP hardware (mapping its BARs, claiming its interrupt), called by [`snd_sof_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L49) inside [`sof_init_environment()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L368). [`probe_early`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) is the optional first pass that may return `-EPROBE_DEFER` for a missing dependency and so must run outside the probe workqueue. [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) is mandatory and releases the DSP cores from reset once the image is in place; [`snd_sof_run_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L109) calls it and then blocks on the firmware-ready message.

### block_read, block_write, and load_firmware

[`block_read`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) and [`block_write`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) are mandatory memcpy-style IO into a DSP memory block selected by an [`enum snd_sof_fw_blk_type`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/sound/sof/fw.h#L27) so the loader can place firmware segments without knowing the bus. [`load_firmware`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) is mandatory and reads the image file; the HDA-generation ops set it to [`snd_sof_load_firmware_raw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L17).

### send_msg

[`send_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) is mandatory and writes one IPC message into the host mailbox and rings the DSP doorbell. It is the hardware end of the channel; the protocol end is the [`tx_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) op of the selected [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), which formats the message before [`send_msg`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) transports it.

### pcm_open, pcm_hw_params, pcm_trigger, and pcm_pointer

The PCM ops connect an ALSA substream to a DSP host-DMA stream and are optional, called from the [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) component's matching callbacks. [`pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) assigns a stream, [`pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) programs its buffer and format, [`pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) starts and stops the DMA, and [`pcm_pointer`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) reports the position. The bodies of these ops are covered on the PCM ops page.

### machine_select, machine_register, drv, and num_drv

[`machine_select`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) returns the [`struct snd_soc_acpi_mach`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-acpi.h#L210) that matches the discovered codecs, and [`machine_register`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) creates the machine platform device. The [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) fields are the DAI driver array the core registers under the component, which for the HDA-generation device is [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) with [`SOF_SKL_NUM_DAIS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L424) entries.

## DETAILS

### The device object at the center

[`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) is the one object the whole subsystem hangs from, and every other structure on this page is either embedded in it or reached by a pointer it holds. The fields that matter for the layering are the [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) back pointer that leads to the platform descriptor and the DSP ops, the [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) ASoC component descriptor SOF fills in place, the [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) channel, the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) bound when the component registers, the [`basefw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) image, and the seven topology lists that the .tplg file fills:

```c
/* sound/soc/sof/sof-priv.h:547 */
struct snd_sof_dev {
	struct device *dev;
	spinlock_t ipc_lock;	/* lock for IPC users */
	spinlock_t hw_lock;	/* lock for HW IO access */
	...
	/* Main, Base firmware image */
	struct sof_firmware basefw;

	/*
	 * ASoC components. plat_drv fields are set dynamically so
	 * can't use const
	 */
	struct snd_soc_component_driver plat_drv;
	...
	enum sof_fw_state fw_state;
	bool first_boot;
	...
	/* DSP HW differentiation */
	struct snd_sof_pdata *pdata;

	/* IPC */
	struct snd_sof_ipc *ipc;
	...
	/* topology */
	struct snd_soc_tplg_ops *tplg_ops;
	struct list_head pcm_list;
	struct list_head kcontrol_list;
	struct list_head widget_list;
	struct list_head pipeline_list;
	struct list_head dai_list;
	struct list_head dai_link_list;
	struct list_head route_list;
	struct snd_soc_component *component;
	...
};
```

The DSP ops are not a field of this struct; they are reached one level out, through the [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) pointer to a [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) and its [`desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) pointer to a [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), whose [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) field is the [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165). The [`sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21) macro is that whole chain in one expression:

```c
/* sound/soc/sof/ops.h:21 */
#define sof_ops(sdev) \
	((sdev)->pdata->desc->ops)
```

The descriptor carries more than the ops; it is the per-platform table the core consults for IPC support and file paths. Its [`ops`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128), and [`ipc_supported_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) fields are the ones the probe path reads:

```c
/* include/sound/sof.h:128 */
struct sof_dev_desc {
	/* list of machines using this configuration */
	struct snd_soc_acpi_mach *machines;
	...
	/* information on supported IPCs */
	unsigned int ipc_supported_mask;
	enum sof_ipc_type ipc_default;
	...
	const struct snd_sof_dsp_ops *ops;
	int (*ops_init)(struct snd_sof_dev *sdev);
	void (*ops_free)(struct snd_sof_dev *sdev);
};
```

### Probe allocates the object and splits in two

[`snd_sof_device_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L630) is the entry point. It allocates the [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) with [`devm_kzalloc()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/device/devres.h#L48), stores the [`pdata`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), sets [`first_boot`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), selects the initial ops with [`sof_init_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L345), then initialises the seven topology lists and the locks before any DSP touch:

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

	INIT_LIST_HEAD(&sdev->pcm_list);
	INIT_LIST_HEAD(&sdev->kcontrol_list);
	INIT_LIST_HEAD(&sdev->widget_list);
	INIT_LIST_HEAD(&sdev->pipeline_list);
	INIT_LIST_HEAD(&sdev->dai_list);
	INIT_LIST_HEAD(&sdev->dai_link_list);
	INIT_LIST_HEAD(&sdev->route_list);
	...
	sof_set_fw_state(sdev, SOF_FW_BOOT_NOT_STARTED);

	/*
	 * first pass of probe which isn't allowed to run in a work-queue,
	 * typically to rely on -EPROBE_DEFER dependencies
	 */
	ret = snd_sof_probe_early(sdev);
	if (ret < 0)
		return ret;

	if (IS_ENABLED(CONFIG_SND_SOC_SOF_PROBE_WORK_QUEUE)) {
		INIT_WORK(&sdev->probe_work, sof_probe_work);
		schedule_work(&sdev->probe_work);
		return 0;
	}

	return sof_probe_continue(sdev);
}
```

The split is for platforms whose DSP bring-up takes long enough that it should not block the probe thread. According to the comment in the body, the first pass "isn't allowed to run in a work-queue, typically to rely on -EPROBE_DEFER dependencies", so [`snd_sof_probe_early()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L41) runs inline and the rest is deferred to [`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) either on a work item or by a direct call.

[`sof_init_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L345) is where the descriptor's advertised IPC support is checked against the requested type before any ops are touched, and it records the chosen [`ipc_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) and topology filename on the [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75). On Meteor Lake the descriptor's [`ipc_supported_mask`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) is `BIT(SOF_IPC_TYPE_4)`, so any other request fails here:

```c
/* sound/soc/sof/core.c:345 */
static int sof_init_sof_ops(struct snd_sof_dev *sdev)
{
	struct snd_sof_pdata *plat_data = sdev->pdata;
	struct sof_loadable_file_profile *base_profile = &plat_data->ipc_file_profile_base;

	/* check IPC support */
	if (!(BIT(base_profile->ipc_type) & plat_data->desc->ipc_supported_mask)) {
		dev_err(sdev->dev,
			"ipc_type %d is not supported on this platform, mask is %#x\n",
			base_profile->ipc_type, plat_data->desc->ipc_supported_mask);
		return -EINVAL;
	}
	...
	plat_data->ipc_type = base_profile->ipc_type;
	plat_data->tplg_filename = base_profile->tplg_name;

	return validate_sof_ops(sdev);
}
```

[`validate_sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L317) then calls into the platform's [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) through [`sof_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L24) and enforces the mandatory-op contract, so a half-filled [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) cannot reach the rest of probe:

```c
/* sound/soc/sof/core.c:317 */
static int validate_sof_ops(struct snd_sof_dev *sdev)
{
	int ret;

	/* init ops, if necessary */
	ret = sof_ops_init(sdev);
	if (ret < 0)
		return ret;

	/* check all mandatory ops */
	if (!sof_ops(sdev) || !sof_ops(sdev)->probe) {
		dev_err(sdev->dev, "missing mandatory ops\n");
		sof_ops_free(sdev);
		return -EINVAL;
	}

	if (!sdev->dspless_mode_selected &&
	    (!sof_ops(sdev)->run || !sof_ops(sdev)->block_read ||
	     !sof_ops(sdev)->block_write || !sof_ops(sdev)->send_msg ||
	     !sof_ops(sdev)->load_firmware || !sof_ops(sdev)->ipc_msg_data)) {
		dev_err(sdev->dev, "missing mandatory DSP ops\n");
		sof_ops_free(sdev);
		return -EINVAL;
	}

	return 0;
}
```

[`sof_ops_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L24) runs the descriptor's [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) when one is supplied, which is how a platform that builds its [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) at runtime gets it filled before the mandatory-op check reads it:

```c
/* sound/soc/sof/ops.h:24 */
static inline int sof_ops_init(struct snd_sof_dev *sdev)
{
	if (sdev->pdata->desc->ops_init)
		return sdev->pdata->desc->ops_init(sdev);

	return 0;
}
```

### The continuation builds the layers in order

[`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) runs the layers bottom up. It probes the DSP hardware and matches a machine in [`sof_init_environment()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L368), fills the platform component descriptor with [`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823), creates the IPC channel with [`snd_sof_ipc_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc.c#L145), loads and boots firmware, and only then registers the ASoC component and the machine driver:

```c
/* sound/soc/sof/core.c:454 */
static int sof_probe_continue(struct snd_sof_dev *sdev)
{
	struct snd_sof_pdata *plat_data = sdev->pdata;
	int ret;

	/* Initialize loadable file paths and check the environment validity */
	ret = sof_init_environment(sdev);
	if (ret)
		return ret;

	sof_set_fw_state(sdev, SOF_FW_BOOT_PREPARE);

	/* set up platform component driver */
	snd_sof_new_platform_drv(sdev);
	...
	/* init the IPC */
	sdev->ipc = snd_sof_ipc_init(sdev);
	if (!sdev->ipc) {
		ret = -ENOMEM;
		dev_err(sdev->dev, "error: failed to init DSP IPC %d\n", ret);
		goto ipc_err;
	}

	/* load the firmware */
	ret = snd_sof_load_firmware(sdev);
	...
	sof_set_fw_state(sdev, SOF_FW_BOOT_IN_PROGRESS);
	...
	ret = snd_sof_run_firmware(sdev);
	...
skip_dsp_init:
	/* hereafter all FW boot flows are for PM reasons */
	sdev->first_boot = false;

	/* now register audio DSP platform driver and dai */
	ret = devm_snd_soc_register_component(sdev->dev, &sdev->plat_drv,
					      sof_ops(sdev)->drv,
					      sof_ops(sdev)->num_drv);
	if (ret < 0) {
		dev_err(sdev->dev,
			"error: failed to register DSP DAI driver %d\n", ret);
		goto fw_trace_err;
	}

	ret = snd_sof_machine_register(sdev, plat_data);
	...
}
```

The [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29) call is the moment SOF becomes an ASoC platform component. It passes the embedded [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) as the component driver and the DSP ops' [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) and [`num_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) as the DAI driver array, so the same registration that publishes the component also publishes its DAIs. The error tail after the `skip_dsp_init` label unwinds in reverse order through labelled `goto`s, calling [`snd_sof_machine_unregister()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L557), [`snd_sof_fw_unload()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L184), [`snd_sof_ipc_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc.c#L218), and [`sof_ops_free()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L32), then resets [`fw_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) to [`SOF_FW_BOOT_NOT_STARTED`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L34).

[`sof_init_environment()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L368) is the bottom layer. It runs the mandatory [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op through [`snd_sof_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L49), matches a machine, and re-initialises the ops if the firmware on the device turned out to need a different IPC type than the one initially selected:

```c
/* sound/soc/sof/core.c:368 */
static int sof_init_environment(struct snd_sof_dev *sdev)
{
	struct snd_sof_pdata *plat_data = sdev->pdata;
	struct sof_loadable_file_profile *base_profile = &plat_data->ipc_file_profile_base;
	int ret;

	/* probe the DSP hardware */
	ret = snd_sof_probe(sdev);
	if (ret < 0) {
		dev_err(sdev->dev, "failed to probe DSP %d\n", ret);
		goto err_sof_probe;
	}

	/* check machine info */
	ret = sof_machine_check(sdev);
	if (ret < 0) {
		dev_err(sdev->dev, "failed to get machine info %d\n", ret);
		goto err_machine_check;
	}

	ret = sof_select_ipc_and_paths(sdev);
	if (ret) {
		goto err_machine_check;
	} else if (plat_data->ipc_type != base_profile->ipc_type) {
		/* IPC type changed, re-initialize the ops */
		sof_ops_free(sdev);

		ret = validate_sof_ops(sdev);
		...
	}

	return 0;
	...
}
```

The mandatory [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op is reached through a one-line wrapper that names no chip, the pattern every accessor in [`ops.h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h) follows:

```c
/* sound/soc/sof/ops.h:49 */
static inline int snd_sof_probe(struct snd_sof_dev *sdev)
{
	return sof_ops(sdev)->probe(sdev);
}
```

That hardware probe is the first rung, and the continuation climbs from it through the component fill, the IPC channel, the firmware boot, and finally the component and machine registration:

```
    sof_probe_continue builds the layers bottom up
    ──────────────────────────────────────────────

    ┌────────────────────────────────────────────────────────────┐
    │ sof_init_environment   (probe DSP HW, match machine)       │
    │   snd_sof_probe ─▶ ops->probe   sof_machine_check          │
    └───────────────────────────────┬────────────────────────────┘
                                    ▼
    ┌────────────────────────────────────────────────────────────┐
    │ snd_sof_new_platform_drv   (fill plat_drv descriptor)      │
    └───────────────────────────────┬────────────────────────────┘
                                    ▼
    ┌────────────────────────────────────────────────────────────┐
    │ snd_sof_ipc_init          (sdev->ipc, pick ipc3/ipc4_ops)  │
    └───────────────────────────────┬────────────────────────────┘
                                    ▼
    ┌────────────────────────────────────────────────────────────┐
    │ snd_sof_load_firmware ─▶ snd_sof_run_firmware  (boot DSP)  │
    └───────────────────────────────┬────────────────────────────┘
                                    ▼
    ┌────────────────────────────────────────────────────────────┐
    │ devm_snd_soc_register_component  (publish component + DAIs)│
    │ snd_sof_machine_register         (machine driver)          │
    └────────────────────────────────────────────────────────────┘
```

### Filling the ASoC component descriptor

[`snd_sof_new_platform_drv()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L823) writes the SOF callbacks into the embedded [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) so that when the component registers, ASoC has a complete component driver to drive. The [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) hook is [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759), the PCM operations are the SOF host-DMA wrappers, and [`be_pcm_base`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L200) is set to [`SOF_BE_PCM_BASE`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-audio.h#L38):

```c
/* sound/soc/sof/pcm.c:823 */
void snd_sof_new_platform_drv(struct snd_sof_dev *sdev)
{
	struct snd_soc_component_driver *pd = &sdev->plat_drv;
	struct snd_sof_pdata *plat_data = sdev->pdata;
	const char *drv_name;

	if (plat_data->machine)
		drv_name = plat_data->machine->drv_name;
	...
	else
		drv_name = NULL;

	pd->name = "sof-audio-component";
	pd->probe = sof_pcm_probe;
	pd->remove = sof_pcm_remove;
	pd->open = sof_pcm_open;
	pd->close = sof_pcm_close;
	pd->hw_params = sof_pcm_hw_params;
	pd->prepare = sof_pcm_prepare;
	pd->hw_free = sof_pcm_hw_free;
	pd->trigger = sof_pcm_trigger;
	pd->pointer = sof_pcm_pointer;
	...
	pd->pcm_construct = sof_pcm_new;
	pd->ignore_machine = drv_name;
	pd->be_pcm_base = SOF_BE_PCM_BASE;
	...
}
```

The bodies of these PCM callbacks ([`sof_pcm_open`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L536), [`sof_pcm_hw_params`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L116), [`sof_pcm_trigger`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L385)) are covered on the PCM ops page, and the build of the registered [`struct snd_soc_component`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/soc-component.h#L207) from this descriptor is covered on the ASoC component page. This page stops at the descriptor fill.

### Topology loading fills the lists

The component's [`probe`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) hook runs after the DSP is booted and the component is registered. [`sof_pcm_probe()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/pcm.c#L759) binds the [`component`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) back pointer, builds the topology filename from the [`struct snd_sof_pdata`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75) prefix and name, and calls [`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494):

```c
/* sound/soc/sof/pcm.c:759 */
static int sof_pcm_probe(struct snd_soc_component *component)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(component);
	struct snd_sof_pdata *plat_data = sdev->pdata;
	const char *tplg_filename;
	int ret;
	...
	/* load the default topology */
	sdev->component = component;

	tplg_filename = devm_kasprintf(sdev->dev, GFP_KERNEL,
				       "%s/%s",
				       plat_data->tplg_filename_prefix,
				       plat_data->tplg_filename);
	if (!tplg_filename) {
		ret = -ENOMEM;
		goto pm_error;
	}

	ret = snd_sof_load_topology(component, tplg_filename);
	if (ret < 0)
		dev_err(component->dev, "error: failed to load DSP topology %d\n",
			ret);
	...
}
```

[`snd_sof_load_topology()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2494) requests the topology binary with [`request_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/base/firmware_loader/main.c#L941) and hands each blob to the ASoC topology loader [`snd_soc_tplg_component_load()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-topology.c#L2122) together with [`sof_tplg_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/topology.c#L2305). The parser invokes the SOF widget and DAI handlers, and those append entries to the [`widget_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`pipeline_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`dai_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), [`pcm_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547), and [`route_list`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547):

```c
/* sound/soc/sof/topology.c:2494 */
int snd_sof_load_topology(struct snd_soc_component *scomp, const char *file)
{
	struct snd_sof_dev *sdev = snd_soc_component_get_drvdata(scomp);
	struct snd_sof_pdata *sof_pdata = sdev->pdata;
	const char *tplg_filename_prefix = sof_pdata->tplg_filename_prefix;
	const struct firmware *fw;
	const char **tplg_files;
	int tplg_cnt = 0;
	int ret;
	int i;
	...
	for (i = 0; i < tplg_cnt; i++) {
		...
		ret = request_firmware(&fw, tplg_files[i], scomp->dev);
		if (ret < 0) {
			...
			goto out;
		}

		if (sdev->dspless_mode_selected)
			ret = snd_soc_tplg_component_load(scomp, &sof_dspless_tplg_ops, fw);
		else
			ret = snd_soc_tplg_component_load(scomp, &sof_tplg_ops, fw);

		release_firmware(fw);
		...
	}
	...
}
```

Each blob the loader requests goes to the topology parser with the SOF ops, whose widget and DAI handlers append onto the five list heads on the device:

```
    The .tplg blob parses into the snd_sof_dev list heads
    ─────────────────────────────────────────────────────

    topology blob (request_firmware)
            │  snd_soc_tplg_component_load + sof_tplg_ops
            ▼
    ┌────────────────────────────────┐
    │ SOF widget / DAI tplg handlers │
    └────────────────┬───────────────┘
                     │ append entries onto struct snd_sof_dev
                     ▼
    ┌────────────────────────────────┐
    │ widget_list                    │
    │ pipeline_list                  │
    │ dai_list                       │
    │ pcm_list                       │
    │ route_list                     │
    └────────────────────────────────┘
```

### The DSP hardware ops abstraction

[`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) is the function pointer struct that hides every hardware difference behind a fixed call surface. According to the comment on the struct it is "Used to abstract DSP HW architecture and any IO busses between host CPU and DSP device(s)". Each callback is tagged mandatory or optional, and the embedded [`drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) array carries the DAI drivers the component registers:

```c
/* sound/soc/sof/sof-priv.h:165 */
struct snd_sof_dsp_ops {

	/* probe/remove/shutdown */
	int (*probe_early)(struct snd_sof_dev *sof_dev); /* optional */
	int (*probe)(struct snd_sof_dev *sof_dev); /* mandatory */
	void (*remove)(struct snd_sof_dev *sof_dev); /* optional */
	...
	/* DSP core boot / reset */
	int (*run)(struct snd_sof_dev *sof_dev); /* mandatory */
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
	int (*send_msg)(struct snd_sof_dev *sof_dev,
			struct snd_sof_ipc_msg *msg); /* mandatory */

	/* FW loading */
	int (*load_firmware)(struct snd_sof_dev *sof_dev); /* mandatory */
	...
	/* DAI ops */
	struct snd_soc_dai_driver *drv;
	int num_drv;
	...
	const struct dsp_arch_ops *dsp_arch_ops;
};
```

The core never names a chip; it dereferences through [`sof_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21). [`snd_sof_load_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L474) is the pattern every wrapper in [`ops.h`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h) follows, a thin indirection through the macro to the op:

```c
/* sound/soc/sof/ops.h:474 */
static inline int snd_sof_load_firmware(struct snd_sof_dev *sdev)
{
	dev_dbg(sdev->dev, "loading firmware\n");

	return sof_ops(sdev)->load_firmware(sdev);
}
```

That one wrapper is the shape every accessor takes, the macro expanding to the descriptor's ops struct where the probe, run, block IO, message send, and firmware load entries sit, the mandatory ones checked at probe:

```
    sof_ops(sdev) reaches the grouped snd_sof_dsp_ops surface
    ────────────────────────────────────────────────────────

    sof_ops(sdev) == sdev->pdata->desc->ops
            │
            ▼
    ┌───────────────────────────────────────────────┐
    │ struct snd_sof_dsp_ops                        │
    ├───────────────────────────────────────────────┤
    │ probe_early (opt)   probe (mand)   remove     │
    │ run (mand)          block_read / block_write  │
    │ send_msg (mand)     load_firmware (mand)      │
    │ drv  num_drv        dsp_arch_ops              │
    └───────────────────────────────────────────────┘
      mandatory ops enforced by validate_sof_ops()
```

### The IPC abstraction and its two versions

The DSP and the host exchange commands over a mailbox-and-doorbell channel modelled by [`struct snd_sof_ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523). It serialises transmits with [`tx_mutex`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523), bounds a single message at [`max_payload_size`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523), and reaches the version-specific protocol through [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523):

```c
/* sound/soc/sof/sof-priv.h:523 */
struct snd_sof_ipc {
	struct snd_sof_dev *sdev;

	/* protects messages and the disable flag */
	struct mutex tx_mutex;
	/* disables further sending of ipc's */
	bool disable_ipc_tx;

	/* Maximum allowed size of a single IPC message/reply */
	size_t max_payload_size;

	struct snd_sof_ipc_msg msg;

	/* IPC ops based on version */
	const struct sof_ipc_ops *ops;
};
```

The version is split out into [`struct sof_ipc_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503), a function pointer struct whose top-level callbacks send and receive messages and whose sub-ops handle topology, PM, PCM, and firmware loading for that protocol generation:

```c
/* sound/soc/sof/sof-priv.h:503 */
struct sof_ipc_ops {
	const struct sof_ipc_tplg_ops *tplg;
	const struct sof_ipc_pm_ops *pm;
	const struct sof_ipc_pcm_ops *pcm;
	const struct sof_ipc_fw_loader_ops *fw_loader;
	const struct sof_ipc_fw_tracing_ops *fw_tracing;

	int (*init)(struct snd_sof_dev *sdev);
	void (*exit)(struct snd_sof_dev *sdev);
	int (*post_fw_boot)(struct snd_sof_dev *sdev);

	int (*tx_msg)(struct snd_sof_dev *sdev, void *msg_data, size_t msg_bytes,
		      void *reply_data, size_t reply_bytes, bool no_pm);
	int (*set_get_data)(struct snd_sof_dev *sdev, void *data, size_t data_bytes,
			    bool set);
	int (*get_reply)(struct snd_sof_dev *sdev);
	void (*rx_msg)(struct snd_sof_dev *sdev);
};
```

[`snd_sof_ipc_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc.c#L145) selects the instance by the firmware's [`ipc_type`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L75), [`ipc3_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc3.c#L1142) for the older [`SOF_IPC_TYPE_3`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L55) protocol and [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912) for the [`SOF_IPC_TYPE_4`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L56) protocol Meteor Lake uses, then refuses any version that left a mandatory message, firmware-loader, PCM, or topology op NULL:

```c
/* sound/soc/sof/ipc.c:145 */
struct snd_sof_ipc *snd_sof_ipc_init(struct snd_sof_dev *sdev)
{
	struct snd_sof_ipc *ipc;
	struct snd_sof_ipc_msg *msg;
	const struct sof_ipc_ops *ops;
	...
	switch (sdev->pdata->ipc_type) {
#if defined(CONFIG_SND_SOC_SOF_IPC3)
	case SOF_IPC_TYPE_3:
		ops = &ipc3_ops;
		break;
#endif
#if defined(CONFIG_SND_SOC_SOF_IPC4)
	case SOF_IPC_TYPE_4:
		ops = &ipc4_ops;
		break;
#endif
	default:
		dev_err(sdev->dev, "Not supported IPC version: %d\n",
			sdev->pdata->ipc_type);
		return NULL;
	}

	/* check for mandatory ops */
	if (!ops->tx_msg || !ops->rx_msg || !ops->set_get_data || !ops->get_reply) {
		dev_err(sdev->dev, "Missing IPC message handling ops\n");
		return NULL;
	}
	...
	ipc->ops = ops;

	return ipc;
}
```

The [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912) instance is the one selected on Meteor Lake, and it points its callbacks at the IPC4 transmit, receive, and reply handlers and its sub-ops at the IPC4 PM, firmware-loader, topology, and PCM tables:

```c
/* sound/soc/sof/ipc4.c:912 */
const struct sof_ipc_ops ipc4_ops = {
	.init = sof_ipc4_init,
	.exit = sof_ipc4_exit,
	.post_fw_boot = sof_ipc4_post_boot,
	.tx_msg = sof_ipc4_tx_msg,
	.rx_msg = sof_ipc4_rx_msg,
	.set_get_data = sof_ipc4_set_get_data,
	.get_reply = sof_ipc4_get_reply,
	.pm = &ipc4_pm_ops,
	.fw_loader = &ipc4_loader_ops,
	.tplg = &ipc4_tplg_ops,
	.pcm = &ipc4_pcm_ops,
	.fw_tracing = &ipc4_mtrace_ops,
};
```

The [`pcm`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) sub-op here, [`ipc4_pcm_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4-pcm.c#L1311), is the IPC4 PCM backend; its body is covered on the IPC4 PCM page.

```
    snd_sof_ipc_init selects sof_ipc_ops by ipc_type
    ────────────────────────────────────────────────

      pdata->ipc_type            sdev->ipc->ops
      ┌──────────────────┐       ┌───────────────┐
      │ SOF_IPC_TYPE_3   │ ────▶ │ ipc3_ops      │
      ├──────────────────┤       ├───────────────┤
      │ SOF_IPC_TYPE_4   │ ────▶ │ ipc4_ops      │  (Meteor Lake)
      └──────────────────┘       └───────┬───────┘
                                         ▼
                          ┌───────────────────────────────┐
                          │ struct sof_ipc_ops            │
                          ├───────────────────────────────┤
                          │ tx_msg  rx_msg                │
                          │ set_get_data  get_reply       │
                          │ tplg  pm  pcm  fw_loader      │
                          └───────────────────────────────┘
```

### Firmware boot ties the abstractions together

[`snd_sof_run_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L109) is where the DSP ops and the IPC ops meet. It runs the pre-boot op, releases the DSP cores with the [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op, then blocks on [`boot_wait`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) until the firmware posts its ready message and the IPC RX path advances [`fw_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) past [`SOF_FW_BOOT_IN_PROGRESS`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L37):

```c
/* sound/soc/sof/loader.c:109 */
int snd_sof_run_firmware(struct snd_sof_dev *sdev)
{
	int ret;

	init_waitqueue_head(&sdev->boot_wait);
	...
	/* perform pre fw run operations */
	ret = snd_sof_dsp_pre_fw_run(sdev);
	...
	/* boot the firmware on the DSP */
	ret = snd_sof_dsp_run(sdev);
	if (ret < 0) {
		snd_sof_dsp_dbg_dump(sdev, "Failed to start DSP",
				     SOF_DBG_DUMP_MBOX | SOF_DBG_DUMP_PCI);
		return ret;
	}

	/*
	 * now wait for the DSP to boot. There are 3 possible outcomes:
	 * 1. Boot wait times out indicating FW boot failure.
	 * 2. FW boots successfully and fw_ready op succeeds.
	 * 3. FW boots but fw_ready op fails.
	 */
	ret = wait_event_timeout(sdev->boot_wait,
				 sdev->fw_state > SOF_FW_BOOT_IN_PROGRESS,
				 msecs_to_jiffies(sdev->boot_timeout));
	if (ret == 0) {
		snd_sof_dsp_dbg_dump(sdev, "Firmware boot failure due to timeout",
				     SOF_DBG_DUMP_REGS | SOF_DBG_DUMP_MBOX |
				     SOF_DBG_DUMP_TEXT | SOF_DBG_DUMP_PCI);
		return -EIO;
	}

	if (sdev->fw_state == SOF_FW_BOOT_READY_FAILED)
		return -EIO; /* FW boots but fw_ready op failed */
	...
	sof_set_fw_state(sdev, SOF_FW_BOOT_COMPLETE);

	/* perform post fw run operations */
	ret = snd_sof_dsp_post_fw_run(sdev);
	...
	if (sdev->ipc->ops->post_fw_boot)
		return sdev->ipc->ops->post_fw_boot(sdev);

	return 0;
}
```

The [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op is the DSP-hardware end and [`post_fw_boot`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L503) is the IPC-protocol end, and the [`fw_state`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) field is the rendezvous between them, set to [`SOF_FW_BOOT_COMPLETE`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L41) only after the firmware-ready handshake succeeds.

```
    fw_state advances as the boot handshake proceeds
    ────────────────────────────────────────────────

    SOF_FW_BOOT_NOT_STARTED        (probe start)
            │  sof_set_fw_state (PREPARE)
            ▼
    SOF_FW_BOOT_PREPARE            (load firmware image)
            │  run op releases DSP cores
            ▼
    SOF_FW_BOOT_IN_PROGRESS        (wait on boot_wait)
            │
            ├──▶ SOF_FW_BOOT_READY_FAILED   (fw_ready op failed)
            │
            ▼  firmware-ready message, IPC RX advances state
    SOF_FW_BOOT_COMPLETE           (post_fw_boot op)
```

### Worked example: Meteor Lake on x86 ACPI

On an x86-64 ACPI Meteor Lake machine the audio DSP is the one embedded in the Intel HDAudio controller, enumerated over PCI, and its descriptor `mtl_desc` sets `.ipc_supported_mask = BIT(SOF_IPC_TYPE_4)`, so [`snd_sof_ipc_init()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc.c#L145) selects [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912). The descriptor does not hold a fully static [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165); it supplies an [`ops_init`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) callback, [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702), that fills the ops in place. That fill copies the SKL+ HDAudio-generic base [`sof_hda_common_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-common-ops.c#L17) and then overrides the Meteor Lake mailbox, doorbell, and IPC4 entry points; the override list is the subject of the sibling Intel MTL/LNL dsp_ops page and is not reproduced here, but the base it starts from is the struct the rest of this page traces:

```c
/* sound/soc/sof/intel/hda-common-ops.c:17 */
const struct snd_sof_dsp_ops sof_hda_common_ops = {
	/* probe/remove/shutdown */
	.probe_early	= hda_dsp_probe_early,
	.probe		= hda_dsp_probe,
	...
	/* Block IO */
	.block_read	= sof_block_read,
	.block_write	= sof_block_write,
	...
	/* machine driver */
	.machine_select = hda_machine_select,
	.machine_register = sof_machine_register,
	...
	/* firmware loading */
	.load_firmware = snd_sof_load_firmware_raw,

	/* firmware run */
	.run = hda_dsp_cl_boot_firmware,
	...
	/* DAI drivers */
	.drv		= skl_dai,
	.num_drv	= SOF_SKL_NUM_DAIS,
	...
	.dsp_arch_ops = &sof_xtensa_arch_ops,
};
EXPORT_SYMBOL_NS(sof_hda_common_ops, "SND_SOC_SOF_INTEL_HDA_GENERIC");
```

Tracing one op through the abstraction shows the layering at work. When [`sof_probe_continue()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/core.c#L454) reaches [`snd_sof_load_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L474), that wrapper expands [`sof_ops(sdev)->load_firmware`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ops.h#L21) to `sdev->pdata->desc->ops->load_firmware`, which on this device is [`snd_sof_load_firmware_raw()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/loader.c#L17). That function reads the image into [`basefw`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and parses its extended manifest before the loader copies each segment into DSP memory with the [`block_write`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op:

```c
/* sound/soc/sof/loader.c:17 */
int snd_sof_load_firmware_raw(struct snd_sof_dev *sdev)
{
	struct snd_sof_pdata *plat_data = sdev->pdata;
	const char *fw_filename;
	ssize_t ext_man_size;
	int ret;

	/* Don't request firmware again if firmware is already requested */
	if (sdev->basefw.fw)
		return 0;

	fw_filename = kasprintf(GFP_KERNEL, "%s/%s",
				plat_data->fw_filename_prefix,
				plat_data->fw_filename);
	if (!fw_filename)
		return -ENOMEM;

	ret = request_firmware(&sdev->basefw.fw, fw_filename, sdev->dev);
	...
	/* check for extended manifest */
	ext_man_size = sdev->ipc->ops->fw_loader->parse_ext_manifest(sdev);
	if (ext_man_size > 0) {
		/* when no error occurred, drop extended manifest */
		sdev->basefw.payload_offset = ext_man_size;
	}
	...
}
```

The core wrote no HDAudio register and named no Xtensa core; it called one op pointer, and the [`struct sof_dev_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/sound/sof.h#L128) supplied the rest. The same indirection routes the boot through the [`run`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) op [`hda_dsp_cl_boot_firmware()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-loader.c#L339), the machine match through [`hda_machine_select()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.c#L1489), and the DAI registration through the [`skl_dai`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda-dai.c#L788) array with [`SOF_SKL_NUM_DAIS`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/hda.h#L424) entries, so the entire Meteor Lake difference is contained in the one [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165) instance [`sof_mtl_set_ops()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/intel/mtl.c#L702) built and the [`ipc4_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/ipc4.c#L912) protocol behind the IPC channel.

### The device object joining the ASoC, DSP, and firmware layers

This figure traces how the ASoC core registers the embedded [`plat_drv`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) of [`struct snd_sof_dev`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) through [`devm_snd_soc_register_component()`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/soc-devres.c#L29), how the topology lists fill from the .tplg file, and how the [`ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) and [`ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L547) fields reach the DSP hardware (through [`struct snd_sof_dsp_ops`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L165)) and the firmware (through [`struct snd_sof_ipc`](https://elixir.bootlin.com/linux/v7.0/source/sound/soc/sof/sof-priv.h#L523)).

```
    ASoC core (sound/soc/soc-core.c)
            │  devm_snd_soc_register_component(plat_drv)
            ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  struct snd_sof_dev          (sound/soc/sof/sof-priv.h:547)  │
    │  ┌────────────────────────────────────────────────────────┐  │
    │  │ dev, pdata ─▶ sof_dev_desc.ops                         │  │
    │  │ plat_drv  (struct snd_soc_component_driver, filled)    │  │
    │  │ component (struct snd_soc_component *, bound at probe) │  │
    │  │ basefw    (struct sof_firmware, base image)            │  │
    │  └────────────────────────────────────────────────────────┘  │
    │                                                              │
    │   topology object lists (filled from the .tplg file)         │
    │   ┌───────────┬───────────┬──────────────┬──────────┬──────┐ │
    │   │ pcm_list  │widget_list│ pipeline_list│ dai_list │route │ │
    │   └───────────┴───────────┴──────────────┴──────────┴──────┘ │
    │                                                              │
    │   ops  ─────────────▶  struct snd_sof_dsp_ops  (per platform)│
    │   ipc  ─────────────▶  struct snd_sof_ipc  ─▶ sof_ipc_ops    │
    └───────────────┬──────────────────────────────┬───────────────┘
                    │ block_read/write, run, ...   │ tx_msg (IPC3/IPC4)
                    ▼                              ▼
            DSP hardware (HDA-gen)            DSP firmware (SOF)
```
