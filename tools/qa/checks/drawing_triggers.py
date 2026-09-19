"""Checks for [drawing.triggers]."""
import re
from pagemodel import CODE_LINK, prose_text
from report import Finding, observations
RULE = 'drawing.triggers'
COMMENT_STARTS = ('/*', '*', '*/', '//')
ENUM_OPEN = re.compile(r'^(?:typedef\s+)?enum\b[^;{]*\{')
ENUMERATOR = re.compile(r'^\s+([A-Z][A-Z0-9_]*)\b')
DEFINITION_OPEN = re.compile(r'^(?:typedef\s+)?(?:struct|union)\s+\w+\s*\{')
ENUM_LIKE = re.compile(r'^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+){2,}$')
ACTOR_PAIRS = [('parent', 'child'), ('upstream', 'downstream'), ('host', 'device'), ('producer', 'consumer'), ('initiator', 'target')]
RESHAPE = re.compile(r'\b(list_add(?:_tail)?|list_del(?:_init)?|list_move(?:_tail)?|hlist_add_head|hlist_del|list_splice|kzalloc\w*|kfree|kvfree|device_add|device_del|put_device)\b')
TOPOLOGY = re.compile(r'\b(tb_switch_parent|device_for_each_child|tb_upstream_port|tb_port_remote|tb_switch_depth)\b')
ORDINALS = re.compile(r'(?:^|[.!?]\s+)(First|Then|Next|After that|Finally|Last)\b,?', re.M)
MIN_STATES, MIN_MEMBERS, MIN_ACTOR_MENTIONS, MIN_ORDINALS, MIN_RESHAPE = 3, 6, 2, 3, 2
KINDS = ('state-set', 'actors', 'layout', 'reshaping', 'topology', 'sequence')

def code_lines(body):
    return [l for l in body if l.strip() and not l.strip().startswith(COMMENT_STARTS)]

def triggers_of(page, sub):
    """{kind: reason} for the shapes the subsection's prose and excerpts carry."""
    bodies = [b.stats.get('body', []) for b in sub['blocks'] if b.kind == 'C' and isinstance(b.stats, dict)]
    prose = ' '.join(t for _n, t in page.paragraph_texts(sub['numbered']))
    plain = prose_text(prose).lower()
    found = {}
    states = 0
    for body in bodies:
        code = code_lines(body)
        if code and ENUM_OPEN.match(code[0]):
            states = max(states, sum(1 for l in code[1:] if ENUMERATOR.match(l)))
    families = {}
    for text, _u in CODE_LINK.findall(prose):
        t = text.strip().strip('`')
        if ENUM_LIKE.match(t):
            families.setdefault('_'.join(t.split('_')[:3]), set()).add(t)
    family = max((len(v) for v in families.values()), default=0)
    if max(states, family) >= MIN_STATES:
        found['state-set'] = f'a set of {max(states, family)} named states: state-transition graph, or the two-field state pair'
    for a, b in ACTOR_PAIRS:
        na = len(re.findall(r'\b' + a + r'\b', plain))
        nb = len(re.findall(r'\b' + b + r'\b', plain))
        if na >= MIN_ACTOR_MENTIONS and nb >= MIN_ACTOR_MENTIONS:
            found['actors'] = f'{a} and {b} hand work across ({na} and {nb} mentions): swimlane sequence'
            break
    for body in bodies:
        code = code_lines(body)
        if code and DEFINITION_OPEN.match(code[0]):
            members = sum(1 for l in code[1:] if l.rstrip().endswith(';'))
            if members >= MIN_MEMBERS:
                found['layout'] = f'a definition of {members} members: side-by-side struct comparison, linked structs, or a memory strip'
                break
    hits = sorted({m.group(1) for body in bodies for l in body for m in RESHAPE.finditer(l)})
    if len(hits) >= MIN_RESHAPE:
        found['reshaping'] = f"{', '.join(hits[:3])}: before-and-after transformation"
    hits = sorted({m.group(1) for body in bodies for l in body for m in TOPOLOGY.finditer(l)})
    if len(re.findall(r'\bdepth\b', plain)) >= 2:
        hits.append('depth')
    if hits:
        found['topology'] = f"{', '.join(hits[:3])}: topology with a boundary, or parent and children fan-out"
    ordinals = len(ORDINALS.findall(prose_text(prose)))
    if ordinals >= MIN_ORDINALS:
        found['sequence'] = f'{ordinals} ordered steps: swimlane sequence or lifetime Gantt'
    return found

def candidates(page, inputs):
    findings, listing = [], []
    counts = {'subsections': 0, 'with_figure': 0, 'candidates': 0}
    counts.update({k: 0 for k in KINDS})
    for sub in page.subsections:
        counts['subsections'] += 1
        if sub['figures']:
            counts['with_figure'] += 1
            continue
        found = triggers_of(page, sub)
        if not found:
            continue
        counts['candidates'] += 1
        for kind in found:
            counts[kind] += 1
        reasons = '; '.join(found.values())
        listing.append(f"{sub['line']:5} [{sub['title'][:40]}] {', '.join(found)}")
        findings.append(Finding(sub['line'], 'review', f"[{sub['title'][:40]}] carries a shape of the trigger table and no figure: {reasons}; draw it, or record why the shape is not the point here", {'triggers': sorted(found)}))
    footer = (f"subsections={counts['subsections']} with-figure={counts['with_figure']} candidates={counts['candidates']} "
              + ' '.join(f"{k}={counts[k]}" for k in KINDS))
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    yield from candidates(page, inputs)
