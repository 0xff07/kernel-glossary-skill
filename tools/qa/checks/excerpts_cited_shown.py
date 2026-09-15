"""Checks for [excerpts.cited-shown]."""
from measurements import cited_lines, reproduced_lines
from report import Finding, Row, reading
import re
RULE = 'excerpts.cited-shown'
LOCATION_LINK = re.compile('\\[`?(?P<file>[\\w./-]+\\.[chS]):(?P<first>\\d+)(?:-(?P<last>\\d+))?`?\\]\\(https://elixir\\.bootlin\\.com/linux/[^/]+/source/(?P<path>[^#)]+)#L(?P<anchor>\\d+)\\)')
LINK_URL = re.compile('\\]\\([^)]*\\)')
ITEM = re.compile('^\\s*(?:[-*+]|\\d+\\.)\\s+')
NUMERAL = ('\\d+|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|'
           'sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred')
SET_NOUN = ('(?:call\\s+)?(?:sites?|callers?|callees?|places?|writers?|readers?|users?|assignments?|functions?|'
            'files?|paths?|occurrences?|locations?|writes?|reads?|mentions?|references?)')
# A stated total: a numeral within two words of a noun naming a population of code locations, or
# the quantifier a universal claim carries ([facts.universal-claims] enumerates such a set).
CENSUS = re.compile(f'\\b(?:{NUMERAL})\\b(?:\\s+[\\w-]+){{0,2}}?\\s+{SET_NOUN}\\b'
                    '|\\b(?:every|all|each|only|none|no other|nowhere else)\\b', re.I)
WORD = re.compile('[A-Za-z0-9_]+')
COMPACT_GAP = 4
CLIP = 140

def is_census(line, matches):
    """A census states the total of the set it cites, by number or by quantifier, and lists the
    members compactly: at most COMPACT_GAP words between consecutive location links. A clause of
    explanation between two links is what each member does, and that is shown, not cited."""
    if not CENSUS.search(LINK_URL.sub(']', line)):
        return False
    for first, second in zip(matches, matches[1:]):
        gap = LINK_URL.sub(']', line[first.end():second.start()])
        if len(WORD.findall(gap)) > COMPACT_GAP:
            return False
    return True

def counted_lines(page):
    """Every prose paragraph and list item, by line: the units the rule counts. Table rows are
    lookups and stay out; the catalog sections carry no location links."""
    for n, line in enumerate(page.lines, 1):
        if page.region_of(n) not in ('prose', 'section6'):
            continue
        if not line.strip() or line.startswith('|') or line.startswith(('    ', '\t')):
            continue
        yield n, line

def file_jumps(page, inputs):
    """A paragraph whose location links reach two or more files no excerpt reproduces fails as a
    file jump; one that states the total of the set it cites and lists the members compactly is a
    census, listed for reading."""
    shown = reproduced_lines(page, inputs)
    rows, paragraphs, jumps, censuses = [], 0, 0, 0
    for n, line in counted_lines(page):
        paragraphs += 1
        unshown = []
        matches = list(LOCATION_LINK.finditer(line))
        for match in matches:
            path = match.group('path')
            if not cited_lines(match.group('first'), match.group('last')) <= shown.get(path, set()):
                cited = match.group('first') + (f"-{match.group('last')}" if match.group('last') else '')
                unshown.append((path, f"{match.group('file')}:{cited}"))
        files = sorted({path for path, _site in unshown})
        if len(files) < 2:
            continue
        sites = ', '.join(site for _path, site in unshown)
        text = LINK_URL.sub(']', line).strip()[:CLIP]
        if is_census(line, matches):
            censuses += 1
            rows.append(Row(n, f'census across {len(files)} files: {sites} | {text}', {'census'}))
            continue
        jumps += 1
        yield Finding(n, 'FAIL', f'file jump: {sites} in {len(files)} files, none reproduced on the page | {text}',
                      {'files': files, 'sites': [site for _path, site in unshown]})
    footer = f'paragraphs={paragraphs} file-jumps={jumps} censuses={censuses}'
    yield from reading(rows, [], footer, {'paragraphs': paragraphs, 'file_jumps': jumps, 'censuses': censuses})

def check(page, inputs):
    yield from file_jumps(page, inputs)
