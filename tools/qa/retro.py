"""kg retro: per rule, what the first pass found over the pages a workspace's first-pass records
hold, and the EXEMPT lines its worksheets carry. Sums only: what they mean for a rule is read
(DESIGN.md, retiring a check)."""
import json
import re
from collections import Counter
from pathlib import Path

import rules

FIRST_PASS_SUFFIX = ".first-pass.json"
WORKSHEET_SUFFIX = ".worksheet.md"
EXEMPT = re.compile(r"^EXEMPT\s+([a-z][a-z0-9-]*\.[a-z0-9][a-z0-9-]*)\b")


def page_of(path, root, suffix):
    return path.relative_to(root).as_posix()[:-len(suffix)]


def read_record(path, root):
    """{page, date, converted, rules: {rule: (fail, review)}} from one first-pass record; a record
    `kg check` wrote names every rule that ran, one converted from a First pass table
    names only the rules that hit."""
    document = json.loads(path.read_text(encoding="utf-8"))
    counts = {}
    for rule, entry in (document.get("rules") or {}).items():
        if rules.SLUG.match(rule) and isinstance(entry, dict):
            counts[rule] = (int(entry.get("FAIL", 0)), int(entry.get("review", 0)))
    return {"page": page_of(path, root, FIRST_PASS_SUFFIX), "date": document.get("date"),
            "converted": bool(document.get("converted")), "rules": counts}


def read_exemptions(path):
    """The EXEMPT lines of one worksheet, counted per rule."""
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    return Counter(m.group(1) for line in lines if (m := EXEMPT.match(line)))


def gather(root):
    """(records, exemptions): the first-pass records under `root` in path order, and the EXEMPT
    counts of every worksheet under it, keyed by page."""
    root = Path(root)
    records = [read_record(path, root) for path in sorted(root.rglob("*" + FIRST_PASS_SUFFIX))]
    exemptions = {page_of(path, root, WORKSHEET_SUFFIX): read_exemptions(path)
                  for path in sorted(root.rglob("*" + WORKSHEET_SUFFIX))}
    return records, exemptions


def known_rules(base):
    """The qa rules of the skill, in guideline order."""
    _found, requirements, _sections, _errors = rules.load(base)
    return [item["slug"] for item in requirements if item["marker"] == "qa"]


def summarize(records, exemptions, known):
    """One row per rule, the known rules in guideline order and then the rules the records or the
    worksheets name that the skill no longer carries: the records naming the rule, those with a
    hit, the first-pass FAIL and review totals, and the EXEMPT lines written against it."""
    named = []
    for record in records:
        named.extend(slug for slug in record["rules"] if slug not in named)
    for counter in exemptions.values():
        named.extend(slug for slug in counter if slug not in named)
    rows = []
    for slug in list(known) + [slug for slug in named if slug not in known]:
        sample = [record for record in records if slug in record["rules"]]
        rows.append({"rule": slug, "known": slug in known, "pages": len(sample),
                     "hit_pages": sum(1 for record in sample if sum(record["rules"][slug]) > 0),
                     "fail": sum(record["rules"][slug][0] for record in sample),
                     "review": sum(record["rules"][slug][1] for record in sample),
                     "exempt": sum(counter.get(slug, 0) for counter in exemptions.values())})
    return rows


def render(root, records, exemptions, rows, rule=None):
    """The report lines: a header, then the per-rule table, or the per-page listing of one rule."""
    converted = sum(1 for record in records if record["converted"])
    plural = lambda n, word: f"{n} {word}{'s' if n != 1 else ''}"
    out = [f"retrospective over {plural(len(records), 'first-pass record')} and "
           f"{plural(len(exemptions), 'worksheet')} in {root}"
           + (f" ({plural(converted, 'record')} converted from a First pass table, naming only the rules that hit)"
              if converted else "")]
    if rule:
        out.append(f"{'page':40} {'date':10} {'FAIL':>5} {'review':>7} {'exempt':>7}")
        by_page = {record["page"]: record for record in records}
        for page in sorted(set(by_page) | set(exemptions)):
            record = by_page.get(page)
            counts = record["rules"].get(rule) if record else None
            exempt = exemptions.get(page, Counter()).get(rule, 0)
            if counts is None and not exempt:
                continue
            fail, review = counts or (0, 0)
            tail = "" if counts is not None else "  (no first-pass record naming the rule)"
            out.append(f"{page[:40]:40} {(record or {}).get('date') or '-':10} {fail:>5} {review:>7} {exempt:>7}{tail}")
        return out
    width = max([len(row["rule"]) for row in rows] + [4])
    line = lambda row: f"{row['rule']:{width}} {row['pages']:>5} {row['hit_pages']:>5} {row['fail']:>5} {row['review']:>6} {row['exempt']:>6}"
    out.append(f"{'rule':{width}} {'pages':>5} {'hit':>5} {'FAIL':>5} {'review':>6} {'exempt':>6}")
    out.extend(line(row) for row in rows if row["known"])
    retired = [row for row in rows if not row["known"]]
    if retired:
        out.append("rules the records or the worksheets name that the skill no longer carries:")
        out.extend(line(row) for row in retired)
    return out
