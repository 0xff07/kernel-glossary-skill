# Researcher agent (optional)

Role: runs the research pass (`guidelines/passes/01-research.md`) for one page and produces its dossier (`guidelines/passes/dossier.md`) without writing the page. The campaign default is that the writer researches its own page (`guidelines/campaign/pipeline.md`); dispatch dedicated researchers only as an explicit opt-in, when research should fan out ahead of writing (pre-building dossiers for a batch) or when a single agent is stepping the passes one at a time across sessions.
Model tier: strong enough for research judgment; the dossier's search bases and version-drift notes are what the write and lint passes build on.
Writes only the dossier under `progress/`; everything else is read-only.
Report: a two-line summary as the final message, never the dossier text.
Death/resume: resume the same agent and ask it to flush what it has into the dossier; a partially filled dossier with accurate OPEN GAPS is a valid deliverable.

## Researcher brief template

```
Research the page <page slug> for the <subsystem> knowledge base; do not
write the page.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order:
1. <SKILL_DIR>/guidelines/passes/00-prep.md — resolve the parameters;
   skip the sample reading, which is the writer's job.
2. <SKILL_DIR>/guidelines/passes/01-research.md — your procedure.
3. <SKILL_DIR>/guidelines/passes/dossier.md — your deliverable's format.
4. <SKILL_DIR>/guidelines/reference/subsystems.md — read only the page's subsystem entry.

MISSION. <Scope statement from the catalog row, naming the anchor symbols
with file:line hints, and the boundary rules for this page's cluster.>

FACTS. Documented tree: <path>, version <tag>, commit <sha>.
Architecture scope: <arch>. Index line numbers are hints; confirm on disk
before recording a location.

Write the dossier to <SKILL_DIR>/progress/<topic>/<slug>.dossier.md.
Your final message is a two-line summary (symbol count, enumerations
recorded, open gaps), not the dossier text.
```
