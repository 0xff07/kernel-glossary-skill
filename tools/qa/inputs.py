"""Resolve and validate shared inputs once; checks ask for them with require()."""
import glob
import hashlib
import os
import re
import subprocess

from lint_record import qa_digest


class MissingInput(Exception):
    """A check cannot finish without this input."""


GIT_TIMEOUT = 60
COMMIT_ID = re.compile(r"\b[0-9a-f]{12,40}\b")
HEADER_FIELD = re.compile(r"^- (output path|campaign|documented version):\s*(.*)$")
# an EXEMPT verdict the engine reads: EXEMPT <rule-id>[/part] ["<fragment>"] [<page line>]: <ruling>,
# the fragment a piece of the flagged text (a double quote inside it written \"), the line only a
# hint, and the ruling the rest of the line
EXEMPT_LINE = re.compile(r"\bEXEMPT\s+([a-z][a-z0-9-]*\.[a-z0-9][a-z0-9-]*(?:/[a-z0-9-]+)?)"
                         r"((?:\s+(?:\d+|\"(?:[^\"\\\n]|\\.)+\"))+)\s*(?::\s*([^\n]*))?")
EXEMPT_KEY = re.compile(r"\"((?:[^\"\\\n]|\\.)+)\"|(\d+)")
EXEMPT_ESCAPE = re.compile(r"\\(\")")
DOCS = "docs"
PROGRESS = "progress"
WORKSHEET_SUFFIX = ".worksheet.md"
TREE_MARKERS = ("Kconfig",)


def skill_dir():
    """The skill checkout: the parent of tools/qa."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GitError(OSError):
    """A Git invocation failed, rather than returning a negative search result."""

    def __init__(self, arguments, returncode, stderr):
        self.returncode, self.stderr = returncode, stderr
        super().__init__(f"git {' '.join(arguments)}: {stderr.strip() or f'exit {returncode}'}")


def git(tree, *arguments, ok=(0,)):
    try:
        done = subprocess.run(["git", "-C", tree, *arguments], capture_output=True, text=True,
                              timeout=GIT_TIMEOUT, env={**os.environ, 'LC_ALL': 'C'})
    except (OSError, subprocess.SubprocessError) as error:
        raise GitError(arguments, None, str(error)) from error
    if done.returncode not in ok:
        raise GitError(arguments, done.returncode, done.stderr)
    return done.stdout


def has_git(tree):
    if not tree:
        return False
    try:
        return git(tree, "rev-parse", "--is-inside-work-tree").strip() == "true"
    except GitError as error:
        if error.returncode == 128 and 'not a git repository' in error.stderr:
            return False
        raise


def is_kernel_tree(path):
    return bool(path) and os.path.isdir(path) and all(os.path.exists(os.path.join(path, m)) for m in TREE_MARKERS)


def page_relative(page_path, base=None):
    return os.path.relpath(os.path.abspath(page_path), base or skill_dir()).replace(os.sep, "/")


def page_key(page_path, base=None):
    """The page's path under docs/ without its suffix: docs/usb4/router/tb-switch.md ->
    usb4/router/tb-switch; a page outside docs/ falls back to its basename."""
    relative = page_relative(page_path, base)
    if relative.startswith(DOCS + "/") and relative.endswith(".md"):
        return relative[len(DOCS) + 1:-len(".md")]
    return os.path.splitext(os.path.basename(page_path))[0]


def page_within(page_path, base=None):
    """The page's path under docs/<dir>/, the form a catalog row names: router/tb-switch.md."""
    relative = page_relative(page_path, base)
    parts = relative.split("/")
    if len(parts) >= 3 and parts[0] == DOCS:
        return parts[1], "/".join(parts[2:])
    return None, os.path.basename(page_path)


def source_lines(tree, relative_path, cache):
    if relative_path in cache:
        return cache[relative_path]
    try:
        cache[relative_path] = open(os.path.join(tree, relative_path), encoding="utf-8",
                                    errors="replace").read().split("\n")
    except OSError:
        cache[relative_path] = None
    return cache[relative_path]


def disk_line(tree, relative_path, line, cache):
    if tree is None:
        return None
    source = source_lines(tree, relative_path, cache)
    if source is None or line < 1 or line > len(source):
        return None
    return source[line - 1]


def sha256_of(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def worksheet_header(path):
    fields = {}
    try:
        for line in open(path, encoding="utf-8"):
            if line.startswith("## ") and not line.startswith("## HEADER") and fields:
                break
            found = HEADER_FIELD.match(line.rstrip("\n"))
            if found and found.group(1) not in fields:
                fields[found.group(1)] = found.group(2).strip()
    except OSError:
        return {}
    return fields


def worksheet_campaign(path, base):
    relative = os.path.relpath(os.path.abspath(path), os.path.join(base, PROGRESS)).replace(os.sep, "/")
    parts = relative.split("/")
    if parts[0] == ".." or len(parts) < 2:
        return os.path.basename(os.path.dirname(path))
    return parts[0]


def worksheet_verdict(path, page_path, head, base, active=None):
    """Why a worksheet is not this page's at this tree's commit, or '' when it is (worksheet.md
    [header])."""
    if not os.path.exists(path):
        return "does not exist"
    fields = worksheet_header(path)
    stated = fields.get("output path", "").split()[0].strip("`") if fields.get("output path") else ""
    if not stated:
        return "carries no output path in its HEADER"
    if os.path.normpath(stated) != os.path.normpath(page_relative(page_path, base)):
        return f"names {stated}, not this page"
    campaign = fields.get("campaign", "").split(" ")[0].strip("`")
    if not campaign:
        return "carries no campaign in its HEADER"
    directory = worksheet_campaign(path, base)
    if campaign != directory:
        return f"names campaign {campaign} but lies under progress/{directory}/"
    if active and campaign != active:
        return f"names campaign {campaign} but the active campaign is {active}"
    commits = COMMIT_ID.findall(fields.get("documented version", ""))
    if not commits:
        return "carries no documented version with its commit in its HEADER"
    if head and not (head.startswith(commits[0]) or commits[0].startswith(head)):
        return f"documents commit {commits[0][:12]}, not the tree's {head[:12]}"
    return ""


class Inputs:
    """The resolved inputs of one run."""

    def __init__(self, page_path, tree=None, worksheet=None, campaign=None, base=None, spec=None):
        self.page_path = page_path
        self.base = base or skill_dir()
        self.problems, self.notes = [], []
        self.cache = {}
        self.source_problems = []
        self.qa_digest = qa_digest(self.base)
        self.spec = spec                          # a campaign spec named outright
        self._resolve_tree(tree)
        self._resolve_worksheet(worksheet, campaign)
        self._resolve_baseline()
        self.page_digest = sha256_of(page_path)

    # ---- the tree ----

    def _resolve_tree(self, explicit):
        explicit = explicit or os.environ.get("KG_TREE")
        if explicit:
            candidate, how = os.path.abspath(explicit), "option"
        else:
            candidate, how = os.path.dirname(os.path.dirname(os.path.dirname(self.base))), "convention"
        self.tree_candidate, self.tree_how = candidate, how
        self.tree = candidate if is_kernel_tree(candidate) else None
        if self.tree is None:
            (self.problems if how == "option" else self.notes).append(
                f"no kernel tree at {candidate} ({how}); the rules that read source skip")
        self.git, self.tree_tag, self.tree_head = False, '', ''
        try:
            self.git = has_git(self.tree)
            if self.git:
                self.tree_head = git(self.tree, "rev-parse", "HEAD").strip()
                # A checkout between tags is valid input; it has no exact tag.
                tags = git(self.tree, 'tag', '--points-at', 'HEAD').splitlines()
                self.tree_tag = tags[0] if tags else ''
        except GitError as error:
            self.source_problems.append(str(error))
            self.problems.append(str(error))

    def bind_version(self, page):
        """The page's one version pin against the tree's tag; a mismatch is a problem."""
        previous = len(self.problems)
        try:
            self._validate_source(page)
        except GitError as error:
            self.problems.append(str(error))
        self.source_problems.extend(self.problems[previous:])

    def _validate_source(self, page):
        versions = page.versions()
        self.page_version = page.version()
        if len(versions) > 1:
            self.problems.append("the page pins several versions: " + ", ".join(
                f"{v} ({n})" for v, n in versions.most_common()))
        if self.tree and self.git and self.page_version:
            pinned = git(self.tree, "rev-parse", "--verify", "--quiet", self.page_version + "^{commit}", ok=(0, 1)).strip()
            if not COMMIT_ID.fullmatch(pinned or "x"):
                self.problems.append(f"the page pins {self.page_version} but the tree has no tag {self.page_version}")
            elif pinned != self.tree_head:
                self.problems.append(f"the page pins {self.page_version} ({pinned[:12]}) but the tree is at "
                                     f"{self.tree_head[:12]}" + (f", tagged {self.tree_tag}" if self.tree_tag else ", not at any tag"))
        if self.tree and self.git:
            files = page.cited_files()
            if files:
                status = git(self.tree, "status", "--porcelain", "--untracked-files=no", "--", *files)
                modified = sorted(line[3:].strip() for line in status.split("\n") if line.strip())
                tracked = set(git(self.tree, "ls-files", "--", *files).split("\n"))
                untracked = sorted(f for f in files if f not in tracked and
                                   not any(t.startswith(f.rstrip("/") + "/") for t in tracked))
                if modified:
                    self.problems.append("the tree has uncommitted changes in files the page cites: "
                                         + ", ".join(modified[:6]) + (" and more" if len(modified) > 6 else ""))
                if untracked:
                    self.problems.append("the page cites paths the commit does not track: "
                                         + ", ".join(untracked[:6]) + (" and more" if len(untracked) > 6 else ""))

    # ---- the worksheet ----

    def _resolve_worksheet(self, explicit, campaign):
        explicit = explicit or os.environ.get("KG_WORKSHEET")
        self.campaign = campaign or os.environ.get("KG_CAMPAIGN") or None
        name = page_key(self.page_path, self.base) + WORKSHEET_SUFFIX
        if explicit:
            candidates, how = [os.path.abspath(explicit)], "option"
        elif self.campaign:
            candidates, how = [os.path.join(self.base, PROGRESS, self.campaign, name)], "campaign"
        else:
            candidates, how = sorted(glob.glob(os.path.join(self.base, PROGRESS, "*", name))), "convention"
        self.worksheet_how = how
        self.worksheet_rejected = []
        accepted = []
        for path in candidates:
            why = worksheet_verdict(path, self.page_path, self.tree_head, self.base, self.campaign)
            if why:
                self.worksheet_rejected.append(f"worksheet {path} {why}; not used")
            else:
                accepted.append(path)
        if len(accepted) > 1:
            where = ", ".join(worksheet_campaign(p, self.base) for p in accepted)
            self.worksheet_rejected.append(f"ambiguous worksheet: {len(accepted)} campaigns name this page at this "
                                         f"commit ({where}); pass --campaign or $KG_CAMPAIGN; none used")
            accepted = []
        self.worksheet = accepted[0] if accepted else None
        if how == "option":
            self.problems.extend(self.worksheet_rejected)
        else:
            self.notes.extend(self.worksheet_rejected)
        if self.worksheet is None and not self.worksheet_rejected and how != "option":
            flat = os.path.splitext(os.path.basename(self.page_path))[0] + WORKSHEET_SUFFIX
            if flat != name:
                pattern = os.path.join(self.base, PROGRESS, self.campaign or "*", flat)
                for stale in sorted(glob.glob(pattern)):
                    mirrored = os.path.join(os.path.dirname(stale), name)
                    self.notes.append(f"a worksheet lies at the retired flat path {stale}; the mirrored path is "
                                      f"{mirrored} (move it there; it was not read)")
        if self.worksheet is None and not self.worksheet_rejected:
            self.notes.append("no worksheet found; the worksheet rules skip")
        self.worksheet_lines = (open(self.worksheet, encoding="utf-8").read().split("\n")
                              if self.worksheet else None)

    def exemptions(self):
        """The EXEMPT verdicts the worksheet's LINT section records for the engine (worksheet.md
        [lint]): [{rule, fragment, line, ruling, text}], the fragment a piece of the flagged text
        and the line an optional hint."""
        found = []
        for match in EXEMPT_LINE.finditer(self.worksheet_section("## LINT")):
            fragment, line = None, None
            for key in EXEMPT_KEY.finditer(match.group(2)):
                if key.group(1):
                    fragment = EXEMPT_ESCAPE.sub(r"\1", key.group(1))
                else:
                    line = int(key.group(2))
            found.append({"rule": match.group(1), "fragment": fragment, "line": line,
                          "ruling": (match.group(3) or "").strip(), "text": match.group(0).strip()})
        return found

    def worksheet_section(self, name):
        """The text under one H2 of the worksheet, or ''."""
        lines = self.worksheet_lines
        if lines is None or name not in lines:
            return ""
        start = lines.index(name)
        end = len(lines)
        for k in range(start + 1, len(lines)):
            if lines[k].startswith("## "):
                end = k
                break
        return "\n".join(lines[start + 1:end])

    # ---- the committed baseline ----

    def _resolve_baseline(self):
        """The page as HEAD of the skill checkout holds it, when it differs from disk."""
        self.baseline = None
        relative = page_relative(self.page_path, self.base)
        if relative.startswith(".."):
            return
        try:
            def run(*args):
                return subprocess.run(['git', '-C', self.base, *args], capture_output=True,
                                      text=True, timeout=GIT_TIMEOUT)
            repository = run('rev-parse', '--is-inside-work-tree')
            if repository.returncode:
                if 'not a git repository' in repository.stderr:
                    return
                raise OSError(repository.stderr.strip())
            head = run('rev-parse', '--verify', 'HEAD')
            if head.returncode:
                # An unborn repository has no committed baseline.
                history = run('rev-list', '--all', '--count')
                if history.returncode:
                    raise OSError(history.stderr.strip())
                if history.stdout.strip() == '0':
                    return
                raise OSError(head.stderr.strip())
            tracked = run('ls-tree', '--name-only', 'HEAD', '--', relative)
            if tracked.returncode:
                raise OSError(tracked.stderr.strip())
            if not tracked.stdout.strip():
                return
            done = run('show', f'HEAD:{relative}')
            if done.returncode:
                raise OSError(done.stderr.strip())
            if done.stdout != open(self.page_path, encoding='utf-8').read():
                self.baseline = done.stdout
        except (OSError, subprocess.SubprocessError) as error:
            self.problems.append(f'cannot read committed baseline: {error}')

    def require(self, name):
        """Return a resolved, usable input, or explain why execution cannot finish."""
        if name not in ('tree', 'git', 'worksheet', 'baseline'):
            raise ValueError(f"unknown input {name!r}")
        if name in ('tree', 'git') and self.source_problems:
            raise MissingInput('source validation failed: ' + '; '.join(self.source_problems))
        if name == 'tree' and self.tree is None:
            raise MissingInput('no kernel tree')
        if name == 'git' and not self.git:
            raise MissingInput('no git in the kernel tree')
        if name == 'worksheet' and self.worksheet is None:
            raise MissingInput('; '.join(self.worksheet_rejected) or 'no worksheet')
        if name == 'baseline' and self.baseline is None:
            raise MissingInput('no committed baseline differs from the page')
        return self.tree if name == 'git' else getattr(self, name)

    def complete(self, results):
        return not self.problems and not any(r.skipped or r.error for r in results)

    def missing(self, results):
        gaps = {}
        for r in results:
            if r.skipped:
                gaps.setdefault(r.skipped, []).append(r.rule.id)
        return [f"{why}: {', '.join(keys)}" for why, keys in gaps.items()]

    def incomplete_reason(self, results):
        return "; ".join(self.problems + self.missing(results) + [f"{r.rule.id}: {r.error}" for r in results if r.error])

    def report_lines(self):
        out = [f"kg 3  page {self.page_path}  tree {self.tree or '-'}"
               + (f" at {self.tree_tag}" if self.tree_tag else "") + f"  worksheet {self.worksheet or '-'}"]
        out += [f"   page sha256: {self.page_digest}  qa sha256: {self.qa_digest}"]
        out += [f"   FAIL  inputs: {p}" for p in self.problems]
        out += [f"   note: {n}" for n in self.notes]
        return out

    def as_dict(self):
        return {"page_digest": self.page_digest, "qa_digest": self.qa_digest, "tree": self.tree, "tree_tag": self.tree_tag, "tree_head": self.tree_head,
                "worksheet": self.worksheet, "campaign": self.campaign, "baseline": self.baseline is not None,
                "problems": self.problems, "notes": self.notes}
