# Pattern: side-by-side struct comparison

1. Use when two related types interact via a third operation (match function, encode / decode pair, pack / unpack helpers).
2. Show both struct definitions as boxes side by side with the operation drawn underneath as the convergence point.
3. Distinct from the data-dependency figure (sources feeding one transform that fills a destination) and from linked structs (a pointer topology): here two peer types meet at one operation and neither owns the other.

```
       struct lhs                     struct rhs
       ┌─────────────────┐            ┌─────────────────┐
       │ field_x         │            │ field_x         │
       │ field_y         │            │ field_y         │
       │ ...             │            │ ...             │
       └────────┬────────┘            └────────┬────────┘
                │                              │
                └────────► matcher / op ◀──────┘
                                │
                                ▼
                       returns match iff
                         lhs.field_x == rhs.field_x
                         AND (rhs.field_y == ANY || ...)
```
