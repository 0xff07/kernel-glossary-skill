# Pattern: topology with a boundary

1. Use when a guard or a policy is a position in the device tree or on a bus (a depth limit, a per-port capability bit, a segment a rule stops at), and which rule can even reach a device depends on where it sits.
2. Draw the tree from the controller down with the tier numbered in the left margin, mark a closed cell where a per-port bit closes it, draw the limit as a dashed `─ ─` line that the trunk crosses on a `┼`, and label each leaf with the guard that refuses it or the outcome for one that passes. Keep every trunk continuous; labels sit beside a trunk, never on it.
3. The shape asserts that place decides: a boundary at a depth, a closed cell at a position. It also shows which guards cannot reach a device at all, which no ordered list of guards can. Distinct from the parent + N children fan-out, which shows identity and ownership. A run of guards with no place and no magnitude is prose, or the boxed flowchart when it has side effects; a ladder of gate labels asserts nothing once stripped and is not drawn.

```
       Where a device must sit for a timeout to be computed at all
       ────────────────────────────────────────────────────────────
       (tier counts from the root hub; a port's lpm_incapable bit is
        read only for the device plugged straight into that port)

       tier 1   ┌─────────────── host controller ────────────────┐
                │ guard 1: LPM support claimed, slot present     │
                │  port 0          port 1          port 2        │
                └─────┬───────────────┬───────────────┬──────────┘
                      │ lpm_incapable │ capable       │ capable
                  ┌───┴───┐       ┌───┴───┐       ┌───┴───┐
       tier 2     │  dev  │       │  dev  │       │  hub  │
                  └───────┘       └───────┘       └───┬───┘
                  guard 3 refuses           computed  │
                                                  ┌───┴───┐
       tier 3                                     │  dev  │ computed
                                                  └───┬───┘
           ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┼─ ─  deepest tier
                                                  ┌───┴───┐ this host permits
       tier 4                                     │  hub  │
                                                  └───┬───┘
                                                      │
                                                  ┌───┴───┐
       tier 5                                     │  dev  │ guard 2 refuses
                                                  └───────┘
```
