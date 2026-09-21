"""Checks for [drawing.legend]."""
from constructs import constructs_of, construct_at
from inputs import source_lines
from measurements import reproduced_lines
from pagemodel import legend_entries
from report import Finding, observations
RULE = 'drawing.legend'
MIN_PHRASE_WORDS = 3

def resolve(cited, file):
    """(tree path, None) for a legend file among the page's cited files, or (None, why)."""
    if file in cited:
        return file, None
    tails = [c for c in cited if c.split('/')[-1] == file or c.endswith('/' + file)]
    if len(tails) == 1:
        return tails[0], None
    return None, ('matches no file the page cites' if not tails else f'is ambiguous among {len(tails)} cited files')

def legends(page, inputs):
    findings, listing = [], []
    counts = {'figures': 0, 'with_legend': 0, 'marks': 0, 'entries': 0, 'phrased': 0, 'findings': 0, 'unresolved': 0}
    reproduced = reproduced_lines(page, inputs)
    cited = page.cited_files()
    tables = {}

    def fail(text):
        counts['findings'] += 1
        findings.append(Finding(None, 'FAIL', text))
    for number, fence in enumerate(page.figures, 1):
        counts['figures'] += 1
        entries, marks = legend_entries(fence.body)
        if not entries and not marks:
            continue
        counts['with_legend'] += bool(entries)
        counts['marks'] += len(marks)
        counts['entries'] += len(entries)
        legend_marks = {e['mark'] for e in entries}
        missing = ''.join(sorted(marks - legend_marks))
        extra = ''.join(sorted(legend_marks - marks))
        if missing:
            fail(f'figure {number}: marks {missing} in the drawing have no legend entry with a site (`① name file:line` beneath the drawing)')
        if extra:
            fail(f'figure {number}: legend entries {extra} mark nothing in the drawing')
        for e in entries:
            where = f"figure {number}: legend {e['mark']} {e['name']} {e['file'] or ''}:{e['line']}"
            if len(e['phrase'].split()) < MIN_PHRASE_WORDS:
                fail(f'{where} carries no phrase; say in a few words what happens there, `{e["mark"]} {e["name"]} file:line  what it does`, one entry per line')
            else:
                counts['phrased'] += 1
            path, why = resolve(cited, e['file']) if e['file'] else (None, 'names no file')
            if path is None:
                fail(f'{where} {why}')
                continue
            source = source_lines(inputs.tree, path, inputs.cache)
            if source is None or not 0 < e['line'] <= len(source):
                fail(f'{where} is beyond the file')
                continue
            if path not in tables:
                tables[path] = constructs_of(source)
            construct = construct_at(tables[path], e['line'])
            if construct is None:
                counts['unresolved'] += 1
                findings.append(Finding(None, 'review', f"{where}: no construct is parsed around that line, so whether it lies in {e['name']}() is unresolved; verify by hand"))
            elif construct.name != e['name']:
                fail(f"{where} does not lie in {e['name']}(): {construct.label(path.rsplit('/', 1)[-1])} holds that line")
                continue
            if e['line'] not in reproduced.get(path, set()):
                fail(f'{where} is a line no excerpt on the page reproduces; show it beside the figure or drop the mark')
        listing.append(f'fig {number}: marks={len(marks)} legend={len(entries)}')
    footer = f"figures={counts['figures']} with-legend={counts['with_legend']} marks={counts['marks']} entries={counts['entries']} phrased={counts['phrased']} findings={counts['findings']} unresolved={counts['unresolved']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from legends(page, inputs)
