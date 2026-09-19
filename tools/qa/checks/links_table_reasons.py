"""Checks for [links-table.reasons]."""
from report import Finding
from report import observations
from links_table import links_rows
from links_table import refused_wholesale
from links_table import entry_texts
RULE = 'links-table.reasons'
REPORTED_POSITIONS = 3

def reasons(page, inputs):
    rows, refused = links_rows(inputs)
    entries = entry_texts(page)
    prose_rows = [k for k, c in rows.items() if len(c) > 1 and c[1] == 'prose']
    catalog_text = [k for k, c in rows.items() if len(c) > 1 and c[1] == 'catalog' and (k not in entries)]
    blank = [k for k in prose_rows + catalog_text if not rows[k][-1].strip()]
    findings, listing = ([], [])
    if refused_wholesale(rows, refused):
        findings.append(Finding(None, 'review', f'the LINKS closure test was not run: only {len(rows)} row(s) of the table could be read'))
    else:
        for key in blank:
            region = 'prose' if key in prose_rows else 'catalog-text'
            findings.append(Finding(None, 'FAIL', f'LINKS {region} row `{key}` has an empty kind / reason cell'))
    for span in sorted(page.bare_only_spans('prose'), key=lambda s: -s.bare):
        reason = (rows.get(span.text) or [''])[-1].strip()
        listing.append(f'bare {span.text[:44]:44s} x{span.bare} at {span.at[:4]} | {reason[:80]}')
        if rows and (not reason):
            findings.append(Finding(None, 'review', f'bare span `{span.text}` at {span.at[:REPORTED_POSITIONS]} has no settled reason in LINKS'))
    for span in sorted(page.bare_only_spans('catalog'), key=lambda s: -s.bare):
        reason = (rows.get(span.text) or [''])[-1].strip()
        listing.append(f'bare in a catalog bullet {span.text[:44]:44s} x{span.bare} | {reason[:80]}')
        if rows and (not reason) and (span.text not in rows):
            findings.append(Finding(None, 'review', f"bare span `{span.text}` in a catalog bullet's text has no LINKS row; re-emit the table with kg table"))
    footer = f'links-rows={len(rows)} prose-rows={len(prose_rows)} catalog-text-rows={len(catalog_text)} blank-reasons={len(blank)}'
    yield from observations(findings, footer, listing, {'links_rows': len(rows), 'prose_rows': len(prose_rows), 'catalog_text_rows': len(catalog_text), 'links_blank_reasons': len(blank)})

def check(page, inputs):
    inputs.require('worksheet')
    yield from reasons(page, inputs)
