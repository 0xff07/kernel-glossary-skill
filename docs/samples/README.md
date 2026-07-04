# Golden samples

This directory holds frozen copies of exemplar pages for the kernel-glossary skill. SKILL.md refers to example pages only by their `docs/samples/` path, so these files stay findable even after the subsystem directory hierarchy under `docs/` is reorganized. The copies are snapshots taken from the memory-management campaign (kernel v7.0); the live pages under `docs/mm/` may evolve independently.

Files prefixed `golden-` met every gate in SKILL.md and passed `scripts/verify_page.py` with zero findings against their kernel tree. They are the standard to calibrate against when writing any new page, for any subsystem.

- `golden-overview-mm-struct.md` (2,940 lines, 98 code blocks, 861 links, 1 figure) demonstrates the structure-tour archetype, documenting one central struct field group by field group with a full accessor and lifecycle catalog.
- `golden-lifecycle-mm-refcount.md` (1,743 lines, 59 code blocks, 591 links, 1 figure) demonstrates the lifecycle/refcount archetype and the smallest acceptable depth for a fine-grained page.
- `golden-encoding-pgtable-entries.md` (3,024 lines, 141 code blocks, 718 links, 3 figures) demonstrates the encoding/bitfield archetype, including register and bitfield figures drawn to SKILL.md rule 7h.
- `golden-enhanced-vma-overview.md` (2,922 lines, 107 code blocks, 634 links) is a page rebuilt from an earlier-generation draft to the current standard.

The file prefixed `plan-` is a planning artifact, and page gates do not apply to it.

- `plan-mm-campaign.md` is the plan file of the campaign that produced the pages above: the request's constraints, per-area inventory digests, the 87-row page catalog with requested/curated tags, fold-in adjudications, overlap boundary rules with seam symbols, batch orders (current and superseded), and dated user amendments. Its Status section is deliberately reduced to generic entry shapes with placeholders, so the example shows the form a living execution log takes without tying the sample to any one run. It is the worked example for the "Plan before generating" and "Plan file structure" sections of SKILL.md.

The file prefixed `draft-` is a counterexample and must not be imitated.

- `draft-original-vma-overview.md` (1,161 lines, 43 code blocks, 409 links) is the stale draft that `golden-enhanced-vma-overview.md` was rebuilt from. It reads plausibly and is wrong in places (it claims `vm_mm` is written exactly once, misstates the anonymous `vm_pgoff` encoding, and miscounts the `vma_set_range()` call-site distribution), and it fails the machine verifier. It is kept so the measurable gap between a plausible draft and a page meeting the SKILL.md standard stays visible. See the "Draft-versus-golden contrast" section of SKILL.md.

Where a sample and a rule in SKILL.md disagree, the rule governs; samples are calibration, not license.
