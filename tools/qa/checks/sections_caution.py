"""Checks for [sections.caution]."""
from report import Finding
RULE = 'sections.caution'

def h1_first_line(page):
    if not page.lines or not page.lines[0].startswith('# '):
        return [Finding(1, 'FAIL', 'the first line is not the H1')]
    return []

def blockquote_after_h1(page):
    expected = '> CAUTION: AI-GENERATED CONTENT\n>\n> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.\n'.rstrip('\n').split('\n')
    got = page.caution_block
    if [l.rstrip() for l in got] != [l.rstrip() for l in expected]:
        return [Finding(3 if len(page.lines) >= 3 else None, 'FAIL',
                        'caution blockquote differs from the required text (lines 3 to 5)')]
    return []

def check(page, inputs):
    yield from h1_first_line(page)
    yield from blockquote_after_h1(page)
