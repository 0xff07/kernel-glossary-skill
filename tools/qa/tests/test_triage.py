"""kind: command — the triage row of a page from its check document, the grade thresholds, and the table."""
import unittest
import triage
from tests.support import page, skeleton

def document(fails_by_rule=(), data_by_rule=(), state='WRITTEN'):
    results = {}
    for rule, n in fails_by_rule:
        results.setdefault(rule, {'findings': []})['findings'].extend({'severity': 'FAIL', 'message': 'x'} for _ in range(n))
    for rule, data in data_by_rule:
        results.setdefault(rule, {'findings': []})['findings'].append({'severity': 'note', 'message': 'm', 'data': data})
    return {'page': 'docs/kg/ring.md', 'results': results, 'state': state}

class Triage(unittest.TestCase):
    def test_grades_follow_the_two_thresholds(self):
        self.assertEqual(triage.grade_of(0, 3, 4, 10, 10), 'current')
        self.assertEqual(triage.grade_of(5, 1, 5, 3, 10), 'fix')
        self.assertEqual(triage.grade_of(5, 2, 5, 3, 10), 'rebuild')
        self.assertEqual(triage.grade_of(5, 1, 2, 0, 8), 'fix')
        self.assertEqual(triage.grade_of(5, 0, 5, 4, 10), 'rebuild')
        self.assertEqual(triage.grade_of(5, 0, 0, 0, 0), 'fix')

    def test_measures_read_the_document(self):
        doc = document([('excerpts.enclosing', 2), ('arrangement.route', 1), ('drawing.model', 1), ('style.hedges', 1)],
                       [('excerpts.enclosing', {'units': 10, 'findings': 2}), ('excerpts.contiguity', {'units': 10, 'in_functions': 1}),
                        ('excerpts.walkthrough', {'functions': 5, 'incomplete': 1})])
        row = triage.measures(doc, page(skeleton()))
        self.assertEqual((row['fail'], row['excerpt_fail'], row['reading_fail'], row['figure_fail']), (5, 2, 1, 1))
        self.assertEqual((row['units'], row['skeleton'], row['functions'], row['gaps']), (10, 3, 5, 1))
        self.assertEqual(row['grade'], 'fix')
        text = '\n'.join(triage.render([row], 'docs'))
        self.assertIn('fix      kg/ring', text)
        self.assertIn('fix      pages=1', text)
if __name__ == '__main__':
    unittest.main()


class CacheReuse(unittest.TestCase):
    def test_a_cached_document_is_reused_only_under_the_same_inputs(self):
        current = {'page_digest': 'p', 'qa_digest': 'q', 'tree': '/t', 'tree_head': 'h', 'worksheet': '/w', 'worksheet_digest': 'wd', 'spec': None, 'campaign': None, 'baseline': False}
        self.assertTrue(triage.reusable({'inputs': dict(current)}, current))
        for key, other in (('worksheet_digest', 'changed'), ('tree_head', 'h2'), ('tree', '/other'), ('worksheet', None), ('page_digest', 'p2'), ('qa_digest', 'q2')):
            self.assertFalse(triage.reusable({'inputs': dict(current, **{key: other})}, current), key)
        legacy = dict(current); legacy['qa_sha256'] = legacy.pop('qa_digest')
        self.assertTrue(triage.reusable({'inputs': legacy}, current))
