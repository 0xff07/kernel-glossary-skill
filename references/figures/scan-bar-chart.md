# Pattern: scan bar chart

1. Use when a loop over a set keeps a running maximum or minimum and one member can abort it (a per-endpoint timeout scan, a per-port capability sweep, a per-child resource walk).
2. Draw the members as filled bars `██` in scan order along one axis with height as the value, mark the kept one, draw the aborting member as a shaded bar `▒▒`, and label the members after it as never examined.
3. The shape asserts magnitude, order and the cut; the data-dependency pattern shows what feeds a transform, this shows what a scan over many produces and where it stops.

```
       One scan, the candidate it keeps, and the one that ends it
       ─────────────────────────────────────────────────────────
       (hub timeout candidate per endpoint, in scan order)

          ▲
          │                   ██  ◀ largest so far, the value kept
          │        ██         ██
          │   ██   ██   ██    ██    ██
          │   ██   ██   ██    ██    ██    ▒▒  USB3_LPM_DISABLED
          │   ██   ██   ██    ██    ██    ▒▒  the scan stops, -E2BIG
          └───██───██───██────██────██────▒▒────────▶ scan order
             ep0  ep1  ep2   ep3   ep4   ep5   ep6 never examined
```
