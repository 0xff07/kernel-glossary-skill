"""Checks for [arrangement.route]."""
from pagemodel import sentences_of
from report import Finding, observations
RULE = 'arrangement.route'
MIN_SENTENCES, MAX_SENTENCES = 3, 5
CLIP = 110

def route(page, inputs):
    findings, listing = [], []
    if page.section('DETAILS') is None or not page.subsections:
        yield from observations([], 'route=absent (no DETAILS subsections)', [], {'route': None})
        return
    paragraphs = page.paragraph_texts(page.details_preamble)
    if not paragraphs:
        findings.append(Finding(page.section('DETAILS').start, 'FAIL', 'DETAILS opens on its first subsection; open it with the route paragraph, three to five sentences naming in order what the subsections establish'))
        yield from observations(findings, 'route=absent sentences=0', [], {'route': False, 'sentences': 0})
        return
    line, text = paragraphs[0]
    sentences = sentences_of(text)
    if not MIN_SENTENCES <= len(sentences) <= MAX_SENTENCES:
        findings.append(Finding(line, 'review', f'the route paragraph has {len(sentences)} sentences; three to five name the order of the subsections without walking them'))
    if len(paragraphs) > 1:
        findings.append(Finding(paragraphs[1][0], 'review', f'{len(paragraphs)} paragraphs before the first subsection; the route is one paragraph, an actor table may follow it'))
    for k, sentence in enumerate(sentences, 1):
        listing.append(f'{line:5} route {k}: {sentence[:CLIP]}')
    footer = f'route=present sentences={len(sentences)} subsections={len(page.subsections)}'
    yield from observations(findings, footer, listing, {'route': True, 'sentences': len(sentences)})

def check(page, inputs):
    yield from route(page, inputs)
