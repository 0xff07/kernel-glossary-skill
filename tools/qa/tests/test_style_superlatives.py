"""Examples, counterexamples and masks for style.superlatives."""
import unittest
from checks.style_superlatives import check
from tests.support import MINIMAL_PAGE, page

class Examples(unittest.TestCase):
    def test_example_0(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:34] + ['The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array. That is the key invariant of the ring.\n'] + MINIMAL_PAGE.splitlines(keepends=True)[35:])), None))
        for expected in [(35, 'FAIL', 'superlatives: …values. § holds both indexes beside the slot array. That is the key invariant of the ring.…')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_example_1(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:34] + ['The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array. The fast path skips the lock.\n'] + MINIMAL_PAGE.splitlines(keepends=True)[35:])), None))
        for expected in [(35, 'review', 'superlatives: …stored values. § holds both indexes beside the slot array. The fast path skips the lock.…')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_example_2(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:34] + ['The producer writes at the head and the consumer reads at the tail, and the difference between the two indexes is the number of stored values. [`struct kg_ring`](https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.h#L12) holds both indexes beside the slot array. The macros are what the ring code applies.\n'] + MINIMAL_PAGE.splitlines(keepends=True)[35:])), None))
        for expected in [(35, 'review', 'superlatives: …ues. § holds both indexes beside the slot array. The macros are what the ring code applies.… (the fix: state it directly)')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_minimal_page_has_no_violations(self):
        self.assertFalse([f for f in check(page(MINIMAL_PAGE), None) if f.severity == 'FAIL'])

    def test_source_excerpt_is_not_prose(self):
        text = '# Title\n\n```c\n' + ' '.join(['— **bold** usually walks straightforward vtable']) + '\n```\n'
        self.assertFalse([f for f in check(page(text), None) if f.severity == 'FAIL'])
