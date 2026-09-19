"""Select universal claims for review against their stated domain and basis."""
import re

from worksheet_utils import bases_rows
from sentence_utils import prose_sentences, sentence_worklist

RULE = 'facts.universal-claims'
UNIVERSAL = re.compile(
    r'\b(only|never|always|every|all|none|no other|exactly|each|sole|solely|the one|the single|once|'
    r'nothing|anything|everything|whole)\b', re.I)


def check(page, inputs):
    baseline = inputs.baseline if inputs is not None else None
    candidates = [sentence for sentence in prose_sentences(page, baseline)
                  if UNIVERSAL.search(sentence.text)]
    yield from sentence_worklist(candidates, label='universal', baseline_present=baseline is not None,
                                 bases=bases_rows(inputs), page=page)
