# Pattern: refcount with threshold actions

1. Use when a reference count gates a hardware action only at a threshold crossing (first user enables, last user disables; the 0↔1 edge).
2. Draw the count as horizontal rungs, the raising events climbing one side and the lowering events descending the other, and mark the one rung crossing that reaches the hardware.
3. The shape puts the acting edge next to the inert ones, so the asymmetry is read off the picture rather than counted out of rows.
4. Never a grid of events against transitions against actions, which is the banned plain table.

```
       be_start: the hardware sees only the edges next to 0
       ─────────────────────────────────────────────────────────────
       (two FEs sharing one BE; START climbs the left side, STOP
        descends the right)

         2  ─────────────────────────────────────────────────────
              ▲  a second FE joins.        │  one of the two FEs
              │  be_start reads 1 first,   │  leaves. be_start does
              │  so no trigger is sent     ▼  not reach 0, no trigger
         1  ─────────────────────────────────────────────────────
              ▲  the first FE starts.      │  the last FE leaves.
              │  soc_pcm_trigger(START)    │  soc_pcm_trigger(STOP)
              │  reaches the BE            ▼  reaches the BE
         0  ─────────────────────────────────────────────────────

         START acts only from BE state PREPARE, STOP or PAUSED;
         STOP acts only from START or PAUSED, and lowers be_start
         only when the BE was in START
```
