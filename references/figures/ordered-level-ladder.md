# Pattern: ordered level ladder

1. Use when a value moves through a small set of strictly-ordered levels and the travel direction matters (power/bias states, D-states, link states).
2. Draw the levels as rows in numeric order, highest at the top, with ▲ (up) and ▼ (down) markers down the side and the per-step rule.
3. Distinct from a state-transition graph: a ladder is monotonic and totally ordered, traversed one step at a time.

```
       enum snd_soc_bias_level: one context climbs and descends the ladder
       ──────────────────────────────────────────────────────────────────

         value   level                  bias_level ──▶ target_bias_level

           3   ┌──────────────┐  ON        full power, signal flowing
               │ SND_SOC_BIAS │
           2   │   _PREPARE   │  PREPARE   transitional, around ON
           1   │              │  STANDBY   supplies up, idle floor
           0   └──────────────┘  OFF       powered down (init seed)

         up:    OFF ─▶ STANDBY ─▶ PREPARE ─▶ ON
         down:  ON  ─▶ PREPARE ─▶ STANDBY ─▶ OFF
```
