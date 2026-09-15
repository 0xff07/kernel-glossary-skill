"""Checks for [style.vtable]."""
from patterns import find_pattern
RULE = 'style.vtable'

def check(page, inputs):
    yield from find_pattern(page, 'vtable', view='prose', region=['prose', 'section6', 'catalog', 'heading'], name='vtable', severity='FAIL', flags=2)
