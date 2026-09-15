"""Execution failures, partial findings, selections and report semantics."""
import contextlib
import io
import json
import unittest

import kg
import report
import rules
from inputs import MissingInput
from tests.support import TestInputs, page


def binding(check, id='test.example'):
    return rules.Binding(id, check, 'guidelines/test.md:3', 'tools/qa/checks/test_example.py', 'tools/qa/tests/test_test_example.py')


class Execution(unittest.TestCase):
    def test_generator_missing_input_preserves_prior_findings(self):
        def check(page, inputs):
            yield report.Finding(1, 'review', 'independent work')
            inputs.require('tree')
        result, = kg.run_rules(page('# T'), TestInputs(), [binding(check)])
        self.assertEqual(result.findings, [report.Finding(1,'review','independent work')])
        self.assertEqual(result.skipped, 'no kernel tree')
        self.assertEqual(report.exit_status([result],TestInputs()), 2)
        text, _ = report.render_text([result],['# T'],None,
            type('Inputs',(TestInputs,),{'report_lines':lambda self: []})(), 'WRITTEN')
        self.assertIn('independent work',text)
        self.assertIn('INCOMPLETE',text)
        doc=json.loads(report.render_json('page.md',[result],
            type('Inputs',(TestInputs,),{'as_dict':lambda self: {}})(),'WRITTEN'))
        self.assertFalse(doc['complete'])
        self.assertEqual(doc['results']['test.example']['findings'][0]['severity'],'review')

    def test_late_error_continues_with_other_checks(self):
        def broken(page, inputs):
            yield report.Finding(1,'FAIL','a real defect')
            raise RuntimeError('boom')
        good=lambda p,i: [report.Finding(1,'note','still ran')]
        results=kg.run_rules(page('# T'),TestInputs(),[binding(broken),binding(good,'test.other')])
        self.assertIn('RuntimeError: boom',results[0].error)
        self.assertEqual(results[0].fails,1)
        self.assertEqual(results[1].findings[0].message,'still ran')
        self.assertEqual(report.exit_status(results,TestInputs()),1)

    def test_invalid_outputs_are_errors(self):
        for value in (None,['text'],[report.Finding(1,'PASS','x')],[report.Finding(0,'note','x')],
                      [report.Finding(True,'note','x')],[report.Finding(1,'note',None)],
                      [report.Finding(1,'note','x',{'bad':set()})]):
            result,=kg.run_rules(page('# T'),TestInputs(),[binding(lambda p,i: value)])
            self.assertIsNotNone(result.error,repr(value))
            self.assertEqual(report.exit_status([result],TestInputs()),1)

    def test_zero_findings_does_not_claim_guideline_pass(self):
        result,=kg.run_rules(page('# T'),TestInputs(),[binding(lambda p,i: [])])
        self.assertEqual(result.state(),'0 findings')
        self.assertEqual(report.exit_status([result],TestInputs()),0)
        self.assertEqual(report.requirement_state({'slug':'test.example','marker':'qa'},[result])[0],'0 findings')

    def test_explicit_selection_is_strict(self):
        found=[binding(lambda p,i: [])]
        for selection in ([],['unknown.rule'],['test.example','unknown.rule']):
            with self.assertRaises(rules.RuleError):
                kg.run_rules(page('# T'),TestInputs(),found,selection)
        self.assertEqual(len(kg.run_rules(page('# T'),TestInputs(),found,['test.example'])),1)

    def test_empty_cli_selection_is_an_error_not_missing_input(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(kg.main(['check', 'unused.md', '--only']), 1)

    def test_page_only_anchor_work_precedes_missing_tree(self):
        from checks.links_definition_line import check
        text='The [`struct ring`](https://example.org/definition) and `ring`.'
        result,=kg.run_rules(page(text),TestInputs(),[binding(check,'links.definition-line')])
        self.assertTrue(any('drops the `struct`' in f.message for f in result.findings))
        self.assertEqual(result.skipped,'no kernel tree')
