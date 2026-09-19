"""kind: rule — a "So far," recap paragraph closes a subsection at most every four subsections."""
import unittest
from checks import arrangement_recap as rule
from tests.support import PROSE, page, skeleton, observed

def details(n, recap_at=()):
    out = []
    for k in range(1, n + 1):
        body = f'### Section {k}\n\n{PROSE}\n'
        if k in recap_at:
            body += '\nSo far, the ring holds its head and its tail and nothing has moved them.\n'
        out.append(body)
    return '\n'.join(out)

def run(text):
    return observed(rule.check(page(skeleton(details=text)), None))

class Recap(unittest.TestCase):
    def test_short_details_need_no_recap(self):
        found = run(details(4))
        self.assertEqual(found.findings, [])
        self.assertIn('no recap needed', found.footer)

    def test_a_run_over_four_is_reviewed_and_a_recap_resets_it(self):
        found = run(details(6))
        self.assertEqual(len(found.findings), 1)
        self.assertIn('5 subsections since the last recap', found.findings[0].message)
        found = run(details(6, recap_at=(3,)))
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'subsections=6 recaps=1 max-run=3')
        self.assertTrue(any('recap after 3 subsection(s): So far, the ring' in f.message for f in found.all))

    def test_a_long_recap_is_reviewed(self):
        long_recap = 'So far, one. Two. Three. Four sentences is too many.'
        text = details(6, recap_at=(3,)).replace('So far, the ring holds its head and its tail and nothing has moved them.', long_recap)
        found = run(text)
        self.assertTrue(any('a recap of 4 sentences' in f.message for f in found.findings))
if __name__ == '__main__':
    unittest.main()
