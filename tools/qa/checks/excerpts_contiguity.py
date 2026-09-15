"""Checks for [excerpts.contiguity]."""
from pagemodel import ELISION
from report import Finding, observations
import re
RULE = 'excerpts.contiguity'
MAX_ELISIONS = 2
MIN_RUN = 3
CLOSING = re.compile(r'^\s*(\}|\};|\*/)\s*$')

def runs_of(unit):
    """The runs of reproduced lines between the unit's elisions, in order."""
    runs, current = [], []
    for line in unit.lines:
        if line.strip() == ELISION:
            runs.append(current)
            current = []
        else:
            current.append(line)
    runs.append(current)
    return runs

def contiguity(page, inputs):
    findings, listing = [], []
    counts = {'units': 0, 'elisions': 0, 'elided': 0, 'findings': 0}
    for unit in page.units:
        if not unit.path:
            continue
        counts['units'] += 1
        # Every declared elision, the stitch before a later unit included, so the count agrees
        # with excerpts.verbatim's; 'elided' counts the units whose own runs an elision separates.
        counts['elisions'] += sum(1 for line in unit.lines if line.strip() == ELISION)
        runs = runs_of(unit)
        base = unit.path.rsplit('/', 1)[-1]
        problems = []
        if len(runs) > 1 and not runs[-1]:
            # A trailing elision before the next unit's provenance comment is the fence's stitch;
            # one that ends the fence truncates the construct.
            if unit is unit.fence.units[-1]:
                problems.append('ends on an elision, which truncates the construct; end on a line of it or on its closing line')
            runs.pop()
        elisions = len(runs) - 1
        if not elisions and not problems:
            continue
        counts['elided'] += 1
        if elisions > MAX_ELISIONS:
            problems.append(f'{elisions} elisions, at most {MAX_ELISIONS}: one after the opening line and one before the closing line')
        for k, run in enumerate(runs[1:], 1):
            closing = k == len(runs) - 1 and run and all(CLOSING.match(line) for line in run)
            if len(run) < MIN_RUN and not closing:
                shown = ' / '.join(line.strip()[:40] for line in run) or 'nothing'
                problems.append(f'a run of {len(run)} after an elision ({shown!r}), at least {MIN_RUN} lines unless it is the closing line alone')
        listing.append(f'{unit.start:5} {base}:{unit.line} elisions={elisions} runs={"+".join(str(len(r)) for r in runs)}')
        for problem in problems:
            counts['findings'] += 1
            findings.append(Finding(unit.start, 'FAIL', f'{base}:{unit.line} is fragmented: {problem}', {'elisions': elisions, 'runs': [len(r) for r in runs]}))
    footer = f"units={counts['units']} elisions={counts['elisions']} elided={counts['elided']} findings={counts['findings']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    yield from contiguity(page, inputs)
