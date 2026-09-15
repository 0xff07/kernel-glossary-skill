"""Checks for [page.one-line-paragraphs]."""
from report import Finding
RULE = 'page.one-line-paragraphs'
CLIP = 60

def paragraphs_unwrapped(page):
    out = []
    for n in range(2, page.counted_lines() + 1):
        if page.is_prose_line(n) and page.is_prose_line(n - 1):
            out.append(Finding(n, 'FAIL', f'paragraph broken over several lines, or two paragraphs with no blank line between: {page.lines[n - 1].strip()[:CLIP]}'))
    return out
SPACES_FOR_TAB = '        '

def tabs_preserved(page):
    out = []
    for fence in page.excerpts:
        for k, line in enumerate(fence.body):
            if line.startswith(SPACES_FOR_TAB):
                out.append(Finding(fence.start + 1 + k, 'review', 'excerpt line indented with spaces where kernel source uses tabs'))
    return out

def check(page, inputs):
    yield from paragraphs_unwrapped(page)
    yield from tabs_preserved(page)
