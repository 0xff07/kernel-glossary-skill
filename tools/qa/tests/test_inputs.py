"""inputs: the EXEMPT line grammar, a page's key and place under docs/, and the worksheet path."""
import os
import shutil
import tempfile
import unittest

from unittest.mock import patch

from inputs import Inputs, page_key, page_within, subsystem_entry


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


class WorksheetPath(unittest.TestCase):
    """One path by convention or option, never a search, and nothing in the file checked for identity."""

    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.page = os.path.join(self.base, "docs", "kg", "ring.md")
        os.makedirs(os.path.dirname(self.page))
        open(self.page, "w", encoding="utf-8").write("# ring\n")

    def tearDown(self):
        shutil.rmtree(self.base)

    def resolve(self, worksheet=None, spec=None, page=None):
        inputs = Inputs.__new__(Inputs)
        inputs.base, inputs.page_path, inputs.spec = self.base, page or self.page, spec
        inputs.problems, inputs.notes = [], []
        with patch.dict(os.environ):
            os.environ.pop("KG_WORKSHEET", None)
            inputs._resolve_worksheet(worksheet)
        return inputs

    def test_the_conventional_path_follows_the_pages_directory(self):
        expected = os.path.join(self.base, "progress", "kg", "kg", "ring.worksheet.md")
        inputs = self.resolve()
        self.assertEqual(inputs.worksheet_path, expected)
        self.assertEqual(inputs.first_pass_path, os.path.join(self.base, "progress", "kg", "kg", "ring.first-pass.json"))
        self.assertIsNone(inputs.worksheet)
        self.assertEqual(inputs.problems, [])
        self.assertTrue(any(n.startswith(f"no worksheet at {expected}") for n in inputs.notes), inputs.notes)
        os.makedirs(os.path.dirname(expected))
        open(expected, "w", encoding="utf-8").write("# Worksheet: anything\n\n## LINT\nEXEMPT style.walk \"w\": ruling\n")
        inputs = self.resolve()
        self.assertEqual(inputs.worksheet, expected)
        self.assertEqual([e["rule"] for e in inputs.exemptions()], ["style.walk"])

    def test_the_spec_names_the_campaign(self):
        inputs = self.resolve(spec=os.path.join(self.base, "campaigns", "other.md"))
        self.assertEqual(inputs.worksheet_path, os.path.join(self.base, "progress", "other", "kg", "ring.worksheet.md"))

    def test_an_explicit_worksheet_is_used_or_is_a_problem(self):
        named = os.path.join(self.base, "elsewhere", "ring.worksheet.md")
        inputs = self.resolve(worksheet=named)
        self.assertIsNone(inputs.worksheet)
        self.assertTrue(any(p.startswith(f"no worksheet at {named}") for p in inputs.problems), inputs.problems)
        os.makedirs(os.path.dirname(named))
        open(named, "w", encoding="utf-8").write("## LINT\n")
        inputs = self.resolve(worksheet=named)
        self.assertEqual((inputs.worksheet, inputs.problems), (named, []))
        self.assertEqual(inputs.first_pass_path, os.path.join(self.base, "elsewhere", "ring.first-pass.json"))

    def test_a_page_outside_docs_has_no_conventional_path(self):
        inputs = self.resolve(page=os.path.join(self.base, "page.md"))
        self.assertIsNone(inputs.worksheet_path)
        self.assertIsNone(inputs.first_pass_path)
        self.assertTrue(any("outside docs/" in n for n in inputs.notes), inputs.notes)


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


class SubsystemEntry(unittest.TestCase):
    MAP = ("# Map\n\n## KG\n\n- tag: `kg`\n- dir: `kg`\n- kernel_paths: `drivers/kg/`, `include/linux/kg.h`\n"
           "- spec: none\n- section6_heading: none\n\n## Other\n\n- dir: `other`\n- kernel_paths: `drivers/other/`\n")

    def test_the_entry_of_the_pages_directory(self):
        base = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(base, "guidelines"))
            open(os.path.join(base, "guidelines", "subsystems.md"), "w", encoding="utf-8").write(self.MAP)
            entry = subsystem_entry(os.path.join(base, "docs", "kg", "ring.md"), base)
            self.assertEqual((entry["name"], entry["dir"], entry["kernel_paths"]), ("KG", "kg", ["drivers/kg/", "include/linux/kg.h"]))
            self.assertEqual(subsystem_entry(os.path.join(base, "docs", "other", "x.md"), base)["kernel_paths"], ["drivers/other/"])
            self.assertIsNone(subsystem_entry(os.path.join(base, "docs", "none", "x.md"), base))
            self.assertIsNone(subsystem_entry(os.path.join(base, "page.md"), base))
        finally:
            shutil.rmtree(base)

    def test_no_map_means_no_entry(self):
        base = tempfile.mkdtemp()
        try:
            self.assertIsNone(subsystem_entry(os.path.join(base, "docs", "kg", "ring.md"), base))
        finally:
            shutil.rmtree(base)


if __name__ == "__main__":
    unittest.main()
