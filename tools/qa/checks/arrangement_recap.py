"""Checks for [arrangement.recap]."""
from pagemodel import prose_text, RECAP, sentences_of
from report import Finding, observations
RULE = 'arrangement.recap'
MAX_RUN = 4
MAX_SENTENCES = 3
CLIP = 110

def recaps(page, inputs):
    findings, listing = [], []
    subs = page.subsections
    if len(subs) <= MAX_RUN:
        yield from observations([], f'subsections={len(subs)} recaps=0 max-run={len(subs)} (no recap needed under {MAX_RUN + 1} subsections)', [], {'recaps': 0, 'max_run': len(subs)})
        return
    run, longest, count = 0, 0, 0
    for k, sub in enumerate(subs):
        run += 1
        found = [(n, t) for n, t in page.paragraph_texts(sub['numbered']) if RECAP.match(prose_text(t))]
        last = k == len(subs) - 1
        if run > MAX_RUN and not found and not last:
            findings.append(Finding(sub['line'], 'review', f'{run} subsections since the last recap; close one of them with a "So far," paragraph stating the object\'s state at that point'))
            longest = max(longest, run)
            run = 0
        for n, t in found:
            count += 1
            sentences = sentences_of(t)
            if len(sentences) > MAX_SENTENCES:
                findings.append(Finding(n, 'review', f'a recap of {len(sentences)} sentences; one to {MAX_SENTENCES} state where the object stands'))
            listing.append(f'{n:5} recap after {run} subsection(s): {prose_text(t)[:CLIP]}')
        if found:
            longest = max(longest, run)
            run = 0
    longest = max(longest, run)
    footer = f'subsections={len(subs)} recaps={count} max-run={longest}'
    yield from observations(findings, footer, listing, {'recaps': count, 'max_run': longest})

def check(page, inputs):
    yield from recaps(page, inputs)
