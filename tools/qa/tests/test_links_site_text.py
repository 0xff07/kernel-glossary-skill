"""kind: rule — a location link's text names its file by base name; the path from the tree root only where two cited files share a base name; links inside fences are not read."""
import unittest
from checks import links_site_text as rule
from tests.support import page, skeleton, observed
RING = 'https://elixir.bootlin.com/linux/v0.1/source/drivers/kg/ring.c'
OTHER = 'https://elixir.bootlin.com/linux/v0.1/source/arch/kg/ring.c'

def run(details):
    return observed(rule.check(page(skeleton(details=f'### A\n\n{details}\n')), None))

class SiteText(unittest.TestCase):
    def test_a_base_name_site_passes(self):
        found = run(f'The push at [`ring.c:3`]({RING}#L3) advances the head.')
        self.assertEqual(found.findings, [])
        self.assertEqual(found.footer, 'location-links=1 with-directory=0 bare-clashes=0 clashing-base-names=0')

    def test_a_site_text_with_its_directory_is_listed(self):
        found = run(f'The push at [`drivers/kg/ring.c:3-5`]({RING}#L3) advances the head.')
        self.assertEqual(found.findings, [])
        self.assertEqual(len(found.rows), 1)
        self.assertIn('write ring.c:3-5', found.rows[0].text)
        self.assertEqual([f.severity for f in found.all if f.line == found.rows[0].line], ['review'])
        self.assertEqual(found.footer, 'location-links=1 with-directory=1 bare-clashes=0 clashing-base-names=0')

    def test_two_files_sharing_a_base_name_keep_their_paths(self):
        found = run(f'The push at [`drivers/kg/ring.c:3`]({RING}#L3) mirrors [`arch/kg/ring.c:9`]({OTHER}#L9).')
        self.assertEqual(found.rows, [])
        self.assertEqual(found.footer, 'location-links=2 with-directory=0 bare-clashes=0 clashing-base-names=1')
        found = run(f'The push at [`ring.c:3`]({RING}#L3) mirrors [`arch/kg/ring.c:9`]({OTHER}#L9).')
        self.assertEqual(len(found.rows), 1)
        self.assertIn('two cited files share this base name', found.rows[0].text)
        self.assertEqual(found.footer, 'location-links=2 with-directory=0 bare-clashes=1 clashing-base-names=1')

    def test_a_link_inside_a_fence_is_not_read(self):
        found = run(f'```\n    see [`drivers/kg/ring.c:3`]({RING}#L3)\n```\n\nThe push advances the head.')
        self.assertEqual(found.rows, [])
        self.assertEqual(found.footer, 'location-links=0 with-directory=0 bare-clashes=0 clashing-base-names=0')

if __name__ == '__main__':
    unittest.main()
