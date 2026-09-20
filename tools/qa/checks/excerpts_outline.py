"""Checks for [excerpts.outline]."""
from report import Finding, observations
from walk_utils import outline_tables, owned_functions, pieces_of, walk
RULE = 'excerpts.outline'
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
                findings.append(Finding(unit.fence.start, 'FAIL', f"{name}() piece {k + 1} ({base}:{first}-{last}) is not introduced with its mark {mark or '?'}; the sentence above the fence carries the outline's mark"))
        listing.append(f'{line:5} outline {name}() pieces={len(chain)} marks={"".join(marks)}')
    footer = f"walked={counts['walked']} outlined={counts['outlined']} pieces={counts['pieces']} marked={counts['marked']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from outline(page, inputs)
