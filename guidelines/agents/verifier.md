# Verifier (orchestrator role)

Role: runs the verify pass (`guidelines/passes/04-verify.md`) as final sign-off on each page. In a campaign this is the orchestrator: it keeps final sign-off and never delegates it. Under the substance-ownership split it is also the pipeline's only independent fact-check: it audits the writer's evidence (the parity table against the page, spot re-runs of the exit suite's excerpt and anchor checks) and re-derives the page's central counts and lead/SUMMARY quantifiers itself (Gate B item 9, run deep, never sampled). It reviews the style-lint finding list against the 7r registry, confirms the patch agent applied exactly the reviewed list, dispatches follow-ups per the pipeline rule (`guidelines/campaign/pipeline.md`: substance defects return to the writer as a resume; confirmed stylistic fixes go to a patch agent), confirms any 7p cuts were reported, and records the outcome: the verify report in the campaign's artifact directory (`progress/<campaign>/`), and the page's completion entry in the plan file's Status section.

In single-agent mode the same agent that wrote and linted the page runs this pass itself. In both modes a page is final only at zero unadjudicated findings.

Reading list:

1. `guidelines/passes/04-verify.md` (the procedure)
2. `guidelines/gates/gate-b.md` (run in full) and `guidelines/gates/gate-a.md` with `guidelines/gates/mechanical-checks.md` (spot re-runs)
3. `guidelines/rules/7r-adjudications.md` (the registry the adjudication audit runs against)
4. `guidelines/rules/7p-derivation.md` (when the page derives from existing material)
5. `guidelines/reference/measured-criteria.md` (the tripwires)
