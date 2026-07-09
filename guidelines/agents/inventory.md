# Inventory agent

Role: read-only research agent producing one compact area digest during campaign planning (`guidelines/campaign/planning.md`, step 2). One agent per major area, three to six areas, dispatched in parallel; read-only inventory agents are safe to parallelize.
Model tier: mid-tier is acceptable; the deliverable is anchored facts, not judgment.
Mandatory reading: none beyond the brief; it is self-contained by design (an inventory agent never needs the writing rules).
Report: the digest itself as the final message, nothing else; the orchestrator records it verbatim in the plan file's Inventory findings section.
Death/resume: when an inventory agent dies (rate limit, transient API error), resume that same agent and ask for the compact report of what it has so far instead of restarting the research; spawn a fresh agent only after resuming fails twice.

## Inventory brief template

One brief per area; fill the brackets. Dispatch all areas in parallel as read-only agents.

```
Inventory the <area name> area of the <subsystem> subsystem for a
documentation campaign. Read-only research; do not write or edit any file.

Tree: <path>, version <tag>. Search with semcode (find_type, find_function,
find_callers, grep_functions) plus Grep and Read, over: <kernel_paths
subset for this area>. Index line numbers are hints; confirm on disk
before reporting a location.

Return a COMPACT digest (a report of anchored facts, not prose chapters):
1. Core structs of the area: each with its field groups, one-line roles,
   and the definition's file:line.
2. API families: entry points, helpers, accessor macros, grouped by
   family, each with file:line and a one-line role.
3. Lifecycle and locking: alloc/init/free paths, the serializing locks,
   refcounting, state fields and their transitions, with file:line anchors.
4. Hard-coded limits: every constant bounding the mechanism, with its
   value and file:line.
5. Version-specific facts: symbols renamed, removed, or newly added at
   this version relative to widely-documented older kernels.
6. Suggested page topics the request does not list, each justified by the
   anchor symbols it would be built around.
Keep every item to one or two lines; the digest lands verbatim in a plan
file. Your final message is the digest itself, nothing else.
```
