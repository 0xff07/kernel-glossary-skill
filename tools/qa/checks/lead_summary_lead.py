"""Checks for [lead-summary.lead]."""
from report import Finding
from report import reading
from report import Row
from measurements import measure
from pagemodel import sentences_of
from pagemodel import word_count
RULE = 'lead-summary.lead'

def lead_shape(page):
    blocks = page.lead_blocks()
    figures = [v for k, v in blocks if k == 'D']
    out = []
    for kind, _v in blocks:
        if kind in 'CTLQ':
            out.append(Finding(1, 'FAIL', 'lead: ' + {'C': 'a source excerpt', 'T': 'a table', 'L': 'a list', 'Q': 'a fence that is neither source nor figure'}[kind]))
    if len(figures) > 1:
        out.append(Finding(1, 'FAIL', f'lead: {len(figures)} figures'))
    if blocks and blocks[0][0] != 'P':
        out.append(Finding(1, 'FAIL', f'lead: opens with {blocks[0][0]}'))
    return out
SENTENCE_CLIP = 150

def lead_sentences(page, inputs):
    blocks = page.lead_blocks()
    paragraphs = [v for k, v in blocks if k == 'P']
    found = [s for p in paragraphs for s in sentences_of(p)]
    words = sum((word_count(p) for p in paragraphs))
    kinds = ' '.join((k for k, _v in blocks))
    figures = [v for k, v in blocks if k == 'D']
    rows = [Row(1, '  lead sentences (tag each purpose, position or promise in the dossier):', set())]
    rows += [Row(1, f'   {n:2} [ ] {s[:SENTENCE_CLIP]}', set()) for n, s in enumerate(found, 1)]
    footer = f"LEAD words={words} paragraphs={len(paragraphs)} sentences={len(found)} blocks={kinds} figure={', '.join((f'{s} lines' for s in figures)) or 'none'}"
    yield from reading(rows, [], footer, {'words': words, 'paragraphs': len(paragraphs), 'sentences': found, 'blocks': kinds}, severity='review')

def check(page, inputs):
    yield from measure(page, 'lead', 'words', normal=[60, 120], review=120, fail=220, note_below=True, name='lead')
    yield from measure(page, 'lead', 'sentences', normal=[4, 6], review=6, fail=8, name='lead')
    yield from measure(page, 'lead', 'paragraphs', review=2, fail=3, name='lead')
    yield from measure(page, 'lead', 'figure-lines', normal=[8, 80], review=80, name='lead')
    yield from lead_shape(page)
    yield from lead_sentences(page, inputs)
