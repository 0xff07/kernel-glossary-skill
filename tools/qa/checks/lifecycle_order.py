"""Checks for [lifecycle.order]."""
import re
from inputs import source_lines
from measurements import positions_of
from pagemodel import MARKS, mark_index
from report import Finding, observations
from worksheet_utils import lifecycle_rows
RULE = 'lifecycle.order'
SITE = re.compile(r'^([\w./-]+):(\d+)$')

def first_showing(page, inputs, file, line):
    """The page line of the first excerpt unit reproducing file:line, or None."""
    for unit in page.units:
        if not unit.path or unit.path.split('/')[-1] != file.split('/')[-1]:
            continue
        source = source_lines(inputs.tree, unit.path, inputs.cache)
        positions = positions_of(unit, source) if source is not None else None
        if positions and line in positions:
            return unit.start
    return None

def order(page, inputs):
    findings, listing = [], []
    rows = [r for r in lifecycle_rows(inputs) if r['mark'] in MARKS and SITE.match(r['site'])]
    counts = {'marks': 0, 'shown': 0, 'inversions': 0}
    by_object = {}
    for row in rows:
        by_object.setdefault(row['object'], []).append(row)
    for obj, orows in by_object.items():
        orows.sort(key=lambda r: mark_index(r['mark']))
        shown = []
        for r in orows:
            counts['marks'] += 1
            m = SITE.match(r['site'])
            at = first_showing(page, inputs, m.group(1), int(m.group(2)))
            if at is None:
                listing.append(f"      {obj} {r['mark']} {r['writer']} {r['site']}: not reproduced")
                continue
            counts['shown'] += 1
            shown.append((r['mark'], r['writer'], at))
            listing.append(f"{at:5} {obj} {r['mark']} {r['writer']} {r['site']}")
        for (m1, w1, a1), (m2, w2, a2) in zip(shown, shown[1:]):
            if a2 < a1:
                counts['inversions'] += 1
                findings.append(Finding(a2, 'review', f'{obj}: the walk shows {m2} {w2}() at page {a2} before {m1} {w1}() at page {a1}; DETAILS follows the lifecycle order unless the page says why not'))
    footer = f"marks={counts['marks']} shown={counts['shown']} inversions={counts['inversions']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('worksheet')
    inputs.require('tree')
    yield from order(page, inputs)
