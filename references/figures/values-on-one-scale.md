# Pattern: values on one scale

1. Use when several computed or configured values are positions on one axis with a floor, a ceiling or both, and the point is where each lands relative to the others (timeout tiers, an encoding's output range, a latency against its limit).
2. Draw one axis with tick labels, a `┬` at each value and an L-connector callout beneath naming it; callouts nest rightmost-first, the register-figure convention. Mark a floor or a ceiling as a labelled tick.
3. The shape asserts order and distance; a value the reader must compare with another belongs on the same axis, never in a second figure.
4. Distinct from the ordered level ladder, whose levels are discrete states a value moves through; here the positions are magnitudes.

```
       Where each endpoint type's U1 candidate lands
       ─────────────────────────────────────────────
       (the periodic floor rises to 105% of the service interval
        when that is larger)

       0        1        2        3        4        5   multiples of SEL
       ├─────────────────┬────────┬─────────────────┬─────────────▶
                         │        │                 └─ bulk
                         │        └─ control, notification interrupt
                         └─ periodic floor
```
