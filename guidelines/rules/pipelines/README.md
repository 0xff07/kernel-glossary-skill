# pipelines/

End-to-end execution strategies over the rules, one file per pipeline, picked per task: PIPELINE-01 is the checking walkthrough, PIPELINE-02 the one-pass build-and-fix order.

**Reference direction is one-way, and it is enforced.** A file in this directory may reference `bans/`, `diagrams/`, `facts/`, `page/`, `plots/`, `routines/`, and its siblings here. No file in those directories may reference `pipelines/` or any `PIPELINE-XX`, by name or by path, ever. A pipeline can therefore be added, renamed, or deleted without touching a single rule or routine.

The boundary is grep-checkable from `guidelines/rules/`:

```
grep -rn 'PIPELINE-[0-9]\|pipelines/' bans/ page/ facts/ plots/ diagrams/ routines/
```

must print nothing. (The pattern is anchored to the numbered names and the path so that kernel-domain tokens in verbatim rule text, such as the `PIPELINE_STATE` IPC message in a reference figure, do not false-positive.)
