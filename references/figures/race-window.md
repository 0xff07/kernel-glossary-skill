# Pattern: race window

1. Use when a hazard is one path acting on something it read earlier while another path changes it in between (a check-then-act on a state word, a cancel against a completion, a wakeup flag against a suspend decision).
2. Draw one time axis and one row per path; the read-to-act stretch of the first path is a span bar `├───┤` with the read at its left end and the act at its right, and the second path's write is an arrowhead `▲` landing inside the bar with its label beside the stem.
3. The shape asserts that a point falls inside an interval. It is a swimlane only in the sense the swimlane pattern tests: deleting either row kills it.

```
       A state test and the death that lands inside it
       ───────────────────────────────────────────────

       time ─────────────────────────────────────────────────────▶
       CPU A   reads xhc_state         acts on what it read
               RUNNING ├────────────────────────────┤ queues the command
                                     ▲
       CPU B                         │ xhci_hc_died() sets DYING

       the write lands inside A's interval, so A queues a command
       on a controller that is already dead
```
