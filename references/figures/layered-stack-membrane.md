# Pattern: layered stack / membrane

1. Use when the point is how layers stack and where one layer calls through to the next across a named API boundary (userspace / core / driver / firmware-or-hardware).
2. Draw each layer as a full-width box stacked above the next, and label each ▼ divider with the boundary it crosses (the ioctl, the ops vector, the message channel).
3. The boundary labels are the point, not the box contents.

```
       ASoC core (sound/soc/soc-core.c)
               │  devm_snd_soc_register_component(&sdev->plat_drv, ...)
               ▼
       ┌──────────────────────────────────────────────────────────────┐
       │  struct snd_sof_dev          (sound/soc/sof/sof-priv.h:547)  │
       │   ops ───── sof_ops() ─────▶  struct snd_sof_dsp_ops         │
       │   ipc ─────────────────────▶  struct snd_sof_ipc ─▶ ops      │
       └───────────────┬──────────────────────────────┬───────────────┘
                       │ block_write, run, send_msg   │ tx_msg (IPC3/IPC4)
                       ▼                              ▼
               DSP hardware (HDA-gen)            DSP firmware (SOF)
```
