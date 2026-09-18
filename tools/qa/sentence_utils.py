"""Sentence normalization, baseline tracking and worklist presentation.

Callers select candidates with their own patterns; this module has no rule IDs,
language heuristics, or selector dispatch.
"""
import re
from collections import namedtuple

from pagemodel import LINK
from report import Row, reading

CODE_SPAN = re.compile(r'`[^`]+`')
SENTENCE_END = re.compile(r'(?<=[.!?])\s+')
SENTENCE_CLIP = 150
Sentence = namedtuple('Sentence', 'line text provenance raw')


def sentences(text):
    return SENTENCE_END.split(CODE_SPAN.sub('X', LINK.sub(r'\1', text)))


def normalized(text):
    """Links reduced to their text, backticks dropped, whitespace collapsed, lower case: the form
    a recorded claim fragment is matched in."""
    return re.sub(r'\s+', ' ', LINK.sub(r'\1', text).replace('`', '')).strip().lower()


def prose_sentences(page, baseline=None):
    """Yield (page line, masked sentence, provenance, raw sentence) in the existing prose scope."""
    before = None if baseline is None else {
        sentence.strip() for line in baseline.split('\n')
        for sentence in sentences(line) if sentence.strip()
    }
    for line, text in enumerate(page.lines[:page.counted_lines()], 1):
        if page.region_of(line) not in ('prose', 'section6') or text.startswith(('#', '|', '>', '- ', '* ')):
            continue
        masked = sentences(text)
        raw = SENTENCE_END.split(LINK.sub(r'\1', text))
        if len(raw) != len(masked):
            raw = [LINK.sub(r'\1', text)] * len(masked)
        for sentence, original in zip(masked, raw):
            provenance = 'n/a' if before is None else 'carried' if sentence.strip() in before else 'NEW'
            yield Sentence(line, sentence, provenance, original)


def sentence_worklist(candidates, *, label, baseline_present, bases=None, page=None, report_stale=False):
    """Report candidates already selected by the caller; label is presentation text. A candidate
    the dossier's Bases table covers (a row at its page line whose claim fragment is in the
    sentence) is a note rather than a reading row; with `report_stale`, a row whose fragment no
    longer sits on its line is reported too."""
    rows, notes, used = [], [], set()
    new = with_basis = 0
    by_line = {}
    for index, row in enumerate(bases or []):
        by_line.setdefault(row['line'], []).append((index, row))
    for line, text, provenance, raw in candidates:
        new += provenance == 'NEW'
        shown = f'{line} {label.upper()} [{provenance}]: {text.strip()[:SENTENCE_CLIP]}'
        match = next((index for index, row in by_line.get(line, [])
                      if index not in used and normalized(row['claim']) in normalized(raw)), None)
        if match is None:
            rows.append(Row(line, shown, set()))
        else:
            used.add(match)
            with_basis += 1
            notes.append((line, f'{shown} (basis recorded)'))
    stale = 0
    if report_stale and page is not None:
        for row in bases or []:
            on_page = 0 < row['line'] <= len(page.lines) and normalized(row['claim']) in normalized(page.lines[row['line'] - 1])
            if not on_page:
                stale += 1
                notes.append((row['line'] if 0 < row['line'] <= len(page.lines) else None,
                              f'bases row at page {row["line"]} names no sentence there: {row["claim"][:SENTENCE_CLIP]}'))
    counted = f"new-since-commit={new if baseline_present else 'n/a'}"
    summary = (f'{label}: sentences={len(candidates)} with-basis={with_basis} without-basis={len(rows)} {counted}'
               + (f' stale-bases={stale}' if report_stale else '')
               + '; each without a basis is re-derived by hand on a second basis')
    data = {'sentences': len(candidates), 'with_basis': with_basis, 'without_basis': len(rows),
            'new_since_commit': new if baseline_present else None}
    if report_stale:
        data['stale_bases'] = stale
    yield from reading(rows, notes, summary=summary, data=data)
