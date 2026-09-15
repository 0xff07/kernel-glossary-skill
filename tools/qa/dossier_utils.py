"""Shared parsing and reporting utilities."""
import re
from pagemodel import TABLE_SEPARATOR
PARITY_SECTION = '## PARITY'
SCOPE_HEADER = re.compile('^\\|.*\\banchors?\\b.*\\|.*\\|', re.I)
ROW_SPAN = re.compile('`([^`]+)`')
ROW_DECORATION = re.compile('^(?:\\\\<)?(?:struct |enum |union )?|\\\\>$|\\(\\)$|\\[[^\\]]*\\]$')
DIGEST_LINE = re.compile('page sha256:\\s*([0-9a-f]{64})', re.I)

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

def parity_tables(inputs):
    body = inputs.dossier_section(PARITY_SECTION)
    if not body and PARITY_SECTION not in (inputs.dossier_lines or []):
        return (None, [], [])
    tables = tables_of(body.split('\n'))
    scope = [t for t in tables if SCOPE_HEADER.match(t[0])]
    catalog = [t for t in tables if not SCOPE_HEADER.match(t[0])]
    return (tables, scope, catalog)
