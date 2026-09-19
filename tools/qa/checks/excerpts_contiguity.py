"""Checks for [excerpts.contiguity]."""
from constructs import constructs_of, construct_at
from inputs import source_lines
from measurements import positions_of
from pagemodel import is_elision
from report import Finding, observations
import re
RULE = 'excerpts.contiguity'
MAX_DEFINITION_ELISIONS = 1
MIN_RUN = 3
CLOSING = re.compile(r'^\s*(\}|\};|\*/)\s*$')

def runs_of(unit):
    """The runs of reproduced lines between the unit's elisions, in order."""
    runs, current = [], []
    for line in unit.lines:
        if is_elision(line):
            runs.append(current)
            current = []
        else:
            current.append(line)
    runs.append(current)
    return runs

def construct_of_unit(unit, inputs, tables):
    """The file-scope construct the unit's first reproduced line lies in: a Construct, 'top-level'
    for a line outside every construct, or None when there is no tree or the unit does not map."""
    tree = getattr(inputs, 'tree', None) if inputs is not None else None
    if not tree or not unit.path:
        return None
    source = source_lines(tree, unit.path, inputs.cache)
    if source is None:
        return None
    positions = positions_of(unit, source)
    shown = [p for p in positions or [] if p]
    if not shown:
        return None
    if unit.path not in tables:
        tables[unit.path] = constructs_of(source)
    return construct_at(tables[unit.path], shown[0]) or 'top-level'

def contiguity(page, inputs):
    findings, listing = [], []
    counts = {'units': 0, 'elisions': 0, 'elided': 0, 'in_functions': 0, 'findings': 0}
    tables = {}
    for unit in page.units:
        if not unit.path:
            continue
        counts['units'] += 1
        elisions = sum(1 for line in unit.lines if is_elision(line))
        if not elisions:
            continue
        counts['elisions'] += elisions
        counts['elided'] += 1
        runs = runs_of(unit)
        base = unit.path.rsplit('/', 1)[-1]
        problems = []
        if not runs[-1]:
            if unit is unit.fence.units[-1]:
                problems.append('ends on an elision, which truncates the construct; end on a line of it or on its closing line')
            else:
                problems.append("ends on an elision before the next unit's provenance comment; the comment marks the jump, so drop the `...`")
            runs.pop()
        inner = len(runs) - 1
        construct = construct_of_unit(unit, inputs, tables)
        kind = getattr(construct, 'kind', construct)
        if kind == 'function' and inner:
            counts['in_functions'] += 1
            problems.append(f'elides inside {construct.name}(): nothing inside a function is elided; show the stage whole, or walk the function through in consecutive pieces ([excerpts.walkthrough])')
        elif inner > MAX_DEFINITION_ELISIONS:
            problems.append(f'{inner} elisions, at most one: a single run of members the page never mentions')
        if kind != 'function':
            for k, run in enumerate(runs[1:], 1):
                closing = k == len(runs) - 1 and run and all(CLOSING.match(line) for line in run)
                if len(run) < MIN_RUN and not closing:
                    shown = ' / '.join(line.strip()[:40] for line in run) or 'nothing'
                    problems.append(f'a run of {len(run)} after an elision ({shown!r}), at least {MIN_RUN} lines unless it is the closing line alone')
        where = f' in {construct.label(base)}' if hasattr(construct, 'label') else ''
        listing.append(f'{unit.start:5} {base}:{unit.line} elisions={inner} runs={"+".join(str(len(r)) for r in runs)}{where}')
        for problem in problems:
            counts['findings'] += 1
            findings.append(Finding(unit.start, 'FAIL', f'{base}:{unit.line} is fragmented: {problem}', {'elisions': inner, 'runs': [len(r) for r in runs]}))
    footer = f"units={counts['units']} elisions={counts['elisions']} elided={counts['elided']} in-functions={counts['in_functions']} findings={counts['findings']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    yield from contiguity(page, inputs)
