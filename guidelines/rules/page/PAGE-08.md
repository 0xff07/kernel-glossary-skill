# PAGE-08: Leading paragraphs open on purpose, never on a count

> Was: none. Added 2026-09-02, when the user read the first page written under the excerpt-explanation rule added earlier that day and found its lead opening on "three groups of writable control bits", its SUMMARY on "one field set with three writers", and a DETAILS section on "six write behaviours in one 32-bit word". The same instruction had been recorded in the sound campaign's spec on 2026-08-20 ("counts serve claims; a count that serves no claim is noise") and never reached the skill.

**INPUT:** The lead (every paragraph between the caution blockquote and `## SUMMARY`); the first paragraph of SUMMARY, of section 6 and of DETAILS; the first paragraph under every H3 and H4 in DETAILS; and SUMMARY as a whole, with its tables and figures counted.

**OUTPUT:** Leading paragraphs whose first sentence says what the mechanism is for and what the thing is, in words a reader who has read nothing else on the page can follow, with any count, size or position arriving only after that; a SUMMARY that carries the model in prose and the state set with its transitions, and nothing a DETAILS excerpt explains better beside it; delivered with the list of leading paragraphs and the verdict on each.

**Problem:**

1. A reader arrives at a paragraph knowing nothing yet. A first sentence that tells them how many of something there are ("one field set with three writers", "six write behaviours in one 32-bit word") or which one this is ("the second of the three PORTSC writers") gives them nothing to hold, because they do not yet know what the things are or why the number matters. Counting with no context leaves the reader clueless.
2. The pipeline rewards the count. Every count on a page is a verified claim that the check pass re-derives, so under verification pressure a writer opens with the sentence that is easiest to defend rather than the one the reader needs, and until this rule nothing said what a first sentence is for.
3. A SUMMARY that carries every member table and every per-request detail has become a second DETAILS without the excerpts, and the reader meets each table before the code it describes.

**Rule:**

1. The lead opens on what the mechanism is for and where it sits: the problem it solves, who decides and who performs, the layer above and the layer below. It names a symbol only once that context is in place, and its first sentence counts nothing.
2. Every leading paragraph opens the same way: its first sentence says what the thing is or what it is for. A count ("six write behaviours"), a size ("one 32-bit word"), a position ("the second of the three writers", "the remaining four") or a partition ("one field set with three writers") is never a leading paragraph's first statement.
3. A count may follow once the reader knows what is being counted and why the number matters, and it is verified as every count is. The test is deletion: take the number out of the first sentence, and if what remains still says what the thing is for, the number was incidental; if nothing remains, the sentence was a count and not an opener.
4. The heading above a DETAILS section has already named the construct. The paragraph under it expands the heading's claim with the purpose and the mechanism, never with the construct's cardinality or its place in a sequence.
5. SUMMARY carries the domain model in prose and the state set with its legal transitions, at most one table and one figure. A member table, a per-bit or per-request table, and the detail of any one path sit in DETAILS beside the excerpt they describe, never in SUMMARY.

**Before** (the lead):

```
A root-hub port on a PCI-attached xHCI host carries three groups of
writable control bits that decide whether it is powered, what link state
it holds, and which events wake the machine through it. The first is the
Port Power bit PORT_POWER, and the second is the four-bit Port Link
State field selected by PORT_PLS_MASK, which a write latches with the
PORT_LINK_STROBE strobe. The third group is the three wake enables ...
```

**After:**

```
A USB port carries both the power a device draws and the link it talks
over, and the kernel controls each of them on its own, apart from the
data traffic through the port. Powering a port off saves the current a
device would draw and isolates a device that has stopped behaving. A
device the USB core suspends needs its link driven into a low-power
state, and driven back out of it when the device is needed again. A
machine about to sleep has to settle which port events are allowed to
wake it, because a port left armed wakes the whole system when someone
plugs in a cable. Port power management is the machinery that carries
decisions like these from the software that makes them down to the
hardware that performs them ...
```

**Before** (the SUMMARY opener):

```
The register side of that model is one field set with three writers.
The set is the part of PORTSC whose bits keep the value written to them,
which the driver names XHCI_PORT_RWS, and it holds the link-state field,
the port-power bit, the port-indicator field and the three wake enables.
```

**After:**

```
PORTSC is the register the controller provides for each root-hub port,
and it works in both directions. Most of its bits report the port's
condition to software. They say whether a device is connected and at
what speed, whether an over-current fault is present, and, through the
change flags, that one of those has moved since the flag was last
cleared. The bits this page is about run the other way. The link state,
the port power, the port indicator and the wake enables are chosen by
software, and the hardware holds each one exactly as it was written,
which is why the driver groups them under a single mask, XHCI_PORT_RWS.
```

**Before** (a DETAILS section opener):

```
PORTSC has six write behaviours in one 32-bit word, and the comment
block at drivers/usb/host/xhci-hub.c:392 names each class as a mask.
```

**After:**

```
A write to PORTSC replaces the whole word, but its bits do not all
respond to a write the same way, and a driver that wrote back exactly
what it had read would clear every change flag that was set, because
those bits clear on a one. The comment block at
drivers/usb/host/xhci-hub.c:392 records how each bit responds, and the
masks beneath it turn that record into what a write must carry.
```

**Before** (a short section opener):

```
The third writer turns a hub wake mask into three PORTSC bits.
```

**After:**

```
A port wakes a sleeping host only for the events its wake enables
select, and the hub protocol lets the hub driver choose those events per
port with one request. xhci_set_remote_wake_mask() turns that request
into the port's wake enables.
```

In every pair the number is still on the page. The after text says first what the thing is and what it is for, and the count, where it still earns its place, comes once the reader can tell what is being counted.

**PASS CRITERIA:**

1. Generate the candidate list from the raw file, because the section headings that mark each leading paragraph are what a prose view drops:

    ```
    python3 - page.md <<'EOF'
    import re, sys
    L = open(sys.argv[1], encoding="utf-8").read().split("\n")
    NUM = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|\d+)\b"
                     r"|\b(first|second|third|fourth|fifth|remaining|other)\b", re.I)
    fence = False; sec = "lead"; lead = True
    for n, l in enumerate(L, 1):
        if l.startswith("```"): fence = not fence; continue
        if fence: continue
        if l.startswith("#"): sec = l.lstrip("#").strip()[:60]; lead = True; continue
        if not l.strip() or l.startswith(("|", "- ", ">")): continue
        if lead:
            s = re.split(r"(?<=[.;:])\s", re.sub(r"\]\(https?://[^)]*\)", "]", l), maxsplit=1)[0]
            print(f"{n} [{sec}]{' COUNT' if NUM.search(s) else ''}: {s[:160]}")
        lead = False
    EOF
    ```

    It prints the first sentence of the lead and of every leading paragraph, tagged `COUNT` when that sentence carries a number word, a digit or an ordinal. It sees words, not purposes, so it generates candidates and is never the gate: "USB 2.0", "bit 9" and "in one word" are tagged and are not hits, and a first sentence that opens on a mechanism detail with no purpose stated is a hit the tag cannot see.
2. Read every tagged sentence. It is a hit when the number or the position is what the sentence tells the reader; it is cleared when the sentence says what the thing is for and the number is incidental to that.
3. Read every printed sentence, tagged or not, against rules 1 and 2: a first sentence that presupposes the page's model ("The register side of that model is ..."), or that opens on how a thing is laid out or where it sits in a sequence before saying what it is for, is a hit.
4. Count SUMMARY's tables and figures and name any member, per-bit or per-request table it carries:

    ```
    awk '/^## SUMMARY/{f=1} /^## SPECIFICATIONS/{f=0} f && /^\|---/{t++} f && /^```/{c++} END{print "tables", t+0, "figures", c/2}' page.md
    ```

    More than one table or more than one figure, or a member table whose excerpt sits in DETAILS, is a finding, fixed by moving the table beside its excerpt.
5. Record the list (leading paragraph, first sentence, verdict) and the SUMMARY counts in the dossier's EVIDENCE section. Pass at zero unadjudicated openers: every hit rewritten to open on purpose, and every SUMMARY table beyond the state set moved beside its excerpt.
