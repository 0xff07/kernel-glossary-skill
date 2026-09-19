---
name: kernel-glossary-skill
description: >
  Generate structured Linux kernel reports for this knowledge base.
user-invocable: true
---

# kernel-glossary-skill

Generate a Linux kernel report following this project's conventions. The rules are eight guideline files, read by phase as the routes below say. Every rule section carries its slug, `## Excerpts and their explanation [excerpts]`, and every requirement its own, `[excerpts.verbatim, qa]` (the subsystem map and template are data and carry none). The `qa` marker means the requirement has one Python module under `tools/qa/checks/`, named by replacing dots and hyphens in its ID with underscores; it exports `RULE` and `check(page, inputs)`. The guideline prose is the writer's reading; the Python module and matching test are the implementation. Unmarked requirements are read by hand.

## What the knowledge base is

A documentation set on Linux kernel subsystems, organized by subsystem under `docs/`. Every fact on a new page is researched against the documented tree.

## Input

`$ARGUMENTS` or the conversation provides the subsystem, the topic, the documented kernel version (the tag of the local tree the pages cite) and, optionally, an output directory. The version is one value used everywhere: every Elixir URL embeds it, every claim is checked at it, the scripts run against the tree checked out at it, and a campaign pins it with its commit. When it is not given, derive it from the tree with `git describe --tags --exact-match` or `make -s kernelversion`; it must be an upstream release tag (a `v` tag, release candidates included), the tags elixir.bootlin.com carries, never a local or vendor tag, and it is stated back before generating. Example URLs in this skill use `v7.0`; substitute the documented version.

## Layout

1. `SKILL.md`, this file: the pipeline, the modes, the artifacts and the policies.
2. `guidelines/writing.md`: how a page explains, every rule any page must meet; `guidelines/kernel.md`: the Linux-kernel profile, what a kernel page is made of (sources, sections, provenance, links, coverage, subsystem conventions).
3. `guidelines/checking.md`: the QA steps, the sweeps, the worksheet evidence and the check pass.
4. `guidelines/figures.md`: when a figure is drawn, how, the register styles and the pattern index; `references/figures/`, one file per pattern with its notes and reference figures, read only when the index matches it.
5. `guidelines/campaign.md`: planning a multi-page campaign, the spec's structure and the four briefs.
6. `guidelines/worksheet.md`, `guidelines/template.md` and `guidelines/subsystems.md`: the worksheet format, the page template and the subsystem map.
7. `docs/`, `campaigns/` and `progress/`: the pages, the campaign specs and the run workspaces. `tools/qa/`: the QA engine, `kg`: `python3 tools/qa/kg.py check <page>` runs every rule the guidelines carry and prints the page's state, `--checklist` prints every requirement with its state, `kg check <page> --only <rule-id>` prints one rule’s findings and reading inventory, `kg table <page>` emits the worksheet's LINKS table, `kg retro <progress dir>` prints per rule what the checks found on the first pass of every page a campaign's worksheets record, `kg selftest` validates the bindings, every rule’s tests, reference figures and shared engine tests, `kg where <slug>` locates a requirement and its rule, and `tools/qa/README.md` describes the engine.

All relative paths resolve against this file's directory, available to the top-level agent as `${CLAUDE_SKILL_DIR}`; a sub-agent brief carries the absolute path instead.

## Reading routes

Each role loads what its phase needs and nothing ahead of it. A writer never loads `guidelines/campaign.md`; the brief carries what its page needs from the campaign.

| role and phase | reads |
|---|---|
| writer, before research | `SKILL.md` (the passes); `guidelines/kernel.md`; `guidelines/worksheet.md`; the page's entry in `guidelines/subsystems.md`; the brief: the catalog row and the boundary rules |
| writer, before writing | `guidelines/writing.md` whole; `guidelines/template.md` |
| writer, when drawing | `guidelines/figures.md` from [drawing] to [patterns], and [register-figures] when the figure is a register or bitfield; the one pattern file under `references/figures/` the index matches |
| writer, at QA | `guidelines/checking.md`; `guidelines/worksheet.md` again for the sections it fills; `tools/qa/README.md` only when the engine's output needs explaining |
| orchestrator, check pass | `guidelines/checking.md` [setup], [steps], [sweeps], [judgement], [figure-check], [report] and [check-pass]; the page's worksheet |
| planner | `guidelines/campaign.md`; `guidelines/subsystems.md` |

## The passes

Producing one page is four passes over three artifacts, and a campaign adds a plan pass in front (`guidelines/campaign.md`). No pass creates an artifact beyond the three: the page, the spec and the workspace with its log and worksheets.

1. Prep. Resolve the subsystem entry in `guidelines/subsystems.md` (dir, kernel_paths, spec, section6_heading), the output path `docs/<dir>/<group>/<slug>.md` and the workspace `progress/<campaign>/`: a run is one invoked slice of a campaign and reuses the campaign's workspace, a single page names a workspace of its own, and only a new campaign checks its name against both `campaigns/` and `progress/` at planning and extends it with the date and a counter on collision. Read `guidelines/worksheet.md` for the worksheet you will keep.
2. Research. Search the local tree, never the web, with the semcode tools first (`find_function`, `find_type`, `find_callers`, `find_calls`, `find_callchain`, `grep_functions`, `find_commit`, `dig`) and with Grep and Read for what they do not reach (macros in headers, `Documentation/`, Kconfig). Record into the worksheet (`guidelines/worksheet.md`) every symbol's definition file and line, at least one concrete usage per catalog symbol, every enumeration with its search basis, the spec sections found in comments and commit messages, and the `Link:` trailers of relevant commits. Print a function by its range and never a whole file, at most about 25 KB per command, and read a persisted output only by the slice needed. Every worksheet entry is a hint to re-verify on disk at write time, never a citation.
3. Write. Read `guidelines/writing.md` whole and `guidelines/template.md`. Compose under `guidelines/writing.md`, keep the completeness table as you go, draw any figure under `guidelines/figures.md` and the one pattern file its index matches, then read `guidelines/checking.md`, run its QA steps, fix what they find, and persist the evidence. Page state: WRITTEN.
4. Check. The orchestrator re-runs the mechanical checks and compares the answers, per the check pass in `guidelines/checking.md`, and closes by writing `LINTED <date> page sha256: <digest> qa sha256: <qa-digest>` at the end of the worksheet's LINT section. Page state: LINTED, the state the check pass reaches, which holds while the page and QA digests it names hold.

## Modes

1. Single page, single agent: run the four passes yourself, keep a worksheet even for one page, and in interactive use ask before saving. The check pass has no independent reader here, and its premise is that a self-report cannot prove itself: run it as a separate step from the output of `kg check` and the worksheet, never from memory of writing, and record `check pass: self-run` in LINT so a later reader knows no second agent compared the answers.
2. Campaign: plan first, then produce pages in user-invoked slices of one batch, one writer agent per page dispatched together, then the check pass per page, then the run log updated. Never launch beyond the invoked slice, and never a whole catalog in parallel. The page is the writer's end to end, facts and prose; what follows is verification, never authorship, and the LINTED record is the check pass's, never the writer's. Writers run on the model the writer agent definition pins; the orchestrator keeps adjudication and never delegates it.
3. Recovery: a writer that dies mid-page is resumed first, with "do not redo the research; write the page now from what you have"; when repeated resumes fail, a fresh agent starts from the worksheet plus the campaign spec, dispatched as a resume from the page's current digest. Stylistic follow-ups the orchestrator applies itself; factual follow-ups return to the original writer while its transcript lives, and after the session go to the user, who decides whether the page is rewritten: the page is removed in a commit of its own and created again from the removed revision as prior material (`guidelines/campaign.md` [deriving]).

## The three artifacts and the two states

1. The page, `docs/<dir>/<group>/<slug>.md`: the product, committed.
2. The campaign spec, `campaigns/<campaign>.md`: the specification and nothing else, committed and machine-portable, tree-relative and skill-relative paths only; the engine finds it by convention at `campaigns/<dir>.md`, so a campaign whose short name differs from its `docs/` directory passes `--spec` at every check (`guidelines/checking.md` [setup.runner]). Durable memory lives here: a refuted claim or an amended scope becomes a dated errata entry, and a settled adjudication is surfaced to the user.
3. The run workspace, `progress/<campaign>/`: the run log (`log.md`) and the worksheets, one per page at `progress/<campaign>/<dir>/<group>/<slug>.worksheet.md`, mirroring the page's path `docs/<dir>/<group>/<slug>.md` because two groups of one subsystem may share a slug; machine-local and never committed, the crash-recovery point for in-flight work. Nothing in it travels.

A page is WRITTEN, then LINTED; a finding is FIXED, ESCALATED or EXEMPT; there is no third state and no certification. Execution state is derived: the catalog is the checklist and `docs/` is the state, and that diff says what exists, never what is finished. A page on disk is WRITTEN. LINTED needs every mechanical check run with its inputs present (`kg check` reported neither a FAIL nor an INCOMPLETE run) and every confirmed finding resolved, and its evidence is the record the check pass writes at the end of the worksheet's LINT section, `LINTED <date> page sha256: <digest> qa sha256: <qa-digest>`, the page and QA digests printed by the final full run; `python3 tools/qa/kg.py check <page>` compares both digests and prints the state. An edit to the page, guidelines or executable QA files after the record returns the page to WRITTEN; a legacy record without a QA digest also requires a new check pass, and a page whose worksheet on this machine carries no LINTED record naming both current digests is WRITTEN whatever its history elsewhere: a recovering executor, on a cold machine above all, assumes WRITTEN and re-runs the check pass, which is cheap and idempotent, before counting the page done. The current rules bind every page whatever its age: a page written under older rules is out of compliance until the check pass fixes it in place, where the fix is exactly specified, or it is removed and created again, and LINTED on a re-run means no finding under the rules as they stand. The user names the campaign and the slice; given a campaign with no slice, ask. Every page in a brief carries its operation: a create, which the overwrite guard protects (a page whose path already exists is never overwritten silently; the run stops and surfaces it, and the answers are skip or rewrite), or a resume of a page a dead writer left, naming the digest it starts from; the resumed page is rebuilt in the writer's scratch directory, and the orchestrator re-checks the starting digest and moves it into place. A rewrite is not an operation and no writer operation writes over a page on disk; the one edit in place is the check pass's exactly specified fix (defined in `guidelines/checking.md` [check-pass.fixes]), and anything beyond it is a rewrite: the user removes the page in a commit of its own, and a create then derives the new page from the removed revision (`git show <commit>:docs/<dir>/<group>/<slug>.md`) as prior material under `guidelines/campaign.md` [deriving]. A run is one invoked slice of a campaign: it works in that campaign's workspace, reads nothing inside another campaign's workspace uninvited, and never renames it; the collision check is planning's, and a new campaign still plans from scratch and names any overlap with an existing spec. Scratch files go under the session scratchpad in a per-page subdirectory named for the page's path under `docs/`, `<dir>/<group>/<slug>/`, because the scratchpad is shared between concurrent writers, two pages may share a slug, and a generically named file is silently overwritten.

## Policies

1. Write the finished page to `docs/<dir>/<group>/<slug>.md`, and nothing else under `docs/`.
2. No git commit without an explicit user go; in an approved campaign, pages of an invoked slice save without per-page asks. A commit go covers the slice's LINTED pages; a page still WRITTEN is named as such and left out unless the user includes it.
3. When asked to discuss or review a plan, discuss; write nothing until the go.
4. A batch edit preserves what earlier passes added; read the whole file before editing it.
5. Commit form. A title opens with `skill:` for a change to the skill's own files (`SKILL.md`, `guidelines/`, `references/`, `tools/`, the READMEs) and with the campaign's short name, `usb4:`, for that campaign's pages, spec and errata; a change reaching several specs is one commit per spec. A page lands as `<campaign>: add <group>/<slug>`, its path under `docs/<dir>/`; its removal for a rewrite as `<campaign>: remove <group>/<slug> for its rewrite`; a check-pass fix as `<campaign>: <fix> on <group>/<slug>`, the fix named in a few words; and errata as `<campaign>: errata from the <page> <write|rewrite|fix pass>`. The body ends with one `Co-Authored-By:` line naming the model that wrote the change, the writer's for a page; no session URL and no other trailer is written, since the log is published.
