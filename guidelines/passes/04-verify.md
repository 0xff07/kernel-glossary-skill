# Pass 04: verify (one page)

Purpose: the independent per-page fact-check. A page is certified only when both gates hold with zero unadjudicated findings; reading the page is not sufficient, and evidence is recorded per item. This pass defines the unit of verification work; when it runs and who runs it is mode-dependent.
Inputs: the page after lint-fix; the kernel tree at the documented version (ground truth); as hints when available — the parity table, the dossier (including its EVIDENCE section), and the fixer report. A foreign corpus arrives with none of these: regenerate the check inventory from the page itself (pages are self-contained by design).
Outputs: a verify report recording the Gate A and Gate B outcomes — solo: `progress/<campaign>/<page-slug>.verify.md`; in a verify campaign: `progress/<verify-run>/<page-slug>.verify.md` plus the CERTIFIED entry the orchestrator stamps into Status.
Run by: single-agent mode inline, immediately after pass 03 (the same agent runs both gates itself and fixes what it finds). In a campaign this pass is deferred: it runs inside a verify campaign (the section below) per the cadence the user chose at the campaign checkpoint, executed by dispatched find-only verifier agents (briefs at the end of this file) — adjudication and sign-off stay with the verify campaign's orchestrator and are never delegated.
Next: save per SKILL.md's save and commit policy (solo); the verify campaign's adjudication and fix loop (campaign).

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

## Procedure (per page)

1. Run Gate B in full (`guidelines/rules/3b-gate-b.md`), performing the named action for each of the nine items and recording the evidence (a count or a list, not "looks fine"). This pass is the pipeline's only independent fact-check: run item 9 deep — re-derive the lead and SUMMARY quantifiers and the page's central counts yourself, with a search basis shaped differently from any basis recorded in the dossier's EVIDENCE section — and audit the parity table independently against the page (item 1); the table and the dossier are hints, never evidence.
2. Spot re-run the writer's mechanical exit suite (excerpt byte-compares and anchor confirmations per `guidelines/rules/3c-mechanical-checks.md`) and the Gate A greps (`guidelines/rules/3a-gate-a.md`); audit the fixer report's adjudications against the 7r registry (`guidelines/rules/7r-adjudications.md`) and its applied diffs (declared drift fixes must satisfy the byte-match precondition; no other fenced-block change is legitimate).
3. For a derived page, confirm every 7p cut was reported (and, in a campaign, recorded in the plan file) before the page can be certified (`guidelines/rules/7p-derivation.md`).
4. Findings. Solo: fix and re-check now — the solo agent is the writer, so the facts are in its hands. Verify campaign: record every finding in the report, find-only; the orchestrator adjudicates and routes (settled style and byte-proved drift to a fixer in fix-list mode per `guidelines/passes/03-lint.md`; every factual finding into the delta catalog — a verify campaign never edits facts), then any fixer-touched units are re-checked.
5. Record the outcome of Gate A and Gate B. Zero unadjudicated findings certifies the page (Status state CERTIFIED, dossier HEADER status `certified` where a dossier exists); any unconfirmable item leaves it uncertified — solo, the page is not written.
6. Residual false-positive classes are recorded as LESSON entries in the governing plan file and folded into the 7r registry for future briefs.

## The verify campaign

Verification at campaign scale is its own campaign, not a stage of the write campaign. It reuses the campaign skeleton unchanged — a plan file under `progress/` as the durable memory, an orchestrator that curates that plan itself, batched sub-agents, a living Status section, resumability from the plan file plus the disk — so writing and verifying can happen in different sessions, on different machines, or by different people. Its work unit is the per-page procedure above; this section adds the orchestration around it and the checks no single page can carry.

When a verify campaign runs:

- Per the cadence the user chose at the write campaign's checkpoint (`guidelines/passes/plan.md`, step 8) and recorded in the write plan's Scope decisions: typical answers are after the first batch (calibration — a systematic writer error caught on five pages instead of seventy), at campaign end (certification), both, or only on demand.
- Standalone, on any corpus, whenever the user asks ("verify docs/<dir>", "verify the drm campaign"): the corpus needs no parent campaign, no artifacts, and no prior contact with this checkout — pages are self-contained by design, and the plan below regenerates every check inventory from the pages themselves when no dossier exists.

Workspace and the parent carve-out: a verify campaign is its own run under `progress/` (naming and isolation: SKILL.md, "The progress/ workspace"): plan file `progress/<parent>-verify.md` and artifact directory `progress/<parent>-verify/` when it verifies a write campaign, any unique `-verify`-suffixed name for a standalone corpus. Its plan file's Context declares the parent campaign (or "standalone"); the user's request to verify licenses reading the parent's plan file and artifact directory as hints — the one exception to the read-nothing isolation rule. The parent's entries are never modified; the only cross-write is the orchestrator mirroring CERTIFIED stamps into the parent plan file's Status. Plan files — the verify plan like any other — are committable (the `progress/` gitignore excepts every top-level plan file), and the plan alone is what needs to travel: its Status carries the certification census and its delta catalog the findings; the artifact directory's per-page reports are local scratch. Committing a plan still requires the user's explicit go like any commit.

Planning is orchestrator-owned — the same rule as catalog design in `guidelines/passes/plan.md`; the orchestrator may dispatch read-only agents to collect per-page inventories for a large corpus, but every routing and batching decision is its own. The verify plan file carries:

1. Context: the corpus (page list with absolute paths), the parent campaign or "standalone", and the documented tree with version tag and commit pin — re-derived and confirmed against the corpus's own version claims before anything runs (a verifier on the wrong tree produces confident nonsense), plus the semcode index state.
2. Status: the living, dated log — batches dispatched, findings adjudicated, fixes applied, pages certified; a later session resumes from here. The per-finding ticker accumulates in a status journal in the verify run's artifact directory (`<verify-run>.journal.md`) and is folded in at verify batch checkpoints, so the committable verify plan stays clean between them.
3. Page table: one row per page — its state, and its check inventory (catalog symbol count, fenced-block count, link count, the counts/universal-claims list, and the expected symbol population for the coverage-of-scope tripwire: the catalog row's anchor symbols plus the dossier's SYMBOLS section when present, `guidelines/reference/measured-criteria.md`) with the inventory's source noted: the dossier EVIDENCE section when the parent's artifacts exist, regenerated from the page when they do not.
4. Cross-page checklist: from the parent plan's boundary rules and fold-in list when there is one; for a standalone corpus, derived by the orchestrator from the pages' own seam recaps. This is the check class per-page verification cannot see: seam consistency, fold-in landing, catalog coverage.
5. Fix routing: the only edits a verify campaign makes are registry-settled style fixes and byte-proved drift corrections, applied by a fixer in fix-list mode (`guidelines/passes/03-lint.md`) and re-checked. Every factual finding — a parity hole, a false count, a drifted excerpt needing re-collection, a wrong model, a scope breach — is recorded in the delta catalog instead, and the page stays uncertified; facts are repaired only by a follow-up delta write campaign, never in place and never by resuming a writer transcript.
6. Batch order: about five pages per batch, the cross-page unit after the per-page rows it depends on.
7. Delta catalog: the campaign's factual output, appended as findings are adjudicated and closed out at campaign end. One row per uncertified page: the page path, each confirmed finding with the verifier's evidence and (where derivable) the exact fix specification, plus — copied in so the catalog is self-contained — that page's boundary statements, the project-specific bans, and the tree pin from the parent plan (so the catalog stands alone even on a checkout that never committed or never held the parent plan). It seeds a follow-up delta write campaign (`guidelines/passes/plan.md`, "Delta write campaigns").

Execution:

- Dispatch find-only verifier agents per the plan — one per page and one cross-page agent, briefs below — about five per batch, with the same death/resume rules as every campaign agent (resume the same agent and ask for findings so far; fresh only after two failed resumes).
- The orchestrator adjudicates every reported finding itself: style classes against the 7r registry, facts against the disk. It never delegates adjudication or the certification stamp.
- Accepted findings route per the plan's fix-routing section; a fixer's output is re-checked (the orchestrator re-runs the touched units, or re-dispatches a verifier for them) before the page's state changes.
- A page with zero unadjudicated findings is stamped CERTIFIED in the verify plan's Status (mirrored to the parent plan's Status when one exists; the dossier HEADER status becomes `certified` where a dossier exists).
- The campaign is complete when every corpus page is CERTIFIED, deferred with its delta recorded (its findings in the delta catalog), or explicitly waived by the user. The delta catalog then seeds a follow-up delta write campaign, and the next verify campaign over the same parent scopes to the still-uncertified pages by default, so the write → verify → delta → verify loop shrinks every round. Residual false-positive classes become LESSON entries and are folded into the 7r registry.

## Dispatching verifier agents (verify-campaign briefs)

Role: executes this pass find-only on one page (or the cross-page checklist on a corpus). Model tier: strong; claim re-derivation and parity auditing are judgment over facts. On death, resume the same agent and ask for the findings recorded so far; spawn fresh only after resuming fails twice. Adjudication, fix routing, and the CERTIFIED stamp belong to the verify campaign's orchestrator, never to this agent.

Per-page verifier brief:

```
Verify the page <path> against the tree, find-only; do not edit anything.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order:
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — every style
   candidate and every fixer-report audit is judged against it.
2. <SKILL_DIR>/guidelines/passes/04-verify.md — your procedure (steps
   1-3; you record findings, you do not fix or route them).
3. <SKILL_DIR>/guidelines/rules/3b-gate-b.md, <SKILL_DIR>/guidelines/rules/3a-gate-a.md,
   and <SKILL_DIR>/guidelines/rules/3c-mechanical-checks.md — the items and
   the by-hand procedures.
4. <SKILL_DIR>/guidelines/reference/measured-criteria.md — the depth
   tripwires.

FACTS. Documented tree: <path>, version <tag>, commit <sha>; the on-disk
tree is ground truth. Hints if present (never evidence): dossier at
<path or "none">, parity table at <path or "none">, fixer report at
<path or "none">. Re-derive counts with bases shaped differently from
any recorded in the dossier EVIDENCE section.
PROJECT-SPECIFIC BANS from the parent plan file: <list, or "none">.

REPORT. Write per-item evidence and the findings list (each finding:
gate item, class, location, exact text, what the tree shows) to
<SKILL_DIR>/progress/<verify-run>/<slug>.verify.md. Your final message
is the summary: items passed with their evidence counts, findings by
class and severity, and the 7r ruling count you applied.
```

Cross-page verifier brief (one per verify campaign, after the per-page rows):

```
Verify cross-page consistency over the corpus below, find-only.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>
CORPUS: <the page list, absolute paths>
FACTS. Documented tree: <path>, version <tag>, commit <sha>.

CHECKS, from the verify plan at <plan path>:
1. Seam consistency: for each boundary statement and seam symbol listed
   in the plan, confirm every sibling page states the seam identically
   (same symbol, same file:line, same one-line role) and that no page
   re-walks a mechanism the boundary deeds to a sibling beyond one short
   recap paragraph.
2. Fold-in landing: every absorbed topic in the plan's fold-in list
   appears in its absorbing page.
3. Catalog coverage: every catalog row's output path exists on disk;
   no orphan page exists outside the catalog.
4. <Any campaign-specific cross-page claims from the plan.>

REPORT. Write findings (each: check, pages involved, exact texts, what
disagrees) to <SKILL_DIR>/progress/<verify-run>/cross-page.verify.md.
Your final message is the summary by check with counts.
```
