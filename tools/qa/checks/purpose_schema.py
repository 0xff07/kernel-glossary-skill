"""Checks for [purpose.schema]."""
import re
from pagemodel import CODE_LINK, prose_text
from report import Finding, observations
RULE = 'purpose.schema'
DENSE = ('C', 'D', 'T')
COUNT_WORDS = re.compile(r'\b(two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(stages?|steps?|parts?|pieces?|fragments?|excerpts?|blocks?|halves|writers?|readers?|calls?|cases?|branches?|places?|paths?|things)\b', re.I)
CLIP = 100

def schema(page, inputs):
    findings, listing = [], []
    counts = {'multi_block': 0, 'named': 0}
    for sub in page.subsections:
        dense = [b for b in sub['blocks'] if b.kind in DENSE]
        if len(dense) < 2:
            continue
        counts['multi_block'] += 1
        paragraphs = page.paragraph_texts(sub['numbered'])
        opener = paragraphs[0][1] if paragraphs else ''
        constructs = [b.text for b in dense if b.kind == 'C' and b.text]
        named_in_opener = [t.strip().strip('`') for t, _u in CODE_LINK.findall(opener)]
        def bare(name):
            return name.split()[-1].rstrip('()') if name.split() else name
        shown = [c for c in constructs if any(bare(c) == bare(n) for n in named_in_opener)]
        counted = COUNT_WORDS.search(prose_text(opener))
        ok = bool(shown) or bool(counted)
        counts['named'] += ok
        listing.append(f"{sub['line']:5} [{sub['title'][:36]}] blocks={len(dense)} constructs={', '.join(constructs[:4]) or '-'} opener names={', '.join(shown) or '-'}{' count=' + counted.group(0) if counted else ''}")
        if not ok:
            findings.append(Finding(sub['line'], 'review', f"[{sub['title'][:40]}] has {len(dense)} blocks and its opening paragraph names none of the constructs they show ({', '.join(constructs[:3]) or 'figures and tables'}); give the reader the parts before the first block"))
    footer = f"multi-block-subsections={counts['multi_block']} schema-named={counts['named']}"
    yield from observations(findings, footer, listing, dict(counts))

def check(page, inputs):
    yield from schema(page, inputs)
