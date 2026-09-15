"""Checks for [arrangement.headings]."""
from measurements import measure
RULE = 'arrangement.headings'

def check(page, inputs):
    yield from measure(page, 'heading', 'words', review=10, name='headings')
