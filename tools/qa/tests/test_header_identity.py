"""plugins.worksheet: the identity verdicts, the scope-closure and catalog tables of PARITY, the
acceptance lines and the evidence digest, and the LINT record that evidences LINTED."""
import unittest
from inputs import Inputs
from checks import header_identity as worksheet
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

class Identity(unittest.TestCase):

    def test_a_refused_candidate_found_by_convention_is_counted_only(self):
        result = check('identity', None, rejected=['worksheet x names another page; not used'])
        self.assertEqual(result.findings, [])
        self.assertIn('refused=1', result.footer)

    def test_a_refused_candidate_named_by_option_fails(self):
        result = check('identity', None, how='option', rejected=['worksheet x names another page; not used'])
        self.assertEqual([f.severity for f in result.findings], ['FAIL'])

    def test_no_worksheet_at_all(self):
        result = check('identity', None)
        self.assertEqual([f.severity for f in result.findings], ['note'])
        self.assertIn('WRITTEN on this machine', result.findings[0].message)
if __name__ == '__main__':
    unittest.main()
