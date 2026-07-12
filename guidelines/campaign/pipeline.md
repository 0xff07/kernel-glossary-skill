# Multi-page campaigns: dispatch, batching, and recovery

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

## Dispatch pipeline: writer, style lint, patch, verify

Campaign pages are produced by a four-stage pipeline with one ownership rule: substance is the writer's, end to end; prose and form are swept by fresh eyes. The split exists because a writer re-reading its own prose misses its own blind spots, while the disk-settleable checks (excerpts, anchors, counts, coverage) are mechanical procedures a writer runs reliably on its own work.

1. Writer (the strongest available model). Researches with semcode plus Grep/Read, writes the complete page following every rule under `guidelines/rules/` and `guidelines/diagrams/` while composing, and delivers the substance verified: the parity table closes at zero empty rows (fill-or-decatalog) and the mechanical exit suite (`guidelines/passes/02-write.md`) — excerpt byte-compare, anchor confirmation, catalog-coverage sweep, second-basis count re-derivation, cited-file recency — runs clean before the writer reports done, with the evidence in its report. The writer does not run the style sweeps on its own prose; its brief says so explicitly.
2. Style lint (a different, cheaper model, fresh context). Runs the Gate A candidate greps, the prose-shape read-throughs (7b list shapes, 7d superlatives in context, negative constructions, anthropomorphic verbs, heading shape), and the exhaustive 7m span-form pass, adjudicating every candidate against the 7r registry (`guidelines/rules/7r-adjudications.md`, mandatory first read). Find-only (`guidelines/passes/03-lint.md`): it proposes 7q-recipe fixes precisely enough to apply without judgment, never edits, never re-derives facts, never audits parity; suspected substance defects noticed in passing go to the verifier as SUBSTANCE NOTES. Concurrent agents use unique scratchpad filenames (shared names have collided).
3. Patch (the style-lint tier). Applies the orchestrator-reviewed stylistic fix list verbatim (`guidelines/agents/patcher.md`) and re-greps the touched paragraphs. It never touches substance; an item needing a decision comes back unapplied.
4. Final verify (the orchestrator). Runs Gate B in full against the writer's evidence: independent audit of the parity table against the page, spot re-runs of the exit suite (excerpts, anchors), review of the style-lint adjudications and the patch output, and the 7p cut check. Under this ownership split the verifier is the pipeline's only independent fact-check, so Gate B item 9 runs deep — the lead and SUMMARY quantifiers and the page's central counts are re-derived by the verifier itself, not sampled. Substance defects found here return to the writer as a resume; residual findings are fixed or recorded in the plan file as settled false-positive classes for future briefs.

Model-tier guidance, subsystem-independent: page writing needs the strongest model available (research judgment, prose discipline, figure quality); the style-lint and patch passes are pattern-plus-recipe work a mid-tier model performs reliably when the brief is explicit; the orchestrator keeps final sign-off and the independent fact-check, and never delegates either.

The writer runs the research pass itself by default (`guidelines/passes/01-research.md`), keeping the page dossier current as it researches; dispatching separate researcher agents (`guidelines/agents/researcher.md`) to pre-build dossiers is an explicit opt-in, never the assumed shape.

The dispatch brief templates and role cards are under `guidelines/agents/`: `writer.md`, `lint.md`, `patcher.md`, and `verifier.md` for this pipeline; `inventory.md` and `plan-reviewer.md` for planning; `researcher.md` for the opt-in research fan-out.

## Follow-up dispatch: substance to the writer, style to the patcher

Anything found after the writer reports done goes to one of two channels, chosen by kind, not by convenience:

- Stylistic (the style-lint findings the orchestrator confirms, plus any prose or form defect verify itself catches): a fresh patch agent applies the reviewed fix list. Resuming a writer for rewordings re-loads its whole transcript on every call — measured an order of magnitude more expensive than the edits themselves — and rewording is not writer work anyway.
- Substantive (a parity hole, a missing/drifted/wrongly-anchored excerpt, a false count or claim, anything touching scope or boundary rules): resume the original writer ("do not redo the research; work from what you have"). Substance is writer-owned end to end and the patcher is forbidden from it by role; a substantive follow-up is also a signal the writer's exit suite was skipped or shallow, worth naming in the plan file. If repeated resumes fail, a fresh writer starts from the dossier, the parity table, and the plan file.

Either channel's output is re-verified by the orchestrator before the page is marked done.

## Batch generation and interruption recovery

- Generate about five pages per batch: one writer agent per page, dispatched together, then a hard checkpoint before the next batch launches. Five keeps what a session rate limit or API outage can kill at once down to a recoverable set (each dead writer resumes from its transcript) while still parallelizing the writing. Do not launch the whole catalog in parallel. Lint agents may trail into the following batch.
- When a writer or lint agent dies mid-page, resume that same agent with a message; its research context survives in its transcript. Say explicitly "do not redo the research; write the page now from what you have". If repeated resumes fail, hand the remainder to a fresh agent started from the page dossier (`progress/<campaign>/<slug>.dossier.md`) plus the plan file Status.
- After every completed page, update the plan file (status, page statistics, adjudications, lessons) so a future session resumes from the plan file plus the on-disk pages alone.
- Pages land only under `docs/<dir>/`, per the save and commit policy in SKILL.md (no navigation-file edits, and no git commits without an explicit user go).
- When using parallel sub-agents (Agent tool), ensure they have Write permissions before spawning. If Write is unavailable to agents, fall back to sequential processing immediately rather than failing and retrying.
