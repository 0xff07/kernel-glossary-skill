"""Validate guideline bindings, execute rule tests and check the reference figures."""
import io
import unittest
from pathlib import Path

import rules
from pagemodel import Page


def plain_fences(path):
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith('```'):
            j = i + 1
            while j < len(lines) and not lines[j].startswith('```'):
                j += 1
            if not lines[i][3:].strip():
                out.append((i + 1, lines[i + 1:j]))
            i = j + 1
        else:
            i += 1
    return out


def reference_figures(base, found):
    from kg import run_rules
    from tests.support import MINIMAL_PAGE, TestInputs
    geometry = rules.select(found, ['geometry.layout', 'geometry.unicode'])
    problems, figures = [], 0
    files = sorted((Path(base) / 'references/figures').glob('*.md')) + [Path(base) / 'guidelines/figures.md']
    for path in files:
        for line, body in plain_fences(path):
            text = MINIMAL_PAGE + '\n```\n' + '\n'.join(body) + '\n```\n\nThe reference figure closes the subsection.\n'
            page = Page('<figure>', text)
            if len(page.figures) != 2:
                problems.append(f'{path}:{line}: reference carries no drawing character')
                continue
            figures += 1
            reference = page.figures[1]
            for result in run_rules(page, TestInputs(), geometry):
                if result.error or result.skipped:
                    problems.append(f'{path}:{line}: {result.error or result.skipped}')
                problems += [f'{path}:{line}: {f.message}' for f in result.findings
                             if f.severity in ('FAIL', 'review') and f.line is not None
                             and reference.start <= f.line <= reference.end]
    return figures, problems


def test_suite(base, selected, only=None):
    """Require real tests for each selected rule, even when discovery has other tests."""
    qa = Path(base) / 'tools/qa'
    loader = unittest.TestLoader()
    problems = []
    selected_suites = []
    for binding in selected:
        path = Path(base) / binding.test_path
        if not path.is_file():
            problems.append(f'{binding.id}: missing test module {binding.test_path}')
            continue
        suite = loader.discover(str(qa / 'tests'), pattern=path.name, top_level_dir=str(qa))
        if suite.countTestCases() == 0:
            problems.append(f'{binding.id}: test module executes zero tests')
        selected_suites.append(suite)
    suite = unittest.TestSuite(selected_suites) if only is not None else loader.discover(
        str(qa / 'tests'), pattern='test_*.py', top_level_dir=str(qa))
    problems.extend(loader.errors)
    return suite, problems


def main(base, only=None):
    found, requirements, _sections, errors = rules.load(base)
    try:
        selected = rules.select(found, [only] if only is not None else None)
    except rules.RuleError as error:
        errors.append(str(error))
        selected = []
    if errors:
        for error in errors:
            print(f'FAIL binding: {error}')
        return 1
    print(f'Bindings: {len(found)} checks, {len(requirements)} requirements')
    suite, errors = test_suite(base, selected, only)
    if errors:
        for error in errors:
            print(f'FAIL tests: {error}')
        return 1
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    print(stream.getvalue().strip())
    if result.testsRun == 0 or result.skipped:
        errors.append('validation requires executed tests; zero-test or skipped-test runs are incomplete')
    if only is None:
        figures, problems = reference_figures(base, found)
        print(f'Reference figures: {figures} checked, {len(problems)} problems')
        errors.extend(problems)
    for error in errors:
        print(f'FAIL: {error}')
    return 0 if result.wasSuccessful() and not errors else 1
