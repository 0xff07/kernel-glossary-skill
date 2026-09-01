# BAN-08: Run-on enumerations in prose

**INPUT:** Every sentence in DETAILS, SUMMARY, and the lead that enumerates members of a set — call sites, register fields, enum members, callers, flags, states — counted by how many members the sentence carries.

**OUTPUT:** No sentence carrying more than three enumerated members; every larger set presented as a Markdown table whose rows are the members, with the prose above it saying what the set is and what its members have in common.

**Rule:**

1. A sentence that strings together four or more members of a set stops being prose. The reader cannot hold the fourth item while parsing the fifth, cannot compare two members without re-reading, and cannot find one member again without scanning the whole sentence. The information is tabular and the sentence is the wrong container for it.
2. Four or more members: build a table. One row per member, one column per thing the prose was trying to say about each. Three or fewer: a sentence is fine and a table is overhead.
3. The prose above the table keeps the part that is genuinely prose — what the set is, what its members share, why the population is closed, and what the exceptions mean. The table carries the members. Neither repeats the other, and the lead-in ends in a full stop: "Here is the set:" is the natural way to introduce a table and it is a banned shape, so a conversion made under this rule reliably manufactures one unless the writer watches for it.
4. Every kernel construct in the table's cells carries its cross-reference link, in every row it appears in. A table of bare names is a worse reference than the sentence it replaced.
5. The tell is ONE LOCATION PER MEMBER, not a repeated path. When each item in the sentence carries its own file and line because each is a distinct place, the sentence has already become a table that has not been drawn: the path belongs in a location column, written once per row rather than once per member. A bare path repeat is a weak generator and was measured at roughly one real hit in ten on a page whose subject is a single file, where several functions defined in that file are discussed in one sentence and every symbol link naturally carries the same path.
6. The discriminator between a SET and a SEQUENCE is whether the items each need the same kind of attribute. Members of a set each want a location, or a value, or a role — the same column filled differently per row, which is what a table is for. Steps of one operation, clauses of one mechanism, and a chain of consequences share no such column, and flattening them into rows destroys the conditionality ("on success", "unless the flag is set", "and then") that the prose was carrying. Six comma-separated steps of one routine are prose; four call sites are a table.
7. Prefer an EXISTING table to a new one. When the page already carries a table over the same set, the enumerating sentence is usually the other half of a census that was split in two: extend that table to cover the whole population rather than building a second one beside it. A conversion pass that mechanically builds one table per flagged sentence produces two censuses of the same enum and a stranded two-row table.

**Before:**

```
register_dmub_notify_callback() is called five times in amdgpu, for
DMUB_NOTIFICATION_AUX_REPLY at drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:2145,
DMUB_NOTIFICATION_FUSED_IO at drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:2154,
DMUB_NOTIFICATION_HPD at drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:4324,
DMUB_NOTIFICATION_HPD_IRQ at drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:4330,
and DMUB_NOTIFICATION_HPD_SENSE_NOTIFY at
drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:4336, and dmub_callback[] is
written only inside that helper.
```

**After:**

```
amdgpu registers five notification callbacks, all through the one helper that
writes dmub_callback[]. Nothing else writes that array.

| notification | registered at |
|---|---|
| DMUB_NOTIFICATION_AUX_REPLY        | drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:2145 |
| DMUB_NOTIFICATION_FUSED_IO         | drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:2154 |
| DMUB_NOTIFICATION_HPD              | drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:4324 |
| DMUB_NOTIFICATION_HPD_IRQ          | drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:4330 |
| DMUB_NOTIFICATION_HPD_SENSE_NOTIFY | drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c:4336 |

Every cell is linked. A location cell keeps the full tree-relative path and line as its
text, because that is what a location link's text is everywhere else on a page; the
saving is that it is written once per row instead of once per member, and it sits in a
column the reader can skip rather than mid-sentence. The lead-in above the table ends in
a full stop, never a colon.
```

**PASS CRITERIA:**

1. Read every enumerating sentence in DETAILS, SUMMARY, and the lead; no candidate pattern expresses this shape, so it is a read-through. The generator is a grep for sentences carrying three or more commas plus "and"; rank the hits by how many DISTINCT file:line locations each carries, because a sentence with four locations is almost always a real hit and a sentence with one is almost never. Split sentences on semicolons as well as full stops, or an eleven-member enumeration written with semicolons is invisible to the generator.
2. Count the enumerated members in each. Confirm none carries more than three.
3. For each set of four or more, confirm a table exists, that its rows are the members, and that the prose above it states what the set is rather than restating the rows.
4. Confirm the table's cells carry their links, in every row.
5. Pass at zero enumerating sentences over three members outside a table.
