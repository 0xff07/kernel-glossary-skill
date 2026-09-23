"""Findings, internal execution results, exemptions and report formats."""
import collections
import json
import re
from dataclasses import dataclass, field

Finding = collections.namedtuple("Finding", "line severity message data", defaults=(None,))
Row = collections.namedtuple("Row", "line text flags")
SEVERITIES = ("FAIL", "review", "note")
LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
MIN_SENTENCE_WORDS = 6
SENTENCE_CLIP = 110
REPORTED_SENTENCES = 8


@dataclass
class Result:
    """Internal runner outcome; errors and missing inputs cannot be exempted."""
    rule: object
    findings: list = field(default_factory=list)
    skipped: str | None = None
    error: str | None = None

    @property
    def fails(self):
        return sum(f.severity == "FAIL" for f in self.findings)

    @property
    def reviews(self):
        return sum(f.severity == "review" for f in self.findings)

    def state(self):
        if self.error:
            return "ERROR"
        if self.fails:
            return "FAIL"
        if self.skipped:
            return "INCOMPLETE"
        if self.reviews:
            return "review"
        return f"{len(self.findings)} findings"


def observations(findings=(), summary="", rows=(), data=None, *, optional=None):
    """Emit findings and informational inventories without an author-side result object."""
    yield from findings
    for text in rows:
        yield Finding(None, "note", text, {"inventory": True})
    if summary or data:
        yield Finding(None, "note", summary or "measurements", data)
    if optional:
        yield Finding(None, "note", optional, {"optional": True})


def reading(rows=(), notes=(), summary="", data=None, *, severity="review"):
    """Turn reading rows into work items; retain their heuristic flags as observations."""
    for row in rows:
        yield Finding(row.line, severity, row.text, {"flags": sorted(row.flags)})
    for line, text in notes:
        yield Finding(line, "note", text)
    if summary or data:
        yield Finding(None, "note", summary or "measurements", data)


def fragment_matches(finding, fragment, page_lines):
    """Whether an EXEMPT fragment is a piece of the finding's message or of the page line it
    names, links reduced to their text."""
    haystacks = [finding.message]
    if finding.line and 0 < finding.line <= len(page_lines):
        raw = page_lines[finding.line - 1]
        haystacks += [raw, LINK.sub(r"\1", raw)]
    return any(fragment in h for h in haystacks)


def apply_exemptions(results, exemptions, page_lines):
    """Every FAIL or review finding an EXEMPT entry names becomes a note carrying the ruling.
    An entry names a finding by its rule and a fragment of the flagged text; a line number is
    only a hint that picks the finding on that line when the fragment matches several. Returns
    [(entry, status)] for the entries that matched nothing (stale) or several findings
    (ambiguous), neither of which exempts anything."""
    problems = []
    # Match every entry against the original observations. An earlier exemption
    # must not turn an ambiguous fragment into a match for one remaining finding.
    observations = [(result, k, finding) for result in results
                    for k, finding in enumerate(result.findings)
                    if finding.severity in ("FAIL", "review")]
    for entry in exemptions:
        if '/' in entry['rule']:
            problems.append((entry, 'legacy part reference; requires re-adjudication'))
            continue
        if not entry['fragment']:
            problems.append((entry, 'a text fragment is required'))
            continue
        candidates = [(result, k, finding) for result, k, finding in observations
                      if entry['rule'] == result.rule.id
                      and fragment_matches(finding, entry['fragment'], page_lines)]
        if len(candidates) > 1 and entry["line"]:
            on_line = [c for c in candidates if c[2].line == entry["line"]]
            if len(on_line) == 1:
                candidates = on_line
        if not candidates:
            problems.append((entry, "stale"))
            continue
        if len(candidates) > 1:
            problems.append((entry, f"ambiguous: {len(candidates)} findings match"))
            continue
        result, k, finding = candidates[0]
        ruling = entry["ruling"] or "no ruling given"
        result.findings[k] = Finding(finding.line, "note",
                                     f"EXEMPT in LINT ({ruling}); was {finding.severity}: {finding.message}",
                                     {"exempted": finding.severity, "observation": finding.data})
    return problems


def sentences(line):
    text = " ".join(LINK.sub(r"\1", line).split())
    out = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if re.search(r"\w", part)]
    return out or ([text] if text else [])


def baseline_sentences(committed):
    found = set()
    for line in committed.split("\n"):
        if line.strip():
            found.update(sentences(line))
    return found


def keyed_line(lines, n):
    line = lines[n]
    if not line.startswith("```"):
        return line
    k = n + 1
    while k < len(lines) and not lines[k].strip():
        k += 1
    return lines[k] if k < len(lines) else line


def provenance_tag(lines, baseline, line_number):
    if baseline is None or not line_number or line_number > len(lines):
        return ""
    found = sentences(keyed_line(lines, line_number - 1))
    if not found:
        return ""
    carried = sum(1 for s in found if s in baseline)
    if carried == len(found):
        return " [carried]"
    if carried == 0:
        return " [NEW]"
    return f" [mixed {carried}/{len(found)} carried]"


def prose_sentences(text):
    out = []
    in_fence = False
    for n, line in enumerate(text.split("\n"), 1):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip() or line.startswith(("#", "|", ">", "- ", "* ")):
            continue
        for sentence in sentences(line):
            if len(sentence.split()) >= MIN_SENTENCE_WORDS:
                out.append((sentence, n))
    return out


def reuse_lines(page_text, committed):
    """Sentences repeated on the page, and dropped or newly repeated against the committed page."""
    def by_sentence(found):
        where = {}
        for sentence, n in found:
            where.setdefault(sentence, []).append(n)
        return where
    now = by_sentence(prose_sentences(page_text))
    lines = []
    for sentence, at in [(s, a) for s, a in now.items() if len(a) > 1][:REPORTED_SENTENCES]:
        lines.append(f"repeated on the page at lines {' '.join(map(str, at))}: {sentence[:SENTENCE_CLIP]}")
    if committed is None:
        return lines
    before = by_sentence(prose_sentences(committed))
    for sentence in [s for s in before if s not in now][:REPORTED_SENTENCES]:
        lines.append(f"dropped since the commit: {sentence[:SENTENCE_CLIP]}")
    newly = [(s, at) for s, at in now.items() if len(at) > 1 and len(before.get(s, [])) < len(at)]
    for sentence, at in newly[:REPORTED_SENTENCES]:
        lines.append(f"newly repeated against the commit at lines {' '.join(map(str, at))}: {sentence[:SENTENCE_CLIP]}")
    return lines



def header(result):
    return f"== {result.rule.id}  {result.rule.home}  {result.state()}"


def finding_line(finding, tag=""):
    where = f"{finding.line}: " if finding.line else ""
    return f"   {finding.severity}: {where}{finding.message}{tag}"


def is_detail(finding):
    """An inventory row or a per-item detail: kept in --json, counted in the text report."""
    data = finding.data if isinstance(finding.data, dict) else {}
    return finding.severity == "note" and bool(data.get("inventory") or data.get("detail"))


def render_text(results, page_lines, baseline, inputs, state_line):
    """The text report: per rule, the FAIL and review findings and the notes a person reads, the
    summary note included; the inventory rows and per-item details are counted, --json keeps them."""
    out = list(inputs.report_lines())
    tally = collections.Counter()
    for result in results:
        out.append(header(result))
        withheld = 0
        for finding in result.findings:
            tally[finding.severity] += 1
            if is_detail(finding):
                withheld += 1
                continue
            out.append(finding_line(finding, provenance_tag(page_lines, baseline, finding.line)))
        if withheld:
            tally['withheld'] += withheld
            out.append(f"   {withheld} inventory line{'s' if withheld != 1 else ''}, in --json")
        if result.skipped:
            tally['incomplete'] += 1
            out.append(f"   INCOMPLETE: {result.skipped}")
        if result.error:
            tally['errors'] += 1
            out.append(f"   ERROR: {result.error}")
    out.append(f"== done: {tally['FAIL']} FAIL, {tally['review']} review, {tally['note']} note "
               f"({tally['withheld']} inventory lines in --json only), "
               f"{tally['errors']} engine errors, {tally['incomplete']} incomplete rules")
    out.append("== validation complete; review findings still require adjudication" if inputs.complete(results)
               else "== INCOMPLETE validation: " + inputs.incomplete_reason(results))
    out.append(state_line)
    return "\n".join(out), tally


def render_json(page_path, results, inputs, state, checklist=None):
    document = {"kg": 3, "page": page_path, "inputs": inputs.as_dict(),
                "results": {r.rule.id: {"id": r.rule.id, "home": r.rule.home,
                    "module": r.rule.module_path, "complete": not (r.skipped or r.error),
                    "skipped": r.skipped, "error": r.error,
                    "findings": [f._asdict() for f in r.findings]} for r in results},
                "complete": inputs.complete(results), "missing": inputs.missing(results), "state": state}
    if checklist is not None:
        document["checklist"] = [{"requirement": slug, "state": st, "detail": detail} for slug, st, detail in checklist]
    return json.dumps(document, indent=2)


def requirement_state(item, results):
    result = next((r for r in results if r.rule.id == item['slug']), None)
    if result is None:
        return ('read', 'by hand') if item['marker'] == 'read' else ('NOT RUN', 'no execution result')
    detail = f"FAIL={result.fails} review={result.reviews} note={sum(f.severity == 'note' for f in result.findings)}"
    if result.skipped or result.error:
        detail += '; ' + (result.error or result.skipped)
    return result.state(), detail


def render_checklist(requirements, results):
    return "\n".join(f"  {item['slug']:40} {state}: {detail}"
                     for item in requirements for state, detail in [requirement_state(item, results)])


def exit_status(results, inputs):
    if inputs.problems or any(r.fails or r.error for r in results):
        return 1
    return 0 if inputs.complete(results) else 2
