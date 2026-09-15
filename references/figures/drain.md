# Pattern: drain

1. Use when a transition waits for in-flight work to leave before it proceeds (stopping an endpoint before a reset, killing URBs, flushing a workqueue, a grace period).
2. Draw the inlet closed with `──┤`, the in-flight items as a strip that empties toward `──▶`, and the gate as a dashed vertical `╎` that opens when the strip is empty, with what runs next beside it.
3. The shape asserts three facts at once: nothing new enters, what is inside leaves, and the next step waits on emptiness. The refcount ladder shows a count reaching zero; this shows the closed inlet that makes it reach zero.

```
       The ring drains before the reset may run
       ────────────────────────────────────────
       (the inlet is closed; nothing new enters while it empties)

       new work ──┤   ┌──────┬──────┬──────┐  completions   ╎
                      │  td  │  td  │  td  │ ─────────────▶ ╎ gate, opens
                      └──────┴──────┴──────┘                ╎ when the ring
                                                            ╎ is empty; then
                                                            ╎ the reset runs
```
