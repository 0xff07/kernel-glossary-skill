"""Checks for [style.headings]."""
from report import reading
from report import Row
from patterns import find_pattern
import re
RULE = 'style.headings'
CODE_SPAN = re.compile('`[^`]+`')
HEADING_VERBS = ('be', 'is', 'are', 'was', 'were', 'been', 'has', 'have', 'had', 'can', 'may', 'must', 'will', 'do', 'does', 'did', 'go', 'put', 'set', 'let', 'cut', 'run', 'take', 'make', 'give', 'turn', 'leave', 'read', 'hold', 'keep', 'send', 'tell', 'hand', 'come', 'get', 'find', 'know', 'mean', 'show', 'tear', 'wait', 'want', 'work', 'write', 'close', 'open', 'start', 'stop', 'drop', 'name', 'map', 'point', 'carry', 'answer', 'fail', 'free', 'use', 'own', 'need', 'meet', 'split')
VERB_SUFFIXES = ('ing', 'ed', 'es', 's')
NOUN_LOOKALIKES = ('ring', 'rings', 'string', 'strings', 'thing', 'things', 'bus', 'status', 'class', 'address', 'access', 'process', 'its', 'this', 'as', 'less', 'plus', 'versus', 'padding', 'pending', 'polling', 'meaning', 'warning', 'setting', 'settings', 'timing')
HEADING_CLIP = 70

def states_action(heading):
    plain = CODE_SPAN.sub(' ', heading)
    for word in re.findall("[A-Za-z][A-Za-z']*", plain):
        low = word.lower()
        if low in NOUN_LOOKALIKES:
            continue
        if low in HEADING_VERBS or low.endswith(VERB_SUFFIXES):
            return True
    return False

def details_headings(page, inputs):
    rows = []
    bare = 0
    for sub in page.subsections:
        flags = set()
        text = f"{sub['line']}: {sub['title'][:HEADING_CLIP]}"
        if not states_action(sub['title']):
            bare += 1
            flags.add('no-verb')
            text = f"bare-noun heading (no word reads as a verb): {sub['title'][:HEADING_CLIP]}"
        rows.append(Row(sub['line'], text, flags))
    yield from reading(rows, [], f'DETAILS headings={len(rows)} bare-noun={bare}', {'headings': len(rows), 'bare_noun': bare}, severity='review')

def check(page, inputs):
    yield from find_pattern(page, '^(Why|How|Where|What)\\b|\\?\\s*$', view='prose', region=['heading'], not_in_cells=True, name='headings', severity='FAIL', flags=2)
    yield from details_headings(page, inputs)
