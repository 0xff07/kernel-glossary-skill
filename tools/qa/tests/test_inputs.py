"""inputs: the EXEMPT line grammar, a page's key and place under docs/, and the worksheet verdict."""
import os
import shutil
import tempfile
import unittest

from inputs import Inputs, worksheet_verdict, page_key, page_within


def exemptions_of(lint_text):
    fake = Inputs.__new__(Inputs)
    fake.worksheet_lines = ("## LINT\n" + lint_text).split("\n")
    return fake.exemptions()


class ExemptLines(unittest.TestCase):
    def test_rule_fragment_line_and_ruling(self):
        found = exemptions_of('EXEMPT style.hedges "in practice" 42: a measured statistic | cites its counter\n')
        self.assertEqual(len(found), 1)
        entry = found[0]
        self.assertEqual((entry["rule"], entry["fragment"], entry["line"]), ("style.hedges", "in practice", 42))
        self.assertEqual(entry["ruling"], "a measured statistic | cites its counter")

    def test_part_and_escaped_quote(self):
        found = exemptions_of('EXEMPT style.label-colon/final-colon "says \\"hi\\"": quoted text\n')
        self.assertEqual(found[0]["rule"], "style.label-colon/final-colon")
        self.assertEqual(found[0]["fragment"], 'says "hi"')
        self.assertEqual(found[0]["ruling"], "quoted text")

    def test_a_backslash_in_the_fragment_stays(self):
        found = exemptions_of("EXEMPT sections.coverage-form \"'\\<struct kg_ring\\>'\": the catalog form\n")
        self.assertEqual(found[0]["fragment"], "'\\<struct kg_ring\\>'")

    def test_line_only_and_no_ruling(self):
        found = exemptions_of("EXEMPT style.walk 7\n")
        self.assertEqual((found[0]["fragment"], found[0]["line"], found[0]["ruling"]), (None, 7, ""))

    def test_prose_naming_no_rule_is_not_an_entry(self):
        self.assertEqual(exemptions_of("the EXEMPT verdicts are listed above\n"), [])

    def test_only_the_lint_section_is_read(self):
        fake = Inputs.__new__(Inputs)
        fake.worksheet_lines = ['## EVIDENCE', 'EXEMPT style.walk "walks" 3: not here', '## LINT', 'EXEMPT style.vtable "vtable": here']
        self.assertEqual([e["rule"] for e in fake.exemptions()], ["style.vtable"])


class PagePlace(unittest.TestCase):
    def test_key_and_place_under_docs(self):
        base = os.path.abspath(os.sep + "skill")
        under = os.path.join(base, "docs", "usb4", "router", "tb-switch.md")
        self.assertEqual(page_key(under, base), "usb4/router/tb-switch")
        self.assertEqual(page_within(under, base), ("usb4", "router/tb-switch.md"))
        outside = os.path.abspath(os.sep + "elsewhere" + os.sep + "page.md")
        self.assertEqual(page_key(outside, base), "page")
        self.assertEqual(page_within(outside, base), (None, "page.md"))


class WorksheetVerdict(unittest.TestCase):
    HEAD = "0123456789abcdef"

    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.page = os.path.join(self.base, "docs", "kg", "ring.md")
        os.makedirs(os.path.dirname(self.page))
        open(self.page, "w", encoding="utf-8").write("# ring\n")
        self.worksheet = os.path.join(self.base, "progress", "kg", "kg", "ring.worksheet.md")
        os.makedirs(os.path.dirname(self.worksheet))

    def tearDown(self):
        shutil.rmtree(self.base)

    def write(self, output="docs/kg/ring.md", campaign="kg", version="v0.1, commit 0123456789ab"):
        open(self.worksheet, "w", encoding="utf-8").write(
            f"# Worksheet: ring\n\n## HEADER\n- output path: {output}\n- campaign: {campaign} (directory progress/kg/)\n"
            f"- documented version: {version}\n\n## LINT\n")

    def verdict(self, active=None):
        return worksheet_verdict(self.worksheet, self.page, self.HEAD, self.base, active)

    def test_accepted(self):
        self.write()
        self.assertEqual(self.verdict(), "")
        self.assertEqual(self.verdict(active="kg"), "")

    def test_refusals(self):
        self.assertEqual(self.verdict(), "does not exist")
        self.write(output="docs/kg/other.md")
        self.assertIn("not this page", self.verdict())
        self.write(campaign="other")
        self.assertIn("lies under progress/kg/", self.verdict())
        self.write(version="v0.1, commit fedcba987654")
        self.assertIn("documents commit fedcba987654", self.verdict())
        self.write(version="v0.1")
        self.assertIn("no documented version with its commit", self.verdict())
        self.write()
        self.assertIn("the active campaign is other", self.verdict(active="other"))


if __name__ == "__main__":
    unittest.main()


class RequiredInputs(unittest.TestCase):
    def test_git_errors_are_not_empty_observations(self):
        import subprocess
        from types import SimpleNamespace
        from unittest.mock import patch
        from inputs import git
        failed = SimpleNamespace(returncode=128, stdout='', stderr='cannot read object')
        for outcome in (failed, OSError('cannot execute git'),
                        subprocess.TimeoutExpired('git', 60)):
            options = {'side_effect': outcome} if isinstance(outcome, Exception) else {'return_value': outcome}
            with patch('inputs.subprocess.run', **options), self.assertRaises(OSError):
                git('/tree', 'log', '-1')

    def test_failed_baseline_probe_is_not_an_unborn_repository(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        inputs = Inputs.__new__(Inputs)
        inputs.base, inputs.page_path, inputs.problems = '/kg', '/kg/docs/page.md', []
        good = SimpleNamespace(returncode=0, stdout='true\n', stderr='')
        failed = SimpleNamespace(returncode=128, stdout='', stderr='cannot read object')
        with patch('inputs.subprocess.run', side_effect=[good, failed, failed]):
            inputs._resolve_baseline()
        self.assertTrue(any('cannot read committed baseline' in p for p in inputs.problems))

    def test_source_probe_error_stays_visible_and_gates_source_checks(self):
        from unittest.mock import patch
        from inputs import GitError, MissingInput
        from tests.support import page, skeleton
        inputs = Inputs.__new__(Inputs)
        inputs.tree, inputs.git = '/tree', True
        inputs.tree_tag, inputs.tree_head = 'v0.1', 'a' * 40
        inputs.problems, inputs.source_problems = [], []
        with patch('inputs.git', side_effect=GitError(('rev-parse',), 128, 'cannot read object')):
            inputs.bind_version(page(skeleton()))
        self.assertIn('cannot read object', inputs.problems[0])
        for name in ('tree', 'git'):
            with self.assertRaisesRegex(MissingInput, 'source validation failed'):
                inputs.require(name)

    def test_untagged_checkout_has_no_tag_without_hiding_probe_errors(self):
        from unittest.mock import patch
        inputs = Inputs.__new__(Inputs)
        inputs.problems, inputs.notes, inputs.source_problems = [], [], []
        with patch('inputs.is_kernel_tree', return_value=True), \
             patch('inputs.has_git', return_value=True), \
             patch('inputs.git', side_effect=['a' * 40, '']):
            inputs._resolve_tree('/tree')
        self.assertEqual(inputs.problems, [])
        self.assertEqual(inputs.tree_tag, '')
        self.assertEqual(inputs.tree_head, 'a' * 40)

    def test_required_names_and_source_validation(self):
        from inputs import MissingInput
        from tests.support import TestInputs
        inputs = TestInputs(tree='/resolved/tree', worksheet='## LINT\n', baseline='old')
        self.assertEqual(inputs.require('tree'), '/resolved/tree')
        self.assertEqual(inputs.require('git'), '/resolved/tree')
        self.assertEqual(inputs.require('worksheet'), '<worksheet>')
        self.assertEqual(inputs.require('baseline'), 'old')
        with self.assertRaises(ValueError):
            inputs.require('invented')
        inputs.source_problems = ['the source version differs']
        for name in ('tree','git'):
            with self.assertRaisesRegex(MissingInput,'source version differs'):
                inputs.require(name)
        self.assertEqual(inputs.require('worksheet'), '<worksheet>')

    def test_optional_absent_baseline_and_read_error(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        inputs = Inputs.__new__(Inputs)
        inputs.base = '/kg'
        inputs.page_path = '/kg/docs/page.md'
        inputs.problems = []
        outside = SimpleNamespace(returncode=128,stdout='',stderr='fatal: not a git repository')
        with patch('inputs.subprocess.run',return_value=outside):
            inputs._resolve_baseline()
        self.assertIsNone(inputs.baseline)
        self.assertEqual(inputs.problems,[])
        with patch('inputs.subprocess.run',side_effect=OSError('cannot execute git')):
            inputs._resolve_baseline()
        self.assertTrue(any('cannot read committed baseline' in p for p in inputs.problems))

    def test_bind_version_rejects_mismatch_and_dirty_cited_source(self):
        from unittest.mock import patch
        from tests.support import page, skeleton
        inputs = Inputs.__new__(Inputs)
        inputs.tree = '/tree'
        inputs.git = True
        inputs.tree_tag = 'v0.2'
        inputs.tree_head = 'b'*40
        inputs.problems = []
        inputs.source_problems = []
        def git(tree,*args,**kwargs):
            if args[0]=='rev-parse': return 'a'*40
            if args[0]=='status': return ' M drivers/kg/ring.h\n'
            if args[0]=='ls-files': return 'drivers/kg/ring.h\n'
            return ''
        with patch('inputs.git',side_effect=git):
            inputs.bind_version(page(skeleton()))
        self.assertTrue(any('pins v0.1' in p for p in inputs.problems))
        self.assertTrue(any('uncommitted changes' in p for p in inputs.problems))
        from inputs import MissingInput
        with self.assertRaises(MissingInput):
            inputs.require('tree')
