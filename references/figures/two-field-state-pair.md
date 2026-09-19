# Pattern: two-field state pair

1. Use when an object's state is the relation between two of its fields (a mode and a requested mode, a count and a limit, a value and its shadow) and a handful of numbered actions move it between the settled state and the divergent one.
2. Draw the two states as boxes named by the relation, each action as a labelled `──►` edge carrying its number, the failure and no-op cases as loops on the box they leave unchanged, and a one-line legend mapping the numbers to functions and lines. The reader checks the figure by finding every writer of either field in the legend.
3. Distinct from the state-transition graph over an enumeration of named states; here the two states are defined by a predicate over the fields, and the actions are the writers the page's excerpts show. Distinct from the object lifecycle strip, which shows one run in time; this shows every legal move.

```
       The (mode, mode_request) pair of one router
       ───────────────────────────────────────────

                                ① init
                                   │
                                   ▼
                   ┌─────────────────────┐    ② configure     ┌─────────────────────┐
                   │       settled       │ ─────────────────► │      requested      │
                   │     mode == req     │    ④ disable       │     mode != req     │ ──┐
                   │                     │ ─────────────────► │                     │ ◄─┘ ③ fails
                   │                     │ ◄───────────────── │                     │
                   └─────────────────────┘    ③ enable ok     └─────────────────────┘
                            ▲ │
                            └─┘ ④ disable while req is OFF

       ① tmu_mode_init tmu.c:357   ② tb_switch_tmu_configure tmu.c:1068
       ③ tb_switch_tmu_enable tmu.c:1013   ④ tb_switch_tmu_disable tmu.c:620
```
