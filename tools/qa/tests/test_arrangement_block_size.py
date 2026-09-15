"""Behavior and boundaries for arrangement block size."""
import unittest
from checks.arrangement_block_size import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_source_and_figure_boundaries(self):
        for count in (40,41):
            code = '```c\n/* f.c:1 */\n'+'\n'.join(['int a;']*count)+'\n```'
            found = list(check(page(skeleton(details='### A\n\n'+code)), None))
            self.assertEqual(any(f.severity == 'review' for f in found), count == 41)
        for count in (80,81):
            figure = '```\n'+'\n'.join(['─']*count)+'\n```'
            found = list(check(page(skeleton(details='### A\n\n'+figure)), None))
            self.assertEqual(any(f.severity == 'review' for f in found), count == 81)
