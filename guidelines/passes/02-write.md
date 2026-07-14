# Pass 02: write

Purpose: compose the complete page, following every writing rule while composing rather than fixing afterward.
Inputs: the dossier (pass 01) and the resolved parameters (pass 00); every dossier fact is re-verified on disk before it lands, because the tree at the documented version is the only ground truth.
Outputs: the draft page at `docs/<dir>/<topic-slug>.md`; the dossier updated where the disk disagreed with it; the parity checklist at `progress/<campaign>/<page-slug>.parity.md`.
Run by: single-agent mode inline; in a campaign a dispatched writer agent (brief at the end of this file), on the strongest available model.
Next: pass 03 (`guidelines/passes/03-lint.md`). A campaign writer finishes this pass by closing the parity table, running the mechanical exit suite below, and persisting its evidence into the dossier — it owns the page's facts end to end — but does not run the style sweeps on its own prose, because a fresh-context lint-fix stage does those better. A solo agent continues into pass 03 itself. Either way the page's state after this pass is WRITTEN: it stays uncertified until a verify pass or verify campaign signs it off (`guidelines/passes/04-verify.md`).

Rules are cited by stable ID; `guidelines/rules/INDEX.md` maps every ID to its file.

## Reading list (mandatory, in order)

This pass owns the writer's reading list; the writer brief points here instead of restating rules.

1. `guidelines/rules/7r-adjudications.md`, the settled adjudications registry, then `guidelines/rules/rules.md`, which carries every writing rule and every gate in one file (7p applies additionally whenever the page derives from existing material).
2. `guidelines/rules/diagrams.md`, but only when the page will carry a figure: 7g's principles always govern one, and 7h and 7i hold the figure catalogs (choose the shape from 7i's use-case index). A page with no figure needs none of it.
3. `guidelines/reference/measured-criteria.md`: the depth rules and tripwires that define what "in-depth, fine-grained" measures as.
4. The sample pages chosen in pass 00 (`guidelines/passes/00-prep.md`), under its doctrine that samples calibrate form only, never facts.
5. The page's subsystem entry in `guidelines/reference/subsystems.md`.
6. `guidelines/rules/rules.md` (3b): the writer satisfies its factual items by construction and by the mechanical exit suite below (1 parity, 2 grounded code, 3 links, 6 coverage, 7 driver recency, 9 behavioral claims); the whole gate is re-run later with fresh eyes — solo in pass 04, in a campaign by a verify campaign (`guidelines/passes/04-verify.md`). Gate A and the style-shaped items stay with the lint-fix stage — the writer never sweeps its own prose.

## Generate the page

Follow the template structure exactly. The page must contain these sections in order:

1. H1: the topic name (just the name, no extra text)
2. The AI-generated-content caution blockquote, immediately below the H1
3. A short summary paragraph with an ASCII diagram if appropriate
4. `## SUMMARY`
5. `## SPECIFICATIONS`
6. `## LINUX KERNEL`
7. `## KERNEL DOCUMENTATION`
8. `## OTHER SOURCES`
9. `## <section6_heading>` (from the subsystem's entry in `guidelines/reference/subsystems.md`; omit entirely if set to "none")
10. `## DETAILS`

## Parity bookkeeping while composing

Maintain the catalog-to-DETAILS parity checklist as the page is composed: one row per LINUX KERNEL catalog symbol, recording where DETAILS reproduces its definition as a fenced ` ```c ` block and where it shows a concrete caller or usage as code — the two evidence columns of Gate B item 1. Persist the table at `progress/<campaign>/<page-slug>.parity.md` in the run's artifact directory (SKILL.md ("The progress/ workspace")) before reporting the page written. Catalog a symbol only when both of its cells can be filled; a symbol the page will not excerpt is mentioned and linked in prose without a catalog bullet. At exit every row is filled or its symbol has been de-cataloged (fill-or-decatalog): there is no deliberately-empty state, and each de-cataloging is named in the writer's final report.

This is construction bookkeeping — tracking coverage forward while writing, the same duty class as the 7o enumerations — not a style sweep. The verify pass audits the table independently against the page; a checklist entry is a hint, never evidence (the same relationship the dossier has). The checklist exists because parity holes that survive the writer cost a follow-up round-trip an order of magnitude more expensive than the missing excerpts themselves.

## Mechanical exit suite (run before reporting done)

After the page is complete, the writer verifies its own facts with the procedures below and fixes what they find before reporting. These are procedures against ground truth, not the style sweeps (which stay with the style-lint stage); running them is part of writing the page, and they are reliable in the writer's own hands precisely because they are mechanical.

1. Excerpts: byte-compare every fenced ` ```c ` unit against its provenance file at the cited line (tabs included; an interior `/* path:line */` delimiter starts a new unit, a standalone `...` line is a declared elision). Every unit begins at its cited line.
2. Anchors: extract every Elixir link target, print the disk line at each, and confirm a symbol link lands on the definition line and a location link on the exact site the prose describes (7m; the 7r settled rulings govern `CONFIG_*` options, generic primitives, and ops-struct members).
3. Parity closure: confirm every catalog symbol appears in at least one fenced block and the parity table has zero empty rows (fill-or-decatalog above).
4. Counts: re-derive every count and every "only"/"never"/"always"/"exactly" enumeration with a search basis shaped differently from the one used during research — a repeated identical grep repeats the same miss — and reconcile, or fix the sentence to what the enumeration shows (7o).
5. Cited examples: for each driver or consumer file cited as an example, confirm a substantive commit within roughly three years (`git log -1` on the file).
6. Persist the evidence: append the suite's outcomes to the dossier's EVIDENCE section (`guidelines/passes/dossier.md`) — every count and universal claim with its two derivation bases and reconciled result, plus the excerpt-unit and anchor-confirmation tallies — so a later verify campaign re-derives from recorded bases instead of reconstructing them. Update the dossier HEADER status to `written`.

Claims that are not disk-settleable (intent, motivation, anything the tree at the documented version cannot witness) are never left as bare assertions: scope them out, weaken them to what the evidence shows (7o), or state them with their basis disclosed (7l, 7n). The writer's report lists this class explicitly; "could not verify" is reserved for it — a disk-settleable claim is settled or dropped, never reported unverified.

## Composing stance

The sample pages under `guidelines/reference/samples/` embody every rule. The closest-matching sample read in the prep pass (`guidelines/passes/00-prep.md`) is the worked example; match its structure, diagram style, code-citation density, and depth. The examples in the rule files use ACPI and mm symbols; they illustrate the rule mechanic, which applies unchanged to every subsystem. All generated content must follow the rules as it is composed; the 7q recipes (`guidelines/rules/rules.md` (7q)) exist so compliant phrasing never has to be re-derived per hit, and the 7r registry settles the boundary cases in advance.

## Dispatching a writer (campaign brief)

Role: researches, writes, and fact-verifies one complete page (passes 01 and 02). The writer owns everything disk-settleable on its page — catalog-to-DETAILS parity, excerpt verbatimness, link-anchor correctness, counts, and behavioral claims — and leaves no substantive holes: a page is not reported written until the parity table has zero empty rows (fill-or-decatalog) and the mechanical exit suite above has run clean with its evidence persisted. What the writer does not run are the style sweeps; the lint-fix stage with fresh context does those better. Model tier: the strongest available model; page writing needs research judgment, prose discipline, and figure quality. On death, resume the same agent first ("do not redo the research; write the page now from what you have"); if repeated resumes fail, a fresh agent starts from the page's dossier, its parity table, and the plan file.

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
   <SKILL_DIR>/guidelines/rules/INDEX.md, the diagram rules 7g-7i among
   them, the depth rules in
   <SKILL_DIR>/guidelines/reference/measured-criteria.md), the parity
   bookkeeping, and the mechanical exit suite you run before reporting
   done. Read everything that list names.
5. <SKILL_DIR>/guidelines/rules/rules.md — you own satisfying its
   factual items by construction and by the exit suite (1 parity,
   2 grounded code, 3 links, 6 coverage, 7 driver recency, 9 behavioral
   claims); a verify campaign re-runs the whole gate later, and a
   factual defect found there costs a follow-up round. Gate A and the
   style items stay with the lint-fix stage: do not run style sweeps on
   your own prose.
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
  commit; persist the evidence into the dossier's EVIDENCE section.
- Do NOT run the style sweeps (the Gate A candidate greps and the
  prose-shape read-throughs) on your own prose after writing; the
  lint-fix stage does that with fresh context.
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
