"""Checks for [registers.ruler]."""
import re
from report import Finding, observations
RULE = 'registers.ruler'
RULER = re.compile(r'^\s*(?:bit\s+)?(?:[0-9] )+[0-9]\s*$')
TOP = re.compile(r'^(\s*[^\s│├└┌]*?\s*)(┌[─┬]+┐)')
BOX = set('│├┤┼┬┴┌┐└┘')


def grids(fence):
    """Each bit-ruler grid in a figure: (top border column, list of (offset, line)) rows from the top border to the bottom border."""
    lines = fence.body if isinstance(fence.body, list) else fence.body.split('\n')
    if not any(RULER.match(l) for l in lines):
        return
    i = 0
    while i < len(lines):
        m = TOP.match(lines[i])
        if m:
            x0 = len(m.group(1))
            rows = [(i, lines[i])]
            j = i + 1
            while j < len(lines) and ('│' in lines[j] or lines[j].lstrip().startswith(('├', '└'))):
                rows.append((j, lines[j]))
                if lines[j].lstrip().startswith('└'):
                    break
                j += 1
            yield x0, rows
            i = j + 1
        else:
            i += 1


def boundaries(line, x0, width):
    return {c for c, ch in enumerate(line) if ch == '│' and x0 <= c <= x0 + width}


def ruler(page, inputs):
    findings, listing = [], []
    counts = {'grids': 0, 'off_grid': 0, 'bad_junctions': 0}
    for number, fence in enumerate(page.figures, 1):
        for x0, rows in grids(fence):
            counts['grids'] += 1
            top = rows[0][1]
            width = len(top.rstrip()) - 1 - x0
            cells = [(o, l) for o, l in rows if '│' in l and not l.lstrip().startswith(('├', '└', '┌'))]
            for offset, line in cells:
                off = sorted(c - x0 for c in boundaries(line, x0, width) if (c - x0) % 2)
                if off:
                    counts['off_grid'] += 1
                    findings.append(Finding(fence.start + 1 + offset, 'FAIL', f'figure {number}: a cell boundary sits off the bit grid at column offset {off[0]} of the ruler; every boundary falls on a bit edge'))
            for k, (offset, line) in enumerate(rows):
                s = line.lstrip()
                if not s.startswith('├'):
                    continue
                above = next(((o, l) for o, l in reversed(rows[:k]) if '│' in l and not l.lstrip().startswith(('├', '┌'))), None)
                below = next(((o, l) for o, l in rows[k + 1:] if '│' in l and not l.lstrip().startswith(('├', '└'))), None)
                if above is None or below is None:
                    continue
                a, b = boundaries(above[1], x0, width), boundaries(below[1], x0, width)
                bad = []
                for c in range(x0 + 1, x0 + width):
                    ch = line[c] if c < len(line) else ' '
                    want = '┼' if c in a and c in b else '┴' if c in a else '┬' if c in b else '─'
                    if ch != want:
                        bad.append((c - x0, ch, want))
                if bad:
                    counts['bad_junctions'] += 1
                    c, ch, want = bad[0]
                    findings.append(Finding(fence.start + 1 + offset, 'FAIL', f'figure {number}: the divider has {ch!r} at column offset {c} where the rows beside it call for {want!r} ({len(bad)} such columns); a divider carries a junction exactly where the rows above and below have a boundary'))
            listing.append(f'{fence.start:5} figure {number}: grid of {len(cells)} cell rows, {width // 2} bits wide')
    footer = f"grids={counts['grids']} off-grid={counts['off_grid']} bad-dividers={counts['bad_junctions']}"
    yield from observations(findings, footer, listing, dict(counts))


def check(page, inputs):
    yield from ruler(page, inputs)
