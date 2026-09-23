"""kind: command — the triage row of a page from its check document, and the table."""
import unittest
import triage
from tests.support import page, skeleton


def document(findings=(), state='WRITTEN'):
    results = {}
    for rule, severity, n in findings:
        results.setdefault(rule, {'findings': []})['findings'].extend({'severity': severity, 'message': 'x'} for _ in range(n))
    return {'page': 'docs/kg/ring.md', 'results': results, 'state': state}


class Triage(unittest.TestCase):
    def test_measures_read_the_document(self):
        doc = document([('excerpts.enclosing', 'FAIL', 2), ('excerpts.verbatim', 'FAIL', 1), ('arrangement.route', 'FAIL', 1),
                        ('drawing.model', 'FAIL', 1), ('style.hedges', 'review', 4), ('style.hedges', 'note', 1)], state='LINTED')
        row = triage.measures(doc, page(skeleton()))
        self.assertEqual((row['fail'], row['review'], row['state']), (5, 4, 'LINTED'))
        self.assertEqual(row['families'], {'arrangement': 1, 'drawing': 1, 'excerpts': 3})
        self.assertEqual(row['page'], 'docs/kg/ring.md')

    def test_the_table_sorts_by_fail_and_sums(self):
        clean = triage.measures(document(), page(skeleton()))
        failing = triage.measures(document([('style.hedges', 'FAIL', 2)]), page(skeleton()))
        failing['page'] = 'docs/kg/other.md'
        text = triage.render([clean, failing], 'docs')
        self.assertTrue(text[0].startswith('triage of 2 pages'))
        self.assertIn('kg/other', text[2])
        self.assertIn('style 2', text[2])
        self.assertIn('kg/ring', text[3])
        self.assertEqual(text[-1].split()[:3], ['pages=2', 'with-FAIL=1', 'FAIL=2'])


if __name__ == '__main__':
    unittest.main()
