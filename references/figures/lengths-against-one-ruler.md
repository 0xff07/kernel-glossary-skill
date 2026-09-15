# Pattern: lengths against one ruler

1. Use when a fixed budget must contain a sum of parts (a latency inside a service interval, a header inside an MTU, an exit latency inside a timeout) and the failing case is as important as the fitting one.
2. Draw the budget as one ruler `├───┤`, then one row per case with its parts as adjoining span bars starting at the ruler's left end, so a part that runs past the ruler's right end is visible as overhang; label the overhang with its consequence.
3. The shape asserts a length comparison; the frame partition grid divides a frame into claimed slots, while this tests whether the parts fit at all.

```
       SEL plus one bus interval against the service interval
       ───────────────────────────────────────────────────────

                      0                                interval
       budget         ├───────────────────────────────────────┤
       fits           ├──── SEL ────┼─ 125 us ─┤    slack
       does not fit   ├───────── SEL ─────────────────┼─ 125 us ─┤
                                                                 ▲ overhang:
                                                          device-initiated
                                                          entry refused
```
