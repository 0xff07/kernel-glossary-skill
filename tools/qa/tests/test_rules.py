"""Discovery and extension require only a guideline, a check and its test."""
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rules
import selftest
from inputs import skill_dir


class Discovery(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        (self.base/'guidelines').mkdir()
        (self.base/'tools/qa/checks').mkdir(parents=True)
        self.doc=self.base/'guidelines/test.md'
        self.doc.write_text('## Testing [test]\n\n1. [test.example, qa] A test.\n')
        self.module=self.base/'tools/qa/checks/test_example.py'
        self.module.write_text("from report import Finding\nRULE = 'test.example'\ndef check(page, inputs):\n    yield Finding(1, 'review', 'new rule')\n")

    def errors(self):
        return rules.load(self.base)[3]

    def test_discovery_and_deterministic_order(self):
        self.assertEqual(self.errors(),[])
        self.doc.write_text(self.doc.read_text()+'2. [test.another, qa] Another test.\n')
        (self.module.parent/'test_another.py').write_text("RULE='test.another'\ndef check(page, inputs):\n    return []\n")
        found,_,_,errors=rules.load(self.base)
        self.assertEqual(errors,[])
        self.assertEqual([r.id for r in found],['test.example','test.another'])

    def test_missing_module_and_missing_marker(self):
        self.module.unlink()
        self.assertTrue(any('no usable check' in e for e in self.errors()))
        self.module.write_text("RULE='test.example'\ndef check(page, inputs): return []\n")
        self.doc.write_text('## Testing [test]\n1. [test.example] Manual.\n')
        self.assertTrue(any('marked qa' in e for e in self.errors()))

    def test_duplicate_ids_and_filename_collision(self):
        self.doc.write_text(self.doc.read_text()+'2. [test.example, qa] Duplicate.\n')
        self.assertTrue(any('duplicate guideline' in e for e in self.errors()))
        self.doc.write_text('## Testing [test]\n1. [test.foo-bar] A.\n2. [test.foo_bar] B.\n')
        # Underscores are invalid IDs; distinct valid IDs can collide across a section dash.
        self.doc.write_text('## Testing [test-a]\n1. [test-a.b, qa] A.\n## Testing [test]\n2. [test.a-b, qa] B.\n')
        self.assertTrue(any('filename collision' in e for e in self.errors()))

    def test_broken_modules_are_visible(self):
        for text,expected in [("raise ImportError('broken')",'ImportError'),
                              ("RULE='test.example'\ncheck=3",'callable'),
                              ("RULE='bad'",'valid guideline ID'),
                              ("RULE='test.other'\ndef check(p,i): return []",'filename'),
                              ("raise SystemExit(0)",'SystemExit')]:
            self.module.write_text(text)
            self.assertTrue(any(expected in e for e in self.errors()),text)

    def test_duplicate_modules_are_rejected(self):
        (self.module.parent/'z_duplicate.py').write_text(self.module.read_text())
        self.assertTrue(any('duplicate implementation' in e for e in self.errors()))

    def test_fenced_markers_do_not_register_and_old_markers_fail(self):
        self.doc.write_text(self.doc.read_text()+'```markdown\n2. [test.ignored, qa] Example.\n```\n')
        self.assertEqual(self.errors(),[])
        self.doc.write_text(self.doc.read_text().replace('test.example, qa','test.example, checked'))
        self.assertTrue(any('unsupported marker' in e for e in self.errors()))

    def test_reload_does_not_reuse_stale_bytecode(self):
        self.assertEqual(self.errors(),[])
        self.module.write_text(self.module.read_text().replace('new rule','new text'))
        found,_,_,errors=rules.load(self.base)
        self.assertEqual(errors,[])
        self.assertEqual(list(found[0].check(None,None))[0].message,'new text')

    def test_malformed_qa_marker_is_not_silently_ignored(self):
        for marker in ('1. [test.bad_id, qa] Invalid.',
                       '| Example | test.bad_id, qa |'):
            self.doc.write_text('## Testing [test]\n' + marker + '\n')
            self.assertTrue(any('malformed qa' in e for e in self.errors()))

    def test_check_can_use_an_ordinary_dataclass_helper(self):
        self.module.write_text(
            'from __future__ import annotations\n'
            'from dataclasses import dataclass\nfrom report import Finding\n'
            'RULE = "test.example"\n'
            '@dataclass\nclass Candidate:\n    text: str\n'
            'def check(page, inputs):\n'
            '    yield Finding(1, "review", Candidate("candidate").text)\n')
        found, _, _, errors = rules.load(self.base)
        self.assertEqual(errors, [])
        self.assertEqual(list(found[0].check(None, None))[0].message, 'candidate')


class Contribution(unittest.TestCase):
    def test_three_file_addition_appears_in_every_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            # Exclude this shared engine test from the fixture so a full selftest
            # does not recursively copy and execute its own contribution test.
            shutil.copytree(Path(skill_dir())/'tools/qa',base/'tools/qa',
                            ignore=shutil.ignore_patterns('__pycache__', 'test_rules.py'))
            shutil.copytree(Path(skill_dir())/'guidelines',base/'guidelines')
            shutil.copytree(Path(skill_dir())/'references/figures',base/'references/figures')
            # These are the only three files changed to add this check.
            (base/'guidelines/extra.md').write_text('## Extra [extra]\n1. [extra.example, qa] Example.\n')
            (base/'tools/qa/checks/extra_example.py').write_text("from report import Finding\nRULE='extra.example'\ndef check(page, inputs):\n    yield Finding(1,'review','newly discovered')\n")
            (base/'tools/qa/tests/test_extra_example.py').write_text("import unittest\nfrom checks.extra_example import check\nfrom tests.support import page\nclass TestExample(unittest.TestCase):\n    def test_observation(self):\n        self.assertEqual(list(check(page('# T'),None))[0].message, 'newly discovered')\n")
            page_file=base/'page.md';page_file.write_text('# T\n')
            def run(*args):
                return subprocess.run([sys.executable,str(base/'tools/qa/kg.py'),*args],capture_output=True,text=True)
            for args,expected in [(('rules',),'extra.example'),(('where','extra.example'),'test_extra_example.py'),
                                  (('check',str(page_file),'--only','extra.example'),'newly discovered'),
                                  (('selftest','--rule','extra.example'),'Ran 1 test'),
                                  (('selftest',),'Reference figures: 34 checked, 0 problems')]:
                result=run(*args)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn(expected,result.stdout)
            for content in ('# no tests\n', "raise ImportError('broken test')\n", 'raise SystemExit(0)\n'):
                (base/'tools/qa/tests/test_extra_example.py').write_text(content)
                result=run('selftest','--rule','extra.example')
                self.assertNotEqual(result.returncode,0,result.stdout)
            (base/'tools/qa/tests/test_extra_example.py').unlink()
            self.assertNotEqual(run('selftest','--rule','extra.example').returncode,0)
            self.assertNotEqual(run('selftest','--rule','missing.rule').returncode,0)
