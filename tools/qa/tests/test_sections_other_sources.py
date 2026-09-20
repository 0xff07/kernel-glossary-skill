"""plugins.recency on a temporary git repository: a commit entry of OTHER SOURCES matches its commit's
Link trailer, the reader's entries are listed and left alone, and a cited driver file has a commit within the window."""
import os
import shutil
import subprocess
import tempfile
import unittest
from checks import sections_other_sources as recency
from tests.support import page, skeleton, TestInputs, observed
LINK = 'https://lore.kernel.org/r/kg-ring@example.org'
BASE = 'https://elixir.bootlin.com/linux/v0.1/source/'

def git(root, *arguments):
    return subprocess.run(['git', '-C', root, '-c', 'user.name=kg', '-c', 'user.email=kg@example.org', *arguments], capture_output=True, text=True, check=True).stdout.strip()

@unittest.skipUnless(shutil.which('git'), 'git is not installed')
class Recency(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        git(self.root, 'init', '-q')
        os.makedirs(os.path.join(self.root, 'drivers', 'kg'))
        for name in ('ring.c', 'ring.h'):
            open(os.path.join(self.root, 'drivers', 'kg', name), 'w', encoding='utf-8').write('int ring;\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-q', '-m', f'kg: add the ring\n\nLink: {LINK}')
        self.sha = git(self.root, 'rev-parse', 'HEAD')

    def tearDown(self):
        shutil.rmtree(self.root)

    def sources(self, entry, block=True):
        body = f'### Added by kg\n\n{entry}' if block else entry
        return skeleton().replace('## OTHER SOURCES\n\n', f'## OTHER SOURCES\n\n{body}\n\n')

    def trailers(self, entry, block=True, baseline=None):
        return observed(recency.check(page(self.sources(entry, block)), TestInputs(tree=self.root, baseline=baseline)))

    def test_entry_matching_its_trailer(self):
        result = self.trailers(f'- [kg: add the ring (commit {self.sha[:12]})]({LINK})')
        self.assertEqual(result.findings, [])
        self.assertEqual(result.data['matched'], 1)

    def test_entry_with_another_url(self):
        result = self.trailers(f'- [kg: add the ring (commit {self.sha[:12]})](https://lore.kernel.org/r/other@example.org)')
        self.assertIn("not one of the commit's Link trailers", result.findings[0].message)

    def test_entry_naming_no_commit_of_the_tree(self):
        result = self.trailers(f'- [kg: add the ring (commit 0123456789ab)]({LINK})')
        self.assertIn('no such commit in the tree', result.findings[0].message)

    def test_the_readers_lines_outside_a_block_are_listed_and_left_alone(self):
        result = self.trailers(f'- [the ring, a talk]({LINK})\n- {LINK} a thread a reader found\n- [kg: add the ring (commit 0123456789ab)](https://example.org/unrelated)', block=False)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.data['reader_lines'], 3)
        self.assertEqual(result.data['commit_entries'], 0)

    def test_a_non_commit_bullet_inside_the_models_block_fails(self):
        result = self.trailers('- a note with no link at all')
        self.assertEqual([f.severity for f in result.findings], ['FAIL'])
        self.assertIn('is not a commit entry', result.findings[0].message)

    def test_a_readers_line_of_the_committed_page_must_survive(self):
        old = self.sources(f'- [kg: add the ring (commit {self.sha[:12]})]({LINK})').replace('## OTHER SOURCES\n\n', '## OTHER SOURCES\n\n- a talk a reader found\n\n')
        kept = old
        result = observed(recency.check(page(kept), TestInputs(tree=self.root, baseline=old)))
        self.assertEqual(result.findings, [])
        self.assertEqual(result.data['kept'], 1)
        dropped = self.sources(f'- [kg: add the ring (commit {self.sha[:12]})]({LINK})')
        result = observed(recency.check(page(dropped), TestInputs(tree=self.root, baseline=old)))
        self.assertEqual([f.severity for f in result.findings], ['FAIL'])
        self.assertIn("reader's shelf in the committed page is gone", result.findings[0].message)

    def test_an_unmigrated_committed_page_binds_nothing(self):
        old = skeleton().replace('## OTHER SOURCES\n\n', f'## OTHER SOURCES\n\n- [kg: add the ring (commit {self.sha[:12]})]({LINK})\n\n')
        result = observed(recency.check(page(self.sources(f'- [kg: add the ring (commit {self.sha[:12]})]({LINK})')), TestInputs(tree=self.root, baseline=old)))
        self.assertEqual(result.findings, [])
        self.assertEqual(result.data['lost'], 0)
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.sections_other_sources import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            text = skeleton().replace('## OTHER SOURCES\n',
                f'## OTHER SOURCES\n### Added by kg\n- [ring (commit 0123456789ab)]({LINK})\n')
            list(check(page(text), TestInputs()))

    def test_page_only_findings_precede_missing_git(self):
        import kg
        from tests.test_runner import binding
        text = skeleton().replace('## OTHER SOURCES\n',
            f'## OTHER SOURCES\n### Added by kg\n- a note with no link at all\n- [ring (commit 0123456789ab)]({LINK})\n')
        result, = kg.run_rules(page(text), TestInputs(), [binding(recency.check, recency.RULE)])
        self.assertIsNotNone(result.skipped)
        self.assertTrue(any(f.severity == 'FAIL' and 'is not a commit entry' in f.message for f in result.findings))

    def test_no_commit_entries_need_no_git(self):
        import kg
        from tests.test_runner import binding
        text = skeleton().replace('## OTHER SOURCES\n', '## OTHER SOURCES\nNone applies.\n')
        result, = kg.run_rules(page(text), TestInputs(), [binding(recency.check, recency.RULE)])
        self.assertIsNone(result.skipped)
        self.assertIsNone(result.error)

    def test_git_failure_is_an_execution_error_with_prior_findings_retained(self):
        import kg
        from types import SimpleNamespace
        from unittest.mock import patch
        from report import exit_status
        from tests.test_runner import binding
        text = skeleton().replace('## OTHER SOURCES\n',
            f'## OTHER SOURCES\n### Added by kg\n- a note with no link at all\n- [ring (commit 0123456789ab)]({LINK})\n')
        inputs = TestInputs(tree='/tree')
        failed = SimpleNamespace(returncode=128, stdout='', stderr='cannot read object')
        with patch('inputs.subprocess.run', return_value=failed):
            result, = kg.run_rules(page(text), inputs, [binding(recency.check, recency.RULE)])
        self.assertIn('cannot read object', result.error)
        self.assertTrue(any('is not a commit entry' in f.message for f in result.findings))
        self.assertFalse(any('no such commit' in f.message for f in result.findings))
        self.assertEqual(exit_status([result], inputs), 1)
