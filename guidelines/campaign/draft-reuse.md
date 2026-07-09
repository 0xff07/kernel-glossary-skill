# Deriving from prior drafts and pages

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

When earlier-generation drafts or prior revisions exist for topics in the catalog, mine them instead of ignoring them, under these rules (rule 7p, `guidelines/rules/7p-derivation.md`, carries the per-page mechanics):

1. Map first, read once. Spawn research agents to read the draft corpus once and record a reuse map in the plan file: for each draft, a verdict (backbone-reusable, mine-sections-only, or ignore), symbol spot-check results against the documented tree, its defect classes with counts (banned wording, stale symbol names, non-verbatim excerpts), and pointers from draft sections to the catalog pages they feed. All later work consults the map, not the corpus.
2. Reuse structure, re-verify everything. A draft may contribute its skeleton, section ordering, tables, and figures. Every symbol, line number, code excerpt, and factual claim taken from a draft is re-verified against the on-disk tree at the documented version before it lands. Treat drafts as unverified claims with good structure; the staleness class that survives spot checks is the silently renamed symbol, so re-find each symbol rather than trusting name continuity.
3. Extend to standard. Reused sections are extended to the definition-plus-usage depth, full enumerations, and lifecycle coverage of the depth rules in `guidelines/reference/measured-criteria.md`. A reused page that stays at draft depth is not done.
4. Scrub to the rules. Sweep reused prose for every Gate A class (`guidelines/gates/gate-a.md`; drafts predate some rules; branch-metaphor "arm" and label-colon idioms cluster in them), add or correct 7l provenance comments, and rebuild OTHER SOURCES per 7n.
5. Collect across drafts. One catalog page may assemble sections mined from several drafts; the boundary rules decide what belongs where.
6. Disposition, not disappearance. Every source catalog entry, DETAILS section, behavior, enumeration, figure, and reference gets a 7p disposition (kept, merged, or cut with its reason). Cuts shrink the derived page's catalog and scope statement in the same change and are recorded in the plan file so the orchestrator or the user can veto them; the derived page then passes the Gate B parity audit like a fresh one.
