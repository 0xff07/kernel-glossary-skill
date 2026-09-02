# WAIVERS: Settled rulings for the page, fact, plot and diagram rules

> Was: the five per-directory `<PREFIX>-WAIVERS.md` files (2026-08-30), themselves split from the settled adjudications registry (7r-adjudications.md, retired to its git pin). The bans' waivers now sit in the exempt column of `BANS.md`; the fact, plot and diagram directories had settled nothing, so this file carries the page rulings and the empty sections where the others will land.

Harness, not a rule: a page cannot violate this file; it modifies how the rules apply, and the checking protocol routes every adjudication here. A ruling lands here only through the user. An agent that settles a boundary during a run records it in the run log and surfaces it; `guidelines/LESSONS.md` keeps the story, and only this file makes the ruling durable. Apply what is written, never summarize it into a brief, and never reword a compliant construct to silence a pattern match.

## Page rules (PAGE-01 to PAGE-06)

Exempt, never flagged:

- Value and expression spans (`a | B`, `map_count + 2 < limit - 3`): link a constituent symbol where one exists; the span itself is not a bare-span violation.
- Wildcard-family names (`VM_*`) when the members they stand for are linked nearby.
- `name(2)` man-page notation when the syscall's kernel entry point is linked elsewhere on the page.
- Designated-initializer citations anchored at the initializer line.
- `/proc`, `/sys` and sysctl path strings; Kconfig fragments (`=y`); tracepoint field names; locals, parameters and goto labels quoted from excerpts; error and literal values; commit hashes; symbols verified absent from the documented tree (state the absence in prose).

Settled rulings, always required; in-family precedent never overrides them:

- `CONFIG_*` options are always linked to the `config X` line of the declaring Kconfig file.
- Generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()` and the like) are always linked to the definition relevant to the documented architecture.
- An ops-struct member named in prose links to that member's line in the struct definition.
- Pre-existing bare spans of the same family get fixed in the same pass; "other pages leave it bare" is never a reason.
- A dense reference table is not exempt: a census or semantics table whose column holds bare symbol names has every occurrence linked, exactly as flowing prose does, even when the same symbol is linked in the text introducing the table. Settled 2026-09-01; the corpus carries no cross-page links, so an unlinked symbol in a table is a dead end for a reader who landed mid-table, and density is the accepted cost.

## Fact rules (FACT-01 to FACT-04)

None settled yet.

## Derivation (PLOT-04)

None settled yet.

## Figure rules (DIAG-01 to DIAG-04)

None settled yet.
