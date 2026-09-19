"""Shared interpretation of human check-pass records and their content digests."""
import hashlib
import re
from pathlib import Path

RECORD = re.compile(r"\bLINTED\s+(\S+)\s+page sha256:\s*([0-9a-f]{64})(?:[ \t]+qa sha256:[ \t]*([0-9a-f]{64}))?", re.I)


def qa_digest(base):
    base = Path(base)
    paths = list((base / "guidelines").glob("*.md"))
    paths += [p for p in (base / "tools/qa").rglob("*.py")
              if "tests" not in p.relative_to(base / "tools/qa").parts]
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.relative_to(base).as_posix()):
        relative = path.relative_to(base).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big") + relative)
        digest.update(len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def page_state_of(inputs):
    """(state, reason, record), independent of the lint check's reporting."""
    if inputs.worksheet_lines is None:
        return "WRITTEN", "no worksheet on this machine", None
    records = RECORD.findall(inputs.worksheet_section("## LINT"))
    if not records:
        return "WRITTEN", "no LINTED record in the worksheet's LINT section", None
    date, page, qa = records[-1]
    record = (date, page.lower(), qa.lower())
    if record[1] != inputs.page_digest:
        return "WRITTEN", "the page was edited after the check pass", record
    if not record[2]:
        return "WRITTEN", "legacy LINTED record has no QA digest; repeat the check pass", record
    if record[2] != inputs.qa_digest:
        return "WRITTEN", "the guidelines or QA code changed after the check pass", record
    return "LINTED", f"the LINT record of {date} names the current page and QA digests", record
