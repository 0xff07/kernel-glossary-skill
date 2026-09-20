"""Checks for [drawing.walk]."""
from pagemodel import CODE_LINK, legend_entries
from report import Finding, observations
RULE = 'drawing.walk'
CLIP = 100

def walk(page, inputs):
    findings, listing = [], []
    counts = {'figures': 0, 'walked': 0, 'missing_names': 0, 'missing_marks': 0, 'out_of_order': 0}
    details = page.section('DETAILS')
    for number, fence in enumerate(page.figures, 1):
        if details is None or not details.start <= fence.start <= details.end:
            continue
        entries, _marks = legend_entries(fence.body)
        if not entries:
            continue
        counts['figures'] += 1
        before = len(findings)
        outro, line = page.outro_of(fence)
        at = line or fence.end
        linked = [t.strip().strip('`').rstrip('()') for t, _u in CODE_LINK.findall(outro)]
        link_order, mark_order = [], []
        for e in entries:
            if e['name'] in linked:
                link_order.append(linked.index(e['name']))
            else:
                counts['missing_names'] += 1
                findings.append(Finding(at, 'FAIL', f"figure {number}: the paragraph after it does not link {e['name']}() ({e['mark']}); the paragraph after a DETAILS figure walks its marks in order, one sentence per mark naming the mark, the function linked"))
            position = outro.find(e['mark'])
            if position < 0:
                counts['missing_marks'] += 1
                findings.append(Finding(at, 'FAIL', f"figure {number}: the paragraph after it does not name mark {e['mark']} ({e['name']}()); each sentence of the walk names its mark so the reader can pair it with the drawing"))
            else:
                mark_order.append(position)
        if (link_order and link_order != sorted(link_order)) or (mark_order and mark_order != sorted(mark_order)):
            counts['out_of_order'] += 1
            findings.append(Finding(at, 'review', f'figure {number}: the paragraph after it walks the marks out of order; walk them from the first mark'))
        if len(findings) == before:
            counts['walked'] += 1
        listing.append(f"{fence.start:5} figure {number}: marks={''.join(e['mark'] for e in entries)} after={outro[:CLIP].replace(chr(10), ' ')!r}")
    footer = f"figures-with-legend={counts['figures']} walked={counts['walked']} missing-names={counts['missing_names']} missing-marks={counts['missing_marks']} out-of-order={counts['out_of_order']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    yield from walk(page, inputs)
