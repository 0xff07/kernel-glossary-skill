# xHCI knowledge-base campaign: plan

> MIGRATED 2026-07-18 to the campaigns/ layout (SKILL.md, "The three artifacts and the three states"): this file is now the committed, execution-free campaign SPEC. Its former Status section moved to the machine-local run log `progress/xhci/log.md` on the machine that ran it; execution state is derived (catalog vs `docs/`), and runs happen only as user-invoked slices under the overwrite guard. This spec predates the machine-portability rule — any absolute path remaining in it is historical record to re-derive from the local environment at dispatch time, and where its older wording conflicts with current `guidelines/`, the guidelines govern.

## Context

Campaign short name: `xhci`. Campaign file: `campaigns/xhci.md`; artifact directory: `progress/xhci/` (dossiers, lint/verify reports, parity tables, and other agent intermediates land there; nothing outside it).

Machine-portability convention (a hard requirement of this campaign's request): this file hardcodes no machine-specific information. Two roots anchor every path:

- `SKILL_DIR` — the kernel-glossary skill root, the directory holding `SKILL.md`; this file lives at `SKILL_DIR/campaigns/xhci.md`. Bare relative paths in this file (`docs/...`, `guidelines/...`, `progress/...`) resolve against SKILL_DIR.
- `TREE_ROOT` — the Linux kernel checkout that contains the skill at `.claude/skills/kernel-glossary-skill`; kernel source paths (`drivers/usb/host/...`) resolve against TREE_ROOT. TREE_ROOT is identified by pin, not by path: at TREE_ROOT, `git describe --tags` prints `v7.0` and `git rev-parse HEAD` prints `028ef9c96e96197026887c0f092424679298aae8`. A resuming agent on any machine verifies both before trusting the tree.

Sub-agent briefs are composed at dispatch time and carry absolute paths resolved on the dispatching machine (per SKILL.md); this file never does.

Request source: `prompt.md` at TREE_ROOT (untracked; may be absent on other machines — the Scope decisions section below carries every load-bearing constraint verbatim, so this file stands alone). The request: a fine-grained xHCI documentation set focused on "how Linux kernel internally tracks/represents some of the major xHCI constructs and topologies, and how they connect to kernel's internal USB subsystem construct", with a 13-heading topic list the prompt itself calls "a rather rough idea" whose missing details this campaign fills in. The session instruction accompanying the request adds: cover most of the general xHCI concepts but not individual xHCI controller implementations, and keep this plan file machine-portable.

Documented tree: tag `v7.0`, commit `028ef9c96e96197026887c0f092424679298aae8` ("Linux 7.0"). semcode index complete at that commit (verified 2026-07-16). elixir.bootlin.com carries the tag (verified 2026-07-16); all Elixir links use `https://elixir.bootlin.com/linux/v7.0/source/...`. Subsystem Map entry xHCI (`guidelines/reference/subsystems.md`): dir `xhci`, tag `usb` (secondary: `xhci`), kernel_paths `drivers/usb/host/xhci*` + `include/linux/usb/hcd.h`, spec "xHCI (eXtensible Host Controller Interface) Specification", section6_heading REGISTERS. The USB-core seam (`drivers/usb/core/`, `include/linux/usb.h`, `include/uapi/linux/usb/ch9.h`) is cited where xHCI meets it; no page documents USB-core internals beyond the seam.

Draft corpus (rule 7p input) — SUPERSEDED 2026-07-21, the corpus was deleted in skill commit `74a4126`; see Amendment 2026-07-21. As planned: the committed draft set at `docs/xhci/` — 43 pages, ~27.6k lines, added to the skill repository as "basic memos" (skill commits `866c476`, `f5b7c3b`). The claim that it is "version-controlled and therefore present on any checkout of the skill" no longer holds: it is reachable only through skill-repo history at `f5b7c3b`. CORRECTION to the request: prompt.md points at `v7.0/kernel-glossary-devel/docs/xhci`; no such directory exists on the planning machine — the corpus it describes is the set committed at `docs/xhci/` (its layout and "primitive results" description match). The prompt licenses mining these drafts for inspiration and page curation, and reusing their ASCII diagrams after conversion to house style (7g-7i).

NOT inputs: other campaigns' entries under `progress/` (run isolation per SKILL.md, "The three artifacts and the three states"); `guidelines/reference/samples/` pages (style/structure/depth calibration only, never kernel facts); the empty `plan.md` at TREE_ROOT (zero bytes, a dead session's leftover); any external xHCI documentation as a source of claims (every fact is researched against the tree; the xHCI specification is cited as SPECIFICATIONS material per the template, never as a substitute for kernel evidence).

Output root: `docs/xhci/` — pages land at the catalog's paths. (As planned this was a rewrite landing in place over the draft corpus; since 2026-07-21 the corpus is deleted and every row is a clean new write — see Amendment 2026-07-21.) No `SUMMARY.md`/`mkdocs.yml` edits. No git commits without an explicit user go.

## Amendment 2026-07-21 — the draft corpus is gone; this is no longer a rewrite-in-place campaign

READ THIS BEFORE THE RE-ENTRY CONTRACT BELOW; it supersedes parts of it.

The user deleted the entire 43-page draft corpus in skill commit `74a4126` ("xhci: remove old pages"), verified: `docs/xhci/` holds zero files and HEAD tracks zero paths beneath it. The drafts remain recoverable in skill-repo git history at `f5b7c3b`. Four consequences, all durable:

1. **Every catalog row is now a clean new write.** The campaign was planned as REWRITE-IN-PLACE, where 40 of the 58 rows sat under a same-slug draft file. That is no longer true of any row. Re-entry contract step 2's warning that "a file on disk may be the old draft, not this campaign's output — existence is not completion" is DISCHARGED: from 2026-07-21 forward, a file present at a catalog path under `docs/xhci/` is this campaign's output, and the catalog-vs-`docs/` diff is an exact statement of remaining work with no ambiguity to resolve.
2. **The overwrite guard's rewrite-in-place form (step 4) is moot.** Nothing on disk can be silently clobbered because nothing is on disk. The ordinary guard still stands for re-invoked slices: a page this campaign already wrote is never overwritten silently — stop and ask.
3. **The save policy's superseded-draft deletion clause is discharged.** `overview.md`, `usb-hcd-bridge.md`, and `device/bandwidth.md` were the three drafts scheduled for removal at the batches shipping their replacements (B1 and B7). All three are already gone; those batches carry no deletion housekeeping, and the Draft reuse map's slug mapping retains no operational role whatsoever.
4. **The Context section's Draft-corpus claim is refuted.** It states the corpus is "version-controlled and therefore present on any checkout of the skill". False as of `74a4126`. The corpus is reachable only through skill-repo history. This changes nothing about execution — user decision 1 already barred the drafts as writer input, and writers were never given pointers to them — but the reuse map's per-file audit record now describes files that a fresh checkout will not contain.

Retained from the reuse map as TREE FACTS (properties of the v7.0 tree, not of the deleted drafts) and carried in every writer brief: `Documentation/usb/xhci.rst` and `Documentation/driver-api/usb/hcd.rst` do not exist and never have — do not re-fabricate them; `xhci_hc_died` is defined in `xhci-ring.c`; the No-Op command TRB is produced by `trb_to_noop()` rewriting a TRB in place, never by a queue helper; no literal `csz` field exists in the driver (HCCPARAMS1 bit 2 via `HCC_64BYTE_CONTEXT`/`CTX_SIZE()` only). The nine write-time cautions in Execution & verification stand unchanged.

TREE REFUTATION FOUND AT WRITE TIME (B1, 2026-07-21) — `xhci_link_segments` DOES NOT EXIST at v7.0. A tree-wide grep returns zero hits. The spec inherited the name from its own Area D inventory and carried it in five places: the Area D event-ring bullet, the Area D ring alloc/free/expand list, the `ring-overview.md` and `segment-chaining.md` catalog rows, and boundary rule 6's seam list. The real symbols are `xhci_set_link_trb` (`xhci-mem.c:96`, writes the Link TRB) and `xhci_initialize_ring_segments` (`xhci-mem.c:116`), whose `type == TYPE_EVENT` early return sits at `:121` — the spec's `:102` anchor is a bare `return;`. Commit `90e91ccbdd00` ("usb: xhci: rework xhci_link_segments()") renamed the writer and `f53ce003ccd5` ("usb: xhci: add xhci_initialize_ring_segments()") added the initializer. All five sites are corrected in place and tagged `[CORRECTED 2026-07-21]`. This mattered before B2: `segment-chaining.md` is a B2 row and would have been briefed on a symbol that does not exist.

BRIEF DEFECT FOUND AT WRITE TIME (B1, 2026-07-21) — the B1 writer briefs instructed writers to cross-cite sibling pages using relative `.md` catalog paths. That contradicts rule 7f, which forbids internal `.md` cross-links ABSOLUTELY (`rules.md:400`, and `rules.md:778`: "only non-URL `.md` targets are violations, and 7f forbids them absolutely"). Two writers resolved the conflict conservatively (naming sibling pages as bare inline-code spans, no link); one resolved it by following the brief and retained the links. Adjudicated: 7f governs — a dispatch brief cannot override a house rule. Sibling pages are named in prose as bare inline code, never linked. Every brief from B2 forward states this correctly, and the affected B1 pages are repaired before they are reported complete.

SIDEBAND RULE-8 WAIVER, MADE EVIDENCE-BASED (verified on disk 2026-07-21; refines review item 3). Review item 3 recorded that sideband.md's only in-tree consumer is vendor-gated and waived rule 8's usage-example mandate. The precise tree facts: all 12 exported `xhci_sideband_*` symbols are gated behind `CONFIG_USB_XHCI_SIDEBAND` (`drivers/usb/host/Kconfig:107`, `Makefile:35-36`). The client-facing registration/endpoint/interrupter API's sole in-tree consumer is `sound/usb/qcom/qc_audio_offload.c` — a banned-vendor offload driver, out of the documented driver tree. TWO exported symbols have non-vendor callers, which the waiver did not distinguish: `xhci_sideband_notify_ep_ring_free` is called from `drivers/usb/host/xhci.c` (the core driver — IN SCOPE, so the page carries exactly one real usage excerpt here), and `xhci_sideband_check` is called only from `drivers/usb/host/xhci-plat.c` (the platform driver — OUT OF SCOPE, documented by surface only like the vendor-consumer symbols). Net: the waiver stands, but the page has one legitimate in-scope usage excerpt rather than zero, and the platform caller is a specific do-not-document trap.

Also corrected in this amendment: the Directory organization block below said "twelve groups" and `device/ … (9)`. The post-review, post-checkpoint reality is thirteen groups and `device/` 8 — review item 14 folded `ep-state.md` into `device-tracking.md`, and the user checkpoint added the `dbc/` group. The Page catalog tables and the tag census were already correct; only that prose block had gone stale, and it is fixed in place.

## Re-entry contract (retrofitted 2026-07-18)

Standing instructions to any executor, on any machine, cold or warm:

1. Confirm the tree: a Linux kernel checkout at tag `v7.0`, commit `028ef9c96e96` (`git describe --tags` at the tree root prints `v7.0`). A different tree voids every anchor in this spec — stop and surface it.
2. Derive campaign state: diff this catalog's 58 rows against `docs/xhci/`. REWRITE-IN-PLACE campaign: the rewrite lands over the draft corpus at the same paths (drafts recoverable in skill-repo git history), so a file on disk may be the old draft, not this campaign's output — existence is not completion. Distinguish by this machine's run log, by git history of the page file, or by asking the invoker.
3. Create or reuse the machine-local workspace `progress/xhci/` (run log `log.md`, dossiers). It is never committed.
4. Execute ONLY the slice the invoker named — a batch from this spec's batch order (its recommended slicing), or an explicit page list. Given a bare "run xhci" with no slice: report the derived state and ask; never pick a slice autonomously. Overwrite guard, rewrite-in-place form: this spec licenses exactly one fresh write over each old-corpus page; when it is ambiguous whether a file on disk is the old corpus page or this campaign's finished output, stop and ask instead of overwriting.
5. Run the slice per SKILL.md "Modes": one writer per page, briefed per `guidelines/passes/02-write.md` with the page's catalog row, its cluster's boundary rules, and the project-specific bans and write-time cautions from this spec's Execution & verification section; then the orchestrator check per page (`guidelines/passes/03-check.md`); events go to the run log.
6. Promote anything durable — a spec claim the tree refuted, a user amendment, a settled adjudication — into this spec as a dated amendment (or surface it for the waivers files). The run log does not travel.
7. Verification: on demand only (user decision 3) — run `xhci-verify` only when the user asks (`guidelines/passes/04-verify.md`); CERTIFIED stamps land in the verify run's log.

## Scope decisions

### Hard constraints from the request (prompt.md, verbatim or near-verbatim)

1. Mission: pages cover "not only ... the common xHCI concepts (not vendor-specific implementation), but more importantly how Linux kernel internally tracks/represents some of the major xHCI constructs and topologies, and how they connect to kernel's internal USB subsystem construct. Make sure for every xHCI concept you also mention corresponding parts in the Linux kernel source code that interacts with that concept. Don't just create pure xHCI concept pages."
2. "Focus only on x86-64, ACPI-based systems. Do not mention any devicetree-based platforms (e.g. Qualcomm, TI, DWC)."
3. "Focus only on the PCI-based xHCI implementation in the kernel." And: "there's a xhci-hcd platform driver and xhci_hcd pci driver. Focus on the PCI-based one. Pay extra attention when you doing research."
4. "Ignore vendor-specific xHCI controller code (e.g. DWC, NVIDIA, TI, RENESAS, MEDIATEK)"; "You must not include vendor-specific things (e.g. Intel, NVIDIA)"; "You must not cover device-specific quirks."
5. "You must not include any content about old UHCI/EHCI/OHCI. Absolutely not. Not even historical revisiting."
6. "Don't limit yourself to 100-400 lines per page. Do as detailed as you can."
7. "You must use semcode tools." "You must not use hedging wordings."
8. "Make sure to cover as many internal tracking structures in the kernel and helper functions to maintain relevant structs in the kernel as possible." And: "For each helper function you mention, you MUST find concrete example usage in the kernel, and cite them as markdown code blocks, and reference them in the DETAILS section." (rules 7e, 7j, 7l)
9. Granularity and coverage: "Make the granularity as fine as possible. Look into the docs/acpi pages to understand how the granularity of each page should be." "Make sure you cover all the major structures for xHCI subsystem in the Linux kernel defined under the files in the drivers/usb/host/xhci-* file, and ONLY the ones relevant to xHCI (no OHCI, EHCI etc.)" Plus: "You may also need to look into things related to kernel's USB host controller framework, like include/linux/usb/hcd.h".
10. Registers folded into topics: "xHCI has some parameters and capabilities defined in its MMIO space. Fold those registers to the respective topics where relevant." "For each of the following topics, also add information for relevant xHCI MMIO registers into each page."
11. Error handling: "add how the ke[r]nel handles errors in xHCI for various scenarios into pages where relevant, but they must have their own section in DETAILS."
12. Naming caution: "some of the internal tracking structures in the kernel contain 'virt' in their naming. That does not mean it's for virtualization purposes, so be very careful when filtering."
13. Generation split: "If xHCI or kernel handle things differently for USB2.0 and USB3.0 devices, create a dedicated page for how each of the generations is handled, and add description in each page on why they differ. Don't fold them in a single page."
14. TRB census: "Make sure to mentioned every types of TRB somewhere."
15. Figures: "Draw ASCII diagrams to illustrate, but do not just draw the code enumerating flow graphs." For TRB/register layout figures: "look into the kmemo's pci TLP diagram style for reference. See pages in `docs/pci/protocol/tlp/msg/`" (7h register/bitfield style).
16. Drafts: the primitive corpus (see Context CORRECTION) is mineable — "you can get inspiration from them, especially when curating the pages"; "you can reuse the ASCII diagram ... just remember convert them to styles that fit your SKILL.md" (rule 7p and `guidelines/passes/plan.md` "Deriving from prior drafts and pages" govern).
17. Curation mandate: "They should include but not limited to the topic listed. Also this plan is a rather rough idea, so you need to fill in the details for them. Research the kernel source and fill in the missing details yourself." Blank bullets ("You have to curate this" — root hub, reset, shutdown, MSI/MSI-X) are curation obligations.

### Session-instruction constraints (the skill invocation)

18. "Make sure to cover most of the general xHCI concepts but not individual xh[c]i controller implementation" (reinforces constraint 4; controller-implementation pages are out of catalog scope entirely).
19. "Make the plan file so that it doesn't hardcode information specific to this machine (e.g. absolute path), to the degree that agents on the other machine should be able to run this campaign without being confused" (the portability convention in Context implements this).

### Planning adjudications (orchestrator, 2026-07-16)

- A1. Constraint 13 (per-generation pages): applied as dedicated pages where the kernel maintains distinct per-generation machinery for devices — ports/port-registers-usb2 vs -usb3, pm/usb2-device-pm vs usb3-device-pm. Where a single function carries generation branches (hub-descriptor/BOS synthesis in roothub/root-hub.md; the xhci_bus_suspend/resume sweep in roothub/bus-suspend-resume.md), a page split would produce sub-floor pages, so those rows carry MANDATORY per-generation sections plus the why-differs explanation instead (review item 6). Recorded so nobody re-litigates; the user checkpoint can veto.
- A2. Bandwidth rescope: the drafted bandwidth row became device/configure-endpoint.md after the slice-2 audit proved the SW accounting model is quirk-dormant outside one legacy device (documenting it as a primary topic would collide with the quirk ban).
- A3. Sideband: folded into interrupters.md with a recorded rule-8 usage-example exception (review item 3). SUPERSEDED by user decision 4: restored as a standalone page carrying the same exception.
- A4. xHCI Debug Capability (DbC) stays out of the catalog. SUPERSEDED by user decision 4: dbc/ group (2 rows) added.

### User-confirmed decisions (checkpoint answers, 2026-07-16)

1. Draft posture: "Write everything fresh" — neither the draft corpus nor its figures are writer inputs; every page is researched and written from the v7.0 tree alone. The Draft reuse map below is downgraded to reference/audit record, and writer briefs carry no draft pointers. (This supersedes the request's "get inspiration"/"reuse the ASCII diagram" clauses for execution; the audit record remains the evidence base for the known-defect classes and for any future round that revisits reuse. The tree-fact cautions in Execution & verification stand regardless — they are properties of the tree, not of the drafts.)
2. Output placement: "Overwrite in place" — pages land at the catalog paths under `docs/xhci/`, overwriting same-slug drafts; superseded/renamed draft files are deleted at the batch checkpoint that ships their replacements; skill-repo git history preserves the old corpus.
3. Verification cadence: "On demand only" — no scheduled verify campaign; the user triggers `xhci-verify` when wanted.
4. Catalog: sideband restored as a standalone page (with the recorded rule-8 exception) and the DbC fold-out reversed — dbc/dbgcap.md + dbc/dbgtty.md added (anchors from a planning-time scout of the three-file DbC set). Final catalog: 58 rows, 14 batches.

EXPLICIT SCOPE LIMIT FROM THE CHECKPOINT: "don't create any page yet. I just need the plan." — The plan is approved as amended, but PAGE GENERATION HAS NOT BEEN AUTHORIZED. No writer dispatches, no page writes, no draft deletions happen until the user gives a separate, explicit go to start batch B1. When that go arrives, pages save without per-page asks per campaign mode; git commits always need their own user go.

## Inventory findings

Six areas, split along the request's own headings; one compact digest per area, recorded verbatim from the read-only inventory agents. Kernel paths below are TREE_ROOT-relative.

- Area A — Host core, MMIO access & lifecycle: `drivers/usb/host/xhci.c`, `xhci.h`, `xhci-pci.c`, `xhci-ext-caps.h`, `drivers/usb/core/hcd.c`, `hcd-pci.c`, `include/linux/usb/hcd.h`. Feeds: overview/structures, MMIO accessors, hcd bridge, init, bus spawn, reset, shutdown.
- Area B — Root hub & ports: `drivers/usb/host/xhci-hub.c`, `xhci.h`, `xhci-ext-caps.h`, port-array setup in `xhci-mem.c`, seam `drivers/usb/core/hub.c`. Feeds: root hub, port registers (USB2/USB3), port events, port-level hotplug.
- Area C — Device slots & contexts: `drivers/usb/host/xhci-mem.c`, `xhci.c`, `xhci.h`. Feeds: slots/xhci_virt_device, context hierarchy (device/slot/endpoint/input), DCBAA, scratchpad, doorbells, numbering rules.
- Area D — Rings, TRBs, command ring, event ring & interrupts: `drivers/usb/host/xhci-ring.c`, `xhci-mem.c`, `xhci.h`, MSI/MSI-X setup in `xhci.c`/`xhci-pci.c`/`drivers/usb/core/hcd-pci.c`, `include/linux/usb/hcd.h`. Feeds: generic ring machinery, segments/link TRBs, cycle bits, TRB type census, command ring/CRCR/lifecycle, ERST/event ring, interrupters, ERDP, MSI/MSI-X, moderation.
- Area E — Transfers & USB-core integration: `drivers/usb/host/xhci-ring.c`, `xhci.c`, `xhci.h`, seams `drivers/usb/core/urb.c`, `hcd.c`, `message.c`, `hub.c`, `include/linux/usb/hcd.h`. Feeds: transfer rings, TD/TRB, doorbell usage, transfer lifecycle, transfer events, per-type pages (control/bulk/interrupt/isoch), streams, downstream hotplug flow.
- Area F — Power management: `drivers/usb/host/xhci.c`, `xhci-pci.c` (generic PM ops), `xhci-hub.c` (bus suspend/resume, LPM), `xhci.h`, seams `drivers/usb/core/hub.c`, `port.c`, `include/linux/usb/hcd.h`. Feeds: host PM, port PM, USB2 device PM, USB3 device PM, system suspend, system resume.

(All six area digests recorded below: A, B, C, D, E, F.)

### Area A: Host core, MMIO access & lifecycle — COMPLETE (recorded 2026-07-16)

#### 1. Core structs

- `xhci_hcd` — drivers/usb/host/xhci.h:1501 — one per controller. Groups: MMIO ptrs `cap_regs`/`op_regs`/`run_regs`/`dba` (xhci.h:1505-1509); cached RO caps `hcs_params2/3`,`hcc_params`,`hcc_params2` (xhci.h:1511-1514), `hci_version` (1519); locks `lock` spinlock_t (1516), `mutex` (1552); sizing `max_interrupters` u16 (1520), `max_slots`/`max_ports` u8 (1521-1522); rings `dcbaa`, `interrupters[]` (1535), `cmd_ring`+`cmd_ring_state` (1538-1540 bits), `cmd_list`, `cmd_timer`, `cmd_ring_stop_completion` (1544); DMA pools; `xhc_state` (1566) + `XHCI_STATE_*` bits (1581-1583); `quirks` u64 (1584) + ~50 `BIT_ULL` flags (1585-1636); `devs[MAX_HC_SLOTS]` (1554); per-roothub `usb2_rhub`/`usb3_rhub`; `debugfs_root`.
- `xhci_cap_regs` — xhci.h:65 — RO Capability block: `hc_capbase`(66, CAPLENGTH+HCIVERSION),`hcs_params1-3`(67-69),`hcc_params`(70),`db_off`(71),`run_regs_off`(72),`hcc_params2`(73).
- `xhci_op_regs` — xhci.h:104 — Operational block: `command`(105,USBCMD),`status`(106,USBSTS),`page_size`(107),`dev_notification`(110,DNCTRL),`cmd_ring`(111,CRCR),`dcbaa_ptr`(114,DCBAAP),`config_reg`(115,CONFIG),`port_regs[]`(118).
- `xhci_run_regs` — xhci.h:283 — `microframe_index`(284)+`ir_set[1024]` interrupter register sets.
- `xhci_intr_reg` — xhci.h:227 — one HW interrupter: `iman`,`imod`,`erst_size`,`erst_base`,`erst_dequeue`.
- `xhci_interrupter` — xhci.h:1446 — SW mirror of one interrupter (`event_ring`,`erst`,`ir_set` ptr, `s3_*` save fields); array element of `xhci_hcd.interrupters[]`.
- `xhci_doorbell_array` — xhci.h:298 — `doorbell[256]`, target of DBOFF.
- `xhci_port_regs` — xhci.h:84 — one port's PORTSC/PORTPMSC/PORTLI/PORTHLMPC.
- `xhci_port`/`xhci_hub` — xhci.h:1474 / xhci.h:1489 — SW mirror of one roothub port, and of a roothub (`ports[]`+`bus_state`).
- `xhci_device_context_array` — xhci.h:796 — the DCBAA: `dev_context_ptrs[MAX_HC_SLOTS]`+`dma`.
- `xhci_command` — xhci.h:528 — one command-ring entry (`in_ctx`,`status`,`completion`,`command_trb`,`cmd_list`).
- `xhci_driver_overrides` — xhci.h:1679 — per-glue hook substitution table consumed by `xhci_init_driver`.
- `usb_hcd` — include/linux/usb/hcd.h:68 — generic per-bus HCD; embeds `usb_bus self`; `driver` ops ptr; `flags`+`HCD_FLAG_*` bits (107-114); `state` (193)+`HC_STATE_*` (198-202); `shared_hcd`/`primary_hcd`; trailing `hcd_priv[]`.
- `hc_driver` — include/linux/usb/hcd.h:237 — the ops table: `reset/start/stop/shutdown`, `pci_suspend/pci_resume/pci_poweroff_late`, `irq`, root-hub hooks, xHCI-specific device/bandwidth hooks.

#### 2. API families

MMIO accessors: plain `readl()`/`writel()` used directly everywhere on `op_regs`/`cap_regs`/`run_regs` fields — xHCI has no `xhci_readl`/`xhci_writel` wrapper. `xhci_read_64`/`xhci_write_64` — xhci.h:1757-1761/1762-1766 — inline wrappers over `lo_hi_readq`/`lo_hi_writeq` for the 64-bit CRCR/DCBAAP/ERSTBA/ERDP fields. `xhci_handshake` — xhci.c:85-98 — generic poll-until-`(val&mask)==done`-or-timeout/removed helper backing halt/reset/start/abort.

Extended-cap walker: `xhci_find_next_ext_cap` — drivers/usb/host/xhci-ext-caps.h:130-157 — inline HCCPARAMS1-rooted linked-list walk. `xhci_ext_cap_init` — drivers/usb/host/xhci-ext-caps.c:84-109 — probe-time walk; in this tree acts only on a vendor role-switch cap, not on BIOS handoff.

hcd↔xhci converters: `hcd_to_xhci` — xhci.h:1698-1708 — casts `usb_hcd.hcd_priv[]`, resolves shared hcd to its primary. `xhci_to_hcd` — xhci.h:1710-1713 — returns `xhci->main_hcd`.

init/run/stop/halt/reset/shutdown (drivers/usb/host/xhci.c): `xhci_gen_setup` 5414-5540 (generic `.reset` body: cache caps 5443-5463, `xhci_halt`, `xhci_zero_64b_regs`, `xhci_reset(LONG)`, `xhci_init`, DMA mask). `xhci_init` 546-591 (static, one-time DCBAA/cmd-ring/interrupter-0 alloc via `xhci_mem_init`, program DCBAAP/doorbell/DNCTRL/interrupter0). `xhci_run` 643-694 (generic `.start`). `xhci_run_finished` 595-629 (static; CMD_EIE, enable interrupter, `xhci_start`). `xhci_start` 151-179 (sets CMD_RUN, waits STS_HALT==0). `xhci_stop` 706-754 (generic `.stop`). `xhci_shutdown` 766-800 (generic `.shutdown`). `xhci_halt` 127-146, `xhci_quiesce` 103-117, `xhci_reset` 188-245. `xhci_init_driver` 5631-5658 (copies base table `xhci_hc_driver`, xhci.c:5564, then applies `xhci_driver_overrides`; note the base table's `.reset` is `NULL` — only `.start=xhci_run/.stop=xhci_stop/.shutdown=xhci_shutdown` are generic, `.reset` is mandatory per-glue).

Generic PCI probe path (drivers/usb/core/hcd-pci.c): `usb_hcd_pci_probe` 172-292 — enables device, allocates one IRQ vector EXCEPT when the driver flags carry `HCD_USB3` (xHCI does, xhci.c:5573, so this generic path skips IRQ setup for it), maps BAR0, `usb_add_hcd`. `usb_hcd_pci_shutdown` 359-374 — calls `hcd->driver->shutdown`.

xHCI PCI glue (drivers/usb/host/xhci-pci.c): `xhci_pci_probe` 699-706 → `xhci_pci_common_probe` 611-689 (usb2 via `usb_hcd_pci_probe(&xhci_pci_hc_driver)`, then usb3 `shared_hcd` via `usb_create_shared_hcd`+`usb_add_hcd`, then `xhci_ext_cap_init`). `xhci_pci_setup` 566-595 (`.reset` override → `xhci_gen_setup(hcd, xhci_pci_quirks)`, `xhci_pci_reinit`). `xhci_pci_run` 211-222 (`.start` override: `xhci_try_enable_msi` then `xhci_run`). `xhci_pci_stop` 224-232 / `xhci_pci_shutdown` 928-939 (`.stop`/`.shutdown` overrides, wrap generic calls with `xhci_cleanup_msix`). `xhci_try_enable_msi` 143-209, `xhci_cleanup_msix` 129-140, `xhci_msix_sync_irqs` 116-126. `xhci_pci_quirks` 251-517 (generic quirk-bit accumulation machinery — contents intentionally not enumerated). `xhci_pci_driver` (`struct pci_driver`) 953-965; `xhci_pci_init`/`_exit` 967-983; `xhci_pci_overrides` 106-110; `xhci_pci_hc_driver` 99.

Generic hcd bring-up/teardown (drivers/usb/core/hcd.c): `usb_create_hcd` 2659-2663 / `usb_create_shared_hcd` 2636-2641. `usb_add_hcd` 2802-3016 (buffers, `usb_register_bus`, alloc root hub, `driver->reset`/`driver->start`, `register_root_hub`). `usb_remove_hcd` 3028-3092. `usb_stop_hcd` 2778-2790 (static; `driver->stop`+`HC_STATE_HALT`). `register_root_hub` 951-1006 (static; roothub descriptor read + `usb_new_device`). `usb_hcd_is_primary_hcd` 2708-2713 (proto hcd.h:461).

#### 3. Lifecycle and locking

- Alloc/init order (PCI): `pci_enable_device` → `usb_create_hcd`(usb2) → `usb_add_hcd`(usb2: `.reset`=`xhci_pci_setup`→`xhci_gen_setup`→`xhci_init`; `.start`=`xhci_pci_run`→`xhci_run`) → `xhci_ext_cap_init` → `usb_create_shared_hcd`(usb3) → `usb_add_hcd`(usb3, reuses same `xhci_hcd`, `xhci_run` finishes/defers 2nd roothub).
- Teardown order: `xhci_pci_remove`(xhci-pci.c:708-734) → `usb_remove_hcd`(shared) → `usb_hcd_pci_remove` → `usb_remove_hcd`(primary) → `.stop` frees memory only once, guarded by `!usb_hcd_is_primary_hcd()` in `xhci_stop` (xhci.c:706-754) → `xhci_mem_cleanup` (xhci-mem.c:1898-1998).
- Locks: `xhci->lock` spinlock_t (xhci.h:1516, init xhci.c:552) — serializes register/state writes, command-ring and URB-giveback paths (held across `xhci_stop`/`xhci_shutdown`/`xhci_run_finished`/`xhci_handle_command_timeout`). `xhci->mutex` (xhci.h:1552, init xhci.c:5441) — serializes slot-enable/address-device, wraps all of `xhci_stop`. `hcd_root_hub_lock` static spinlock (drivers/usb/core/hcd.c:92) — guards `rh_registered`/`HCD_FLAG_RH_RUNNING`/`DEAD`. `usb_bus_idr_lock` mutex (hcd.c:88) — guards bus-id alloc & roothub disconnect ordering. `cmd_ring_stop_completion` (xhci.h:1544) — abort-ring rendezvous.
- State fields: `xhci_hcd.xhc_state` (xhci.h:1566): 0 ↔ `XHCI_STATE_DYING`(1)/`HALTED`(2)/`REMOVING`(4) (xhci.h:1581-1583), OR-ed in by `xhci_halt`/`xhci_stop`/`xhci_hc_died`/`xhci_pci_remove`, cleared only by `xhci_start` (xhci.c:151-179, `xhci->xhc_state = 0`). `cmd_ring_state`: `RUNNING`/`ABORTED`/`STOPPED` (xhci.h:1538-1540). `usb_hcd.state` (hcd.h:193): `HC_STATE_HALT`(0)/`RUNNING`/`QUIESCING`/`RESUMING`/`SUSPENDED` (hcd.h:198-202) from `__ACTIVE`/`__SUSPEND`/`__TRANSIENT` bits (194-196).

#### 4. Hard-coded limits

- `MAX_HC_SLOTS` 256 — xhci.h:36 (spec §6.1 cap).
- `MAX_HC_PORTS` 127 — xhci.h:41 (spec allows up to 255).
- `MAX_HC_INTRS` 128 — xhci.h:46 (spec allows up to 1024; `xhci_run_regs.ir_set[]` stays sized 1024, xhci.h:283-285 — array is oversized vs. the SW cap).
- `XHCI_MAX_HALT_USEC` = 32*1000 — drivers/usb/host/xhci-ext-caps.h:12 — halt-bit/start-bit handshake timeout.
- `XHCI_RESET_LONG_USEC` = 10*1000*1000 — xhci.h:151 — used only for the first reset in `xhci_gen_setup`.
- `XHCI_RESET_SHORT_USEC` = 250*1000 — xhci.h:152 — used by `xhci_stop`/`xhci_shutdown`/`xhci_mem_init`-failure resets.
- Command-ring abort handshake: inline `5*1000*1000` us literal — drivers/usb/host/xhci-ring.c:524 (`xhci_abort_cmd_ring`) — plus a 2000 ms `wait_for_completion_timeout` at xhci-ring.c:537.
- `XHCI_CMD_DEFAULT_TIMEOUT` 5000 (ms) — xhci.h:1322; `XHCI_STOP_EP_CMD_TIMEOUT` 5 (s) — xhci.h:1417.
- `XHCI_MAX_EXT_CAPS` 50 — drivers/usb/host/xhci-ext-caps.h:25 — defined but never referenced as a loop bound (the walker trusts the HW NEXT-chain/all-ones sentinel instead).
- `COMP_MODE_RCVRY_MSECS` 2000 — xhci.h:1667. `AVOID_BEI_INTERVAL_MAX` 32 — xhci.h:1276 (clamp applied once in `xhci_init`).

#### 5. Version-specific facts

- Interrupter restructuring: `xhci_hcd` no longer embeds one event-ring/ERST/ir_set trio inline; it holds `struct xhci_interrupter **interrupters` (xhci.h:1535) sized by `max_interrupters` (xhci.h:1520), each a heap object (xhci.h:1446) built by `xhci_mem_init`/`xhci_add_interrupter` (xhci-mem.c:2401,2320) — widely-documented older-kernel xhci_hcd carried those fields directly instead of this array-of-objects.
- Capability/port macros split out of xhci.h: `HC_LENGTH`/`HC_VERSION`/`HCS_MAX_SLOTS`/`HCS_MAX_PORTS`/`HCS_MAX_INTRS`/`HCC_64BIT_ADDR`/`HCC_MAX_PSA`/`RTSOFF_MASK`/`DBOFF_MASK` now live in the new drivers/usb/host/xhci-caps.h (pulled in at xhci.h:27); PORTSC/PLS bitmasks live in the new drivers/usb/host/xhci-port.h (xhci.h:26). Code citing "xhci.h" alone for these macros is citing the wrong file at this version.
- MSI ownership fully in xhci-pci.c: generic `usb_hcd_pci_probe` (hcd-pci.c:172) skips its own IRQ-vector allocation for drivers flagged `HCD_USB3` (xHCI is, xhci.c:5573); all MSI-X/MSI/legacy setup happens in `xhci_try_enable_msi` (xhci-pci.c:143) called from the `.start` override `xhci_pci_run` (xhci-pci.c:211) — not from hcd-pci.c, not from generic `xhci_run()`.
- `xhci_driver_overrides` (xhci.h:1679) has no `pci_suspend`/`pci_resume`/`pci_poweroff_late`/`stop`/`shutdown` members; xhci-pci.c assigns those directly onto `xhci_pci_hc_driver` after `xhci_init_driver()` returns (xhci-pci.c:970-974) — the override struct alone doesn't capture every PCI-specific hook swap.
- "FLADJ" does not exist for xHCI in this tree: no FLADJ/GFLADJ symbol appears anywhere under drivers/usb/host/xhci*, drivers/usb/core/hcd*.c, or include/linux/usb/hcd.h — the only FLADJ hits in the whole USB tree are dwc3 (`DWC3_GFLADJ`, out of scope). Any initialization-page bullet naming FLADJ against xHCI must be dropped or retargeted (FLADJ is a PCI config register the firmware owns; the v7.0 driver never programs it); `xhci_gen_setup`'s HC-capability read block is exactly xhci.c:5443-5463 and touches no such register.

#### 6. Suggested page topics

- Extended-capabilities walk & USB Legacy Support (BIOS/OS handoff): `xhci_find_next_ext_cap` (xhci-ext-caps.h:130), cap IDs (xhci-ext-caps.h:36-42), `XHCI_HC_BIOS_OWNED`/`OS_OWNED` (xhci-ext-caps.h:47-48); the actual handoff is a PCI-class fixup, `quirk_usb_handoff_xhci` (drivers/usb/host/pci-quirks.c:1158) registered via `quirk_usb_early_handoff` `DECLARE_PCI_FIXUP_CLASS_FINAL` (pci-quirks.c:1305) — runs before xhci-pci.c's own `.probe` at all [CORRECTED 2026-07-21 from `DECLARE_PCI_FIXUP_CLASS_EARLY`: disk at v7.0 is FINAL (section `.pci_fixup_final`), run from `pci_bus_add_device` bus.c:354 before `device_initial_probe` bus.c:374; the "runs before probe" conclusion is unchanged, only the fixup class name was wrong]. Note: pci-quirks.c is outside the assigned file set but is load-bearing for this topic.
- The quirks bitmask mechanism itself (not its vendor bits): `xhci_hcd.quirks` u64 (xhci.h:1584) and its accumulation point (`xhci->quirks |= quirks` in `xhci_gen_setup` xhci.c:5465), as a mechanism note.
- Command-ring timeout/abort machinery: `xhci_handle_command_timeout` (xhci-ring.c:1717-1793) and `xhci_abort_cmd_ring` (xhci-ring.c:490-547) — natural companion to "host reset", since a wedged command ring is a major dying/died trigger.
- Generic hcd teardown symmetry: `usb_stop_hcd`/`usb_remove_hcd`/`register_root_hub` (hcd.c) as the explicit mirror of the planned `usb_add_hcd`/roothub-registration page.
- Operational-register programming quartet: `xhci_hcd_page_size`, `xhci_enable_max_dev_slots`, `xhci_set_cmd_ring_deq`, `xhci_set_doorbell_ptr`, `xhci_set_dev_notifications` (all xhci.c:464-537) — currently only implicitly covered by "command/event ring setup".

#### 7. MMIO registers/fields touched

- CAPLENGTH/HCIVERSION (`hc_capbase`, xhci.h:66) — read via `HC_LENGTH()`/`HC_VERSION()` (xhci-caps.h:11,14) in `xhci_gen_setup` xhci.c:5444-5445,5452.
- HCSPARAMS1 (`hcs_params1`, xhci.h:67) — `HCS_MAX_SLOTS`/`HCS_MAX_PORTS`/`HCS_MAX_INTRS` (xhci-caps.h:18,23,21) consumed xhci.c:5449,5457-5463.
- HCSPARAMS2/3 (xhci.h:68-69) — cached verbatim into `xhci_hcd.hcs_params2/3` (xhci.h:1511-1512) at xhci.c:5450-5451.
- HCCPARAMS1 (`hcc_params`, xhci.h:70) — cached xhci.h:1513, read xhci.c:5453; `HCC_64BIT_ADDR`/`HCC_MAX_PSA` (xhci-caps.h:57,80) used xhci.c:5497 and xhci-pci.c:665.
- HCCPARAMS2 (xhci.h:73, xhci 1.1+ gated on `hci_version>0x100`) — cached xhci.h:1514, read xhci.c:5454-5455.
- DBOFF (`db_off`, xhci.h:71) — `DBOFF_MASK` (xhci-caps.h:87) in `xhci_set_doorbell_ptr` xhci.c:515-523.
- RTSOFF (`run_regs_off`, xhci.h:72) — `RTSOFF_MASK` (xhci-caps.h:92) in `xhci_gen_setup` xhci.c:5446-5447.
- USBCMD (`command`, xhci.h:105) — `CMD_RUN`/`CMD_RESET`/`CMD_EIE`/`CMD_HSEIE`/`CMD_EWE` (xhci.h:123-140) in `xhci_start`/`xhci_quiesce`/`xhci_reset`/`xhci_run_finished`.
- USBSTS (`status`, xhci.h:106) — `STS_HALT`/`STS_CNR`/`STS_EINT`/`STS_FATAL` (xhci.h:156-171) polled via `xhci_handshake` in `xhci_halt`/`xhci_start`/`xhci_reset`/`xhci_zero_64b_regs`.
- PAGESIZE (`page_size`, xhci.h:107) — `XHCI_PAGE_SIZE_MASK` (xhci.h:209) in `xhci_hcd_page_size` xhci.c:464-478.
- DNCTRL (`dev_notification`, xhci.h:110) — `DEV_NOTE_MASK`/`DEV_NOTE_FWAKE` (xhci.h:181,185) in `xhci_set_dev_notifications` xhci.c:529-537.
- CRCR (`cmd_ring`, xhci.h:111, 64-bit) — `CMD_RING_PTR_MASK`/`CMD_RING_CYCLE`/`CMD_RING_RUNNING`/`CMD_RING_ABORT` via `xhci_read_64`/`xhci_write_64` in `xhci_set_cmd_ring_deq` xhci.c:496-513 and `xhci_abort_cmd_ring` xhci-ring.c:490-547.
- DCBAAP (`dcbaa_ptr`, xhci.h:114, 64-bit) — written once via `xhci_write_64` in `xhci_init` xhci.c:571.
- CONFIG (`config_reg`, xhci.h:115) — `HCS_SLOTS_MASK` (xhci-caps.h:19) in `xhci_enable_max_dev_slots` xhci.c:480-494.
- Runtime MFINDEX (`microframe_index`, xhci.h:284) — read in `xhci_run` for a debug trace only.
- IMAN/IMOD/ERSTSZ/ERSTBA/ERDP (`xhci_intr_reg`, xhci.h:227-236, per interrupter) — programmed by `xhci_add_interrupter` xhci-mem.c:2320-2346.
- Doorbell array (`dba`/`doorbell[256]`, xhci.h:298-300) — located via DBOFF.
- Extended-cap ID/NEXT/VAL (xhci-ext-caps.h:32-34) — walked by `xhci_find_next_ext_cap` off HCCPARAMS1's pointer (xhci-ext-caps.h:19).
- Legacy Support Capability (BIOS/OS handoff) (xhci-ext-caps.h:47-58) — read/written only from `quirk_usb_handoff_xhci` (pci-quirks.c, outside the xhci* file set).

#### 8. Error-handling paths

- Handshake timeout (generic): `xhci_handshake` (xhci.c:85-98) → `-ETIMEDOUT`, or `-ENODEV` if register reads all-ones (card gone); checked by every halt/reset/start/abort call site.
- Halt failure: `xhci_halt` (xhci.c:127-146) warns (suppressed if `XHCI_STATE_DYING` already set) and propagates the handshake error.
- Reset failure/host gone: `xhci_reset` (xhci.c:188-245) special-cases `status==~0` (`-ENODEV`) and "not halted" (returns 0, no-op) before the CMD_RESET/STS_CNR handshakes.
- Host-death declaration: `xhci_hc_died` (drivers/usb/host/xhci-ring.c:1381-1407) — idempotent on `XHCI_STATE_DYING`, cleans command queue, kills all endpoints' pending URBs, calls `usb_hc_died` (drivers/usb/core/hcd.c:2508-2547) which sets `HCD_FLAG_DEAD` and schedules `died_work`.
- Command-ring wedge: `xhci_handle_command_timeout` (xhci-ring.c:1717-1793, the `cmd_timer` watchdog) escalates to `xhci_halt`+`xhci_hc_died` on a stuck stop-endpoint command or all-ones `cmd_ring` read, else drives `xhci_abort_cmd_ring` (xhci-ring.c:490-547), which itself calls `xhci_hc_died` if its 5 s handshake times out.
- Init allocation failure: `xhci_mem_init`'s `fail:` label (xhci-mem.c:2401-2511) unwinds via `xhci_halt`+`xhci_reset(SHORT)`+`xhci_mem_cleanup`, returning `-ENOMEM` up through `xhci_init`/`xhci_gen_setup`.
- usb_add_hcd unwind: `err_register_root_hub`/`err_hcd_driver_start`/…/`err_usb_phy_roothub_power_on` goto chain (hcd.c:2802-3016) reverses in order (`usb_stop_hcd`, `free_irq`, put rhdev, deregister bus, destroy buffers, phy power-off/exit).
- usb_hcd_pci_probe unwind: `put_hcd`/`free_irq_vectors`/`disable_pci` labels (hcd-pci.c:172-292).
- Start failure inside run: `xhci_run_finished` (xhci.c:595-629) re-halts via `xhci_halt` and returns `-ENODEV` under `xhci->lock` if `xhci_start()` fails.
- Global lifecycle guard: every long-running/externally-triggered path tests/sets `xhc_state`'s `XHCI_STATE_DYING`/`HALTED`/`REMOVING` bits (xhci.h:1581-1583) so a dying/being-removed controller short-circuits further hardware touches (e.g. duplicate-warning suppression in `xhci_halt`/`xhci_reset`).

### Area B: Root hub & ports — COMPLETE (recorded 2026-07-16)

Tree pin re-confirmed by the agent (`git describe`/`git log`). All line numbers from direct on-disk Read/grep, not the semcode index.

#### 1. Core structs

- `struct xhci_port_regs` — drivers/usb/host/xhci.h:84 — HW register quad {portsc, portpmsc, portli, porthlmpc}, one per port, spec §5.4.8.
- `struct xhci_cap_regs` / `struct xhci_op_regs` — xhci.h:65 / xhci.h:104 — capability regs (hcs_params1-3, hcc_params) and operational regs; `op_regs->port_regs[]` (xhci.h:118) is the flexible-array base every port's `port_reg` points into.
- `struct xhci_port_cap` — xhci.h:1465 — one per Supported-Protocol-Capability entry: `psi`/`psi_count`/`psi_uid_count` (Protocol Speed ID table + unique-ID count for BOS synthesis), `maj_rev`/`min_rev` (bcdUSB), `protocol_caps` (raw dword3).
- `struct xhci_port` — xhci.h:1474 — one per physical port: `port_reg` (iomem), `hw_portnum` (index into HCSPARAMS1 MaxPorts space), `hcd_portnum` (index within owning rhub = usbcore wIndex-1), `rhub` (owning fake roothub), `port_cap`, `lpm_incapable:1`, `resume_timestamp`+`rexit_active` (USB2 resume s/w state), `slot_id` (attached device's slot, 0 if none), `rexit_done`/`u3exit_done` completions.
- `struct xhci_hub` — xhci.h:1489 — one fake roothub: `ports` (array of `xhci_port*`), `num_ports`, `hcd` (owning `usb_hcd`), `bus_state`, `maj_rev`/`min_rev`.
- `struct xhci_bus_state` — xhci.h:1433 — `bus_suspended`/`resuming_ports` (unsigned long bitmaps), `port_c_suspend`/`suspended_ports`/`port_remote_wakeup` (u32 bitmaps, comment "max 31 ports USB2, 15 USB3" at xhci.h:1438), `next_statechange`.
- `struct xhci_hcd` rhub-relevant fields (struct starts xhci.h:1501): topology — `main_hcd`/`shared_hcd` (1502-3), `usb2_rhub`/`usb3_rhub` (1651-2), `hw_ports` (1650, flat array all ports), `max_ports` (1522, u8), `allow_single_roothub` (1658); protocol-cap cache — `port_caps`/`num_port_caps` (1660-1); locking — `lock` spinlock_t (1516), `mutex` struct mutex (1552, guards cmd ring/device ctx, NOT ports); misc port state — `port_status_u0` (1664), `test_mode` (1665), `comp_mode_recovery_timer` (1663), `run_graceperiod` (1567).
- `struct xhci_protocol_caps` — xhci-ext-caps.h:95 — documents the raw Supported-Protocol-Capability dword layout but is never instantiated; driver hand-decodes with `XHCI_EXT_PORT_*` macros instead (see item 7).
- `xhci_virt_device.rhub_port` — xhci.h:749 — reverse link slot→port, set in `xhci_setup_addressable_virt_dev`.

#### 2. API families

A. hub_control / status_data emulation
- `xhci_hub_control` — xhci-hub.c:1205 (EXPORT_SYMBOL_GPL:1629) — GetHubStatus/Descriptor/BOS, GetPortStatus, Set/ClearPortFeature.
- `xhci_hub_status_data` — xhci-hub.c:1639 — builds usbcore's status-change bitmap; handles `run_graceperiod` SS settle window (1673-8).
- `xhci_get_port_status`/`xhci_get_usb2_port_status`/`xhci_get_usb3_port_status`/`xhci_get_ext_port_status` — xhci-hub.c:1156/1092/1041/1025 — raw PORTSC→wPortStatus/Change, generation-split (see item 9).

B. hub-descriptor / BOS synthesis
- `xhci_hub_descriptor` — xhci-hub.c:367 — dispatch by `hcd->speed`.
- `xhci_common_hub_descriptor`/`xhci_usb2_hub_descriptor`/`xhci_usb3_hub_descriptor` — xhci-hub.c:256/279/334.
- `xhci_create_usb3x_bos_desc` — xhci-hub.c:36 — psi[] tables → SS/SSP BOS capability descriptors (USB3 only, gated xhci-hub.c:1254).

C. Port register access helpers
- `xhci_portsc_readl`/`xhci_portsc_writel` — xhci.c:51/xhci.c:44 (both EXPORT_SYMBOL_GPL) — traced PORTSC accessors.
- `xhci_port_state_to_neutral` — xhci-hub.c:445 (EXPORT_SYMBOL_GPL) — masks RO/RWS bits for safe read-modify-write.
- `xhci_test_and_clear_bit` — xhci-hub.c:842 — generic RWC (write-1-clear) helper.
- `xhci_clear_port_change_bit` — xhci-hub.c:580 — ClearPortFeature change-bit dispatch table.

D. Link-state / power / test-mode setters
- `xhci_set_link_state` — xhci-hub.c:798 — writes PLS + LWS strobe.
- `xhci_set_port_power` — xhci-hub.c:645 — PP bit + ACPI hand-off (`usb_acpi_power_manageable/set_power_state`, 670-4), `__must_hold(&xhci->lock)`.
- `xhci_set_remote_wake_mask` — xhci-hub.c:815 — WKCONN_E/WKDISC_E/WKOC_E.
- `xhci_port_set_test_mode`/`xhci_enter_test_mode`/`xhci_exit_test_mode` — xhci-hub.c:678/694/736 — USB2-only PORTPMSC.PTC.

E. Port-array / protocol-capability parsing
- `xhci_setup_port_arrays` — xhci-mem.c:2185 — allocs `hw_ports[]`, walks `XHCI_EXT_CAPS_PROTOCOL` entries, caps rhub sizes (item 4).
- `xhci_add_in_port` — xhci-mem.c:2017 — decodes one capability entry into `xhci_port_cap` + assigns `hw_ports[i].rhub`.
- `xhci_create_rhub_port_array` — xhci-mem.c:2152 — compacts `rhub->ports[]`, assigns `hcd_portnum`.
- `xhci_find_next_ext_cap` — xhci-ext-caps.h:130 (static inline) — generic ext-cap list walker, any ID.
- `xhci_find_rhub_port` — xhci-mem.c:1071 (static) — `usb_device`→`xhci_port` reverse lookup.
- `xhci_get_rhub` — xhci-hub.c:631 — `hcd`→owning `xhci_hub`. Note: get_rhub/set_link_state/test_and_clear_bit are plain non-static externs (declared xhci.h), NOT EXPORT_SYMBOL_GPL — only 2 exports exist in xhci-hub.c (port_state_to_neutral, hub_control).

F. Port reset / warm-reset
- xHCI side: `USB_PORT_FEAT_RESET`/`_BH_PORT_RESET` cases in `xhci_hub_control` — xhci-hub.c:1501-8 / 1515-9 — fire-and-forget PORT_RESET/PORT_WR write, no in-driver polling or timeout.
- usbcore side owns the state machine: `hub_port_reset` — hub.c:3050, `hub_port_wait_reset` — hub.c:2953, `hub_port_warm_reset_required` — hub.c:2937.

G. Port-status-change-event handler chain
- `xhci_irq`/`xhci_msi_irq` (xhci-ring.c:3177/3224) → `xhci_handle_events` (3086) → `xhci_handle_event_trb` (2986, case `TRB_PORT_STATUS` at 3007-8) → `handle_port_status` (1992) → `usb_hcd_poll_rh_status` (2162).
- usbcore: hub_wq → `hub_events` → `port_event` — hub.c:5746 → `hub_port_connect`/`hub_port_reset`/`hub_port_disable`.

#### 3. Lifecycle and locking

- Build: `xhci_mem_init` (xhci-mem.c:2401) → `xhci_setup_port_arrays` (2185, called 2501) allocs `hw_ports[max_ports]`, populates both rhubs; invoked from `xhci_init` (xhci.c:560).
- Teardown: `xhci_mem_cleanup` (xhci-mem.c:1898) frees `hw_ports`, both `rhub->ports`, `port_caps[].psi`+`port_caps`, zeroes `num_ports`/`num_port_caps`/`bus_suspended`; called from `xhci_stop` (xhci.c:748) and `xhci_init` error path (xhci.c:1186).
- Per-slot binding: `xhci_setup_addressable_virt_dev` (xhci-mem.c:1091) sets `dev->rhub_port` (1137) and `rhub_port->slot_id` (1142); cleared in `xhci_free_virt_device` (868, clear at ~920-1).
- Locking: single `xhci->lock` spinlock (xhci.h:1516) serializes ALL PORTSC/PORTPMSC access and all `xhci_bus_state` field updates; `xhci_set_port_power` drops+reacquires it around the ACPI call (xhci-hub.c:669-675); `xhci_get_port_status` is annotated `__releases`/`__acquires` (1160-1) since USB2 resume handling sleeps.
- State/transitions: PLS field (XDEV_U0..RESUME) is HW truth; SW mirrors resume progress in `port->resume_timestamp`+`bus_state.resuming_ports` (USB2) and `port->u3exit_done`/`rexit_done` completions (USB3/USB2 exit) plus `bus_state.port_remote_wakeup`/`suspended_ports`/`port_c_suspend`.

#### 4. Hard-coded limits

- `MAX_HC_PORTS` = 127 — xhci.h:41 — applied `xhci->max_ports = min(HCS_MAX_PORTS(hcs_params1), MAX_HC_PORTS)` xhci.c:5458 (HCS_MAX_PORTS field itself allows 255, xhci-caps.h:23).
- `USB_MAXCHILDREN` = 31 / `USB_SS_MAXPORTS` = 15 — include/uapi/linux/usb/ch11.h:22/25 — cap `usb2_rhub`/`usb3_rhub.num_ports` (xhci-mem.c:2265-9 / 2259-64).
- `XHCI_MAX_REXIT_TIMEOUT_MS` = 20 — xhci.h:1464 — USB2 RExit→U0 wait (xhci-hub.c:995).
- `USB_RESUME_TIMEOUT` = 40ms — include/linux/usb.h:337 — USB2 resume signalling (xhci-hub.c:969,1582,1951).
- `XHCI_PORT_POLLING_LFPS_TIME` = 36ms — xhci-port.h:181 — USB3 polling grace step ×10 in `xhci_bus_suspend` (xhci-hub.c:1751,1764) ≈ spec's 360ms tPollingLFPSTimeout.
- Inline 500ms `wait_for_completion_timeout` on `u3exit_done` for SetPortFeature LINK_STATE=U0 — xhci-hub.c:1461.
- Inline 10ms `xhci_handshake` poll on PORT_PLC after resume — xhci-hub.c:1965-6.
- `XHCI_L1_TIMEOUT`=512µs / `XHCI_DEFAULT_BESL`=4 — xhci-port.h:161/173 — USB2 LPM L1 defaults (xhci.c:4774-5).
- `COMP_MODE_RCVRY_MSECS` = 2000 — xhci.h:1667 — compliance-mode recovery timer period (xhci.c:406,425).
- usbcore: `PORT_RESET_TRIES`=5 (2 if `CONFIG_USB_FEW_INIT_RETRIES`) hub.c:2892/2885; `HUB_RESET_TIMEOUT`=800/`HUB_ROOT_RESET_TIME`=60/`HUB_SHORT_RESET_TIME`=10/`HUB_LONG_RESET_TIME`=200/`HUB_BH_RESET_TIME`=50 — hub.c:2901-5; `HUB_DEBOUNCE_TIMEOUT`=2000/`_STEP`=25/`_STABLE`=100 — hub.c:138-140; `DETECT_DISCONNECT_TRIES`=5 — hub.c:2899; `PORT_INIT_TRIES`=4 — hub.c:2889/2896.

#### 5. Version-specific facts

- Commit `c35ba0ac4835` "XHCI: Separate PORT and CAPs macros into dedicated file" (2024-01-24) moved every PORTSC/PORTPMSC/PORTLI/PORTHLPMC bit macro out of xhci.h into new drivers/usb/host/xhci-port.h, and HCS/HCC/DBOFF/RTSOFF macros into new drivers/usb/host/xhci-caps.h. Older write-ups citing "PORT_CONNECT etc. in xhci.h" are stale at v7.0.
- xhci-port.h gained an "eUSB2v2 protocol PORTLI" field group (`PORTLI_RDR`/`PORTLI_TDR`, xhci-port.h:151-3) and `HCC2_EUSB2_DIC`/`HCC2_E2V2C` capability bits (xhci-caps.h:117,119) — a newer optional capability absent from older docs.
- Commit `384c57ec7205` "Add debugfs support for xHCI Port Link Info (PORTLI) register" (2025-11-19, months before v7.0) added debugfs `portli` file per port (xhci-debugfs.c:386-421).
- `xhci->run_graceperiod` (xhci.h:1567, SS-only post-start polling grace, xhci-hub.c:1673-8) is a comparatively recent addition to `xhci_hub_status_data`.
- `struct xhci_protocol_caps` (xhci-ext-caps.h:95) is defined but structurally unused (see item 1) — flag so a page doesn't present it as the parsed type.

#### 6. Suggested page topics not in the current list

- Port-array & protocol-capability construction page — `xhci_setup_port_arrays`/`xhci_add_in_port`/`xhci_create_rhub_port_array`/`xhci_find_next_ext_cap` (xhci-mem.c:2185,2017,2152; xhci-ext-caps.h:130) — meaty enough (psi[] tables, duplicate-port handling) to stand alone or be explicitly folded into the "port structures/PORTSC" page.
- Root-hub bus suspend/resume page — `xhci_bus_suspend`/`xhci_bus_resume`/`xhci_get_resuming_ports`/`xhci_port_missing_cas_quirk` (xhci-hub.c:1715,1871,1987,1848) plus the compliance-mode recovery timer (xhci.c:369) — its own state machine/constants, only implicitly covered by "port events"/"hotplug".
- USB2 hardware LPM (L1) page/section — `xhci_set_usb2_hardware_lpm`/`xhci_calculate_hird_besl`/`xhci_calculate_usb2_hw_lpm_params` (xhci.c:4647,4591,4626) — touches PORTPMSC/PORTHLPMC but untouched by the current catalog.
- BOS/SuperSpeed(Plus) descriptor synthesis (`xhci_create_usb3x_bos_desc`, xhci-hub.c:36) is large/self-contained enough to warrant its own subsection under the hub-descriptor page rather than a passing mention.

#### 7. MMIO registers/fields (kernel accessor/macro + file:line)

PORTSC (all in xhci-port.h post-split):
- CCS: `PORT_CONNECT` bit0 — xhci-port.h:5
- PED: `PORT_PE` bit1 — xhci-port.h:7 (cleared via `xhci_disable_port` xhci-hub.c:550)
- OCA: `PORT_OC` bit3 — xhci-port.h:10
- PR: `PORT_RESET` bit4 — xhci-port.h:12
- PLS: `PORT_PLS_MASK` bits5:8 + `XDEV_U0..XDEV_RESUME` — xhci-port.h:17-30
- PP: `PORT_POWER` bit9 — xhci-port.h:33 (`xhci_set_port_power` xhci-hub.c:645)
- Speed: `DEV_SPEED_MASK`/`XDEV_FS|LS|HS|SS|SSP`/`DEV_PORT_SPEED()` bits10:13 — xhci-port.h:42-55 (`xhci_port_speed` xhci-hub.c:378)
- PIC: `PORT_LED_OFF/AMBER/GREEN/MASK` bits14:15 — xhci-port.h:64-67
- LWS: `PORT_LINK_STROBE` bit16 — xhci-port.h:69
- Change bits CSC/PEC/WRC/OCC/PRC/PLC/CEC bits17:23 — `PORT_CSC/PEC/WRC/OCC/RC/PLC/CEC`, `PORT_CHANGE_MASK` — xhci-port.h:71-101 (cleared via `xhci_clear_port_change_bit` xhci-hub.c:580)
- CAS: `PORT_CAS` bit24 — xhci-port.h:108 (`xhci_hub_report_usb3_link_state` xhci-hub.c:856, USB3 only)
- Wake bits WCE/WDE/WOE: `PORT_WKCONN_E/WKDISC_E/WKOC_E` bits25:27 — xhci-port.h:110-4 (`xhci_set_remote_wake_mask` xhci-hub.c:815)
- DR: `PORT_DEV_REMOVE` bit30 — xhci-port.h:117
- WPR: `PORT_WR` bit31 — xhci-port.h:119 (BH_PORT_RESET, xhci-hub.c:1516)

PORTPMSC (layout is generation-dependent — see item 9): USB3 `PORT_U1_TIMEOUT()`/`PORT_U2_TIMEOUT()` — xhci-port.h:128-132 (xhci-hub.c:1520-35); USB2 `PORT_L1S_MASK/PORT_RWE/PORT_HIRD()/PORT_L1DS()/PORT_HLE/PORT_TEST_MODE_SHIFT` — xhci-port.h:136-144 (xhci.c:4647 LPM path, xhci-hub.c:678 test mode).

PORTLI: USB3 `PORT_LEC()/PORT_RX_LANES()/PORT_TX_LANES()` — xhci-port.h:147-9 (`xhci_get_ext_port_status` xhci-hub.c:1025, debugfs xhci-debugfs.c:404-5); USB2/eUSB2v2 `PORTLI_RDR()/PORTLI_TDR()` — xhci-port.h:152-3 (RsvdP for plain USB2).

PORTHLPMC (USB2-only): `PORT_HIRDM()/PORT_L1_TIMEOUT()/PORT_BESLD()` — xhci-port.h:156-8 (`xhci_set_usb2_hardware_lpm` xhci.c:4707-9, no USB3 use anywhere).

Supported-Protocol extended capability (ID 2, xhci-ext-caps.h): `XHCI_EXT_CAPS_PROTOCOL`=2 (xhci-ext-caps.h:37); `XHCI_EXT_PORT_MAJOR()/MINOR()/PSIC()` dword1 — 101-3 (xhci-mem.c:2028-9,2076); `XHCI_EXT_PORT_OFF()/COUNT()` dword3 — 104-5 (xhci-mem.c:2062-3); `XHCI_EXT_PORT_PSIV()/PSIE()/PLT()/PFD()/LP()/PSIM()` PSI dwords — 107-112 (xhci-mem.c:2087-2107, BOS synthesis xhci-hub.c:149-221); walker `xhci_find_next_ext_cap()` — xhci-ext-caps.h:130. Note: xhci-ext-caps.c itself is out of hard scope — it only builds a vendor platform-device for a vendor extended-cap ID, no port logic.

#### 8. Error-handling paths

- Over-current: HW sets `PORT_OC`/`PORT_OCC` (xhci-port.h:10,81); reported read-only via `xhci_get_port_status` (xhci-hub.c:1175,1187); `xhci_bus_suspend` bails `-EBUSY` on `PORT_OC` (xhci-hub.c:1770-6); recovery (cooldown+re-power+uevent) is entirely usbcore's `port_event()` (hub.c:5787-5801) via `port_over_current_notify` (hub.c:5712).
- Port reset timeout: xHCI never times out (fire-and-forget write, item 2F); usbcore's `hub_port_reset`/`hub_port_wait_reset` (hub.c:3050/2953) own the `PORT_RESET_TRIES`/`HUB_RESET_TIMEOUT` budget.
- Cold Attach Status (CAS): forces synthetic Compliance-Mode report to usbcore (`xhci_hub_report_usb3_link_state` xhci-hub.c:864-880); stuck-CAS workaround `xhci_port_missing_cas_quirk` (xhci-hub.c:1848) issues a warm reset, called from `xhci_bus_resume` (1917-24) when `XHCI_MISSING_CAS` bit set (xhci.h:1619).
- Link training failure (SS.Inactive/Compliance): usbcore `hub_port_warm_reset_required` (hub.c:2937) + `port_event()` warm-reset retry loop (hub.c:5841-65, `DETECT_DISCONNECT_TRIES`=5); xHCI-side generic Compliance-Mode recovery timer (`XHCI_COMP_MODE_QUIRK` xhci.h:1608, `compliance_mode_recovery()` xhci.c:369, period 2000ms) re-polls so usbcore can warm-reset.
- Host death / disconnect-storm proxies: `xhci_hc_died` (xhci-ring.c:1381) fires on PORTSC reading all-1s inside `xhci_hub_control`/`xhci_hub_status_data` (xhci-hub.c:1268,1314,1561,1686); per-device `VDEV_PORT_ERROR` (xhci.h:759, set/cleared in `handle_port_status` xhci-ring.c:2049-54) short-circuits `xhci_urb_enqueue` (xhci.c:1670) and `xhci_handle_halted_endpoint` (xhci-ring.c:996) until link recovers; usbcore's `port_dev->early_stop`/`ignore_event` (hub.c:3209-30, sysfs-controlled) is the closest thing to disconnect-storm suppression — admin-opt-in, not automatic.

#### 9. USB2 vs USB3 port register divergence (evidence-based, for the two catalog pages)

1. Same register set, different semantics: both share one `struct xhci_port_regs` layout (xhci.h:84) and common PORTSC bits (CONNECT/PE/OC/RESET/POWER/common change bits) — divergence is in specific bits' meaning plus the PORTPMSC/PORTLI/PORTHLPMC contents, not the register map.
2. PLS state machine differs: USB2 uses only U0/U2(=L1)/U3/Resume/RxDetect/Polling and drives a timestamp-based SW resume state machine (`xhci_handle_usb2_port_link_resume` xhci-hub.c:937); USB3 additionally has U1/Recovery/Compliance/SS.Inactive, and the raw PLS nibble is placed directly into wPortStatus bits5:8 (`xhci_hub_report_usb3_link_state` xhci-hub.c:856-907), resume completion signalled by `u3exit_done` only.
3. `PORT_WRC`/`PORT_CEC`/`PORT_CAS` are "RsvdZ for USB 2.0 ports" per the header comment (xhci-port.h:74-9,98-9) — architecturally USB3-only; `USB_PORT_FEAT_BH_PORT_RESET`/`_C_BH_PORT_RESET`/`_C_PORT_CONFIG_ERROR` are exercised only on the USB3 rhub.
4. PORTPMSC layout is generation-exclusive: USB3 = U1/U2 LPM inactivity timeouts, gated `if (hcd->speed < HCD_USB3) goto error;` (xhci-hub.c:1521,1529); USB2 = L1 LPM fields (L1S/RWE/HIRD/L1DS/HLE) + Test Mode field, manipulated only by `xhci_set_usb2_hardware_lpm` (xhci.c:4647) and `xhci_port_set_test_mode` (xhci-hub.c:678), both of which reject USB3 ports.
5. PORTHLPMC exists only for USB2 — no USB3 code path ever touches it (xhci.c:4707-9).
6. PORTLI differs: USB3 always carries Link-Error-Count + Rx/Tx lane counts; the same offset for plain USB2 is RsvdP unless eUSB2v2-capable, in which case it carries RDR/TDR (xhci-port.h:146-153).
7. Descriptor synthesis is generation-specific end to end: `xhci_usb2_hub_descriptor` (byte-packed DeviceRemovable, bDescLength via ports/8) vs `xhci_usb3_hub_descriptor` (fixed `USB_DT_SS_HUB_SIZE`, u16 DeviceRemovable, header decode latency) — xhci-hub.c:279 vs 334; only USB3 gets a BOS descriptor at all (`xhci_create_usb3x_bos_desc`, gated xhci-hub.c:1254).
8. Root cause (state once, cite from both pages): xHCI models USB2 and USB3 as two independent fake roothubs (`usb2_rhub`/`usb3_rhub`) because the xHCI spec itself defines distinct port state machines, link-management registers, and descriptor formats per generation (spec §5.4.8-5.4.11) — the driver's split mirrors the spec's split, it is not an implementation choice.

### Area C: Device slots & contexts — COMPLETE (recorded 2026-07-16)

All line numbers verified on disk at the pinned commit.

#### 1. Core structs

- `xhci_virt_device` — drivers/usb/host/xhci.h:734 — SW mirror of one HW device slot (slot_id, out_ctx/in_ctx, eps[31], rhub_port, bw_table, tt_info, flags incl. `VDEV_PORT_ERROR` BIT(0), sideband ptr). NOT a virtual-machine construct.
- `xhci_virt_ep` — drivers/usb/host/xhci.h:652 — SW mirror of one endpoint (vdev back-ptr, ep_index, ring, stream_info, new_ring, err_count, ep_state bitmask, bw_info, sideband).
- `xhci_container_ctx` — drivers/usb/host/xhci.h:320 — generic raw DMA blob backing either a Device Context or Input Context (`type`, `size`, `bytes`, `dma`); also reused type-less for port-bandwidth ctx.
- `xhci_slot_ctx` — drivers/usb/host/xhci.h:342 — HW slot context: dev_info (route string, speed, hub, last-ctx), dev_info2 (max exit latency, root-hub port), tt_info (TT slot/port + interrupter target), dev_state (address, slot state).
- `xhci_ep_ctx` — drivers/usb/host/xhci.h:426 — HW endpoint context: ep_info (state/mult/interval), ep_info2 (type/max packet/burst/CErr), deq (64-bit TR dequeue ptr+DCS), tx_info (avg TRB len, max ESIT payload).
- `xhci_input_control_ctx` — drivers/usb/host/xhci.h:513 — Input Context header: drop_flags/add_flags bitmaps (bit0=slot, bit(n+1)=ep n) for Address/Configure/Evaluate commands.
- `xhci_device_context_array` (DCBAA) — drivers/usb/host/xhci.h:796 — `dev_context_ptrs[MAX_HC_SLOTS]` array of 64-bit DMA ptrs to per-slot output device contexts, + `dma` of the array itself.
- `xhci_scratchpad` — drivers/usb/host/xhci.h:1400 — `sp_array` (DMA ptr array), `sp_dma`, `sp_buffers` (kernel VAs); scratchpad pages required when HCSPARAMS2 Max Scratchpad Buffers > 0.
- `xhci_bw_info` — drivers/usb/host/xhci.h:597 — per-endpoint bandwidth bookkeeping (interval, mult, num_packets, max_packet_size, max_esit_payload, type); lives in `xhci_virt_ep.bw_info`.
- `xhci_interval_bw` / `xhci_interval_bw_table` — drivers/usb/host/xhci.h:711 / 723 — per-interval endpoint list + bw_used/ss_bw_in/out; table embedded in `xhci_virt_device.bw_table`.
- `xhci_tt_bw_info` — drivers/usb/host/xhci.h:783 — per-hub-TT bandwidth domain (slot_id, ttport, embedded bw_table); linked from `xhci_virt_device.tt_info`.
- `xhci_root_port_bw_info` — drivers/usb/host/xhci.h:777 — per-roothub-port bandwidth domain + list of child TTs; array `xhci->rh_bw`.
- `xhci_doorbell_array` — drivers/usb/host/xhci.h:298 — MMIO `__le32 doorbell[256]`, one per slot ID (index 0 = HC/command doorbell).
- `xhci_op_regs` — drivers/usb/host/xhci.h:104 — operational registers incl. `page_size` (:107), `dcbaa_ptr` (:114), `config_reg` (:115).
- `xhci_hcd` (relevant fields only) — drivers/usb/host/xhci.h:1501 — `dcbaa` (:1534), `devs[MAX_HC_SLOTS]` (:1554, "Internal mirror of the HW's dcbaa"), `scratchpad` (:1548), `dba` (:1508), `lock` spinlock (:1516), `mutex` for slot-enable/address-device (:1552), cached `hcc_params`/`hcc_params2`/`max_slots`/`max_interrupters` (:1513-1521).

#### 2. API families (file:line — role)

Alloc/free:
- `xhci_alloc_container_ctx` drivers/usb/host/xhci-mem.c:452 — allocates device/input ctx blob; size = 1024/2048 (32B/64B ctx) +CTX_SIZE more if input.
- `xhci_free_container_ctx` drivers/usb/host/xhci-mem.c:478 — DMA-pool free.
- `xhci_alloc_port_bw_ctx`/`xhci_free_port_bw_ctx` drivers/usb/host/xhci-mem.c:487/507 — third, type-less user of `xhci_container_ctx` for Get Port Bandwidth command.
- `xhci_alloc_virt_device` drivers/usb/host/xhci-mem.c:968 — allocates `xhci_virt_device`, out/in ctx, ep0 ring, wires `xhci->devs[slot_id]` and `dcbaa->dev_context_ptrs[slot_id]`; uses `kzalloc_obj(*dev, flags)` (:980).
- `xhci_free_virt_device` drivers/usb/host/xhci-mem.c:868 — frees rings/streams/tt_info/contexts for one slot; clears dcbaa entry, `xhci->devs[slot_id]`, `udev->slot_id`.
- `xhci_free_virt_devices_depth_first` drivers/usb/host/xhci-mem.c:933 — recursively frees hub-children before the hub itself (TT hierarchy safe order).

Context accessors / sizing:
- `xhci_get_input_control_ctx` drivers/usb/host/xhci-mem.c:516 — casts ctx->bytes iff type==INPUT.
- `xhci_get_slot_ctx` drivers/usb/host/xhci-mem.c:525 — offset 0 for device ctx, +CTX_SIZE(hcc_params) for input ctx (skips input-control ctx).
- `xhci_get_ep_ctx` drivers/usb/host/xhci-mem.c:535 (EXPORT_SYMBOL_GPL :547) — `(ep_index+1[+1 if input])*CTX_SIZE(hcc_params)`.
- `CTX_SIZE(_hcc)` / `HCC_64BYTE_CONTEXT` drivers/usb/host/xhci-caps.h:62/61 — 32 vs 64-byte context stride, driven by HCCPARAMS1 bit 2 (CSZ).

Endpoint-index math:
- `xhci_get_endpoint_index` drivers/usb/host/xhci.c:1457 (EXPORT :1467) — `epnum*2 + dir_in - 1` (ctrl uses epnum*2).
- `xhci_get_endpoint_address` drivers/usb/host/xhci.c:1472 — reverse of above.
- `xhci_get_endpoint_flag` drivers/usb/host/xhci.c:1483 — `1 << (ep_index+1)` bitmask for input-control add/drop flags.
- `xhci_last_valid_endpoint` drivers/usb/host/xhci.c:1494 — `fls(added_ctxs)-1`.

Encode/decode macros (drivers/usb/host/xhci.h): `ROUTE_STRING_MASK` :353, `LAST_CTX`/`LAST_CTX_MASK`/`LAST_CTX_TO_EP_NUM` :363-365, `ROOT_HUB_PORT`/`DEVINFO_TO_ROOT_HUB_PORT` :373-374, `GET_SLOT_STATE`/`SLOT_STATE_*` :399-406, `EP_STATE_MASK`/`GET_EP_CTX_STATE` :445/451, `EP_TYPE`/`CTX_TO_EP_TYPE` :477-478, `MAX_PACKET`/`MAX_BURST` :488-490, `TRB_TO_SLOT_ID`/`SLOT_ID_FOR_TRB` :817-818, `GET_INTR_TARGET` :1038 (reused to decode slot ctx's `tt_info` interrupter-target field, xhci.h:2351).

Setup helpers:
- `xhci_setup_addressable_virt_dev` drivers/usb/host/xhci-mem.c:1091 — fills slot ctx (route, speed, root-hub port, TT info) + ep0 ctx for Set Address.
- `xhci_endpoint_init` drivers/usb/host/xhci-mem.c:1407 — allocates ep ring, fills ep_ctx from `usb_host_endpoint` desc.
- `xhci_endpoint_zero` drivers/usb/host/xhci-mem.c:1513 — zeroes input ep_ctx (ring freed later).
- `xhci_slot_copy` / `xhci_endpoint_copy` drivers/usb/host/xhci-mem.c:1626 / 1600 — copy output ctx fields into input ctx before Evaluate-Context-style commands.
- `xhci_copy_ep0_dequeue_into_input_ctx` drivers/usb/host/xhci-mem.c:1039 — re-syncs ep0 deq ptr after device reset.
- `xhci_zero_in_ctx` drivers/usb/host/xhci.c:2086 — clears input-control flags + all ep contexts, resets slot LAST_CTX to 1.

DCBAA/scratchpad/PAGESIZE setup:
- `xhci_mem_init` drivers/usb/host/xhci-mem.c:2401 — allocates DCBAA (64-byte aligned, per xHCI 5.4.6), ring/device/stream/port-bw dma pools, cmd ring, primary interrupter, calls scratchpad_alloc + xhci_setup_port_arrays.
- `scratchpad_alloc`/`scratchpad_free` drivers/usb/host/xhci-mem.c:1643/1706 — sizes via `HCS_MAX_SCRATCHPAD(hcs_params2)`; buffer 0 pointer written to `dcbaa->dev_context_ptrs[0]` (slot 0 doesn't hold a device!).
- `xhci_hcd_page_size` drivers/usb/host/xhci.c:464 — reads op_regs->page_size & `XHCI_PAGE_SIZE_MASK`, feeds scratchpad buffer size.
- `xhci_enable_max_dev_slots` drivers/usb/host/xhci.c:480 — writes MaxSlotsEn into CONFIG using `HCS_SLOTS_MASK`.
- `xhci_mem_cleanup` drivers/usb/host/xhci-mem.c:1898 — frees all slots depth-first (:1929-1930), pools, DCBAA (:1955-1958), scratchpad (:1960).

Doorbell helpers:
- `xhci_ring_cmd_db` drivers/usb/host/xhci-ring.c:422 — writes `DB_VALUE_HOST` to `dba->doorbell[0]`.
- `xhci_ring_ep_doorbell` drivers/usb/host/xhci-ring.c:549 — writes `DB_VALUE(ep_index,stream_id)` to `dba->doorbell[slot_id]`, skipped if ep_state has pending-cancel/halt/set-deq/clearing-TT bits.
- `ring_doorbell_for_active_rings` / `xhci_ring_doorbell_for_active_rings` drivers/usb/host/xhci-ring.c:576/601 — ring per-stream doorbells for non-empty TD lists.

Slot-ID acquisition (Enable Slot):
- `xhci_alloc_dev` drivers/usb/host/xhci.c:4211 — queues TRB_ENABLE_SLOT, waits, reads `command->slot_id`, then calls `xhci_alloc_virt_device`.
- `xhci_queue_slot_control` drivers/usb/host/xhci-ring.c:4395 — builds Enable/Disable Slot command TRB.
- `xhci_handle_cmd_enable_slot` drivers/usb/host/xhci-ring.c:1590 — stashes HW-returned slot_id into `command->slot_id` on success, else 0.

#### 3. Lifecycle and locking

- Enable: `xhci_alloc_dev` (xhci.c:4211) queues TRB_ENABLE_SLOT under `xhci->lock` (spin_lock_irqsave :4224), rings doorbell, waits outside lock; on success calls `xhci_alloc_virt_device` (xhci-mem.c:968) which sets `xhci->devs[slot_id]` — no lock held there (device pool alloc under GFP_NOIO).
- Address: `xhci_setup_device`/`xhci_address_device` (xhci.c:4304/4487) serialized by `xhci->mutex` (xhci.h:1552 "not thread safe so use mutex"); queues TRB_ADDR_DEV under `xhci->lock`; completion updates SW slot_ctx via `xhci_handle_cmd_addr_dev` (xhci-ring.c:1654).
- Configure: `xhci_check_bandwidth`/`xhci_configure_endpoint` (xhci.c:3080/2960) install `eps[i].new_ring` into `eps[i].ring` under `xhci->lock` only after command success; completion traced via `xhci_handle_cmd_config_ep` (xhci-ring.c:1621).
- Disable: `xhci_free_dev` (xhci.c:4091) clears EP_STOP_CMD_PENDING on all 31 eps, calls `xhci_disable_slot` (xhci.c:4130, queues TRB_DISABLE_SLOT under `xhci->lock`), then `xhci_free_virt_device` (xhci-mem.c:868) under `xhci->lock` (spin_lock_irqsave, xhci.c:4124-4126) — this is what actually frees `xhci->devs[slot_id]`/kfree(dev). `xhci_handle_cmd_disable_slot` (xhci-ring.c:1599) clears `dcbaa->dev_context_ptrs[slot_id]` and `xhci->devs[slot_id]=NULL` only `if (cmd_comp_code == COMP_SUCCESS)`.
- Module/host teardown: `xhci_mem_cleanup` (xhci-mem.c:1898) walks `for (i = xhci->max_slots; i>0; i--) xhci_free_virt_devices_depth_first()` (:1929) — frees every slot unconditionally, no per-slot HC command sent.
- ep_state transitions (`xhci_virt_ep.ep_state`, xhci.h:658-666): `SET_DEQ_PENDING` (Set TR Dequeue outstanding) → cleared by `xhci_handle_cmd_set_deq`; `EP_HALTED`/stall handling; `EP_STOP_CMD_PENDING` set on URB cancel, cleared in cmd completion or forcibly in `xhci_free_dev` (xhci.c:4119-4120); `EP_GETTING_STREAMS`→`EP_HAS_STREAMS` and `EP_GETTING_NO_STREAMS`→(clear `EP_HAS_STREAMS`) during stream (re)configuration; `EP_HARD_CLEAR_TOGGLE`/`EP_SOFT_CLEAR_TOGGLE`; `EP_CLEARING_TT` during `usb_hub_clear_tt_buffer`. Distinct from the HW `ep_info` field's `EP_STATE_*` (disabled/running/halted/stopped/error, xhci.h:445-451) — two different "endpoint state" spaces.

#### 4. Hard-coded limits

- `MAX_HC_SLOTS` = 256 — drivers/usb/host/xhci.h:36 — size of `dcbaa->dev_context_ptrs[]` and `xhci->devs[]`; slot IDs run 0..255, 0 reserved (holds scratchpad ptr, not a device).
- `EP_CTX_PER_DEV` = 31 — drivers/usb/host/xhci.h:732 — endpoint contexts per device (15 IN + 15 OUT + control), size of `eps[]` array.
- Device-pool ctx blob = 2112 bytes / 64-byte alignment — drivers/usb/host/xhci-mem.c:2437 (comment: "See Table 46… Figure 55"); per-container size = 1024 or 2048 (device) via xhci-mem.c:466, +CTX_SIZE more (1024+32/2048+64) for input ctx :467-468.
- Scratchpad bound: `HCS_MAX_SCRATCHPAD(p)` — drivers/usb/host/xhci-caps.h:42-46 — 10-bit field (Hi 5 + Lo 5 bits), max 1023 buffers; consulted xhci-mem.c:1647.
- `SMALL_STREAM_ARRAY_SIZE`=256, `MEDIUM_STREAM_ARRAY_SIZE`=1024, `GET_PORT_BW_ARRAY_SIZE`=256 — drivers/usb/host/xhci.h:587-589.
- `XHCI_MAX_INTERVAL` = 16 — drivers/usb/host/xhci.h:721 — size of `interval_bw[]` in bandwidth table.
- Adjacent (not slot/ctx-specific but capped nearby): `MAX_HC_PORTS`=127 (xhci.h:41), `MAX_HC_INTRS`=128 (xhci.h:46).

#### 5. Version-specific facts

- New in v7.0: `xhci_alloc_virt_device` uses `kzalloc_obj(*dev, flags)` (xhci-mem.c:980) instead of `kzalloc(sizeof(*dev),...)` — `kzalloc_obj()` itself is brand-new (commit 2932ba8d9c99 "slab: Introduce kmalloc_obj() and family", merged for v7.0) applied treewide by 69050f8d6d07. Any pre-v7.0 doc/example showing `kzalloc(sizeof(*dev), flags)` here is now stale.
- Since v6.9: capability-register macros (`HCS_MAX_SLOTS`, `CTX_SIZE`, `HCC_64BYTE_CONTEXT`, `DBOFF_MASK`, `RTSOFF_MASK`, HCCPARAMS2 bits, etc.) live in new file drivers/usb/host/xhci-caps.h, split out of xhci.h by commit c35ba0ac4835 ("XHCI: Separate PORT and CAPs macros into dedicated file"). Older docs pointing at "xhci.h" for these macros need updating.
- Since v6.16: `xhci_virt_device.sideband` / `xhci_virt_ep.sideband` fields added (commit de66754e9f80, "xhci: sideband: add initial api…") for secondary-interrupter sideband access — absent from all pre-2025 documentation.
- Since v5.2: `xhci_virt_device.flags` + `VDEV_PORT_ERROR` bit added (commit b8c3b718087b) — a pure-software "port error/link inactive" flag with no HW context counterpart; not present in older write-ups of the struct.
- Since v4.10: slot teardown is depth-first/recursive (`xhci_free_virt_devices_depth_first`, commit ee8665e28e8d) to avoid freeing a hub's TT info while children still reference it; older descriptions of "just loop over devs[] and free" are inaccurate for hub topologies.
- Stable since the original 2010 driver: `MAX_HC_SLOTS`=256, `EP_CTX_PER_DEV`=31, and the `xhci_slot_ctx`/`xhci_ep_ctx`/`xhci_input_control_ctx` layouts are structurally unchanged since the first upstream xHCI driver (commits like a74588f94655 "Device context array allocation", 3ffbba9511b4 "Allocate and address USB devices") — safe to describe as long-term-stable facts.

#### 6. Suggested additional page topics

- Scratchpad page — `xhci_scratchpad` (xhci.h:1400), `HCS_MAX_SCRATCHPAD` capability, `scratchpad_alloc`/`free` (xhci-mem.c:1643/1706); the "slot 0 holds the scratchpad array pointer, not a device" gotcha.
- Container-context / ctx-size page — `xhci_container_ctx` (xhci.h:320) as the one struct backing device ctx, input ctx, AND port-bandwidth ctx (`xhci_alloc_port_bw_ctx`, xhci-mem.c:487); CSZ bit and 32-vs-64-byte consequences for every `xhci_get_*_ctx` accessor.
- Endpoint-state (ep_state) page — the 9 SW `ep_state` bits in `xhci_virt_ep` (xhci.h:658-666) vs. the HW `EP_STATE_*` codes in `ep_info` (xhci.h:445-451) — two "endpoint state" concepts that collide by name.
- Bandwidth-domain page — `xhci_bw_info`/`xhci_interval_bw`/`xhci_interval_bw_table`/`xhci_tt_bw_info`/`xhci_root_port_bw_info`, all hanging off `xhci_virt_device`/`xhci_virt_ep` (generic SW bandwidth accounting, not a vendor quirk).
- Command/doorbell/completion pipeline page — `xhci_alloc_command` (xhci-mem.c:1730), `cmd_ring`, `handle_cmd_completion`'s dispatch table (xhci-ring.c:1795-1918) — the shared plumbing every slot/endpoint command page will otherwise re-explain.
- "virt ≠ virtualization" disambiguation note — worth a callout given real xHCI virtualization exists in the same files under a different name: `HCC2_VTC` (xhci-caps.h:114), `TRB_FORCE_EVENT`/`TRB_TO_VF_INTR_TARGET`/VF ID (xhci.h:985, 2234-2241) — unrelated SR-IOV-style feature, easily confused with `xhci_virt_device`.
- Slot state-machine page — `SLOT_STATE_DISABLED/DEFAULT/ADDRESSED/CONFIGURED` (xhci.h:402-406) transitions spanning Enable Slot → Address Device → Configure Endpoint → Reset Device → Disable Slot; currently split across the planned pages with no single home.

#### 7. MMIO/DMA-visible registers & structures

- DCBAAP — `xhci_op_regs.dcbaa_ptr` (xhci.h:114); programmed via `xhci_write_64(xhci, xhci->dcbaa->dma, &xhci->op_regs->dcbaa_ptr)` in `xhci_init` (xhci.c:571), restored on resume (xhci.c:836).
- CONFIG (MaxSlotsEn) — `xhci_op_regs.config_reg` (xhci.h:115); written by `xhci_enable_max_dev_slots` (xhci.c:480-493) using mask `HCS_SLOTS_MASK` (xhci-caps.h:19).
- PAGESIZE — `xhci_op_regs.page_size` (xhci.h:107); read by `xhci_hcd_page_size` (xhci.c:464) with `XHCI_PAGE_SIZE_MASK` (xhci.h:209); result feeds `xhci->page_size` used for scratchpad-buffer size (xhci-mem.c:1674).
- Doorbell Array — `xhci_doorbell_array.doorbell[256]` (xhci.h:298, MMIO via `xhci->dba`, xhci.h:1508); target/stream encoding `DB_VALUE(ep,stream)` = `((ep+1)&0xff) | (stream<<16)` (xhci.h:302), host/command doorbell = `DB_VALUE_HOST` 0 (xhci.h:303); index 0 = command-ring doorbell, index N = slot N.
- CSZ (Context Size) capability bit — `HCC_64BYTE_CONTEXT` = BIT(2) of HCCPARAMS1 (drivers/usb/host/xhci-caps.h:61), cached in `xhci->hcc_params` (xhci.h:1513, read at xhci.c:5453); `CTX_SIZE(hcc)` macro (xhci-caps.h:62) is the single choke point all ctx accessors use.
- HCSPARAMS1 Number-of-Device-Slots — `HCS_MAX_SLOTS(p)` (xhci-caps.h:18), cached `xhci->max_slots` (xhci.h:1521, assigned xhci.c:5457), reused to program CONFIG (see above).
- HCSPARAMS2 Max Scratchpad Buffers — `HCS_MAX_SCRATCHPAD(p)` (xhci-caps.h:42-46), consulted in `scratchpad_alloc` (xhci-mem.c:1647).

#### 8. Error-handling paths

- Slot exhaustion: `xhci_alloc_dev` (xhci.c:4211) checks `!slot_id || command->status != COMP_SUCCESS` (:4238), logs via `xhci_trb_comp_code_string()` (xhci.h:869, covers `COMP_NO_SLOTS_AVAILABLE_ERROR`=9 at xhci.h:841/890) and `xhci->max_slots`; returns 0, nothing to free (no slot was bound).
- Context/virt-device allocation failure: `xhci_alloc_virt_device` fail-path (xhci-mem.c:1028-1036) frees whatever of in_ctx/out_ctx succeeded, then kfree(dev); caller `xhci_alloc_dev`'s `disable_slot:` label (xhci.c:4288) invokes `xhci_disable_and_free_slot` (xhci.c:4174).
- Failed Address Device command: `xhci_setup_device` (xhci.c:4304), switch on `command->status` (:4408-4448); `COMP_USB_TRANSACTION_ERROR` (:4420-4431) explicitly calls `xhci_disable_and_free_slot()` then `xhci_alloc_dev()` to get a fresh slot and retries `xhci_setup_addressable_virt_dev()`; other error codes just propagate `ret`, slot stays allocated.
- Failed Configure Endpoint/Evaluate Context: `xhci_configure_endpoint` (xhci.c:2960) → result mapped by `xhci_configure_endpoint_result`/`xhci_evaluate_context_result` (xhci.c:2120/2170); `xhci_check_bandwidth` (xhci.c:3080) leaves `eps[i].new_ring` allocated on failure ("Callee should call reset_bandwidth()", xhci.c:3141) — actual cleanup in `xhci_reset_bandwidth` (xhci.c:3179), which frees leftover `new_ring`s and calls `xhci_zero_in_ctx` (xhci.c:2086).
- Disable-slot on error: `xhci_disable_and_free_slot` (xhci.c:4174) issues TRB_DISABLE_SLOT then unconditionally calls `xhci_free_virt_device()` regardless of the HW completion result.
- Completion-dispatch guards: `handle_cmd_completion` (xhci-ring.c:1795) rejects `slot_id >= MAX_HC_SLOTS` (:1807) before dereferencing `xhci->devs[]`; `xhci_handle_cmd_disable_slot` (xhci-ring.c:1599) only clears `dcbaa`/`devs[]` entries `if (cmd_comp_code == COMP_SUCCESS)` — a failed/aborted Disable Slot deliberately leaves the SW mirror in place.

### Area D: Rings, TRBs, command ring, event ring & interrupts — COMPLETE (recorded 2026-07-16)

#### 1. Core structs

- `xhci_ring` — drivers/usb/host/xhci.h:1362 — enqueue/dequeue ptrs+segs, `cycle_state`, `td_list`, `type` (enum), `trb_address_map`; shared by transfer, command AND event rings.
- `xhci_segment` — xhci.h:1281 — one TRBS_PER_SEGMENT-TRB page (`trbs`, `dma`) + `next` + bounce-buffer fields; singly software-linked via `next` regardless of ring type.
- `union xhci_trb` — xhci.h:1087 — overlay of `link`/`trans_event`/`event_cmd`/`generic` 16-byte views.
- `xhci_generic_trb` — xhci.h:1083 — raw `__le32 field[4]`, the producer-side write view used by `queue_trb`.
- `xhci_link_trb` — xhci.h:949 — `segment_ptr`+`intr_target`+`control` (holds TRB_LINK type + TC via `LINK_TOGGLE` bit1, xhci.h:957); the segment-chaining TRB.
- `xhci_event_cmd` — xhci.h:960 — `cmd_trb`+`status`+`flags`; Command Completion Event layout.
- `xhci_transfer_event` — xhci.h:808 — `buffer`+`transfer_len`+`flags`; Transfer Event layout.
- `xhci_command` — xhci.h:528 — `in_ctx`,`status`,`comp_param`,`slot_id`,`completion`,`command_trb`,`cmd_list`,`timeout_ms`; SW handle for one queued command.
- `xhci_interrupter` — xhci.h:1446 — `event_ring`+`erst`+`ir_set`+`intr_num`+`ip_autoclear`+`isoc_bei_interval`+s3 save fields; one full per-interrupter state object (v7.0 restructuring, see item 5).
- `xhci_erst` — xhci.h:1393 — `entries[]`+`num_entries`+`erst_dma_addr`; host descriptor of one interrupter's ERST.
- `xhci_erst_entry` — xhci.h:1385 — `seg_addr`+`seg_size`(+rsvd); one HW ERST row, 1:1 with an `xhci_segment`.
- `xhci_intr_reg` — xhci.h:227 — `iman`/`imod`/`erst_size`/`erst_base`/`erst_dequeue`; MMIO mirror of one interrupter register set (spec §5.5.2).
- `enum xhci_ring_type` — xhci.h:1330 — `TYPE_CTRL,ISOC,BULK,INTR,STREAM,COMMAND,EVENT`.
- `xhci_doorbell_array` — xhci.h:298 — `doorbell[256]` __iomem, DBOFF-relative.
- `xhci_op_regs`/`xhci_run_regs` — xhci.h:104 / xhci.h:283 — `cmd_ring`(CRCR)/`dcbaa_ptr`; `microframe_index`(MFINDEX)+`ir_set[1024]`.
- `xhci_hcd` (relevant fields) — xhci.h:1501 — `cmd_ring`,`cmd_ring_state`,`cmd_list`,`cmd_timer`,`cmd_ring_stop_completion`,`current_cmd`; `struct xhci_interrupter **interrupters` (xhci.h:1535) + `max_interrupters` (xhci.h:1520); single `spinlock_t lock` (xhci.h:1516).
- Event ring differs by design: `xhci_initialize_ring_segments` skips Link-TRB setup when `type==TYPE_EVENT` (early return xhci-mem.c:121) [CORRECTED 2026-07-21: `xhci_link_segments` does not exist at v7.0; :102 is a bare `return;`] — HW navigates segments via the ERST, not in-band links; SW is consumer-only (cycle bit read, not written — comment at inc_deq, xhci-ring.c:186); dequeue is published via ERDP, not a doorbell.

#### 2. API families (S=static)

- Ring alloc/free/expand: `xhci_ring_alloc` xhci-mem.c:370; `xhci_segment_alloc`(S) xhci-mem.c:29; `xhci_alloc_segments_for_ring`(S) xhci-mem.c:330; `xhci_ring_free` xhci-mem.c:289; `xhci_ring_expansion` xhci-mem.c:414; `xhci_ring_expansion_needed`(S) xhci-ring.c:379; `xhci_set_link_trb`(S) xhci-mem.c:96 (writes Link TRB; the name `xhci_link_segments` is DEAD at v7.0 — CORRECTED 2026-07-21); `xhci_link_rings`(S) xhci-mem.c:136 (splices expansion ring in); `xhci_initialize_ring_segments`(S) xhci-mem.c:116; `xhci_initialize_ring_info` xhci-mem.c:305 (reset enq=deq, cycle_state=1).
- Enqueue/dequeue advance: `inc_deq` xhci-ring.c:186; `inc_enq`(S) xhci-ring.c:283; `inc_enq_past_link`(S) xhci-ring.c:232; `prepare_ring`(S) xhci-ring.c:3263; `xhci_num_trbs_free`(S) xhci-ring.c:343; `queue_trb`(S) xhci-ring.c:3239.
- DMA↔virtual: `xhci_trb_virt_to_dma` xhci-ring.c:71; `xhci_dma_to_trb`(S) xhci-ring.c:85; `xhci_dma_to_transfer_ring` xhci-mem.c:591 (decl xhci.h:1842, walks stream radix tree); `trb_in_td`(S)/`dma_in_range`(S) xhci-ring.c:331/307; `xhci_insert_segment_mapping`(S)/`xhci_remove_segment_mapping`(S)/`xhci_update_stream_segment_mapping`(S)/`xhci_remove_stream_mapping`(S) xhci-mem.c:206/228/238/271 (radix tree `trb_address_map`, streams only).
- Link/chain helpers: `trb_is_link`(S) xhci-ring.c:107; `last_trb_on_seg`/`last_trb_on_ring`(S) xhci-ring.c:112/117; `link_trb_toggles_cycle`(S) xhci-ring.c:123; `next_trb`(S) xhci-ring.c:172; `trb_to_noop`(S, 2 variants) xhci-ring.c:148; `xhci_set_link_trb`(S) xhci-mem.c:96; `xhci_link_chain_quirk`(inline) xhci.h:1779.
- Command family: `xhci_alloc_command`/`_with_ctx` xhci-mem.c:1730/1758; `xhci_free_command` xhci-mem.c:1782; `queue_command`(S) xhci-ring.c:4352 (generic enqueue); `xhci_queue_slot_control` xhci-ring.c:4395, `xhci_queue_address_device` :4403, `xhci_queue_vendor_command` :4412, `xhci_queue_reset_device` :4419, `xhci_queue_configure_endpoint` :4428, `xhci_queue_get_port_bw` :4439, `xhci_queue_evaluate_context` :4450, `xhci_queue_stop_endpoint` :4463, `xhci_queue_reset_ep` :4475 (all thin wrappers → queue_command); `handle_cmd_completion`(S) xhci-ring.c:1795; `xhci_complete_del_and_free_cmd`(S) xhci-ring.c:1696; `xhci_mod_cmd_timer`(S) xhci-ring.c:436; `xhci_handle_command_timeout` xhci-ring.c:1717; `xhci_abort_cmd_ring`(S) xhci-ring.c:490; `xhci_handle_stopped_cmd_ring`(S) xhci-ring.c:453; `xhci_cleanup_command_queue` xhci-ring.c:1709; `xhci_next_queued_cmd`(S) xhci-ring.c:442.
- Event-loop/IRQ entry: `xhci_irq` xhci-ring.c:3177; `xhci_msi_irq` xhci-ring.c:3224; `xhci_handle_events`(S) xhci-ring.c:3086; `xhci_handle_event_trb`(S) xhci-ring.c:2986; `unhandled_event_trb`(S) xhci-ring.c:135; `xhci_skip_sec_intr_events` xhci-ring.c:3147 (secondary-interrupter drain-and-rewind).
- ERDP update: `xhci_update_erst_dequeue` xhci-ring.c:3038; `xhci_set_hc_event_deq`(S) xhci-mem.c:2000 (initial program).
- Interrupter alloc/setup (primary+secondary): `xhci_alloc_interrupter`(S) xhci-mem.c:2285; `xhci_add_interrupter` xhci-mem.c:2320; `xhci_remove_interrupter`(S) xhci-mem.c:1822; `xhci_free_interrupter`(S) xhci-mem.c:1844; `xhci_alloc_erst`(S) xhci-mem.c:1791; `xhci_create_secondary_interrupter` (EXPORT_SYMBOL_GPL) xhci-mem.c:2349; `xhci_remove_secondary_interrupter` (EXPORT_SYMBOL_GPL) xhci-mem.c:1868.
- Interrupt moderation: `xhci_set_interrupter_moderation` xhci.c:350; `xhci_enable_interrupter`/`xhci_disable_interrupter` xhci.c:313/330; `xhci_clear_interrupt_pending`(S) xhci-ring.c:3068.
- MSI/MSI-X acquisition (true location = drivers/usb/host/xhci-pci.c, see item 5): `xhci_try_enable_msi`(S) xhci-pci.c:143; `xhci_pci_run`(S) xhci-pci.c:211; `xhci_msix_sync_irqs`(S) xhci-pci.c:116; `xhci_cleanup_msix`(S) xhci-pci.c:129.
- Doorbell: `xhci_ring_cmd_db` xhci-ring.c:422; `xhci_ring_ep_doorbell` xhci-ring.c:549; `ring_doorbell_for_active_rings`(S)/`xhci_ring_doorbell_for_active_rings` xhci-ring.c:576/601.

#### 3. Lifecycle and locking

- `cmd_ring_state` values `CMD_RING_STATE_RUNNING/ABORTED/STOPPED` (1<<0/1/2) — xhci.h:1538-1540; `cmd_list` (xhci.h:1541) is the in-flight `xhci_command` list; `cmd_timer` delayed_work + `cmd_ring_stop_completion` (xhci.h:1543-1544) drive timeout→abort→stop.
- One global `spinlock_t xhci->lock` (xhci.h:1516) serializes enqueue (`xhci_urb_enqueue` xhci.c:1622, held across the whole queue_*_tx call) against event handling (`xhci_irq` xhci-ring.c:3183 `spin_lock`); handlers may drop+reacquire it mid-event (comment, xhci-ring.c:3086). Separate `xhci->mutex` (xhci.h:1552) serializes non-atomic multi-command sequences (slot enable/address device), not enqueue/event.
- Event-loop budget: `xhci_handle_events` loops until `unhandled_event_trb()` is false; every `TRBS_PER_SEGMENT/2` (128) events it force-flushes ERDP and halves `isoc_bei_interval` (xhci-ring.c:3120-3125) — no hard per-ISR event cap otherwise.

#### 4. Hard-coded limits

- `TRBS_PER_SEGMENT`=256 xhci.h:1259; `MAX_RSVD_CMD_TRBS`=253 xhci.h:1261; `TRB_SEGMENT_SIZE`=4096B xhci.h:1262.
- `MAX_HC_SLOTS`=256 xhci.h:36; `MAX_HC_INTRS`=128 xhci.h:46 (caps `HCS_MAX_INTRS(HCSPARAMS1)`, applied xhci.c:5461); `ir_set[1024]` MMIO array bound xhci.h:286.
- `ERST_DEFAULT_SEGS`=2 xhci.h:1413; per-interrupter max ERST segs = `BIT(HCS_ERST_MAX(hcs_params2))` xhci-mem.c:2295 (`HCS_ERST_MAX` xhci-caps.h:39).
- `XHCI_CMD_DEFAULT_TIMEOUT`=5000ms xhci.h:1322; abort handshake wait for CRR=0: 5,000,000us xhci-ring.c:523; abort stop-event wait: 2000ms xhci-ring.c:538; `XHCI_MAX_HALT_USEC`=32000us xhci-ext-caps.h:12.
- Ring expansion has no fixed cap (grows by `xhci_ring_expansion_needed()`'s computed segs, xhci-ring.c:379); command ring explicitly REFUSES expansion (`prepare_ring`, xhci-ring.c:3300 "Do not support expand command ring").
- MSI-X vectors: `nvecs = min(num_online_cpus()+1, max_interrupters)` xhci-pci.c:166; default `imod_interval`=40000ns(40us) xhci-pci.c:576 (HW spec default is 1ms/IMODI=4000, xhci.h:246).

#### 5. Version-specific facts

- Interrupter restructuring: old single `xhci->event_ring`/`erst`/`ir_set` triple is gone; replaced by `struct xhci_interrupter **interrupters` (xhci.h:1535), an array of up to `max_interrupters` pointers, each a self-contained `xhci_interrupter` (event_ring+erst+ir_set, xhci.h:1446). `xhci_irq` now explicitly uses `xhci->interrupters[0]` for primary (xhci-ring.c:3220).
- New secondary-interrupter public API: `xhci_create_secondary_interrupter`/`xhci_remove_secondary_interrupter` (EXPORT_SYMBOL_GPL, xhci-mem.c:2349/1868), consumed by the new drivers/usb/host/xhci-sideband.c (~495 lines) + include/linux/usb/xhci-sideband.h, giving external clients (e.g. audio DSP offload) a dedicated interrupter/event-ring/xfer-ring bypassing the xHCI driver's own IRQ (`ip_autoclear`, xhci.h:1451, lets the external device autoclear IMAN.IP itself so `xhci_clear_interrupt_pending` xhci-ring.c:3068 skips that interrupter).
- True MSI/MSI-X location: fully in drivers/usb/host/xhci-pci.c (`xhci_try_enable_msi`/`xhci_pci_run`/`xhci_msix_sync_irqs`/`xhci_cleanup_msix`, lines 116-231), not xhci.c or xhci.h. `xhci_run()` (xhci.c:641) only calls `xhci_enable_interrupter()`/`xhci_set_interrupter_moderation()` on the already-allocated vector. drivers/usb/core/hcd-pci.c explicitly carves out xHCI: `if ((driver->flags & HCD_MASK) < HCD_USB3)` (hcd-pci.c:187) skips its own generic `pci_alloc_irq_vectors` for USB3 controllers, deferring entirely to xhci-pci.c. include/linux/usb/hcd.h only supplies the generic `msi_enabled`/`msix_enabled:1` bitfields (hcd.h:145-146) that xhci-pci.c sets.
- Per-interrupter functions now take an explicit `struct xhci_interrupter *ir` (`xhci_update_erst_dequeue`, `xhci_set_hc_event_deq`, `xhci_handle_events`) rather than implicitly operating on one primary ring.

#### 6. Suggested additional pages

- TRB completion-code taxonomy: 36 `COMP_*` codes [CORRECTED 2026-07-21 from 35; values 0-29 and 31-36, gap at 30; 38 macros at 37 distinct values incl. a driver-internal 2000 sentinel; cross-checked against 36 case labels in `xhci_trb_comp_code_string`] (xhci.h:832-867) drive `handle_tx_event`/`handle_cmd_completion` branching — distinct from the TRB-type page.
- Command-abort & command-ring-stopped recovery: `xhci_abort_cmd_ring`/`xhci_handle_stopped_cmd_ring`/`xhci_handle_command_timeout` + `CMD_RING_STATE_*` (xhci-ring.c:490,453,1717) is a nontrivial protocol.
- Halted endpoint / Set-TR-Dequeue-Pointer recovery: `xhci_handle_halted_endpoint`/`xhci_reset_halted_ep`/`xhci_handle_cmd_set_deq`/`xhci_move_dequeue_past_td` (xhci-ring.c:984,960,1416,689).
- xHCI sideband / secondary-interrupter offload: xhci-sideband.c is a whole subsystem built on secondary interrupters (`struct xhci_sideband`, include/linux/usb/xhci-sideband.h:52) worth its own page.
- Host-controller-dead (HCE/STS_FATAL) recovery: `xhci_hc_died`/`xhci_halt`/`xhci_quiesce`/`xhci_reset` (xhci-ring.c:1381; xhci.c:127,103,188).
- PCI probe / IRQ-ownership handoff: hcd-pci.c's `HCD_MASK<HCD_USB3` carve-out vs xhci-pci.c's own vector management (hcd-pci.c:187-201) — easy to get backwards, worth a dedicated short page or section.

#### 7. xHCI MMIO registers touched

- CRCR (`op_regs->cmd_ring`, xhci.h:111): RCS=`CMD_RING_CYCLE`(bit0), CS=`CMD_RING_PAUSE`(bit1), CA=`CMD_RING_ABORT`(bit2), CRR=`CMD_RING_RUNNING`(bit3), ptr=`CMD_RING_PTR_MASK`(63:6) — xhci.h:189-197; accessed via `xhci_read_64`/`xhci_write_64` (xhci.h:1757) in `xhci_set_cmd_ring_deq` xhci.c:496 and `xhci_abort_cmd_ring` xhci-ring.c:490.
- Interrupter set (`xhci_intr_reg`, xhci.h:227): IMAN IP/IE (xhci.h:238-240) via `xhci_enable_interrupter`/`xhci_disable_interrupter` xhci.c:313/330 + `xhci_clear_interrupt_pending` xhci-ring.c:3068; IMOD (xhci.h:248-250) via `xhci_set_interrupter_moderation` xhci.c:350; ERSTSZ (xhci.h:254) and ERSTBA (xhci.h:258) via `xhci_add_interrupter`/`xhci_remove_interrupter` xhci-mem.c:2320/1822; ERDP incl. DESI(bits2:0)/EHB(bit3) (xhci.h:265-272) via `xhci_update_erst_dequeue`/`xhci_set_hc_event_deq` xhci-ring.c:3038 / xhci-mem.c:2000.
- Doorbell array (`dba->doorbell[256]`, xhci.h:298, `DB_VALUE`/`DB_VALUE_HOST` xhci.h:302-303) via `xhci_ring_cmd_db`/`xhci_ring_ep_doorbell` xhci-ring.c:422/549.
- USBSTS (`op_regs->status`): `STS_EINT`(bit3)/`STS_HCE`(bit12)/`STS_FATAL`(bit2) xhci.h:158-173, read/cleared in `xhci_irq` xhci-ring.c:3177-3222.
- MFINDEX (`run_regs->microframe_index`, xhci.h:284) read via `readl` in `xhci_get_frame` xhci.c:5354 and isoc frame-ID calc xhci-ring.c:4014,4314.
- TRB Interrupter-Target field (`TRB_INTR_TARGET`, xhci.h:1037) — per-TRB field selecting which interrupter/MSI-X vector gets the event; standard queue_* helpers hardcode `TRB_INTR_TARGET(0)`, sideband clients use `xhci_sideband_interrupter_id()`'s value.

#### 8. Error-handling paths

- Command timeout→abort→restart: `xhci_handle_command_timeout` xhci-ring.c:1717 → `xhci_abort_cmd_ring` xhci-ring.c:490 (writes CA, handshakes CRR→0) → `COMP_COMMAND_RING_STOPPED` completes `cmd_ring_stop_completion` in `handle_cmd_completion` xhci-ring.c:1795 → `xhci_handle_stopped_cmd_ring` xhci-ring.c:453 (no-ops aborted cmds, re-rings doorbell).
- HCE/host-system-error: `xhci_irq`'s `STS_HCE`/`STS_FATAL` branches xhci-ring.c:3196-3206 → `xhci_halt` xhci.c:127 → `xhci_hc_died` xhci-ring.c:1381 (flushes cmd_list, kills all endpoint URBs, `usb_hc_died()`); register-gone (`0xffffffff`) detected in `xhci_irq`, `xhci_handshake` xhci.c:85, and `xhci_handle_command_timeout`'s `hw_ring_state==~(u64)0` check, all funnel to `xhci_hc_died`.
- Event-ring-full: no dedicated recovery — `COMP_EVENT_RING_FULL_ERROR`/`COMP_VF_EVENT_RING_FULL_ERROR` (xhci.h:853/848) just decoded; avoided proactively by ERDP flush + BEI-interval halving in `xhci_handle_events` xhci-ring.c:3120-3125.
- Stopped/halted transfer-ring recovery: `xhci_handle_halted_endpoint`/`xhci_reset_halted_ep` xhci-ring.c:984/960 (issues TRB_RESET_EP), `xhci_handle_cmd_stop_ep`/`find_halted_td` xhci-ring.c:1183/1158, `xhci_handle_cmd_set_deq`→`xhci_move_dequeue_past_td` xhci-ring.c:1416/689.
- Generic TRB/transfer errors: `handle_tx_event`'s switch on `trb_comp_code` xhci-ring.c:2633 (STALL/USB_TRANSACTION/BABBLE/TRB_ERROR/... → -EPIPE/-EPROTO/-EOVERFLOW/-EILSEQ etc., given back to URB).

#### THE COMPLETE TRB TYPE CENSUS

(All `TRB_*` type-ID constants, xhci.h; used via `TRB_TYPE()`/`TRB_FIELD_TO_TYPE()` macros at xhci.h:1096-1097, mask `TRB_TYPE_BITMASK`=0xfc00 at xhci.h:1095.)

- TRB_NORMAL = 1 — xhci.h:1100 (transfer TRB: bulk/intr/isoc S-G, control data stage)
- TRB_SETUP = 2 — xhci.h:1102 (transfer TRB: control setup stage)
- TRB_DATA = 3 — xhci.h:1104 (transfer TRB: control data stage)
- TRB_STATUS = 4 — xhci.h:1106 (transfer TRB: control status stage)
- TRB_ISOC = 5 — xhci.h:1108 (transfer TRB: isochronous)
- TRB_LINK = 6 — xhci.h:1110 (ring-segment link TRB)
- TRB_EVENT_DATA = 7 — xhci.h:1111 (transfer TRB: event-data)
- TRB_TR_NOOP = 8 — xhci.h:1113 (transfer-ring no-op)
- TRB_ENABLE_SLOT = 9 — xhci.h:1116 (command TRB)
- TRB_DISABLE_SLOT = 10 — xhci.h:1118 (command TRB)
- TRB_ADDR_DEV = 11 — xhci.h:1120 (command TRB)
- TRB_CONFIG_EP = 12 — xhci.h:1122 (command TRB)
- TRB_EVAL_CONTEXT = 13 — xhci.h:1124 (command TRB)
- TRB_RESET_EP = 14 — xhci.h:1126 (command TRB)
- TRB_STOP_RING = 15 — xhci.h:1128 (command TRB, "Stop Transfer Ring")
- TRB_SET_DEQ = 16 — xhci.h:1130 (command TRB, "Set TR Dequeue Pointer")
- TRB_RESET_DEV = 17 — xhci.h:1132 (command TRB)
- TRB_FORCE_EVENT = 18 — xhci.h:1134 (command TRB, optional)
- TRB_NEG_BANDWIDTH = 19 — xhci.h:1136 (command TRB, optional)
- TRB_SET_LT = 20 — xhci.h:1138 (command TRB, optional)
- TRB_GET_BW = 21 — xhci.h:1140 (command TRB)
- TRB_FORCE_HEADER = 22 — xhci.h:1142 (command TRB)
- TRB_CMD_NOOP = 23 — xhci.h:1144 (command-ring no-op)
- [24-31 reserved — xhci.h:1145]
- TRB_TRANSFER = 32 — xhci.h:1148 (event TRB: Transfer Event)
- TRB_COMPLETION = 33 — xhci.h:1150 (event TRB: Command Completion Event)
- TRB_PORT_STATUS = 34 — xhci.h:1152 (event TRB: Port Status Change)
- TRB_BANDWIDTH_EVENT = 35 — xhci.h:1154 (event TRB, optional)
- TRB_DOORBELL = 36 — xhci.h:1156 (event TRB, optional)
- TRB_HC_EVENT = 37 — xhci.h:1158 (event TRB: Host Controller Event)
- TRB_DEV_NOTE = 38 — xhci.h:1160 (event TRB: Device Notification)
- TRB_MFINDEX_WRAP = 39 — xhci.h:1162 (event TRB: MFINDEX Wrap)
- [40-47 reserved, 48-63 vendor-defined — xhci.h:1163]
- TRB_VENDOR_DEFINED_LOW = 48 — xhci.h:1164 (start marker of vendor-defined range)
- TRB_NEC_CMD_COMP = 48 — xhci.h:1166 (vendor-specific event, shares 48; out of general PCI/x86 scope, listed only for census completeness)
- TRB_NEC_GET_FW = 49 — xhci.h:1168 (vendor-specific command; same caveat)

### Area E: Transfers & USB-core integration — COMPLETE (recorded 2026-07-16)

#### 1. Core structs

- `xhci_td` — one Transfer Descriptor: td_list/cancelled_td_list, status, `cancel_status` (enum), urb*, start/end seg+trb, bounce_seg, urb_length_set, error_mid_td. drivers/usb/host/xhci.h:1302-1316.
- `urb_priv` — xHCI's per-URB private data (NOT the same-named UHCI struct in uhci-hcd.h:480 — that file is out of scope): num_tds, num_tds_done, flexible `td[]` array (`__counted_by(num_tds)`); `urb->hcpriv` points here. drivers/usb/host/xhci.h:1406-1410.
- `xhci_stream_info` — per-endpoint stream state: stream_rings[], num_streams, stream_ctx_array (DMA'able), num_stream_ctxs, trb_address_map (radix tree TRB-DMA→segment), free_streams_command. drivers/usb/host/xhci.h:572-583.
- `xhci_stream_ctx` — HW stream context: __le64 stream_ring (ptr+DCS+SCT), reserved[2]. drivers/usb/host/xhci.h:549-554.
- `xhci_ring` — first/last_seg, enqueue/enq_seg, dequeue/deq_seg, td_list, cycle_state, stream_id, num_segs, type (`enum xhci_ring_type`: TYPE_CTRL/ISOC/BULK/INTR/STREAM/COMMAND/EVENT, xhci.h:1330-1337). drivers/usb/host/xhci.h:1362-1380.
- `xhci_segment` — trbs[] (one 4KB page, TRBS_PER_SEGMENT=256 × 16B), next, dma, bounce_dma/buf/offs/len (TD-fragment alignment). drivers/usb/host/xhci.h:1281-1291.
- `xhci_virt_ep` — vdev, ep_index, `ring` (default, non-stream) vs `stream_info->stream_rings[]` (stream mode) — `ep->ring` is used when `!(ep_state & EP_HAS_STREAMS)`, else lookup goes through stream_info; new_ring (pending bandwidth change); ep_state flags (SET_DEQ_PENDING, EP_HALTED, EP_STOP_CMD_PENDING, EP_GETTING_STREAMS, EP_HAS_STREAMS, EP_GETTING_NO_STREAMS, EP_HARD_CLEAR_TOGGLE, EP_SOFT_CLEAR_TOGGLE, EP_CLEARING_TT); cancelled_td_list; queued_deq_seg/ptr; skip (isoc). drivers/usb/host/xhci.h:652-701.
- `xhci_virt_device` — slot_id, udev, out_ctx/in_ctx (`xhci_container_ctx`), eps[EP_CTX_PER_DEV=31] (xhci.h:732), rhub_port, bw_table, flags (VDEV_PORT_ERROR). drivers/usb/host/xhci.h:734-756.
- `xhci_container_ctx` — type (XHCI_CTX_TYPE_DEVICE=1/INPUT=2), size, bytes*, dma; input ctx = `xhci_input_control_ctx` (drop_flags/add_flags, xhci.h:513-521) + slot_ctx + up to 31 ep_ctx. drivers/usb/host/xhci.h:320-337.
- `xhci_slot_ctx` / `xhci_ep_ctx` — raw HW contexts (dev_info/dev_info2/tt_info/dev_state; ep_info/ep_info2/deq/tx_info). drivers/usb/host/xhci.h:342-354, 426-441.
- `union xhci_trb` (link/trans_event/event_cmd/generic over `xhci_generic_trb{field[4]}`). drivers/usb/host/xhci.h:1083-1092.
- `xhci_transfer_event` — buffer (DMA ptr of TRB event points to), transfer_len (residual+comp code via GET_COMP_CODE), flags (slot/ep id). drivers/usb/host/xhci.h:808-814.
- `xhci_command` — in_ctx, status, comp_param, slot_id, completion*, command_trb, cmd_list, timeout_ms — the unit of command-ring submission (enable slot/addr dev/config ep/stop ep/set-deq/reset ep all build one). drivers/usb/host/xhci.h:528-541.
- `xhci_hcd` — main_hcd/shared_hcd, lock (spinlock_t, the big xHCI lock), mutex (serializes enable-slot/address-device sequences), cmd_ring, devs[MAX_HC_SLOTS=256] (SW mirror of DCBAA), dcbaa, interrupters[]. drivers/usb/host/xhci.h:1501 onward.
- USB-core seam: `urb` (include/linux/usb.h:1629; hcpriv, ep*, pipe, stream_id, transfer_flags, sg/sgt, iso_frame_desc[]); `usb_host_endpoint` (include/linux/usb.h:68; desc, urb_list, hcpriv, streams count) — `ep->hcpriv` is unused by xHCI (endpoint state lives in `xhci_virt_ep`, reached via slot/ep index, not hcpriv); `usb_hcd` (include/linux/usb/hcd.h:68; self, status_urb, high/low_prio_bh giveback work, bandwidth_mutex/address0_mutex); `hc_driver` (include/linux/usb/hcd.h:237; urb_enqueue/urb_dequeue/alloc_dev/address_device/... ops table).

#### 2. API families (file:line — role — seam caller)

Enqueue/dequeue core:
- `xhci_urb_enqueue` drivers/usb/host/xhci.c:1622 — hc_driver.urb_enqueue; allocates urb_priv (num_tds by type), dispatches by `usb_endpoint_type()`. Called from `usb_hcd_submit_urb` drivers/usb/core/hcd.c:1515 (`hcd->driver->urb_enqueue`), itself called from `usb_submit_urb` drivers/usb/core/urb.c:367.
- `xhci_urb_dequeue` drivers/usb/host/xhci.c:1756 — hc_driver.urb_dequeue; cancel via Stop Endpoint or immediate cleanup. Called from `usb_hcd_unlink_urb` drivers/usb/core/hcd.c:1597.

Per-type queue functions + TRB/fragment math:
- `xhci_queue_ctrl_tx` xhci-ring.c:3770 — Setup+Data+Status TRBs (num_trbs=2 or 3), calls `prepare_transfer`.
- `xhci_queue_bulk_tx` xhci-ring.c:3611 — Normal TRBs, sg-aware, 64KB-boundary split, URB_ZERO_PACKET extra TD, bounce-buffer align via `xhci_align_td` (xhci-ring.c:3541).
- `xhci_queue_intr_tx` xhci-ring.c:3483 — thin wrapper: `check_interval` (xhci-ring.c:3448) then calls `xhci_queue_bulk_tx` (same Normal-TRB machinery as bulk).
- `xhci_queue_isoc_tx_prepare` xhci-ring.c:4270 → `xhci_queue_isoc_tx` xhci-ring.c:4077 — one TD per `iso_frame_desc[i]`, Isoc TRB + chained Normal TRBs, burst/TBC via `xhci_get_burst_count`/`xhci_get_last_burst_packet_count`, extended-TBC path (`xep->use_extended_tbc`, xHCI 1.1 ETE).
- `count_trbs` xhci-ring.c:3374 — `DIV_ROUND_UP(len+(addr&(TRB_MAX_BUFF_SIZE-1)), TRB_MAX_BUFF_SIZE)`; `count_trbs_needed` xhci-ring.c:3386, `count_sg_trbs_needed` xhci-ring.c:3391, `count_isoc_trbs_needed` xhci-ring.c:3410 (per-packet).
- `xhci_td_remainder` xhci-ring.c:3514 — TD-size field (packets remaining) for TRB_TD_SIZE. `xhci_urb_suitable_for_idt` xhci.h:2015 — immediate-data eligibility (≤`TRB_IDT_MAX_SIZE`).
- `prepare_ring` xhci-ring.c:3263 (ep-state check + ring-expansion) and `prepare_transfer` xhci-ring.c:3325 (ring lookup incl. streams via `xhci_triad_to_transfer_ring` xhci-ring.c:652, td init, first-TD `usb_hcd_link_urb_to_ep` call) are the shared setup both use before building TRBs.
- `queue_trb` xhci-ring.c:3239 / `queue_command` xhci-ring.c:4352 — generic single-TRB enqueue onto transfer/command ring; `inc_enq` xhci-ring.c:283 advances producer past Link TRBs.
- `giveback_first_trb` xhci-ring.c:3432 — flips the first TRB's cycle bit (transfers ownership to HW) and calls `xhci_ring_ep_doorbell`.

Doorbell:
- `xhci_ring_ep_doorbell` xhci-ring.c:549 (exported) — writes `DB_VALUE(ep_index,stream_id)` (xhci.h:302, `((ep+1)&0xff)|(stream<<16)`) to `xhci->dba->doorbell[slot_id]`; skipped if EP_STOP_CMD_PENDING/SET_DEQ_PENDING/EP_HALTED/EP_CLEARING_TT.
- `ring_doorbell_for_active_rings` xhci-ring.c:578 (static) / `xhci_ring_doorbell_for_active_rings` xhci-ring.c:601 (exported) — re-rings all active stream rings after a command completes.
- `xhci_ring_cmd_db` — rings command-ring doorbell (slot 0); used after every `queue_command`.

Transfer-event handler chain:
- `xhci_handle_event_trb` xhci-ring.c:2986 — top-level event dispatch by TRB type: TRB_COMPLETION→`handle_cmd_completion`, TRB_PORT_STATUS→`handle_port_status`, TRB_TRANSFER→`handle_tx_event`, TRB_DEV_NOTE→`handle_device_notification`.
- `handle_tx_event` xhci-ring.c:2633 — decodes comp code, finds TD via `trb_in_td` (xhci-ring.c:331), dispatches per endpoint type: `process_ctrl_td` xhci-ring.c:2293, `process_isoc_td` xhci-ring.c:2388, `process_bulk_intr_td` xhci-ring.c:2518; all funnel into `finish_td` xhci-ring.c:2234 → `xhci_dequeue_td` xhci-ring.c:926 → `xhci_td_cleanup` xhci-ring.c:879.
- Completion codes: `#define COMP_*` xhci.h:832-867 (COMP_SUCCESS=1 … COMP_SPLIT_TRANSACTION_ERROR=36); decoded by `xhci_trb_comp_code_string` xhci.h:869.

Giveback:
- `xhci_giveback_urb_in_irq` xhci-ring.c:825 — frees urb_priv, `usb_hcd_unlink_urb_from_ep`, `usb_hcd_giveback_urb`. Seam: `usb_hcd_giveback_urb` drivers/usb/core/hcd.c:1731 (queues to `high_prio_bh`/`low_prio_bh` workqueue since xHCI sets HCD_BH, xhci.c:5574, so completion runs off the hardirq/lock).

Cancel / stop-endpoint / set-TR-dequeue family:
- `xhci_urb_dequeue` xhci.c:1756 → `xhci_queue_stop_endpoint` xhci-ring.c:4463 (TRB_STOP_RING) → completion `xhci_handle_cmd_stop_ep` xhci-ring.c:1183 → `xhci_invalidate_cancelled_tds` xhci-ring.c:1034 → (if needed) `xhci_move_dequeue_past_td` xhci-ring.c:689 (TRB_SET_DEQ) → completion `xhci_handle_cmd_set_deq` xhci-ring.c:1416 → `xhci_giveback_invalidated_tds` xhci-ring.c:937.
- `enum xhci_cancelled_td_status` xhci.h:1294: TD_DIRTY, TD_HALTED, TD_CLEARING_CACHE, TD_CLEARING_CACHE_DEFERRED, TD_CLEARED.

Stall / reset-endpoint family:
- `xhci_handle_halted_endpoint` xhci-ring.c:984 — adds TD to cancelled list, calls `xhci_reset_halted_ep` xhci-ring.c:960 → `xhci_queue_reset_ep` xhci-ring.c:4475 (TRB_RESET_EP, EP_HARD_RESET/EP_SOFT_RESET via `enum xhci_ep_reset_type` xhci.h:979) → completion `xhci_handle_cmd_reset_ep` xhci-ring.c:1556. `xhci_clear_hub_tt_buffer` xhci-ring.c:2166 clears LS/FS TT buffer (`usb_hub_clear_tt_buffer`, USB-core hub.c) as part of halt recovery. Seam: `xhci_endpoint_reset` xhci.c:3307 = hc_driver.endpoint_reset, called after USB core's CLEAR_FEATURE(ENDPOINT_HALT) control message.

Stream alloc/free:
- `xhci_alloc_streams` xhci.c:3609 = hc_driver.alloc_streams (called from USB-core `usb_alloc_streams`) — `xhci_calculate_streams_and_bitmask` xhci.c:3520, `xhci_calculate_streams_entries` xhci.c:3494 (rounds up to power of 2, clamps to `HCC_MAX_PSA`), `xhci_alloc_stream_info` xhci-mem.c:610, issues Configure Endpoint via `xhci_configure_endpoint` xhci.c:2960.
- `xhci_free_streams` xhci.c:3776 = hc_driver.free_streams — reverse path, also through `xhci_configure_endpoint`.

Enumeration-command family (xHCI side):
- Enable Slot: `xhci_alloc_dev` xhci.c:4211 = hc_driver.alloc_dev → `xhci_queue_slot_control` xhci-ring.c:4395 (TRB_ENABLE_SLOT) → completion `xhci_handle_cmd_enable_slot` xhci-ring.c:1590 → `xhci_alloc_virt_device` xhci-mem.c:968 (allocs out_ctx/in_ctx, ep0 ring, DCBAA entry).
- Address Device: `xhci_address_device` xhci.c:4487 = hc_driver.address_device → `xhci_setup_device` xhci.c:4304 → `xhci_setup_addressable_virt_dev` xhci-mem.c:1091 (fills input-ctx slot+ep0 ctx) → `xhci_queue_address_device` xhci-ring.c:4403 (TRB_ADDR_DEV) → completion `xhci_handle_cmd_addr_dev` xhci-ring.c:1654.
- Configure Endpoint: `xhci_check_bandwidth` xhci.c:3080 = hc_driver.check_bandwidth (built from `xhci_add_endpoint` xhci.c:1985 / `xhci_drop_endpoint` xhci.c:1902 = hc_driver.add/drop_endpoint) → `xhci_configure_endpoint` xhci.c:2960 → `xhci_queue_configure_endpoint` xhci-ring.c:4428 (TRB_CONFIG_EP) → completion path via `handle_cmd_completion`'s TRB_CONFIG_EP case (xhci-ring.c:1868) → `xhci_handle_cmd_config_ep`.

#### 3. Lifecycle and locking

- URB life: `usb_submit_urb`(urb.c:367) → `usb_hcd_submit_urb`(hcd.c:1515) → `xhci_urb_enqueue`(xhci.c:1622, takes `xhci->lock`) → per-type queue fn builds TD(s) on `ep_ring`/stream ring → `xhci_ring_ep_doorbell` → xHC executes → Transfer Event → `xhci_irq`(xhci-ring.c:3177, holds `xhci->lock` for the whole ISR incl. event processing) → `xhci_handle_events`→`handle_tx_event`→per-type processor→`finish_td`→`xhci_dequeue_td`→`xhci_td_cleanup`(checks `last_td_in_urb` xhci-ring.c:128/`inc_td_cnt` xhci-ring.c:141)→`xhci_giveback_urb_in_irq`→`usb_hcd_giveback_urb` (deferred to BH workqueue, runs WITHOUT xhci->lock).
- Cancellation: `ep_state` bits (xhci.h:658-670) gate re-entrancy (SET_DEQ_PENDING/EP_STOP_CMD_PENDING/EP_HALTED block doorbell ringing, xhci-ring.c:564); `cancelled_td_list` per `xhci_virt_ep` holds in-flight cancels; `td->cancel_status` state machine (TD_DIRTY→TD_CLEARING_CACHE→TD_CLEARED, or →TD_HALTED) drives whether a Set-TR-Dequeue is needed before giveback.
- Locks: `xhci->lock` serializes ring/event-ring/command-ring access — held across `xhci_urb_enqueue`/`xhci_urb_dequeue`/`xhci_irq`/`xhci_configure_endpoint`. `xhci->mutex` serializes `xhci_setup_device` (xhci.c:4304, `mutex_lock(&xhci->mutex)`) i.e. enable-slot/address-device sequencing. Seam-side: `hcd->bandwidth_mutex` held across `usb_set_configuration`'s bandwidth calls (message.c:2054, around `usb_hcd_alloc_bandwidth`); `hcd->address0_mutex` held by `hub_port_connect` (hub.c:5390) across device-alloc+reset+init for one port.

#### 4. Hard-coded limits

- `TRB_MAX_BUFF_SIZE` = 1<<16 = 65536B, `TRB_MAX_BUFF_SHIFT`=16; TRB buffer must not cross a 64KB boundary (`TRB_BUFF_LEN_UP_TO_BOUNDARY`). xhci.h:1265-1269.
- `TRBS_PER_SEGMENT` = 256, `TRB_SEGMENT_SIZE` = 256×16 = 4096B (one page), `MAX_RSVD_CMD_TRBS` = 256-3 = 253. xhci.h:1259-1263.
- TD fragment rule: `count_trbs()` = `DIV_ROUND_UP(len+(addr&(SIZE-1)), SIZE)` (xhci-ring.c:3374); bulk/isoc TRBs additionally split for max-packet alignment via `xhci_align_td` (bounce buffer) when a TRB would end unaligned mid-segment (xhci-ring.c:3541).
- Isoch/interrupt interval: HW field `EP_INTERVAL` is 8 bits, decoded as `1 << interval` microframes (`EP_INTERVAL_TO_UFRAMES`, xhci.h:459-460); USB-core clamps requested `urb->interval` before submit — mismatch vs xHC's stored value is corrected+logged in `check_interval` (xhci-ring.c:3448).
- Stream counts: `HCC_MAX_PSA(p)` → 2 to 65536 primary streams (spec floor: xHC must support ≥4, xhci.c:3502-3506 comment); endpoint-context `EP_MAXPSTREAMS` field is 5 bits (xhci.h:462-463); stream-ctx-array size rounded to power of 2 via `xhci_calculate_streams_entries` (xhci.c:3494), clamped to `HCC_MAX_PSA`.
- `MAX_SOFT_RETRY` = 3 (bulk/intr USB_TRANSACTION_ERROR soft-retry cap before hard halt-recovery). xhci.h:1270; used in `process_bulk_intr_td` xhci-ring.c:2555.
- `MAX_HC_SLOTS` = 256 (xhci.h:36), `EP_CTX_PER_DEV` = 31 (xhci.h:732) — bounds on `xhci->devs[]` and `xhci_virt_device.eps[]`.

#### 5. Version-specific facts

- Set-TR-Dequeue is a single function `xhci_move_dequeue_past_td()` (xhci-ring.c:689); no `xhci_find_new_dequeue_state()`/`xhci_queue_new_dequeue_state()` pair exists at this SHA (semcode find_function returns not-found) — at v7.0 the two-function split of older kernels is gone.
- No function literally named `ring_doorbell_for_endpoint` exists; doorbell ringing is split between `xhci_ring_ep_doorbell` (xhci-ring.c:549, single-enqueue path) and `ring_doorbell_for_active_rings`/`xhci_ring_doorbell_for_active_rings` (xhci-ring.c:578/601, post-command restart path).
- `struct urb_priv` (xhci.h:1406) uses a `__counted_by(num_tds)` flexible-array annotation and `kzalloc_flex()` (xhci.c:1650) — 2024/2025-era bounds-hardening idiom; older trees use plain `kzalloc(sizeof+n*sizeof)`.
- `xhci_td` carries a `cancel_status` state machine (`enum xhci_cancelled_td_status`, xhci.h:1294) and `error_mid_td`/`urb_length_set`/`bounce_seg` fields, and `xhci_virt_ep` carries `EP_CLEARING_TT`/`EP_HARD_CLEAR_TOGGLE`/`EP_SOFT_CLEAR_TOGGLE` — reflects a substantially reworked cancellation/halt-recovery path (deferred cache-clearing across streams, TT-buffer clear integration) vs the simpler single-state cancellation of older documented kernels.
- Isoch queuing carries xHCI-1.1 ETE/extended-TBC support (`xep->use_extended_tbc`, `TRB_TD_SIZE_TBC`, xhci.h:1035) and Contiguous-Frame-ID (`HCC_CFC`, `sia_frame_id`/`TRB_FRAME_ID`).
- `COMP_RING_UNDERRUN`/`COMP_RING_OVERRUN` handling with a dedicated `ring_xrun_event` bool in `handle_tx_event` (xhci-ring.c:2633).

#### 6. Suggested page topics

- Stream rings as their own page — `xhci_stream_info`/`xhci_stream_ctx`, `xhci_alloc_stream_info` (xhci-mem.c:610), the `ep->ring` vs `stream_info->stream_rings[stream_id]` selection (`xhci_virt_ep_to_ring`, xhci-ring.c:628), radix-tree TRB→segment mapping — enough machinery for a standalone page, referenced but not owned by the transfer-ring page.
- Scatter-gather bulk transfers — `count_sg_trbs_needed`/sg walk in `xhci_queue_bulk_tx` (xhci-ring.c:3611-3660) and bounce-buffer alignment (`xhci_align_td`, xhci-ring.c:3541) merit their own subsection distinct from plain bulk.
- Zero-length-packet / short-packet handling — `URB_ZERO_PACKET` extra-TD logic, `COMP_SHORT_PACKET`/`URB_SHORT_NOT_OK` decoding spread across all three `process_*_td` functions — cross-cutting.
- Command ring & command lifecycle — `queue_command`/`xhci_alloc_command`/`handle_cmd_completion` (xhci-ring.c:1795) dispatch table is distinct machinery from transfer TRBs, worth its own page rather than folding into per-transfer-type pages.
- Bandwidth accounting (`xhci_bw_info`, `xhci_interval_bw_table`, `XHCI_SW_BW_CHECKING` quirk path in `xhci_configure_endpoint`) — touched by every configure-endpoint call but deserves separate treatment from the enumeration page.
- Isoch Missed-Service / skip machinery — `ep->skip`, `skip_isoc_td` (xhci-ring.c:2495), `COMP_MISSED_SERVICE_ERROR` — enough dedicated logic in `handle_tx_event` to warrant a boxed callout on the isoch page.

#### 7. xHCI MMIO/DMA-visible constructs (transfer-relevant)

- Doorbell register array `xhci->dba->doorbell[slot_id]` (`struct xhci_doorbell_array`, xhci.h:298); value = `DB_VALUE(ep_index, stream_id)` = `((ep_index+1)&0xff) | (stream_id<<16)` (xhci.h:302); write+readback in `xhci_ring_ep_doorbell` xhci-ring.c:549-573 (`writel`/`readl`).
- TR Dequeue Pointer + DCS: ep-context `deq` field (`__le64`, xhci.h:432) packs pointer | DCS bit; software tracks via `ep_ring->dequeue`/`cycle_state`; HW's live copy read back with `xhci_get_hw_deq` and masked with `TR_DEQ_PTR_MASK` in `xhci_move_dequeue_past_td` xhci-ring.c:715-716 before issuing Set-TR-Dequeue.
- Event-data TRBs: `TRB_EVENT_DATA`=7 (xhci.h:1111); `TRB_BEI` (Block Event Interrupt) flag set conditionally via `trb_block_event_intr()` for isoc TDs (inside `xhci_queue_isoc_tx`) to reduce event-ring pressure.
- Transfer-TRB field layout (all built via `queue_trb(xhci,ring,more,field1..field4)`, xhci-ring.c:3239):
  - Control: Setup TRB — `TRB_IDT|TRB_TYPE(TRB_SETUP)`, bRequestType/bRequest/wValue in field1, wIndex/wLength in field2 (xhci-ring.c:3833-3841); Data TRB — `TRB_TYPE(TRB_DATA)`, `TRB_LEN`/`TRB_TD_SIZE`/`TRB_DIR_IN` (xhci-ring.c:3855-3880); Status TRB — `TRB_TYPE(TRB_STATUS)|TRB_IOC` (xhci-ring.c:3906-3913).
  - Bulk/Interrupt: Normal TRB — `TRB_TYPE(TRB_NORMAL)`, `TRB_LEN`/`TRB_TD_SIZE(remainder)`/`TRB_CHAIN`/`TRB_IOC`/`TRB_ISP` (xhci-ring.c:3644-3706).
  - Isoch: first TRB `TRB_TYPE(TRB_ISOC)|TRB_TLBPC(last_burst)|TRB_TBC(burst)|sia_frame_id`, subsequent TRBs `TRB_TYPE(TRB_NORMAL)` (xhci-ring.c:4155-4225); TD-size/TBC macros `TRB_TD_SIZE`/`TRB_TD_SIZE_TBC` xhci.h:1032-1035, `TRB_TBC`/`TRB_TLBPC` xhci.h:1074-1076.
- TRB type encoding: `TRB_TYPE(p)`=`p<<10`, `TRB_FIELD_TO_TYPE(p)` decode (xhci.h:1094-1152).
- Completion-code field: `GET_COMP_CODE()` on `event->transfer_len` (event TRB field1), full enum xhci.h:832-867.

#### 8. Error-handling paths (completion code → handler, file:line)

- Stall (`COMP_STALL_ERROR`) — `handle_tx_event` sets `status=-EPIPE` (xhci-ring.c:2703); per-type processor sets `td->status`; `finish_td`(xhci-ring.c:2234) detects halt via `xhci_halted_host_endpoint` and calls `xhci_handle_halted_endpoint(...,EP_HARD_RESET)` (xhci-ring.c:984) → Reset Endpoint command → USB core's subsequent CLEAR_FEATURE(HALT) drives `xhci_endpoint_reset` (xhci.c:3307).
- Babble (`COMP_BABBLE_DETECTED_ERROR`) — `status=-EOVERFLOW` (xhci-ring.c:2712); isoc path additionally marks `td->error_mid_td` and sums partial length (`process_isoc_td` xhci-ring.c:2440-2445).
- Transaction error (`COMP_USB_TRANSACTION_ERROR`/`COMP_SPLIT_TRANSACTION_ERROR`) — `status=-EPROTO` (xhci-ring.c:2696-2701); bulk/intr retries in-place up to `MAX_SOFT_RETRY`=3 via `xhci_handle_halted_endpoint(...,EP_SOFT_RESET)` (`process_bulk_intr_td` xhci-ring.c:2555-2562) before giving up.
- Short packet (`COMP_SHORT_PACKET`, and `COMP_SUCCESS` with nonzero residual reclassified to short at xhci-ring.c:2686-2691) — `td->status=0`, actual_length computed from residual in each `process_*_td`; not an error unless `URB_SHORT_NOT_OK`.
- Ring underrun/overrun (`COMP_RING_UNDERRUN`/`COMP_RING_OVERRUN`, isoch OUT/IN) — flagged `ring_xrun_event=true` in `handle_tx_event` (xhci-ring.c:2724-2733), suppresses the "no TDs queued" warning and skips normal TD matching for that event.
- Missed service (`COMP_MISSED_SERVICE_ERROR`, isoch) — `ep->skip=true` (xhci-ring.c:2736-2743); subsequent TDs walked and marked via `skip_isoc_td` (xhci-ring.c:2495) until the ring catches up to the event's TD.
- Halted-endpoint recovery (generic) — `xhci_handle_halted_endpoint` xhci-ring.c:984 → `xhci_reset_halted_ep` xhci-ring.c:960 → `xhci_queue_reset_ep` xhci-ring.c:4475 (TRB_RESET_EP) → completion `xhci_handle_cmd_reset_ep` xhci-ring.c:1556 (invalidates cancelled TDs and restarts ring).
- Cancel/timeout — `xhci_urb_dequeue` xhci.c:1756 (URB unlink) and `xhci_handle_cmd_stop_ep` xhci-ring.c:1183 (Stop-Endpoint completion racing a halt, context-state-error retries); dying-host fallback `xhci_hc_died` xhci-ring.c:1381 completes all URBs with `-ESHUTDOWN` when `xhci->xhc_state & XHCI_STATE_DYING` / register read returns ~0 (checked in `xhci_urb_dequeue` xhci.c:1808-1811).

#### Hotplug skeleton (port change → xHCI commands → set configuration), both sides of the seam

1. Physical connect → xHC posts Port Status Change Event on event ring → `xhci_handle_event_trb` (xhci-ring.c:2986, TRB_PORT_STATUS) → `handle_port_status` (xhci-ring.c:1992) → `usb_hcd_poll_rh_status(hcd)` (xhci-ring.c:2162, calling into drivers/usb/core/hcd.c:721) which reads `hcd->driver->hub_status_data` = `xhci_hub_status_data` (drivers/usb/host/xhci-hub.c:1639) and gives back the roothub's pending `status_urb`.
2. That status-urb completion is `hub_irq` (drivers/usb/core/hub.c:773) → `kick_hub_wq` → work `hub_event` (hub.c:5874) → per-port `port_event` (hub.c:5746, reads `usb_hub_port_status`, clears change bits) → `hub_port_connect_change` (hub.c:5637) → `hub_port_connect` (hub.c:5390).
3. `hub_port_connect` allocates the device: `usb_alloc_dev` (drivers/usb/core/usb.c:644) → `hcd->driver->alloc_dev` = `xhci_alloc_dev` (xhci.c:4211) → Enable Slot command `xhci_queue_slot_control(TRB_ENABLE_SLOT)` (xhci-ring.c:4395) → completion `xhci_handle_cmd_enable_slot` (xhci-ring.c:1590) → device-context init `xhci_alloc_virt_device` (xhci-mem.c:968, allocs out_ctx/in_ctx via `xhci_alloc_container_ctx`, ep0 ring, DCBAA entry).
4. `hub_port_connect` → `hub_port_init` (hub.c:4902): `hub_port_reset` (physical reset) → `hub_enable_device`(hub.c:4809)→`hcd->driver->enable_device`=`xhci_enable_device` → `get_bMaxPacketSize0` (control transfer at address 0, first real xHCI Control-TRB transfer through the just-created ep0 ring) → `hub_set_address` (hub.c:4747) → `hcd->driver->address_device` = `xhci_address_device` (xhci.c:4487) → `xhci_setup_device`(xhci.c:4304, input-ctx fill via `xhci_setup_addressable_virt_dev`, xhci-mem.c:1091) → Address Device command `xhci_queue_address_device(TRB_ADDR_DEV)` (xhci-ring.c:4403) → completion `xhci_handle_cmd_addr_dev` (xhci-ring.c:1654).
5. `usb_get_device_descriptor` (drivers/usb/core/message.c:1114) → `usb_get_descriptor`→`usb_control_msg`(message.c:150)→`usb_submit_urb`→`xhci_queue_ctrl_tx` (xhci-ring.c:3770) reads the device descriptor off the now-addressed control endpoint — first steady-state Control transfer.
6. `usb_new_device` (hub.c:2642) → `usb_enumerate_device` reads remaining (config/string) descriptors via more Control transfers → `device_add`.
7. Configuration selection → `usb_set_configuration` (drivers/usb/core/message.c:2054): `usb_hcd_alloc_bandwidth` drives `hcd->driver->add_endpoint/drop_endpoint`=`xhci_add_endpoint`/`xhci_drop_endpoint` (xhci.c:1985/1902) then `hcd->driver->check_bandwidth`=`xhci_check_bandwidth` (xhci.c:3080) → `xhci_configure_endpoint` (xhci.c:2960) → Configure Endpoint command `xhci_queue_configure_endpoint(TRB_CONFIG_EP)` (xhci-ring.c:4428) → completion via `handle_cmd_completion`'s TRB_CONFIG_EP case (xhci-ring.c:1868); then `usb_control_msg_send(SET_CONFIGURATION)` (message.c:2229) sends the actual device-side request over the control endpoint (another Control transfer).
8. Note: root-hub status URBs (step 1) never enter the transfer-ring machinery — `rh_urb_enqueue` (drivers/usb/core/hcd.c:812) intercepts them before `hcd->driver->urb_enqueue`; only the downstream device's real transfers (steps 5-7) use the TD/TRB/doorbell path documented above.

### Area F: Power management — COMPLETE (recorded 2026-07-16)

PCI/x86-64/ACPI scope only.

#### 1. Core structs and fields

- `struct xhci_hcd` — drivers/usb/host/xhci.h:1501. PM fields: `lock` (spinlock_t) :1516; `mutex` :1552; `xhc_state` :1566 (XHCI_STATE_DYING=BIT0/HALTED=BIT1/REMOVING=BIT2 :1581-1583); `s3` (struct s3_save) :1568; `quirks` (u64) :1584 with PM bits XHCI_RESET_ON_RESUME BIT(7):1601, XHCI_LPM_SUPPORT BIT(11):1605, XHCI_SLOW_SUSPEND BIT(17):1611, XHCI_SPURIOUS_WAKEUP BIT(18):1612, XHCI_U2_DISABLE_WAKE BIT(27):1623, XHCI_HW_LPM_DISABLE BIT(29):1625, XHCI_SUSPEND_DELAY BIT(30):1626, XHCI_DEFAULT_PM_RUNTIME_ALLOW BIT(33):1629, XHCI_SNPS_BROKEN_SUSPEND BIT(35):1631, XHCI_BROKEN_D3COLD_S2I BIT(41):1637; `hw_ports/usb2_rhub/usb3_rhub` :1650-1652; `hw_lpm_support:1`:1654, `broken_suspend:1`:1656; `port_caps/num_port_caps`:1660-1661; `port_status_u0`:1664; `main_hcd/shared_hcd`:1502-1503.
- `struct s3_save` (register snapshot) — xhci.h:1420-1425: command, dev_nt, dcbaa_ptr, config_reg. Per-interrupter save fields `s3_iman/s3_imod/s3_erst_size/s3_erst_base/s3_erst_dequeue` in `struct xhci_interrupter` — xhci.h:1451-1457.
- `struct xhci_bus_state` (per-roothub PM state) — xhci.h:1433-1442: bus_suspended, next_statechange, port_c_suspend, suspended_ports, port_remote_wakeup, resuming_ports.
- `struct xhci_hub` — xhci.h:1489-1497: ports[], num_ports, hcd, embedded `bus_state`.
- `struct xhci_port` — xhci.h:1474-1487: port_reg, hw_portnum/hcd_portnum, rhub, port_cap, `lpm_incapable:1`, `resume_timestamp`, `rexit_active`, slot_id, `rexit_done`/`u3exit_done` completions.
- `struct xhci_port_cap` — xhci.h:1465-1471: protocol_caps (carries XHCI_HLC/XHCI_BLC hw-LPM capability, xhci-ext-caps.h:65-66).
- Per-device LPM tracking, `struct usb_device` — include/linux/usb.h:660: `lpm_capable/usb2_hw_lpm_capable/besl_capable/enabled/allowed:1` :702-707; `usb3_lpm_u1_enabled/u2_enabled:1`:708-709; `l1_params`(usb2_lpm_parameters: besl,timeout):738,def:527-538; `u1_params/u2_params`(usb3_lpm_parameters: mel,sel,pel,timeout):739-740,def:547-568; `lpm_disable_count`:741; `do_remote_wakeup/reset_resume/port_is_suspended:1`:728-730.
- `struct usb_port` (per-port bookkeeping) — drivers/usb/core/hub.h:101-121: connect_type, state, `usb3_lpm_u1_permit:1`/`usb3_lpm_u2_permit:1` (sysfs-controlled), quirks.
- `usb_hcd` PM hooks — include/linux/usb/hcd.h:68: `flags` bits HCD_FLAG_HW_ACCESSIBLE=0:107, HCD_FLAG_POLL_RH=2:108, HCD_FLAG_WAKEUP_PENDING=4:110, HCD_FLAG_RH_RUNNING=5:111, HCD_FLAG_DEAD=6:112; `rh_timer`:83; `wakeup_work`(CONFIG_PM):86; `bandwidth_mutex`:185 (governs LPM enable/disable).

#### 2. API families (function — file:line — role — USB-core/PCI-core caller)

- `xhci_suspend` xhci.c:968-1073 — stop HC, CSS save — called by `xhci_pci_suspend` xhci-pci.c:800→829.
- `xhci_resume` xhci.c:1082-1292 — CRS restore or full reinit — called by `xhci_pci_resume` xhci-pci.c:840→876.
- `xhci_save_registers`/`xhci_restore_registers` xhci.c:804-827/829-851 — static; save/restore USBCMD/DNCTRL/DCBAAP/CONFIG + per-interrupter ERST/IMAN/IMOD; called only from xhci_suspend/xhci_resume.
- `xhci_pci_suspend`/`xhci_pci_resume` xhci-pci.c:800-838/840-877 — generic wrapper (+`xhci_msix_sync_irqs` xhci-pci.c:116); wired as `hc_driver.pci_suspend/pci_resume` at xhci-pci.c:970-971; invoked by hcd-pci.c `suspend_common`/`resume_common`.
- `xhci_bus_suspend`/`xhci_bus_resume` xhci-hub.c:1715-1841/1871-1985 — per-roothub PORTSC suspend/resume; wired as `hc_driver.bus_suspend/bus_resume` xhci.c:5616-5617; root hub reached via `hcd_bus_suspend/hcd_bus_resume` (hcd.h:694-695) called from drivers/usb/core/generic.c:287/315 (`usb_generic_driver_suspend/resume`, `!udev->parent` branch).
- `xhci_set_usb2_hardware_lpm` xhci.c:4647-4739 — programs PORTPMSC(HIRD/BESL/L1DS/HLE)+PORTHLPMC(BESLD/L1_TIMEOUT/HIRDM); wired `hc_driver.set_usb2_hw_lpm` xhci.c:5624; reached via `usb_set_usb2_hardware_lpm` driver.c:2042 ← `usb_enable/disable_usb2_hardware_lpm` driver.c:2056/2066 ← `usb_port_suspend/resume` hub.c:3529/3871.
- `xhci_calculate_u1_timeout`/`xhci_calculate_u2_timeout` xhci.c:4880-4915/4944-4973 — per-endpoint hub-encoded timeout; called from `xhci_update_timeout_for_endpoint` xhci.c:4989 ← `xhci_calculate_lpm_timeout` xhci.c:5059.
- `xhci_enable_usb3_lpm_timeout`/`xhci_disable_usb3_lpm_timeout` xhci.c:5167-5207/5209-5222 — compute timeout+MEL, issue Evaluate-Context; wired `hc_driver` hooks xhci.c:5625-5626; called by `usb_enable_link_state`/`usb_disable_link_state` hub.c:4327/4398 ← `usb_enable_lpm`/`usb_disable_lpm` hub.c:4503/4440.
- `xhci_change_max_exit_latency` xhci.c:4517-4582 — Evaluate-Context command writing slot-ctx MAX_EXIT field (device-context based — contrast with USB2's port-register based LPM).
- `xhci_set_link_state` xhci-hub.c:798-813 — PORTSC PLS write w/ strobe; used by bus_resume, hub_control, usb2 resume path.
- `xhci_set_remote_wake_mask` xhci-hub.c:815-839 — PORTSC WKCONN_E/WKDISC_E/WKOC_E from SetPortFeature(REMOTE_WAKE_MASK); called from `xhci_hub_control` xhci-hub.c:1509-1510.
- `xhci_disable_hub_port_wake` xhci.c:895-925 — clears wake bits on all roothub ports if `!do_wakeup`; only caller is xhci_suspend (xhci.c:984-985).
- `xhci_hub_control` xhci-hub.c:1205-1628 — root-hub control-endpoint emulation (SetPortFeature/ClearPortFeature POWER, SUSPEND, C_SUSPEND, U1/U2_TIMEOUT, LINK_STATE, REMOTE_WAKE_MASK); `hc_driver.hub_control` xhci.c:5614; reached from `usb_port_suspend/resume` (hub.c) via `set_port_feature`/`usb_clear_port_feature` control-transfer helpers.
- `xhci_get_resuming_ports` xhci-hub.c:1987-1993 — USB2 resuming_ports bitmap; `hc_driver.get_resuming_ports` xhci.c:5618; called by `report_wakeup_requests` hub.c:4025-4035 during `hub_resume`.
- Generic PCI glue, drivers/usb/core/hcd-pci.c: `suspend_common`/`resume_common` :418-479/481-520 call `hcd->driver->pci_suspend/pci_resume`; `hcd_pci_suspend/_freeze/_suspend_noirq/_poweroff_late/_resume/_resume_noirq/_restore` :524-598 (CONFIG_PM_SLEEP); `hcd_pci_runtime_suspend/_runtime_resume` :612-631 (PMSG_AUTO_*); `const struct dev_pm_ops usb_hcd_pci_pm_ops` :633-649, wired at xhci-pci.c:963 (`.driver.pm = pm_ptr(&usb_hcd_pci_pm_ops)`).
- Runtime-PM enablement, `xhci_pci_common_probe` xhci-pci.c:611-690: `pm_runtime_get_noresume`:624 (guards 2-roothub bring-up) → `pm_runtime_put_noidle`:668 → `pm_runtime_get`:671 (if PCI_D0) or `pm_runtime_allow`:673 (if XHCI_DEFAULT_PM_RUNTIME_ALLOW, auto-set xhci-pci.c:511-512 when hci_version≥0x120).
- ACPI seam: `xhci_set_port_power` xhci-hub.c:645-676 drops/retakes xhci->lock to call `usb_acpi_power_manageable`/`usb_acpi_set_power_state` (usb-acpi.c); `xhci_find_lpm_incapable_ports` xhci-pci.c:532-558 (CONFIG_ACPI) calls `usb_acpi_port_lpm_incapable()` (_DSM), feeding `xhci_port.lpm_incapable` consumed at xhci.c:5188-5192.

#### 3. Lifecycle and locking

- Suspend order: hub/port suspend → `xhci_bus_suspend` (roothub PORTSC→U3) → `xhci_pci_suspend`/`xhci_suspend` (controller: CMD_RUN clear, CSS save) → hcd-pci.c `suspend_common` (pci_disable_device) → `hcd_pci_suspend_noirq`(pci_prepare_to_sleep, hcd-pci.c:557).
- Resume order (reverse): PCI D0 → `hcd_pci_resume_noirq`/`hcd_pci_resume`/`hcd_pci_restore` (hcd-pci.c:584-598) → `resume_common`(pci_enable_device+set_master) → `xhci_pci_resume`/`xhci_resume` (CRS restore or reinit) → `xhci_bus_resume` (roothub PORTSC→U0) via `usb_hcd_resume_root_hub`/pending-portevent (xhci.c:1262-1266).
- What survives: op-regs saved xhci.c:1029(`xhci_save_registers`)→restored xhci.c:1125 when `!power_lost`. Falls back to FULL REINIT (nothing survives — dcbaa/rings/device contexts freed, xhci->devs[] and current_mel LPM cache lost until re-enumeration) when: XHCI_RESET_ON_RESUME or broken_suspend xhci.c:1108-1109, or USBSTS SRE|HCE after restore xhci.c:1149-1154 → `xhci_halt`:1170→`xhci_reset(XHCI_RESET_LONG_USEC)`:1175→`xhci_mem_cleanup`:1186→`xhci_init`:1196→`xhci_run`:1202/1205 (skipped, -ENODEV, if XHCI_STATE_REMOVING:1172-1173).
- Locking: `xhci->lock` (spin_lock_irq/irqsave) held across register RMW in suspend/resume/bus_suspend/bus_resume/hub_control; dropped/retaken around `xhci_stop_device`, ACPI power calls, and `rexit_done`/`u3exit_done` waits. `bandwidth_mutex` (hcd.h:185) must be held by callers of usb_enable_lpm/usb_disable_lpm (comment hub.c:4327-4331). Port device lock (`usb_lock_port`) held across `usb_port_suspend`/`usb_port_resume` (hub.c:3501/3793).
- Per-device suspend dispatch split, drivers/usb/core/generic.c:284-287 (`usb_generic_driver_suspend`): root hub (`!udev->parent`) → `hcd_bus_suspend`; normal device → `usb_port_suspend` (hub.c:3501).

#### 4. Hard-coded limits

- XHCI_MAX_HALT_USEC=32ms (xhci-ext-caps.h:12), doubled xhci.c:971, ×10 more if XHCI_SLOW_SUSPEND xhci.c:1018.
- STS_SAVE handshake 20ms xhci.c:1036-1037; STS_RESTORE handshake 100ms xhci.c:1138-1139; STS_CNR handshake 10s xhci.c:1116-1117; post-resume STS_HALT clear 250ms xhci.c:1228-1229.
- XHCI_RESET_LONG_USEC=10s / XHCI_RESET_SHORT_USEC=250ms — xhci.h:151-152.
- msleep(100) roothub settle xhci.c:1098-1100; msleep(120) USB3 U3-wake retry xhci.c:1257-1258.
- XHCI_DEFAULT_BESL=4 — xhci-port.h:173; XHCI_L1_TIMEOUT=512us — xhci-port.h:161; `xhci_besl_encoding[16]` table — xhci.c:4587.
- USB3_LPM_U1_MAX_TIMEOUT=0x7F / U2_MAX_TIMEOUT=0xFE — include/uapi/linux/usb/ch9.h:1262-1263 (used xhci.c:4910/4968); USB3_LPM_MAX_U1_SEL_PEL=0xFF/U2=0xFFFF — ch9.h:1278-1279 (used xhci.c:4805/4811).
- MAX_EXIT=0xffff (16-bit MEL ceiling, else -E2BIG) — xhci.h:371, checked xhci.c:5158-5161.
- XHCI_PORT_POLLING_LFPS_TIME=36ms ×10 retries — xhci-port.h:181, used xhci-hub.c:1764.
- XHCI_MAX_REXIT_TIMEOUT_MS=20ms (USB2 RExit→U0) — xhci.h:1464, used xhci-hub.c:995.
- 500ms U3-exit completion wait (SetPortFeature LINK_STATE=U0) — xhci-hub.c:1461.
- USB_RESUME_TIMEOUT=40ms (USB2 L2/global resume signaling) — include/linux/usb.h:337, used xhci-hub.c:969,1582,1951.
- `run_graceperiod`=500ms post-start USB3 polling grace window — xhci.c:175, consumed xhci-hub.c:1673-1677.

#### 5. Version-specific facts

- Per-port `resume_timestamp`/`rexit_done` (xhci.h:1481-1486, struct xhci_port) replaced an older flat array design — proven by a stale comment still referencing `resume_done[]` at xhci-hub.c:959 even though that array no longer exists.
- PM state is nested per-roothub (`xhci_hub.bus_state`, xhci.h:1495) rather than one flat `xhci_hcd`-level bus_state — a structural refactor from the older single-roothub-array model.
- XHCI_DEFAULT_PM_RUNTIME_ALLOW (xhci-pci.c:511-512) ties runtime-PM default policy to xHCI-spec version (≥1.2 mandates D3hot/D3cold) — newer than the plain save/restore (CSS/CRS) mechanism which is spec-0.96-era.
- Entire USB2-HW-LPM/USB3-LPM block is `#ifdef CONFIG_PM` (xhci.c:4584-5247) with `#else` no-op stubs (xhci.c:5223-5247) — LPM support is compile-gated, not merely runtime-gated, in this tree.
- XHCI_SNPS_BROKEN_SUSPEND/XHCI_BROKEN_D3COLD_S2I/XHCI_RESET_TO_DEFAULT (xhci.h:1631/1637, xhci-pci.c:813-817) are relatively recent additions distinguishing S3 vs s2idle (`pm_suspend_target_state`) suspend targets — this granularity is newer than the base suspend/resume design.
- Quirks bitmask has grown to BIT_ULL(50) (XHCI_LIMIT_ENDPOINT_INTERVAL_9, xhci.h) — PM core logic itself is stable; most growth is vendor-quirk related (out of hard scope here).

#### 6. Suggested page topics the six miss

- USB2 `usb2_hardware_lpm` sysfs store (hub.c ~6196/6309) and USB3 `usb3_lpm_permit` sysfs store (port.c:262) — user-space override knobs for pages 3/4, currently unanchored.
- Port-device runtime PM / peer-linking distinct from roothub bus_suspend — `usb_port_runtime_suspend/resume` port.c:410/351, `link_peers/unlink_peers` port.c:484/568 — natural subsection under page 2.
- ACPI `_DSM`/power-resource integration (`usb_acpi_power_manageable/set_power_state`, `usb_acpi_port_lpm_incapable`) — xhci-hub.c:670-674, xhci-pci.c:519-558 — merits explicit callout given the ACPI-only hard scope.
- Compliance Mode Recovery timer's suspend/resume lifecycle (`comp_mode_recovery_timer`, XHCI_COMP_MODE_QUIRK) — xhci.c:1064-1070,1156-1162 — timer start/stop is coupled to every suspend/resume transition.
- Dying/surprise-removal handling during PM (`xhci_hc_died`, XHCI_STATE_DYING vs REMOVING) — xhci-ring.c:1381-1407 — could be its own page or a mandatory subsection of the system-resume page.

#### 7. xHCI MMIO registers/fields touched (accessor — file:line)

- USBCMD.CSS/CRS — `CMD_CSS`(bit8) xhci.h:137 / `CMD_CRS`(bit9) xhci.h:138; read/write via `&xhci->op_regs->command` xhci.c:1013-1015(suspend), 1130-1132/1225-1227(resume).
- USBSTS.SSS/RSS/SRE/CNR/HCE — `STS_SAVE`(bit8):165, `STS_RESTORE`(bit9):167, `STS_SRE`(bit10):169, `STS_CNR`:171, `STS_HCE`(bit12):173, all xhci.h; read via `&xhci->op_regs->status`.
- PORTSC — `xhci_port_regs.portsc` xhci.h:85; accessors `xhci_portsc_readl`/`writel` xhci.c:51/44. `.PLS`+values `XDEV_U0..RESUME` xhci-port.h:17-30; `.PP`=`PORT_POWER`(bit9) xhci-port.h:33; wake enables WCE/WDE/WOE=`PORT_WKCONN_E/WKDISC_E/WKOC_E`(bits25-27) xhci-port.h:110-114, combined `PORT_WAKE_BITS` xhci-hub.c:20.
- PORTPMSC USB2 layout (field `portpmsc` xhci.h:86) — L1S(bits0-2)`PORT_L1S_MASK/SUCCESS` xhci-port.h:136-137; RWE(bit3) :138; HIRD/BESL(bits4-7)`PORT_HIRD` :139-140; L1DS(bits8-15, device slot)`PORT_L1DS` :141-142; HLE(bit16) :143 — written xhci.c:4700-4711 (`xhci_set_usb2_hardware_lpm`).
- PORTPMSC USB3 layout (same field) — U1 Timeout(bits0-7)`PORT_U1_TIMEOUT` xhci-port.h:128-129; U2 Timeout(bits8-15)`PORT_U2_TIMEOUT` :131-132 — written directly xhci-hub.c:1520-1535 (SetPortFeature U1/U2_TIMEOUT). Spec's FLA (bit16) is not defined/used anywhere in this driver.
- PORTHLPMC (field `porthlmpc`, note kernel misspelling, xhci.h:88) — USB2-only HIRDM/L1_TIMEOUT/BESLD, xhci-port.h:156-158, computed `xhci_calculate_usb2_hw_lpm_params` xhci.c:4626, written xhci.c:4707. USB3 PORTHLPMC layout is never referenced by this driver.
- Extended-cap `protocol_caps` XHCI_HLC(bit19)/XHCI_BLC(bit20) — xhci-ext-caps.h:65-66; consumed `xhci_update_device` xhci.c:4772-4777.

#### 8. Error-handling paths

- STS_SRE after CSS set (SNPS quirk, SRE==0&&HCE==0 → false-positive) → `xhci->broken_suspend=1` xhci.c:1047-1051, else `-ETIMEDOUT` xhci.c:1053-1055.
- STS_SRE|STS_HCE after restore attempt → force `power_lost=true` → full reinit path xhci.c:1149-1221 (skips with `-ENODEV` if XHCI_STATE_REMOVING, xhci.c:1172-1173).
- STS_CNR handshake timeout(10s) at resume start → `-ETIMEDOUT`, no register touch, xhci.c:1116-1122.
- CMD_RUN-clear / STS_HALT handshake timeout in suspend → `-ETIMEDOUT` xhci.c:1020-1025.
- CMD_CRS / STS_RESTORE handshake timeout(100ms) → `-ETIMEDOUT` xhci.c:1138-1143.
- Port stuck resuming: `xhci_handle_usb2_port_link_resume` waits `rexit_done` up to 20ms (XHCI_MAX_REXIT_TIMEOUT_MS); on timeout leaves `rexit_active` set so `xhci_get_usb2_port_status` keeps reporting `USB_PORT_STAT_SUSPEND` — xhci-hub.c:1004-1015,1124-1125.
- Port stuck U3→U0: `wait_for_completion_timeout(u3exit_done, 500ms)` only logs dbg on timeout, doesn't fail request — xhci-hub.c:1460-1463.
- Remote-wake race: `suspend_common` rechecks `HCD_WAKEUP_PENDING` after `pci_suspend`, calls `pci_resume` back and returns `-EBUSY` if raced — hcd-pci.c:441-462; `xhci_bus_suspend` itself bails `-EBUSY` on resuming_ports/port_remote_wakeup already set or connect-change/over-current mid-suspend — xhci-hub.c:1723-1730,1750-1761.
- Delayed USB3 wake resend: `xhci_resume` retries `xhci_pending_portevent` after `msleep(120)` for auto-resume only — xhci.c:1257-1259.
- Dying host: any PORTSC/USBSTS `readl`==0xffffffff → `xhci_hc_died` (xhci-ring.c:1381-1407) sets XHCI_STATE_DYING, kills pending URBs, calls `usb_hc_died()`; checked in `xhci_hub_control` GetPortStatus/SetPortFeature/ClearPortFeature xhci-hub.c:1267-1270,1313-1317,1560-1564 and `xhci_hub_status_data` xhci-hub.c:1685-1689.
- `HCD_DEAD(hcd)` suppresses `pci_suspend`/`pci_resume` in `suspend_common`/`resume_common` (hcd-pci.c:441,502) and forces `device_set_wakeup_enable(dev,0)` at suspend_noirq (hcd-pci.c:550-551).
- `check_root_hub_suspended` (hcd-pci.c:400-416) guards PCI suspend_noirq/freeze_noirq: `-EBUSY`+dev_warn if `HCD_FLAG_RH_RUNNING` still set on either roothub.

## Directory organization

All pages under `docs/xhci/`, thirteen groups (ring/ carries two sub-groups, following the `docs/pci/` precedent for a third level). Group counts corrected 2026-07-21 to match the catalog tables and the tag census; see Amendment 2026-07-21:

```
docs/xhci/
├── core/       the xhci_hcd object, MMIO access, hcd bridge, PCI probe, ext-caps (4)
├── init/       bring-up: DCBAA/scratchpad, host init sequence, bus spawn (3)
├── lifecycle/  reset, shutdown, host-death machinery (3)
├── roothub/    hub emulation, port-array construction, bus suspend/resume (3)
├── ports/      per-generation port registers, port events, port hotplug (4)
├── device/     slots, contexts, doorbells, configure-endpoint (8)
├── ring/       generic ring machinery + TRB taxonomy (6)
│   ├── command/   command ring, command TRBs, lifecycle, abort (4)
│   └── transfer/  transfer rings, TDs, events, per-type pages, streams, recovery (9)
├── interrupt/  event ring, event TRBs, interrupters, MSI/MSI-X, sideband (5)
├── hotplug/    the end-to-end enumeration narrative (1)
├── pm/         host, port, USB2/USB3 device, system suspend/resume (6)
└── dbc/        the Debug Capability: DbC core + TTY function driver (2, user-added)
```

Rationale: the layout keeps the draft corpus's proven grouping (which itself mirrors the request's 13 headings) and adds `core/` so no page sits ungrouped at the root — the two top-level draft files (`overview.md`, `usb-hcd-bridge.md`) are superseded by `core/` rows. Granularity calibrates against `docs/acpi` (43 pages, ~640-2,600 lines each, one mechanism per page), the request's named granularity reference. Event-ring pages live in `interrupt/` (not `ring/`) because the event ring is consumer-only by design and its machinery is inseparable from interrupters — the request groups them the same way.

## Page catalog

Tags: [prompt] = explicitly in a prompt.md bullet (or a split of one, marked); [curated] = gap-fill under the prompt's "include but not limited to" / "curate new ones if you see fit" mandate. Every anchor symbol carries a file:line hint from the digests above; all hints re-verified on disk at write time.

### core/

| page | scope (anchor symbols) | tag |
|---|---|---|
| xhci-hcd.md | struct xhci_hcd tour (xhci.h:1501): MMIO block pointers cap/op/run/dba + xhci_cap_regs/xhci_op_regs/xhci_run_regs (xhci.h:65/104/283), cached caps + hci_version, lock vs mutex split, xhc_state + XHCI_STATE_*, devs[]/interrupters[]/rhubs as subsystem indexes, the quirks-u64 mechanism (accumulation `xhci->quirks |= quirks` xhci.c:5465 — mechanism only, no vendor bits); accessors: direct readl/writel, xhci_read_64/write_64 (xhci.h:1757-1766), xhci_handshake (xhci.c:85), hcd_to_xhci/xhci_to_hcd (xhci.h:1698/1710); register-space layout figure (CAPLENGTH→op regs→runtime→doorbell via DBOFF/RTSOFF) | [prompt] |
| usb-hcd-bridge.md | how xHCI plugs into the USB-core HCD framework: struct usb_hcd (hcd.h:68, flags/state/hcd_priv), struct hc_driver ops (hcd.h:237), base table xhci_hc_driver (xhci.c:5564) + xhci_driver_overrides (xhci.h:1679) + xhci_init_driver (xhci.c:5631), the .reset=NULL/per-glue-mandatory fact, primary/shared hcd pairing + usb_hcd_is_primary_hcd, HCD_BH giveback consequence (xhci.c:5574) | [prompt] |
| pci-probe.md | the PCI attach path (generic only): usb_hcd_pci_probe (hcd-pci.c:172), xhci_pci_probe/xhci_pci_common_probe (xhci-pci.c:699/611) two-hcd creation order, xhci_pci_setup (xhci-pci.c:566), BAR0 mapping, runtime-PM enablement at probe (xhci-pci.c:624-673), teardown xhci_pci_remove (xhci-pci.c:708); the HCD_USB3 IRQ carve-out (hcd-pci.c:191) is cited in one sentence — interrupt/msi-msix.md owns the walkthrough; usb_hcd_pci_shutdown is cited — lifecycle/host-shutdown.md owns it | [curated] |
| ext-caps.md | extended-capability list walk + USB Legacy Support handoff: xhci_find_next_ext_cap (xhci-ext-caps.h:130), capability IDs (xhci-ext-caps.h:36-42), XHCI_HC_BIOS_OWNED/OS_OWNED handoff in quirk_usb_handoff_xhci (pci-quirks.c:1158, PCI CLASS_FINAL fixup — runs before probe; CORRECTED 2026-07-21 from "early fixup"), XHCI_MAX_EXT_CAPS unused-bound fact; supported-protocol caps deferred to roothub/port-arrays.md. ROW EXCEPTIONS (review item 5): pci-quirks.c is outside the Subsystem Map kernel_paths — this row carries the file-set exception explicitly; and the class dispatcher this function hangs off sits beside legacy-HCI handoff functions in the same file — cite ONLY the xHCI-specific function, never quote or name the dispatcher's neighbors (absolute UHCI/EHCI/OHCI ban) | [curated] |

### init/

| page | scope (anchor symbols) | tag |
|---|---|---|
| host-init.md | xhci_gen_setup (xhci.c:5414, caps read 5443-5463 + halt + zero-64b + reset LONG), xhci_init (xhci.c:546), the op-reg programming quartet xhci_hcd_page_size/xhci_enable_max_dev_slots/xhci_set_cmd_ring_deq/xhci_set_doorbell_ptr/xhci_set_dev_notifications (xhci.c:464-537), xhci_run/xhci_run_finished/xhci_start (xhci.c:643/595/151, CNR + CMD_RUN + STS_HALT handshakes), CMD_EIE/EWE; states that Linux never programs FLADJ (firmware-owned PCI config register; verified absent from the driver — request bullet retargeted) | [prompt] |
| dcbaa-scratchpad.md | struct xhci_device_context_array (xhci.h:796), DCBAAP programming (xhci_write_64, xhci.c:571), devs[] as SW mirror, scratchpad: xhci_scratchpad (xhci.h:1400), scratchpad_alloc/free (xhci-mem.c:1643/1706), HCS_MAX_SCRATCHPAD (xhci-caps.h:42), the slot-0-holds-scratchpad-pointer fact, PAGESIZE consumption | [prompt] |
| usb-bus-spawn.md | usb_create_hcd/usb_create_shared_hcd (hcd.c:2659/2636), usb_add_hcd (hcd.c:2802) incl. usb_register_bus + roothub udev alloc + register_root_hub (hcd.c:951), the usb2-then-usb3 bring-up order from xhci_pci_common_probe, teardown mirror usb_remove_hcd/usb_stop_hcd (hcd.c:3028/2778), xhci_stop's primary-hcd-only memory free (xhci.c:706) | [prompt] |

### lifecycle/

| page | scope (anchor symbols) | tag |
|---|---|---|
| host-reset.md | xhci_quiesce/xhci_halt/xhci_reset (xhci.c:103/127/188), USBCMD CMD_RESET + STS_CNR handshake, XHCI_RESET_LONG_USEC vs SHORT_USEC call sites, xhci_zero_64b_regs, reset-at-setup vs reset-at-stop vs reset-at-resume-reinit, not-halted no-op + ~0 detection | [prompt] |
| host-shutdown.md | xhci_stop (xhci.c:706) vs xhci_shutdown (xhci.c:766), xhci_pci_stop/xhci_pci_shutdown wrappers (xhci-pci.c:224/928) + MSI cleanup ordering, OWNS usb_hcd_pci_shutdown (hcd-pci.c:359; core/pci-probe.md cites), XHCI_STATE_HALTED/REMOVING, mem cleanup single-shot guard | [prompt] |
| host-dying.md | the death machinery every page's error section escalates to: xhci_hc_died (xhci-ring.c:1381), XHCI_STATE_DYING vs HALTED vs REMOVING semantics (xhci.h:1581-1583, cleared only by xhci_start), STS_HCE/STS_FATAL ISR branches (xhci-ring.c:3196-3206), all-ones register detection in xhci_handshake/xhci_irq, usb_hc_died + HCD_FLAG_DEAD seam (hcd.c:2508), URB flush with -ESHUTDOWN | [curated] |

### roothub/

| page | scope (anchor symbols) | tag |
|---|---|---|
| root-hub.md | the emulated hub: struct xhci_hub (xhci.h:1489), xhci_hub_control (xhci-hub.c:1205) + xhci_hub_status_data (:1639, incl. run_graceperiod), hub-descriptor synthesis xhci_common/usb2/usb3_hub_descriptor (:256/279/334), BOS synthesis xhci_create_usb3x_bos_desc (:36) from psi[] tables, xhci_get_rhub (:631), rh_urb_enqueue interception seam (hcd.c:812) — why roothub URBs never touch transfer rings; MANDATORY per-generation sections + why-differs for the descriptor/BOS synthesis (constraint-13 adjudication in Scope decisions: generation branches of single functions get sections, not page splits) | [prompt] |
| port-arrays.md | port bookkeeping construction: struct xhci_port/xhci_port_cap (xhci.h:1474/1465), xhci_setup_port_arrays (xhci-mem.c:2185), xhci_add_in_port (:2017), xhci_create_rhub_port_array (:2152), supported-protocol capability decode (XHCI_EXT_PORT_* macros, xhci-ext-caps.h:101-112), hw_portnum vs hcd_portnum, USB_MAXCHILDREN=31/USB_SS_MAXPORTS=15 caps, xhci_find_rhub_port (:1071), the unused struct xhci_protocol_caps caution | [curated] |
| bus-suspend-resume.md | per-roothub suspend/resume sweep: struct xhci_bus_state (xhci.h:1433), xhci_bus_suspend/xhci_bus_resume (xhci-hub.c:1715/1871), bus_suspended/resuming_ports/port_remote_wakeup bitmaps, LFPS polling grace (XHCI_PORT_POLLING_LFPS_TIME ×10), the three -EBUSY bail paths (pre-loop wake race, OC, connect-change — slice-3 audit corrected the drafts' count of two), xhci_get_resuming_ports (:1987) + report_wakeup_requests seam (hub.c:4025); MANDATORY per-generation sections + why-differs for the divergent USB2 (resume signalling/RExit) vs USB3 (U3/CAS) branches (constraint-13 adjudication in Scope decisions) | [curated] |

### ports/

| page | scope (anchor symbols) | tag |
|---|---|---|
| port-registers-usb2.md | USB2 port register semantics: shared xhci_port_regs quad (xhci.h:84), PORTSC bits from xhci-port.h (common set + USB2-only semantics), USB2 PLS subset (U0/U2=L1/U3/Resume/RxDetect/Polling), the SW resume state machine xhci_handle_usb2_port_link_resume (xhci-hub.c:937) + resume_timestamp/rexit_active/rexit_done + XHCI_MAX_REXIT_TIMEOUT_MS, PORTPMSC USB2 layout (L1S/RWE/HIRD/L1DS/HLE + test mode, xhci-port.h:136-144), PORTHLPMC (USB2-only, xhci-port.h:156-158; kernel field misspelling `porthlmpc`), eUSB2v2 PORTLI RDR/TDR, xhci_get_usb2_port_status (xhci-hub.c:1092); why-the-generations-differ section (two-rhub spec split) | [prompt] |
| port-registers-usb3.md | USB3 port register semantics: USB3-only PORTSC bits WRC/CEC/CAS (xhci-port.h:74-108, RsvdZ on USB2), full PLS set (U1/Recovery/Compliance/SS.Inactive) + raw-PLS-in-wPortStatus via xhci_hub_report_usb3_link_state (xhci-hub.c:856), warm reset PORT_WR/BH_PORT_RESET, u3exit_done completion, PORTPMSC USB3 layout (U1/U2 timeouts, xhci-port.h:128-132; FLA unused by Linux), PORTLI LEC/lane counts, xhci_get_usb3_port_status (xhci-hub.c:1041) + xhci_get_ext_port_status (:1025); why-the-generations-differ section | [prompt] |
| port-event-handling.md | Port Status Change Event chain: TRB_PORT_STATUS dispatch (xhci-ring.c:3007) → handle_port_status (:1992) → usb_hcd_poll_rh_status (hcd.c:721) → hub_irq → hub_wq → port_event (hub.c:5746); change-bit RWC protocol xhci_clear_port_change_bit (xhci-hub.c:580) + xhci_test_and_clear_bit (:842), PORT_CHANGE_MASK, VDEV_PORT_ERROR set/clear (xhci-ring.c:2049) | [prompt] |
| port-hotplug.md | port-level connect/disconnect: CSC detect, debounce (HUB_DEBOUNCE_* hub.c:138), reset ownership split — xHCI fire-and-forget PORT_RESET/PORT_WR writes (xhci-hub.c:1501-19) vs usbcore's state machine hub_port_reset/hub_port_wait_reset (hub.c:3050/2953) with PORT_RESET_TRIES budget, warm-reset-required (hub.c:2937), over-current recovery (hub.c:5787), disconnect + early_stop/ignore_event; hands off to hotplug/downstream-hotplug.md at hub_port_connect | [prompt] |

### device/

| page | scope (anchor symbols) | tag |
|---|---|---|
| device-tracking.md | the SW mirrors: struct xhci_virt_device (xhci.h:734) + xhci_virt_ep (xhci.h:652), devs[MAX_HC_SLOTS] as the DCBAA mirror (xhci.h:1554), slot numbering (256 slots, 0 reserved — scratchpad ptr), rhub_port back-link + port->slot_id forward link, VDEV_PORT_ERROR flag, the "virt = software mirror, NOT virtualization" disambiguation (contrast: real VF machinery HCC2_VTC/TRB_FORCE_EVENT/TRB_TO_VF_INTR_TARGET, xhci-caps.h:114/xhci.h:985 — out of scope), sideband pointers noted; owns the two-endpoint-state-namespaces section — SW xhci_virt_ep.ep_state bits (xhci.h:658-670) vs HW EP_STATE_* context codes (:445-451), disambiguation table with per-bit owner cross-cites (halt/cancel bits → endpoint-halt-recovery, stream bits → streams, doorbell gating → doorbell) | [prompt] |
| slot-lifecycle.md | the slot state machine Enable→Address→Configure→Reset→Disable: SLOT_STATE_DISABLED/DEFAULT/ADDRESSED/CONFIGURED (xhci.h:400-406), xhci_alloc_dev (xhci.c:4211) → xhci_alloc_virt_device (xhci-mem.c:968, kzalloc_obj idiom); the Address leg — xhci_address_device/xhci_enable_device (xhci.c:4487/4493, BSR split) → xhci_setup_device (:4304, xhci->mutex serialization, COMP_USB_TRANSACTION_ERROR fresh-slot retry) → xhci_handle_cmd_addr_dev (xhci-ring.c:1654); the Reset Device leg — xhci_discover_or_reset_device (xhci.c:3910, hc_driver.reset_device) → xhci_queue_reset_device (xhci-ring.c:4419) → xhci_handle_cmd_reset_dev; xhci_disable_slot/xhci_free_dev/xhci_disable_and_free_slot (xhci.c:4130/4091/4174), xhci_free_virt_device (xhci-mem.c:868) + depth-first teardown (:933), disable-only-on-COMP_SUCCESS asymmetry (xhci-ring.c:1599) | [curated] |
| container-context.md | struct xhci_container_ctx (xhci.h:320) as the one blob behind device ctx, input ctx, and port-bandwidth ctx (xhci_alloc_port_bw_ctx xhci-mem.c:487); CSZ bit HCC_64BYTE_CONTEXT + CTX_SIZE choke point (xhci-caps.h:61-62), alloc/free (xhci-mem.c:452/478), accessors xhci_get_slot_ctx/xhci_get_ep_ctx/xhci_get_input_control_ctx (xhci-mem.c:525/535/516), device-pool sizing (2112B, xhci-mem.c:2437) | [curated] |
| slot-context.md | struct xhci_slot_ctx fields (xhci.h:342): route string (ROUTE_STRING_MASK :353), speed, hub/MTT, LAST_CTX, max exit latency, root-hub port (ROOT_HUB_PORT :373), TT slot/port + interrupter target (GET_INTR_TARGET reuse, xhci.h:2351), USB address + SLOT_STATE (GET_SLOT_STATE :400); who writes each field and when (setup_addressable_virt_dev, Address/Evaluate completions); owns the TT-bookkeeping-population section — xhci_update_hub_device (xhci.c:5254, hc_driver.update_hub_device) and xhci_alloc_tt_info (xhci-mem.c:823) fill the TT fields and tt_bw_info (configure-endpoint.md cites) | [prompt] |
| endpoint-context.md | struct xhci_ep_ctx fields (xhci.h:426): HW EP_STATE_* codes (:445-451), interval/mult/ESIT (EP_INTERVAL_TO_UFRAMES :459), EP_TYPE (:477), max packet/burst (:488), 64-bit deq + DCS, tx_info avg-TRB-len/max-ESIT; endpoint-index math xhci_get_endpoint_index/address/flag/last_valid_endpoint (xhci.c:1457-1494); xhci_endpoint_init (xhci-mem.c:1407) fills it from usb_host_endpoint | [prompt] |
| input-context.md | struct xhci_input_control_ctx (xhci.h:513) add/drop flag bitmaps; input-ctx assembly: xhci_setup_addressable_virt_dev (xhci-mem.c:1091), xhci_slot_copy/xhci_endpoint_copy (:1626/1600), xhci_endpoint_zero (:1513), xhci_copy_ep0_dequeue_into_input_ctx (:1039), xhci_zero_in_ctx (xhci.c:2086); which commands consume an input ctx (Address/Configure/Evaluate) vs which don't | [prompt] |
| doorbell.md | struct xhci_doorbell_array (xhci.h:298), DB_VALUE/DB_VALUE_HOST encoding (xhci.h:302-303: target=ep_index+1, stream_id<<16; doorbell 0 = command), DBOFF location, xhci_ring_cmd_db (xhci-ring.c:422), xhci_ring_ep_doorbell (:549) + its ep_state skip conditions, ring_doorbell_for_active_rings (:576/601), write+readback ordering | [prompt] |
| configure-endpoint.md | the Configure Endpoint operation end to end: xhci_add_endpoint/xhci_drop_endpoint (xhci.c:1985/1902) and xhci_check_bandwidth/xhci_reset_bandwidth (xhci.c:3080/3179) as the hc_driver hooks usb_hcd_alloc_bandwidth drives, xhci_configure_endpoint (xhci.c:2960) + result mapping (xhci.c:2120/2170), new_ring install/discard; bandwidth-bookkeeping structs as a section — xhci_bw_info (xhci.h:597), xhci_interval_bw/_table (:711/723, XHCI_MAX_INTERVAL=16), xhci_tt_bw_info (:783), xhci_root_port_bw_info (:777) + xhci->rh_bw — documented as definitions with the verified statement that the SW accounting model engages only behind a quirk-mechanism bit and is otherwise dormant (no vendor naming; slice-2 audit finding); endpoint-teardown side — xhci_endpoint_disable (xhci.c:3252, wired :5597) and xhci_free_device_endpoint_resources (xhci.c:3868), with endpoint-halt-recovery.md citing the disable-while-halted interaction; Get Port Bandwidth command flow (xhci-ring.c:4439 — rule-8 usage example legitimately cites its debugfs consumer under the recorded carve-out; container-context.md owns the type-less blob xhci_alloc_port_bw_ctx, this page owns the command flow) | [curated] |

### ring/

| page | scope (anchor symbols) | tag |
|---|---|---|
| ring-overview.md | struct xhci_ring (xhci.h:1362) + xhci_segment (:1281), enum xhci_ring_type (:1330), producer/consumer ownership model shared by transfer+command rings, td_list, cycle_state field; the by-design event-ring difference (no link TRBs — xhci_initialize_ring_segments early-returns for TYPE_EVENT, xhci-mem.c:116/121; ERST navigation; consumer-only; ERDP not doorbell) stated once with pointers to interrupt/event-ring.md | [prompt] |
| trb-types.md | the TRB taxonomy page guaranteeing "every TRB type mentioned": union xhci_trb/xhci_generic_trb 16-byte layout (xhci.h:1083-1092), TRB_TYPE()/TRB_FIELD_TO_TYPE()/TRB_TYPE_BITMASK (:1094-1097), the full census — transfer 1-8, command 9-23, reserved 24-31, event 32-39, reserved 40-47, vendor-defined 48-63 (xhci.h:1100-1168) — each DEFINED type with one-liner + owning page; the two type-48/49 macros the kernel defines inside the vendor range are LISTED with value + "vendor-defined; outside scope, no coverage" and nothing more (review item 20: the census mandate governs mention, the vendor ban governs coverage); completion-code section: 36 COMP_* codes [CORRECTED 2026-07-21 from 35] (xhci.h:832-867) + xhci_trb_comp_code_string (:869); 7h-style generic-TRB bitfield figure (docs/pci/protocol/tlp/msg style) | [prompt, split of "mention every type of TRB somewhere"] |
| ring-memory.md | ring memory & DMA tracking: xhci_ring_alloc/xhci_segment_alloc/xhci_alloc_segments_for_ring/xhci_ring_free (xhci-mem.c:370/29/330/289), segment_pool DMA pools, TRBS_PER_SEGMENT=256/TRB_SEGMENT_SIZE=4096, xhci_ring_expansion (+_needed) (xhci-mem.c:414/xhci-ring.c:379) + xhci_link_rings splice (:136), radix-tree trb_address_map insert/remove (xhci-mem.c:206-271, stream rings), xhci_trb_virt_to_dma/xhci_dma_to_trb/trb_in_td (xhci-ring.c:71/85/331), bounce-buffer segment fields | [prompt] |
| ring-maintenance.md | enqueue/dequeue mechanics and iteration helpers: inc_enq/inc_enq_past_link/inc_deq (xhci-ring.c:283/232/186), queue_trb (:3239), prepare_ring ep-state checks + expansion trigger (:3263), xhci_initialize_ring_info (xhci-mem.c:305), xhci_num_trbs_free (:343), next_trb/last_trb_on_seg/last_trb_on_ring (:172/112/117), trb_to_noop (:148) | [prompt] |
| segment-chaining.md | link TRBs: struct xhci_link_trb (xhci.h:949) + LINK_TOGGLE (:957), xhci_set_link_trb (xhci-mem.c:96) + xhci_initialize_ring_segments (xhci-mem.c:116, TYPE_EVENT early return :121) [CORRECTED 2026-07-21], trb_is_link/link_trb_toggles_cycle (xhci-ring.c:107/123), chain-bit-on-link mechanism xhci_link_chain_quirk (xhci.h:1779) — EXCERPT STRATEGY (review item 4): cite the generic setter (xhci.c:5477-5480, hci_version==0x95 spec-revision check + link_quirk module param) and the call sites (xhci_set_link_trb/xhci_initialize_ring_segments/inc_enq_past_link/prepare_ring); never excerpt the predicate body (its two lines name vendor flags); per-ring-type sections: transfer rings (multi-segment, expandable), command ring (fixed size — prepare_ring refuses expansion, xhci-ring.c:3300), event ring (none — ERST instead) | [prompt] |
| cycle-bit.md | C and TC usage model: producer-writes/consumer-compares ownership, cycle_state tracking, giveback_first_trb deferred first-TRB flip (xhci-ring.c:3432), inc_enq cycle flip at link TRBs, link_trb_toggles_cycle; per-ring-type sections: command ring (RCS in CRCR, xhci_set_cmd_ring_deq xhci.c:496), transfer ring (DCS in ep-ctx deq + Set TR Dequeue, TR_DEQ_PTR_MASK xhci-ring.c:715), event ring (CCS consumer-side, SW never writes — inc_deq comment xhci-ring.c:186) | [prompt] |

### ring/command/

| page | scope (anchor symbols) | tag |
|---|---|---|
| command-ring.md | the command ring itself (hard-rescoped per review item 13): CRCR bits RCS/CS/CA/CRR + CMD_RING_PTR_MASK (xhci.h:189-197), xhci_set_cmd_ring_deq (xhci.c:496), ring allocation/config + fixed sizing + MAX_RSVD_CMD_TRBS=253 (xhci.h:1261) + no-expansion fact, cmd_ring_state VALUES (xhci.h:1538-1540; transitions are command-abort.md's), doorbell-0 pointer (DB_VALUE_HOST via xhci_ring_cmd_db — array is doorbell.md's); queue_command/handle_cmd_completion are NEVER walked here (command-lifecycle.md owns the fill→doorbell→completion model). Coverage-of-scope tripwire: if the register+config material lands thin against the depth floor at write time, the recorded fallback is folding this row into command-lifecycle.md | [prompt] |
| command-trb.md | structure of every command TRB: per-command field layouts built by the xhci_queue_* family (xhci-ring.c:4395-4487 — slot control, address device incl. BSR, configure endpoint, evaluate context, reset endpoint/TSP, stop ring/SP, set TR dequeue incl. SCT+stream, reset device, get port bandwidth, vendor/noop), TRB_TO_SLOT_ID/SLOT_ID_FOR_TRB (xhci.h:817-818); 7h-style per-command TRB figures | [prompt] |
| command-lifecycle.md | struct xhci_command (xhci.h:528) end to end: xhci_alloc_command/_with_ctx/xhci_free_command (xhci-mem.c:1730/1758/1782), queue_command (xhci-ring.c:4352), cmd_list ordering, completion decode via xhci_event_cmd + comp_param, handle_cmd_completion dispatch table (:1795), xhci_complete_del_and_free_cmd (:1696), waiting patterns (completion + XHCI_CMD_DEFAULT_TIMEOUT) | [prompt] |
| command-abort.md | timeout/abort/recovery protocol: cmd_timer + xhci_mod_cmd_timer (xhci-ring.c:436), xhci_handle_command_timeout (:1717), xhci_abort_cmd_ring (:490, CA write + 5s CRR handshake + 2s stop-event wait), COMP_COMMAND_RING_STOPPED, xhci_handle_stopped_cmd_ring (:453), xhci_cleanup_command_queue (:1709), escalation to lifecycle/host-dying.md | [curated] |

### interrupt/

| page | scope (anchor symbols) | tag |
|---|---|---|
| event-ring.md | event ring + ERST hierarchy: xhci_erst/xhci_erst_entry (xhci.h:1393/1385), xhci_alloc_erst (xhci-mem.c:1791, ERST_DEFAULT_SEGS=2, HCS_ERST_MAX bound), no-link-TRB allocation, the event loop xhci_handle_events/xhci_handle_event_trb/unhandled_event_trb (xhci-ring.c:3086/2986/135), ERDP dequeue maintenance xhci_update_erst_dequeue (:3038) + EHB/DESI + the 128-event force-flush, initial dequeue program xhci_set_hc_event_deq (xhci-mem.c:2000), consumer cycle (CCS); ERSTSZ/ERSTBA programming is interrupters.md's (xhci_add_interrupter — cited here, never walked) | [prompt] |
| event-trb.md | event TRB structures: xhci_transfer_event (xhci.h:808, buffer/transfer_len/flags + GET_COMP_CODE), xhci_event_cmd (:960), port status change/MFINDEX wrap/HC event layouts, slot/ep id decode macros; owns the Device Notification event — layout + handle_device_notification (xhci-ring.c:1943), with a DNCTRL cross-cite to init/host-init.md (review item 16); 7h-style event-TRB figures; the census itself is ring/trb-types.md's | [prompt] |
| interrupters.md | struct xhci_interrupter (xhci.h:1446) + xhci_intr_reg (:227): interrupters[] array + max_interrupters/MAX_HC_INTRS=128 vs ir_set[1024], xhci_alloc/add/remove/free_interrupter (xhci-mem.c:2285/2320/1822/1844 — this page owns xhci_add_interrupter's register programming wholly; event-ring.md cites), IMAN IP/IE enable/disable (xhci.c:313/330) + xhci_clear_interrupt_pending, interrupt moderation IMOD xhci_set_interrupter_moderation (xhci.c:350, 40us PCI default vs 1ms HW default), isoc_bei_interval; owns the secondary-interrupter allocation machinery — xhci_create/remove_secondary_interrupter (xhci-mem.c:2349/1868), ip_autoclear, xhci_skip_sec_intr_events (xhci-ring.c:3147); the client-side API story is sideband.md's (restored at the user checkpoint) | [prompt] |
| sideband.md | the secondary-interrupter client API: struct xhci_sideband (include/linux/usb/xhci-sideband.h:52), xhci-sideband.c register/unregister + endpoint/interrupter handoff, xhci_sideband_interrupter_id feeding TRB_INTR_TARGET, xhci_virt_device.sideband/xhci_virt_ep.sideband fields, ip_autoclear rationale — how offload clients own an interrupter without the xHCI IRQ path. RECORDED EXCEPTION (review item 3, user-confirmed): the API's only in-tree consumer is vendor-gated, so the page documents the exported surface and registration flow without a consumer excerpt — rule 8's usage-example mandate is explicitly waived for this page | [curated] |
| msi-msix.md | MSI/MSI-X acquisition for PCI xHCI: OWNS the hcd-pci carve-out walkthrough (`(driver->flags & HCD_MASK) < HCD_USB3` — real code line hcd-pci.c:191; :187-190 is its comment block — generic layer skips IRQ setup; core/pci-probe.md cites in one sentence), xhci_try_enable_msi (xhci-pci.c:143, called from .start override xhci_pci_run :211), vector count min(num_online_cpus()+1, max_interrupters) (:166), MSI-X→MSI→INTx fallback, xhci_msi_irq vs xhci_irq (xhci-ring.c:3224/3177), xhci_msix_sync_irqs/xhci_cleanup_msix (xhci-pci.c:116/129), vector↔interrupter mapping + TRB_INTR_TARGET (xhci.h:1037) | [prompt] |

### dbc/ (user-added at the checkpoint)

| page | scope (anchor symbols) | tag |
|---|---|---|
| dbgcap.md | the xHCI Debug Capability core: discovery via XHCI_EXT_CAPS_DEBUG=10 (xhci-ext-caps.h:42) + xhci_find_next_ext_cap from xhci_create_dbc_dev (xhci-dbgcap.c:1475, offset walk :1486); struct dbc_regs (xhci-dbgcap.h:15), dbc_info_context (:31), enum dbc_state (:94), struct dbc_ep (:103), struct xhci_dbc (:141), struct dbc_request (:172); lifecycle xhci_alloc_dbc (xhci-dbgcap.c:1422)/xhci_dbc_remove (:1461)/xhci_dbc_suspend/resume (:1513/1535); DbC's own contexts and rings reusing the generic machinery (xhci_dbc_init_contexts :142, dbc_erst_alloc :422 — cites ring/ and device/ owners, never re-walks them); transfer path dbc_ep_queue (:374) + dbc_handle_xfer_event (:771); the sysfs enable knob + descriptor attributes (dbc_show/dbc_store :1052/1068, DEVICE_ATTR_RW set :1398-1403); generic mechanism only — no vendor content exists in the file set | [curated] |
| dbgtty.md | the DbC TTY function driver: struct dbc_port (xhci-dbgcap.h:119), struct dbc_driver (:136), tty_operations dbc_tty_ops (xhci-dbgtty.c:391) with install/open/put_char (:265/281/328), dbc_tty_init/exit (:622/659), buffering between dbc_requests and the tty layer (tty internals cited at the seam only). Coverage-of-scope tripwire: if the material lands thin against the depth floor at write time, the recorded fallback is folding this row into dbc/dbgcap.md | [curated] |

### ring/transfer/

| page | scope (anchor symbols) | tag |
|---|---|---|
| transfer-ring.md | endpoint transfer rings: ep-ctx deq as the HW entry point, xhci_virt_ep.ring vs stream selection (xhci_virt_ep_to_ring xhci-ring.c:628, xhci_triad_to_transfer_ring :652), OWNS prepare_transfer (:3325, ring lookup + td init + first-TD usb_hcd_link_urb_to_ep) and cites prepare_ring as ring/ring-maintenance.md's seam symbol, enqueue model + giveback_first_trb doorbell hand-off (:3432), TR Dequeue+DCS ownership, ring-full → expansion (cited; internals are ring-memory.md's) | [prompt] |
| transfer-td.md | TDs and transfer-TRB construction: struct xhci_td (xhci.h:1302), urb_priv (:1406, __counted_by + kzalloc_flex idiom xhci.c:1650), count_trbs/count_trbs_needed/count_sg_trbs_needed/count_isoc_trbs_needed (xhci-ring.c:3374-3410), 64KB TRB_MAX_BUFF_SIZE rule (xhci.h:1265), xhci_td_remainder TD-size math (:3514), bounce alignment xhci_align_td (:3541), IDT xhci_urb_suitable_for_idt (xhci.h:2015), CHAIN/IOC/ISP flags, TD lifecycle TRB→doorbell→event | [prompt] |
| transfer-events.md | the completion side: handle_tx_event (xhci-ring.c:2633) comp-code decode + trb_in_td TD matching, the per-type processors named as dispatch pointers only (process_ctrl_td/process_isoc_td/process_bulk_intr_td :2293/2388/2518 — owned by their xfer pages), the shared funnel finish_td (:2234) → xhci_dequeue_td (:926) → xhci_td_cleanup (:879), giveback xhci_giveback_urb_in_irq (:825) → usb_hcd_giveback_urb BH deferral (hcd.c:1731, HCD_BH), short-packet reclassification (:2686), ring_xrun_event underrun/overrun | [prompt] |
| xfer-control.md | control transfers: 2/3-TRB TDs — Setup (TRB_IDT immediate data, xhci-ring.c:3833), Data (TRB_DIR_IN :3855), Status (:3906) — via xhci_queue_ctrl_tx (:3770), ep0 shared-ring specifics, process_ctrl_td stage tracking (:2293), seam usb_control_msg/usb_control_msg_send (message.c:150/2229) down to the TRBs; per-stage TRB figures | [prompt] |
| xfer-bulk.md | bulk transfers: xhci_queue_bulk_tx (xhci-ring.c:3611) normal-TRB chains, scatter-gather walk + count_sg_trbs_needed, 64KB splits + bounce alignment, URB_ZERO_PACKET extra ZLP TD, OWNS the shared process_bulk_intr_td walkthrough (:2518) incl. soft-retry MAX_SOFT_RETRY=3 (:2555) — xfer-interrupt.md cites it, transfer-events.md names it as a dispatch pointer only; seam usb_bulk_msg/usb_submit_urb | [prompt] |
| xfer-interrupt.md | interrupt transfers: xhci_queue_intr_tx thin wrapper (xhci-ring.c:3483) over bulk machinery, check_interval mismatch correction (:3448), the interval decoder chain xhci_get_endpoint_interval/xhci_parse_exponent_interval/xhci_parse_frame_interval (xhci-mem.c:1284/1212/1269), EP_INTERVAL encoding + ESIT (xhci.h:459), urb->interval seam and USB-core clamping; process_bulk_intr_td is xfer-bulk.md's — cited, never re-walked | [prompt] |
| xfer-isoch.md | isochronous transfers: xhci_queue_isoc_tx_prepare/xhci_queue_isoc_tx (xhci-ring.c:4270/4077), one TD per iso_frame_desc, TRB_ISOC + TBC/TLBPC + extended-TBC (ETE, use_extended_tbc) + frame ID/SIA (HCC_CFC), BEI + isoc_bei_interval interplay, missed-service skip machinery (ep->skip, skip_isoc_td :2495), underrun/overrun, process_isoc_td partial-length accounting, MFINDEX use | [prompt] |
| streams.md | bulk stream rings: xhci_stream_info/xhci_stream_ctx (xhci.h:572/549) + SCT, xhci_alloc_streams/xhci_free_streams as hc_driver ops (xhci.c:3609/3776) through Configure Endpoint, xhci_alloc_stream_info (xhci-mem.c:610), stream-id in DB_VALUE, radix-tree TRB→ring lookup, HCC_MAX_PSA/EP_MAXPSTREAMS bounds, EP_GETTING_STREAMS/EP_HAS_STREAMS transitions | [curated] |
| endpoint-halt-recovery.md | halt and cancel recovery: EP_HALTED + xhci_handle_halted_endpoint/xhci_reset_halted_ep (xhci-ring.c:984/960), EP_HARD_RESET vs EP_SOFT_RESET (xhci.h:979), Reset Endpoint completion (:1556), Stop Endpoint cancel path xhci_urb_dequeue (xhci.c:1756) → xhci_handle_cmd_stop_ep (:1183) → xhci_invalidate_cancelled_tds (:1034) → Set TR Dequeue xhci_move_dequeue_past_td (:689) → xhci_handle_cmd_set_deq (:1416), cancel_status machine (xhci.h:1294), TT-buffer clear (:2166), endpoint_reset seam (xhci.c:3307) | [curated] |

### hotplug/

| page | scope (anchor symbols) | tag |
|---|---|---|
| downstream-hotplug.md | the end-to-end narrative (recaps ≤1 paragraph per owned mechanism, cites owners): port event (xhci-ring.c:2986→1992) → hub_irq/hub_wq (hub.c:773/5874/5746) → hub_port_connect (:5390) → usb_alloc_dev + Enable Slot (usb.c:644, xhci.c:4211) → hub_port_init (:4902): reset, xhci_enable_device, bMaxPacketSize0, Address Device (xhci.c:4487→4304, input ctx) → descriptor reads over control (message.c:1114 → xhci-ring.c:3770) → usb_new_device (hub.c:2642) → usb_set_configuration (message.c:2054) → add/drop/check_bandwidth + Configure Endpoint (xhci.c:1985/1902/3080→xhci-ring.c:4428) → SET_CONFIGURATION (message.c:2207); address0_mutex/bandwidth_mutex serialization | [prompt] |

### pm/

| page | scope (anchor symbols) | tag |
|---|---|---|
| host-controller-pm.md | controller suspend/resume + runtime PM: xhci_suspend/xhci_resume (xhci.c:968/1082), s3_save + per-interrupter s3_* (xhci.h:1420/1451), CSS/CRS + SSS/RSS/SRE handshakes with their timeouts, the power_lost full-reinit fork (xhci.c:1149-1221 — devs[]/rings lost, re-enumeration), xhci_pci_suspend/resume wrappers (xhci-pci.c:800/840), hcd-pci dev_pm_ops glue (hcd-pci.c:633), runtime-PM enablement + XHCI_DEFAULT_PM_RUNTIME_ALLOW ≥1.2 policy (xhci-pci.c:511), PM quirk-bit mechanism note | [prompt] |
| port-power-management.md | per-port power: PORT_POWER + xhci_set_port_power ACPI hand-off (xhci-hub.c:645, usb_acpi_power_manageable/set_power_state), wake bits WCE/WDE/WOE + xhci_set_remote_wake_mask (:815) + xhci_disable_hub_port_wake (xhci.c:895), PLS setters xhci_set_link_state (:798), usb_port runtime PM + peer linking seam (port.c:410/351/484), usb3_lpm_permit + usb2_hardware_lpm sysfs knobs (port.c:262, hub.c) | [prompt] |
| usb2-device-pm.md | USB2 device PM through xHCI — port-register-based: hardware LPM (L1) xhci_set_usb2_hardware_lpm (xhci.c:4647) programming PORTPMSC HIRD/BESL/L1DS/HLE + PORTHLPMC BESLD/L1_TIMEOUT/HIRDM, xhci_calculate_hird_besl/xhci_calculate_usb2_hw_lpm_params (:4591/4626) + xhci_besl_encoding table (:4587), XHCI_HLC/BLC capability gates (xhci-ext-caps.h:65), L2 suspend/resume signaling (USB_RESUME_TIMEOUT=40ms) citing xhci_handle_usb2_port_link_resume as ports/port-registers-usb2.md's seam symbol (that page owns the RExit state machine), usb_enable/disable_usb2_hardware_lpm seam (driver.c:2056/2066 ← hub.c:3529/3871); why-differs: register-programmed vs USB3's context-programmed | [prompt] |
| usb3-device-pm.md | USB3 device PM — device-context-based: U1/U2 timeout calculation per endpoint (xhci_calculate_u1/u2_timeout xhci.c:4880/4944, tiers + USB3_LPM_U1/U2_MAX_TIMEOUT), xhci_calculate_lpm_timeout (:5059), Evaluate Context MEL write xhci_change_max_exit_latency (:4517, MAX_EXIT ceiling), enable/disable_usb3_lpm_timeout hooks (:5167/5209) ← usb_enable/disable_link_state (hub.c:4327/4398) ← usb_enable/disable_lpm (:4503/4440) under bandwidth_mutex, U3 via SetPortFeature, lpm_incapable ACPI _DSM (xhci-pci.c:532), u1/u2_params SEL/PEL; why-differs section | [prompt] |
| system-suspend.md | system-wide suspend walk (narrative, cites owners): device tree order — udevs (usb_port_suspend) → roothubs (hcd_bus_suspend → xhci_bus_suspend) → controller (suspend_common → xhci_pci_suspend → xhci_suspend) → noirq (pci_prepare_to_sleep, hcd-pci.c:557); do_wakeup decisions + wake-bit clearing, HCD_WAKEUP_PENDING -EBUSY race (hcd-pci.c:441), check_root_hub_suspended guard (:400), S3-vs-s2idle mechanism distinctions (pm_suspend_target_state, generic), compliance-timer stop (xhci.c:1064) | [prompt] |
| system-resume.md | system-wide resume walk: noirq → resume_common (pci_enable_device+set_master) → xhci_pci_resume → xhci_resume restore-vs-reinit fork → xhci_bus_resume port sweep → usb_hcd_resume_root_hub + pending-portevent recheck (xhci.c:1262, 120ms retry :1257), reinit consequences (re-enumeration of every device), comp-mode timer restart (:1156), resume error paths (SRE/HCE→reinit; CNR timeout; REMOVING abort) | [prompt] |

### Fold-in adjudications (topics that do NOT get pages)

Review-added fold-ins (2026-07-16): the two endpoint-state namespaces → device/device-tracking.md section (was a drafted row). (The review also folded sideband into interrupters.md; the user checkpoint restored it standalone — see the interrupt/ table.) Device Notification event + handle_device_notification → interrupt/event-trb.md. Hub-TT bookkeeping population (xhci_update_hub_device, xhci_alloc_tt_info) → device/slot-context.md TT section. Endpoint teardown ops (xhci_endpoint_disable, xhci_free_device_endpoint_resources) → device/configure-endpoint.md. Reset Device command leg → device/slot-lifecycle.md. Address Device command flow → device/slot-lifecycle.md (input-context.md keeps ctx-contents ownership).

Scratchpad → init/dcbaa-scratchpad.md (suggested standalone; the DCBAA slot-0 coupling argues for one page). Completion-code taxonomy → ring/trb-types.md section (+ per-use decode in transfer-events/command-lifecycle). Interrupt moderation + secondary-interrupter overview → interrupt/interrupters.md. MSI↔interrupter mapping → interrupt/msi-msix.md. Quirks-bitmask mechanism → core/xhci-hcd.md (mechanism only; no vendor bits anywhere in the corpus). Operational-register programming quartet → init/host-init.md. BOS/SuperSpeed(Plus) synthesis → roothub/root-hub.md subsection. USB2 hardware LPM → pm/usb2-device-pm.md (flow) + ports/port-registers-usb2.md (register layout only). Scatter-gather bulk + ZLP → ring/transfer/xfer-bulk.md sections; short-packet decode → transfer-events.md. Isoch missed-service/skip → xfer-isoch.md section. Slot-0/scratchpad gotcha → dcbaa-scratchpad + device-tracking cite. "virt ≠ virtualization" + VF/VTC contrast → device/device-tracking.md callout (write-time caution for every writer). Port test mode (PORTPMSC.PTC) → ports/port-registers-usb2.md. Compliance-mode recovery timer → ports/port-registers-usb3.md (mechanism) with PM-lifecycle notes in pm pages. Roothub status-URB interception (rh_urb_enqueue) → roothub/root-hub.md. hcd teardown symmetry → init/usb-bus-spawn.md.

Fold-OUTs (out of campaign scope, recorded so nobody re-litigates): every DT/platform glue (xhci-plat*, xhci-mtk*, xhci-tegra*, xhci-rcar*, xhci-histb*, dwc3) and vendor driver — banned by the request. Individual vendor/device quirk bits — banned; only the mechanism is documented. UHCI/EHCI/OHCI — banned outright, no historical mention. xhci-ext-caps.c body — builds a vendor platform device only (Area A evidence); ext-caps.md covers the generic walker+handoff. (SUPERSEDED at the checkpoint: the xHCI Debug Capability fold-out is reversed — the user added dbc/dbgcap.md + dbc/dbgtty.md to the catalog.) xhci-debugfs.c — instrumentation, not a concept; individual pages may cite a debugfs file where it exposes a documented register (e.g. portli). Virtualization (VTC/VF force-event machinery) — named once in device-tracking's disambiguation, never documented. USB4/Thunderbolt tunneled USB3 — docs/usb4 territory. PCI MSI capability internals — docs/pci territory; msi-msix.md cites pci_alloc_irq_vectors without documenting it. usbcore hub driver internals beyond the named seams — the pages stop at the call boundary.

### Projected total and tag census

58 pages (post-review, post-checkpoint): core/ 4, init/ 3, lifecycle/ 3, roothub/ 3, ports/ 4, device/ 8, ring/ 6, ring/command/ 4, interrupt/ 5, ring/transfer/ 9, hotplug/ 1, pm/ 6, dbc/ 2.
Tag census: 44 [prompt] (incl. 1 split: trb-types), 14 [curated]. Deltas from the drafted 57: device/ep-state.md folded into device-tracking.md (review item 14); interrupt/sideband.md briefly folded by review item 3, then RESTORED standalone at the user checkpoint carrying the recorded rule-8 exception; dbc/ group (2 rows) added at the user checkpoint, reversing the DbC fold-out.

### Overlap boundary rules (seam symbols named)

1. core cluster: xhci-hcd.md owns the struct tour + MMIO accessors + quirks mechanism; usb-hcd-bridge.md owns the hc_driver/usb_hcd mapping; pci-probe.md owns probe/remove order; ext-caps.md owns the capability walk + BIOS handoff. Seams: hcd_to_xhci (xhci-hcd owns), xhci_init_driver (usb-hcd-bridge owns), usb_hcd_pci_probe (pci-probe owns), the HCD_USB3 IRQ carve-out at hcd-pci.c:191 (msi-msix owns the walkthrough; pci-probe cites in one sentence), usb_hcd_pci_shutdown (host-shutdown owns; pci-probe cites), xhci_find_next_ext_cap (ext-caps owns; port-arrays cites the protocol-cap walk).
2. init cluster: host-init.md owns the bring-up order + op-reg programming; dcbaa-scratchpad.md owns DCBAA/scratchpad allocation; usb-bus-spawn.md owns bus/roothub registration. Ring-allocation internals belong to ring/ring-memory.md and interrupter-0 setup to interrupt/interrupters.md — host-init cites xhci_mem_init (xhci-mem.c:2401) and xhci_add_interrupter once each. Seam: xhci_mem_init (dcbaa-scratchpad owns its DCBAA/scratchpad slices; ring-memory owns its pool/ring slices; host-init walks the order).
3. lifecycle cluster: host-reset.md owns halt/quiesce/reset; host-shutdown.md owns stop/shutdown; host-dying.md owns died/dying/fatal machinery; ring/command/command-abort.md owns command-ring recovery and escalates into host-dying. Seams: xhci_halt (host-reset owns; shutdown/dying cite), xhci_hc_died (host-dying owns; every error section cites).
4. roothub/ports cluster: root-hub.md owns hub emulation + descriptor/BOS synthesis; port-arrays.md owns construction + port structs; port-registers-usb2/usb3.md own per-generation register semantics and each carries its why-differs section (the two-rhub root cause stated once in root-hub.md, cited by both); port-event-handling.md owns the event→hub_wq chain; port-hotplug.md owns port-level connect/reset; hotplug/downstream-hotplug.md owns the end-to-end narrative. Seams: xhci_get_port_status (register pages own decode; event page cites), handle_port_status (port-event-handling owns), hub_port_connect (port-hotplug owns the port side; downstream-hotplug walks it), xhci_setup_port_arrays (port-arrays owns).
5. device cluster: device-tracking.md owns virt_device/virt_ep + devs[] + the two-endpoint-state-namespaces section (endpoint-context cites the HW codes; per-bit stories stay with their owners: halt/cancel bits → endpoint-halt-recovery, stream bits → streams, doorbell gating → doorbell); slot-lifecycle.md owns the command-driven slot state machine including the Address Device and Reset Device command flows (input-context.md owns what goes INTO the input context; slot-lifecycle owns when and why each command fires); container-context.md owns blob/CSZ/accessors; slot-context.md and endpoint-context.md own their HW-context field tours (citing container-context for access, never re-touring it), slot-context additionally owning the TT-bookkeeping population; input-context.md owns input assembly; doorbell.md owns the array + encoding; configure-endpoint.md owns the Configure-Endpoint op (add/drop_endpoint, check_bandwidth/reset_bandwidth, xhci_configure_endpoint + result mapping), the endpoint-teardown ops, and the bandwidth-bookkeeping section. Seams: xhci_get_ep_ctx (container-context owns), xhci_setup_addressable_virt_dev (input-context owns; slot-lifecycle and downstream-hotplug cite), xhci_ring_ep_doorbell (doorbell owns; transfer pages cite), xhci_alloc_virt_device (slot-lifecycle owns; device-tracking cites), xhci_configure_endpoint (configure-endpoint owns the internals; slot-lifecycle, streams, and downstream-hotplug cite it as a step).
6. ring cluster: ring-overview.md owns concepts + the type enum + the event-ring-differs statement; trb-types.md owns the census + completion codes; ring-memory.md owns alloc/DMA/radix/expansion; ring-maintenance.md owns enq/deq helpers; segment-chaining.md owns link TRBs; cycle-bit.md owns C/TC. Per-ring-type sections in segment-chaining and cycle-bit are mandatory (request). Seams: inc_enq/inc_deq (ring-maintenance owns), xhci_set_link_trb + xhci_initialize_ring_segments (segment-chaining owns; ring-memory cites) [CORRECTED 2026-07-21], TRB_TYPE macros (trb-types owns).
7. command cluster: command-ring.md owns CRCR + ring config + doorbell-0 use; command-trb.md owns per-command TRB layouts; command-lifecycle.md owns the xhci_command flow + completion dispatch; command-abort.md owns timeout/abort/stopped recovery. Seams: queue_command (command-lifecycle owns; command-trb cites), handle_cmd_completion (command-lifecycle owns; command-abort owns only its stopped/aborted branches).
8. interrupt cluster: event-ring.md owns ERST structures/alloc + event loop + ERDP maintenance; event-trb.md owns event-TRB field semantics + the Device Notification handler; interrupters.md owns xhci_interrupter/IMAN/IMOD/moderation + the secondary-interrupter allocation machinery; sideband.md owns the client API story (restored standalone with its recorded rule-8 exception); msi-msix.md owns vector acquisition + mapping + the HCD_USB3 carve-out walkthrough. Seams: xhci_handle_events (event-ring owns), xhci_add_interrupter (interrupters owns wholly; event-ring cites), xhci_create_secondary_interrupter (interrupters owns the machinery; sideband owns the client story), TRB_INTR_TARGET (msi-msix owns the mapping claim; trb-types owns the field). dbc cluster: dbgcap.md owns the capability core and cites ring/device owners for the generic machinery it reuses (one paragraph max per boundary rule 12); dbgtty.md owns the TTY function driver; seam: dbc_ep_queue (dbgcap owns; dbgtty cites), the tty layer cited at the boundary only.
9. transfer cluster: transfer-ring.md owns ep-ring mechanics + doorbell usage; transfer-td.md owns TD/TRB construction math; transfer-events.md owns the completion funnel; xfer-*.md own per-type queueing; streams.md owns stream machinery; endpoint-halt-recovery.md owns halt/cancel recovery. Seams: prepare_ring (ring-maintenance owns; transfer-ring cites), prepare_transfer (transfer-ring owns), count_trbs (transfer-td owns), handle_tx_event (transfer-events owns the dispatch), the per-type processors — process_ctrl_td (xfer-control owns), process_isoc_td (xfer-isoch owns), process_bulk_intr_td (xfer-bulk owns incl. soft-retry; xfer-interrupt cites; transfer-events names all three as dispatch pointers only), finish_td (transfer-events owns), xhci_handle_halted_endpoint (endpoint-halt-recovery owns; transfer-events and xfer pages cite).
10. pm cluster: host-controller-pm.md owns xhci_suspend/resume internals; roothub/bus-suspend-resume.md owns the rhub sweep; port-power-management.md owns port power/wake/ACPI; usb2/usb3-device-pm.md own per-generation LPM flows (register bit layouts stay in ports/port-registers-*.md); system-suspend/resume.md are ordered narratives citing the owners. Seams: xhci_suspend (host-controller-pm owns; system-suspend cites), xhci_bus_suspend (bus-suspend-resume owns), xhci_set_usb2_hardware_lpm (usb2-device-pm owns), xhci_change_max_exit_latency (usb3-device-pm owns), xhci_handle_usb2_port_link_resume (port-registers-usb2 owns the RExit state machine; usb2-device-pm and bus-suspend-resume cite).
11. Cross-subsystem boundary (applies to every row): USB-core code (drivers/usb/core/) is cited at the named seams and never documented beyond the call boundary; PCI-core machinery (config space, MSI capability internals, PCI PM states) is docs/pci territory — pages name the entry (pci_alloc_irq_vectors, pci_prepare_to_sleep) in one sentence; USB4/Thunderbolt-tunneled USB3 is docs/usb4 territory and out of scope; ACPI method internals (_DSM/_PLD evaluation) are cited as usb_acpi_* entry points only.
12. House narrative rule: the narrative pages (downstream-hotplug, system-suspend, system-resume) recap any owned mechanism in at most one short paragraph and cite the owning page's anchor symbol instead of re-walking it.

### Batch order (foundational → derived, ~5 pages per batch)

- B1: core/xhci-hcd, core/usb-hcd-bridge, ring/ring-overview, ring/trb-types, device/container-context
- B2: ring/ring-memory, ring/ring-maintenance, ring/segment-chaining, ring/cycle-bit, device/doorbell, lifecycle/host-dying (hoisted per review item 7 — every page's error section cites it)
- B3: device/device-tracking, device/slot-context, device/endpoint-context, device/input-context
- B4: ring/command/command-ring, ring/command/command-trb, ring/command/command-lifecycle, ring/command/command-abort
- B5: interrupt/event-ring, interrupt/event-trb, interrupt/interrupters, interrupt/msi-msix, interrupt/sideband
- B6: init/dcbaa-scratchpad, init/host-init, init/usb-bus-spawn, core/pci-probe, core/ext-caps
- B7: lifecycle/host-reset, lifecycle/host-shutdown, device/slot-lifecycle, device/configure-endpoint
- B8: roothub/root-hub, roothub/port-arrays, ports/port-registers-usb2, ports/port-registers-usb3
- B9: ports/port-event-handling, ports/port-hotplug, roothub/bus-suspend-resume, ring/transfer/transfer-ring
- B10: ring/transfer/transfer-td, ring/transfer/transfer-events, ring/transfer/endpoint-halt-recovery, ring/transfer/streams
- B11: ring/transfer/xfer-control, ring/transfer/xfer-bulk, ring/transfer/xfer-interrupt, ring/transfer/xfer-isoch, hotplug/downstream-hotplug
- B12: pm/host-controller-pm, pm/port-power-management, pm/usb2-device-pm, pm/usb3-device-pm
- B13: pm/system-suspend, pm/system-resume
- B14: dbc/dbgcap, dbc/dbgtty (user-added tail)

Ordering rationale: the xhci_hcd object, ring concepts, TRB taxonomy, and context-blob machinery first (everything cites them); host-dying hoisted to B2 because every page's mandatory error section cites it (review item 7 — B1 pages carry a one-batch forward-cite, the recorded minimum); ring mechanics before contexts-that-point-at-rings; command and event machinery before init (which allocates and programs them); init/lifecycle before roothub/ports (which assume a running host); ports before transfers (hotplug's prerequisite); the three narrative pages (downstream-hotplug, system-suspend, system-resume) last in their clusters so they cite verified anchors; PM last since it exercises everything else. The B4/B5 command↔event circularity is inherent (command completions are events); each side recaps the other in one paragraph per boundary rule 12.

### Adversarial review outcome (2026-07-16)

Reviewer (fresh strong-model agent) checked ~70 anchors across all 12 groups including every v7.0-new symbol: 3 wrong (hcd-pci.c:187→191 twice; message.c:2229→2207; GET_SLOT_STATE xhci.h:399→400 — all corrected in the rows), everything else confirmed, including the FLADJ verified-negative. 22 items returned; disposition:

1. ACCEPTED — Reset Device command leg added to slot-lifecycle.md (was unowned; trb-types census cell dangled).
2. ACCEPTED — Address Device flow (setup_device/address_device/enable_device/addr-dev completion, mutex, transaction-error retry) added to slot-lifecycle.md.
3. ACCEPTED — sideband row folded into interrupters.md as a section with a recorded rule-8 exception (only in-tree consumer is vendor-gated; standalone page unwritable under the bans); restoring a standalone page is a checkpoint option.
4. ACCEPTED — segment-chaining row now names its excerpt strategy (cite the spec-revision setter + call sites; never the vendor-naming predicate body).
5. ACCEPTED — ext-caps row carries the pci-quirks.c file-set exception and the legacy-HCI-neighbor citation caution explicitly.
6. ACCEPTED — constraint-13 adjudication recorded (Scope decisions): root-hub.md and bus-suspend-resume.md carry mandatory per-generation sections + why-differs instead of sub-floor page splits.
7. ACCEPTED — lifecycle/host-dying hoisted B7→B2 (citation target of every error section).
8. ACCEPTED — HCD_USB3 carve-out: msi-msix owns, pci-probe cites; anchor corrected to hcd-pci.c:191.
9. ACCEPTED — prepare_ring owned by ring-maintenance; transfer-ring owns prepare_transfer and cites.
10. ACCEPTED — process_bulk_intr_td owned by xfer-bulk (incl. soft-retry); xfer-interrupt cites; transfer-events holds dispatch pointers only.
11. ACCEPTED — USB2 RExit/resume state machine owned by port-registers-usb2; usb2-device-pm cites via named seam.
12. ACCEPTED — ERST register programming: interrupters owns xhci_add_interrupter wholly; event-ring owns alloc_erst/set_hc_event_deq/update_erst_dequeue and cites.
13. ACCEPTED AS RESCOPE (merge declined for now) — command-ring.md keeps CRCR/config/state-values only, never walks queue_command/handle_cmd_completion; coverage-of-scope tripwire recorded: fold into command-lifecycle.md if thin at write time.
14. ACCEPTED — ep-state row folded into device-tracking.md as the two-namespaces section; rule-5 seams updated.
15. ACCEPTED — usb_hcd_pci_shutdown owned by host-shutdown; pci-probe cites.
16. ACCEPTED — Device Notification event + handle_device_notification folded into event-trb.md with DNCTRL cross-cite.
17. ACCEPTED — hub-TT bookkeeping (xhci_update_hub_device, xhci_alloc_tt_info) folded into slot-context.md; configure-endpoint cites.
18. ACCEPTED — endpoint teardown ops (xhci_endpoint_disable, xhci_free_device_endpoint_resources) folded into configure-endpoint.md.
19. ACCEPTED — configure-endpoint's Get Port Bandwidth clause notes the debugfs-consumer citation carve-out + container-context seam.
20. ACCEPTED — trb-types row states the vendor-range census wording exactly (list-with-value, no coverage).
21. ACCEPTED — all three anchor corrections applied.
22. RECORDED — no-change verdicts: 13-heading bullet sweep complete, TRB census complete for all defined types, per-ring-type and error-section mandates correctly carried, remaining cluster boundaries clean, batch order otherwise sound (B4/B5 circularity inherent).

Net effect: 57 → 55 rows; B2 grew to 6 and B5/B7 shrank to 4 each; no coverage regression (all folds carry their material into named owning sections).

## Execution & verification

- Pipeline: writer → orchestrator check per SKILL.md ("Modes") — the page is the writer's end to end (facts and prose, mechanical exit suite run, evidence persisted into the dossier); the orchestrator re-runs the checks per `guidelines/passes/03-check.md` and stamps WRITTEN → LINTED at batch checkpoints; certification happens in a separate verify campaign (`xhci-verify`, per `guidelines/passes/04-verify.md`) ON DEMAND ONLY (user decision 3).
- Execution state is NOT recorded here (SKILL.md: a spec records no execution state; state is the catalog-vs-`docs/` diff, and per-run events live in a machine-local run log). Historical note, retained because it explains the gap between the 2026-07-16 plan date and the first page: the checkpoint approved the plan but explicitly deferred generation ("don't create any page yet"), so batch B1 required a separate user go. That go was given on 2026-07-21 and the deferral in Scope decisions is spent — it gates nothing further.
- Draft posture: write everything fresh (user decision 1) — writers research from the tree alone; the reuse map is reference only.
- Per-page procedure: passes 00-03 at write time (`guidelines/passes/`); every writer brief carries this file's boundary statements (its cluster's rules plus rules 11-12), the project bans below, and the write-time cautions below.
- Project-specific writing bans (from the request, on top of Gate A): no vendor mentions (no Intel/NVIDIA/AMD/Renesas/MediaTek/TI/Qualcomm/DesignWare names anywhere — the quirks MECHANISM is documented without naming any vendor bit); no devicetree/platform-driver content; no UHCI/EHCI/OHCI mentions, not even historical; no device-specific quirk coverage; no hedging wordings; PCI-based xhci_hcd driver only; x86-64/ACPI systems assumed.
- Mandatory page features (from the request): every helper function mentioned gets a concrete usage example cited as a code block referenced from DETAILS (rules 7e/7j/7l); relevant MMIO registers folded into each page (REGISTERS is section 6 per the Subsystem Map); every page carries an error-handling section in DETAILS; USB2/USB3 divergences get per-generation pages (ports, device PM) with a why-differs explanation in each; ring-mechanism pages (segment-chaining, cycle-bit) carry per-ring-type sections; figures are structural/spatial (7g-7i) — TRB and register bitfield figures calibrate against `docs/pci/protocol/tlp/msg/` (7h), never call-graph flowcharts.
- Write-time cautions (line numbers in this file are hints — re-verify on disk): (1) FLADJ is absent from the v7.0 driver — the init page states the negative, verified per 7o; (2) "virt" naming means software mirror, not virtualization — device-tracking owns the disambiguation, every writer avoids the misreading; (3) PORTSC/PORTPMSC/PORTLI/PORTHLPMC macros live in xhci-port.h and HCS/HCC/CTX macros in xhci-caps.h at v7.0 (older docs say xhci.h — stale); (4) the kernel misspells the PORTHLPMC field `porthlmpc`; (5) allocation idioms are kzalloc_obj/kzalloc_flex at v7.0, not kzalloc(sizeof) — excerpts must match disk bytes; (6) struct xhci_protocol_caps is defined but never instantiated; (7) MSI/MSI-X setup lives in xhci-pci.c, not xhci.c/hcd-pci.c; (8) interrupters are an array of heap objects, not inline xhci_hcd fields; (9) stale comment referencing removed `resume_done[]` exists at xhci-hub.c:959 — do not cite the comment as current structure.
- semcode is required by the request for research; agents on a machine without a semcode index fall back to Grep/Read against the pinned tree and state so in the dossier.
- Save policy: pages land only under `docs/xhci/<group>/` at their catalog paths, overwriting same-slug drafts in place; the superseded top-level drafts (`overview.md`, `usb-hcd-bridge.md`) and any draft whose slug the catalog renames are removed at the batch checkpoint that ships their replacements, recorded in Status. No `SUMMARY.md`/`mkdocs.yml` edits. No git commits without an explicit user go.

## Draft reuse map — DOWNGRADED TO REFERENCE (2026-07-16 user decision 1: write everything fresh)

This section is retained as the audit record of the draft corpus (evidence for the Status CORRECTIONs, the known-defect classes, and any future round that revisits reuse). It is NOT an execution input: writers do not consult the drafts, and briefs carry no pointers into this section. The slug mapping below still governs one operational thing — which superseded draft files are deleted at which batch checkpoint (user decision 2, overwrite in place).

Corpus: the 43 files under `docs/xhci/` (see Context). Audited read-only in three slices; per-file verdicts, spot-check results, defect classes, figure dispositions, and mining pointers recorded here.

Slug mapping where the catalog renames or splits a draft topic: overview.md → core/xhci-hcd.md; usb-hcd-bridge.md → core/usb-hcd-bridge.md; init/host-init.md keeps its slug (FLADJ bullet retargeted); ring/ring-overview.md absorbs the drafts' generic-ring framing with the TRB census split out to ring/trb-types.md (new); device/device-tracking.md keeps its slug with slot-lifecycle.md, container-context.md, and ep-state.md split out (new); ring/command gains command-lifecycle.md and command-abort.md (new); interrupt/ gains sideband.md (new, optional); ring/transfer/ gains transfer-td.md and endpoint-halt-recovery.md (new); roothub/ gains port-arrays.md and bus-suspend-resume.md (new); core/ gains pci-probe.md and ext-caps.md (new); lifecycle/ gains host-dying.md (new); device/bandwidth.md → device/configure-endpoint.md (rescoped per the slice-2 quirk-gating finding). All other draft slugs map 1:1 to catalog rows.

### Slice 2: device/ + hotplug/ + ring/ + ring/command/ (14 files; audit complete, recorded 2026-07-16)

HEADLINE: staleness low at the code level, concentrated in citation apparatus. ~150 spot-checks: ZERO symbols renamed/moved/removed; drift is citation-metadata — ~6 root-cause bad anchors producing ~17 wrong links, overwhelmingly in ring/command/command-ring.md (3 completion-code macros cited ~330 lines off across 11 links; xhci_hc_died cited in the wrong FILE — real definition xhci-ring.c), plus 2 off-by-one anchor slips in doorbell.md, 1 wrong-line link in ring-maintenance.md (EP_HAS_STREAMS is xhci.h:669, not :745), and 3 factual/count errors (slot-context.md "eighteen call sites" — real count 21; endpoint-context.md unscoped "28 call sites" — real 30; command-trb.md mis-attributes the No-Op command to xhci_queue_vendor_command — that function's only caller queues a vendor-specific firmware command, and the real No-Op mechanism is trb_to_noop() in-place rewrite, never queue_command()). Dominant defects: (1) OTHER SOURCES 7n — ~54 entries, 100% banned git.kernel.org form; ~half recoverable by trailer relink (cycle-bit.md 4-for-4 — best case), rest drop to prose sha+subject; ONE FABRICATED SHA TAIL in downstream-hotplug.md (real short prefix, invented tail). (2) KERNEL DOCUMENTATION fabrication cluster: `Documentation/usb/xhci.rst` and `Documentation/driver-api/usb/hcd.rst` do not exist anywhere in tree history yet appear across device-tracking.md, doorbell.md, downstream-hotplug.md; plus one stale moved path (bulk-streams). (3) Gate A tics: ~29 anthropomorphic placement verbs (12/14 files), ~19 hollow clefts (11/14), bare-noun DETAILS headings (worst device-tracking.md 5/7); zero em-dash/boldface/banned-words/Why-How-Where anywhere. (4) Campaign bans nearly clean: DT 0, UHCI/EHCI/OHCI 0, vendor 0 real except segment-chaining.md (genuine vendor mentions + quirk content STRUCTURALLY baked in: catalog entries, a DETAILS heading, part of SUMMARY around a link-TRB quirk — the corpus's only MINE-SECTIONS-ONLY; note the underlying gate is hci_version==0x95, a spec-revision check, worth preserving as mechanism); one endpoint-interval-limit quirk paragraph in endpoint-context.md (mandatory cut, narrowly excisable); one verbatim-fidelity break where segment-chaining.md silently drops vendor names from a quoted kernel comment (laundering that broke fidelity instead of fixing scope). Depth: ~301 c-blocks, 100% correct 7l provenance, every sampled block byte-exact. Verdicts: 13 BACKBONE-REUSABLE, 1 MINE-SECTIONS-ONLY (segment-chaining.md), 0 IGNORE. Strongest: device/doorbell.md (cleanest prose + two textbook drop-in register figures) and ring/cycle-bit.md (best citation precision, zero banned content, best temporal figure in corpus, fully recoverable OTHER SOURCES). Weakest: segment-chaining.md and command-ring.md (drift cluster). Process note: one audit sub-agent disclosed a transient file accidentally written to its own /tmp scratchpad (self-corrected, pipes thereafter); no corpus/tree/skill file touched.

Per-file (line count · c-blocks · verdict · deltas):
- device/bandwidth.md (673 · 18) BACKBONE; 10/10 spot-checks exact; clean on all prose bans; OTHER SOURCES 3/3 fail (0 recoverable); one quote silently drops the vendor word from the real kernel comment (unmarked). CRITICAL SCOPE FINDING (catalog answer a): every cited symbol is defined in generic core files, BUT the entire SW bandwidth-accounting apparatus runs only under XHCI_SW_BW_CHECKING, set at exactly one call site gated to one specific 2012-era PCI device ID — dormant everywhere else; only xhci_check_bandwidth's Context-Entries fixup + Configure-Endpoint issuance and xhci_reset_bandwidth's unwind are universal. Figure 1/1 reusable — "bandwidth domains linked through field-level pointers," the single cleanest figure in the corpus. Mines: universal op slice → device/configure-endpoint.md (rescoped row); struct definitions + dormancy statement → same page's bandwidth section.
- device/device-tracking.md (557 · 22) BACKBONE; 6/6 exact; 5/7 bare-noun headings, lives/sits×2, cleft×1, hedge×1; OTHER SOURCES 4/4 fail; KERNEL DOCUMENTATION 0/3 correct (two fabricated paths + one stale). Figure reusable (DCBAA→ctx tree) but one cell contains placeholder text "(DEMO)" — fix. Mines: struct catalog + CSZ sizing table (verified against real alloc math) → device-tracking + container-context rewrites; SLOT_STATE catalog → slot-lifecycle.
- device/doorbell.md (443 · 15) BACKBONE, cleanest prose in corpus (0/8 bad headings); 4 exact + 2 anchor-on-comment slips (xhci_hcd at :1501 not :1500; EP_GETTING_NO_STREAMS :671 not :670); lives×3, cleft×1, one catalog↔DETAILS gap (xhci_ring_device never discussed); OTHER SOURCES 4/4 fail; KERNEL DOC 1/2 (xhci.rst fabricated). Figures 2/2 textbook 7h, drop-in ready (doorbell DWORD grid; array address map). Mines: whole page → device/doorbell rewrite backbone.
- device/endpoint-context.md (712 · 20) BACKBONE; 6/6 exact; ONE REAL QUIRK-BAN HIT: dedicated paragraph + code block on endpoint-interval-limit quirk flags — mandatory cut; parity gap (two cataloged accessors never in DETAILS; the mult() gloss omits a third vendor-gated branch — state generically); "28 call sites" unscoped (real 30); OTHER SOURCES 4/4 fail (3 recoverable). Figure reusable (ep_ctx DWORD grid). Mines: REGISTERS + figure → endpoint-context rewrite; halt-recovery section → endpoint-halt-recovery.
- device/input-context.md (562 · 21) BACKBONE, cleanest of trio; 6/6 exact + one quantifier verified exactly right (14/14); clefts×4 (file's tic); OTHER SOURCES 4/4 fail (0 recoverable). Figures: container layout reusable (answers the container question visually); add_flags grid needs 7h style pass (placeholder grid + text legend → L-connectors). Mines: layout figure → container-context page seed; flag tables + Address/Configure DETAILS → input-context rewrite.
- device/slot-context.md (603 · 18) BACKBONE; 6/6 exact; "eighteen call sites" undercount (real 21); one claimed-but-unmarked elision; sitting×1; OTHER SOURCES 4/4 fail (0 recoverable). Figure reusable — slot_ctx DWORD grid (DW0-DW3), clean 7h match, best direct-reuse for slot-context. Mines: DW tables + figure → slot-context rewrite; setup_addressable walk → input-context/hotplug cites.
- hotplug/downstream-hotplug.md (551 · 26) BACKBONE; 6/6 core + ~20 incidental exact; FABRICATED SHA TAIL in one OTHER SOURCES entry; KERNEL DOC 2/4 (same xhci.rst/hcd.rst fabrications); negative×1, lives×1, bad heading×1, one catalog↔DETAILS gap (xhci_check_args). Figure borderline: declared 3-lane swimlane collapses into a linear stage pipeline restating SUMMARY — substantial redraw into a true persistent swimlane. Mines: Stage 1-4 walkthroughs (full verified code) → downstream-hotplug rewrite backbone; stage→command→slot-state table reusable as-is.
- ring/ring-overview.md (619 · 22) BACKBONE; 6+/6 exact (ring_alloc/set_link_trb bodies verbatim); cleft×1, lives×3; OTHER SOURCES 4/4 fail (0 recoverable). Figures 2/2 reusable (DW3 control-dword bitfield; segments-ring hybrid). HEAVY 3-way duplication with ring-memory/ring-maintenance on construction/enqueue/growth — rewrite: overview owns the outline, siblings own depth (matches catalog boundaries). Mines: outline + type enum → ring-overview rewrite.
- ring/ring-memory.md (712 · 26) BACKBONE, deepest DMA-pool + stream-radix treatment; 6/6 exact; clefts×2, lives×1; STANDOUT: a cataloged chain-quirk helper + a verbatim excerpt reproducing a PCI-gated overfetch-quirk branch — elide/excise on reuse; OTHER SOURCES 4/4 fail (0 recoverable). Figure reusable — most detailed segment-chain hybrid (concrete DMA addresses). Mines: DMA-pool sizing (unique) + radix quartet (deepest) + teardown/unwind (unique) → ring-memory rewrite backbone.
- ring/ring-maintenance.md (592 · 20) BACKBONE; 5/6 + 1 genuine wrong-line link (EP_HAS_STREAMS xhci.h:669); clefts×3, lives×3; 2 real coverage gaps (link_rings' cycle-normalization block absent from its own excerpt; inc_deq caller list omits xhci_dequeue_td); OTHER SOURCES 4/4 fail (2 recoverable). Figure — enqueue-wrap before/after pair, clearest temporal ring figure in corpus. Mines: inc_deq (unique) + virt_to_dma/trb_in_td (unique) + fullest ring-growth treatment → ring-maintenance/ring-memory rewrites; wrap figure → cycle-bit.
- ring/segment-chaining.md (520 · 21) MINE-SECTIONS-ONLY (only one in corpus): quirk/vendor content structurally baked in (catalog bullets, a DETAILS heading, SUMMARY fragment, 100% of OTHER SOURCES built around the link-TRB quirk; genuine vendor names; plus the fidelity-breaking laundered comment). ~15 checks 0 drift otherwise. Figure reusable after 2-glyph fix (non-canonical arrows). Mines: set_link_trb/initialize_ring_segments DETAILS → segment-chaining rewrite (generic mechanism + spec-revision nuance, no vendor names); drop the quirk sections/bullets/sources entirely.
- ring/cycle-bit.md (600 · 21) BACKBONE, best citation precision in corpus; ~20/20 exact (confirms LINK_TOGGLE/TRB_TC "two spellings, one bit"; speculative TRB_TOGGLE name confirmed absent — drafts never invented it); clefts×2, lives×3, 3/8 bad headings, reverse parity gap (inc_deq DETAILS but no catalog row), one figure-legend abbreviation matches no real macro; OTHER SOURCES 4/4 wrong form but ALL FOUR recoverable — best relink case. Figures 3/3 reusable: "cycle bit ownership across a wrap" is the best figure in the corpus; CRCR + ep-deq bitfields need minor L-connector pass. Mines: whole page → cycle-bit rewrite backbone; wmb-before-cycle ordering → same page; dequeue-resync → endpoint-halt-recovery.
- ring/command/command-ring.md (745 · 27) BACKBONE; struct/macro/queue/doorbell cites exact BUT worst drift cluster in corpus: 3 completion-code macros ~330 lines off across 11 links; xhci_hc_died in wrong file; halt/handshake anchored on comments; one excerpt silently skips the aborted-command short-circuit branch; arm×1, cleft×1, lives×2, bad heading×1; OTHER SOURCES 4/4 fail (0 recoverable). Figures: 2-lane command-lifecycle swimlane reusable (best on page); CRCR bitfield needs style unification. Mines: command-object/ring-state catalog → command-ring + command-lifecycle rewrites (prefer command-trb.md's correct macro cites); timeout/abort walk → command-abort.
- ring/command/command-trb.md (712 · 24) BACKBONE; 25+/25 line-cites exact (completion codes correct HERE — cross-file inconsistency with sibling); ONE REAL FACTUAL ERROR: No-Op command attributed to the vendor-command queuer (real caller queues a vendor firmware command; real No-Op mechanism is trb_to_noop in-place, never queue_command) — fix in rewrite, evidence trail is vendor territory so state generically; label-colon×1, cleft×1, sits/lives×3; OTHER SOURCES 4/4 fail (1 recoverable). Figures: "four dwords" listing is not a diagram (prose/table it); control-dword bitfield has measured ruler defect (16 vs 30 vs 32 columns — rebuild per 7h). Mines: TRB type-id + completion-code catalogs → command-trb + trb-types rewrites (fix No-Op row first).

Catalog answers from slice 2: (a) bandwidth machinery: structs generic, apparatus quirk-dormant (see HEADLINE finding) → catalog row RESCOPED to device/configure-endpoint.md (amendment recorded in Status). (b) container-context: covered as background in 4 files, accurately (CSZ/CTX_SIZE line-verified), BUT alloc/free lifecycle functions never named anywhere in the corpus — confirms the curated container-context.md row fills a real gap; terminology note: no literal `csz` field exists in the driver — HCCPARAMS1 bit 2 via HCC_64BYTE_CONTEXT/CTX_SIZE() only.

### Slice 1: overview + usb-hcd-bridge + init/ + lifecycle/ + roothub/ + ports/ (12 files; audit complete, recorded 2026-07-16)

HEADLINE: staleness effectively 0% across ~150+ symbol/file:line spot-checks — every function, struct, macro, and bit-position citation resolved to the exact cited line; no renamed or moved symbols anywhere in the 12 files. The corpus is contemporaneous and code-accurate; the real defects sit one layer up: (1) corpus-wide OTHER SOURCES failure — all 49 entries use the banned `git.kernel.org/.../commit/?id=` form (7n), and roughly half the cited commits have no Link: trailer at all, so per 7n they get no OTHER SOURCES entry regardless of format; (2) a narrow band of higher-severity provenance problems — one FABRICATED KERNEL DOCUMENTATION citation (`Documentation/usb/xhci.rst` in port-hotplug.md; never existed in repo history), one vendor-quirk LAUNDERING (host-reset.md presents `xhci_zero_64b_regs()` as generic IOMMU handling; the real gate `XHCI_ZERO_64B_REGS` is set only for two specific vendor device IDs, and the excerpt starts one line after a 14-line comment naming the vendor, unmarked), one silent unmarked line-drop in a usb.c excerpt (usb-bus-spawn.md — the dropped line is a devicetree call), two positionally-shifted (phantom-blank-line) blocks in port-event-handling.md, and two verbatim vendor-codename quirk comments reproduced in host-shutdown.md (vendor+quirk ban hit); (3) a fixable style layer — "arm" for switch-case ~16 hits concentrated in ports/ (port-event-handling.md correctly says "branch" — proof of the fix), anthropomorphic "lives/sits in" ~18-20, hollow-cleft "is what makes/lets" ~9, ~60 unlinked peripheral `USB_PORT_STAT_*`/`USB_PORT_FEAT_*` macros in ports/ (7m). Vendor/DT/legacy-HCI bleed otherwise confined to 4 of 12 files; UHCI/EHCI/OHCI mentions 100% absent. Figures: 21 total, 17 reusable-structural, 4 banned — and all 4 banned ones are intro/opening flowcharts (host-init, host-shutdown, port-event-handling, port-hotplug): every draft intro flowchart gets redrawn, downstream figures are generally fine. Depth: genuinely source-grounded — 248 c-blocks across ~7,700 lines, majority provenance-tagged and byte-verified. Strongest: roothub/root-hub.md (clean on all bans, field-level citation precision, best figure in slice), ports/port-registers-usb3.md, init/dcbaa-scratchpad.md. Weakest: ports/port-hotplug.md (fabricated citation), lifecycle/host-reset.md (quirk laundering). Verdicts: 10 BACKBONE-REUSABLE, 2 MINE-SECTIONS-ONLY, 0 IGNORE.

Per-file (line count · c-blocks · verdict · deltas):
- overview.md (530 · 16) BACKBONE; 8/8 spot-checks exact (incl. hand-summed port_regs offset 0x400, MAX_HC_PORTS/INTRS); defects: 1 vendor spec-PDF link in OTHER SOURCES, 5/5 OTHER SOURCES fail 7n, 3 "lives in". Figures 2/2 reusable (BAR0 address map; HCSPARAMS1 DWORD grid — best in file). Mines: struct field groups → core/xhci-hcd; register tables → same; dead-controller section → lifecycle/host-dying.
- usb-hcd-bridge.md (940 · 35, densest) BACKBONE; 6/6 exact (hc_driver flags values, DB_VALUE, shared-hcd body); 0/35 provenance defects; OTHER SOURCES 4/4 fail 7n AND none of the 4 commits has any Link: trailer; "contract"×1, "canonical"×1, is-what×3, lives-in×3 (one inside the intro figure — rule 7 binds figure text). Figures 2/2 reusable (two-bus pointer topology needs one-word fix; doorbell DWORD grid clean). Mines: hc_driver template/override walk → core/usb-hcd-bridge; two-roothub construction → core/pci-probe + init/usb-bus-spawn; died/unwind → lifecycle/host-dying.
- init/host-init.md (937 · 22) BACKBONE; 6/6 exact — notably xhci_reset()'s "..." elisions fall exactly on two real vendor-quirk branches (good discipline); 0/22 provenance defects; OTHER SOURCES 4/4 fail 7n (3 have real unused lore trailers); is-what×1. Figures: intro init-sequence flowchart BANNED (redraw); USBCMD + USBSTS bitfields reusable. Mines: op-reg programming quartet + failure ladder → init/host-init rewrite backbone.
- init/dcbaa-scratchpad.md (520 · 20) BACKBONE; 5/5 exact incl. full xhci_mem_init body byte-match; hedging×1, "contract"×1, vendor spec-PDF link×1, OTHER SOURCES 5/5 fail 7n; "wants none"×1. Figures 2/2 reusable (DCBAA/scratchpad address map — best in file; HCSPARAMS2 split-field). Mines: whole page is the rewrite backbone; alloc-failure goto ladder → error section.
- init/usb-bus-spawn.md (744 · 26) BACKBONE; 4/5 exact + 1 REAL DRIFT: usb_alloc_dev() excerpt silently drops the devicetree line (usb.c:698) with no elision mark — refetch verbatim and mark elisions; OTHER SOURCES 3/3 fail 7n (2 commits have no trailer); arm×1, negative×1. Figures 2/2 reusable (two-bus ownership tree — best in file; CONFIG bits). Mines: whole page backbone; HCD_FLAG_DEFER_RH_REGISTER section → roothub registration ordering.
- lifecycle/host-reset.md (520 · 14) MINE-SECTIONS-ONLY; halt/quiesce/reset/handshake mechanics byte-exact, BUT: xhci_zero_64b_regs subsection launders a two-device vendor quirk as generic IOMMU behavior (prose claim + excerpt cut one line below the vendor-naming comment, unmarked) — cut or rewrite that subsection under the quirk-exclusion rule; intro halt/reset flowchart BANNED; USBCMD/USBSTS figures reusable (USBSTS best in file); OTHER SOURCES 4/4 fail 7n. Mines: quiesce/halt/start/handshake DETAILS → lifecycle/host-reset rewrite; state-flags section → host-dying.
- lifecycle/host-shutdown.md (503 · 14) BACKBONE; 4/4 exact (shutdown/stop bodies verbatim, hook wiring line confirmed); REAL vendor+quirk hit: two verbatim kernel comments naming vendor platform codenames reproduced at lines 164-165/215 — elide on reuse; OTHER SOURCES 4/4 fail 7n (all 4 have real unused lore trailers); is-what×1. Figure 1/1 BANNED (linear call chain). Mines: xhci_stop+xhci_mem_cleanup walk → lifecycle/host-shutdown rewrite; s3 fields → pm/host-controller-pm.
- roothub/root-hub.md (638 · 20) BACKBONE, cleanest in slice; 6/6 exact incl. per-field line numbers (usb2_rhub/usb3_rhub/hw_ports/port_caps/max_ports); zero vendor/DT/legacy/quirk; OTHER SOURCES 4/4 fail 7n (2 commits trailer-less, 1 non-lore trailer); arm×3, is-what×1, kcalloc_node unlinked×2. Figure 1/1 reusable — "one connector, two rhub ports" mapping, BEST FIGURE IN SLICE, carry forward as-is. Mines: struct tour → roothub/port-arrays + root-hub rewrites; port-array construction walk → port-arrays; hub_control/status_data → root-hub.
- ports/port-registers-usb2.md (556 · 17) BACKBONE; 5/5 exact (~25 bit macros bit-position-verified; RO/RWS/RW1CS masks bit-for-bit); clean on all campaign bans; OTHER SOURCES 4/4 fail 7n (3 trailer-less); lives-in×1, soft superlative×1, ~6 distinct unlinked USB-core macros. Figure: PORTSC+PORTPMSC bit layouts reusable (note: diagram shows a USB3-only bit the prose disclaims — fix on reuse). Mines: PORTSC table → both port-register rewrites; LPM walkthrough → pm/usb2-device-pm; RW1C/neutral-mask discussion duplicated in usb3 file — state once, cite.
- ports/port-registers-usb3.md (609 · 22) BACKBONE; 6/6 exact (LPM-timeout full bodies verbatim, correctly citing the real implementation not the !CONFIG_PM stub; all 13 PLS macros exact); clean on bans; OTHER SOURCES 4/4 fail 7n (3 trailer-less, 1 real trailer ignored); arm×7 (worst in slice), "contract"×1, negative×1, ~21 bare macro occurrences. Figure: PORTSC/PORTPMSC/PORTLI layout — among best in slice, reusable as-is. Mines: bit-role tables → port-registers-usb3 rewrite; LPM walkthrough → pm/usb3-device-pm; warm-reset/CAS material → dedup with port-hotplug.
- ports/port-event-handling.md (620 · 14) BACKBONE; 5 exact + 2 blocks with phantom-blank-line positional shift (refetch); "only caller" claim verified true; zero arm-metaphor (uses "branch" — the model fix); OTHER SOURCES 4/4 fail 7n (all 4 trailer-less); lives/sits×2, negative×1, soft superlative×1, 1 non-declarative heading. Figures: PSC-event TRB bitfield reusable; intro event-flow figure BANNED. Mines: handle_port_status walkthrough → port-event-handling rewrite; TRB figure → interrupt/event-trb.
- ports/port-hotplug.md (589 · 28) MINE-SECTIONS-ONLY; 6/6 code checks exact — best verbatim record in slice — BUT the KERNEL DOCUMENTATION entry cites a file that never existed in repo history (FABRICATED) — re-derive all reference sections from scratch, never copy-forward; OTHER SOURCES 4/4 fail 7n (all trailer-less); arm×5, lives/live×2, ~20 bare macro occurrences, 1 non-declarative heading. Figure 1/1 BANNED (intro sequence chain). Mines: debounce→reset→alloc_dev DETAILS walk (fully verified) → ports/port-hotplug rewrite backbone; warm-reset retry → dedup with port-registers-usb3.

### Slice 3: interrupt/ + ring/transfer/ + pm/ (17 files; audit complete, recorded 2026-07-16)

HEADLINE: staleness ~6% (6 of ~100 named spot-checks), every drift confined to pm/ and all of them anchor/line-pointer or fidelity slips, none rewriting behavior: usb_hcd definition line (hcd.h:68 not :88), PMSG_AUTO_SUSPEND (pm.h:568 not :571), HCD_FLAG_HW_ACCESSIBLE (hcd.h:107 not :141), an undercounted -EBUSY enumeration in system-suspend.md ("two abort paths"; tree has three), readl_poll_timeout line off by 174, and silently ASCII-normalized curly quotes in a quoted kernel comment. interrupt/ (22 checks) and ring/transfer/ (~42 checks) returned ZERO drift. Dominant defect: 7n — 66/66 OTHER SOURCES entries fail corpus-wide (banned git.kernel.org form); 20 have recoverable lore Link: trailers (URL swap), 46 cite 2009-2018 commits with no trailer (delete the entry; cite sha+subject in prose at most). One OTHER SOURCES SHA in host-controller-pm.md is FABRICATED (diverges from the real commit after the 28th hex digit). Style totals: anthropomorphic placement verbs ≈34; arm-metaphor ≈29 (concentrated in pm/ ≈17, worst usb3-device-pm.md ×6 and port-power-management.md ×5; xfer-interrupt.md ×6); negative constructions ≈10; hollow clefts ≈6; non-declarative DETAILS headings ≈4 (three are the same closing "error handling" bare-noun pattern in xfer files); hedging ≈7; boldface/em-dash/label-colon ≈0. Campaign bans nearly clean in prose: single genuine hit — xfer-bulk.md explains a named SG-cache quirk flag in flowing prose (rework to mechanism-only); vendor code elsewhere only inside verbatim excerpts or properly elided (one whole cataloged function, xhci_check_tier_policy, is pure vendor logic and correctly never shown — leaving a Gate-B coverage gap to resolve in rewrite, stated generically). Zero UHCI/EHCI/OHCI anywhere. Depth: 377 c-blocks, 100% carrying valid 7l provenance; ~140 diffed byte-exact; BUT xfer-bulk/control/interrupt/isoch run 0.53-0.76 c-blocks per catalog entry (below the 1.0 floor — rewrites must deepen), and usb3-device-pm.md has two confirmed catalog↔DETAILS parity gaps. Verdicts: 17/17 BACKBONE-REUSABLE. Strongest: interrupters.md (zero drift; the interrupters[] fan-out figure is the richest in the corpus; only file whose OTHER SOURCES are all URL-swap-fixable) and system-resume.md (richest DETAILS, one drift, one style defect). Weakest: usb3-device-pm.md (parity gaps + worst arm count), transfer-ring.md (densest anthropomorphic cluster incl. its opening sentence and an H3), msi-msix.md (highest defect-per-line; its only diagram is one-third banned call-chain, redraw that panel).

Per-file (line count · c-blocks · verdict · deltas):
- interrupt/event-ring.md (726 · 23) BACKBONE; 6/6 exact (half-segment ERDP flush verbatim); lives/sits×3; OTHER SOURCES 4/4 fail (2 recoverable). Figures 2/2 reusable (ERST→segments pointer topology; ERDP low-bits register). Mines: whole page → interrupt/event-ring rewrite backbone.
- interrupt/event-trb.md (756 · 23) BACKBONE; 5/5 exact (comp-code values verified); sits/lives×2, negative×2, is-what×1; OTHER SOURCES 4/4 fail (1 recoverable). Figures 3/3 reusable (generic-TRB 4-dword; status dword; control dword). Mines: TRB/comp-code tables → ring/trb-types + interrupt/event-trb.
- interrupt/interrupters.md (667 · 24) BACKBONE, STRONGEST IN CORPUS; 5/5 exact (sideband caller confirmed live); lives-in×1, hedge×1 borderline; OTHER SOURCES 4/4 wrong form but ALL 4 recoverable by URL swap. Figures 3/3 reusable — interrupters[] fan-out is the single richest figure in the corpus; IMAN/IMOD clean. Mines: object-model catalog + fan-out figure → interrupt/interrupters rewrite; ip_autoclear overlap with msi-msix → interrupters owns.
- interrupt/msi-msix.md (504 · 17) BACKBONE (weakest of group); 6/6 exact incl. confirmed absence of speculative xhci_setup_msi/msix names; lives/wants×3 (one is the rule doc's textbook example), is-what×2, negative×1 INSIDE the figure; OTHER SOURCES 3/3 fail (2 recoverable). Figure 1: bottom two-thirds (vector→interrupter→event-ring lanes) reusable, top third banned call-chain — redraw panel; bespoke "··" connector not in approved set. Mines: vector-allocation-policy DETAILS → interrupt/msi-msix rewrite.
- ring/transfer/streams.md (749 · 27) BACKBONE; 6/6 exact; "is deliberate:"×1 (named-banned), lives×1, negative×2, hedge×1, non-declarative heading×1; OTHER SOURCES 4/4 fail (1 recoverable). Figure 1/1 reusable (deq→Stream Context Array→per-stream rings — strongest of trio). Mines: whole page → ring/transfer/streams rewrite.
- ring/transfer/transfer-events.md (769 · 29) BACKBONE, cleanest of trio; 6/6 exact (14 comp-code values verified); arm×2, sits×2, non-declarative heading×1; OTHER SOURCES 4/4 fail (3 recoverable — clearest URL-swap case). Figure 1/1 BANNED (linear chain below the 3-decision bar; small struct-field top box salvageable). Mines: decode/processor/halted catalog → transfer-events rewrite backbone.
- ring/transfer/transfer-ring.md (746 · 25) BACKBONE (weakest of trio on prose); 6/6 exact; lives-on×5 incl. opening sentence and an H3 heading, negative×1; OTHER SOURCES 4/4 fail (0 recoverable — all four predate trailers; delete). Figure 1/1 BANNED (URB→TD→doorbell→event chain; middle TRB-ring row with start/end braces is a salvageable fragment). Mines: ring/TD/urb_priv catalog + prepare_ring/prepare_transfer walk → transfer-ring + transfer-td rewrites.
- ring/transfer/xfer-bulk.md (649 · 22) BACKBONE; 6/6 exact (count_trbs body verbatim); THE one prose quirk-ban hit (named SG-cache quirk flag explained in prose — rework mechanism-only); vendor only in-excerpt; arm×1, lives×3, hedge×1; OTHER SOURCES 4/4 fail (0 recoverable). Figures: sg-list→TRB fan-out reusable (trim call-chain tail); Normal-TRB dword clean. Mines: TRB-counting/64KB/bounce math → transfer-td; bulk specifics → xfer-bulk rewrite; shared STALL narrative → endpoint-halt-recovery owns.
- ring/transfer/xfer-control.md (625 · 26) BACKBONE; 6/6 exact; is-what×1, arm×1, sits×5 worst of four incl. one inside the figure; OTHER SOURCES 4/4 fail (0 recoverable). Figures: 3-TRB control-TD diagram with direction-rules truth table reusable (trim tail); Setup-TRB control dword clean. Mines: stage sequencing + direction-reversal rule (unique) → xfer-control rewrite; duplicated STALL narrative → endpoint-halt-recovery.
- ring/transfer/xfer-interrupt.md (566 · 17) BACKBONE, thinnest of four (correctly defers to bulk); 6/6 exact (interval decoder chain verified); arm×6 WORST SINGLE FILE, hedge×1, negative×1; OTHER SOURCES 4/4 fail (0 recoverable). Figures: interval-on-ep diagram reusable (trim tail); ep_info/tx_info dwords clean (feeds device/endpoint-context too). Mines: interval decoder chain → xfer-interrupt rewrite + endpoint-context cite.
- ring/transfer/xfer-isoch.md (710 · 23) BACKBONE, strongest of four; 6/6 exact (frame-window math verbatim; AMD PLL branch properly elided); arm×2, negative×2; OTHER SOURCES 4/4 fail (0 recoverable). Figures: URB→N-TDs fan-out reusable (trim tail); Isoch-TRB control dword — richest single-register figure of the four. Mines: SIA/frame-ID math + burst encoding (unique) → xfer-isoch rewrite; error_mid_td deferred giveback → transfer-events section.
- pm/host-controller-pm.md (588 · 18) BACKBONE; 4/6 + 2 anchor drifts (usb_hcd hcd.h:68; PMSG_AUTO_SUSPEND pm.h:568); 18/18 blocks verbatim; one OTHER SOURCES SHA FABRICATED; OTHER SOURCES 4/4 fail (2 recoverable); hedge×1. Figures: USBCMD + USBSTS bitfields reusable; opener dense — redraw or drop to prose. Mines: suspend/resume/s3 catalog → host-controller-pm rewrite; PCI-hook chain duplicated in system-resume — own once.
- pm/port-power-management.md (636 · 26) BACKBONE; 0/8 drift; "contract"×1, arm×5, lives×2, is-what×1; OTHER SOURCES 4/4 fail (0 recoverable). Figures 4/4 reusable (PP, PLS, HCCPARAMS1 bitfields; U0-U3 ladder — legitimate 7i state figure, drawn horizontal vs canonical vertical). Mines: PP/PLS catalog + ladder → port-power-management rewrite; bus_suspend material → roothub/bus-suspend-resume owns.
- pm/system-resume.md (704 · 20) BACKBONE, strongest of six; 5/6 + 1 anchor drift (HCD_FLAG_HW_ACCESSIBLE hcd.h:107); sits×1 only; OTHER SOURCES 4/4 fail (2 recoverable). Figures 4/4: three bitfields reusable; opener defensible (real two-stage ordering guarantee) but dense. Mines: bus_resume per-speed walk + 3-way error section → system-resume rewrite backbone.
- pm/system-suspend.md (522 · 15) BACKBONE, cleanest of six; 4/5 + 1 enumeration drift (three -EBUSY paths, not two — the pre-loop wake-race check never shown); all 15 blocks verbatim w/ correctly-disclosed elisions (two vendor workarounds properly hidden); hedge×1, lives×1, arm×1; OTHER SOURCES 4/4 fail (2 recoverable). Figures: opener BANNED (linear chain restating prose); PORTSC wake-bits + USBCMD bitfields reusable. Mines: two-pass bus_suspend algorithm → roothub/bus-suspend-resume + system-suspend rewrites.
- pm/usb2-device-pm.md (640 · 20) BACKBONE; 3/5 + 2 fidelity drifts (readl_poll_timeout iopoll.h:227; curly quotes normalized); arm×4, lives×2+3 borderline, negative-in-heading×1; OTHER SOURCES 4/4 fail (1 recoverable); quirk correctly elided. Figures 2/2 reusable (U0/L1/L2 transition + PORTPMSC legend; PORTPMSC bitfield — strongest in file). Mines: PORTPMSC/PORTHLPMC REGISTERS + HIRD/BESL walk → usb2-device-pm rewrite; register layouts stay in ports/port-registers-usb2 per boundary.
- pm/usb3-device-pm.md (734 · 22) BACKBONE, weakest of six on completeness; 0/6 location drift BUT 2 confirmed catalog↔DETAILS parity gaps (a cataloged function whose real body is pure vendor logic — never shown; a helper cited 5× never excerpted) + 1 undisclosed dropped guard in the BOS excerpt; arm×6 CORPUS-WORST, soft cross-page reference evading the .md-link grep; OTHER SOURCES 3/3 fail (0 recoverable). Figures 4/4 reusable (U0/U1/U2/U3 graph with back-edges — strongest in file; two PORTPMSC timeout bitfields; HCSPARAMS3). Mines: U1/U2 timeout pipeline + sysfs catalog → usb3-device-pm rewrite; resolve the two parity gaps generically (state the policy check's role without naming vendors).

Catalog answers from slice 3: (a) streams machinery confirmed generic-and-current (hc_driver-inherited by every glue; live consumers uas/devio; recent commits) — the [curated] streams row stands; (b) msi-msix draft's location story confirmed exact at v7.0 (xhci_try_enable_msi/xhci-pci.c:143 from xhci_pci_run; hcd-pci HCD_USB3 skip; speculative names confirmed absent) — the msi-msix row's anchors stand.

### Write-time consequences (all slices so far)

1. OTHER SOURCES: rebuild from scratch per 7n on every page — never copy a draft's reference sections forward (one fabricated doc path, one fabricated SHA found). Where a cited commit has a real lore Link: trailer, swap in; where none exists, no entry.
2. Figures: reuse the structural ones (register bitfields, pointer topologies, fan-outs, state ladders — 40+ identified above) after 7g-7i style conversion; EVERY intro/opening flowchart is redrawn as prose + structural figure (7 banned figures, all openers).
3. Vendor hygiene on reuse: elide the vendor-comment reproductions (host-shutdown), rewrite the laundered-quirk subsection (host-reset), mechanism-only rework of the SG-cache-quirk prose (xfer-bulk), keep the properly-elided pattern everywhere else.
4. Refetch every excerpt from disk (byte-compare per 7e/7l); known bad spots: usb-bus-spawn's unmarked line-drop, port-event-handling's phantom blank lines, usb2-device-pm's normalized quotes, usb3-device-pm's dropped guard.
5. Style sweep priorities measured from the corpus: arm-metaphor (~45 genuine hits, worst in ports/ and pm/), anthropomorphic placement verbs (~52), hollow clefts (~15), bare USB-core macros (~80 occurrences — 7m linking sweep), non-declarative error-handling headings in xfer files.
6. Depth: xfer-* pages and usb3-device-pm rewrites must deepen (c-block ratios 0.53-0.76 vs the 1.0 floor); usb3-device-pm's two parity gaps are resolved generically.
7. KERNEL DOCUMENTATION: never copy a draft's KERNEL DOCUMENTATION section — fabricated paths (`Documentation/usb/xhci.rst`, `Documentation/driver-api/usb/hcd.rst`) recur across four files; derive entries from the tree's real Documentation/ contents only.
8. Command-cluster corrections for writers: refetch every completion-code macro citation (command-ring.md's are ~330 lines off; command-trb.md's are correct); xhci_hc_died is defined in xhci-ring.c; the No-Op command TRB is produced by trb_to_noop() in-place rewriting, not by the vendor-command queue helper — fix the draft's table.
9. Known micro-defects to not inherit: device-tracking figure's "(DEMO)" placeholder cell; endpoint-context's interval-limit quirk paragraph (cut); ring-memory's overfetch-quirk excerpt branch (elide); segment-chaining's quirk-built sections (drop; keep the spec-revision nuance generically); doorbell.md's two anchor-on-comment slips; ring-maintenance's EP_HAS_STREAMS wrong-line link and its two coverage gaps (link_rings cycle normalization; inc_deq's third caller xhci_dequeue_td); slot-context "eighteen call sites" (21) and endpoint-context "28 call sites" (30 unscoped) miscounts.
