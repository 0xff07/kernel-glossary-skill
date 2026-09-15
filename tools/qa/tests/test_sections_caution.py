"""Behavior and boundaries for sections caution."""
import unittest
from checks.sections_caution import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_exact_caution_and_first_line(self):
        self.assertEqual(list(check(page(skeleton()), None)), [])
        found = list(check(page(skeleton().replace('STRICTLY DO NOT', 'DO NOT')), None))
        self.assertEqual((found[0].line, found[0].severity), (3, 'FAIL'))
        found = list(check(page('before\n'+skeleton()), None))
        self.assertTrue(any(f.line == 1 and f.severity == 'FAIL' for f in found))

    def test_short_page_is_a_violation_without_an_invalid_location(self):
        import kg
        from tests.test_runner import binding
        for text in ('', '# T'):
            result, = kg.run_rules(page(text), TestInputs(), [binding(check, 'sections.caution')])
            self.assertIsNone(result.error)
            self.assertTrue(any(f.line is None and f.severity == 'FAIL' and 'caution' in f.message
                                for f in result.findings))
