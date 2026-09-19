"""Page state follows shared LINT records, full execution and content digests."""
import tempfile
import unittest
from pathlib import Path

import kg
from lint_record import qa_digest
from report import Finding, Result
from tests.support import TestInputs
from tests.test_runner import binding


class State(unittest.TestCase):
    def inputs(self):
        return TestInputs(worksheet='## LINT\nLINTED 2026-09-15 page sha256: '+'a'*64+' qa sha256: '+'c'*64)

    def test_matching_record_and_failed_or_incomplete_run(self):
        clean=Result(binding(lambda p,i: []))
        self.assertEqual(kg.page_state([clean],self.inputs())[0],'LINTED')
        for result in (Result(clean.rule,[Finding(1,'FAIL','defect')]),Result(clean.rule,error='boom'),Result(clean.rule,skipped='no tree')):
            self.assertEqual(kg.page_state([result],self.inputs())[0],'WRITTEN')
        inputs=self.inputs();inputs.problems.append('input error')
        self.assertEqual(kg.page_state([clean],inputs)[0],'WRITTEN')

    def test_partial_run_and_missing_record(self):
        self.assertEqual(kg.page_state([],self.inputs(),only=True)[0],'not evaluated')
        self.assertEqual(kg.page_state([],TestInputs())[0],'WRITTEN')

    def test_qa_digest_tracks_runtime_and_guidelines_but_not_tests_or_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'tools/qa/checks').mkdir(parents=True)
            (root/'tools/qa/tests').mkdir()
            (root/'guidelines').mkdir()
            files=['guidelines/writing.md','tools/qa/kg.py','tools/qa/pagemodel.py','tools/qa/checks/example.py']
            for name in files:
                (root/name).write_text('first')
            original=qa_digest(root)
            self.assertEqual(qa_digest(root),original)
            for name in ('tools/qa/tests/test_example.py','tools/qa/DESIGN.md'):
                (root/name).write_text('outside digest')
            self.assertEqual(qa_digest(root),original)
            for name in files:
                path=root/name;path.write_text('other')
                self.assertNotEqual(qa_digest(root),original,name)
                path.write_text('first')
            (root/'tools/qa/helper.py').write_text('new shared helper')
            self.assertNotEqual(qa_digest(root),original)
