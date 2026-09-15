"""Checks for [style.verification-narration]."""
from patterns import find_pattern
RULE = 'style.verification-narration'

def check(page, inputs):
    yield from find_pattern(page, '\\bgrep\\b|semcode|caller index|search basis|second basis|re-derived|verified (negative|absent)|tree-wide (search|scan|sweep)\\b|by a (case-insensitive )?(search|scan|sweep)\\b', view='spans-visible', region=['prose', 'section6', 'catalog', 'heading'], fix='delete the method clause, keep the result and its scope', name='verification narration', severity='FAIL', flags=2)
