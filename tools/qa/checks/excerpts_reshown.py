"""Checks for [excerpts.reshown]."""
from inputs import source_lines
from measurements import cited_lines, positions_of
from report import Row, reading
import re
RULE = 'excerpts.reshown'
LOCATION_LINK = re.compile(r'\[`?(?P<file>[\w./-]+\.[chS]):(?P<first>\d+)(?:-(?P<last>\d+))?`?\]\(https://elixir\.bootlin\.com/linux/[^/]+/source/(?P<path>[^#)]+)#L(?P<anchor>\d+)\)')
LINK_URL = re.compile(r'\]\(https?://[^)]*\)')
MAX_RESHOW = 12
SENTENCE_CLIP = 100
TITLE_CLIP = 40

def sentence_around(line, pos):
    starts = [m.end() for m in re.finditer(r'(?<=[.!?])\s+', line[:pos])]
    start = starts[-1] if starts else 0
    tail = re.search(r'[.!?](\s|$)', line[pos:])
    end = pos + tail.end() if tail else len(line)
    return LINK_URL.sub(']', line[start:end]).strip()

def unit_lines(page, inputs):
    """[(unit, {source lines})] for every unit that maps onto the tree."""
    tree = getattr(inputs, 'tree', None) if inputs is not None else None
    out = []
    for unit in page.units:
        if not unit.path:
            continue
        source = source_lines(tree, unit.path, inputs.cache) if tree else None
        positions = positions_of(unit, source) if source is not None else None
        lines = {p for p in positions if p} if positions is not None else set(range(unit.line, unit.line + len(unit.lines)))
        out.append((unit, lines))
    return out

def subsection_at(page, n):
    for k, sub in enumerate(page.subsections):
        if sub['line'] <= n <= sub['end']:
            return k
    return None

def reshown(page, inputs):
    units = unit_lines(page, inputs)
    rows = []
    counts = {'location_links': 0, 'beside': 0, 'elsewhere': 0, 'unreproduced': 0, 'long_reshows': 0}
    for n, line in enumerate(page.lines, 1):
        if page.region_of(n) not in ('prose', 'section6') or line.lstrip().startswith('|'):
            continue  # a table row is a lookup, as [excerpts.cited-shown] counts it
        for match in LOCATION_LINK.finditer(line):
            counts['location_links'] += 1
            cited = cited_lines(match.group('first'), match.group('last'))
            holders = [unit for unit, lines in units if unit.path == match.group('path') and cited <= lines]
            if not holders:
                counts['unreproduced'] += 1
                continue
            here = subsection_at(page, n)
            if any(subsection_at(page, unit.start) == here for unit in holders):
                counts['beside'] += 1
                continue
            counts['elsewhere'] += 1
            nearest = min(holders, key=lambda unit: abs(unit.start - n))
            k = subsection_at(page, nearest.start)
            where = f"page {nearest.start}" + (f" [{page.subsections[k]['title'][:TITLE_CLIP]}]" if k is not None else '')
            text = match.group('first') + (f"-{match.group('last')}" if match.group('last') else '')
            rows.append(Row(n, f"{match.group('file')}:{text} shown only at {where}; re-show the lines beside this paragraph or move it | {sentence_around(line, match.start())[:SENTENCE_CLIP]}", set()))
    seen = {}
    for unit, lines in units:
        earlier = seen.setdefault(unit.path, set())
        if lines and lines <= earlier and len(lines) > MAX_RESHOW:
            counts['long_reshows'] += 1
            rows.append(Row(unit.start, f"{unit.path.rsplit('/', 1)[-1]}:{unit.line} re-shows {len(lines)} lines shown earlier; a re-show is the few lines the paragraph reasons about, about {MAX_RESHOW} at most", set()))
        earlier.update(lines)
    footer = (f"location-links={counts['location_links']} beside={counts['beside']} elsewhere={counts['elsewhere']} "
              f"unreproduced={counts['unreproduced']} reshows-over-{MAX_RESHOW}={counts['long_reshows']}")
    yield from reading(rows, [], footer, dict(counts), severity='review')

def check(page, inputs):
    yield from reshown(page, inputs)
