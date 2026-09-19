"""Checks for [provenance.form]."""
from report import Finding
import re
from pagemodel import ELISION, is_elision
from pagemodel import PROVENANCE
RULE = 'provenance.form'
CLIP = 60

def fence_opens_with(page):
    pattern = re.compile('^/\\* [\\w./-]+:\\d+\\b[^*]*\\*/\\s*$')
    out = []
    for fence in page.excerpts:
        body = [l for l in fence.body if l.strip()]
        if not body:
            out.append(Finding(fence.start, 'FAIL', 'empty C fence'))
        elif not pattern.match(body[0].strip()):
            out.append(Finding(fence.start, 'FAIL', f'C fence does not open with a provenance comment: {body[0][:CLIP]!r}'))
    return out
LOOSE_COMMENT = re.compile('^/\\*.*\\*/\\s*$')
COMMENT_LOCATION = re.compile('[\\w-]+\\.(c|h|S):\\d+')

def provenance_form_in_body(page):
    pattern = re.compile('^/\\* [\\w./-]+:\\d+\\b[^*]*\\*/\\s*$')
    out = []
    for fence in page.excerpts:
        for k, line in enumerate(fence.body):
            text = line.strip()
            if LOOSE_COMMENT.match(text) and COMMENT_LOCATION.search(text) and (not pattern.match(text)):
                out.append(Finding(fence.start + 1 + k, 'FAIL', f'provenance-like comment not in the `/* path:LINE */` form: {text[:CLIP]!r}'))
    return out

def elisions_standalone(page):
    out = []
    for fence in page.excerpts:
        for k, line in enumerate(fence.body):
            text = line.strip()
            if text.startswith(ELISION) and not is_elision(text):
                out.append(Finding(fence.start + 1 + k, 'review', f'an elision marker is a standalone `...` line, bare or as `... /* N lines, to :LINE */`: {text[:40]!r}'))
    return out

def no_provenance_outside_excerpts(page):
    out = []
    for fence in page.fences:
        if fence.kind == 'excerpt':
            continue
        for k, line in enumerate(fence.body):
            if PROVENANCE.match(line.strip()):
                out.append(Finding(fence.start + 1 + k, 'FAIL', 'a non-code fence carries a provenance comment'))
    return out

def check(page, inputs):
    yield from fence_opens_with(page)
    yield from provenance_form_in_body(page)
    yield from elisions_standalone(page)
    yield from no_provenance_outside_excerpts(page)
