"""Checks for [purpose.spine]."""
from report import reading
from report import Row
import re
RULE = 'purpose.spine'
RUN_REVIEW = 6
FRACTION_REVIEW = 0.5
MIN_RUN = 3
SPAN_SYMBOL = re.compile('`(?:struct |enum |union )?([A-Za-z_]\\w*)(?:\\(\\))?`')
TITLE_CLIP = 60

def subsection_first_symbol(page, inputs):
    names = page.catalog_names
    order = {name: i for i, name in enumerate(names)}
    pattern = re.compile('\\b(' + '|'.join((re.escape(n) for n in names)) + ')\\b') if names else None
    rows = []
    sequence = []
    for sub in page.subsections:
        opening = next((l for _n, l in sub['numbered'] if l.strip() and (not l.startswith(('```', '|', '#')))), '')
        found = None
        for text in (sub['title'], opening):
            hits = [(m.start(), m.group(1)) for m in SPAN_SYMBOL.finditer(text) if m.group(1) in order]
            if not hits and pattern:
                hits = [(m.start(), m.group(0)) for m in pattern.finditer(text)]
            if hits:
                found = min(hits)[1]
                break
        sequence.append(order.get(found))
        rows.append(Row(sub['line'], f"{sub['line']:5} {sub['title'][:TITLE_CLIP]:60} -> {found or '-'}", set()))
    best = run = 0
    for before, after in zip(sequence, sequence[1:]):
        run = run + 1 if before is not None and after is not None and (after > before) else 0
        best = max(best, run + 1 if run else 0)
    with_symbol = sum((1 for p in sequence if p is not None))
    threshold = min(RUN_REVIEW, max(MIN_RUN, int(len(page.subsections) * FRACTION_REVIEW)))
    if page.subsections and best >= threshold:
        rows.append(Row(None, f'{best} consecutive DETAILS subsections follow the catalog order (the spine is a journey, not the catalog; read the headings)', {'catalog-order-run'}))
    footer = f'spine: subsections={len(page.subsections)} subsections-with-a-symbol={with_symbol} longest-run-in-catalog-order={best}'
    yield from reading(rows, [], footer, {'subsections': len(page.subsections), 'with_catalog_symbol': with_symbol, 'longest_catalog_order_run': best}, severity='review')

def check(page, inputs):
    yield from subsection_first_symbol(page, inputs)
