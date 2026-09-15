"""Checks for [coverage.recency]."""
from report import Finding
from report import observations
import datetime
from inputs import git
from pagemodel import ELIXIR
RULE = 'coverage.recency'
YEARS = 3
DAYS_PER_YEAR = 365.25
DRIVER_PREFIX = 'drivers/'
BUILD_FILES = ('Kconfig', 'Makefile')

def years_between(head, date):
    try:
        return (datetime.date.fromisoformat(head) - datetime.date.fromisoformat(date)).days / DAYS_PER_YEAR
    except ValueError:
        return None

def drivers(page, inputs):
    head = git(inputs.tree, 'log', '-1', '--format=%cs', 'HEAD').strip()
    findings, listing = ([], [])
    if years_between(head, head) is None:
        yield from observations([Finding(None, 'FAIL', "the tree's HEAD date is unreadable")], '', [], {})
        return
    files = sorted({m.group(2) for m in ELIXIR.finditer(page.raw) if m.group(2).startswith(DRIVER_PREFIX) and m.group(2).split('/')[-1] not in BUILD_FILES})
    old = 0
    for path in files:
        date = git(inputs.tree, 'log', '-1', '--format=%cs', '--', path).strip()
        age = years_between(head, date)
        if age is None:
            findings.append(Finding(None, 'note', f'{path}: no commit date'))
            continue
        listing.append(f'{date} {path}')
        if age > YEARS:
            old += 1
            findings.append(Finding(None, 'review', f'{path}: newest commit {date}, more than {YEARS} years before HEAD ({head})'))
    footer = f'cited files={len(files)} older-than-{YEARS}y={old} (HEAD {head})'
    yield from observations(findings, footer, listing, {'files': len(files), 'older_than_years': old, 'head': head})

def check(page, inputs):
    inputs.require('git')
    yield from drivers(page, inputs)
