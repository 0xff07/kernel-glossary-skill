"""Checks for [style.run-on-enumeration]."""
from report import reading
from report import Row
import re
RULE = 'style.run-on-enumeration'
REVIEW_LOCATIONS = 4
HINT_LOCATIONS = 2
MIN_COMMAS = 3
CONJUNCTION = ' and '
LISTING_CLIP = 170
LOCATION = re.compile('\\b[\\w./-]+\\.(?:c|h|rst|S):\\d+(?:-\\d+)?')
ENUMERATION_LINK_URL = re.compile('\\]\\([^)]*\\)')
SENTENCE_SPLIT = re.compile('(?<=[.;!?])\\s+')

def run_on_enumerations(page, inputs):
    found = []
    for n, line in enumerate(page.lines[:page.counted_lines()], 1):
        if page.region_of(n) not in ('prose', 'section6'):
            continue
        if line.startswith(('#', '|', '>', '- ', '* ')):
            continue
        plain = ENUMERATION_LINK_URL.sub(']', line)
        for sentence in SENTENCE_SPLIT.split(plain):
            if sentence.count(',') >= MIN_COMMAS and CONJUNCTION in sentence:
                found.append((len(set(LOCATION.findall(sentence))), n, sentence))
    found.sort(key=lambda c: (-c[0], c[1]))
    rows, notes = ([], [])
    many = some = 0
    for locations, n, sentence in found:
        flags = set()
        if locations >= REVIEW_LOCATIONS:
            many += 1
            flags.add('four-or-more-locations')
            text = f'enumeration with {locations} distinct locations at line {n} (four or more members of one set need a table; steps of one operation are prose): {sentence[:LISTING_CLIP]}'
        else:
            text = f'{locations} locations, line {n}: {sentence[:LISTING_CLIP]}'
            if locations >= HINT_LOCATIONS:
                some += 1
        rows.append(Row(n, text, flags))
    footer = f'enumeration candidates={len(found)} with>={REVIEW_LOCATIONS} locations={many} with 2-3={some}'
    yield from reading(rows, notes, footer, {'candidates': len(found), 'with_four_or_more_locations': many, 'with_two_or_three': some}, severity='review')

def check(page, inputs):
    yield from run_on_enumerations(page, inputs)
