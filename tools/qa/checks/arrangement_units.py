"""Checks for [arrangement.units]."""
from report import reading
from report import Row
import collections
from pagemodel import DENSE
import re
RULE = 'arrangement.units'
NOTED_BRIDGE_SENTENCES = 1
NOTED_REPEAT = 3
FINDING_CLIP = 40

def block_measure(kind):
    return {'C': 'source lines', 'D': 'visible lines', 'T': 'rows', 'Q': 'lines', 'H': 'words'}.get(kind, 'items')

def block_map(page, inputs):
    rows, notes = ([], [])
    maps = []
    measures = []
    entries = []
    prose_words = 0
    for sub in page.subsections:
        blocks = sub['blocks']
        rows.append(Row(sub['line'], f"{sub['line']} [{sub['title'][:52]}] map={sub['map']} words={sub['words']} paras={len(sub['paragraphs'])} blocks={sub['dense']}", set()))
        for block in blocks:
            if block.kind == 'P':
                longest = max(block.stats[2]) if block.stats[2] else 0
                rows.append(Row(block.line, f'    P@{block.line:<6} sentences={block.stats[1]:<3} words={block.size:<4} longest={longest}', set()))
            else:
                label = f'{block.label} {block.text}'.rstrip() if block.kind == 'C' else block.label
                rows.append(Row(block.line, f'    {block.kind}@{block.line:<6} {block_measure(block.kind)}={block.size:<4} {label}', set()))
            if block.kind in DENSE:
                entries.append({'kind': block.kind, 'line': block.line, 'size': block.size, 'label': block.label, 'construct': block.text if block.kind == 'C' else ''})
        for before, middle, after in zip(blocks, blocks[1:], blocks[2:]):
            if before.kind in DENSE and after.kind in DENSE and (middle.kind == 'P') and (middle.stats[1] <= NOTED_BRIDGE_SENTENCES):
                notes.append((middle.line, f'''[{sub['title'][:FINDING_CLIP]}] {before.kind}@{before.line} -> P@{middle.line} ({middle.stats[1]} sentence) -> {after.kind}@{after.line} one-sentence bridge, read for the work it does: "{middle.text}"'''))
        for block in blocks:
            if block.kind == 'Q':
                notes.append((block.line, f"[{sub['title'][:FINDING_CLIP]}] Q@{block.line} {block.size} lines, neither source nor figure ({block.label}); confirm it is a quotation or listing"))
        maps.append(sub['map'])
        measures.append({'figures': sub['figures'], 'others': sub['kinds'].count('Q'), 'words': sub['words'], 'source': sub['source']})
        prose_words += sub['words']
    worst = run_length = 1
    for before, after in zip(maps, maps[1:]):
        run_length = run_length + 1 if before == after else 1
        worst = max(worst, run_length)
    if worst >= NOTED_REPEAT:
        for i in range(len(maps) - worst + 1):
            if len(set(maps[i:i + worst])) == 1:
                named = '; '.join((page.subsections[k]['title'][:FINDING_CLIP] for k in range(i, i + worst)))
                notes.append((None, f'one block map repeats {worst} times in a row (read for whether each repeats the same explanation): {named}'))
                break
    counts = collections.Counter((e['kind'] for e in entries))
    notes.insert(0, (None, f"inventory: structured blocks={len(entries)} excerpts={counts['C']} figures={counts['D']} tables={counts['T']} other fences={counts['Q']} prose words under DETAILS={prose_words}"))
    footer = f"subsections={len(page.subsections)} distinct-maps={len(set(maps))} longest-repeat={worst} figures={sum((m['figures'] for m in measures))} other-fences={sum((m['others'] for m in measures))}"
    yield from reading(rows, notes, footer, {'subsections': len(page.subsections), 'maps': maps, 'inventory': entries, 'prose_words': prose_words}, severity='note')
LABEL_LOCATION = re.compile('^([\\w./-]+):(\\d+)')

def inventory_of(page):
    """Every structured block of the page with its label, size and H2 section."""
    out = []
    numbered = [(i + 1, line) for i, line in enumerate(page.lines)]
    for block in page.blocks_of(numbered):
        if block.kind in DENSE:
            size = len(block.stats.get('body', [])) if block.kind == 'C' else block.size
            out.append((block.kind, block.label, block.line, size, page.section_of(block.line).name))
    return out

def baseline_inventory(page, inputs):
    from pagemodel import Page
    if inputs is None or inputs.baseline is None:
        yield from reading([], [], 'no committed baseline', {}, severity='note')
        return
    baseline = Page(page.path, inputs.baseline)
    now, before = (inventory_of(page), inventory_of(baseline))

    def by_label(blocks):
        groups = {}
        for block in blocks:
            groups.setdefault((block[0], block[1]), []).append(block)
        return groups
    now_groups, before_groups = (by_label(now), by_label(before))
    added, removed, moved = ([], [], [])
    for key, blocks_now in now_groups.items():
        blocks_before = before_groups.get(key, [])
        paired = min(len(blocks_now), len(blocks_before))
        added.extend(blocks_now[paired:])
        moved.extend(((n, o) for n, o in zip(blocks_now[:paired], blocks_before[:paired]) if n[4] != o[4]))
    for key, blocks_before in before_groups.items():
        paired = min(len(now_groups.get(key, [])), len(blocks_before))
        removed.extend(blocks_before[paired:])

    def is_split_of(new, old):
        if old[0] != 'C' or new[0] != 'C':
            return False
        a, b = (LABEL_LOCATION.match(new[1]), LABEL_LOCATION.match(old[1]))
        if not a or not b or a.group(1) != b.group(1):
            return False
        return int(b.group(2)) < int(a.group(2)) <= int(b.group(2)) + old[3] + 2
    notes = []
    for block in sorted(added, key=lambda b: b[2]):
        note = next((f' (a split of the baseline unit {o[1]})' for o in before if is_split_of(block, o)), '') if block[0] == 'C' else ''
        notes.append((block[2], f'structured block added against the baseline: {block[0]} {block[1]}{note}'))
    for block in sorted(removed, key=lambda b: b[2]):
        notes.append((None, f'structured block removed against the baseline: {block[0]} {block[1]} (was at baseline line {block[2]})'))
    for new, old in sorted(moved, key=lambda p: p[0][2]):
        notes.append((new[2], f'structured block moved against the baseline: {new[0]} {new[1]} from {old[4]} to {new[4]}'))
    shapes_now = {s['title']: s for s in page.subsections}
    shapes_before = {s['title']: s for s in baseline.subsections}
    changed = 0
    for title, after in shapes_now.items():
        was = shapes_before.get(title)
        if was is None:
            continue
        parts = [f'{label} {was[f]} -> {after[f]}' for f, label in (('map', 'map'), ('words', 'words'), ('dense', 'blocks')) if was[f] != after[f]]
        if len(was['paragraphs']) != len(after['paragraphs']):
            parts.append(f"paragraphs {len(was['paragraphs'])} -> {len(after['paragraphs'])}")
        if parts:
            changed += 1
            notes.append((after['line'], f"subsection changed against the baseline: [{title[:FINDING_CLIP]}] {', '.join(parts)}"))
    carried = len(set(shapes_now) & set(shapes_before))
    footer = f'inventory against the baseline: before={len(before)} after={len(now)} added={len(added)} removed={len(removed)} moved={len(moved)}; subsections carried={carried} changed={changed} new={len(shapes_now) - carried} gone={len(shapes_before) - carried}'
    yield from reading([], notes, footer, {'added': len(added), 'removed': len(removed), 'moved': len(moved), 'changed': changed}, severity='note')

def reuse(page, inputs):
    from report import reuse_lines
    lines = reuse_lines(page.raw, inputs.baseline if inputs is not None else None)
    yield from reading([Row(None, line, set()) for line in lines], [], f'reuse: {len(lines)} line(s)', {'lines': len(lines)}, severity='note')

def check(page, inputs):
    yield from block_map(page, inputs)
    yield from baseline_inventory(page, inputs)
    yield from reuse(page, inputs)
