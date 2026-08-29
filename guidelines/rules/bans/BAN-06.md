# BAN-06

> Was: Banned words

**Words to watch:** contract, tally, tallied, tallies, tallying, canonical, arm, arms (for a branch or union case)

**Problem:** Each of these asserts a framing without naming a mechanism. Replace each with the concrete rule, count, or helper it stands in for.

**"contract"** (including "the X, Y, Z contract") — name the actual precondition, guarantee, rule, or invariant. **Before:**

```
The reset, duplicate, destroy contract spans every per-object state.
```

**After:** state the reset rule, the duplicate rule, and the destroy rule each path follows.

**"tally"** — use "count" or "running count". **Before:**

```
the running tally of VMAs
```

**After:**

```
the running count of VMAs
```

**"canonical"** — name the helper or path plainly. **Before:**

```
the canonical helper is vma_link() in mm/vma.c
```

**After:**

```
the helper that performs it is vma_link() in mm/vma.c
```

**"arm" / "arms"** for a case of a union, a branch of a conditional, a side of a split, or one member of a pair of code paths — use "branch", "case", "side", "leg", "half", or the concrete symbol name. **Before:**

```
the write-fault arm of do_wp_page
```

**After:**

```
the write-fault branch of do_wp_page
```

Do not flag CPU-architecture names (Arm, ARM64, arm64) or verbatim quotes from kernel source or commit messages.
