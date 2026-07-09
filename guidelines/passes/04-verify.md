# Pass 04: verify

Purpose: final sign-off. A page is done only when both gates hold with zero unadjudicated findings; reading the page is not sufficient, and evidence is recorded per item.
Inputs: the linted page, the lint report, the dossier (hints), and the kernel tree at the documented version.
Outputs: the recorded Gate A and Gate B outcomes in a verify report at `progress/<campaign-or-topic>/<page-slug>.verify.md`; in a campaign, the page's completion entry in the plan file's Status section.
Run by: single-agent mode inline (the same agent runs both gates itself); in a campaign the orchestrator (`guidelines/agents/verifier.md`), because final sign-off is never delegated.
Next: save per SKILL.md's save and commit policy.

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

## Procedure

1. Run Gate B in full (`guidelines/gates/gate-b.md`), performing the named action for each of the nine items and recording the evidence (a count or a list, not "looks fine").
2. Spot re-run the mechanical checks after lint (`guidelines/gates/mechanical-checks.md`) and the Gate A greps (`guidelines/gates/gate-a.md`); audit the lint report's exempt adjudications against the 7r registry (`guidelines/rules/7r-adjudications.md`).
3. Confirm the Gate B parity table has zero empty cells. In a campaign, dispatch a writer follow-up for any coverage gap lint flagged (lint does not write new sections), then re-verify the affected sections.
4. For a derived page, confirm every 7p cut was reported (and, in a campaign, recorded in the plan file) before the page can be marked done (`guidelines/rules/7p-derivation.md`).
5. Record the outcome of Gate A and Gate B before saving. If any item cannot be confirmed, the page is not done and is not written.
6. Residual findings are fixed or recorded as settled false-positive classes for future lint briefs; in a campaign they land in the plan file as LESSON entries and are folded into the 7r registry.
