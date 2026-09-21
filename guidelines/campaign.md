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
3. [deriving.extend] Extend to standard: definition plus usage, full enumerations, lifecycle coverage. Scrub with every sweep pattern of the style table, add or correct provenance comments, carry OTHER SOURCES over verbatim and add your own `### Added by <model>` block with the commit entries the tree's trailers give.
4. [deriving.dispositions] Every source entry, section, behavior, enumeration, figure and reference gets a disposition; cuts shrink the derived page's catalog and scope in the same change, are recorded in the spec, and the page passes the completeness audit like a fresh one.
5. [deriving.rewrite] A committed page the user directs to be rewritten is prior material like any draft. The user removes it in a commit of its own; the rewrite is then a create of the same catalog row, under the overwrite guard like any create, whose brief names the removed revision (`git show <commit>:docs/<dir>/<group>/<slug>.md`) as the derivation source together with the findings that motivated the rewrite. Items 1 to 4 govern what may be reused and what is re-found on disk. There is no repair operation and no repair campaign: a page is created, or resumed from the digest a dead writer left; no writer operation writes over a page on disk, and the check pass's exactly specified fix is the one edit in place.

## Slices and the run log [slices]

1. [slices.one-batch] A slice is one batch: writers dispatched together, one per page, then the check pass per page, then the run closed with its log updated. Before dispatch, apply the overwrite guard to every page the slice creates; a resume names its starting digest in the brief instead, and the writer verifies it against the page on disk before continuing the page there; a page whose digest no longer matches is surfaced, never written over.
2. [slices.log] After every completed page and at the checkpoint, append to `progress/<campaign>/log.md` the page state, statistics, adjudications and agent events. Anything durable goes to the spec as a dated errata entry; the log dies with the machine by design.
3. [slices.permissions] Sub-agents need Write permission before dispatch; without it, process sequentially rather than fail and retry.

## The briefs [briefs]

The four briefs are `references/briefs/`, one file each, filled from the spec with absolute paths composed at dispatch time; a brief is read only by the role that dispatches it, never by a writer.

- `references/briefs/writer.md`: the writer brief, one page end to end; its MISSION carries the catalog row and the cluster's boundary rules verbatim, its CAMPAIGN FACTS the tree, the version, the section-six heading, the bans, the cautions and the errata, and its DIRECTIVES the walkthrough, lifecycle, reading and figure rules the page is written under.
- `references/briefs/researcher.md`: the researcher brief, an explicit opt-in when research fans out ahead of writing; the researcher writes only the worksheet and reports a two-line summary.
- `references/briefs/inventory.md`: the inventory brief, one per area, dispatched in parallel to read-only agents on a mid-tier model; the digest lands verbatim in the spec, every location tree-relative.
- `references/briefs/plan-review.md`: the plan-review brief, dispatched to a fresh strong agent after the catalog and boundaries exist; it returns amendments and never rewrites the plan.
