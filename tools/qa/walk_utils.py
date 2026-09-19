"""The pieces a page shows of an owned function: which catalog entries are functions, which
units reproduce their lines, and how the pieces chain from the signature to the closing brace."""
from constructs import constructs_of, construct_at
from inputs import source_lines
from measurements import positions_of
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
    """[(unit, first, last)] for every contiguous run of the function's lines a unit reproduces,
    in page order."""
    out = []
    source = source_lines(inputs.tree, path, inputs.cache)
    for unit in page.units:
        if unit.path != path:
            continue
        positions = positions_of(unit, source)
        if positions is None:
            continue
        for first, last in ranges_of(p for p in positions if p and start <= p <= end):
            out.append((unit, first, last))
    return out


def walk(pieces, start, end):
    """(chain, reshown, previews, missing): the pieces that continue the walk from the signature,
    the pieces whose every line was shown before, the pieces shown before the walk reached them,
    and the ranges of the function never shown."""
    shown = set()
    chain, reshown, previews = [], [], []
    expected = start
    for unit, first, last in pieces:
        span = set(range(first, last + 1))
        if first == expected:
            chain.append((unit, first, last))
            expected = last + 1
            while expected in shown:
                expected += 1
        elif span <= shown:
            reshown.append((unit, first, last))
        else:
            previews.append((unit, first, last))
        shown |= span
    missing = ranges_of(set(range(start, end + 1)) - shown)
    return chain, reshown, previews, missing


def describe(ranges):
    return ', '.join(f'{a}-{b}' if a != b else str(a) for a, b in ranges) or '-'
