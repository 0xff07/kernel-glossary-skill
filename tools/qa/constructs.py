"""File-scope constructs of a kernel source file: functions, definitions, initializers, macros and comment blocks, with their line extents."""
import re

TITLE = re.compile(r'^\s*\*\s+((?:struct|enum|union)\s+)?(\w+)(\(\))?\s+-')
DEFINITION = re.compile(r'^(typedef\s+)?(struct|union|enum)\b\s*(\w+)?')
INITIALIZER = re.compile(r'^[\w\s\*]*?\b(\w+)(?:\[[^\]]*\])?\s*=\s*\{')
FUNCTION = re.compile(r'\b(\w+)\s*\(')
DEFINE = re.compile(r'^\s*#\s*define\s+(\w+)')
TYPEDEF_CLOSE = re.compile(r'^\}\s*(\w+)\s*;')
LITERALS = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')

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


STRUCT_OPEN = r'^(?:typedef\s+)?struct\s+%s\s*\{'
MEMBER = re.compile(r'(?:\(\s*\*\s*)?([A-Za-z_]\w*)\s*\)?\s*(?:\([^)]*\))?\s*(?:\[[^\]]*\])*\s*(?::\s*\d+)?\s*;\s*$')
STRUCT_POINTER = r'\bstruct\s+%s\s*\*+\s*([A-Za-z_]\w*)'
ASSIGN = r'\b%s\s*(?:->|\.)\s*%s\s*(?:\[[^\]]*\])?\s*(?:(?:[-+*/|&^%%]|<<|>>)?=(?!=)|\+\+|--)'
ASSIGN_ANY = r'(?:->|\.)\s*%s\s*(?:\[[^\]]*\])?\s*(?:(?:[-+*/|&^%%]|<<|>>)?=(?!=)|\+\+|--)'


def members_of(source, name):
    """The member names of `struct name` as the file defines it, nested members included, or []."""
    opener = re.compile(STRUCT_OPEN % re.escape(name))
    start = next((i for i, line in enumerate(source) if opener.match(line)), None)
    if start is None:
        return []
    out, depth = [], 0
    for line in source[start:]:
        code = re.sub(r'/\*.*?\*/', '', line)
        depth += code.count('{') - code.count('}')
        if depth <= 0 and line.strip().startswith('}'):
            break
        m = MEMBER.search(code.strip())
        if m and depth >= 1 and not code.strip().startswith(('/*', '*', '//')):
            out.append(m.group(1))
    return out


def assignment_to(line, field, variable=None):
    """Whether the line assigns the field, through the given variable when one is named."""
    pattern = ASSIGN % (re.escape(variable), re.escape(field)) if variable else ASSIGN_ANY % re.escape(field)
    return re.search(pattern, re.sub(r'/\*.*?\*/', '', line)) is not None


EMBEDDING = r'^\s*struct\s+%s\s*(\*?)\s*([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*;'


def embeddings_of(sources, name):
    """{(container struct, member, pointer)} for every struct that holds `struct name` as a
    member, by value or by pointer, across the given sources."""
    out = set()
    member = re.compile(EMBEDDING % re.escape(name))
    for source in sources.values():
        if source is None:
            continue
        container = None
        depth = 0
        for line in source:
            opened = re.match(r'^(?:typedef\s+)?struct\s+([A-Za-z_]\w*)\s*\{', line)
            if opened and depth == 0:
                container = opened.group(1)
            m = member.match(line)
            if m and container and depth >= 1:
                out.add((container, m.group(2), bool(m.group(1))))
            code = re.sub(r'/\*.*?\*/', '', line)
            depth += code.count('{') - code.count('}')
            if depth <= 0:
                container = None
                depth = 0
    return out


def field_writers(sources, name):
    """{field: [(path, line, function)]} for every assignment to a member of `struct name`:
    through a variable a function declares or receives as `struct name *`, or through a
    variable of a struct that embeds it, `container->member.field`. `sources` maps a tree path
    to its lines; comment blocks and prototypes are skipped with the constructs."""
    out = {}
    routes = [(re.compile(STRUCT_POINTER % re.escape(name)), '')]
    for container, member, pointer in embeddings_of(sources, name):
        routes.append((re.compile(STRUCT_POINTER % re.escape(container)), member + ('->' if pointer else '.')))
    for path, source in sources.items():
        if source is None:
            continue
        for construct in constructs_of(source):
            if construct.kind != 'function':
                continue
            body = source[construct.start - 1:construct.end]
            for pointer, via in routes:
                variables = {m.group(1) for line in body for m in pointer.finditer(line)}
                if not variables:
                    continue
                for offset, line in enumerate(body):
                    code = re.sub(r'/\*.*?\*/', '', line)
                    for variable in variables:
                        prefix = r'\b' + re.escape(variable) + r'\s*(?:->|\.)\s*' + (re.escape(via) if via else '')
                        for m in re.finditer(prefix + r'([A-Za-z_]\w*)', code):
                            if re.match(r'\s*(?:\[[^\]]*\])?\s*(?:(?:[-+*/|&^%]|<<|>>)?=(?!=)|\+\+|--)', code[m.end():]):
                                out.setdefault(m.group(1), []).append((path, construct.start + offset, construct.name))
    return out


def sources_under(tree, dirs, cache):
    """{tree path: lines} for every .c and .h file under the given tree directories, test files
    left out, so a census reads the neighbourhood the page cites."""
    import os
    out = {}
    for directory in sorted(set(dirs)):
        try:
            names = sorted(os.listdir(os.path.join(tree, directory)))
        except OSError:
            continue
        for name in names:
            if name.endswith(('.c', '.h')) and 'test' not in name:
                rel = f'{directory}/{name}' if directory else name
                from inputs import source_lines
                out[rel] = source_lines(tree, rel, cache)
    return out
