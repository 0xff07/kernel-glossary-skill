"""Checks for [header.identity]."""
from report import Finding
from report import observations
RULE = 'header.identity'

def identity(page, inputs):
    """A refused candidate fails the run only when `--dossier` named it; one the convention or
    `--campaign` found and refused is already a note of the inputs, the footer counts it, and
    the dossier rules skip."""
    findings = [Finding(None, 'FAIL', why) for why in inputs.dossier_rejected] if inputs.dossier_how == 'option' else []
    if inputs.dossier is None and (not inputs.dossier_rejected):
        findings.append(Finding(None, 'note', 'no dossier found for this page; the page is WRITTEN on this machine'))
    footer = f"dossier={inputs.dossier or '-'} found-by={inputs.dossier_how} refused={len(inputs.dossier_rejected)} identity={('ok' if inputs.dossier else '-')}"
    yield from observations(findings, footer, [], {'dossier': inputs.dossier, 'refused': inputs.dossier_rejected})

def check(page, inputs):
    yield from identity(page, inputs)
