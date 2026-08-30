# BAN-WAIVERS: Waivers and settled rulings for bans/

> Was: the bans-owned entries of the settled adjudications registry (7r-adjudications.md, retired to its git pin).

Harness, not a rule: a page cannot violate this file; it modifies how this directory's rules apply. A ruling lands here only through the user — an agent that settles a boundary during a run records it as a LESSON in the run log and surfaces it; only this file makes it durable. Apply what is written, never summarize it into a brief, and never reword a compliant construct to silence a pattern match.

## Exempt (never flag)

- Capitalized CPU-architecture names for the arm-word ban: Arm, ARM64, arm64, "32-bit Arm".
- Label-colon shapes inside double-quoted verbatim text (commit subjects, kernel comments), in catalog bullets of LINUX KERNEL / KERNEL DOCUMENTATION / OTHER SOURCES, in table cells, and in H3/H4 catalog labels.
- Hyphenated compounds embedding a hedge word ("read-mostly"); verbatim quotes containing hedges or superlatives.

## Settled rulings (always required; in-family precedent never overrides them)

- Anthropomorphic placement verbs (`sits`, `lives`, `hangs`, and the lemma set in BAN-01) are banned in the writer's own authored prose REGARDLESS of the subject — code, data, or a physical device alike. "The device sits behind a translator" and "the field sits in dword 2" are both reworded ("is attached behind", "occupies dword 2", "connects to"); the physical-hardware reading earns no exemption on its own. The ban lifts ONLY where the text is not the writer's own: a verbatim quotation from kernel source, a kernel comment, or in-tree Documentation keeps whatever verb it quotes (this is the general verbatim-quote exemption, stated explicitly for this class), and the same holds for text quoted from this skill's own files. Adjective forms are not the verb and are never in scope: "the live ring", "a live context", "live endpoints" stay. (Settled after a slot-context writer flagged "the device sits in the hub tree" as possibly exempt for physical position; ruled not exempt in authored prose, exempt only when quoted.)
