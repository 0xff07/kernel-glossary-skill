"""Checks for [excerpts.enclosing]."""
from inputs import source_lines
from measurements import positions_of
from report import Finding, observations
import re
RULE = 'excerpts.enclosing'
CLOSER = re.compile(r'^\};?\s*$')
TITLE = re.compile(r'^\s*\*\s+((?:struct|enum|union)\s+)?(\w+)(\(\))?\s+-')
DEFINITION = re.compile(r'^(typedef\s+)?(struct|union|enum)\b\s*(\w+)?')
INITIALIZER = re.compile(r'^[\w\s\*]*?\b(\w+)(?:\[[^\]]*\])?\s*=\s*\{')
FUNCTION = re.compile(r'\b(\w+)\s*\(')
DEFINE = re.compile(r'^\s*#\s*define\s+(\w+)')
TYPEDEF_CLOSE = re.compile(r'^\}\s*(\w+)\s*;')
LITERALS = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
LINE_CLIP = 60

class Construct:
    def __init__(self, start, end, kind, name):
        self.start, self.end, self.kind, self.name = start, end, kind, name

    def label(self, base):
        if self.kind == 'function': return f'{self.name}()'
        if self.kind in ('struct', 'union', 'enum'): return f'{self.kind} {self.name}' if self.name else f'the {self.kind} at {base}:{self.start}'
        if self.kind == 'typedef': return f'the typedef of {self.name}' if self.name else f'the typedef at {base}:{self.start}'
        if self.kind == 'initializer': return f'the initializer of {self.name}'
        if self.kind == 'macro': return f'the macro {self.name}'
        if self.kind == 'kerneldoc': return f'the kerneldoc of {self.name}' if self.name else f'the kerneldoc at {base}:{self.start}'
        return f'the {self.kind} at {base}:{self.start}'

def header_of(source, brace_line):
    """The first line of the construct whose opening brace stands on brace_line: the line itself
    when it opens a definition or an initializer, else the column-0 line above a signature's
    continuation lines."""
    text = source[brace_line]
    if not text[:1].isspace() and (is_definition(text) or INITIALIZER.match(text) or FUNCTION.search(LITERALS.sub('""', text))):
        return brace_line
    h = brace_line - 1
    while h >= 0 and (source[h][:1].isspace() or not source[h].strip()):
        if not source[h].strip():
            return brace_line
        h -= 1
    return h if h >= 0 else brace_line

def is_definition(text):
    """A struct, union or enum definition line: the keyword at column 0 and no parenthesis before
    the brace, which tells it from a signature returning a struct."""
    if not DEFINITION.match(text):
        return False
    return '(' not in text or ('{' in text and text.index('{') < text.index('('))

def classify(source, header, end):
    text = source[header]
    m = DEFINITION.match(text) if is_definition(text) else None
    if m:
        if m.group(1):
            close = TYPEDEF_CLOSE.match(source[end]) if end < len(source) else None
            return 'typedef', close.group(1) if close else m.group(3)
        return m.group(2), m.group(3)
    m = INITIALIZER.match(text)
    if m:
        return 'initializer', m.group(1)
    m = FUNCTION.search(LITERALS.sub('""', text))
    if m and not text[:1].isspace():
        return 'function', m.group(1)
    return 'block', None

def constructs_of(source):
    """Every file-scope construct of a source file, in order: functions, struct, union and enum
    definitions, top-level initializers, multi-line macros, and kerneldoc or comment blocks."""
    out = []
    depth = 0
    in_comment = False
    comment_start = None
    header = None
    i = 0
    n = len(source)
    while i < n:
        text = source[i]
        if in_comment:
            if '*/' in text:
                in_comment = False
                if comment_start is not None:
                    kind = 'kerneldoc' if source[comment_start].lstrip().startswith('/**') else 'comment'
                    name = None
                    if kind == 'kerneldoc' and comment_start + 1 < n:
                        t = TITLE.match(source[comment_start + 1])
                        name = ((t.group(1) or '') + t.group(2) + (t.group(3) or '')) if t else None
                    out.append(Construct(comment_start + 1, i + 1, kind, name))
                    comment_start = None
            i += 1
            continue
        stripped = text.strip()
        if depth == 0 and stripped.startswith('/*') and '*/' not in stripped[2:]:
            in_comment = True
            comment_start = i
            i += 1
            continue
        if depth == 0 and stripped.startswith('#'):
            m = DEFINE.match(text)
            start = i
            while i < n and source[i].rstrip().endswith('\\'):
                i += 1
            if m and i > start:
                out.append(Construct(start + 1, i + 1, 'macro', m.group(1)))
            i += 1
            continue
        code = re.sub(r'//.*', '', re.sub(r'/\*.*?\*/', '', LITERALS.sub('""', text)))
        if '/*' in code:
            code = code[:code.index('/*')]
            in_comment = True
            comment_start = None
        for ch in code:
            if ch == '{':
                if depth == 0:
                    header = header_of(source, i)
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and header is not None:
                    kind, name = classify(source, header, i)
                    out.append(Construct(header + 1, i + 1, kind, name))
                    header = None
                elif depth < 0:
                    depth = 0
        i += 1
    out.sort(key=lambda c: c.start)
    return out

def construct_at(constructs, line):
    for c in constructs:
        if c.start <= line <= c.end:
            return c
    return None

def enclosing(page, inputs):
    findings, listing = [], []
    counts = {'units': 0, 'top_level': 0, 'opened': 0, 'continued': 0, 'unmapped': 0, 'findings': 0}
    tables = {}
    for fence in page.excerpts:
        opened = {}
        for unit in fence.units:
            if not unit.path:
                continue
            counts['units'] += 1
            source = source_lines(inputs.tree, unit.path, inputs.cache)
            positions = positions_of(unit, source) if source is not None else None
            if positions is None:
                counts['unmapped'] += 1
                findings.append(Finding(unit.start, 'review', f'{unit.path}:{unit.line} could not be mapped onto the file; [excerpts.verbatim] reports why'))
                continue
            if unit.path not in tables:
                tables[unit.path] = constructs_of(source)
            constructs = tables[unit.path]
            shown = {p for p in positions if p}
            base = unit.path.rsplit('/', 1)[-1]
            touched = []
            for p in sorted(shown):
                c = construct_at(constructs, p)
                if c is None:
                    counts['top_level'] += 1
                elif c not in touched:
                    touched.append(c)
            for c in touched:
                seen = opened.setdefault(unit.path, set())
                needs_title = c.kind == 'kerneldoc' and c.start < len(source) and TITLE.match(source[c.start])
                if c.start in shown and (not needs_title or c.start + 1 in shown):
                    counts['opened'] += 1
                    seen.add(c.start)
                    listing.append(f'{unit.start:5} {base}:{unit.line} opens {c.label(base)}')
                    continue
                if c.start in seen:
                    counts['continued'] += 1
                    listing.append(f'{unit.start:5} {base}:{unit.line} continues {c.label(base)}')
                    continue
                counts['findings'] += 1
                opener = source[c.start - 1].strip()[:LINE_CLIP]
                if c.kind == 'kerneldoc':
                    what = f'without its "/**" line and the title line beneath it; begin the unit at {base}:{c.start} and keep {source[c.start].strip()[:LINE_CLIP]!r}'
                else:
                    what = f'without its opening line; begin the unit at {base}:{c.start} {opener!r} and elide to the lines it is about'
                findings.append(Finding(unit.start, 'FAIL', f'{base}:{unit.line} shows lines of {c.label(base)} ({base}:{c.start}-{c.end}) {what}',
                                        {'construct': c.label(base), 'opener': c.start, 'end': c.end}))
    footer = (f"units={counts['units']} openers-shown={counts['opened']} continued={counts['continued']} "
              f"top-level-lines={counts['top_level']} unmapped={counts['unmapped']} findings={counts['findings']}")
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    inputs.require('tree')
    yield from enclosing(page, inputs)
