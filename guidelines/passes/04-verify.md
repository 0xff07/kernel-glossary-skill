# Pass 04: verify (one page)

Purpose: the independent per-page fact-check. A page is certified only when both gates hold with zero unadjudicated findings; reading the page is not sufficient, and evidence is recorded per item. This pass defines the unit of verification work; when it runs and who runs it is mode-dependent.
Inputs: the page after lint-fix; the kernel tree at the documented version (ground truth); and, as hints when they exist, the dossier's PARITY, EVIDENCE and LINT sections. A foreign corpus arrives with no dossier: regenerate the check inventory from the page itself (pages are self-contained by design).
Outputs: the dossier's VERIFY section, recording the Gate A and Gate B outcomes with their evidence, plus the CERTIFIED entry the orchestrator stamps into the verify run's log. No report file (a durable, committed certification record exists only on an explicit user go).
Run by: a verify campaign (the section below), executed by dispatched find-only verifier agents; adjudication and sign-off stay with its orchestrator and are never delegated.

WHEN it runs, and why NOT in the writing session. The writer verifies its own work mechanically and the orchestrator reproduces those checks (`guidelines/passes/03-check.md`), so a verify campaign run immediately afterwards, in the same session, on the same tree, under the same model, buys almost nothing: its errors are CORRELATED with the ones already made, and it re-derives the same facts with the same blind spots. Its value comes from breaking exactly that correlation, so run it when at least one of these is true:

- The TREE HAS MOVED. The pages document a pinned version; the kernel does not stand still. A verify campaign against a newer tree is how version drift is found — a renamed symbol, a moved line, a changed count — and it is the main reason the pass exists.
- A DIFFERENT MODEL can audit. A page checked by the model family that wrote it inherits that family's blind spots. An independent auditor is one that does not share them.
- The corpus is FOREIGN. Pages written elsewhere, with no dossiers and no prior contact with this checkout, need their check inventory regenerated from the pages themselves — which is what this pass does.
Next: save per SKILL.md's save and commit policy (solo); the verify campaign's adjudication and fix loop (campaign).

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Procedure (per page)

1. Run Gate B in full (`guidelines/rules/rules.md` (3b)), performing the named action for each of the nine items and recording the evidence (a count or a list, not "looks fine"). This pass is the pipeline's only independent fact-check: run item 9 deep — re-derive the lead and SUMMARY quantifiers and the page's central counts yourself, with a search basis shaped differently from any basis recorded in the dossier's EVIDENCE section — and audit the dossier's PARITY table independently against the page (item 1); the table and the dossier are hints, never evidence.
2. Spot re-run the writer's mechanical exit suite (excerpt byte-compares and anchor confirmations per `guidelines/rules/rules.md` (3c)) and the Gate A greps (`guidelines/rules/rules.md` (3a)); audit the dossier's LINT section — its adjudications against the 7r registry (`guidelines/rules/7r-adjudications.md`), and its applied diffs (declared drift fixes must satisfy the byte-match precondition; no other fenced-block change is legitimate).
3. For a derived page, confirm every 7p cut was reported (and, in a campaign, recorded in the campaign spec) before the page can be certified (`guidelines/rules/rules.md` (7p)).
4. Findings. Solo: fix and re-check now — the solo agent is the writer, so the facts are in its hands. Verify campaign: record every finding in the dossier's VERIFY section, find-only; the orchestrator adjudicates and routes (settled style and byte-proved drift to a fixer in fix-list mode per `guidelines/passes/03-lint-fixlist.md`; every factual finding into the verify run's log and the user-facing report — a verify campaign never edits facts), then any fixer-touched units are re-checked.
5. Record the outcome of Gate A and Gate B in the dossier's VERIFY section. Zero unadjudicated findings certifies the page (state CERTIFIED in the verify run's log); any unconfirmable item leaves it uncertified — solo, the page is not written.
6. Residual false-positive classes are recorded as LESSON entries in the verify run's log and surfaced to the user, who alone folds a ruling into the 7r registry.

## The verify campaign

Verification at campaign scale is a CAMPAIGN LIKE ANY OTHER — same spec-plus-workspace shape, same structure, same slicing, same resumability (`guidelines/passes/plan.md`). The only difference is what its catalog lists: pages to CERTIFY, rather than pages to write. There is no separate plan format, no certification census, and no delta catalog; the campaign spec's page table IS the census, and the confirmed factual findings it surfaces ARE the catalog of the follow-up write campaign that repairs them.

When a verify campaign runs:

- Per the cadence the user chose at the write campaign's checkpoint (`guidelines/passes/plan.md`, step 8) and recorded in its Scope decisions: typical answers are after the first batch (calibration — a systematic writer error caught on five pages instead of seventy), at campaign end (certification), both, or only on demand.
- Standalone, on any corpus, whenever the user asks ("verify docs/<dir>", "verify the drm campaign"): the corpus needs no parent campaign, no dossiers, and no prior contact with this checkout — pages are self-contained by design, and the orchestrator regenerates each check inventory from the pages themselves when no dossier exists.

Workspace and the parent carve-out: a verify campaign is its own campaign, named `<parent>-verify`, with the same artifacts as any campaign — a spec at `campaigns/<parent>-verify.md` (committable like any spec; for an ad-hoc "verify docs/<dir>" request it may be short) and a workspace `progress/<parent>-verify/`. Its Context declares the parent (or "standalone"); the parent's spec is readable like every spec, and the user's request to verify additionally licenses reading this machine's parent dossiers as hints — never as evidence. The parent's spec and workspace are not modified, and there is NO cross-write: certification lands in the verify run's own log, and a durable certification record — a committed verify report, or a dated certification amendment in the parent spec — exists only on an explicit user go.

Planning is orchestrator-owned — the same rule as catalog design. The verify campaign spec carries the standard sections, with these specializations:

1. Context: the corpus (page list, skill-relative paths — the spec stays machine-portable), the parent campaign or "standalone", and the documented tree with version tag and commit pin — re-derived and confirmed against the corpus's own version claims before anything runs, because a verifier on the wrong tree produces confident nonsense.
2. Catalog: one row per page — its state, and its check inventory (catalog symbol count, fenced-block count, link count, the counts and universal claims to re-derive, and the expected symbol population for the coverage-of-scope tripwire: the parent catalog row's anchor symbols plus the dossier's SYMBOLS section when one exists, `guidelines/reference/measured-criteria.md`). Note each inventory's source: the dossier when the parent's artifacts exist, regenerated from the page when they do not.
3. Cross-page checklist: from the parent's boundary rules and fold-in list when there is one; for a standalone corpus, derived by the orchestrator from the pages' own seam recaps. This is the check class per-page verification cannot see — seam consistency, fold-in landing, catalog coverage.
4. Run log (in the workspace, never in the spec): the living machine-local record — slices dispatched, findings adjudicated, fixes applied, pages CERTIFIED, and every confirmed factual finding with its evidence and (where derivable) its exact fix specification. A later session on this machine resumes from here; the findings, surfaced to the user, are what seed the repair campaign.

Execution:

- Dispatch find-only verifier agents per the catalog — one per page and one cross-page agent, briefs below — about five per batch, with the same death and resume rules as every campaign agent.
- The orchestrator adjudicates every reported finding itself: style classes against the 7r registry, facts against the disk. It never delegates adjudication or the certification stamp.
- The only in-place edits are registry-settled style fixes and byte-proved drift corrections, applied by a fixer in fix-list mode (`guidelines/passes/03-lint-fixlist.md`) and re-checked before any page's state changes. Every FACTUAL finding — a parity hole, a false count, a drifted excerpt, a wrong model, a scope breach — is recorded in the run log, surfaced to the user, and the page stays uncertified; facts are repaired only by a follow-up write campaign whose catalog is those findings, never in place and never by resuming a writer transcript.
- A page with zero unadjudicated findings is stamped CERTIFIED in the run log; a durable certification record (committed verify report, or a dated certification amendment in the parent spec) is produced only on an explicit user go.
- The campaign is complete when every page is CERTIFIED, deferred with its findings recorded, or explicitly waived by the user. Those findings become the next write campaign's catalog, and the next verify campaign scopes to the still-uncertified pages by default, so the write → verify → repair → verify loop shrinks every round.

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
3. <SKILL_DIR>/guidelines/rules/rules.md — the writing rules and the
   gates in one file: Gate B's nine items (3b), Gate A's greps (3a), and
   the by-hand check procedures both gates use (3c).
4. <SKILL_DIR>/guidelines/reference/measured-criteria.md — the depth
   tripwires.

FACTS. Documented tree: <path>, version <tag>, commit <sha>; the on-disk
tree is ground truth. Hints if present, never evidence: the page's
dossier at <path or "none">, whose PARITY, EVIDENCE and LINT sections
record what earlier passes found. Re-derive every count with a basis
shaped differently from any recorded in EVIDENCE.
PROJECT-SPECIFIC BANS from the parent campaign spec: <list, or "none">.

REPORT. Write per-item evidence and the findings list (each finding:
gate item, class, location, exact text, what the tree shows) into the
VERIFY section of <SKILL_DIR>/progress/<verify-run>/<slug>.dossier.md.
Your final message is the summary: items passed with their evidence
counts, findings by class and severity, and the 7r ruling count you
applied.
```

Cross-page verifier brief (one per verify campaign, after the per-page rows):

```
Verify cross-page consistency over the corpus below, find-only.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>
CORPUS: <the page list, absolute paths>
FACTS. Documented tree: <path>, version <tag>, commit <sha>.

CHECKS, from the verify campaign spec at <path>:
1. Seam consistency: for each boundary statement and seam symbol listed
   in the campaign spec, confirm every sibling page states the seam identically
   (same symbol, same file:line, same one-line role) and that no page
   re-walks a mechanism the boundary deeds to a sibling beyond one short
   recap paragraph.
2. Fold-in landing: every absorbed topic in the fold-in list
   appears in its absorbing page.
3. Catalog coverage: every catalog row's output path exists on disk;
   no orphan page exists outside the catalog.
4. <Any campaign-specific cross-page claims from the campaign spec.>

REPORT. Write findings (each: check, pages involved, exact texts, what
disagrees) into the VERIFY section of
<SKILL_DIR>/progress/<verify-run>/cross-page.dossier.md. Your final
message is the summary by check with counts.
```
