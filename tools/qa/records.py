"""The records kg check keeps beside the worksheet: the first pass, written once the page is whole
and never overwritten, and the last run, written on every full run for the next run's delta."""
import collections
import datetime
import json
import os

from inputs import page_relative
from lint_record import RECORD
from report import finding_key

# the H2 sections a page carries before its first pass is worth recording (section six is optional)
WHOLE_PAGE_H2 = ("SUMMARY", "SPECIFICATIONS", "COVERAGE", "DOCUMENTATION", "OTHER SOURCES", "DETAILS")


def keys_of(results):
    """The FAIL and review findings of a run as a multiset of their keys."""
    return collections.Counter(finding_key(r.rule.id, f) for r in results for f in r.findings
                               if f.severity in ("FAIL", "review"))


def missing_sections(page):
    return [name for name in WHOLE_PAGE_H2 if name not in page.h2_names]


def counts_document(page_path, results, inputs):
    return {'kg': 3, 'page': page_relative(page_path), 'date': datetime.date.today().isoformat(),
            'page_digest': inputs.page_digest, 'qa_digest': inputs.qa_digest,
            'rules': {r.rule.id: {'FAIL': r.fails, 'review': r.reviews, 'complete': not (r.skipped or r.error)}
                      for r in results}}


def write_json(path, document):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as out:
        json.dump(document, out, indent=1)
        out.write('\n')


def record_first_pass(page_path, page, results, inputs):
    """Once, on the first full run over the whole page: the FAIL and review counts per rule before
    any fix. Returns a note for the report, or None when the record exists."""
    path = inputs.first_pass_path
    if path is None:
        return 'first pass not recorded: no worksheet path for this page (pass --worksheet)'
    if os.path.exists(path) or past_first_pass(inputs):
        return None
    missing = missing_sections(page)
    if missing:
        return (f"draft: no {', '.join(missing)}; the first pass is recorded on the first full run "
                f"over the whole page")
    write_json(path, counts_document(page_path, results, inputs))
    return f'first pass recorded at {path}'


def past_first_pass(inputs):
    """A worksheet that carries a LINTED record is past its first pass: a check pass follows the
    fixes, so a page checked under later rules records none."""
    if not getattr(inputs, 'worksheet_lines', None):
        return False
    return bool(RECORD.search(inputs.worksheet_section('## LINT')))


def read_last_run(path):
    """{'date', 'keys'} of the previous full run, or None without a readable record."""
    try:
        with open(path, encoding='utf-8') as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return None
    keys = document.get('keys') if isinstance(document, dict) else None
    if not isinstance(keys, dict):
        return None
    return {'date': document.get('date', '?'),
            'keys': collections.Counter({k: int(v) for k, v in keys.items() if isinstance(v, int)})}


def record_last_run(page_path, results, inputs, keys):
    """Every full run: the counts per rule and the keys of the FAIL and review findings."""
    path = inputs.last_run_path
    if path is None:
        return
    document = counts_document(page_path, results, inputs)
    document['keys'] = dict(keys)
    write_json(path, document)
