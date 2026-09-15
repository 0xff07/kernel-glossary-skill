"""Checks for [purpose.openers]."""
from report import reading
from report import Row
import re
RULE = 'purpose.openers'
NUMBER = re.compile('\\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|\\d+)\\b|\\b(first|second|third|fourth|fifth|remaining|other)\\b', re.I)
OPENS_ON_A_SYMBOL = re.compile('^\\[`[^`]+`\\]\\(')
OPENER_LINK_URL = re.compile('\\]\\(https?://[^)]*\\)')
FIRST_SENTENCE = re.compile('(?<=[.;:])\\s')
SECTION_CLIP = 60
OPENER_CLIP = 160

def openers(page, inputs):
    rows = []
    counts = {'openers': 0, 'count': 0, 'symbol': 0}
    in_fence = False
    section = 'lead'
    leading = True
    for n, line in enumerate(page.lines[:page.counted_lines()], 1):
        if line.startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith('#'):
            section = line.lstrip('#').strip()[:SECTION_CLIP]
            leading = True
            continue
        if not line.strip() or line.startswith(('|', '- ', '>')):
            continue
        if leading:
            sentence = FIRST_SENTENCE.split(OPENER_LINK_URL.sub(']', line), maxsplit=1)[0]
            counts['openers'] += 1
            flags = set()
            if NUMBER.search(sentence):
                counts['count'] += 1
                flags.add('number-led')
            if OPENS_ON_A_SYMBOL.match(line.strip()):
                counts['symbol'] += 1
                flags.add('symbol-led')
            rows.append(Row(n, f"{n} [{section}]{(' COUNT' if 'number-led' in flags else '')}{(' SYMBOL' if 'symbol-led' in flags else '')}: {sentence[:OPENER_CLIP]}", flags))
        leading = False
    footer = f"openers={counts['openers']} count-tagged={counts['count']} symbol-led={counts['symbol']} (every opener is read; the tag only prompts)"
    yield from reading(rows, [], footer, counts, severity='review')

def check(page, inputs):
    yield from openers(page, inputs)
