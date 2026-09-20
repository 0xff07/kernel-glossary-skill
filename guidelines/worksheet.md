# The worksheet

The worksheet is the page's entire working file: the research, the completeness table, the QA evidence and the lint findings, at `progress/<campaign>/<dir>/<group>/<slug>.worksheet.md`, one per page, mirroring the page's path `docs/<dir>/<group>/<slug>.md` because two groups of one subsystem may share a slug, machine-local and never committed. It exists so a page's work survives the agent that did it, so passes can run in different sessions or by different agents, and so a later pass starts its re-derivations from recorded search bases.

## The file [file]

1. [file.hint-sheet] The worksheet is a hint sheet, never a source. Every fact taken from it is re-verified against the on-disk tree at the documented version before it lands in the page, the check pass never accepts an entry as evidence, and a worksheet that disagrees with the disk is corrected the moment the disagreement is found.
2. [file.kept-current] Whoever runs the research pass creates it and keeps it current, and each later pass appends its own section. Entries are one or two lines each, in the anchored-facts style of an inventory digest: locations, search bases and outcomes, never prose.
3. [file.promoted] Anything durable it records, a correction against the spec, a lesson, a settled adjudication, is promoted into the campaign spec as a dated errata entry or surfaced to the user; run events go to the run log; a finding left only here is lost when the machine is, by design.
4. [file.disposable] A run's worksheets are disposable once its campaign closes and are kept until then; another campaign's worksheets are off limits unless the user directs resume or reuse. Helper scripts and scratch go to the scratchpad under a per-page subdirectory, never here.

## HEADER [header]

1. [header.fields] The HEADER states the output path, the campaign with its directory, the subsystem entry, the documented version with its commit, the research tooling with the index state or the fallback and why, the architecture and CONFIG scope, and, in a campaign, the boundary statement verbatim.
2. [header.identity, qa] Only a worksheet whose HEADER names this page, lies under the campaign directory it names, and documents the commit the tree is at is read; the scripts refuse any other candidate, whether the convention found it or an option named it, and several accepted candidates are an ambiguity that no age order resolves.

## LINKS [links-table]

1. [links-table.machine-emitted, qa] LINKS is machine-emitted by `python3 tools/qa/kg.py table <page>`, eight columns per distinct inline span: span, region, linked, bare, bare at, anchor URL, disk line, kind / reason. The first seven are the script's and are never hand-edited: region is catalog inside the four catalog sections (SPECIFICATIONS, COVERAGE, DOCUMENTATION, OTHER SOURCES) and prose everywhere else (the lead, SUMMARY, section six and DETAILS); linked and bare are occurrence counts; bare at lists up to six page lines of the bare prose occurrences; anchor URL and disk line are what the script fetched. A re-emitted table keeps every kind / reason cell the worksheet already holds; the check pass re-runs the same command and diffs its rows against the page's spans.

2. [links-table.reasons, qa] The last cell is the writer's: a kind (symbol, location, config, generated, file) confirming a linked row's anchor, or the reason that licenses a bare row. Anchor confirmation is page-wide, catalog rows included; span closure requires a non-empty last cell on every prose row and on every catalog row whose span is not one of the catalog's own entries, the bare spans in a bullet's descriptive text.

## COMPLETENESS [completeness]

1. [completeness.scope-table, qa] First the scope closure: every anchor symbol and behavior the catalog row names, with its location on the page or its scope reduction and reason, as a table whose header names the anchors; a catalog cut never discharges it.

2. [completeness.catalog-table, qa] Then one row per COVERAGE catalog symbol, two cells: where DETAILS shows its DEFINITION as a fenced C block, and where it shows a concrete USAGE. At exit every row is filled or its symbol is de-cataloged to a linked prose mention with a one-line reason; the catalog-table rule matches the rows to the catalog by name and reports a symbol with no row and any empty cell. Block and unit counts are measurements and prove nothing, because one fence can hold several definitions and one caller excerpt can serve several usages.

## EVIDENCE [evidence]

1. [evidence.bases] Per count and universal claim, one row of a `### Bases` table with the columns line, claim, basis 1, basis 2 and result: the page line and a fragment of the sentence as `kg check` printed them, the two derivation bases (tool, pattern and scope) and the reconciled result (agrees, weakened to what, or refuted and fixed). The two facts checks read the table, list only the sentences without a row, and report a row whose fragment no longer sits on its line. Then the QA outcomes, starting points for the check pass and never proof:
   - excerpt units byte-verified, link anchors confirmed, quotations checked;
   - every leading paragraph with the verdict on its first sentence;
   - every definition excerpt with the members shown and named and the group phrase covering each member not named;
   - the DETAILS spine; the lead's and SUMMARY's counts with every sentence's role; and the excerpt-introduction list.
2. [evidence.block-map] The block map of every DETAILS subsection under a `### Block map` heading, a table with the columns subsection (page line), map, words, paras and blocks, one row per subsection copied from what `arrangement.units` prints, followed by each outlier's disposition; the check matches the rows to the page by subsection title and reports a subsection whose map differs from its row or has none.
3. [evidence.acceptance-lines, qa] The seven acceptance lines of checking.md [judgement], from [judgement.scope-covered] to [judgement.constructs], each done or not applicable with the reason; then `page sha256: <digest>` of the page the evidence describes, which the check pass refreshes after an in-place fix (checking.md [check-pass.fixes]).
4. [evidence.lifecycle, qa] Per object drawn under figures.md [lifecycle], the rows of a `### Lifecycle` table with the columns object, field, mark, writer, site, event and value: the struct, the member, the circled number the figure carries, the function that writes, its `file:line`, the event under which it runs and the value it leaves. The check reads the table against the tree: the field is a member of the struct, the site is an assignment to it inside the named writer, the mark stands in a figure's legend with that writer, and every writer of the field the subsystem's sources hold has a row (the kernel paths of its subsystems.md entry), a line `excluded: file (reason)` under the table naming the files whose writers the page leaves out and why.

## LINT [lint]

1. [lint.layout] LINT is four blocks in this order, each under its own `###` heading: `First pass`, the table of [lint.first-pass]; `Verdicts`, every candidate with its verdict; `Exemptions`, the `EXEMPT` lines and nothing else; `Check pass`, the check pass's reproduction and fixes. The `LINTED` record is the section's last line, and OPEN GAPS follows the section.
2. [lint.verdicts] Every candidate the prose view and the figure sweep surfaced, each FIXED (exact before and after), ESCALATED, or EXEMPT (with the ruling applied), the verdict written before acting; then the check pass's own reproduction, where a disagreement is a finding. An EXEMPT verdict is also written on a line of its own, which `kg check` reads: the finding of that rule whose text carries the fragment is printed as a note with the ruling and no longer fails the run.
   - The form is `EXEMPT <rule-id> "<a fragment of the flagged text>": <the ruling applied>`; a double quote inside the fragment is written `\"`, and the ruling runs to the end of the line, pipes included.
   - A page line may follow the fragment as a hint that picks one finding where the fragment matches several. A fragment is required; a line number alone exempts nothing.
   - A line that matches nothing is reported as stale and one that matches several as ambiguous, and neither exempts anything, so an exemption survives an edit above it and a stale one is seen rather than silently kept.
   - Legacy `EXEMPT rule-id/part` entries require re-adjudication and are never broadened by dropping the part. Engine errors and missing inputs cannot be exempted.
3. [lint.first-pass] Before the first fix, the writer runs `kg check` once over the composed page and records, under a `First pass` heading, a table of the FAIL and review counts per rule exactly as the run printed them, one row per rule that reported any and a total; `kg retro` reads that table across a campaign's worksheets, so the heading and the two count columns keep this form.
4. [lint.record, qa] LINT ends with the check pass's record, `LINTED <date> page sha256: <digest> qa sha256: <qa-digest>`, using both digests printed by the final full `kg check` run; single-agent mode records `check pass: self-run` before it. The page digest covers the page bytes. The QA digest covers sorted repository-relative paths and bytes of guideline Markdown and executable Python under `tools/qa/`, including shared helpers, excluding tests. A missing record, a legacy record without a QA digest, or either changed digest means WRITTEN and requires a new check pass. A current record stands only with completed human adjudication and a complete full run without FAIL, engine errors or input problems. Partial `--only` runs establish no page state. The engine never writes this record automatically. The last LINTED line is the record; earlier lines remain as history and settle nothing.

## The skeleton [skeleton]

```
# Worksheet: <page slug>

## HEADER
- output path: docs/<dir>/<group>/<slug>.md
- campaign: <run short name> (directory progress/<campaign>/)
- subsystem: <name> (entry in guidelines/subsystems.md)
- documented version: <tag>, commit <sha>
- research tooling: semcode with its index state, or the Grep and Read fallback and why
- architecture / CONFIG scope: <arch>; <CONFIG assumptions>
- boundary statement: <verbatim from the campaign spec, campaigns only>

## SYMBOLS
One line per function, struct, enum, macro or typedef the page will
catalog: name, kind, file:line of the DEFINITION, one-line role.

## USAGE
Per catalog symbol: at least one concrete caller or user, with the
caller name and file:line and the exact line range the page will excerpt.

## ENUMERATIONS
Per behavior or counted claim: the full site list with file:line per
site, AND the search basis used (tool, pattern, directories, headers
included or excluded). The basis is what a later pass re-runs.

## SPECIFICATIONS
One line per spec reference: <spec name>, section <N.N>: <title>, and
where in the code or commit history it was found.

## COMMITS AND LORE
Per relevant commit: sha, subject, and the byte-exact Link: trailer URL
from git log (or the dig result), marked usable or unusable for OTHER
SOURCES.

## HARD LIMITS
Per constant bounding the mechanism: name or literal, value, file:line.

## VERSION DRIFT
Symbols renamed, removed or newly added at the documented version
relative to widely-documented older kernels; known stale-index hints.

## LINKS
MACHINE-EMITTED by `kg table`, one eight-column row per distinct inline
span:

| span | region | linked | bare | bare at | anchor URL | disk line | kind / reason |

The first seven columns are the script's and are never hand-edited:
region is catalog inside the four catalog sections and prose everywhere
else; linked and bare are occurrence counts; bare at lists up to six page lines of the bare
prose occurrences; anchor URL and disk line are what the script fetched.
The last cell is the writer's: a kind (symbol, location, config,
generated, file) confirming a linked row's anchor, or the reason that
licenses a bare row. Anchor confirmation is page-wide, catalog rows
included; span closure requires a non-empty last cell on every prose row
and on every catalog row whose span is not a catalog entry.
The check pass re-runs the same command and diffs.

## COMPLETENESS
First the scope closure: every anchor symbol and behavior the catalog
row names, with its location on the page or its scope reduction and
reason; a catalog cut never discharges it. Then one row per COVERAGE
catalog symbol, two cells: where DETAILS shows its
DEFINITION as a fenced C block, and where it shows a concrete USAGE. At
exit every row is filled or its symbol is de-cataloged to a linked prose
mention with a one-line reason; block and unit counts are measurements
and prove nothing.

## EVIDENCE
### Bases
| line | claim | basis 1 | basis 2 | result |
One row per count and universal claim `kg check` lists: the page line and
a fragment of the sentence, the two derivation bases (tool, pattern,
scope) and the reconciled result.

### Block map
| subsection (page line) | map | words | paras | blocks |
One row per DETAILS subsection, copied from what `arrangement.units`
prints, then each outlier's disposition.

### Lifecycle
| object | field | mark | writer | site | event | value |
One row per write a lifecycle figure marks, the writers of each drawn
field complete.

The QA outcomes: excerpt units byte-verified, link anchors confirmed,
quotations checked; every leading paragraph with the verdict on its first
sentence; every definition excerpt with the members shown and named and
the group phrase covering each member not named; the DETAILS spine; the
lead's and SUMMARY's counts with every sentence's role; the
excerpt-introduction list; and the seven acceptance lines of checking.md
[judgement], each done or not applicable with the reason. Starting points
for the check pass, never proof. Ends with `page sha256: <digest>` of the
page this evidence describes.

## LINT
### First pass
| rule | FAIL | review |
The counts of the first full `kg check` run over the composed page, before
any fix, one row per rule that reported any and a total.

### Verdicts
Every candidate the prose view and the figure sweep surfaced, each FIXED
(exact before and after), ESCALATED, or EXEMPT (with the ruling applied),
the verdict written before acting.

### Exemptions
`EXEMPT <rule-id> "<fragment of the flagged text>": <ruling>`, one per line
for the engine, nothing else.

### Check pass
The check pass's own reproduction and fixes, where a disagreement is a
finding. Ends with the check pass's record,
`LINTED <date> page sha256: <digest> qa sha256: <qa-digest>`, the evidence
of LINTED, as the section's last line.

## OPEN GAPS
Anything not yet located or verified, so a resuming agent knows exactly
what remains.
```
