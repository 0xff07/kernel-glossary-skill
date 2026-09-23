# QA checks by guideline

One requirement in `guidelines/` marked `qa` owns one Python module under
`tools/qa/checks/`, one `check(page, inputs)` function and one test module.
This document is the design of `tools/qa/` and the contract for changing it.
The guidelines carry the requirements themselves; `README.md` shows the
commands as a user runs them.

## 1. Purpose and scope

Adding a check means understanding one requirement and its detection, with one
predictable place for the implementation and one for its tests. Regex sweeps,
structural checks, measurements and reading inventories share one interface,
and a requirement with several detection methods keeps them together. Small
rule files bound what an author has to read; parsing, input resolution and
reporting stay shared. A detection technique never opens a second extension
route.

The engine proves what it can and lists what a person must read. Human
adjudication is part of every check pass, and a clean run never stands in for
it.

## 2. Ownership

Guidelines keep their requirement IDs and normative prose. A `qa` marker says
the requirement has a programmatic check; an unmarked requirement is manual.
The marker does not claim that the check covers the whole requirement.

```markdown
5. [facts.counts-serve-claims, qa] A count that serves no claim is noise.
```

Each marked requirement has one module in the flat `checks/` directory and one
module under `tests/`:

| Guideline ID | Check module, relative to `tools/qa/` | Test module |
|---|---|---|
| `style.counting-headings` | `checks/style_counting_headings.py` | `tests/test_style_counting_headings.py` |
| `facts.counts-serve-claims` | `checks/facts_counts_serve_claims.py` | `tests/test_facts_counts_serve_claims.py` |
| `page.self-contained` | `checks/page_self_contained.py` | `tests/test_page_self_contained.py` |
| `excerpts.verbatim` | `checks/excerpts_verbatim.py` | `tests/test_excerpts_verbatim.py` |

The filename stem is the ID with dots and hyphens replaced by underscores; the
module's `RULE` value is its authoritative identity, and discovery validates
the convention and rejects filename collisions between distinct IDs.

All detection for a requirement lives in its module: candidate selection,
regexes, thresholds, exceptions and local helpers. Internal links, named page
references, anonymous deflections and template residue all belong to
`page_self_contained.py`.

## 3. The check contract

A check module exports `RULE` and `check(page, inputs)`. `check()` returns an
iterable of `report.Finding` records, usually as a generator; the runner
supplies the parsed page and the resolved inputs and attaches the rule ID and
guideline location to the output. A requirement with several detectors composes
ordinary local functions:

```python
RULE = "page.self-contained"


def check(page, inputs):
    yield from check_internal_links(page)
    yield from check_named_pages(page)
    yield from review_deflections(page)
    yield from check_template_residue(page)
```

There is no descriptor, `CHECKS` export, registered part, kind, coverage field
or dependency declaration, and no YAML schema, rule dictionary or selector
dispatch as an alternative authoring interface. Each rule is implemented
directly: no generic dispatcher copied in with branches left under constant
selectors, no configuration fallback for a case that cannot occur.

Shared functions exist where there are real shared callers, take ordinary
Python arguments and live outside `checks/`. The judgment stays in the rule
even when the mechanics are shared:

- `patterns.py` and `measurements.py` provide the operations; the caller
  supplies its rule's patterns and thresholds.
- `sentence_utils.py` normalizes sentences, tracks the committed baseline and
  presents worklists; the facts rules select their candidates with their own
  count, ordinal and universal regexes, and presentation never dispatches on a
  rule ID.
- The two geometry rules are independent: layout owns width limits, the
  register exceptions and the loose-vertical scan; unicode owns the emoji ban.

A check reads its arguments and yields output. It does not print, modify files
or shared inputs, call another rule's entry point, or carry its own CLI or
selftest. Source caches belong to the input resolver.

## 4. Findings and reporting

A finding is `Finding(line, severity, message, data=None)`. The line is a page
line number or `None` when no page location exists; missing content never gets
a fabricated location. `data` is JSON-serializable. `report.observations()`
packages a rule's findings with its summary note and listing rows, and
`report.reading()` its review rows; both are the ordinary way to yield an
inventory.

| Severity | Meaning |
|---|---|
| `FAIL` | A detected violation under the check's conditions |
| `review` | A candidate or reading work item that needs human judgment |
| `note` | Context: an inventory row, a measurement or a recorded exemption |

Every observation appears in the output: reading candidates as review findings,
informational rows as notes, aggregate measurements as summary notes with
structured `data`. `--json` groups the results by guideline ID with the full
details; the text report prints the same inventories and summaries.

Execution completeness is separate from guideline judgment. A rule that emits
nothing is `0 findings`, which does not say the requirement holds; `INCOMPLETE`
means a required input was unavailable, `ERROR` a broken binding, an execution
failure or invalid output, and both keep the findings emitted before them.

A candidate's label describes what the algorithm observed, never what a person
must decide: the counts inventory says `CONTAINS UNIVERSAL WORD` because it saw
one, not because the count serves a claim, and a review row's `data.flags`
records heuristic observations that do not clear its reading task. Each
inventory's summary note carries its own rule's measurements under `data`; a
run with `--only` selects a rule's inventory alone.

Deduplication that needs knowledge of a rule stays in that rule: the
self-contained check counts an owning-page cell once and does not report a
named page and a local link twice. The reporter never merges observations
across rules or guesses equivalence from similar messages, and a review finding
is never cleared to make a run look clean.

## 5. Discovery and execution

`rules.py` indexes the guideline markers and discovers `checks/*.py`, reading
each module's `RULE` and `check`; nothing is registered centrally. Imports and
discovery are deterministic and checks run in guideline order, a stable
reporting order rather than a dependency between checks. Modules enter
`sys.modules` before execution so ordinary Python, dataclasses with deferred
annotations included, works during import.

Discovery and execution validate that guideline IDs and markers are well
formed and unique; that every `qa` requirement has exactly one module and every
module names a requirement marked `qa`; that filenames follow the convention
without collisions; that `RULE` is a valid ID and `check` callable; and that
every yielded record has a valid location, message, severity and serializable
data. A malformed marker, a missing module, a broken import, a duplicate ID,
invalid output or an unknown requested ID is a visible error and never removes
a check from the run silently.

`kg.py` consumes each iterable and records findings and execution outcomes.
Errors are caught while the generator runs, findings emitted before an error or
a `MissingInput` stay in the report, and the other checks continue.

## 6. Inputs

`inputs.Inputs` resolves everything a run reads, once, and validates it before
any check depends on it:

- the page, with its sha256;
- the kernel tree, from `--tree`, `KG_TREE` or the checkout convention,
  checked to be a kernel tree, its Git availability, the version the page's
  links pin and the cleanliness of the files the page cites;
- the worksheet, at `progress/<campaign>/<dir>/<group>/<slug>.worksheet.md` by
  convention, the campaign being the page's top directory under `docs/` or the
  basename of `--spec`, or from `--worksheet`: one path, never a search, and
  nothing in the file checked for identity, since every row a check reads is
  matched to the page or the tree;
- the campaign spec, `campaigns/<dir>.md` by convention or `--spec`;
- the baseline, the last committed revision of the page that differs from it,
  which the facts rules use for provenance;
- the subsystem, the `guidelines/subsystems.md` entry whose `dir` is the
  page's directory under `docs/`, exposed as `inputs.subsystem` with its
  kernel paths;
- a per-run cache of source lines, and the QA digest of section 10.

`inputs.require(name)` returns a usable `tree`, `git`, `worksheet` or
`baseline` or raises `MissingInput` with the reason. A check does its
page-only work before requiring an input, so the runner keeps those findings
and marks the rule incomplete when the input is missing:

```python
def check(page, inputs):
    yield from page_only_findings(page)
    tree = inputs.require("tree")
    yield from source_findings(page, tree)
```

Checks use the resolved inputs and never discover alternate paths that bypass
the validation. Optional absence differs from failure: a rule may find that no
differing baseline exists or that no spec applies and say so, but a failed
history probe or a read failure is an input error, not an empty observation.
`inputs.git()` raises on failed commands and timeouts, and a caller that wants
a negative search result allows it explicitly, `ok=(0, 1)` for `git grep`.

## 7. Shared parsing and censuses

Shared modules exist for real shared callers and never depend on a rule's
registration:

- `pagemodel.py` is the page as every check reads it, parsed once per run:
  sections and regions, headings, paragraphs, tables and cells (escaped pipes,
  separator rows validated whole), spans, fences, excerpt units with their
  provenance, figures and their marked legends, the catalog keys and
  entries, the cited files, a fence's introduction and outro, readable
  sentences and the skim of DETAILS.
- `constructs.py` parses a kernel source file into its file-scope constructs,
  functions, definitions, initializers, macros and comment blocks with their
  extents, and answers `construct_at`, `members_of` and `assignment_to`
  (plain, compound, `++` and `--`). Its writer census, `field_writers`,
  follows an embedded object through its container (`sw->tmu.mode`).
  `sources_within` collects the `.c` and `.h` files a subsystem's kernel paths
  name, a directory recursively, a glob or a single file, test files left out,
  and `object_sources` hands a census the subsystem's sources, falling back to
  the directories the page cites only for a page with no subsystem entry.
- `walk_utils.py` maps a page's units onto an owned function: the pieces
  shown, the chain they form, what was shown ahead of the walk and what was
  never shown.
- `worksheet_utils.py` reads the worksheet's tables: the Bases rows, the
  recorded block map, the COMPLETENESS tables, the Lifecycle rows and the
  `excluded:` files under them; `Inputs.exemptions()` reads the LINT section.
- `span_utils.py` classifies link anchors and `links_table.py` emits the
  LINKS table; `sentence_utils.py`, `patterns.py` and `measurements.py` serve
  the style and facts sweeps as section 3 describes.

## 8. Rule families on that machinery

The guidelines define what each rule requires; this section says only what the
implementation leans on.

Links. `links.site-text` reads each location link's text against its URL path
and lists for reading a text that carries its directory where no cited file
shares the base name, and a bare base name where two cited files share it, so
the reader sees `tb.c:130` while the URL keeps the path. `sections.other-sources`
verifies the entries under the `### Added by <model>` headings of OTHER SOURCES
against their `Link:` trailers, lists the reader's lines without reading them,
and, once the committed page is in that form, fails a reader's line that the
page no longer carries.

Excerpts. `excerpts.walkthrough` takes each cataloged function's extent from
`constructs.py`, maps the page's units onto it with `walk_utils.py` and reports
lines never shown as FAIL, pieces shown before the walk reaches them as review
and lines shown again as a count; `excerpts.outline` requires the piece table
and the marks the introductions repeat. `excerpts.reshown` lists
every location link whose lines the page reproduces only elsewhere and every
re-show longer than about twelve lines; `excerpts.contiguity` fails an elision
inside a function; `excerpts.verbatim` validates the one surviving elision
marker, `... /* N lines, to :LINE */`, and prints the exact marker when it is
missing; `excerpts.enclosing` accepts a unit from inside a function when the
sentence above names and links the function. `kg excerpt` prints a unit ready
to paste, so no source is transcribed by hand.

Reading. `arrangement.route`, `purpose.conclusion-first`, `arrangement.recap`
and `purpose.schema` make the skim of DETAILS carry the argument, and
`lifecycle.order` ties the order of DETAILS to the object's lifecycle figure.
`kg skim` prints that skim and `kg view --load` the measurements behind these
rules, so a rule change is judged by what it does to a page.

Figures. `drawing.model` requires the page's map under the lead or in SUMMARY.
`drawing.triggers` detects the trigger table's shapes heuristically, an enum or
three enumerator spans, two actors of a known pair named twice each, a
definition of six or more members, two list or allocation primitives in one
excerpt, a topology helper or the word depth twice, three ordinal openers, and
lists every DETAILS subsection carrying one with no figure; the writer answers
each row with a figure or a recorded reason. `drawing.legend` verifies a
legend the way prose sites are verified, the numbers match the drawing, each
site is reproduced and lies inside the named function, each entry carries its
phrase, and `drawing.walk` requires the paragraph after a DETAILS figure to name
every mark and link the legend's functions in mark order; `drawing.marks` reads
the marked series in page order, outlines and legends alike, one alphabet per
series and the five alphabets taken in a fixed cycle. `geometry.layout` and
`geometry.unicode` measure the drawing itself. `registers.section` lists a table
under REGISTERS and a REGISTERS that links register definitions (a URL ending
in `regs.h`) and draws none; `registers.ruler` reads the grids of figures that
carry a bit ruler and fails a cell boundary off the bit grid or a divider
junction that meets no boundary in the rows beside it.

Lifecycle. `lifecycle.when` takes as candidates the cataloged `struct name`
keys the subsystem's sources define, a catalog entry for a member such as
`struct tb_nhi *nhi` naming no object, and lists each with a field two or more
functions write and no Lifecycle table, the `excluded:` files left out.
`evidence.lifecycle` reads every table row against the tree, the member exists,
the site assigns it inside the named writer, the mark stands in a legend, and
against the same census, so a drawn lifecycle is complete or says what it left
out. Both read `object_sources`, the subsystem's kernel paths, never the whole
neighbourhood a page cites.

## 9. Commands

| Command | What it does |
|---|---|
| `check <page> [--only ID ...] [--json] [--checklist] [--tree] [--worksheet] [--spec]` | runs the checks and prints findings, inventories and the page state |
| `view <page> --regions / --prose / --raw / --spans-visible / --load` | prints a page representation, `--load` the reading-load measurements |
| `skim <page>` | prints the reading path of DETAILS: the route, then each subsection's title, first sentence, recaps and last sentence |
| `table <page>` | emits the worksheet's LINKS table |
| `excerpt <path:first[-last]> [--whole]` | prints a verbatim unit with its provenance comment, or the whole construct holding the line |
| `selftest [--rule ID]` | validates the bindings and runs the rule tests, the shared engine tests and the reference figures |
| `where <ID>` | names the guideline, the check module and the test module |
| `rules` | lists the checks by guideline ID |
| `retro <progress dir> [--rule ID]` | per rule, what the checks found on the first pass of every page a campaign's worksheets record |
| `triage <docs dir> [--cache DIR] [--json] [--verbose]` | one row per page under the current rules, graded current, fix or rebuild |

`retro` prints, per rule, the pages with a first-pass record, the pages where
the rule fired, the first-pass FAIL and review totals, the `EXEMPT` lines
written against it and the share of its hits they cover, and the last page and
date it fired; `--rule` lists the pages instead. `triage` prints, per page, the
FAIL and review totals, the excerpt-rule failures, the units and the share that
are skeletons, the walkthrough gaps, the reading and figure failures, lines,
figures and state, then a summary per grade: no FAIL is current; walk gaps at
most one owned function in five and skeletons at most a third of the units is
fix; the rest is rebuild. Its `--cache` reuses a page's check document while
the page and QA digests match. Both commands change nothing.

| Exit code | Meaning |
|---|---|
| `0` | complete execution without FAIL; human review may remain |
| `1` | a FAIL, or an engine or input error |
| `2` | missing required inputs without another failure |

A nonexistent ID or an empty explicit selection is an error, and a partial
`--only` run never establishes LINTED state.

## 10. Exemptions and page state

Exemptions live in the worksheet's LINT section:

```text
EXEMPT rule-id "fragment" [line]: ruling
```

The fragment identifies exactly one observation under that rule, an optional
line hint resolving ambiguity; every exemption matches against the original
findings, and an earlier exemption cannot make another ambiguous fragment
unique. Stale, ambiguous and line-only entries exempt nothing, and no exemption
suppresses an engine error or a missing input. There are no registered parts:
a legacy `EXEMPT rule-id/part` entry is re-adjudicated rather than silently
widened.

After a complete run and human adjudication the worksheet records:

```text
LINTED <date> page sha256: <digest> qa sha256: <qa-digest>
```

`lint_record.py` interprets the record for the `lint.record` check and the
CLI; page state never depends on a check's human-readable messages. The QA
digest hashes, in sorted order of their repository-relative paths, the bytes of
every guideline Markdown file and every Python file under `tools/qa/` except
the tests and the reporting-only modules `retro.py` and `triage.py`, which read
findings and produce none. File bytes include uncommitted changes, so a commit
ID cannot stand in for the digest.

A changed page or QA digest, or a record without a QA digest, returns the page
to WRITTEN. LINTED needs a current record, completed human review and a
complete full run without FAIL; a clean run creates no record and establishes
no factual correctness.

## 11. Tests and validation

Tests use the standard `unittest`, inline text and small page builders, and
need Python 3.10+ and Git for temporary source repositories; no external kernel
tree or worksheet. Each rule's test module exercises its real `check()`: an
offending example, a similar allowed one, the relevant regions and boundaries,
and missing-input behavior where it applies, asserting location, severity,
provenance and structured data rather than message text alone.

`selftest --rule <id>` validates one binding and runs its tests. The full
`selftest` validates every binding, requires nonempty test modules, runs the
rule and shared-engine tests and checks the reference figures under
`references/figures/` and `guidelines/figures.md` with the geometry checks.
Unknown IDs, missing or broken modules and zero executed tests fail visibly.
GitHub Actions runs the full selftest.

Shared regression tests cover discovery, imports, invalid selections and
output, generator failures, findings retained before a missing input, input
errors, exemption ambiguity and LINT state; the reading algorithms and the
LINKS emitter are tested against their real implementations. The contribution
integration test adds exactly a guideline, a check module and a test module and
exercises `rules`, `where`, `check` and both selftests without central edits,
its temporary suite excluding the contribution test itself.

A refactoring preserves candidate scope, exceptions, severity, locations,
ordering, provenance and execution outcomes; a deliberate change of detection or
reporting is written into the guideline or this document and covered by a
behavior test. No per-rule fixture language, fixture directory or selftest
scaffold exists.

## 12. Adding, extending and retiring a check

Adding one:

1. Find the requirement in `guidelines/` and add `qa` to its marker.
2. Create `checks/<stem>.py`, with every detector and candidate selector for
   that requirement together.
3. Add `tests/test_<stem>.py`.
4. Run the selected selftest, then the full selftest.

The rule then appears in `check`, `where`, `rules` and `selftest` with no edit
to a loader, dispatcher, selector list, CLI option or reporter. Extending a
rule changes its module and tests, and its guideline when the requirement
changes; shared parsing grows only when another caller needs it.

Retiring one rests on what the check found across pages, not on an impression.
Before fixing anything, a writer runs `kg check` once over the composed page
and records the FAIL and review counts per rule under `First pass` in the
worksheet's LINT (worksheet.md [lint.first-pass]); with the `EXEMPT` lines,
every page then holds per rule what was found, what was fixed and what was
judged a false hit, and `kg retro` sums them.

The thresholds, applied by a person over at least twenty pages: a check with no
first-pass hit is a guard the writers no longer need, and goes when it carries
maintenance and stays when it costs nothing to run; a check whose hits are
mostly exempted, seven in ten or more, is producing reading work, so its exempt
logic is reworked or the check goes and the prose stays; a check with fixed
hits stays; a manual rule whose reading rows are adjudicated "no change" page
after page is merged into its neighbour or given a form the engine can verify.
`retro` marks the first two cases in its last column.

Retirement is deletion. The module and its test go, the requirement drops its
`qa` marker, and a retired rule loses its sentence with a clause added to the
neighbour that absorbs it. There is no parked state: Git history is the
archive, and the `skill:` commit that retires carries the `kg retro` numbers
that justified it. After a style sweep is retired, one batch is checked with
the deleted check re-run from history, because a first-pass rate measured while
the sweep existed does not prove what writers do without it.
