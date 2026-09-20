"""kind: rule — a marked series uses one alphabet from its first symbol, and consecutive series take
the alphabets in the cycle ① ❶ Ⓐ ⓐ ⓵."""
import unittest
from checks import drawing_marks as rule
from pagemodel import next_alphabet
from tests.support import PROSE, page, skeleton, TestInputs, observed

OUTLINE = '| piece | lines | stage |\n|---|---|---|\n| ① | drivers/kg/ring.c:1-5 | pushes |\n| ② | drivers/kg/ring.c:6-11 | resets |\n'


def figure(marks):
    legend = '\n'.join(f'    {m} kg_ring_push ring.c:3  head advances by one' for m in marks)
    return f'```\n    ┌──────┐  {marks[0]}  ┌──────┐\n    │ push │ ──► │ head │\n    └──────┘     └──────┘\n{legend}\n```'


def details(*blocks):
    return '### A\n\n' + f'\n\n{PROSE}\n\n'.join(blocks) + f'\n\n{PROSE}\n'


class Marks(unittest.TestCase):

    def run_on(self, text):
        return observed(rule.check(page(skeleton(details=text)), TestInputs()))

    def severities(self, found):
        return [f.severity for f in found.all if f.severity != 'note']

    def test_the_cycle_passes(self):
        found = self.run_on(details(OUTLINE, figure('❶❷'), figure('ⒶⒷⒸ'), figure('ⓐ'), figure('⓵⓶'), figure('①')))
        self.assertEqual(self.severities(found), [])
        self.assertEqual(found.footer, 'series=6 mixed=0 gaps=0 out-of-cycle=0')

    def test_a_series_out_of_the_cycle_is_listed_for_reading(self):
        found = self.run_on(details(OUTLINE, figure('①②')))
        reviews = [f.message for f in found.all if f.severity == 'review']
        self.assertEqual(len(reviews), 1)
        self.assertIn('counts in circled digits; the cycle ① ❶ Ⓐ ⓐ ⓵ puts negative circled digits (❶) here', reviews[0])
        found = self.run_on(details(OUTLINE, figure('ⒶⒷ')))
        self.assertEqual(len([f for f in found.all if f.severity == 'review']), 1)

    def test_a_long_series_skips_the_short_alphabets(self):
        eleven = '①②③④⑤⑥⑦⑧⑨⑩⑪'
        found = self.run_on(details(figure('①'), figure('❶'), figure('Ⓐ'), figure('ⓐ'), figure(eleven)))
        self.assertEqual(self.severities(found), [])
        self.assertEqual(next_alphabet('circled small letters', 11), 'circled digits')
        self.assertEqual(next_alphabet('circled small letters', 10), 'double-circled digits')
        self.assertEqual(next_alphabet(None, 3), 'circled digits')

    def test_negative_digits_continue_past_ten(self):
        found = self.run_on(details(OUTLINE, figure('❶❷❸❹❺❻❼❽❾❿⓫⓬')))
        self.assertEqual(self.severities(found), [])

    def test_a_mixed_series_fails_and_a_gap_is_read(self):
        found = self.run_on(details(figure('①Ⓑ'), figure('❶❸')))
        fails = [f.message for f in found.all if f.severity == 'FAIL']
        reviews = [f.message for f in found.all if f.severity == 'review']
        self.assertEqual(len(fails), 1)
        self.assertIn('two alphabets', fails[0])
        self.assertEqual(len(reviews), 1)
        self.assertIn('runs ❶❸', reviews[0])


if __name__ == '__main__':
    unittest.main()
