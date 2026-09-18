"""Shared parsing and reporting utilities."""
import re
from pagemodel import TABLE_SEPARATOR
PARITY_SECTION = '## PARITY'
SCOPE_HEADER = re.compile('^\\|.*\\banchors?\\b.*\\|.*\\|', re.I)
ROW_SPAN = re.compile('`([^`]+)`')
ROW_DECORATION = re.compile('^(?:\\\\<)?(?:struct |enum |union )?|\\\\>$|\\(\\)$|\\[[^\\]]*\\]$')
DIGEST_LINE = re.compile('page sha256:\\s*([0-9a-f]{64})', re.I)
EVIDENCE_SECTION = '## EVIDENCE'
BASES_HEADER = re.compile(r'^\|.*\bline\b.*\bbasis\b.*\|', re.I)

def tables_of(lines):
    tables, current = ([], [])
    for line in lines:
        if line.startswith('|'):
            if not TABLE_SEPARATOR.match(line):
                current.append(line)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables

def row_symbols(cells):
    for cell in cells:
        spans = ROW_SPAN.findall(cell)
        if spans:
            return {ROW_DECORATION.sub('', word).strip('*&') for span in spans for word in span.split()}
    return set()

def bases_rows(inputs):
    """The rows of the EVIDENCE Bases table: {line, claim, bases, result}, or [] when the dossier
    holds none."""
    body = inputs.dossier_section(EVIDENCE_SECTION) if inputs is not None and inputs.dossier_lines else ''
    rows = []
    for table in tables_of(body.split('\n')):
        if not BASES_HEADER.match(table[0]):
            continue
        for line in table[1:]:
            cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
            if len(cells) < 2 or not cells[0].isdigit():
                continue
            rows.append({'line': int(cells[0]), 'claim': cells[1], 'bases': cells[2:4], 'result': cells[4] if len(cells) > 4 else ''})
        break
    return rows


def parity_tables(inputs):
    body = inputs.dossier_section(PARITY_SECTION)
    if not body and PARITY_SECTION not in (inputs.dossier_lines or []):
        return (None, [], [])
    tables = tables_of(body.split('\n'))
    scope = [t for t in tables if SCOPE_HEADER.match(t[0])]
    catalog = [t for t in tables if not SCOPE_HEADER.match(t[0])]
    return (tables, scope, catalog)
