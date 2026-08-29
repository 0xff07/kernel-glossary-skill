# PLOT-04: Deriving from an existing page

> Was: 7p. Deriving from an existing page

**Rule:** Producing a page from existing material of any provenance — an earlier-generation draft, a prior revision, pages being compressed, merged, or split — follows four steps:

1. **Inventory the source first.** List its LINUX KERNEL catalog entries, DETAILS sections, distinct behaviors and call-site enumerations, figures, and KERNEL DOCUMENTATION and OTHER SOURCES entries.

2. **Give every inventory item an explicit disposition:** kept (and where it lands), merged (into which section), or cut (with the reason). No item disappears without a disposition — silent coverage loss during rewriting is the failure mode this rule exists to prevent.

3. **A cut is a scope decision, not an edit.** It removes the item from the LINUX KERNEL catalog and the scope statement in the same change, and is reported in the final message (and the campaign plan file) so the orchestrator or user can veto it. A symbol that stays in the catalog cannot have its DETAILS coverage cut.

4. **The derived page passes the same catalog-to-DETAILS parity audit as a fresh page.** Coverage in the source is not coverage in the derived page; "the source covered it" fails the audit.

History, and the measured failure that motivates the rule: a 2,645-line page compressed to 1,268 lines kept its iterator-helper symbols in the catalog while silently dropping their DETAILS sections, kept one catalog symbol with no DETAILS mention at all, and landed at 0.73 fenced blocks per catalog entry where every conforming page measures at least 1.0. The parity audit catches the desync mechanically; the disposition list is what makes any removal legitimate.

**PASS CRITERIA:** A derived page passes only with the four artifacts on record: the source inventory (its LINUX KERNEL catalog entries, DETAILS sections, distinct behaviors and call-site enumerations, figures, and KERNEL DOCUMENTATION and OTHER SOURCES entries); a disposition for every inventory item (kept and where, merged into which section, or cut with the reason), with zero items lacking one; for every cut, evidence that the catalog and the scope statement shrank in the same change and that the cut was reported in the final message and the campaign plan file; and the derived page's own catalog-to-DETAILS parity audit, since coverage in the source is not coverage in the derived page. Check the tripwire: fenced C blocks per catalog entry at or above 1.0. Pass at zero items without a disposition and zero silent drops.
