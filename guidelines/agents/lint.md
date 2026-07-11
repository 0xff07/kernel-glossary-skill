# Lint agent

Role: runs the lint pass (`guidelines/passes/03-lint.md`) on one finished page: mechanical checks, Gate A, the exhaustive 7m span pass, the 7o re-derivations, and the parity audit in flag-only mode. Fixes findings in place; never writes new sections; never changes scope.
Model tier: a different, cheaper model than the writer, in fresh context; the pass is mechanical-plus-checklist work a mid-tier model performs reliably when the brief is explicit (`guidelines/campaign/pipeline.md`).
Mandatory reading: carried inside the brief below, as absolute paths.
Report: written to the run's artifact directory (`progress/<campaign>/`) and summarized in the final message (format in the brief).
Death/resume: resume the same agent first; if repeated resumes fail, a fresh agent re-runs the pass from the page and the dossier (lint holds no research state worth salvaging beyond its report draft).

## Lint brief template

```
Lint the finished page <path> against the kernel tree at <tree path>,
version <tag>.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before touching the page:
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — first action. Judge
   every candidate against it BEFORE editing; a hit on an exempt
   construct is a false candidate, and rewording a compliant phrase to
   silence a pattern is itself a defect.
2. <SKILL_DIR>/guidelines/passes/03-lint.md — your procedure, steps 1
   through 6. Execute it in order.
3. <SKILL_DIR>/guidelines/gates/gate-a.md,
   <SKILL_DIR>/guidelines/gates/gate-b.md, and
   <SKILL_DIR>/guidelines/gates/mechanical-checks.md.
4. <SKILL_DIR>/guidelines/rules/INDEX.md, then the rule files it lists
   that the lint pass exercises: 7q (rephrase recipes), 7 and 7a-7d and
   7f (the prose gates), 7l, 7m, 7n, 7o (provenance, links, sources,
   claims).
5. <SKILL_DIR>/guidelines/reference/measured-criteria.md — the tripwires.
6. The page's dossier at <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md,
   if present: its recorded search bases seed your 7o re-derivations; a
   dossier entry is never evidence.

CONSTRAINTS.
- Fix confirmed findings in place and re-check after your own edits.
- Do not write missing sections; report every parity gap (Gate B item 1)
  as a coverage gap for a writer follow-up.
- Beyond the 7o corrections, do not change facts, scope, or structure.
- Any helper script or intermediate file you persist goes under
  <SKILL_DIR>/progress/<campaign>/ with a unique <slug>.-prefixed name
  (shared names have collided between concurrent lint agents); write
  nowhere else in progress/, which belongs to other runs too.

REPORT. Write the lint report to
<SKILL_DIR>/progress/<campaign>/<slug>.lint.md and summarize it as your
final message: findings fixed by class with counts, 7o corrections with
the search evidence, parity gaps, candidates adjudicated as exempt with
reasoning (state the 7r ruling count you applied as proof of the
registry read), and residual items you could not resolve.
```
