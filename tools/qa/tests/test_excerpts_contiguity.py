'kind: rule — a unit carries at most two elisions and every run after an elision is at least three\nlines unless it is the closing line alone; an unelided unit and a run that closes the construct pass.'
import unittest
from checks import excerpts_contiguity as rule
from tests.support import PROSE, page, skeleton, observed

def run(*lines):
    fence = '```c\n/* drivers/kg/ring.h:6 */\n' + '\n'.join(lines) + '\n```'
    found = observed(rule.check(page(skeleton(details=f'### A\n\n{PROSE}\n\n{fence}\n\n{PROSE}\n')), None))
    return [f.message for f in found.all if f.severity == 'FAIL'], found.footer

class Contiguity(unittest.TestCase):

    def test_two_elisions_around_runs_of_three_pass(self):
        fails, footer = run('struct kg_ring {', '...', '\tint a;', '\tint b;', '\tint c;', '...', '};')
        self.assertEqual(fails, [])
        self.assertEqual(footer, 'units=1 elisions=2 elided=1 findings=0')

    def test_a_single_line_between_elisions_is_a_fragment(self):
        fails, _ = run('struct kg_ring {', '...', '\tint b;', '...', '};')
        self.assertEqual(len(fails), 1)
        self.assertIn("a run of 1 after an elision ('int b;'), at least 3 lines", fails[0])

    def test_three_elisions_fail(self):
        fails, _ = run('struct kg_ring {', '...', '\tint a;', '\tint b;', '\tint c;', '...', '\tint d;', '\tint e;', '\tint f;', '...', '};')
        self.assertEqual(len(fails), 1)
        self.assertIn('3 elisions, at most 2', fails[0])

    def test_an_opener_with_nothing_after_the_elision_is_a_truncation(self):
        fails, _ = run('struct kg_ring {', '...')
        self.assertEqual(len(fails), 1)
        self.assertIn('ends on an elision, which truncates the construct', fails[0])

    def test_a_short_last_run_that_is_not_the_closing_line_fails(self):
        fails, _ = run('struct kg_ring {', '...', '\tint b;', '};')
        self.assertEqual(len(fails), 1)
        fails, _ = run('/**', ' * struct kg_ring - a ring', '...', ' * @a: a', ' * @b: b', ' * @c: c', ' */')
        self.assertEqual(fails, [])

    def test_the_stitch_before_a_second_unit_is_not_an_elision_but_a_trailing_one_is_a_truncation(self):
        fails, footer = run('struct kg_ring {', '\tint a;', '\tint b;', '...', '/* drivers/kg/ring.c:1 */', 'int kg_push(void)', '{', '}')
        self.assertEqual(fails, [])
        self.assertEqual(footer, 'units=2 elisions=1 elided=0 findings=0')
        fails, _ = run('struct kg_ring {', '\tint a;', '\tint b;', '...')
        self.assertEqual(len(fails), 1)
        self.assertIn('ends on an elision, which truncates the construct', fails[0])

    def test_an_unelided_unit_is_not_counted(self):
        fails, footer = run('struct kg_ring {', '\tint a;', '};')
        self.assertEqual(fails, [])
        self.assertEqual(footer, 'units=1 elisions=0 elided=0 findings=0')
if __name__ == '__main__':
    unittest.main()
