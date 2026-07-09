# 7n. OTHER SOURCES provenance (mandatory)

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

Every OTHER SOURCES entry is a mailing-list URL taken byte-exactly from a `Link:` trailer in `git log` output for a commit the page discusses (both `https://lore.kernel.org/...` and `https://lkml.kernel.org/r/<message-id>` trailer forms qualify), or a lore.kernel.org URL returned by the semcode `dig` tool for that commit. Never construct, guess, or "normalize" a URL: no hand-built `git.kernel.org/.../commit/?id=` links, no reconstructed lore paths, no search-result URLs. Format each entry as `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`. A relevant commit that has no `Link:` trailer is cited in prose by sha and subject and gets no OTHER SOURCES entry.
