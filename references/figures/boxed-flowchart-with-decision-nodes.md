# Pattern: boxed flowchart with decision nodes

1. Use when a function has 3+ sequential decision points with side effects and back-edges, and showing each step in its own box adds clarity.
2. Each step gets its own box; each decision node has explicit yes / no labels on outgoing edges; loops draw an explicit back-edge with an arrow.
3. Reserve this for paths with real branching; a 2-state decision should be written as prose instead.
4. The boxes name conditions and effects, never callees.
5. A chart whose boxes are function names and whose edges mean "calls" is the banned flow graph however many decision diamonds are drawn around it; the test is whether removing every function name would leave a decision structure behind.

```
       ┌─────────────────┐
       │ acquire lock    │
       └────────┬────────┘
                │
       ┌────────▼────────┐    yes
       │ early-exit cond?│──────────▶  break
       └────────┬────────┘
                │ no
                ▼
       ┌─────────────────┐
       │ read register   │
       └────────┬────────┘
                │
       ┌────────▼────────┐    yes ┌──────────────┐
       │ event present?  │──────▶ │ handle event,│
       └────────┬────────┘        │ continue ────┼── back-edge to top
                │ no              └──────────────┘
                ▼
              break

       break ─▶ release lock, return
```
