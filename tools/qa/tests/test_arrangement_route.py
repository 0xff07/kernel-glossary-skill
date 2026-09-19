"""kind: rule — DETAILS opens with one route paragraph of three to five sentences before its first subsection."""
import unittest
from checks import arrangement_route as rule
from tests.support import PROSE, page, skeleton, observed
ROUTE = 'The first subsection shows the record. The second shows the writers. The third shows the readers, and the last closes the walk.'

def run(preamble, details='### A\n\n' + PROSE + '\n'):
    text = skeleton(details=(preamble + '\n\n' if preamble else '') + details)
    return observed(rule.check(page(text), None))

class Route(unittest.TestCase):
    def test_a_route_of_three_to_five_sentences_passes_and_is_listed(self):
        found = run(ROUTE)
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'route=present sentences=3 subsections=1')
        self.assertTrue(any('route 1:' in f.message for f in found.all))

    def test_no_route_fails_and_a_short_or_double_route_is_reviewed(self):
        found = run('')
        self.assertIn('DETAILS opens on its first subsection', found.findings[0].message)
        self.assertEqual(found.findings[0].severity, 'FAIL')
        found = run('Two sentences only. Not enough.')
        self.assertIn('has 2 sentences', found.findings[0].message)
        found = run(ROUTE + '\n\nA second paragraph before the first subsection.')
        self.assertTrue(any('2 paragraphs before the first subsection' in f.message for f in found.findings))
if __name__ == '__main__':
    unittest.main()
