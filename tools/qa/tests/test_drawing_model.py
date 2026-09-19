"""kind: rule — every page carries a model figure under the lead or in SUMMARY."""
import unittest
from checks import drawing_model as rule
from tests.support import FIGURE, PROSE, page, skeleton, observed

def run(**kw):
    return observed(rule.check(page(skeleton(**kw)), None))

class Model(unittest.TestCase):
    def test_a_figure_in_the_lead_or_summary_passes(self):
        found = run(lead=f'A ring hands values from a producer to a consumer.\n\n{FIGURE}')
        self.assertEqual(found.findings, [])
        self.assertIn('model-figure=present', found.footer)
        found = run(summary=f'The model is one struct.\n\n{FIGURE}')
        self.assertEqual(found.findings, [])

    def test_no_figure_or_a_figure_only_in_details_fails(self):
        found = run()
        self.assertEqual(found.findings[0].severity, 'FAIL')
        self.assertIn('no model figure', found.findings[0].message)
        found = run(details=f'### A\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}\n')
        self.assertEqual(found.findings[0].severity, 'FAIL')
        self.assertEqual(found.footer, 'model-figure=absent')
if __name__ == '__main__':
    unittest.main()
