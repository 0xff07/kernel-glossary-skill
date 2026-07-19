# Pass plan: campaign planning (multi-page work only)

Purpose: turn a multi-page request into a user-approved, durable campaign plan that survives context loss and session interruption.
Inputs: the request (a prompt file or the conversation) and the documented tree.
Outputs: the committed campaign spec at `campaigns/<campaign>.md` (structured per "The campaign spec's structure" below) plus the machine-local workspace `progress/<campaign>/` (run log and dossiers), and the approved plan, complete per the checklist below, with the user checkpoint recorded in the spec.
Run by: the orchestrator itself (or the human planner), never a dispatchable sub-agent — catalog design is the load-bearing judgment of the campaign. The planner dispatches read-only inventory agents and a plan-review agent (briefs at the end of this file) and makes every catalog decision itself from their outputs. In single-agent mode, the same agent runs this as its first pass for any multi-page task, under the same methodology.
Next: batched writer → fixer production per SKILL.md ("Modes"); certification per the verify campaign in `guidelines/passes/04-verify.md`.

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

The numbered passes define a single page; this pass defines the set. It is the workflow that produced the sample pages under `guidelines/reference/samples/`, written here in subsystem-independent terms; substitute any subsystem's `kernel_paths`, structures, and syscall surface for the mm examples.

## Plan before generating

A campaign starts with a plan the user approves, kept in a durable, committed campaign spec (`campaigns/<campaign>.md`) — the campaign's specification and one of the skill's three artifacts (SKILL.md, "The three artifacts and the three states"); execution events never land in it. The moment planning starts, choose the campaign's unique short name (collision-check both `campaigns/` and `progress/`) and create its workspace per SKILL.md: the spec at `campaigns/<campaign>.md` and the machine-local workspace `progress/<campaign>/` beside it, holding the run log and every dossier and agent intermediate of this campaign. (Claude Code's plan mode provides a plan buffer of its own; the durable copy is still `campaigns/<campaign>.md`.) Treat the spec as the single source of truth for everything durable: every phase below writes its output into the spec, and nothing load-bearing stays only in conversation, in agent transcripts, or in the run log — the log records the planning run's events, the spec records the plan. The spec must be machine-portable: no absolute paths and no local-environment information anywhere in it (tree-relative and skill-relative paths only); sub-agent briefs get absolute paths at dispatch time, composed from the spec plus the local environment. Existing campaigns constrain only the name choice, and nothing inside another campaign's workspace is read unless the user explicitly asks. `guidelines/reference/samples/plan-drm-campaign.md` is the frozen plan file of a real campaign (DRM/KMS) from the previous spec-plus-log layout: imitate its section shapes for the spec, with one reinterpretation — its Status section, reduced to generic entry shapes with placeholders, now teaches the form of the machine-local run log (`progress/<campaign>/log.md`), not a spec section. Read it once before planning a campaign for any subsystem rather than inventing new shapes.

Build the plan in this order:

1. Extract the request's constraints before touching the tree. From the request (a prompt file or the conversation), record verbatim into the campaign spec's Context and Scope sections: the documented tree with its version tag and commit pin, the architecture scope, the granularity preference, the emphasis areas the request stresses (lifecycle, state transitions, hard limits, callback semantics), any wording bans or mandatory tools, and the topic list itself. Note where the request is explicitly incomplete ("this list is rough", a blank bullet, an area with no bullets); each such gap is a curation obligation, never an omission to mirror.
2. Inventory with parallel read-only agents, one per major area. Split the topic into three to six areas along the request's own headings and dispatch one read-only research agent per area, in parallel (read-only inventory agents are safe to parallelize; writers are not). Each brief follows the inventory template at the end of this file: the area, the `kernel_paths` subset to search, the documented tree and version, the toolset (semcode `find_type`, `find_function`, `find_callers`, `grep_functions`, plus Grep and Read), and the ten digest deliverables. Demand a COMPACT digest; a compact report survives agent deaths and resumes better than prose chapters, and it lands verbatim in the campaign spec. When an inventory agent dies (rate limit, transient API error), resume that same agent and ask for the compact report of what it has so far instead of restarting the research; spawn a fresh agent only after resuming fails twice. When the subsystem is large or the request stresses observability or asynchrony, add one or two dedicated whole-subsystem sweep areas (one for tracing and debug infrastructure, one for async/deferred designs) on top of the per-area agents — a sweep agent enumerates its dimension across the subsystem's full kernel_paths, while the per-area items 7-10 stay scoped to each area's paths; otherwise the per-area items suffice.
3. Record the digests in the campaign spec, one Inventory findings subsection per area, before any catalog work — digests are specification (writers consume their drift ledgers), not runtime. Treat every line number in a digest as a hint to re-verify at write time, never as a citation; semcode indexes can lag the tree, and the on-disk source at the documented version is always ground truth. Give the version-specific renames and removals their own prominence; they are the facts that keep pages version-correct.
4. Curate the catalog yourself; do not delegate it. Catalog design is the load-bearing judgment of the campaign, and the orchestrator (or the human planner) makes it from the digests. Map every bullet of the request to one or more catalog rows; curate gap-fill rows for topics the digests surfaced that the request missed; and for every suggested topic that does NOT get a page, record a fold-in adjudication in the spec naming the page that absorbs it (the fold-in list prevents re-litigating scope later). Each catalog row carries (a) the output path `docs/<dir>/<group>/<slug>.md`, (b) a scope statement naming the anchor symbols the page is built around, each with a file:line hint from the digest, and (c) a tag recording whether the row was explicitly requested or curated. Prefer fine granularity: one mechanism, one page; a request bullet that mixes kinds of page (the object itself, its ops structure, the syscalls that drive it) becomes multiple groups, and a "walkthrough" bullet becomes an overview row plus an algorithm row. Choose the directory organization at the same time (two levels, `docs/<dir>/<group>/`, matching the house layout) and state its rationale in the file.
5. Write the boundary rules. Self-contained pages overlap by design, so for every cluster of sibling rows write one boundary statement that fixes each page's mission. The useful form names the seam symbol: "page A owns the syscall surface and treats the X machinery as a black box; page B owns X's object pipeline; page C owns the physical teardown; helper Y at file:line is the seam where A's coverage ends and B's opens". These statements go into the campaign spec and later verbatim into each writer brief, so siblings recap each other in at most one short paragraph instead of duplicating walkthroughs.
6. Have the catalog adversarially reviewed by a fresh agent. Dispatch a plan-review agent (brief template at the end of this file) whose only job is to attack the catalog: coverage gaps against the digests, duplicated ownership, wrong granularity, ordering defects, anchor symbols absent at the documented version. Apply the amendments you accept and record the outcome in the campaign spec; the campaign that produced the sample pages took two merges, two splits, six scope amendments, four new fold-ins, and its boundary statements from this review. A catalog nobody attacked ships its blind spots.
7. Order the batches foundational-to-derived: encodings and counters before the objects that hold them, objects before the tree/list machinery that indexes them, machinery before the syscalls that drive it, core mechanisms before driver instances. Split the catalog into batches of about five pages. A batch is the RECOMMENDED slice a user invokes and the unit of dispatch and checkpointing within a run (SKILL.md "Modes"); it is advice to the invoker, not a state machine the campaign executes on its own.
8. Checkpoint with the user before generating anything. Ask only the genuine scope questions, each with two to four concrete options (include a supporting construct group or not; cover a full syscall surface or a subset), plus one standing question every campaign carries: the verification cadence — when the verify campaign (`guidelines/passes/04-verify.md`) should run for this catalog (after the first batch for calibration, at campaign end, both, or only on demand). Present the final catalog and directory layout, and get an explicit go. The go approves the CATALOG; it does not start generation — execution happens only through user-invoked slices (SKILL.md, "The three artifacts and the three states"). Record the questions, the answers (the cadence decision lands in Scope decisions), and every later amendment (priority reorders, pipeline changes, new bans) in the spec's dated amendments at the moment it arrives; amendments supersede the original order silently otherwise, and a superseded ordering stays in the spec marked as reference.

A plan is complete when every item below holds; confirm each before presenting it:

- The Context section records the campaign short name, the spec's own path (`campaigns/<campaign>.md`), and the workspace directory (`progress/<campaign>/`).
- The spec is machine-portable: no absolute paths and no local-environment information anywhere in it; a grep for local path fragments comes back empty.
- The re-entry contract is present: the standing section telling a cold executor what to do first (confirm the tree pin, derive state from the catalog-vs-`docs/` diff, create or reuse the local workspace, execute only the invoked slice under the overwrite guard, promote durable findings into spec amendments).
- Every bullet of the request maps to at least one catalog row or one recorded fold-in, and blank or vague bullets became curated rows.
- Every catalog row has its output path, a scope statement with at least one anchor symbol carrying a file:line hint, and a requested-or-curated tag.
- The catalog states the projected page total and the tag census (how many requested, how many curated).
- Every sibling cluster has a boundary statement naming its seam symbol.
- The fold-in list records every absorbed topic and its absorbing page.
- One inventory digest per area is in the file, including the version-specific renames and removals, and items 7-10 (tracing integration, debug printing, async/deferred/lazy processing, subsystem debugging infrastructure), each populated or closed with a verified negative.
- The batch order is foundational-to-derived in batches of about five, labeled as the recommended slicing, and the write-time cautions (line numbers are hints, with the known drift examples found so far) are recorded.
- The adversarial review ran and its accepted amendments are recorded.
- The user checkpoint happened: the questions, the decisions (including the verification cadence), and the explicit go are in the file.
- The save and commit policy is stated (where pages land, no navigation-file edits, no git commits without a user go).

The campaign spec is the campaign's durable memory: inventory digests, the catalog, boundary rules, dated amendments, and the draft-reuse map. Execution history is deliberately NOT in it: run events live in each machine's run log, per-page pipeline states live only there, and campaign progress is derived — the catalog is the checklist, `docs/` is the state. After any interruption, the spec plus the pages on disk are sufficient to continue on any machine without redoing research; this machine's run log and dossiers add crash recovery for in-flight pages, and lessons that settle adjudications reach the 7r registry through the user.

## The campaign spec's structure

`guidelines/reference/samples/plan-drm-campaign.md` predates this layout (it is a spec-plus-log hybrid); its sections other than Status remain the worked example for a conforming spec (the nesting may vary, the presence may not), and its Status section — reduced to generic entry shapes with placeholders — now teaches the entry shapes of the machine-local run log (`progress/<campaign>/log.md`), which is where such entries land today. A few guideline-path references inside it predate the current guidelines layout — where a sample and a rule disagree, the rule governs.

A conforming spec carries these elements, and no execution log:

1. Context: what was asked, where the requirements come from, the campaign short name with the spec's path (`campaigns/<campaign>.md`) and the workspace directory (`progress/<campaign>/`), the documented tree with its version tag and commit pin, what is explicitly not an input, the output root, and the portability rule (no machine-specific information; how a resuming machine gets absolute paths).
2. Re-entry contract: the standing instructions to a cold executor — confirm the tree pin (and the Elixir tag) before anything else; derive campaign state as the catalog-vs-`docs/` diff; create or reuse `progress/<campaign>/`; execute only the slice the invoker named, under the overwrite guard; record run events in the local log; promote anything durable into this spec as a dated amendment (or surface it for 7r).
3. Scope decisions: the user-confirmed choices, numbered, including the verification cadence decision from the checkpoint.
4. Inventory findings: one compact digest per area, from the inventory agents, including the version-specific renames and removals and the items 7-10 enumerations (populated or verified-negative).
5. Directory organization: the group layout with its rationale.
6. Page catalog: one table per group with columns page | scope (anchor symbols) | tag, followed by the fold-in adjudications, the projected total with tag census, and the overlap boundary rules (one statement per sibling cluster, seam symbols named).
7. Execution and verification: the per-page procedure and its campaign-specific deltas, project-specific writing bans from the request, gate ownership for the pipeline, write-time rules (line numbers are hints, with the known-drift list), user amendments (dated, explicitly superseding what they replace), the recommended batch order (current, plus any superseded order kept for reference), and the save/commit policy.
8. Draft reuse map, when prior material exists (next section, with rule 7p, `guidelines/rules/rules.md` (7p), carrying the per-page mechanics): per source file, a reuse verdict, symbol spot-check results, defect classes with counts, and section-to-page mining pointers, plus an enhancement backlog for already-written pages.

Per-page pipeline states (WRITTEN → LINTED → CERTIFIED) are recorded only in run logs, never in the spec; a verify run stamps CERTIFIED in its own log, and a durable certification record exists only on an explicit user go (SKILL.md, "The three artifacts and the three states").

## Deriving from prior drafts and pages

When earlier-generation drafts or prior revisions exist for topics in the catalog, mine them instead of ignoring them, under these rules (rule 7p, `guidelines/rules/rules.md` (7p), carries the per-page mechanics):

1. Map first, read once. Spawn research agents to read the draft corpus once and record a reuse map in the campaign spec: for each draft, a verdict (backbone-reusable, mine-sections-only, or ignore), symbol spot-check results against the documented tree, its defect classes with counts (banned wording, stale symbol names, non-verbatim excerpts), and pointers from draft sections to the catalog pages they feed. All later work consults the map, not the corpus.
2. Reuse structure, re-verify everything. A draft may contribute its skeleton, section ordering, tables, and figures. Every symbol, line number, code excerpt, and factual claim taken from a draft is re-verified against the on-disk tree at the documented version before it lands. Treat drafts as unverified claims with good structure; the staleness class that survives spot checks is the silently renamed symbol, so re-find each symbol rather than trusting name continuity.
3. Extend to standard. Reused sections are extended to the definition-plus-usage depth, full enumerations, and lifecycle coverage of the depth rules in `guidelines/reference/measured-criteria.md`. A reused page that stays at draft depth is not done.
4. Scrub to the rules. Sweep reused prose for every Gate A class (`guidelines/rules/rules.md` (3a); drafts predate some rules; branch-metaphor "arm" and label-colon idioms cluster in them), add or correct 7l provenance comments, and rebuild OTHER SOURCES per 7n.
5. Collect across drafts. One catalog page may assemble sections mined from several drafts; the boundary rules decide what belongs where.
6. Disposition, not disappearance. Every source catalog entry, DETAILS section, behavior, enumeration, figure, and reference gets a 7p disposition (kept, merged, or cut with its reason). Cuts shrink the derived page's catalog and scope statement in the same change and are recorded in the campaign spec so the orchestrator or the user can veto them; the derived page then passes the Gate B parity audit like a fresh one.

## Repair campaigns (seeded by a verify run)

A repair campaign is an ordinary write campaign whose catalog comes ready-made: the confirmed factual findings a verify campaign recorded in its run log and surfaced to the user (`guidelines/passes/04-verify.md`). There is no separate plan format and no separate artifact — planning collapses to lifting those findings into a catalog (a spec at `campaigns/<name>.md` like any other), one row per page to repair, carrying each finding with its evidence and, where the verifier derived one, its exact fix specification. The tree pin, the boundary statements, and the project-specific bans come from the parent campaign spec.

Writers in a repair campaign run in the derivation form (rule 7p, "Deriving from prior drafts and pages" above): the source is the current page plus its finding list, every touched claim is re-verified on disk, and every cut is reported. The page's dossier, where one survives, is the starting evidence — never proof.

## Inventory brief (planning step 2)

One brief per area; fill the brackets. Dispatch all areas in parallel as read-only agents. Model tier: mid-tier is acceptable; the deliverable is anchored facts, not judgment. The agent's final message is the digest itself, recorded verbatim in the campaign spec's Inventory findings section. Instruct agents to report every location tree-relative (never absolute), so the digest lands portable.

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
7. Tracing integration: everything in the area's paths that plugs into the
   kernel's general tracing infrastructure — tracepoint definitions
   (TRACE_EVENT, DECLARE_EVENT_CLASS/DEFINE_EVENT, bare DECLARE_TRACE) and
   their CREATE_TRACE_POINTS instantiation sites; every trace_*() call
   site; probes registered on other subsystems' tracepoints
   (register_trace_*/tracepoint_probe_register); private ftrace instances
   (trace_array API); tracers, exporters, and relay-based trace ABIs
   registered with the tracing core; trace_printk leftovers; and the seams
   where this area's code fires an adjacent subsystem's events, cited at
   both ends. Per class: enumerate with file:line, or a verified negative
   with the search evidence.
8. Debug and diagnostic printing: the mechanisms in play (subsystem print
   macros, dev_dbg/pr_debug and their dynamic-debug interplay, WARN/BUG
   usage), per-file counts for the heavy hitters, every control knob
   (Kconfig, module params, boot params) with file:line, and the
   load-bearing sites. Mechanisms-and-counts altitude: exhaustive per-flow
   call-site listing is write-time work, not digest work; assertion
   families (VM_BUG_ON-class) are a mechanism entry with counts, never a
   site enumeration.
9. Asynchronous, deferred, or lazy processing: every workqueue (name
   string, flags, creation site), work item, timer and delayed work,
   irq_work, tasklet, kthread, RCU/SRCU deferral, completion handoff,
   async_schedule, task_work, and notifier chain (noting synchronous
   dispatch) in the area — each with queuing site, execution context, and
   handler at file:line — plus lazy or deferred init/enumeration designs.
   Absent primitive classes and fully synchronous paths get verified
   negatives with evidence.
10. Subsystem-specific debugging infrastructure: dedicated debugfs, sysfs,
    and procfs diagnostic surfaces; debug chardevs and ioctl interfaces;
    error- and fault-injection facilities; in-kernel debuggers, dump, or
    replay facilities; and in-tree userspace tooling — each with file:line
    and the Kconfig option that gates it. Scope: only facilities this
    subsystem itself declares (its own Kconfig files and sources);
    kernel-wide instrumentation (KASAN, KCSAN, lockdep, DEBUG_OBJECTS and
    kin) is out of scope unless the documented subsystem implements it.
    Enumerated facilities that transform code paths (KASAN-class) are
    resolved by catalog decision — dedicated rows or a recorded fold-out —
    never absorbed as per-page documentation duty.
Items 7-10 are inventory devices: they demand enumeration (or verified
negatives) at plan time and gate-naming at write time. They never oblige a
page to document config-conditional code-path variants; pages document the
default build and name a config gate in one sentence where a cited path
sits behind one.
Keep every enumerated entry to one or two lines; the digest lands verbatim
in the campaign spec. Your final message is the digest itself, nothing else.
```

## Plan-review brief (planning step 6)

Dispatch after the catalog and boundary rules exist, to a fresh agent that took no part in writing them. Model tier: strong; this is judgment work over the whole catalog. The reviewer returns a numbered amendment list and never rewrites the plan; the orchestrator applies the amendments it accepts and records the outcome. On death, resume the same agent and ask for the amendments found so far.

```
Adversarially review this documentation-campaign plan for <subsystem
area>. You are attacking the catalog, not the prose. Input: the campaign spec
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
