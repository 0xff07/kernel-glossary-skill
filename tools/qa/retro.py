"""kg retro: per rule, what the checks found on the first pass of every page a campaign's
worksheets record, for the retrospective that decides which checks to keep."""
import re
from collections import Counter
from pathlib import Path

import rules

FIRST_PASS = re.compile(r"^(?:#{1,6}\s*|\*\*\s*)?first pass\b", re.I)
EXEMPT = re.compile(r"^EXEMPT\s+([a-z][a-z0-9-]*\.[a-z0-9][a-z0-9-]*)\b")
LINTED = re.compile(r"^LINTED\s+(\d{4}-\d{2}-\d{2})\b")
GUARD_PAGES = 20   # pages without a hit before a check reads as a guard nobody needs
NOISE_HITS = 5     # hits before an exempted share says anything
NOISE_SHARE = 0.7


def first_pass_table(lines):
    """{slug: (fail, review)} from the table under the first line that reads 'First pass', or
    None when the worksheet records none."""
    for i, line in enumerate(lines):
        if not FIRST_PASS.match(line.strip()):
            continue
        j = i + 1
        while j < len(lines) and not lines[j].startswith("|"):
            if lines[j].startswith("#"):
                break
            j += 1
        table = {}
        while j < len(lines) and lines[j].startswith("|"):
            cells = [cell.strip() for cell in lines[j].strip().strip("|").split("|")]
            slug = cells[0].strip("`*").strip() if cells else ""
            numbers = [int(cell) for cell in cells[1:] if cell.isdigit()]
            if rules.SLUG.match(slug) and len(numbers) >= 2:
                table[slug] = (numbers[0], numbers[1])
            j += 1
        if table:
            return table
    return None


def read_worksheet(path, root):
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    dates = [m.group(1) for line in lines if (m := LINTED.match(line))]
    return {"page": path.relative_to(root).as_posix()[:-len(".worksheet.md")],
            "first": first_pass_table(lines),
            "exempt": Counter(m.group(1) for line in lines if (m := EXEMPT.match(line))),
            "date": dates[-1] if dates else None}


def gather(root):
    """One record per worksheet under `root`, in path order."""
    root = Path(root)
    return [read_worksheet(path, root) for path in sorted(root.rglob("*.worksheet.md"))]


def known_rules(base):
    """The qa rules of the skill, in guideline order."""
    _found, requirements, _sections, _errors = rules.load(base)
    return [item["slug"] for item in requirements if item["marker"] == "qa"]


def summarize(pages, known):
    """One row per rule: the known rules in order, then rules the worksheets name that the skill no
    longer carries. Hits, exemptions and the share come from the pages with a first-pass record;
    `exempt_all` counts the EXEMPT lines of every worksheet."""
    recorded = [page for page in pages if page["first"]]
    seen = []
    for page in recorded:
        seen.extend(slug for slug in page["first"] if slug not in seen)
    for page in pages:
        seen.extend(slug for slug in page["exempt"] if slug not in seen)
    rows = []
    for slug in list(known) + [slug for slug in seen if slug not in known]:
        fails = sum(page["first"].get(slug, (0, 0))[0] for page in recorded)
        reviews = sum(page["first"].get(slug, (0, 0))[1] for page in recorded)
        hit = [page for page in recorded if sum(page["first"].get(slug, (0, 0))) > 0]
        exempt = sum(page["exempt"].get(slug, 0) for page in recorded)
        exempt_all = sum(page["exempt"].get(slug, 0) for page in pages)
        hits = fails + reviews
        share = min(exempt / hits, 1.0) if hits else None
        last = max(hit, key=lambda page: (page["date"] or "", page["page"])) if hit else None
        notes = []
        if slug not in known:
            notes.append("not a rule now")
        if not hit and len(recorded) >= GUARD_PAGES:
            notes.append(f"no hit in {len(recorded)} pages")
        if hits >= NOISE_HITS and share is not None and share >= NOISE_SHARE:
            notes.append(f"{share:.0%} exempt")
        rows.append({"rule": slug, "pages": len(recorded), "hit_pages": len(hit), "fail": fails,
                     "review": reviews, "exempt": exempt, "exempt_all": exempt_all, "share": share, "last": last,
                     "note": "; ".join(notes)})
    return rows


def render(root, pages, rows, rule=None):
    """The report lines: a header, then the per-rule table, or the per-page listing of one rule."""
    recorded = [page for page in pages if page["first"]]
    missing = len(pages) - len(recorded)
    out = [f"retrospective over {len(recorded)} page{'s' if len(recorded) != 1 else ''} in {root}"
           f" ({missing} worksheet{'s' if missing != 1 else ''} without a first-pass record)"]
    if rule:
        out.append(f"{'page':40} {'date':10} {'FAIL':>5} {'review':>7} {'exempt':>7}")
        for page in pages:
            fail, review = page["first"].get(rule, (0, 0)) if page["first"] else (0, 0)
            exempt = page["exempt"].get(rule, 0)
            if page["first"] is None and not exempt:
                continue
            tail = "" if page["first"] else "  (no first-pass record)"
            out.append(f"{page['page'][:40]:40} {page['date'] or '-':10} {fail:>5} {review:>7} {exempt:>7}{tail}")
        return out
    width = max([len(row["rule"]) for row in rows] + [4])
    out.append(f"{'rule':{width}} {'pages':>5} {'hits':>5} {'FAIL':>5} {'review':>6} {'exempt':>6} {'share':>5} {'all-ex':>6}  {'last hit':42} note")
    for row in rows:
        share = f"{row['share']:.0%}" if row["share"] is not None else "-"
        last = f"{row['last']['page'][:31]} {row['last']['date'] or ''}".strip() if row["last"] else "-"
        out.append(f"{row['rule']:{width}} {row['pages']:>5} {row['hit_pages']:>5} {row['fail']:>5} {row['review']:>6} "
                   f"{row['exempt']:>6} {share:>5} {row['exempt_all']:>6}  {last:42} {row['note']}".rstrip())
    return out
