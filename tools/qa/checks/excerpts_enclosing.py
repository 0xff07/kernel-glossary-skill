"""Checks for [excerpts.enclosing]."""
from constructs import Construct, TITLE, constructs_of, construct_at
from inputs import source_lines
from measurements import positions_of
from pagemodel import CODE_LINK
from report import Finding, observations
import re
RULE = 'excerpts.enclosing'
CLOSER = re.compile(r'^\};?\s*$')
LINE_CLIP = 60

def enclosing(page, inputs):
    findings, listing = [], []
    counts = {'units': 0, 'top_level': 0, 'opened': 0, 'continued': 0, 'named_above': 0, 'unmapped': 0, 'findings': 0}
    tables = {}
    for fence in page.excerpts:
        opened = {}
        intro, _first = page.intro_of(fence)
        linked_above = [text.strip().strip('`') for text, _url in CODE_LINK.findall(intro)]
        for unit in fence.units:
            if not unit.path:
                continue
            counts['units'] += 1
            source = source_lines(inputs.tree, unit.path, inputs.cache)
            positions = positions_of(unit, source) if source is not None else None
            if positions is None:
                counts['unmapped'] += 1
                findings.append(Finding(unit.start, 'review', f'{unit.path}:{unit.line} could not be mapped onto the file; [excerpts.verbatim] reports why'))
                continue
            if unit.path not in tables:
                tables[unit.path] = constructs_of(source)
            constructs = tables[unit.path]
            shown = {p for p in positions if p}
            base = unit.path.rsplit('/', 1)[-1]
            touched = []
            for p in sorted(shown):
                c = construct_at(constructs, p)
                if c is None:
                    counts['top_level'] += 1
                elif c not in touched:
                    touched.append(c)
            for c in touched:
                seen = opened.setdefault(unit.path, set())
                needs_title = c.kind == 'kerneldoc' and c.start < len(source) and TITLE.match(source[c.start])
                if c.start in shown and (not needs_title or c.start + 1 in shown):
                    counts['opened'] += 1
                    seen.add(c.start)
                    listing.append(f'{unit.start:5} {base}:{unit.line} opens {c.label(base)}')
                    continue
                if c.start in seen:
                    counts['continued'] += 1
                    listing.append(f'{unit.start:5} {base}:{unit.line} continues {c.label(base)}')
                    continue
                if c.kind == 'function' and any(text in (c.name, c.name + '()') for text in linked_above):
                    counts['named_above'] += 1
                    listing.append(f'{unit.start:5} {base}:{unit.line} shows a piece of {c.label(base)}, named above the fence')
                    continue
                counts['findings'] += 1
                opener = source[c.start - 1].strip()[:LINE_CLIP]
                if c.kind == 'kerneldoc':
                    what = f'without its "/**" line and the title line beneath it; begin the unit at {base}:{c.start} and keep {source[c.start].strip()[:LINE_CLIP]!r}'
                elif c.kind == 'function':
                    what = f'without its signature, and no sentence above the fence links {c.name}(); name and link the function in the sentence above the fence, or begin the unit at {base}:{c.start} {opener!r}'
                else:
                    what = f'without its opening line; begin the unit at {base}:{c.start} {opener!r}'
                findings.append(Finding(unit.start, 'FAIL', f'{base}:{unit.line} shows lines of {c.label(base)} ({base}:{c.start}-{c.end}) {what}',
                                        {'construct': c.label(base), 'opener': c.start, 'end': c.end}))
    footer = (f"units={counts['units']} openers-shown={counts['opened']} continued={counts['continued']} named-above={counts['named_above']} "
              f"top-level-lines={counts['top_level']} unmapped={counts['unmapped']} findings={counts['findings']}")
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from enclosing(page, inputs)
