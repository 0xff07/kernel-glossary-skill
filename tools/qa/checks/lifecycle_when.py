"""Checks for [lifecycle.when]."""
import os
from constructs import field_writers, sources_under
from report import Finding, observations
from worksheet_utils import lifecycle_exclusions, lifecycle_rows
RULE = 'lifecycle.when'
MIN_WRITERS = 2

def qualifying_fields(sources, name, excluded=()):
    """{field: [writer functions]} for the fields of `struct name` that MIN_WRITERS or more functions write,
    writers in the excluded files left out."""
    out = {}
    for field, sites in field_writers(sources, name).items():
        functions = sorted({fn for p, _l, fn in sites if p.split('/')[-1] not in excluded})
        if len(functions) >= MIN_WRITERS:
            out[field] = functions
    return out

def candidates(page, inputs):
    findings, listing = [], []
    structs = [key.split()[1] for key in page.catalog_keys if key.startswith('struct ')]
    counts = {'objects': len(structs), 'qualifying': 0, 'recorded': 0}
    recorded = {row['object'] for row in lifecycle_rows(inputs)}
    excluded = lifecycle_exclusions(inputs)
    dirs = {os.path.dirname(f) for f in page.cited_files() if f.endswith(('.c', '.h'))}
    sources = sources_under(inputs.tree, dirs, inputs.cache) if structs else {}
    for name in structs:
        fields = qualifying_fields(sources, name, excluded)
        if not fields:
            listing.append(f'struct {name}: no field with {MIN_WRITERS} or more writers')
            continue
        counts['qualifying'] += 1
        summary = '; '.join(f"{field} ({len(fns)}: {', '.join(fns)})" for field, fns in sorted(fields.items(), key=lambda kv: -len(kv[1])))
        if f'struct {name}' in recorded:
            counts['recorded'] += 1
            listing.append(f'struct {name}: {summary}; Lifecycle table recorded')
            continue
        findings.append(Finding(None, 'review', f'struct {name} has fields written by several functions, {summary}: draw its lifecycle figure and record the Lifecycle table (figures.md [lifecycle], worksheet.md [evidence.lifecycle])', {'object': name, 'fields': fields}))
    footer = f"objects={counts['objects']} qualifying={counts['qualifying']} recorded={counts['recorded']} excluded-files={len(excluded)}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from candidates(page, inputs)
