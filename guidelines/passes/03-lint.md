# Pass 03: lint-fix

Purpose: an independent, fresh-context sweep of a finished page for prose and form defects — the classes a writer reliably misses in its own prose — with the settled classes fixed in place and everything unsettled escalated find-only. Fixing here is what keeps post-writer repair cheap: no finding in a settled class ever costs a writer resume or an extra dispatch round.
Inputs: the draft page; the 7r registry; the writing rules the sweeps exercise; the mechanical-check procedures.
Outputs: the page with lane-1 fixes applied, and a report at `progress/<campaign>/<page-slug>.lint.md` (the run's artifact directory, SKILL.md ("The progress/ workspace")): every candidate found, each FIXED (with the exact before/after), ESCALATED (with a proposed fix), or EXEMPT (with the 7r ruling applied). Page state after this pass: LINTED.
Run by: single-agent mode inline (a solo agent sweeps and fixes its own page the same way, then continues); in a campaign a fixer agent on a different, cheaper model with fresh context (brief at the end of this file).
Next: the orchestrator checkpoint (campaigns: escalations are adjudicated there and accepted ones applied by re-dispatching a fixer with the reviewed fix list); a solo agent continues into pass 04 (`guidelines/passes/04-verify.md`).

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

Read `guidelines/rules/7r-adjudications.md` before touching the page, and judge every candidate against it BEFORE fixing or proposing anything. A hit on an exempt construct is a false candidate, and rewording a compliant phrase to silence a pattern is itself a defect — the two-lane split below exists precisely so that nothing gets "fixed" on an unsettled judgment.

## The two lanes

Lane 1 — fix in place. Only candidates whose ruling the 7r registry settles and whose rewrite is a 7q recipe or a mechanically provable correction:

- Prose classes with a 7q recipe: em-dashes, label-colon idioms, hedges, banned words, the arm-word ban, negative constructions, anthropomorphic verbs, banned heading shapes, boldface, 7b intro-sentence-plus-list shapes.
- Bare-span linking (7m): fix a bare kernel-symbol span only after deriving its link target and printing the disk line to confirm the anchor (mechanical-checks item 1 procedure); an ambiguous target escalates.
- Line-drift correction, under a strict byte-match precondition: when an excerpt unit's bytes match its provenance file exactly but at a shifted line (mechanical-checks item 2 procedure, unique match required), update the cited line in the `/* path:line */` provenance comment and in any prose anchor that cites the same location. Any content difference, or a non-unique match, is a substance finding — escalate, never adjust the number to make it fit.
- Diagram geometry only: junction alignment, over-80-column lines, ASCII `\|/` connectors replaced with box-drawing — where the fix preserves the figure's content exactly. Anything amounting to a redraw escalates.

Lane 2 — escalate find-only. Everything else: candidates without a settled ruling, 7d superlatives whose in-context judgment is not obvious, heading-truth questions, anything touching the page's mission or boundary, and every suspected substance defect (wrong count, dubious claim, parity hole, excerpt content mismatch) — the last class goes in a SUBSTANCE NOTES section of the report for the verify stage; do not act on it.

Hard boundary, inherited unchanged from the old patch stage: the fixer never fixes substance — no excerpt additions or extensions, no coverage or parity closure, no fact, count, or claim edits, no anchor re-derivation beyond the two byte-proved procedures above. Fenced blocks are preserved byte-for-byte except the provenance-comment line of a byte-proved drift fix.

## Steps

1. Gate A candidate greps, fence-aware, per `guidelines/rules/3c-mechanical-checks.md` item 3: em-dashes, label-colon shapes, hedges, the arm-word ban, banned words, negative constructions, internal `.md` links, banned heading shapes, boldface.
2. Read-through sweeps for what the greps cannot express: 7b intro-sentence-plus-list shapes, 7d superlatives judged in context, anthropomorphic verbs (`lives`/`sits`/`wants` for code or data placement; `walk` outside data-structure traversal), and heading shape (declarative subject-verb-object, no bare nouns or symbol names; heading truth against section content stays with verification).
3. Exhaustive 7m span-form pass: every occurrence of every kernel symbol outside fenced blocks is linked, INCLUDING repeats, `CONFIG_*` options, generic primitives, field paths, and named ops-struct members, with `struct`/`enum` keywords kept (7f). Exemptions and rulings come from the 7r registry.
4. Sort every candidate into its lane and apply lane 1: each fix per its 7q recipe or byte-proved procedure, exactly and minimally. Re-run the Gate A candidate greps over every paragraph you touched (fence-aware) to confirm the edits introduced no new candidates.
5. Write the report: FIXED items grouped by class with counts and the exact before/after per fix; ESCALATED items each with location, exact current text, and a fix stated precisely enough to apply without judgment; EXEMPT candidates with the ruling applied (state the 7r ruling count as proof of the registry read); SUBSTANCE NOTES last. Anything you persist goes in `progress/<campaign>/` under a unique `<page-slug>.`-prefixed name (shared names have collided between concurrent agents).

## Dispatching a fixer (campaign brief)

Role: runs this pass on one finished page — sweeps, fixes lane 1, escalates lane 2 — or, when dispatched with a FIX LIST, applies an orchestrator-reviewed list of already-adjudicated fixes exactly as stated (the application round for accepted escalations, and the fix channel of a verify campaign, `guidelines/passes/04-verify.md`). Model tier: a different, cheaper model than the writer, in fresh context; the work is pattern-plus-registry sweeping and recipe application, and fresh eyes are the point. On death, re-dispatch fresh from the same brief; the agent holds no state worth resuming beyond its report draft.

```
Lint-fix the finished page <path>.
[FIX-LIST MODE: apply the reviewed fix list below to <path>; skip the
sweeps entirely; every constraint still applies.]

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before touching the page:
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — first action. Judge
   every candidate against it BEFORE fixing or proposing; a hit on an
   exempt construct is a false candidate, and rewording a compliant
   phrase to silence a pattern is itself a defect.
2. <SKILL_DIR>/guidelines/passes/03-lint.md — your procedure: the two
   lanes and steps 1 through 5. Execute in order.
3. <SKILL_DIR>/guidelines/rules/3a-gate-a.md and the procedures in
   <SKILL_DIR>/guidelines/rules/3c-mechanical-checks.md (items 1-3; items 1
   and 2 are the preconditions for span-link and line-drift fixes).
4. <SKILL_DIR>/guidelines/rules/INDEX.md, then the rule files this pass
   exercises: 7q (the fix recipes), 7 and 7a-7d and 7f (the prose
   gates), 7m (span form).
5. The frozen samples for catalog-form questions:
   <SKILL_DIR>/guidelines/reference/samples/page-encoding-pgtable-entries.md and
   <SKILL_DIR>/guidelines/reference/samples/page-overview-mm-struct.md — the LINUX
   KERNEL bullet display form they use is the house convention, not
   corruption (form only, never facts).

FACTS. Documented tree: <path>, version <tag>, commit <sha> (the disk is
ground truth for every byte-match precondition).
PROJECT-SPECIFIC BANS carried from the plan file: <list, or "none">.
[FIX LIST. <One numbered item per reviewed finding: the current text
(exact), the replacement (exact, or the 7q recipe to apply), and its
location by section heading. Span-form fixes name the exact link target
URL. Nothing else is in scope.>]

CONSTRAINTS.
- Fix ONLY lane-1 classes (or, in fix-list mode, only the listed items,
  exactly as briefed); escalate everything unsettled. Never fix
  substance: no excerpt additions or extensions, no coverage or parity
  closure, no fact, count, or claim edits. Fenced blocks stay
  byte-for-byte except the provenance line of a byte-proved drift fix.
- An item that cannot be applied exactly as briefed (text not found,
  ambiguous placement, needs a decision) is returned in the report with
  what you found; never improvise.
- Re-run the Gate A candidate greps over the paragraphs you touched
  (fence-aware) to confirm no new candidates.
- Anything you persist goes under <SKILL_DIR>/progress/<campaign>/ with a
  unique <slug>.-prefixed name; write nowhere else in progress/, which
  belongs to other runs too.

REPORT. Write the report to
<SKILL_DIR>/progress/<campaign>/<slug>.lint.md and summarize it as your
final message: FIXED by class with counts and before/after, ESCALATED
with proposed fixes, EXEMPT with the 7r ruling count applied, SUBSTANCE
NOTES, and confirmation that touched paragraphs re-grep clean and no
fenced block changed (beyond declared drift fixes).
```
