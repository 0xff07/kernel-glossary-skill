"""Checks for [style.negative-construction]."""
from patterns import find_pattern
RULE = 'style.negative-construction'

def check(page, inputs):
    yield from find_pattern(page, '(,|\\band)\\s+(not|never)\\s|\\brather than\\b|\\binstead of\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading', 'figure'], name='negative construction', severity='review', flags=2)
