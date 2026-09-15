# Pattern: signal-timing / waveform

1. Use when the point is where a data bit or sample lands in time relative to a clock or frame edge (a serial-bus frame, a strobe, a sampling instant).
2. Draw each wire as a square-wave trace built from ─ levels and ┌ ┐ └ ┘ │ edges, one trace per line, with a vertical reference column (▼ and │) marking the frame edge so the offset reads straight off the grid; align the data cells under a per-cell clock tick.
3. Distinct from the swimlane (actors handing work over time) and from the frame partition grid (slots claimed on one medium): here the axis is a clock, and the point is where an edge lands relative to it.

```
       I2S vs left-justified: where the left-channel MSB sits
       ────────────────────────────────────────────────────────
       (▼ = tick 0, the WS falling edge that opens the left slot;
        each data cell is one BCLK period)

                     ▼
       WS    ────────┐
                     └────────────────────────────────

       I2S   ─────────────┌────┬────┬────┬────┐    MSB starts one
       SD            ·····│MSB │ b14│ b13│ b12│    BCLK after the edge

       LEFT  ────────┌────┬────┬────┬────┐          MSB starts on
       SD            │MSB │ b14│ b13│ b12│          the edge (no delay)
```
