"""Behavior and boundaries for sources one version."""
import unittest
from checks.sources_one_version import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_one_pin_and_mixed_pins(self):
        self.assertEqual(list(check(page(skeleton()), None)), [])
        text = skeleton(details=f'### A\n\nSee [`x`]({URL.replace("v0.1", "v0.2")}).\n')
        found = list(check(page(text), None))
        self.assertEqual(len(found), 1)
        self.assertEqual((found[0].line, found[0].severity), (None, 'FAIL'))
