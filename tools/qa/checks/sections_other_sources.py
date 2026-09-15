"""Checks for [sections.other-sources]."""
from report import Finding
from report import observations
import re
from inputs import git
RULE = 'sections.other-sources'
ENTRY = re.compile('^- \\[(.+?) \\(commit ([0-9a-f]{10,})\\)\\]\\((\\S+)\\)\\s*$')
BARE_URL = re.compile('^- https?://')
DOCUMENTATION = 'Documentation/'
EMPTY_EXPLANATION = re.compile('\\b(none|no)\\b', re.I)
MESSAGE_CLIP = 80
SHA_CLIP = 12

def trailers(page, inputs):
    section = page.section('OTHER SOURCES')
    findings = []
    if section is None:
        yield from observations([Finding(None, 'FAIL', 'no OTHER SOURCES section')], '', [], {})
        return
    body = page.lines[section.start:section.end]
    entries = [l for l in body if l.startswith('- [')]
    bare = [l for l in body if BARE_URL.match(l)]
    documentation = sum((l.count(DOCUMENTATION) for l in body))
    for line in bare:
        findings.append(Finding(None, 'FAIL', f'bare URL entry: {line[:MESSAGE_CLIP]}'))
    if documentation:
        findings.append(Finding(None, 'review', f'{documentation} Documentation/ reference(s) in OTHER SOURCES (they belong under DOCUMENTATION)'))
    pending = []
    for entry in entries:
        match = ENTRY.match(entry)
        if not match:
            findings.append(Finding(None, 'FAIL', f'entry not in the `[<subject> (commit <sha>)](<url>)` form: {entry[:MESSAGE_CLIP]}'))
            continue
        pending.append(match.groups())
    if not entries and (not EMPTY_EXPLANATION.search(' '.join(body).strip())):
        findings.append(Finding(None, 'review', 'OTHER SOURCES has no entry and does not say why'))
    yield from findings
    matched = 0
    if pending:
        inputs.require('git')
    for _subject, sha, url in pending:
        if not git(inputs.tree, 'rev-parse', '--verify', '--quiet', sha + '^{commit}', ok=(0, 1)).strip():
            yield Finding(None, 'FAIL', f'{sha[:SHA_CLIP]}: no such commit in the tree')
            continue
        trailers = tuple(git(inputs.tree, 'log', '-1', '--format=%(trailers:key=Link,valueonly)', sha).split())
        if url in trailers:
            matched += 1
            yield Finding(None, 'note', f'{sha[:SHA_CLIP]} Link trailer match: True', {'inventory': True})
        else:
            yield Finding(None, 'FAIL', f"{sha[:SHA_CLIP]}: URL is not one of the commit's Link trailers {list(trailers) or '(none)'}")
    footer = f'other-sources: entries={len(entries)} trailer-matched={matched} bare-urls={len(bare)} documentation-refs={documentation}'
    yield from observations([], footer, [], {'entries': len(entries), 'matched': matched, 'bare_urls': len(bare), 'documentation_refs': documentation})

def check(page, inputs):
    yield from trailers(page, inputs)
