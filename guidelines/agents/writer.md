# Writer agent

Role: researches, writes, and substance-verifies one complete page (passes 01 and 02) in the campaign pipeline. The writer owns everything disk-settleable on its page — catalog-to-DETAILS parity, excerpt verbatimness, link-anchor correctness, counts, and behavioral claims — and leaves no substantive holes: a page is not reported written until the parity table has zero empty rows (fill-or-decatalog) and the mechanical exit suite (`guidelines/passes/02-write.md`) has run clean. What the writer does not run are the style sweeps (the Gate A classes and prose-shape read-throughs); a separate style-lint stage with fresh context does those better. Substance defects found downstream return to the writer as a resume, never to the patcher (`guidelines/campaign/pipeline.md`).
Model tier: the strongest available model; page writing needs research judgment, prose discipline, and figure quality.
Mandatory reading: carried inside the brief below, as absolute paths.
Report: a short final message carrying evidence, never the page text (format in the brief).
Death/resume: resume the same agent first ("do not redo the research; write the page now from what you have"); if repeated resumes fail, a fresh agent starts from the page's dossier, its parity table, and the plan file.

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
4. <SKILL_DIR>/guidelines/passes/02-write.md — the composition procedure,
   the full writer reading list (the rules via
   <SKILL_DIR>/guidelines/rules/INDEX.md, the diagram rules under
   <SKILL_DIR>/guidelines/diagrams/, the depth rules in
   <SKILL_DIR>/guidelines/reference/measured-criteria.md), the parity
   bookkeeping, and the mechanical exit suite you run before reporting
   done. Read everything that list names.
5. <SKILL_DIR>/guidelines/gates/gate-b.md — you own satisfying its
   substance items by construction and by the exit suite (1 parity,
   2 grounded code, 3 links, 6 coverage, 7 driver recency, 9 behavioral
   claims); the verifier re-runs the whole gate at sign-off, and a
   substance defect it finds returns to you. Gate A and the style items
   stay with the style stage: do not run style sweeps on your own prose.
6. <SKILL_DIR>/guidelines/reference/subsystems.md — read only the page's
   subsystem entry.

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
- Everything you persist besides the page itself (the dossier, the
  parity table, any notes or helper output) goes under
  <SKILL_DIR>/progress/<campaign>/, named <slug>.<purpose>.<ext>; write
  nowhere else in progress/, which belongs to other runs too.
- Enumerate call-site populations before writing any prose that counts or
  characterizes them (7o).
- Keep the parity checklist as you compose and close it before you
  finish: one row per LINUX KERNEL catalog symbol, two cells — where
  DETAILS shows its definition excerpt, where it shows a concrete usage
  excerpt. At exit every row is filled or its symbol is de-cataloged to a
  prose mention with a link (fill-or-decatalog; there is no
  deliberately-empty state). Persist the table at
  <SKILL_DIR>/progress/<campaign>/<slug>.parity.md.
- Run the mechanical exit suite (02-write.md) after the page is complete
  and fix what it finds before reporting: byte-compare every excerpt
  unit against the tree; print and confirm the disk line behind every
  link anchor; confirm every catalog symbol appears in at least one
  fenced block and the parity table has zero empty rows; re-derive every
  count with a search basis shaped differently from the one used while
  researching; confirm cited example files carry a recent substantive
  commit.
- Do NOT run the style sweeps (the Gate A candidate greps and the
  prose-shape read-throughs) on your own prose after writing; the
  style-lint stage does that with fresh context.
- Write the file to <output path>. Your final message is a short
  evidence report: sections written; catalog symbol count and the
  parity-table outcome (rows filled, symbols de-cataloged with one-line
  reasons); exit-suite results (excerpt units verified, anchors
  confirmed, counts re-derived with their second bases); the 7r ruling
  count you applied as proof of the registry read; and any claim that is
  not disk-settleable, stated with how the page scopes, weakens, or
  discloses it ("could not verify" is reserved for that class — a
  disk-settleable claim is settled or dropped, never reported
  unverified). Not the page text.
```
