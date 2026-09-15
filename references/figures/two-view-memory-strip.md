# Pattern: two-view memory strip

1. Use when one region of memory is seen from two address spaces and something on each side points into it (a context array under its DMA base and its kernel pointer, a ring segment, a descriptor block, an skb's data area).
2. Draw the strip once as `┌─┬─┐` cells, the CPU-side name or address on a ruler above and the device-side address on a ruler below, the register or field that holds each address as a labelled arrow into its ruler, and a `├───┤` measurement bar under the first cell giving the cell size.
3. Distinct from the register / address-offset map, which lays out a register block by offset; this is one buffer under two rulers.

```
       One device's context array, as the driver and the controller see it
       ───────────────────────────────────────────────────────────────────

       CPU view virt_dev->out_ctx->bytes
                ┌──────────────┬───────────────┬─────────────────────┐
                │ slot context │ ep context 0  │ ep contexts 1 to 30 │
                └──────────────┴───────────────┴─────────────────────┘
       DMA view virt_dev->out_ctx->dma  ◀── DCBAA[slot_id]
                ├─ CTX_SIZE ───┤  32 or 64 bytes, from HCCPARAMS1
```
