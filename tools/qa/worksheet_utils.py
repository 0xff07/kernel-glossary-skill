"""Shared parsing and reporting utilities."""
import re
from pagemodel import TABLE_SEPARATOR
COMPLETENESS_SECTION = '## COMPLETENESS'
SCOPE_HEADER = re.compile('^\\|.*\\banchors?\\b.*\\|.*\\|', re.I)
ROW_SPAN = re.compile('`([^`]+)`')
ROW_DECORATION = re.compile('^(?:\\\\<)?(?:struct |enum |union )?|\\\\>$|\\(\\)$|\\[[^\\]]*\\]$')
DIGEST_LINE = re.compile('page sha256:\\s*([0-9a-f]{64})', re.I)
EVIDENCE_SECTION = '## EVIDENCE'
BASES_HEADER = re.compile(r'^\|.*\bline\b.*\bbasis\b.*\|', re.I)
# a recorded block map: a table row `| <line> <title> | <map> | ... |` or the engine's own line
MAP_ROW = re.compile(r'^\|\s*(\d+)\s+(.*?)\s*\|\s*([A-Z](?: [A-Z])*)\s*\|')
MAP_LINE = re.compile(r'^\s*(\d+)\s+\[(.*?)\]\s+map=([A-Z](?: [A-Z])*)\b')

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
    """The rows of the EVIDENCE Bases table: {line, claim, bases, result}, or [] when the worksheet
    holds none."""
    body = inputs.worksheet_section(EVIDENCE_SECTION) if inputs is not None and inputs.worksheet_lines else ''
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


def recorded_maps(inputs):
    """The block maps the EVIDENCE section records: [{line, title, map}], the title as written,
    which may be a prefix of the page's."""
    body = inputs.worksheet_section(EVIDENCE_SECTION) if inputs is not None and inputs.worksheet_lines else ''
    out = []
    for line in body.split('\n'):
        found = MAP_ROW.match(line) or MAP_LINE.match(line)
        if found:
            out.append({'line': int(found.group(1)), 'title': found.group(2).strip(), 'map': found.group(3)})
    return out


def completeness_tables(inputs):
    body = inputs.worksheet_section(COMPLETENESS_SECTION)
    if not body and COMPLETENESS_SECTION not in (inputs.worksheet_lines or []):
        return (None, [], [])
    tables = tables_of(body.split('\n'))
    scope = [t for t in tables if SCOPE_HEADER.match(t[0])]
    catalog = [t for t in tables if not SCOPE_HEADER.match(t[0])]
    return (tables, scope, catalog)


LIFECYCLE_HEADER = re.compile(r'^\|.*\bobject\b.*\bfield\b.*\bwriter\b.*\|', re.I)
STRUCT_NAME = re.compile(r'struct\s+([A-Za-z_]\w*)')


def lifecycle_rows(inputs):
    """The rows of the EVIDENCE Lifecycle table: {object, field, mark, writer, site, event, value},
    the object as `struct name`, or [] when the worksheet holds none."""
    body = inputs.worksheet_section(EVIDENCE_SECTION) if inputs is not None and inputs.worksheet_lines else ''
    rows = []
    for table in tables_of(body.split('\n')):
        if not LIFECYCLE_HEADER.match(table[0]):
            continue
        for line in table[1:]:
            cells = [cell.strip().strip('`') for cell in line.strip().strip('|').split('|')]
            if len(cells) < 5:
                continue
            found = STRUCT_NAME.search(cells[0])
            rows.append({'object': f'struct {found.group(1)}' if found else cells[0], 'field': cells[1], 'mark': cells[2],
                         'writer': re.sub(r'\(\)$', '', cells[3]), 'site': cells[4],
                         'event': cells[5] if len(cells) > 5 else '', 'value': cells[6] if len(cells) > 6 else ''})
        break
    return rows


EXCLUDED_LINE = re.compile(r'^excluded:\s*(.+?)\s*(?:\((.*)\))?\s*$', re.I)


def lifecycle_exclusions(inputs):
    """{file basename: reason} from `excluded: file[, file] (reason)` lines under the Lifecycle heading:
    the files whose writers the lifecycle census leaves out, each with its stated reason."""
    body = inputs.worksheet_section(EVIDENCE_SECTION) if inputs is not None and inputs.worksheet_lines else ''
    out = {}
    active = False
    for line in body.split('\n'):
        if line.startswith('### '):
            active = line.strip().lower() == '### lifecycle'
            continue
        m = EXCLUDED_LINE.match(line.strip()) if active else None
        if m:
            for name in re.split(r'\s*,\s*', m.group(1)):
                out[name.split('/')[-1].strip('`')] = (m.group(2) or '').strip()
    return out
