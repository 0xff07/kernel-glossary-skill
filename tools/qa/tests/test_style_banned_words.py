"""Examples, counterexamples and masks for style.banned-words."""
import unittest
from checks.style_banned_words import check
from tests.support import MINIMAL_PAGE, page

class Examples(unittest.TestCase):
    def test_example_0(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:34] + ['The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array. The contract is the tally.\n'] + MINIMAL_PAGE.splitlines(keepends=True)[35:])), None))
        for expected in [(35, 'FAIL', 'banned words: …red values. § holds both indexes beside the slot array. The contract is the tally.…')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_example_1(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:34] + ['The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array. The else arm handles it.\n'] + MINIMAL_PAGE.splitlines(keepends=True)[35:])), None))
        for expected in [(35, 'review', 'banned words: …values. § holds both indexes beside the slot array. The else arm handles it.…')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_minimal_page_has_no_violations(self):
        self.assertFalse([f for f in check(page(MINIMAL_PAGE), None) if f.severity == 'FAIL'])

    def test_source_excerpt_is_not_prose(self):
        text = '# Title\n\n```c\n' + ' '.join(['— **bold** usually walks straightforward vtable']) + '\n```\n'
        self.assertFalse([f for f in check(page(text), None) if f.severity == 'FAIL'])


class ArmExemption(unittest.TestCase):

    def test_arm64_is_not_the_noun_arm(self):
        found = list(check(page('On ARM64 and arm64 hosts the timer fires.'), None))
        self.assertFalse([f for f in found if f.severity in ('FAIL', 'review')])
        found = list(check(page('The else arm handles it.'), None))
        self.assertTrue(any(f.severity == 'review' for f in found))
