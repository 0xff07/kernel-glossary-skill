"""Checks for [links.bare-spans]."""
from report import Finding
from report import reading
from report import Row
import re
from pagemodel import BARE_SPAN
from pagemodel import CODE_LINK_ANY
RULE = 'links.bare-spans'
CELL_LITERAL = re.compile('^(0x[0-9a-fA-F]+|\\d+|-E[A-Z0-9]+|\\".*\\"|\'.*\'|true|false|NULL|default|else|return|if)$')

def every_cell_span_linked(page):
    out = []
    positions = {}
    for n, line in page.raw_view():
        if not line.startswith('|'):
            continue
        for cell in BARE_SPAN.findall(CODE_LINK_ANY.sub(' ', line)):
            positions.setdefault(cell, []).append(n)
    for cell, at in sorted(positions.items()):
        if CELL_LITERAL.match(cell.strip()):
            out.append(Finding(at[0], 'note', f'bare literal cell `{cell}` at {at[:3]} (a literal is a settled bare span)'))
        else:
            out.append(Finding(at[0], 'review', f'bare cell `{cell}` at {at[:3]} (link it, or record the settled class)'))
    return out

def bare_spans(page, inputs):
    from span_utils import bare_span_rows
    rows = [Row(span.at[0] if span.region == 'prose' and span.at else None, text, set()) for span, text in bare_span_rows(page)]
    footer = f"bare-only-prose={len(page.bare_only_spans('prose'))} bare-only-catalog-text={len(page.bare_only_spans('catalog'))} bare-occurrences={page.bare_occurrences()}"
    yield from reading(rows, [], footer, {'bare_only_prose': len(page.bare_only_spans('prose'))}, severity='review')

def check(page, inputs):
    yield from every_cell_span_linked(page)
    yield from bare_spans(page, inputs)
