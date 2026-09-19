"""Checks for [drawing.model]."""
from report import Finding, observations
RULE = 'drawing.model'
TITLE_CLIP = 70

def model_figure(page):
    summary = page.section('SUMMARY')
    spans = [(page.lead.start, page.lead.end)] + ([(summary.start, summary.end)] if summary else [])
    return [f for f in page.figures if any(a <= f.start <= b for a, b in spans)]

def check(page, inputs):
    found = model_figure(page)
    if not found:
        at = page.section('SUMMARY').start if page.section('SUMMARY') else 1
        yield Finding(at, 'FAIL', "no model figure: the lead or SUMMARY carries the page's primary figure, the objects and relationships the page is about or the spine of its journey (figures.md [drawing.model])")
        yield from observations([], 'model-figure=absent', [], {'model_figure': None})
        return
    title = next((l.strip()[:TITLE_CLIP] for l in found[0].body if l.strip()), '')
    yield from observations([], f'model-figure=present at={found[0].start}', [f'{found[0].start:5} model figure: {title}'], {'model_figure': found[0].start})
