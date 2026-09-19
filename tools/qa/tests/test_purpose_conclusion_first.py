"""kind: rule — the skim lists every subsection's closer and flags an opener that announces or asks."""
import unittest
from checks import purpose_conclusion_first as rule
from tests.support import PROSE, page, skeleton, observed

def run(opener, closer='The head therefore never passes the tail.'):
    text = skeleton(details=f'### A\n\n{opener} {PROSE}\n\n{PROSE} {closer}\n')
    return observed(rule.check(page(text), None))

class ConclusionFirst(unittest.TestCase):
    def test_a_conclusion_opener_is_not_flagged_and_the_closer_is_listed(self):
        found = run('The head never passes the tail, because the push checks it first.')
        self.assertEqual([r for r in found.rows if r.flags], [])
        self.assertEqual(len(found.rows), 1)
        self.assertIn('closer: The head therefore never passes the tail.', found.rows[0].text)
        self.assertEqual(found.footer, 'subsections=1 announcing-openers=0 questions=0')

    def test_announcing_and_questioning_openers_are_flagged(self):
        found = run('The following shows how the head moves.')
        self.assertTrue(any('announces' in r.flags for r in found.rows))
        found = run('Why does the head never pass the tail?')
        self.assertTrue(any('question' in r.flags for r in found.rows))
        self.assertIn('questions=1', found.footer)
if __name__ == '__main__':
    unittest.main()
