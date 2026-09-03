# BANS: What is trimmed from every sentence

> Replaces BAN-01 through BAN-08 and BAN-WAIVERS. Every pattern, fix and exemption they carried is here; the eight files of framing around them are not. The bans are negative on purpose: trimming a style the writer already produces is cheap and checkable, and WRITING.md says what the trimmed sentence is for.

Sweep them over a prose view of the page (ROUTINE-01 builds it: fences dropped, links resolved to their text, code spans, quoted text and file:line citations masked), case-insensitively and never anchored to line start, because a paragraph is one line and an anchored pattern sees only its first clause. A pattern generates candidates; the exemptions column decides. Never reword an exempt construct to silence a pattern, and re-run after every edit, your own included. A new exemption lands in this table only through the user; an agent that settles a boundary during a run records it in the lessons file and surfaces it.

| ban | pattern to sweep | fix | exempt |
|---|---|---|---|
| em dash | `—` | parentheses, or two sentences | nothing; figure text included |
| boldface | `**` on the raw file | plain text | `/**` kerneldoc openers inside fences |
| negative construction ("X, not Y", "X rather than Y") | `(,\|\band)\s+(not\|never)\s\|\brather than\b\|\binstead of\b`, then read: a sentence asserting X by denying Y is a hit | state what the thing is | a quoted comment; a comparison whose denied alternative is a real design the reader could otherwise assume |
| placement verbs | the lemmas live, lives, lived, living, sit, sits, sat, sitting, hang, hangs, hung, hanging, want, wants, wanted, wanting | "is defined in", "is held in", "occupies", "is attached behind"; a field "transitions through" its values | the adjective ("the live ring"); a real actor ("the reader wants the buffer"); a verbatim quote. Physical hardware earns no exemption: "the device sits behind a translator" is reworded |
| "walk" for a scalar | `\bwalks?\b`, then read | "advances through" | traversing a data structure (a list, a tree, page tables, the namespace) |
| "vtable" | `vtable` | "function pointer struct" or the type name | nothing |
| question or bare-noun headings | `^#{2,4} (Why\|How\|Where\|What)`, a trailing `?`, and every DETAILS H3 and H4 read | a declarative what-does-what heading | the H3 catalog labels of LINUX KERNEL |
| label-colon prose ("X: Y", "X is Y: Z", "is the key:", "The intent:", "says: quote", "called from N places: A, B, C") | `[^:;.!?]{3,90}:\s+[A-Za-z0-9§]` | one plain declarative sentence; a quote as "According to the comment <quote>, ..."; never "X matters because Y" or "The reasoning:" in its place | the paragraph-final colon that introduces the fenced excerpt on the next non-blank line (from the raw file: `awk '/^```/{f=!f} !f && /:$/{p=NR; next} p && NF{ if(/^```/) print p; p=0 }'`); colons in H3/H4 labels, link titles, code, URLs, ratios, catalog bullets, table cells and double-quoted text |
| intro sentence plus list | every list in DETAILS, SUMMARY and the lead, read | fold the items into one flowing paragraph | the catalog lists of LINUX KERNEL, KERNEL DOCUMENTATION and OTHER SOURCES; tables |
| hollow superlatives and importance frames | the words below, plus `\bis what\b`, `\bwhat matters\b`, `\bthe reasoning\b`; every adjective read with the deletion test | name the mechanic in the same clause and drop the ranking; delete an adjective the sentence survives without | "fast path" and "slow path" where the kernel names them; verbatim quotes |
| banned words | `contract`, `tally`, `tallied`, `tallies`, `tallying`, `canonical`; `(^\|[^a-z])arms?([^a-z]\|$)` for a branch or union case | the rule, count or helper the word stood in for; "branch", "case", "side" | Arm, ARM64, arm64, "32-bit Arm"; the verb ("arms a timer"); verbatim quotes |
| hedges | usually, typically, generally, often, normally, commonly, mostly, in practice, tends to, on a hot cpu, simply, essentially, basically, arguably | name the exact condition the code tests | hyphenated compounds ("read-mostly"); a hedge inside a quote; a measured statistic that cites its counter |
| run-on enumeration | a sentence carrying four or more members of one set (generate with three commas plus " and ", ranked by distinct file:line locations; read) | a Markdown table, one row per member, every construct linked in every row, the lead-in ending in a full stop; extend an existing table over the same set rather than adding a second | the steps of one operation (a sequence shares no column); the member-by-member walk beside the excerpt that shows those members (WRITING rule 3) |

Superlative and importance words: the most invasive, the most fragmenting, the most aggressive, the most consequential, the most preferred, the least preferred, the most expensive, the cheapest, the cheap path, the slow path, the fast path, the strongest guarantee, the weakest guarantee, the worst outcome, the best outcome, the entire performance benefit, the entire correctness benefit, the key invariant, the key difference, the key innovation, the key role, the design assumption, the design intent, X matters, X matters because Y, X is what makes Y, what makes X work, the only mode that, elaborate, elegant, fundamental, cornerstone, linchpin, crucial, critical.

Label-colon families, all one shape: "The reasoning:", "The intent:", "The asymmetry:", "The fix:", "The point is:", "The takeaway:", "The pattern is:", "is the key:", "is essential:", "is explicit:", "is significant:", "is conservative:", "is deliberate:", "is the linchpin:", "is asymmetric:", "is intentional:", "is correct:", "becomes clear here:", `says: "`, `spells this out: "`, `makes explicit: "`, `Comment: "` (the LINUX KERNEL bullet form `[symbol]: bit 0xN. Comment: "..."` is a catalog entry and stays).

Where the bans reach: body prose and headings; figure text for the em dash, the negative construction and the placement verbs (the phrase bans lift inside a figure); never inside a ` ```c ` excerpt or a verbatim quotation.

## Before and after

```
The IBF gate is essential: IBF stays 1 until the EC consumes the byte just written.
IBF stays 1 until the EC consumes the byte just written, so advance_transaction sends the next byte only when IBF reads 0.

It is synchronous, not asynchronous.
It is synchronous.

The three wake enables sit at bits 25 to 27.
The three wake enables occupy bits 25 to 27.

What matters here is that the lock is dropped before the method.
The lock is dropped before the ACPI method, so the method runs without it.

### Why _Exx clears status before the method
### _Exx clears status before the method runs

Two details deserve attention.
- advance_transaction writes EC_DATA only while IBF is clear.
- It reads EC_DATA only while OBF is set.
advance_transaction writes the next byte only while IBF reads 0, and reads a result byte only while OBF reads 1.

register_dmub_notify_callback() is called five times, for AUX_REPLY at file:2145, FUSED_IO at file:2154, HPD at file:4324, HPD_IRQ at file:4330, and HPD_SENSE_NOTIFY at file:4336.
amdgpu registers five notification callbacks through the one helper that writes dmub_callback[]. (then a five-row table: notification, linked location)
```

## Checked by

ROUTINE-01's batched sweep over the prose view with every pattern above, its figure sweep over the non-C fences for the three bans that reach figures, the raw-file greps for boldface and headings, and the read-throughs for lists, enumerations, superlatives in context and heading shape. Every candidate is fixed or recorded exempt with the exemption that applies. Pass at zero unadjudicated candidates, with exempt constructs left unreworded.
