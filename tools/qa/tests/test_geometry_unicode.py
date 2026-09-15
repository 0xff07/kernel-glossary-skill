"""Connector candidates and the existing literal exceptions."""
import unittest
from checks.geometry_unicode import check
from tests.support import FIGURE, page


class Geometry(unittest.TestCase):
    def test_connectors(self):
        for cell in ('│  /  │','│ ┘/┌ │',r'│ a \ b │','│ x  /  y │','│ a | b │'):
            found = list(check(page(FIGURE.replace('│ s0 │ s1 │',cell)),None))
            self.assertTrue(any(f.severity == 'review' and 'ASCII' in f.message for f in found), cell)

    def test_word_separators_paths_and_c_expressions(self):
        for cell in ('│ a || b │','│ put / get │','│ R/W  a|b │','│ !x / !y │','│ /* c */ │','│ /sys/bus/kg/ │','│ /sys │'):
            found = list(check(page(FIGURE.replace('│ s0 │ s1 │',cell)),None))
            self.assertFalse(any(f.severity == 'review' for f in found), cell)

    def test_no_quotation_warning_from_unicode_check(self):
        found = list(check(page('```\nplain text\n```'), None))
        self.assertFalse(any('quotation' in f.message for f in found))

    def test_inventory_contains_connector_measurements(self):
        found = list(check(page(FIGURE.replace('│ s0 │ s1 │', '| s0 | s1 |')), None))
        self.assertEqual(found[-1].data, {'figures': 1, 'ascii_connectors': 1})

    def test_width_and_loose_verticals_do_not_raise_unicode_findings(self):
        text = '```\n' + '─' * 121 + '\n\n│\n```'
        found = list(check(page(text), None))
        self.assertTrue(all(f.severity == 'note' for f in found))
