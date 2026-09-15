"""Checks for [style.banned-words]."""
from patterns import find_pattern
RULE = 'style.banned-words'

def check(page, inputs):
    yield from find_pattern(page, '\\b(contract|tally|tallied|tallies|tallying|canonical)\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading'], name='banned words', severity='FAIL', flags=2)
    yield from find_pattern(page, '(^|[^a-z])arms?(?!64)([^a-z]|$)', view='prose', region=['prose', 'section6', 'catalog', 'heading'], name='banned words', severity='review', flags=2)
