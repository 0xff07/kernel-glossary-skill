"""Behavior and boundaries for links bare spans."""
import unittest
from checks.links_bare_spans import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_literal_and_unsettled_cell(self):
        text = '| member | role |\n|---|---|\n| `head` | index |\n| `0` | literal |'
        found = list(check(page(skeleton(details=text)), None))
        self.assertTrue(any(f.severity == 'review' and 'bare cell `head`' in f.message for f in found))
        self.assertTrue(any(f.severity == 'note' and 'bare literal cell `0`' in f.message for f in found))
        self.assertFalse(any(f.severity == 'FAIL' for f in found))

    def test_bare_span_inventory_retains_reason(self):
        found = list(check(page('The helper returns `-EINVAL`.'), None))
        self.assertTrue(any(f.severity == 'review' and 'error value' in f.message for f in found))
        linked = list(check(page(f'The [`head`]({URL}) advances.'), None))
        self.assertFalse(any(f.severity == 'review' for f in linked))
