# Pattern: directed graph / DAG

1. Use when a multi-node signal or dependency graph has fan-in and fan-out, plus auxiliary nodes (supplies, clocks) that attach to the side rather than carry signal.
2. Draw the signal nodes as boxes joined left-to-right by ──▶ edges, mux fan-in with ─┐/─┘ collectors, and side nodes attached with ◀── or a ▲ stem.
3. More general than parent + N children fan-out (one parent, one level).

```
       rt722-sdca playback + speaker paths; PDE supplies hang off sideways
       ──────────────────────────────────────────────────────────────────

         ┌────────┐      ┌────────┐      ┌────────┐
         │ DP1RX  │ ───▶ │ FU 42  │ ───▶ │   HP   │ ◀── PDE 47 (supply)
         │ aif_in │      │  dac   │      │ output │
         └────────┘      └────────┘      └────────┘

         ┌────────┐      ┌────────┐      ┌────────┐
         │ DP3RX  │ ───▶ │ FU 21  │ ───▶ │  SPK   │ ◀── PDE 23 (supply)
         │ aif_in │      │  dac   │      │ output │
         └────────┘      └────────┘      └────────┘

         static routes {"HP",NULL,"FU 42"} and {"SPK",NULL,"FU 21"} pass
         signal; {"HP",NULL,"PDE 47"} ties the supply to the output pin.
```
