"""Checks for [excerpts.verbatim]."""
from report import Finding
from report import observations
from inputs import source_lines
from pagemodel import ELISION
import re
RULE = 'excerpts.verbatim'
RESYNC_WINDOW = 600
MESSAGE_CLIP = 70
UNIT_CLIP = 60
RESYNC_CLIP = 60
# A column-0 closing brace after an elision is the construct's own end, the first one to follow.
CLOSER = re.compile(r'^\};?\s*$')

def resynchronise(source, position, line):
    limit = min(position + RESYNC_WINDOW, len(source))
    for q in range(position, limit):
        if source[q] == line:
            return q
    return None

def compare_unit(unit, source, findings, counts):
    if unit.line < 1:
        findings.append(Finding(unit.fence.start, 'FAIL', f'{unit.path}:{unit.line} cites no line of the file (lines count from 1)'))
        counts['bad'] += 1
        return
    position = unit.line - 1
    first = True
    after_elision = False
    for line in unit.lines:
        if line.strip() == ELISION:
            counts['elisions'] += 1
            after_elision = True
            continue
        if position < len(source) and source[position] == line:
            first = False
            after_elision = False
            position += 1
            continue
        found = resynchronise(source, position, line) if after_elision else None
        if found is None or first:
            what = 'does not begin at the cited line' if first else f'mismatch at source line {position + 1}'
            findings.append(Finding(unit.fence.start, 'FAIL', f'{unit.path}:{unit.line} {what}: {line[:MESSAGE_CLIP]!r}'))
            counts['bad'] += 1
            return
        counts['resyncs'] += 1
        if source.count(line) > 1 and not CLOSER.match(line):
            findings.append(Finding(unit.fence.start, 'FAIL', f'{unit.path}:{unit.line} elision resynchronises on a line that occurs {source.count(line)} times in the file; split the block into two units: {line.strip()[:RESYNC_CLIP]!r}'))
            counts['bad'] += 1
            return
        position = found + 1
        first = False
        after_elision = False

def verbatim(page, inputs):
    findings, listing = ([], [])
    counts = {'elisions': 0, 'resyncs': 0, 'bad': 0}
    for unit in page.units:
        if not unit.path:
            findings.append(Finding(unit.fence.start, 'FAIL', f'unit without a provenance comment: {unit.lines[0][:UNIT_CLIP]!r}'))
            counts['bad'] += 1
            continue
        source = source_lines(inputs.tree, unit.path, inputs.cache)
        if source is None:
            findings.append(Finding(unit.fence.start, 'FAIL', f'{unit.path} cannot be opened under the tree'))
            counts['bad'] += 1
            verdict = 'BAD'
        else:
            before = counts['bad']
            compare_unit(unit, source, findings, counts)
            verdict = 'BAD' if counts['bad'] > before else 'ok'
        listing.append(f'{unit.fence.start:5} {unit.path}:{unit.line} {len(unit.lines)} lines {verdict}')
    footer = f"excerpts: C blocks={len(page.excerpts)} units={len(page.units)} elisions={counts['elisions']} resyncs={counts['resyncs']} findings={counts['bad']}"
    yield from observations(findings, footer, listing, {'blocks': len(page.excerpts), 'units': len(page.units), **counts})

def check(page, inputs):
    inputs.require('tree')
    yield from verbatim(page, inputs)
