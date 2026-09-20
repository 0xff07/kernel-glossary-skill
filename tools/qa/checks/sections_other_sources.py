"""Checks for [sections.other-sources]."""
from report import Finding
from report import observations
import re
from inputs import git
from pagemodel import Page
RULE = 'sections.other-sources'
BLOCK = re.compile('^### Added by (.+?)\\s*$')
ENTRY = re.compile('^- \\[(.+?) \\(commit ([0-9a-f]{10,})\\)\\]\\((\\S+)\\)\\s*$')
DOCUMENTATION = 'Documentation/'
EMPTY_EXPLANATION = re.compile('\\b(none|no)\\b', re.I)
MESSAGE_CLIP = 80
SHA_CLIP = 12


def split(lines):
    """(the reader's lines, [(model, lines)]) of an OTHER SOURCES body: a block is a `### Added by <model>`
    heading with the lines under it up to the next `###` heading; everything else is the reader's."""
    readers, blocks, current = [], [], None
    for line in lines:
        match = BLOCK.match(line)
        if match:
            current = (match.group(1), [])
            blocks.append(current)
            continue
        if line.startswith('### '):
            current = None
        if current is not None:
            current[1].append(line)
        else:
            readers.append(line)
    return readers, blocks


def section_body(page):
    section = page.section('OTHER SOURCES')
    return None if section is None else page.lines[section.start:section.end]


def trailers(page, inputs):
    """The entries under the model blocks are verified against their Link trailers; the reader's lines,
    everything outside those blocks, are listed and never read, and once the committed page carries a
    block, each of its reader lines must still be on the page."""
    body = section_body(page)
    if body is None:
        yield from observations([Finding(None, 'FAIL', 'no OTHER SOURCES section')], '', [], {})
        return
    readers, blocks = split(body)
    findings, commits = [], []
    for model, lines in blocks:
        bullets = [l for l in lines if l.startswith('- ')]
        for line in bullets:
            match = ENTRY.match(line)
            if match:
                commits.append(match.groups())
            else:
                findings.append(Finding(None, 'FAIL', f"an entry of the block added by {model} is not a commit entry `[<subject> (commit <sha>)](<url>)`: {line[:MESSAGE_CLIP]}"))
        if not bullets and not EMPTY_EXPLANATION.search(' '.join(lines).strip()):
            findings.append(Finding(None, 'review', f'the block added by {model} has no entry and does not say why'))
    documentation = sum((l.count(DOCUMENTATION) for l in body))
    if documentation:
        findings.append(Finding(None, 'review', f'{documentation} Documentation/ reference(s) in OTHER SOURCES (they belong under DOCUMENTATION)'))
    reader_lines = [l for l in readers if l.strip()]
    kept = lost = 0
    baseline = inputs.baseline if inputs is not None else None
    if baseline is not None:
        old_body = section_body(Page(page.path, baseline))
        if old_body is not None:
            old_readers, old_blocks = split(old_body)
            if old_blocks:
                present = set(l for l in body)
                for line in (l for l in old_readers if l.strip()):
                    if line in present:
                        kept += 1
                    else:
                        lost += 1
                        findings.append(Finding(None, 'FAIL', f"a line of the reader's shelf in the committed page is gone or changed: {line[:MESSAGE_CLIP]}"))
    yield from findings
    matched = 0
    if commits:
        inputs.require('git')
    for _subject, sha, url in commits:
        if not git(inputs.tree, 'rev-parse', '--verify', '--quiet', sha + '^{commit}', ok=(0, 1)).strip():
            yield Finding(None, 'FAIL', f'{sha[:SHA_CLIP]}: no such commit in the tree')
            continue
        trailers = tuple(git(inputs.tree, 'log', '-1', '--format=%(trailers:key=Link,valueonly)', sha).split())
        if url in trailers:
            matched += 1
            yield Finding(None, 'note', f'{sha[:SHA_CLIP]} Link trailer match: True', {'inventory': True})
        else:
            yield Finding(None, 'FAIL', f"{sha[:SHA_CLIP]}: URL is not one of the commit's Link trailers {list(trailers) or '(none)'}")
    rows = [f"reader line, left as it is: {line[:MESSAGE_CLIP]}" for line in reader_lines]
    footer = f'other-sources: blocks={len(blocks)} commit-entries={len(commits)} trailer-matched={matched} reader-lines={len(reader_lines)} kept={kept} lost={lost} documentation-refs={documentation}'
    yield from observations([], footer, rows, {'blocks': len(blocks), 'commit_entries': len(commits), 'matched': matched, 'reader_lines': len(reader_lines), 'kept': kept, 'lost': lost, 'documentation_refs': documentation})


def check(page, inputs):
    yield from trailers(page, inputs)
