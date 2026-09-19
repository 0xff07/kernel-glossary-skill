"""Checks for [arrangement.actors]."""
from pagemodel import CODE_LINK, split_cells, TABLE_SEPARATOR
from report import Finding, observations
RULE = 'arrangement.actors'
MIN_CATALOG = 8
MIN_ACTORS = 3

def actor_table(page):
    """(header line, rows) of the actor table in the DETAILS preamble, or (None, [])."""
    lines = page.details_preamble
    for i, (n, line) in enumerate(lines):
        if not line.startswith('|'):
            continue
        header = [c.lower() for c in split_cells(line)]
        if header and 'actor' in header[0] and any('role' in c for c in header[1:]):
            rows = []
            for m, text in lines[i + 1:]:
                if not text.startswith('|'):
                    break
                if TABLE_SEPARATOR.match(text):
                    continue
                rows.append((m, split_cells(text)))
            return n, rows
    return None, []

def actors(page, inputs):
    findings, listing = [], []
    catalog = len(page.catalog_keys)
    header, rows = actor_table(page)
    structs = {key for key in page.catalog_keys if key.startswith('struct ')}
    if header is None:
        if catalog >= MIN_CATALOG and page.subsections:
            findings.append(Finding(page.section('DETAILS').start, 'FAIL', f'{catalog} catalog symbols and no actor table; open DETAILS, after the route paragraph, with a table of the actors the page keeps naming and their one-line roles'))
        yield from observations(findings, f'catalog={catalog} actors=absent', [], {'catalog': catalog, 'actors': 0})
        return
    named = []
    for m, cells in rows:
        links = CODE_LINK.findall(cells[0]) if cells else []
        if not links:
            findings.append(Finding(m, 'review', f'actor row without a linked symbol in its first cell: {cells[0][:60] if cells else ""!r}'))
        named.extend(t.strip().strip('`') for t, _u in links)
        listing.append(f'{m:5} actor {cells[0][:40] if cells else ""} | {cells[1][:70] if len(cells) > 1 else ""}')
    if len(rows) < MIN_ACTORS:
        findings.append(Finding(header, 'review', f'{len(rows)} actor rows; the table names the objects and functions the page keeps returning to, normally {MIN_ACTORS} or more'))
    missing = sorted(s for s in structs if not any(s.split()[-1] == n.split()[-1] for n in named))
    if missing:
        findings.append(Finding(header, 'review', f"cataloged objects absent from the actor table: {', '.join(missing)}"))
    footer = f'catalog={catalog} actors={len(rows)} structs-covered={len(structs) - len(missing)}/{len(structs)}'
    yield from observations(findings, footer, listing, {'catalog': catalog, 'actors': len(rows), 'structs_missing': missing})

def check(page, inputs):
    yield from actors(page, inputs)
