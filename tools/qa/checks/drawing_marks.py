"""Checks for [drawing.marks]."""
from pagemodel import MARK_ALPHABETS, legend_entries, mark_alphabet, mark_index, next_alphabet
from report import Finding, observations
from walk_utils import outline_tables
RULE = 'drawing.marks'
CYCLE = ' '.join(symbols[0] for symbols in MARK_ALPHABETS.values())


def series_of(page):
    """[(page line, kind, [marks])] for every marked series in page order: an outline table's
    pieces or a figure legend's entries."""
    out = [(line, 'outline', [m for m, _f, _a, _b in rows]) for line, rows in outline_tables(page)]
    for number, fence in enumerate(page.figures, 1):
        entries, _marks = legend_entries(fence.body)
        if entries:
            out.append((fence.start, f'figure {number}', [e['mark'] for e in entries]))
    return sorted(out, key=lambda s: s[0])


def marks(page, inputs):
    findings, listing = [], []
    counts = {'series': 0, 'mixed': 0, 'gaps': 0, 'out_of_cycle': 0}
    previous = None
    for line, kind, series in series_of(page):
        counts['series'] += 1
        alphabets = sorted({mark_alphabet(m) for m in series})
        alphabet = alphabets[0] if len(alphabets) == 1 else None
        expected = next_alphabet(previous, len(series))
        if alphabet is None:
            counts['mixed'] += 1
            findings.append(Finding(line, 'FAIL', f"{kind} at page {line} numbers its marks from two alphabets ({', '.join(alphabets)}); one series, one alphabet"))
        else:
            if [mark_index(m) for m in series] != list(range(1, len(series) + 1)):
                counts['gaps'] += 1
                findings.append(Finding(line, 'review', f"{kind} at page {line} runs {''.join(series)}; a series counts from the alphabet's first symbol without a gap"))
            if alphabet != expected:
                counts['out_of_cycle'] += 1
                first = MARK_ALPHABETS[expected][0]
                findings.append(Finding(line, 'review', f"{kind} at page {line} counts in {alphabet}; the cycle {CYCLE} puts {expected} ({first}) here, after the {previous or 'start of the page'}"))
        listing.append(f"{line:5} {kind}: {''.join(series)} ({alphabet or 'mixed'}; expected {expected})")
        previous = alphabet or expected
    footer = f"series={counts['series']} mixed={counts['mixed']} gaps={counts['gaps']} out-of-cycle={counts['out_of_cycle']}"
    yield from observations(findings, footer, listing, dict(counts))


def check(page, inputs):
    yield from marks(page, inputs)
