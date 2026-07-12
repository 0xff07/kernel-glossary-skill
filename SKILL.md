---
name: kernel-glossary-skill
description: >
  Generate structured Linux kernel reports for this knowledge base.
user-invocable: true
---

# kernel-glossary-skill

Generate a Linux kernel reports following this project's conventions.

## Project Overview

This is a documentation knowledge base covering Linux kernel subsystems, hardware architecture, and driver development. It is built with MkDocs (Material theme) and consists of Markdown articles organized by subsystem.

Content structure:

- `docs/` — all documentation articles
- `guidelines/reference/TEMPLATE-FULL.md` — full page template with all sections
- `guidelines/reference/samples/` — the reference samples for writing and planning. This directory holds frozen copies of exemplar pages, one labelled counterexample, and the campaign plan file that produced the exemplars, kept independent of the live subsystem directories, outside `docs/`, so they stay findable even after the hierarchy under `docs/` is reorganized. The worked examples here define the house standard for the lead summary, section structure, prose, ASCII diagrams, self-contained kernel-source citation, depth of coverage, and campaign planning. Samples are style, structure, and depth guidance ONLY; they are never an authoritative source of kernel knowledge. Each documents its own tree at its own version and can carry errors found later, so no technical claim, line number, or excerpt is ever taken from a sample into new work; every fact is researched against the documented tree (7e, 7o). When writing any new page or plan, calibrate against the closest-matching file under `guidelines/reference/samples/`, and refer to example files only by their `guidelines/reference/samples/` path.
- Major subsystem directories under `docs/`: one per entry in the Subsystem Map (`guidelines/reference/subsystems.md`; the `dir` field of each entry)

## Input

`$ARGUMENTS` or conversation context provides:
- The subsystem (e.g., xHCI, PCIe, ACPI, USB4, DRM)
- The topic name (e.g., "host controller initialization", "MSI-X vectors")
- The documented kernel version (e.g., `v7.0`): the tag of the local tree the pages cite
- Optionally, an output directory override

If `$ARGUMENTS` is empty, derive the subsystem and topic from the conversation context.

The documented kernel version is a single value set once and used everywhere: every Elixir URL embeds it, every version-specific claim is checked at it, the mechanical checks run against the tree checked out at it, and a campaign pins it (tag plus commit) in the plan file's Context section. When the version is not given, derive it from the local tree (`git describe --tags` or `make -s kernelversion` at the tree root), confirm elixir.bootlin.com carries that tag, and state the value back to the user before generating. All version-bearing examples in this skill use `v7.0`; substitute the documented version.

## Skill layout

Everything in this skill lives in one of three top-level directories beside this file:

- `docs/` — the knowledge base itself: the generated articles, organized by subsystem.
- `guidelines/` — all doctrine, split by concern:
  - `guidelines/passes/` — the pipeline, one file per stage (plan, 00-04), each carrying both the procedure and (where a campaign dispatches that stage to a sub-agent) the dispatch brief, plus the dossier spec
  - `guidelines/rules/` — every stable-ID criterion file: the gates (3a Gate A, 3b Gate B, 3c the by-hand mechanical checks) and the writing rules (7, 7a-7r, including the diagram rules 7g-7i); `INDEX.md` maps every ID
  - `guidelines/reference/` — the Subsystem Map (`subsystems.md`, one entry per subsystem), the measured criteria, the draft-versus-page contrast, the page template (`TEMPLATE-FULL.md`), and the frozen samples with the exemplar campaign plan file (`guidelines/reference/samples/`)
- `progress/` — per-run workspaces ("The progress/ workspace" below). Progress artifacts are hints and evidence trails; the on-disk kernel tree at the documented version is always ground truth.

All relative paths in this skill resolve against this file's directory, available to the top-level agent as `${CLAUDE_SKILL_DIR}`. Sub-agent briefs carry the absolute skill path instead (a `SKILL_DIR` bracket in every brief template), because sub-agents do not inherit that variable.

Rule IDs (3a-3c, 7, 7a-7r) and Gate B's item numbers (1-9) are stable identifiers: every guideline file cites them by ID, and `guidelines/rules/INDEX.md` maps each ID to its file. The gates keep their prose names — Gate A (3a), Gate B (3b) — alongside the IDs.

## The passes

Producing one page is five passes over named artifacts (a campaign adds the plan pass in front). Each pass file states its purpose, inputs, outputs, and who runs it in each mode, and carries the dispatch brief for its stage, so a campaign can fan any pass out across agents while a single agent single-steps the same pipeline, checkpointing between passes through the dossier.

| pass | spec | input → output |
|---|---|---|
| plan (multi-page work only) | `guidelines/passes/plan.md` | request → approved plan file at `progress/<campaign>.md` |
| 00 prep | `guidelines/passes/00-prep.md` | subsystem + topic + version → resolved subsystem entry, output path, run workspace, sample archetype |
| 01 research | `guidelines/passes/01-research.md` | page scope → dossier at `progress/<campaign>/<slug>.dossier.md` (format: `guidelines/passes/dossier.md`) |
| 02 write | `guidelines/passes/02-write.md` | dossier → fact-verified page at `docs/<dir>/<slug>.md`, the closed parity table at `progress/<campaign>/<slug>.parity.md`, and the exit-suite evidence persisted into the dossier |
| 03 lint-fix | `guidelines/passes/03-lint.md` | page → page with the 7r-settled classes fixed in place, plus the report at `progress/<campaign>/<slug>.lint.md` (fixed / escalated find-only / exempt); page state LINTED |
| 04 verify | `guidelines/passes/04-verify.md` | page after lint-fix → Gate A/B outcomes with recorded evidence; solo: run inline, page final; campaign: deferred to a verify campaign (the pass file's verify-campaign section), which stamps CERTIFIED |

## Modes

Single page, single agent (the default for one topic): execute passes 00 through 04 in order yourself. You run both gates (Gate A and Gate B, mapped in `guidelines/rules/INDEX.md`), and the page is done only at zero unadjudicated findings. Write the dossier even for a single page, in the run's own workspace under `progress/` ("The progress/ workspace" below); it is what makes each pass resumable in a later session. In interactive single-page use, ask before the actual save.

Multi-page write campaign (a documentation set of tens of pages): plan first per `guidelines/passes/plan.md` (a campaign starts with a unique short name and workspace, then a plan the user approves at `progress/<campaign>.md` — including the verification cadence decision), then produce pages in batches through a two-stage pipeline with one ownership rule: the facts are the writer's, end to end; prose and form are swept — and their settled classes fixed — by fresh eyes. The split exists because a writer re-reading its own prose misses its own blind spots, while the disk-settleable checks (excerpts, anchors, counts, coverage) are mechanical procedures a writer runs reliably on its own work.

1. Writer (the strongest available model; brief in `guidelines/passes/02-write.md`). Researches with semcode plus Grep/Read, writes the complete page following every rule under `guidelines/rules/` while composing, and delivers the facts verified: the parity table closes at zero empty rows (fill-or-decatalog) and the mechanical exit suite runs clean with its evidence persisted into the dossier's EVIDENCE section, before the writer reports done. The writer does not run the style sweeps on its own prose; its brief says so explicitly.
2. Fixer (a different, cheaper model, fresh context; brief in `guidelines/passes/03-lint.md`). Runs the lint-fix pass: Gate A candidate greps, the prose-shape read-throughs, and the exhaustive 7m span-form pass, every candidate adjudicated against the 7r registry — then fixes lane 1 in place (7r-settled classes via 7q recipes, byte-proved line-drift corrections, diagram geometry) and escalates everything unsettled find-only, with an exact before/after report. Concurrent agents use unique scratchpad filenames (shared names have collided).
3. Orchestrator checkpoint, per batch. Collect the writer and fixer reports; adjudicate the escalations (accepted ones go back to a fixer in fix-list mode — never to the writer); sample the fixer diffs; update the plan file's Status (page states WRITTEN → LINTED). No fact-checking happens here: pages stay uncertified until a verify campaign runs per the cadence decision recorded at the checkpoint, and that campaign — with its own orchestrator adjudicating find-only verifier agents — is the pipeline's independent fact-check.

Model-tier guidance, subsystem-independent: page writing needs the strongest model available (research judgment, prose discipline, figure quality); the fixer pass is pattern-plus-recipe work a mid-tier model performs reliably when the brief is explicit; orchestrators keep adjudication and sign-off — the write orchestrator over escalations, the verify orchestrator over findings and certification — and never delegate either. The writer runs the research pass itself by default, keeping the page dossier current as it researches; dispatching separate researcher agents (brief in `guidelines/passes/01-research.md`) to pre-build dossiers is an explicit opt-in, never the assumed shape.

Follow-up dispatch: kind decides the channel.

- Within the writing session: stylistic follow-ups (escalations the orchestrator confirms, or a defect noticed at a checkpoint) go to a fixer in fix-list mode. Factual follow-ups return to the original writer as a resume ("do not redo the research; work from what you have") while its transcript is alive; if repeated resumes fail, a fresh writer starts from the dossier, the parity table, and the plan file.
- After the writing session: every further finding belongs to a verify campaign. Its findings route to fixers (appliable classes) or become user-surfaced rewrite decisions executed by a fresh writer from the dossier — a writer transcript is never resumed across sessions; the dossier plus the plan file replace it, which is why the writer persists its evidence before reporting done.

Either channel's output is re-checked by the dispatching orchestrator before a page's state changes.

Batch generation and interruption recovery:

- Generate about five pages per batch: one writer agent per page, dispatched together, then a hard checkpoint before the next batch launches. Five keeps what a session rate limit or API outage can kill at once down to a recoverable set (each dead writer resumes from its transcript) while still parallelizing the writing. Do not launch the whole catalog in parallel. Fixer agents may trail into the following batch.
- When a writer or fixer dies mid-page, resume that same agent with a message; its context survives in its transcript. Say explicitly "do not redo the research; write the page now from what you have". If repeated resumes fail, hand the remainder to a fresh agent started from the page dossier (`progress/<campaign>/<slug>.dossier.md`) plus the plan file Status (a dead fixer is simply re-dispatched fresh; it holds no research state).
- After every completed page, append its entry (status, page statistics, adjudications, lessons) to the run's status journal (`progress/<campaign>/<campaign>.journal.md`, local scratch); at each batch checkpoint, fold the journal into the plan file's Status section. The tracked plan file thereby stays clean between checkpoints (no stashing around rebases), and a future session resumes from the plan file plus the on-disk pages alone.
- When using parallel sub-agents (Agent tool), ensure they have Write permissions before spawning. If Write is unavailable to agents, fall back to sequential processing immediately rather than failing and retrying.

In a campaign whose page catalog the user has already approved, save each finished page without a per-page ask and checkpoint per the pipeline above; git commits still require an explicit user go.

Verify campaign (certifying written pages — same session, a later session, or a different machine): plan and run per the verify-campaign section of `guidelines/passes/04-verify.md`. It is its own run under `progress/` (named `<parent>-verify`; its plan — census and delta catalog included — is committable, like every plan file), whose orchestrator curates the verify plan itself, dispatches find-only verifier agents (one per page plus one cross-page agent for seam consistency, fold-in landing, and catalog coverage), adjudicates every finding, and stamps clean pages CERTIFIED. Its only in-place edits are settled style fixes and byte-proved drift corrections through a fixer in fix-list mode; every factual finding is deferred into a committable delta catalog that seeds a follow-up delta write campaign (`guidelines/passes/plan.md`, "Delta write campaigns"), and the next verify campaign re-checks only the pages still uncertified. It works on any page corpus, including one written elsewhere with no artifacts ("verify docs/<dir>").

## The progress/ workspace

`progress/` (under the skill root, gitignored) is the runtime workspace for every run of this skill, and it accumulates: finished, suspended, and abandoned runs stay on disk until the user deletes them. One committable exception to the gitignore: top-level plan files (`progress/*.md` — write, verify, and delta write campaigns alike), so a campaign's memory, certification census, and delta catalog can travel with the repository and resume on another machine; committing one still requires the user's explicit go, taken at commit-worthy checkpoints (plan approval, batch completion, campaign close). Artifact directories and status journals are local scratch, never committed. The layout below keeps runs from contaminating each other, so a prompt similar to an earlier one produces a clean new run beside the old one instead of inheriting its files.

Every run — a multi-page campaign or a single-page task — owns a unique short name, chosen at run start, and at most two top-level entries under `progress/`:

- `progress/<campaign>.md` — the plan file (structure: `guidelines/passes/plan.md`). Campaigns only; a single-page run keeps no plan file.
- `progress/<campaign>/` — the artifact directory: the per-page dossiers (`<slug>.dossier.md`), lint reports (`<slug>.lint.md`), verify reports (`<slug>.verify.md`), and every other intermediate a sub-agent persists (parity tables, span inventories, follow-up notes, helper-script output), named `<slug>.<purpose>.<ext>`.

Nothing else lands at the top level of `progress/`. Pages never land here (they go under `docs/` per the save policy below), and no run writes inside another run's entries. Create the artifact directory the moment the run starts: at planning for a campaign, at pass 00 for a single page. The chosen name is recorded where a resuming agent will find it — the plan file's Context section for a campaign, the dossier HEADER for a single page — and every sub-agent brief carries the artifact directory as an absolute path (the `<campaign>` bracket in the brief templates inside the pass files); a sub-agent writes only inside its own run's directory.

Choosing the name: one to three lowercase hyphenated words naming the run's subsystem area (`mm`, `pagecache`, `usb4-tunneling`); a single-page run uses its topic slug. A verify campaign is named `<parent>-verify` when it verifies a write campaign, and any unique `-verify`-suffixed name for a standalone corpus; the `-verify` suffix is reserved for verify runs: it identifies the run kind at a glance and derives the parent campaign's name. The name must not collide with any existing top-level entry in `progress/`: list the entry names (`ls progress/`), and on collision append the date, then a counter — `pagecache` → `pagecache-20260711` → `pagecache-20260711-2`. That listing is a name-availability check only, never license to read the colliding run's files.

New runs start from scratch. Existing `progress/` entries belong to other runs: earlier sessions, parallel campaigns, superseded attempts. A session starting a new run reads nothing inside them — not the plan files, not the dossiers — and plans from scratch per `guidelines/passes/plan.md`, even when an old entry plainly covers a similar topic. Never resume, merge, or adopt half-finished work found in `progress/` uninvited; the old run stays untouched for reference, and deleting or overwriting another run's entries is the user's call, never the skill's. There are three ways into an existing run's files, all requiring the user to say so:

- Resume: the user asks to continue a specific campaign. The resume state is `progress/<campaign>.md` (Status section first), the pages on disk, and the artifact directory. When the user wants to resume but names no run, list `progress/*.md` and ask which.
- Reuse: the user directs the new run to consume a prior run's artifacts ("reuse the dossiers from the mm campaign"). Record what was reused in the new plan file's Context section; prior-run artifacts are hints under the same ground-truth rule as any dossier (7e, 7o), never evidence.
- Verify: the user asks to verify a campaign or corpus. The verify run declares its parent write campaign in its plan file's Context, and that request licenses reading the parent's plan file and artifact directory — as hints under the same ground-truth rule, never as evidence (`guidelines/passes/04-verify.md`). The parent's entries are still never modified; the verify run writes only inside its own two entries, and the one cross-write is the orchestrator mirroring CERTIFIED stamps into the parent plan file's Status.

Entries following neither shape (layouts predating this scheme) are opaque: treat them as reserved names and leave them alone.

## Writing rules and gates

Every criterion is its own rule file, stated once and referenced everywhere: `guidelines/rules/INDEX.md` maps IDs 3a-3c and 7/7a-7r to their files, the diagram rules with their figure catalogs (7g-7i) among them. The gates a page must pass are Gate A (`guidelines/rules/3a-gate-a.md`, the mechanical grep gate), Gate B (`guidelines/rules/3b-gate-b.md`, the nine-item review sign-off, with its ownership/timing split stated in the file), and the by-hand check procedures both gates use (`guidelines/rules/3c-mechanical-checks.md`; there is no checker script). Writers, fixers, and verifiers reference the same rule files, so the criteria cannot diverge between the agent that writes and the agents that check.

## Save and commit policy

Write the completed page to: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

Do not modify `SUMMARY.md` or `mkdocs.yml`.

No git commits without an explicit user go.

## Behavioral rules

- When asked to "discuss" or "review" a plan, engage conversationally with concise observations and questions. Do not immediately start executing, writing files, or producing verbose output. Wait for explicit approval before creating files.
- `progress/` accumulates the workspaces of prior runs; the isolation rules in "The progress/ workspace" above govern (list names only for the collision check; open another run's entries only on an explicit user resume, reuse, or verify request).
- Always read template/reference files first before generating any content; no page is generated before the prep pass (`guidelines/passes/00-prep.md`).
- When performing batch edits across many files, preserve existing content (e.g., lspci output, code references) that was added in prior passes. Read the full file before editing to avoid accidentally removing prior enrichments.
