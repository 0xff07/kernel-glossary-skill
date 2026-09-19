"""Checks for [completeness.scope-table]."""
from report import Finding
from report import observations
from worksheet_utils import completeness_tables
RULE = 'completeness.scope-table'

def scope_table(page, inputs):
    tables, scope, _catalog = completeness_tables(inputs)
    if tables is None:
        yield from observations([Finding(None, 'review', 'no COMPLETENESS section in the worksheet')], 'scope-table=absent', [], {})
        return
    findings = []
    if not scope:
        findings.append(Finding(None, 'review', 'no scope-closure table above the catalog table in COMPLETENESS (every anchor the catalog row names, with its location or its reduction)'))
    yield from observations(findings, f"scope-table={('present' if scope else 'absent')}", [], {'scope_table': bool(scope)})

def check(page, inputs):
    inputs.require('worksheet')
    yield from scope_table(page, inputs)
