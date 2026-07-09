# Verifier (orchestrator role)

Role: runs the verify pass (`guidelines/passes/04-verify.md`) as final sign-off on each page. In a campaign this is the orchestrator: it keeps final sign-off and never delegates it. It audits the lint report's exempt adjudications against the 7r registry, spot re-runs the mechanical checks and the Gate A greps, confirms the Gate B parity table has zero empty cells, dispatches writer follow-ups for the coverage gaps lint flagged (lint does not write new sections), confirms any 7p cuts were reported, and records the outcome: the verify report under `progress/`, and the page's completion entry in the plan file's Status section.

In single-agent mode the same agent that wrote and linted the page runs this pass itself. In both modes a page is final only at zero unadjudicated findings.

Reading list:

1. `guidelines/passes/04-verify.md` (the procedure)
2. `guidelines/gates/gate-b.md` (run in full) and `guidelines/gates/gate-a.md` with `guidelines/gates/mechanical-checks.md` (spot re-runs)
3. `guidelines/rules/7r-adjudications.md` (the registry the adjudication audit runs against)
4. `guidelines/rules/7p-derivation.md` (when the page derives from existing material)
5. `guidelines/reference/measured-criteria.md` (the tripwires)
