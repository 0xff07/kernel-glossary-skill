"""Checks for [style.boldface]."""
from patterns import find_pattern
RULE = 'style.boldface'

def check(page, inputs):
    yield from find_pattern(page, '\\*\\*', view='raw', region=['prose', 'section6', 'catalog', 'heading'], name='boldface', severity='FAIL', flags=2)
