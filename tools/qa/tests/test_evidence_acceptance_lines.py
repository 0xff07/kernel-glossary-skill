"""plugins.worksheet: the identity verdicts, the scope-closure and catalog tables of PARITY, the
acceptance lines and the evidence digest, and the LINT record that evidences LINTED."""
import unittest
from inputs import Inputs
from checks import evidence_acceptance_lines as worksheet
from tests.support import page, skeleton, TestInputs, observed
DIGEST = 'a' * 64
OTHER = 'b' * 64
ACCEPTANCE = '- scoped behaviors covered: done\n- claims supported nearby: done\n- guards preserved: done\n- invariants searched: done\n- activation delta: not applicable, nothing switches on\n- modes told apart: not applicable\n- constructs and limits covered: done\n'

class FakeInputs(TestInputs):
    worksheet_section = Inputs.worksheet_section

    def __init__(self, text, how='convention', rejected=(), digest=DIGEST):
        super().__init__()
        self.worksheet_lines = text.split('\n') if text is not None else None
        self.worksheet = '<worksheet>' if text is not None else None
        self.worksheet_how = how
        self.worksheet_rejected = list(rejected)
        self.page_digest = digest

def check(name, text, **fields):
    return observed(worksheet.check(page(skeleton()), FakeInputs(text, **fields)))

class Acceptance(unittest.TestCase):

    def test_all_lines_and_a_current_digest(self):
        result = check('acceptance-lines', f'## EVIDENCE\n{ACCEPTANCE}page sha256: {DIGEST}\n')
        self.assertEqual(result.findings, [])
        self.assertEqual(result.data['digest'], 'current')

    def test_a_missing_line_and_a_stale_digest(self):
        text = f"## EVIDENCE\n{ACCEPTANCE.replace('- guards preserved: done', '')}page sha256: {OTHER}\n"
        result = check('acceptance-lines', text)
        messages = [f.message for f in result.findings]
        self.assertTrue(any(('guards preserved' in m for m in messages)))
        self.assertTrue(any(('predates an edit' in m for m in messages)))
        self.assertEqual(result.data['digest'], 'stale')
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.evidence_acceptance_lines import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
