# Pattern: metro map (routes over shared stations)

1. Use when several ordered paths (the legs of a callback chain, the modes of one mechanism, the variants of one journey) pass through one set of common stops, and the point is which stops each path visits, in which order, and which it skips.
2. Draw one horizontal line per path, named by a letter at its left end, with its stops as ◉ placed in columns shared across every line, so a stop two paths visit reads as an interchange; a stop a path skips is a ╳ on its line in that column; under each stop write the state it establishes (a lock taken, a channel stopped, a flag carried), never the next function called; a path that runs the stops in the other direction says so once, in a footer line, rather than being drawn twice.
3. Distinct from a swimlane (actors over one timeline, one path through them): here N paths each carry their own order and share stops. Distinct from a DAG: the order along each line is the point, not fan-in or fan-out.
4. The labels under the stops carry what holds after the stop. A line whose stops are function names in call order is the banned flow graph drawn as rails.
5. If every line visits every stop in the same order, the figure has one line and belongs to a swimlane or a ladder instead; the value is in the ╳ and in the columns that differ.

```
    Three legs through the same stations, suspend direction

    system   S ──◉─────────────◉──────────◉──────────────◉──────────────◉──▶
                nhi_suspend    tb->lock   cm hook:       tb_ctl_stop    nhi->ops->
                _noirq         taken      tb_suspend     (inside the    suspend_noirq
                                          _noirq         lock)          (nhi, wakeup)

    hibernate H ──◉─────────────◉──────────◉──────────────◉──────────────╳
                nhi_freeze     tb->lock   cm hook:       tb_ctl_stop    no host-
                _noirq         taken      tb_freeze      (inside the    interface
                                          _noirq         lock)          stop

    runtime  R ──◉─────────────╳──────────◉──────────────◉──────────────◉──▶
                nhi_runtime    no lock    cm hook:       tb_ctl_stop    nhi->ops->
                _suspend                  tb_runtime     (unlocked)     runtime_suspend
                                          _suspend

    resume runs each line right to left, with tb_ctl_start where tb_ctl_stop stands
```
