# PAGE-05: OTHER SOURCES provenance

> Was: 7n. OTHER SOURCES provenance

**INPUT:** The OTHER SOURCES section, and the `Link:` trailers from git log (or semcode dig output) for the commits the page discusses.

**OUTPUT:** Every entry a byte-exact trailer or dig URL in the `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)` format, with trailer-less commits cited in prose only; delivered with each entry traced to its source.

**Rule:**

1. Every OTHER SOURCES entry is a mailing-list URL taken byte-exactly from a `Link:` trailer in `git log` output for a commit the page discusses (both `https://lore.kernel.org/...` and `https://lkml.kernel.org/r/<message-id>` trailer forms qualify), or a lore.kernel.org URL returned by the semcode `dig` tool for that commit.
2. Never construct, guess, or "normalize" a URL: no hand-built `git.kernel.org/.../commit/?id=` links, no reconstructed lore paths, no search-result URLs.
3. Format each entry as `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`.
4. A relevant commit with no `Link:` trailer is cited in prose by sha and subject and gets no OTHER SOURCES entry.

**PASS CRITERIA:**

1. For every OTHER SOURCES entry, re-derive the URL: re-run `git log` on the discussed commit (or semcode `dig`) and confirm the entry's URL matches the `Link:` trailer or dig output byte for byte.
2. Any constructed, guessed, or normalized URL fails, hand-built `git.kernel.org/.../commit/?id=` links and reconstructed lore paths included.
3. Confirm each entry's format is `[<commit subject> (commit <abbreviated sha>)](<trailer URL>)`, and that every relevant commit lacking a `Link:` trailer is cited in prose only, with no OTHER SOURCES entry.
4. Pass when every entry is traced to its trailer or dig source.
