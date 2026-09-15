# Pattern: state-transition graph

1. Use when an object moves through named states and the legal transitions (including back-edges and self-loops) are the point.
2. Draw each state as a boxed node and each event as a labelled directed ──▶ edge; draw the back-edges explicitly.
3. Distinct from the boxed decision flowchart, which traces control flow through one function; this traces an object's state across its lifetime.

```
       Tip-sense plug state machine (in cs42l42_irq_thread)
       ────────────────────────────────────────────────────
       current_plug_status drives plug_state; only a real change
       of state acts, so repeated reports are ignored.

                       ┌───────────────────────────┐
               ┌──────▶│ CS42L42_TS_UNPLUG         │
               │       │  cancel hs type detect,   │
               │       │  report 0 over the wide   │
               │       │  HEADSET + BTN_0..3 mask  │
               │       └─────────────┬─────────────┘
               │ TS_UNPLUG           │ TS_PLUG
               │                     ▼
               │       ┌───────────────────────────┐
               │       │ CS42L42_TS_PLUG           │
               └───────┤  cs42l42_init_hs_type_    │
                       │  detect (start a cycle)   │
                       └─────────────┬─────────────┘
                                     │ neither bit set
                                     ▼
                       ┌───────────────────────────┐
                       │ CS42L42_TS_TRANS          │
                       │  transient, no report     │
                       └───────────────────────────┘
```
