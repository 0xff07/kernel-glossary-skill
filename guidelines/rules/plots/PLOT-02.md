# PLOT-02: Semantics tables for state sets and taxonomies

> Was: 7t. Semantics tables for state sets and taxonomies

**INPUT:** Every fixed state set, mode set, and part taxonomy the page documents, with the defining code for each member.

**OUTPUT:** One member-meaning-construct Markdown table per set, every state set with its legal transitions (as a transition table or a state figure), and every taxonomy with its classifying axis named; zero bare constant lists.

**Rule:**

1. A fixed set of states or modes, or a classification of parts (a device power-state set, a page-fault-type set, a flag taxonomy, an error-code family, an ops struct's callback set), is presented as a table, not a bare list of constants: one row per member, a meaning column stating what the member is in the model, and a construct column linking the defining code.
2. The exemplar pages under `docs/sound/` show this member-meaning-construct shape: `docs/sound/dapm/widgets/widget-types.md` tables every `enum snd_soc_dapm_type` member against its constructor macro and its role, and `docs/sound/flows/playback.md` tables each ioctl against the core function it reaches and the PCM state it leaves.

**Rule:**

1. A state set additionally documents its legal transitions — which member advances to which, and what drives each edge — as a transition table or, where the transitions carry spatial or temporal structure, an ASCII state figure.
2. The table stays Markdown.
3. A taxonomy documents its classifying axis: what distinguishes each class from its siblings, not only that the classes exist.

**PASS CRITERIA:**

1. Enumerate the page's fixed state or mode sets and part taxonomies (power states, fault types, flag families, error-code families, ops callback sets).
2. Each must appear as a table with one row per member, a meaning column stating what the member is in the model, and a construct column linking the defining code; a bare list of constants fails.
3. Each state set additionally shows its legal transitions, as a transition table or, where the transitions carry spatial or temporal structure, as an ASCII state figure; the Markdown table itself is never redrawn in box characters.
4. Each taxonomy names its classifying axis, what distinguishes each class from its siblings.
5. Pass when every enumerated set has its member-meaning-construct table and every state set its transitions.
