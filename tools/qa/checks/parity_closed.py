"""Checks for [parity.closed]."""
from report import Finding
from report import observations
from dossier_utils import parity_tables
from dossier_utils import row_symbols
from pagemodel import split_cells
RULE = 'parity.closed'
PAIRED_ROW = '` / `'
MIN_PARITY_CELLS = 3
PARITY_CLIP = 80
REPORTED_MISSING = 8

def parity(page, inputs):
    tables, _scope, catalog = parity_tables(inputs)
    if tables is None:
        yield from observations([Finding(None, 'review', 'no PARITY section in the dossier')], 'parity: absent', [], {})
        return
    findings = []
    rows = empty = 0
    present = set()
    for table in catalog:
        for line in table[1:]:
            cells = split_cells(line)
            if len(cells) < MIN_PARITY_CELLS:
                continue
            rows += cells[0].count(PAIRED_ROW) + 1
            present |= row_symbols(cells)
            if any((not cell for cell in cells)):
                empty += 1
                findings.append(Finding(None, 'FAIL', f'PARITY row with an empty cell: {line[:PARITY_CLIP]}'))
    keys = page.catalog_keys
    if keys and rows < len(keys):
        findings.append(Finding(None, 'review', f'PARITY has {rows} catalog row(s) for {len(keys)} catalog symbols; a symbol is missing its row or was de-cataloged'))
    missing = [name for name in page.catalog_names if name not in present] if catalog else []
    if missing:
        named = ', '.join((f'`{n}`' for n in missing[:REPORTED_MISSING])) + (f', and {len(missing) - REPORTED_MISSING} more' if len(missing) > REPORTED_MISSING else '')
        findings.append(Finding(None, 'review', f'{len(missing)} catalog symbol(s) with no PARITY row naming them (matched by name): {named}'))
    footer = f'catalog symbols={len(keys)} parity rows={rows} empty-cells={empty} missing-rows={len(missing)}'
    yield from observations(findings, footer, [], {'catalog_symbols': len(keys), 'parity_rows': rows, 'parity_empty': empty, 'missing_rows': missing})

def check(page, inputs):
    inputs.require('dossier')
    yield from parity(page, inputs)
