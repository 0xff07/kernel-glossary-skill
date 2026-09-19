"""Checks for [excerpts.outline]."""
import re
from pagemodel import LEGEND_MARK, split_cells, TABLE_SEPARATOR
from report import Finding, observations
from walk_utils import owned_functions, pieces_of, walk
RULE = 'excerpts.outline'
RANGE = re.compile(r'([\w./-]+):(\d+)-(\d+)')

def outline_tables(page):
    """[(line, [(mark, file, first, last)])] for every table whose header names piece and lines."""
    out = []
    lines = page.lines
    details = page.section('DETAILS')
    if details is None:
        return out
    i = details.start
    while i < details.end:
        line = lines[i]
        if line.startswith('|'):
            header = [c.lower() for c in split_cells(line)]
            rows = []
            j = i + 1
            while j < len(lines) and lines[j].startswith('|'):
                if not TABLE_SEPARATOR.match(lines[j]):
                    cells = split_cells(lines[j])
                    mark = LEGEND_MARK.search(cells[0]) if cells else None
                    span = RANGE.search(cells[1]) if len(cells) > 1 else None
                    if mark and span:
                        rows.append((mark.group(0), span.group(1), int(span.group(2)), int(span.group(3))))
                j += 1
            if header and 'piece' in header[0] and any('line' in c for c in header[1:]) and rows:
                out.append((i + 1, rows))
            i = j
            continue
        i += 1
    return out

def outline(page, inputs):
    findings, listing = [], []
    counts = {'walked': 0, 'outlined': 0, 'pieces': 0, 'marked': 0}
    tables = {}
    outlines = outline_tables(page)
    for name, path, start, end in owned_functions(page, inputs, tables):
        chain, _reshown, _previews, _missing = walk(pieces_of(page, inputs, path, start, end), start, end)
        if len(chain) < 2:
            continue
        counts['walked'] += 1
        counts['pieces'] += len(chain)
        base = path.rsplit('/', 1)[-1]
        first_fence = chain[0][0].fence.start
        matching = [(line, rows) for line, rows in outlines if line < first_fence and rows and rows[0][1].split('/')[-1] == base and rows[0][2] == chain[0][1]]
        if not matching:
            findings.append(Finding(first_fence, 'FAIL', f'{name}() is walked in {len(chain)} pieces with no outline table above its first piece; give a table with the columns piece, lines and stage, one row per piece in order (① {base}:{chain[0][1]}-{chain[0][2]} ...)'))
            continue
        line, rows = matching[-1]
        counts['outlined'] += 1
        expected = [(unit_first, unit_last) for _u, unit_first, unit_last in chain]
        got = [(a, b) for _m, _f, a, b in rows]
        if got != expected:
            findings.append(Finding(line, 'FAIL', f"{name}(): the outline's rows {got} do not match the pieces shown {expected}; one row per piece, in order, with the lines the piece reproduces"))
        marks = [m for m, _f, _a, _b in rows]
        for k, (unit, first, last) in enumerate(chain):
            mark = marks[k] if k < len(marks) else None
            intro, _n = page.intro_of(unit.fence)
            if mark and mark in intro:
                counts['marked'] += 1
            else:
                findings.append(Finding(unit.fence.start, 'FAIL', f"{name}() piece {k + 1} ({base}:{first}-{last}) is not introduced with its mark {mark or '?'}; the sentence above the fence carries the outline's circled number"))
        listing.append(f'{line:5} outline {name}() pieces={len(chain)} marks={"".join(marks)}')
    footer = f"walked={counts['walked']} outlined={counts['outlined']} pieces={counts['pieces']} marked={counts['marked']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from outline(page, inputs)
