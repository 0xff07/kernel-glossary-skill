"""Checks for [style.counting-headings]."""
from patterns import find_pattern
RULE = 'style.counting-headings'

def check(page, inputs):
    yield from find_pattern(page, '^(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty|[0-9]+)\\s', view='prose', region=['heading'], not_in_cells=True, name='counting headings', severity='FAIL', flags=2)
