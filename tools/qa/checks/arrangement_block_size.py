"""Checks for [arrangement.block-size]."""
from measurements import measure
RULE = 'arrangement.block-size'

def check(page, inputs):
    yield from measure(page, 'excerpt', 'source-lines', normal=[6, 40], review=40, name='block size')
    yield from measure(page, 'figure', 'visible-lines', normal=[8, 80], review=80, name='block size')
