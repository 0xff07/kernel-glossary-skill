"""Checks for [arrangement.figure-placement]."""
from report import reading
from report import Row
RULE = 'arrangement.figure-placement'
FINDING_CLIP = 40

def figure_distribution(page, inputs):
    rows, notes = ([], [])
    measures = [{'figures': s['figures'], 'words': s['words'], 'source': s['source']} for s in page.subsections]
    info_runs = []
    run = {'subs': 0, 'words': 0, 'source': 0, 'first': None, 'last': None}
    with_figures = total = 0
    for sub, m in zip(page.subsections, measures):
        if m['figures']:
            with_figures += 1
            total += m['figures']
            rows.append(Row(sub['line'], f"figures: {m['figures']} in [{sub['title'][:FINDING_CLIP]}] after {run['subs']} subsection(s), {run['words']} prose words and {run['source']} source lines without one", set()))
            if run['subs']:
                info_runs.append(dict(run))
            run = {'subs': 0, 'words': 0, 'source': 0, 'first': None, 'last': None}
        else:
            if run['first'] is None:
                run['first'] = sub['title']
            run['last'] = sub['title']
            run['subs'] += 1
            run['words'] += m['words']
            run['source'] += m['source']
    if run['subs']:
        info_runs.append(dict(run))
    if page.subsections:
        summary = f'figures: {total} in {with_figures} of {len(page.subsections)} subsections'
        longest = max(info_runs, key=lambda r: r['subs']) if info_runs else None
        if longest:
            summary += f"; longest run without one: {longest['subs']} subsection(s) from [{longest['first'][:FINDING_CLIP]}] to [{longest['last'][:FINDING_CLIP]}] ({longest['words']} prose words, {longest['source']} source lines); a long run locates a passage to read and establishes nothing by itself"
        notes.append((None, summary))
    footer = f'figures={total} subsections-with-figures={with_figures} of {len(page.subsections)}'
    yield from reading(rows, notes, footer, {'figures': total, 'subsections_with_figures': with_figures}, severity='note')

def check(page, inputs):
    yield from figure_distribution(page, inputs)
