"""Checks for [style.placement-verbs]."""
from patterns import find_pattern
RULE = 'style.placement-verbs'

def check(page, inputs):
    yield from find_pattern(page, '\\b(live|lives|lived|living|sit|sits|sat|sitting|hang|hangs|hung|hanging|want|wants|wanted|wanting)\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading', 'figure'], name='placement verbs', severity='review', flags=2)
