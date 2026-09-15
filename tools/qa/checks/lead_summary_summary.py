"""Checks for [lead-summary.summary]."""
from report import Finding
from report import reading
from report import Row
from measurements import measure
from pagemodel import sentences_of
from pagemodel import word_count
RULE = 'lead-summary.summary'
MAX_TABLE_ROWS = 6
MAX_TABLE_COLUMNS = 4

def summary_shape(page):
    blocks = page.summary_blocks()
    section = page.section('SUMMARY')
    if blocks is None:
        return [Finding(None, 'FAIL', 'no SUMMARY section')]
    line = section.start + 1
    tables = [v for k, v in blocks if k == 'T']
    figures = [v for k, v in blocks if k == 'D']
    excerpts = sum((1 for k, _v in blocks if k == 'C'))
    out = []
    if excerpts:
        out.append(Finding(line, 'FAIL', f'SUMMARY: {excerpts} source excerpt(s)'))
    for kind, _v in blocks:
        if kind == 'Q':
            out.append(Finding(line, 'FAIL', 'SUMMARY: a fence that is neither source nor figure'))
    if tables and figures:
        out.append(Finding(line, 'FAIL', 'SUMMARY: a table and a figure'))
    if len(tables) > 1 or len(figures) > 1:
        out.append(Finding(line, 'FAIL', 'SUMMARY: more than one structured block'))
    for rows, columns in tables:
        if rows > MAX_TABLE_ROWS or columns > MAX_TABLE_COLUMNS:
            out.append(Finding(line, 'FAIL', f'SUMMARY: table {rows} rows x {columns} columns'))
    if blocks and blocks[0][0] != 'P':
        out.append(Finding(line, 'FAIL', f'SUMMARY: opens with {blocks[0][0]}'))
    if blocks and blocks[-1][0] != 'P':
        out.append(Finding(line, 'FAIL', f'SUMMARY: ends with {blocks[-1][0]}'))
    return out
SENTENCE_CLIP = 150

def summary_sentences(page, inputs):
    blocks = page.summary_blocks()
    section = page.section('SUMMARY')
    if blocks is None:
        yield from reading([], [(None, 'no SUMMARY section')], 'SUMMARY absent', {}, severity='review')
        return
    paragraphs = [v for k, v in blocks if k == 'P']
    found = [s for p in paragraphs for s in sentences_of(p)]
    words = sum((word_count(p) for p in paragraphs))
    kinds = ' '.join((k for k, _v in blocks))
    tables = [v for k, v in blocks if k == 'T']
    figures = [v for k, v in blocks if k == 'D']
    shape = ', '.join([f'table {r}x{c}' for r, c in tables] + [f'figure {s} lines' for s in figures]) or 'none'
    rows = [Row(section.start, '  SUMMARY sentences (tag each M, J, I or B in the dossier):', set())]
    rows += [Row(section.start, f'   {n:2} [ ] {s[:SENTENCE_CLIP]}', set()) for n, s in enumerate(found, 1)]
    footer = f"SUMMARY words={words} paragraphs={len(paragraphs)} sentences={len(found)} excerpts={sum((1 for k, _v in blocks if k == 'C'))} blocks={kinds} dense={shape}"
    yield from reading(rows, [], footer, {'words': words, 'paragraphs': len(paragraphs), 'sentences': found, 'blocks': kinds}, severity='review')

def check(page, inputs):
    yield from measure(page, 'summary', 'words', where='without-block', normal=[80, 160], review=160, fail=300, note_below=True, name='summary')
    yield from measure(page, 'summary', 'words', where='with-block', normal=[60, 140], review=140, fail=220, name='summary')
    yield from measure(page, 'summary', 'sentences', normal=[4, 6], review=6, fail=9, name='summary')
    yield from measure(page, 'summary', 'paragraphs', review=2, fail=3, name='summary')
    yield from measure(page, 'summary', 'figure-lines', normal=[8, 80], review=80, name='summary')
    yield from summary_shape(page)
    yield from summary_sentences(page, inputs)
