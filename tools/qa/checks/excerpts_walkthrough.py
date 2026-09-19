"""Checks for [excerpts.walkthrough]."""
from constructs import constructs_of, construct_at
from inputs import source_lines
from measurements import positions_of
from report import Finding, observations
RULE = 'excerpts.walkthrough'
SOURCE_SUFFIXES = ('.c', '.h', '.S')

def owned_functions(page, inputs, tables):
    """[(name, path, start, end)] for every catalog entry whose anchor lies in a function
    definition, in catalog order, each function once."""
    out, seen = [], set()
    for _key, path, line, _n in page.catalog_entries:
        if not path or not line or not path.endswith(SOURCE_SUFFIXES):
            continue
        source = source_lines(inputs.tree, path, inputs.cache)
        if source is None:
            continue
        if path not in tables:
            tables[path] = constructs_of(source)
        construct = construct_at(tables[path], line)
        if construct is None or construct.kind != 'function' or (path, construct.start) in seen:
            continue
        seen.add((path, construct.start))
        out.append((construct.name, path, construct.start, construct.end))
    return out

def ranges_of(lines):
    """[(first, last)] over a sorted iterable of line numbers."""
    out = []
    for n in sorted(lines):
        if out and n == out[-1][1] + 1:
            out[-1] = (out[-1][0], n)
        else:
            out.append((n, n))
    return out

def pieces_of(page, inputs, path, start, end):
    """[(page line, first, last)] for every contiguous run of the function's lines a unit
    reproduces, in page order."""
    out = []
    source = source_lines(inputs.tree, path, inputs.cache)
    for unit in page.units:
        if unit.path != path:
            continue
        positions = positions_of(unit, source)
        if positions is None:
            continue
        for first, last in ranges_of(p for p in positions if p and start <= p <= end):
            out.append((unit.start, first, last))
    return out

def walk(pieces, start, end):
    """(chain, reshown, previews, missing): the pieces that continue the walk from the signature,
    the pieces whose every line was shown before, the pieces shown before the walk reached them,
    and the ranges of the function never shown."""
    shown = set()
    chain, reshown, previews = [], [], []
    expected = start
    for line, first, last in pieces:
        span = set(range(first, last + 1))
        if first == expected:
            chain.append((line, first, last))
            expected = last + 1
            while expected in shown:
                expected += 1
        elif span <= shown:
            reshown.append((line, first, last))
        else:
            previews.append((line, first, last))
        shown |= span
    missing = ranges_of(set(range(start, end + 1)) - shown)
    return chain, reshown, previews, missing

def describe(ranges):
    return ', '.join(f'{a}-{b}' if a != b else str(a) for a, b in ranges) or '-'

def walkthrough(page, inputs):
    findings, listing = [], []
    counts = {'functions': 0, 'whole': 0, 'walked': 0, 'incomplete': 0, 'previewed': 0, 'pieces': 0, 'reshown_lines': 0}
    tables = {}
    for name, path, start, end in owned_functions(page, inputs, tables):
        counts['functions'] += 1
        base = path.rsplit('/', 1)[-1]
        length = end - start + 1
        chain, reshown, previews, missing = walk(pieces_of(page, inputs, path, start, end), start, end)
        counts['pieces'] += len(chain)
        again = sum(last - first + 1 for _l, first, last in reshown)
        counts['reshown_lines'] += again
        if missing:
            counts['incomplete'] += 1
            at = chain[-1][0] if chain else (previews[0][0] if previews else None)
            findings.append(Finding(at, 'FAIL', f'{name}() ({base}:{start}-{end}, {length} lines) is not read whole: lines {describe(missing)} are never shown; add them as pieces in order, each introduced by its stage', {'function': name, 'missing': missing}))
        elif len(chain) == 1 and not previews:
            counts['whole'] += 1
        else:
            counts['walked'] += 1
        if previews:
            counts['previewed'] += 1
            spots = ', '.join(f'page {line} shows {first}-{last}' for line, first, last in previews)
            findings.append(Finding(previews[0][0], 'review', f'{name}() is shown out of order: {spots} before the walk reaches those lines; reorder the pieces, or keep the preview and record why', {'function': name, 'previews': previews}))
        listing.append(f'{name}() {base}:{start}-{end} lines={length} pieces={len(chain)} reshown-lines={again} previews={len(previews)} missing={describe(missing)}')
    footer = (f"functions={counts['functions']} whole={counts['whole']} walked={counts['walked']} incomplete={counts['incomplete']} "
              f"previewed={counts['previewed']} pieces={counts['pieces']} reshown-lines={counts['reshown_lines']}")
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from walkthrough(page, inputs)
