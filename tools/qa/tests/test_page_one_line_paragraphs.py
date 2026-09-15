"""Behavior and boundaries for page one line paragraphs."""
import unittest
from checks.page_one_line_paragraphs import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_wrapped_paragraph_and_blank_separator(self):
        found = list(check(page('A first line\nand continuation.\n'), None))
        self.assertEqual((found[0].line, found[0].severity), (2, 'FAIL'))
        self.assertEqual(list(check(page('A first line.\n\nAnother paragraph.\n'), None)), [])

    def test_tabs_are_kept_in_source(self):
        self.assertEqual(list(check(page('```c\n\tint a;\n```'), None)), [])
        found = list(check(page('```c\n        int a;\n```'), None))
        self.assertEqual(found[0].severity, 'review')
