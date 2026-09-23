"""records: the first pass recorded once the page is whole, the last run recorded on every full
run, and the delta the text report prints against it."""
import collections
import json
import os
import shutil
import tempfile
import unittest

import records
import report
from report import Finding, Result
from tests.support import TestInputs, page, skeleton
from tests.test_runner import binding


def result(rule_id, *findings):
    return Result(binding(lambda p, i: [], rule_id), list(findings))


class Keys(unittest.TestCase):
    def test_a_moved_finding_keeps_its_key(self):
        a = Finding(674, 'review', '674 COUNT [NEW]: bare req x2 at [674, 698]')
        b = Finding(702, 'review', '702 COUNT [carried]: bare req x3 at [702, 731, 800]')
        self.assertEqual(report.finding_key('links.bare-spans', a), report.finding_key('links.bare-spans', b))
        self.assertNotEqual(report.finding_key('links.bare-spans', a), report.finding_key('other.rule', a))
        self.assertNotEqual(report.finding_key('r', Finding(1, 'review', 'P@12 words=130, over 120')),
                            report.finding_key('r', Finding(1, 'FAIL', 'P@12 words=130, over 120')))
        self.assertEqual(report.finding_key('r', Finding(1, 'review', 'P@12 words=130, over 120')),
                         report.finding_key('r', Finding(9, 'review', 'P@90 words=130, over 120')))

    def test_keys_of_a_run_count_repeats(self):
        found = [result('a', Finding(1, 'review', 'same'), Finding(2, 'review', 'same'), Finding(3, 'note', 'ignored'))]
        self.assertEqual(records.keys_of(found), collections.Counter({'a|review|same': 2}))


class Records(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.inputs = TestInputs()
        self.inputs.first_pass_path = os.path.join(self.root, 'ring.first-pass.json')
        self.inputs.last_run_path = os.path.join(self.root, 'ring.last-run.json')
        self.inputs.page_digest = self.inputs.qa_digest = 'd' * 64

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_the_first_pass_waits_for_the_whole_page_and_is_written_once(self):
        draft = page('# T\n\n## SUMMARY\n\nOne.\n\n## DETAILS\n\n### A\n\nTwo.\n')
        note = records.record_first_pass('docs/kg/ring.md', draft, [result('a', Finding(1, 'FAIL', 'x'))], self.inputs)
        self.assertIn('draft: no SPECIFICATIONS, COVERAGE, DOCUMENTATION, OTHER SOURCES', note)
        self.assertFalse(os.path.exists(self.inputs.first_pass_path))
        whole = page(skeleton())
        note = records.record_first_pass('docs/kg/ring.md', whole, [result('a', Finding(1, 'FAIL', 'x'))], self.inputs)
        self.assertIn('first pass recorded at', note)
        first = json.load(open(self.inputs.first_pass_path, encoding='utf-8'))
        self.assertEqual(first['rules'], {'a': {'FAIL': 1, 'review': 0, 'complete': True}})
        self.assertIsNone(records.record_first_pass('docs/kg/ring.md', whole, [result('a')], self.inputs))
        self.assertEqual(json.load(open(self.inputs.first_pass_path, encoding='utf-8')), first)

    def test_a_worksheet_with_a_check_pass_record_is_past_its_first_pass(self):
        from inputs import Inputs
        self.inputs.worksheet_lines = ['## LINT', 'LINTED 2026-09-01 page sha256: ' + 'a' * 64 + ' qa sha256: ' + 'b' * 64]
        self.inputs.worksheet_section = lambda name: Inputs.worksheet_section(self.inputs, name)
        self.assertIsNone(records.record_first_pass('docs/kg/ring.md', page(skeleton()), [], self.inputs))
        self.assertFalse(os.path.exists(self.inputs.first_pass_path))

    def test_no_worksheet_path_no_record(self):
        self.inputs.first_pass_path = None
        self.assertIn('no worksheet path', records.record_first_pass('p.md', page(skeleton()), [], self.inputs))

    def test_the_last_run_round_trips(self):
        self.assertIsNone(records.read_last_run(self.inputs.last_run_path))
        keys = collections.Counter({'a|review|same': 2, 'b|FAIL|x': 1})
        records.record_last_run('docs/kg/ring.md', [result('a')], self.inputs, keys)
        previous = records.read_last_run(self.inputs.last_run_path)
        self.assertEqual(previous['keys'], keys)
        self.assertTrue(previous['date'])


class Delta(unittest.TestCase):
    def test_standing_reviews_are_counted_and_new_ones_printed(self):
        found = [result('a', Finding(1, 'review', 'stood'), Finding(2, 'review', 'fresh'),
                        Finding(3, 'FAIL', 'a standing defect'), Finding(4, 'FAIL', 'a new defect'))]
        previous = {'date': '2026-09-23', 'keys': collections.Counter(
            {'a|review|stood': 1, 'a|FAIL|a standing defect': 1, 'a|review|repaired': 2})}
        inputs = type('Inputs', (TestInputs,), {'report_lines': lambda self: []})()
        text, tally = report.render_text(found, ['# T'] * 5, None, inputs, '== state: WRITTEN', previous=previous)
        self.assertNotIn('stood', text)
        self.assertIn('review: 2: fresh', text)
        self.assertIn('FAIL: 3: a standing defect (standing)', text)
        self.assertIn('FAIL: 4: a new defect', text)
        self.assertIn('standing: 1 review as at the last run; --only a lists them', text)
        self.assertIn('== since the last run (2026-09-23): 2 new, 2 gone, 1 standing review', text)
        self.assertEqual((tally['new'], tally['standing']), (2, 1))

    def test_without_a_record_everything_is_printed(self):
        found = [result('a', Finding(1, 'review', 'stood'))]
        inputs = type('Inputs', (TestInputs,), {'report_lines': lambda self: []})()
        text, _tally = report.render_text(found, ['# T'] * 2, None, inputs, '== state: WRITTEN')
        self.assertIn('review: 1: stood', text)
        self.assertNotIn('since the last run', text)
