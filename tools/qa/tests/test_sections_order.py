"""Behavior and boundaries for sections order."""
import unittest
from checks.sections_order import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_slot_alternatives_and_wrong_order(self):
        for title in ('REGISTERS', 'METHODS', 'PRIMITIVES', 'INTERFACES'):
            text = skeleton(registers='x').replace('## REGISTERS', '## '+title)
            self.assertEqual(list(check(page(text), None)), [], title)
        self.assertEqual(list(check(page(skeleton()), None)), [])
        wrong = skeleton().replace('## SUMMARY','## TMP').replace('## SPECIFICATIONS','## SUMMARY').replace('## TMP','## SPECIFICATIONS')
        self.assertEqual(list(check(page(wrong), None))[0].severity, 'FAIL')
