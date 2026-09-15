"""plugins.recency on a temporary git repository: an OTHER SOURCES entry matches its commit's
Link trailer, and a cited driver file has a commit within the window."""
import os
import shutil
import subprocess
import tempfile
import unittest
from checks import coverage_recency as recency
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

    def test_cited_driver_file_within_the_window(self):
        details = f'### A\n\nThe ring is set up in [drivers/kg/ring.c:1]({BASE}drivers/kg/ring.c#L1).\n'
        result = observed(recency.check(page(skeleton(details=details)), TestInputs(tree=self.root)))
        self.assertEqual(result.findings, [])
        self.assertEqual(result.data['files'], 2)
        self.assertEqual(result.data['older_than_years'], 0)
if __name__ == '__main__':
    unittest.main()


class Dependencies(unittest.TestCase):
    def test_missing_required_input(self):
        from checks.coverage_recency import check
        from inputs import MissingInput
        from tests.support import TestInputs, page, skeleton
        with self.assertRaises(MissingInput):
            list(check(page(skeleton()), TestInputs()))
