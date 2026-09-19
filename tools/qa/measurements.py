"""Measurement units, thresholds and consecutive runs over the shared page model."""
from inputs import source_lines
from pagemodel import is_elision
from report import Finding
from report import observations

def positions_of(unit, source):
    """The 1-based source line of every reproduced line of a verbatim unit, None for an elision
    marker; None for the whole unit when it does not match the file, which [excerpts.verbatim]
    reports. After an elision a line resynchronises on its first later occurrence, a column-0
    closing brace included."""
    out = []
    pos = unit.line - 1
    after = False
    for line in unit.lines:
        if is_elision(line):
            out.append(None)
            after = True
            continue
        if after:
            q = next((k for k in range(pos, len(source)) if source[k] == line), None)
            if q is None:
                return None
            pos = q
        elif pos >= len(source) or source[pos] != line:
            return None
        out.append(pos + 1)
        pos += 1
        after = False
    return out

def reproduced_lines(page, inputs=None):
    """Per tree path, the source lines the page's excerpt units reproduce. With a tree the lines
    are mapped through each unit's elisions; without one a unit counts as contiguous from its
    provenance line."""
    out = {}
    tree = getattr(inputs, 'tree', None) if inputs is not None else None
    for unit in page.units:
        if not unit.path:
            continue
        lines = None
        source = source_lines(tree, unit.path, inputs.cache) if tree else None
        if source is not None:
            mapped = positions_of(unit, source)
            if mapped is not None:
                lines = {p for p in mapped if p}
        if lines is None:
            lines = set(range(unit.line, unit.line + len(unit.lines)))
        out.setdefault(unit.path, set()).update(lines)
    return out

def cited_lines(first, last=None):
    """The source lines a location link cites: one line, or every line of a first-last range."""
    first = int(first)
    last = int(last) if last else first
    return set(range(first, last + 1))

def paragraph_units(page):
    """Every DETAILS paragraph with its sequence number in the block order, so a run of paragraphs
    breaks where another block or a subsection boundary stands between them."""
    out = []
    seq = 0
    for sub in page.subsections:
        seq += 2
        for block in sub['blocks']:
            seq += 1
            if block.kind == 'P':
                out.append({'line': block.line, 'words': block.size, 'sentences': block.stats[1], 'label': f'P@{block.line}', 'sub': sub, 'lengths': block.stats[2], 'seq': seq})
    return out

def units_of(page, unit, measure, where=None):
    """[{line, label, <measure>: value, ...}] for the rule's unit, in page order."""
    if unit == 'paragraph':
        return paragraph_units(page)
    if unit == 'sentence':
        out = []
        seq = 0
        last_sub = None
        for p in paragraph_units(page):
            if p['sub'] is not last_sub:
                seq += 2
                last_sub = p['sub']
            for k, length in enumerate(p['lengths'], 1):
                seq += 1
                out.append({'line': p['line'], 'words': length, 'label': f"sentence {k} of P@{p['line']}", 'seq': seq})
        return out
    if unit == 'prose-run':
        out = []
        for sub in page.subsections:
            run = []
            for block in sub['blocks'] + [None]:
                if block is not None and block.kind == 'P':
                    run.append(block)
                    continue
                if run:
                    out.append({'line': run[0].line, 'paragraphs': len(run), 'label': f'prose run from P@{run[0].line}'})
                run = []
        return out
    if unit == 'subsection':
        out = []
        for sub in page.subsections:
            if where == 'without-block' and sub['dense']:
                continue
            if where == 'with-block' and (not sub['dense']):
                continue
            out.append({'line': sub['line'], 'words': sub['words'], 'paragraphs': len(sub['paragraphs']), 'label': f"[{sub['title'][:40]}]"})
        return out
    if unit == 'excerpt':
        return [{'line': b.line, 'source-lines': b.size, 'label': f'C@{b.line} ({b.label})'} for sub in page.subsections for b in sub['blocks'] if b.kind == 'C']
    if unit == 'figure':
        return [{'line': b.line, 'visible-lines': b.size, 'label': f'D@{b.line} ({b.label})'} for sub in page.subsections for b in sub['blocks'] if b.kind == 'D']
    if unit == 'heading':
        return [{'line': sub['line'], 'words': len(sub['title'].split()), 'label': f"heading [{sub['title'][:40]}]"} for sub in page.subsections]
    if unit == 'lead':
        blocks = page.lead_blocks()
        return section_units('lead', blocks, 1, measure)
    if unit == 'summary':
        blocks = page.summary_blocks()
        section = page.section('SUMMARY')
        if blocks is None:
            return []
        dense = sum((1 for k, _v in blocks if k in ('T', 'D')))
        if where == 'with-block' and (not dense):
            return []
        if where == 'without-block' and dense:
            return []
        return section_units('SUMMARY', blocks, section.start, measure)
    return []

def section_units(name, blocks, line, measure):
    """The lead or the SUMMARY as one unit (words, sentences, paragraphs) or one unit per figure
    or table, by the rule's measure."""
    from pagemodel import sentences_of, word_count
    paragraphs = [v for k, v in blocks if k == 'P']
    if measure == 'figure-lines':
        return [{'line': line, 'figure-lines': v, 'label': f'{name} figure'} for k, v in blocks if k == 'D']
    if measure == 'table-rows':
        return [{'line': line, 'table-rows': v[0], 'label': f'{name} table'} for k, v in blocks if k == 'T' and isinstance(v, tuple)]
    if measure == 'table-columns':
        return [{'line': line, 'table-columns': v[1], 'label': f'{name} table'} for k, v in blocks if k == 'T' and isinstance(v, tuple)]
    words = sum((word_count(p) for p in paragraphs))
    count = sum((len(sentences_of(p)) for p in paragraphs))
    return [{'line': line, 'words': words, 'sentences': count, 'paragraphs': len(paragraphs), 'label': name}]

def breach_of(value, *, fail=None, review=None, review_below=None, normal=None, note_below=False):
    """(severity, threshold text) for one value, or None."""
    below = review_below
    if fail is not None and value > fail:
        return ('FAIL', f'over {fail}')
    if review is not None and value > review:
        return ('review', f'over {review}')
    if below is not None and value < below:
        return ('review', f'under {below}')
    if normal is not None and value > normal[1]:
        return ('note', f'over the normal {normal[0]}-{normal[1]}')
    if normal is not None and value < normal[0] and note_below:
        return ('note', f'under the normal {normal[0]}-{normal[1]}')
    return None

def measure(page, unit_kind, measure, *, name, normal=None, review=None, fail=None, review_below=None, run=1, where=None, note_below=False):
    units = units_of(page, unit_kind, measure, where)
    length = int(run or 1)
    findings = []
    listing = []
    counts = {'FAIL': 0, 'review': 0, 'note': 0}
    if length == 1:
        for unit in units:
            breach = breach_of(unit[measure], fail=fail, review=review, review_below=review_below, normal=normal, note_below=note_below)
            if breach:
                severity, threshold = breach
                findings.append(Finding(unit['line'], severity, f"{unit['label']} {measure}={unit[measure]}, {threshold} ({name})"))
                counts[severity] += 1
    run = []
    for unit in units + [None] if length > 1 else []:
        breach = breach_of(unit[measure], fail=fail, review=review, review_below=review_below, normal=normal, note_below=note_below) if unit is not None else None
        adjacent = unit is not None and (not run or 'seq' not in unit or unit['seq'] == run[-1][0].get('seq', unit['seq'] - 1) + 1)
        if breach and adjacent and (not run or run[0][1][0] == breach[0]):
            run.append((unit, breach))
            continue
        if len(run) >= length:
            first, (severity, threshold) = run[0]
            message = f"{length} consecutive {unit_kind}s from {first['label']} with {measure} {threshold}: {', '.join((str(u[measure]) for u, _b in run[:length]))} ({name})"
            findings.append(Finding(first['line'], severity, message))
            counts[severity] += 1
        run = [(unit, breach)] if breach else []
    for unit in units:
        listing.append(f"{unit['line']}: {unit['label']} {measure}={unit[measure]}")
    footer = f"{unit_kind}s={len(units)} {measure}-fail={counts['FAIL']} {measure}-review={counts['review']} {measure}-note={counts['note']}"
    yield from observations(findings, footer, listing, {'units': len(units), 'counts': counts, 'values': [u[measure] for u in units]})
