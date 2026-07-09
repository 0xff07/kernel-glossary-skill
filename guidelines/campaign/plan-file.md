# Plan file structure

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

`guidelines/samples/plan-mm-campaign.md` carries eight top-level sections; a conforming plan file carries the same elements (the nesting may vary, the presence may not):

1. Context: what was asked, where the requirements come from, the documented tree with its version tag and commit pin, what is explicitly not an input, and the output root.
2. Status: a living, dated checklist. Every phase completion, batch result, suspension, correction, and lesson is appended at the moment it happens; a future session resumes from this section plus the pages on disk.
3. Scope decisions: the user-confirmed choices, numbered.
4. Inventory findings: one compact digest per area, from the inventory agents, including the version-specific renames and removals.
5. Directory organization: the group layout with its rationale.
6. Page catalog: one table per group with columns page | scope (anchor symbols) | tag, followed by the fold-in adjudications, the projected total with tag census, and the overlap boundary rules (one statement per sibling cluster, seam symbols named).
7. Execution and verification: the per-page procedure and its campaign-specific deltas, project-specific writing bans from the request, gate ownership for the pipeline, write-time rules (line numbers are hints, with the known-drift list), user amendments (dated, explicitly superseding what they replace), the batch order (current, plus any superseded order kept for reference), and the save/commit policy.
8. Draft reuse map, when prior material exists (rule 7p, `guidelines/rules/7p-derivation.md`, and `guidelines/campaign/draft-reuse.md`): per source file, a reuse verdict, symbol spot-check results, defect classes with counts, and section-to-page mining pointers, plus an enhancement backlog for already-written pages.
