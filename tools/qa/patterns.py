"""Regex sweeps over the shared page views, with ordinary Python arguments."""
import re
from pagemodel import ITEM
from report import Finding
DEFAULT_REGIONS = ('prose', 'section6', 'catalog', 'heading')
CONTEXT = 60

def rows_of(page, view='prose', region=None, not_in_cells=False):
    """(line, tag, text, region, in_catalog) for every row the rule sweeps."""
    regions = set(region or DEFAULT_REGIONS)
    rows = []
    if view == 'raw':
        for n, text in page.raw_view():
            region = page.region_of(n)
            if region == 'blank':
                continue
            section = page.section_of(n)
            tag = '[C] ' if section.region == 'catalog' or text.startswith('|') or (section.region == 'section6' and ITEM.match(text)) else ''
            if region == 'heading':
                tag = '[H] '
            rows.append((n, tag, text, region, section.region == 'catalog'))
    else:
        for row in page.prose_view(spans_visible=view == 'spans-visible'):
            rows.append((row.line, row.tag, row.text, row.region, row.in_catalog))
    selected = [r for r in rows if r[3] in regions]
    if not_in_cells:
        selected = [r for r in selected if r[1] != '[C] ' and (not (r[3] == 'heading' and r[4]))]
    for kind in ('figure', 'quotation', 'excerpt'):
        if kind not in regions:
            continue
        for fence in page.fences:
            if fence.kind != kind:
                continue
            for k, text in enumerate(fence.body):
                selected.append((fence.start + 1 + k, '', text, kind, False))
    return selected

def exempt(text, match, flags, unless=()):
    """True when an `unless` shape encloses the hit or, anchored at the row's start, names the
    row's shape."""
    for shape in unless or []:
        pattern = re.compile(str(shape), flags)
        for found in pattern.finditer(text):
            if found.start() <= match.start() and match.end() <= found.end():
                return True
            if str(shape).startswith('^'):
                return True
    return False

def context_of(text, match):
    start = max(0, match.start() - CONTEXT)
    end = min(len(text), match.end() + CONTEXT)
    return text[start:end].strip()

def find_pattern(page, pattern, *, name, severity='review', view='prose', region=None, flags=re.I, unless=(), not_in_cells=False, fix=None):
    regex = re.compile(pattern, flags)
    hits = 0
    for n, _tag, text, area, _cat in rows_of(page, view, region, not_in_cells):
        match = regex.search(text)
        if not match or exempt(text, match, flags, unless):
            continue
        hits += 1
        context = context_of(text, match)
        label = f'{name} in a {area}' if area in ('figure', 'quotation', 'excerpt') else name
        message = f'{label}: …{context}…'
        if fix:
            message += f' (the fix: {fix})'
        yield Finding(n, severity, message)
    yield Finding(None, 'note', f"{name.replace(' ', '-')}={hits}", {'hits': hits})
