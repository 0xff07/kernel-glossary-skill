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