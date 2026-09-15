"""Checks for [excerpts.catalog-parity]."""
from report import Finding
import re
from pagemodel import on_page_pattern
RULE = 'excerpts.catalog-parity'

def catalog_symbols_in_some_fence(page):
    code = page.excerpted_code()
    return [Finding(None, 'FAIL', f'catalog symbol `{key}` appears in no fenced C block on the page') for key in page.catalog_keys if not re.search(on_page_pattern(key), code)]

def check(page, inputs):
    yield from catalog_symbols_in_some_fence(page)
