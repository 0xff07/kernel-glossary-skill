"""Behavior and boundaries for sections coverage form."""
import unittest
from checks.sections_coverage_form import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_catalog_form_and_unreadable_bullets(self):
        self.assertEqual(list(check(page(skeleton()), None)), [])
        for wrong in (skeleton().replace(r"'\<struct kg_ring\>'", r"'\\<struct kg_ring\\>'"),
                      skeleton().replace(r"[`'\<struct kg_ring\>':'drivers/kg/ring.h'`]", '[`struct kg_ring`]')):
            found = list(check(page(wrong), None))
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].severity, 'FAIL')
