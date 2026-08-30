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
- `campaigns/` — committed, reusable campaign specifications ("The three artifacts and the three states" below)
- `guidelines/reference/TEMPLATE-FULL.md` — full page template with all sections
- `guidelines/reference/samples/` — the reference samples for writing and planning. This directory holds frozen copies of exemplar pages, one labelled counterexample, and an exemplar campaign plan file, kept independent of the live subsystem directories, outside `docs/`, so they stay findable even after the hierarchy under `docs/` is reorganized. The worked examples here define the house standard for the lead summary, section structure, prose, ASCII diagrams, self-contained kernel-source citation, depth of coverage, and campaign planning. Samples are style, structure, and depth guidance ONLY; they are never an authoritative source of kernel knowledge. Each documents its own tree at its own version and can carry errors found later, so no technical claim, line number, or excerpt is ever taken from a sample into new work; every fact is researched against the documented tree (PAGE-02, FACT-03). When writing any new page or plan, calibrate against the closest-matching file under `guidelines/reference/samples/`, and refer to example files only by their `guidelines/reference/samples/` path.
- Major subsystem directories under `docs/`: one per entry in the Subsystem Map (`guidelines/reference/subsystems.md`; the `dir` field of each entry)

## Input

`$ARGUMENTS` or conversation context provides:
- The subsystem (e.g., xHCI, PCIe, ACPI, USB4, DRM)
- The topic name (e.g., "host controller initialization", "MSI-X vectors")
- The documented kernel version (e.g., `v7.0`): the tag of the local tree the pages cite
- Optionally, an output directory override

If `$ARGUMENTS` is empty, derive the subsystem and topic from the conversation context.

The documented kernel version is a single value set once and used everywhere: every Elixir URL embeds it, every version-specific claim is checked at it, the mechanical checks run against the tree checked out at it, and a campaign pins it (tag plus commit) in the campaign spec's Context. When the version is not given, derive it from the local tree (`git describe --tags` or `make -s kernelversion` at the tree root), confirm elixir.bootlin.com carries that tag, and state the value back to the user before generating. All version-bearing examples in this skill use `v7.0`; substitute the documented version.

## Skill layout

Everything in this skill lives in one of four top-level directories beside this file:

- `docs/` — the knowledge base itself: the generated articles, organized by subsystem.
- `guidelines/` — all doctrine, split by concern:
  - `guidelines/passes/` — the pipeline, one file per stage (plan, 00-04), each carrying both the procedure and (where a campaign dispatches that stage to a sub-agent) the dispatch brief, plus the dossier spec
  - `guidelines/rules/` — every stable-ID criterion, one rule per file, grouped by directory: `bans/` (the prose bans), `page/` (page structure, citation, linking, provenance), `facts/` (coverage and claim verification), `plots/` (domain model, semantics tables, organization, derivation), `diagrams/` (the ASCII-figure rules and their catalogs, read only when a page carries a figure), and `routines/` (the checking harness: ROUTINE-01's protocol, ROUTINE-04's patterns, ROUTINE-05's recipes); each rule directory also carries its `<PREFIX>-WAIVERS.md` (waivers and settled rulings — the five together are the mandatory first read for every agent), and `INDEX.md` maps every ID — current and retired — to its file
  - `guidelines/reference/` — the Subsystem Map (`subsystems.md`, one entry per subsystem), the measured criteria, the draft-versus-page contrast, the page template (`TEMPLATE-FULL.md`), and the frozen samples with the exemplar campaign plan file (`guidelines/reference/samples/`)
- `campaigns/` — committed campaign specs: version-pinned, machine-portable playbooks any agent can execute by name and slice ("The three artifacts and the three states" below).
- `progress/` — per-campaign, machine-local run workspaces (run log + dossiers; never committed — all of `progress/` is gitignored). Progress artifacts are hints and evidence trails; the on-disk kernel tree at the documented version is always ground truth.

All relative paths in this skill resolve against this file's directory, available to the top-level agent as `${CLAUDE_SKILL_DIR}`. Sub-agent briefs carry the absolute skill path instead (a `SKILL_DIR` bracket in every brief template), because sub-agents do not inherit that variable.

Rule IDs are stable identifiers: every guideline file cites them by ID, and `guidelines/rules/INDEX.md` maps each ID to its file — including the retired old scheme (7-7v, 3a-3c, the gate names, and the old sign-off's item numbers), which historical dossiers, campaign specs, and registry rulings still cite. IDs never renumber, and no file carries a rule-range enumeration, so adding a rule touches only the new rule file, its one INDEX row, and the pass step that consumes it.

## The passes

Producing one page is five passes over named artifacts (a campaign adds the plan pass in front). Each pass file states its purpose, inputs, outputs, and who runs it in each mode, and carries the dispatch brief for its stage, so a campaign can fan any pass out across agents while a single agent single-steps the same pipeline, checkpointing between passes through the dossier.

Every pass writes into one of the three artifacts below; no pass creates a file of its own.

| pass | spec | input → output |
|---|---|---|
| plan (multi-page work only) | `guidelines/passes/plan.md` | request → approved campaign spec at `campaigns/<campaign>.md` |
| 00 prep | `guidelines/passes/00-prep.md` | subsystem + topic + version → resolved subsystem entry, output path, run workspace, sample archetype |
| 01 research | `guidelines/passes/01-research.md` | page scope → the dossier's research sections (`progress/<campaign>/<slug>.dossier.md`; format: `guidelines/passes/dossier.md`) |
| 02 write | `guidelines/passes/02-write.md` | dossier → verified page at `docs/<dir>/<slug>.md` — the writer owns facts AND prose, running the mechanical exit suite (excerpts, anchors, parity, counts, span closure, and the ROUTINE-01 sweeps) before reporting; the dossier's LINKS, PARITY, LINT and EVIDENCE sections are written; page state WRITTEN |
| 03 check | `guidelines/passes/03-check.md` | page → the orchestrator re-runs the writer's checks mechanically and compares the answers (sweep reproduction, figure sweep, span closure, excerpt and anchor spot-checks, geometry, counts); residuals adjudicated and applied, directly or through a fix-list fixer (`guidelines/passes/03-lint-fixlist.md`); page state LINTED |
| 04 verify | `guidelines/passes/04-verify.md` | a LINTED page, audited later — on a newer tree, or by a different model — → sweep and criteria outcomes (was Gate A and Gate B) with their evidence in the dossier's VERIFY section; page state CERTIFIED at zero unadjudicated findings |

## Modes

Single page, single agent (the default for one topic): execute passes 00 through 04 in order yourself. You run the full rule set under ROUTINE-01's protocol (mapped in `guidelines/rules/INDEX.md`), and the page is done only at zero unadjudicated findings. Write the dossier even for a single page, in the run's own workspace under `progress/` ("The three artifacts and the three states" below); it is what makes each pass resumable in a later session. In interactive single-page use, ask before the actual save.

Multi-page write campaign (a documentation set of tens of pages): plan first per `guidelines/passes/plan.md` (a campaign starts with a unique short name and workspace, then a plan the user approves at `campaigns/<campaign>.md`), then produce pages in user-invoked slices ("The three artifacts and the three states" below: the user names the campaign AND the slice; the batch order is a recommendation, not a state machine). One ownership rule governs the pipeline: **the page is the writer's, end to end — facts and prose — and what follows is verification, not authorship.**

1. Writer (the strongest available model; brief in `guidelines/passes/02-write.md`). Researches with semcode plus Grep/Read, writes the complete page under every rule, and then verifies its own work with the mechanical exit suite: excerpts byte-compared, anchors printed and confirmed (and persisted as the dossier's LINKS table), the PARITY table closed, every count re-derived on a differently-shaped second basis, the span inventory closed against LINKS, and the ROUTINE-01 prose and figure sweeps run with every candidate adjudicated against the waivers. It fixes what the suite finds and re-runs the suite over what it touched, because fixes introduce defects.
2. Orchestrator check, per page (`guidelines/passes/03-check.md`, never delegated). Re-runs those procedures independently and compares the answers. It is mechanical, costs on the order of ten thousand tokens, and exists for the one thing a self-report cannot supply: evidence that the self-report is true. A writer that skipped its suite and reported "clean" is indistinguishable from one that ran it, unless somebody re-runs it. Residuals are adjudicated by the orchestrator and applied — directly, or by a fixer in fix-list mode (`guidelines/passes/03-lint-fixlist.md`), which sweeps nothing and decides nothing. Page state WRITTEN → LINTED.

The fresh-eyes lint sweep this pipeline used to run was retired, and the reasoning is in 03-check.md. In short: its premise (a writer misses its own blind spots on re-reading) is true but irrelevant, because the sweeps are procedure, not perception — measured, a writer using the ROUTINE-01 prose view (was 3c) fixed 32 of 35 prose defects in its own draft, including 20 label-colons it had re-read twice without seeing, and a fresh fixer afterwards found 2 items on a 2,000-line page.

Model-tier guidance, subsystem-independent: page writing needs the strongest model available (research judgment, prose discipline, figure quality); the fixer pass is pattern-plus-recipe work a mid-tier model performs reliably when the brief is explicit; orchestrators keep adjudication and sign-off — the write orchestrator over escalations, the verify orchestrator over findings and certification — and never delegate either. The writer runs the research pass itself by default, keeping the page dossier current as it researches; dispatching separate researcher agents (brief in `guidelines/passes/01-research.md`) to pre-build dossiers is an explicit opt-in, never the assumed shape.

Follow-up dispatch: kind decides the channel.

- Within the writing session: stylistic follow-ups (escalations the orchestrator confirms, or a defect noticed at a checkpoint) go to a fixer in fix-list mode. Factual follow-ups return to the original writer as a resume ("do not redo the research; work from what you have") while its transcript is alive; if repeated resumes fail, a fresh writer starts from the dossier and the campaign spec.
- After the writing session: every further finding belongs to a verify campaign. Its findings route to fixers (appliable classes) or become user-surfaced rewrite decisions executed by a fresh writer from the dossier — a writer transcript is never resumed across sessions; the dossier plus the campaign spec replace it, which is why the writer persists its evidence before reporting done.

Either channel's output is re-checked by the dispatching orchestrator before a page's state changes.

Slice execution and interruption recovery:

- A run executes exactly the slice the user named. The recommended slice is one batch from the spec's batch order, about five pages: one writer agent per page, dispatched together, then the orchestrator check per page, then the run closes with its log updated. Five keeps what a session rate limit or API outage can kill at once down to a recoverable set (each dead writer resumes from its transcript) while still parallelizing the writing. Never launch beyond the invoked slice, and never a whole catalog in parallel. Fixer agents may trail while the run is alive.
- Before dispatching any writer, apply the overwrite guard ("The three artifacts and the three states"): a catalog page that already exists on disk is never overwritten silently — stop and surface it.
- When a writer or fixer dies mid-page, resume that same agent with a message; its context survives in its transcript. Say explicitly "do not redo the research; write the page now from what you have". If repeated resumes fail, hand the remainder to a fresh agent started from the page dossier (`progress/<campaign>/<slug>.dossier.md`) plus the campaign spec (a dead fixer is simply re-dispatched fresh; it holds no research state).
- After every completed page and at the slice checkpoint, append the entry (page state, statistics, adjudications, agent events) to the run log (`progress/<campaign>/log.md`). Anything DURABLE the run learned — a spec claim the tree refuted, a user amendment, a settled adjudication — is applied to the campaign spec as a dated amendment (or surfaced to the user for the waivers files), never left only in the log: the log is machine-local and dies with the machine, by design.
- When using parallel sub-agents (Agent tool), ensure they have Write permissions before spawning. If Write is unavailable to agents, fall back to sequential processing immediately rather than failing and retrying.

In a campaign whose catalog the user has approved, the pages of an invoked slice save without per-page asks; git commits still require an explicit user go.

Verify campaign (certifying written pages — same session, a later session, or a different machine): a campaign like any other, whose catalog lists pages to CERTIFY rather than pages to write. Plan and run it per `guidelines/passes/04-verify.md`. Its orchestrator dispatches find-only verifier agents (one per page, plus one cross-page agent for seam consistency, fold-in landing, and catalog coverage), adjudicates every finding itself, and stamps clean pages CERTIFIED in its run log. Its only in-place edits are settled style fixes and byte-proved drift corrections through a fixer in fix-list mode; every factual finding is recorded find-only in its run log and surfaced to the user, becoming the catalog of the follow-up repair campaign (a spec the user can commit) — a verify campaign never edits facts. A durable certification record exists only on an explicit user go (a committed verify report, or a dated certification amendment in the parent spec). It works on any page corpus, including one written elsewhere with no dossiers ("verify docs/<dir>").

## The three artifacts and the three states

Everything this skill produces is one of three things. There is no fourth, and no agent invents one.

1. **The page** — `docs/<dir>/<slug>.md`. The product, and the only artifact a reader ever sees. Committed.
2. **The campaign spec** — `campaigns/<campaign>.md`. The campaign's SPECIFICATION and nothing else: context with the version pin, scope decisions, inventory digests, the page catalog, boundary rules, the recommended batch order, write-time cautions, and the re-entry contract. Committed and REUSABLE: it records no execution state and no machine-specific information (machine portability is a hard requirement — tree-relative and skill-relative paths only, no absolute paths), so any agent on any machine with this skill plus a checkout at the pinned version can execute any slice of it from the spec alone. Durable campaign memory lives here and only here: when the tree refutes a spec claim or the user amends scope, the spec is edited in place with a dated amendment; a lesson that settles an adjudication is surfaced to the user, who alone folds it into the owning directory's waivers file. Structure: `guidelines/passes/plan.md`. Campaigns only; a single-page run keeps none.
3. **The run workspace** — `progress/<campaign>/`. Machine-local runtime, never committed (all of `progress/` is gitignored): the run log (`progress/<campaign>/log.md` — dated events of THIS machine's runs: slices invoked, pages WRITTEN → LINTED, adjudications, agent deaths and resumes) and the dossiers (`progress/<campaign>/<slug>.dossier.md`, one per page: the research, the PARITY table, the exit-suite EVIDENCE, the LINT and VERIFY findings; structure: `guidelines/passes/dossier.md`). The workspace is the crash-recovery point for in-flight work on this machine, and nothing in it travels: anything durable is promoted into the spec as a dated amendment, or it dies with the machine — by design.

**Execution state is derived, not recorded.** There is no shared campaign log anywhere: the catalog is the checklist and `docs/` is the state — "what remains of campaign X" is the diff between its catalog rows and the pages on disk. Runs are invoked, not self-directed: the user names the campaign AND the slice ("campaign networking, batch B3"; "pages skb-layout and skb-lifecycle"), and picking sane, non-colliding slices — across machines and across sessions — is the invoker's responsibility. Given a campaign with no slice, ask; never pick one autonomously. The spec's batch order is the recommended slicing and dependency order, not a state machine. The executor's one backstop against a mis-chosen slice is the **overwrite guard**: a catalog page that already exists on disk is never overwritten silently — the run stops and surfaces it ("already exists — repair, skip, or rewrite?").

**Three states, and no others.** A page is WRITTEN, then LINTED, then CERTIFIED. A finding is FIXED, ESCALATED, or EXEMPT. A fix is settled (applied in place) or unsettled (escalated to the orchestrator). The page states are pipeline-internal: WRITTEN → LINTED completes inside the run that writes the page, and per-page state is recorded only in the run log — so a page on disk is presumed to have completed its run's check pass, and a run that died between WRITTEN and LINTED is visible only in its own machine's log. CERTIFIED is stamped by a verify run in its own log; a durable certification record exists only when the user explicitly asks for one (a committed verify report, or a dated certification amendment in the parent spec).

The parity table, the lint report, and the verify report are SECTIONS OF THE DOSSIER, not files beside it — a pass records its outcome in the dossier and reports it in its final message, which is what the orchestrator actually reads. Helper scripts and working scratch belong in the agent's scratchpad directory, never in `progress/` — and inside it, under a per-page subdirectory the agent names for its own slug. The session scratchpad is SHARED between concurrently dispatched agents, so a generically named file (`links.md`, `prose.txt`, `v2.py`) is silently overwritten or read back mixed with a sibling's data. This has happened: a writer's emitted LINKS table came back carrying another page's spans, and its first anchor review ran against the merged table before it noticed. Namespace the scratch, or a batch's mechanical checks quietly verify the wrong page. `progress/` accumulates, and finished, suspended, and abandoned workspaces stay on disk until the user deletes them.

Every run owns a campaign name and at most ONE top-level entry under `progress/`: the workspace directory `progress/<campaign>/`. Successive slices of the same campaign on the same machine share that workspace — the log appends, dossiers accumulate, and a later slice may reuse the earlier dossiers as hints; concurrent same-machine runs of one campaign are the invoker's coordination problem, exactly like cross-machine ones. Pages never land there (they go under `docs/`), and no run writes inside another campaign's workspace. Create the directory the moment the run starts: at planning for a campaign, at pass 00 for a single page. The campaign name is recorded where a resuming agent will find it — the spec's Context, or the dossier HEADER for a single-page run — and every sub-agent brief carries the workspace directory as an absolute path.

Choosing the name: one to three lowercase hyphenated words naming the campaign's subsystem area (`mm`, `pagecache`, `usb4-tunneling`); a single-page run uses its topic slug; a verify campaign is named `<parent>-verify`. A NEW campaign's name must not collide with any existing entry in `campaigns/` or `progress/`: list both (`ls campaigns/ progress/`), and on collision append the date, then a counter — `pagecache` → `pagecache-20260711` → `pagecache-20260711-2`. That listing is a name-availability check only, never license to read another campaign's runtime files.

**Who may read what.** `campaigns/` is a shared library: any agent may read any spec — that is its purpose. `progress/` workspaces are per-campaign runtime and stay isolated: an agent executing campaign X touches only `progress/X/` and reads nothing inside other workspaces uninvited. A session starting a NEW campaign still plans from scratch per `guidelines/passes/plan.md`, even when an existing spec covers a similar topic (name the overlap to the user instead of silently adopting it); deleting or rewriting another campaign's spec or workspace is the user's call, never the skill's. Three user-initiated ways into existing campaign material:

- Execute/resume: the user names a campaign and a slice to run. The spec comes from `campaigns/`; when this machine already has the workspace, the run log and dossiers are the local recovery state; cold on a new machine, state is derived from the catalog-vs-`docs/` diff and the workspace is created fresh.
- Reuse: the user directs a new campaign to consume another campaign's artifacts ("reuse the dossiers from the mm campaign"). Record what was reused in the new spec's Context; prior artifacts are hints under the same ground-truth rule as any dossier (PAGE-02, FACT-03), never evidence.
- Verify: the user asks to verify a campaign or corpus. The verify campaign declares its parent in its own spec's Context; the request licenses reading this machine's parent dossiers as hints, never as evidence (`guidelines/passes/04-verify.md`). The verify run writes only inside its own workspace; durable certification records need an explicit user go (see the states above).

Entries following neither shape — including old-layout spec-plus-log hybrid files at `progress/<campaign>.md` — are opaque: treat them as reserved names and leave them alone.

## Writing rules and gates

Every criterion is stated once, under a stable ID, and referenced everywhere by that ID; `guidelines/rules/INDEX.md` maps each ID to its file. The rules live one per file, grouped by who reads them: `bans/`, `page/`, `facts/`, and `plots/` carry the writing rules; `guidelines/rules/diagrams/` carries the ASCII-figure rules with their figure catalogs (DIAG-01 through DIAG-04), read only when a page will carry a figure — DIAG-02's four banned shapes outrank the catalogs; `guidelines/rules/routines/` carries the checking harness. Each rule directory carries its `<PREFIX>-WAIVERS.md` — waivers and settled rulings, harness routed by ROUTINE-01 — and the five together are the mandatory first read for every agent.

What a page must pass is every rule's PASS CRITERIA, checked under ROUTINE-01's protocol with ROUTINE-04's candidate patterns (the mechanical sweeps that were Gate A, the review criteria that were Gate B's nine items, and the by-hand procedures that were 3c; there is no checker script, and `INDEX.md` maps the retired names onto the owning rules). Writers, fixers, and verifiers read the same rules, so the criteria cannot diverge between the agent that writes and the agents that check.

## Save and commit policy

Write the completed page to: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

Do not modify `SUMMARY.md` or `mkdocs.yml`.

No git commits without an explicit user go.

## Behavioral rules

- When asked to "discuss" or "review" a plan, engage conversationally with concise observations and questions. Do not immediately start executing, writing files, or producing verbose output. Wait for explicit approval before creating files.
- Campaign specs under `campaigns/` are a shared, readable library; `progress/` accumulates machine-local workspaces of prior runs, and the isolation rules in "The three artifacts and the three states" govern them (list names only for the collision check; open another campaign's workspace only on an explicit user execute/resume, reuse, or verify request).
- Runs are invoked: execute only the slice the user named, apply the overwrite guard before dispatching writers, and ask when a campaign is named without a slice.
- Always read template/reference files first before generating any content; no page is generated before the prep pass (`guidelines/passes/00-prep.md`).
- When performing batch edits across many files, preserve existing content (e.g., lspci output, code references) that was added in prior passes. Read the full file before editing to avoid accidentally removing prior enrichments.
