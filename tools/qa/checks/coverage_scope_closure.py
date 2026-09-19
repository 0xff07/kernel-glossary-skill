"""Checks for [coverage.scope-closure]."""
from report import Finding
from report import observations
import os
import re
from inputs import git
from inputs import page_within
RULE = 'coverage.scope-closure'
ROW = re.compile('^\\| ([\\w/-]+\\.md) \\| (.*) \\| ([^|]*)\\|$')
ERRATA = re.compile('\\[errata[^\\]]*\\]')
DIR_HEADING = re.compile('^### ([\\w/-]+/)\\s*$')
SPAN = re.compile('`([^`]+)`')
LOCATION = re.compile('^(?:[\\w./-]+\\.[ch])?:\\d+(?:-\\d+)?$|^[\\w./-]+\\.[ch]$')
IDENTIFIER = re.compile('^[A-Za-z_]\\w*(?:(?:->|\\.)[A-Za-z_]\\w*)*$')
LISTED = 80

def spec_path(inputs):
    if inputs.spec:
        return inputs.spec
    top, _within = page_within(inputs.page_path, inputs.base)
    if top is None:
        return None
    path = os.path.join(inputs.base, 'campaigns', top + '.md')
    return path if os.path.exists(path) else None

def catalog_row(spec, within):
    directory = os.path.dirname(within)
    directory = directory + '/' if directory else ''
    name = os.path.basename(within)
    current = ''
    for line in open(spec, encoding='utf-8'):
        found = DIR_HEADING.match(line)
        if found:
            current = found.group(1)
            continue
        found = ROW.match(line.rstrip('\n'))
        if found and (found.group(1) == within or (found.group(1) == name and current == directory)):
            return found.group(2)
    return None

def normalize(span):
    text = span.strip()
    for prefix in ('struct ', 'enum ', 'union '):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text.rstrip('()').strip()

def spans_of(scope):
    out = []
    for span in SPAN.findall(ERRATA.sub('', scope)):
        symbol = normalize(span)
        if symbol and (not LOCATION.match(symbol)) and IDENTIFIER.match(symbol):
            out.append(symbol)
    return out

def expansions(symbol, previous):
    if not previous:
        return []
    segments = previous.split('_')
    if symbol.startswith('_') and symbol.endswith('_') and (len(symbol) > 2):
        inner = symbol.strip('_')
        return ['_'.join(segments[:k] + [inner] + segments[k:]) for k in range(1, len(segments))]
    joiner = '' if symbol.startswith('_') else '_'
    return ['_'.join(segments[:k]) + joiner + symbol for k in range(len(segments), 0, -1)]

class TreeOracle:

    def __init__(self, tree, dirs, names):
        self.tree, self.dirs, self.known = (tree, dirs, {})
        if names:
            pattern = '|'.join((re.escape(n) for n in sorted(names)))
            found = set(git(tree, 'grep', '-h', '-o', '-w', '-E', pattern, '--', *dirs, ok=(0, 1)).split())
            for name in names:
                self.known[name] = name in found

    def __call__(self, name):
        if name not in self.known:
            self.known[name] = bool(git(self.tree, 'grep', '-l', '-w', '-F', name, '--', *self.dirs, ok=(0, 1)).strip())
        return self.known[name]

    def family(self, name):
        key = name + '_*'
        if key not in self.known:
            self.known[key] = bool(git(self.tree, 'grep', '-l', '-E', '\\b' + re.escape(name) + '_[A-Za-z0-9]', '--', *self.dirs, ok=(0, 1)).strip())
        return self.known[key]

def named_on(text, symbol, families=frozenset()):
    tail = '(?:_\\w+)?' if symbol in families else ''
    return re.search('(?<![\\w])' + re.escape(symbol) + tail + '(?![\\w])', text) is not None

def inspect_page(page, inputs):
    spec = spec_path(inputs)
    _top, within = page_within(inputs.page_path, inputs.base)
    if spec is None:
        yield from observations([], "scope: row=absent (no campaign spec for this page's directory)", [], {}, optional="no campaign spec for this page's directory: the scope closure is read by hand")
        return
    scope = catalog_row(spec, within)
    if scope is None:
        yield from observations([], 'scope: row=absent', [], {'spec': spec}, optional=f'no catalog row for {within} in {os.path.relpath(spec, inputs.base)}: the scope closure is read by hand')
        return
    inputs.require('git')
    text = page.raw
    dirs = sorted({os.path.dirname(f) for f in page.cited_files() if os.path.dirname(f)}) or ['.']
    oracle = TreeOracle(inputs.tree, dirs, set(spans_of(scope)))
    symbols, unresolved, families = ([], [], set())
    for symbol in spans_of(scope):
        if not oracle(symbol) and symbols:
            for candidate in expansions(symbol, symbols[-1]):
                if oracle(candidate):
                    symbol = candidate
                    break
                if oracle.family(candidate):
                    symbol = candidate
                    families.add(candidate)
                    break
            else:
                unresolved.append(symbol)
        if symbol not in symbols:
            symbols.append(symbol)
    completeness = inputs.worksheet_section('## COMPLETENESS')
    findings, listing = ([], [])
    counts = {'named': 0, 'absent': 0, 'accounted': 0}
    for symbol in symbols:
        if named_on(text, symbol, families):
            counts['named'] += 1
            listing.append(f'named: {symbol}' + (' (family)' if symbol in families else ''))
        elif symbol in completeness:
            counts['accounted'] += 1
            listing.append(f'accounted in COMPLETENESS, not on the page: {symbol}')
            findings.append(Finding(None, 'note', f"scoped symbol `{symbol}` is absent from the page and accounted for in the worksheet's COMPLETENESS section; read the reason"))
        else:
            counts['absent'] += 1
            listing.append(f'absent: {symbol}')
            findings.append(Finding(None, 'review', f'scoped symbol `{symbol}` is never named on the page (scope closure: cover it, or record the scope reduction and its reason above COMPLETENESS)'))
    for symbol in unresolved:
        findings.append(Finding(None, 'review', f'scoped span `{symbol}` resolves to no name in the tree under any expansion; read the catalog row'))
    footer = f"scope: row=found symbols={len(symbols)} named={counts['named']} absent={counts['absent']} accounted={counts['accounted']} unresolved={len(unresolved)} resolved-against=tree"
    yield from observations(findings, footer, listing[:LISTED], {'symbols': symbols[:LISTED], 'unresolved': unresolved, 'families': sorted(families), 'counts': counts})

def check(page, inputs):
    yield from inspect_page(page, inputs)
