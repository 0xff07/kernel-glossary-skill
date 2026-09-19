"""The human check-pass record must name the current page and QA implementation."""
import re
from lint_record import page_state_of
from report import Finding
RULE = 'lint.record'
SELF_RUN = re.compile('check pass:\\s*self-run', re.I)

def check(page, inputs):
    inputs.require('worksheet')
    state, reason, record = page_state_of(inputs)
    yield Finding(None, 'note', f'state {state}: {reason}', {'state': state, 'reason': reason, 'digest': inputs.page_digest, 'qa_digest': inputs.qa_digest, 'record_digest': record[1] if record else None, 'record_qa_digest': record[2] if record else None, 'self_run': bool(SELF_RUN.search(inputs.worksheet_section('## LINT')))})
    if record and state != 'LINTED':
        yield Finding(None, 'review', reason + '; renew the record after the check pass')
    if SELF_RUN.search(inputs.worksheet_section('## LINT')):
        yield Finding(None, 'note', 'LINT says the check pass was self-run (single-agent mode)')
