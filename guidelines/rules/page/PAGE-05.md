# PAGE-05: OTHER SOURCES provenance

> Was: 7n. OTHER SOURCES provenance

**Rule:** Every OTHER SOURCES entry is a mailing-list URL taken byte-exactly from a `Link:` trailer in `git log` output for a commit the page discusses (both `https://lore.kernel.org/...` and `https://lkml.kernel.org/r/<message-id>` trailer forms qualify), or a lore.kernel.org URL returned by the semcode `dig` tool for that commit. Never construct, guess, or "normalize" a URL: no hand-built `git.kernel.org/.../commit/?id=` links, no reconstructed lore paths, no search-result URLs. Format each entry as `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`. A relevant commit with no `Link:` trailer is cited in prose by sha and subject and gets no OTHER SOURCES entry.

**PASS CRITERIA:** For every OTHER SOURCES entry, re-derive the URL: re-run `git log` on the discussed commit (or semcode `dig`) and confirm the entry's URL matches the `Link:` trailer or dig output byte for byte. Any constructed, guessed, or normalized URL fails, hand-built `git.kernel.org/.../commit/?id=` links and reconstructed lore paths included. Confirm each entry's format is `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`, and that every relevant commit lacking a `Link:` trailer is cited in prose only, with no OTHER SOURCES entry. Pass when every entry is traced to its trailer or dig source.
