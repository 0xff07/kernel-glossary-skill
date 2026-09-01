# PAGE-06: Linked code in table cells

**INPUT:** Every Markdown table on the page — census tables, semantics tables, register and limit tables, parity and mapping tables — and every inline code span inside their cells, read from the raw file rather than from a prose view, because a prose view that strips or tags table rows cannot see them.

**OUTPUT:** Every kernel construct named in a table cell carrying an Elixir cross-reference link to the documented version, anchored at the line that defines it; delivered with the table's spans inventoried and each one either linked or recorded against an exemption below.

**Rule:**

1. A table is a reference surface, and its cells are read in isolation. A reader scanning the rows never sees the paragraph that introduced the table, so a construct linked once in that paragraph is unlinked as far as the row is concerned. Link it in the cell.
2. Every occurrence in every row is linked, including a construct that repeats down a column and a construct already linked in an earlier row. Linking the first row and leaving the rest bare produces a table whose usefulness decays as the reader scrolls.
3. The link target is the same one prose would use: the line that defines the construct at the documented version, not the line the row happens to discuss. Where a row's point is a particular call site, the location gets its own link in its own cell.
4. This binds every kind of table, catalog sections included. Density is the accepted cost: a table of thirty rows carries thirty links, and that is the intended outcome rather than a sign of over-linking.

**Rule:**

1. These stay bare in a cell, and are not defects: literal values (`true`, `false`, `0`, `-EINVAL`), literal strings a function prints or logs, C keywords and operators, locals, parameters and goto labels quoted from an excerpt, path strings, Kconfig fragments and keywords, commit hashes, tracepoint field names, and a construct verified absent from the documented tree, whose absence the prose states.
2. A span left bare for any other reason is recorded with the reason before the page is reported done, never left unexplained.

**Before:**

```
| notification | callback site |
|---|---|
| `DMUB_NOTIFICATION_AUX_REPLY` | amdgpu_dm.c:2145 |
| `DMUB_NOTIFICATION_HPD` | amdgpu_dm.c:4324 |
```

**After:**

```
| notification | callback site |
|---|---|
| [`DMUB_NOTIFICATION_AUX_REPLY`](https://elixir.../source/.../dmub_cmd.h#L3020) | [`amdgpu_dm.c:2145`](https://elixir.../source/.../amdgpu_dm.c#L2145) |
| [`DMUB_NOTIFICATION_HPD`](https://elixir.../source/.../dmub_cmd.h#L3022) | [`amdgpu_dm.c:4324`](https://elixir.../source/.../amdgpu_dm.c#L4324) |
```

**PASS CRITERIA:**

1. Extract every table row from the RAW file (a fence-aware scan; rows inside fenced blocks are excerpt content and out of scope), and inventory every inline code span in every cell.
2. Confirm each span is either linked, or matches an exemption in the second rule with the reason recorded. A span that is neither is a defect.
3. Confirm no span is linked in only some of the rows in which it appears; the count of linked occurrences equals the count of occurrences.
4. Open a sample of the link targets and confirm each lands on the defining line at the documented version.
5. Pass at zero unexplained bare spans in any table cell.
