"""Checks for [links.definition-line]."""
from report import Finding
from report import observations
from pagemodel import TAGS
from span_utils import bare_span_rows
from span_utils import CONFIG_PREFIX
from span_utils import FILE
from span_utils import LOCATION
import os
import re
from inputs import disk_line
from pagemodel import ELIXIR
from pagemodel import RETURN_TYPE_LINE
RULE = 'links.definition-line'

def struct_keyword_kept(page):
    tagged = {}
    for span in page.spans.values():
        words = span.text.split()
        if len(words) == 2 and words[0] in TAGS:
            tagged[words[1]] = words[0]
    out = []
    for span in page.spans.values():
        if span.text in tagged and span.region == 'prose':
            out.append(Finding(span.at[0] if span.at else None, 'review', f'span `{span.text}` drops the `{tagged[span.text]}` keyword the page uses elsewhere'))
    return out
SYMBOL = re.compile('^(?:struct |enum |union )?([A-Za-z_]\\w*)(?:\\(\\))?$')
FIELD = re.compile('^[A-Za-z_]\\w*(?:(?:->|\\.)[A-Za-z_]\\w*)+(?:\\[[^\\]]*\\])?$')
LOCATION_ANY = re.compile('^([\\w./-]+):(\\d+)(?:-(\\d+))?$')
TRACE_PREFIX = 'trace_'
DISK_CLIP = 60

def tree_holds(inputs, path):
    """Whether the tree holds the path, as a file or as a directory (a link may name either),
    the path confined to the tree: one that escapes it by `..` or an absolute form is not held."""
    if inputs.tree is None:
        return False
    root = os.path.realpath(inputs.tree)
    target = os.path.realpath(os.path.join(root, path))
    return (target == root or target.startswith(root + os.sep)) and os.path.exists(target)

def names_anything(haystack, names):
    return any((re.search('(?<![\\w])' + re.escape(n) + '(?![\\w])', haystack) for n in names))

def check_one_anchor(span, url, inputs, findings):
    """(opened, misses) for one URL of one span."""
    match = ELIXIR.search(url)
    if not match:
        return (0, 0)
    if not match.group(3):
        if not tree_holds(inputs, match.group(2)):
            findings.append(Finding(None, 'FAIL', f'file link {match.group(2)} names a path the tree does not hold (span `{span.text}`)'))
            return (1, 1)
        return (1, 0)
    path, line = (match.group(2), int(match.group(3)))
    disk = disk_line(inputs.tree, path, line, inputs.cache)
    if disk is None:
        findings.append(Finding(None, 'FAIL', f'anchor {path}:{line} is beyond the file or unreadable (span `{span.text}`)'))
        return (0, 1)
    misses = 0
    text = span.text.strip()
    location = LOCATION.match(text)
    if not location:
        loose = LOCATION_ANY.match(text)
        if loose and loose.group(1).split('/')[-1] == path.split('/')[-1]:
            location = loose
    if FILE.match(text):
        if path.split('/')[-1] != text:
            findings.append(Finding(None, 'FAIL', f'file span `{span.text}` links {path}:{line}'))
            misses += 1
    elif location:
        first, last = int(location.group(2)), int(location.group(3)) if location.group(3) else None
        if first != line or location.group(1).split('/')[-1] != path.split('/')[-1]:
            what = ', not its first line' if last is not None and first != line else ''
            findings.append(Finding(None, 'FAIL', f'location span `{span.text}` links {path}:{line}{what}'))
            misses += 1
        elif last is not None and (last < first or disk_line(inputs.tree, path, last, inputs.cache) is None):
            why = 'before its first line' if last < first else 'beyond the file'
            findings.append(Finding(None, 'FAIL', f'location span `{span.text}` cites a range ending at {last}, {why}'))
            misses += 1
    elif SYMBOL.match(text):
        name = SYMBOL.match(text).group(1)
        names = [name]
        if name.startswith(CONFIG_PREFIX):
            names.append(name[len(CONFIG_PREFIX):])
        if name.startswith(TRACE_PREFIX):
            names.append(name[len(TRACE_PREFIX):])
        haystack = disk
        if RETURN_TYPE_LINE.match(disk.rstrip()):
            haystack = disk + '\n' + (disk_line(inputs.tree, path, line + 1, inputs.cache) or '')
        if not names_anything(haystack, names):
            findings.append(Finding(None, 'FAIL', f'symbol span `{span.text}` links {path}:{line}, a line that does not name it: {disk.strip()[:DISK_CLIP]!r}'))
            misses += 1
    elif FIELD.match(text):
        last = re.split('->|\\.', re.sub('\\[[^\\]]*\\]$', '', text))[-1]
        if not re.search('(?<![\\w])' + re.escape(last) + '(?![\\w])', disk):
            findings.append(Finding(None, 'FAIL', f'field span `{span.text}` links {path}:{line}, a line that does not name `{last}`: {disk.strip()[:DISK_CLIP]!r}'))
            misses += 1
    if not disk.strip():
        findings.append(Finding(None, 'FAIL', f'anchor {path}:{line} of `{span.text}` is an empty line'))
        misses += 1
    return (1, misses)

def inspect_page(page, inputs):
    findings, listing = ([], [])
    checked = misses = 0
    for span in page.linked_spans():
        for url in span.urls:
            opened, missed = check_one_anchor(span, url, inputs, findings)
            checked += opened
            misses += missed
    entries = bad = 0
    for key, path, line, page_line in page.catalog_entries:
        if line is None or '/' in key:
            continue
        entries += 1
        disk = disk_line(inputs.tree, path, line, inputs.cache) or ''
        if key.split()[-1].rstrip('()') not in disk:
            bad += 1
            findings.append(Finding(page_line, 'FAIL', f'catalog entry {key} links {path}:{line}, a line that does not name it: {disk.strip()[:DISK_CLIP]!r}'))
    listing.extend((text for _span, text in bare_span_rows(page)))
    located = [LOCATION.match(span.text.strip()) for span in page.linked_spans()]
    ranges = sum(1 for m in located if m and m.group(3))
    single = sum(1 for m in located if m and not m.group(3))
    footer = f"spans={len(page.spans)} linked={len(page.linked_spans())} bare-only-prose={len(page.bare_only_spans('prose'))} bare-only-catalog-text={len(page.bare_only_spans('catalog'))} bare-occurrences={page.bare_occurrences()} anchors-checked={checked} anchor-misses={misses} catalog-entries={entries} catalog-misses={bad} location-ranges={ranges} location-single={single}"
    data = {'spans': len(page.spans), 'linked': len(page.linked_spans()), 'anchors_checked': checked, 'anchor_misses': misses, 'catalog_entries': entries, 'catalog_misses': bad, 'bare_only': len(page.bare_only_spans('prose')), 'bare_occurrences': page.bare_occurrences(), 'location_ranges': ranges, 'location_single': single}
    yield from observations(findings, footer, listing, data)

def check(page, inputs):
    yield from struct_keyword_kept(page)
    inputs.require('tree')
    yield from inspect_page(page, inputs)
