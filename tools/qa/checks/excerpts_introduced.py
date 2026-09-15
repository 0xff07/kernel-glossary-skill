"""Checks for [excerpts.introduced]."""
from report import Finding
from report import observations
import os
import re
from inputs import source_lines
from inputs import MissingInput
from pagemodel import CODE_LINK
from pagemodel import RETURN_TYPE_LINE
from pagemodel import is_code_line
from pagemodel import CONSTRUCT_TAGGED as DEFINITION_TAGGED
from pagemodel import CONSTRUCT_MACRO as DEFINITION_MACRO
from pagemodel import CONSTRUCT_FUNCTION as DEFINITION_FUNCTION
from pagemodel import CONSTRUCT_NAME_LINE as NAME_LINE
from pagemodel import CONSTRUCT_PROTOTYPE
RULE = 'excerpts.introduced'
DEFINITION_TABLE = re.compile('^(?:static\\s+|const\\s+)*(?:struct|enum)\\s+\\w+\\s+(\\w+)(?:\\[\\])?\\s*=\\s*\\{')
DEFINITION_BY_MACRO = re.compile('^(?:static\\s+|const\\s+)*(?:DEFINE_\\w+|TRACE_EVENT|DECLARE_EVENT_CLASS|DECLARE_\\w+|DEVICE_ATTR\\w*|module_\\w+|MODULE_\\w+)\\((\\w+)')
DEFINITION_VARIABLE = re.compile('^(?:static\\s+|const\\s+|unsigned\\s+|extern\\s+)*(?:struct\\s+|enum\\s+|union\\s+)?[A-Za-z_]\\w*\\s+\\**\\s*(?:const\\s+)?\\**([A-Za-z_]\\w*)(?:\\[[^\\]]*\\])?\\s*(?:=|;)')
MODULE_DEVICE_TABLE = re.compile('^MODULE_DEVICE_TABLE\\(\\w+,\\s*(\\w+)\\)')
ARRAY_OPENER = re.compile('^(?:static\\s+|const\\s+|extern\\s+)*(?:struct\\s+|enum\\s+|union\\s+)?[A-Za-z_]\\w*\\s+\\**\\s*(?:const\\s+)?\\**([A-Za-z_]\\w*)(?:\\[[^\\]]*\\])?\\s*=\\s*\\{\\s*$')
TYPEDEF_FUNCTION = re.compile('^typedef\\s+.*\\(\\s*\\*\\s*(\\w+)\\s*\\)\\s*\\(')
ENCLOSING_FUNCTION = re.compile('^(?:[\\w*]+\\s+)+\\*?(\\w+)\\s*\\(')
ENCLOSING_TYPE = re.compile('^(?:struct|enum|union)\\s+\\w+\\s*\\{')
ANONYMOUS_ENUM = re.compile('^enum\\s*\\{\\s*$')
SKIPPED_DIRECTIVE = re.compile('^#\\s*(?:include|if|ifdef|ifndef|elif|else|endif|pragma)\\b')
FIRST_ENUMERATOR = re.compile('^\\s+([A-Za-z_]\\w*)\\s*(?:=[^,]*)?,?\\s*$')
LOCATION_SPAN = re.compile('^([\\w./-]+):(\\d+)(?:-(\\d+))?$')
KERNELDOC_OPEN = '/**'
KERNELDOC_CLOSE = '*/'
COMMENT_BODY = ('*', '/*')
BLOCK_END = '};'
FORWARD_DECLARATION = re.compile('^struct\\s+(\\w+)\\s*;\\s*$')
STRUCT_DEFINITION = '^struct\\s+%s\\s*\\{'
SOURCE_SUFFIXES = ('.c', '.h')
KEYWORDS = ('if', 'for', 'while', 'switch', 'return', 'sizeof')
ENCLOSING_KEYWORDS = ('if', 'for', 'while', 'switch', 'return')

def intro_text(page, fence):
    """The prose above a fence: what lies between the previous heading, figure, table, list or
    excerpt and the fence, with its own first page line."""
    lines = page.lines
    out = []
    j = fence.start - 2
    first = None
    while j >= 0:
        line = lines[j]
        if line.startswith(('```', '#', '|')) or re.match('^\\s*[-*]\\s', line):
            break
        out.append(line)
        if line.strip():
            first = j + 1
        j -= 1
    return ('\n'.join(reversed(out)), first)

def defined_name(line):
    for pattern in (DEFINITION_TAGGED, DEFINITION_MACRO, DEFINITION_FUNCTION, DEFINITION_TABLE, DEFINITION_BY_MACRO, DEFINITION_VARIABLE):
        match = pattern.match(line)
        if match and match.group(1) not in KEYWORDS:
            return match.group(1)
    return None

def shown_all(body):
    out = []
    for i, line in enumerate(body):
        text = line.rstrip()
        if not is_code_line(text) or text.startswith(('\t', ' ')):
            continue
        match = MODULE_DEVICE_TABLE.match(text)
        if match:
            out.append((match.group(1), i))
            continue
        name = defined_name(text)
        if name:
            out.append((name, i))
    return out

def shown(body):
    """(name, kind, offset) of the construct the unit's first code line defines."""
    for i, line in enumerate(body):
        text = line.rstrip()
        if not is_code_line(text):
            continue
        if SKIPPED_DIRECTIVE.match(text):
            continue
        match = TYPEDEF_FUNCTION.match(text) or MODULE_DEVICE_TABLE.match(text)
        if match:
            return (match.group(1), 'definition', i)
        if ANONYMOUS_ENUM.match(text):
            for j in range(i + 1, len(body)):
                member = FIRST_ENUMERATOR.match(body[j].rstrip())
                if member:
                    return (member.group(1), 'definition', j)
            break
        name = defined_name(text)
        if name:
            return (name, 'definition', i)
        match = CONSTRUCT_PROTOTYPE.match(text)
        if match:
            return (match.group(1), 'definition', i)
        if NAME_LINE.match(text) and (not text.endswith(';')):
            return (NAME_LINE.match(text).group(1), 'definition', i)
        if RETURN_TYPE_LINE.match(text) and len(body) > i + 1:
            following = body[i + 1].rstrip()
            match = NAME_LINE.match(following)
            if match and (not following.endswith(';')):
                return (match.group(1), 'definition', i + 1)
        break
    return (None, 'body', 0)

def definition_named_at(text):
    match = NAME_LINE.match(text)
    if match and (not text.rstrip().endswith(';')):
        return match.group(1)
    match = ENCLOSING_FUNCTION.match(text)
    if match and (not text.rstrip().endswith(';')) and (match.group(1) not in ENCLOSING_KEYWORDS):
        return match.group(1)
    if ENCLOSING_TYPE.match(text):
        return re.match('^(?:struct|enum|union)\\s+(\\w+)', text).group(1)
    match = ARRAY_OPENER.match(text)
    if match:
        return match.group(1)
    return None

def in_kerneldoc(source, line):
    for i in range(min(line, len(source)) - 1, -1, -1):
        text = source[i].strip()
        if text.startswith(KERNELDOC_OPEN):
            return True
        if text.startswith(KERNELDOC_CLOSE):
            return False
        if not text.startswith(COMMENT_BODY):
            return False
    return False

def definition_below(source, line):
    i = line - 1
    while i < len(source) and (not source[i].strip().endswith(KERNELDOC_CLOSE)):
        i += 1
    i += 1
    while i < len(source) and (not source[i].strip()):
        i += 1
    if i >= len(source):
        return (None, None)
    name = definition_named_at(source[i])
    return (name, i + 1) if name else (None, None)

def enclosing(tree, path, line, cache):
    source = source_lines(tree, path, cache) or []
    if in_kerneldoc(source, line):
        name, at = definition_below(source, line)
        if name:
            return (name, at)
    for i in range(min(line, len(source)) - 1, -1, -1):
        text = source[i]
        if text.rstrip() == BLOCK_END and i < line - 1:
            return (None, None)
        name = definition_named_at(text)
        if name:
            return (name, i + 1)
    return (None, None)

def directory_definition(tree, path, name, cache):
    key = (os.path.dirname(path), name)
    if key in cache:
        return cache[key]
    cache[key] = None
    pattern = re.compile(STRUCT_DEFINITION % re.escape(name))
    directory = os.path.join(tree, os.path.dirname(path))
    try:
        entries = sorted(os.listdir(directory))
    except OSError:
        return None
    for entry in entries:
        if not entry.endswith(SOURCE_SUFFIXES):
            continue
        relative = os.path.join(os.path.dirname(path), entry)
        for n, text in enumerate(source_lines(tree, relative, cache) or [], 1):
            if pattern.match(text):
                cache[key] = (relative, n)
                return cache[key]
    return cache[key]

def hint_target(tree, path, line, cache):
    if tree is None or not line:
        return (path, line)
    source = source_lines(tree, path, cache) or []
    if line > len(source):
        return (path, line)
    match = FORWARD_DECLARATION.match(source[line - 1].strip())
    if not match:
        return (path, line)
    found = directory_definition(tree, path, match.group(1), cache)
    return found if found else (path, line)

def names_construct(text, candidates):
    for candidate in candidates:
        if re.match('^(?:struct |enum |union )?' + re.escape(candidate) + '(\\(\\))?$', text.strip()):
            return True
    return False

def introduction_state(intro, symbol, path, line, body):
    candidates = [symbol] + [n for n, _o in shown_all(body) if n != symbol] if symbol else []
    linked = [t.strip() for t, _u in CODE_LINK.findall(intro)]
    named = [c for c in candidates if any((names_construct(t, [c]) for t in linked))]
    if candidates and (candidates[0] in named or len(named) == len(candidates)):
        return ('linked', named, candidates)
    if named:
        return ('PART LINKED', named, candidates)
    if symbol and re.search('`' + re.escape(symbol) + '(\\(\\))?`', re.sub('\\[`[^`]+`\\]\\([^)]*\\)', ' ', intro)):
        return ('BARE mention', named, candidates)
    for text, _u in CODE_LINK.findall(intro):
        located = LOCATION_SPAN.match(text.strip())
        if located and located.group(1).split('/')[-1] == path.split('/')[-1] and (line <= int(located.group(2)) < line + len(body) + 1):
            return ('LOCATION LINK ONLY', named, candidates)
    return ('ABSENT', named, candidates)

def introduction_rows(page, inputs, *, known_only=False):
    """([(fence line, row text)], [state], [detail tuple]) for every excerpt unit with a
    provenance; the details carry what run_introductions turns into findings."""
    tree = inputs.tree if inputs is not None else None
    cache = inputs.cache if inputs is not None else {}
    rows, states, details = ([], [], [])
    for fence in page.excerpts:
        intro, intro_line = intro_text(page, fence)
        for unit in fence.units:
            if not unit.path:
                continue
            body = unit.lines
            symbol, kind, offset = shown(body)
            if known_only and symbol is None:
                continue
            definition_line = unit.line + offset if symbol else None
            if symbol is None and tree is not None:
                symbol, definition_line = enclosing(tree, unit.path, unit.line, cache)
                kind = 'body'
            state, named, candidates = introduction_state(intro, symbol, unit.path, unit.line, body)
            hint = hint_target(tree, unit.path, definition_line, cache)
            where = f'  define {hint[0]}:{hint[1]}' if symbol and hint[1] else ''
            rows.append((fence.start, f'{fence.start:5} {unit.path}:{unit.line:<5} {kind:10} {str(symbol):32} {state}{where}'))
            states.append(state)
            details.append((fence.start, unit.path, unit.line, kind, symbol, state, hint, intro_line, named, candidates))
    return (rows, states, details)

def introductions(page, inputs, *, known_only=False):
    rows, states, details = introduction_rows(page, inputs, known_only=known_only)
    findings = []
    for fence_line, path, line, kind, symbol, state, hint, intro_line, named, candidates in details:
        if state == 'linked':
            continue
        message = f'{path}:{line} {kind} {symbol}: {state} in the prose above the fence'
        if intro_line:
            message += f' (the prose from page line {intro_line})'
        if named:
            message += f"; linked: {', '.join(named)} of {len(candidates)} construct(s) shown"
        if symbol and hint[1]:
            message += f'; link it to {hint[0]}:{hint[1]}'
        findings.append(Finding(fence_line, 'review', message))
    introduced = sum((1 for s in states if s == 'linked'))
    footer = f'excerpt units={len(rows)} introduced-and-linked={introduced} residual={len(rows) - introduced}'
    yield from observations(findings, footer, [text for _l, text in rows], {'units': len(rows), 'introduced': introduced, 'residual': len(rows) - introduced})

def check(page, inputs):
    if not page.units:
        yield from introductions(page, None)
        return
    try:
        inputs.require('tree')
    except MissingInput:
        # Constructs shown in full can be checked from the page. Body slices
        # need the validated tree to identify their enclosing construct.
        yield from introductions(page, None, known_only=True)
        raise
    yield from introductions(page, inputs)
