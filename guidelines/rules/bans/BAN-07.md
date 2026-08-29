# BAN-07

> Was: Hedges

**Words to watch:** usually, typically, generally, often, normally, commonly, mostly, in practice, tends to, on a hot cpu

**Problem:** Each hedge dodges the actual condition the code tests. Name that condition instead.

**Before:**

```
A vm_area_alloc() on a hot cpu usually takes a ready object from the per-cpu sheaf without locking a shared slab.
```

**After:**

```
A vm_area_alloc() takes a ready object from the per-cpu main sheaf without locking a shared slab while that sheaf is non-empty, and reaches the shared slab only to refill an empty sheaf.
```

Do not flag a frequency word reproduced verbatim from kernel source inside a fenced block, or a genuine measured statistic that cites a counter or benchmark.

**PASS CRITERIA:** Sweep the words-to-watch list case-insensitively over the prose view (the fuller sweep in `../rules.md` under 3c adds `simply`, `essentially`, `basically`, `arguably` to the same pass). Every confirmed hit is rewritten to name the exact condition the code tests, so no frequency word stands in for a testable predicate. Exempt: hyphenated compounds embedding a hedge word ("read-mostly", "update-often"), frequency words inside verbatim quotes or fenced source, and a genuine measured statistic that cites its counter or benchmark. Pass at zero unadjudicated hedges in body prose.