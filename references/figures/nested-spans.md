# Pattern: nested spans

1. Use when the point is what holds true inside a bracket (a lock held, a feature switched off, a device quiesced) around an operation, and the bracket nests inside another.
2. Draw one time axis, one span bar `├───┤` per bracket on its own row, each inner span strictly inside the outer, and beneath them one row per affected holder showing the value it reads inside the span against the values outside; dashed guides `╎` drop from the span ends to those rows.
3. The shape asserts containment in time; the holder rows show the state of a thing that is not an actor, which a swimlane cannot.

```
       What the two holders read while link power management is off
       ────────────────────────────────────────────────────────────

       time ─────────────────────────────────────────────────────▶
       bandwidth_mutex   ├───────────────────────────────────────┤
       both states off       ├───────────────────────────────┤
       the change itself         ├───────────────────────┤
                             ╎                               ╎
       hub idle timeout 0x7F ╎ 0  0  0  0  0  0  0  0  0  0  ╎ recomputed
       slot exit latency old ╎ 0                             ╎ new
```
