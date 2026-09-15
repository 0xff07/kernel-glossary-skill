"""Shared parsing and reporting utilities."""
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
    """({span: cells}, refused spans) from the dossier's LINKS section."""
    rows, refused = ({}, [])
    for line in inputs.dossier_section(LINKS_SECTION).split('\n'):
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

def emit_table(page, inputs, out=sys.stdout, err=sys.stderr):
    """The table on stdout, and on stderr the rows it could not read and the delta."""
    if inputs.tree is None:
        print('no kernel tree: the disk lines cannot be read, so no table is emitted', file=err)
        return 2
    rows, refused = links_rows(inputs) if inputs.dossier_lines else ({}, [])
    lines = [HEADER, SEPARATOR]
    for key in sorted(page.spans, key=str.lower):
        span = page.spans[key]
        url = span.urls[0] if span.urls else ''
        existing = (rows.get(key) or [''])[-1].strip() if rows else ''
        reason = existing or (linked_kind(key.strip(), span) if span.linked else classify(key))
        positions = ' '.join((str(n) for n in span.at[:TABLE_LISTED_POSITIONS]))
        lines.append(f"| `{key.replace('|', chr(92) + '|')}` | {span.region} | {span.linked} | {span.bare} | {positions} | {url} | {disk_cell(url, inputs)} | {reason} |")
    print('\n'.join(lines), file=out)
    for key in refused[:REPORTED_REFUSALS]:
        print(f'review: LINKS row `{key}` could not be read; its kind / reason cell was not carried', file=err)
    if len(refused) > REPORTED_REFUSALS:
        print(f'review: {len(refused) - REPORTED_REFUSALS} further LINKS row(s) refused for the same reason', file=err)
    if rows:
        added = sorted(set(page.spans) - set(rows))
        removed = sorted(set(rows) - set(page.spans))
        moved = [k for k in page.spans if k in rows and len(rows[k]) > 1 and (rows[k][1] != page.spans[k].region)]

        def named(keys):
            if not keys:
                return '-'
            text = ', '.join((f'`{k}`' for k in keys[:REPORTED_SPANS]))
            return text if len(keys) <= REPORTED_SPANS else f'{text}, and {len(keys) - REPORTED_SPANS} more'
        changes = ', '.join((f'`{k}` ({rows[k][1]} -> {page.spans[k].region})' for k in moved)) or '-'
        print(f'links delta against {inputs.dossier}: carried {len(lines) - 2 - len(added)} kind / reason cells; {len(added)} added row(s) to fill: {named(added)}; {len(removed)} removed: {named(removed)}; {len(moved)} region change(s): {changes}', file=err)
    return 0
