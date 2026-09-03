# ROUTINE-07: Figure repair

> Was: none — new with the repair pass over the figures in `../diagrams/`, which found broken geometry the per-figure sign-off had passed by eye. Harness, not a rule: a page cannot violate this file; it is the procedure for repairing a figure the geometry criteria reject.

The geometry criteria in `../diagrams/DIAG-01.md` and `../diagrams/DIAG-03.md` say what a figure must look like. This file says how to find the breakage mechanically and how to repair each class of it, because eyeballing a figure passes broken geometry: the defects below all survived a per-figure sign-off.

## Find the breakage mechanically

1. Extract every fenced block, then drop the ones that are not figures: a ` ```c ` source excerpt and a fence reproducing a verbatim quotation are exempt from the figure rules and are never repaired.
2. Flag any line longer than 80 columns, allowing the one exception the register rules name (a register drawn as a single row with L-connectors).
3. Flag ASCII `\`, `/`, and `|` used as a side, corner, junction, connector, or extent marker. Leave the three exempt uses alone: an English word separator, a C expression such as `||`, and reproduced kernel source.
4. Group the rows of ONE box, then check that box against itself: its left border column, its right border column, and every interior `│` must meet a border or junction character (`┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ │`) in the row above and the row below.
5. Follow every vertical trunk to both ends. A trunk must terminate on a junction, an arrowhead, or a labelled elbow at each end; a trunk that stops in blank space is broken however straight it looks.
6. Check that a measurement bar, an extent drawn under a strip or a box, spans exactly the columns of the thing it measures, since a bar that overshoots asserts a width the figure does not have. A span bar on a time or value axis (a Gantt holder, a bracket, a budget) is the datum itself, sized to its own extent, and is measured against nothing.

## Repair each class

1. Replace an ASCII extent marker with a Unicode bar sized to the box it measures: `├` on the box's left border column, `┤` on its right border column, `─` between them.
2. When the label no longer fits inside the bar, put the label on its own line beneath the bar rather than letting the bar grow past the box.
3. Re-anchor a trunk that leaves a border at a non-junction: change the border character under it to `┬` where the trunk descends, `┴` where it rises, and `┼` where it crosses, or move the trunk to a column that already carries a junction.
4. Delete a trunk that hangs in blank space, and redraw the relationship it was carrying as a straight arrow between the two boxes' facing borders, with its label in the gutter directly above the arrow.
5. Re-pad the rows of a box so every row of that box ends on the same column, and leave annotations outside the box alone: they legitimately run past its right border.
6. Re-run the check after every repair, because a repair moves columns and a moved column breaks the next junction.

## Before and after

An ASCII extent marker, replaced by a Unicode bar with the label moved beneath it. **Before:**

```
                 │      ┌────┬────┬────┬────┬─────┬─────┐
                 │      │ t0 │ t1 │ t2 │ t3 │ ... │tN-1 │
                 │      └────┴────┴────┴────┴─────┴─────┘
                 │      |<── one entry per index in outer ──>|
```

**After:**

```
                 │      ┌────┬────┬────┬────┬─────┬─────┐
                 │      │ t0 │ t1 │ t2 │ t3 │ ... │tN-1 │
                 │      └────┴────┴────┴────┴─────┴─────┘
                 │      ├───────────────────────────────┤
                 │        one entry per index in outer
```

An extent bar that overshot the strip it measures by seven columns, resized to the strip. **Before:**

```
                 ┌────┬────┬────┬────┬────┬────┬─────┐
                 │ U0 │ U1 │ U2 │ U3 │ U4 │ ...│UN-1 │  fixed-size units
                 └────┴────┴────┴────┴────┴────┴─────┘  one bit per unit
                 |<──── total span of one linked_t ──────────>|
```

**After:**

```
                 ┌────┬────┬────┬────┬────┬────┬─────┐
                 │ U0 │ U1 │ U2 │ U3 │ U4 │ ...│UN-1 │  fixed-size units
                 └────┴────┴────┴────┴────┴────┴─────┘  one bit per unit
                 ├───────────────────────────────────┤
                      total span of one linked_t
```

A trunk hanging in blank space and an arrow stopping short of its target, redrawn as straight arrows between the facing borders. **Before:**

```
       │ Stage A reads    │       │e0│e1│e2│ ... │e_n│        │ Stage B      │
       │ source, RW1C     │  put  └──┴──┴──┴─────┴───┘  get   │ dequeues,    │
       │ clear, enqueue   │ ──▶      ▲              │   ──▶   │ processes    │
       │ ... return       │          │              └──────▶  │ ... return   │
       │ IRQ_WAKE_THREAD  │          │                        │ IRQ_HANDLED  │
       └──────────────────┘          │                        └──────────────┘
```

**After:**

```
       │ Stage A reads    │  put  │e0│e1│e2│ ... │e_n│  get   │ Stage B      │
       │ source, RW1C     │──────▶└──┴──┴──┴─────┴───┘───────▶│ dequeues,    │
       │ clear, enqueue   │                                   │ processes    │
       │ ... return       │                                   │ ... return   │
       │ IRQ_WAKE_THREAD  │                                   │ IRQ_HANDLED  │
       └──────────────────┘                                   └──────────────┘
```

## What the check reports that is not breakage

1. A row that runs past the box because an annotation sits outside its right border, which the geometry rules allow.
2. Two boxes drawn at different indents inside one figure, which differ in width by design.
3. A `│` above a `▼` or below a `▲`, which is a trunk meeting its own arrowhead.
4. A C expression such as `field_y == ANY || ...` inside annotation text, which the ASCII exemption covers.
5. A dashed vertical `╎` used as a guide or a barrier: it aligns rows across a figure or marks a gate, terminates on the row it aligns or beside its label, and carries no trunk relationship, so rule 5's termination test does not apply to it. (Added 2026-09-03.)
6. A span bar `├───┤` on a time or value axis with no box above it, which is a datum and not a measurement; rule 6 applies to measurement bars only. (Added 2026-09-03.)

**PASS CRITERIA:** This file imposes no page-level check of its own; a page cannot fail it directly. It passes through use: every figure the geometry criteria reject is repaired by the matching repair above rather than by nudging characters until it looks right, the check is re-run after each repair, and the four classes above are recorded as cleared rather than fixed.
