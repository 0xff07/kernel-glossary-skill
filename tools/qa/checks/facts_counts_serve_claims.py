"""Checks for [facts.counts-serve-claims]."""
from report import reading
from report import Row
import re
from pagemodel import LINK
RULE = 'facts.counts-serve-claims'
CODE_SPAN = re.compile('`[^`]+`')
_ONES = 'one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen'
_TENS = 'twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety'
NUMERAL = f'(?:(?:{_TENS})(?:-(?:{_ONES}))?|{_ONES}|\\d{{1,3}})'
POPULATION = 'call ?sites?|callers?|callees?|readers?|writers?|assignments?|accesses|occurrences?|entry points?|call expressions?|references?|removal sites?|mentions?|acquisitions?|places that|sites that|sites in|sites are|sites reach|sites under|such calls'
CENSUS_POPULATION = re.compile(f'(?<![-\\w]){NUMERAL}\\s+(?:further |more |other |remaining |such |distinct |separate |in-tree |production |direct |indirect |static |exported ){{0,2}}(?:{POPULATION})', re.I)
POPULATION_CELL = re.compile(f'^{NUMERAL}\\s+(?:{POPULATION}|lines?|calls?)\\b', re.I)
POPULATION_HEADER = re.compile(f'^(?:number of |how many )?(?:#|n|count|counts|how often|times|{POPULATION}|reads?|writes?|uses?|hits?|sites?|lines?|read on|read at|written at)(?:\\s+(?:in|per|across|under|from|to)\\b.*)?$', re.I)
BARE_NUMERAL_CELL = re.compile(f'^{NUMERAL}$', re.I)
COUNT_COLUMN_SHARE = 0.6
UNIVERSAL = re.compile('\\b(only|never|always|every|all|none|no other|exactly|each|sole|solely|the one|the single|once|nothing|anything|everything|whole)\\b', re.I)
FACT_SPLIT = re.compile('(?<=[.!?])\\s+')
FACT_CLIP = 150

def census_sentences(page, inputs):
    """Sentences counting a population of code locations, for [facts.counts-serve-claims]."""
    rows, served, bare, columns = ([], 0, 0, 0)
    for table in page.tables:
        if table.region not in ('prose', 'section6'):
            continue
        for col, name in enumerate(table.header):
            cells = [r.cells[col] for r in table.rows if col < len(r.cells) and r.cells[col]]
            if len(cells) < 2:
                continue
            plain = [CODE_SPAN.sub('X', LINK.sub('\\1', c)) for c in cells]
            counts = sum((bool(POPULATION_CELL.match(c)) for c in plain))
            if POPULATION_HEADER.match(CODE_SPAN.sub('X', name)):
                counts = max(counts, sum((bool(BARE_NUMERAL_CELL.match(c)) for c in plain)))
            if counts >= COUNT_COLUMN_SHARE * len(cells):
                columns += 1
                rows.append(Row(table.line, f'{table.line} COUNT COLUMN: | {name} | over {len(cells)} rows, {counts} of them counting a population', set()))
    for n, line in enumerate(page.lines[:page.counted_lines()], 1):
        if page.region_of(n) not in ('prose', 'section6'):
            continue
        if line.startswith(('#', '|', '>', '- ', '* ')):
            continue
        clean = CODE_SPAN.sub('X', LINK.sub('\\1', line))
        for sentence in FACT_SPLIT.split(clean):
            m = CENSUS_POPULATION.search(sentence)
            if not m:
                continue
            claim = bool(UNIVERSAL.search(sentence))
            served += claim
            bare += not claim
            tag = 'CONTAINS UNIVERSAL WORD' if claim else 'BARE COUNT'
            rows.append(Row(n, f'{n} {tag}: {sentence.strip()[:FACT_CLIP]}', set()))
    rows.sort(key=lambda row: row.line)
    footer = f'census sentences={len(rows) - columns} bare={bare} carrying-a-universal={served} count-columns={columns}; each is read for the invariant or boundary it establishes, which the paragraph states before it, or it is cut'
    yield from reading(rows, [], footer, {'census': len(rows) - columns, 'bare': bare, 'count_columns': columns}, severity='review')

def check(page, inputs):
    yield from census_sentences(page, inputs)
