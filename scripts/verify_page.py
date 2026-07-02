#!/usr/bin/env python3
"""Machine verifier for kernel-glossary pages.

Checks, per page:
  1. Every Elixir link: target file exists in the local kernel tree, the cited
     line is in range, and the linked symbol text appears at/near the cited
     line (definition-line anchoring check).
  2. Every fenced ```c block: appears verbatim (modulo '...' elision lines and
     trailing whitespace) as a contiguous run in the on-disk file named by its
     /* path:line */ provenance comment (or any file cited on the page).
  3. Gate A banned-pattern sweep, fence-aware (prose only).

The Elixir version tag (e.g. v7.0) is auto-detected per page from the first
Elixir link, so the same script serves any documented kernel version.

Usage: verify_page.py [--tree /path/to/kernel] <page.md> [<page.md> ...]
       --tree defaults to $KERNEL_TREE, else the current directory.
Exit code 0 = all clean, 1 = findings printed.

Known false-positive classes that need a human/agent adjudication pass (the
script cannot see them; do NOT "fix" a page to silence them without checking):
  - expression spans like `` `a | B` `` linking one constituent symbol
  - syscall-name links `mmap(2)` anchored at the kernel entry point
  - designated-initializer citations anchored at the initializer line
  - hyphenated compounds containing hedge words ("read-mostly" is exempt and
    handled; new compounds may not be)
  - macro-generated accessors whose generator stem heuristics miss
"""
import argparse
import os
import re
import sys
from pathlib import Path

TREE = Path(".")

VERSION_RE = re.compile(r"https://elixir\.bootlin\.com/linux/([^/]+)/source/")


def make_link_res(version):
    v = re.escape(version)
    elixir_re = re.compile(
        r"\]\(https://elixir\.bootlin\.com/linux/" + v + r"/source/([^#()\s]+?)(?:#L(\d+))?\)"
    )
    linkline_re = re.compile(
        r"\[([^\]]+)\]\(https://elixir\.bootlin\.com/linux/" + v + r"/source/([^#()\s]+)#L(\d+)\)"
    )
    return elixir_re, linkline_re


GATE_A = [
    ("em-dash", re.compile("—")),
    ("label-colon", re.compile(r"^[A-Z][^:`]{2,80}: [a-z]")),
    ("editorializing", re.compile(
        r"the reasoning|is the key|matters because|the pattern is|\bcrucial\b|"
        r"\belegant\b|cornerstone|linchpin|worthwhile|is essential|is what makes",
        re.I)),
    ("banned-word", re.compile(r"\b(contract|tall(?:y|ies|ied|ying)|canonical|vtable)\b", re.I)),
    ("hedge", re.compile(
        r"\b(usually|typically|generally|normally|commonly|(?<!-)mostly|in practice|tends to)\b",
        re.I)),
    ("arm-word", re.compile(r"\barms?\b", re.I)),
    ("internal-md-link", re.compile(r"\]\((?!https?://)[^)]*\.md\)")),
    ("negative-notX", re.compile(r", not [a-z]+[.,]")),
]
HEADING_BAD = re.compile(r"^#{2,4} (Why|How|Where|What)\b|^#{2,4} .*\?\s*$")


def split_fences(lines):
    """Yield (in_fence, line) pairs."""
    fence = False
    for ln in lines:
        if ln.startswith("```"):
            fence = not fence
            yield True, ln
        else:
            yield fence, ln


def extract_c_blocks(lines):
    blocks, cur, lang, in_f = [], [], None, False
    for ln in lines:
        if ln.startswith("```"):
            if not in_f:
                in_f, lang, cur = True, ln.strip()[3:], []
            else:
                if lang == "c":
                    blocks.append(cur)
                in_f = False
        elif in_f:
            cur.append(ln)
    return blocks


def norm(s):
    return s.rstrip()


PROV_RE = re.compile(r"^\s*/\* ([^\s:*]+):(\d+)(?:[^*]*) \*/\s*$")


def block_in_file(block, file_lines):
    """Verbatim contiguous match allowing '...'-only elision lines."""
    segs, cur = [], []
    for ln in block:
        if ln.strip() in ("...", "/* ... */", "// ...", "…"):
            if cur:
                segs.append(cur)
                cur = []
        else:
            cur.append(norm(ln))
    if cur:
        segs.append(cur)
    if not segs:
        return True
    fl = [norm(x) for x in file_lines]

    def find_seg(seg, start):
        n = len(seg)
        for i in range(start, len(fl) - n + 1):
            if fl[i:i + n] == seg:
                return i + n
        return -1

    pos = 0
    for seg in segs:
        pos = find_seg(seg, pos)
        if pos < 0:
            return False
    return True


SYM_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def link_symbols(text):
    """All candidate symbol names from a link text: `func()`, `struct foo`,
    `'\\<sym\\>':'path'`, `MACRO`, `a->b`, `x | Y` expressions."""
    text = text.strip("`")
    m = re.search(r"\\<(?:struct |enum |union )?([A-Za-z_][A-Za-z0-9_]*)\\>", text)
    if m:
        syms = [m.group(1)]
    elif "/" in text or re.match(r"^[\w.-]+\.(h|c|rst|S):?\d*$", text):
        return []  # path or file-location reference
    else:
        t = re.sub(r"\b(struct|enum|union)\s+", "", text).strip("'\"")
        syms = [s for s in SYM_RE.findall(t) if len(s) >= 4 or "_" in s]
        # field names after -> or . are the linked symbol even when short
        syms += re.findall(r"(?:->|\.)([A-Za-z_][A-Za-z0-9_]*)", t)
    out = []
    for s in syms:
        out.append(s)
        if s.startswith("CONFIG_"):
            out.append(s[len("CONFIG_"):])  # Kconfig files drop the prefix
        else:
            out.append(s + "_noprof")  # alloc_hooks wrapper convention
        m2 = re.match(r"^(?:__)?(?:Set|Clear|TestSet|TestClear|Test)?Page([A-Z]\w+)$", s)
        if m2:
            out.append(m2.group(1))  # PAGEFLAG(X, ...) generator stem
    return out


def verify(page):
    findings = []
    raw = Path(page).read_text().splitlines()
    text = "\n".join(raw)

    vm = VERSION_RE.search(text)
    version = vm.group(1) if vm else None
    if version:
        elixir_re, linkline_re = make_link_res(version)
    else:
        elixir_re = linkline_re = None

    # 1. Elixir links
    cited_files = set()
    n_links = 0
    if elixir_re:
        for lineno, ln in enumerate(raw, 1):
            for m in elixir_re.finditer(ln):
                n_links += 1
                rel, lstr = m.group(1), m.group(2)
                f = TREE / rel
                if not f.is_file():
                    if f.is_dir() and not lstr:
                        continue  # Elixir directory-listing link
                    findings.append(f"LINK missing file {rel} (page line {lineno})")
                    continue
                cited_files.add(rel)
                if lstr:
                    target = int(lstr)
                    flines = f.read_text(errors="replace").splitlines()
                    if target > len(flines):
                        findings.append(
                            f"LINK line out of range {rel}#L{target} ({len(flines)} lines) (page line {lineno})")

    # symbol-near-line check
    checked = set()
    n_symchecks = 0
    if linkline_re:
        for lineno, ln in enumerate(raw, 1):
            for m in linkline_re.finditer(ln):
                text_, rel, target = m.group(1), m.group(2), int(m.group(3))
                key = (text_, rel, target)
                if key in checked:
                    continue
                checked.add(key)
                syms = link_symbols(text_)
                f = TREE / rel
                if not syms or not f.is_file():
                    continue
                flines = f.read_text(errors="replace").splitlines()
                if target > len(flines):
                    continue
                n_symchecks += 1
                lo = max(0, target - 6)
                hi = min(len(flines), target + 5)
                window = "\n".join(flines[lo:hi])
                ok = any(re.search(r"\b" + re.escape(s) + r"\b", window) for s in syms)
                if not ok and any(s.endswith("_") or text_.strip("`").endswith("*") for s in syms):
                    # wildcard-group link (FOO_* anchored at the family's first member)
                    ok = any(re.search(r"\b" + re.escape(s.rstrip("_")) + r"[A-Za-z0-9_]*", window) for s in syms)
                if not ok and ("TYPE_OPS(" in window or "PAGEFLAG(" in window or "_FLAG(" in window
                               or "INTERVAL_TREE_DEFINE(" in window or "DEFINE_" in window):
                    # macro-generated accessors: match the symbol's stem parts
                    ok = any(re.search(r"\b" + re.escape(part) + r"\b", window, re.I)
                             for s in syms for part in s.lower().split("_") if len(part) > 3)
                if not ok:
                    findings.append(
                        f"SYMBOL '{syms[0]}' not within ±5 of {rel}#L{target} (page line {lineno})")

    # 2. C blocks
    blocks = extract_c_blocks(raw)
    unmatched = []
    file_cache = {}

    def get_file(rel):
        if rel not in file_cache:
            p = TREE / rel
            file_cache[rel] = p.read_text(errors="replace").splitlines() if p.is_file() else []
        return file_cache[rel]

    for i, blk in enumerate(blocks, 1):
        if not blk:
            continue
        # split into units: each interior /* path:line */ starts a new unit
        units = []  # (relpath_or_None, [lines])
        cur_rel, cur = None, []
        for ln in blk:
            pm = PROV_RE.match(ln)
            if pm:
                if cur:
                    units.append((cur_rel, cur))
                cur_rel, cur = pm.group(1), []
            else:
                cur.append(ln)
        if cur:
            units.append((cur_rel, cur))
        for rel, body in units:
            while body and not body[0].strip():
                body = body[1:]
            while body and not body[-1].strip():
                body = body[:-1]
            if not any(l.strip() and l.strip() != "..." for l in body):
                continue
            ok = False
            if rel:
                if not (TREE / rel).is_file():
                    unmatched.append(f"CBLOCK #{i} provenance file missing: {rel}")
                    continue
                ok = block_in_file(body, get_file(rel))
            if not ok:
                for c_rel in cited_files:
                    if block_in_file(body, get_file(c_rel)):
                        ok = True
                        break
            if not ok:
                first = next((l for l in body if l.strip() and l.strip() != "..."), "")[:70]
                tag = f" (prov {rel})" if rel else ""
                unmatched.append(f"CBLOCK #{i} unit not verbatim{tag}: '{first}'")
    findings.extend(unmatched)

    # 3. Gate A prose sweep
    for (fence, ln), lineno in zip(split_fences(raw), range(1, len(raw) + 1)):
        if fence:
            continue
        if ln.startswith("> CAUTION") or ln.startswith(">"):
            continue
        if HEADING_BAD.match(ln):
            findings.append(f"GATEA heading ({lineno}): {ln[:70]}")
        # strip inline code spans and link URLs before pattern checks
        stripped = re.sub(r"`[^`]*`", "", ln)
        stripped = re.sub(r"\]\([^)]*\)", "]", stripped)
        for name, rx in GATE_A:
            if name == "label-colon" and (ln.startswith("|") or ln.startswith("-") or ln.startswith("#")):
                continue
            m = rx.search(stripped)
            if not m:
                continue
            qpos = m.end() if name == "label-colon" else m.start() + 1
            if stripped[:qpos].count('"') % 2 == 1:
                continue  # match inside a quoted span (verbatim quote exemption)
            findings.append(f"GATEA {name} ({lineno}): {ln[:70]}")

    print(f"== {page}")
    print(f"   lines={len(raw)} links={n_links} symchecks={n_symchecks} cblocks={len(blocks)}"
          + ("" if version else "  (no Elixir links found; link checks skipped)"))
    if findings:
        for f_ in findings:
            print("   " + f_)
    else:
        print("   CLEAN")
    return not findings


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", default=os.environ.get("KERNEL_TREE", "."),
                    help="kernel source tree root (default: $KERNEL_TREE or cwd)")
    ap.add_argument("pages", nargs="+", help="page .md files to verify")
    args = ap.parse_args()
    TREE = Path(args.tree)
    ok = all([verify(p) for p in args.pages])
    sys.exit(0 if ok else 1)
