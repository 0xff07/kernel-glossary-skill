"""Checks for [page.self-contained]."""
from report import Finding
from report import reading
from report import Row
import re
from pagemodel import LINK
from pagemodel import CODE_SPAN
from pagemodel import QUOTATION
RULE = 'page.self-contained'
LINK_TARGET = re.compile('\\]\\(([^)]*)\\)')
CLIP = 60

def no_link_target(page):
    pattern = re.compile('^(?![a-z]+://).*\\.md$')
    out = []
    for n, line in masked_rows(page):
        for match in LINK_TARGET.finditer(line):
            if pattern.search(match.group(1)):
                out.append(Finding(n, 'FAIL', f'link target {match.group(1)[:CLIP]} (a page links to no other page)'))
    return out
CODE_SPAN = re.compile('`[^`]+`')
FACT_SPLIT = re.compile('(?<=[.!?])\\s+')
FACT_CLIP = 150
DEFLECTION_NAMED = re.compile('(?<![\\w/])(?:[a-z0-9][a-z0-9-]*/)*[a-z0-9][a-z0-9-]*\\.md\\b')
DEFLECTION_ANON = re.compile("\\b(?:another|other|a different|its own|the owning)\\s+pages?\\b|\\bpages?\\s+(?:that\\s+)?owns?\\b|\\b(?:documented|covered|described|explained|walked|traced|handled)\\s+elsewhere\\b|\\belsewhere\\s+in\\s+(?:the|this)\\s+(?:knowledge base|documentation|set)\\b|\\b(?:outside|beyond)\\s+(?:this|the)\\s+page(?:'s)?(?:\\s+\\w+)?\\s+scope\\b|\\bnot\\s+(?:covered|explained|traced)\\s+(?:here|on this page)\\b|\\bthis\\s+page\\s+does\\s+not\\s+(?:cover|follow|trace|walk|document)\\b", re.I)
OWNING_COLUMN = re.compile('^(?:owning page|owner|page that owns(?:\\s+.*)?|owned by|which page)$', re.I)

def owning_columns(page):
    return {table.line: (table, {col for col, cell in enumerate(table.header) if OWNING_COLUMN.match(CODE_SPAN.sub('', cell))}) for table in page.tables if table.region in ('prose', 'section6')}

def masked_rows(page):
    """Remove cells already accounted for by an owning-page column observation."""
    masked = {}
    for table, columns in owning_columns(page).values():
        if columns:
            for row in table.rows:
                masked[row.line] = '|'.join((cell for col, cell in enumerate(row.cells) if col not in columns))
    for n, text in page.raw_view():
        yield (n, masked.get(n, text))

def deflections(page, inputs):
    rows, named, anon, columns = ([], 0, 0, 0)
    tables = owning_columns(page)
    for n, line in masked_rows(page):
        if page.region_of(n) not in ('prose', 'section6'):
            continue
        if n in tables:
            table, owning = tables[n]
            for col in sorted(owning):
                columns += 1
                rows.append(Row(n, f'{n} OWNING-PAGE COLUMN: | {table.header[col]} | drop it and put the content in its place', set()))
            continue
        clean = CODE_SPAN.sub('X', LINK.sub('\\1', line))
        for sentence in FACT_SPLIT.split(clean):
            hit = DEFLECTION_NAMED.search(sentence)
            if hit:
                named += 1
                rows.append(Row(n, f'{n} NAMES A PAGE ({hit.group(0)}): {sentence.strip()[:FACT_CLIP]}', set()))
                continue
            hit = DEFLECTION_ANON.search(sentence)
            if hit:
                anon += 1
                rows.append(Row(n, f'{n} ANONYMOUS HANDOFF ({hit.group(0).strip()}): {sentence.strip()[:FACT_CLIP]}', set()))
    footer = f'deflections={len(rows)} naming-a-page={named} anonymous={anon} owning-page-columns={columns}; a boundary is a floor, so each is read for the fact it withholds, which is written in its place, or the clause is cut'
    yield from reading(rows, [], footer, {'deflections': len(rows), 'named': named, 'anonymous': anon, 'owning_columns': columns}, severity='review')

def no_sibling_page_named(page):
    """A page that hands its explanation to another page of the knowledge base.

    The link form is caught by no_link_target; writers reach the same effect by
    naming the page as plain prose. campaign.md [planning.boundaries] makes a
    boundary a floor and never a fence, so every page reaches the symbols its own
    narrative needs and explains them where it needs them.
    """
    pattern = re.compile('(?<![\\w/])(?:[a-z0-9][a-z0-9-]*/)*[a-z0-9][a-z0-9-]*\\.md\\b')
    out = []
    for n, line in masked_rows(page):
        masked = QUOTATION.sub(' ', CODE_SPAN.sub(' ', line))
        match = pattern.search(masked)
        if match:
            out.append(Finding(n, 'review', f'another page of the knowledge base is named in prose, `{match.group(0)}`: a boundary is a floor, so write the fact here instead of handing it over: {line.strip()[:CLIP]}'))
    return out

def no_text_outside_fences(page):
    pattern = re.compile('\\{L\\(|\\{\\{|(?<![Tt]he )(?<![Aa] )(?<![Ii]ts )(TODO|XXX|FIXME)')
    out = []
    for n, line in masked_rows(page):
        masked = QUOTATION.sub(' ', CODE_SPAN.sub(' ', line))
        match = pattern.search(masked)
        if match:
            out.append(Finding(n, 'FAIL', f'template text `{match.group(0)}` left on the page: {line.strip()[:CLIP]}'))
    return out

def check(page, inputs):
    links = no_link_target(page)
    named = no_sibling_page_named(page)
    yield from links
    yield from named
    accounted = {f.line for f in links + named}
    for finding in deflections(page, inputs):
        if finding.data is not None and 'flags' not in finding.data:
            yield finding
        elif finding.line not in accounted or 'NAMES A PAGE' not in finding.message:
            yield finding
    yield from no_text_outside_fences(page)
