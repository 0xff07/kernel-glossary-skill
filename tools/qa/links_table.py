"""The worksheet's LINKS table: read back, emitted from the page's spans and written into the
worksheet with every kind / reason cell it already holds."""
import os
import re
import sys
from inputs import disk_line
from pagemodel import ELIXIR
from pagemodel import split_cells
from span_utils import CONFIG_PREFIX
from span_utils import FILE
from span_utils import LOCATION
from span_utils import classify
LINKS_SECTION = '## LINKS'
LINKS_COLUMNS = 8
GROUPED_ROW = '` / `'
HEADER = '| span | region | linked | bare | bare at | anchor URL | disk line | kind / reason |'
SEPARATOR = '|---|---|---|---|---|---|---|---|'
REPORTED_REFUSALS = 6
TABLE_LISTED_POSITIONS = 6
TABLE_DISK_CLIP = 48
ELLIPSIS = '…'
REPORTED_SPANS = 20
CATALOG_SPAN_MARK = "'\\<"
FRAGMENT = '#L'

def links_rows(inputs):
    """({span: cells}, refused spans) from the worksheet's LINKS section."""
    rows, refused = ({}, [])
    for line in inputs.worksheet_section(LINKS_SECTION).split('\n'):
        if not line.startswith('| `'):
            continue
        cells = split_cells(line)
        if GROUPED_ROW in cells[0]:
            continue
        key = cells[0].strip('`').replace('\\|', '|')
        if len(cells) != LINKS_COLUMNS:
            refused.append(key)
            continue
        rows[key] = cells
    return (rows, refused)

def refused_wholesale(rows, refused):
    return bool(refused) and (not rows or len(refused) > len(rows))

def entry_texts(page):
    """The exact span texts of the catalog's own entries, as the bullets carry them."""
    out = set()
    for n, line in enumerate(page.lines, 1):
        if page.region_of(n) == 'catalog' and line.startswith('- [`'):
            match = re.match('^- \\[`([^`]+)`\\]\\(', line)
            if match:
                out.add(match.group(1))
    return out

def linked_kind(text, span):
    if text.startswith(CATALOG_SPAN_MARK):
        return 'symbol'
    if LOCATION.match(text):
        return 'location'
    if FILE.match(text) or (bool(span.urls) and FRAGMENT not in span.urls[0]):
        return 'file'
    if text.startswith(CONFIG_PREFIX):
        return 'config'
    return 'symbol'

def disk_cell(url, inputs):
    if not url:
        return ''
    match = ELIXIR.search(url)
    if not match or not match.group(3):
        return ''
    text = (disk_line(inputs.tree, match.group(2), int(match.group(3)), inputs.cache) or '').strip()
    if len(text) > TABLE_DISK_CLIP:
        text = text[:TABLE_DISK_CLIP] + ELLIPSIS
    return text.replace('|', '\\|')

def table_lines(page, inputs, rows):
    """The table for the page's spans, each kind / reason cell carried from `rows` when it holds one."""
    lines = [HEADER, SEPARATOR]
    for key in sorted(page.spans, key=str.lower):
        span = page.spans[key]
        url = span.urls[0] if span.urls else ''
        existing = (rows.get(key) or [''])[-1].strip() if rows else ''
        reason = existing or (linked_kind(key.strip(), span) if span.linked else classify(key))
        positions = ' '.join((str(n) for n in span.at[:TABLE_LISTED_POSITIONS]))
        lines.append(f"| `{key.replace('|', chr(92) + '|')}` | {span.region} | {span.linked} | {span.bare} | {positions} | {url} | {disk_cell(url, inputs)} | {reason} |")
    return lines


def with_table(worksheet_lines, table):
    """The worksheet's lines with `table` in place of the table under ## LINKS: the first run of
    table lines in the section whose header names the span column, a lone header row included;
    a section without one gets the table at its end, a worksheet without the section gets both."""
    lines = list(worksheet_lines)
    if LINKS_SECTION not in lines:
        return lines + ['', LINKS_SECTION, ''] + table
    start = lines.index(LINKS_SECTION)
    end = next((k for k in range(start + 1, len(lines)) if lines[k].startswith('## ')), len(lines))
    first = next((k for k in range(start + 1, end) if lines[k].startswith('|') and 'span' in lines[k].lower()), None)
    if first is None:
        insert = end
        while insert > start + 1 and not lines[insert - 1].strip():
            insert -= 1
        return lines[:insert] + [''] + table + [''] + lines[end:]
    last = first
    while last + 1 < end and lines[last + 1].startswith('|'):
        last += 1
    return lines[:first] + table + lines[last + 1:]


def named(keys):
    if not keys:
        return '-'
    text = ', '.join((f'`{k}`' for k in keys[:REPORTED_SPANS]))
    return text if len(keys) <= REPORTED_SPANS else f'{text}, and {len(keys) - REPORTED_SPANS} more'


def emit_table(page, inputs, out=sys.stdout, err=sys.stderr):
    """Writes the table into the worksheet's LINKS section, every kind / reason cell the section
    holds carried, and prints the delta with the rows to fill; without a worksheet on disk the
    table itself is printed. Refused rows go to stderr."""
    if inputs.tree is None:
        print('no kernel tree: the disk lines cannot be read, so no table is emitted', file=err)
        return 2
    rows, refused = links_rows(inputs) if inputs.worksheet_lines else ({}, [])
    lines = table_lines(page, inputs, rows)
    path = inputs.worksheet if inputs.worksheet and os.path.isfile(inputs.worksheet) else None
    if path:
        text = '\n'.join(with_table(inputs.worksheet_lines, lines))
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text if text.endswith('\n') else text + '\n')
        print(f'LINKS table written to {path}: {len(lines) - 2} row(s)', file=out)
    else:
        print('\n'.join(lines), file=out)
        print(f"no worksheet on disk at {inputs.worksheet or '-'}; the table is printed, not written", file=err)
    for key in refused[:REPORTED_REFUSALS]:
        print(f'review: LINKS row `{key}` could not be read; its kind / reason cell was not carried', file=err)
    if len(refused) > REPORTED_REFUSALS:
        print(f'review: {len(refused) - REPORTED_REFUSALS} further LINKS row(s) refused for the same reason', file=err)
    if rows or path:
        added = sorted(set(page.spans) - set(rows))
        removed = sorted(set(rows) - set(page.spans))
        moved = [k for k in page.spans if k in rows and len(rows[k]) > 1 and (rows[k][1] != page.spans[k].region)]
        changes = ', '.join((f'`{k}` ({rows[k][1]} -> {page.spans[k].region})' for k in moved)) or '-'
        print(f'links delta against {inputs.worksheet}: carried {len(lines) - 2 - len(added)} kind / reason cells; {len(added)} added row(s) to fill: {named(added)}; {len(removed)} removed: {named(removed)}; {len(moved)} region change(s): {changes}', file=out)
    return 0
