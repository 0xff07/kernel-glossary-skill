# Pattern: register / address-offset map

1. Use when several registers sit at fixed offsets within a block, or one block repeats at base + stride · index, and the addressing is the point (per-stream, per-port, or per-lane blocks).
2. Draw the index ──▶ base-address column on the left, and one representative block expanded as a box of its named registers on the right.
3. Distinct from a single-register bitfield figure, which plots the bits of one register.

```
       Per-stream SDn register blocks (one per host DMA engine)
       ──────────────────────────────────────────────────────────
       SDn block base = remap_addr + 0x80 + 0x20 * idx   (stride 0x20)

         idx        SDn block base
         ───        ──────────────
          0   ───▶  remap_addr + 0x80     ┌──────────────────────┐
          1   ───▶  remap_addr + 0xA0     │ SDn descriptor:      │
          2   ───▶  remap_addr + 0xC0     │   stream tag         │
          .                               │   cyclic buf length  │
          .                               │   format value       │
          n   ───▶  remap_addr            │   last-valid-index   │
                     + 0x80 + 0x20*n      │   BDL base address   │
                                          └──────────────────────┘

       snd_hdac_stream_setup() programs the block for the assigned idx
       idx split: capture  = [0 .. capture_streams)
                  playback = [capture_streams .. num_streams)
```
