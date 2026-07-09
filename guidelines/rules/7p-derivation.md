# 7p. Deriving from an existing page (mandatory)

Rule IDs (7, 7a-7r) resolve via `guidelines/rules/INDEX.md`; 7g-7i live under `guidelines/diagrams/`.

These rules govern producing a page from existing material of any provenance, in any subsystem: an earlier-generation draft, a prior revision of the same page, or pages being compressed, merged, or split.

1. Inventory the source first. List the source's LINUX KERNEL catalog entries, its DETAILS sections, the distinct behaviors and call-site enumerations it documents, its figures, and its KERNEL DOCUMENTATION and OTHER SOURCES entries.
2. Give every inventory item an explicit disposition: kept (and where it now lands), merged (into which section), or cut (with the reason). No item disappears without a disposition; a coverage loss that happens as a side effect of rewriting is the failure mode this rule exists to prevent.
3. A cut is a scope decision, not an edit. It removes the item from the LINUX KERNEL catalog and from the scope statement in the same change, and it is reported in the final message (and recorded in the campaign plan file) so the orchestrator or the user can veto it. A symbol that stays in the catalog cannot have its DETAILS coverage cut.
4. The derived page passes the same Gate B parity audit (item 1; `guidelines/gates/gate-b.md`) as a fresh page. Coverage in the source is not coverage in the derived page; "the source covered it" fails the audit.

A measured failure of exactly this kind motivates the rule: a 2,645-line page compressed to 1,268 lines kept its iterator-helper symbols in the LINUX KERNEL catalog while silently dropping their DETAILS sections, kept one catalog symbol with no DETAILS mention at all, and landed at 0.73 fenced blocks per catalog entry where every conforming page measures at least 1.0. The parity audit catches the desync mechanically; the disposition list is what makes any removal legitimate.
