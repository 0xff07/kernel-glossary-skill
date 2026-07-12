# Style-lint agent

Role: runs the style-lint pass (`guidelines/passes/03-lint.md`) on one finished page: the Gate A candidate greps, the prose-shape read-throughs, and the exhaustive 7m span-form pass, every candidate adjudicated against the 7r registry. Find-only — it proposes fixes (7q recipes, stated precisely enough to apply without judgment) but never edits the page, never re-derives facts, never audits parity, and never touches excerpts or anchors; substance is the writer's to deliver and the verifier's to audit. Its confirmed-finding list is reviewed by the orchestrator and applied by a patch agent (`guidelines/agents/patcher.md`).
Model tier: a different, cheaper model than the writer, in fresh context; the pass is pattern-plus-judgment work over prose, and fresh eyes are the point.
Mandatory reading: carried inside the brief below, as absolute paths.
Report: written to the run's artifact directory (`progress/<campaign>/`) and summarized in the final message (format in the brief).
Death/resume: resume the same agent first; if repeated resumes fail, a fresh agent re-runs the pass from the page (the pass holds no research state worth salvaging beyond its report draft).

## Style-lint brief template

```
Style-lint the finished page <path>. Find and adjudicate; do not edit.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before touching the page:
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — first action. Judge
   every candidate against it BEFORE proposing a fix; a hit on an exempt
   construct is a false candidate, and proposing to reword a compliant
   phrase to silence a pattern is itself a defect.
2. <SKILL_DIR>/guidelines/passes/03-lint.md — your procedure, steps 1
   through 5. Execute it in order.
3. <SKILL_DIR>/guidelines/gates/gate-a.md and the candidate greps in
   <SKILL_DIR>/guidelines/gates/mechanical-checks.md (item 3).
4. <SKILL_DIR>/guidelines/rules/INDEX.md, then the rule files this pass
   exercises: 7q (rephrase recipes), 7 and 7a-7d and 7f (the prose
   gates), 7m (span form).
5. The frozen samples for catalog-form questions:
   <SKILL_DIR>/guidelines/samples/page-encoding-pgtable-entries.md and
   <SKILL_DIR>/guidelines/samples/page-overview-mm-struct.md — the LINUX
   KERNEL bullet display form they use is the house convention, not
   corruption (form only, never facts).

PROJECT-SPECIFIC BANS carried from the plan file: <list, or "none">.

CONSTRAINTS.
- Find-only: do not modify the page, do not re-derive counts or claims,
  do not audit parity, do not byte-check excerpts or anchor targets
  (passes 02 and 04 own those). A suspected substance defect noticed in
  passing goes in a SUBSTANCE NOTES section for the verifier; do not act
  on it.
- Every confirmed finding carries the exact current text, its location by
  section heading, and a fix stated precisely enough to apply without
  judgment; every exempt candidate carries the ruling applied.
- Anything you persist goes under <SKILL_DIR>/progress/<campaign>/ with a
  unique <slug>.-prefixed name (shared names have collided between
  concurrent agents); write nowhere else in progress/, which belongs to
  other runs too.

REPORT. Write the finding list to
<SKILL_DIR>/progress/<campaign>/<slug>.lint.md and summarize it as your
final message: confirmed findings by class with counts and proposed
fixes, candidates adjudicated exempt with reasoning (state the 7r ruling
count you applied as proof of the registry read), and any SUBSTANCE
NOTES for the verifier.
```
