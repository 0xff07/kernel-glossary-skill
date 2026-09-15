"""Shared parsing and reporting utilities."""
import re
FILE = re.compile('^[\\w.-]+\\.(?:c|h|S|rst|txt|json|yaml|dts|dtsi|py|sh)$')
LOCATION = re.compile('^((?:[\\w.-]+/)*[\\w.-]+\\.(?:c|h|S|rst|txt|json|yaml|dts|dtsi|py|sh)|(?:[\\w.-]+/)+[\\w.-]+):(\\d+)(?:-(\\d+))?$')
CONFIG_PREFIX = 'CONFIG_'
SPAN_CLIP = 44
REASON_CLIP = 80
LISTED_POSITIONS = 4
SETTLED_CLASSES = [('^-E[A-Z0-9]+$', 'error value (links.bare-spans settled class)'), ('^(0x[0-9a-fA-F]+|\\d+|true|false|NULL)$', 'literal value (links.bare-spans settled class)'), ('^[0-9a-f]{12,40}$', 'commit hash (links.bare-spans settled class)'), ('^(if|else|return|goto|switch|case|default|break|continue|for|while|do|sizeof|static|const|struct|enum|union)\\b.*$', 'C keyword excerpt (links.bare-spans settled class)'), ('^(/|\\.\\.?/|[\\w.-]+/)[\\w./-]*$', 'path string (settled ruling, kernel.md [links])'), ('^"[^"]*"$|^\\\'[^\\\']*\\\'$', 'string or character literal excerpt (links.bare-spans settled class)'), ('^\\S+\\s*(==|!=|<=|>=|<|>|=|%|\\|\\||&&|<<|>>)\\s*\\S+', 'expression span; a constituent symbol is linked nearby (settled ruling, kernel.md [links])')]

def classify(text):
    """The pre-filled reason for a bare span, marked (auto) for the writer to confirm."""
    for pattern, reason in SETTLED_CLASSES:
        if re.match(pattern, text.strip()):
            return '(auto) ' + reason
    return ''

def bare_span_rows(page):
    """The bare-only spans of the prose and of the catalog bullets' text, most occurrences first,
    each as (span, listing text) with its pre-filled reason; the bare-spans selector and the
    anchors listing print the same rows."""
    rows = []
    for span in sorted(page.bare_only_spans('prose'), key=lambda s: -s.bare):
        rows.append((span, f'bare {span.text[:SPAN_CLIP]:44s} x{span.bare} at {span.at[:LISTED_POSITIONS]} | {classify(span.text)[:REASON_CLIP]}'))
    for span in sorted(page.bare_only_spans('catalog'), key=lambda s: -s.bare):
        rows.append((span, f'bare in a catalog bullet {span.text[:SPAN_CLIP]:44s} x{span.bare} | {classify(span.text)[:REASON_CLIP]}'))
    return rows
