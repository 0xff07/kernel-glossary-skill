# BAN-02: Label-colon prose

> Was: 7a. Label-colon prose

**INPUT:** The flowing prose paragraphs and the lead summary paragraph, presented as a prose view of the page (fenced blocks dropped, links resolved to their text, inline code, double-quoted text, and file:line citations masked); headings, catalog bullets, table cells, URLs, ratios, and code are out of scope.

**OUTPUT:** Body prose whose every sentence is a plain declarative, with quotes introduced as "According to the comment <quote>, ..."; delivered with the adjudicated label-colon candidate list at zero unadjudicated hits.

**Problem:**

1. Generated prose leans on the "label: explanation" idiom — a noun phrase, a colon, then the clause that should have been the sentence.
2. Body prose (everything outside H1–H4 headings, fenced code blocks, ASCII diagrams, list bullets, table cells, and Elixir links) must never use it.
3. State the same content as a plain declarative sentence.

The banned forms, each with its fix:

**"X: Y." — Before:**

```
Two-phase handshake: a status read, then a gated write.
```

**After:**

```
The handshake has two phases. advance_transaction reads EC_SC first, and writes the next byte only when IBF is clear.
```

**"X is Y: Z." — Before:**

```
The asymmetry: an edge GPE clears status before the method, a level GPE after.
```

**After:**

```
An edge-triggered GPE clears its status before the method runs; a level-triggered GPE clears it after.
```

**The "is the key:" family** ("X is the key: Y" / "X is essential: Y" / "X is explicit: Y" / "X is significant: Y" / "X is conservative: Y" / "X is deliberate: Y" / "X is the linchpin: Y" / "X is asymmetric: Y" / "X is intentional: Y" / "X is correct: Y" / "X becomes clear here: Y") — **Before:**

```
The IBF gate is essential: IBF stays 1 until the EC consumes the byte just written.
```

**After:**

```
IBF stays 1 until the EC consumes the byte just written, so advance_transaction sends the next byte only when IBF reads 0.
```

**The "The intent:" family** ("The intent: Y" / "The reasoning: Y" / "The result: Y" / "The fix: Y" / "The condition is: Y" / "The order of operations matters: Y" / "The pattern is: Y" / "The point is: Y" / "The takeaway is: Y") — **Before:**

```
The reasoning: a level source stays asserted until the AML quiesces it.
```

**After:**

```
A level-triggered source stays asserted until the AML quiesces the device.
```

**Colon-introduced quotes** ("X says: <quote>" / "X makes Y explicit: <quote>" / "X spells this out: <quote>" / "Comment: <quote>") — **Before:**

```
The comment "Note: disables and clears all GPEs in the block" is the key: events only flow after an explicit enable.
```

**After:**

```
According to the comment "Note: disables and clears all GPEs in the block", events only flow after an explicit enable.
```

**Colon-introduced lists** ("X is called from N places: A, B, C."). Replace with "X is called from N places. A does ..., B does ..., C does ...". The list-after-colon shape is banned even when the items are short.

**The colon that introduces a fenced excerpt is not this shape.** A sentence whose colon is the last character of its paragraph and whose next non-blank line opens a fenced block points the reader at the code, and the sentence before it names what the code is about to show: "The runtime holds the stream state, the negotiated hardware parameters, and the DMA ring buffer pointer:" followed by the excerpt of those members. That is the binding sentence between prose and excerpt, and it is exempt. Until 2026-09-02 this file read as banning it, and every page written under that reading introduced its excerpts with nothing at all: measured over the corpus, a corpus written before this ban bound 98 of every 100 excerpts with such a sentence, and every corpus written after it bound none. The exemption is exactly that shape and no wider: a colon that introduces items in the same sentence is still the banned list, and a colon that introduces a table is still a label-colon, because a table's lead-in ends in a full stop.

Never editorialise with "The reasoning:" or any synonym ("The rationale is", "The motivation:") that asserts authorial reasoning: the page describes what the code does, and a rationale exists only where a comment or commit message states one, quoted via "According to the comment <quote>, ...". When removing a colon-label, state the underlying mechanic as a plain declarative sentence; swapping the colon for "X matters because Y" or "X is what makes Y" asserts importance the same way and is banned.

Do not flag the colon inside H3/H4 headings (catalog labels like `### _Lxx: level-triggered GPE method`), Elixir link titles, code blocks, URLs, ratios (`M:N`), or after Markdown list bullets when the item is a catalog entry in the LINUX KERNEL or KERNEL DOCUMENTATION section, or at the end of a paragraph whose next non-blank line opens a fenced excerpt. The ban binds flowing prose paragraphs and the lead summary paragraph.

**PASS CRITERIA:**

1. Sweep label-colon candidates with `[^:;.!?]{3,90}:\s+[A-Za-z0-9§]` over a prose view of the page (fenced blocks dropped, links resolved to their text, inline code and double-quoted text masked, file:line citations masked). Never anchor the pattern to line start: each paragraph is one unwrapped line, so a line-anchored pattern sees only the first clause; measured over eleven pages the anchored form caught 12% of known hits, the unanchored form 100% at roughly eleven candidates per page. Adjudicate every candidate.
2. A candidate is a hit when a noun phrase, a colon, and its explanation sit in flowing body prose or the lead: the "X: Y" and "X is Y: Z" shapes, the "is the key:" family, the "The intent:" family, colon-introduced quotes, and colon-introduced lists. Editorializing labels asserting authorial reasoning ("The reasoning:", "The rationale is") are hits with or without the colon.
3. Exempt, and never reworded to silence the pattern: colons inside H3/H4 headings and catalog labels, Elixir link titles, code blocks, URLs, ratios, list bullets and table cells (the scope sentence above puts them outside body prose), double-quoted verbatim text, and the paragraph-final colon that introduces the fenced excerpt on the next non-blank line. The prose view cannot see that last shape (it drops the fence and shows the paragraph on its own line), so adjudicate it from the raw file: `awk '/^```/{f=!f} !f && /:$/{p=NR; next} p && NF{ if(/^```/) print p": introduces a fence"; p=0 }' page.md` lists the paragraphs whose colon is followed by a fence, and each is exempt.
4. Confirm every quote is introduced as "According to the comment <quote>, ..." (or "The comment reads <quote>."), and that no removed colon-label was replaced with "X matters because Y" or "X is what makes Y", which assert importance the same way.
5. Pass at zero unadjudicated label-colon shapes in body prose.
