"""kg triage: every page of a directory under the current rules, one row each, graded by how far
it stands from them, so a repair campaign can be planned and its progress read."""
import hashlib
import json
import os
from pathlib import Path

EXCERPT_RULES = ('excerpts.verbatim', 'excerpts.enclosing', 'excerpts.contiguity', 'excerpts.cited-shown',
                 'excerpts.walkthrough', 'excerpts.outline', 'provenance.form')
READING_RULES = ('arrangement.route', 'arrangement.recap', 'purpose.schema', 'purpose.conclusion-first')
FIGURE_RULES = ('drawing.model', 'drawing.triggers', 'drawing.legend', 'drawing.walk', 'lifecycle.when', 'evidence.lifecycle')
GRADES = ('current', 'fix', 'rebuild')
FIX_GAP_SHARE = 0.2        # at most one owned function in five not read whole
FIX_GAPS_ABSOLUTE = 1      # or a single function, whatever the share on a page with few
FIX_SKELETON_SHARE = 0.35  # at most a third of the excerpt units without their opener or eliding inside a function


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


def _count(results, rules, severity):
    return sum(1 for rule in rules if rule in results
               for finding in results[rule].get('findings', []) if finding.get('severity') == severity)


def _data(results, rule, key):
    for finding in results.get(rule, {}).get('findings', []):
        data = finding.get('data')
        if isinstance(data, dict) and key in data:
            return data
    return {}


def grade_of(fails, gaps, functions, skeleton, units):
    if fails == 0:
        return 'current'
    gap_share = gaps / functions if functions else 0.0
    skeleton_share = skeleton / units if units else 0.0
    few_gaps = gaps <= FIX_GAPS_ABSOLUTE or gap_share <= FIX_GAP_SHARE
    return 'fix' if few_gaps and skeleton_share <= FIX_SKELETON_SHARE else 'rebuild'


def measures(document, page):
    """One row: the page's distance from the rules, from a check document and the parsed page."""
    results = document.get('results', {})
    fails = sum(1 for r in results.values() for f in r.get('findings', []) if f.get('severity') == 'FAIL')
    reviews = sum(1 for r in results.values() for f in r.get('findings', []) if f.get('severity') == 'review')
    enclosing = _data(results, 'excerpts.enclosing', 'units')
    contiguity = _data(results, 'excerpts.contiguity', 'units')
    units = enclosing.get('units') or contiguity.get('units') or 0
    skeleton = min(units, (enclosing.get('findings') or 0) + (contiguity.get('in_functions') or 0))
    walk = _data(results, 'excerpts.walkthrough', 'functions')
    functions, gaps = walk.get('functions', 0) or 0, walk.get('incomplete', 0) or 0
    return {'page': document.get('page', ''), 'state': str(document.get('state', '')), 'lines': len(page.lines),
            'figures': len(page.figures), 'fail': fails, 'review': reviews,
            'excerpt_fail': _count(results, EXCERPT_RULES, 'FAIL'), 'units': units, 'skeleton': skeleton,
            'functions': functions, 'gaps': gaps, 'reading_fail': _count(results, READING_RULES, 'FAIL'),
            'figure_fail': _count(results, FIGURE_RULES, 'FAIL'),
            'grade': grade_of(fails, gaps, functions, skeleton, units)}


def qa_digest(document):
    inputs = document.get('inputs') or {}
    return inputs.get('qa_digest') or inputs.get('qa_sha256') or ''


REUSE_KEYS = ('page_digest', 'qa_digest', 'tree', 'tree_head', 'worksheet', 'worksheet_digest', 'spec', 'campaign', 'baseline')


def reusable(candidate, current):
    """Whether a cached document was checked under the inputs a fresh check would resolve now: the
    page and QA digests, the tree and its head, the worksheet and its digest, the spec, the campaign
    and whether a committed baseline differed."""
    inputs = candidate.get('inputs') or {}
    if not inputs.get('qa_digest') and inputs.get('qa_sha256'):
        inputs = dict(inputs, qa_digest=inputs['qa_sha256'])
    return all(inputs.get(key) == current.get(key) for key in REUSE_KEYS)


def gather(base, directory, cache=None, tree=None, progress=None):
    """Rows for every page under the directory, reusing a cached document whose page and QA
    digests still match; a fresh check is written to the cache when one is given."""
    from pagemodel import Page
    base = Path(base)
    rows = []
    pages = sorted(p for p in Path(directory).rglob('*.md') if p.name != 'README.md')
    for k, path in enumerate(pages, 1):
        page_path = str(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        key = str(path.relative_to(directory)).replace('/', '_')[:-3] if str(path).startswith(str(directory)) else path.stem
        document = None
        cached = Path(cache) / f'{key}.json' if cache else None
        if cached and cached.exists():
            try:
                candidate = json.load(open(cached, encoding='utf-8'))
                from inputs import Inputs
                current = Inputs(page_path, tree=tree).as_dict()
                if reusable(candidate, current):
                    document = candidate
            except (OSError, ValueError):
                document = None
        if document is None:
            document = check_document(base, page_path, tree)
            if cached:
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_text(json.dumps(document), encoding='utf-8')
        if progress:
            progress(k, len(pages), page_path)
        rows.append(measures(document, Page(page_path)))
    return rows


def current_qa_digest(base):
    """The digest kg check prints for the guidelines and the QA code."""
    from lint_record import qa_digest
    return qa_digest(base)


def render(rows, directory):
    order = {g: i for i, g in enumerate(GRADES)}
    rows = sorted(rows, key=lambda r: (order[r['grade']], -(r['gaps'] / r['functions'] if r['functions'] else 0), -(r['skeleton'] / r['units'] if r['units'] else 0), r['page']))
    out = [f"triage of {len(rows)} pages under {directory}",
           f"{'grade':8} {'page':40} {'lines':>5} {'fig':>3} {'FAIL':>4} {'review':>6} {'excF':>4} {'units':>5} {'skel':>5} {'walk gaps':>9} {'readF':>5} {'figF':>4}  state"]
    for r in rows:
        skel = f"{100 * r['skeleton'] // r['units']}%" if r['units'] else '-'
        gaps = f"{r['gaps']}/{r['functions']}" if r['functions'] else '-'
        name = r['page'].split('docs/', 1)[-1][:-3] if r['page'].endswith('.md') else r['page']
        out.append(f"{r['grade']:8} {name[:40]:40} {r['lines']:5} {r['figures']:3} {r['fail']:4} {r['review']:6} {r['excerpt_fail']:4} {r['units']:5} {skel:>5} {gaps:>9} {r['reading_fail']:5} {r['figure_fail']:4}  {r['state'][:7]}")
    out.append('')
    for grade in GRADES:
        group = [r for r in rows if r['grade'] == grade]
        if not group:
            continue
        shares = [r['skeleton'] / r['units'] for r in group if r['units']]
        gapped = sum(1 for r in group if r['gaps'])
        out.append(f"{grade:8} pages={len(group)} lines={sum(r['lines'] for r in group)} figures={sum(r['figures'] for r in group)} "
                   f"mean-FAIL={sum(r['fail'] for r in group) // len(group)} mean-skeleton={int(100 * sum(shares) / len(shares)) if shares else 0}% pages-with-walk-gaps={gapped}")
    out.append(f"grades: current = no FAIL; fix = walk gaps at most {int(FIX_GAP_SHARE * 100)}% of the owned functions (or one function) and skeletons at most "
               f"{int(FIX_SKELETON_SHARE * 100)}% of the excerpt units; rebuild = the rest")
    return out
