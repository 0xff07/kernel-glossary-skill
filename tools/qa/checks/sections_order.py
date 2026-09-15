"""Checks for [sections.order]."""
from report import Finding
RULE = 'sections.order'

def h2_order(page):
    expected = ['SUMMARY', 'SPECIFICATIONS', 'COVERAGE', 'DOCUMENTATION', 'OTHER SOURCES', 'REGISTERS', 'DETAILS']
    slot = ['REGISTERS', 'METHODS', 'PRIMITIVES', 'INTERFACES']
    found = page.h2_names
    fixed = [h for h in expected if h not in slot]
    ok = [h for h in found if h not in slot] == fixed
    six = [h for h in found if h in slot]
    if ok and six:
        position = next((k for k, h in enumerate(expected) if h in slot), None)
        ok = len(six) == 1 and position is not None and (found.index(six[0]) == position)
    if not ok:
        return [Finding(None, 'FAIL',
                        f'H2 order {found} differs from {expected} (one of {slot} at that position, or none)')]
    return []

def check(page, inputs):
    yield from h2_order(page)
