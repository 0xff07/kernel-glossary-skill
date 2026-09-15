"""Behavior and boundaries for arrangement open close."""
import unittest
from checks.arrangement_open_close import check
from tests.support import CAUTION, EXCERPT, FIGURE, PROSE, URL, MINIMAL_PAGE, TestInputs, observed, page, skeleton

class Behavior(unittest.TestCase):

    def test_open_close_and_recovery(self):
        bad = skeleton(details=f'### A\n\n{EXCERPT}\n\n{FIGURE}')
        found = list(check(page(bad), None))
        for fragment in ('opens with C', 'ends with D', 'no prose between'):
            self.assertTrue(any(f.severity == 'review' and fragment in f.message for f in found), fragment)
        good = skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n{PROSE}\n\n{FIGURE}\n\n{PROSE}')
        self.assertEqual(list(check(page(good), None)), [])

    def test_opening_and_closing_have_distinct_sentence_limits(self):
        for opening_count, closing_count, expected in ((4, 3, []), (5, 3, ['opening']), (4, 4, ['closing'])):
            opening = 'The ring advances. ' * opening_count
            closing = 'The ring drains. ' * closing_count
            text = skeleton(details=f'### A\n\n{opening}\n\n{EXCERPT}\n\n{closing}')
            found = list(check(page(text), None))
            self.assertEqual(len(found), len(expected))
            for finding, fragment in zip(found, expected):
                self.assertEqual(finding.severity, 'review')
                self.assertIn(fragment, finding.message)

    def test_empty_subsection_does_not_invent_a_boundary(self):
        self.assertEqual(list(check(page(skeleton(details='### Empty\n')), None)), [])


class ListsAreNotRecovery(unittest.TestCase):

    def test_a_list_between_two_blocks_is_named(self):
        found = list(check(page(skeleton(details=f'### A\n\n{PROSE}\n\n{EXCERPT}\n\n- one item\n- another\n\n{FIGURE}\n\n{PROSE}')), None))
        self.assertTrue(any('no prose between (a list is not recovery)' in f.message for f in found), [f.message for f in found])
