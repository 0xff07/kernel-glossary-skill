# PAGE-WAIVERS: Waivers and settled rulings for page/

> Was: the page-owned entries of the settled adjudications registry (7r-adjudications.md, retired; the split ledger is tests/TEST-08.md).

Harness, not a rule: a page cannot violate this file; it modifies how this directory's rules apply. A ruling lands here only through the user — an agent that settles a boundary during a run records it as a LESSON in the run log and surfaces it; only this file makes it durable. Apply what is written, never summarize it into a brief, and never reword a compliant construct to silence a pattern match.

## Exempt (never flag)

- Value and expression spans (`a | B`, `map_count + 2 < limit - 3`): link a constituent symbol where one exists; the span itself is not a bare-span violation.
- Wildcard-family names (`VM_*`) when the members they stand for are linked nearby.
- `name(2)` man-page notation when the syscall's kernel entry point is linked elsewhere on the page.
- Designated-initializer citations anchored at the initializer line.
- `/proc`, `/sys`, and sysctl path strings; Kconfig fragments (`=y`); tracepoint field names; locals, parameters, and goto labels quoted from excerpts; error and literal values; commit hashes; symbols verified absent from the documented tree (state the absence in prose).

## Settled rulings (always required; in-family precedent never overrides them)

- `CONFIG_*` options are always linked to the `config X` line of the declaring Kconfig file (settled after two lint passes diverged on exactly this).
- Generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()`, and the like) are always linked to the definition relevant to the documented architecture.
- An ops-struct member named in prose links to that member's line in the struct definition.
- Pre-existing bare spans of the same family get fixed in the same pass; "other pages leave it bare" is never a reason.
