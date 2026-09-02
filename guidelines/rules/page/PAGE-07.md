# PAGE-07: Prose explains what it quotes

> Was: none. Added 2026-09-02, when a measure over the corpus found that half of the definition excerpts on the two page batches written that week had no member named in the prose beside them, against a sixth of the excerpts in the corpus written in June.

**INPUT:** Every fenced ` ```c ` block in SUMMARY and DETAILS that reproduces a definition (a struct, union, or enum body, a register layout, or a run of members from one) together with the paragraph immediately before it and the paragraph immediately after it; and every fenced block that reproduces a function body, with the same two paragraphs.

**OUTPUT:** Beside every definition excerpt, a paragraph that says what each member the excerpt shows holds or selects and which code writes or reads it, or an excerpt elided with the house `...` marker down to the members that paragraph explains; beside every function excerpt, a paragraph that says what the shown lines do; delivered with the per-excerpt list of members shown, members named, and the group phrase that covers each member not named.

**Problem:**

1. An excerpt is a claim that the reader needs to see these lines, and the paragraph beside it is where the page pays that claim off. A paragraph that says how many fields the struct has, which pass writes them, or where the struct sits relative to another has described the excerpt's shape and explained none of its content.
2. Anyone can count fields. "The first five fields are what the construction pass writes, and everything after them belongs to later paths" tells the reader nothing the excerpt does not already show, and it postpones the one question the excerpt raised: what each field holds, and who uses it.
3. A field table elsewhere on the page does not discharge the excerpt. The reader at the excerpt is reading the excerpt, and a table in another section is not beside it.
4. The heading over the section states the construct's purpose. The paragraph under it is not a second heading: it explains the members that deliver that purpose.

**Rule:**

1. The paragraph beside a definition excerpt names the members the excerpt shows and states, for each, what it holds or selects and which path writes or reads it. A member the page does not explain is not shown: elide it with `...` and say in one clause what the elision drops.
2. A member is also explained when the paragraph names the group the excerpt's own comment files it under ("the negotiated hardware parameters" for the members under a `/* -- HW params -- */` comment). The group phrase stands in for its members only when the excerpt shows that grouping.
3. Position, count, and lifetime partition ("the first five", "the remaining", "adjacent fields", "a few fields further down", "everything after them") are never the explanation. They may follow it when the position is itself something the code relies on (a member placed on its own cache line, a member that must stay last), and then the reason is stated with it.
4. A long definition is cut into several excerpts of a few members each, each with its own paragraph, rather than one excerpt of the whole type with one paragraph beside it. The comments and `#ifdef` regions an excerpt shows are part of what its paragraph explains.
5. The paragraph beside a function excerpt says what the shown lines do to the objects the page is about: which member they write, which condition they test, which call they make and with what. That the body "has three branches", "runs after the previous one", or "is the longest of the four" is shape, and shape is not the explanation.
6. Walk the members one or two sentences each. A single sentence that strings every member's name together is not an explanation either; it is the excerpt again, without the types.

**Before:**

```
One struct xhci_port exists per hardware port for the lifetime of the host
controller's memory setup. The first five fields are what the construction
pass writes, and everything after them belongs to paths that run once the
root hubs are live.

/* drivers/usb/host/xhci.h:1474 */
struct xhci_port {
	struct xhci_port_regs __iomem	*port_reg;
	int			hw_portnum;
	int			hcd_portnum;
	struct xhci_hub		*rhub;
	struct xhci_port_cap	*port_cap;
	unsigned int		lpm_incapable:1;
	unsigned long		resume_timestamp;
	bool			rexit_active;
	/* Slot ID is the index of the device directly connected to the port */
	int			slot_id;
	struct completion	rexit_done;
	struct completion	u3exit_done;
};
```

**After:**

```
One struct xhci_port exists per hardware port. port_reg is the port's
register quad in MMIO, and every PORTSC read or write on this page goes
through it. hw_portnum is the port's index in the flat hw_ports array,
the numbering a Port Status Change Event carries minus one, which is how
handle_port_status finds the port. hcd_portnum is the port's index inside
the root hub that claimed it, the numbering the hub driver works in, and it
holds DUPLICATE_ENTRY when two capability entries claimed the same port.
xhci_setup_port_arrays writes port_reg and hw_portnum; xhci_add_in_port
writes rhub and port_cap, which point back at the claiming root hub and at
the cached capability entry the port was found under; and
xhci_create_rhub_port_array assigns hcd_portnum last. The six members the
elision drops are the per-port flags, timestamps, and completions that
the LPM, resume, and device-slot paths write, and their pages explain
them.

/* drivers/usb/host/xhci.h:1474 */
struct xhci_port {
	struct xhci_port_regs __iomem	*port_reg;
	int			hw_portnum;
	int			hcd_portnum;
	struct xhci_hub		*rhub;
	struct xhci_port_cap	*port_cap;
	...
};
```

The after text is longer because it carries the explanation; the excerpt is shorter because it shows only what the paragraph explains. Both moves are the rule.

**PASS CRITERIA:**

1. Generate the candidate list from the raw file, never from a fence-stripped view, because the members live inside the fences:

    ```
    python3 - page.md <<'EOF'
    import re, sys
    lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
    MEMBER = re.compile(r"^\t[^\t/*#}].*?\b(\w+)\s*(?:\[[^\]]*\])?\s*(?::\s*\d+)?\s*;")
    ENUMV  = re.compile(r"^\t([A-Z][A-Z0-9_]*)\s*(?:=[^,/]*)?,?\s*(?:/\*.*)?$")
    def para(i, step):
        j = i + step
        while 0 <= j < len(lines) and not lines[j].strip(): j += step
        if not (0 <= j < len(lines)) or lines[j].startswith(("```", "#")): return ""
        k = j
        while 0 <= k + step < len(lines) and lines[k + step].strip() and not lines[k + step].startswith("```"): k += step
        a, b = sorted((j, k))
        return " ".join(lines[a:b + 1])
    i = 0; blocks = 0; zero = 0; fr = []
    while i < len(lines):
        if lines[i].rstrip() != "```c": i += 1; continue
        j = i + 1
        while j < len(lines) and not lines[j].startswith("```"): j += 1
        body = lines[i + 1:j]; kind = None; mem = []
        for l in body:
            if re.search(r"\b(struct|union) \w*\s*\{|\bunion\s*\{", l): kind = "struct"
            elif re.search(r"\benum \w*\s*\{", l): kind = "enum"
            elif l.startswith("}"): kind = None
            m = (MEMBER if kind == "struct" else ENUMV if kind == "enum" else None)
            m = m and m.match(l)
            if m and m.group(1) not in mem: mem.append(m.group(1))
        if len(mem) >= 2:
            prose = re.sub(r"\(https?://[^)]*\)", "", para(i, -1) + " " + para(j, +1))
            named = [m for m in mem if re.search(r"\b" + re.escape(m) + r"\b", prose)]
            blocks += 1; fr.append(len(named) / len(mem)); zero += not named
            print(f"{i + 1}: {len(named)}/{len(mem)} named; unnamed: {' '.join(m for m in mem if m not in named) or '-'}")
        i = j + 1
    print(f"definition blocks={blocks} zero-named={zero} mean-fraction-named={sum(fr) / max(len(fr), 1):.2f}")
    EOF
    ```

    It prints one row per fenced C block that shows two or more members of a struct, union, or enum: the block's line, how many of those members the two adjacent paragraphs name, and the members they do not name. It sees names, not explanations, so it generates candidates and is never the gate.
2. Read every row. A member listed as unnamed is a defect unless the adjacent paragraph names the group the excerpt's own comment files it under; record that group phrase against the member. A block with zero members named is a defect outright: no group phrase covers a whole excerpt.
3. Read the adjacent paragraph of every definition block, named members included, for the position, count, and lifetime shapes of rule 3 standing in for the explanation. A paragraph whose only statement about the members is where they sit or how many there are is a defect even when it names every one of them.
4. Read the paragraph beside every function excerpt against rule 5; no pattern expresses shape-only description, so this is a read-through.
5. Record the generator's footer for the page. Across the corpus at v7.0, pages written to this rule's standard measure a sixth or fewer of their definition blocks at zero named and a mean fraction near a third; a page at half its blocks zero-named has the defect page-wide, and the fix is the paragraphs, never a shorter excerpt that hides the members.
6. Pass at zero unadjudicated rows: every unnamed member covered by a recorded group phrase or explained in a rewritten paragraph, every zero-named block rewritten or its excerpt elided to what its paragraph explains, and no shape-only paragraph beside any excerpt.
