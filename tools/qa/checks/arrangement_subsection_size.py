"""Checks for [arrangement.subsection-size]."""
from measurements import measure
RULE = 'arrangement.subsection-size'

def check(page, inputs):
    yield from measure(page, 'subsection', 'words', normal=[0, 400], review=600, name='subsection size')
    yield from measure(page, 'subsection', 'paragraphs', review=8, name='subsection size')
