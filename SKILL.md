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
- `guidelines/templates/TEMPLATE-FULL.md` — full page template with all sections
- `guidelines/samples/` — the reference samples for writing and planning. This directory holds frozen copies of exemplar pages, one labelled counterexample, and the campaign plan file that produced the exemplars, kept independent of the live subsystem directories, outside `docs/`, so they stay findable even after the hierarchy under `docs/` is reorganized. The worked examples here define the house standard for the lead summary, section structure, prose, ASCII diagrams, self-contained kernel-source citation, depth of coverage, and campaign planning. Samples are style, structure, and depth guidance ONLY; they are never an authoritative source of kernel knowledge. Each documents its own tree at its own version and can carry errors found later, so no technical claim, line number, or excerpt is ever taken from a sample into new work; every fact is researched against the documented tree (7e, 7o). When writing any new page or plan, calibrate against the closest-matching file under `guidelines/samples/`, and refer to example files only by their `guidelines/samples/` path.
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
  - `guidelines/templates/` — the page template (`TEMPLATE-FULL.md`)
  - `guidelines/samples/` — the frozen reference samples and the exemplar campaign plan file
  - `guidelines/passes/` — the per-page pipeline, one file per pass, plus the dossier spec
  - `guidelines/rules/` — the writing rules, one file per rule ID (`INDEX.md` maps every ID)
  - `guidelines/diagrams/` — the diagram rules and figure catalogs (7g, 7h, 7i)
  - `guidelines/gates/` — Gate A, Gate B, and the by-hand mechanical checks
  - `guidelines/campaign/` — multi-page campaign methodology: planning, plan file structure, dispatch pipeline, draft reuse
  - `guidelines/agents/` — role cards and dispatch brief templates for campaign sub-agents
  - `guidelines/reference/` — the Subsystem Map (`subsystems.md`, one entry per subsystem), the measured criteria, and the draft-versus-page contrast
- `progress/` — gitignored runtime artifacts: per-page research dossiers and lint/verify reports (spec in `guidelines/passes/dossier.md`). Progress artifacts are hints and evidence trails; the on-disk kernel tree at the documented version is always ground truth.

All relative paths in this skill resolve against this file's directory, available to the top-level agent as `${CLAUDE_SKILL_DIR}`. Sub-agent briefs carry the absolute skill path instead (a `SKILL_DIR` bracket in every brief template), because sub-agents do not inherit that variable.

Rule IDs (7, 7a-7r), Gate A, and Gate B (items 1-9) are stable identifiers: every guideline file cites them by ID, and `guidelines/rules/INDEX.md` maps each ID to its file.

## The passes

Producing one page is five passes over named artifacts. Each pass file states its purpose, inputs, outputs, and who runs it in each mode, so a campaign can fan any pass out across agents while a single agent single-steps the same pipeline, checkpointing between passes through the dossier.

| pass | spec | input → output |
|---|---|---|
| plan (multi-page work only) | `guidelines/campaign/planning.md` | request → approved plan file |
| 00 prep | `guidelines/passes/00-prep.md` | subsystem + topic + version → resolved subsystem entry, output path, sample archetype |
| 01 research | `guidelines/passes/01-research.md` | page scope → dossier at `progress/<topic>/<slug>.dossier.md` (format: `guidelines/passes/dossier.md`) |
| 02 write | `guidelines/passes/02-write.md` | dossier → draft page at `docs/<dir>/<slug>.md` |
| 03 lint | `guidelines/passes/03-lint.md` | draft page → page fixed in place, plus `progress/<topic>/<slug>.lint.md` |
| 04 verify | `guidelines/passes/04-verify.md` | linted page → Gate A/B outcomes recorded in `progress/<topic>/<slug>.verify.md`; page final |

## Modes

Single page, single agent (the default for one topic): execute passes 00 through 04 in order yourself. You run both gates (`guidelines/gates/`), and the page is done only at zero unadjudicated findings. Write the dossier even for a single page; it is what makes each pass resumable in a later session. In interactive single-page use, ask before the actual save.

Multi-page campaign (a documentation set of tens of pages): plan first per `guidelines/campaign/planning.md` (a campaign starts with a plan the user approves), then produce pages in batches through the writer → lint → verify pipeline per `guidelines/campaign/pipeline.md`, dispatching sub-agents with the role cards and brief templates under `guidelines/agents/`. Gate ownership splits by role: the writer composes under every rule but never runs the gate loops; the lint agent runs Gate A, the mechanical checks, the exhaustive 7m span pass, and the 7o re-derivations, fixing findings in place; the orchestrator runs final verify and never delegates sign-off. In a campaign whose page catalog the user has already approved, save each finished page without a per-page ask and checkpoint per the pipeline; git commits still require an explicit user go.

## Writing rules and gates

Every writing criterion is its own rule file, stated once and referenced everywhere: `guidelines/rules/INDEX.md` maps IDs 7 and 7a-7r to their files, and the diagram rules with their figure catalogs (7g-7i) are under `guidelines/diagrams/`. The gates a page must pass are `guidelines/gates/gate-a.md` (the mechanical grep gate), `guidelines/gates/gate-b.md` (the nine-item review sign-off), and `guidelines/gates/mechanical-checks.md` (the by-hand check procedures; there is no checker script). Writers, lint agents, and the final verifier reference the same rule files, so the criteria cannot diverge between the agent that writes and the agents that check.

## Save and commit policy

Write the completed page to: `${CLAUDE_SKILL_DIR}/docs/<dir>/<topic-slug>.md`

Do not modify `SUMMARY.md` or `mkdocs.yml`.

No git commits without an explicit user go.

## Behavioral rules

- When asked to "discuss" or "review" a plan, engage conversationally with concise observations and questions. Do not immediately start executing, writing files, or producing verbose output. Wait for explicit approval before creating files.
- Always read template/reference files first before generating any content; no page is generated before the prep pass (`guidelines/passes/00-prep.md`).
- When performing batch edits across many files, preserve existing content (e.g., lspci output, code references) that was added in prior passes. Read the full file before editing to avoid accidentally removing prior enrichments.
