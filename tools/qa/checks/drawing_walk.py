"""Checks for [drawing.walk]."""
from pagemodel import CODE_LINK, legend_entries
from report import Finding, observations
RULE = 'drawing.walk'
CLIP = 100

def walk(page, inputs):
    findings, listing = [], []
    counts = {'figures': 0, 'walked': 0, 'missing_names': 0, 'out_of_order': 0}
    details = page.section('DETAILS')
    for number, fence in enumerate(page.figures, 1):
        if details is None or not details.start <= fence.start <= details.end:
            continue
        entries, _marks = legend_entries(fence.body)
        if not entries:
            continue
        counts['figures'] += 1
        outro, line = page.outro_of(fence)
        linked = [t.strip().strip('`').rstrip('()') for t, _u in CODE_LINK.findall(outro)]
        order = []
        for e in entries:
            if e['name'] in linked:
                order.append(linked.index(e['name']))
            else:
                counts['missing_names'] += 1
                findings.append(Finding(line or fence.end, 'FAIL', f"figure {number}: the paragraph after it does not link {e['name']}() ({e['mark']}); the paragraph after a DETAILS figure walks its marks in order, one sentence per mark, the function linked"))
        if order and order != sorted(order):
            counts['out_of_order'] += 1
            findings.append(Finding(line or fence.end, 'review', f'figure {number}: the paragraph after it names the legend functions out of mark order; walk them from the first mark'))
        if not findings or all(f.line != (line or fence.end) for f in findings[-len(entries):]):
            counts['walked'] += 1
        listing.append(f"{fence.start:5} figure {number}: marks={''.join(e['mark'] for e in entries)} after={outro[:CLIP].replace(chr(10), ' ')!r}")
    footer = f"figures-with-legend={counts['figures']} walked={counts['walked']} missing-names={counts['missing_names']} out-of-order={counts['out_of_order']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    yield from walk(page, inputs)
