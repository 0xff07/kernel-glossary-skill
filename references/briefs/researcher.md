# The researcher brief

The researcher brief, an explicit opt-in when research fans out ahead of writing; the researcher writes only the worksheet and reports a two-line summary:

```
Research the page <page slug> for the <subsystem> knowledge base; do not
write the page.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order:
1. <SKILL_DIR>/SKILL.md, the prep and research passes.
2. <SKILL_DIR>/guidelines/kernel.md [sources], the source rules.
3. <SKILL_DIR>/guidelines/worksheet.md, your deliverable's format.
4. <SKILL_DIR>/guidelines/subsystems.md, the page's subsystem entry only.

MISSION. <Scope statement from the catalog row, naming the anchor symbols
with file:line hints, and the boundary rules for this page's cluster.>

FACTS. Documented tree: <path>, version <tag>, commit <sha>.
Architecture scope: <arch>. Index line numbers are hints; confirm on disk
before recording a location.

Write the worksheet to <SKILL_DIR>/progress/<campaign>/<dir>/<group>/<slug>.worksheet.md
(mirroring docs/<dir>/<group>/<slug>.md), and write nowhere else in progress/, which
belongs to other campaigns too.
Your final message is a two-line summary (symbol count, enumerations
recorded, open gaps), not the worksheet text.
```
