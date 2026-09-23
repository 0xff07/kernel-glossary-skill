# QA checks by guideline

One guideline ID owns one Python module and one test module. A `[section.name, qa]`
marker connects the guideline to `checks/section_name.py`; unmarked requirements
remain manual. The only check interface is `RULE` and `check(page, inputs)`.

## Run

```sh
python3 tools/qa/kg.py check page.md
python3 tools/qa/kg.py check page.md --only page.self-contained --json
python3 tools/qa/kg.py check page.md --checklist
python3 tools/qa/kg.py check page.md --first-pass
python3 tools/qa/kg.py where page.self-contained
python3 tools/qa/kg.py rules
python3 tools/qa/kg.py selftest --rule page.self-contained
python3 tools/qa/kg.py selftest
python3 tools/qa/kg.py table page.md
python3 tools/qa/kg.py retro progress/usb4
python3 tools/qa/kg.py view page.md --prose
```

`view` also accepts `--raw`, `--spans-visible` or `--regions`. Reading inventories
belong to checks: use `check --only <id>` to retrieve them. See
[checking.md](../../guidelines/checking.md) for the inventory-to-guideline mapping.

The resolver uses the existing checkout conventions for the kernel tree,
`progress/<campaign>/<dir>/<group>/<slug>.worksheet.md` (the campaign being the page's
top directory under `docs/`, or the basename of `--spec`), the differing committed page at
`HEAD`, and `campaigns/<dir>.md` (a campaign whose short name differs from the
docs directory passes `--spec` at every check). Override them with `--tree`, `--worksheet`,
`--spec`, or `KG_TREE`, `KG_WORKSHEET`. Check pages in place so their worksheet and
baseline resolve. Source version and cited-file cleanliness are validated before
dependent work; the worksheet is read as found, since every row a check takes from it
is matched to the page or the tree.

## Add or extend a check

1. Find the requirement in `guidelines/`. Add `qa` to its marker if needed.
2. Edit `checks/<id>.py`, replacing dots and hyphens in the ID with underscores.
   Keep every detector and candidate selector for that requirement together.
3. Add or update `tests/test_<id>.py`. Test the real `check()` with an offending
   example, a similar allowed example, relevant regions and boundaries, and missing
   input behavior where applicable. Use `unittest`, inline text and temporary files.
4. Run the selected selftest, then the full selftest.

For example, the core of a heading check can be this small:

```python
from report import Finding

RULE = "style.counting-headings"


def check(page, inputs):
    for row in page.prose_view():
        if row.region == "heading" and not row.in_catalog:
            if row.text[:1].isdigit():
                yield Finding(row.line, "FAIL", "heading opens with a number")
```

This example illustrates the interface; the actual counting-heading check also
recognizes word numerals. A rule may call local helpers or ordinary shared
functions from `patterns.py` and `measurements.py`. The facts checks share sentence
normalization, baseline tracking and presentation through `sentence_utils.py`;
each rule keeps its own candidate-selection regexes. There is no registry, descriptor,
kind, registered part, or second command to add. New bindings are discovered in
all commands. `where` names the guideline, implementation and corresponding test.

The shared `Page` supplies regions, headings, paragraphs, fences, excerpt units,
spans, tables and cells with source locations. Add shared parsing only when needed
by real callers. Keep guideline judgments, regexes and thresholds with their rule.
Helpers shared by several rules live outside `checks/`.

A check reads its arguments and yields `Finding(line, severity, message, data=None)`.
It does not print, edit files, create result objects, call another check's entry
point, or carry a separate CLI. `data` must be JSON-serializable; a line is a
positive page line number or `None`.

```python
def check(page, inputs):
    yield from page_only_findings(page)
    tree = inputs.require("tree")
    yield from source_findings(page, tree)
```

`require()` returns a resolved input or raises `MissingInput`. Supported inputs
are `tree`, `git` (returns the source tree path), `worksheet` and `baseline`.
The runner catches missing inputs and errors during iteration, retains findings
already yielded, and continues other checks. A baseline may be intentionally
optional: inspect `inputs.baseline` and emit a note if no differing committed page
exists. An actual baseline read failure is an input error.

The shared `inputs.git()` helper raises an error for failed commands and timeouts.
Where a Git operation defines a negative search result, explicitly allow that
return code (for example, `ok=(0, 1)` for `git grep`). Do not turn execution errors
into empty observations. Optional work with no applicable catalog row or commit
entry need not require Git.

## Interpret a run

| Output | Meaning |
|---|---|
| `FAIL` | Detected violation under the check's conditions |
| `review` | Candidate or reading work item requiring human judgment |
| `note` | Context, inventory, measurement or recorded exemption |
| `INCOMPLETE` | Required input was unavailable; earlier findings remain valid |
| `ERROR` | Broken binding, checker failure or invalid output |
| `0 findings` | Nothing emitted; not a judgment that the full guideline passes |

JSON version 3 groups results by guideline ID. Every observation is in `findings`;
former listing rows and footer measurements now appear as findings and summary
notes with `data`. Text output includes them too. A review row's `data.flags`
records what the heuristic observed, without declaring that the full guideline
passed. Empty flags do not clear the reading task.

Measurements live with the rule that owns them: `geometry.layout` reports width
and loose verticals, while `geometry.unicode` reports ASCII connectors. Request
both with `check page.md --only geometry.layout geometry.unicode --json` for the
complete geometry inventory. Facts worklists label their own candidates `COUNT`
or `UNIVERSAL`; a sentence matching both appears under both rules.

Exit 1 means a FAIL or engine/input error; exit 2 means missing required inputs
without another failure; exit 0 means complete execution without FAIL. Human review
can remain at exit 0. `--only` never establishes LINTED state.

Exemptions use `EXEMPT rule-id "fragment" [line]: ruling` in the worksheet's LINT
section. A fragment must match one observation; a line hint resolves ambiguity.
Stale, ambiguous and line-only entries exempt nothing. Legacy `rule-id/part`
entries require re-adjudication. Exemptions cannot suppress execution errors or
missing inputs.

After the full check pass and human adjudication, record the digests printed by
that run:

```text
LINTED <date> page sha256: <digest> qa sha256: <qa-digest>
```

The QA digest includes guideline Markdown and executable QA Python, including
shared helpers; tests, this README and the reporting-only modules `retro.py` and
`triage.py` are excluded, since they read findings and produce none. Either changed digest, or an
old record without a QA digest, returns the page to WRITTEN. Records are never
created automatically from a clean run.

## Retire a check

`python3 tools/qa/kg.py check <page> --first-pass` writes a page's first-pass counts per
rule beside its worksheet, once. `python3 tools/qa/kg.py retro progress/<campaign>` sums
those records and the `EXEMPT` lines of the worksheets and prints, per rule, the records
naming it, those where it fired, its first-pass FAIL and review totals and its `EXEMPT`
lines; `--rule <id>` lists the pages instead. [DESIGN.md](DESIGN.md) section 12 says how
the numbers turn into a retirement.

## Validation and maintenance

Full selftest validates all bindings, requires a nonempty test module for every
rule, executes rule and shared engine tests, and checks all reference figures.
Selected selftest executes that rule's tests regardless of its detection technique.
Unknown IDs, missing tests, zero executed tests and broken modules fail visibly.
Tests need Python 3.10+ and Git for temporary source repositories, with no external
kernel tree or worksheet. The GitHub Actions workflow runs the full selftest.

`rules.py` owns discovery and binding validation; `kg.py` executes checks;
`inputs.py` resolves inputs; `pagemodel.py` parses pages; `report.py` reports findings
and applies exemptions; `lint_record.py` interprets records and hashes QA sources;
`selftest.py` validates tests and reference figures. Shared source/worksheet utilities
and the LINKS emitter remain ordinary modules beside them.

[DESIGN.md](DESIGN.md) defines the current design principles and check contract.
The contribution integration test demonstrates a new rule entering all commands
through exactly three files.
