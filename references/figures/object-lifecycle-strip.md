# Pattern: object lifecycle strip

1. Use when one object's fields are written by different functions at named events and the order matters: a per-router record whose two fields are set by different callers at enumeration, at a policy decision, at a tunnel event, at resume and at unplug; a register field rewritten along the same run.
2. Draw one time axis with the events as column heads and a `▼` under each, one segmented bar per field with the value written into each segment, a row of numbered markers under the bars naming the writer at each boundary, and a legend beneath, one entry per mark naming the writer, its site and what it does to the field. Where two bars change at different columns the reader sees the interval in which the object is inconsistent, which is the figure's main assertion.
3. Distinct from the lifetime Gantt, which shows holders and a count; this shows values and their writers. Distinct from the two-field state pair, which shows the legal moves; this shows one actual run. On a page the paragraph after the figure walks the marks in order with the writers linked ([drawing.walk]).

```
       One router's sw->tmu from enumeration to unplug
       ───────────────────────────────────────────────

       time ───────────────────────────────────────────────────────────────────────────►

       event          add          decide           DP tunnel          resume          unplug
                       ▼            ▼   ▼             ▼    ▼             ▼   ▼            ▼
                     ┌────────────┬────┬────────────┬─────┬────────────┬────┬───────────┬──────
       mode          │ hw         │    │ ENH_UNI    │     │ HIFI_BI    │ hw │ re-picked │ OFF
                     └────────────┴────┴────────────┴─────┴────────────┴────┴───────────┴──────
                     ┌────────────┬─────────────────┬──────────────────┬────┬───────────┬──────
       mode_request  │ = mode     │ ENH_UNI         │ HIFI_BI          │ =m │ re-picked │ kept
                     └────────────┴─────────────────┴──────────────────┴────┴───────────┴──────
                      ①            ②   ③             ②    ③             ①   ② ③          ④

       ① tmu_mode_init            tmu.c:357   mode ← what the hardware reports, mode_request ← mode
       ② tb_switch_tmu_configure  tmu.c:1068  mode_request ← the mode the policy asked for
       ③ tb_switch_tmu_enable     tmu.c:1013  mode ← mode_request, once the registers are written
       ④ tb_switch_tmu_disable    tmu.c:620   mode ← OFF, mode_request left as it was
```
