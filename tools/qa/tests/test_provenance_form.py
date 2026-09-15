"""Behavior and boundaries for provenance form."""
import unittest
from checks.provenance_form import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_valid_units_and_bad_forms(self):
        self.assertEqual(list(check(page(skeleton(details=EXCERPT)), None)), [])
        bad = '```c\nint a;\n/* see ring.c:40 for the rest */\n... int b;\n```'
        found = list(check(page(skeleton(details=bad)), None))
        self.assertEqual([f.severity for f in found], ['FAIL', 'FAIL', 'review'])
        figure = FIGURE.replace('Two indexes', '/* drivers/kg/ring.h:12 */')
        self.assertTrue(any('non-code fence' in f.message for f in check(page(skeleton(details=figure)), None)))

    def test_standalone_elision_and_empty_fence(self):
        self.assertEqual(list(check(page('```c\n/* f.c:1 */\nint a;\n...\nint b;\n```'), None)), [])
        self.assertIn('empty C fence', list(check(page('```c\n```'), None))[0].message)
