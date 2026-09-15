"""plugins.recency on a temporary git repository: an OTHER SOURCES entry matches its commit's
Link trailer, and a cited driver file has a commit within the window."""
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

    def sources(self, entry):
        return skeleton().replace('## OTHER SOURCES\n\n', f'## OTHER SOURCES\n\n{entry}\n\n')

    def trailers(self, entry):
        return observed(recency.check(page(self.sources(entry)), TestInputs(tree=self.root)))

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

    def test_entry_out_of_form_and_bare_url(self):
        result = self.trailers(f'- [the ring]({LINK})\n- {LINK}')
        messages = ' '.join((f.message for f in result.findings))
        self.assertIn('not in the `[<subject> (commit <sha>)](<url>)` form', messages)
        self.assertIn('bare URL entry', messages)
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.sections_other_sources import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            text = skeleton().replace('## OTHER SOURCES\n',
                f'## OTHER SOURCES\n- [ring (commit 0123456789ab)]({LINK})\n')
            list(check(page(text), TestInputs()))

    def test_page_only_findings_precede_missing_git(self):
        import kg
        from tests.test_runner import binding
        text = skeleton().replace('## OTHER SOURCES\n',
            f'## OTHER SOURCES\n- {LINK}\n- [ring (commit 0123456789ab)]({LINK})\n')
        result, = kg.run_rules(page(text), TestInputs(), [binding(recency.check, recency.RULE)])
        self.assertIsNotNone(result.skipped)
        self.assertTrue(any(f.severity == 'FAIL' and 'bare URL' in f.message for f in result.findings))

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
            f'## OTHER SOURCES\n- {LINK}\n- [ring (commit 0123456789ab)]({LINK})\n')
        inputs = TestInputs(tree='/tree')
        failed = SimpleNamespace(returncode=128, stdout='', stderr='cannot read object')
        with patch('inputs.subprocess.run', return_value=failed):
            result, = kg.run_rules(page(text), inputs, [binding(recency.check, recency.RULE)])
        self.assertIn('cannot read object', result.error)
        self.assertTrue(any('bare URL' in f.message for f in result.findings))
        self.assertFalse(any('no such commit' in f.message for f in result.findings))
        self.assertEqual(exit_status([result], inputs), 1)
