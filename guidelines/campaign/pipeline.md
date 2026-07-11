# Multi-page campaigns: dispatch, batching, and recovery

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

## Dispatch pipeline: writer, lint, verify

Campaign pages are produced by a three-stage pipeline. The separation exists because a writer re-reading its own page misses its own blind spots; an independent pass with fresh context reliably catches wrong anchors, drifted excerpts, and skipped spans the writer cannot see.

1. Writer (the strongest available model). Researches with semcode plus Grep/Read, confirms every fact on disk, and writes the complete page following every rule under `guidelines/rules/` and `guidelines/diagrams/` while composing. The writer does not run the Gate A/B loops after writing; its brief says so explicitly, because self-lint spends the strongest model's budget on work the next stage redoes better.
2. Lint (a different, cheaper model, fresh context). Runs the mechanical checks by hand (`guidelines/gates/mechanical-checks.md`: link targets, excerpt verbatimness, Gate A candidate greps, judging every hit against the 7r registry (`guidelines/rules/7r-adjudications.md`) named as mandatory reading in its brief); performs the read-through sweeps (boldface, 7b prose-list shapes, 7d superlatives judged in context, negative constructions, anthropomorphic verbs); re-derives the page's counts, universal claims, and restated conditions per 7o; and executes the exhaustive 7m span-linking pass. Fixes everything in place, re-checks after its own edits, and reports what changed plus every candidate it adjudicated as exempt, with reasoning. Concurrent lint agents use unique scratchpad filenames for any helper scripts they improvise (shared names have collided).
3. Final verify (the orchestrator). Spot re-runs the mechanical checks after lint, audits the adjudications against the 7r registry, confirms the Gate B parity table (`guidelines/gates/gate-b.md`, item 1) has zero empty cells (dispatching a writer follow-up for any coverage gap lint flagged, since lint does not write new sections), and confirms any 7p cuts were reported before marking the page done in the plan file. Residual findings are fixed or recorded in the plan file as settled false-positive classes for future lint briefs.

Model-tier guidance, subsystem-independent: page writing needs the strongest model available (research judgment, prose discipline, figure quality); the lint pass is mechanical-plus-checklist work a mid-tier model performs reliably when the brief is explicit and exhaustive; the orchestrator keeps final sign-off and never delegates it.

The writer runs the research pass itself by default (`guidelines/passes/01-research.md`), keeping the page dossier current as it researches; dispatching separate researcher agents (`guidelines/agents/researcher.md`) to pre-build dossiers is an explicit opt-in, never the assumed shape.

The dispatch brief templates and role cards are under `guidelines/agents/`: `writer.md`, `lint.md`, and `verifier.md` for this pipeline; `inventory.md` and `plan-reviewer.md` for planning; `researcher.md` for the opt-in research fan-out.

## Batch generation and interruption recovery

- Generate about five pages per batch: one writer agent per page, dispatched together, then a hard checkpoint before the next batch launches. Five keeps what a session rate limit or API outage can kill at once down to a recoverable set (each dead writer resumes from its transcript) while still parallelizing the writing. Do not launch the whole catalog in parallel. Lint agents may trail into the following batch.
- When a writer or lint agent dies mid-page, resume that same agent with a message; its research context survives in its transcript. Say explicitly "do not redo the research; write the page now from what you have". If repeated resumes fail, hand the remainder to a fresh agent started from the page dossier (`progress/<campaign>/<slug>.dossier.md`) plus the plan file Status.
- After every completed page, update the plan file (status, page statistics, adjudications, lessons) so a future session resumes from the plan file plus the on-disk pages alone.
- Pages land only under `docs/<dir>/`, per the save and commit policy in SKILL.md (no navigation-file edits, and no git commits without an explicit user go).
- When using parallel sub-agents (Agent tool), ensure they have Write permissions before spawning. If Write is unavailable to agents, fall back to sequential processing immediately rather than failing and retrying.
