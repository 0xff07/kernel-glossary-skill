"""Checks for [links.site-text]."""
import re
from report import Row, reading
RULE = 'links.site-text'
SITE_LINK = re.compile(r'\[`?(?P<text>(?P<file>[\w./-]+\.(?:c|h|S|rst|txt|json|yaml|dts|dtsi|py|sh)):(?P<lines>\d+(?:-\d+)?))`?\]\(https://elixir\.bootlin\.com/linux/[^/]+/source/(?P<path>[^#)]+)#L\d+\)')
LINK_URL = re.compile(r'\]\([^)]*\)')
CLIP = 100

def sites(page):
    """Every location link outside a fence: line number, link text, its file part, its line part, the URL path, the line."""
    in_fence = False
    for n, line in enumerate(page.lines, 1):
        if line.startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in SITE_LINK.finditer(line):
            yield n, m.group('text'), m.group('file'), m.group('lines'), m.group('path'), line

def site_text(page, inputs):
    found = list(sites(page))
    by_base = {}
    for _n, _text, _file, _lines, path, _line in found:
        by_base.setdefault(path.rsplit('/', 1)[-1], set()).add(path)
    clashes = {base for base, paths in by_base.items() if len(paths) > 1}
    rows, with_directory, bare_clashes = [], 0, 0
    for n, text, file, lines, path, line in found:
        base = path.rsplit('/', 1)[-1]
        snippet = LINK_URL.sub(']', line).strip()[:CLIP]
        if base in clashes:
            if '/' not in file:
                bare_clashes += 1
                rows.append(Row(n, f"{text}: two cited files share this base name ({', '.join(sorted(by_base[base]))}); write the path from the tree root | {snippet}", set()))
        elif '/' in file:
            with_directory += 1
            rows.append(Row(n, f"{text}: the site text carries its directory; write {base}:{lines}, the URL and the excerpt provenance carry the path | {snippet}", set()))
    footer = f'location-links={len(found)} with-directory={with_directory} bare-clashes={bare_clashes} clashing-base-names={len(clashes)}'
    yield from reading(rows, [], footer, {'location_links': len(found), 'with_directory': with_directory, 'bare_clashes': bare_clashes, 'clashing_base_names': len(clashes)}, severity='review')

def check(page, inputs):
    yield from site_text(page, inputs)
