"""Checks for [excerpts.sufficiency]."""
from measurements import cited_lines, reproduced_lines
from report import reading
from report import Row
import re
RULE = 'excerpts.sufficiency'
OPENER_LINK_URL = re.compile('\\]\\(https?://[^)]*\\)')
LOCATION_LINK = re.compile('\\[`?(?P<file>[\\w./-]+\\.[chS]):(?P<first>\\d+)(?:-(?P<last>\\d+))?`?\\]\\(https://elixir\\.bootlin\\.com/linux/[^/]+/source/(?P<path>[^#)]+)#L(?P<anchor>\\d+)\\)')
LOCATION_CLIP = 120

def sentence_around(line, pos):
    """The sentence of `line` holding the character at `pos`, its link URLs dropped."""
    starts = [m.end() for m in re.finditer('(?<=[.!?])\\s+', line[:pos])]
    start = starts[-1] if starts else 0
    tail = re.search('[.!?](\\s|$)', line[pos:])
    end = pos + tail.end() if tail else len(line)
    return OPENER_LINK_URL.sub(']', line[start:end]).strip()

def unreproduced_locations(page, inputs):
    """Every location link (a `path:line` or `path:first-last` link) whose lines no excerpt unit on the page reproduces,
    with the sentence around it, for reading: such a link cites a site and never stands in for its
    code, so the sentence must name the function and the operation there."""
    reproduced = reproduced_lines(page, inputs)
    rows = []
    total = 0
    for n, line in enumerate(page.lines, 1):
        if page.region_of(n) not in ('prose', 'section6'):
            continue
        for match in LOCATION_LINK.finditer(line):
            total += 1
            if cited_lines(match.group('first'), match.group('last')) <= reproduced.get(match.group('path'), set()):
                continue
            cited = match.group('first') + (f"-{match.group('last')}" if match.group('last') else '')
            rows.append(Row(n, f"{match.group('file')}:{cited} | {sentence_around(line, match.start())[:LOCATION_CLIP]}", set()))
    footer = f'location-links={total} unreproduced={len(rows)}'
    yield from reading(rows, [], footer, {'location_links': total, 'unreproduced': len(rows)}, severity='review')

def check(page, inputs):
    yield from unreproduced_locations(page, inputs)
