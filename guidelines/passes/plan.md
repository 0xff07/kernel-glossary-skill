# Pass plan: campaign planning (multi-page work only)

Purpose: turn a multi-page request into a user-approved, durable campaign plan that survives context loss and session interruption.
Inputs: the request (a prompt file or the conversation) and the documented tree.
Outputs: the campaign's workspace (the plan file at `progress/<campaign>.md`, structured per "The plan file's structure" below, plus the artifact directory `progress/<campaign>/`) and the approved plan, complete per the checklist below, with the user checkpoint recorded in it.
Run by: the orchestrator itself (or the human planner), never a dispatchable sub-agent — catalog design is the load-bearing judgment of the campaign. The planner dispatches read-only inventory agents and a plan-review agent (briefs at the end of this file) and makes every catalog decision itself from their outputs. In single-agent mode, the same agent runs this as its first pass for any multi-page task, under the same methodology.
Next: batched writer → fixer production per SKILL.md ("Modes"); certification per the verify campaign in `guidelines/passes/04-verify.md`.

Rule IDs (3a-3c, 7, 7a-7r) resolve via `guidelines/rules/INDEX.md`.

The numbered passes define a single page; this pass defines the set. It is the workflow that produced the sample pages under `guidelines/reference/samples/`, written here in subsystem-independent terms; substitute any subsystem's `kernel_paths`, structures, and syscall surface for the mm examples.

## Plan before generating

A campaign starts with a plan the user approves, kept in a durable plan file. The moment planning starts, choose the campaign's unique short name and create its workspace per SKILL.md ("The progress/ workspace"): the plan file at `progress/<campaign>.md` and the artifact directory `progress/<campaign>/` beside it, where every dossier, lint report, verify report, and other agent intermediate of this campaign will land. (Claude Code's plan mode provides a plan buffer of its own; the durable copy is still `progress/<campaign>.md`.) Treat the plan file as the single source of truth: every phase below writes its output into the file, and nothing load-bearing stays only in conversation or in agent transcripts. Existing entries under `progress/` belong to other runs: they constrain only the name choice, and nothing inside them is read or reused unless the user explicitly asks. `guidelines/reference/samples/plan-mm-campaign.md` is the plan file of the campaign that produced the sample pages, with one curation: its Status section is reduced to generic entry shapes with placeholders, so the example teaches the log's form without tying the sample to any one execution. Read it once before planning a campaign for any subsystem and imitate its section shapes rather than inventing new ones.

Build the plan in this order:

1. Extract the request's constraints before touching the tree. From the request (a prompt file or the conversation), record verbatim into the plan file's Context and Scope sections: the documented tree with its version tag and commit pin, the architecture scope, the granularity preference, the emphasis areas the request stresses (lifecycle, state transitions, hard limits, callback semantics), any wording bans or mandatory tools, and the topic list itself. Note where the request is explicitly incomplete ("this list is rough", a blank bullet, an area with no bullets); each such gap is a curation obligation, never an omission to mirror.
2. Inventory with parallel read-only agents, one per major area. Split the topic into three to six areas along the request's own headings and dispatch one read-only research agent per area, in parallel (read-only inventory agents are safe to parallelize; writers are not). Each brief follows the inventory template at the end of this file: the area, the `kernel_paths` subset to search, the documented tree and version, the toolset (semcode `find_type`, `find_function`, `find_callers`, `grep_functions`, plus Grep and Read), and the six digest deliverables. Demand a COMPACT digest; a compact report survives agent deaths and resumes better than prose chapters, and it lands verbatim in the plan file. When an inventory agent dies (rate limit, transient API error), resume that same agent and ask for the compact report of what it has so far instead of restarting the research; spawn a fresh agent only after resuming fails twice.
3. Record the digests in the plan file, one Inventory findings subsection per area, before any catalog work. Treat every line number in a digest as a hint to re-verify at write time, never as a citation; semcode indexes can lag the tree, and the on-disk source at the documented version is always ground truth. Give the version-specific renames and removals their own prominence; they are the facts that keep pages version-correct.
4. Curate the catalog yourself; do not delegate it. Catalog design is the load-bearing judgment of the campaign, and the orchestrator (or the human planner) makes it from the digests. Map every bullet of the request to one or more catalog rows; curate gap-fill rows for topics the digests surfaced that the request missed; and for every suggested topic that does NOT get a page, record a fold-in adjudication naming the page that absorbs it (the fold-in list prevents re-litigating scope later). Each catalog row carries (a) the output path `docs/<dir>/<group>/<slug>.md`, (b) a scope statement naming the anchor symbols the page is built around, each with a file:line hint from the digest, and (c) a tag recording whether the row was explicitly requested or curated. Prefer fine granularity: one mechanism, one page; a request bullet that mixes kinds of page (the object itself, its ops structure, the syscalls that drive it) becomes multiple groups, and a "walkthrough" bullet becomes an overview row plus an algorithm row. Choose the directory organization at the same time (two levels, `docs/<dir>/<group>/`, matching the house layout) and state its rationale in the file.
5. Write the boundary rules. Self-contained pages overlap by design, so for every cluster of sibling rows write one boundary statement that fixes each page's mission. The useful form names the seam symbol: "page A owns the syscall surface and treats the X machinery as a black box; page B owns X's object pipeline; page C owns the physical teardown; helper Y at file:line is the seam where A's coverage ends and B's opens". These statements go into the plan file and later verbatim into each writer brief, so siblings recap each other in at most one short paragraph instead of duplicating walkthroughs.
6. Have the catalog adversarially reviewed by a fresh agent. Dispatch a plan-review agent (brief template at the end of this file) whose only job is to attack the catalog: coverage gaps against the digests, duplicated ownership, wrong granularity, ordering defects, anchor symbols absent at the documented version. Apply the amendments you accept and record the outcome in the plan file; the campaign that produced the sample pages took two merges, two splits, six scope amendments, four new fold-ins, and its boundary statements from this review. A catalog nobody attacked ships its blind spots.
7. Order the batches foundational-to-derived: encodings and counters before the objects that hold them, objects before the tree/list machinery that indexes them, machinery before the syscalls that drive it, core mechanisms before driver instances. Split the catalog into batches of about five pages; the batch is the unit of dispatch and checkpointing (SKILL.md "Modes").
8. Checkpoint with the user before generating anything. Ask only the genuine scope questions, each with two to four concrete options (include a supporting construct group or not; cover a full syscall surface or a subset), plus one standing question every campaign carries: the verification cadence — when the verify campaign (`guidelines/passes/04-verify.md`) should run for this catalog (after the first batch for calibration, at campaign end, both, or only on demand). Present the final catalog and directory layout, and get an explicit go. Record the questions, the answers (the cadence decision lands in Scope decisions), and every later amendment (priority reorders, pipeline changes, new bans) in a dated amendments section at the moment it arrives; amendments supersede the original order silently otherwise, and a superseded ordering stays in the file marked as reference.

A plan is complete when every item below holds; confirm each before presenting it:

- The Context section records the campaign short name and its workspace entries (`progress/<campaign>.md`, `progress/<campaign>/`).
- Every bullet of the request maps to at least one catalog row or one recorded fold-in, and blank or vague bullets became curated rows.
- Every catalog row has its output path, a scope statement with at least one anchor symbol carrying a file:line hint, and a requested-or-curated tag.
- The catalog states the projected page total and the tag census (how many requested, how many curated).
- Every sibling cluster has a boundary statement naming its seam symbol.
- The fold-in list records every absorbed topic and its absorbing page.
- One inventory digest per area is in the file, including the version-specific renames and removals.
- The batch order is foundational-to-derived in batches of about five, and the write-time cautions (line numbers are hints, with the known drift examples found so far) are recorded.
- The adversarial review ran and its accepted amendments are recorded.
- The user checkpoint happened: the questions, the decisions (including the verification cadence), and the explicit go are in the file.
- The save and commit policy is stated (where pages land, no navigation-file edits, no git commits without a user go).

The plan file is the campaign's memory: inventory digests, the catalog, boundary rules, amendments, per-batch status, the draft-reuse map, and lessons learned (verifier false-positive classes, settled linking adjudications). After any interruption, the plan file plus the pages on disk are sufficient to resume without redoing research.

## The plan file's structure

`guidelines/reference/samples/plan-mm-campaign.md` carries eight top-level sections; a conforming plan file carries the same elements (the nesting may vary, the presence may not). The sample predates the progress workspace layout and carries no campaign-name line; new plan files carry it — where a sample and a rule disagree, the rule governs.

1. Context: what was asked, where the requirements come from, the campaign short name with its artifact directory (`progress/<campaign>/`), the documented tree with its version tag and commit pin, what is explicitly not an input, and the output root.
2. Status: a living, dated checklist. Every phase completion, batch result, suspension, correction, and lesson is appended at the moment it happens; a future session resumes from this section plus the pages on disk. Per-page state is tracked here as WRITTEN → LINTED → CERTIFIED: the first two are stamped by the write campaign's checkpoints, CERTIFIED only by a verify campaign (`guidelines/passes/04-verify.md`), which mirrors its stamp into this section when this campaign is its parent.
3. Scope decisions: the user-confirmed choices, numbered, including the verification cadence decision from the checkpoint.
4. Inventory findings: one compact digest per area, from the inventory agents, including the version-specific renames and removals.
5. Directory organization: the group layout with its rationale.
6. Page catalog: one table per group with columns page | scope (anchor symbols) | tag, followed by the fold-in adjudications, the projected total with tag census, and the overlap boundary rules (one statement per sibling cluster, seam symbols named).
7. Execution and verification: the per-page procedure and its campaign-specific deltas, project-specific writing bans from the request, gate ownership for the pipeline, write-time rules (line numbers are hints, with the known-drift list), user amendments (dated, explicitly superseding what they replace), the batch order (current, plus any superseded order kept for reference), and the save/commit policy.
8. Draft reuse map, when prior material exists (next section, with rule 7p, `guidelines/rules/7p-derivation.md`, carrying the per-page mechanics): per source file, a reuse verdict, symbol spot-check results, defect classes with counts, and section-to-page mining pointers, plus an enhancement backlog for already-written pages.

## Deriving from prior drafts and pages

When earlier-generation drafts or prior revisions exist for topics in the catalog, mine them instead of ignoring them, under these rules (rule 7p, `guidelines/rules/7p-derivation.md`, carries the per-page mechanics):

1. Map first, read once. Spawn research agents to read the draft corpus once and record a reuse map in the plan file: for each draft, a verdict (backbone-reusable, mine-sections-only, or ignore), symbol spot-check results against the documented tree, its defect classes with counts (banned wording, stale symbol names, non-verbatim excerpts), and pointers from draft sections to the catalog pages they feed. All later work consults the map, not the corpus.
2. Reuse structure, re-verify everything. A draft may contribute its skeleton, section ordering, tables, and figures. Every symbol, line number, code excerpt, and factual claim taken from a draft is re-verified against the on-disk tree at the documented version before it lands. Treat drafts as unverified claims with good structure; the staleness class that survives spot checks is the silently renamed symbol, so re-find each symbol rather than trusting name continuity.
3. Extend to standard. Reused sections are extended to the definition-plus-usage depth, full enumerations, and lifecycle coverage of the depth rules in `guidelines/reference/measured-criteria.md`. A reused page that stays at draft depth is not done.
4. Scrub to the rules. Sweep reused prose for every Gate A class (`guidelines/rules/3a-gate-a.md`; drafts predate some rules; branch-metaphor "arm" and label-colon idioms cluster in them), add or correct 7l provenance comments, and rebuild OTHER SOURCES per 7n.
5. Collect across drafts. One catalog page may assemble sections mined from several drafts; the boundary rules decide what belongs where.
6. Disposition, not disappearance. Every source catalog entry, DETAILS section, behavior, enumeration, figure, and reference gets a 7p disposition (kept, merged, or cut with its reason). Cuts shrink the derived page's catalog and scope statement in the same change and are recorded in the plan file so the orchestrator or the user can veto them; the derived page then passes the Gate B parity audit like a fresh one.

## Inventory brief (planning step 2)

One brief per area; fill the brackets. Dispatch all areas in parallel as read-only agents. Model tier: mid-tier is acceptable; the deliverable is anchored facts, not judgment. The agent's final message is the digest itself, recorded verbatim in the plan file's Inventory findings section.

```
Inventory the <area name> area of the <subsystem> subsystem for a
documentation campaign. Read-only research; do not write or edit any file.

Tree: <path>, version <tag>. Search with semcode (find_type, find_function,
find_callers, grep_functions) plus Grep and Read, over: <kernel_paths
subset for this area>. Index line numbers are hints; confirm on disk
before reporting a location.

Return a COMPACT digest (a report of anchored facts, not prose chapters):
1. Core structs of the area: each with its field groups, one-line roles,
   and the definition's file:line.
2. API families: entry points, helpers, accessor macros, grouped by
   family, each with file:line and a one-line role.
3. Lifecycle and locking: alloc/init/free paths, the serializing locks,
   refcounting, state fields and their transitions, with file:line anchors.
4. Hard-coded limits: every constant bounding the mechanism, with its
   value and file:line.
5. Version-specific facts: symbols renamed, removed, or newly added at
   this version relative to widely-documented older kernels.
6. Suggested page topics the request does not list, each justified by the
   anchor symbols it would be built around.
Keep every item to one or two lines; the digest lands verbatim in a plan
file. Your final message is the digest itself, nothing else.
```

## Plan-review brief (planning step 6)

Dispatch after the catalog and boundary rules exist, to a fresh agent that took no part in writing them. Model tier: strong; this is judgment work over the whole catalog. The reviewer returns a numbered amendment list and never rewrites the plan; the orchestrator applies the amendments it accepts and records the outcome. On death, resume the same agent and ask for the amendments found so far.

```
Adversarially review this documentation-campaign plan for <subsystem
area>. You are attacking the catalog, not the prose. Input: the plan file
at <path> (context, inventory digests, catalog, boundary rules, batch
order). Tree for spot checks: <path>, version <tag>.

Hunt for, and propose concrete fixes with one-line justifications:
1. Coverage gaps: topics present in the inventory digests or the user
   request but absent from both the catalog and the fold-in list.
2. Duplicated ownership: sibling pages whose scope statements would force
   the same walkthrough twice; propose the boundary statement and seam
   symbol, or a merge.
3. Wrong granularity: rows whose scope exceeds one page's material
   (propose the split line) and rows too thin to stand alone (propose the
   merge target).
4. Ordering defects: pages batched before the pages that explain their
   prerequisites.
5. Anchor errors: scope-statement symbols that do not exist at the
   documented version (spot-check against the tree).

Return a numbered amendment list (merge / split / rescope / reorder /
fold-in), each naming the affected rows. Do not rewrite the plan yourself.
```
