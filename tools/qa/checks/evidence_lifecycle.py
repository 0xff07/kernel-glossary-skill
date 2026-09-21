"""Checks for [evidence.lifecycle]."""
import re
from constructs import assignment_to, constructs_of, construct_at, field_writers, members_of, object_sources
from inputs import source_lines
from pagemodel import legend_entries
from report import Finding, observations
from worksheet_utils import lifecycle_exclusions, lifecycle_rows
RULE = 'evidence.lifecycle'
SITE = re.compile(r'^([\w./-]+):(\d+)$')
LINE_CLIP = 60

def resolve(cited, file):
    if file in cited:
        return file
    tails = [c for c in cited if c.split('/')[-1] == file or c.endswith('/' + file)]
    return tails[0] if len(tails) == 1 else None

def lifecycle(page, inputs):
    rows = lifecycle_rows(inputs)
    excluded = lifecycle_exclusions(inputs)
    findings, listing = [], []
    counts = {'rows': len(rows), 'objects': 0, 'verified': 0, 'missing_writers': 0, 'findings': 0, 'uncorroborated': 0}
    if not rows:
        yield from observations([], 'lifecycle rows=0', [], dict(counts))
        return
    legends = [e for fence in page.figures for e in legend_entries(fence.body)[0]]
    cited = page.cited_files()
    definitions = {key.split()[1]: path for key, path, _line, _n in page.catalog_entries if key.startswith('struct ') and path}
    sources = object_sources(page, inputs)
    tables = {}

    def fail(text):
        counts['findings'] += 1
        findings.append(Finding(None, 'FAIL', text))
    by_object = {}
    for row in rows:
        by_object.setdefault(row['object'], []).append(row)
    for obj, orows in by_object.items():
        counts['objects'] += 1
        name = obj.split()[-1]
        defined = definitions.get(name)
        if defined is None:
            # another page's struct whose field this page's writers set: its definition is found in the cited neighbourhood
            defined = next((path for path, source in sources.items() if source and members_of(source, name)), None)
        if defined is None:
            fail(f'{obj} is defined in no file the page cites; a lifecycle figure draws a struct the page catalogs or one defined beside the code it cites')
            continue
        members = members_of(source_lines(inputs.tree, defined, inputs.cache) or [], name)
        census = field_writers(sources, name)
        for row in orows:
            field, mark, writer, site = row['field'], row['mark'], row['writer'], row['site']
            tag = f'{obj}.{field} {mark}'
            if members and field not in members:
                fail(f'{tag}: {field} is not a member of the struct as {defined} defines it')
                continue
            m = SITE.match(site)
            path = resolve(cited, m.group(1)) if m else None
            if path is None:
                fail(f'{tag}: site {site!r} is not a file:line the page cites')
                continue
            line = int(m.group(2))
            source = source_lines(inputs.tree, path, inputs.cache)
            if source is None or not 0 < line <= len(source):
                fail(f'{tag}: {site} is beyond the file')
                continue
            if not assignment_to(source[line - 1], field):
                fail(f'{tag}: {site} does not assign {field}: {source[line - 1].strip()[:LINE_CLIP]!r}')
                continue
            if path not in tables:
                tables[path] = constructs_of(source)
            construct = construct_at(tables[path], line)
            if construct is None or construct.name != writer:
                holder = construct.label(path.rsplit('/', 1)[-1]) if construct else 'no function'
                fail(f'{tag}: {site} lies in {holder}, not in {writer}()')
                continue
            matching = [e for e in legends if e['mark'] == mark and e['name'] == writer]
            if not matching:
                findings.append(Finding(None, 'review', f'{tag} {writer} {site}: no figure legend on the page carries this mark with this writer'))
            elif not any(re.search(r'\b' + re.escape(field) + r'\b', e['phrase']) for e in matching):
                findings.append(Finding(None, 'review', f"{tag} {writer} {site}: the legend phrase does not name {field}; say which field the writer sets and to what"))
            if any(p == path and l == line and f == writer for p, l, f in census.get(field, [])):
                counts['verified'] += 1
            else:
                counts['uncorroborated'] += 1
                findings.append(Finding(None, 'review', f"{tag} {writer} {site}: the census of struct {name}'s writers does not list this site, so the assignment may set another struct's {field}; verify by hand that the variable is a {obj}"))
        for field in sorted({r['field'] for r in orows}):
            in_table = {r['writer'] for r in orows if r['field'] == field}
            for fn in sorted({f for p, _l, f in census.get(field, []) if p.split('/')[-1] not in excluded} - in_table):
                sites = ', '.join(sorted(f"{p.rsplit('/', 1)[-1]}:{l}" for p, l, f2 in census[field] if f2 == fn))
                counts['missing_writers'] += 1
                findings.append(Finding(None, 'review', f'{obj}.{field}: {fn}() also writes it ({sites}) and has no row; a lifecycle with a writer missing asserts a state the code can leave'))
        listing.append(f"{obj}: rows={len(orows)} fields={', '.join(sorted({r['field'] for r in orows}))}")
    footer = f"rows={counts['rows']} objects={counts['objects']} verified={counts['verified']} uncorroborated={counts['uncorroborated']} missing-writers={counts['missing_writers']} excluded-files={len(excluded)} findings={counts['findings']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('worksheet')
    inputs.require('tree')
    yield from lifecycle(page, inputs)
