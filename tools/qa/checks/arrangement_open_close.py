"""Checks for [arrangement.open-close]."""
from report import Finding
from pagemodel import DENSE
RULE = 'arrangement.open-close'
OPENING_SENTENCES = 4
CLOSING_SENTENCES = 3

def prose_open(page):
    out = []
    for sub in page.subsections:
        if not sub['blocks']:
            continue
        opening = sub['blocks'][0]
        title = sub['title'][:40]
        if opening.kind != 'P':
            out.append(Finding(opening.line, 'review', f'[{title}] opens with {opening.kind}@{opening.line}'))
        elif opening.stats[1] > OPENING_SENTENCES:
            out.append(Finding(opening.line, 'review',
                               f'[{title}] opening P {opening.stats[1]} sentences (at most {OPENING_SENTENCES})'))
    return out

def prose_close(page):
    out = []
    for sub in page.subsections:
        if not sub['blocks']:
            continue
        closing = sub['blocks'][-1]
        title = sub['title'][:40]
        if closing.kind != 'P':
            out.append(Finding(closing.line, 'review', f'[{title}] ends with {closing.kind}@{closing.line}'))
        elif closing.stats[1] > CLOSING_SENTENCES:
            out.append(Finding(closing.line, 'review',
                               f'[{title}] closing P {closing.stats[1]} sentences (at most {CLOSING_SENTENCES})'))
    return out

def no_adjacent_blocks(page):
    out = []
    for sub in page.subsections:
        chain = []
        for block in sub['blocks']:
            if block.kind == 'P':
                chain = []
            elif block.kind in DENSE:
                if chain:
                    names = ' -> '.join((f'{k}@{m}' for k, m in chain))
                    kinds = {k for k, _m in chain[1:]} | ({'H'} if chain[0][0] == 'H' else set())
                    parts = [p for p, k in (('a heading', 'H'), ('a list', 'l')) if k in kinds]
                    note = f" ({' and '.join(parts)} is not recovery)" if parts else ''
                    out.append(Finding(chain[0][1], 'review', f"[{sub['title'][:40]}] {names} -> {block.kind}@{block.line} no prose between{note}"))
                chain = [(block.kind, block.line)]
            elif block.kind == 'H':
                chain.append((block.kind, block.line))
            elif chain:
                chain.append((block.kind, block.line))
    return out

def check(page, inputs):
    yield from prose_open(page)
    yield from prose_close(page)
    yield from no_adjacent_blocks(page)
