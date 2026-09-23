"""kg triage: every page of a directory under the current rules, one row each with its FAIL and
review totals, its FAIL count per rule family, lines, figures and state. Measurements only: what
to do with a page is read, never graded."""
import json
from collections import Counter
from pathlib import Path


def check_document(base, page_path, tree=None):
    """The document `kg check --json` prints for the page, as a dict."""
    from kg import load_rules, page_state, run_rules
    import report
    import rules as rulebook
    from inputs import Inputs
    from pagemodel import Page
    found, _requirements, _sections, errors = load_rules(base)
    page = Page(page_path)
    inputs = Inputs(page_path, tree=tree)
    inputs.bind_version(page)
    inputs.problems.extend(errors)
    results = run_rules(page, inputs, rulebook.select(found, None))
    for _entry, _status in report.apply_exemptions(results, inputs.exemptions(), page.lines):
        pass
    state, _reason = page_state(results, inputs, False)
    return json.loads(report.render_json(page_path, results, inputs, state))


def measures(document, page):
    """One row: the page's FAIL and review totals, its FAIL count per rule family (the part of the
    rule ID before the dot), lines, figures and state."""
    families, reviews = Counter(), 0
    for rule, result in document.get('results', {}).items():
        for finding in result.get('findings', []):
            if finding.get('severity') == 'FAIL':
                families[rule.split('.')[0]] += 1
            elif finding.get('severity') == 'review':
                reviews += 1
    return {'page': document.get('page', ''), 'state': str(document.get('state', '')), 'lines': len(page.lines),
            'figures': len(page.figures), 'fail': sum(families.values()), 'review': reviews,
            'families': dict(sorted(families.items()))}


def gather(base, directory, tree=None, progress=None):
    """Rows for every page under the directory, each checked afresh."""
    from pagemodel import Page
    pages = sorted(p for p in Path(directory).rglob('*.md') if p.name != 'README.md')
    rows = []
    for k, path in enumerate(pages, 1):
        if progress:
            progress(k, len(pages), str(path))
        rows.append(measures(check_document(base, str(path), tree), Page(str(path))))
    return rows


def render(rows, directory):
    rows = sorted(rows, key=lambda r: (-r['fail'], -r['review'], r['page']))
    out = [f"triage of {len(rows)} pages under {directory}",
           f"{'page':40} {'lines':>5} {'fig':>3} {'FAIL':>4} {'review':>6}  {'state':8} FAIL by family"]
    for r in rows:
        name = r['page'].split('docs/', 1)[-1][:-3] if r['page'].endswith('.md') else r['page']
        families = ', '.join(f'{family} {n}' for family, n in r['families'].items())
        out.append(f"{name[:40]:40} {r['lines']:5} {r['figures']:3} {r['fail']:4} {r['review']:6}  {r['state'][:8]:8} {families}".rstrip())
    out.append('')
    out.append(f"pages={len(rows)} with-FAIL={sum(1 for r in rows if r['fail'])} FAIL={sum(r['fail'] for r in rows)} "
               f"review={sum(r['review'] for r in rows)} lines={sum(r['lines'] for r in rows)} figures={sum(r['figures'] for r in rows)}")
    return out
