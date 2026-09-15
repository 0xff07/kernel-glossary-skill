"""Checks for [style.hedges]."""
from patterns import find_pattern
RULE = 'style.hedges'

def check(page, inputs):
    yield from find_pattern(page, '\\b(usually|typically|generally|often|normally|commonly|mostly|in practice|tends to|on a hot cpu|simply|essentially|basically|arguably)\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading'], unless=['\\w-(usually|typically|generally|often|normally|commonly|mostly)\\b', '\\b(usually|typically|generally|often|normally|commonly|mostly)-\\w'], name='hedges', severity='FAIL', flags=2)
