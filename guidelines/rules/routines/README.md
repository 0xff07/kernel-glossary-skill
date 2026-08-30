# routines/

The harness's protocol and tools, one file each: ROUTINE-01 (the checking protocol: ownership and independence, the prose-view builder, the figure sweep, the blind-spot discipline), ROUTINE-04 (the scan-pattern watch list and sweep-execution audit), ROUTINE-05 (the fix recipes).

## Reference boundary

**Reference direction is one-way, and it is enforced.** A routine may reference every rule directory (bans/, diagrams/, facts/, page/, plots/), each directory's `<PREFIX>-WAIVERS.md` harness file, and its siblings here — never the retired pipelines/ or any PIPELINE-XX, by name or by path (retired names stay forbidden, and the grep below keeps guarding). Routines are referenced from the passes above the rules tree; no rule file references a routine.

The boundary is grep-checkable from `guidelines/rules/`:

```
grep -rn 'PIPELINE-[0-9]\|pipelines/' routines/ROUTINE-*.md
```

must print nothing (the glob keeps this README out of the sweep).
