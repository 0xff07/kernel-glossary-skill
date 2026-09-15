"""Select count-bearing sentences to re-derive on a second basis."""
import re

from sentence_utils import prose_sentences, sentence_worklist

RULE = 'facts.two-bases'
NUMBER = re.compile(
    r'\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|'
    r'fifteen|sixteen|twenty|thirty|forty|fifty|hundred|\d+)\b', re.I)
ORDINAL = re.compile(
    r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last|remaining|other)\b', re.I)


def check(page, inputs):
    baseline = inputs.baseline if inputs is not None else None
    candidates = [sentence for sentence in prose_sentences(page, baseline)
                  if NUMBER.search(sentence.text) or ORDINAL.search(sentence.text)]
    yield from sentence_worklist(candidates, label='count', baseline_present=baseline is not None)
