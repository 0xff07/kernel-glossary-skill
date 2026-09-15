"""Current, stale and pre-migration human check-pass records."""
import unittest
from checks.lint_record import check
from inputs import MissingInput
from lint_record import page_state_of
from tests.support import TestInputs, page


class Records(unittest.TestCase):
    def inputs(self, page_digest='a'*64, qa_digest='c'*64, suffix=''):
        return TestInputs(dossier=f'## LINT\nLINTED 2026-09-15 page sha256: {page_digest} qa sha256: {qa_digest}\n{suffix}')

    def test_current_page_and_qa(self):
        inputs = self.inputs(suffix='check pass: self-run\n')
        found = list(check(page('# T'), inputs))
        self.assertEqual(page_state_of(inputs)[0], 'LINTED')
        self.assertTrue(any(f.data and f.data.get('state') == 'LINTED' and f.data['self_run'] for f in found))
        self.assertFalse(any(f.severity == 'review' for f in found))

    def test_stale_page_and_qa(self):
        for inputs in (self.inputs(page_digest='b'*64), self.inputs(qa_digest='d'*64)):
            self.assertEqual(page_state_of(inputs)[0], 'WRITTEN')
            self.assertTrue(any(f.severity == 'review' for f in check(page('# T'), inputs)))

    def test_legacy_missing_and_last_record(self):
        inputs = TestInputs(dossier='## LINT\nLINTED 2026-09-14 page sha256: '+'a'*64)
        self.assertEqual(page_state_of(inputs)[0], 'WRITTEN')
        self.assertTrue(any('legacy' in f.message and f.severity == 'review' for f in check(page('# T'),inputs)))
        self.assertEqual(page_state_of(TestInputs(dossier='## LINT\n'))[0], 'WRITTEN')
        self.assertEqual(page_state_of(TestInputs())[0], 'WRITTEN')
        with self.assertRaises(MissingInput):
            list(check(page('# T'),TestInputs()))
        current=self.inputs(suffix='LINTED 2026-09-16 page sha256: '+'b'*64)
        self.assertEqual(page_state_of(current)[0], 'WRITTEN')


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.lint_record import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
