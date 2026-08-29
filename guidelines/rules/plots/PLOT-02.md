# PLOT-02: Semantics tables for state sets and taxonomies

> Was: 7t. Semantics tables for state sets and taxonomies

**INPUT:** Every fixed state set, mode set, and part taxonomy the page documents, with the defining code for each member.

**OUTPUT:** One member-meaning-construct Markdown table per set, every state set with its legal transitions (as a transition table or a state figure), and every taxonomy with its classifying axis named; zero bare constant lists.

**Rule:** A fixed set of states or modes, or a classification of parts (a device power-state set, a page-fault-type set, a flag taxonomy, an error-code family, an ops struct's callback set), is presented as a table, not a bare list of constants: one row per member, a meaning column stating what the member is in the model, and a construct column linking the defining code. The encoding and lifecycle archetypes among the frozen samples show this member-meaning-construct shape for bitfields and object states.

**Rule:** A state set additionally documents its legal transitions — which member advances to which, and what drives each edge — as a transition table or, where the transitions carry spatial or temporal structure, an ASCII state figure. The table stays Markdown. A taxonomy documents its classifying axis: what distinguishes each class from its siblings, not only that the classes exist.

**PASS CRITERIA:** Enumerate the page's fixed state or mode sets and part taxonomies (power states, fault types, flag families, error-code families, ops callback sets). Each must appear as a table with one row per member, a meaning column stating what the member is in the model, and a construct column linking the defining code; a bare list of constants fails. Each state set additionally shows its legal transitions, as a transition table or, where the transitions carry spatial or temporal structure, as an ASCII state figure; the Markdown table itself is never redrawn in box characters. Each taxonomy names its classifying axis, what distinguishes each class from its siblings. Pass when every enumerated set has its member-meaning-construct table and every state set its transitions.
