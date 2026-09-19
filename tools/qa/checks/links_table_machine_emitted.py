"""Checks for [links-table.machine-emitted]."""
from report import Finding
from report import observations
from links_table import links_rows
from links_table import refused_wholesale
RULE = 'links-table.machine-emitted'
LINKS_COLUMNS = 8
REPORTED_REFUSALS = 6

def emitted(page, inputs):
    rows, refused = links_rows(inputs)
    findings = []
    if refused:
        named = ', '.join((f'`{k}`' for k in refused[:REPORTED_REFUSALS])) + (f', and {len(refused) - REPORTED_REFUSALS} more' if len(refused) > REPORTED_REFUSALS else '')
        findings.append(Finding(None, 'review', f"{len(refused)} LINKS row(s) do not carry the table's {LINKS_COLUMNS} columns and were not read: {named}; re-emit the table with kg table"))
    if refused_wholesale(rows, refused):
        only_extractor, only_worksheet = ([], [])
        findings.append(Finding(None, 'review', f"the span comparison against the worksheet's LINKS table was not run: only {len(rows)} row(s) could be read"))
    else:
        only_extractor = sorted(set(page.spans) - set(rows))
        only_worksheet = sorted(set(rows) - set(page.spans))
        for key in only_extractor:
            findings.append(Finding(None, 'review', f'span `{key}` has no LINKS row in the worksheet'))
        for key in only_worksheet:
            findings.append(Finding(None, 'review', f'LINKS row `{key}` has no span on the page (stale or hand-edited)'))
    footer = f'worksheet-rows={len(rows)} only-in-extractor={len(only_extractor)} only-in-worksheet={len(only_worksheet)}'
    yield from observations(findings, footer, [], {'worksheet_rows': len(rows), 'only_in_extractor': only_extractor, 'only_in_worksheet': only_worksheet, 'refused': refused})

def check(page, inputs):
    inputs.require('worksheet')
    yield from emitted(page, inputs)
