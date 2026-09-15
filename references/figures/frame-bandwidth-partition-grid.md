# Pattern: frame / bandwidth partition grid

1. Use when one frame or period of a shared medium is divided into slots or row/column cells, each claimed by an entity (TDM slots, a bus frame's columns, channel allocations).
2. Draw the frame as a contiguous ┌─┬─┐ strip of equal cells labelled by slot, optionally a second strip showing a wider or narrower division of the same frame.
3. The point is how the fixed bandwidth partitions.

```
       I2S frame = the two-slot case of TDM
       ──────────────────────────────────────
       (one sample per slot; set_fmt picks I2S, set_tdm_slot widens it)

       One WS (LRCLK) period:
       ┌───────────────────────┬───────────────────────┐
       │       left slot       │       right slot      │
       │       (WS low)        │       (WS high)       │   I2S = 2 slots
       └───────────────────────┴───────────────────────┘

       Same wires, a wider TDM frame (one FSYNC period, N slots):
       ┌──────┬──────┬──────┬──────┬──────┬─────┬───────┐
       │slot 0│slot 1│slot 2│slot 3│slot 4│ ... │slotN-1│
       └──────┴──────┴──────┴──────┴──────┴─────┴───────┘
          set_tdm_slot assigns each codec channel a slot mask (N > 2)
```
