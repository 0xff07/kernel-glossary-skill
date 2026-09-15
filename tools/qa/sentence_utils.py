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
Sentence = namedtuple('Sentence', 'line text provenance')


def sentences(text):
    return SENTENCE_END.split(CODE_SPAN.sub('X', LINK.sub(r'\1', text)))


def prose_sentences(page, baseline=None):
    """Yield (page line, masked sentence, provenance) in the existing prose scope."""
    before = None if baseline is None else {
        sentence.strip() for line in baseline.split('\n')
        for sentence in sentences(line) if sentence.strip()
    }
    for line, text in enumerate(page.lines[:page.counted_lines()], 1):
        if page.region_of(line) not in ('prose', 'section6') or text.startswith(('#', '|', '>', '- ', '* ')):
            continue
        for sentence in sentences(text):
            provenance = 'n/a' if before is None else 'carried' if sentence.strip() in before else 'NEW'
            yield Sentence(line, sentence, provenance)


def sentence_worklist(candidates, *, label, baseline_present):
    """Report candidates already selected by the caller; label is presentation text."""
    rows = []
    new = 0
    for line, text, provenance in candidates:
        new += provenance == 'NEW'
        rows.append(Row(line, f'{line} {label.upper()} [{provenance}]: {text.strip()[:SENTENCE_CLIP]}', set()))
    summary = (f'{label}: worklist only, no verification '
               f"(sentences={len(rows)} new-since-commit={new if baseline_present else 'n/a'}; "
               'each is re-derived by hand on a second basis)')
    yield from reading(rows, summary=summary,
                       data={'sentences': len(rows), 'new_since_commit': new if baseline_present else None})
