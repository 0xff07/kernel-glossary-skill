"""Checks for [excerpts.walkthrough]."""
from report import Finding, observations
from walk_utils import describe, owned_functions, pieces_of, walk
RULE = 'excerpts.walkthrough'

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
            at = chain[-1][0].start if chain else (previews[0][0].start if previews else None)
            findings.append(Finding(at, 'FAIL', f'{name}() ({base}:{start}-{end}, {length} lines) is not read whole: lines {describe(missing)} are never shown; add them as pieces in order, each introduced by its stage', {'function': name, 'missing': missing}))
        elif len(chain) == 1 and not previews:
            counts['whole'] += 1
        else:
            counts['walked'] += 1
        if previews:
            counts['previewed'] += 1
            spots = ', '.join(f'page {unit.start} shows {first}-{last}' for unit, first, last in previews)
            findings.append(Finding(previews[0][0].start, 'review', f'{name}() is shown out of order: {spots} before the walk reaches those lines; reorder the pieces, or keep the preview and record why', {'function': name, 'previews': [(u.start, a, b) for u, a, b in previews]}))
        listing.append(f'{name}() {base}:{start}-{end} lines={length} pieces={len(chain)} reshown-lines={again} previews={len(previews)} missing={describe(missing)}')
    footer = (f"functions={counts['functions']} whole={counts['whole']} walked={counts['walked']} incomplete={counts['incomplete']} "
              f"previewed={counts['previewed']} pieces={counts['pieces']} reshown-lines={counts['reshown_lines']}")
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from walkthrough(page, inputs)
