"""Checks for [sources.one-version]."""
from report import Finding
RULE = 'sources.one-version'

def one_url_base(page):
    versions = page.versions()
    if len(versions) > 1:
        return [Finding(None, 'FAIL', f'more than one Elixir version on the page: {dict(versions)}')]
    return []

def check(page, inputs):
    yield from one_url_base(page)
