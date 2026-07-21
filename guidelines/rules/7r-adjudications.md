# 7r. Settled adjudications registry (mandatory reading for every brief)

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

This registry consolidates the exemptions scattered through 7a-7m plus the adjudications settled across generation batches. Writer and lint briefs name this file as a mandatory first read (never summarize it into a brief), so agents apply the decisions instead of re-litigating them, and two agents in the same batch cannot diverge on a boundary. When a new adjudication is settled during a campaign, record it in the run log as a LESSON and surface it to the user, who folds it into this registry (the log is machine-local; only this registry makes a ruling durable).

Exempt (never flag, and never reword a compliant construct to silence a pattern match):
- Capitalized CPU-architecture names for the arm-word ban: Arm, ARM64, arm64, "32-bit Arm".
- Label-colon shapes inside double-quoted verbatim text (commit subjects, kernel comments), in catalog bullets of LINUX KERNEL / KERNEL DOCUMENTATION / OTHER SOURCES, in table cells, and in H3/H4 catalog labels.
- Value and expression spans (`a | B`, `map_count + 2 < limit - 3`): link a constituent symbol where one exists; the span itself is not a bare-span violation.
- Wildcard-family names (`VM_*`) when the members they stand for are linked nearby.
- Hyphenated compounds embedding a hedge word ("read-mostly"); verbatim quotes containing hedges or superlatives.
- `name(2)` man-page notation when the syscall's kernel entry point is linked elsewhere on the page.
- Designated-initializer citations anchored at the initializer line.
- `/proc`, `/sys`, and sysctl path strings; Kconfig fragments (`=y`); tracepoint field names; locals, parameters, and goto labels quoted from excerpts; error and literal values; commit hashes; symbols verified absent from the documented tree (state the absence in prose).

Settled rulings (always required; in-family precedent never overrides them):
- `CONFIG_*` options are always linked to the `config X` line of the declaring Kconfig file (settled after two lint passes diverged on exactly this).
- Generic primitives (`READ_ONCE()`, `memcpy()`, `rcu_read_lock()`, `atomic_read()`, and the like) are always linked to the definition relevant to the documented architecture.
- An ops-struct member named in prose links to that member's line in the struct definition.
- Pre-existing bare spans of the same family get fixed in the same pass; "other pages leave it bare" is never a reason.
- Anthropomorphic placement verbs (`sits`, `lives`, `hangs`, and the lemma set in 3c) are banned in the writer's own authored prose REGARDLESS of the subject — code, data, or a physical device alike. "The device sits behind a translator" and "the field sits in dword 2" are both reworded ("is attached behind", "occupies dword 2", "connects to"); the physical-hardware reading earns no exemption on its own. The ban lifts ONLY where the text is not the writer's own: a verbatim quotation from kernel source, a kernel comment, or in-tree Documentation keeps whatever verb it quotes (this is the general verbatim-quote exemption, stated explicitly for this class), and the same holds for text quoted from this skill's own files. Adjective forms are not the verb and are never in scope: "the live ring", "a live context", "live endpoints" stay. (Settled after a slot-context writer flagged "the device sits in the hub tree" as possibly exempt for physical position; ruled not exempt in authored prose, exempt only when quoted.)
