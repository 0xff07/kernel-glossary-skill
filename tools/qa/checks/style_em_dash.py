"""Checks for [style.em-dash]."""
from patterns import find_pattern
RULE = 'style.em-dash'

def check(page, inputs):
    yield from find_pattern(page, '—', view='prose', region=['prose', 'section6', 'catalog', 'heading', 'figure'], name='em dash', severity='FAIL', flags=2)
