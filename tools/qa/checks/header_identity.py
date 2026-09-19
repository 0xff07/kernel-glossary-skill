"""Checks for [header.identity]."""
from report import Finding
from report import observations
RULE = 'header.identity'

def identity(page, inputs):
    """A refused candidate fails the run only when `--worksheet` named it; one the convention or
    `--campaign` found and refused is already a note of the inputs, the footer counts it, and
    the worksheet rules skip."""
    findings = [Finding(None, 'FAIL', why) for why in inputs.worksheet_rejected] if inputs.worksheet_how == 'option' else []
    if inputs.worksheet is None and (not inputs.worksheet_rejected):
        findings.append(Finding(None, 'note', 'no worksheet found for this page; the page is WRITTEN on this machine'))
    footer = f"worksheet={inputs.worksheet or '-'} found-by={inputs.worksheet_how} refused={len(inputs.worksheet_rejected)} identity={('ok' if inputs.worksheet else '-')}"
    yield from observations(findings, footer, [], {'worksheet': inputs.worksheet, 'refused': inputs.worksheet_rejected})

def check(page, inputs):
    yield from identity(page, inputs)
