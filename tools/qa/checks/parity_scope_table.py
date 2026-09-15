"""Checks for [parity.scope-table]."""
from report import Finding
from report import observations
from dossier_utils import parity_tables
RULE = 'parity.scope-table'

def scope_table(page, inputs):
    tables, scope, _catalog = parity_tables(inputs)
    if tables is None:
        yield from observations([Finding(None, 'review', 'no PARITY section in the dossier')], 'scope-table=absent', [], {})
        return
    findings = []
    if not scope:
        findings.append(Finding(None, 'review', 'no scope-closure table above the catalog table in PARITY (every anchor the catalog row names, with its location or its reduction)'))
    yield from observations(findings, f"scope-table={('present' if scope else 'absent')}", [], {'scope_table': bool(scope)})

def check(page, inputs):
    inputs.require('dossier')
    yield from scope_table(page, inputs)
