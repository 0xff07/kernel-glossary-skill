"""Index guideline markers and discover their Python implementations."""
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SLUG = re.compile(r"^[a-z][a-z0-9-]*\.[a-z0-9][a-z0-9-]*$")
ITEM_MARKER = re.compile(r"^\s*(?:\d+\.|-)\s+\[([a-z][a-z0-9-]*\.[a-z0-9][a-z0-9-]*)(?:, ([a-z]+))?\]\s")
ROW_MARKER = re.compile(r"\|\s*([a-z][a-z0-9-]*\.[a-z0-9][a-z0-9-]*)(?:, ([a-z]+))?\s*\|\s*$")
SECTION_HEADING = re.compile(r"^## (.+?) \[([a-z][a-z0-9-]*)\]\s*$")
DOC_ORDER = ("kernel", "writing", "figures", "dossier", "checking", "campaign")


class RuleError(ValueError):
    """Invalid binding or explicit selection."""


def module_stem(rule_id):
    return rule_id.replace(".", "_").replace("-", "_")


@dataclass(frozen=True)
class Binding:
    """Internal runner metadata; check authors export RULE and check only."""
    id: str
    check: object
    home: str
    module_path: str
    test_path: str


def guideline_files(base):
    found = {p.stem: p for p in (Path(base) / "guidelines").glob("*.md")}
    return [found[d] for d in DOC_ORDER if d in found] + [found[d] for d in sorted(found) if d not in DOC_ORDER]


def parse_doc(path):
    sections, requirements = [], []
    current = fence = None
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        found = SECTION_HEADING.match(line)
        if found:
            current = found.group(2)
            sections.append({"slug": current, "heading": found.group(1), "line": line_number, "doc": Path(path).stem})
        found = ITEM_MARKER.match(line) or ROW_MARKER.search(line)
        if not found and re.search(r",\s*qa\s*[\]|]", line):
            raise RuleError(f"line {line_number}: malformed qa guideline marker")
        if found:
            requirements.append({"slug": found.group(1), "marker": found.group(2) or "read",
                                 "line": line_number, "section": current, "doc": Path(path).stem,
                                 "text": line.strip()})
    return sections, requirements


def load(base):
    """Bindings in guideline order, requirements, sections, and validation errors."""
    base = Path(base)
    requirements, sections, errors = [], [], []
    for path in guideline_files(base):
        try:
            found_sections, found_requirements = parse_doc(path)
            sections.extend(found_sections)
            requirements.extend(found_requirements)
        except (OSError, UnicodeError, RuleError) as error:
            errors.append(f"{path}: {error}")
    by_id, stems = {}, {}
    for item in requirements:
        slug = item["slug"]
        home = f"guidelines/{item['doc']}.md:{item['line']}"
        if slug in by_id:
            errors.append(f"{home}: duplicate guideline ID {slug}")
        by_id[slug] = item
        if item["marker"] not in ("qa", "read"):
            errors.append(f"{home}: unsupported marker {item['marker']!r}; use qa or leave unmarked")
        if slug.split(".")[0] != item["section"]:
            errors.append(f"{home}: {slug} is outside its own section")
        stem = module_stem(slug)
        if stem in stems and stems[stem] != slug:
            errors.append(f"{home}: filename collision: {slug} and {stems[stem]}")
        stems[stem] = slug
    modules = {}
    for path in sorted((base / "tools/qa/checks").glob("*.py")):
        if path.name == "__init__.py":
            continue
        relative = path.relative_to(base).as_posix()
        try:
            # Fresh source avoids stale bytecode for same-size edits within one timestamp.
            spec = importlib.util.spec_from_file_location(f"checks.{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            previous = sys.modules.get(spec.name)
            sys.modules[spec.name] = module
            try:
                exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
            except BaseException:
                if previous is None:
                    sys.modules.pop(spec.name, None)
                else:
                    sys.modules[spec.name] = previous
                raise
            slug = getattr(module, "RULE", None)
            if not isinstance(slug, str) or not SLUG.fullmatch(slug):
                raise RuleError("RULE must be a valid guideline ID")
            if slug in modules:
                raise RuleError(f"duplicate implementation of {slug}")
            if path.stem != module_stem(slug):
                raise RuleError(f"{slug} requires filename {module_stem(slug)}.py")
            if not callable(getattr(module, "check", None)):
                raise RuleError(f"{slug} must export callable check(page, inputs)")
            item = by_id.get(slug)
            if item is None or item["marker"] != "qa":
                raise RuleError(f"{slug} must refer to a guideline marked qa")
            modules[slug] = Binding(slug, module.check,
                                    f"guidelines/{item['doc']}.md:{item['line']}", relative,
                                    f"tools/qa/tests/test_{path.stem}.py")
        except (Exception, SystemExit) as error:
            errors.append(f"{relative}: {type(error).__name__}: {error}")
    for item in requirements:
        if item["marker"] == "qa" and item["slug"] not in modules:
            errors.append(f"{item['slug']}: qa marker has no usable check module")
    return [modules[i["slug"]] for i in requirements if i["slug"] in modules], requirements, sections, errors


def select(found, only=None):
    if only is None:
        return found
    requested = set(only)
    if not requested:
        raise RuleError("an explicit selection must name at least one rule")
    unknown = requested - {r.id for r in found}
    if unknown:
        raise RuleError("unknown check ID(s): " + ", ".join(sorted(unknown)))
    return [r for r in found if r.id in requested]
