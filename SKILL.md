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
- `guidelines/reference/samples/` — the reference samples for writing and planning. This directory holds frozen copies of exemplar pages, one labelled counterexample, and an exemplar campaign plan file, kept independent of the live subsystem directories, outside `docs/`, so they stay findable even after the hierarchy under `docs/` is reorganized. The worked examples here define the house standard for the lead summary, section structure, prose, ASCII diagrams, self-contained kernel-source citation, depth of coverage, and campaign planning. Samples are style, structure, and depth guidance ONLY; they are never an authoritative source of kernel knowledge. Each documents its own tree at its own version and can carry errors found later, so no technical claim, line number, or excerpt is ever taken from a sample into new work; every fact is researched against the documented tree (7e, 7o). When writing any new page or plan, calibrate against the closest-matching file under `guidelines/reference/samples/`, and refer to example files only by their `guidelines/reference/samples/` path.
- Major subsystem directories under `docs/`: one per entry in the Subsystem Map (`guidelines/reference/subsystems.md`; the `dir` field of each entry)

## Input

`$ARGUMENTS` or conversation context provides:
- The subsystem (e.g., xHCI, PCIe, ACPI, USB4, DRM)
- The topic name (e.g., "host controller initialization", "MSI-X vectors")
- The documented kernel version (e.g., `v7.0`): the tag of the local tree the pages cite
- Optionally, an output directory override

If `$ARGUMENTS` is empty, derive the subsystem and topic from the conversation context.

The documented kernel version is a single value set once and used everywhere: every Elixir URL embeds it, every version-specific claim is checked at it, the mechanical checks run against the tree checked out at it, and a campaign pins it (tag plus commit) in the campaign file's Context. When the version is not given, derive it from the local tree (`git describe --tags` or `make -s kernelversion` at the tree root), confirm elixir.bootlin.com carries that tag, and state the value back to the user before generating. All version-bearing examples in this skill use `v7.0`; substitute the documented version.

## Skill layout

Everything in this skill lives in one of three top-level directories beside this file:

- `docs/` — the knowledge base itself: the generated articles, organized by subsystem.
- `guidelines/` — all doctrine, split by concern:
  - `guidelines/passes/` — the pipeline, one file per stage (plan, 00-04), each carrying both the procedure and (where a campaign dispatches that stage to a sub-agent) the dispatch brief, plus the dossier spec
  - `guidelines/rules/` — every stable-ID criterion, in three files: `rules.md` (the writing rules and the gates — Gate A, Gate B, and the by-hand mechanical checks), `diagrams.md` (the ASCII-figure rules and their figure catalogs, read only when a page carries a figure), and `7r-adjudications.md` (the settled adjudications registry, the mandatory first read for every agent); `INDEX.md` maps every ID to its file
  - `guidelines/reference/` — the Subsystem Map (`subsystems.md`, one entry per subsystem), the measured criteria, the draft-versus-page contrast, the page template (`TEMPLATE-FULL.md`), and the frozen samples with the exemplar campaign plan file (`guidelines/reference/samples/`)
- `progress/` — per-run workspaces ("The three artifacts and the three states" below). Progress artifacts are hints and evidence trails; the on-disk kernel tree at the documented version is always ground truth.

All relative paths in this skill resolve against this file's directory, available to the top-level agent as `${CLAUDE_SKILL_DIR}`. Sub-agent briefs carry the absolute skill path instead (a `SKILL_DIR` bracket in every brief template), because sub-agents do not inherit that variable.

Rule IDs and Gate B's item numbers (1-9) are stable identifiers: every guideline file cites them by ID, and `guidelines/rules/INDEX.md` maps each ID to its file. IDs never renumber, and no file carries a rule-range enumeration, so adding a rule touches only the file that holds it. The gates keep their prose names — Gate A (3a), Gate B (3b) — alongside the IDs.

## The passes

Producing one page is five passes over named artifacts (a campaign adds the plan pass in front). Each pass file states its purpose, inputs, outputs, and who runs it in each mode, and carries the dispatch brief for its stage, so a campaign can fan any pass out across agents while a single agent single-steps the same pipeline, checkpointing between passes through the dossier.

Every pass writes into one of the three artifacts below; no pass creates a file of its own.

| pass | spec | input → output |
|---|---|---|
| plan (multi-page work only) | `guidelines/passes/plan.md` | request → approved campaign file at `progress/<campaign>.md` |
| 00 prep | `guidelines/passes/00-prep.md` | subsystem + topic + version → resolved subsystem entry, output path, run workspace, sample archetype |
| 01 research | `guidelines/passes/01-research.md` | page scope → the dossier's research sections (`progress/<campaign>/<slug>.dossier.md`; format: `guidelines/passes/dossier.md`) |
| 02 write | `guidelines/passes/02-write.md` | dossier → fact-verified page at `docs/<dir>/<slug>.md`, plus the closed PARITY table and the exit-suite EVIDENCE written into the dossier; page state WRITTEN |
| 03 lint-fix | `guidelines/passes/03-lint.md` | page → page with the settled classes fixed in place, plus the LINT section written into the dossier (fixed / escalated / exempt); page state LINTED |
| 04 verify | `guidelines/passes/04-verify.md` | page after lint-fix → Gate A and Gate B outcomes with their evidence written into the dossier's VERIFY section; page state CERTIFIED at zero unadjudicated findings |

## Modes

Single page, single agent (the default for one topic): execute passes 00 through 04 in order yourself. You run both gates (Gate A and Gate B, mapped in `guidelines/rules/INDEX.md`), and the page is done only at zero unadjudicated findings. Write the dossier even for a single page, in the run's own workspace under `progress/` ("The three artifacts and the three states" below); it is what makes each pass resumable in a later session. In interactive single-page use, ask before the actual save.

Multi-page write campaign (a documentation set of tens of pages): plan first per `guidelines/passes/plan.md` (a campaign starts with a unique short name and workspace, then a plan the user approves at `progress/<campaign>.md` — including the verification cadence decision), then produce pages in batches through a two-stage pipeline with one ownership rule: the facts are the writer's, end to end; prose and form are swept — and their settled classes fixed — by fresh eyes. The split exists because a writer re-reading its own prose misses its own blind spots, while the disk-settleable checks (excerpts, anchors, counts, coverage) are mechanical procedures a writer runs reliably on its own work.

1. Writer (the strongest available model; brief in `guidelines/passes/02-write.md`). Researches with semcode plus Grep/Read, writes the complete page following every rule under `guidelines/rules/` while composing, and delivers the facts verified: the dossier's PARITY table closes at zero empty rows (fill-or-decatalog) and the mechanical exit suite runs clean with its evidence persisted into the dossier's EVIDENCE section, before the writer reports done. The writer does not run the style sweeps on its own prose; its brief says so explicitly.
2. Fixer (a different, cheaper model, fresh context; brief in `guidelines/passes/03-lint.md`). Runs the lint-fix pass: Gate A candidate greps, the prose-shape read-throughs, and the exhaustive 7m span-form pass, every candidate adjudicated against the 7r registry — then fixes lane 1 in place (7r-settled classes via 7q recipes, byte-proved line-drift corrections, diagram geometry) and escalates everything unsettled find-only, recording an exact before/after in the dossier's LINT section.
3. Orchestrator checkpoint, per batch. Collect the writer and fixer reports; adjudicate the escalations (accepted ones go back to a fixer in fix-list mode — never to the writer); sample the fixer diffs; append the batch entry to the campaign file's Status (page states WRITTEN → LINTED). No fact-checking happens here: pages stay uncertified until a verify campaign runs per the cadence decision recorded at the checkpoint, and that campaign — with its own orchestrator adjudicating find-only verifier agents — is the pipeline's independent fact-check.

Model-tier guidance, subsystem-independent: page writing needs the strongest model available (research judgment, prose discipline, figure quality); the fixer pass is pattern-plus-recipe work a mid-tier model performs reliably when the brief is explicit; orchestrators keep adjudication and sign-off — the write orchestrator over escalations, the verify orchestrator over findings and certification — and never delegate either. The writer runs the research pass itself by default, keeping the page dossier current as it researches; dispatching separate researcher agents (brief in `guidelines/passes/01-research.md`) to pre-build dossiers is an explicit opt-in, never the assumed shape.

Follow-up dispatch: kind decides the channel.

- Within the writing session: stylistic follow-ups (escalations the orchestrator confirms, or a defect noticed at a checkpoint) go to a fixer in fix-list mode. Factual follow-ups return to the original writer as a resume ("do not redo the research; work from what you have") while its transcript is alive; if repeated resumes fail, a fresh writer starts from the dossier and the campaign file.
- After the writing session: every further finding belongs to a verify campaign. Its findings route to fixers (appliable classes) or become user-surfaced rewrite decisions executed by a fresh writer from the dossier — a writer transcript is never resumed across sessions; the dossier plus the campaign file replace it, which is why the writer persists its evidence before reporting done.

Either channel's output is re-checked by the dispatching orchestrator before a page's state changes.

Batch generation and interruption recovery:

- Generate about five pages per batch: one writer agent per page, dispatched together, then a hard checkpoint before the next batch launches. Five keeps what a session rate limit or API outage can kill at once down to a recoverable set (each dead writer resumes from its transcript) while still parallelizing the writing. Do not launch the whole catalog in parallel. Fixer agents may trail into the following batch.
- When a writer or fixer dies mid-page, resume that same agent with a message; its context survives in its transcript. Say explicitly "do not redo the research; write the page now from what you have". If repeated resumes fail, hand the remainder to a fresh agent started from the page dossier (`progress/<campaign>/<slug>.dossier.md`) plus the campaign file (a dead fixer is simply re-dispatched fresh; it holds no research state).
- After every completed page and at every batch checkpoint, append the entry (page state, statistics, adjudications, corrections, lessons) to the campaign file's Status. That file is the campaign's only memory: a future session resumes from it plus the on-disk pages, and anything not written there is lost when the machine is.
- When using parallel sub-agents (Agent tool), ensure they have Write permissions before spawning. If Write is unavailable to agents, fall back to sequential processing immediately rather than failing and retrying.

In a campaign whose page catalog the user has already approved, save each finished page without a per-page ask and checkpoint per the pipeline above; git commits still require an explicit user go.

Verify campaign (certifying written pages — same session, a later session, or a different machine): a campaign like any other, whose catalog lists pages to CERTIFY rather than pages to write. Plan and run it per `guidelines/passes/04-verify.md`. Its orchestrator dispatches find-only verifier agents (one per page, plus one cross-page agent for seam consistency, fold-in landing, and catalog coverage), adjudicates every finding itself, and stamps clean pages CERTIFIED in its own campaign file. Its only in-place edits are settled style fixes and byte-proved drift corrections through a fixer in fix-list mode; every factual finding is recorded in its Status and becomes the catalog of the follow-up write campaign that repairs it — a verify campaign never edits facts. It works on any page corpus, including one written elsewhere with no dossiers ("verify docs/<dir>").

## The three artifacts and the three states

Everything this skill produces is one of three things. There is no fourth, and no agent invents one.

1. **The page** — `docs/<dir>/<slug>.md`. The product, and the only artifact a reader ever sees. Committed.
2. **The campaign file** — `progress/<campaign>.md`. The campaign's SPECIFICATION and its LOG, in one file: context, scope decisions, inventory digests, the page catalog, the boundary rules, the batch order, the write-time cautions, and a living dated Status recording what happened, what the tree refuted, and what was learned. It is the campaign's only memory. Committable — the one exception to the `progress/` gitignore — so a campaign resumes on another machine from this file plus the pages on disk. Structure: `guidelines/passes/plan.md`. Campaigns only; a single-page run keeps none.
3. **The dossier** — `progress/<campaign>/<slug>.dossier.md`. One per page, and the page's entire working file: the research, the PARITY table, the exit-suite EVIDENCE, the LINT findings, the VERIFY findings. Local scratch, never committed. It is the recovery point when an agent dies mid-page, and the starting evidence when a later pass re-derives. Structure: `guidelines/passes/dossier.md`.

**Three states, and no others.** A page is WRITTEN, then LINTED, then CERTIFIED. A finding is FIXED, ESCALATED, or EXEMPT. A fix is settled (applied in place) or unsettled (escalated to the orchestrator).

The parity table, the lint report, and the verify report are SECTIONS OF THE DOSSIER, not files beside it — a pass records its outcome in the dossier and reports it in its final message, which is what the orchestrator actually reads. Helper scripts and working scratch belong in the agent's own scratchpad directory, never in `progress/`. `progress/` is gitignored (excepting the campaign files), it accumulates, and finished, suspended, and abandoned runs stay on disk until the user deletes them.

Every run — a multi-page campaign or a single-page task — owns a unique short name chosen at run start, and at most two top-level entries under `progress/`: the campaign file `progress/<campaign>.md`, and the directory `progress/<campaign>/` that holds its dossiers. Nothing else lands there. Pages never land there (they go under `docs/`), and no run writes inside another run's entries. Create the directory the moment the run starts: at planning for a campaign, at pass 00 for a single page. The chosen name is recorded where a resuming agent will find it — the campaign file's Context, or the dossier HEADER for a single page — and every sub-agent brief carries the directory as an absolute path.

Choosing the name: one to three lowercase hyphenated words naming the run's subsystem area (`mm`, `pagecache`, `usb4-tunneling`); a single-page run uses its topic slug; a verify campaign is named `<parent>-verify`. The name must not collide with any existing top-level entry in `progress/`: list the entry names (`ls progress/`), and on collision append the date, then a counter — `pagecache` → `pagecache-20260711` → `pagecache-20260711-2`. That listing is a name-availability check only, never license to read the colliding run's files.

New runs start from scratch. Existing `progress/` entries belong to other runs: earlier sessions, parallel campaigns, superseded attempts. A session starting a new run reads nothing inside them — not the plan files, not the dossiers — and plans from scratch per `guidelines/passes/plan.md`, even when an old entry plainly covers a similar topic. Never resume, merge, or adopt half-finished work found in `progress/` uninvited; the old run stays untouched for reference, and deleting or overwriting another run's entries is the user's call, never the skill's. There are three ways into an existing run's files, all requiring the user to say so:

- Resume: the user asks to continue a specific campaign. The resume state is `progress/<campaign>.md` (Status section first), then the pages on disk, then the dossiers. When the user wants to resume but names no run, list `progress/*.md` and ask which.
- Reuse: the user directs the new run to consume a prior run's artifacts ("reuse the dossiers from the mm campaign"). Record what was reused in the new campaign file's Context; prior-run artifacts are hints under the same ground-truth rule as any dossier (7e, 7o), never evidence.
- Verify: the user asks to verify a campaign or corpus. The verify run declares its parent in its own campaign file's Context, and that request licenses reading the parent's campaign file and dossiers — as hints under the same ground-truth rule, never as evidence (`guidelines/passes/04-verify.md`). The verify run writes only inside its own two entries; the one cross-write is the orchestrator mirroring CERTIFIED stamps into the parent's Status.

Entries following neither shape (layouts predating this scheme) are opaque: treat them as reserved names and leave them alone.

## Writing rules and gates

Every criterion is stated once, under a stable ID, and referenced everywhere by that ID; `guidelines/rules/INDEX.md` maps each ID to its file. `guidelines/rules/rules.md` carries the writing rules and the gates together, grouped by who reads them — the prose and style classes a lint pass sweeps, the fact and coverage classes a writer owns, and the gates themselves. `guidelines/rules/diagrams.md` carries the ASCII-figure rules with their figure catalogs (7g-7i), and is read only when a page will carry a figure. `guidelines/rules/7r-adjudications.md` is the settled adjudications registry and is the mandatory first read for every agent.

The gates a page must pass are Gate A (3a, the mechanical grep gate), Gate B (3b, the nine-item review sign-off, with its ownership/timing split stated in the rule), and the by-hand check procedures both gates use (3c; there is no checker script). Writers, fixers, and verifiers read the same rules, so the criteria cannot diverge between the agent that writes and the agents that check.

## Save and commit policy

Write the completed page to: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

Do not modify `SUMMARY.md` or `mkdocs.yml`.

No git commits without an explicit user go.

## Behavioral rules

- When asked to "discuss" or "review" a plan, engage conversationally with concise observations and questions. Do not immediately start executing, writing files, or producing verbose output. Wait for explicit approval before creating files.
- `progress/` accumulates the workspaces of prior runs; the isolation rules in "The progress/ workspace" above govern (list names only for the collision check; open another run's entries only on an explicit user resume, reuse, or verify request).
- Always read template/reference files first before generating any content; no page is generated before the prep pass (`guidelines/passes/00-prep.md`).
- When performing batch edits across many files, preserve existing content (e.g., lspci output, code references) that was added in prior passes. Read the full file before editing to avoid accidentally removing prior enrichments.
