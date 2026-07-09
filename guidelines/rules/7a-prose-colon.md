# 7a. Prose colon idioms (mandatory)

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

Body prose (everything outside H1, H2, H3, H4 headings, fenced code blocks, ASCII diagrams, list bullets, table cells, and Elixir links) must never use the "label-colon-explanation" idiom. The colon-followed-by-clause pattern in prose is banned. State the same content as a plain declarative sentence.

This applies to forms like:

- "X: Y." where X is a noun phrase and Y is the explanation. BAD: `Two-phase handshake: a status read, then a gated write.` GOOD: `The handshake has two phases. advance_transaction reads EC_SC first, and writes the next byte only when IBF is clear.`
- "X is Y: Z." BAD: `The asymmetry: an edge GPE clears status before the method, a level GPE after.` GOOD: `An edge-triggered GPE clears its status before the method runs; a level-triggered GPE clears it after.`
- "X is the key: Y" / "X is essential: Y" / "X is explicit: Y" / "X is significant: Y" / "X is conservative: Y" / "X is deliberate: Y" / "X is the linchpin: Y" / "X is asymmetric: Y" / "X is intentional: Y" / "X is correct: Y" / "X becomes clear here: Y". BAD: `The IBF gate is essential: IBF stays 1 until the EC consumes the byte just written.` GOOD: `IBF stays 1 until the EC consumes the byte just written, so advance_transaction sends the next byte only when IBF reads 0.`
- "The intent: Y" / "The reasoning: Y" / "The result: Y" / "The fix: Y" / "The condition is: Y" / "The order of operations matters: Y" / "The pattern is: Y" / "The point is: Y" / "The takeaway is: Y". BAD: `The reasoning: a level source stays asserted until the AML quiesces it.` GOOD: `A level-triggered source stays asserted until the AML quiesces the device.`
- "X says: <quote>" / "X makes Y explicit: <quote>" / "X spells this out: <quote>" / "Comment: <quote>" introducing direct quotes. BAD: `The comment "Note: disables and clears all GPEs in the block" is the key: events only flow after an explicit enable.` GOOD: `According to the comment "Note: disables and clears all GPEs in the block", events only flow after an explicit enable.`
- "X is called from N places: A, B, C." Replace with "X is called from N places. A does ..., B does ..., C does ...". The list-after-colon shape is banned even when the items are short.

Never editorialise with "The reasoning:" or any synonym ("The rationale is", "The motivation:", etc.) that asserts authorial reasoning. The page describes what the code does; if a comment or commit message states a rationale, quote it via "According to the comment <quote>, ..." instead. When you remove a colon-label, state the underlying mechanic as a plain declarative sentence; do not swap the colon for "X matters because Y" or "X is what makes Y", which asserts importance the same way and is banned by 7d.

The colon is acceptable inside H3/H4 headings (catalog labels like `### _Lxx: level-triggered GPE method`), inside Elixir link titles, inside code blocks, inside URLs, inside ratios (`M:N`), and after Markdown list bullets when the item is a catalog entry in the LINUX KERNEL or KERNEL DOCUMENTATION section. It is banned in flowing prose paragraphs and in the lead summary paragraph.
