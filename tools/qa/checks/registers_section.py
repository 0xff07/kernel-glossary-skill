"""Checks for [registers.section]."""
import re
from report import Row, reading
RULE = 'registers.section'
REGISTER_LINK = re.compile(r'\]\(https://elixir\.bootlin\.com/linux/[^/]+/source/[^#)]*regs\.h#L\d+\)')
LINK_URL = re.compile(r'\]\([^)]*\)')
CLIP = 90

def registers(page, inputs):
    sec = page.section('REGISTERS')
    if sec is None:
        yield from reading([], [], 'no REGISTERS section', {'tables': 0, 'register_links': 0, 'figures': 0})
        return
    lines = [(n, page.lines[n - 1]) for n in range(sec.start, min(sec.end, len(page.lines)) + 1)]
    figures = sum(1 for f in page.figures if sec.start <= f.start <= sec.end)
    rows, tables, register_links, in_fence, i = [], 0, 0, False, 0
    while i < len(lines):
        n, line = lines[i]
        if line.startswith('```'):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        register_links += len(REGISTER_LINK.findall(line))
        if line.startswith('|'):
            j = i
            while j < len(lines) and lines[j][1].startswith('|'):
                register_links += len(REGISTER_LINK.findall(lines[j][1])) if j > i else 0
                j += 1
            tables += 1
            head = LINK_URL.sub(']', line)[:CLIP]
            rows.append(Row(n, f'table of {max(j - i - 2, 0)} rows under REGISTERS ({head}); the section draws its registers, bitfields and fields, and the helpers belong to COVERAGE and to DETAILS at their stage', set()))
            i = j
            continue
        i += 1
    if register_links and not figures:
        rows.append(Row(sec.start, f'REGISTERS links {register_links} register definitions and draws none; draw the registers, bitfields and fields the page touches ([registers.styles])', set()))
    footer = f'tables={tables} register-links={register_links} figures={figures}'
    yield from reading(rows, [], footer, {'tables': tables, 'register_links': register_links, 'figures': figures}, severity='review')

def check(page, inputs):
    yield from registers(page, inputs)
