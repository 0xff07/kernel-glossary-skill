# Planning and running a campaign

A campaign is a documentation set of tens of pages. It starts with a plan the user approves, kept in a committed, machine-portable spec at `campaigns/<campaign>.md`, and it runs in user-invoked slices whose state is derived from the catalog against `docs/`. The orchestrator plans; catalog design is the load-bearing judgment and is never delegated.

## Planning [planning]

1. [planning.name] Choose the campaign's short name (one to three lowercase hyphenated words naming the area), check it against `campaigns/` and `progress/`, and create the spec and the workspace `progress/<campaign>/` the moment planning starts.
2. [planning.constraints] Extract the request's constraints before touching the tree, verbatim into the spec's Context and Scope: the tree with its version tag and commit pin, the architecture scope, the granularity preference, the emphasis areas, any wording bans or mandatory tools, and the topic list, with every gap the request admits noted as work.
3. [planning.inventory] Inventory with parallel read-only agents, one per area, three to six areas along the request's own headings, each with the inventory brief below. Record every digest verbatim in the spec, one Inventory findings subsection per area; every line number in a digest is a hint to re-verify at write time.
4. [planning.catalog] Curate the catalog yourself. Map every bullet of the request to one or more rows, curate gap-fill rows for what the digests surfaced, and record a fold-in adjudication for every suggested topic that gets no page. Each row carries its output path `docs/<dir>/<group>/<slug>.md`, a scope statement naming its anchor symbols with file:line hints, and a tag, requested or curated.
5. [planning.boundaries] Write one boundary statement per sibling cluster, naming the seam symbol. A boundary is a floor, never a fence: it says what a page must cover exhaustively (the definition excerpt, the lifecycle, the locking, the enumerated call sites), and any other page reaches the same symbol to whatever depth its own narrative needs, cataloging none of it (kernel.md [sections.coverage-form]).
6. [planning.review] Have the catalog adversarially reviewed by a fresh agent with the review brief below, apply the amendments you accept, and record the outcome.
7. [planning.batches] Order the batches foundational to derived: encodings and counters before the objects that hold them, objects before the machinery that indexes them, machinery before the syscalls that drive it, core mechanisms before driver instances, in batches of about five pages. A batch is the recommended slice, advice to the invoker, never a state machine.
8. [planning.checkpoint] Checkpoint with the user: only the genuine scope questions, each with two to four concrete options, then the final catalog and layout, then an explicit go. The go approves the catalog and starts nothing; execution happens only through invoked slices.

A plan is complete when the spec records its own name, path and workspace; carries no absolute path or local detail; carries the re-entry contract; maps every request bullet to a row or a fold-in; gives every row its path, anchor symbols and tag; states the projected total and tag census; names a seam symbol per cluster; records the fold-in list, the digests with their version-specific renames and the four enumerations (tracing integration, debug printing, deferred processing, debugging infrastructure) populated or verified negative, the batch order with the write-time cautions, the review's accepted amendments, the user checkpoint with its decisions, and the save and commit policy.

## The spec's structure [spec]

1. [spec.context] Context: what was asked and where the requirements come from, the short name with the spec's path and the workspace, the tree with tag and commit, what is explicitly not an input, the output root, the portability rule.
2. [spec.re-entry] Re-entry contract: confirm the tree pin and the Elixir tag first; derive state as the catalog-versus-`docs/` diff, which says what exists and never what is finished (SKILL.md, the two states); create or reuse the workspace; execute only the invoked slice, each page under its operation, a create under the overwrite guard or a resume from the digest its brief names; record run events in the local log; promote anything durable here as a dated errata entry or surface it to the user for a ruling. The per-page procedure is named as SKILL.md's passes and the guideline sections by slug, never as a path that only git history holds, so the spec stays executable on any machine after the skill changes shape.
3. [spec.scope-decisions] Scope decisions, numbered, as the user confirmed them.
4. [spec.inventory] Inventory findings, one compact digest per area.
5. [spec.directories] Directory organization with its rationale.
6. [spec.catalog] Page catalog: one table per group (page, scope with anchor symbols, tag), the fold-in adjudications, the projected total with tag census, and the boundary rules.
7. [spec.execution] Execution and verification: the per-page procedure and its campaign-specific deltas, project-specific bans from the request, which pass owns each check, write-time rules with the known drift list, dated errata that say what they supersede, the recommended batch order, and the save and commit policy.
8. [spec.draft-reuse] Draft reuse map, when prior material exists: per source file a verdict (backbone-reusable, mine-sections-only, ignore), symbol spot checks, defect classes with counts, and section-to-page mining pointers; a superseded corpus is archived under a tag and cited by tag and path.

Per-page states are recorded only in run logs, never in the spec. A lesson that settles an adjudication is surfaced to the user, who alone makes it a ruling.

## Deriving from drafts and from removed pages [deriving]

1. [deriving.map-first] Map first, read once: research agents read the draft corpus once and record the reuse map; later work consults the map.
2. [deriving.re-verify] Reuse structure, re-verify everything: a draft may contribute skeleton, ordering, tables and figures, and every symbol, line number, excerpt and claim taken from it is re-found on disk, because the renamed symbol is the staleness that survives spot checks.
3. [deriving.extend] Extend to standard: definition plus usage, full enumerations, lifecycle coverage. Scrub with every ban pattern, add or correct provenance comments, rebuild OTHER SOURCES from trailers.
4. [deriving.dispositions] Every source entry, section, behavior, enumeration, figure and reference gets a disposition; cuts shrink the derived page's catalog and scope in the same change, are recorded in the spec, and the page passes the parity audit like a fresh one.
5. [deriving.rewrite] A committed page the user directs to be rewritten is prior material like any draft. The user removes it in a commit of its own; the rewrite is then a create of the same catalog row, under the overwrite guard like any create, whose brief names the removed revision (`git show <commit>:docs/<dir>/<group>/<slug>.md`) as the derivation source together with the findings that motivated the rewrite. Items 1 to 4 govern what may be reused and what is re-found on disk. There is no repair operation and no repair campaign: a page is created, or resumed from the digest a dead writer left; no writer operation writes over a page on disk, and the check pass's exactly specified fix is the one edit in place.

## Slices and the run log [slices]

1. [slices.one-batch] A slice is one batch: writers dispatched together, one per page, then the check pass per page, then the run closed with its log updated. Before dispatch, apply the overwrite guard to every page the slice creates; a resume names its starting digest in the brief instead, the writer rebuilds the page in its scratch directory, and the orchestrator re-checks the digest and moves the rebuilt page into place; a page whose digest no longer matches is surfaced, never written over.
2. [slices.log] After every completed page and at the checkpoint, append to `progress/<campaign>/log.md` the page state, statistics, adjudications and agent events. Anything durable goes to the spec as a dated errata entry; the log dies with the machine by design.
3. [slices.permissions] Sub-agents need Write permission before dispatch; without it, process sequentially rather than fail and retry.

## The briefs [briefs]

The writer brief, filled from the spec with absolute paths composed at dispatch time:

```
Write the page <output path> for the <subsystem> knowledge base.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>
WORKSPACE: <SKILL_DIR>/progress/<campaign>/
OPERATION: <create | resume>; for a resume, the page's starting digest: sha256 <digest>, and the rebuilt page goes to YOUR SCRATCH/<slug>.md; for a create that derives from a removed page, its revision: git show <commit>:<path>, reused under writing.md [facts.derived-pages]
YOUR DOSSIER: <SKILL_DIR>/progress/<campaign>/<dir>/<group>/<slug>.dossier.md (mirroring docs/<dir>/<group>/<slug>.md)
YOUR SCRATCH: <session scratchpad>/<dir>/<group>/<slug>/ (the scratchpad is shared and two pages may share a slug; scratch and a resumed page go only here)

MANDATORY READING, by phase (SKILL.md, "Reading routes"); nothing ahead of its phase:
1. Before research: <SKILL_DIR>/SKILL.md, the passes you run yourself; <SKILL_DIR>/guidelines/kernel.md, what a kernel page is made of; <SKILL_DIR>/guidelines/dossier.md, the dossier you keep, which is the recovery point; the page's entry in <SKILL_DIR>/guidelines/subsystems.md; and the campaign facts below.
2. Before writing: <SKILL_DIR>/guidelines/writing.md whole, every rule the page must meet, composed under from the first sentence; and <SKILL_DIR>/guidelines/template.md.
3. When the page will carry a figure: <SKILL_DIR>/guidelines/figures.md from [drawing] to [patterns], [register-figures] as well when the figure is a register or bitfield, then only the pattern file under <SKILL_DIR>/references/figures/ that the index matches.
4. At QA: <SKILL_DIR>/guidelines/checking.md, the steps you run before reporting done, with python3 <SKILL_DIR>/tools/qa/kg.py check <page> for the mechanical ones.

MISSION. <Scope statement from the catalog row, naming the anchor symbols with file:line hints.> <The boundary rules for this page's cluster: what this page owns, what each sibling owns, the seam symbols, which sibling pages exist on disk.> Line numbers are hints; the disk is ground truth, and a hint you cannot reproduce is reported, never written around.

CAMPAIGN FACTS:
- Documented tree: <path>, version <tag>, commit <sha>. Architecture scope: <arch>. CONFIG assumptions to state where behavior depends on them: <list>.
- Section-six heading: <value or "omit">.
- Project-specific bans and errata from the campaign spec: <list, or "none">.
- <Derivation source and known defects, if an existing page feeds this one. Otherwise omit.>

DIRECTIVES.
- At most about 25 KB of output per command; a persisted output is read by slice only.
- Under the skill checkout the only files you write are the page and your dossier, nowhere else in progress/ and never in guidelines/ or campaigns/; scratch goes only to YOUR SCRATCH. No git operation that changes state.
- A create: if the output path exists when you are about to write, stop and report. A resume: stop and report if the page on disk is not at the starting digest the brief names; otherwise write the rebuilt page to YOUR SCRATCH/<slug>.md, never over the page on disk, and report its digest, and the orchestrator moves it into place.
- Enumerate call-site populations before any prose that counts or characterizes them.
- The page states results and their scope, never the search; the search stays in the dossier.
- Keep the parity checklist as you compose; fill or de-catalog every row.
- Run the QA steps after the page is complete, fix what they find before reporting, and persist the LINKS table with every kind / reason cell filled and the EVIDENCE and LINT sections into the dossier, ending EVIDENCE with `page sha256: <digest>` of the page the evidence describes.
- LINT ends with your verdicts. The `LINTED <date> page sha256: <digest> qa sha256: <qa-digest>` record and the `check pass:` line are the check pass's, never yours; a writer that writes either is reported.
- Final message: the lead verbatim; sections written; catalog count and parity outcome (de-catalogings with reasons); QA results (units verified, anchors confirmed, counts with second bases, the generator summary notes, the lead and SUMMARY counts and sentence roles, sweep candidates per class with dispositions, the rhythm outliers with dispositions, the introduction summary); the exemptions applied; any hint that did not reproduce; any claim that is not disk-settleable and how the page scopes it. Not the page text beyond the lead.
```

The researcher brief, an explicit opt-in when research fans out ahead of writing; the researcher writes only the dossier and reports a two-line summary:

```
Research the page <page slug> for the <subsystem> knowledge base; do not
write the page.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order:
1. <SKILL_DIR>/SKILL.md, the prep and research passes.
2. <SKILL_DIR>/guidelines/kernel.md [sources], the source rules.
3. <SKILL_DIR>/guidelines/dossier.md, your deliverable's format.
4. <SKILL_DIR>/guidelines/subsystems.md, the page's subsystem entry only.

MISSION. <Scope statement from the catalog row, naming the anchor symbols
with file:line hints, and the boundary rules for this page's cluster.>

FACTS. Documented tree: <path>, version <tag>, commit <sha>.
Architecture scope: <arch>. Index line numbers are hints; confirm on disk
before recording a location.

Write the dossier to <SKILL_DIR>/progress/<campaign>/<dir>/<group>/<slug>.dossier.md
(mirroring docs/<dir>/<group>/<slug>.md), and write nowhere else in progress/, which
belongs to other campaigns too.
Your final message is a two-line summary (symbol count, enumerations
recorded, open gaps), not the dossier text.
```

The inventory brief, one per area, dispatched in parallel to read-only agents on a mid-tier model; the digest lands verbatim in the spec, every location tree-relative:

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
7. Tracing integration: tracepoint definitions and their instantiation
   sites, every trace_*() call site, probes on other subsystems'
   tracepoints, private ftrace instances, tracers and exporters, and the
   seams where this area fires an adjacent subsystem's events, cited at
   both ends. Per class: enumerate with file:line, or a verified negative.
8. Debug and diagnostic printing: the mechanisms in play, per-file counts
   for the heavy hitters, every control knob (Kconfig, module params, boot
   params) with file:line, and the load-bearing sites; assertion families
   are a mechanism entry with counts, never a site enumeration.
9. Asynchronous, deferred, or lazy processing: every workqueue, work item,
   timer, irq_work, tasklet, kthread, RCU deferral, completion handoff,
   task_work and notifier chain, each with queuing site, execution context
   and handler at file:line, plus lazy or deferred init designs; absent
   classes get verified negatives.
10. Subsystem-specific debugging infrastructure: dedicated debugfs, sysfs
    and procfs surfaces, debug chardevs and ioctls, fault injection, dump
    or replay facilities, in-tree userspace tooling, each with file:line
    and its Kconfig gate; only what this subsystem itself declares.
Items 7-10 are inventory devices: enumerate or verify negative at plan
time, and name gates at write time. Pages document the default build and
name a config gate in one sentence where a cited path sits behind one.
Keep every entry to one or two lines. Your final message is the digest
itself, nothing else.
```

The plan-review brief, dispatched to a fresh strong agent after the catalog and boundaries exist; it returns amendments and never rewrites the plan:

```
Adversarially review this documentation-campaign plan for <subsystem
area>. You are attacking the catalog, not the prose. Input: the campaign spec
at <path> (context, inventory digests, catalog, boundary rules, batch
order). Tree for spot checks: <path>, version <tag>.

Hunt for, and propose concrete fixes with one-line justifications:
1. Coverage gaps: topics in the digests or the request absent from both
   the catalog and the fold-in list.
2. Duplicated ownership: sibling pages whose scope statements would force
   the same walkthrough twice; propose the boundary statement and seam
   symbol, or a merge.
3. Wrong granularity: rows whose scope exceeds one page (propose the split
   line) and rows too thin to stand alone (propose the merge target).
4. Ordering defects: pages batched before the pages that explain their
   prerequisites.
5. Anchor errors: scope-statement symbols that do not exist at the
   documented version.

Return a numbered amendment list (merge / split / rescope / reorder /
fold-in), each naming the affected rows. Do not rewrite the plan yourself.
```
