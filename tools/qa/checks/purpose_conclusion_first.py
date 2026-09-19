"""Checks for [purpose.conclusion-first]."""
import re
from report import Row, reading
RULE = 'purpose.conclusion-first'
ANNOUNCES = re.compile(r'\b((shown|listed|given|described|explained|reproduced) below|below (shows|lists|is|are)|as follows|the following|this (sub)?section|here (is|are)|let us|we (now|will|first))\b|:\s*$', re.I)
CLIP = 120

def skim_rows(page):
    rows, notes = [], []
    counts = {'subsections': 0, 'announcing_openers': 0, 'questions': 0}
    for sub in page.skim()['subsections']:
        counts['subsections'] += 1
        flags = set()
        opener, closer = sub['opener'], sub['closer']
        if ANNOUNCES.search(opener):
            flags.add('announces'); counts['announcing_openers'] += 1
        if opener.rstrip().endswith('?'):
            flags.add('question'); counts['questions'] += 1
        if flags:
            rows.append(Row(sub['line'], f"[{sub['title'][:40]}] opener {'/'.join(sorted(flags))}: {opener[:CLIP]}", flags))
        rows.append(Row(sub['line'], f"[{sub['title'][:40]}] closer: {closer[:CLIP]}", set()))
    footer = f"subsections={counts['subsections']} announcing-openers={counts['announcing_openers']} questions={counts['questions']}"
    return rows, notes, footer, counts

def check(page, inputs):
    rows, notes, footer, counts = skim_rows(page)
    yield from reading(rows, notes, footer, counts, severity='review')
