# Pass 03: lint

Purpose: mechanical and checklist compliance on a finished page; an independent pass with fresh context reliably catches the wrong anchors, drifted excerpts, and skipped spans the writer cannot see in its own work.
Inputs: the draft page, the kernel tree at the documented version, and the page's dossier (hints for re-derivation, never evidence).
Outputs: the page fixed in place, plus a lint report at `progress/<campaign-or-topic>/<page-slug>.lint.md` covering findings fixed by class with counts, 7o corrections with the search evidence, parity gaps, candidates adjudicated as exempt with reasoning, and residual items.
Run by: single-agent mode inline (lint your own page before verifying it); in a campaign a lint agent on a different, cheaper model with fresh context (`guidelines/agents/lint.md`).
Next: pass 04 (`guidelines/passes/04-verify.md`).

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

Read `guidelines/rules/7r-adjudications.md` before touching the page, and judge every candidate against it BEFORE editing. A hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself a defect.

## Steps

All fixes are made in place, and every check is re-run after your own edits.

1. Mechanical checks by hand, per `guidelines/gates/mechanical-checks.md`: open every Elixir link target and confirm definition-line anchoring (7m); compare every ` ```c ` block against its `/* path:line */` provenance on disk, unit by unit, confirming each excerpt begins at its cited line; run the Gate A candidate greps fence-aware (`guidelines/gates/gate-a.md`). Fix confirmed findings in place: wrong anchors get re-looked-up on disk, non-verbatim blocks get re-excerpted from the file, banned prose gets rewritten with the 7q recipes.
2. Read-through Gate A sweep for what the candidate greps cannot express: boldface in prose, intro-sentence-plus-list shapes (7b), hollow superlatives judged in context (7d), negative constructions, anthropomorphic verbs.
3. Exhaustive span pass (7m): every occurrence of every kernel symbol outside fenced blocks is linked, INCLUDING repeats, `CONFIG_*` options (to the Kconfig `config` line), generic primitives (`READ_ONCE`, `memcpy`, `rcu_read_lock`, and the like, to their definitions for the documented architecture), field paths `a->b` (to the field declaration), and named ops-struct members. Exemptions and rulings come from the 7r registry. Never cite in-page or in-family precedent to leave a span bare; the rule always wins, and pre-existing bare spans in the same family get fixed too.
4. Correctness re-derivation (7o): re-run the enumeration behind every count and every "only"/"never"/"always"/"exactly" claim (start from the dossier's recorded search bases, then re-run them); rebuild the member-to-property mapping behind every "each/every X" sentence (one exception falsifies it; fix the sentence, restrict the family, or state the classifier and its boundary); check every lead and SUMMARY quantifier against the DETAILS section, table, or enumeration that carries its evidence; re-derive every restated guard against its excerpt; confirm each DETAILS heading is true of everything in its section; confirm each excerpt begins at its claimed provenance line. These are the only fact edits this pass may make; report each with the search run and its result.
5. Parity audit (Gate B item 1, `guidelines/gates/gate-b.md`): build the catalog-to-DETAILS table, one row per LINUX KERNEL symbol, recording where its definition excerpt and its usage excerpt land. Flag the tripwire if the page has fewer ` ```c ` blocks than catalog entries. In a campaign, do not write missing sections; report every empty cell as a coverage gap for a writer follow-up. A solo agent fixes the gaps itself before moving to verify.
6. Beyond the 7o corrections, do not change facts, scope, or structure; this is a compliance pass. Use a unique scratchpad filename for any helper script you improvise (shared names have collided between concurrent lint agents).
