# Pattern: before / after transformation

1. Use when an operation changes the shape of one data structure (a split, a merge, an insert, a remove, a move, an in-place encode) and the point is the structure before versus after.
2. Draw the structure twice in the same cell style, labelled `before` and `after`, with the operation as a labelled `──▶` between them (or the two states stacked, before above after), so the change is read by diffing the two drawings.
3. Keeping the cell style identical across the two sides is what makes the diff legible.
4. Distinct from data dependency, which feeds inputs through a transform into a *different* destination struct: here the *same* structure is shown reshaped on both sides.

```
    __split_vma at boundary S: one maple-tree interval before and after
    ───────────────────────────────────────────────────────────────────

    before                          after
    ┌─────────────────────────┐     ┌────────────┬────────────┐
    │ node  [vm_start, vm_end)│ ──▶ │ [vm_start, │ [S,        │
    │ one interval            │     │  S)        │  vm_end)   │
    └─────────────────────────┘     └────────────┴────────────┘

    one node becomes two, the covered range is unchanged, and the
    new node is a vm_area_dup copy of the original with its own range
```
