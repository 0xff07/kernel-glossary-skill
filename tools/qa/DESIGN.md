# QA Checks by Guideline

One guideline ID owns one Python module, one `check(page, inputs)` function and
one corresponding test module. This document defines the current design of
`tools/qa/` and the contribution contract for adding or extending a check.

## 1. Purpose

Adding a check requires understanding its guideline and detection logic, with one
predictable implementation location and one test location. Regex checks,
structural checks, measurements and reading inventories use the same interface.
A requirement with several detection methods keeps them together.

Small rule files limit the scope an author needs to read and modify. Reusable
parsing, input resolution and reporting remain shared. Detection technique does
not create a separate extension route.

## 2. Guidelines and file ownership

Guidelines retain their requirement IDs and normative prose. A `qa` marker means
that a requirement has a programmatic check; an unmarked requirement remains
manual. The marker does not claim that automation covers the full requirement.

For example, the marker in a requirement can be written as:

```markdown
5. [facts.counts-serve-claims, qa] A count that serves no claim is noise.
```

Each marked requirement has one module in the flat `tools/qa/checks/` directory
and one corresponding module under `tools/qa/tests/`:

| Guideline ID | Check module, relative to `tools/qa/` | Test module |
|---|---|---|
| `style.counting-headings` | `checks/style_counting_headings.py` | `tests/test_style_counting_headings.py` |
| `facts.counts-serve-claims` | `checks/facts_counts_serve_claims.py` | `tests/test_facts_counts_serve_claims.py` |
| `page.self-contained` | `checks/page_self_contained.py` | `tests/test_page_self_contained.py` |
| `excerpts.verbatim` | `checks/excerpts_verbatim.py` | `tests/test_excerpts_verbatim.py` |

The filename stem is the ID with dots and hyphens replaced by underscores. The
module's `RULE` value is its authoritative identity. Discovery validates this
convention and rejects filename collisions between distinct IDs.

All detection for a requirement belongs to its module: candidate selection,
regexes, thresholds, exceptions and local helpers. For example, internal links,
named page references, anonymous deflections and template residue all belong to
`page_self_contained.py`.

## 3. Rule interface and implementation

A check module has two required exports: `RULE` and `check(page, inputs)`.
`check()` returns an iterable of `report.Finding` records; a generator is the
usual implementation. The runner supplies the parsed page and resolved inputs,
then attaches the rule ID and guideline location to the output.

A requirement with several checks composes ordinary local functions. For example,
with the helper implementations in the same module:

```python
RULE = "page.self-contained"


def check(page, inputs):
    yield from check_internal_links(page)
    yield from check_named_pages(page)
    yield from review_deflections(page)
    yield from check_template_residue(page)
```

The authoring interface requires no descriptor, `CHECKS` export, registered part,
kind, coverage field or dependency declaration. A check yields findings rather
than creating runner result objects. YAML schemas, rule dictionaries and
selector dispatch are not alternative authoring interfaces.

Implement each rule directly. Do not copy a generic dispatcher into a rule and
leave branches controlled by constant selector values. Opening and closing
checks inspect their respective subsection boundaries with distinct sentence
limits. Lead, summary and section-order checks express their constraints without
configuration fallbacks that cannot occur.

Use ordinary shared functions when there are actual shared callers. Their
parameters are regular Python arguments, and helpers live outside `checks/`.
Keep guideline judgments local even when the mechanics are shared:

- `patterns.py` and `measurements.py` provide common operations; callers supply
  their rule's patterns and thresholds.
- `sentence_utils.py` provides sentence normalization, baseline provenance and
  worklist presentation. Facts rules select candidates with their own count,
  ordinal or universal regexes. Presentation accepts already selected candidates
  and does not dispatch on rule IDs or selector names.
- Geometry rules independently implement layout and ASCII connector checks.
  Width limits and register exceptions belong to layout; literal-text connector
  exceptions belong to Unicode. Vertical-connection helpers stay local to layout
  because it is their only caller.

A check reads its arguments and yields output. It does not print, modify files or
shared inputs, invoke another rule's entry point, or carry its own CLI or selftest.
Shared input caches belong to the input resolver.

## 4. Findings and reporting

A finding is `Finding(line, severity, message, data=None)`. Its line is a positive
page line number or `None` when no page location exists; missing content must not
produce a fabricated location. `data` must be JSON-serializable.

| Severity | Meaning |
|---|---|
| `FAIL` | A detected violation under the check's conditions |
| `review` | A candidate or reading work item requiring human judgment |
| `note` | Context, an informational inventory, measurement or recorded exemption |

JSON version 3 groups results by guideline ID. Every observation appears in
`findings`: reading candidates are review findings, informational rows are notes,
and aggregate measurements are summary notes with structured `data`. Text output
also includes inventories and summaries; `--json` provides their full details.

Execution completeness is separate from guideline judgment. A rule that emits
nothing is reported as `0 findings`, without implying that the full guideline
passes. `INCOMPLETE` means required input was unavailable; `ERROR` means a broken
binding, execution failure or invalid output. Both retain earlier findings.

Candidate labels describe observations the algorithm can establish. The counts
inventory uses `CONTAINS UNIVERSAL WORD` when it observes a universal word; this
cannot establish that the count serves a useful claim. A review row's `data.flags`
records heuristic observations, and empty flags do not clear its reading task.

Inventories report the measurements owned by their rule:

| Rule | Summary data fields |
|---|---|
| `geometry.layout` | `figures`, `over_width`, `loose_verticals` |
| `geometry.unicode` | `figures`, `ascii_connectors` |

A full run, or `check page.md --only geometry.layout geometry.unicode --json`,
provides the complete geometry inventory. Facts worklists label candidates
`COUNT` under `facts.two-bases` and `UNIVERSAL` under `facts.universal-claims`.
A sentence matching both appears under both rules.

Deduplication requiring knowledge of a rule stays in that module. The
self-contained check accounts for references in owning-page column cells once
and avoids duplicate named/local-link deflection reports. The reporter does not
guess equivalence from similar messages or merge observations across rules.

Human adjudication remains part of the check pass. Review findings are not
cleared automatically to make a run appear clean.

## 5. Discovery and execution

`rules.py` indexes guidelines and discovers `checks/*.py`, excluding
`__init__.py`. It reads each module's `RULE` and `check`; no central registration
is required. Imports and discovery are deterministic, and checks execute in
guideline order. This stable reporting order is not a dependency between checks.

Modules enter `sys.modules` before execution so ordinary Python features,
including dataclasses with deferred annotations, work during import.

Discovery and execution validate that:

- Guideline IDs and markers are valid, with unique IDs.
- Every `qa` requirement has exactly one check module, and every module refers to
  a requirement marked `qa`.
- Module filenames follow the convention without collisions.
- `RULE` is a valid ID and `check` is callable.
- Yielded records have valid locations, messages, severities and serializable data.

Malformed markers, missing modules, broken imports, duplicate IDs, invalid output
and unknown requested IDs are visible errors. They cannot silently remove a check
from the run.

`kg.py` consumes each iterable and records findings and execution outcomes. Errors
are caught during iteration, when a generator's body runs. Findings emitted before
an error or `MissingInput` remain in the report. Other checks continue so their
observations and remaining work are visible.

## 6. Inputs and shared parsing

`inputs.require(name)` returns a resolved, usable input or raises `MissingInput`
with a useful reason. Supported names are `tree`, `git`, `dossier` and `baseline`;
`git` returns the source tree path after checking Git availability.

Perform independent page work before work that requires another input where
practical. For example, with local helpers:

```python
def check(page, inputs):
    yield from page_only_findings(page)
    tree = inputs.require("tree")
    yield from source_findings(page, tree)
```

The runner preserves earlier findings and marks a rule incomplete when a required
input is unavailable. Excerpt introductions and OTHER SOURCES formatting can
produce page observations before source resolution; source body slices wait for
a validated tree.

Source version, cited-file cleanliness and dossier identity are validated before
dependent work. Checks use resolved inputs rather than discovering alternate
paths that bypass validation. A catalog lookup requires Git when it needs tree
resolution; work with no applicable catalog row or commit entry need not do so.

Optional absence differs from failure. A check may inspect `inputs.baseline` and
report that no differing committed baseline applies, or note that an optional
spec is absent. A failed baseline-history probe or actual read failure is an
input error, not an empty observation or evidence of an unborn repository.

The shared `inputs.git()` helper raises errors for failed commands and timeouts.
Callers explicitly allow meaningful negative results, such as `ok=(0, 1)` for
`git grep`; other failures must not become empty search results.

`pagemodel.py` owns reusable document structure and source locations: regions,
headings, paragraphs, tables and cells, spans, fences and excerpt units. Counts
and self-contained checks share its table parsing, including escaped pipes.
Separator recognition validates the whole row so negative values remain data.
Sentence helpers share normalization and baseline tracking while rule modules
retain the language heuristics that select candidates.

Add shared parsing when real callers need it. Source and dossier utilities,
anchor classification and the LINKS emitter are ordinary shared modules; checks
and emitters do not depend on another rule's registration. `dossier_utils.py`
also reads the dossier's EVIDENCE for the two facts checks (the Bases table) and
for `arrangement.units` (the recorded block map).

## 7. Commands

The command surface uses guideline IDs for checks and reading inventories:

```sh
python3 tools/qa/kg.py check page.md
python3 tools/qa/kg.py check page.md --only page.self-contained
python3 tools/qa/kg.py check page.md --only page.self-contained --json
python3 tools/qa/kg.py check page.md --checklist
python3 tools/qa/kg.py where page.self-contained
python3 tools/qa/kg.py rules
python3 tools/qa/kg.py selftest --rule page.self-contained
python3 tools/qa/kg.py selftest
python3 tools/qa/kg.py table page.md
python3 tools/qa/kg.py retro progress/usb4
python3 tools/qa/kg.py view page.md --prose
```

`where` names the guideline, implementation and corresponding test. `rules` lists
implementations by requirement. `check --only <id>` retrieves that requirement's
findings and inventory; lead sentences, summary sentences and excerpt
introductions belong to their respective rule outputs.

`table` emits the LINKS table. `view` provides page representations through
`--prose`, `--raw`, `--spans-visible` or `--regions`.
`retro` reads a campaign's dossiers and prints, per rule, what the checks found on
first passes (section 11).

A nonexistent ID or an empty explicit selection is an error. Exit codes are:

| Exit code | Meaning |
|---|---|
| `1` | A detected FAIL or engine/input error |
| `2` | Missing required inputs, without another failure |
| `0` | Complete execution without FAIL; human review may remain |

A partial `--only` run never establishes LINTED state.

## 8. Exemptions and page state

Exemptions are recorded in the dossier's LINT section:

```text
EXEMPT rule-id "fragment" [line]: ruling
```

A fragment must identify one observation under that rule; an optional line hint
resolves ambiguity. Every exemption matches against the original findings. An
earlier exemption cannot make another ambiguous fragment become unique. Stale,
ambiguous and line-only entries exempt nothing. Exemptions cannot suppress engine
errors or missing inputs.

There are no registered parts. Legacy `EXEMPT rule-id/part` entries require
re-adjudication; their suffix is not dropped to broaden their scope silently.

`lint_record.py` provides record interpretation for both the `lint.record` check
and the CLI. Page state does not depend on a check's human-readable messages.
After a complete full check pass and human adjudication, the dossier records:

```text
LINTED <date> page sha256: <digest> qa sha256: <qa-digest>
```

The QA digest deterministically hashes sorted repository-relative paths and file
bytes for guideline Markdown and executable QA Python, including the parser,
input resolver, loader, reporter and shared helpers. Tests and QA documentation
are excluded. File bytes include uncommitted changes, so a Git commit ID alone
cannot substitute for the digest.

A changed page or QA digest, or a record lacking a QA digest, returns the page to
WRITTEN and requires a new check pass. LINTED requires a current record, completed
human review and a complete full run without failures. A clean run does not
automatically create a record or establish factual correctness.

## 9. Tests and validation

Use standard-library `unittest`, inline text and small page builders. Tests need
Python 3.10+ and Git for temporary source repositories, with no external kernel
tree or dossier. Create temporary source trees and dossiers only where needed.

Each rule's corresponding test module exercises its real `check()` callable.
Cover an offending example, a similar allowed example, relevant regions and
boundaries, and missing-input behavior where applicable. Assert meaningful
observations such as location, severity, baseline provenance and structured data.

`selftest --rule <id>` validates the selected binding and executes that rule's
tests regardless of detection technique. Full `selftest` validates every binding,
requires nonempty test modules, runs rule and shared-engine tests, and validates
reference figures through the discovered geometry checks with their applicable
acceptance scope. Unknown IDs, missing or broken modules and zero executed tests
fail visibly. GitHub Actions runs the full selftest.

Shared regression tests cover discovery, imports, invalid selections and output,
generator failures, retained findings before missing inputs, input errors,
exemption ambiguity and LINT state. Algorithm and LINKS emitter tests exercise
their real implementations. Tests establish these behaviors; human review still
establishes whether a documentation page satisfies its factual requirements.

The contribution integration test adds exactly a guideline, check module and test
module, then exercises `rules`, `where`, `check`, selected selftest and full
selftest without central edits. Its temporary suite excludes the contribution
test itself to avoid recursion.

Refactoring preserves candidate scope, exceptions, severity, locations, ordering,
provenance and execution outcomes. Deliberate detection or reporting changes are
explicitly documented in the relevant contract and covered by behavior tests.
No per-rule fixture language, fixture directory or selftest scaffold is required.

## 10. Adding or extending a check

1. Find the requirement in `guidelines/` and add `qa` to its marker if needed.
2. Create or edit `checks/<id>.py`, replacing dots and hyphens with underscores.
   Keep every detector and candidate selector for that requirement together.
3. Add or update the corresponding `tests/test_<id>.py`.
4. Run the selected selftest, then the full selftest.

A new rule appears in `check`, `where`, `rules` and `selftest` without edits to a
loader, dispatcher, selector list, CLI option list or reporter. Extending an
existing rule changes its implementation and tests, plus its guideline when the
requirement changes. Shared parsing grows only when the check exposes a real
need shared with other callers.

## 11. Retiring a check

Retirement applies to checks, not to the prose a writer reads, and it rests on
what each check found across pages rather than on an impression.

The record. Before fixing anything the engine finds, a writer runs `kg check`
once over the composed page and records in the dossier's LINT, under a `First
pass` heading, the FAIL and review counts per rule exactly as printed
(dossier.md [lint.first-pass]). Together with the `EXEMPT` lines the dossier
carries in machine-readable form, every page then holds three numbers per rule:
what the check found before any fix, what was fixed, and what was judged a
false hit.

The command. `kg retro <progress dir> [--rule <id>]` reads every dossier under
the directory and prints one row per rule: pages with a record, pages where the
rule fired on the first pass, the first-pass FAIL and review totals, the
`EXEMPT` lines written against it on those pages and the share of its hits they
cover, the `EXEMPT` lines across every dossier, and the last page and date it
fired. `--rule` lists the pages instead. It is run once per
batch or campaign and changes nothing; dossiers without a record are counted in
its first line, and a rule the dossiers name that the skill no longer carries
is listed last and marked.

The thresholds, applied by a person. Over at least twenty pages: a check with no
first-pass hit is a guard the writers no longer need; it goes when it carries
maintenance (a test module, a coupling to shared parsing) and stays when it
costs nothing to run. A check whose hits are mostly exempted, seven in ten or
more, is producing reading work; its exempt logic is reworked or the check goes
and the prose stays. A check with fixed hits stays. A manual rule whose reading
rows are adjudicated "no change" page after page is merged into its neighbour
or given a form the engine can verify, which is an improvement rather than a
retirement. `retro` marks the first two cases in its last column.

Retirement is deletion. A retired check loses its module and its test and its
requirement drops the `qa` marker; a retired rule loses its sentence, with a
clause added to the neighbour that absorbs it. There is no parked state: git
history is the archive, and the `skill:` commit that retires carries the `kg
retro` numbers that justified it. After a style sweep is retired, one batch is
checked with the deleted check re-run from history, because a first-pass rate
measured while the sweep existed does not prove what writers do without it.
