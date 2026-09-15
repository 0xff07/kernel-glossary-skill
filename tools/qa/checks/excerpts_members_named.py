"""Checks for [excerpts.members-named]."""
from report import reading
from report import Row
import re
RULE = 'excerpts.members-named'
MEMBER_LINK_URL = re.compile('\\(https?://[^)]*\\)')
MIN_MEMBERS = 2
HALF = 0.5
MEMBER = re.compile('^\\t[^\\t/*#}].*?\\b(\\w+)\\s*(?:\\[[^\\]]*\\])?\\s*(?::\\s*\\d+)?\\s*;')
ENUM_VALUE = re.compile('^\\t([A-Z][A-Z0-9_]*)\\s*(?:=[^,/]*)?,?\\s*(?:/\\*.*)?$')
STRUCT_OPENER = re.compile('\\b(struct|union) \\w*\\s*\\{|\\bunion\\s*\\{')
ENUM_OPENER = re.compile('\\benum \\w*\\s*\\{')

def members_of(fence):
    found = []
    kind = None
    for line in fence.body:
        if STRUCT_OPENER.search(line):
            kind = 'struct'
        elif ENUM_OPENER.search(line):
            kind = 'enum'
        elif line.startswith('}'):
            kind = None
        match = MEMBER.match(line) if kind == 'struct' else ENUM_VALUE.match(line) if kind == 'enum' else None
        if match and match.group(1) not in found:
            found.append(match.group(1))
    return found

def surrounding_prose(page, fence):
    lines = page.lines
    i = fence.start - 1
    j = i - 1
    while j >= 0 and (not lines[j].strip()):
        j -= 1
    before = ''
    if j >= 0 and (not lines[j].startswith(('```', '#'))):
        k = j
        while k - 1 >= 0 and lines[k - 1].strip() and (not lines[k - 1].startswith('```')):
            k -= 1
        before = ' '.join(lines[k:j + 1])
    table = []
    j = i - 1
    while j >= 0 and (not lines[j].startswith('#')):
        if lines[j].startswith('|'):
            table.append(lines[j])
        j -= 1
    after = []
    k = fence.end
    while k < len(lines) and (not lines[k].startswith(('```', '#', '|', '- ', '* '))):
        after.append(lines[k])
        k += 1
    return MEMBER_LINK_URL.sub('', before + ' ' + ' '.join(table) + ' ' + ' '.join(after))

def members_named_beside_definition(page, inputs):
    rows, notes = ([], [])
    fractions = []
    blocks = zero = 0
    for fence in page.excerpts:
        members = members_of(fence)
        if len(members) < MIN_MEMBERS:
            continue
        prose = surrounding_prose(page, fence)
        named = [m for m in members if re.search('\\b' + re.escape(m) + '\\b', prose)]
        blocks += 1
        fractions.append(len(named) / len(members))
        flags = set()
        if not named:
            zero += 1
            flags.add('none-named')
        elif len(named) / len(members) < HALF:
            notes.append((fence.start, f'definition excerpt names {len(named)} of {len(members)} members'))
        missing = ' '.join((m for m in members if m not in named)) or '-'
        text = f'{fence.start}: {len(named)}/{len(members)} named; unnamed: {missing}'
        if not named:
            text = f'definition excerpt at {fence.start} names none of its {len(members)} members in the prose around it'
        rows.append(Row(fence.start, text, flags))
    mean = sum(fractions) / max(len(fractions), 1)
    footer = f'definition blocks={blocks} zero-named={zero} mean-fraction-named={mean:.2f}'
    yield from reading(rows, notes, footer, {'blocks': blocks, 'zero_named': zero, 'mean_fraction_named': round(mean, 2)}, severity='review')

def check(page, inputs):
    yield from members_named_beside_definition(page, inputs)
