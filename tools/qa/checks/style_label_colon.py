"""Checks for [style.label-colon]."""
from report import Finding
from patterns import find_pattern
import re
RULE = 'style.label-colon'
CLIP = 60

def paragraph_final_colon(page):
    out = []
    lines = page.lines
    for n in range(1, page.counted_lines() + 1):
        if not page.is_prose_line(n) or not lines[n - 1].rstrip().endswith(':'):
            continue
        k = n
        while k < len(lines) and (not lines[k].strip()):
            k += 1
        following = lines[k] if k < len(lines) else ''
        if not following.startswith('```'):
            tail = re.sub('\\[([^\\]]*)\\]\\([^)]*\\)', '\\1', lines[n - 1]).strip()[-CLIP:]
            out.append(Finding(n, 'review', f'paragraph-final colon: no fenced excerpt follows …{tail}'))
    return out

def check(page, inputs):
    yield from find_pattern(page, '[^:;.!?]{3,90}:\\s+[A-Za-z0-9§]', view='prose', region=['prose', 'section6'], not_in_cells=True, name='label colon', severity='review', flags=2)
    yield from paragraph_final_colon(page)
