# The inventory brief

The inventory brief, one per area, dispatched in parallel to read-only agents on a mid-tier model; the digest lands verbatim in the spec, every location tree-relative:

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
7. Tracing integration: tracepoint definitions and their instantiation
   sites, every trace_*() call site, probes on other subsystems'
   tracepoints, private ftrace instances, tracers and exporters, and the
   seams where this area fires an adjacent subsystem's events, cited at
   both ends. Per class: enumerate with file:line, or a verified negative.
8. Debug and diagnostic printing: the mechanisms in play, per-file counts
   for the heavy hitters, every control knob (Kconfig, module params, boot
   params) with file:line, and the load-bearing sites; assertion families
   are a mechanism entry with counts, never a site enumeration.
9. Asynchronous, deferred, or lazy processing: every workqueue, work item,
   timer, irq_work, tasklet, kthread, RCU deferral, completion handoff,
   task_work and notifier chain, each with queuing site, execution context
   and handler at file:line, plus lazy or deferred init designs; absent
   classes get verified negatives.
10. Subsystem-specific debugging infrastructure: dedicated debugfs, sysfs
    and procfs surfaces, debug chardevs and ioctls, fault injection, dump
    or replay facilities, in-tree userspace tooling, each with file:line
    and its Kconfig gate; only what this subsystem itself declares.
Items 7-10 are inventory devices: enumerate or verify negative at plan
time, and name gates at write time. Pages document the default build and
name a config gate in one sentence where a cited path sits behind one.
Keep every entry to one or two lines. Your final message is the digest
itself, nothing else.
```
