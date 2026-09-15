"""Behavior and boundaries for arrangement figure placement."""
import unittest
from checks.arrangement_figure_placement import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_figures_and_longest_gap_remain_informational(self):
        text = skeleton(details=f'### A\n\n{PROSE}\n\n### B\n\n{PROSE}\n\n{FIGURE}')
        found = list(check(page(text), None))
        self.assertTrue(any('longest run without one: 1' in f.message for f in found))
        self.assertTrue(any(f.data == {'figures': 1, 'subsections_with_figures': 1} for f in found))
        self.assertTrue(all(f.severity == 'note' for f in found))
        empty = list(check(page(skeleton()), None))
        self.assertTrue(any(f.data and f.data.get('figures') == 0 for f in empty))
