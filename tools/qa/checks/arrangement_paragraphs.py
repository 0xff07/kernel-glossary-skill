"""Checks for [arrangement.paragraphs]."""
from measurements import measure
RULE = 'arrangement.paragraphs'

def check(page, inputs):
    yield from measure(page, 'paragraph', 'words', normal=[45, 80], review=120, name='paragraphs')
    yield from measure(page, 'paragraph', 'sentences', normal=[2, 4], review=5, name='paragraphs')
    yield from measure(page, 'sentence', 'words', review=35, run=3, name='paragraphs')
    yield from measure(page, 'paragraph', 'sentences', review_below=2, run=2, name='paragraphs')
    yield from measure(page, 'paragraph', 'words', review=80, run=3, name='paragraphs')
    yield from measure(page, 'prose-run', 'paragraphs', review=3, name='paragraphs')
    yield from measure(page, 'subsection', 'words', where='without-block', review=250, name='paragraphs')
