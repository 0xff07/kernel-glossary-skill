# The writer brief

The writer brief, filled from the spec with absolute paths composed at dispatch time:

```
Write the page <output path> for the <subsystem> knowledge base.

SKILL_DIR: <absolute path to the kernel-glossary-skill checkout>
WORKSPACE: <SKILL_DIR>/progress/<campaign>/
OPERATION: <create | takeover>; for a takeover, the page and the worksheet on disk are the starting state, continued in place with every entry re-verified before it is used; for a create that derives from a removed page, its revision: git show <commit>:<path>, reused under writing.md [facts.derived-pages]; the removed page is material, never a floor or a ceiling: every rule applies as on a fresh create, the catalog is re-curated (ownership follows the campaign's boundary statements: a symbol they assign to this page is cataloged here whatever a page not yet rebuilt holds, one they assign elsewhere is left to that page, and one they leave unassigned goes to the sibling that catalogs it on disk), every figure the trigger table asks for is drawn, and a sentence that does not meet the writing rules is rewritten rather than kept
YOUR WORKSHEET: <SKILL_DIR>/progress/<campaign>/<dir>/<group>/<slug>.worksheet.md (mirroring docs/<dir>/<group>/<slug>.md)
YOUR SCRATCH: <session scratchpad>/<dir>/<group>/<slug>/ (the scratchpad is shared and two pages may share a slug; scratch goes only here)

MANDATORY READING, by phase (SKILL.md, "Reading routes"); nothing ahead of its phase:
1. Before research: <SKILL_DIR>/SKILL.md, the passes you run yourself; <SKILL_DIR>/guidelines/kernel.md, what a kernel page is made of; <SKILL_DIR>/guidelines/worksheet.md, the worksheet you keep, which is the recovery point; the page's entry in <SKILL_DIR>/guidelines/subsystems.md; and the campaign facts below.
2. Before writing: <SKILL_DIR>/guidelines/writing.md whole, every rule the page must meet, composed under from the first sentence; and <SKILL_DIR>/guidelines/template.md.
3. Before outlining: <SKILL_DIR>/guidelines/figures.md from [drawing] to [patterns], the trigger table and the model figure included, so the block map marks the subsections that carry a figure; [register-figures] as well when a figure is a register or bitfield; then only the pattern file under <SKILL_DIR>/references/figures/ that the index matches, per figure.
4. At QA: <SKILL_DIR>/guidelines/checking.md, the steps you run before reporting done, with python3 <SKILL_DIR>/tools/qa/kg.py check <page> for the mechanical ones.

MISSION. <Scope statement from the catalog row, naming the anchor symbols with file:line hints.> <The boundary rules for this page's cluster: what this page owns, what each sibling owns, the seam symbols, which sibling pages exist on disk.> Line numbers are hints; the disk is ground truth, and a hint you cannot reproduce is reported, never written around.

CAMPAIGN FACTS:
- Documented tree: <path>, version <tag>, commit <sha>. Architecture scope: <arch>. CONFIG assumptions to state where behavior depends on them: <list>.
- Section-six heading: <value or "omit">.
- Project-specific bans and errata from the campaign spec: <list, or "none">.
- <Derivation source and known defects, if an existing page feeds this one. Otherwise omit.>

DIRECTIVES.
- At most about 25 KB of output per command; a persisted output is read by slice only.
- Under the skill checkout the only files you write are the page and your worksheet, nowhere else in progress/ and never in guidelines/ or campaigns/; scratch goes only to YOUR SCRATCH. No git operation that changes state.
- A create: if the output path exists when you are about to write, stop and report. A takeover: continue the page and the worksheet on disk in place, the one case in which a writer writes over a page on disk, trusting nothing in either; a hint that does not reproduce is reported, never written around.
- Enumerate call-site populations before any prose that counts or characterizes them, and give every count and universal claim its row in the worksheet's Bases table (worksheet.md [evidence.bases]).
- The page states results and their scope, never the search; the search stays in the worksheet.
- A site is cited as a location link whose text is the file's base name and line, `tb.c:130`, the path from the tree root only where two cited files share a base name or the file has no extension (kernel.md [links.site-text]).
- Keep the completeness table as you compose; fill or de-catalog every row.
- OTHER SOURCES is the reader's shelf: your commit entries, taken from the tree's `Link:` trailers, go under your own `### Added by <model>` heading; a page derived from a removed revision carries everything outside such blocks over verbatim (an unmigrated section of the removed page, with no block, is re-seeded under your heading and its reader-added lines kept); nothing outside your block is rewritten, reordered or removed, and no link in the section is fetched (kernel.md [sections.other-sources]).
- The reader is meant to have read the code: walk every owned function through whole, in one excerpt or in consecutive pieces with one sentence per stage (writing.md [excerpts.walkthrough]); show another page's function only at the stage the subject reaches; show the lines a later paragraph reasons about again beside it ([excerpts.reshown]); no `...` inside a function, and a `...` inside a long definition carries its count and resumption line.
- DETAILS opens with the route paragraph ([arrangement.route]); every subsection's first sentence is its conclusion and its last sentence restates it ([purpose.conclusion-first]); a subsection with two or more blocks names its parts before the first block ([purpose.schema]); a function walked in pieces is outlined in a table and each piece carries its mark, consecutive marked series, outlines and legends alike, taking the alphabets in the cycle ① ❶ Ⓐ ⓐ ⓵ ([excerpts.outline], [drawing.marks]); a "So far," recap closes a subsection at most every four subsections ([arrangement.recap]); a symbol is linked at its first occurrence in each paragraph and left bare after it; sentences run 15 to 22 words. Read `kg skim <page>` before reporting: it must read as the argument.
- Plan the figures before writing: the model figure under the lead or in SUMMARY ([drawing.model]) and a figure wherever a subsection carries a shape of the trigger table ([drawing.triggers]); `kg check` lists the subsections that carry a shape and no figure, and each is drawn or its reason recorded in the worksheet.
- REGISTERS draws the registers, bitfields and fields the page touches and carries no table of helpers per register ([registers.section]); a register no other page catalogs is a catalog entry of this page under a COVERAGE heading naming its block and header, and every helper is named in DETAILS at its stage.
- An object with a field written by two or more functions gets its lifecycle figure, a strip or a state pair with a numbered legend, backed by the worksheet's Lifecycle table (figures.md [lifecycle], worksheet.md [evidence.lifecycle]); every figure names a function only through such a legend, one entry per line with a phrase saying what happens there ([drawing.legend]), and the paragraph after a DETAILS figure walks its marks in order, one sentence per mark naming the mark with its function linked ([drawing.walk]).
- Before your first fix, run `python3 <SKILL_DIR>/tools/qa/kg.py check <page> --first-pass` once over the composed page; the engine records the run's counts per rule beside your worksheet (worksheet.md [lint.first-pass]).
- Run the QA steps after the page is complete, fix what they find before reporting, and persist the LINKS table with every kind / reason cell filled and the EVIDENCE and LINT sections into the worksheet, ending EVIDENCE with `page sha256: <digest>` of the page the evidence describes.
- LINT ends with your verdicts. The `LINTED <date> page sha256: <digest> qa sha256: <qa-digest>` record and the `check pass:` line are the check pass's, never yours; a writer that writes either is reported.
- Final message: the lead verbatim; sections written; catalog count and completeness outcome (de-catalogings with reasons); QA results (units verified, the walkthrough summary, anchors confirmed, counts with second bases, the generator summary notes, the lead and SUMMARY counts and sentence roles, sweep candidates per class with dispositions, the rhythm outliers with dispositions, the introduction summary); the exemptions applied; any hint that did not reproduce; any claim that is not disk-settleable and how the page scopes it. Not the page text beyond the lead.
```
