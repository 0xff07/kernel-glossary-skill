"""Exemptions stay attached to one observation and cannot clear execution errors."""
import unittest
import report
from report import Finding, Result
from tests.test_runner import binding


def entry(fragment=None,line=None,id='style.hedges'):
    return {'rule':id,'fragment':fragment,'line':line,'ruling':'recorded reason','text':'EXEMPT '+id}


def result(*findings, **kwargs):
    return Result(binding(lambda p,i: [],'style.hedges'),list(findings),**kwargs)


class Exemptions(unittest.TestCase):
    def test_fragment_and_line_hint(self):
        found=result(Finding(3,'FAIL','It usually settles.'),Finding(4,'review','It usually fails.'))
        errors=report.apply_exemptions([found],[entry('usually',4)],['# T','','It usually settles.','It usually fails.'])
        self.assertEqual(errors,[])
        self.assertEqual([f.severity for f in found.findings],['FAIL','note'])
        self.assertEqual(found.findings[1].data['exempted'],'review')

    def test_line_shift_and_link_text(self):
        found=result(Finding(4,'review','candidate'))
        errors=report.apply_exemptions([found],[entry('usually settles.',3)],['# T','','','It [usually](https://example.org) settles.'])
        self.assertEqual(errors,[])
        self.assertEqual(found.findings[0].severity,'note')

    def test_stale_and_ambiguous_exempt_nothing(self):
        for fragment,expected in [('absent','stale'),('usually','ambiguous')]:
            found=result(Finding(1,'FAIL','usually settles'),Finding(2,'review','usually fails'))
            errors=report.apply_exemptions([found],[entry(fragment)],['usually settles','usually fails'])
            self.assertTrue(errors[0][1].startswith(expected))
            self.assertEqual([f.severity for f in found.findings],['FAIL','review'])

    def test_legacy_parts_and_line_only_need_readjudication(self):
        for exemption,expected in [(entry('usually',id='style.hedges/old-part'),'re-adjudication'),(entry(line=1),'fragment')]:
            found=result(Finding(1,'FAIL','usually'))
            errors=report.apply_exemptions([found],[exemption],['usually'])
            self.assertIn(expected,errors[0][1])
            self.assertEqual(found.findings[0].severity,'FAIL')

    def test_errors_and_missing_inputs_cannot_be_exempted(self):
        found=result(Finding(1,'FAIL','usually'),skipped='no tree',error='boom')
        self.assertEqual(report.apply_exemptions([found],[entry('usually')],['usually']),[])
        self.assertEqual((found.skipped,found.error),('no tree','boom'))
        self.assertEqual(found.state(),'ERROR')

    def test_an_earlier_exemption_cannot_disambiguate_a_broad_fragment(self):
        found = result(Finding(1, 'review', 'usually settles'),
                       Finding(2, 'review', 'usually fails'))
        errors = report.apply_exemptions(
            [found], [entry('usually settles'), entry('usually')],
            ['usually settles', 'usually fails'])
        self.assertEqual(len(errors), 1)
        self.assertIn('ambiguous', errors[0][1])
        self.assertEqual([f.severity for f in found.findings], ['note', 'review'])
