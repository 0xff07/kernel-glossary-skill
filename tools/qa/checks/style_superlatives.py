"""Checks for [style.superlatives]."""
from patterns import find_pattern
RULE = 'style.superlatives'

def check(page, inputs):
    yield from find_pattern(page, '\\b(the most invasive|the most fragmenting|the most aggressive|the most consequential|the most preferred|the least preferred|the most expensive|the cheapest|the cheap path|the strongest guarantee|the weakest guarantee|the worst outcome|the best outcome|the entire performance benefit|the entire correctness benefit|the key invariant|the key difference|the key innovation|the key role|the design assumption|the design intent|matters because|is what makes|what makes|the only mode that|elaborate|elegant|fundamental|cornerstone|linchpin|crucial|critical)\\b|(?<!\\ba )\\bmatters?\\b(?!\\s+of\\b)|\\bthe reasoning\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading'], name='superlatives', severity='FAIL', flags=2)
    yield from find_pattern(page, '\\bthe (fast|slow) path\\b|\\ba matters?\\s+of\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading'], name='superlatives', severity='review', flags=2)
    yield from find_pattern(page, '\\b(is|are) what\\b', view='prose', region=['prose', 'section6', 'catalog', 'heading'], fix='state it directly', name='superlatives', severity='review', flags=2)
