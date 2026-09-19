"""Checks for [evidence.acceptance-lines]."""
from report import Finding
from report import observations
import re
RULE = 'evidence.acceptance-lines'
EVIDENCE_SECTION = '## EVIDENCE'
ACCEPTANCE = [('scoped behaviors covered', re.compile('scoped behavio', re.I)), ('claims supported nearby', re.compile('claims supported', re.I)), ('guards preserved', re.compile('guards? preserved', re.I)), ('invariants searched', re.compile('invariants? (counterexample-)?searched', re.I)), ('activation delta', re.compile('activation delta', re.I)), ('modes told apart', re.compile('modes told apart', re.I)), ('constructs and limits covered', re.compile('constructs (and limits )?covered', re.I))]
DIGEST_LINE = re.compile('page sha256:\\s*([0-9a-f]{64})', re.I)
SHORT = 12

def acceptance(page, inputs):
    text = inputs.worksheet_section(EVIDENCE_SECTION)
    present = [name for name, pattern in ACCEPTANCE if pattern.search(text)]
    missing = [name for name, _p in ACCEPTANCE if name not in present]
    findings = []
    if not text.strip():
        findings.append(Finding(None, 'review', 'no EVIDENCE section in the worksheet'))
    for name in missing:
        findings.append(Finding(None, 'review', f'acceptance line not found in EVIDENCE: {name}'))
    found = DIGEST_LINE.findall(text)
    recorded = found[-1].lower() if found else None
    if recorded is None:
        findings.append(Finding(None, 'review', 'EVIDENCE names no page digest (`page sha256: <digest>` of the page it describes)'))
        described = 'none'
    elif recorded != inputs.page_digest:
        findings.append(Finding(None, 'review', f'EVIDENCE describes the page at sha256 {recorded[:SHORT]}, and the page on disk is {inputs.page_digest[:SHORT]}: the evidence predates an edit'))
        described = 'stale'
    else:
        described = 'current'
    footer = f'acceptance-lines={len(present)} of {len(ACCEPTANCE)} evidence-digest={described}'
    yield from observations(findings, footer, [], {'present': present, 'missing': missing, 'digest': described})

def check(page, inputs):
    inputs.require('worksheet')
    yield from acceptance(page, inputs)
