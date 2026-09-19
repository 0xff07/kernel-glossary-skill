"""Behavior and boundaries for arrangement units."""
import unittest
from checks.arrangement_units import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_inventory_and_optional_baseline(self):
        now = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}')
        found = list(check(page(now), TestInputs()))
        self.assertTrue(any(f.data and f.data.get('maps') == ['P C P'] for f in found))
        self.assertTrue(any(f.data and f.data.get('inventory') for f in found))
        self.assertTrue(any('no committed baseline' in f.message for f in found))
        changed = list(check(page(now), TestInputs(baseline=skeleton())))
        self.assertTrue(any(f.data and f.data.get('added') == 1 for f in changed))
        self.assertTrue(any('structured block added' in f.message for f in changed))

    def test_the_recorded_block_map_is_compared_by_subsection(self):
        now = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n\n### B\n\n{PROSE}\n')
        bare = list(check(page(now), TestInputs()))
        self.assertTrue(any('no worksheet, not compared' in f.message for f in bare))
        lines = {m.group(2): int(m.group(1)) for f in bare if f.message and (m := __import__('re').match(r'^(\d+) \[(A|B)\] map=', f.message))}
        self.assertEqual(sorted(lines), ['A', 'B'])
        worksheet = ('## EVIDENCE\n### Block map\n| subsection (page line) | map | words | paras | blocks |\n|---|---|---|---|---|\n'
                   f"| {lines['A']} A | P C P | 20 | 2 | 1 |\n| {lines['B']} B | P P | 10 | 2 | 0 |\n| 999 Gone | P | 1 | 1 | 0 |\n")
        found = list(check(page(now), TestInputs(worksheet=worksheet)))
        reviews = [f.message for f in found if f.severity == 'review']
        self.assertEqual(reviews, ['[B] block map differs from the record: recorded P P, now P'])
        self.assertTrue(any('names no subsection on the page: [Gone] P' in f.message for f in found))
        self.assertTrue(any(f.data and f.data.get('recorded') == 3 and f.data.get('matching') == 1 and f.data.get('differing') == 1 for f in found))
        empty = list(check(page(now), TestInputs(worksheet='## EVIDENCE\nnothing recorded\n')))
        self.assertTrue(any(f.severity == 'review' and 'no block map recorded' in f.message for f in empty))
        partial = list(check(page(now), TestInputs(worksheet=f"## EVIDENCE\n| {lines['A']} A | P C P |\n")))
        self.assertEqual([f.message for f in partial if f.severity == 'review'], ['[B] block map not recorded (now map=P)'])
