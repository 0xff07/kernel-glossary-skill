"""Checks for [style.walk]."""
from patterns import find_pattern
RULE = 'style.walk'

def check(page, inputs):
    yield from find_pattern(page, '\\b(walk|walks|walked|walking)\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading'], name='walk', severity='review', flags=2)
