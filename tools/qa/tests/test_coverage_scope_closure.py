"""plugins.coverage: the catalog row read from a campaign spec, its anchor spans resolved against
a temporary tree, and the ones the page never names."""
import os
import shutil
import subprocess
import tempfile
import unittest
from inputs import Inputs
from checks import coverage_scope_closure as coverage
from tests.support import URL, skeleton, TestInputs, observed
from pagemodel import Page
SPEC = '# Campaign\n\n## Page catalog\n\n### router/\n\n| page | scope (anchor symbols) | tag |\n|---|---|---|\n| ring.md | the ring: `struct kg_ring` [errata 2026-01-01: `stale_name` renamed], `kg_ring_push`, `_pop` | usb4 |\n'

def git(root, *arguments):
    return subprocess.run(['git', '-C', root, '-c', 'user.name=kg', '-c', 'user.email=kg@example.org', *arguments], capture_output=True, text=True, check=True).stdout.strip()

class CatalogRow(unittest.TestCase):

    def setUp(self):
        self.spec = tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8')
        self.spec.write(SPEC)
        self.spec.close()

    def tearDown(self):
        os.unlink(self.spec.name)

    def test_row_found_under_its_directory_heading(self):
        scope = coverage.catalog_row(self.spec.name, 'router/ring.md')
        self.assertIn('`struct kg_ring`', scope)
        self.assertIsNone(coverage.catalog_row(self.spec.name, 'other/ring.md'))

    def test_spans_and_expansions(self):
        scope = coverage.catalog_row(self.spec.name, 'router/ring.md')
        self.assertEqual(coverage.spans_of(scope), ['kg_ring', 'kg_ring_push', '_pop'])
        self.assertEqual(coverage.expansions('_pop', 'kg_ring_push'), ['kg_ring_push_pop', 'kg_ring_pop', 'kg_pop'])
        self.assertEqual(coverage.expansions('_x_', 'a_b_c'), ['a_x_b_c', 'a_b_x_c'])

@unittest.skipUnless(shutil.which('git'), 'git is not installed')
class Run(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        open(os.path.join(self.root, 'drivers', 'kg', 'ring.h'), 'w', encoding='utf-8').write('struct kg_ring {\n};\nint kg_ring_push(void);\nint kg_ring_pop(void);\n')
        git(self.root, 'init', '-q')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-q', '-m', 'kg: add the ring')
        self.base = tempfile.mkdtemp()
        self.spec = os.path.join(self.base, 'campaigns', 'kg.md')
        os.makedirs(os.path.dirname(self.spec))
        open(self.spec, 'w', encoding='utf-8').write(SPEC)
        self.page_path = os.path.join(self.base, 'docs', 'kg', 'router', 'ring.md')
        os.makedirs(os.path.dirname(self.page_path))

    def tearDown(self):
        shutil.rmtree(self.root)
        shutil.rmtree(self.base)

    def run_on(self, details):
        open(self.page_path, 'w', encoding='utf-8').write(skeleton(details=details))
        inputs = TestInputs(tree=self.root)
        inputs.spec, inputs.page_path, inputs.base, inputs.tree = (self.spec, self.page_path, self.base, self.root)
        inputs.worksheet_lines = None
        return observed(coverage.check(Page(self.page_path), inputs))

    def test_an_anchor_the_page_never_names(self):
        result = self.run_on(f'### A\n\n[`struct kg_ring`]({URL}) is pushed by `kg_ring_push`.\n')
        self.assertEqual(result.data['counts'], {'named': 2, 'absent': 1, 'accounted': 0})
        self.assertEqual([f.severity for f in result.findings], ['review'])
        self.assertIn('`kg_ring_pop` is never named', result.findings[0].message)

    def test_every_anchor_named(self):
        result = self.run_on(f'### A\n\n[`struct kg_ring`]({URL}) is pushed by `kg_ring_push` and popped by `kg_ring_pop`.\n')
        self.assertEqual(result.findings, [])
        self.assertEqual(result.data['symbols'], ['kg_ring', 'kg_ring_push', 'kg_ring_pop'])
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from inputs import MissingInput
        from tests.support import page
        with tempfile.NamedTemporaryFile('w', suffix='.md') as spec:
            spec.write(SPEC)
            spec.flush()
            inputs = TestInputs(tree='/unversioned/tree', git=False, spec=spec.name,
                                base='/kg', page_path='/kg/docs/kg/router/ring.md')
            with self.assertRaisesRegex(MissingInput, 'no git'):
                list(coverage.check(page(skeleton()), inputs))

    def test_absent_spec_is_optional_even_without_a_tree(self):
        from tests.support import page
        found = list(coverage.check(page(skeleton()), TestInputs()))
        self.assertTrue(any(f.data and f.data.get('optional') for f in found))

    def test_git_no_match_is_distinct_from_a_failed_search(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        outcomes = [SimpleNamespace(returncode=1, stdout='', stderr=''),
                    SimpleNamespace(returncode=128, stdout='', stderr='cannot read object')]
        with patch('inputs.subprocess.run', side_effect=outcomes):
            self.assertFalse(coverage.TreeOracle('/tree', ['.'], {'absent'})('absent'))
            with self.assertRaises(OSError):
                coverage.TreeOracle('/tree', ['.'], {'unknown'})
