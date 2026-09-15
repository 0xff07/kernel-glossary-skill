"""Checks for [sections.coverage-form]."""
from report import Finding
from pagemodel import CATALOG_ENTRY
RULE = 'sections.coverage-form'
CLIP = 60

def catalog_entry_form(page):
    """Every bullet under COVERAGE is a catalog entry in the quoted form with one backslash; a
    bullet the catalog parser does not read would otherwise vanish from every catalog check."""
    section = page.section('COVERAGE')
    if section is None:
        return []
    findings = []
    for n in range(section.start + 1, section.end + 1):
        line = page.lines[n - 1]
        if not line.startswith('- [') or page.in_fence(n):
            continue
        match = CATALOG_ENTRY.match(line)
        if not match or not match.group(1):
            findings.append(Finding(n, 'FAIL', f"COVERAGE bullet is not in the catalog form `'\\<name\\>':'path'` (one backslash before < and >, then the file, then the Elixir link), so no catalog check sees it: {line[:CLIP]}"))
    return findings

def check(page, inputs):
    yield from catalog_entry_form(page)
