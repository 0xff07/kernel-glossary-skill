"""Checks for [style.lists]."""
from pagemodel import ITEM
from report import Finding
RULE = 'style.lists'
BANNED = ('DETAILS', 'SUMMARY')


def lists_under(page, name):
    """The first page line of every list under the H2 section `name`: an item line outside a
    fence, or an indented continuation of one."""
    section = page.section(name)
    if section is None:
        return
    previous = False
    for n in range(section.start + 1, section.end + 1):
        line = page.lines[n - 1]
        in_list = page.region_of(n) == 'prose' and (bool(ITEM.match(line)) or (previous and line[:1] in (' ', '\t') and bool(line.strip())))
        if in_list and not previous:
            yield n
        previous = in_list


def check(page, inputs):
    for name in BANNED:
        for n in lists_under(page, name):
            yield Finding(n, 'FAIL', f'a list under {name}: fold the items into one flowing paragraph or a table')
