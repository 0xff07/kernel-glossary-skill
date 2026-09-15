"""Examples, counterexamples and masks for style.headings."""
import unittest
from checks.style_headings import check
from tests.support import MINIMAL_PAGE, page

class Examples(unittest.TestCase):
    def test_example_0(self):
        found = list(check(page(''.join(MINIMAL_PAGE.splitlines(keepends=True)[:32] + ['### Why the host resets\n\n\n'] + MINIMAL_PAGE.splitlines(keepends=True)[32:])), None))
        for expected in [(33, 'FAIL', 'headings: …Why the host resets…')]:
            self.assertIn(expected, [(f.line, f.severity, f.message) for f in found])

    def test_minimal_page_has_no_violations(self):
        self.assertFalse([f for f in check(page(MINIMAL_PAGE), None) if f.severity == 'FAIL'])

    def test_source_excerpt_is_not_prose(self):
        text = '# Title\n\n```c\n' + ' '.join(['— **bold** usually walks straightforward vtable']) + '\n```\n'
        self.assertFalse([f for f in check(page(text), None) if f.severity == 'FAIL'])
