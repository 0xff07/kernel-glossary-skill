#!/usr/bin/env python3
"""kg: run guideline checks, inspect page views, locate rules and run their tests.

Exit status: 0 complete without FAIL (human review may remain), 1 a failure or
engine/input error, 2 missing required inputs without another failure.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import report
import rules as rulebook
from inputs import Inputs, MissingInput, skill_dir
from lint_record import page_state_of
from pagemodel import Page


def load_rules(base):
    return rulebook.load(base)


def run_rules(page, inputs, found, only=None):
    results = []
    for binding in rulebook.select(found, only):
        result = report.Result(binding)
        try:
            for finding in binding.check(page, inputs):
                if not isinstance(finding, report.Finding):
                    raise TypeError('check must yield Finding records')
                if finding.severity not in report.SEVERITIES:
                    raise ValueError(f'unsupported severity {finding.severity!r}')
                if finding.line is not None and (type(finding.line) is not int or not 1 <= finding.line <= len(page.lines)):
                    raise ValueError(f'invalid page line {finding.line!r}')
                if not isinstance(finding.message, str):
                    raise TypeError('finding message must be text')
                json.dumps(finding.data, allow_nan=False)
                result.findings.append(finding)
        except MissingInput as error:
            result.skipped = str(error)
        except (Exception, SystemExit) as error:
            result.error = f'{type(error).__name__}: {error}'
        results.append(result)
    return results


def page_state(results, inputs, only=False):
    if only:
        return 'not evaluated', '--only: a partial run settles no state'
    state, reason, _record = page_state_of(inputs)
    if state == 'LINTED':
        if any(r.fails or r.error for r in results):
            return 'WRITTEN', 'this run raised failures; repeat the check pass'
        if not inputs.complete(results):
            return 'WRITTEN', 'this run is INCOMPLETE; repeat with every required input'
    return state, reason


def state_line(results, inputs, only=False):
    state, reason = page_state(results, inputs, only)
    return f'== state: {state} ({reason})'


def cmd_check(args):
    found, requirements, _sections, errors = load_rules(skill_dir())
    selected = rulebook.select(found, args.only)
    page = Page(args.page)
    inputs = Inputs(args.page, tree=args.tree, worksheet=args.worksheet, campaign=args.campaign, spec=args.spec)
    inputs.bind_version(page)
    inputs.problems.extend(errors)
    results = run_rules(page, inputs, selected)
    exemptions = inputs.exemptions()
    if args.only is not None:
        # Unselected current-ID entries cannot be evaluated by a partial run.
        exemptions = [e for e in exemptions if '/' in e['rule'] or e['rule'] in args.only]
    for entry, status in report.apply_exemptions(results, exemptions, page.lines):
        inputs.notes.append(f"{entry['text']}: {status}; exempts nothing")
    state, reason = page_state(results, inputs, args.only is not None)
    if args.json:
        checklist = [(item['slug'], *report.requirement_state(item, results)) for item in requirements] if args.checklist else None
        print(report.render_json(args.page, results, inputs, state, checklist))
    else:
        baseline = report.baseline_sentences(inputs.baseline) if inputs.baseline is not None else None
        text, _tally = report.render_text(results, page.lines, baseline, inputs, f'== state: {state} ({reason})')
        print(text)
        if args.checklist:
            print(report.render_checklist(requirements, results))
    return report.exit_status(results, inputs)


def print_skim(page):
    """The reading path of DETAILS: route, then per subsection the title, opener, recaps and closer."""
    skim = page.skim()
    for text in skim['preamble']:
        print(f'route: {text}')
    for sub in skim['subsections']:
        print(f"\n### {sub['title']}  (page {sub['line']})")
        print(f"  first: {sub['opener']}")
        for recap in sub['recaps']:
            print(f"  recap: {recap}")
        print(f"  last:  {sub['closer']}")


def print_load(page):
    """Reading-load measurements of the page, no rule attached."""
    import statistics
    from pagemodel import CODE_LINK, prose_text, sentences_of, RECAP
    details = page.section('DETAILS')
    prose = [(n, l) for n, l in enumerate(page.lines, 1)
             if page.region_of(n) == 'prose' and l.strip() and not l.startswith(('#', '|')) and not l.startswith(('    ', '\t'))]
    words = sum(len(prose_text(l).split()) for _n, l in prose)
    sentences = [s for _n, l in prose for s in sentences_of(l)]
    links = sum(len(CODE_LINK.findall(l)) for _n, l in prose)
    symbols = {t.strip().strip('`') for _n, l in prose for t, _u in CODE_LINK.findall(l)}
    skim = page.skim()
    recaps = sum(len(s['recaps']) for s in skim['subsections'])
    run = longest = 0
    for s in skim['subsections']:
        run += 1
        if s['recaps']:
            longest = max(longest, run); run = 0
    longest = max(longest, run)
    rows = [('lines', len(page.lines)), ('DETAILS starts at line', details.start if details else '-'),
            ('prose words', words), ('sentences', len(sentences)),
            ('words per sentence', round(statistics.mean(len(s.split()) for s in sentences), 1) if sentences else 0),
            ('links per sentence', round(links / len(sentences), 2) if sentences else 0),
            ('distinct linked symbols', len(symbols)), ('excerpts', len(page.excerpts)), ('figures', len(page.figures)),
            ('DETAILS subsections', len(page.subsections)), ('route paragraph', 'present' if skim['preamble'] else 'absent'),
            ('recaps', recaps), ('longest run without a recap', longest)]
    width = max(len(k) for k, _v in rows)
    for k, v in rows:
        print(f'{k:{width}}  {v}')


def cmd_view(args):
    page = Page(args.page)
    if args.skim:
        print_skim(page)
    elif args.load:
        print_load(page)
    elif args.regions:
        for n, line in enumerate(page.lines[:page.counted_lines()], 1):
            print(f'{n}:{page.region_of(n):10} {line}')
    elif args.raw:
        for n, line in page.raw_view():
            print(f'{n}:{line}')
    else:
        for row in page.prose_view(spans_visible=args.spans_visible):
            print(Page.printed(row))
    return 0


def cmd_table(args):
    from links_table import emit_table
    page = Page(args.page)
    inputs = Inputs(args.page, tree=args.tree, worksheet=args.worksheet, campaign=args.campaign)
    inputs.bind_version(page)
    if inputs.problems:
        for problem in inputs.problems:
            print(f'FAIL inputs: {problem}', file=sys.stderr)
        return 1
    return emit_table(page, inputs)


def cmd_where(args):
    found, requirements, sections, errors = load_rules(skill_dir())
    if errors:
        raise rulebook.RuleError('; '.join(errors))
    item = next((i for i in requirements if i['slug'] == args.rule_id), None)
    section = next((s for s in sections if s['slug'] == args.rule_id), None)
    if item is None and section is None:
        raise rulebook.RuleError(f'{args.rule_id}: no such requirement or section')
    entry = item or section
    print(f"{entry['slug']}: guidelines/{entry['doc']}.md:{entry['line']}")
    if item:
        print(f"  {item['text']}")
    for binding in found:
        if binding.id == args.rule_id:
            print(f'  check: {binding.module_path}')
            print(f'  tests: {binding.test_path}')
    return 0


def cmd_rules(args):
    found, _requirements, _sections, errors = load_rules(skill_dir())
    for binding in found:
        print(f'{binding.id:40} {binding.module_path}  {binding.home}')
    for error in errors:
        print(f'ERROR {error}', file=sys.stderr)
    return int(bool(errors))


def cmd_selftest(args):
    import selftest
    return selftest.main(skill_dir(), only=args.rule)


def cmd_retro(args):
    from inputs import skill_dir
    from retro import gather, known_rules, render, summarize
    if not os.path.isdir(args.dir):
        print(f'kg: no directory {args.dir}', file=sys.stderr)
        return 1
    pages = gather(args.dir)
    rows = summarize(pages, known_rules(skill_dir()))
    if args.rule:
        rows = [row for row in rows if row['rule'] == args.rule]
    print('\n'.join(render(args.dir, pages, rows, rule=args.rule)))
    return 0


def cmd_excerpt(args):
    """Print one unit ready to paste: the provenance comment and the verbatim lines of
    `path:first[-last]`, or with --whole the file-scope construct that holds the cited line."""
    import re as _re
    from constructs import constructs_of, construct_at
    from inputs import is_kernel_tree, skill_dir, source_lines
    match = _re.match(r'^([\w./-]+):(\d+)(?:-(\d+))?$', args.location)
    if not match:
        print('excerpt: give path:first or path:first-last', file=sys.stderr)
        return 2
    path, first = match.group(1), int(match.group(2))
    last = int(match.group(3)) if match.group(3) else first
    tree = os.path.abspath(args.tree or os.environ.get('KG_TREE') or os.path.dirname(os.path.dirname(os.path.dirname(skill_dir()))))
    if not is_kernel_tree(tree):
        print(f'excerpt: no kernel tree at {tree}; pass --tree', file=sys.stderr)
        return 2
    source = source_lines(tree, path, {})
    if source is None or first < 1 or last > len(source) or last < first:
        print(f'excerpt: {path}:{first}-{last} is not in the tree', file=sys.stderr)
        return 2
    if args.whole:
        construct = construct_at(constructs_of(source), first)
        if construct is None:
            print(f'excerpt: {path}:{first} lies in no file-scope construct', file=sys.stderr)
            return 2
        first, last = construct.start, construct.end
    print(f'/* {path}:{first} */')
    print('\n'.join(source[first - 1:last]))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog='kg', description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    check = sub.add_parser('check', help='run guideline checks over a page')
    check.add_argument('page')
    check.add_argument('--json', action='store_true')
    check.add_argument('--checklist', action='store_true')
    check.add_argument('--only', nargs='*', metavar='RULE')
    check.add_argument('--spec')
    check.set_defaults(func=cmd_check)
    view = sub.add_parser('view', help='print a page representation')
    view.add_argument('page')
    mode = view.add_mutually_exclusive_group(required=True)
    for name in ('regions', 'prose', 'raw', 'spans-visible', 'skim', 'load'):
        mode.add_argument('--' + name, action='store_true')
    view.set_defaults(func=cmd_view)
    table = sub.add_parser('table', help="emit the worksheet's LINKS table")
    table.add_argument('page')
    table.set_defaults(func=cmd_table)
    for command in (check, table):
        command.add_argument('--tree')
        command.add_argument('--worksheet')
        command.add_argument('--campaign')
    excerpt = sub.add_parser('excerpt', help='print a verbatim unit with its provenance comment, ready to paste')
    excerpt.add_argument('location', help='path:first or path:first-last, relative to the tree')
    excerpt.add_argument('--whole', action='store_true', help='the whole function or definition holding the cited line')
    excerpt.add_argument('--tree')
    excerpt.set_defaults(func=cmd_excerpt)
    st = sub.add_parser('selftest', help='validate bindings, rule tests and shared engine tests')
    st.add_argument('--rule', metavar='ID', help="execute this rule's test module")
    st.set_defaults(func=cmd_selftest)
    where = sub.add_parser('where', help='locate a guideline, its check and its tests')
    where.add_argument('rule_id')
    where.set_defaults(func=cmd_where)
    sub.add_parser('rules', help='list checks by guideline ID').set_defaults(func=cmd_rules)
    retro = sub.add_parser('retro', help="per rule, what the checks found on the first pass of every page a campaign's worksheets record")
    retro.add_argument('dir', nargs='?', default='progress', help='a progress directory (default: progress)')
    retro.add_argument('--rule', metavar='ID', help='list the pages for this rule instead')
    retro.set_defaults(func=cmd_retro)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, UnicodeError, rulebook.RuleError) as error:
        print(f'kg: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
