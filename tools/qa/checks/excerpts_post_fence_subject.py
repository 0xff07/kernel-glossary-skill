"""Checks for [excerpts.post-fence-subject]."""
from report import reading
from report import Row
import re
RULE = 'excerpts.post-fence-subject'
FIRST_SENTENCE = re.compile('(?<=[.;:])\\s')
PRONOUN_OPENER = re.compile('^(It|Its|This|That|These|Those|Both|Each|Either|Neither|They|Their|Here|There)\\b')
CODE_SPAN = re.compile('`[^`]+`')
POSTFENCE_CLIP = 120
MEMBER_LINK_URL = re.compile('\\(https?://[^)]*\\)')

def sentence_after(page, j):
    """(1-based line, first sentence) below the fence closing at 0-based line j, or (None, None)."""
    lines = page.lines
    k = j + 1
    while k < len(lines) and (not lines[k].strip()):
        k += 1
    if k >= len(lines) or lines[k].startswith(('```', '#', '|', '- ', '* ', '>')):
        return (None, None)
    text = MEMBER_LINK_URL.sub('', lines[k]).strip()
    return (k + 1, FIRST_SENTENCE.split(text, 1)[0].strip())

def first_sentence_after_fence(page, inputs):
    rows = []
    total = pronouns = symbol_less = 0
    for fence in page.excerpts:
        n, sentence = sentence_after(page, fence.end - 1)
        if sentence is None:
            continue
        total += 1
        flags = set()
        verdict = ''
        if PRONOUN_OPENER.match(sentence):
            pronouns += 1
            verdict = 'opens on a pronoun'
        elif not CODE_SPAN.search(sentence):
            symbol_less += 1
            verdict = 'names no symbol'
        if verdict:
            flags.add('opens-on-pronoun-or-no-symbol')
        text = f'{n}: {sentence[:POSTFENCE_CLIP]}'
        if verdict:
            text = f'post-fence sentence {verdict}: {sentence[:POSTFENCE_CLIP]}'
        rows.append(Row(n, text, flags))
    footer = f'post-fence sentences={total} pronoun-openers={pronouns} symbol-less={symbol_less}'
    yield from reading(rows, [], footer, {'sentences': total, 'pronoun_openers': pronouns, 'symbol_less': symbol_less}, severity='review')

def check(page, inputs):
    yield from first_sentence_after_fence(page, inputs)
