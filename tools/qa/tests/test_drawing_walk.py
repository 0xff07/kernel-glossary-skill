"""kind: rule — the paragraph after a DETAILS figure with a legend names every mark and links every legend function, in mark order; a lead or SUMMARY figure is left alone."""
import unittest
from checks import drawing_walk as rule
from tests.support import PROSE, page, skeleton, observed
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c'
FIG = '```\n    ┌──────┐  ①  ┌──────┐\n    │ push │ ──► │ head │ ②\n    └──────┘     └──────┘\n    ① kg_ring_push ring.c:3  head advances by one\n    ② kg_ring_reset :9  head returns to zero\n```'
PUSH = f'[`kg_ring_push()`]({BASE}#L1)'
RESET = f'[`kg_ring_reset()`]({BASE}#L7)'

def run(after, where='details'):
    if where == 'details':
        text = skeleton(details=f'### A\n\n{PROSE}\n\n{FIG}\n\n{after}\n')
    else:
        text = skeleton(lead=f'A ring hands values from a producer to a consumer.\n\n{FIG}\n\n{after}')
    return observed(rule.check(page(text), None))

class Walk(unittest.TestCase):
    def test_a_walk_in_mark_order_passes(self):
        found = run(f'{PUSH} ① advances the head by one. {RESET} ② returns it to zero.')
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'figures-with-legend=1 walked=1 missing-names=0 missing-marks=0 out-of-order=0')

    def test_a_missing_function_fails_and_a_reversed_walk_is_reviewed(self):
        found = run(f'{PUSH} ① advances the head by one, and the reset returns it.')
        self.assertEqual(found.findings[0].severity, 'FAIL')
        self.assertIn('does not link kg_ring_reset() (②)', found.findings[0].message)
        found = run(f'{RESET} ② returns the head to zero after {PUSH} ① advanced it.')
        self.assertEqual([f.severity for f in found.findings], ['review'])

    def test_a_walk_that_names_no_mark_fails(self):
        found = run(f'{PUSH} advances the head by one. {RESET} returns it to zero.')
        self.assertEqual([f.severity for f in found.findings], ['FAIL', 'FAIL'])
        self.assertIn('does not name mark ① (kg_ring_push())', found.findings[0].message)
        self.assertIn('does not name mark ②', found.findings[1].message)
        self.assertEqual(found.footer, 'figures-with-legend=1 walked=0 missing-names=0 missing-marks=2 out-of-order=0')

    def test_marks_named_out_of_order_are_reviewed(self):
        found = run(f'{PUSH} advances the head by one at ②, no, at ①, and {RESET} returns it at ②.')
        self.assertEqual([f.severity for f in found.findings], ['review'])

    def test_a_lead_figure_is_left_alone(self):
        found = run('A sentence with no links at all.', where='lead')
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'figures-with-legend=0 walked=0 missing-names=0 missing-marks=0 out-of-order=0')
if __name__ == '__main__':
    unittest.main()
