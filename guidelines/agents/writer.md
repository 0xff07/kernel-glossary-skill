# Writer agent

Role: researches and writes one complete page (passes 01 and 02) in the campaign pipeline. The writer follows every rule while composing but does not run the gate loops afterward; a separate lint stage with fresh context does that better (`guidelines/campaign/pipeline.md`).
Model tier: the strongest available model; page writing needs research judgment, prose discipline, and figure quality.
Mandatory reading: carried inside the brief below, as absolute paths.
Report: a short final message, never the page text (format in the brief).
Death/resume: resume the same agent first ("do not redo the research; write the page now from what you have"); if repeated resumes fail, a fresh agent starts from the page's dossier plus the plan file.

## Writer brief template

Fill the brackets from the plan file. The brief names the files that carry every house rule, as absolute paths; a writer must never have to guess where a rule lives.

```
Write the page <output path> for the <subsystem> knowledge base.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>

MANDATORY READING, in order, before any research or writing. Every house
rule lives in these files and nothing is pasted into this brief, so a
skipped read is a skipped rule set.
1. <SKILL_DIR>/guidelines/rules/7r-adjudications.md — the settled
   adjudications registry. First action. Apply it as written; never
   reword an exempt construct.
2. <SKILL_DIR>/guidelines/passes/00-prep.md — template and samples
   doctrine (samples calibrate form only, never facts).
3. <SKILL_DIR>/guidelines/passes/01-research.md and
   <SKILL_DIR>/guidelines/passes/dossier.md — the research procedure and
   the dossier you keep at <SKILL_DIR>/progress/<campaign>/<slug>.dossier.md.
4. <SKILL_DIR>/guidelines/passes/02-write.md — the composition procedure
   and the full writer reading list (the rules via
   <SKILL_DIR>/guidelines/rules/INDEX.md, the diagram rules under
   <SKILL_DIR>/guidelines/diagrams/, the depth rules in
   <SKILL_DIR>/guidelines/reference/measured-criteria.md). Read
   everything that list names.
5. <SKILL_DIR>/guidelines/reference/subsystems.md — read only the page's subsystem entry.

MISSION. <Scope statement from the catalog row, naming the anchor symbols
with file:line hints.> <The boundary rules for this page's cluster: what
this page owns, what each sibling page owns, the seam symbols. Recap of
sibling territory is limited to one short paragraph.>

CAMPAIGN FACTS (carried by this brief because no guideline file can):
- Documented tree: <path>, version <tag>, commit <sha>. Every fact, line
  number, and excerpt is verified against the on-disk tree before it
  lands; semcode results and the dossier are hints, the disk is ground
  truth. Architecture scope: <arch>. State CONFIG assumptions in the page
  where behavior depends on them: <list>.
- Section 6 heading for this subsystem: <value or "omit">.
- Project-specific bans and amendments from the plan file: <list, or
  "none">.
- <If an existing draft or prior page feeds this one: the source file(s)
  and sections to mine, the known source defects from the reuse map; rule
  7p applies (inventory the source, give every item a kept/merged/cut
  disposition, report every cut and shrink the catalog and scope
  statement with it). Otherwise omit this bullet.>

DIRECTIVES.
- Run the research pass yourself (pass 01), keeping the dossier current
  as you research; it is the recovery point if you die mid-page.
- Everything you persist besides the page itself (the dossier, any notes
  or helper output) goes under <SKILL_DIR>/progress/<campaign>/, named
  <slug>.<purpose>.<ext>; write nowhere else in progress/, which belongs
  to other runs too.
- Enumerate call-site populations before writing any prose that counts or
  characterizes them (7o).
- Do NOT run the Gate A/B verification loops after writing; a separate
  lint stage does that (the gates are deliberately absent from your
  reading list).
- Write the file to <output path>. Your final message is a short report
  (sections written, catalog symbol count, call-site counts you verified,
  the 7r ruling count you applied as proof of the registry read, anything
  you could not verify), not the page text.
```
