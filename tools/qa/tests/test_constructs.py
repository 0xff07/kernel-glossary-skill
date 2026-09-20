"""kind: helper — the subsystem's sources: a directory with everything under it, a glob, a single
file, test files left out; and the structs those sources define."""
import os
import shutil
import tempfile
import unittest
from constructs import defined_structs, sources_within


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)


class SourcesWithin(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        write(self.root, 'drivers/kg/a.c', 'int a;\n')
        write(self.root, 'drivers/kg/sub/b.h', 'struct kg_b {\n\tint x;\n};\n')
        write(self.root, 'drivers/kg/a_test.c', 'int t;\n')
        write(self.root, 'drivers/kg/README', 'text\n')
        write(self.root, 'drivers/usb/host/xhci-ring.c', 'int r;\n')
        write(self.root, 'drivers/usb/host/other.c', 'int o;\n')
        write(self.root, 'include/linux/kg.h', 'struct kg_ring {\n\tint head;\n};\n')
        write(self.root, 'include/linux/kg_other.h', 'struct kg_other {\n\tint y;\n};\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_a_directory_a_glob_and_a_file(self):
        found = sources_within(self.root, ['drivers/kg/', 'drivers/usb/host/xhci*', 'include/linux/kg.h'], {})
        self.assertEqual(sorted(found), ['drivers/kg/a.c', 'drivers/kg/sub/b.h', 'drivers/usb/host/xhci-ring.c', 'include/linux/kg.h'])
        self.assertEqual(found['include/linux/kg.h'][0], 'struct kg_ring {')
        self.assertEqual(defined_structs(found), {'kg_b', 'kg_ring'})

    def test_a_missing_path_is_skipped(self):
        self.assertEqual(sources_within(self.root, ['drivers/none/', 'include/linux/none.h', ''], {}), {})


if __name__ == '__main__':
    unittest.main()

class MembersBehindAnOpenComment(unittest.TestCase):
    def test_a_member_whose_line_ends_in_an_opening_comment_is_seen(self):
        from constructs import members_of
        source = ["struct kg_hdr {", "\tu32 delay:8; /*", "\t\t * a comment that runs on", "\t\t */", "\tu32 cmuv:8; // trailing", "};"]
        self.assertEqual(members_of(source, 'kg_hdr'), ['delay', 'cmuv'])
