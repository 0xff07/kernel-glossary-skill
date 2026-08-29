# BAN-06

> Was: Banned words

**INPUT:** Body prose and catalog cells, swept case-insensitively and fence-aware for the banned tokens, with letters as the only delimiter for the arm pattern; CPU-architecture names and verbatim quotes are out of scope.

**OUTPUT:** Prose in which every banned token is replaced by the concrete rule, count, helper, or branch word it stood in for; delivered with the adjudicated hit list at zero unadjudicated findings.

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

**PASS CRITERIA:**

- Zero unadjudicated hits for `contract`, `tally` (also `tallied`/`tallies`/`tallying`), and `canonical` in body prose, swept case-insensitively and fence-aware; each confirmed hit is replaced by the concrete rule, count, or helper it stands in for.
- Sweep `(^|[^a-z])arms?([^a-z]|$)` with letters as the only delimiter: `\b` treats `_` as a word character, so a banned token inside an identifier is invisible to a `\b`-bounded pattern. A hit is "arm"/"arms" for a union case, conditional branch, split side, or one of a pair of code paths. The capitalized architecture names (Arm, ARM64, arm64, "32-bit Arm"), verbatim quotes, and the ordinary English verb ("arms a delayed work item") are exempt per the settled adjudications registry (`../7r-adjudications.md`).
- An exempt hit is cleared, never reworded: a writer once reworded a correct "32-bit Arm" purely to quiet the arm-word pattern, and that rewording was the only defect introduced.
