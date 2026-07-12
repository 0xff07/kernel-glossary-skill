# 7c. Forbidden phrases checklist

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

Before writing any body paragraph, scan for these patterns and rewrite if any appear:

- `^.*: [a-z]` (any line where prose ends in `: ` followed by a lowercase clause)
- `The reasoning` (in any case, with or without colon)
- `The intent:` / `The asymmetry:` / `The fix:` / `The point is:` / `The takeaway:` / `The pattern is:` / `Two-phase pattern:`
- `is the key:` / `is essential:` / `is explicit:` / `is significant:` / `is conservative:` / `is deliberate:` / `is the linchpin:` / `is asymmetric:` / `is intentional:` / `is correct:` / `becomes clear here:`
- `Comment: "` introducing a quote in prose (different from the LINUX KERNEL bullet form `[symbol]: bit 0xN. Comment: "..."` which is a catalog entry and acceptable)
- `says: "` / `spells this out: "` / `makes explicit: "` / `makes the trade-off explicit: "` introducing a direct quote in prose
- `X is called from N places: A, B, C` (intro-colon list)
- Any `"intro sentence." + bullet/numbered list` shape in DETAILS, SUMMARY, or lead summary paragraphs

If any of these appear in body prose, rewrite the paragraph as plain declarative sentences. Quote comments with "According to the comment <quote>, ..." or "The comment reads <quote>." instead of label-colon framing.

Do not use these words in body prose; each asserts a framing without naming a mechanism. Replace each with the concrete rule, count, or helper it stands in for.

- "contract" (including "the X, Y, Z contract"): name the actual precondition, guarantee, rule, or invariant. BAD: `The reset, duplicate, destroy contract spans every per-object state.` GOOD: state the reset rule, the duplicate rule, and the destroy rule each path follows.
- "tally": use "count" or "running count". BAD: `the running tally of VMAs`. GOOD: `the running count of VMAs`.
- "canonical": name the helper or path plainly. BAD: `the canonical helper is vma_link() in mm/vma.c`. GOOD: `the helper that performs it is vma_link() in mm/vma.c`.
- "arm" / "arms" for a case of a union, a branch of a conditional, a side of a split, or one member of a pair of code paths: use "branch", "case", "side", "leg", "half", or the concrete symbol name instead. BAD: `the write-fault arm of do_wp_page`. GOOD: `the write-fault branch of do_wp_page`. CPU-architecture names (Arm, ARM64, arm64) and verbatim quotes from kernel source or commit messages are exempt.

Do not hedge with vague frequency or generality words in prose ("usually", "typically", "generally", "often", "normally", "commonly", "mostly", "in practice", "tends to", "on a hot cpu"). Each dodges the actual condition the code tests. Name that condition instead. BAD: `A vm_area_alloc() on a hot cpu usually takes a ready object from the per-cpu sheaf without locking a shared slab.` GOOD: `A vm_area_alloc() takes a ready object from the per-cpu main sheaf without locking a shared slab while that sheaf is non-empty, and reaches the shared slab only to refill an empty sheaf.` A frequency word reproduced verbatim from kernel source inside a fenced block, or a genuine measured statistic that cites a counter or benchmark, is exempt.
