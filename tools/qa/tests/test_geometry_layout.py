"""Width limits, loose verticals, quotations and the register exception."""
import unittest
from checks.geometry_layout import check, loose_verticals
from tests.support import FIGURE, page


class Geometry(unittest.TestCase):
    def test_width_boundary(self):
        for width in (120, 121):
            found = list(check(page('```\n'+'─'*width+'\n```'), None))
            self.assertEqual(any(f.severity == 'FAIL' for f in found), width == 121)

    def test_vertical_connections(self):
        for body in (['┌──┐','│  │','└──┘'], ['▲','│'], ['◉','│'], ['·','│'], ['╚═╤═╝','  │','┌─┴─┐']):
            self.assertEqual(loose_verticals(body), 0)
        self.assertEqual(loose_verticals(['  │  ']), 1)
        found = list(check(page('```\n  │  \n```'), None))
        self.assertTrue(any(f.severity == 'review' and f.line == 1 and 'loose vertical' in f.message for f in found))

    def test_register_width_exception_and_quotation(self):
        text = '```\nbit 0\n'+'─'*120+'┘\n```'
        found = list(check(page(text), None))
        self.assertFalse(any(f.severity == 'FAIL' for f in found))
        self.assertTrue(any(f.severity == 'review' and 'register' in f.message for f in found))
        found = list(check(page('```\nplain text\n```'), None))
        self.assertTrue(any('quotation' in f.message for f in found))
        self.assertTrue(all(f.severity == 'note' for f in found))

    def test_inventory_contains_layout_measurements(self):
        found = list(check(page(FIGURE.replace('│ s0 │ s1 │','| s0 | s1 |')), None))
        self.assertEqual(found[-1].data, {'figures': 1, 'over_width': 0, 'loose_verticals': 0})
        self.assertFalse(any(f.severity == 'review' and 'ASCII' in f.message for f in found))
