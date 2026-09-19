# USB4 knowledge-base campaign: plan

> Campaign spec (SKILL.md, "The three artifacts and the two states"): the committed, execution-free specification of the `usb4` campaign. Run events live in the machine-local run log `progress/usb4/log.md`; per-page pipeline state is derived (catalog vs `docs/usb4/`). Structure per `guidelines/campaign.md`; `campaigns/xhci.md` is the shape this file imitates.

## Context

Campaign short name: `usb4`. Campaign file: `campaigns/usb4.md`; workspace directory: `progress/usb4/` (run log, worksheets, agent intermediates; nothing outside it). Name collision check on 2026-09-04: no `campaigns/usb4.md` and no `progress/usb4/` existed.

Machine-portability convention (a hard requirement of the skill): this file hardcodes no machine-specific information. Two roots anchor every path:

- `SKILL_DIR`: the kernel-glossary skill root, the directory holding `SKILL.md`; this file lives at `SKILL_DIR/campaigns/usb4.md`. Bare relative paths in this file (`docs/...`, `guidelines/...`, `progress/...`) resolve against SKILL_DIR.
- `TREE_ROOT`: the Linux kernel checkout that contains the skill at `.claude/skills/kernel-glossary-skill`; kernel source paths (`drivers/thunderbolt/...`) resolve against TREE_ROOT. TREE_ROOT is identified by pin, never by path: at TREE_ROOT, `git describe --tags` prints `v7.2` and `git rev-parse HEAD` prints `8d3ae59288f1e7d58d76558a6ee96d533bc5019f`. A resuming agent on any machine verifies both before trusting the tree.

Sub-agent briefs are composed at dispatch time and carry absolute paths resolved on the dispatching machine (per SKILL.md); this file never does.

Request source: `prompt.md` at TREE_ROOT (untracked; may be absent on other machines, so the Scope decisions section below carries every load-bearing constraint verbatim and this file stands alone). The request: fine-grained USB4 documentation focused "not only on the common USB4 concepts (not vendor-specific implementation), but more importantly how Linux kernel internally tracking/representing some of the major USB4 constructs", with a 13-heading topic list the prompt calls "very rough" and a standing mandate to "curate new pages where you see fit". The session instruction accompanying the request: "read prompt.md and plan a deep and thorough usb4 campaign. Note that pages in kernel-glossary-devel/ are based in 7.0 kernel while the tree we're at is 7.2. Be very careful when reusing those pages. Curate topics where needed."

Documented tree: tag `v7.2`, commit `8d3ae59288f1e7d58d76558a6ee96d533bc5019f` ("Linux 7.2", 2026-08-16). semcode index complete at that commit (verified 2026-09-04: `indexing_status` reports Completed at 8d3ae592). elixir.bootlin.com carries the tag (verified 2026-09-04); all Elixir links use `https://elixir.bootlin.com/linux/v7.2/source/...`. Subsystem Map entry USB4 (`guidelines/subsystems.md`): dir `usb4`, tag `usb4`, kernel_paths `drivers/thunderbolt/` + `include/linux/thunderbolt.h`, spec "USB4 Specification, Thunderbolt 3/4 Specification", section6_heading REGISTERS. Seams cited where the subsystem meets them, never documented beyond the call boundary: the PCI core (`drivers/pci/`, the tunneled PCIe hotplug handled by pciehp), the DRM DP tunnel consumer (`drivers/gpu/drm/display/drm_dp_tunnel.c`, docs/dp territory), the network service driver (`drivers/net/thunderbolt/`), ACPI core (`drivers/acpi/`), the device core and PM core.

Kernel source at the documented version: 34 files, 42,848 lines under `drivers/thunderbolt/` plus `include/linux/thunderbolt.h`. Build gates (`drivers/thunderbolt/Kconfig`, `Makefile`): `CONFIG_USB4` (the `thunderbolt` module: nhi, ctl, tb, switch, cap, pci, path, tunnel, eeprom, domain, dma_port, icm, property, xdomain, lc, tmu, usb4, usb4_port, nvm, retimer, quirks, clx); `acpi.o` under `CONFIG_ACPI`; `debugfs.o` under `CONFIG_DEBUG_FS`; `configfs.o` under `CONFIG_USB4_CONFIGFS`; `test.o` under `CONFIG_USB4_KUNIT_TEST`; the separate modules `thunderbolt_dma_test` (`CONFIG_USB4_DMA_TEST`) and `thunderbolt_stream` (`CONFIG_USB4_STREAM`, new at v7.2). Write-visible debugfs knobs `CONFIG_USB4_DEBUGFS_WRITE` and `CONFIG_USB4_DEBUGFS_MARGINING`.

Version delta that motivates the campaign (v7.0 → v7.2 over `drivers/thunderbolt/` + `include/linux/thunderbolt.h`: 31 files changed, 3,658 insertions, 974 deletions, 63 commits): the NHI driver was split (the common ring/NHI code stays in `nhi.c`; the PCI driver moved to the new `pci.c` as `nhi_pci_*`, `nhi_ops.c` was deleted, `pci_device` moved out of `struct tb_nhi`, `nhi->ops` became mandatory); `stream.c` (USB4STREAM, 1,698 lines) and `configfs.c` were added; `tb_ring_flush()`, `tb_ring_size()`, `tb_ring_frame_size()` and per-service interrupt throttling were added to the ring API; path hops are now activated from source to destination and the path config space avoids reserved fields on USB4 routers; the PCIe adapter is verified in the Detect LTSSM state before tunnel setup (`tb_pci_pre_activate`, `usb4_pci_port_ltssm_state`); multi-display DP tunnel allocation and bandwidth-group reservation indexing changed; router enumeration now verifies the Router Ready bit, with longer Configuration Ready and Notification timeouts; the domain gained a `domain_released` completion and NULLs `root_switch` on stop; XDomain lane bonding follows USB4 v2, XDomain removal no longer holds `tb->lock`, services keep an XDomain reference, and the property parser was hardened (`tb_property_merge_dir`, `tb_property_copy`, bounds checks with KUnit tests). Every prior-draft anchor is therefore suspect and the Inventory findings carry a per-area drift ledger.

Draft corpora ([facts.derived-pages] inputs; `guidelines/campaign.md`, "Deriving from prior drafts and pages"), two, both older than the documented tree:

1. The request-named corpus: `kernel-glossary-devel/docs/usb4/` at TREE_ROOT (untracked, a separate git repository; 50 files, about 7,050 lines; the prompt calls it "primitive results" and licenses inspiration). Its Elixir links are pinned at `v6.19` (379 links), although the session instruction describes it as 7.0-based; either way it predates the documented tree. Spec-oriented: register layouts drawn in plain-ASCII box art, link-training phases, TLP formats, tbtools dumps, CLx entry and exit, with zero to three C excerpts per file.
2. The skill's own prior revision: `docs/usb4/` under SKILL_DIR (46 pages, about 36,900 lines, nine groups: adapter, control, credit, domain, host-if, pm, router, sideband, tunnel), committed 2026-06-13 as skill commit `d2c04f9` ("usb4: add memos for USB4 subsystem") and re-touched by `03c608d`; every one of its 10,761 Elixir links is pinned at `v7.0`, and it was written under the June 2026 rules that `guidelines/LESSONS.md` (at commit 1bea4ac, before the compaction) describes. This corpus is on disk at the catalog's own output root, so the overwrite guard binds every row that lands on one of its paths (Re-entry contract, step 2), and the user checkpoint decides its fate (Scope decisions, pending).

NOT inputs: other campaigns' entries under `progress/` (run isolation per SKILL.md); the pages under any other `docs/` directory as fact sources (calibration is `docs/sound/` only, form only); any external USB4 or Thunderbolt specification text as a source of claims (every fact is researched against the tree; the specification is cited as SPECIFICATIONS material per the template, never as a substitute for kernel evidence).

Output root: `docs/usb4/`; pages land at the catalog's paths. No `SUMMARY.md` or `mkdocs.yml` edits. No git commits without an explicit user go.

## Re-entry contract

Standing instructions to any executor, on any machine, cold or warm:

1. Confirm the tree: a Linux kernel checkout at tag `v7.2`, commit `8d3ae59288f1e7d58d76558a6ee96d533bc5019f` (`git describe --tags` at the tree root prints `v7.2`). A different tree voids every anchor in this spec; stop and surface it. Confirm elixir.bootlin.com still serves `v7.2` before the first link is written.
2. Derive campaign state: diff this catalog's rows against `docs/usb4/`. This is a rewrite over a prior revision: the user decided (Scope decisions, User-confirmed decisions, 2026-09-04) that the June 2026 corpus is deleted before slice B1; until that removal has run on the checkout in front of you, a file on disk under `docs/usb4/` is presumed to be that corpus (pinned at v7.0), never this campaign's output; existence is not completion. Distinguish by this machine's run log, by the page's Elixir version pin (`grep -o 'linux/v7\.[02]' <page> | sort | uniq -c`: a v7.2-only page is this campaign's), or by asking the invoker.
3. Create or reuse the machine-local workspace `progress/usb4/` (run log `log.md`, worksheets). It is never committed.
4. Execute ONLY the slice the invoker named, a batch from this spec's batch order (its recommended slicing) or an explicit page list. Given a bare "run usb4" with no slice: report the derived state and ask; never pick a slice autonomously. Overwrite guard: a catalog page whose path already exists on disk is never overwritten silently; the checkpoint decision (delete the June corpus before B1) means a v7.0-pinned file found under `docs/usb4/` is removed with the rest of that corpus before writing, and a v7.2-pinned file is this campaign's output and is never overwritten without asking.
5. Run the slice per SKILL.md "Modes": one writer per page, briefed per `guidelines/campaign.md` [briefs] (the writer brief) with the page's catalog row, its cluster's boundary rules, the project-specific bans, the write-time cautions, the drift ledger from this spec and, where the Draft reuse map's Corpus 2 section D lists a register-layout figure for the page, that figure's pointer under the amendment of 2026-09-04 (Scope decisions, decision 4); then the orchestrator check per page (`guidelines/checking.md` [check-pass]); events go to the run log.
6. Promote anything durable (a spec claim the tree refuted, a user decision after approval, a settled adjudication) into this spec as a dated errata entry, or surface it for the waivers files. The run log does not travel.

## Scope decisions

### Hard constraints from the request (prompt.md, verbatim)

1. Mission: "The pages you're going to create should focus not only on the common USB4 concepts (not vendor-specific implementation), but more importantly how Linux kernel internally tracking/representing some of the major USB4 constructs."
2. Granularity: "You can decide divisions of pages. I'd prefer finer granularity. Look into the docs/acpi pages to understand how the granularity of each page should be." (docs/acpi at SKILL_DIR: 43 pages, 640 to 2,620 lines each, one mechanism per page.)
3. Drafts: "v7.0/kernel-glossary-devel/docs/usb4 contains some primitive results, but they are too primitive. Still, you can get inspiration from them." (Context records what that corpus is and its true version pin.)
4. Connection-manager scope: "Focus on generic tb_cm_ops. Exclude all the icm-specific things. Also ignore details for Intel's "Ridge" series controllers and their firmware-based connection managers."
5. Figures: "Draw ASCII diagram to illustrate, but do not just draw the code enumerating flow graphs. Again, make sure to look into your SKILL.md" (the banned function-flow shape of figures.md [shapes] is the rule this names).
6. Depth: "Don't limit yourself to 100-400 lines per page. Do as detailed as you can."
7. Tools: "You must use semcode tools."
8. Wording: "You must not use hedging wordings." (The style table's hedge row governs the sweep.)
9. Vendors: "You must not include vendor-specific thigns (e.g. Intel, NVIDIA)".
10. Curation: "This topic list is very rough. Curate new pages where you see fit." And per heading: "ACPI-aspects under drivers/thunderbolt/: Curate pages for this"; "Power Management: CLx; Curate pages for yourself"; "TMU: Curate page for yourself". Each is a curation obligation, never an omission to mirror.

### The request's topic list (verbatim; the mapping checklist for the catalog)

```
Router and some of its properties: tb_switch
- Route Strings
- Router config space
- Router capability structures and its helpers
- Router operations
- (Some other properties?)

Domains: tb, and tb_xdomain
- Basic elements for kernel to track current view of router topologies
- Router Hotplug flow: from host interface MSI triggered, to control channel handling packets, to hotplug event callback, to router enumeration (e.g. assign route string), to adding structures to the domain
- Router Hot unplug flow

Adapters: tb_port
- Adapter numbering and rules
- Adapter config space (common)
- Capability structure of a port and helpers in kernel

Lane adapters
- note that lane 0 is special. Have specific capability structures

Protocol adapters
- USB3, PCIe, DP. Have their respective capability structures

Host interface:
- Top level structure: tb_nhi
- Transfer/receive rings: tb_ring
- Raw mode vs. frame mode
- How DMA is set up
- PCIe config space of the Host Interface
- MSI-X setup

Control Traffic
- Control channel: tb_ctl
- How host interface handles control traffic
- Special routing rules (HopID 0)
- Helper functions in the kernel construct control packets (some of them are in drivers/thunderbolt/tb_msgs.h) and send/receive through the rings of the host interface.

General Protocol Tunneling
- in general look into drivers/thunderbolt/path.c and tunnel.c
- Path config space
- Kernel structures for tracking hops and paths (tb_path_hop and tb_path)
- Tunneling of protocol traffics and tracking structures in the kernel (tb_tunnel)
- Helper functions in the kernel to build up/maintain structures above (e.g. allocation, activation, credit maintenance, priority setup, bandwidth allocation) (fold into respective protocol tunneling pages if needed)

PCIe tunneling
- Helper functions in the kernel to build up/maintain PCIe tunneling.
- Scenario: Flow from enabling a PCIe tunneling to actual PCIe hotplug
- Scenario: PCIe hot unplug
- How tunneling are maintained across suspend/resume

USB3 Tunneling
- Helper functions in the kernel to build up/maintain USB3 tunneling.
- How tunneling are maintained across suspend/resume

DP tunneling
- Helper functions in the kernel to build up/maintain tunneling.
- HPD handling flow; how it relays to graphic driver after path being enabled
- Bandwidth allocation
- How tunneling are maintained across suspend/resume

Sideband registers:
- Sideband operations and helpers
- Retimer enumeration

ACPI-aspects under drivers/thunderbolt/
- Curate pages for this

Power Management
- CLx
- Curate pages for yourself

TMU
- Curate page for yourself
```

### Session-instruction constraints (the skill invocation)

11. "plan a deep and thorough usb4 campaign" (depth over economy; the catalog errs toward more, finer rows).
12. "pages in kernel-glossary-devel/ are based in 7.0 kernel while the tree we're at is 7.2. Be very careful when reusing those pages." (Every draft anchor is a hint re-found on the v7.2 tree; the per-area drift ledgers in Inventory findings and the Draft reuse map's spot checks implement this; a draft symbol that does not survive `git grep` at v7.2 is reported, never carried.)
13. "Curate topics where needed." (Reinforces constraint 10.)

### Seams already recorded by sibling campaigns (binding on this catalog's boundaries)

- `campaigns/dp.md`: "USB4 connection-manager tunneling (drivers/thunderbolt tb_tunnel machinery) — docs/usb4 territory; tunnel/dp-tunnel.md stops at the DPCD 0xE0000 protocol and the drm-side API." and "docs/usb4 (Thunderbolt/USB4): tunnel/ pages own the DPCD-visible tunneling protocol (0xE0000 region) and the GPU-driver-side API and IRQ handling; the connection manager (tb_tunnel setup, bandwidth negotiation inside drivers/thunderbolt) is usb4/ territory and is named in one sentence." The reciprocal holds here: this campaign's DP tunneling pages own the connection-manager side exhaustively and name the DRM tunnel consumer in one sentence at the seam.
- `campaigns/xhci.md`: "USB4/Thunderbolt tunneled USB3 — docs/usb4 territory." The reciprocal: this campaign's USB3 tunneling pages own the tunnel and the USB3 adapter machinery and stop at the xHCI root port the tunnel feeds.
- `campaigns/pci.md`: the `bridge_d3` policy ladder's Thunderbolt step is docs/pci territory; this campaign's PCIe tunneling pages stop at the tunneled downstream port and name pciehp as the consumer.

### Planning adjudications (orchestrator, 2026-09-04)

1. Granularity calibrated on docs/acpi (one mechanism per page, 640 to 2,620 lines): the request's headings became 80 firm rows plus 5 optional (after the adversarial review); every "helper functions" bullet became one mechanism page per helper family, and every "scenario" or "flow" bullet became a journey row separate from the mechanism rows it walks (pcie-tunnel-scenarios, dp-hotplug-flow, router-hotplug, router-unplug, system-suspend, system-resume).
2. Constraint 4 (generic `tb_cm_ops`, no ICM): implemented as a fill table in domain/connection-manager-ops.md (which members `tb_cm_ops` sets, tb.c:3287-3303), `tb_switch_is_icm` cited as the discriminator, and every ICM-only field, callback or attribute named as ICM-only in one clause and never explained; `icm.c` is never excerpted.
3. Constraint 9 (no vendor-specific things): the ban binds authored text and excerpts alike; the quirk table, the NVM vendor-ops table, the PCI ID table and the NHI ops selection are documented as mechanisms with no entry, device ID, vendor or code name; the vendor-named predicates (Sweep S1 10i) are never cited; an excerpt that would carry a vendor or device identifier is elided with `...` and the elision is stated; a vendor-named kernel symbol inside a citation URL is a URL, never authored text.
4. The two prior corpora are audit inputs only (Draft reuse map); no writer brief carries a pointer into either until the checkpoint decides question 4 (decided 2026-09-04: none for Corpus 1; Corpus 2's register-layout figures only, per the amendment under decision 4); every anchor from either is a hint re-found on the v7.2 tree (constraint 12).
5. The three "curate" headings became pm/ (11 rows) and acpi/ (3 rows after the review's merge and move, with the retimer `_DSM` and the IOMMU signal owned where their mechanisms are); the ACPI-core `_OSC` code is reached only as far as the USB4 bits (boundary rule 14).
6. Tracing has one home (control/tb-ctl.md) because the subsystem's only tracepoints are the control channel's; debug printing is stated per object page; sysfs and uevents are stated on the page of the object that carries them (the fold-in list).
7. Directory organization follows the house two-level layout with one third level (`adapter/protocol/`) on the docs/pci precedent; the June corpus's `credit/` group is renamed `bandwidth/`, so 25 of its 46 files collide by path with catalog rows and 21 would linger under old paths if it were kept in place (checkpoint question 1).
8. The [optional] rows were the user's call at the checkpoint (all five confirmed 2026-09-04); the batch order keeps them at the tails of their batches.

### User-confirmed decisions (checkpoint answers)

Checkpoint held 2026-09-04 (the four questions are recorded verbatim under "Checkpoint questions" in the Page catalog). Decisions:

1. June 2026 corpus: DELETE BEFORE B1. The first action of slice B1, before any writer is dispatched, is the removal of every v7.0-pinned page under `docs/usb4/` at SKILL_DIR (`git rm` of the 46 files whose Elixir links carry `linux/v7.0`; their content stays in the skill's git history and in the Draft reuse map); the removal is committed together with B1's pages at the user's commit go. [Amended 2026-09-04 at B1 dispatch: the removal excludes this campaign's own v7.2-pinned pages, at that time `sideband/retimer-enumeration.md` from the test slice, which is why the command is a per-file `git rm` and not `git rm -r docs/usb4/`.] An executor on another machine that still finds v7.0-pinned files under `docs/usb4/` (Re-entry contract step 2) removes them the same way before writing.
2. Optional rows: ALL FIVE IN (router/dma-port.md, sideband/lane-margining.md, debug/debugfs.md, debug/kunit-tests.md, service/usb4-stream.md). The `[optional]` tag no longer appears in the tables; the catalog is 85 firm pages.
3. Catalog: APPROVED at 80 rows plus the 5 confirmed optional rows, with the directory layout, the boundary rules and the batch order as recorded. This is the explicit go for the CATALOG; it starts no page. Execution happens only through user-invoked slices ("campaign usb4, batch B1" or an explicit page list).
4. Draft pointers: NONE. Writers research only the v7.2 tree; no writer brief names a page of either prior corpus; the Draft reuse map stays an orchestrator-side reference ([facts.derived-pages] applies only if a later amendment reverses this).

Amendment 2026-09-04 (user, later the same day; supersedes decision 4 for Corpus 2 only): the ASCII figures of the kernel-glossary-devel corpus (`kernel-glossary-devel/docs/usb4/` at TREE_ROOT, v6.19) MAY be reused, but only the figures that draw registers, configuration spaces and other bit-field layouts. The user's words: "The ASCII diagram in the old drafts may be reused, but only for the registers, config spaces, and other bitfield-oriented diagrams. Don't reuse diagrams exibiting code flow in the old drafts because they may change in newer kernel here." How this binds a writer:
   - The reusable set is exactly the Draft reuse map's Corpus 2 section D ("Register-layout figure inventory"): the Router CS, TopologyID route string, Adapter CS, TMU adapter capability, Lane Adapter capability, PORT_CS_18/19, PORT_CS_1, DP adapter CS, PCIe adapter CS, USB3 adapter CS, Path CS, Counter Config Set, sideband register map and registers, TX/RX descriptor and control-packet header figures (the USB PD figures in that table stay out of scope). A writer brief for a page whose section-D row names it carries the source file path under `kernel-glossary-devel/docs/usb4/` and the row's verification note.
   - Every other Corpus 2 figure is drawn fresh from the v7.2 tree: the section E figures (topology trees, the descriptor-ring picture, the CLx port-block pair, the swimlanes) and every figure that exhibits code flow, a call sequence, a state machine of kernel code paths or the ordering of kernel functions, in either corpus, because the code changed between v6.19, v7.0 and v7.2. This does not loosen figures.md [shapes], which bans plain function-flow figures outright.
   - A reused figure is derived, never copied: it is redrawn in the [registers] style (Unicode DWORD-grid or L-connector, geometry per [geometry]), and every bit range, field name, offset and width is re-verified against the v7.2 defines (`drivers/thunderbolt/tb_regs.h`, `sb_regs.h`, `nhi_regs.h`, `tb_msgs.h`, `include/linux/thunderbolt.h`) before it lands, with section D's recorded mismatches corrected (the Router CS DW3 `route_hi`/`enabled` split, the Adapter CS DW1/DW2 `revision` fields, the lane adapter width mask, the counter-set third DWORD label, the sideband debug-data size, the missing `USB4_SB_FW_VERSION`, the control-packet DW0 that no kernel struct defines). A field the kernel defines nothing for is handled as [registers] directs (verified against the governing specification, which SPECIFICATIONS names) and is never presented as a kernel construct.
   - [facts.derived-pages] governs the derivation: the worksheet records the source figure as an inventory item with its disposition (kept and redrawn, or cut with the reason), and the page's own completeness audit is unaffected by what the source covered.
   - Corpus 2 is untracked at TREE_ROOT and may be absent on another machine; where it is absent, the writer draws the figure from the tree and the worksheet says so. Corpus 1 (the June corpus under `docs/usb4/`) stays at decision 4: no pointers of any kind.
   - Which brief carries which pointer (section D figure → catalog page; a cold executor composes the brief from this table and the section D row):

     | section D figure (Corpus 2 file) | catalog page whose brief carries the pointer |
     |---|---|
     | Router CS DW0-DW26 and its cutaways (cfg-router.md, cfg-router-cs.md, cfg-router-ops.md) | router/router-config-space.md (the DW26 opcode cells also router/router-operations.md) |
     | TopologyID route string (topology-id.md, tlp-ctrl.md) | router/route-string.md |
     | Adapter CS DW0-DW8 (cfg-adapter.md) | adapter/adapter-config-space.md |
     | TMU Adapter Capability (cfg-adapter-lane.md appendix) | pm/tmu.md |
     | Lane Adapter Capability (cfg-adapter-lane.md appendix) | adapter/lane-adapter.md |
     | PORT_CS_18 / PORT_CS_19 (cfg-adapter-lane.md, link-train-2.md, 3-2, 3-4) | adapter/usb4-port-capability.md |
     | PORT_CS_1 sideband command (sideband-regs.md, cfg-adapter-lane.md) | sideband/sideband-access.md |
     | DP adapter CS 0-8 with the LOCAL/REMOTE/COMMON caps (cfg-adapter-dp.md) | adapter/protocol/dp-adapter.md (the bandwidth-mode cells also adapter/protocol/dp-adapter-bandwidth-mode.md) |
     | PCIe adapter CS 0 (cfg-adapter-pcie.md) | adapter/protocol/pcie-adapter.md |
     | USB3 adapter CS 0-4 (cfg-adapter-usb3.md) | adapter/protocol/usb3-adapter.md |
     | Path Entry PATH_CS_0/1 (cfg-adapter-path.md, cfg-adapter-counter.md) | tunnel/path-config-space.md |
     | Counter Config Set (cfg-adapter-counter.md) | adapter/adapter-config-space.md |
     | Sideband register map, SB 0x0C Link Configuration, SB 0x0D TxFFE (sideband-regs.md, link-train-3*.md) | sideband/sideband-access.md (the TxFFE figure also sideband/lane-margining.md) |
     | TX descriptor, RX descriptor and depleted RX descriptor (host-if/tx.md, host-if/rx.md) | host-if/rings.md |
     | TLP DW0 header and Control Packet header (tlp/tlp.md, tlp/tlp-ctrl.md) | control/control-packets.md (the DW0 that no kernel struct defines is drawn only as the NHI-prepended word the driver never touches) |
     | PD Message Header, VDM Header, VDO, EUDO (lt/*) | none (out of scope) |

## Inventory findings

Inventory dispatched 2026-09-04 as read-only agents over the v7.2 tree, one per area, plus two whole-subsystem sweeps and two draft-reuse audits. Every line number below is a hint to re-verify on disk at write time, never a citation (semcode indexes can lag; the on-disk source at v7.2 is ground truth). Areas:

- Area A: Router (`struct tb_switch`), route strings, router config space and capabilities, router operations, DROM, NVM, security and authorization.
- Area B: Domain (`struct tb`), the software connection manager (`tb_cm_ops`, `struct tb_cm`), hotplug and unplug, XDomain and services, properties.
- Area C: Adapters (`struct tb_port`), adapter numbering and config space, port capabilities, lane adapters and bonding, the USB4 port device, link controller port operations.
- Area D: Protocol adapters (PCIe, USB3, DP capability structures and helpers), sideband access, retimers.
- Area E: Host interface (`struct tb_nhi`, the PCI NHI driver, rings, raw and frame modes, DMA, MSI-X) and the control channel (`struct tb_ctl`, control packets, HopID 0, requests).
- Area F: Paths and hops, tunnels, credits, bandwidth groups and DP bandwidth allocation, PCIe/USB3/DP/DMA tunneling and their consumers.
- Area G: Power management (system and runtime suspend/resume, wakes), CLx, TMU, ACPI integration.
- Sweep S1: tracing, debug printing and debugging infrastructure across the whole subsystem (digest items 7, 8, 10).
- Sweep S2: asynchronous, deferred and lazy processing across the whole subsystem (digest item 9).

### Area A: Router — COMPLETE (recorded 2026-09-04)

#### 1. Core structs

**`struct tb_switch` — drivers/thunderbolt/tb.h:171** (kerneldoc drivers/thunderbolt/tb.h:111-170). EVERY field, role, writer:
- `dev` (172) embedded `struct device`; initialized `tb_switch_alloc` switch.c:2539 / `tb_switch_alloc_safe_mode` switch.c:2584; registered by `device_add` switch.c:3412. [Orchestrator note 2026-09-04, refuted at write time (tb-switch.md): `device_add(&sw->dev)` is at switch.c:3369; :3411 is `tb_switch_debugfs_init(sw)`.]
- `config` (173) cached `struct tb_regs_switch_header`; read by `tb_cfg_read(..., TB_CFG_SWITCH, 0, 5)` switch.c:2478; patched+written back in `tb_switch_configure` switch.c:2605.
- `ports` (174) `kzalloc_objs(*sw->ports, max_port_number + 1)` switch.c:2501; freed in `tb_switch_release` switch.c:2303.
- `dma_port` (175) pre-USB4 mailbox handle; set `tb_switch_add_dma_port` switch.c:2772; freed switch.c:2291. Non-NULL also means NVM upgradeable.
- `tmu` (176) `struct tb_switch_tmu` (tb.h:105); `.cap` written by tmu.c (other area).
- `tb` (177) owning domain; set switch.c:2477 / 2580.
- `uid` (178) 64-bit router UID; written `usb4_switch_read_uid` (eeprom.c:679/701), `tb_drom_read_uid_only` (eeprom.c:539/689), `tb_drom_parse_v1` eeprom.c:606.
- `uuid` (179) kmemdup'd in `tb_switch_set_uuid` switch.c:2716.
- `vendor` / `device` (180-181) from DROM: eeprom.c:352-353 (USB4 desc entry 9), eeprom.c:607-608 (v1 header).
- `vendor_name` / `device_name` (182-183) DROM generic entries 1 and 2, `kstrndup` eeprom.c:335, 342.
- `link_speed` (184) `tb_switch_update_link_attributes` switch.c:2879.
- `link_width` (185) same, switch.c:2886.
- `preferred_link_width` (186) Gen-4 only, `tb_switch_link_init` switch.c:2935.
- `link_usb4` (187) `usb4_switch_setup` usb4.c:259 via `link_is_usb4()` (PORT_CS_18_TCM).
- `generation` (188) `tb_switch_get_generation` switch.c:2380, assigned switch.c:2482.
- `cap_plug_events` (189) TB_VSE_CAP_PLUG_EVENTS offset, switch.c:2521.
- `cap_vsec_tmu` (190) TB_VSE_CAP_TIME2, switch.c:2525.
- `cap_lc` (191) TB_VSE_CAP_LINK_CONTROLLER, switch.c:2529.
- `cap_lp` (192) TB_VSE_CAP_CP_LP (CLx), switch.c:2533.
- `is_unplugged` (193) set only by `tb_sw_set_unplugged` switch.c:3483; gates `tb_sw_read`/`tb_sw_write` (tb.h:675, 689).
- `drom` (194) `tb_switch_drom_alloc` eeprom.c:449, freed eeprom.c:466 and switch.c:2306.
- `nvm` (195) `tb_switch_nvm_init` switch.c:346; cleared `tb_switch_nvm_remove` switch.c:399.
- `no_nvm_upgrade` (196) switch.c:351/388, tb.c:3014 (host router, non-USB4).
- `safe_mode` (197) only `tb_switch_alloc_safe_mode` switch.c:2582 — ICM-only path.
- `boot` (198) SW CM sets it in `tb_discover_tunnels` tb.c:1706 for routers on a boot-firmware PCIe tunnel; ICM sets it from messages.
- `rpm` (199) `sw->rpm = sw->generation > 1` tb.c:1373; host router tb.c:3016.
- `authorized` (200) tb.h `unsigned int`; switch.c:2537 (root always 1), 1859, 1812, tb.c:2985.
- `security_level` (201) per-router; **written only by icm.c:881, 1315 — ICM-only**; read by `switch_attr_is_visible` switch.c:2247.
- `debugfs_dir` (202) debugfs.c:2424 (CONFIG_DEBUG_FS).
- `key` (203) 32-byte secure-connect key; `key_store` switch.c:1971-1973; freed switch.c:2305.
- `connection_id` (204), `connection_key` (205) — **ICM-only** (icm.c:690-691).
- `link` (206), `depth` (207) — **ICM-only** (icm.c:692-693); read by `tb_switch_match` switch.c:3779-3781.
- `rpm_complete` (208) — **ICM-only** completion (icm.c:657 init, icm.c:700 complete).
- `quirks` (209) OR-ed by quirks.c:12/29/51.
- `credit_allocation` (210) `usb4_switch_credits_init` usb4.c:871.
- `max_usb3_credits`, `min_dp_aux_credits`, `min_dp_main_credits`, `max_pcie_credits`, `max_dma_credits` (211-215) usb4.c:872-880 from BUFFER_ALLOC op.
- `clx` (216) clx.c:236/383/424 (other area).
- `drom_blob` (218) `struct debugfs_blob_wrapper`, gated `#ifdef CONFIG_DEBUG_FS`; eeprom.c:454/463.

**`struct tb_regs_switch_header` — drivers/thunderbolt/tb_regs.h:166** (`__packed`, Router CS dword layout):
- DWORD0 (ROUTER_CS_0): `vendor_id` u16 bits 0-15, `device_id` u16 bits 16-31.
- DWORD1 (ROUTER_CS_1 = 0x01): `first_cap_offset:8` b0-7, `upstream_port_number:6` b8-13, `max_port_number:6` b14-19, `depth:3` b20-22, `__unknown1:1` b23, `revision:8` b24-31.
- DWORD2: `route_lo` (full dword) — low 32 bits of route string.
- DWORD3 (ROUTER_CS_3 = 0x03): `route_hi:31` b0-30, `enabled:1` b31 == `ROUTER_CS_3_V` (tb_regs.h:197).
- DWORD4 (ROUTER_CS_4 = 0x04): `plug_events_delay:8` b0-7 (Notification Timeout ms), `cmuv:8` b8-15 (`ROUTER_CS_4_CMUV_V1` 0x10 / `_V2` 0x20, tb_regs.h:200-201), `__unknown4:8` b16-23, `thunderbolt_version:8` b24-31 (masked by `USB4_VERSION_MAJOR_MASK` GENMASK(7,5), tb_regs.h:193).

**`struct tb_nvm` — drivers/thunderbolt/tb.h:52** (kerneldoc tb.h:30-51): `dev` owner, `major`/`minor` active version, `id` IDA id, `active`/`active_size` read-only nvmem, `non_active` write nvmem, `buf` vmalloc'd staging image, `buf_data_start`/`buf_data_size` post-validation window, `authenticating`, `flushed`, `vops` vendor ops.
**`enum tb_nvm_write_ops` — tb.h:68**: `WRITE_AND_AUTHENTICATE`=1, `WRITE_ONLY`=2, `AUTHENTICATE_ONLY`=3.
**`struct tb_dma_port` — dma_port.c:54**: `sw`, `port` (NHI port 3/5/7), `base` (=DMA_PORT_CAP 0x3e), `buf[]` flex array (v7.2 change).
**`struct tb_nvm_vendor_ops` — nvm.c:37**: `read_version` / `validate` / `write_headers`. **`struct tb_nvm_vendor` — nvm.c:51**: `{vendor, vops}`.
**`struct tb_quirk` — quirks.c:55**: `hw_vendor_id`, `hw_device_id` (config-space IDs), `vendor`, `device` (DROM IDs), `hook`.
**Capability headers**: `tb_cap_basic` tb_regs.h:62, `tb_cap_extended_short` :76, `tb_cap_extended_long` :92, `tb_cap_any` union :107, `tb_cap_link_controller` :117, `tb_cap_phy` :129, `tb_eeprom_ctl` :139, `tb_cap_plug_events` :151 (holds `eeprom_ctl` + `drom_offset` at VSC_CS_12).
**Enums**: `tb_switch_cap` tb_regs.h:28 (`TB_SWITCH_CAP_TMU`=0x03, `TB_SWITCH_CAP_VSE`=0x05); `tb_switch_vse_cap` tb_regs.h:33 (`PLUG_EVENTS`=0x01 also EEPROM, `TIME2`=0x03, `CP_LP`=0x04, `LINK_CONTROLLER`=0x06 also IECS).
**DROM structs (eeprom.c)**: `tb_drom_header` :221, `enum tb_drom_entry_type` :239 (GENERIC=0, PORT=1), `tb_drom_entry_header` :245, `tb_drom_entry_generic` :252, `tb_drom_entry_port` :257, `tb_drom_entry_desc` :284 (USB4 product descriptor).
**`enum tb_security_level` — include/linux/thunderbolt.h:58**: NONE, USER, SECURE, DPONLY, USBONLY, NOPCIE.

#### 2. API families

**Route strings & topology (all inline, tb.h)**
- `TB_ROUTE_SHIFT` 8 — tb_regs.h:19. `tb_route()` tb.h:583 (route_hi<<32|route_lo). `tb_route_length()` tb.h:1240 `(fls64(route)+7)/8`. `tb_downstream_route()` tb.h:1253 (parent route | port << depth*8). `tb_port_at()` tb.h:587. `tb_upstream_port()` tb.h:565. `tb_switch_downstream_port()` tb.h:915. `tb_switch_parent()` tb.h:902. `tb_switch_depth()` tb.h:928. `tb_switch_for_each_port()` tb.h:874 (skips control port 0).
- Route upload: `tb_switch_alloc` sets `upstream_port_number/depth/route_hi/route_lo/enabled=0` switch.c:2487-2491; `tb_switch_configure` sets `enabled=1`, `plug_events_delay=0xff`, `cmuv`, then `tb_sw_write((u32*)&sw->config+1, TB_CFG_SWITCH, ROUTER_CS_1, 4)` switch.c:2637/2651 — i.e. dwords 1..4. USB4 then runs `usb4_switch_setup()`.
- Route derivation during scan: `tb_switch_alloc(..., tb_downstream_route(port))` tb.c:1325-1326; root at route 0 tb.c:3001.
- `tb_switch_find_by_route()` (E) switch.c:3848 (route 0 → `tb_switch_get(root_switch)`).

**Config-space access (seam only)**
- `tb_sw_read()` tb.h:672 / `tb_sw_write()` tb.h:686 → `tb_cfg_read`/`tb_cfg_write` with `TB_CFG_SWITCH`, port 0; both return `-ENODEV` if `sw->is_unplugged`. `TB_MAX_CONFIG_RW_LENGTH` 60 tb_regs.h:26.

**Capability walk (cap.c)**
- `tb_switch_next_cap()` (E) cap.c:154 — reads 2 dwords, TMU→`basic.next`, VSE→`extended_short.next` or `extended_long.next` when length==0; clamps `>= VSE_CAP_OFFSET_MAX` to 0.
- `tb_switch_find_cap()` (E) cap.c:198; `tb_switch_find_vse_cap()` (E) cap.c:234 (matches `cap==TB_SWITCH_CAP_VSE && vsec_id`).
- Port-side (other area but same file): `tb_port_next_cap` :76, `__tb_port_find_cap` (S) :91, `tb_port_find_cap` :124, `tb_port_enable_tmu` (S) :18 and `tb_port_dummy_read` (S) :47 — **vendor-only** (Light Ridge / Eagle Ridge).

**Router operations (usb4.c)**
- `usb4_native_switch_op()` (S) usb4.c:54 — metadata→ROUTER_CS_25, tx data→ROUTER_CS_9.., opcode|`ROUTER_CS_26_OV`→ROUTER_CS_26, wait OV clear 500 ms, `ROUTER_CS_26_ONS`→`-EOPNOTSUPP`, status = `ROUTER_CS_26_STATUS_MASK>>24`, read back metadata + rx data.
- `__usb4_switch_op()` (S) usb4.c:109 — bounds tx/rx to `USB4_DATA_DWORDS`; calls `cm_ops->usb4_switch_op` proxy first, falls back to native on `-EOPNOTSUPP` (**proxy is ICM-only**; tb.c's `tb_cm_ops` does not set it).
- `usb4_switch_op()` (S inline) usb4.c:142; `usb4_switch_op_data()` (S inline) usb4.c:148.
- `enum usb4_switch_op` tb_regs.h:231: QUERY_DP_RESOURCE 0x10, ALLOC_DP_RESOURCE 0x11, DEALLOC_DP_RESOURCE 0x12, NVM_WRITE 0x20, NVM_AUTH 0x21, NVM_READ 0x22, NVM_SET_OFFSET 0x23, DROM_READ 0x24, NVM_SECTOR_SIZE 0x25, BUFFER_ALLOC 0x33.
- Registers: `ROUTER_CS_9` 0x09 (data area, up to 16 dwords), `ROUTER_CS_25` 0x19 metadata, `ROUTER_CS_26` 0x1a (`OPCODE_MASK` GENMASK(15,0), `STATUS_MASK` GENMASK(29,24)/shift 24, `ONS` BIT(30), `OV` BIT(31)) — tb_regs.h:220-228.

**usb4_switch_* helpers (all E unless noted)**
- `usb4_switch_check_wakes()` usb4.c:163 — reads ROUTER_CS_6 WOPS/WOUS + per-port PORT_CS_18 WOU4S/WOCS/WODS; `pm_wakeup_event()`.
- `link_is_usb4()` (S) usb4.c:213 — PORT_CS_18_TCM.
- `usb4_switch_setup()` usb4.c:243 — reads ROUTER_CS_6 (HCI/TNS), sets ROUTER_CS_5 UTO/PTO/HCO, clears CNS, then **waits ROUTER_CS_6_RR 500 ms** (v7.2).
- `usb4_switch_configuration_valid()` usb4.c:316 — sets `ROUTER_CS_5_CV`, waits `ROUTER_CS_6_CR` **500 ms** (was 50).
- `usb4_switch_read_uid()` usb4.c:347 — `tb_sw_read(ROUTER_CS_7, 2)`.
- `usb4_switch_drom_read_block()` (S) usb4.c:352 (DROM_READ; addr/size masks usb4.c:29-32); `usb4_switch_drom_read()` usb4.c:386 via `tb_nvm_read_data(..., USB4_DATA_RETRIES, ...)`.
- `usb4_switch_lane_bonding_possible()` usb4.c:402 — upstream PORT_CS_18_BE.
- `usb4_switch_set_wake()` usb4.c:426 — per-port PORT_CS_19 WOC/WOD/WOU4; router ROUTER_CS_5 WOP/WOU/WOD (device routers only).
- `usb4_switch_set_sleep()` usb4.c:507 — ROUTER_CS_5_SLP, wait ROUTER_CS_6_SLPR 500 ms.
- `usb4_switch_nvm_sector_size()` usb4.c:536 (status 0x2 → `-EOPNOTSUPP`); `usb4_switch_nvm_read_block` (S) :553; `usb4_switch_nvm_read()` :588; `usb4_switch_nvm_set_offset()` :605; `usb4_switch_nvm_write_next_block` (S) :623; `usb4_switch_nvm_write()` :652; `usb4_switch_nvm_authenticate()` :680 (EACCES/ENOTCONN/ETIMEDOUT treated as success); `usb4_switch_nvm_authenticate_status()` :714 (proxy `cm_ops->usb4_switch_nvm_authenticate_status` = **ICM-only**; else reads ROUTER_CS_26 and checks opcode==NVM_AUTH).
- `usb4_switch_credits_init()` usb4.c:758 — BUFFER_ALLOC, parses `enum usb4_ba_index` (usb4.c:39: MAX_USB3 1, MIN_DP_AUX 2, MIN_DP_MAIN 3, MAX_PCIE 4, MAX_HI 5); validates then sets `credit_allocation`.
- `usb4_switch_query_dp_resource()` :900, `usb4_switch_alloc_dp_resource()` :933, `usb4_switch_dealloc_dp_resource()` :958.
- `usb4_port_index()` :982; `usb4_switch_map_pcie_down()` :1015; `usb4_switch_map_usb3_down()` :1048.
- `usb4_switch_add_ports()` :1078 (skips ICM and non-USB4); `usb4_switch_remove_ports()` :1111.
- `usb4_switch_version()` (inline) tb.h:1311; `tb_switch_is_usb4()` (inline) tb.h:1322.

**Router lifecycle (switch.c)**
- `tb_switch_alloc()` (E) :2451; `tb_switch_alloc_safe_mode()` (E) :2570 — **only caller is icm.c:2203**; `tb_switch_configure()` (E) :2605; `tb_switch_configuration_valid()` (E) :2669; `tb_switch_add()` (E) :3298; `tb_switch_remove()` (E) :3430; `tb_switch_release()` (S) :2288; `tb_switch_uevent()` (S) :2309 (USB4_VERSION, USB4_TYPE=host/hub/device); `tb_switch_type` (E) :2373; `tb_switch_pm_ops` (S) :2368 (SET_RUNTIME_PM_OPS, CONFIG_PM).
- `tb_switch_get()`/`tb_switch_put()` (inline) tb.h:878/885 → `get_device`/`put_device`.
- `tb_switch_set_uuid()` (S) :2676; `tb_switch_add_dma_port()` (S) :2722; `tb_switch_default_link_ports()` (S) :2821; `tb_switch_update_link_attributes()` (S) :2863; `tb_switch_link_init()` (S) :2896; `tb_switch_credits_init()` (S) :3256; `tb_switch_port_hotplug_enable()` (S) :3266; `tb_sw_set_unplugged()` (E) :3471.
- `tb_switch_resume()` (E) :3525; `tb_switch_suspend()` (E) :3641; `tb_switch_set_wake()` (S) :3492; `tb_switch_check_wakes()` (S) :3504.
- `tb_switch_match()` (S) :3759; `tb_switch_find_by_link_depth()` (E) :3795 — **ICM-only callers**; `tb_switch_find_by_uuid()` (E) :3822 — **ICM-only callers**; `tb_switch_find_by_route()` (E) :3848; `tb_switch_find_port()` (E) :3874.
- `tb_switch_get_generation()` (S) :2380 — **vendor-only** device-ID table; `tb_switch_generation_name()` (S) :1547; `tb_dump_switch()` (S) :1563; `tb_switch_exceeds_max_depth()` (S) :2425.
- Predicates tb.h: `tb_is_switch()` :890, `tb_to_switch()` :895, `tb_switch_is_icm()` :1023 (`!sw->config.enabled` — exists purely to branch away from ICM), `tb_switch_is_usb4()` :1322. **Vendor-only**: `tb_switch_is_light_ridge` :933, `_eagle_ridge` :939, `_cactus_ridge` :945, `_falcon_ridge` :957, `_alpine_ridge` :969, `_titan_ridge` :984, `_tiger_lake` :997.
- Vendor-only router helpers: `tb_switch_pcie_bridge_write()` (S) :3891, `tb_switch_pcie_l1_enable()` (E) :3944, `tb_switch_xhci_connect()` (E) :3980, `tb_switch_xhci_disconnect()` (E) :4024 (all gen-3 Alpine/Titan Ridge).

**Reset**
- `tb_switch_reset()` (E) switch.c:1682; `tb_switch_enumerated()` (S) :1651 (reads ROUTER_CS_3 for `ROUTER_CS_3_V`; skips reset if not enumerated); `tb_switch_reset_host()` (S) :1581; `tb_switch_reset_device()` (S) :1646 (`tb_port_reset` on parent downstream port); `tb_switch_wait_for_bit()` (E) :1723.

**DROM (eeprom.c)**
- Bit-banged EEPROM (pre-USB4, vendor legacy): `tb_eeprom_ctl_write/read` :18/:26, `tb_eeprom_active` :42, `tb_eeprom_transfer` :71, `tb_eeprom_out` :96, `tb_eeprom_in` :116, `tb_eeprom_get_drom_offset` :137, `tb_eeprom_read_n` :168 (all S).
- CRC: `tb_crc8()` (S) :200 (init 0xff, poly 7); `tb_crc32()` (S) :212 (`~crc32c(~0,...)`).
- Parser: `tb_drom_parse_entry_generic` (S) :326 (index 1 vendor_name, 2 device_name, 9 USB4 desc→vendor/device); `tb_drom_parse_entry_port` (S) :362 (dual-link pairing, **v7.2 bounds check** :398-403); `tb_drom_parse_entries` (S) :416; `tb_drom_parse_v1` (S) :592 (uid crc8 + data crc32, header 22 B); `usb4_drom_parse` (S) :620 (crc32 only, header 16 B); `tb_drom_parse` (S) :636 (dispatch on `device_rom_revision`: 3→USB4, else v1).
- Acquisition: `tb_switch_drom_alloc/free` (S) :447/:460; `tb_drom_copy_efi` (S) :473 (ACPI/EFI `ThunderboltDROM` property, Apple path); `tb_drom_copy_nvm` (S) :503 (via dma_port); `usb4_copy_drom` (S) :543 (router op); `tb_drom_bit_bang` (S) :564.
- Entry points: `tb_drom_read_uid_only()` (E) :304; `tb_drom_host_read` (S) :674; `tb_drom_device_read` (S) :695; `tb_drom_read()` (E) :723.

**NVM (nvm.c + switch.c)**
- Vendor-ops table mechanism: `switch_nvm_vendors[]` nvm.c:193 — rows `{0x174c, &asmedia_switch_nvm_ops}`, `{PCI_VENDOR_ID_INTEL, &intel_switch_nvm_ops}`, `{0x8087, &intel_switch_nvm_ops}` (**all rows vendor-specific**); `retimer_nvm_vendors[]` :273. Hooks `intel_switch_nvm_version` :56, `intel_switch_nvm_validate` :89, `intel_switch_nvm_write_headers` :136 (CSS via dma_port), `asmedia_switch_nvm_version` :160 — all S and vendor-only. No matching row ⇒ `tb_nvm_alloc` returns `-EOPNOTSUPP` ⇒ upgrade disabled.
- Generic: `tb_nvm_alloc()` (E) :289, `tb_nvm_read_version()` (E) :359, `tb_nvm_validate()` (E) :379, `tb_nvm_write_headers()` (E) :414, `tb_nvm_add_active()` (E) :433, `tb_nvm_write_buf()` (E) :475, `tb_nvm_add_non_active()` (E) :503, `tb_nvm_free()` (E) :535, `tb_nvm_read_data()` (E) :560, `tb_nvm_write_data()` (E) :607, `tb_nvm_exit()` (E) :641.
- Router side: `nvm_auth_status` cache — `struct nvm_auth_status` switch.c:23, `nvm_auth_status_cache` LIST_HEAD :35, `nvm_auth_status_lock` mutex :36, `__nvm_get_auth_status` (S) :38, `nvm_get_auth_status` (S) :50, `nvm_set_auth_status` (S) :61, `nvm_clear_auth_status` (S) :86.
- `nvm_validate_and_write` (S) :99; `nvm_authenticate_host_dma_port` (S) :127; `nvm_authenticate_device_dma_port` (S) :167; `nvm_readable` (S inline) :212; `nvm_upgradeable` (S inline) :228; `nvm_authenticate` (S) :235; `tb_switch_nvm_read()` (E) :276; `nvm_read`/`nvm_write` nvmem callbacks (S) :284/:307; `tb_switch_nvm_init` (S) :328 **new at v7.2**; `tb_switch_nvm_add` (S) :358; `tb_switch_nvm_remove` (S) :394.

**DMA port (pre-USB4 upgrade path)**
- `dma_port_match`/`dma_port_copy` (S) dma_port.c:65/:82; `dma_port_read`/`dma_port_write` (S) :88/:129; `dma_find_port` (S) :168; `dma_port_alloc()` (E) :203; `dma_port_free()` (E) :227; `dma_port_wait_for_completion` (S) :232; `status_to_errno` (S) :257; `dma_port_request` (S) :271; `dma_port_flash_read_block`/`_write_block` (S) :295/:317; `dma_port_flash_read()` (E) :353; `dma_port_flash_write()` (E) :373; `dma_port_flash_update_auth()` (E) :396; `dma_port_flash_update_auth_status()` (E) :420; `dma_port_power_cycle()` (E) :452. Header dma_port.h:21-29.

**Security / authorization**
- `authorized_show` (S) switch.c:1785, `disapprove_switch` (S) :1794 (recursive over children), `tb_switch_set_authorized` (S) :1819, `authorized_store` (S) :1873.
- Seams (domain.c): `tb_domain_disapprove_switch()` :638, `tb_domain_approve_switch()` :657, `tb_domain_approve_switch_key()` :683, `tb_domain_challenge_switch_key()` :715 (HMAC-SHA256 over 32-byte random challenge), `tb_domain_disconnect_all_paths()` :845.
- **SW CM `tb_cm_ops` instance — drivers/thunderbolt/tb.c:3287-3303, exact member list**: `.start`, `.stop`, `.deinit`, `.suspend_noirq`, `.resume_noirq`, `.freeze_noirq`, `.thaw_noirq`, `.complete`, `.runtime_suspend`, `.runtime_resume`, `.handle_event`, `.disapprove_switch = tb_disconnect_pci`, `.approve_switch = tb_tunnel_pci`, `.approve_xdomain_paths`, `.disconnect_xdomain_paths`. **NOT set: `add_switch_key`, `challenge_switch_key`, `usb4_switch_op`, `usb4_switch_nvm_authenticate_status`, `get_boot_acl`, `set_boot_acl`, `driver_ready`, `suspend`, `runtime_suspend_switch`, `runtime_resume_switch`, `disconnect_pcie_paths` — all ICM-only.** Consequence: for the SW CM, `authorized=1` means "PCIe tunnel from parent created" (`tb_tunnel_pci` tb.c:2275); `authorized=2` (challenge) always returns `-EPERM`; `key` attribute is invisible unless domain+router security level is SECURE, which only ICM ever sets.
- `struct tb_cm_ops` tb.h:507.

**Quirks**: `tb_check_quirks()` (E) quirks.c:125 — matches on config vendor/device and DROM vendor/device, calls hook. Hooks (all S): `quirk_force_power_link` :10 (generic flag, Dell dock rows — vendor-only rows), `quirk_dp_credit_allocation` :16 (**vendor-only**, Goshen Ridge), `quirk_clx_disable` :24 (Titan Ridge + AMD rows, **vendor-only**), `quirk_usb3_maximum_bandwidth` :33 (**vendor-only**, ADL/RPL/MTL/Barlow Ridge), `quirk_block_rpm_in_redrive` :49 (**vendor-only**, Barlow Ridge).
- Quirk-flag test sites: `QUIRK_FORCE_POWER_LINK_CONTROLLER` — switch.c:2270 (`nvm_authenticate_on_disconnect` visibility) **generic mechanism, vendor-triggered**; `QUIRK_NO_CLX` — clx.c:189 (other area); `QUIRK_KEEP_POWER_IN_DP_REDRIVE` — tb.c:2108, 2133, 2163 (generic RPM gate).

**lc.c router-level (all pre-USB4 / Thunderbolt-generation, i.e. legacy)**
- `tb_lc_read_uuid()` (E) lc.c:20 — `cap_lc + TB_LC_FUSE` (tb_regs.h:595), 4 dwords; returns `-EINVAL` if no `cap_lc`.
- `read_lc_desc()` (S) :27 — `cap_lc + TB_LC_DESC` (tb_regs.h:589), yields NLC/size/port-size.
- `tb_lc_set_wake_one()` (S) :389; `tb_lc_set_wake()` (E) :428 (gen ≥ 2, device routers only); `tb_lc_set_sleep()` (E) :469 (gen ≥ 2, `TB_LC_SX_CTRL_SLP`); `tb_lc_lane_bonding_possible()` (E) :515 (`TB_LC_PORT_ATTR_BE`); `tb_lc_force_power()` (E) :712 (writes 0xffff to `TB_LC_POWER` 0x740) — used only for `nvm_authenticate_on_disconnect` (switch.c:2111).

#### 3. Lifecycle and locking

- **Alloc**: `tb_switch_alloc` switch.c:2451 → unlock parent downstream port, `tb_cfg_get_upstream_port`, `kzalloc_obj(*sw)` :2473, read 5 dwords config :2478, `tb_switch_get_generation` :2482, patch route/depth/upstream, depth check :2493, `kzalloc_objs` ports :2501 (**size = max_port_number + 1**), per-port `ida_init` for in/out hopids (port 0 skipped) :2510-2513, cache 4 VSE cap offsets :2519-2534, root authorized :2537, `device_initialize` + bus/type/groups + `dev_set_name("%u-%llx", tb->index, tb_route(sw))` :2539-2544. Error path frees ports+sw directly (device not yet initialized).
- **Configure**: `tb_switch_configure` :2605 → `tb_plug_events_active(sw, true)` :2658.
- **Add**: `tb_switch_add` :3298 → `tb_switch_add_dma_port` → `tb_switch_nvm_init` → (non-safe-mode) credits, `tb_drom_read`, `tb_switch_set_uuid`, per-port `tb_init_port`, `tb_check_quirks`, default link ports, link attributes/init, clx init, tmu init → `tb_switch_port_hotplug_enable` → `device_add` :3412 → `usb4_switch_add_ports` → `tb_switch_nvm_add` → `device_init_wakeup` → runtime PM (`TB_AUTOSUSPEND_DELAY`) :3402-3410 → `tb_switch_debugfs_init` :3412. Error unwind `err_ports`/`err_del` :3415-3419.
- **Remove**: `tb_switch_remove` :3430 → debugfs remove, `pm_runtime_get_sync`+`disable`, recursive child removal :3444, xdomain removal, retimer removal, `tb_plug_events_active(false)`, `tb_switch_nvm_remove`, `usb4_switch_remove_ports`, `device_unregister` :3468.
- **Refcount**: `tb_switch_get`/`tb_switch_put` tb.h:878/885. The **put that frees** is the final `put_device` (from `device_unregister` in `tb_switch_remove`, or `tb_switch_put` on the alloc-only error paths tb.c:1345/1376, tb.c:3020/3026) → `tb_switch_release` switch.c:2288 frees dma_port, hopid IDAs, uuid, device_name, vendor_name, ports, drom, key, sw.
- **Locks**: `tb->lock` (mutex, tb.h:85 "Big lock … must be held when accessing any struct tb_switch/tb_port") — taken with `mutex_trylock` + `restart_syscall()` in every sysfs store/show that touches hardware: switch.c:1823 (`tb_switch_set_authorized`), :1939 (key_show), :1962 (key_store), :2069 (nvm_authenticate_sysfs), :2159 (nvm_version_show), :290 (nvm_read), :313 (nvm_write). `nvm_auth_status_lock` (module-global mutex, switch.c:36) guards `nvm_auth_status_cache`. `nvm_ida` (nvm.c:29) module-global IDA for nvmem ids.
- **State fields / transitions**: `config.enabled` 0 at alloc → 1 at configure (also the `tb_switch_is_icm` discriminator); `is_unplugged` false → true (one-way, `tb_sw_set_unplugged`); `authorized` 0→1/2 or →0 (guarded by `tb->lock`, uevent `AUTHORIZED=n`); `nvm->authenticating` false→true at `nvm_authenticate`; `nvm->flushed` set by `nvm_validate_and_write`, cleared by `tb_nvm_write_buf`; `no_nvm_upgrade` latched true on any NVM init failure.
- **Runtime PM**: `tb_switch_runtime_suspend/resume` switch.c:2347/2358 route to `cm_ops->runtime_{suspend,resume}_switch` — **ICM-only callbacks**, so no-ops under the SW CM.

#### 4. Hard-coded limits

| Constant / literal | Value | Anchor |
|---|---|---|
| `TB_ROUTE_SHIFT` | 8 | tb_regs.h:19 |
| `TB_MAX_CONFIG_RW_LENGTH` | 60 | tb_regs.h:26 |
| `TB_SWITCH_KEY_SIZE` | 32 | tb.h:74 |
| `TB_SWITCH_MAX_DEPTH` | 6 | tb.h:75 |
| `USB4_SWITCH_MAX_DEPTH` | 5 | tb.h:76 |
| `TB_AUTOSUSPEND_DELAY` | 15000 ms | tb.h:550 |
| `CAP_OFFSET_MAX` | 0xff — **defined but unused** | cap.c:14 |
| `VSE_CAP_OFFSET_MAX` | 0xffff | cap.c:15 |
| `TMU_ACCESS_EN` | BIT(20) | cap.c:16 |
| `USB4_DATA_RETRIES` | 3 | usb4.c:18 |
| `USB4_DATA_DWORDS` | 16 | usb4.c:19 |
| router-op OV wait | 500 ms | usb4.c:79 |
| Router Ready (RR) wait | 500 ms | usb4.c:302 |
| Configuration Ready (CR) wait | 500 ms | usb4.c:335 |
| Sleep Ready (SLPR) wait | 500 ms | usb4.c:524 |
| NVM sector-size "unsupported" status | 0x2 | usb4.c:548 |
| `tb_switch_wait_for_bit` poll | `usleep_range(50, 100)` | switch.c:1739 |
| device NVM auth poll | 10 retries × `msleep(500)` | switch.c:169, 206 |
| Notification Timeout | `plug_events_delay = 0xff` (255 ms) | switch.c:2620 |
| plug-events enable/disable masks | `0xFFFFFF83` / `0x7c` | switch.c:1763, 1779 |
| `authorized` max value | 2 | switch.c:1884 |
| `NVM_MIN_SIZE` / `NVM_MAX_SIZE` / `NVM_DATA_DWORDS` | SZ_32K / SZ_1M / 16 | nvm.c:15-17 |
| Intel NVM offsets DEVID/VERSION/CSS/FLASH_SIZE | 0x05 / 0x08 / 0x10 / 0x45 | nvm.c:20-23 |
| ASMedia NVM DATE/VERSION | 0x1c / 0x28; fixed size SZ_512K | nvm.c:26-27, 183 |
| Intel header size | SZ_8K (gen<3) / SZ_16K; 4K alignment | nvm.c:74, 107 |
| `DMA_PORT_CAP` | 0x3e | dma_port.c:16 |
| `MAIL_DATA` / `MAIL_DATA_DWORDS` / `MAIL_IN` / `MAIL_OUT` | 1 / 16 / 17 / 18 | dma_port.c:18-35 |
| `DMA_PORT_TIMEOUT` / `DMA_PORT_RETRIES` | 5000 ms / 3 | dma_port.c:44-45 |
| DMA-port completion inner read timeout | 50 ms; poll `usleep_range(50,100)` | dma_port.c:243, 251 |
| update_auth / power_cycle timeout | 150 ms (bare literal, both) | dma_port.c:403, 459 |
| DMA/NHI port candidates | `{3, 5, 7}` | dma_port.c:170 |
| `DMA_PORT_CSS_ADDRESS` / `_MAX_SIZE` | 0x3fffff / SZ_128 | dma_port.h:18-19 |
| `TB_DROM_DATA_START` / `TB_DROM_HEADER_SIZE` / `USB4_DROM_HEADER_SIZE` | 13 / 22 / 16 | eeprom.c:217-219 |
| DROM size mask / size fixup | `0x3ff`; `+= 1 + 8 + 4` | eeprom.c:572; 524, 552 |
| DROM offset ceiling | 0xffff | eeprom.c:156 |
| DROM size field offset | byte 14 | eeprom.c:518, 547, 568 |
| EEPROM read opcode | 3 | eeprom.c:183 |
| USB3 max-bandwidth quirk | 16376 Mb/s | quirks.c:43 |
| DP-main credits quirk | 56 → 18 | quirks.c:18-19 |
| Titan Ridge CLx NVM cutoff | major ≥ 0x65 | quirks.c:26 |

#### 5. Version-specific facts (v7.2)

- **Added** `tb_switch_nvm_init()` switch.c:328 (split out of `tb_switch_nvm_add`); `tb_switch_nvm_add` switch.c:358 now consumes `sw->nvm`. Called from `tb_switch_add` switch.c:3313 [errata 2026-09-10, write time of router/router-device-model.md: switch.c:3315 on disk] [errata 2026-09-12, write time of router/router-lifecycle.md: switch.c:3315 is the `tb_switch_nvm_init` call; `tb_switch_nvm_add` is called at switch.c:3389, after `device_add` at :3369 and `usb4_switch_add_ports`; `device_init_wakeup` is at :3400, `pm_runtime_set_active` at :3402, `err_ports:` at :3414 and `err_del:` at :3416; `tb_switch_nvm_init` is defined at :328] **before** `tb_check_quirks`, so quirks can read `sw->nvm->major` (commit 4573add760b8).
- **Removed** `nvm_authenticate_start_dma_port()` / `nvm_authenticate_complete_dma_port()` (were switch.c, v7.0) → replaced by `nhi->ops->pre_nvm_auth` / `post_nvm_auth` at switch.c:249-250, 2784-2785, 2801-2802 (commits e241d98e04ef, dd60fb487e55).
- **Added** `ROUTER_CS_6_RR` BIT(24) tb_regs.h:218 and the Router Ready wait in `usb4_switch_setup` usb4.c:301-302 (commit 062023c4364f).
- **Changed** Configuration Ready timeout 50 ms → 500 ms, usb4.c:335 (commit ba2cc3851101).
- **Changed** Notification Timeout: `plug_events_delay = 0xff` for *all* routers in `tb_switch_configure` switch.c:2620; the old `0xa` USB4 value and the separate dword-4 write inside `tb_plug_events_active` are gone; ROUTER_CS_1 write length 3 → **4** switch.c:2651; tb_regs.h:183-186 comment lost the "writing 0x00 == 255ms" note (commit e24f3c0df483).
- **Changed** `tb_switch_reset_host` skips path-config cleanup for USB4 Lane 1 adapters (`tb_switch_is_usb4(sw) && !port->usb4` → continue) switch.c:1601-1606 (commit 95c4379e37a0).
- **Changed** `tb_drom_parse_entry_port` rejects `dual_link_port_nr > max_port_number` eeprom.c:398-403 (commit d6764992f17b).
- **Changed** `struct tb_dma_port.buf` pointer → flex array dma_port.c:58; `dma_port_alloc` uses `kzalloc_flex(*dma, buf, MAIL_DATA_DWORDS)` :212; `dma_port_free` is now a bare `kfree` :227 (commit 500e54d449f6).
- **Changed** `tb_switch_lane_bonding_enable` returns `-EOPNOTSUPP` (was 0) switch.c:2957, 2964 (commit 0ab47718345d).
- **Changed** print macros `tb_err/tb_WARN/tb_warn/tb_info/tb_dbg` now `dev_*((tb)->nhi->dev, …)` (was `&(tb)->nhi->pdev->dev`) tb.h:729-733; `tb_drom_copy_efi` uses `sw->tb->nhi->dev` eeprom.c:475 (commit 8c3ff7c5ae15).
- **Added** quirk row `{0x8086, PCI_DEVICE_ID_INTEL_TITAN_RIDGE_DD_BRIDGE, …, quirk_clx_disable}` quirks.c:69-70 and the NVM ≥ 0x65 escape in `quirk_clx_disable` quirks.c:26 (commits 59b03d12b1f6, 4573add760b8).
- **Added** `tb_switch_resume` XDomain-replaced-by-router handling switch.c:3611-3624 (commit a8937f35cf39).
- Relative to older widely-documented kernels: allocation spellings changed at v7.0 (`kzalloc_obj` switch.c:2473/2574, `kzalloc_objs` :2501, `kzalloc_flex` dma_port.c:212 — commit 69050f8d6d07); `tb_switch_wait_for_bit` lives in switch.c since v5.17 (was `usb4_switch_wait_for_bit`, commit 1639664fb74f); `tb_switch_configuration_valid` exists since v6.5 (commit d49b4f043d63).

#### 6. Suggested page topics (one mechanism per page)

1. `struct tb_switch` field-by-field reference — tb.h:171, with ICM-only fields flagged.
2. Router config-space header on the wire: `struct tb_regs_switch_header` ↔ ROUTER_CS_0..4 — tb_regs.h:166-201.
3. Route strings: `tb_route`, `TB_ROUTE_SHIFT`, `tb_route_length`, `tb_downstream_route`, `tb_port_at` — tb.h:583, 1240, 1253, 587.
4. Uploading the route/topology ID: `tb_switch_configure` ROUTER_CS_1..4 write — switch.c:2605.
5. Router capability walk: `tb_switch_next_cap`/`find_cap`/`find_vse_cap` and the four cached offsets — cap.c:154-256, switch.c:2519-2534.
6. USB4 router-operation mailbox: ROUTER_CS_25/26/9 and `usb4_native_switch_op` — usb4.c:54.
7. The `cm_ops->usb4_switch_op` proxy seam and why the SW CM never sets it — usb4.c:109-140, tb.c:3287.
8. `usb4_switch_setup` and tunnel enablement bits (ROUTER_CS_5 UTO/PTO/HCO/CNS, ROUTER_CS_6 HCI/TNS/RR) — usb4.c:243.
9. Configuration Valid handshake: `tb_switch_configuration_valid` → CV/CR — switch.c:2669, usb4.c:316.
10. Router allocation and the ports array — `tb_switch_alloc` switch.c:2451.
11. `tb_switch_add` ordering contract (DMA port → NVM init → DROM → ports → quirks → device_add → USB4 ports → NVM add) — switch.c:3298.
12. `tb_switch_remove`/`tb_switch_release` teardown and refcounting — switch.c:3430, 2288.
13. Router device model: `tb_switch_type`, `tb_bus_type` (domain.c:311/897), naming `%u-%llx`, uevent vars — switch.c:2373, 2309, 2544.
14. Router sysfs attribute group and `switch_attr_is_visible` decision table — switch.c:2202-2286.
15. Authorization state machine and the domain approve seams — switch.c:1819, domain.c:638-757.
16. Secure connect: `key` attribute, HMAC challenge, and why it is ICM-only — switch.c:1932-1982, domain.c:715.
17. DROM acquisition paths (EFI / DMA-port NVM / router op / bit-bang) — eeprom.c:674-731.
18. DROM parsing and validation (crc8/crc32, generic vs port entries, dual-link pairing) — eeprom.c:326-672.
19. Router NVM object and vendor-ops dispatch — nvm.c:37-197, 289.
20. `nvm_authenticate` sysfs flow and the `nvm_auth_status` cache — switch.c:23-96, 2061-2151.
21. DMA-port mailbox protocol (MAIL_IN/MAIL_OUT, commands, polling) — dma_port.c:16-45, 271.
22. Router reset: `tb_switch_reset`, host vs device, enumerated check — switch.c:1651-1707.
23. `tb_switch_wait_for_bit` as the router polling primitive and its four USB4 users — switch.c:1723. [Orchestrator note 2026-09-04, refuted at write time (router-config-space.md): five callers at v7.2, the four in usb4.c (:79 OV, :301 RR, :334 CR, :523 SLPR, all 500 ms) plus `tb_switch_pcie_bridge_write` at switch.c:3918 waiting 100 ms on a plug-events capability register.]
24. Wake and sleep programming: `tb_switch_set_wake`/`suspend`/`check_wakes`, ROUTER_CS_5/6 bits — switch.c:3492-3690, usb4.c:426, 507.
25. Router suspend/resume re-enumeration and UID identity check — switch.c:3525.
26. Generation and USB4 version detection: `tb_switch_get_generation`, `usb4_switch_version`, CMUV programming — switch.c:2380, tb.h:1311, switch.c:2626-2631.
27. Quirk table mechanism (`tb_quirk`, `tb_check_quirks`, the three flags) — quirks.c:55-144, tb.h:24-28.
28. Router credit/buffer-allocation discovery: BUFFER_ALLOC and `usb4_switch_credits_init` — usb4.c:758.
29. DP resource query/alloc/dealloc at the router level (USB4 op vs LC sink) — switch.c:3692-3757.
30. Link controller router-level registers (uuid, sleep, wake, force power) and their pre-USB4 scope — lc.c:20, 428, 469, 712.
31. Router debugfs surface (`regs`, `drom` blob, per-port dirs) — debugfs.c:2418.
32. Adapter-index mapping: `usb4_port_index`, `map_pcie_down`, `map_usb3_down` — usb4.c:982-1076.
33. Router lookup helpers and which are ICM-only — switch.c:3759-3872.
34. `tb_switch_is_icm` and the ICM/SW-CM branch points across the router code — tb.h:1023.

#### 7. Tracing integration

**Verified negative.** `grep -n "trace_\|trace_printk\|CREATE_TRACE_POINTS\|#include \"trace.h\"" ` over switch.c, cap.c, eeprom.c, nvm.c, dma_port.c, quirks.c, usb4.c, lc.c, tb.h, tb_regs.h → no matches. The only tracepoints in the subsystem are in the control channel: `trace_tb_tx` ctl.c:388, `trace_tb_event` ctl.c:405, `trace_tb_rx` ctl.c:512, defined in drivers/thunderbolt/trace.h (`#include <trace/define_trace.h>` :197). Router config reads/writes are therefore traced only indirectly, as `TB_CFG_SWITCH` packets on the control channel.

#### 8. Debug and diagnostic printing

- Macros: `tb_err/tb_WARN/tb_warn/tb_info/tb_dbg` tb.h:729-733 (→ `dev_*((tb)->nhi->dev, …)`); `__TB_SW_PRINT` tb.h:735 with `tb_sw_WARN`/`tb_sw_warn`/`tb_sw_info`/`tb_sw_dbg` tb.h:741-744 (prefix `"%llx: "` = route string); `__TB_PORT_PRINT` tb.h:746 with `tb_port_WARN/warn/info/dbg` :752-759.
- Per-file counts (grep occurrences): switch.c — `tb_sw_dbg` 17, `tb_sw_warn` 10, `tb_sw_info` 7, `tb_sw_WARN` 2, `tb_dbg` 13, `dev_err/warn/info` 10, `WARN_ON*` 3, `tb_port_dbg/warn` 19. usb4.c — `tb_sw_dbg` 10, `tb_sw_warn` 6, `WARN_ON` 4, `tb_port_dbg` 3. eeprom.c — `tb_sw_warn` 14, `tb_sw_dbg` 2, `dev_info_once` 1. quirks.c — `tb_sw_dbg` 5, `tb_port_dbg` 1. lc.c — `tb_port_dbg` 4. cap.c — `tb_sw_dbg` 1. nvm.c — `tb_sw_dbg` 1, `dev_dbg` 1. dma_port.c — none.
- Control knobs: everything routes through `dev_dbg`, so **dynamic debug** (`CONFIG_DYNAMIC_DEBUG`, `dyndbg=+p` on `thunderbolt`) is the only gate; there is no module parameter for verbosity in this area. `tb_dump_switch` switch.c:1563 is the one-shot router dump emitted from `tb_switch_alloc` switch.c:2485.

#### 9. Asynchronous, deferred, lazy processing

- **Work items / delayed work / timers in this area: none.** `grep` for `INIT_WORK|INIT_DELAYED_WORK|queue_work|queue_delayed_work|schedule_work|timer_setup|mod_timer` over switch.c, cap.c, eeprom.c, nvm.c, dma_port.c, quirks.c, lc.c returns no matches. (The SW CM's hotplug work `tb_handle_hotplug` tb.c:2421 is the neighbouring area's; it *calls into* `tb_switch_alloc/add/remove` from the domain workqueue.)
- **Completion: one, ICM-only** — `sw->rpm_complete` tb.h:208, `init_completion` icm.c:657, `complete()` icm.c:700. No SW CM use.
- **Polling loops**:
  - `tb_switch_wait_for_bit` switch.c:1723 — `usleep_range(50, 100)` per iteration, caller timeout; four call sites all 500 ms: usb4.c:79 (OV), :302 (RR), :335 (CR), :524 (SLPR) [orchestrator note 2026-09-04: refuted at write time, five call sites; the fifth is switch.c:3918 in `tb_switch_pcie_bridge_write`, 100 ms; the usb4.c sites are at :79/:301/:334/:523 on disk]. Process context, under `tb->lock`.
  - `dma_port_wait_for_completion` dma_port.c:232 — `usleep_range(50, 100)`, jiffies deadline; 5000 ms for read/write, 150 ms for update_auth/power_cycle; inner control read timeout 50 ms (dma_port.c:243). Process context.
  - `nvm_authenticate_device_dma_port` switch.c:167 — 10 iterations × `msleep(500)` polling `dma_port_flash_update_auth_status`; ≈5 s worst case; runs from the `nvm_authenticate` sysfs store under `tb->lock` with runtime PM held.
- **Deferred/lazy**: runtime PM autosuspend armed in `tb_switch_add` — `pm_runtime_set_autosuspend_delay(TB_AUTOSUSPEND_DELAY)` switch.c:3404 and `pm_request_autosuspend` :3409 (only when `sw->rpm`). Every sysfs entry point does `pm_runtime_get_sync` / `pm_runtime_mark_last_busy` / `pm_runtime_put_autosuspend` (switch.c:1886-1890, 2066, 2119-2121, 288-303). Gated by CONFIG_PM (`__maybe_unused` on switch.c:2347/2358).
- **Retry loops (not sleeping)**: `tb_nvm_read_data` nvm.c:560 / `tb_nvm_write_data` nvm.c:607 — `retries` decremented on failure; `USB4_DATA_RETRIES` 3, `DMA_PORT_RETRIES` 3.

#### 10. Subsystem-specific debugging infrastructure

- **sysfs (router)**: `switch_attrs[]` switch.c:2202, `switch_attr_is_visible` switch.c:2222, `switch_group`/`switch_groups` :2278/:2283. Attributes: `authorized` (RW, :1894 — hidden at NOPCIE/DPONLY), `boot` (RO :1903 — device routers only), `device` (:1912), `device_name` (:1921), `generation` (:1930), `key` (0600 :1982 — visible only when domain **and** router security_level are SECURE, i.e. **ICM-only in practice**), `nvm_authenticate` (RW :2135 — visible iff `nvm_upgradeable`), `nvm_authenticate_on_disconnect` (RW :2151 — visible **only** with `QUIRK_FORCE_POWER_LINK_CONTROLLER`), `nvm_version` (RO :2173 — iff `nvm_readable`), `rx_speed`/`tx_speed` (0444 :1996/:1997), `rx_lanes`/`tx_lanes` (0444 :2023/:2049) — all four device-routers-only, `vendor` (:2182), `vendor_name` (:2191), `unique_id` (:2200). Safe-mode routers expose only the attributes with an explicit early return (switch.c:2275).
- **debugfs**: `tb_switch_debugfs_init` debugfs.c:2418 / `tb_switch_debugfs_remove` :2462 — `<domain>-<route>/regs` (mode `DEBUGFS_MODE` = 0600 under **CONFIG_USB4_DEBUGFS_WRITE**, else 0400; debugfs.c:446/453), `drom` blob 0400 (only if `sw->drom`, debugfs.c:2428, needs CONFIG_DEBUG_FS for `sw->drom_blob`), per-port `regs`/`path`/`counters`/`sb_regs`, plus `margining_switch_init` (**CONFIG_USB4_DEBUGFS_MARGINING**).
- **KUnit (CONFIG_USB4_KUNIT_TEST, drivers/thunderbolt/test.c, suite name "thunderbolt" test.c:3148)**: `alloc_switch` test.c:36 fabricates `struct tb_switch` with `tb_route_length`/`route_hi`/`route_lo` (test.c:48-50) and a `kunit_kzalloc` ports array; `alloc_host` :72, `alloc_host_usb4` :154, `alloc_host_br` :173, `alloc_dev_default` :190, `alloc_dev_usb4` :402. **Verified negative: no KUNIT_CASE exercises router lifecycle, DROM parsing, NVM, capability walk, or router operations** — the 45 cases (test.c:3099-3145) cover paths, tunnels, credit allocation and XDomain properties only; the router struct appears purely as a fixture, and `tb_route()`/`tb_port_at()` are exercised incidentally by the path-walk cases (e.g. test.c:511, 523).
- **ConfigFS** (**CONFIG_USB4_CONFIGFS**, drivers/thunderbolt/configfs.c, new at v7.2) does not expose router-level knobs in this area.

#### 11. v7.0 → v7.2 drift ledger

`git log --oneline v7.0..v7.2` over the area paths → 21 commits; `git diff --stat` → dma_port.c 15, eeprom.c 11, quirks.c 7, switch.c 107, tb.c 88, tb.h 26, tb_regs.h 19, usb4.c 35 (198 insertions / 110 deletions). cap.c, nvm.c, lc.c, dma_port.h **unchanged**.

Symbol-level changes:
- **Removed** `nvm_authenticate_start_dma_port` (v7.0 switch.c:212) and `nvm_authenticate_complete_dma_port` (v7.0 switch.c:227) — no replacement symbol; call sites now `nhi->ops->pre_nvm_auth` (switch.c:249-250) and `nhi->ops->post_nvm_auth` (switch.c:2784-2785, 2801-2802). *A v7.0 page describing PCIe-root-port D0 pinning inside switch.c is now wrong — that logic moved behind `nhi->ops`.* (e241d98e04ef, dd60fb487e55)
- **Added** `tb_switch_nvm_init` switch.c:328 (no v7.0 counterpart); `tb_switch_nvm_add` moved v7.0 switch.c:350 → v7.2 switch.c:358 and lost its `tb_nvm_alloc`/`tb_nvm_read_version` body. *NVM version is now known before `tb_check_quirks` runs.* (4573add760b8)
- **Added** `ROUTER_CS_6_RR` tb_regs.h:218 (new macro). *`usb4_switch_setup` no longer returns immediately after the ROUTER_CS_5 write; it blocks up to 500 ms for Router Ready.* (062023c4364f)
- **Changed value** CR wait 50 → 500 ms, usb4.c:335 (v7.0 usb4.c:330). (ba2cc3851101)
- **Moved behavior** `plug_events_delay` programming: v7.0 `tb_plug_events_active` wrote dword 4 with 0xff for legacy routers and `tb_switch_configure` set 0xa for USB4; v7.2 sets 0xff once in `tb_switch_configure` switch.c:2620 and widens the ROUTER_CS_1 write from 3 to 4 dwords switch.c:2651. *Any page saying "USB4 routers get a 10 ms notification timeout" or "plug_events_delay is written by tb_plug_events_active" is now wrong.* (e24f3c0df483)
- **Behavior** `tb_switch_reset_host` switch.c:1601-1606 now `continue`s for USB4 lane-1 adapters instead of walking their path config space. *A v7.0 page saying host reset clears path config on every lane adapter now misstates it.* (95c4379e37a0)
- **Behavior** `tb_drom_parse_entry_port` eeprom.c:398-403 now returns `-EIO` on out-of-range `dual_link_port_nr`; previously indexed `sw->ports[]` unchecked. (d6764992f17b)
- **Struct change** `tb_dma_port.buf` `u8 *` → `u8 buf[]` dma_port.c:58; `dma_port_alloc` no longer does a second allocation and `dma_port_free` no longer frees `dma->buf`. (500e54d449f6)
- **Behavior** `tb_switch_lane_bonding_enable` switch.c:2957/2964 returns `-EOPNOTSUPP` where v7.0 returned 0. *Callers/log text differ.* (0ab47718345d)
- **Macro change** `tb_err/tb_WARN/tb_warn/tb_info/tb_dbg` tb.h:729-733 dereference `(tb)->nhi->dev` instead of `&(tb)->nhi->pdev->dev`; `tb_drom_copy_efi` eeprom.c:475 likewise. *`struct tb_nhi` no longer carries `pdev` for these paths.* (8c3ff7c5ae15)
- **Data change** quirks.c gains the Titan Ridge DD bridge `quirk_clx_disable` row (:69-70) and `quirk_clx_disable` gains the `nvm->major >= 0x65` bypass (:26). *A v7.0 page listing the quirk table is now short one row and misses the NVM-version escape.* (59b03d12b1f6, 4573add760b8)
- **Behavior** `tb_switch_resume` switch.c:3611-3624 adds detection of an XDomain replaced by a router. (a8937f35cf39)
- Adjacent-but-relevant: `tb->root_switch` is set to `NULL` after `tb_switch_remove` in `tb_stop` tb.c:2959-2960 (e56249d8a68e); `tb_start` error paths now use `dev_err_probe` tb.c:3003, 3020, 3027 (15bcac35ba04).
- **No symbol renames or cross-file moves** occurred in this area between v7.0 and v7.2.

#### 12. Kernel documentation and ABI

- **Documentation/admin-guide/thunderbolt.rst** sections touching this area: "Security levels and how to use them" :24-100 (maps `enum tb_security_level` to the `security` domain attribute); "Authorizing devices when security level is user or secure" :101-162 (`authorized`, `key`); "De-authorizing devices" :163-178; "DMA protection utilizing IOMMU" :179-198; "Upgrading NVM on Thunderbolt device, host or retimer" :199-240; "Upgrading firmware manually" :241-279; "Upgrading on-board retimer NVM when there is no cable connected" :280-307 [errata 2026-09-10, write time of router/router-device-model.md: the heading is at :279 on disk]; "Upgrading NVM when host controller is in safe mode" :308-319; "Tunneling events" :319-351.
- **Documentation/ABI/testing/sysfs-bus-thunderbolt** entries for the router device: `authorized` :64, `boot` :98, `generation` :105, `key` :113, `device` :123, `device_name` :130, `rx_speed` :144, `rx_lanes` :151, `tx_speed` :158, `tx_lanes` :165, `vendor` :172, `vendor_name` :179, `unique_id` :186, `nvm_version` :195, `nvm_authenticate` :204, `nvm_authenticate_on_disconnect` :232. (`maxhopid` :137 is the XDomain attribute, xdomain.c:1894 — not this area.) Domain-level context: `boot_acl` :1, `deauthorization` :24, `iommu_dma_protection` :33, `security` :42.
- **Kerneldoc blocks** (counts of `/**` openers): usb4.c 73, switch.c 59, tb.h 34, lc.c 19, nvm.c 12, dma_port.c 8, cap.c 5, tb_regs.h 3, eeprom.c 2, quirks.c 1; dma_port.h 0. Key struct blocks: `struct tb_nvm` tb.h:30-51, `struct tb_switch` tb.h:111-170, `struct tb_switch_tmu` tb.h:96-104, `struct tb_cap_extended_short` tb_regs.h:67-75, `struct tb_cap_extended_long` tb_regs.h:80-91, `struct tb_cap_any` tb_regs.h:100-106, `struct tb_nvm_vendor_ops` nvm.c:31-41, `struct tb_nvm_vendor` nvm.c:43-54, `struct tb_dma_port` dma_port.c:47-53, `enum tb_security_level` include/linux/thunderbolt.h:46-57.
- **Verified negative**: no `.. kernel-doc:: drivers/thunderbolt/...` directive exists anywhere under Documentation/ (`grep -rn "kernel-doc:: drivers/thunderbolt" Documentation/` → no matches), so none of these kerneldoc blocks are rendered into the kernel docs build; they exist only for in-tree readers and `scripts/kernel-doc` checks.

### Area B: Domain, connection manager, XDomain — COMPLETE (recorded 2026-09-04)

Scope note: software CM only. ICM (icm.c, `icm_*_ops`, `icm_*`) is not inventoried; generic symbols that exist only for ICM are flagged **[ICM-only]**.

#### 1. Core structs

**`struct tb`** — include/linux/thunderbolt.h:82 (kerneldoc :67). Allocated `kzalloc(sizeof(*tb) + privsize)` in `tb_domain_alloc()`.
- `dev` — domain device, name `domain%d`, bus `tb_bus_type`, type `tb_domain_type`; written domain.c:408-413.
- `lock` — "big lock"; must be held to touch any `tb_switch`/`tb_port`; `mutex_init` domain.c:394, destroyed domain.c:327.
- `nhi` — back pointer to host interface; written domain.c:393 (only).
- `ctl` — control channel; `tb_ctl_alloc()` domain.c:404, freed domain.c:324; started/stopped under `tb->lock` (domain.c:451, 509, 541, 561, 582, 593, 614, 620).
- `wq` — ordered workqueue `"thunderbolt%d"`, flags `0`, domain.c:400; destroyed domain.c:325.
- `root_switch` — host router; set tb.c:3001 (`tb_start`), cleared tb.c:2960 (`tb_stop`, new at v7.2); ICM writers icm.c:2203/2205/2218/2230.
- `cm_ops` — CM vector; set tb.c:3388 (`&tb_cm_ops`) or icm.c:2505..2594.
- `index` — ida-allocated domain number, domain.c:396; freed domain.c:326.
- `security_level` — `enum tb_security_level`; software CM sets it tb.c:3384/3386 only; **[ICM-only]** otherwise from firmware (icm.c:2021).
- `nboot_acl` — number of boot ACLs; **[ICM-only]** (written icm.c:2021/2031; no software-CM writer).
- `privdata[]` — flexible CM private area, reached via `tb_priv()` tb.h:545.

**`struct tb_cm_ops`** — drivers/thunderbolt/tb.h:507 (kerneldoc :471). Every callback + domain.c invoker + whether the software instance fills it:

| callback | invoker | sw CM |
|---|---|---|
| `driver_ready` :508 | domain.c:453-454 | no **[ICM-only]** |
| `start(tb, reset)` :509 | domain.c:467-468 | yes → `tb_start` |
| `stop` :510 | domain.c:506-507 | yes → `tb_stop` |
| `deinit` :511 | domain.c:514-515 (no `tb->lock`) | yes → `tb_deinit` |
| `suspend_noirq` :512 | domain.c:538 | yes |
| `resume_noirq` :513 | domain.c:562 | yes |
| `suspend` :514 | domain.c:571 | no **[ICM-only]** |
| `freeze_noirq` :515 | domain.c:579 | yes |
| `thaw_noirq` :516 | domain.c:594 | yes |
| `complete` :517 | domain.c:603 | yes |
| `runtime_suspend` :518 | domain.c:609 | yes |
| `runtime_resume` :519 | domain.c:621 | yes |
| `runtime_suspend_switch` :520 | switch.c:2352 (not domain.c) | no **[ICM-only]** |
| `runtime_resume_switch` :521 | switch.c:2363 | no **[ICM-only]** |
| `handle_event` :522 | domain.c:343/356 (`tb_domain_event_cb`) | yes |
| `get_boot_acl` :524 | domain.c:139, visibility :292 | no **[ICM-only]** |
| `set_boot_acl` :525 | domain.c:218, visibility :293 | no **[ICM-only]** |
| `disapprove_switch` :526 | domain.c:640-643; also gates `deauthorization` sysfs domain.c:247 | yes → `tb_disconnect_pci` |
| `approve_switch` :527 | domain.c:661/669/700/744 | yes → `tb_tunnel_pci` |
| `add_switch_key` :528 | domain.c:688/696 | no **[ICM-only]** |
| `challenge_switch_key` :529 | domain.c:723/732 | no **[ICM-only]** |
| `disconnect_pcie_paths` :531 | domain.c:758/761 | no **[ICM-only]** |
| `approve_xdomain_paths` :532 | domain.c:786/789 | yes → `tb_approve_xdomain_paths` |
| `disconnect_xdomain_paths` :535 | domain.c:815/818 | yes → `tb_disconnect_xdomain_paths` |
| `usb4_switch_op` :538 | usb4.c:123/126 | no **[ICM-only]** |
| `usb4_switch_nvm_authenticate_status` :541 | usb4.c:721/722 | no **[ICM-only]** |

Software instance, verbatim member list — `static const struct tb_cm_ops tb_cm_ops` tb.c:3287-3303: `.start = tb_start`, `.stop = tb_stop`, `.deinit = tb_deinit`, `.suspend_noirq = tb_suspend_noirq`, `.resume_noirq = tb_resume_noirq`, `.freeze_noirq = tb_freeze_noirq`, `.thaw_noirq = tb_thaw_noirq`, `.complete = tb_complete`, `.runtime_suspend = tb_runtime_suspend`, `.runtime_resume = tb_runtime_resume`, `.handle_event = tb_handle_event`, `.disapprove_switch = tb_disconnect_pci`, `.approve_switch = tb_tunnel_pci`, `.approve_xdomain_paths = tb_approve_xdomain_paths`, `.disconnect_xdomain_paths = tb_disconnect_xdomain_paths`.

**`struct tb_cm`** — tb.c:64 (kerneldoc :52). Lives in `tb->privdata`; `tcm_to_tb()` tb.c:72 reverses it by pointer arithmetic (`(void *)tcm - sizeof(struct tb)`).
- `tunnel_list` — active tunnels; INIT tb.c:3391 (tunnel area owns entries).
- `dp_resources` — available DP IN resources; INIT tb.c:3392.
- `hotplug_active` — gate for `tb_handle_hotplug`; set true tb.c:3073 (`tb_start`), 3197 (`tb_resume_noirq`), 3215 (`tb_thaw_noirq`), 3275 (`tb_runtime_resume`); false tb.c:2961, 3085, 3207, 3244.
- `remove_work` — delayed work → `tb_remove_work`; INIT tb.c:3393.
- `groups[MAX_GROUPS]` — bandwidth groups (bandwidth area); `tb_init_bandwidth_groups()` tb.c:3394.

**`struct tb_hotplug_event`** — tb.c:77. Shared by two work handlers.
- `work` — `struct delayed_work`; `INIT_DELAYED_WORK` tb.c:105 (hotplug) / tb.c:2881 (DP BW).
- `tb` — domain; holds a domain reference since v7.2 (tb.c:101 `tb_domain_get`, released tb.c:2533).
- `route` — router route string; `port` — adapter number; `unplug` — plug vs unplug.
- `retry` — retry counter, used only by `tb_handle_dp_bandwidth_request` (tb.c:2765, 2830-2836).

**`struct tb_xdomain`** — include/linux/thunderbolt.h:250 (kerneldoc :198).
- `dev` — device, name `"%u-%llx"` (domain index, route) xdomain.c:2169; type `tb_xdomain_type`.
- `tb`, `route` — owning domain / route to the remote host.
- `remote_uuid` — remote host UUID (filled by UUID exchange xdomain.c:1394); `local_uuid` — cached local UUID copy.
- `vendor`, `device` — IDs from remote properties (`populate_properties` xdomain.c:1286/1291).
- `local_max_hopid` — from downstream adapter `max_in_hop_id` (xdomain.c:2139); `remote_max_hopid` — from remote `maxhopid` property or `XDOMAIN_DEFAULT_MAX_HOPID`.
- `lock` — serializes the fields below; taken under `xdomain_lock` when both needed.
- `vendor_name`, `device_name` — optional text properties.
- `link_speed`, `link_width` — refreshed by `tb_xdomain_update_link_attributes()` xdomain.c:1317.
- `link_usb4` — set only in usb4.c:1290 (`usb4_port_configure_xdomain`); read by usb4_port.c:57.
- `is_unplugged` — set tb.c:2488 (hotplug unplug), xdomain.c:1388 (UUID mismatch).
- `removing` — **new at v7.2**; set under `xd->lock` in `tb_xdomain_remove()` xdomain.c:2229; every external queue site checks it (xdomain.c:814, 832, 904, 995).
- `needs_uuid` — set when allocated without remote UUID (xdomain.c:2159); drives `XDOMAIN_STATE_INIT` branch.
- `service_ids`, `in_hopids`, `out_hopids` — idas; init xdomain.c:2140-2142, destroyed xdomain.c:2023-2025.
- `local_property_block`, `_gen`, `_len` — packed local property block, rebuilt by `update_property_block()` xdomain.c:674.
- `remote_properties`, `remote_property_block_gen` — parsed remote directory; only newer generations accepted (xdomain.c:1566).
- `state`, `state_work`, `state_retries` — discovery state machine (see §3).
- `properties_changed_work`, `properties_changed_retries` — outbound PROPERTIES_CHANGED notification.
- `bonding_possible` — set in `tb_xdomain_link_init()` xdomain.c:2070; cleared on loopback xdomain.c:1378.
- `target_link_width` — set from a peer LINK_STATE_CHANGE request xdomain.c:905.
- `ntunnels` — **new at v7.2**; atomic tunnel count, inc/dec xdomain.c:2450/2481, read only by icm.c:590/1166 **[ICM-only consumer]**.
- `link`, `depth` — **[ICM-only]** (written icm.c:721/722/735; matched in `switch_find_xdomain` xdomain.c:2512).

**`struct tb_service`** — include/linux/thunderbolt.h:419 (kerneldoc :395).
- `dev` — device, name `"<xdomain>.<id>"` xdomain.c:1265; parent takes a reference (`get_device` xdomain.c:1263, dropped xdomain.c:1129).
- `id` — from `xd->service_ids` ida; freed in release xdomain.c:1126.
- `key` — protocol key (dir name); `prtcid`/`prtcvers`/`prtcrevs`/`prtcstns` — from `populate_service()` xdomain.c:1193-1204.
- `lock` — protects `local_properties`; `mutex_init` xdomain.c:1264.
- `local_properties` — **new at v7.2**; driver-owned dir merged into the local block (xdomain.c:668-670).
- `remote_properties` — copy of the remote service dir; refreshed by `update_service()` xdomain.c:1146.
- `debugfs_dir` — created xdomain.c:1267 / debugfs.c:2486 (gate `CONFIG_DEBUG_FS`).

**`struct tb_service_driver`** — include/linux/thunderbolt.h:466: `driver`, `probe`, `remove`, `shutdown`, `id_table`. `TB_SERVICE(key,id)` macro :474.
**`struct tb_service_id`** — **moved at v7.2** to include/linux/device-id/tb.h:28 (was include/linux/mod_devicetable.h). Fields `match_flags`, `protocol_key[9]`, `protocol_id`, `protocol_version`, `protocol_revision`, `driver_data`; flags `TBSVC_MATCH_PROTOCOL_{KEY,ID,VERSION,REVISION}` :10-13.
**`struct tb_protocol_handler`** — include/linux/thunderbolt.h:385: `uuid`, `callback` (return 1 = consumed), `data`, `list`.
**`struct tb_property_dir`** — include/linux/thunderbolt.h:114: `uuid` (NULL = root), `properties` list.
**`struct tb_property`** — include/linux/thunderbolt.h:139: `list`, `key[TB_PROPERTY_KEY_SIZE+1]`, `type`, `length` (dwords), `value` union {`dir`,`data`,`text`,`immediate`}.
**`enum tb_property_type`** — :119 (`UNKNOWN 0x00`, `DIRECTORY 0x44`, `DATA 0x64`, `TEXT 0x74`, `VALUE 0x76`). **`enum tb_security_level`** — :58 (`NONE,USER,SECURE,DPONLY,USBONLY,NOPCIE`), names table domain.c:112.
On-wire property structs (S, private to property.c): `tb_property_entry` :17, `tb_property_rootdir_entry` :26, `tb_property_dir_entry` :32.
**XDomain wire structs** — tb_msgs.h: `tb_xdomain_header` :516 (`route_hi`,`route_lo`,`length_sn`); `enum tb_xdp_type` :526; `tb_xdp_header` :541 (`xd_hdr`,`uuid`,`type`); `tb_xdp_error_response` :547; `tb_xdp_link_state_status` :552 / `_response` :556 (`status`,`slw`,`tlw`,`sls`,`tls`); `tb_xdp_link_state_change` :570 (`tlw`,`tls`) / `_response` :577; `tb_xdp_uuid` :587 / `_response` :591 (`src_uuid`,`src_route_hi/lo`); `tb_xdp_properties` :603 (`src_uuid`,`dst_uuid`,`offset`) / `_response` :611 (`offset`,`data_length`,`generation`,`data[]`); `tb_xdp_properties_changed` :636 / `_response` :641; `enum tb_xdp_error` :648.
Local helpers: `struct xdomain_request_work` xdomain.c:55 (`work`,`pkg`,`pkg_len` **new v7.2**,`tb`); `struct tb_xdomain_lookup` xdomain.c:2486; `struct unregister_context` domain.c:856 (**new v7.2**).

#### 2. API families

**Domain lifecycle** (tb.h:773-796 prototypes)
- `tb_domain_alloc()` domain.c:377 — alloc + ida + wq + ctl + device_initialize.
- `tb_domain_add(tb, reset)` domain.c:439 — ctl start → `driver_ready` → `device_add` → `cm_ops->start` → runtime-PM enable.
- `tb_domain_remove()` domain.c:503 — `stop` → ctl stop → `flush_workqueue` → `deinit` → `device_unregister`.
- `tb_domain_get()` (inline) tb.h:798; `tb_domain_put()` (inline) tb.h:805 → `put_device()`, last put runs `tb_domain_release()` domain.c:319 (frees ctl/wq/ida/lock/tb, then `complete(&nhi->domain_released)`).
- `tb_domain_init()` domain.c:886 (E via module init path) — `tb_configfs_init` (`CONFIG_CONFIGFS_FS`), `tb_debugfs_init` (`CONFIG_DEBUG_FS`), `tb_acpi_init` (`CONFIG_ACPI`), `tb_xdomain_init`, `bus_register(&tb_bus_type)`.
- `tb_domain_exit()` domain.c:912 — reverse + `ida_destroy` + `tb_nvm_exit`.
- Bus/type objects: `tb_bus_type` domain.c:311 (`.match=tb_service_match`, `.probe=tb_service_probe`, `.remove=tb_service_remove`, `.shutdown=tb_service_shutdown`); `tb_domain_type` domain.c:333; `tb_service_type` xdomain.c:1132 (E :1138); `tb_xdomain_type` xdomain.c:2050 (E :2055).
- Service bus ops (S): `match_service_id` domain.c:22, `__tb_service_match` :48, `tb_service_match` :71, `tb_service_probe` :76, `tb_service_remove` :88, `tb_service_shutdown` :98.
- `static DEFINE_IDA(tb_domain_ida)` domain.c:20.

**Domain sysfs** (group `domain_attr_group` domain.c:301; visibility `domain_attr_is_visible` domain.c:284)
- `boot_acl` RW — `boot_acl_show` domain.c:121 (S), `boot_acl_store` domain.c:161 (S), attr :235; visible only when `nboot_acl && get/set_boot_acl` → **[ICM-only]** in practice.
- `deauthorization` RO — `deauthorization_show` domain.c:237 (S), attr :251; reports `!!cm_ops->disapprove_switch` when level is user/secure (software CM: 1).
- `iommu_dma_protection` RO — `iommu_dma_protection_show` domain.c:253 (S), attr :261; reads `tb->nhi->iommu_dma_protection`.
- `security` RO — `security_show` domain.c:263 (S), attr :274.

**Domain PM seams** (flows owned by another area): `tb_domain_suspend_noirq` :528, `resume_noirq` :556, `suspend` :569, `freeze_noirq` :574, `thaw_noirq` :588, `complete` :601, `runtime_suspend` :607, `runtime_resume` :618.

**Domain authorization / paths**: `tb_domain_disapprove_switch` :638, `approve_switch` :657, `approve_switch_key` :683 **[ICM-only]**, `challenge_switch_key` :715 **[ICM-only]**, `disconnect_pcie_paths` :756 **[ICM-only]**, `approve_xdomain_paths` :782, `disconnect_xdomain_paths` :811, `disconnect_all_paths` :845 (**[ICM-only]** — only caller is `disconnect_pcie_paths`-based NVM prep), helper `disconnect_xdomain` :822 (S).
- `tb_domain_unregister_unplugged_xdomains()` domain.c:874 — **new at v7.2**; helper `unregister_unplugged_xdomain` :861 (S); returns count.
- `tb_domain_event()` (inline) tb.h:818 — `kobject_uevent_env(KOBJ_CHANGE)`; callers domain.c:221, tunnel.c:268.
- `tb_domain_event_cb()` domain.c:338 (S) — ctl callback: XDOMAIN_REQ/RESP → `tb_xdomain_handle_request()` when `tb_is_xdomain_enabled()`, everything else → `cm_ops->handle_event`.

**Software CM (tb.c)** — all S unless noted
- `tb_probe()` tb.c:3374 (non-static, declared tb.h:761) — the only place the software `tb_cm_ops` is installed. Seam: nhi.c:1163 `nhi_select_cm()` → `tb_probe()` when `tb_acpi_is_native()`, else `icm_probe()` then fall back to `tb_probe()`; nhi.c:1231/1238 call `tb_domain_add()`.
- `tb_apple_add_links()` tb.c:3312 — **vendor/Apple-specific**, `x86_apple_machine` + four Intel NHI device IDs; pairs with `tb_acpi_add_links()` (`CONFIG_ACPI`).
- `tb_start(tb, reset)` tb.c:2995; `tb_stop` :2941; `tb_deinit` :2964; `tb_scan_finalize_switch` :2974.
- Discovery/scan: `tb_scan_switch` :1273, `tb_scan_port` :1289, `tb_configure_link` :1232, `tb_scan_xdomain` :431, `tb_port_configure_xdomain` :416, `tb_port_unconfigure_xdomain` :423.
- Hotplug: `tb_queue_hotplug` :93, `tb_handle_hotplug` :2421, `tb_handle_event` :2916, `tb_handle_notification` :2885, `tb_free_unplugged_children` :1790, `tb_free_unplugged_xdomains` :3123, `tb_remove_work` :3250.
- XDomain paths: `tb_approve_xdomain_paths` :2319, `__tb_disconnect_xdomain_paths` :2368, `tb_disconnect_xdomain_paths` :2400.
- PM: `tb_suspend_noirq` :3077, `tb_resume_noirq` :3141, `tb_restore_children` :3091, `tb_freeze_noirq` :3203, `tb_thaw_noirq` :3211, `tb_complete` :3219, `tb_runtime_suspend` :3232, `tb_runtime_resume` :3263.
- Seams into the tunnel/bandwidth area (not inventoried here): `tb_discover_tunnels` :1694, `tb_discover_dp_resources` :172, `tb_add_dp_resources` :111, `tb_remove_dp_resources` :138, `tb_create_usb3_tunnels` :997, `tb_tunnel_usb3` :905, `tb_tunnel_dp` :2063, `tb_recalc_estimated_bandwidth` :1515, `tb_free_invalid_tunnels` :1775, `tb_dp_resource_available` :2209 / `_unavailable` :2178, `tb_tunnel_pci` :2275, `tb_disconnect_pci` :2254, `tb_enable_clx` :184 / `tb_disable_clx` :235, `tb_enable_tmu` :319, `tb_switch_enter_redrive` :2147 / `_exit_redrive` :2159, `tb_handle_dp_bandwidth_request` :2736, `tb_queue_dp_bandwidth_request` :2868.

**XDomain object API** (tb.h:1259-1284 + include/linux/thunderbolt.h)
- `tb_xdomain_alloc()` xdomain.c:2121, `tb_xdomain_add()` :2202, `tb_xdomain_remove()` :2224, `tb_xdomain_unregister()` :2257 (**new at v7.2**), `tb_xdomain_release()` :2015 (S).
- `tb_xdomain_get/put` (inline) include/linux/thunderbolt.h:334/341; `tb_is_xdomain`/`tb_to_xdomain` :347/352; `tb_xdomain_parent` tb.h:1271; `tb_xdomain_downstream_port` tb.h:1282.
- Lookup: `switch_find_xdomain` xdomain.c:2493 (S), `tb_xdomain_find_by_uuid` :2545 (E), `tb_xdomain_find_by_link_depth` :2576 (**[ICM-only]** caller), `tb_xdomain_find_by_route` :2607 (E); `*_locked` inlines include/linux/thunderbolt.h:311/323.
- Link: `tb_xdomain_link_init` :2057 (S), `tb_xdomain_link_exit` :2074 (S), `tb_xdomain_lane_bonding_enable` :2277 (E), `_disable` :2329 (E), `tb_xdomain_bond_lanes_uuid_high` :1475 (S), `tb_xdomain_link_state_change` :1434 (S), `tb_xdomain_update_link_attributes` :1317 (S).
- HopIDs: `tb_xdomain_alloc_in_hopid` :2364 (E), `alloc_out_hopid` :2390 (E), `release_in_hopid` :2407 (E), `release_out_hopid` :2418 (E).
- Paths: `tb_xdomain_enable_paths` :2439 (E), `tb_xdomain_disable_paths` :2470 (E), `tb_xdomain_disable_all_paths` (inline) include/linux/thunderbolt.h:302.
- XDomain sysfs (group xdomain.c:2006): `device` :1863/1870, `device_name` :1872/1885, `maxhopid` :1887/1894, `vendor` :1896/1903, `vendor_name` :1905/1918, `unique_id` :1920/1927, `rx_speed`/`tx_speed` :1929/1937/1938, `rx_lanes` :1940/1964, `tx_lanes` :1966/1990.
- XDomain PM: `tb_xdomain_suspend/resume` :2034/:2040 (S, `__maybe_unused`, gate `CONFIG_PM_SLEEP` via `SET_SYSTEM_SLEEP_PM_OPS` :2047) — stop/start the handshake.

**XDomain protocol (XDP)**
- Transport: `__tb_xdomain_response` :138 (S), `tb_xdomain_response` :173 (E), `__tb_xdomain_request` :180 (S), `tb_xdomain_request` :225 (E); ctl matching `tb_xdomain_match` :90 (S), `tb_xdomain_copy` :123 (S), `response_ready` :133 (S).
- Header/error: `tb_xdp_fill_header` :236 (S inline), `tb_xdp_handle_error` :251 (S), `tb_xdp_error_response` :317 (S).
- Message pairs (all S): `tb_xdp_uuid_request` :271 / `_response` :300; `tb_xdp_properties_request` :331 / `_response` :424; `tb_xdp_properties_changed_request` :478 / `_response` :501; `tb_xdp_link_state_status_request` :513 / `_response` :547; `tb_xdp_link_state_change_request` :566 / `_response` :593.
- Dispatch: `tb_xdomain_handle_request` :2620 (non-static, tb.h:1260), `tb_xdp_schedule_request` :938 (S), `tb_xdp_handle_request` :758 (S, work handler).
- Handlers: `tb_register_protocol_handler` :619 (E), `tb_unregister_protocol_handler` :640 (E); list `protocol_handlers` :78 under `xdomain_lock` :71.
- Module gate: `tb_is_xdomain_enabled()` :85 — module param `xdomain` (`bool`, 0444) :62-64 AND `tb_acpi_is_xdomain_allowed()` (`CONFIG_ACPI`).

**Services**
- `tb_register_service_driver` :969 (E), `tb_unregister_service_driver` :982 (E).
- `tb_service_get/put`, `tb_is_service`, `tb_to_service`, `tb_service_get/set_drvdata`, `tb_service_parent` — inlines include/linux/thunderbolt.h:433-496.
- `enumerate_services` :1219 (S), `populate_service` :1186 (S), `update_service` :1140 (S), `find_service` :1174 (S), `remove_missing_service` :1158 (S), `__unregister_service` :1150 (S, **new v7.2**), `unregister_service` :2208 (S), `tb_service_release` :1120 (S), `tb_service_uevent` :1111 (S), `get_modalias` :1039 (S).
- Service sysfs (group :1102): `key` :1026/:1037, `modalias` :1045/:1054, `prtcid` :1056/:1063, `prtcvers` :1065/:1072, `prtcrevs` :1074/:1081, `prtcstns` :1083/:1090.
- `tb_service_properties_changed` :1013 (E, **new v7.2**); `update_service_properties` :648 (S), `update_xdomain` :988 (S), `update_all_xdomains` :2663 (S).
- Consumers named as seams only: drivers/net/thunderbolt/main.c, drivers/thunderbolt/dma_test.c (`CONFIG_USB4_DMA_TEST`), drivers/thunderbolt/stream.c (`CONFIG_USB4_STREAM`).

**Properties (property.c; all E unless noted)**
- `tb_property_parse_dir` :243, `__tb_property_parse_dir` :170 (S), `tb_property_parse` :103 (S), `tb_property_entry_valid` :55 (S), `tb_property_key_valid` :82 (S), `tb_property_alloc` :87 (S).
- `tb_property_format_dir` :515, `__tb_property_format_dir` :373 (S), `tb_property_dir_length` :334 (S), `parse_dwdata`/`format_dwdata` :45/:50 (S).
- `tb_property_create_dir` :267, `tb_property_free_dir` :318, `tb_property_free` :288 (S).
- `tb_property_copy_dir` :611 (**new v7.2**), `copy_dir` :531 (S), `tb_property_copy` :557 (S), `tb_property_merge_dir` :628 (**new v7.2**).
- `tb_property_add_immediate` :677, `_add_data` :708, `_add_text` :746, `_add_dir` :782, `tb_property_remove` :808, `tb_property_find` :826, `tb_property_get_next` :847; iteration macro `tb_property_for_each` include/linux/thunderbolt.h:176.
- Host-wide dir: `tb_register_property_dir` xdomain.c:2693 (E), `tb_unregister_property_dir` :2734 (E), `remove_directory` :2668 (S), globals `xdomain_property_dir` :74 / `xdomain_property_block_gen` :75, seeded in `tb_xdomain_init()` :2748 (vendorid 0x1d6b, "Linux", deviceid 0x0004, devicerv 0x80000100, gen = `get_random_u32()`); `tb_xdomain_exit()` :2771.

#### 3. Lifecycle and locking

- **`tb->lock`** (mutex, include/linux/thunderbolt.h:84) — the domain big lock. Held across `cm_ops->start/stop/suspend_noirq/resume_noirq/freeze/thaw` (domain.c:446-510, 537-598), across all of `tb_handle_hotplug` (tb.c:2432-2525), `tb_handle_dp_bandwidth_request`, `tb_approve_xdomain_paths` (tb.c:2333), `tb_remove_work` (tb.c:3255), `tb_complete` (tb.c:3227). **Not** held for `cm_ops->deinit` (documented tb.h:476) nor for `tb_domain_unregister_unplugged_xdomains()` / `tb_xdomain_unregister()` (`lockdep_assert_not_held(&xd->tb->lock)` xdomain.c:2259). Sysfs stores use `mutex_lock_interruptible` (domain.c:135, 214).
- **`xdomain_lock`** (static mutex, xdomain.c:71) — global; guards `xdomain_property_dir`, `xdomain_property_block_gen`, `protocol_handlers`. Documented ordering: take it **before** `xd->lock` (xdomain.c:66-70; enforced in `update_property_block()` :676-677).
- **`xd->lock`** — guards `remote_properties`, `local_property_block*`, `removing`, name strings; also used by sysfs shows.
- **`svc->lock`** — guards `local_properties`/`remote_properties` (xdomain.c:658, 1144).
- **`nhi->domain_released`** (completion, include/linux/thunderbolt.h:530, **new v7.2**) — `init_completion` nhi.c:1229 (before use); `complete()` at the end of `tb_domain_release()` domain.c:330; `wait_for_completion()` nhi.c:1245 (probe failure) and pci.c:492 (remove, right after `tb_domain_remove()`).
- **Refcounting**: `tb_domain_get/put` (put that frees → `tb_domain_release`). Hotplug work holds one (tb.c:101 ↔ 2533); `tb_xdp_schedule_request` holds one (xdomain.c:955 ↔ 935); `tb_domain_unregister_unplugged_xdomains` holds one (domain.c:878/881). `tb_xdomain_get/put` — put that frees → `tb_xdomain_release` xdomain.c:2015; `tb_xdomain_remove()` drops the alloc reference explicitly when the device was never added (xdomain.c:2245). A service holds a reference on its XDomain (`get_device` xdomain.c:1263 → `tb_xdomain_put` xdomain.c:1129, **new v7.2**). `tb_service_get/put` → `tb_service_release` xdomain.c:1120 (frees ida id owned by the parent).
- **Runtime PM**: domain `pm_runtime_no_callbacks/set_active/enable/autosuspend` domain.c:478-483; hotplug work does `pm_runtime_get_sync(&tb->dev)` tb.c:2430 ↔ `mark_last_busy/put_autosuspend` :2529-2530, plus a nested pair on the router :2456 ↔ :2519. `tb_scan_switch` pairs on `sw->dev` (tb.c:1277/1282); `tb_scan_port` pairs on `port->usb4->dev` (tb.c:1316 ↔ 1425-1427). XDomain: `pm_runtime_set_active/get_noresume/enable` at alloc (xdomain.c:2179-2181) keeps DMA powered; undone in `tb_xdomain_remove()` :2242-2244 only when never registered.
- **XDomain state machine** — `xd->state`, values xdomain.c:29-40, names :42. Transitions in `tb_xdomain_state_work()` :1720: `INIT` → (`needs_uuid`) `UUID` else `PROPERTIES` (+ queue properties-changed); `UUID` → `LINK_STATUS` if `bonding_possible` else `PROPERTIES`, error → `ERROR`; `LINK_STATUS` → `tb_xdomain_queue_bonding()` :1675 which picks `BONDING_UUID_HIGH` (our UUID greater — peer bonds) or `LINK_STATE_CHANGE` (we bond); `LINK_STATE_CHANGE` → `LINK_STATUS2` → `BONDING_UUID_LOW` → `PROPERTIES`; `BONDING_UUID_HIGH` → `PROPERTIES`; `PROPERTIES` → `ENUMERATED` (or `ERROR`); `ENUMERATED` re-queues `PROPERTIES`; `ERROR` → `__stop_handshake()`. Any bonding-stage failure falls through to `PROPERTIES` (comment :1762-1766). `start_handshake()` :737, `stop_handshake()` :752, `__stop_handshake()` :745 (safe from inside state_work). Restart from `ERROR` on an inbound UUID request xdomain.c:830-836.
- **Scan decision tree** (`tb_scan_port` tb.c:1289): upstream port → return :1296; DP OUT with HPD active and not enabled → queue a synthetic plug event :1299-1305; non-`TB_TYPE_PORT` → return :1307; secondary lane (`dual_link_port && link_nr`) → return :1309; `tb_wait_for_port()<=0` → out :1318; `port->remote` already set → out :1320; `tb_switch_alloc` error → `tb_retimer_scan` then, on `-EIO`/`-EADDRNOTAVAIL` (depth limit), `tb_scan_xdomain()` :1332-1341; `tb_switch_configure` fail → put :1344; pre-existing `port->xdomain` removed :1353-1357; uevent suppression while `!hotplug_active` (`discovery`) :1364-1367; `sw->rpm = sw->generation > 1` :1373; `tb_switch_add` fail → put :1375; `tb_configure_link()` :1381 (sets both `remote` pointers, enables lane bonding via `tb_switch_set_link_width(TB_LINK_WIDTH_DUAL)` :1250, Gen-4 symmetric reconfig :1257-1263, `tb_switch_configure_link` :1267); retimer scans :1389/:1410; CLx unless discovery :1395-1398; TMU :1400; `tb_switch_configuration_valid` :1407; USB3 tunnels only when `hotplug_active` :1418; `tb_add_dp_resources` :1421; recurse `tb_scan_switch` :1422. (`usb4_port_device_add` is *not* called here — it lives in usb4.c:1093 under `tb_switch_add`.)
- **Unplug ordering** (`tb_handle_hotplug` tb.c:2461-2473): `tb_retimer_remove_all` → `tb_sw_set_unplugged` → `tb_free_invalid_tunnels` → `tb_remove_dp_resources` → `tb_switch_tmu_disable` → `tb_switch_unconfigure_link` → `tb_switch_set_link_width(SINGLE)` → `tb_switch_remove` → clear both `remote` pointers → `tb_recalc_estimated_bandwidth` + `tb_tunnel_dp`.
- **XDomain unplug** tb.c:2477-2493: `xd->is_unplugged = true` *before* `tb_xdomain_remove()` (comment: service drivers unbind there and may call `tb_xdomain_disable_paths()`), then `port->xdomain = NULL`, `__tb_disconnect_xdomain_paths(-1,-1,-1,-1)`, `tb_xdomain_put`, `tb_port_unconfigure_xdomain`. The actual bus removal happens later, outside `tb->lock`, in `tb_domain_unregister_unplugged_xdomains()` tb.c:2527.

#### 4. Hard-coded limits

- `TB_TIMEOUT` 100 ms — tb.c:19 (control-channel timeout passed to `tb_domain_alloc` tb.c:3379).
- `TB_RELEASE_BW_TIMEOUT` 10000 ms — tb.c:20 (bandwidth area).
- `TB_BW_ALLOC_RETRIES` 3 — tb.c:26; checked tb.c:2830.
- `TB_ASYM_MIN` 36000 (`40000*90/100`) tb.c:32; `TB_ASYM_THRESHOLD` 45000 tb.c:42 (module param `asym_threshold`, 0444, tb.c:46-50).
- `MAX_GROUPS` 7 — tb.c:44 (sizes `tb_cm.groups`).
- Bare literals in tb.c: `queue_delayed_work(..., 0)` :106 (hotplug runs immediately); `msecs_to_jiffies(50)` :2836 (BW retry delay) and :3283 (post-runtime-resume `remove_work` delay); `usb3_delay = 500` :3172 and `msleep(100)` :3193 in `tb_resume_noirq`.
- `TB_AUTOSUSPEND_DELAY` 15000 ms — tb.h:550 (used domain.c:481).
- `TB_SWITCH_MAX_DEPTH` 6 / `USB4_SWITCH_MAX_DEPTH` 5 — tb.h:75/76 (produce `-EADDRNOTAVAIL` at switch.c:2496, which routes `tb_scan_port` to XDomain detection).
- `TB_SWITCH_KEY_SIZE` 32 — tb.h:74 (challenge/response/hmac buffers domain.c:717-719; `static_assert(sizeof(hmac) == SHA256_DIGEST_SIZE)` domain.c:736).
- `XDOMAIN_SHORT_TIMEOUT` 100 ms, `XDOMAIN_DEFAULT_TIMEOUT` 1000 ms, `XDOMAIN_BONDING_TIMEOUT` 10000 ms, `XDOMAIN_RETRIES` 10, `XDOMAIN_DEFAULT_MAX_HOPID` 15 — xdomain.c:23-27.
- Bare literals in xdomain.c: `retry % 4` sequence-number wrap (:279, :348, :486); `msecs_to_jiffies(50)` :998 (`update_xdomain` properties-changed delay); `tb_port_wait_for_link_width(..., 100)` :2338 (bonding-disable timeout); `char modalias[64]` :1114; `strlen(key) > 8` :2700; `tb_xdomain_link_state_change(xd, 2)` :1774.
- `TB_XDOMAIN_LENGTH_MASK` GENMASK(5,0), `TB_XDOMAIN_SN_MASK` GENMASK(28,27), `TB_XDOMAIN_SN_SHIFT` 27 — tb_msgs.h:522-524.
- `TB_XDP_PROPERTIES_MAX_DATA_LENGTH` = `(256 - 4 - sizeof(struct tb_xdp_properties_response))/4` — tb_msgs.h:630; `TB_XDP_PROPERTIES_MAX_LENGTH` 500 dwords — tb_msgs.h:634 (enforced xdomain.c:392 → `-E2BIG`).
- `TB_PROPERTY_KEY_SIZE` 8 — include/linux/thunderbolt.h:127; `TB_PROPERTY_ROOTDIR_MAGIC` 0x55584401 and `TB_PROPERTY_MAX_DEPTH` 8 — property.c:37/38 (**new v7.2**); minimum non-root `dir_len` 4 dwords — property.c:196; `TB_PROPERTY_TYPE_VALUE` length must be exactly 1 — property.c:74.
- `TB_LINKS_PER_PHY_PORT` 2 — include/linux/thunderbolt.h:100.

#### 5. Version-specific facts (v7.2 vs widely-documented older kernels)

- `struct tb_service_id` **moved** from `include/linux/mod_devicetable.h` to `include/linux/device-id/tb.h:28`; `include/linux/thunderbolt.h:26` now includes `<linux/device-id/tb.h>` (commits ad428f5811bd, ecca1d63c1ea).
- `tb_xdomain_unregister()` **added** (xdomain.c:2257, tb.h:1267); `tb_xdomain_remove()` no longer unregisters the device.
- `tb_domain_unregister_unplugged_xdomains()` **added** (domain.c:874, tb.h:796) with `struct unregister_context` (domain.c:856).
- `tb_property_copy_dir()` **re-implemented** as a wrapper over new static `copy_dir()`; new `tb_property_copy()` (property.c:557) and new exported `tb_property_merge_dir()` (property.c:628).
- `tb_service_properties_changed()` **added** (xdomain.c:1013); `struct tb_service` gained `local_properties`; `__unregister_service()` added.
- `struct tb_xdomain` gained `removing` and `ntunnels`; `struct xdomain_request_work` gained `pkg_len`; `struct tb_nhi` gained `domain_released`.
- `tb_domain_alloc()` now uses `nhi->dev` rather than `nhi->pdev->dev` (`pci_device` moved out of `tb_nhi`, commit 8c3ff7c5ae15) — a v7.0-era page describing `tb->dev.parent = &nhi->pdev->dev` is wrong.
- `tb_domain_init/exit()` now call `tb_configfs_init/exit()` (gate `CONFIG_CONFIGFS_FS` / `CONFIG_USB4_CONFIGFS`).
- `tb_xdp_link_state_status_response()` signature changed (now takes `slw,sls,tls,tlw`); the register read moved into the request handler.

#### 6. Suggested page topics (one mechanism each)

1. **`struct tb` and the domain object** — every field, who writes it, `tb_priv()`; anchors include/linux/thunderbolt.h:82, tb.h:545.
2. **Domain allocation and registration** — `tb_domain_alloc/add/remove`, ida, `tb->wq`, ctl start ordering; domain.c:377/439/503.
3. **Domain release and the `domain_released` completion** — `tb_domain_release`, `tb_domain_get/put`, nhi.c:1245 / pci.c:492 wait; domain.c:319.
4. **The thunderbolt bus** — `tb_bus_type`, `tb_domain_type`, `tb_service_type`, `tb_xdomain_type`, match/probe/remove/shutdown/uevent; domain.c:22-336, xdomain.c:1132/2050.
5. **Domain sysfs attributes** — the four attrs, visibility callback, which are ICM-only; domain.c:121-309.
6. **`struct tb_cm_ops`: the connection-manager vector** — every callback, invoker, sw-CM coverage table; tb.h:507, tb.c:3287.
7. **`tb_probe()` and CM selection** — `nhi_select_cm` fallback, security-level choice, device links (incl. the Apple vendor branch); tb.c:3374, nhi.c:1163.
8. **`struct tb_cm` and domain bring-up (`tb_start`)** — root switch at route 0, `reset` semantics, discovery vs reset paths, `hotplug_active`; tb.c:64/2995.
9. **`tb_stop`/`tb_deinit` and domain teardown** — root_switch NULL-ing, DMA tunnel teardown, work cancellation; tb.c:2941/2964.
10. **Topology scanning: `tb_scan_switch`/`tb_scan_port`** — the full per-port decision tree and every early exit; tb.c:1273/1289.
11. **`tb_configure_link` and lane bonding at scan time** — dual-link remote wiring, width promotion, Gen-4 symmetric reconfig; tb.c:1232.
12. **`tb_scan_finalize_switch` and uevent suppression during discovery** — `sw->boot` → `authorized`; tb.c:2974, 1364.
13. **From control-channel event to work item** — `tb_domain_event_cb` → `tb_handle_event` → `tb_cfg_ack_plug`/`tb_cfg_ack_notification` → `tb_queue_hotplug`; domain.c:338, tb.c:2916/2885.
14. **`tb_handle_hotplug`: every branch** — router unplug, XDomain unplug, DP adapter unplug, xHCI connect/disconnect on port 0, null-port scan, DP resource available; tb.c:2421.
15. **Unplug cleanup outside the hotplug path** — `tb_free_unplugged_children`, `tb_free_unplugged_xdomains`, `tb_remove_work` after runtime resume; tb.c:1790/3123/3250.
16. **XDomain DMA path approval from the software CM** — `tb_approve_xdomain_paths`, `__tb_disconnect_xdomain_paths`, CLx interplay; tb.c:2319-2412.
17. **`struct tb_xdomain`: the cross-domain object** — every field and its lock; include/linux/thunderbolt.h:250.
18. **XDomain creation and destruction** — `tb_scan_xdomain`, `tb_xdomain_alloc/add/remove/unregister/release`, runtime-PM pinning; tb.c:431, xdomain.c:2121-2265.
19. **The XDomain discovery state machine** — ten states, per-state retries/timeouts, restart-from-ERROR; xdomain.c:29-53, 1720.
20. **XDomain lane bonding (USB4 v2 rules)** — UUID-high vs UUID-low roles, `tb_xdomain_bond_lanes_uuid_high`, `tb_xdomain_lane_bonding_enable/disable`, `tb_xdomain_link_init/exit`; xdomain.c:1475/2057/2277.
21. **XDP transport and packet framing** — `tb_xdp_fill_header`, sequence numbers, `tb_xdomain_match/copy`, `tb_xdomain_request/response`; xdomain.c:90-235.
22. **The XDP message set** — every request/response pair and `enum tb_xdp_error`; tb_msgs.h:514-654.
23. **Inbound XDP dispatch** — `tb_xdomain_handle_request`, `tb_xdp_schedule_request`, `tb_xdp_handle_request` and its size validations; xdomain.c:2620/938/758.
24. **Protocol handlers for service drivers** — `tb_register/unregister_protocol_handler`, the XDP-UUID exclusion; xdomain.c:619-646.
25. **HopID allocation for DMA tunnels** — in/out idas, `TB_PATH_MIN_HOPID`..`local/remote_max_hopid`; xdomain.c:2364-2422.
26. **`tb_xdomain_enable_paths`/`disable_paths` and `ntunnels`**; xdomain.c:2439/2470.
27. **The property block format and parser** — entries, root magic, depth cap, every validation; property.c:17-256.
28. **Property formatting** — `tb_property_format_dir`, two-pass sizing; property.c:334-529.
29. **Property directory copy and merge** — `copy_dir`, `tb_property_copy`, `tb_property_merge_dir` semantics of `replace`; property.c:531-667.
30. **The host property directory** — `xdomain_property_dir`, generation counter, `tb_register/unregister_property_dir`, `update_property_block`, `tb_xdomain_properties_changed`; xdomain.c:74-75, 674, 1838, 2693.
31. **`struct tb_service` and service enumeration** — `enumerate_services`, `populate_service`, `update_service`, `remove_missing_service`, id ida, reference to the XDomain; xdomain.c:1120-1275.
32. **Service driver binding and matching** — `tb_service_id`, `TB_SERVICE()`, `match_service_id`, modalias/uevent; domain.c:22-74, include/linux/device-id/tb.h.
33. **Service-supplied local properties** — `svc->local_properties`, `update_service_properties`, `tb_service_properties_changed`; xdomain.c:648/1013.
34. **XDomain and service sysfs surfaces**; xdomain.c:1026-1109, 1863-2013.
35. **Domain authorization API and the CM split** — which `tb_domain_*` entry points the software CM implements and which return `-EPERM`/`-ENOTSUPP`; domain.c:638-820.

Topics not named in the request: #3, #12, #13 (ack seam), #22, #26, #29, #34, #35.

#### 7. Tracing

Verified negative for this area's files: `grep -n "trace_\|tracepoint\|TRACE_EVENT\|CREATE_TRACE"` over domain.c, tb.c, xdomain.c, property.c, tb.h, tb_msgs.h, include/linux/thunderbolt.h returns nothing. The subsystem's tracepoints live in drivers/thunderbolt/trace.h (`CREATE_TRACE_POINTS` at ctl.c:18-19): `tb_tx` trace.h:153, `tb_event` :158, `tb_rx` :163, class `tb_raw` :131. XDomain traffic is covered only indirectly, because the PDF-name table decodes `TB_CFG_PKG_XDOMAIN_REQ`/`_RESP` (trace.h:29-30) as the packets pass through the control channel. No area-specific tracepoint exists.

#### 8. Debug and diagnostic printing

- Macros in play, defined in tb.h: `tb_dbg`/`tb_warn`/`tb_info`/`tb_WARN` (`__TB_*` family, tb.h ~700-758), router variants `tb_sw_dbg`/`tb_sw_warn`, port variants `tb_port_dbg`/`tb_port_info`/`tb_port_warn`/`tb_port_WARN` (tb.h:751-758); plus plain `dev_dbg`/`dev_warn`/`dev_err`/`dev_info` in xdomain.c (XDomain/service devices).
- Per-file counts (occurrences): **domain.c** `tb_dbg` 1, `tb_warn` 1, `WARN_ON` 1, `BUILD_BUG_ON` 3, `static_assert` 1. **tb.c** `tb_dbg` 20, `tb_port_dbg` 33, `tb_sw_dbg` 6, `dev_dbg` 1, `tb_warn` 9, `tb_sw_warn` 10, `tb_port_warn` 5, `tb_port_info` 4, `dev_warn` 1, `WARN_ON` 6. **xdomain.c** `dev_dbg` 33, `tb_dbg` 8, `tb_warn` 1, `tb_port_warn` 5, `dev_warn` 5, `dev_err` 6, `dev_info` 3, `WARN_ON_ONCE` 3, `WARN_ON` 1. **property.c** `WARN_ON` 1.
- `WARN` sites: domain.c:443 (`!tb->cm_ops` in `tb_domain_add`), property.c:634 (`parent == dir` in merge), xdomain.c:1725 (state out of range), :1958/:1984 (unreachable link-width case), :2697 (`!xdomain_property_dir`), tb.c:1452/1598/1844/1851/2260/2264 (tunnel/bandwidth area).
- Control knobs: dynamic debug (`CONFIG_DYNAMIC_DEBUG`) for every `*_dbg`; module params `thunderbolt.xdomain` (xdomain.c:63) and `thunderbolt.asym_threshold` (tb.c:47); `dev_err_probe()` used for probe-time messages (tb.c:3003/3021/3028, nhi.c:1233/1247).

#### 9. Asynchronous / deferred / lazy processing

- **Workqueue `tb->wq`** — ordered, `alloc_ordered_workqueue("thunderbolt%d", 0, tb->index)` domain.c:400; drained by `flush_workqueue()` domain.c:512 in `tb_domain_remove`; destroyed in `tb_domain_release` domain.c:325.
- **Hotplug delayed work** — `struct tb_hotplug_event.work`; queued `queue_delayed_work(tb->wq, &ev->work, 0)` tb.c:106 from `tb_queue_hotplug` (called from `tb_handle_event` tb.c:2938, ctl-callback context, and from `tb_scan_port` tb.c:1302); handler `tb_handle_hotplug` tb.c:2421 (process context on `tb->wq`).
- **DP bandwidth-request delayed work** — same struct; queued tb.c:2882 (delay 0 or 50 ms retry); handler `tb_handle_dp_bandwidth_request` tb.c:2736 (bandwidth area).
- **`tb_cm.remove_work`** delayed work — `INIT_DELAYED_WORK` tb.c:3393; queued tb.c:3283 with 50 ms after runtime resume; handler `tb_remove_work` tb.c:3250; cancelled `cancel_delayed_work()` tb.c:2947 in `tb_stop`.
- **Bandwidth-group release work** — `tb_bandwidth_group_release_work` tb.c:1567, cancelled tb.c:1688 and `cancel_delayed_work_sync()` for all groups in `tb_deinit` tb.c:2971 (bandwidth area).
- **`xd->state_work`** delayed work — `INIT_DELAYED_WORK` xdomain.c:2144; queue sites xdomain.c:740 (`start_handshake`), 815 and 906 (inbound XDP, under `xd->lock` + `!removing`), 1655/1663/1671/1686/1694/1702/1716 (state queuers), 1834 (`retry_state`); handler `tb_xdomain_state_work` xdomain.c:1720 on `tb->wq`; cancelled `cancel_delayed_work_sync()` xdomain.c:754.
- **`xd->properties_changed_work`** delayed work — `INIT_DELAYED_WORK` xdomain.c:2145; queued :996 (50 ms, from `update_xdomain`), :1709, :1852 (retry); handler `tb_xdomain_properties_changed` xdomain.c:1838; cancelled :747.
- **`xdomain_request_work`** — plain `work_struct`, `INIT_WORK` xdomain.c:948, `schedule_work()` xdomain.c:957 onto **system_wq** (deliberately *not* `tb->wq`); handler `tb_xdp_handle_request` xdomain.c:758.
- **Completion** — `nhi->domain_released` only (see §3).
- **Timers**: verified negative — no `timer_setup`, `mod_timer`, or `hrtimer` in domain.c/tb.c/xdomain.c/property.c.
- **Kthreads / wait queues**: verified negative — no `kthread_*` or `wait_event*` in these files.
- **Blocking/polling in-line**: `msleep(usb3_delay)` tb.c:3181 and `msleep(100)` tb.c:3193 in `tb_resume_noirq`; polling loops are delegated to `tb_wait_for_port()` (tb.c:1318, xdomain.c:2291) and `tb_port_wait_for_link_width()` (xdomain.c:1518, 2307 with `XDOMAIN_BONDING_TIMEOUT`; :2338 with 100 ms) in switch.c.

#### 10. Subsystem-specific debugging infrastructure

- **Domain sysfs**: `boot_acl`, `deauthorization`, `iommu_dma_protection`, `security` — domain.c:276-309 (no Kconfig gate).
- **XDomain sysfs**: 10 attributes, xdomain.c:1992-2013. **Service sysfs**: 6 attributes, xdomain.c:1092-1109.
- **debugfs**: `tb_xdomain_debugfs_init/remove` debugfs.c:2468/2473 → `margining_xdomain_init/remove` (real bodies debugfs.c:1835/1846, stubs :1871/:1872, gate `CONFIG_USB4_DEBUGFS_MARGINING`, which itself requires `CONFIG_USB4_DEBUGFS_WRITE` + `DEBUG_FS`); `tb_service_debugfs_init/remove` debugfs.c:2484/2496 create `svc->debugfs_dir` (gate `CONFIG_DEBUG_FS`, declarations tb.h:1538-1560). `tb_debugfs_init/exit` called from `tb_domain_init/exit` domain.c:891/919.
- **configfs**: `tb_configfs_init/exit` called domain.c:890/920; `tb_configfs_register_group/unregister_group` include/linux/thunderbolt.h:733-734 (gate `CONFIG_CONFIGFS_FS` / `CONFIG_USB4_CONFIGFS`) — **new at v7.2**.
- **KUnit** (gate `CONFIG_USB4_KUNIT_TEST`, Kconfig:49-52; suite test.c:3147, registered :3152) — property-parser cases: `tb_test_property_parse` test.c:2667, `_format` :2727, `_copy` :2824, `_parse_u32_wrap` :2868, `_parse_recursion` :2899, `_parse_dir_len_underflow` :2939, `_parse_zero_length` :2979, `_parse_rootdir_overflow` :2999, `tb_test_property_merge` (~:3020); `KUNIT_CASE` registrations test.c:3099-3101 and :3138-3143. Fixture data `root_directory[]` test.c:2607, `network_dir_uuid` :2663, comparator `compare_dirs` :2754. No KUnit coverage of domain.c, tb.c CM paths, or the XDomain state machine.
- **DMA/service exercisers** (seams): dma_test.c (`CONFIG_USB4_DMA_TEST`, Kconfig:54), stream.c (`CONFIG_USB4_STREAM`, Kconfig:67).

#### 11. v7.0 → v7.2 drift (paths of this area)

Diffstat: domain.c +37/−, property.c 192, tb.c 88, tb.h 26, xdomain.c 325, thunderbolt.h 61, new include/linux/device-id/tb.h 37, mod_devicetable.h 1009.

- `ad428f5811bd` / `ecca1d63c1ea` — `struct tb_service_id` **moved** include/linux/mod_devicetable.h → include/linux/device-id/tb.h:28; `TBSVC_MATCH_*` moved with it (:10-13); include/linux/thunderbolt.h:26 include changed. A v7.0 page citing mod_devicetable.h is now wrong.
- `a8937f35cf39` "Remove XDomain from the bus without holding tb->lock" — **`tb_xdomain_remove()` split**. v7.0 xdomain.c:2065 unregistered services + device; v7.2 `tb_xdomain_remove()` xdomain.c:2224 only leaves topology, new **`tb_xdomain_unregister()`** xdomain.c:2257 (`lockdep_assert_not_held(&xd->tb->lock)`) does the bus removal; new **`tb_domain_unregister_unplugged_xdomains()`** domain.c:874 (+`unregister_unplugged_xdomain` :861, `struct unregister_context` :856, prototype tb.h:796) is called from `tb_handle_hotplug` tb.c:2527 and `tb_complete` tb.c:3226, both outside `tb->lock`. Pages saying "`tb_xdomain_remove()` unregisters the XDomain" now misstate behaviour.
- `8b4060998637` "Keep XDomain reference during the lifetime of a service" — `svc->dev.parent = get_device(&xd->dev)` xdomain.c:1263 and `tb_xdomain_put(xd)` in `tb_service_release()` xdomain.c:1129 (v7.0 had a plain parent assignment and no put).
- `4d5fc3f40685` "Remove service debugfs entries during unregister" — new static **`__unregister_service()`** xdomain.c:1150 calling `tb_service_debugfs_remove()` before `device_unregister()`; used by `remove_missing_service` :1169 and `unregister_service` :2210. v7.0 removed debugfs only in the release callback.
- `138ec65b2c76` "Keep the domain reference while processing hotplug" — `ev->tb = tb_domain_get(tb)` tb.c:101 and `tb_domain_put(tb)` tb.c:2533. v7.0 stored the bare pointer; a page describing hotplug lifetime must now mention the reference.
- `e56249d8a68e` "Set tb->root_switch to NULL when domain is stopped" — `tb->root_switch = NULL` tb.c:2960; `tb_xdp_handle_request()` now snapshots the UUID under `tb->lock` and answers `ERROR_NOT_READY` when the root switch is gone (xdomain.c:776-786).
- `f5cc545f5969` "Wait for tb_domain_release() to complete" — `struct tb_nhi.domain_released` include/linux/thunderbolt.h:530, `init_completion` nhi.c:1229, `complete()` domain.c:330, waits nhi.c:1245 / pci.c:492.
- `4c63f29872cb` — `__tb_xdomain_response()` now calls `tb_cfg_request_put(req)` when `tb_cfg_request()` fails (xdomain.c:155-156).
- `2c5d2d3c3f70` "Prevent XDomain delayed work use-after-free" — new `xd->removing` (include/linux/thunderbolt.h:267), set under `xd->lock` in `tb_xdomain_remove()` xdomain.c:2229; guards at xdomain.c:814, 832, 904, 995. A v7.0 page saying inbound XDP may queue `state_work` unconditionally is now wrong.
- `a504b9f2797b` — `struct xdomain_request_work.pkg_len` xdomain.c:58, set :954; PROPERTIES_REQUEST and LINK_STATE_CHANGE_REQUEST now require `pkg_len >= sizeof(...)` before the cast (xdomain.c:795, 897).
- `4db2bd2ed478` — `tb_xdomain_copy()` copies `min_t(size_t, pkg->frame.size, req->response_size)` (xdomain.c:126) instead of the full `response_size`.
- `322e93448d90` — properties reassembly clamps `len` to `data_len - req.offset` (xdomain.c:404-405).
- `2fb199dc6405` "Make XDomain lane bonding comply with USB4 v2" — `tb_xdp_link_state_status_response()` signature gained `slw, sls, tls, tlw` (xdomain.c:547); the LANE_ADP register read moved into the request handler (xdomain.c:853-865) which now returns `ERROR_NOT_READY` while `xd->target_link_width != tlw` in state `BONDING_UUID_HIGH` (xdomain.c:873-879). Pages written against v7.0's `tb_xdp_link_state_status_response(tb, ctl, xd, sequence)` are wrong.
- `7c7345bcde6c` — lane-1 adapter is disabled at the end of `tb_xdomain_get_properties()` only when `xd->bonding_possible` (xdomain.c:1611-1617); previously unconditional.
- `7e6445d9d6f7` "Add tb_property_merge_dir()" — new exported `tb_property_merge_dir()` property.c:628 and `tb_property_copy_dir()` property.c:611; the old inline deep-copy body inside `tb_property_copy_dir` became static `copy_dir()` property.c:531 + `tb_property_copy()` property.c:557 (a single property). Prototypes added include/linux/thunderbolt.h:156-159.
- `abc27e5bfed2` "Allow service drivers to specify their own properties" — `struct tb_service.local_properties`/`remote_properties`/`lock` semantics (include/linux/thunderbolt.h:427-429), new `tb_service_properties_changed()` xdomain.c:1013, `update_service_properties()` :648 merging into the rebuilt block (:699), `update_service()` :1140, `mutex_init(&svc->lock)` :1264, `update_xdomain()` relocated to :988.
- `928abe19fbf0` — `TB_PROPERTY_MAX_DEPTH` 8 property.c:38; `__tb_property_parse_dir()`/`tb_property_parse()` gained a `depth` parameter (property.c:170-172, :103-105).
- `de21b59c29e3` — non-root directories with `dir_len < 4` rejected (property.c:196-199).
- `01deda015206` — `tb_property_entry_valid()` uses `check_add_overflow()` (property.c:68-70).
- `cff8eb65d1ea` — zero-length DIRECTORY/DATA/TEXT entries rejected (property.c:64-65).
- `65423079c742` — root directory content bounded by block length (property.c:191-194).
- `8c3ff7c5ae15` — `tb->dev.parent = nhi->dev` (domain.c:408), was `&nhi->pdev->dev`.
- `cba57ed6f1e7` — `tb_configfs_init/exit()` added to `tb_domain_init/exit` (domain.c:890/920), declarations tb.h:1562-1568, include/linux/thunderbolt.h:732-735.
- `15bcac35ba04` — `tb_start()` now returns `dev_err_probe()` results for root-switch alloc/configure/add (tb.c:3003, 3021, 3028); previously plain `PTR_ERR`/`ret` with no message.
- `cf0c38ee554c` — `atomic_t ntunnels` added to `struct tb_xdomain` (include/linux/thunderbolt.h:284), maintained in `tb_xdomain_enable/disable_paths` (xdomain.c:2450/2481); consumed only by icm.c **[ICM-only]**.

#### 12. Kernel documentation and ABI

**Documentation/admin-guide/thunderbolt.rst** — "Security levels and how to use them" :24 (enumerates none/user/secure/dponly/usbonly/nopcie, mirrors domain.c:112 and include/linux/thunderbolt.h:58; describes reading `/sys/bus/thunderbolt/devices/domainX/security` :87); "Authorizing devices when security level is user or secure" :101; "De-authorizing devices" :163 (pairs with `deauthorization` attribute and `cm_ops->disapprove_switch`); "DMA protection utilizing IOMMU" :179 (pairs with `iommu_dma_protection`); "Upgrading NVM …" :199/:241/:308; "Networking over Thunderbolt cable" :352 (the XDomain/service consumer story); "Forcing power" :437.

**Documentation/ABI/testing/sysfs-bus-thunderbolt** — domain attributes: `domainX/boot_acl` :1 (4.17), `domainX/deauthorization` :24 (5.12), `domainX/iommu_dma_protection` :33 (4.21), `domainX/security` :42 (4.13). XDomain-shared device attributes: `device` :123, `device_name` :130, `maxhopid` :137 (5.13), `rx_speed` :144, `rx_lanes` :151, `tx_speed` :158, `tx_lanes` :165, `vendor` :172, `vendor_name` :179, `unique_id` :186. Service attributes: `<xdomain>.<service>/key` :246 (4.15), `modalias` :261, `prtcid` :268, `prtcvers` :275, `prtcrevs` :282, `prtcstns` :289.

**Kerneldoc blocks in this area** — include/linux/thunderbolt.h: `enum tb_security_level` :46, `struct tb` :67, `struct tb_property_dir` :107, `struct tb_property` :129, `enum tb_link_width` :184, `struct tb_xdomain` :198, `struct tb_protocol_handler` :367, `struct tb_service` :395, `struct tb_service_driver` :458, `struct tb_nhi` :500 (`@domain_released` :516). include/linux/device-id/tb.h:16 `struct tb_service_id`. drivers/thunderbolt/tb.h: `struct tb_cm_ops` :471, `tb_domain_event()` :810, `tb_xdomain_downstream_port()` :1276, `tb_upstream_port()` :554, `tb_is_upstream_port()` :570, `tb_port_has_remote()` :614, `tb_downstream_route()` (:~1245). drivers/thunderbolt/tb.c: `struct tb_cm` :52. domain.c: `tb_domain_alloc()` :362, `tb_domain_add()` :427, `tb_domain_remove()` :496, `tb_domain_suspend_noirq()` :520, `tb_domain_resume_noirq()` :547, `tb_domain_disapprove_switch()` :629, `tb_domain_approve_switch()` :646, `tb_domain_approve_switch_key()` :672, `tb_domain_challenge_switch_key()` :703, `tb_domain_disconnect_pcie_paths()` :747, `tb_domain_approve_xdomain_paths()` :764, `tb_domain_disconnect_xdomain_paths()` :793, `tb_domain_disconnect_all_paths()` :835. xdomain.c: `tb_xdomain_response()` :161, `tb_xdomain_request()` :208, `tb_register_protocol_handler()` :608, `tb_unregister_protocol_handler()` :634, `tb_register_service_driver()` :961, `tb_unregister_service_driver()` :976, `tb_service_properties_changed()` :1005, `tb_xdomain_alloc()` :2107, `tb_xdomain_add()` :2193, `tb_xdomain_remove()` :2214, `tb_xdomain_unregister()` :2249, `tb_xdomain_lane_bonding_enable()` :2267, `_disable()` :2322, `tb_xdomain_alloc_in_hopid()` :2350, `alloc_out_hopid()` :2376, `release_in_hopid()` :2402, `release_out_hopid()` :2413, `tb_xdomain_enable_paths()` :2424, `disable_paths()` :2455, `tb_xdomain_find_by_uuid()` :2528, `find_by_link_depth()` :2558, `find_by_route()` :2590, `tb_register_property_dir()` :2681, `tb_unregister_property_dir()` :2726, `tb_service_debugfs_init/remove` debugfs.c:2478/2490. property.c: `tb_property_parse_dir()` :228, `tb_property_create_dir()` :258, `tb_property_free_dir()` :310, `tb_property_format_dir()` :~500, `tb_property_copy_dir()` :603, `tb_property_merge_dir()` :617, `tb_property_add_immediate()` :669, `_add_data()` :~700, `_add_text()` :~738, `_add_dir()` :~774, `tb_property_remove()` :~800, `tb_property_find()` :815, `tb_property_get_next()` :840.

### Area C: Adapters, lane adapters, USB4 port device — COMPLETE (recorded 2026-09-04)

[Orchestrator note 2026-09-04, line hints refuted at write time (tb-port.md), disk values at v7.2: inside `tb_switch_alloc` the per-port `sw` back pointer is written at switch.c:2509 and `port` at :2510 (digest: 2514/2515), the two `ida_init` calls are at :2514-2515 (digest: 2519-2520); the `disabled` read in the reset walk is at switch.c:3335 (3334 is the loop head) and the debugfs read at debugfs.c:2434 (2436 tests `TB_TYPE_INACTIVE`); `total_credits` is re-assigned at switch.c:1253 (1250 is the debug print) and the cached header copy is rewritten at switch.c:1252 (1239 is the register read); `tb_port_at` is at tb.h:588; `TB_PATH_MIN_HOPID` at tb.h:450.]

Verified against `git describe --tags` = v7.2. All locations confirmed on disk.

#### 1. Core structs

##### struct tb_port — drivers/thunderbolt/tb.h:280 (kerneldoc at tb.h:246; "an adapter, protocol or lane")
- `config` tb.h:281 — cached 8-dword `tb_regs_port_header` read once by tb_init_port (switch.c:711); re-read partially by tb_port_do_update_credits (switch.c:1239) and written back by tb_port_add_nfc_credits (switch.c:594).
- `sw` tb.h:282 — owning router; set in tb_switch_alloc loop (switch.c:2514); never cleared.
- `remote` tb.h:283 — peer lane adapter of the connected router; set by tb_configure_link (tb.c:1238-1242) and icm.c:667 (ICM); cleared in tb.c:1805/2471, switch.c:3445 (tb_switch_remove), icm.c:672/683/705.
- `xdomain` tb.h:284 — remote host; set in tb.c:451 (tb_scan_xdomain) and icm.c:724; cleared tb.c:1356/2490/3134, switch.c:3449, icm.c:745/2108.
- `cap_phy` tb.h:285 — offset of TB_PORT_CAP_PHY (lane adapter regs); set only in tb_init_port (switch.c:724-728); 0 ⇒ not a lane adapter, read by every LANE_ADP_CS_* accessor.
- `cap_tmu` tb.h:286 — TB_PORT_CAP_TIME1 offset; set outside this area by tb_switch_tmu_init (tmu.c:426-427).
- `cap_adap` tb.h:287 — TB_PORT_CAP_ADAP offset for protocol adapters; set in tb_init_port (switch.c:750-752), mutually exclusive with cap_phy.
- `cap_usb4` tb.h:288 — USB4 port capability offset; set in tb_init_port (switch.c:731-733); gates every PORT_CS_* access and usb4_port_device_add.
- `usb4` tb.h:289 — USB4 port device; set by usb4_switch_add_ports (usb4.c:1103), cleared by usb4_switch_remove_ports (usb4.c:1117). Non-NULL only on lane 0 adapters that carry the USB4 cap.
- `port` tb.h:290 — adapter number (index into `sw->ports`); set in tb_switch_alloc (switch.c:2515); 0 = router control adapter.
- `disabled` tb.h:291 — set from DROM `port_disabled` (eeprom.c:379) or on -ENODEV from the config read (switch.c:717); read at switch.c:3334 and debugfs.c:2436.
- `bonded` tb.h:292 — both lanes act as one; set/cleared in tb_port_lane_bonding_enable/disable (switch.c:1167-1168, 1181-1182) and tb_switch_link_init (switch.c:2916-2923).
- `dual_link_port` tb.h:293 — the other lane of the pair; set from DROM (eeprom.c:404) or by tb_switch_default_link_ports (switch.c:2839-2842).
- `link_nr:1` tb.h:294 — 0 = primary (lane 0), 1 = secondary (lane 1); DROM eeprom.c:396 or default pairing switch.c:2838/2840.
- `in_hopids` / `out_hopids` tb.h:295-296 — per-adapter IDAs; `ida_init` in tb_switch_alloc (switch.c:2519-2520, skipped for adapter 0), `ida_destroy` in tb_switch_release (switch.c:2296-2297).
- `list` tb.h:297 — links DP IN/OUT adapters onto `tcm->dp_resources`; `INIT_LIST_HEAD` in tb_init_port (switch.c:705); used only by tb.c:130/152/169/2199/2224/2250.
- `total_credits` tb.h:298 — ADP_CS_4 Total Buffers; set in tb_init_port (switch.c:755) and refreshed by tb_port_do_update_credits (switch.c:1250).
- `ctl_credits` tb.h:299 — control-path buffers; read from hop 0 initial_credits for USB4 (switch.c:740-744), else hard-coded 2 (switch.c:746).
- `dma_credits` tb.h:300 — credits held by DMA tunnels through this adapter; only tunnel.c:1762/1787/1821/1863 write it.
- `group` tb.h:301 + `group_list` tb.h:302 — DP IN bandwidth group membership; set tb.c:1601-1602, cleared tb.c:1681-1682 (group struct at tb.h:238). `group_list` relies on kzalloc + list_add_tail; never INIT_LIST_HEAD'ed.
- `max_bw` tb.h:303 — per-adapter bandwidth cap; only writer is the Barlow Ridge USB3 quirk (quirks.c:43, value 16376); reader usb4.c:2192-2193.
- `redrive` tb.h:304 — DP IN in redrive mode (monitor on the Type-C port); set tb.c:2123, cleared tb.c:2141/2171.

##### struct usb4_port — tb.h:316 (kerneldoc tb.h:307)
- `dev` tb.h:317 device; `port` tb.h:318 back-pointer to the lane 0 adapter; `can_offline` tb.h:319 set by tb_acpi_setup when the retimer _DSM exists (acpi.c:345-348); `offline` tb.h:320 written by offline_store (usb4_port.c:197); `margining` tb.h:322 under `#ifdef CONFIG_USB4_DEBUGFS_MARGINING`.

##### struct tb_regs_port_header — tb_regs.h:283 (no kerneldoc; read as 8 dwords at TB_CFG_PORT offset 0)
- DWORD0: `vendor_id` [15:0], `device_id` [31:16].
- DWORD1: `first_cap_offset` [7:0] (start of the port cap list), `max_counters` [18:8], `counters_support` [19], `__unknown1` [23:20], `revision` [31:24].
- DWORD2: `type` [23:0] = `enum tb_port_type`, `thunderbolt_version` [31:24].
- DWORD3: `__unknown2` [19:0], `port_number` [25:20], `__unknown3` [31:26].
- DWORD4 = **ADP_CS_4**: `nfc_credits` (whole dword cached) — NFC buffers [9:0], Total buffers [29:20], LCK [31].
- DWORD5 = **ADP_CS_5**: `max_in_hop_id` [10:0], `max_out_hop_id` [21:11], `__unknown4` [31:22] — the ADP_CS_5 LCA [28:22] and DHP [31] bits live inside `__unknown4`.
- DWORD6/7: `__unknown5`, `__unknown6`.

##### Register/enum families (tb_regs.h)
- `enum tb_port_type` tb_regs.h:268 — INACTIVE 0, PORT 1 (lane adapter), NHI 2, DP_HDMI_IN 0x0e0101, DP_HDMI_OUT 0x0e0102, PCIE_DOWN/UP 0x100101/2, USB3_DOWN/UP 0x200101/2.
- `enum tb_port_cap` tb_regs.h:40 — PHY 0x01, POWER 0x02, TIME1 0x03, ADAP 0x04, VSE 0x05, USB4 0x06. Only PHY/TIME1/ADAP/USB4 are looked up by the driver; POWER and VSE are decoded only by debugfs (debugfs.c:2022, 2049).
- `enum tb_port_state` tb_regs.h:49 — DISABLED 0, CONNECTING 1, UP 2, TX_CL0S 3, RX_CL0S 4, CL1 5, CL2 6, UNPLUGGED 7.
- `struct tb_cap_phy` tb_regs.h:129 — legacy 2-dword overlay of LANE_ADP_CS_0/1: `disable` = LANE_ADP_CS_1 bit14 (== LANE_ADP_CS_1_LD), `state:4` = LANE_ADP_CS_1 bits [29:26] (link state field, no LANE_ADP_CS_1_* define exists for it).
- ADP_CS_4 tb_regs.h:314-318, ADP_CS_5 tb_regs.h:319-322. Readers/writers: usb4_port_unlock clears LCK (usb4.c:1137-1142); usb4_port_hotplug_enable clears DHP (usb4.c:1159-1164); tb_port_add_nfc_credits R/W NFC field (switch.c:581-594); tb_init_port and tb_port_do_update_credits extract TOTAL_BUFFERS (switch.c:755, 1246). `ADP_CS_5_LCA_MASK/SHIFT` are defined but unused tree-wide at v7.2.
- LANE_ADP_CS_0 tb_regs.h:339-347 — SUPPORTED_SPEED [19:16], SUPPORTED_WIDTH [25:20] (+`_DUAL` 0x2), CL0S/CL1/CL2_SUPPORT bits 26/27/28. Read by tb_port_width_supported (switch.c:1006), clx.c:89-96, xdomain.c:861/1426.
- LANE_ADP_CS_1 tb_regs.h:348-371 — TARGET_SPEED [3:0], TARGET_WIDTH [5:4] (SINGLE 0x1 / DUAL 0x3), TARGET_WIDTH_ASYM [7:6] (DUAL 0x0 / TX 0x1 / RX 0x2), CL0S/CL1/CL2_ENABLE 10/11/12, LD 14, LB 15, CURRENT_SPEED [19:16] (GEN4 0x2, GEN3 0x4, GEN2 0x8), CURRENT_WIDTH [25:20], PMS 30. `LANE_ADP_CS_1_TARGET_SPEED_GEN3` and `_CURRENT_SPEED_GEN2` are defined but unused.
- PORT_CS_18 tb_regs.h:384-392 — BE 8 (bonding enabled, usb4.c:413), TCM 9 (TBT-CM present ⇒ link is TBT not USB4, usb4.c:224), CPS 10 (CL support, usb4.c:1589), WOCS/WODS/WOU4S 16/17/18 (wake status, usb4.c:196-200), CSA 22 (asym capable, usb4.c:1610), TIP 24 (transition in progress, usb4.c:1704).
- PORT_CS_19 tb_regs.h:393-400 — DPR 0 (downstream port reset, usb4.c:1189/1203), PC 3 (port configured, usb4.c:1223), PID 4 (port is XDomain, usb4.c:1271), WOC/WOD/WOU4 16/17/18 (usb4.c:451-464), START_ASYM 24 (usb4.c:1678).
- PORT_CS_1 tb_regs.h:374-382 and PORT_CS_2 tb_regs.h:383 are the sideband access window (usb4_port_sb_read/write) — sideband area, not this one.
- Plug-events VSE regs tb_regs.h:560-578; `struct tb_cap_plug_events` tb_regs.h:151 (`plug_events:5` in VSC_CS_1, `eeprom_ctl`, `drom_offset`).
- Link-controller port regs tb_regs.h:589-632: TB_LC_DESC 0x02, TB_LC_PORT_MODE 0x26 (+DPR), TB_LC_CS_42 0x2a (+USB_PLUGGED), TB_LC_PORT_ATTR 0x8d (+BE), TB_LC_SX_CTRL 0x96 (L1C/L1D/L2C/L2D/SLI/UPSTREAM/SLP), TB_LC_LINK_ATTR 0x97 (+CPS), TB_LC_LINK_REQ 0xad (+XHCI_CONNECT).
- `enum tb_cfg_space` tb_msgs.h:15 — HOPS 0, PORT 1, SWITCH 2, **COUNTERS 3**.
- `enum tb_link_width` include/linux/thunderbolt.h:191 — SINGLE BIT(0), DUAL BIT(1), ASYM_TX BIT(2), ASYM_RX BIT(3); encoding deliberately matches LANE_ADP_CS_0_SUPPORTED_WIDTH / LANE_ADP_CS_1_CURRENT_WIDTH.

#### 2. API families ((S)=static, (E)=exported)

**Adapter init / numbering**
- tb_init_port (S) switch.c:700 — reads 8 dwords, finds PHY/USB4 or ADAP caps, derives ctl_credits and total_credits; -ENODEV ⇒ `disabled = true`.
- tb_dump_port (S) switch.c:442, tb_port_type (S) switch.c:413 — debug decode of the header.
- tb_switch_default_link_ports (S) switch.c:2821 — pairs adjacent lane adapters when DROM did not.
- tb_switch_find_port switch.c:3874 — first adapter of a given `tb_port_type`.
- usb4_port_index usb4.c:982 — ordinal of a USB4 port among primary lane adapters; feeds usb4_switch_map_pcie_down (usb4.c:1015) / map_usb3_down (usb4.c:1048).
- tb_switch_for_each_port tb.h:874 (skips adapter 0), tb_upstream_port tb.h:565, tb_port_at tb.h:588 (WARN_ON out-of-range), tb_switch_downstream_port tb.h:915, tb_is_upstream_port tb.h:577, tb_downstream_route tb.h:1253.

**Predicates / accessors (all inline, tb.h)**
- tb_port_has_remote tb.h:620 (false for upstream and for link_nr==1), tb_port_is_null tb.h:632 (lane adapter ⇔ `port != 0 && type == TB_TYPE_PORT`), tb_port_is_nhi 637, is_pcie_down 642, is_pcie_up 647, is_dpin 652, is_dpout 657, is_usb3_down 662, is_usb3_up 667, tb_port_use_credit_allocation 1128, tb_port_path_direction_downstream 1122, tb_width_name 598.
- tb_port_read tb.h:700 / tb_port_write tb.h:714 — thin `tb_cfg_read/write` wrappers keyed on `port->port`, short-circuit `-ENODEV` when `sw->is_unplugged`.
- tb_is_usb4_port_device tb.h:1486, tb_to_usb4_port_device tb.h:1491, usb4_port_device_is_offline tb.h:1503 (only retimer.c:222/240 use it).
- Path iterators: tb_next_port_on_path switch.c:860, tb_for_each_port_on_path tb.h:1141, tb_for_each_upstream_port_on_path tb.h:1153.

**Port capability walk (cap.c)**
- tb_port_next_cap cap.c:76 — returns `first_cap_offset` for offset 0, else `header.basic.next`.
- __tb_port_find_cap (S) cap.c:91 — linear walk, `-ENOENT` if absent.
- tb_port_find_cap cap.c:124 — wraps the walk in tb_port_enable_tmu (S) cap.c:18 (Light Ridge 0x26 / Eagle Ridge 0x2a, TMU_ACCESS_EN BIT(20)) plus tb_port_dummy_read (S) cap.c:47 (Light Ridge stale-data workaround). **There is no PHY-specific branch in the walk at v7.2** — the only special handling is this legacy/vendor pair.

**Lane adapter state and enable**
- tb_port_state switch.c:467 — reads 2 dwords at `cap_phy`, returns `tb_cap_phy.state`.
- tb_wait_for_port switch.c:498 — polls up to 10×100 ms for TB_PORT_UP (returns 1), 0 for DISABLED/UNPLUGGED/timeout.
- __tb_port_enable (S) switch.c:631 / tb_port_enable switch.c:667 / tb_port_disable switch.c:680 — clear/set LANE_ADP_CS_1_LD.
- tb_port_unlock switch.c:620 — USB4 only, delegates to usb4_port_unlock; no-op for ICM/legacy.
- tb_port_reset (S) switch.c:685 — usb4_port_reset if `cap_usb4`, else tb_lc_reset_port.
- tb_port_start_lane_initialization (S) switch.c:1282 — non-USB4 only; wraps tb_lc_start_lane_initialization, maps -EINVAL to 0.
- tb_port_resume (S) switch.c:1297 — resumes the usb4 device or restarts lane init; returns whether something was attached.
- tb_port_is_enabled switch.c:1326 — dispatch by `config.type` to the PCIe/DP/USB3 predicates.

**Link speed / width / bonding**
- tb_port_get_link_speed switch.c:905 (40/20/10 Gb/s), tb_port_get_link_generation switch.c:941 (4/3/2), tb_port_get_link_width switch.c:966, tb_port_width_supported switch.c:994 (note: name is `tb_port_width_supported`, not `tb_port_is_width_supported`), tb_port_set_link_width switch.c:1031 (Gen4 single is -EOPNOTSUPP; Gen4 dual and both asym forms delegate to usb4_port_asym_set_link_width).
- tb_port_set_lane_bonding (S) switch.c:1085 (LANE_ADP_CS_1_LB), tb_port_lane_bonding_enable switch.c:1119, tb_port_lane_bonding_disable switch.c:1177, tb_port_wait_for_link_width switch.c:1203.
- tb_port_do_update_credits (S) switch.c:1234 / tb_port_update_credits switch.c:1269 (also updates the dual link port).
- Router level (all S except set_link_width): tb_switch_lane_bonding_possible switch.c:2851, tb_switch_update_link_attributes switch.c:2863, tb_switch_link_init switch.c:2896, tb_switch_lane_bonding_enable switch.c:2950, tb_switch_lane_bonding_disable switch.c:3002, tb_switch_asym_enable switch.c:3034, tb_switch_asym_disable switch.c:3077, tb_switch_set_link_width switch.c:3127.
- usb4_switch_lane_bonding_possible usb4.c:402 (PORT_CS_18_BE) vs tb_lc_lane_bonding_possible lc.c:515 (TB_LC_PORT_ATTR_BE).
- Asym helpers: usb4_port_asym_supported usb4.c:1595, usb4_port_asym_set_link_width usb4.c:1618, usb4_port_asym_start usb4.c:1666.

**USB4 port capability ops (usb4.c)**
- link_is_usb4 (S) usb4.c:213 (PORT_CS_18_TCM), usb4_port_unlock usb4.c:1132, usb4_port_hotplug_enable usb4.c:1154, usb4_port_reset usb4.c:1175, usb4_port_set_configured (S) usb4.c:1208, usb4_port_configure usb4.c:1238, usb4_port_unconfigure usb4.c:1251, usb4_set_xdomain_configured (S) usb4.c:1256, usb4_port_configure_xdomain usb4.c:1288, usb4_port_unconfigure_xdomain usb4.c:1300, usb4_port_wait_for_bit (S) usb4.c:1305, usb4_port_set_router_offline (S) usb4.c:1504, usb4_port_router_offline usb4.c:1529, usb4_port_router_online usb4.c:1542, usb4_port_enumerate_retimers usb4.c:1556, usb4_port_clx_supported usb4.c:1574.
- There is **no `usb4_port_is_offline`**; the state lives in `usb4->offline` and is read via usb4_port_device_is_offline (tb.h:1503). Router Ready / Configuration Valid are *router*-level (ROUTER_CS_5/6), reached from usb4_switch_setup usb4.c:243 and usb4_switch_configuration_valid usb4.c:316 via tb_switch_wait_for_bit switch.c:1723.
- Registration: usb4_switch_add_ports usb4.c:1078, usb4_switch_remove_ports usb4.c:1111.

**USB4 port device (usb4_port.c)**
- connector_bind (S) :15 / connector_unbind (S) :30 / connector_ops :36 — component-framework `connector` symlink pair (both directions).
- link_show (S) :41 → DEVICE_ATTR_RO(link) :65; common_group :72.
- usb4_port_offline (S) :76 (power on retimers → router offline → retimer scan, unwinding on failure); usb4_port_online (S) :100.
- usb4_usb3_port_match :118 **(E, EXPORT_SYMBOL_GPL :149)** — matches a USB3 port fwnode to this USB4 port via `usb4-host-interface` + `usb4-port-number`.
- offline_show/store (S) :151/:159 → DEVICE_ATTR_RW(offline) :208; rescan_store (S) :210 → DEVICE_ATTR_WO(rescan) :250; service_attr_is_visible (S) :258 hides both unless `can_offline`.
- usb4_port_device_release (S) :282; `usb4_port_device_type` :289; usb4_port_device_add :303; usb4_port_device_remove :349; usb4_port_device_resume :363.
- ACPI seam: tb_acpi_bus_match acpi.c:283, tb_acpi_find_companion acpi.c:315 (companion found by `_ADR` == lane 0 adapter number, acpi.c:333-335), tb_acpi_setup acpi.c:338 (sets `can_offline` from the retimer _DSM), tb_acpi_retimer_set_power acpi.c:188. All under `CONFIG_ACPI` (tb.h:1510-1537 provides no-op stubs).

**Hop-ID allocation per adapter**
- tb_port_alloc_hopid (S) switch.c:763 — chooses in/out IDA and `config.max_in_hop_id`/`max_out_hop_id` as ceiling; floors at TB_PATH_MIN_HOPID **except for NHI adapters** (switch.c:779-781).
- tb_port_alloc_in_hopid switch.c:799, tb_port_alloc_out_hopid switch.c:813, tb_port_release_in_hopid switch.c:823, tb_port_release_out_hopid switch.c:833.
- Callers: path.c:181/188/189 (tb_path_discover), path.c:279/311/314 (tb_path_alloc), path.c:354/357 (tb_path_free). xdomain.c uses its own `xd->in_hopids/out_hopids` IDAs (xdomain.c:2364/2390/2407/2418), not the port ones.

**Counters**
- tb_port_clear_counter switch.c:604 — writes 3 zero dwords at `TB_CFG_COUNTERS`, offset `3*counter`. Sole caller: tb_path_activate (path.c:512).

**Plug events**
- tb_plug_events_active (S) switch.c:1750 — no-op for ICM and USB4; RMW of `sw->cap_plug_events + 1` (VSC_CS_1): mask `0xFFFFFF83` to arm, `| 0x7c` to disarm; sets TB_PLUG_EVENTS_USB_DISABLE except on Light/Eagle/Port Ridge and Alpine Ridge (vendor-specific branch).
- `sw->cap_plug_events` found by tb_switch_find_vse_cap(TB_VSE_CAP_PLUG_EVENTS) in tb_switch_alloc (switch.c:2523-2525).

**Link controller port ops (lc.c) — all pre-USB4 only**
- read_lc_desc (S) lc.c:27, find_port_lc_cap (S) lc.c:34 — per-*physical* port window: `sw->cap_lc + start + tb_phy_port_from_link(port->port) * size` (both lanes share one LC block).
- tb_lc_reset_port lc.c:62 — `generation < 2` ⇒ -EINVAL; pulses TB_LC_PORT_MODE_DPR with a 10 ms fsleep.
- tb_lc_set_port_configured (S) lc.c:96 / tb_lc_configure_port lc.c:141 / tb_lc_unconfigure_port lc.c:154 — TB_LC_SX_CTRL L1C (odd port) or L2C (even port), plus UPSTREAM for upstream ports; `generation < 2` ⇒ 0.
- tb_lc_set_xdomain_configured (S) lc.c:159 / tb_lc_configure_xdomain lc.c:199 / tb_lc_unconfigure_xdomain lc.c:210 — L1D/L2D.
- tb_lc_start_lane_initialization lc.c:225 — sets TB_LC_SX_CTRL_SLI; returns 0 for host router or `generation < 2`.
- tb_lc_is_clx_supported lc.c:259 (TB_LC_LINK_ATTR_CPS). tb_lc_is_usb_plugged lc.c:283, tb_lc_is_xhci_connected lc.c:310, __tb_lc_xhci_connect (S) lc.c:330, tb_lc_xhci_connect lc.c:364, tb_lc_xhci_disconnect lc.c:383 — **all gated `generation != 3`, i.e. Thunderbolt 3 (Alpine/Titan Ridge) only**; callers tb_switch_xhci_connect switch.c:3980 / disconnect switch.c:4024 further branch on Alpine vs Titan Ridge.
- tb_lc_dp_sink_from_port (S) lc.c:536, tb_lc_dp_sink_available (S) lc.c:550, tb_lc_dp_sink_query lc.c:588, tb_lc_dp_sink_alloc lc.c:618, tb_lc_dp_sink_dealloc lc.c:667 — TB_LC_SNK_ALLOCATION arbitration, legacy counterpart of usb4_switch_*_dp_resource.

**Link configure seams (switch.c)**
- tb_switch_configure_link switch.c:3198 / tb_switch_unconfigure_link switch.c:3227 — pick usb4_port_configure vs tb_lc_configure_port per end; unconfigure does the downstream end first so wake-on-connect survives unplug.
- tb_switch_port_hotplug_enable (S) switch.c:3266 — usb4_port_hotplug_enable for every adapter with `cap_usb4`.
- tb.c seam: tb_port_configure_xdomain (S) tb.c:416 / tb_port_unconfigure_xdomain (S) tb.c:423 dispatch usb4 vs lc.

#### 3. Lifecycle and locking

- **Single serializing lock**: `tb->lock` ("Big lock. Must be held when accessing any struct tb_switch / struct tb_port", include/linux/thunderbolt.h:69-71). There is **no lockdep assertion in any of switch.c / usb4.c / usb4_port.c / lc.c / cap.c** (verified: zero `lockdep_assert_held`). Only usb4_port.c takes the lock itself (link_show :49, offline_store :174, rescan_store :228); debugfs port files take it at debugfs.c:2114/2270/2333.
- **Runtime PM**: usb4_port_device_add enables autosuspend on the usb4 device (usb4_port.c:332-337); sysfs stores wrap in pm_runtime_get_sync/put_autosuspend; tb_scan_port takes a reference on `port->usb4` (tb.c:1315-1316).
- **Allocate**: tb_switch_alloc switch.c:2451 → `sw->ports = kzalloc_objs(..., max_port_number + 1)` (switch.c:2500), then for `i = 0..max_port_number` set `sw`/`port` and `ida_init` both hop-id IDAs for `i != 0` (switch.c:2506-2521).
- **Enumerate**: tb_switch_add switch.c:3298 → tb_drom_read → per-port tb_init_port (switch.c:3333-3344, skipping `disabled`) → tb_check_quirks → tb_switch_default_link_ports → tb_switch_update_link_attributes → tb_switch_link_init → tb_switch_port_hotplug_enable → device_add → usb4_switch_add_ports (switch.c:3381) → tb_switch_debugfs_init.
- **Teardown**: tb_switch_remove switch.c:3430 — per-port recursion into `remote->sw`, `remote = NULL`, xdomain removal, tb_retimer_remove_all; then tb_plug_events_active(false) and usb4_switch_remove_ports. Final free in tb_switch_release switch.c:2288 (ida_destroy both IDAs, kfree(sw->ports)).
- **Resume**: tb_switch_resume switch.c:3525 — for every lane adapter: tb_port_resume, tb_wait_for_port(port, true), tb_port_unlock, recurse or flag XDomain unplugged.
- **Port state machine**: hardware `enum tb_port_state` read through tb_port_state; software transitions are only `disabled` (set once at init or from DROM, never cleared) and `bonded` (set in pairs by tb_port_lane_bonding_enable / tb_switch_link_init, cleared in tb_port_lane_bonding_disable). `bonded` is always written for both members of the dual-link pair.
- Width state lives on the router (`sw->link_width`, `sw->preferred_link_width`, tb.h:185-186) and is refreshed only by tb_switch_update_link_attributes, which also emits a KOBJ_CHANGE uevent (switch.c:2891).

#### 4. Hard-coded limits

- `TB_PATH_MIN_HOPID` 8 — tb.h:450 ("HopIDs 0-7 reserved"); floor in tb_port_alloc_hopid switch.c:780, start of the path dump debugfs.c:2285, reset loop switch.c:1620.
- `TB_PATH_MAX_HOPS` (7*2) = 14 — tb.h:455.
- Per-adapter hop-id ceiling: `config.max_in_hop_id` / `max_out_hop_id`, 11 bits each (tb_regs.h:306-307) ⇒ ≤ 2047.
- NHI adapters may start at HopID 1 (switch.c:779-781; mirrored at debugfs.c:2285).
- `ctl_credits` fallback = **2** — switch.c:745-746 (bare literal).
- tb_wait_for_port: `retries = 10`, `msleep(100)` per retry ⇒ ~1 s ceiling — switch.c:501, 523, 548.
- tb_port_wait_for_link_width: caller-supplied `timeout_msec`, poll step `usleep_range(1000, 2000)` — switch.c:1206, 1228. Callers pass **100 ms** (switch.c:2986, 3033, 3069, 3106, 3126) and **10000 ms** from XDomain (`XDOMAIN_BONDING_TIMEOUT`, xdomain.c:25, used xdomain.c:2308).
- usb4_port_asym_start: 1000 ms for START_ASYM to clear, then 5000 ms for PORT_CS_18_TIP to clear, poll step `USB4_PORT_DELAY` 50 µs — usb4.c:1685-1689, 1693-1694, usb4.c:52.
- `USB4_PORT_SB_DELAY` 1000 µs — usb4.c:53. `USB4_DATA_DWORDS` 16, `USB4_DATA_RETRIES` 3 — usb4.c:18-19.
- usb4_port_reset: `fsleep(10000)` (10 ms) between assert and de-assert of PORT_CS_19_DPR — usb4.c:1195. Same 10 ms in tb_lc_reset_port — lc.c:85.
- tb_switch_wait_for_bit poll step `usleep_range(50, 100)` — switch.c:1739; Router Ready and Configuration Ready both use **500 ms** (usb4.c:295, 334).
- Plug-events masks `0xFFFFFF83` / `0x7c` (bare literals) — switch.c:1770, 1785. Notification Timeout `plug_events_delay = 0xff` (255 ms) — switch.c:2619.
- Counters: 3 dwords per counter set (`zero[3]`, stride `3 * counter`, switch.c:606-609; `COUNTER_SET_LEN` 3 debugfs.c:38); count bounded by `config.max_counters`, 11 bits ⇒ ≤ 2047.
- Cap walk bounds: `CAP_OFFSET_MAX` 0xff, `VSE_CAP_OFFSET_MAX` 0xffff, `TMU_ACCESS_EN` BIT(20) — cap.c:14-16; legacy TMU offsets 0x26 / 0x2a — cap.c:29/31.
- Adapter count: `sw->config.max_port_number` is 6 bits (tb_regs.h:170) ⇒ ≤ 63 adapters, array is `max_port_number + 1`.
- `TB_AUTOSUSPEND_DELAY` 15000 ms — tb.h:550, applied to the usb4 port device at usb4_port.c:335.
- `TB_ROUTE_SHIFT` 8, `TB_MAX_CONFIG_RW_LENGTH` 60 — tb_regs.h:19, 26. `TB_LINKS_PER_PHY_PORT` 2 — include/linux/thunderbolt.h:99 (used by find_port_lc_cap via tb_phy_port_from_link).
- Barlow Ridge USB3 `max_bw` = 16376 Mb/s — quirks.c:43.
- debugfs dump lengths: PORT_CAP_BASIC_LEN 9, PORT_CAP_LANE_LEN 3, PORT_CAP_USB4_LEN 20, PATH_LEN 2, COUNTER_SET_LEN 3 — debugfs.c:24-38.

#### 5. Version-specific facts at v7.2

- `tb_switch_lane_bonding_enable` now returns **-EOPNOTSUPP** (was 0) when bonding is impossible or DUAL is unsupported — switch.c:2957, 2963 (0ab47718345d). Pages written against older kernels that say "returns 0 and continues" are wrong; the caller tb_switch_set_link_width now short-circuits before tb_port_update_credits and the "link width set to" log.
- `tb_switch_reset_host` skips path-config cleanup for USB4 lane-1 adapters (`tb_switch_is_usb4(sw) && !port->usb4` ⇒ continue) — switch.c:1601-1607 (95c4379e37a0). TB1-3 lane 1 still gets cleaned.
- DROM `dual_link_port_nr` is now bounds-checked against `max_port_number` before indexing `sw->ports` — eeprom.c:398-403 (d6764992f17b, CVE-class fix, Cc: stable).
- `ROUTER_CS_6_RR` (Router Ready, BIT(24)) is **new** — tb_regs.h:218; usb4_switch_setup waits 500 ms for it after writing ROUTER_CS_5 (usb4.c:295-296, 062023c4364f).
- Configuration Ready timeout raised 50 ms → **500 ms** — usb4.c:334 (ba2cc3851101).
- Notification Timeout: `plug_events_delay = 0xff` now set for **all** routers in tb_switch_configure (switch.c:2619) and removed from tb_plug_events_active; the USB4 `0xa` value is gone; the legacy write length grew ROUTER_CS_1 3 → 4 dwords (switch.c:2652) — e24f3c0df483.
- `tb_dbg`/`tb_err`/`tb_warn`/`tb_info`/`tb_WARN` now take `(tb)->nhi->dev` instead of `&(tb)->nhi->pdev->dev` — tb.h:725-729; `struct tb_nhi` lost `pdev` in favour of `dev` (usb4_port.c:141 follows).
- New at v7.2 in adjacent register space: `ADP_PCIE_CS_0_LTSSM_MASK` + `enum tb_pcie_ltssm_state` (tb_regs.h:476-491) and `usb4_pci_port_ltssm_state` (usb4.c:3160) — PCIe adapter area, listed here only because it lands in tb_regs.h.
- Nothing in `struct tb_port`, `struct usb4_port`, `struct tb_regs_port_header`, `enum tb_port_state`, `enum tb_port_cap` or `enum tb_link_width` changed between v7.0 and v7.2.

#### 6. Suggested page topics (one mechanism per page)

1. **Adapter numbering and the ports array** — `sw->ports`, `max_port_number`, adapter 0 as the router control adapter, tb_switch_for_each_port, tb_port_at, tb_upstream_port (switch.c:2500-2521, tb.h:565/588/874).
2. **tb_init_port: what one adapter learns at enumeration** — the 8-dword header read, cap discovery order, ctl/total credits (switch.c:700).
3. **struct tb_regs_port_header on the wire** — dword↔ADP_CS mapping, why ADP_CS_4/5 overlap `nfc_credits`/`__unknown4` (tb_regs.h:283, 314-322).
4. **The port capability list and tb_port_find_cap** — walk, `first_cap_offset`, the Light Ridge/Eagle Ridge TMU-access and dummy-read workarounds (cap.c:18-138).
5. **struct tb_cap_phy vs LANE_ADP_CS_0/1** — the legacy overlay, where `state` and `disable` actually live (tb_regs.h:129, switch.c:467).
6. **The lane adapter port state machine** — `enum tb_port_state`, tb_port_state, tb_wait_for_port and its 10×100 ms budget (tb_regs.h:49, switch.c:467/498).
7. **Enabling and disabling a lane** — LANE_ADP_CS_1_LD, tb_port_enable/disable and why they are also called for lane 1 (switch.c:631-683, xdomain.c:2287).
8. **Dual-link pairing** — DROM port entries, `dual_link_port`/`link_nr`, tb_switch_default_link_ports, the v7.2 bounds fix (eeprom.c:362-408, switch.c:2821).
9. **Lane bonding, port level** — tb_port_lane_bonding_enable/disable, LANE_ADP_CS_1_LB, the error unwinding ladder (switch.c:1085-1201).
10. **Lane bonding, router level** — tb_switch_lane_bonding_possible/enable/disable, the CL0 precondition on lane 1, credit re-read (switch.c:2851-3032).
11. **Link speed and generation** — CURRENT_SPEED encodings, Gen 2/3/4 mapping, why Gen 4 cannot be single-lane (switch.c:905-964, 1043, 1211).
12. **Asymmetric links** — TARGET_WIDTH_ASYM, PORT_CS_18_CSA/TIP, PORT_CS_19_START_ASYM, tb_switch_asym_enable/disable, usb4_port_asym_* (switch.c:3034-3125, usb4.c:1595-1707).
13. **tb_port_wait_for_link_width** — the mask semantics, -EACCES retry, the 100 ms vs 10 s callers (switch.c:1203).
14. **rx/tx speed and lanes sysfs** — width→lane-count mapping incl. asym, visibility rule `tb_route(sw)` (switch.c:1984-2049, 2250-2256).
15. **Adapter credits** — total/ctl/dma_credits, ADP_CS_4 fields, tb_port_add_nfc_credits and tb_port_update_credits (switch.c:567, 1234-1280).
16. **HopID allocation per adapter** — the two IDAs, TB_PATH_MIN_HOPID, the NHI exception, the path.c seam (switch.c:763-836, path.c:181/279).
17. **The counters config space** — TB_CFG_COUNTERS, 3-dword sets, `max_counters`/`counters_support`, tb_port_clear_counter and the debugfs `counters` file (switch.c:604, debugfs.c:2302-2354).
18. **Plug events on legacy routers** — cap_plug_events, `struct tb_cap_plug_events`, tb_plug_events_active and its vendor branches, plug_events_delay (switch.c:1750, tb_regs.h:151).
19. **The USB4 port capability** — PORT_CS_18/19 bit map, unlock, hotplug enable, downstream port reset (usb4.c:1132-1206, tb_regs.h:384-400).
20. **Port configured / XDomain configured** — PORT_CS_19_PC / PID and the LC L1C/L2C / L1D/L2D equivalent, tb_switch_configure_link ordering for wake-on-connect (usb4.c:1208-1303, lc.c:96-222, switch.c:3198-3254).
21. **struct usb4_port device** — creation, connector symlink through the component framework and ACPI companion, `link` attribute, release (usb4_port.c end-to-end, acpi.c:315-350).
22. **Offline mode and retimer rescan without a cable** — usb4_port_router_offline/online, ACPI _DSM power, offline/rescan attributes, resume replay (usb4_port.c:76-250/363, acpi.c:180-280).
23. **Link controller port window** — find_port_lc_cap and why both lanes share one LC block; which functions are TB2 vs TB3 only (lc.c:34, 62-390).
24. **remote and xdomain pointers** — who sets, who clears, the primary-port invariant behind tb_port_has_remote (tb.c:1238/1355/1805, switch.c:3445, tb.h:620).
25. **Router reset through adapters** — tb_port_reset, tb_switch_reset_host/device, the v7.2 lane-1 rule (switch.c:685, 1581-1706).

#### 7. Tracing

**Verified negative for adapter-specific tracepoints.** `grep -rn "trace_tb_\|CREATE_TRACE_POINTS" drivers/thunderbolt/*.c` returns only ctl.c:18-19, ctl.c:388 (`trace_tb_tx`), ctl.c:405 (`trace_tb_event`), ctl.c:512 (`trace_tb_rx`). No tracepoint is defined or called in switch.c, usb4.c, usb4_port.c, lc.c, cap.c, eeprom.c. Events are declared in drivers/thunderbolt/trace.h:131 (`DECLARE_EVENT_CLASS(tb_raw)`), :153 (`tb_tx`), :158 (`tb_event`), :163 (`TRACE_EVENT(tb_rx)`).
Indirect coverage worth stating on a page: every `tb_port_read`/`tb_port_write` (tb.h:700/714) becomes a `tb_cfg_read`/`tb_cfg_write` control packet, so all adapter register traffic is visible under `thunderbolt:tb_tx` / `thunderbolt:tb_rx` with route+adapter in the decoded header.

#### 8. Debug and diagnostic printing

- Macros: `__TB_PORT_PRINT` tb.h:745 → `tb_port_WARN` tb.h:751, `tb_port_warn` tb.h:753, `tb_port_info` tb.h:755, `tb_port_dbg` tb.h:757; all prefix `"%llx:%u: "` (route:adapter). Router-level `__TB_SW_PRINT` tb.h:739-744. Base `tb_dbg`/`tb_warn`/`tb_WARN` tb.h:725-729 resolve to `dev_dbg`/`dev_warn`/`dev_WARN` on `tb->nhi->dev`.
- Per-file counts (grep -c at v7.2): switch.c — tb_port_dbg 12, tb_port_warn 7, tb_port_WARN 4, tb_sw_dbg 17, tb_sw_warn 10, tb_dbg 13, WARN_ON 3. usb4.c — tb_port_dbg 2, tb_port_warn 1, tb_sw_dbg 10, tb_sw_warn 6, WARN_ON 4. usb4_port.c — tb_port_dbg 1 (usb4_port.c:198). lc.c — tb_port_dbg 4. cap.c — tb_sw_dbg 1. eeprom.c — tb_sw_dbg 2, tb_sw_warn 14. `tb_port_info` is unused across all of them.
- Control knobs: everything below `tb_port_dbg` is `dev_dbg`, so dynamic debug (`dyndbg`, `/sys/kernel/debug/dynamic_debug/control`, module `+p` per file/line) is the only gate; no module parameter and no `#define DEBUG` in this area. `tb_port_WARN`/`tb_WARN` go through `dev_WARN` (taints, honours `panic_on_warn`).
- Notable WARNs: tb_port_at WARN_ON on out-of-range adapter (tb.h:592), tb_switch_downstream_port WARN_ON for host router (tb.h:917), rx_lanes_show/tx_lanes_show `WARN_ON_ONCE(1)` on an unknown width (switch.c:2018, 2044), tb_acpi_retimer_set_power `WARN_ON(!adev)` (acpi.c:200).

#### 9. Asynchronous, deferred, lazy processing

- **Work items / completions: verified negative.** `grep -n "INIT_WORK|INIT_DELAYED_WORK|queue_work|schedule_work|completion|complete\(|wait_for_completion"` over switch.c, usb4.c, usb4_port.c, lc.c, cap.c returns no match (only the words "completion"/"completed" inside comments at usb4.c:1654/1659/1779/2103). The one delayed work touching a `tb_port` field is `tb_bandwidth_group.release_work` (tb.h:242, queued/cancelled in tb.c — DP bandwidth area, not this one).
- **Polling loops** (all synchronous, caller context = whichever thread holds `tb->lock`; typically the domain workqueue via tb_handle_hotplug, or a sysfs/debugfs write):
  - tb_wait_for_port switch.c:498 — `msleep(100)` ×10 (switch.c:523/548), callers tb.c:1318, switch.c:2970, switch.c:3592, xdomain.c:2291.
  - tb_port_wait_for_link_width switch.c:1203 — `usleep_range(1000, 2000)` until `timeout_msec` (switch.c:1228).
  - tb_switch_wait_for_bit switch.c:1723 — `usleep_range(50, 100)` (switch.c:1739); used for Router Ready and Config Ready.
  - usb4_port_wait_for_bit usb4.c:1305 — `fsleep(delay_usec)` until `timeout_msec` (usb4.c:1320); used by usb4_port_asym_start.
  - Fixed sleeps: `fsleep(10000)` in usb4_port_reset (usb4.c:1195) and tb_lc_reset_port (lc.c:85).
- **Lazy / deferred**: the USB4 port device runs autosuspend with `TB_AUTOSUSPEND_DELAY` 15 s (usb4_port.c:335); usb4_port_device_resume (usb4_port.c:363) lazily re-enters offline mode after sleep; tb_port_resume (switch.c:1297) defers lane re-initialisation to resume time for non-USB4 disconnected adapters.
- **Notification**: tb_switch_update_link_attributes emits `KOBJ_CHANGE` on the router device when speed or width changed (switch.c:2891) [errata 2026-09-10, write time of router/router-device-model.md: switch.c:2890 on disk] — the userspace-visible async signal for rx/tx speed/lanes.

#### 10. Subsystem-specific debugging infrastructure

- **Per-adapter debugfs** (gate `CONFIG_DEBUG_FS`; created in tb_switch_debugfs_init debugfs.c:2418, directory `port%d` at debugfs.c:2439-2440, skipped for `disabled` or `TB_TYPE_INACTIVE` adapters, debugfs.c:2431-2434):
  - `regs` — debugfs.c:2441, port_regs_show debugfs.c:2105 + port_basic_regs_show debugfs.c:2090 + port_cap_show debugfs.c:1996 (per-capability length table debugfs.c:20-31); writable only under `CONFIG_USB4_DEBUGFS_WRITE` (`DEBUGFS_MODE` 0600 vs 0400, debugfs.c:446/453; port_regs_write debugfs.c:273, stubbed to NULL at debugfs.c:448).
  - `path` — debugfs.c:2443, path_show debugfs.c:2261 / path_show_one debugfs.c:2241; hop 0 shown only for lane and NHI adapters, then TB_PATH_MIN_HOPID (or 1 for NHI) up to `max_in_hop_id`.
  - `counters` — debugfs.c:2445-2447, only when `port->config.counters_support`; counters_show debugfs.c:2324, counters_write debugfs.c:1895 with a bare `\n` clearing all sets via port_clear_all_counters debugfs.c:1878.
  - `sb_regs` — debugfs.c:2448-2450, only when `port->usb4` (sideband area).
  - `margining/` subtree — gate `CONFIG_USB4_DEBUGFS_MARGINING` (which itself depends on `USB4_DEBUGFS_WRITE`), debugfs.c:1720-1763; owns `usb4_port.margining` (tb.h:321-323).
- **Sysfs**: `usb4_portX/link|offline|rescan` (usb4_port.c:65/208/250) plus the `connector` symlink (usb4_port.c:19-23); router `rx_speed`/`tx_speed`/`rx_lanes`/`tx_lanes` (switch.c:1996-1997, 2023, 2049), visible only for device routers (switch.c:2250-2256).
- **KUnit** (gate `CONFIG_USB4_KUNIT_TEST`, drivers/thunderbolt/Kconfig:50): drivers/thunderbolt/test.c. The area's constructs are exercised indirectly — alloc_switch test.c:36 builds `sw->ports` and `ida_init`s the hop-id IDAs exactly like tb_switch_alloc; alloc_host test.c:72 / alloc_dev_default test.c:190 populate `dual_link_port`, `link_nr`, `total_credits`, `ctl_credits`; the link helper (test.c:315-331) sets `remote` on both lanes and simulates bonding (`bonded = true`, lane-0 credits doubled, lane-1 zeroed). Cases: `tb_test_path_*` (test.c:423-1333) walk tb_next_port_on_path across bonded/not-bonded/mixed chains, `tb_test_tunnel_port_on_path` test.c:1724, `tb_test_credit_alloc_*` test.c:2024-2660 assert credit accounting. Case list at test.c:3098.

#### 11. v7.0 → v7.2 drift (paths: switch.c, tb_regs.h, usb4.c, usb4_port.c, lc.c, tb.h, cap.c, eeprom.c, include/linux/thunderbolt.h, ABI doc)

`git log --oneline v7.0..v7.2` over those paths: 24 commits; `--stat`: eeprom.c +11/-, switch.c 107, tb.h 26, tb_regs.h 19, usb4.c 35, usb4_port.c 2, include/linux/thunderbolt.h 61. **lc.c, cap.c and the ABI doc are untouched.**

Symbols added / removed / renamed:
- Added: `ROUTER_CS_6_RR` tb_regs.h:218 (062023c4364f). Added: `ADP_PCIE_CS_0_LTSSM_MASK` tb_regs.h:477 and `enum tb_pcie_ltssm_state` tb_regs.h:481 plus `usb4_pci_port_ltssm_state` usb4.c:3160 / decl tb.h:1484 (69a7b98770b7).
- Renamed/split in switch.c: `tb_switch_nvm_add` split into `tb_switch_nvm_init` (new, switch.c:328) + `tb_switch_nvm_add` (switch.c:358); v7.0 had only `tb_switch_nvm_add` at switch.c:350. NVM area, but it shifts every switch.c line below it.
- Removed: `nvm_authenticate_start_dma_port` / `nvm_authenticate_complete_dma_port` (v7.0 switch.c:212/226) → replaced by `nhi->ops->pre_nvm_auth` / `post_nvm_auth`.
- Removed from tb_plug_events_active: the `plug_events_delay = 0xff` write (v7.0 switch.c:1758-1762); moved to tb_switch_configure switch.c:2619.
- `struct tb_path.hops` changed from `struct tb_path_hop *hops` to a `__counted_by(path_length)` flex array (tb.h:446) — affects any page that describes path allocation, not the adapter structs.
- tb.h print macros retargeted from `&(tb)->nhi->pdev->dev` to `(tb)->nhi->dev` (tb.h:725-729); usb4_port.c:141 `device_match_fwnode(nhi->dev, ...)` follows.
- New decls in tb.h: `tb_domain_unregister_unplugged_xdomains` (tb.h:796), `tb_xdomain_unregister` (tb.h:1267), the `CONFIG_CONFIGFS_FS` block (tb.h:1562-1569).

Line moves for this area's anchors (old → new):
- tb_init_port switch.c:704 → switch.c:700; tb_port_lane_bonding_enable switch.c:1123 → 1119; tb_switch_reset_host switch.c:1585 → 1581; tb_plug_events_active switch.c:1750 → 1750 (unchanged); tb_switch_lane_bonding_enable switch.c:2949 → 2950; tb_switch_add switch.c:3297 → 3298; tb_switch_resume switch.c:3520 → 3525.
- Unmoved: `struct tb_port` tb.h:280, `struct usb4_port` tb.h:316, `struct tb_regs_port_header` tb_regs.h:283, `enum tb_port_state` tb_regs.h:49, tb_drom_parse_entry_port eeprom.c:362. `TB_PATH_MIN_HOPID` tb.h:449 → tb.h:450.

Behaviour changes a v7.0-based page would now misstate (one line each):
- 0ab47718345d — "bonding not possible returns 0 and the caller logs success" is now false: -EOPNOTSUPP, no credit re-read, no success log (switch.c:2957/2963).
- 95c4379e37a0 — "tb_switch_reset_host cleans path config space for every adapter it resets" is now false for USB4 lane-1 adapters (switch.c:1601-1607).
- d6764992f17b — "DROM dual_link_port_nr is used unchecked" is now false; an out-of-range value fails the whole port entry with -EIO and a warning (eeprom.c:398-403).
- 062023c4364f — usb4_switch_setup now blocks up to 500 ms waiting for ROUTER_CS_6_RR after the ROUTER_CS_5 write (usb4.c:295).
- ba2cc3851101 — Configuration Ready wait is 500 ms, not 50 ms (usb4.c:334); the kerneldoc "does nothing for the latter" was corrected to "the former".
- e24f3c0df483 — USB4 routers no longer get `plug_events_delay = 0xa` (10 ms); all routers get 0xff (255 ms) set once in tb_switch_configure, and the legacy enumeration write is 4 dwords not 3 (switch.c:2619, 2652).
- switch.c:3608-3621 (2c5d2d3c3f70 series) — tb_switch_resume now re-probes a surviving `port->xdomain` and marks it unplugged if a router replaced it.

#### 12. Kernel documentation and ABI

- `Documentation/ABI/testing/sysfs-bus-thunderbolt`:144 `rx_speed`, :151 `rx_lanes`, :158 `tx_speed`, :165 `tx_lanes` (all Jan 2020 / 5.5, per-lane speed and simultaneous lane count through the upstream port); :296 `usb4_portX/connector` (April 2022, symlink, only with USB Type-C Connector Class and firmware describing the port↔connector link); :306 `usb4_portX/link` (Sep 2021 / v5.14, "usb4" | "tbt" | "none"); :313 `usb4_portX/offline` (Sep 2021 / v5.14, only when the platform can power retimers with no cable); :328 `usb4_portX/rescan` (Sep 2021 / v5.14).
- `Documentation/admin-guide/thunderbolt.rst`:279 — "Upgrading on-board retimer NVM when there is no cable connected", the canonical offline/rescan procedure (lines 279-306), incl. the 5 s wait after `nvm_authenticate`.
- No `kernel-doc` directive anywhere in Documentation/ pulls in drivers/thunderbolt or include/linux/thunderbolt.h (verified), so the kerneldoc below is source-only, never rendered.
- Kerneldoc blocks documenting this area's constructs: `struct tb_port` tb.h:246, `struct usb4_port` tb.h:307, `struct tb_bandwidth_group` tb.h:229, `tb_upstream_port` tb.h:555, `tb_is_upstream_port` tb.h:571, `tb_port_has_remote` tb.h:615, `tb_port_path_direction_downstream` tb.h:1114, `tb_switch_for_each_port` tb.h:868, `tb_switch_downstream_port` tb.h:906, `tb_for_each_port_on_path` tb.h:1134, `tb_for_each_upstream_port_on_path` tb.h:1146; `enum tb_link_width` include/linux/thunderbolt.h:184; `struct tb` (the `@lock` contract) include/linux/thunderbolt.h:67-71.
- tb_regs.h carries only 3 kerneldoc blocks (`tb_cap_extended_short` :67, `tb_cap_extended_long` :81, `tb_cap_any` :99) — `struct tb_regs_port_header`, `struct tb_cap_phy`, `struct tb_cap_plug_events`, `enum tb_port_type/cap/state` and every ADP_CS_/LANE_ADP_CS_/PORT_CS_ define are undocumented, which is where new pages add the most value.
- Function kerneldoc density: switch.c 59 blocks, usb4.c 73, lc.c 19, cap.c 5, usb4_port.c 4, tb.h 34. Notably undocumented in this area: `tb_init_port` (plain comment, switch.c:694), `tb_plug_events_active` (plain comment, switch.c:1747), `tb_port_resume` (plain comment, switch.c:1293), `tb_port_start_lane_initialization`, `tb_port_reset`.
- MAINTAINERS:26909 "THUNDERBOLT DRIVER" covers `Documentation/admin-guide/thunderbolt.rst`, `drivers/thunderbolt/` and `include/linux/thunderbolt.h`; tree `git://git.kernel.org/pub/scm/linux/kernel/git/westeri/thunderbolt.git`.

### Area D: Protocol adapters, sideband, retimers — COMPLETE (recorded 2026-09-04)

Tree confirmed: `git describe --tags` → `v7.2`. All line numbers below were re-read from disk with `awk`/`sed`.

#### 1. CORE STRUCTS

**Register-layout "structs" are #define blocks, not C structs.** The adapter capability structures live at `port->cap_adap` (set once in `tb_port_parse_cap`/`tb_init_port` at drivers/thunderbolt/switch.c:750-752 from `TB_PORT_CAP_ADAP`=0x04, drivers/thunderbolt/tb_regs.h:44); the USB4 port capability at `port->cap_usb4` (drivers/thunderbolt/switch.c:731-733, `TB_PORT_CAP_USB4`=0x06). Both fields: drivers/thunderbolt/tb.h:287-288.

##### DP adapter capability structure (cap_adap + n) — drivers/thunderbolt/tb_regs.h:402-472
- `ADP_DP_CS_0` 0x00 — tb_regs.h:403; `_VIDEO_HOPID_MASK` GENMASK(26,16) :404, `_SHIFT` 16 :405; `_AE` BIT(30) AUX enable :406; `_VE` BIT(31) Video enable :407.
- `ADP_DP_CS_1` — **no offset define exists**; only fields: `_AUX_TX_HOPID_MASK` GENMASK(10,0) :408, `_AUX_RX_HOPID_MASK` GENMASK(21,11) :409, `_AUX_RX_HOPID_SHIFT` 11 :410. Accessed as `data[1]` of a 2-dword read at ADP_DP_CS_0.
- `ADP_DP_CS_2` 0x02 — tb_regs.h:411. `_NRD_MLC_MASK` GENMASK(2,0) non-reduced max lane count :412; `_HPD` BIT(6) hot-plug detect :413; `_NRD_MLR_MASK` GENMASK(9,7)/`_SHIFT` 7 non-reduced max link rate :414-415; `_CA` BIT(10) CM acknowledge :416; `_GR_MASK` GENMASK(12,11)/`_SHIFT` 11 granularity :417-418 with values `_GR_0_25G`=0x0, `_GR_0_5G`=0x1, `_GR_1G`=0x2 :419-421; `_GROUP_ID_MASK` GENMASK(15,13)/`_SHIFT` 13 :422-423; `_CM_ID_MASK` GENMASK(19,16)/`_SHIFT` 16 :424-425; `_CMMS` BIT(20) CM supports BW-alloc mode :426; `_ESTIMATED_BW_MASK` GENMASK(31,24)/`_SHIFT` 24 :427-428.
- `ADP_DP_CS_3` 0x03 — tb_regs.h:429; `_HPDC` BIT(9) HPD clear (write-1) :430.
- `DP_LOCAL_CAP` 0x04 :431, `DP_REMOTE_CAP` 0x05 :432 — share the `DP_COMMON_CAP_*` field layout.
- `DP_STATUS` 0x06 (DP IN) :434; `_ALLOCATED_BW_MASK` GENMASK(31,24)/`_SHIFT` 24 :435-436.
- `DP_STATUS_CTRL` 0x06 (DP OUT, same offset, different role) :438; `_CMHS` BIT(25) CM handshake :439; `_UF` BIT(26) upgrade firmware/"force" :440.
- `DP_COMMON_CAP` 0x07 :441.
- `ADP_DP_CS_8` 0x08 — **defined twice**, tb_regs.h:443 and again :470 (harmless duplicate, same value); `_REQUESTED_BW_MASK` GENMASK(7,0) :444; `_DPME` BIT(30) DP bandwidth-mode enabled :445/:471; `_DR` BIT(31) DPTX request :446/:472.
- Shared cap fields (valid for LOCAL/REMOTE/COMMON, DPRX_DONE only in COMMON) — tb_regs.h:448-468: `DP_COMMON_CAP_RATE_MASK` GENMASK(11,8)/`_SHIFT` 8 :452-453 with `_RATE_RBR`=0, `_HBR`=1, `_HBR2`=2, `_HBR3`=3 :454-457; `_LANES_MASK` GENMASK(14,12)/`_SHIFT` 12 :458-459 with `_1_LANE`=0, `_2_LANES`=1, `_4_LANES`=2 :460-462; `_UHBR10` BIT(17) :463, `_UHBR20` BIT(18) :464, `_UHBR13_5` BIT(19) :465; `_LTTPR_NS` BIT(27) LTTPR non-transparent :466; `_BW_MODE` BIT(28) BW-alloc mode supported :467; `_DPRX_DONE` BIT(31) DPRX capability read done :468.

##### PCIe adapter capability structure — drivers/thunderbolt/tb_regs.h:474-493
- `ADP_PCIE_CS_0` 0x00 :475; `_LTSSM_MASK` GENMASK(28,25) **new at v7.2** :476; `_PE` BIT(31) path enable :477.
- `ADP_PCIE_CS_1` 0x01 :478; `_EE` BIT(0) extended encapsulation enable :479.
- `enum tb_pcie_ltssm_state` — tb_regs.h:481-493, **new at v7.2**, 11 values in order: `USB4_PCIE_LTSSM_DETECT`(0), `_POLLING`, `_CONFIG`, `_CONFIG_IDLE`, `_RECOVERY`, `_RECOVERY_IDLE`, `_L0`, `_L1`, `_L2`, `_DISABLED`, `_HOT_RESET`(10).
- No tx/rx-specific bits exist beyond `_PE`; the mission hint's "link/tx/rx" bits are not present in v7.2.

##### USB3 adapter capability structure — drivers/thunderbolt/tb_regs.h:495-514
- `ADP_USB3_CS_0` 0x00 :496; `_V` BIT(30) valid :497; `_PE` BIT(31) path enable :498.
- `ADP_USB3_CS_1` 0x01 :499 (consumed bandwidth); `_CUBW_MASK` GENMASK(11,0) consumed upstream :500; `_CDBW_MASK` GENMASK(23,12)/`_SHIFT` 12 consumed downstream :501-502; `_HCA` BIT(31) host CM ack :503.
- `ADP_USB3_CS_2` 0x02 :504 (allocated bandwidth); `_AUBW_MASK` GENMASK(11,0) :505; `_ADBW_MASK` GENMASK(23,12)/`_SHIFT` 12 :506-507; `_CMR` BIT(31) CM request :508.
- `ADP_USB3_CS_3` 0x03 :509; `_SCALE_MASK` GENMASK(5,0) bandwidth scale exponent :510.
- `ADP_USB3_CS_4` 0x04 :511; `_MSLR_MASK` GENMASK(18,12)/`_SHIFT` 12 max supported link rate :512-513; `_MSLR_20G` 0x1 :514.

##### `enum tb_port_type` — drivers/thunderbolt/tb_regs.h:268-280
Protocol-adapter members: `TB_TYPE_DP_HDMI_IN`=0x0e0101 :274, `TB_TYPE_DP_HDMI_OUT`=0x0e0102 :275, `TB_TYPE_PCIE_DOWN`=0x100101 :276, `TB_TYPE_PCIE_UP`=0x100102 :277, `TB_TYPE_USB3_DOWN`=0x200101 :278, `TB_TYPE_USB3_UP`=0x200102 :279. Stored as `enum tb_port_type type:24` in `struct tb_regs_port_header` (tb_regs.h:294).

##### Sideband transaction register (in the USB4 port cap) — drivers/thunderbolt/tb_regs.h:374-383
`PORT_CS_1` 0x01 :374 — the sideband command/status word. `_LENGTH_SHIFT` 8 :375; `_TARGET_MASK` GENMASK(18,16)/`_SHIFT` 16 :376-377; `_RETIMER_INDEX_SHIFT` 20 :378; `_WNR_WRITE` BIT(24) :379; `_NR` BIT(25) no-response→`-ENODEV` :380; `_RC` BIT(26) result code→`-EIO` :381; `_PND` BIT(31) pending :382. `PORT_CS_2` 0x02 :383 — the 16-dword sideband data window.

##### `struct tb_retimer` — drivers/thunderbolt/tb.h:339-352 (kerneldoc :326-338) — EVERY field
- `struct device dev` :340 — the retimer's bus device; parent is `&port->usb4->dev`; released by `tb_retimer_release`.
- `struct tb *tb` :341 — owning domain; source of the serializing `tb->lock`.
- `u8 index` :342 — retimer index (1..TB_MAX_RETIMER_INDEX) facing the router USB4 port; the sideband target index.
- `u32 vendor` :343 — VendorID read from `USB4_SB_VENDOR_ID`; exposed as sysfs `vendor`.
- `u32 device` :344 — ProductID read from `USB4_SB_PRODUCT_ID`; exposed as sysfs `device`.
- `struct tb_port *port` :345 — the lane-0 adapter through which sideband runs.
- `struct tb_nvm *nvm` :346 — NVM handle (NULL if none); backs `nvm_version`/nvmem devices.
- `bool no_nvm_upgrade` :347 — set when not on-board, sector size ≤0, or NVM add failed; hides `nvm_authenticate`/`nvm_version` via `retimer_is_visible`.
- `u32 auth_status` :348 — raw status from last NVM authentication; sysfs `nvm_authenticate` read value.
- `struct tb_margining *margining` :349-351 — **gated by `#ifdef CONFIG_USB4_DEBUGFS_MARGINING`**.

##### `struct usb4_port` — drivers/thunderbolt/tb.h:316-324 (kerneldoc :307-315)
`dev` :317 (the `usb4_portX` device); `port` :318 (lane-0 adapter); `can_offline` :319 (platform `_DSM` present — set in drivers/thunderbolt/acpi.c:350); `offline` :320 (current offline state); `margining` :321-323 (**CONFIG_USB4_DEBUGFS_MARGINING**).

##### `struct usb4_port_margining_params` — drivers/thunderbolt/tb.h:1421-1430 (kerneldoc :1409-1420)
`error_counter` (enum `usb4_margin_sw_error_counter`), `ber_level`, `lanes` (enum `usb4_margining_lane`), `voltage_time_offset`, `optional_voltage_offset_range`, `right_high`, `upper_eye`, `time`. Consumed by `usb4_port_hw_margin` and `usb4_port_sw_margin`.

##### `struct retimer_info` — drivers/thunderbolt/usb4.c:2013-2016
`struct tb_port *port; u8 index;` — the private cookie handed to `tb_nvm_read_data`/`tb_nvm_write_data` block callbacks.

##### `struct tb_retimer_lookup` — drivers/thunderbolt/retimer.c:473-476
`const struct tb_port *port; u8 index;` — key for `retimer_match`/`device_find_child`.

##### `struct sb_reg` — drivers/thunderbolt/debugfs.c:67-70 — `{unsigned int reg; unsigned int size;}`, one entry per dumped sideband register.

##### `struct tb_margining` — drivers/thunderbolt/debugfs.c:489-516 (kerneldoc :457-488), **CONFIG_USB4_DEBUGFS_MARGINING**
`port`, `target`, `index`, `dev`, `gen`, `asym_rx`, `caps[3]`, `results[3]`, `lanes`, `min/max/ber_level`, `voltage_steps`, `max_voltage_offset`, `voltage_steps_optional_range`, `max_voltage_offset_optional_range`, `time_steps`, `max_time_offset`, `voltage_time_offset`, `dwell_time`, `error_counter`, `optional_voltage_offset_range`, `software`, `time`, `right_high`, `upper_eye`.

##### Enums
- `enum usb4_sb_target` — tb.h:1377-1381: `USB4_SB_TARGET_ROUTER`(0), `_PARTNER`(1), `_RETIMER`(2). Encoded into `PORT_CS_1_TARGET_MASK`.
- `enum usb4_sb_opcode` — sb_regs.h:21-39 (see §Sideband below).
- `enum usb4_margin_sw_error_counter` — tb.h:1395-1400: NOP/CLEAR/START/STOP.
- `enum usb4_margining_lane` — tb.h:1402-1407: RX0=0, RX1=1, RX2=2, ALL=7.
- `enum tb_nvm_write_ops` — tb.h:68-72: `WRITE_AND_AUTHENTICATE`=1, `WRITE_ONLY`=2, `AUTHENTICATE_ONLY`=3 (drives `nvm_authenticate_store`).

#### 2. API FAMILIES  (S = static/file-local, E = EXPORT_SYMBOL_GPL, otherwise driver-internal external linkage)

##### PCIe adapter
- `tb_pci_port_is_enabled()` switch.c:1387 — reads ADP_PCIE_CS_0, tests `_PE`.
- `tb_pci_port_enable()` switch.c:1405 — writes ADP_PCIE_CS_0 = `_PE` or `0x0` (full-word overwrite, not RMW); `-ENXIO` if `!cap_adap`.
- `usb4_pci_port_set_ext_encapsulation()` usb4.c:3132 — RMW `ADP_PCIE_CS_1_EE`; requires PCIe up/down else `-EINVAL`.
- `usb4_pci_port_ltssm_state()` usb4.c:3162 — `FIELD_GET(ADP_PCIE_CS_0_LTSSM_MASK, ADP_PCIE_CS_0)`; **new at v7.2**.
- `tb_pci_port_ltssm_state_detect()` (S) tunnel.c:293 — polls for `USB4_PCIE_LTSSM_DETECT`; **new at v7.2**.
- `tb_pci_pre_activate()` (S) tunnel.c:312 — the `tunnel->pre_activate` hook; **new at v7.2**; wired at tunnel.c:542.
- `tb_pci_set_ext_encapsulation()` (S) tunnel.c:327 — requires both routers USB4 v2 and gen ≥4 link.
- `tb_pci_activate()` (S) tunnel.c:361 — the ordering: on activate, encapsulation → dst enable → src enable; on deactivate, src → dst → encapsulation off.

##### USB3 adapter
- `tb_usb3_port_is_enabled()` switch.c:1352 / `tb_usb3_port_enable()` switch.c:1370 — writes `_PE|_V` or `_V` alone to ADP_USB3_CS_0.
- `usb4_usb3_port_max_bandwidth()` (S inline) usb4.c:2188 — clamps to `port->max_bw` (quirk-set, drivers/thunderbolt/quirks.c:43).
- `usb4_usb3_port_max_link_rate()` usb4.c:2204 — ADP_USB3_CS_4 MSLR → 20000 or 10000 Mb/s.
- **`usb4_usb3_port_actual_link_rate` does not exist at v7.2** (verified: `grep -rn actual_link_rate drivers/thunderbolt/` returns nothing).
- `usb4_usb3_port_cm_request()` (S) usb4.c:2223 — sets/clears `ADP_USB3_CS_2_CMR`, then waits for `ADP_USB3_CS_1_HCA` to match; host router downstream adapter only.
- `usb4_usb3_port_set_cm_request()` / `_clear_cm_request()` (S inline) usb4.c:2258 / :2263.
- `usb3_bw_to_mbps()` (S) usb4.c:2268 / `mbps_to_usb3_bw()` (S) usb4.c:2276 — 512-byte micro-frame ↔ Mb/s with the scale exponent.
- `usb4_usb3_port_read_allocated_bandwidth()` (S) usb4.c:2285 — ADP_USB3_CS_2 + CS_3 scale.
- `usb4_usb3_port_read_consumed_bandwidth()` (S) usb4.c:2340 — ADP_USB3_CS_1 + CS_3 scale.
- `usb4_usb3_port_write_allocated_bandwidth()` (S) usb4.c:2368 — picks the scale, writes CS_3, then RMW CS_2.
- `usb4_usb3_port_allocated_bandwidth()` usb4.c:2324; `usb4_usb3_port_allocate_bandwidth()` usb4.c:2426; `usb4_usb3_port_release_bandwidth()` usb4.c:2468 — all three bracket the work in set/clear CM request.

##### DP adapter
- `tb_dp_port_hpd_is_active()` switch.c:1422 — reads ADP_DP_CS_2, `_HPD`.
- `tb_dp_port_hpd_clear()` switch.c:1443 — RMW ADP_DP_CS_3 setting `_HPDC`.
- `tb_dp_port_set_hops()` switch.c:1471 — 2-dword RMW at ADP_DP_CS_0; **returns 0 immediately on USB4 routers** (fields are read-only there).
- `tb_dp_port_is_enabled()` switch.c:1505 / `tb_dp_port_enable()` switch.c:1526 — `ADP_DP_CS_0_VE|_AE`.
- `is_usb4_dpin()` (S) usb4.c:2504 — the `-EOPNOTSUPP` gate on every `usb4_dp_port_*`.
- `usb4_dp_port_set_cm_id()` usb4.c:2525 — RMW `ADP_DP_CS_2_CM_ID`.
- `usb4_dp_port_bandwidth_mode_supported()` usb4.c:2555 — reads DP_LOCAL_CAP, `DP_COMMON_CAP_BW_MODE`.
- `usb4_dp_port_bandwidth_mode_enabled()` usb4.c:2581 — reads ADP_DP_CS_8, `_DPME`.
- `usb4_dp_port_set_cm_bandwidth_mode_supported()` usb4.c:2611 — RMW `ADP_DP_CS_2_CMMS`.
- `usb4_dp_port_group_id()` usb4.c:2646 / `usb4_dp_port_set_group_id()` usb4.c:2674 — `ADP_DP_CS_2_GROUP_ID`.
- `usb4_dp_port_nrd()` usb4.c:2707 / `usb4_dp_port_set_nrd()` usb4.c:2766 — `ADP_DP_CS_2_NRD_MLR`/`_NRD_MLC`; rate table 1620/2700/5400/8100, lanes 1/2/4.
- `usb4_dp_port_granularity()` usb4.c:2831 / `usb4_dp_port_set_granularity()` usb4.c:2872 — `ADP_DP_CS_2_GR` ↔ 250/500/1000 Mb/s.
- `usb4_dp_port_set_estimated_bandwidth()` usb4.c:2919 — RMW `ADP_DP_CS_2_ESTIMATED_BW` (divides by granularity). **No reader counterpart exists.**
- `usb4_dp_port_allocated_bandwidth()` usb4.c:2953 — reads `DP_STATUS_ALLOCATED_BW` × granularity.
- `__usb4_dp_port_set_cm_ack()` (S) usb4.c:2977 / `usb4_dp_port_set_cm_ack()` (S inline) usb4.c:2996 — RMW `ADP_DP_CS_2_CA`.
- `usb4_dp_port_wait_and_clear_cm_ack()` (S) usb4.c:3001 — clears CA, polls `ADP_DP_CS_8_DR` to clear, then clears CA again. **This is the request-acknowledge helper.**
- `usb4_dp_port_allocate_bandwidth()` usb4.c:3050 — writes `DP_STATUS_ALLOCATED_BW`, then set-ack + wait-and-clear (500 ms).
- `usb4_dp_port_requested_bandwidth()` usb4.c:3098 — `-ENODATA` if `ADP_DP_CS_8_DR` clear; else `_REQUESTED_BW_MASK` × granularity.
- **DPRX-capability helpers are in tunnel.c, not usb4.c**: `tb_dp_wait_dprx()` (S) tunnel.c:1060 polls `DP_COMMON_CAP_DPRX_DONE`; `tb_dp_dprx_start/stop` (S) tunnel.c:1114/:1134; `tb_dp_dprx_work` (S) tunnel.c:1088.
- DP cap accessors (S inline) tunnel.c:664 `tb_dp_cap_get_rate`, :687 `tb_dp_cap_get_rate_ext` (UHBR20/13.5/10), :699 `tb_dp_is_uhbr_rate`, :704 `tb_dp_cap_set_rate`, :727 `tb_dp_cap_get_lanes`, :743 `tb_dp_cap_set_lanes`; `tb_dp_bandwidth()` (S) tunnel.c:764 (128/132 for UHBR, 8/10 otherwise); `tb_dp_reduce_bandwidth()` (S) tunnel.c:772; `tb_dp_cm_handshake()` (S) tunnel.c:624 (DP_STATUS_CTRL `_UF|_CMHS`); `tb_dp_read_cap()` (S) tunnel.c:1337; `tb_dp_xchg_caps()` (S) tunnel.c:815.
- **Vendor-only branch:** `tb_dp_is_usb4()` (S) tunnel.c:618-622 returns true for Titan Ridge too — flag as vendor-specific.

##### Sideband
- `usb4_port_wait_for_bit()` (S) usb4.c:1305 — generic poll of a port config bit with `fsleep(delay_usec)`.
- `usb4_port_read_data()` / `usb4_port_write_data()` (S) usb4.c:1327 / :1336 — the `PORT_CS_2` data window, capped at `USB4_DATA_DWORDS`.
- `usb4_port_sb_read()` usb4.c:1359 — builds `reg | size<<8 | target<<16 | index<<20 | PND`, writes PORT_CS_1, waits PND=0 (500 ms), decodes `_NR`→`-ENODEV` / `_RC`→`-EIO`, then reads the data window.
- `usb4_port_sb_write()` usb4.c:1412 — same but data first, `_WNR_WRITE` set.
- `usb4_port_sb_opcode_err_to_errno()` (S) usb4.c:1459 — 0→0, `USB4_SB_OPCODE_ERR`→`-EAGAIN`, `USB4_SB_OPCODE_ONS`→`-EOPNOTSUPP`, else `-EIO`.
- `usb4_port_sb_op()` (S) usb4.c:1473 — writes opcode to `USB4_SB_OPCODE`, then re-reads it until it differs from the written value (that is the completion signal), `fsleep(USB4_PORT_SB_DELAY)` per iteration.
- `usb4_port_set_router_offline()` (S) usb4.c:1504; `usb4_port_router_offline()` usb4.c:1529; `usb4_port_router_online()` usb4.c:1542 — metadata=!offline then `USB4_SB_OPCODE_ROUTER_OFFLINE` **written raw, no `sb_op` handshake**.
- `usb4_port_enumerate_retimers()` usb4.c:1556 — raw write of `USB4_SB_OPCODE_ENUMERATE_RETIMERS` (broadcast RT), no handshake.
- `usb4_port_retimer_op()` (S inline) usb4.c:1848 — `usb4_port_sb_op` bound to `USB4_SB_TARGET_RETIMER`.

**Opcode inventory (sb_regs.h:21-39) and its user:**
| opcode | value | user |
|---|---|---|
| `USB4_SB_OPCODE_ERR` | 0x20525245 "ERR " | error decode, usb4.c:1464 |
| `_ONS` | 0x444d4321 "!CMD" | error decode, usb4.c:1466 |
| `_ROUTER_OFFLINE` | 0x4e45534c "LSEN" | usb4.c:1514 |
| `_ENUMERATE_RETIMERS` | 0x4d554e45 "ENUM" | usb4.c:1560 |
| `_SET_INBOUND_SBTX` | 0x5055534c "LSUP" | usb4.c:1870, :1881 |
| `_UNSET_INBOUND_SBTX` | 0x50555355 "USUP" | usb4.c:1897 |
| `_QUERY_LAST_RETIMER` | 0x5453414c "LAST" | usb4.c:1918 |
| `_QUERY_CABLE_RETIMER` | 0x524c4243 "CBLR" | usb4.c:1944 |
| `_GET_NVM_SECTOR_SIZE` | 0x53534e47 "GNSS" | usb4.c:1973 |
| `_NVM_SET_OFFSET` | 0x53504f42 "BOPS" | usb4.c:2009 |
| `_NVM_BLOCK_WRITE` | 0x574b4c42 "BLKW" | usb4.c:2032 |
| `_NVM_AUTH_WRITE` | 0x48545541 "AUTH" | usb4.c:2088 (raw write, no handshake) |
| `_NVM_READ` | 0x52524641 "AFRR" | usb4.c:2156 |
| `_READ_LANE_MARGINING_CAP` | 0x50434452 "RDCP" | usb4.c:1717 |
| `_RUN_HW_LANE_MARGINING` | 0x474d4852 "RHMG" | usb4.c:1765 |
| `_RUN_SW_LANE_MARGINING` | 0x474d5352 "RSMG" | usb4.c:1814 |
| `_READ_SW_MARGIN_ERR` | 0x57534452 "RDSW" | usb4.c:1840 |

**Sideband register map (sb_regs.h):** `USB4_SB_VENDOR_ID` 0x00 :13; `_PRODUCT_ID` 0x01 :14; `_FW_VERSION` 0x02 :15 (retimer only); `_DEBUG_CONF` 0x05 :16; `_DEBUG` 0x06 :17; `_LRD_TUNING` 0x07 :18; `_OPCODE` 0x08 :19; `_METADATA` 0x09 :41 with `_NVM_AUTH_WRITE_MASK` GENMASK(5,0) :42; `_LINK_CONF` 0x0c :43; `_GEN23_TXFFE` 0x0d :44; `_GEN4_TXFFE` 0x0e :45; `_VERSION` 0x0f :46; `_DATA` 0x12 :47. **TxFFE registers are read/written only through the debugfs `sb_regs` dump/write tables (debugfs.c:84-85, :98-99) — no in-driver helper touches them.**

##### Retimer
- `usb4_port_retimer_set_inbound_sbtx()` usb4.c:1866 — issues SET_INBOUND_SBTX and **retries once on `-ENODEV`** (spec: no RT response for the first command).
- `usb4_port_retimer_unset_inbound_sbtx()` usb4.c:1895.
- `usb4_port_retimer_is_last()` usb4.c:1913 / `usb4_port_retimer_is_cable()` usb4.c:1939 — opcode then metadata `& 1`.
- `usb4_port_retimer_nvm_sector_size()` usb4.c:1968 — metadata `& USB4_NVM_SECTOR_SIZE_MASK`.
- `usb4_port_retimer_nvm_set_offset()` usb4.c:1994; `_nvm_write_next_block()` (S) usb4.c:2018; `usb4_port_retimer_nvm_write()` usb4.c:2052; `usb4_port_retimer_nvm_authenticate()` usb4.c:2079 (**raw `sb_write` on purpose** — the retimer loses its index on success); `usb4_port_retimer_nvm_authenticate_status()` usb4.c:2106 (`-EAGAIN` from the opcode decode is the "status available" path); `_nvm_read_block()` (S) usb4.c:2138; `usb4_port_retimer_nvm_read()` usb4.c:2179.
- `tb_retimer_nvm_read()` retimer.c:34; `nvm_read()` (S) retimer.c:40 / `nvm_write()` (S) retimer.c:63 (nvmem callbacks); `tb_retimer_nvm_add()` (S) retimer.c:78; `tb_retimer_nvm_validate_and_write()` (S) retimer.c:116; `tb_retimer_nvm_authenticate()` (S) retimer.c:138.
- `tb_retimer_nvm_authenticate_status()` (S, static void, name-collides with the usb4 one) retimer.c:197 — pre-reads status for indices 1..MAX before enumeration.
- `tb_retimer_set_inbound_sbtx()` (S) retimer.c:214 / `tb_retimer_unset_inbound_sbtx()` (S) retimer.c:231 — both **no-op unless the offline state matches** (`usb4_port_device_is_offline`, tb.h:1503).
- `tb_retimer_release()` (S) retimer.c:376; `tb_retimer_type` retimer.c:383; `tb_retimer_add()` (S) retimer.c:389; `tb_retimer_remove()` (S) retimer.c:465; `retimer_match()` (S) retimer.c:478; `tb_port_find_retimer()` (S) retimer.c:486; `tb_retimer_scan()` retimer.c:510; `remove_retimer()` (S) retimer.c:576; `tb_retimer_remove_all()` retimer.c:592.
- sysfs: `device_show` retimer.c:169, `nvm_authenticate_show` :178 / `_store` :251, `nvm_version_show` :317, `vendor_show` :336, `retimer_is_visible` :345, `retimer_attrs` :358, `retimer_group` :366, `retimer_groups` :371.
- offline/rescan seam: `usb4_port_offline()` (S) usb4_port.c:76, `usb4_port_online()` (S) usb4_port.c:100, `offline_show/store` usb4_port.c:151/:159, `rescan_store` usb4_port.c:210, `service_attr_is_visible` usb4_port.c:258 (gated on `can_offline`), `usb4_port_device_resume()` usb4_port.c:363.
- ACPI seam (**CONFIG_ACPI**, tb.h:1510-1536): `tb_acpi_retimer_set_power()` (S) acpi.c:188, `tb_acpi_power_on_retimers()` acpi.c:263, `tb_acpi_power_off_retimers()` acpi.c:277, `retimer_dsm_guid` acpi.c:181-183, `can_offline` set in `tb_acpi_setup()` acpi.c:350.
- `usb4_usb3_port_match()` (E) usb4_port.c:118 — the only EXPORT_SYMBOL_GPL in the area's files (usb4_port.c:149).

##### Margining (all **CONFIG_USB4_DEBUGFS_MARGINING** consumers; the usb4.c helpers themselves are unconditional)
- `usb4_port_margining_caps()` usb4.c:1711 — RDCP (500 ms) then read `USB4_SB_DATA` into `caps[ncaps]`.
- `usb4_port_hw_margin()` usb4.c:1739 — builds metadata from params (`USB4_MARGIN_HW_TIME`, `_RHU`, `_BER_MASK`, `_OPT_VOLTAGE`), RHMG (2500 ms), reads results.
- `usb4_port_sw_margin()` usb4.c:1786 — `USB4_MARGIN_SW_TIME`, `_OPT_VOLTAGE`, `_RH`, `_UPPER_EYE`, `_COUNTER_MASK`, `_VT_MASK`; RSMG (2500 ms).
- `usb4_port_sw_margin_errors()` usb4.c:1834 — RDSW (150 ms) then read `USB4_SB_METADATA`.
- Both hw/sw guard `WARN_ON_ONCE(!params)` (usb4.c:1746, :1793).

#### 3. LIFECYCLE AND LOCKING

- **Serializing lock: `tb->lock` (a mutex) for everything in this area.** Sysfs readers use `mutex_trylock` + `restart_syscall()` (retimer.c:48, :69, :184, :259, :323); usb4_port and debugfs use `mutex_lock_interruptible` → `-ERESTARTSYS` (usb4_port.c:174, :228; debugfs.c:2395, :2510, :1241). There is no per-retimer or per-adapter lock.
- **Retimer lifecycle:** `tb_retimer_scan()` retimer.c:510 → ENUM broadcast (usb4.c:1556) → pre-read auth status for 1..MAX (retimer.c:527) → `tb_retimer_set_inbound_sbtx` (retimer.c:533) → probe `is_last` upward to find `max`/`last_idx` (retimer.c:535-548) → clamp `max = min(last_idx, max)` unless margining is enabled (retimer.c:551-552) → per index skip cable retimers (retimer.c:559) → `tb_port_find_retimer` / `tb_retimer_add` (retimer.c:562-569) → `tb_retimer_unset_inbound_sbtx` (retimer.c:572).
- `tb_retimer_add()` retimer.c:389: sideband VendorID/ProductID reads → `kzalloc_obj` :413 → `no_nvm_upgrade` decision :428 → `device_register` :437 (on failure `put_device` :440) → `tb_retimer_nvm_add` :444 (on failure `device_unregister` :447) → runtime-PM enable with `TB_AUTOSUSPEND_DELAY` :454-459 → `tb_retimer_debugfs_init` :461.
- **Refcounting:** `tb_port_find_retimer` returns a reference from `device_find_child` (retimer.c:491); `tb_retimer_scan` drops it with `put_device` at retimer.c:564. `tb_retimer_release` (retimer.c:376) `kfree`s only after the last reference.
- `tb_retimer_remove()` retimer.c:465 → debugfs remove → `tb_nvm_free` → `device_unregister`. `tb_retimer_remove_all()` retimer.c:592 walks children **in reverse** (`device_for_each_child_reverse`, retimer.c:598).
- **NVM auth state machine** (`nvm_authenticate_store`, retimer.c:251-314): `rt->auth_status = 0` always cleared first (:274); `AUTHENTICATE_ONLY`(3) → set offset 0 then AUTH (:285-286); otherwise if `!nvm->flushed` require `nvm->buf` (:288-292) then validate+write (:294); `WRITE_ONLY`(2) stops there (:295); `WRITE_AND_AUTHENTICATE`(1) proceeds to auth (:298-299). `tb_retimer_unset_inbound_sbtx` is called **only** on error or WRITE_ONLY (:304-305) because the retimer is unreachable during authentication. `tb_retimer_nvm_authenticate` (retimer.c:138) sleeps 100-150 µs then reads status; a *failed* status read is treated as success (`return 0`, :166) since the index is gone.
- **Resume behavior:** there is no `tb_retimer_resume`. Retimer state is re-established through `tb_port_resume` → `usb4_port_device_resume` (switch.c:1302 → usb4_port.c:363), which re-enters offline mode (re-powering retimers and re-scanning) only if the port was offline. On normal resume retimers are re-discovered by `tb_retimer_scan` from `tb_scan_port`.
- **Removal seams:** switch.c:3453 (`tb_switch_remove`), tb.c:1799 (`tb_free_unplugged_children`), tb.c:2459 (unplug hotplug), tb.c:3131 (`tb_free_unplugged_xdomains`).

#### 4. HARD-CODED LIMITS

- `USB4_DATA_DWORDS` 16 — usb4.c:19 (sideband/data window cap; enforced usb4.c:1329, :1339).
- `USB4_DATA_RETRIES` 3 — usb4.c:18 (NVM block retry count).
- `USB4_PORT_DELAY` 50 µs — usb4.c:51.
- `USB4_PORT_SB_DELAY` 1000 µs — usb4.c:52.
- Sideband PND wait: **500 ms** bare literal — usb4.c:1382 and usb4.c:1442.
- `usb4_port_sb_op` timeouts (bare literals at call sites): 500 ms (SET/UNSET_INBOUND_SBTX usb4.c:1871/:1882/:1898; LAST :1919; CBLR :1945; GNSS :1974; BOPS :2010; NVM_READ :2156; RDCP :1717); **1000 ms** (BLKW usb4.c:2033); **2500 ms** (RHMG usb4.c:1765, RSMG usb4.c:1814); **150 ms** (RDSW usb4.c:1840).
- `TB_MAX_RETIMER_INDEX` — **2 normally, 6 when CONFIG_USB4_DEBUGFS_MARGINING** — retimer.c:17-21. Status array sized `TB_MAX_RETIMER_INDEX + 1` at retimer.c:512.
- `usleep_range(100, 150)` after NVM auth — retimer.c:153.
- `TB_AUTOSUSPEND_DELAY` 15000 ms — tb.h:550.
- NVM: `USB4_NVM_SECTOR_SIZE_MASK` GENMASK(23,0) usb4.c:34; `USB4_NVM_READ_OFFSET_MASK` GENMASK(23,2)/`_SHIFT` 2 usb4.c:21-22; `_READ_LENGTH_MASK` GENMASK(27,24)/`_SHIFT` 24 usb4.c:23-24; `_SET_OFFSET_*` alias usb4.c:26-27; `USB4_SB_METADATA_NVM_AUTH_WRITE_MASK` GENMASK(5,0) sb_regs.h:42. Block size `NVM_DATA_DWORDS` 16 (=64 bytes) nvm.c:17, used in nvm.c:566, :571, :613, :618. Image bounds `NVM_MIN_SIZE` SZ_32K nvm.c:15, `NVM_MAX_SIZE` SZ_1M nvm.c:16 (checked nvm.c:392, buffer nvm.c:479).
- USB3 bandwidth: scale search loop bounded at **64** (usb4.c:2378, `WARN_ON(scale >= 64)` :2384); per-scale field cap **4096** (usb4.c:2379); micro-frame unit **512** bytes and **8000** µframes/s (usb4.c:2272-2273, :2281-2282); CM-request/HCA wait **1500 ms** (usb4.c:2254); USB3 release floor **900 Mb/s** both directions (usb4.c:2486-2489); max link rate **20000/10000 Mb/s** (usb4.c:2218); quirked cap `port->max_bw = 16376` (quirks.c:43).
- DP: granularities **250 / 500 / 1000** Mb/s (usb4.c:2849-2853, :2888-2896); rate table **1620 / 2700 / 5400 / 8100** (usb4.c:2723-2732, :2782-2795; tunnel.c:670-676, :711-722); UHBR rates **10000 / 13500 / 20000** (tunnel.c:690-694); lane table **1/2/4** (usb4.c:2739-2745, :2803-2809); UHBR threshold **10000** (tunnel.c:701); encoding ratios **128/132** and **8/10** (tunnel.c:768-769); `dp_bw[12][2]` reduction table tunnel.c:776-790; CM-ack clear wait **500 ms** (usb4.c:3080) with `usleep_range(50, 100)` poll (usb4.c:3022); DP CM handshake poll `usleep_range(100, 150)` (tunnel.c:654); DPRX poll `usleep_range(100, 150)` (tunnel.c:1081); `TB_DPRX_WAIT_TIMEOUT` 25 ms tunnel.c:82, `TB_DPRX_POLL_DELAY` 50 ms tunnel.c:83, `TB_BW_ALLOC_RETRIES` 3 tb.c:26.
- PCIe LTSSM detect: **500 ms** timeout with **50 µs** `fsleep` — tunnel.c:295, :306.
- Debugfs: `SB_MAX_SIZE` 64 debugfs.c:72; per-register sizes in `port_sb_regs` (debugfs.c:75-88, note `USB4_SB_DEBUG` 54 bytes, `USB4_SB_DATA` 64, `USB4_SB_LINK_CONF` 3) and `retimer_sb_regs` (debugfs.c:91-102); `MIN_DWELL_TIME` 100 ms / `MAX_DWELL_TIME` 500 ms debugfs.c:44-45; `DWELL_SAMPLE_INTERVAL` 10 ms debugfs.c:46; margining voltage offset formula `74 + val * 2` mV (debugfs.c:1692, :1697, :1706) and time offset `200 + 10 * val` mUI (debugfs.c:1717); `dir_name[10]` (debugfs.c:1770, :1785).

#### 5. VERSION-SPECIFIC FACTS (v7.2 vs widely-documented older kernels)

- **New at v7.2:** `ADP_PCIE_CS_0_LTSSM_MASK` (tb_regs.h:476), `enum tb_pcie_ltssm_state` (tb_regs.h:481-493), `usb4_pci_port_ltssm_state()` (usb4.c:3162, proto tb.h:1484), `tb_pci_port_ltssm_state_detect()` (tunnel.c:293), `tb_pci_pre_activate()` (tunnel.c:312) — commit `69a7b98770b7`.
- **Renamed after v6.12** (sb_regs.h): `USB4_MARGIN_CAP_0_2_LANES` → `USB4_MARGIN_CAP_0_ALL_LANES`; `USB4_MARGIN_HW_RH` → `USB4_MARGIN_HW_RHU`; `USB4_MARGIN_HW_RES_1_MARGIN_MASK`/`_RES_1_EXCEEDS` → `USB4_MARGIN_HW_RES_MARGIN_MASK`/`_RES_EXCEEDS`.
- **Removed after v6.12:** `USB4_MARGIN_HW_RES_1_L0_LL_MARGIN_SHIFT`, `_L1_RH_MARGIN_SHIFT`, `_L1_LL_MARGIN_SHIFT` (replaced by `USB4_MARGIN_HW_RES_LANE_SHIFT` 16 / `_RES_LL_SHIFT` 8); `USB4_MARGIN_SW_LANE_0/_LANE_1/_ALL_LANES` (replaced by `enum usb4_margining_lane`, tb.h:1402).
- **Added after v6.12:** the whole `USB4_MARGIN_CAP_2_*` gen-4/PAM3 block (sb_regs.h:72-82), `USB4_MARGIN_SW_UPPER_EYE` (:106), `USB4_MARGIN_SW_ERR_COUNTER_LANE_2_MASK` (:110).
- **Added after v6.6:** `usb4_port_retimer_is_cable()` and cable-retimer skipping in `tb_retimer_scan`; `struct usb4_port_margining_params` (previously long positional arg lists on `usb4_port_hw_margin`/`_sw_margin`).
- **Renamed between v6.12 and v6.17:** `usb4_port_idx()` (static) → `usb4_port_index()` (non-static, tb.h:1501, usb4.c:982).
- **Allocator idiom changed at v7.0:** `kzalloc(sizeof(*rt), GFP_KERNEL)` → `kzalloc_obj(*rt)` (retimer.c:413).
- **Retimer sysfs visibility changed after v6.12:** `nvm_authenticate`/`nvm_version` no longer return `-EOPNOTSUPP` when `no_nvm_upgrade`; they are hidden by `retimer_is_visible()` (retimer.c:345-356) instead. A page written against v6.12 misstates this.
- Stable across the range: `usb4_dp_port_*` names (no `bw_mode`/`allocated_bw` short forms ever existed), `TB_MAX_RETIMER_INDEX`, `usb4_port_sb_opcode_err_to_errno`, `ADP_USB3_CS_4_MSLR_20G`, `DP_COMMON_CAP_UHBR*`.

#### 6. SUGGESTED PAGE TOPICS (one mechanism per page)

1. **Adapter capability structure discovery** — `cap_adap`/`cap_usb4` (tb.h:287-288), `TB_PORT_CAP_ADAP`/`_USB4` (tb_regs.h:44-46), switch.c:723-753; why every helper does `port->cap_adap + ADP_*_CS_n`.
2. **PCIe adapter enable/disable** — `tb_pci_port_enable/is_enabled` (switch.c:1387/:1405), `ADP_PCIE_CS_0_PE`, and the non-RMW full-word write.
3. **PCIe extended encapsulation** — `usb4_pci_port_set_ext_encapsulation` (usb4.c:3132), `tb_pci_set_ext_encapsulation` (tunnel.c:327), the USB4-v2-and-gen4 gate.
4. **PCIe LTSSM detect gate (v7.2)** — `enum tb_pcie_ltssm_state`, `usb4_pci_port_ltssm_state`, `tb_pci_port_ltssm_state_detect`, `tb_pci_pre_activate`.
5. **USB3 adapter enable and the V bit** — `tb_usb3_port_enable/is_enabled` (switch.c:1352/:1370).
6. **USB3 CM request handshake** — `usb4_usb3_port_cm_request` (usb4.c:2223), CMR/HCA, 1500 ms.
7. **USB3 bandwidth scaling arithmetic** — `usb3_bw_to_mbps`/`mbps_to_usb3_bw`/`_write_allocated_bandwidth` (usb4.c:2268-2408), the scale search.
8. **USB3 allocate/release** — usb4.c:2426/:2468, the 900 Mb/s floor, consumed-can't-be-taken-away rule.
9. **DP adapter hop programming and enable** — `tb_dp_port_set_hops`/`_enable`/`_is_enabled` (switch.c:1471-1543), the USB4 read-only-field short circuit.
10. **DP HPD** — `tb_dp_port_hpd_is_active`/`_hpd_clear` (switch.c:1422/:1443), ADP_DP_CS_2_HPD / ADP_DP_CS_3_HPDC.
11. **DP capability exchange** — `tb_dp_cm_handshake`, `tb_dp_xchg_caps`, LOCAL/REMOTE/COMMON cap copy, LTTPR_NS (tunnel.c:624-912).
12. **DP rate/lane encoding and the reduction table** — tunnel.c:664-813.
13. **DP bandwidth allocation mode enablement** — `usb4_dp_port_set_cm_id`/`_set_cm_bandwidth_mode_supported`/`_set_group_id`/`_set_nrd`/`_set_granularity` and `tb_dp_bandwidth_alloc_mode_enable` (tunnel.c:914).
14. **DP request/allocate/acknowledge cycle** — `usb4_dp_port_requested_bandwidth`, `_allocate_bandwidth`, `__set_cm_ack`, `_wait_and_clear_cm_ack` (usb4.c:2953-3120).
15. **DPRX capability read completion** — `DP_COMMON_CAP_DPRX_DONE`, `tb_dp_wait_dprx`, `tb_dp_dprx_work` (tunnel.c:1060-1142) — *not in the request's list*.
16. **Sideband transaction protocol** — PORT_CS_1 encoding, PND/NR/RC, `usb4_port_sb_read/write` (usb4.c:1359/:1412).
17. **Sideband opcode handshake** — `usb4_port_sb_op`, `usb4_port_sb_opcode_err_to_errno`, why some opcodes bypass it (usb4.c:1459-1502, :1514, :2088).
18. **Sideband register map** — sb_regs.h in full, including the TxFFE/LINK_CONF registers only debugfs touches — *not in the request's list*.
19. **Router offline mode** — `usb4_port_router_offline/online` (usb4.c:1529/:1542), `usb4_port_offline/online` (usb4_port.c:76/:100).
20. **Inbound SBTX** — `usb4_port_retimer_set/unset_inbound_sbtx`, the first-command `-ENODEV` retry, the offline-state guards (usb4.c:1866, retimer.c:214/:231).
21. **Retimer enumeration** — `usb4_port_enumerate_retimers`, `_is_last`, `_is_cable`, `tb_retimer_scan` (retimer.c:510).
22. **Retimer device model** — `struct tb_retimer`, `tb_retimer_type`, add/remove/release, refcount, lookup.
23. **Retimer NVM read/write over sideband** — sector size, set offset, block write/read, `tb_nvm_read_data`/`write_data` plumbing.
24. **Retimer NVM authentication state machine** — `nvm_authenticate_store`, `enum tb_nvm_write_ops`, `auth_status`, index loss.
25. **Offline no-cable NVM upgrade flow** — offline/rescan sysfs + ACPI `_DSM` power (usb4_port.c, acpi.c:180-280) tied to the admin-guide section.
26. **ACPI retimer power resources** — `retimer_dsm_guid`, `can_offline`, `tb_acpi_power_on/off_retimers` — *not in the request's list*.
27. **Lane margining sideband API** — caps/hw/sw/errors + `struct usb4_port_margining_params`.
28. **Margining debugfs surface** — `struct tb_margining`, file set, gen<4 vs gen≥4 cap parsing.
29. **Sideband register debugfs dump/write** — `sb_reg` tables, `sb_regs_show/write`, taint (debugfs.c:339) — *not in the request's list*.
30. **`tb_port_is_enabled` dispatcher** — switch.c:1326-1344, the single type-switch entry point — *not in the request's list*.

#### 7. TRACING

**Verified negative.** `grep -rn "trace_" drivers/thunderbolt/` shows tracepoint call sites only in drivers/thunderbolt/ctl.c (`trace_tb_tx`, `trace_tb_event`, `trace_tb_rx`); the events themselves are defined in drivers/thunderbolt/trace.h:153, :158, :163 and cover raw control packets, not adapter/sideband/retimer operations. No `trace_` call exists in usb4.c, retimer.c, switch.c, debugfs.c, usb4_port.c, tb_regs.h or sb_regs.h. Sideband and adapter register traffic is therefore observable only through `tb_port_dbg` and the debugfs dumps.

#### 8. DEBUG AND DIAGNOSTIC PRINTING

- Macros: `tb_port_dbg`/`tb_port_warn`/`tb_port_WARN` built on `__TB_PORT_PRINT` (tb.h, the `tb_dbg` family redefined at tb.h:725-729 to use `(tb)->nhi->dev`); `tb_sw_dbg`/`tb_sw_warn`; `tb_tunnel_dbg`/`tb_tunnel_warn`; plain `dev_dbg`/`dev_info`/`dev_err` in retimer.c.
- Per-file counts (v7.2): usb4.c — 2 `tb_port_dbg`, 1 `tb_port_warn`, 10 `tb_sw_dbg`, 4 WARN-family. retimer.c — 3 `tb_port_dbg`, 2 `tb_port_warn`, 2 `dev_dbg`, 0 WARN. switch.c — 12 `tb_port_dbg`, 7 `tb_port_warn`, 17 `tb_sw_dbg`, 3 WARN. debugfs.c — 2 `tb_port_dbg`, 4 `tb_port_warn`, 0 WARN. usb4_port.c — 1 `tb_port_dbg`, 0 WARN. tunnel.c — 4 `tb_port_dbg`, 3 `tb_port_warn`, 9 WARN-family.
- Notable WARNs inside the area's mechanisms: `WARN_ON(scale >= 64)` usb4.c:2384; `WARN_ON_ONCE(!params)` usb4.c:1746 and :1793; `WARN(1, ...)` on invalid DP rate/lane tunnel.c:709 and :748.
- Control knobs: dynamic debug (`dyndbg`) for all `*_dbg`; the debugfs tree under `/sys/kernel/debug/thunderbolt/` (see §10); module params `dprx_timeout` (tunnel.c:85-87, 0444), `bw_alloc_mode` (tunnel.c:97), `dma_credits` (tunnel.c:92). Writing sideband registers via debugfs calls `add_taint(TAINT_USER, LOCKDEP_STILL_OK)` (debugfs.c:339).

#### 9. ASYNCHRONOUS / DEFERRED / LAZY PROCESSING

- **Polling loops (the dominant class here).** `usb4_port_wait_for_bit()` usb4.c:1305 — caller-supplied interval/timeout; used for sideband PND (1000 µs / 500 ms, usb4.c:1382, :1442) and USB3 HCA (50 µs / 1500 ms, usb4.c:2253-2255). `usb4_port_sb_op()` usb4.c:1488-1499 — opcode-completion loop, 1000 µs interval, per-opcode timeout. `usb4_dp_port_wait_and_clear_cm_ack()` usb4.c:3013-3023 — 50-100 µs, 500 ms. `tb_pci_port_ltssm_state_detect()` tunnel.c:297-307 — 50 µs, 500 ms. `tb_dp_cm_handshake()` tunnel.c:647-655 — 100-150 µs, caller timeout. `tb_dp_wait_dprx()` tunnel.c:1069-1082 — 100-150 µs. `margining_run_sw()` debugfs.c:1164-1189 — `dwell_time / DWELL_SAMPLE_INTERVAL` iterations at 10 ms.
- **Delayed work.** `tb_dp_dprx_work` — queued at tunnel.c:1126 (`tb_dp_dprx_start`, delay 0) and re-queued at tunnel.c:1098 with `TB_DPRX_POLL_DELAY` 50 ms; runs on `tb->wq`, handler tunnel.c:1088; cancelled by `tb_dp_dprx_stop` tunnel.c:1139. Holds `tb->lock` while polling and takes a tunnel reference across the work.
- **Non-work deferral.** `tb_handle_dp_bandwidth_request` (queued tb.c:2881-2882 on `tb->wq`) is the consumer of `usb4_dp_port_requested_bandwidth`; it self-requeues up to `TB_BW_ALLOC_RETRIES` (tb.c:2830).
- **Verified negatives:** no `struct completion`, no `wait_event*`, no timers, no threaded IRQ, no RCU and no tasklet anywhere in usb4.c, retimer.c, sb_regs.h, usb4_port.c or the adapter helpers of switch.c. Sideband and retimer NVM operations are entirely synchronous polling under `tb->lock`, executed in process context (sysfs store, debugfs write, or the domain workqueue via hotplug).
- **Lazy work.** `tb_retimer_scan` is deliberately deferred until after router enumeration (comment and call at tb.c:1383-1389) to avoid tripping Pluggable-device enumeration timeouts.

#### 10. SUBSYSTEM-SPECIFIC DEBUGGING INFRASTRUCTURE

- **Root:** `tb_debugfs_root` = `/sys/kernel/debug/thunderbolt` (debugfs.c:125, created debugfs.c:2557). Gate: `CONFIG_DEBUG_FS` (tb.h:1538-1560 provides no-op stubs).
- **Port sideband dump:** `port%d/sb_regs` created only when `port->usb4` (debugfs.c:2448-2450); mode `DEBUGFS_MODE` = 0600 with `CONFIG_USB4_DEBUGFS_WRITE`, else 0400 (debugfs.c:446, :453). Show `port_sb_regs_show` debugfs.c:2386, write `port_sb_regs_write` debugfs.c:381 (**CONFIG_USB4_DEBUGFS_WRITE**; NULL otherwise, debugfs.c:451). Table `port_sb_regs[]` debugfs.c:75-88. Common renderer `sb_regs_show` debugfs.c:2357 (prints `<not accessible>` and continues per register since v7.2), writer `sb_regs_write` debugfs.c:330, line parser `parse_sb_line` debugfs.c:300.
- **Retimer sideband dump:** `<device>:<port>.<index>/sb_regs` (debugfs.c:2538-2539); show debugfs.c:2502, write debugfs.c:414; table `retimer_sb_regs[]` debugfs.c:91-102. Created by `tb_retimer_debugfs_init` debugfs.c:2533 (called retimer.c:461), removed by `tb_retimer_debugfs_remove` debugfs.c:2549 (called retimer.c:468).
- **Margining files (CONFIG_USB4_DEBUGFS_MARGINING, which itself `depends on DEBUG_FS && USB4_DEBUGFS_WRITE`, Kconfig:38-41):** directory `margining/` under the USB4 port dir or the retimer dir (debugfs.c:1720). Files: `ber_level_contour` (0400, only if HW margining, debugfs.c:1730), `caps` (0400, :1733), `lanes` (0600, :1734), `mode` (0600, :1735), `run` (0600, :1736), `results` (0600, :1737), `test` (0600, :1739), `margin` (0600, conditional, :1743), `optional_voltage_offset` (:1749), `voltage_time_offset`/`error_counter`/`dwell_time` (SW only, :1753-1758), `eye` (gen ≥4, :1762). Allocator `margining_alloc` (ends debugfs.c:1765), port init/remove debugfs.c:1767/:1782, switch init/remove :1801/:1818, xdomain :1835/:1846, retimer :1856/:1863; no-op stubs :1869-1875.
- **Retimer sysfs:** `device`, `vendor`, `nvm_version`, `nvm_authenticate` (retimer.c:358-374), plus `nvm_activeN`/`nvm_non_activeN` nvmem devices from `tb_retimer_nvm_add` (retimer.c:78). USB4 port sysfs: `link` (usb4_port.c:65), `offline`/`rescan` (usb4_port.c:208/:250, visible only if `can_offline`).
- **KUnit (CONFIG_USB4_KUNIT_TEST, Kconfig:49-52):** **verified negative for this area.** `grep -n "retimer|sb_regs|ADP_DP_CS|ADP_PCIE|ADP_USB3|margining" drivers/thunderbolt/test.c` returns nothing. The PCIe/DP/USB3 tunnel cases (`tb_test_tunnel_pcie` test.c:1334, `_dp` :1389, `_usb3` :1669, credit-alloc cases :2090-:2250) exercise path/credit allocation on mock routers where `cap_adap` is stubbed (test.c:120, :125, :184, :287, :292, :385) and never reach the adapter register helpers. No sideband, retimer or margining KUnit coverage exists.

#### 11. v7.0 → v7.2 DRIFT LEDGER

`git log --oneline v7.0..v7.2 -- <area paths>` → 16 commits; `git diff v7.0..v7.2 --stat` → debugfs.c +18/-, switch.c +107, tb.h +26, tb_regs.h +19, tunnel.c +45, usb4.c +35, usb4_port.c +2. **retimer.c and sb_regs.h are byte-identical between v7.0 and v7.2**, as are `Documentation/ABI/testing/sysfs-bus-thunderbolt` and the retimer sections of `Documentation/admin-guide/thunderbolt.rst`.

Symbols added:
- `ADP_PCIE_CS_0_LTSSM_MASK` — new, tb_regs.h:476 (`69a7b98770b7`).
- `enum tb_pcie_ltssm_state` (11 members) — new, tb_regs.h:481-493 (`69a7b98770b7`).
- `usb4_pci_port_ltssm_state()` — new, usb4.c:3162; prototype tb.h:1484 (`69a7b98770b7`).
- `tb_pci_port_ltssm_state_detect()` — new, tunnel.c:293 (`69a7b98770b7`).
- `tb_pci_pre_activate()` — new, tunnel.c:312, wired to `tunnel->pre_activate` at tunnel.c:542 (`69a7b98770b7`).
- `ROUTER_CS_6_RR` — new, tb_regs.h:218 (`062023c4364f`); router-scope, adjacent to this area.

Symbols renamed/removed in this area: **none**.

Behavior changes a v7.0-written page would now misstate (one line each):
- PCIe tunnel activation now *first* waits (500 ms, 50 µs poll) for both USB4 PCIe adapters to report LTSSM `DETECT`; `tb_tunnel_alloc_pci` installs a `pre_activate` hook that did not exist at v7.0 — `69a7b98770b7`.
- `sb_regs_show` no longer aborts the whole dump on the first failing sideband register; it prints `0x%02x <not accessible>` and continues (debugfs.c:2372-2375) — `babaad95670d`.
- `sb_regs_write` size check was against the whole table entry pointer (`sb_regs->size`, i.e. entry 0) and is now against the matched register (`sb_reg->size`, debugfs.c:369) — `c1bef05763c9`.
- `margining_error_counter_write` freed its page on every path; the invalid-input path now goes through `err_free` instead of leaking (debugfs.c:959-977) — `503c5ae1e72a`.
- `margining_port_remove` now returns early when `port->usb4->margining` is NULL (debugfs.c:1789-1790) — `a8937f35cf39`.
- `usb4_switch_setup` now additionally waits 500 ms for `ROUTER_CS_6_RR` (usb4.c:297-302) — `062023c4364f`; and `usb4_switch_configuration_valid`'s CR wait grew 50 ms → 500 ms (usb4.c:334-335) — `ba2cc3851101`.
- `usb4_switch_configuration_valid` kerneldoc corrected: "does nothing for the *former*" (host), not "latter" (usb4.c:312) — `062023c4364f`.
- `tb_switch_reset_host` now skips path-config cleanup on USB4 Lane 1 adapters (switch.c:1601-1606) — `95c4379e37a0`; the protocol-adapter disable arms (`tb_usb3_port_enable`/`tb_dp_port_enable`/`tb_pci_port_enable`, switch.c:1607-1615) are unchanged.
- All `tb_err/tb_warn/tb_info/tb_dbg` now resolve through `(tb)->nhi->dev` rather than `&(tb)->nhi->pdev->dev` (tb.h:725-729) — `8c3ff7c5ae15`; `usb4_usb3_port_match` follows suit (usb4_port.c:141) — same series.
- `struct tb_path` gained a flexible `hops[]` array (tb.h:443), so `tunnel->paths`/`path->hops` are no longer separately allocated (tunnel.c:183) — `c3e7cc8bc5ca`; affects any page that described tunnel/path allocation.
- Plug-events delay: `tb_plug_events_active` no longer programs 0xff, and `tb_switch_configure` now sets 255 ms for *all* routers (previously 0xa for USB4) — `e24f3c0df483`.

#### 12. DOCUMENTATION AND ABI

- `Documentation/admin-guide/thunderbolt.rst:199-277` — "Upgrading NVM on Thunderbolt device, host or retimer" (heading :199-200; fwupd recommendation :206-209; hazard warning :211-214; `nvm_authenticate` error-code semantics :271-273; nvmem naming :275-277).
- `Documentation/admin-guide/thunderbolt.rst:279-306` — "Upgrading on-board retimer NVM when there is no cable connected": `offline` write (:287), `rescan` write (:293), the **5-second wait after `nvm_authenticate` before re-running rescan** (:298-301), and the return to online (:306).
- `Documentation/ABI/testing/sysfs-bus-thunderbolt:306-311` — `usb4_portX/link` (v5.14).
- `.../sysfs-bus-thunderbolt:313-326` — `usb4_portX/offline` (v5.14), including the note that the attribute is visible only if the platform can power retimers with no cable.
- `.../sysfs-bus-thunderbolt:328-337` — `usb4_portX/rescan` (v5.14).
- `.../sysfs-bus-thunderbolt:339-343` — retimer `device` (v5.9); `:345-358` — retimer `nvm_authenticate` (v5.9); `:360-364` — retimer `nvm_version` (v5.9); `:366-370` — retimer `vendor` (v5.9).
- `.../sysfs-bus-thunderbolt:224` — mentions NVM upgrade support "with USB4 devices and retimers".
- Kerneldoc blocks in-tree for this area (**none are pulled into `Documentation/`** — verified: no `drivers/thunderbolt` reference anywhere under `Documentation/`, and no `Documentation/driver-api` page exists for thunderbolt/USB4): `struct usb4_port` tb.h:307-315; `struct tb_retimer` tb.h:326-338; `enum usb4_sb_target` tb.h:1371-1376; `enum usb4_margin_sw_error_counter` tb.h:1388-1394; `struct usb4_port_margining_params` tb.h:1409-1420; `struct tb_margining` debugfs.c:457-488; and full function kerneldoc on every non-static helper in usb4.c (e.g. `usb4_port_sb_read` :1346-1358, `usb4_port_retimer_is_last` :1901-1912, `usb4_port_margining_caps` :1699-1710, `usb4_dp_port_requested_bandwidth` :3083-3097, `usb4_pci_port_ltssm_state` :3154-3161), switch.c (:1320-1325, :1346-1351, :1363-1369, :1381-1386, :1398-1404, :1414-1421, :1435-1442, :1458-1470, :1499-1504, :1516-1525), retimer.c (:23-33, :498-509, :586-591), usb4_port.c (:108-117, :295-302, :343-348, :355-362), acpi.c (:249-262, :268-276) and debugfs.c (:2412-2417, :2490-2495, :2527-2532, :2543-2548).

### Area E: Host interface and control channel — COMPLETE (recorded 2026-09-04)

Confirmed `git describe --tags` = **v7.2**. All locations verified on disk with `sed -n`.

#### 1. CORE STRUCTS

##### `struct tb_nhi` — include/linux/thunderbolt.h:518 (kerneldoc :500)
| Field | Line | Role / writer / reader |
|---|---|---|
| `spinlock_t lock` | :519 | Serializes ring create/destroy + interrupt dispatch. Init `nhi.c:1217`; held by `nhi_alloc_hop`, `tb_ring_start/stop/free`, `ring_msix`, `nhi_interrupt_work`, `tb_ring_poll_complete` |
| `struct device *dev` | :520 | Generic device (was `struct pci_dev *pdev` at v7.0). Written `pci.c:466`; read everywhere (dev_dbg, DMA, dma_pool) |
| `const struct tb_nhi_ops *ops` | :521 | Per-controller hooks. Written `pci.c:467`; **must be non-NULL** since v7.2 (`nhi.c:1192`) |
| `void __iomem *iobase` | :522 | BAR0 MMIO. Written `pci.c:469` (`pcim_iomap_region(pdev,0,"thunderbolt")`); read by every register accessor |
| `struct tb_ring **tx_rings` | :523 | hop_count-sized array. Alloc `nhi.c:1201` (devm_kcalloc); written `nhi.c:520`, `nhi.c:806`; read `nhi.c:950`, `1119` |
| `struct tb_ring **rx_rings` | :524 | Same, RX. Alloc `nhi.c:1203`; written `nhi.c:522`, `808`; read `nhi.c:952`, `1122` |
| `bool going_away` | :525 | Controller vanished. Set `nhi.c:1047` (`nhi_resume_noirq`); read `nhi.c:649` (`tb_ring_start`), `757` (`tb_ring_stop`), `icm.c:2137` |
| `bool iommu_dma_protection` | :526 | IOMMU isolates external ports. Written `pci.c:106`; read `domain.c:259` (sysfs) |
| `struct work_struct interrupt_work` | :527 | Single-MSI fallback bottom half. INIT_WORK `pci.c:133`; queued `nhi.c:971`; flushed `pci.c:244` |
| `u32 hop_count` | :528 | Rings supported. Written `nhi.c:1198` (`REG_CAPS & 0x3ff`); read by every index/mask helper |
| `unsigned long quirks` | :529 | `QUIRK_AUTO_CLEAR_INT`/`QUIRK_E2E`. Written `pci.c:52`, `pci.c:62`; read `nhi.c:53,65,107,433,463` |
| `struct completion domain_released` | :530 | **New at v7.2.** init `nhi.c:1229`; completed `domain.c:330` (`tb_domain_release`); waited `nhi.c:1245`, `pci.c:492` |

##### `struct tb_nhi_pci` — drivers/thunderbolt/pci.c:31 (kerneldoc :26) — **new at v7.2**
- `struct tb_nhi nhi` (:32) — embedded generic NHI; first member.
- `struct ida msix_ida` (:33) — MSI-X vector allocator; `ida_init` `pci.c:118`, `ida_alloc_max` `pci.c:195`, `ida_free` `pci.c:215,228`, `ida_destroy` `pci.c:246`.
- `nhi_to_pci()` — pci.c:36 (S, inline) — `container_of(nhi, struct tb_nhi_pci, nhi)`. The `struct pci_dev` is recovered by `to_pci_dev(nhi->dev)`, never stored.

##### `struct tb_nhi_ops` — drivers/thunderbolt/nhi.h:56 (kerneldoc :41)
| Callback | Line | Role / caller |
|---|---|---|
| `init` | :57 | NHI-specific init; `nhi.c:1223` |
| `suspend_noirq(nhi, wakeup)` | :58 | `nhi.c:985` |
| `resume_noirq` | :59 | `nhi.c:1048` |
| `runtime_suspend` | :60 | `nhi.c:1089` |
| `runtime_resume` | :61 | `nhi.c:1103` |
| `shutdown` | :62 | `nhi.c:1128` |
| `pre_nvm_auth` | :63 | **new v7.2**; `switch.c:254` (TB3 host-router NVM auth; NOT ICM-only — `sw->dma_port` is allocated only when `!tb_route(sw) && !tb_switch_is_icm(sw)`, switch.c:2769-2772, i.e. software-CM host router) |
| `post_nvm_auth` | :64 | **new v7.2**; `switch.c:2785`, `2802` |
| `request_ring_irq(ring, no_suspend)` | :65 | **new v7.2**; `nhi.c:571-572` |
| `release_ring_irq(ring)` | :66 | **new v7.2**; `nhi.c:582`, `816` |
| `is_present` | :67 | **new v7.2**; `nhi.c:1046` |
| `init_interrupts` | :68 | **new v7.2**, mandatory; `nhi.c:1195`, `1213` |

Instances at v7.2 — both in pci.c, both bus-specific:
- `pci_nhi_default_ops` — pci.c:254 (generic PCI; `.init_interrupts=nhi_pci_init_msi`, `.request/release_ring_irq`, `.shutdown`, `.is_present`, `.pre/post_nvm_auth`).
- `icl_nhi_ops` — pci.c:432 — **VENDOR-ONLY** (Intel Ice Lake and later; adds `.init/.suspend_noirq/.resume_noirq/.runtime_*`/`.shutdown` built on VS_CAP_* config-space registers).
- Selection mechanism: `nhi->ops = (const struct tb_nhi_ops *)id->driver_data ?: &pci_nhi_default_ops;` — pci.c:467.

##### `struct tb_ring` — include/linux/thunderbolt.h:563 (kerneldoc :533)
`lock` :564 (spinlock, taken after nhi->lock) · `nhi` :565 · `size` :566 (descriptors) · `hop` :567 (DMA channel/HopID) · `head` :568 (write index) · `tail` :569 (complete index) · `descriptors` :570 (`struct ring_desc *`, coherent) · `descriptors_dma` :571 · `queue` :572 (pending frames) · `in_flight` :573 (posted frames) · `work` :574 (`ring_work`) · `is_tx:1` :575 · `running:1` :576 · `irq` :577 (MSI-X irq, 0 = none) · `vector` :578 (u8 MSI-X vector) · `flags` :579 (`RING_FLAG_*`) · `e2e_tx_hop` :580 (RX only) · `sof_mask` :581 (u16) · `eof_mask` :582 (u16) · `start_poll` :583 (poll-mode cb) · `poll_data` :584 · `interval_nsec` :585 (**new v7.2**, throttling) · `wait` :586 (**new v7.2**, waitqueue for `tb_ring_flush`).

##### `struct ring_desc` — drivers/thunderbolt/nhi_regs.h:34 (kerneldoc :22), `__packed`, 16 bytes
`u64 phys` :35 (DMA address of the frame buffer) · `u32 length:12` :36 · `u32 eof:4` :37 · `u32 sof:4` :38 · `enum ring_desc_flags flags:12` :39 · `u32 time` :40 (write zero). **TX**: driver sets length/eof/sof (`nhi.c:247-249`). **RX**: NHI writes back length/eof/sof/flags, driver reads them in `ring_work` (`nhi.c:294-297`) and `tb_ring_poll` (`nhi.c:365-368`).

##### `struct ring_frame` — include/linux/thunderbolt.h:627 (kerneldoc :617)
`dma_addr_t buffer_phy` :628 (caller-mapped) · `ring_cb callback` :629 (typedef :597, `(ring, frame, canceled)`) · `struct list_head list` :630 · `u32 size:12` :631 (0 ⇒ 4096) · `u32 flags:12` :632 (`RING_DESC_*` on RX) · `u32 eof:4` :633 · `u32 sof:4` :634.

##### `struct tb_ctl` — drivers/thunderbolt/ctl.c:39 (kerneldoc :24) — opaque to the rest of the driver (fwd-declared ctl.h:19)
`nhi` :40 · `tx` :41 (TX ring 0) · `rx` :42 (RX ring 0) · `frame_pool` :44 (`dma_pool`, TB_FRAME_SIZE, align 4) · `rx_packets[TB_CTL_RX_PKG_COUNT]` :45 · `request_queue_lock` :46 (mutex) · `request_queue` :47 · `running` :48 · `timeout_msec` :50 · `callback` :51 (`event_cb`) · `callback_data` :52 · `index` :54 (domain number, emitted in trace records).

##### `struct tb_cfg_request` — drivers/thunderbolt/ctl.h:77 (kerneldoc :52)
`kref` :78 · `ctl` :79 (set only while queued) · `request` :80 / `request_size` :81 / `request_type` :82 · `response` :84 / `response_size` :85 / `response_type` :86 · `npackets` :86… (`size_t npackets` :86) · `match()` :87 · `copy()` :89 · `callback()` :90 / `callback_data` :91 · `flags` :92 (`TB_CFG_REQUEST_ACTIVE`=0 ctl.h:98, `TB_CFG_REQUEST_CANCELED`=1 ctl.h:99) · `work` :93 · `result` :94 · `list` :95.
Companions: `struct tb_cfg_result` ctl.h:32 (`response_route`, `response_port`, `err` (−errno / 0 / 1), `tb_error`); `struct ctl_pkg` ctl.h:46 (`ctl`, `buffer`, `frame`).

##### Packet formats — drivers/thunderbolt/tb_msgs.h
- `enum tb_cfg_space` :15 — `TB_CFG_HOPS=0`, `TB_CFG_PORT=1`, `TB_CFG_SWITCH=2`, `TB_CFG_COUNTERS=3`.
- `enum tb_cfg_error` :22 — `PORT_NOT_CONNECTED=0`, `LINK_ERROR=1`, `INVALID_CONFIG_SPACE=2`, `NO_SUCH_PORT=4`, `ACK_PLUG_EVENT=7`, `LOOP=8`, `HEC_ERROR_DETECTED=12`, `FLOW_CONTROL_ERROR=13`, `LOCK=15`, `DP_BW=32`, `ROP_CMPLT=33`, `POP_CMPLT=34`, `PCIE_WAKE=35`, `DP_CON_CHANGE=36`, `DPTX_DISCOVERY=37`, `LINK_RECOVERY=38`, `ASYM_LINK=39`.
- `struct tb_cfg_header` :43 `__packed` — `route_hi:22` :44, `unknown:10` :45 (must be `1<<9`; top bit set on replies), `route_lo` :46.
- `struct tb_cfg_address` :50 `__packed` — `offset:13` :51 (dwords), `length:6` :52 (dwords), `port:6` :53, `enum tb_cfg_space space:2` :54, `seq:2` :55 (sequence/retry counter), `zero:3` :56.
- `struct cfg_read_pkg` :60 — `header`, `addr` (also the *response* to a write).
- `struct cfg_write_pkg` :66 — `header`, `addr`, `u32 data[64]` :69 (max because `addr.length` is 6 bits) (also the response to a read).
- `struct cfg_error_pkg` :73 — `header`, `enum tb_cfg_error error:8` :75, `port:6` :76, `reserved:16` :77, `pg:2` :78; `TB_CFG_ERROR_PG_HOT_PLUG 0x2` :85, `TB_CFG_ERROR_PG_HOT_UNPLUG 0x3` :86.
- `struct cfg_ack_pkg` :81 — `header` only (not `__packed`).
- `struct cfg_event_pkg` :89 — `header`, `port:6` :91, `zero:25` :92, `bool unplug:1` :93.
- `struct cfg_reset_pkg` :97 — `header` only.
- `enum tb_cfg_pkg_type` — include/linux/thunderbolt.h:31 — `READ=1, WRITE=2, ERROR=3, NOTIFY_ACK=4, EVENT=5, XDOMAIN_REQ=6, XDOMAIN_RESP=7, OVERRIDE=8, RESET=9, ICM_EVENT=10, ICM_CMD=11, ICM_RESP=12` (last three ICM-only).

#### 2. API FAMILIES  (S = static, E = EXPORT_SYMBOL_GPL)

**PCI driver (pci.c)** — everything here is bus-specific
- `nhi_pci_probe` :447 (S) — `pcim_enable_device`, devm_kzalloc of `tb_nhi_pci`, sets `dev`/`ops`, `pcim_iomap_region(pdev,0)` = BAR0, quirks, IOMMU check, `pci_set_master`, then `nhi_probe()`.
- `nhi_pci_remove` :482 (S) — also used as `.shutdown`; runtime PM sync, `tb_domain_remove`, `wait_for_completion(&nhi->domain_released)`, `nhi_shutdown`.
- `nhi_pci_init_msi` :111 (S) — `.init_interrupts`; `ida_init`, MSI-X `pci_alloc_irq_vectors(pdev, MSIX_MIN_VECS, MSIX_MAX_VECS, PCI_IRQ_MSIX)`; on failure single `PCI_IRQ_MSI` + `INIT_WORK(interrupt_work, nhi_interrupt_work)` + `devm_request_irq(irq, nhi_msi, IRQF_NO_SUSPEND, "thunderbolt", nhi)`.
- `nhi_pci_ring_request_msix` :184 (S) — no-op unless `pdev->msix_enabled`; `ida_alloc_max(msix_ida, MSIX_MAX_VECS-1)` → `ring->vector`, `pci_irq_vector` → `ring->irq`, `request_irq(ring_msix, no_suspend?IRQF_NO_SUSPEND:0)`.
- `nhi_pci_ring_release_msix` :220 (S) — `free_irq` + `ida_free`, zeroes `vector`/`irq`.
- `nhi_pci_check_quirks` :41 (S) — MECHANISM: vendor/device switch setting `nhi->quirks`; **vendor-only branches** (`PCI_VENDOR_ID_INTEL` ⇒ `QUIRK_AUTO_CLEAR_INT`; Falcon Ridge 2C/4C ⇒ `QUIRK_E2E`).
- `nhi_pci_check_iommu` :77 (S) + `nhi_pci_check_iommu_pdev` :68 (S) — walk to root bus, `pci_walk_bus`, look for any `external_facing` device whose IOMMU is `IOMMU_CAP_PRE_BOOT_PROTECTION`-capable; sets `nhi->iommu_dma_protection`.
- `nhi_pci_imr_valid` :148 (S) — `device_property_read_u8(dev, "IMR_VALID")`, defaults true.
- `nhi_pci_is_present` :249 (S) — `pci_device_is_present`.
- `nhi_pci_shutdown` :233 (S) — frees the single-MSI irq before `flush_work(interrupt_work)`, then `ida_destroy(msix_ida)`.
- `nhi_pci_start_dma_port` :158 / `nhi_pci_complete_dma_port` :174 (S) — `pcie_find_root_port` + `pm_runtime_get_noresume`/`pm_runtime_put`, keeping the root port in D0 across TB3 host NVM auth.
- ICL block (**VENDOR-ONLY**, all S): `check_for_device` :268, `icl_nhi_is_device_connected` :273, `icl_nhi_force_power` :283, `icl_nhi_lc_mailbox_cmd` :328, `icl_nhi_lc_mailbox_cmd_complete` :337, `icl_nhi_set_ltr` :362, `icl_nhi_suspend` :374, `icl_nhi_suspend_noirq` :397, `icl_nhi_resume` :413, `icl_nhi_shutdown` :425. Only PCI config-space accesses in the driver live here: `VS_CAP_9/15/16/18/19/22` (nhi_regs.h:146-166).
- Table shape: `static struct pci_device_id nhi_ids[]` :496 — four legacy entries pin `.class = PCI_CLASS_SYSTEM_OTHER<<8, .class_mask=~0` plus subvendor/subdevice `0x2222/0x1111`; the rest are `PCI_VDEVICE(INTEL, …)` with optional `.driver_data = (kernel_ulong_t)&icl_nhi_ops`; final generic catch-all `{ PCI_DEVICE_CLASS(PCI_CLASS_SERIAL_USB_USB4, ~0) }` :582 (`PCI_CLASS_SERIAL_USB_USB4 0x0c0340`, nhi.h:119). `MODULE_DEVICE_TABLE` :587.
- `struct pci_driver nhi_driver` :591 (`.driver.pm = &nhi_pm_ops`); `nhi_init` :600 (`rootfs_initcall` :621), `nhi_unload` :615.

**NHI generic (nhi.c)**
- `nhi_probe(struct tb_nhi *)` :1186 (global, nhi.h:37) — validates `ops`/`ops->init_interrupts`, reads hop_count, allocs ring arrays, `nhi_reset`, `nhi_disable_interrupts`, `ops->init_interrupts`, `spin_lock_init`, `dma_set_mask_and_coherent(dev, DMA_BIT_MASK(64))`, `ops->init`, `init_completion(domain_released)`, `nhi_select_cm`, `tb_domain_add`, `dev_set_drvdata`, runtime-PM enable.
- `nhi_shutdown(struct tb_nhi *)` :1112 (global) — warns on live rings, `nhi_disable_interrupts`, `ops->shutdown`.
- `nhi_select_cm` :1163 (S) — `tb_acpi_is_native()` (**CONFIG_ACPI**; stub returns true, tb.h:1513/1526) ⇒ `tb_probe()` (software CM); else `icm_probe()` then fall back to `tb_probe()`.
- `nhi_reset` :1132 (S) — only for `REG_CAPS` version ≥ `REG_CAPS_VERSION_2`; writes `REG_RESET_HRR`, gated by module param.
- `nhi_disable_interrupts` :157 (global) — mask all + clear all status.
- `nhi_wake_supported` :1013 (S) — `device_property_read_u8(dev,"WAKE_SUPPORTED")`.
- PM (all S, wired into `nhi_pm_ops` :1266): `__nhi_suspend_noirq` :975, `nhi_suspend_noirq` :994, `nhi_freeze_noirq` :999, `nhi_thaw_noirq` :1006, `nhi_poweroff_noirq` :1027, `nhi_resume_noirq` :1035, `nhi_suspend` :1057, `nhi_complete` :1064, `nhi_runtime_suspend` :1079, `nhi_runtime_resume` :1097. Table members: `.suspend_noirq .resume_noirq .freeze_noirq .thaw_noirq .restore_noirq .suspend .poweroff_noirq .poweroff .complete .runtime_suspend .runtime_resume` (:1267-1280). Not `#ifdef CONFIG_PM`-gated — the file has **no preprocessor conditionals at all**.
- ICM-only, one line each (software CM never reaches them; sole callers are icm.c): `nhi_mailbox_cmd` nhi.c:870, `nhi_mailbox_mode` nhi.c:907, `enum nhi_fw_mode` nhi.h:14, `enum nhi_mailbox_cmd` nhi.h:21, `REG_INMAIL_*` nhi_regs.h:125-130, `REG_OUTMAIL_*` :132-134, `REG_FW_STS*` :136-141, `NHI_MAILBOX_TIMEOUT` nhi.c:37.

**Ring (nhi.c + thunderbolt.h)**
- Register accessors (S): `ring_desc_base` :171 (`REG_TX/RX_RING_BASE + hop*16`), `ring_options_base` :179 (`REG_TX/RX_OPTIONS_BASE + hop*32`), `ring_iowrite_cons` :187, `ring_iowrite_prod` :197, `ring_iowrite32desc` :203, `ring_iowrite64desc` :208, `ring_iowrite32options` :214.
- State (S): `ring_full` :219, `ring_empty` :224, `tb_ring_empty` :712 (list-based, guard spinlock).
- `ring_write_descriptors` :234 (S) — moves queue→in_flight, fills `ring_desc`, bumps prod/cons.
- `ring_work` :268 (S) — workqueue completion handler.
- `__tb_ring_enqueue` :320 (E :335) — under `ring->lock`; `-ESHUTDOWN` when stopped. Inline wrappers `tb_ring_rx` thunderbolt.h:682, `tb_ring_tx` :703 (each `WARN_ON` on direction).
- `tb_ring_alloc` :530 (S) — kzalloc, list/work/waitqueue init, `dma_alloc_coherent(nhi->dev, size*sizeof(struct ring_desc), &descriptors_dma, GFP_KERNEL|__GFP_ZERO)`, `ops->request_ring_irq`, `nhi_alloc_hop`.
- `nhi_alloc_hop` :458 (S) — auto-allocates hop in `[start_hop, hop_count)`; `QUIRK_E2E` bumps start_hop to 2 and forces `e2e_tx_hop = RING_E2E_RESERVED_HOPID`.
- `tb_ring_alloc_tx` :603 (E :608), `tb_ring_alloc_rx` :626 (E :634).
- `tb_ring_start` :642 (E :710), `tb_ring_flush` :728 (E :735, **new v7.2**), `tb_ring_stop` :751 (E :784), `tb_ring_free` :796 (E :838), `tb_ring_throttling` :850 (E :858, **new v7.2**).
- `tb_ring_poll` :348 (E :378), `tb_ring_poll_complete` :416 (E :427).
- Inline helpers: `tb_ring_frame_size` thunderbolt.h:641 (**new v7.2**; 0 ⇒ `TB_MAX_FRAME_SIZE`), `tb_ring_size` :648 (**new v7.2**), `tb_ring_dma_device` :724 (returns `ring->nhi->dev`).

**Interrupt (nhi.c)**
- `ring_interrupt_index` :43 (S) — `hop` for TX, `hop + hop_count` for RX.
- `nhi_mask_interrupt` :51 (S) — quirked: RMW `REG_RING_INTERRUPT_BASE` vs write `REG_RING_INTERRUPT_MASK_CLEAR_BASE`.
- `nhi_clear_interrupt` :63 (S) — quirked: read `REG_RING_NOTIFY_BASE` vs write `~0` to `REG_RING_INT_CLEAR`.
- `ring_interrupt_active` :76 (S) — programs `REG_DMA_MISC` auto-clear bit, the `REG_INT_VEC_ALLOC_BASE` nibble (`step = index/8*4`, `shift = index%8*4`, 4-bit vector per hop), the per-vector `REG_INT_THROTTLING_RATE + vector*4`, then the enable bit in `REG_RING_INTERRUPT_BASE`.
- `__ring_interrupt_mask` :380 (S), `__ring_interrupt` :396 (S — `start_poll` ⇒ mask+callback, else `schedule_work`), `ring_clear_msix` :429 (S).
- `ring_msix` :444 (global, hard IRQ), `nhi_msi` :968 (global, hard IRQ), `nhi_interrupt_work` :918 (global, work handler scanning the three `REG_RING_NOTIFY_BASE` bitfields TX/RX/RX-overflow).

**Control TX (ctl.c)**
- `tb_ctl_tx` :366 (S) — rejects `len % 4`, rejects `len > TB_FRAME_SIZE - 4`; allocates `ctl_pkg`, sets `frame.size = len+4`, `frame.sof = frame.eof = type` (the PDF carries the packet type), `trace_tb_tx`, `cpu_to_be32_array`, appends `tb_crc`, `tb_ring_tx(ctl->tx, …)`.
- `tb_ctl_tx_callback` :352 (S) — frees the pkg back to the pool.
- `tb_crc` :320 (S) — `cpu_to_be32(~crc32c(~0, data, len))`.
- `tb_ctl_pkg_alloc` :334 (S) / `tb_ctl_pkg_free` :325 (S) — `dma_pool_alloc/free` on `ctl->frame_pool`.
- Ring 0 = the control channel: `tb_ctl_alloc` allocates hop 0 TX and RX explicitly (ctl.c:674, :678); `tb_cfg_make_header(route)` (ctl.h:115) puts the route string in the packet, so the packet is addressed to a router while riding HopID 0 end-to-end.

**Control RX (ctl.c)**
- `tb_ctl_rx_callback` :445 (S) — drop on bad size; strip 4-byte CRC; per-type CRC verify; `tb_async_error` ⇒ `tb_ctl_handle_event`; `TB_CFG_PKG_EVENT`/`XDOMAIN_RESP`/`XDOMAIN_REQ`/`ICM_EVENT` ⇒ `tb_ctl_handle_event`; otherwise `tb_cfg_request_find` + `req->copy` + `schedule_work(&req->work)`; `trace_tb_rx(…, !req)` :512 records drops; always re-submits via `tb_ctl_rx_submit`.
- `tb_ctl_handle_event` :402 (S) — `trace_tb_event` then `ctl->callback` = `tb_domain_event_cb` (domain.c:338), which routes `XDOMAIN_REQ/RESP` to `tb_xdomain_handle_request` (xdomain.c:2620) and everything else to `tb->cm_ops->handle_event` (tb.h:522).
- `tb_ctl_rx_submit` :409 (S), `tb_async_error` :419 (S — the 11 asynchronous `TB_CFG_ERROR_*` codes).
- `check_header` :195 (S), `check_config_address` :223 (S), `decode_error` :245 (S), `parse_header` :263 (S), `tb_cfg_print_error` :278 (S), `tb_cfg_get_error` :1088 (S — maps tb_error to `-ENODEV`/`-EACCES`/`-ENOTCONN`/`-EIO`).

**Request (ctl.c / ctl.h)**
- `tb_cfg_request_alloc` :88, `_get` :105, `_put` :126, `tb_cfg_request_destroy` :112 (S).
- `tb_cfg_request_enqueue` :133 (S), `tb_cfg_request_dequeue` :151 (S), `tb_cfg_request_is_active` :168 (S), `tb_cfg_request_find` :173 (S).
- `tb_cfg_request_work` :524 (S), `tb_cfg_request` :547, `tb_cfg_request_cancel` :589, `tb_cfg_request_complete` :597 (S), `tb_cfg_request_sync` :616.
- `tb_cfg_match` :856 (S — masks bit 63 of route, compares eof/route/size and `addr.seq`), `tb_cfg_copy` :883 (S).
- Public commands: `tb_ctl_alloc` :653, `tb_ctl_free` :705, `tb_ctl_start` :730, `tb_ctl_stop` :751, `tb_cfg_ack_notification` :778, `tb_cfg_ack_plug` :842, `tb_cfg_reset` :911, `tb_cfg_read_raw` :956, `tb_cfg_write_raw` :1030, `tb_cfg_read` :1111, `tb_cfg_write` :1137, `tb_cfg_get_upstream_port` :1173. Prototypes ctl.h:101-142.

**Packet helpers** — `tb_cfg_get_route` ctl.h:110 (inline), `tb_cfg_make_header` ctl.h:115 (inline, `WARN_ON` on route overflow since route_hi is 22 bits).

**Seams into other areas (tb.h)** — `tb_sw_read` :672, `tb_sw_write` :686, `tb_port_read` :700, `tb_port_write` :714 (each short-circuits `-ENODEV` on `is_unplugged`, then calls `tb_cfg_read/write(sw->tb->ctl, …)`); `cm_ops->handle_event` :522; `tb_xdomain_handle_request` :1260.

**Trace (trace.h)** — `show_data_read_write` :39, `show_data_error` :52, `show_data_event` :63, `show_route` :73, `show_data` :83 (all `static inline`, guarded by `TB_TRACE_HELPERS` :37); `show_type_name`/`tb_cfg_type_name` :21-35.

#### 3. LIFECYCLE AND LOCKING

- **NHI**: `nhi_pci_probe` (pci.c:447) → devm-allocated `tb_nhi_pci` → `nhi_probe` (nhi.c:1186) → `nhi_select_cm` → `tb_domain_add`. Teardown `nhi_pci_remove` (pci.c:482) → `tb_domain_remove` → `wait_for_completion(&nhi->domain_released)` (pci.c:492) → `nhi_shutdown` (nhi.c:1112) → `ops->shutdown` = `nhi_pci_shutdown` (pci.c:233). Error path in probe mirrors this at nhi.c:1244-1246.
- **Ring**: `tb_ring_alloc_tx/rx` → `tb_ring_alloc` (nhi.c:530) → `tb_ring_start` (:642, sets `running=true` :705) → `tb_ring_stop` (:751, clears `running` :772, then `schedule_work`+`flush_work` :781-782 so canceled callbacks run) → `tb_ring_free` (:796, unhooks from `nhi->tx_rings/rx_rings`, `ops->release_ring_irq`, `dma_free_coherent`, `flush_work`, `kfree`). `tb_ring_flush` (:728) waits on `ring->wait` for `in_flight` to drain before stopping.
- **Locks**: `nhi->lock` (spinlock, thunderbolt.h:519) — protects ring create/destroy and the ring arrays; held across interrupt dispatch. `ring->lock` (thunderbolt.h:564) — protects `head/tail/queue/in_flight/running/interval_nsec`; **must be taken after `nhi->lock`** (nesting shown at nhi.c:420-425, 647-648, 753-754, 800). `ctl->request_queue_lock` (mutex, ctl.c:46) — protects `request_queue` and `ctl->running`. `tb_cfg_request_lock` (static mutex, ctl.c:78) — serializes every `kref_get/put` on requests. `tb_cfg_request_cancel_queue` (static waitqueue, ctl.c:76).
- **Refcounting**: `tb_cfg_request_alloc` `kref_init` (ctl.c:96); pairs — `tb_cfg_request` gets (:558) / `tb_cfg_request_work` puts (:532); `tb_cfg_request_find` gets each iterated entry (:180) and puts non-matches (:185), caller puts at :517; the API callers put after `tb_cfg_request_sync` (:935, :995, :1071). Final put runs `tb_cfg_request_destroy` → `kfree` (ctl.c:112-117).
- **State transitions**: `ring->running` false→true at nhi.c:705, true→false at :772; guarded by `nhi->going_away` (:649, :757) so a vanished controller is never touched. `TB_CFG_REQUEST_ACTIVE` set at ctl.c:146, cleared at :162; `TB_CFG_REQUEST_CANCELED` set at :591, tested at :163, :528. `ctl->running` set at ctl.c:739, cleared at :754 under the queue mutex.

#### 4. HARD-CODED LIMITS

| Constant | Value | Location |
|---|---|---|
| `RING_FIRST_USABLE_HOPID` | 1 | nhi.c:30 |
| `RING_E2E_RESERVED_HOPID` | = 1 | nhi.c:35 |
| `NHI_MAILBOX_TIMEOUT` | 500 ms | nhi.c:37 (ICM-only path) |
| hop_count mask | `& 0x3ff` (bare literal, 1024 max) | nhi.c:1198 |
| DMA mask | `DMA_BIT_MASK(64)` | nhi.c:1219 |
| host-router reset settle | `msleep(100)` then 500 ms poll, `usleep_range(10,20)` | nhi.c:1148, :1150, :1157 |
| throttling granularity | 256 ns per unit; `REG_INT_THROTTLING_RATE_INTERVAL_MASK` GENMASK(15,0) | nhi.c:125-126, nhi_regs.h:105 |
| `MSIX_MIN_VECS` / `MSIX_MAX_VECS` | 6 / 16 | nhi.h:129, :130 |
| `REG_INT_VEC_ALLOC_BITS` / `_MASK` / `_REGS` | 4 / GENMASK(3,0) / 8 | nhi_regs.h:109-111 |
| `REG_CAPS_VERSION_MASK` / `_VERSION_2` | GENMASK(23,16) / 0x40 | nhi_regs.h:115, :116 |
| `TB_FRAME_SIZE` / `TB_MAX_FRAME_SIZE` | 256 / 4096 | thunderbolt.h:638, :639 |
| control TX payload cap | `TB_FRAME_SIZE - 4` (252 B; 4 B CRC) | ctl.c:375-377 |
| `TB_CTL_RX_PKG_COUNT` | 10 | ctl.c:21 |
| `TB_CTL_RETRIES` | 4 | ctl.c:22 |
| ctl ring size / masks | `10` descriptors each; sof/eof masks `0xffff`/`0xffff` (bare literals) | ctl.c:674, :678-679 |
| ctl dma_pool | size `TB_FRAME_SIZE`, align 4, boundary 0 | ctl.c:669-670 |
| retry backoff | `usleep_range(10, 100)` | ctl.c:1001, :1077 |
| cfg read/write response size | `12 + 4*length` (bare literal 12 = header+addr) | ctl.c:990, :1063 |
| `cfg_write_pkg.data[]` | 64 dwords | tb_msgs.h:69 |
| `ICL_LC_MAILBOX_TIMEOUT` | 500 ms (vendor) | pci.c:266 |
| ICL force-power poll | 350 retries × `usleep_range(3000,3100)` (vendor) | pci.c:311, :319 |
| ICL mailbox poll | `usleep_range(1000,1100)` (vendor) | pci.c:351 |
| `TB_AUTOSUSPEND_DELAY` | 15000 ms | tb.h:550 (used nhi.c:1254) |
| software-CM ctl timeout | `TB_TIMEOUT` 100 ms → `ctl->timeout_msec` | tb.c:19, passed via `tb_domain_alloc` tb.c:3379 → domain.c:404 |
| stream flush timeout | 500 ms | stream.c:613, :615 |
| consumer throttling | 128000 ns (`TBNET_THROTTLING` net/thunderbolt/main.c:37; dma_test.c:158,:186) | — |
| consumer ring sizes | `TBNET_RING_SIZE` 256; `DMA_TEST_TX_RING_SIZE` 64 / `_RX_` 256 | net/thunderbolt/main.c:34; dma_test.c:16-17 |

Register map (nhi_regs.h): `REG_TX_RING_BASE 0x00000` :52 (16 B/hop) · `REG_RX_RING_BASE 0x08000` :62 (16 B/hop, +0x14 max frame size) · `REG_TX_OPTIONS_BASE 0x19800` :70 (32 B/hop) · `REG_RX_OPTIONS_BASE 0x29800` :80 with `REG_RX_OPTIONS_E2E_HOP_MASK GENMASK(22,12)` :81 / `_SHIFT 12` :82 (note: the prose comment at :75-76 says "bits 13-23", one-off vs. the macro) · `REG_RING_NOTIFY_BASE 0x37800` :90, `RING_NOTIFY_REG_COUNT(nhi) = (31 + 3*hop_count)/32` :91, `REG_RING_INT_CLEAR 0x37808` :92 · `REG_RING_INTERRUPT_BASE 0x38200` :99, `RING_INTERRUPT_REG_COUNT(nhi) = (31 + 2*hop_count)/32` :100, `REG_RING_INTERRUPT_MASK_CLEAR_BASE 0x38208` :102 · `REG_INT_THROTTLING_RATE 0x38c00` :104 · `REG_INT_VEC_ALLOC_BASE 0x38c40` :108 · `REG_CAPS 0x39640` :114 · `REG_DMA_MISC 0x39864` :118 with `REG_DMA_MISC_INT_AUTO_CLEAR BIT(2)` :119 / `REG_DMA_MISC_DISABLE_AUTO_CLEAR BIT(17)` :120 · `REG_RESET 0x39898` / `REG_RESET_HRR BIT(0)` :122-123.
Ring option bits — `enum ring_flags` nhi_regs.h:14: `RING_FLAG_ISOCH_ENABLE 1<<27`, `RING_FLAG_E2E_FLOW_CONTROL 1<<28`, `RING_FLAG_PCI_NO_SNOOP 1<<29`, `RING_FLAG_RAW 1<<30`, `RING_FLAG_ENABLE 1<<31`.
Software ring flags — thunderbolt.h: `RING_FLAG_NO_SUSPEND BIT(0)` :590 (⇒ `IRQF_NO_SUSPEND`, pci.c:207), `RING_FLAG_FRAME BIT(1)` :592 (⇒ frame_size 0/4096, no `RING_FLAG_RAW`), `RING_FLAG_E2E BIT(2)` :594 (⇒ `RING_FLAG_E2E_FLOW_CONTROL` + hop field, nhi.c:684-701).
Descriptor flags — `enum ring_desc_flags` thunderbolt.h:608: `RING_DESC_ISOCH 0x1` / `RING_DESC_CRC_ERROR 0x1` (same bit, TX vs RX meaning), `RING_DESC_COMPLETED 0x2`, `RING_DESC_POSTED 0x4`, `RING_DESC_BUFFER_OVERRUN 0x04`, `RING_DESC_INTERRUPT 0x8`. Driver always posts `RING_DESC_POSTED | RING_DESC_INTERRUPT` (nhi.c:245).
`tb_ring_start` raw-vs-frame programming: frame mode ⇒ `frame_size = 0` (means 4096) and `flags = RING_FLAG_ENABLE`; raw mode ⇒ `frame_size = TB_FRAME_SIZE` and `flags = RING_FLAG_ENABLE | RING_FLAG_RAW` (nhi.c:658-665); RX writes `(frame_size<<16)|size` at desc+12 and `sof_mask<<16 | eof_mask` at options+4 (nhi.c:673-677); TX writes `size` at desc+12 and 0 at options+4 (:669-670).
DMA ownership: the descriptor array is `dma_alloc_coherent` by the ring (nhi.c:565-567, freed :585 / :819); **frame data buffers are mapped by the caller** — ctl.c uses `dma_pool_alloc` (ctl.c:340), net/dma_test/stream use `dma_map_single` against `tb_ring_dma_device(ring)`. Raw vs frame mode changes only the register programming, not who maps.

#### 5. VERSION-SPECIFIC FACTS (v7.2 vs widely-documented older kernels)

- `struct tb_nhi.pdev` (`struct pci_dev *`) → `struct tb_nhi.dev` (`struct device *`). Every `&nhi->pdev->dev` becomes `nhi->dev`.
- `struct tb_nhi.msix_ida` removed from the public struct; now `struct tb_nhi_pci.msix_ida` (pci.c:33).
- `struct tb_nhi.domain_released` added (thunderbolt.h:530).
- `struct tb_ring.interval_nsec` and `.wait` added (thunderbolt.h:585, :586).
- `extern const struct tb_nhi_ops icl_nhi_ops;` removed from nhi.h; `icl_nhi_ops` is now file-static in pci.c:432.
- `TB_FRAME_SIZE` respelled `0x100` → `256`; `TB_MAX_FRAME_SIZE 4096` added.
- New exported API: `tb_ring_flush()`, `tb_ring_throttling()`; new inlines `tb_ring_frame_size()`, `tb_ring_size()`.
- `nhi_enable_int_throttling()` **deleted**; throttling is now per-ring inside `ring_interrupt_active()`. Its prototype survives as a dead declaration at **nhi.h:32** (no definition anywhere in the tree).
- `nhi->ops` may no longer be NULL; every `if (nhi->ops && …)` guard was dropped.
- Neither `TB_CFG_DEFAULT_TIMEOUT` nor `TB_CTL_RX_PKG_SIZE` exists at v7.2 (verified absent tree-wide). The per-domain default is `ctl->timeout_msec`, set from `tb_domain_alloc(nhi, timeout_msec, …)` — software CM passes `TB_TIMEOUT` = 100 ms (tb.c:19, tb.c:3379).
- The "Increase Notification Timeout to 255 ms for USB4 routers" change (e24f3c0df483) is **not in this area**: the value is programmed at **switch.c:2620** (`sw->config.plug_events_delay = 0xff` in `tb_switch_configure`), and the write width grew from 3 to 4 dwords at `ROUTER_CS_1`. `tb_plug_events_active` no longer writes it, and the `plug_events_delay` comment in tb_regs.h:183 was corrected.

#### 6. SUGGESTED PAGE TOPICS (fine granularity)

1. **`struct tb_nhi` — the generic host-interface object** — every field, `dev`/`ops`/`iobase`/`hop_count`/`quirks`/`going_away`/`domain_released`.
2. **The v7.2 bus split: nhi.c vs pci.c** — `nhi_probe`/`nhi_shutdown` vs `nhi_pci_probe`/`nhi_pci_remove`, `struct tb_nhi_pci`, `nhi_to_pci`.
3. **`struct tb_nhi_ops` — the controller-hook vtable** — 12 callbacks, mandatory `init_interrupts`, table selection via `id->driver_data`.
4. **PCI attach: BAR0, bus mastering, DMA mask** — `pcim_enable_device`, `pcim_iomap_region`, `pci_set_master`, `dma_set_mask_and_coherent(64)`.
5. **MSI-X vs single-MSI: `nhi_pci_init_msi` and the vector allocator** — `MSIX_MIN_VECS`/`MSIX_MAX_VECS`, `msix_ida`, `pci_irq_vector`, `nhi_msi` fallback.
6. **`REG_INT_VEC_ALLOC_BASE` encoding** — 4-bit vector per (TX hop | RX hop + hop_count) index, the step/shift arithmetic.
7. **Interrupt masking and the auto-clear quirk** — `REG_RING_INTERRUPT_BASE`, `REG_RING_INT_CLEAR`, `REG_DMA_MISC_INT_AUTO_CLEAR` vs `_DISABLE_AUTO_CLEAR`.
8. **`nhi_interrupt_work`: the three notify bitfields** — TX / RX / RX-overflow scan, read-to-clear semantics.
9. **`struct tb_ring` and `struct ring_desc`: the descriptor ring** — head/tail, prod/cons registers, hardware write-back.
10. **Ring lifecycle: alloc → start → stop → free** — including the coherent descriptor allocation and `flush_work` ordering.
11. **Raw mode vs frame mode** — `RING_FLAG_RAW`, `RING_FLAG_FRAME`, frame_size 0/256/4096, sof/eof masks, PDF semantics.
12. **HopID allocation and the E2E quirk** — `nhi_alloc_hop`, `RING_FIRST_USABLE_HOPID`, `RING_E2E_RESERVED_HOPID`, `REG_RX_OPTIONS_E2E_HOP_*`.
13. **Polling mode: `start_poll`, `tb_ring_poll`, `tb_ring_poll_complete`** — masked-interrupt handoff to a service driver.
14. **Interrupt throttling (new at v7.2)** — `tb_ring_throttling`, `interval_nsec`, 256 ns granularity, consumers (tbnet, dma_test, stream).
15. **`tb_ring_flush` (new at v7.2)** — the `ring->wait` waitqueue and `tb_ring_empty`.
16. **The ring lock model** — `nhi->lock` vs `ring->lock`, ordering, IRQ context vs work context.
17. **DMA buffer ownership** — who maps what in raw vs frame mode; `tb_ring_dma_device`.
18. **IOMMU DMA protection detection** — `nhi_pci_check_iommu`, `external_facing`, `IOMMU_CAP_PRE_BOOT_PROTECTION`, the `iommu_dma_protection` sysfs attribute.
19. **`nhi_pci_check_quirks` as a mechanism** — how a quirk word is derived from vendor/device (flagging the vendor-only branches).
20. **The PCI ID table shape** — class-pinned legacy entries, `PCI_VDEVICE`, `driver_data` carrying an ops table, the generic USB4-class catch-all.
21. **Host router reset (`nhi_reset`) and the `host_reset` module parameter.**
22. **`struct tb_ctl`: ring 0 is the control channel** — why HopID 0, how `tb_ctl_alloc` wires TX/RX and the RX packet pool.
23. **Control TX: `tb_ctl_tx` and the CRC32C trailer** — big-endian conversion, PDF = packet type, size limits.
24. **Control RX: `tb_ctl_rx_callback` dispatch table** — checksum check, async-error path, event path, request matching, always-resubmit.
25. **`struct tb_cfg_request`: refcount, flags, and the request queue.**
26. **`tb_cfg_request_sync`: completion, timeout, cancel** — and how the retry loop above it works.
27. **Config read/write: `tb_cfg_read_raw`/`write_raw`, the seq field, `TB_CTL_RETRIES`.**
28. **Error decoding: `tb_cfg_result` → errno** — `tb_cfg_get_error`, `tb_cfg_print_error`, the async vs synchronous error split.
29. **Packet formats: header, address, and the cfg_*_pkg family** — every bit field.
30. **Notifications and acks: `tb_cfg_ack_notification`, `tb_cfg_ack_plug`, `TB_CFG_PKG_NOTIFY_ACK`.**
31. **The event seam: `event_cb` → `tb_domain_event_cb` → `cm_ops->handle_event` / `tb_xdomain_handle_request`.**
32. **Config-space wrappers as the seam to the rest of the driver** — `tb_sw_read/write`, `tb_port_read/write`.
33. **Tracing the control channel** — `tb_tx`/`tb_rx`/`tb_event`, the `tb_raw` event class, the pretty-printers.
34. *(not in the request's list)* **PM ops wiring: where `nhi_pm_ops` lives vs who registers it** — nhi.c table, pci.c `driver.pm`.
35. *(not in the request's list)* **Module init order: `rootfs_initcall(nhi_init)` and `tb_domain_init` ordering.**
36. *(not in the request's list)* **Domain-release synchronisation: `nhi->domain_released`** — why remove/probe-error must wait.
37. *(not in the request's list)* **`nhi_select_cm`: how the driver decides software CM vs ICM** (the boundary page that tells writers what is out of scope).

#### 7. TRACING INTEGRATION

- `CREATE_TRACE_POINTS` — **drivers/thunderbolt/ctl.c:18** (immediately before `#include "trace.h"` at :19). Only definition site in the subsystem.
- `DECLARE_EVENT_CLASS(tb_raw, …)` — trace.h:131 (`index, type, data, size`; `__dynamic_array(u32, data, size/4)`).
- `DEFINE_EVENT(tb_raw, tb_tx)` — trace.h:153. `DEFINE_EVENT(tb_raw, tb_event)` — trace.h:158.
- `TRACE_EVENT(tb_rx, …)` — trace.h:163 (adds `bool dropped`).
- Call sites (exhaustive, tree-wide): `trace_tb_tx` — ctl.c:388; `trace_tb_event` — ctl.c:405; `trace_tb_rx` — ctl.c:512.
- Trace system name `thunderbolt` (trace.h:11); `TRACE_INCLUDE_PATH .` / `TRACE_INCLUDE_FILE trace` (trace.h:191, :194).
- **Verified negative**: no `trace_printk` anywhere under drivers/thunderbolt.
- Gate: tracepoints compile away without `CONFIG_TRACEPOINTS`/`CONFIG_TRACING`; trace.h itself has no Kconfig symbol and no Makefile conditional.

#### 8. DEBUG AND DIAGNOSTIC PRINTING

- Macros in play: `RING_TYPE(ring)` — nhi.c:28 (prints "TX ring"/"RX ring"). Control-channel wrappers, all defined ctl.c:58-74 over `ctl->nhi->dev`: `tb_ctl_WARN` :58, `tb_ctl_err` :61, `tb_ctl_warn` :64, `tb_ctl_info` :67, `tb_ctl_dbg` :70, `tb_ctl_dbg_once` :73. Domain-level `tb_err`/`tb_WARN`/`tb_warn` at tb.h:728-730 (used by the event seam, not by this area's files).
- Counts — **nhi.c**: `dev_dbg` 12, `dev_warn` 8, `dev_WARN` 6, `dev_err_probe` 7, `WARN_ON_ONCE` 1.
- **pci.c**: `dev_dbg` 1, `dev_err_probe` 4. (No WARNs.)
- **ctl.c**: `tb_ctl_WARN` 7, `tb_ctl_dbg` 6, `tb_ctl_warn` 4, `tb_ctl_err` 4, `tb_ctl_dbg_once` 2, `tb_ctl_info` 1 (the macro definitions themselves account for one raw `dev_*` each); bare `WARN(...)` 11 (all in `check_header`/`check_config_address`/`tb_cfg_read`/`tb_cfg_write`), `WARN_ON` 3.
- Control knobs: `dev_dbg`/`dev_dbg_once` are the dynamic-debug surface (`CONFIG_DYNAMIC_DEBUG`, per-file/per-line via `/sys/kernel/debug/dynamic_debug/control`); `dev_WARN`/`WARN` obey `panic_on_warn`. Module parameter `host_reset` (nhi.c:39-41, `bool`, mode 0444) gates the host-router reset and its dbg/warn output. `nhi_probe` and `nhi_pci_probe` use `dev_err_probe` so probe failures are deferred-probe-aware.

#### 9. ASYNCHRONOUS / DEFERRED / LAZY PROCESSING

- **`ring->work` → `ring_work`** (handler nhi.c:268). INIT_WORK nhi.c:548. Queued from `__ring_interrupt` (nhi.c:405, hard-IRQ or work context, under `nhi->lock`+`ring->lock`) and from `tb_ring_stop` (nhi.c:781, process context). Flushed nhi.c:782 and nhi.c:835. Runs on `system_wq`; frame callbacks are invoked with **no lock held** (nhi.c:305-315) so they may re-enqueue.
- **`nhi->interrupt_work` → `nhi_interrupt_work`** (handler nhi.c:918). INIT_WORK pci.c:133 (single-MSI path only). Queued from `nhi_msi` (nhi.c:971, hard IRQ). Flushed pci.c:244 in `nhi_pci_shutdown`.
- **`req->work` → `tb_cfg_request_work`** (handler ctl.c:524). INIT_WORK ctl.c:555. Queued from `tb_ctl_rx_callback` (ctl.c:516, ring-work context), from `tb_cfg_request` for response-less requests (ctl.c:569), and from `tb_cfg_request_cancel` (ctl.c:592). Flushed ctl.c:634.
- **Hard IRQ handlers** (no threaded IRQs in this area — verified): `ring_msix` nhi.c:444, registered `request_irq` pci.c:208 (flags `IRQF_NO_SUSPEND` iff `RING_FLAG_NO_SUSPEND`); `nhi_msi` nhi.c:968, registered `devm_request_irq` pci.c:139 (always `IRQF_NO_SUSPEND`). Released `free_irq` pci.c:227 / `devm_free_irq` pci.c:243.
- **Completions**: `DECLARE_COMPLETION_ONSTACK(done)` ctl.c:622, signalled by `tb_cfg_request_complete` (ctl.c:597) via `req->callback`, waited by `wait_for_completion_timeout` ctl.c:631. `nhi->domain_released` — `init_completion` nhi.c:1229, `complete` domain.c:330, `wait_for_completion` nhi.c:1245 and pci.c:492.
- **Wait queues**: `ring->wait` — `init_waitqueue_head` nhi.c:549, `wake_up` nhi.c:317, `wait_event_timeout` nhi.c:730 (`tb_ring_flush`, caller-supplied ms). `tb_cfg_request_cancel_queue` — declared ctl.c:76, `wake_up` ctl.c:164, `wait_event` ctl.c:593.
- **Polling loops**: `nhi_mailbox_cmd` nhi.c:883-888 (500 ms deadline, `usleep_range(10,20)`) — ICM-only. `nhi_reset` nhi.c:1150-1158 (`msleep(100)` then 500 ms deadline, `usleep_range(10,20)`). `icl_nhi_force_power` pci.c:315-320 (350 × `usleep_range(3000,3100)` ≈ 1.05 s) — vendor. `icl_nhi_lc_mailbox_cmd_complete` pci.c:347-352 (caller timeout, `usleep_range(1000,1100)`) — vendor.
- **Retry backoff**: `usleep_range(10,100)` between config-request retries, ctl.c:1001 and ctl.c:1077.
- **Verified negatives**: no timers, no delayed work, no tasklets, no kthreads, no RCU callbacks in nhi.c / pci.c / ctl.c.

#### 10. SUBSYSTEM-SPECIFIC DEBUGGING INFRASTRUCTURE

- **sysfs**: `domainX/iommu_dma_protection` — `iommu_dma_protection_show` domain.c:253, `DEVICE_ATTR_RO` domain.c:261, in `domain_attrs[]` domain.c:279; reads `tb->nhi->iommu_dma_protection` written at pci.c:106. No Kconfig gate.
- **module parameter**: `host_reset` nhi.c:39-41 (`0444`, default true) — the only runtime knob owned by this area.
- **debugfs**: **verified negative** — drivers/thunderbolt/debugfs.c contains no NHI, ring, or control-channel entry (its only `nhi` mentions are `tb_port_is_nhi()` at debugfs.c:2278, :2284, i.e. the NHI *adapter port*, a different construct). Gates `CONFIG_USB4_DEBUGFS_WRITE` (Kconfig:25) and `CONFIG_USB4_DEBUGFS_MARGINING` (Kconfig:38) do not reach this area.
- **KUnit**: **verified negative** — drivers/thunderbolt/test.c (gate `CONFIG_USB4_KUNIT_TEST`, Kconfig:49; Makefile:11) exercises no ring and no control channel; its `nhi` variables (test.c:1792, 1808, 1835, 1872, 1910, …) are `struct tb_port *` NHI adapter ports used for DMA-tunnel path tests.
- **Related test/consumer drivers** (separate modules, exercise this area's exported ring API): `dma_test.c` (gate `CONFIG_USB4_DMA_TEST`, Kconfig:54, needs `DEBUG_FS`), `stream.c` (gate `CONFIG_USB4_STREAM`, Kconfig:67, needs `USB4_CONFIGFS`).

#### 11. v7.0 → v7.2 DRIFT (this area's paths)

`git log --oneline v7.0..v7.2` over the area's files (16 commits) and `git diff --stat`: ctl.c ±16, nhi.c −606-ish, nhi.h +33, **nhi_ops.c −185 (deleted)**, nhi_regs.h ±3, **pci.c +622 (new)**, thunderbolt.h +61.

**File-level moves**
- `drivers/thunderbolt/nhi_ops.c` **deleted** by `e241d98e04ef` ("Separate out common NHI bits") after `8c3ff7c5ae15` ("Move pci_device out of tb_nhi") rewrote its bodies. Its entire contents moved verbatim into **pci.c** as the Ice Lake block; Makefile line `thunderbolt-objs := nhi.o nhi_ops.o …` (v7.0 Makefile:4) is now `nhi.o ctl.o tb.o switch.o cap.o pci.o …` (Makefile:4).

**Functions moved nhi_ops.c (v7.0) → pci.c (v7.2)** — commit `e241d98e04ef`, all still `static`:
| old | new |
|---|---|
| nhi_ops.c:20 `check_for_device` | pci.c:268 |
| nhi_ops.c:25 `icl_nhi_is_device_connected` | pci.c:273 (`pci_get_drvdata(nhi->pdev)` → `dev_get_drvdata(nhi->dev)`) |
| nhi_ops.c:35 `icl_nhi_force_power` | pci.c:283 (gains local `to_pci_dev(nhi->dev)`) |
| nhi_ops.c:79 `icl_nhi_lc_mailbox_cmd` | pci.c:328 |
| nhi_ops.c:87 `icl_nhi_lc_mailbox_cmd_complete` | pci.c:337 |
| nhi_ops.c:111 `icl_nhi_set_ltr` | pci.c:362 |
| nhi_ops.c:122 `icl_nhi_suspend` | pci.c:374 |
| nhi_ops.c:145 `icl_nhi_suspend_noirq` | pci.c:397 |
| nhi_ops.c:161 `icl_nhi_resume` | pci.c:413 |
| nhi_ops.c:173 `icl_nhi_shutdown` | pci.c:425 (now calls `nhi_pci_shutdown` first) |
| `icl_nhi_ops` (extern, nhi.h:49 v7.0) | pci.c:432, now file-static |

**Functions moved+renamed nhi.c (v7.0) → pci.c (v7.2)** — commits `8c3ff7c5ae15`, `e241d98e04ef`:
| old | new |
|---|---|
| nhi.c:462 `ring_request_msix` | pci.c:184 `nhi_pci_ring_request_msix` |
| nhi.c:496 `ring_release_msix` | pci.c:220 `nhi_pci_ring_release_msix` |
| nhi.c:1169 `nhi_check_quirks` | pci.c:41 `nhi_pci_check_quirks` |
| nhi.c:1193 `nhi_check_iommu_pdev` | pci.c:68 `nhi_pci_check_iommu_pdev` |
| nhi.c:1202 `nhi_check_iommu` | pci.c:77 `nhi_pci_check_iommu` |
| nhi.c:1265 `nhi_init_msi` | pci.c:111 `nhi_pci_init_msi` |
| nhi.c:1306 `nhi_imr_valid` | pci.c:148 `nhi_pci_imr_valid` |
| nhi.c:1339 `nhi_probe(struct pci_dev *, const struct pci_device_id *)` | **split**: pci.c:447 `nhi_pci_probe` + nhi.c:1186 `nhi_probe(struct tb_nhi *)` |
| nhi.c:1426 `nhi_remove` | pci.c:482 `nhi_pci_remove` |
| nhi.c `nhi_ids[]` / `nhi_driver` / `nhi_init` / `nhi_unload` | pci.c:496 / :591 / :600 / :615 |
| switch.c:212 `nvm_authenticate_start_dma_port(struct tb_switch*)` | pci.c:158 `nhi_pci_start_dma_port(struct tb_nhi*)` — now a `tb_nhi_ops` hook |
| switch.c:227 `nvm_authenticate_complete_dma_port(struct tb_switch*)` | pci.c:174 `nhi_pci_complete_dma_port(struct tb_nhi*)` |

**Functions newly extracted at v7.2 (no v7.0 counterpart as a function)**
- `nhi_to_pci` pci.c:36; `nhi_pci_shutdown` pci.c:233 (was inline in v7.0 `nhi_shutdown`, nhi.c:1155-1163); `nhi_pci_is_present` pci.c:249 (was `pci_device_is_present(pdev)` inline in v7.0 `nhi_resume_noirq`, nhi.c:1066); `pci_nhi_default_ops` pci.c:254.

**Functions that stayed in nhi.c but changed linkage** (commit `e241d98e04ef`, static → global, declared nhi.h:32-39)
`nhi_disable_interrupts` v7.0 nhi.c:163 → v7.2 nhi.c:157 · `ring_msix` v7.0 :448 → :444 · `nhi_interrupt_work` v7.0 :915 → :918 · `nhi_msi` v7.0 :967 → :968 · `nhi_shutdown` v7.0 :1140 → :1112.

**Signature changes**
- `nhi_wake_supported(struct pci_dev *)` v7.0 nhi.c:1015 → `nhi_wake_supported(struct device *)` v7.2 nhi.c:1013.
- `nhi_probe` — see split above.

**Removed symbols**
- `nhi_enable_int_throttling` — v7.0 nhi.c:1038, **deleted** by `c51777370ac2`. Dead prototype left at nhi.h:32. A page written against v7.0 that says "the driver programs a fixed 128 µs throttle on all 16 vectors at probe and on resume" is now wrong: throttling is per-ring, opt-in via `tb_ring_throttling()`, programmed in `ring_interrupt_active()` (nhi.c:124-128), and `nhi_resume_noirq` no longer touches it.
- `struct tb_nhi.pdev` (thunderbolt.h v7.0 :500) — removed by `8c3ff7c5ae15`; replaced by `.dev` (v7.2 :520).
- `struct tb_nhi.msix_ida` (thunderbolt.h v7.0 :505) — removed; now `struct tb_nhi_pci.msix_ida` (pci.c:33).
- `extern const struct tb_nhi_ops icl_nhi_ops;` (nhi.h v7.0 :51) — removed.

**Moved constants**
- `MSIX_MIN_VECS`/`MSIX_MAX_VECS`: v7.0 nhi.c:41-42 → v7.2 nhi.h:129-130.
- `QUIRK_AUTO_CLEAR_INT`/`QUIRK_E2E`: v7.0 nhi.c:47-48 → v7.2 nhi.h:122-123.
- `RING_TYPE`, `RING_FIRST_USABLE_HOPID`, `RING_E2E_RESERVED_HOPID`, `NHI_MAILBOX_TIMEOUT` stayed in nhi.c (:28, :30, :35, :37).

**Added constants / fields / API**
- `REG_INT_THROTTLING_RATE_INTERVAL_MASK` GENMASK(15,0) — nhi_regs.h:105 (`c51777370ac2`).
- `TB_MAX_FRAME_SIZE 4096` — thunderbolt.h:639; `TB_FRAME_SIZE` respelled 256 (`5140737c592d`).
- `tb_ring_frame_size()` thunderbolt.h:641 (`5140737c592d`, hoisted from tbnet's private `ring_frame_size()`); `tb_ring_size()` :648 (`d614113c10ae`).
- `tb_ring_flush()` thunderbolt.h:660 / nhi.c:728 + `tb_ring_empty()` nhi.c:712 + `tb_ring.wait` (`94a11cd5ddb1`).
- `tb_ring_throttling()` thunderbolt.h:713 / nhi.c:850 + `tb_ring.interval_nsec` (`c51777370ac2`).
- `tb_nhi.domain_released` thunderbolt.h:530 (`f5cc545f5969`; `init_completion` moved earlier in probe by `9cbc63400f7d`).
- `tb_nhi_ops.pre_nvm_auth/.post_nvm_auth/.request_ring_irq/.release_ring_irq/.is_present/.init_interrupts` — nhi.h:63-68.

**Behavior changes a v7.0-based page would misstate**
1. `nhi->ops` is now mandatory — `nhi_probe` returns `-EINVAL` if `!nhi->ops` or `!nhi->ops->init_interrupts` (nhi.c:1192-1196). Every `if (nhi->ops && …)` guard was dropped (`dd60fb487e55`).
2. MSI-X request/release is no longer inline in the ring code — it goes through `ops->request_ring_irq`/`release_ring_irq` (nhi.c:571, :582, :816), so a non-PCI NHI can supply its own (`e241d98e04ef`).
3. `nhi_disable_interrupts()` no longer runs from `nhi_init_msi`; it runs from `nhi_probe` at nhi.c:1211, before `ops->init_interrupts` (`e241d98e04ef`).
4. `pci_set_master()` moved earlier — v7.0 called it after the DMA mask inside probe (nhi.c:1389); v7.2 calls it in `nhi_pci_probe` (pci.c:477) before `nhi_probe`, and the DMA mask is set inside `nhi_probe` (nhi.c:1219) (`8c3ff7c5ae15`).
5. Quirk and IOMMU detection now run in the PCI probe before the generic probe (pci.c:474-475) rather than mid-way through the single probe.
6. `nhi_remove`/`nhi_pci_remove` and the probe error path now `wait_for_completion(&nhi->domain_released)` before `nhi_shutdown` (pci.c:492, nhi.c:1245) — previously `nhi_shutdown` ran immediately after `tb_domain_remove` (`f5cc545f5969`).
7. `nhi_shutdown` no longer frees the MSI irq or destroys `msix_ida`; that is `ops->shutdown` = `nhi_pci_shutdown` (pci.c:233).
8. The driver stores drvdata on the generic device (`dev_set_drvdata` nhi.c:1249, `dev_get_drvdata` nhi.c:977 etc.) rather than `pci_set_drvdata`; only pci.c still uses `pci_get_drvdata` (pci.c:484).
9. All control-channel print macros now target `ctl->nhi->dev` instead of `&ctl->nhi->pdev->dev`, and the ctl DMA pool is created on `nhi->dev` (ctl.c:669) (`8c3ff7c5ae15`).
10. `tb_ring_dma_device()` returns `ring->nhi->dev` directly (thunderbolt.h:726).

#### 12. DOCUMENTATION AND ABI

- **Documentation/admin-guide/thunderbolt.rst:179-197** — section "DMA protection utilizing IOMMU" (heading :179-180); names `/sys/bus/thunderbolt/devices/domainX/iommu_dma_protection` at :187 and gives the udev rule at :197. Related IOMMU prose at :22 and :47.
- **Documentation/ABI/testing/sysfs-bus-thunderbolt:33-40** — `.../domainX/iommu_dma_protection`, Mar 2019 / 4.21, RO, "1 means IOMMU is used".
- **Kerneldoc blocks — include/linux/thunderbolt.h**: `struct tb_nhi` :500, `struct tb_ring` :533, `enum ring_desc_flags` :599, `struct ring_frame` :617, `tb_ring_rx()` :666, `tb_ring_tx()` :688, `tb_ring_dma_device()` :715.
- **nhi.c**: `tb_ring_poll()` :337, `tb_ring_poll_complete()` :409, `tb_ring_alloc_tx()` :594, `tb_ring_alloc_rx()` :610, `tb_ring_start()` :636, `tb_ring_flush()` :718, `tb_ring_stop()` :737, `tb_ring_throttling()` :840, `nhi_mailbox_cmd()` :860, `nhi_mailbox_mode()` :898. (Non-kerneldoc `/*` blocks document `ring_interrupt_active` :71, `nhi_disable_interrupts` :152, `ring_write_descriptors` :229, `ring_work` :259, `tb_ctl_tx`-style `tb_ring_free` :786.)
- **ctl.c**: `struct tb_ctl` :24, `tb_cfg_request_alloc()` :80, `tb_cfg_request_get()` :101, `tb_cfg_request_put()` :119, `tb_cfg_request()` :535, `tb_cfg_request_cancel()` :581, `tb_cfg_request_sync()` :602, `tb_ctl_alloc()` :641, `tb_ctl_free()` :697, `tb_ctl_start()` :726, `tb_ctl_stop()` :742, `tb_cfg_ack_notification()` :768, `tb_cfg_ack_plug()` :831, `tb_cfg_reset()` :899, `tb_cfg_read_raw()` :940, `tb_cfg_write_raw()` :1014, `tb_cfg_get_upstream_port()` :1163.
- **pci.c**: `struct tb_nhi_pci` :26. **nhi.h**: `struct tb_nhi_ops` :41. **ctl.h**: `struct tb_cfg_request` :52. **nhi_regs.h**: `struct ring_desc` :22, `enum icl_lc_mailbox_cmd` :168 (vendor).
- No `Documentation/driver-api/` entry covers the NHI ring or the control channel; register semantics live only in the nhi_regs.h comments (:45-51 TX ring, :54-61 RX ring, :64-69 TX options, :72-79 RX options, :84-88 notify bitfields, :94-98 interrupt bitfields, :113 REG_CAPS hop count).

### Area F: Paths, tunnels, credits and bandwidth — COMPLETE (recorded 2026-09-04)

#### 1. CORE STRUCTS

**`struct tb_regs_hop`** — drivers/thunderbolt/tb_regs.h:517, `__packed`, 2 dwords; one path-config-space entry indexed by ingress HopID.
- DWORD0 `next_hop:11` (519) HopID the packet carries out of `out_port`, i.e. the in-HopID at the next router
- `out_port:6` (523) egress adapter number on the *same* router
- `initial_credits:7` (524) Path Credits Allocated (VD for USB4 protocol adapters — not written since 7e49bb89df86)
- `pmps:1` (525) path PM packet support (USB4 v2 lane-to-lane hops)
- `unknown1:6` (526) RsvdZ, written 0
- `enable:1` (527) hop enable; `!enable` ⇒ end of / incomplete path
- DWORD1 `weight:4` (530) weight inside the priority group
- `unknown2:4` (531) RsvdZ, written 0
- `priority:3` (532) priority group
- `drop_packages:1` (533) drop from queue tail vs head
- `counter:11` (534) index into TB_CFG_COUNTERS on the in-port
- `counter_enable:1` (535) enable that counter
- `ingress_fc:1` (536, IFC) / `egress_fc:1` (537, EFC) flow control
- `ingress_shared_buffer:1` (538, ISE) / `egress_shared_buffer:1` (539, ESE)
- `pending:1` (540) hardware still draining this hop (polled on deactivate)
- `unknown3:3` (541) RsvdZ, written 0

**Addressing**: `enum tb_cfg_space { TB_CFG_HOPS = 0, ... }` drivers/thunderbolt/tb_msgs.h:15-20. Every access is `tb_port_read/write(port, &hop, TB_CFG_HOPS, 2 * hop_index, 2)` — hop entry N lives at dword offset `2*N`, N = ingress HopID at that adapter (path.c:48, 134, 175, 386, 396, 403, 423, 537, 576; switch.c:743 for the control path hop 0). debugfs uses the same stride, `PATH_LEN 2` (debugfs.c:36).

**`struct tb_path_hop`** — tb.h:381 (kerneldoc tb.h:354)
- `in_port` ingress adapter (owns the config entry) · `out_port` egress adapter on the same router
- `in_hop_index` HopID = index of the entry in `in_port`'s path config space
- `in_counter_index` TB_CFG_COUNTERS index, `-1` = disabled (always -1 in-tree)
- `next_hop_index` HopID written out of `out_port`
- `initial_credits` flow-controlled credits for this hop
- `nfc_credits` non-flow-controlled buffers added to `in_port` (DP video only)
- `pm_support` sets `hop.pmps` (USB4 v2 lane↔lane hops only, tunnel.c:168)

**`enum tb_path_port`** — tb.h:400: `TB_PATH_NONE 0`, `TB_PATH_SOURCE 1`, `TB_PATH_INTERNAL 2`, `TB_PATH_DESTINATION 4`, `TB_PATH_ALL 7`. Used as a per-hop position mask ANDed with the path-wide fc/shared-buffer settings (path.c:548-568).

**`struct tb_path`** — tb.h:430 (kerneldoc tb.h:408); unidirectional path
- `tb` domain · `name` debug string ("PCIe Up", "Video", "AUX TX", "DMA RX"…)
- `ingress_shared_buffer` / `egress_shared_buffer` (`enum tb_path_port` masks)
- `ingress_fc_enable` / `egress_fc_enable` (`enum tb_path_port` masks)
- `priority:3` · `weight:4` (signed bitfield) · `drop_packages`
- `activated` — path is programmed into hardware (double-activate guard)
- `clear_fc` — clear FC/shared-buffer bits when deactivating (DMA paths only)
- `path_length` — hop count · `alloc_hopid` — path owns port HopID reservations
- `hops[] __counted_by(path_length)` — flexible array (v7.2; was a separate `struct tb_path_hop *hops` pointer at v7.0)
- NOTE: there is **no** path-level `nfc_credits` field; NFC credits are per-hop.

**`struct tb_bandwidth_group`** — tb.h:238 (kerneldoc tb.h:222)
- `tb` domain · `index` Group_ID, 1..7 (`MAX_GROUPS`) · `ports` list of DP IN adapters (`tb_port.group_list`)
- `reserved` Mb/s released by one tunnel in the group, offered to the others via estimated_bw
- `release_work` delayed work releasing `reserved` after `TB_RELEASE_BW_TIMEOUT`

**`struct tb_tunnel`** — tunnel.h:73 (kerneldoc tunnel.h:33)
- `kref` refcount · `tb` domain · `src_port` / `dst_port` (dst may be NULL/null-adapter for discovered incomplete tunnels) · `npaths`
- callbacks: `pre_activate` (before path activation, may touch HW), `activate(tunnel,bool)`, `post_deactivate`, `destroy` (memory release, no HW), `maximum_bandwidth`, `allocated_bandwidth`, `alloc_bandwidth`, `consumed_bandwidth`, `release_unused_bandwidth`, `reclaim_available_bandwidth`
- `list` link into `tb_cm.tunnel_list` · `type` (`enum tb_tunnel_type`) · `state` (`enum tb_tunnel_state`)
- `max_up`/`max_down` Mb/s cap (only when limited) · `allocated_up`/`allocated_down` (USB3 only)
- `bw_mode` DP BW-allocation-mode registers usable for consumed/allocated
- `dprx_started`, `dprx_canceled`, `dprx_timeout` (ktime), `dprx_work` (delayed work)
- `callback`/`callback_data` — called (without tb->lock) once DP tunnel is fully active
- `paths[] __counted_by(npaths)` flexible array (v7.2; was `struct tb_path **paths` at v7.0)

**`enum tb_tunnel_type`** tunnel.h:14 — `TB_TUNNEL_PCI, TB_TUNNEL_DP, TB_TUNNEL_DMA, TB_TUNNEL_USB3`; names `tb_tunnel_names[] = {"PCI","DP","DMA","USB3"}` tunnel.c:101.
**`enum tb_tunnel_state`** tunnel.h:27 — exactly three at v7.2: `TB_TUNNEL_INACTIVE`, `TB_TUNNEL_ACTIVATING`, `TB_TUNNEL_ACTIVE`.
**`enum tb_tunnel_event`** tunnel.h:209 — `TB_TUNNEL_ACTIVATED`/`TB_TUNNEL_CHANGED`/`TB_TUNNEL_DEACTIVATED`/`TB_TUNNEL_LOW_BANDWIDTH`/`TB_TUNNEL_NO_BANDWIDTH` [errata 2026-09-13, migration of usb3-tunnel.md: the row contracted these five as one slash-joined token, which no oracle expands, so the coverage rule reported the tail names unresolved; each is spelled in full here]; strings `tb_event_names[]` tunnel.c:103 ("activated","changed","deactivated","low bandwidth","insufficient bandwidth").
**`struct tb_cm`** tb.c:64 — `tunnel_list`, `dp_resources`, `hotplug_active`, `remove_work`, `groups[MAX_GROUPS]`.
**Credit fields** — `struct tb_port` tb.h:280: `total_credits` (298), `ctl_credits` (299), `dma_credits` (300), `in_hopids`/`out_hopids` idas (295-296), `group` (301), `group_list` (302), `max_bw` (303), `redrive` (304). `struct tb_switch` tb.h:171: `credit_allocation` (210), `max_usb3_credits` (211), `min_dp_aux_credits` (212), `min_dp_main_credits` (213), `max_pcie_credits` (214), `max_dma_credits` (215).

#### 2. API FAMILIES  (S = static, E = exported)

**Path core (path.c)**
- `tb_dump_hop` path.c:16 (S) — dump one hop's registers via `tb_port_dbg`
- `tb_path_find_dst_port` path.c:34 (S) — follow enabled hops from src/hopid, return final out-port
- `tb_path_find_src_hopid` path.c:65 (S) — brute-force src HopID `TB_PATH_MIN_HOPID..max_in_hop_id` that lands on dst/dst_hopid
- `tb_path_discover` path.c:101 — reconstruct a path from hardware; two passes (count, then fill+`tb_port_alloc_in/out_hopid`); sets `activated=true`
- `tb_path_alloc` path.c:233 — walk `tb_for_each_port_on_path`, `num_hops = ports/2`, `kzalloc_flex`, per-hop `tb_port_alloc_in_hopid(in_hopid,in_hopid)` then `tb_port_alloc_out_hopid(-1,-1)` (last hop: `dst_hopid`), bonded/`link_nr` lane selection at 274-308
- `tb_path_free` path.c:345 — releases in/out HopIDs when `alloc_hopid`, then `kfree`
- `__tb_path_deallocate_nfc` path.c:365 (S) — subtract per-hop `nfc_credits` from in_port
- `__tb_path_deactivate_hop` path.c:378 (S) — clear enable, poll `hop.pending` (500 ms / `usleep_range(10,20)`), optionally clear FC/shared-buffer
- `tb_path_deactivate_hop` path.c:446 — public single-entry clear (`clear_fc=true`); used by switch.c reset paths
- `__tb_path_deactivate_hops` path.c:451 (S) · `tb_path_deactivate` path.c:466
- `tb_path_activate` path.c:492 — clear counters (reverse), add NFC credits (reverse), then **activate hops source→destination** (v7.2), read-modify-write each entry, set `activated`
- `tb_path_is_invalid` path.c:598 · `tb_path_port_on_path` path.c:620
- `tb_path_for_each_hop` macro tb.h:1213
- **Negative**: `tb_path_switch_on_path()` does not exist at v7.2 (`grep -rn` over drivers/ and include/ returns nothing); last referenced by 0bd680cd900c (v5.9).

**HopID / port helpers (switch.c)** — `tb_port_alloc_hopid` switch.c:763 (S, clamps min to `TB_PATH_MIN_HOPID` for non-NHI), `tb_port_alloc_in_hopid` 799, `tb_port_alloc_out_hopid` 813, `tb_port_release_in_hopid` 823, `tb_port_release_out_hopid` 833, `tb_next_port_on_path` 860, `tb_port_add_nfc_credits` 567, `tb_port_clear_counter` 604. Iterators `tb_for_each_port_on_path` tb.h:1141, `tb_for_each_upstream_port_on_path` tb.h:1153, `tb_port_path_direction_downstream` tb.h:1121 (inline), `tb_port_use_credit_allocation` tb.h:1128 (inline).

**Per-protocol path init (tunnel.c)** — see table in §3-adjacent list below: `tb_pci_init_path` 418 (S), `tb_usb3_init_path` 2178 (S), `tb_dp_init_aux_path` 1465 (S), `tb_dp_init_video_path` 1512 (S), `tb_dma_init_rx_path` 1800 (S), `tb_dma_init_tx_path` 1835 (S); shared `tb_init_pm_support` 168 (S).

**PATH-PARAMETER TABLE** (all file:line in drivers/thunderbolt/tunnel.c)

| init fn | egress_fc | ingress_fc | shared buf (in/eg) | priority | weight | drop | credits |
|---|---|---|---|---|---|---|---|
| `tb_pci_init_path` :418 | SOURCE\|INTERNAL :422 | ALL :424 | NONE/NONE :423,425 | 3 (`TB_PCI_PRIORITY` :24) :426 | 1 (`TB_PCI_WEIGHT` :25) :427 | 0 :428 | `tb_pci_init_credits` :391 → `min(max_pcie_credits, avail)`, ≥`TB_MIN_PCIE_CREDITS`; legacy 32/16 (bonded/not) or 7 :409-411 |
| `tb_usb3_init_path` :2178 | SOURCE\|INTERNAL :2182 | ALL :2184 | NONE/NONE :2183,2185 | 3 (`TB_USB3_PRIORITY` :33) :2186 | 2 (`TB_USB3_WEIGHT` :34) :2187 | 0 :2188 | `tb_usb3_init_credits` :2160 → `sw->max_usb3_credits`; legacy 32/16 or 7 :2170-2172 |
| `tb_dp_init_video_path` :1512 | NONE :1516 | NONE :1518 | NONE/NONE :1517,1519 | 1 (`TB_DP_VIDEO_PRIORITY` :45) :1520 | 1 (:46) :1521 | unset (0) | `tb_dp_init_video_credits` :1483 → **nfc_credits** = `sw->min_dp_main_credits`; legacy `min(total_credits-2, 12U)` :1506 |
| `tb_dp_init_aux_path` :1465 | SOURCE\|INTERNAL :1469 | ALL :1471 | NONE/NONE :1470,1472 | 2 (`TB_DP_AUX_PRIORITY` :48) :1473 | 1 (:49) :1474 | unset (0) | `tb_dp_init_aux_credits` :1454 → `sw->min_dp_aux_credits`; legacy 1 :1462 |
| `tb_dma_init_rx_path` :1800 | SOURCE\|INTERNAL :1805 | ALL :1806 | NONE/NONE :1807,1808 | 5 (`TB_DMA_PRIORITY` :61) :1809 | 1 (:62) :1810 | unset; `clear_fc = true` :1811 | hop0 `min(tb_usable_credits, credits)` :1819-1821; rest `tb_dma_reserve_credits` :1767 |
| `tb_dma_init_tx_path` :1835 | **ALL** :1839 | ALL :1840 | NONE/NONE :1841,1842 | 5 :1843 | 1 :1844 | unset; `clear_fc = true` :1845 | all hops `tb_dma_reserve_credits` :1767 |

**Tunnel core (tunnel.c)** — `tb_tunnel_alloc` 178 (S, `kzalloc_flex(*tunnel, paths, npaths)` + `kref_init`), `tb_tunnel_get` 197 (S), `tb_tunnel_destroy` 204 (S, kref release: `destroy` cb → `tb_path_free` each → kfree), `tb_tunnel_put` 220, `tb_tunnel_event` 241, `tb_tunnel_set_active` 274 (S inline), `tb_tunnel_changed` 287 (S inline), `tb_tunnel_activate` 2405, `tb_tunnel_deactivate` 2458, `tb_tunnel_is_invalid` 2382, `tb_tunnel_port_on_path` 2486, `tb_tunnel_is_activated` 2503 (S), `tb_tunnel_maximum_bandwidth` 2520, `tb_tunnel_allocated_bandwidth` 2545, `tb_tunnel_alloc_bandwidth` 2570, `tb_tunnel_consumed_bandwidth` 2603, `tb_tunnel_release_unused_bandwidth` 2641, `tb_tunnel_reclaim_available_bandwidth` 2668, `tb_tunnel_type_name` 2680. Inline predicates tunnel.h: `tb_tunnel_is_active` 152, `tb_tunnel_is_pci` 173, `_is_dp` 178, `_is_dma` 183, `_is_usb3` 188, `tb_tunnel_direction_downstream` 193. Print macros tunnel.h:224 `__TB_TUNNEL_PRINT`, 236/238/240/242 `tb_tunnel_WARN/warn/info/dbg`.
- **Negative**: `tb_tunnel_restart()` does not exist at v7.2 (dropped by cab96faacf53, v6.14); resume re-activates via `tb_tunnel_activate()` on `tunnel_list` (tb.c:3185, 3273).

**Callback fill table** (which protocol sets which `tb_tunnel` op)

| callback | PCIe | USB3 | DP | DMA |
|---|---|---|---|---|
| `pre_activate` | `tb_pci_pre_activate` :312 (alloc only, :542) | `tb_usb3_pre_activate` :2044 (host-router tunnels only, :2276/:2361) | `tb_dp_pre_activate` :1016 (:1603,:1708) | — |
| `activate` | `tb_pci_activate` :361 (:465,:543) | `tb_usb3_activate` :2054 (:2218,:2337) | `tb_dp_activate` :1144 (:1604,:1709) | — |
| `post_deactivate` | — | — | `tb_dp_post_deactivate` :1042 | — |
| `destroy` | — | — | — | `tb_dma_destroy` :1878 (:1931) |
| `maximum_bandwidth` | — | — | `tb_dp_maximum_bandwidth` :1368 | — |
| `allocated_bandwidth` | — | — | `tb_dp_allocated_bandwidth` :1263 | — |
| `alloc_bandwidth` | — | — | `tb_dp_alloc_bandwidth` :1301 | — |
| `consumed_bandwidth` | — | `tb_usb3_consumed_bandwidth` :2068 | `tb_dp_consumed_bandwidth` :1391 | — |
| `release_unused_bandwidth` | — | `tb_usb3_release_unused_bandwidth` :2091 | — | — |
| `reclaim_available_bandwidth` | — | `tb_usb3_reclaim_available_bandwidth` :2106 | — | — |

**PCIe tunnels** — `tb_tunnel_discover_pci` tunnel.c:452, `tb_tunnel_alloc_pci` 532, `tb_tunnel_reserved_pci` 585, `tb_pci_port_ltssm_state_detect` 293 (S, v7.2), `tb_pci_pre_activate` 312 (S, v7.2), `tb_pci_set_ext_encapsulation` 327 (S), `tb_pci_activate` 361 (S), `tb_pci_init_credits` 391 (S). HW seams: `tb_pci_port_is_enabled` switch.c:1387, `tb_pci_port_enable` switch.c:1405, `usb4_pci_port_ltssm_state` usb4.c:3162, `usb4_pci_port_set_ext_encapsulation` usb4.c:3132, `enum tb_pcie_ltssm_state` tb_regs.h:481, `ADP_PCIE_CS_0_LTSSM_MASK` tb_regs.h:476.
tb.c side: `tb_tunnel_pci` 2275 (S) — `tb_switch_find_port(TB_TYPE_PCIE_UP)`, `tb_switch_downstream_port`, `tb_find_pcie_down` 1814 (S; `usb4_switch_map_pcie_down` usb4.c:1015, else hard-coded per-controller index, else `tb_find_unused_port` 460), `tb_tunnel_alloc_pci` → `tb_tunnel_activate` → `tb_switch_pcie_l1_enable` → `tb_switch_xhci_connect` → `list_add_tail(&tunnel->list, &tcm->tunnel_list)`. Teardown: `tb_disconnect_pci` tb.c:2254 (S, `.disapprove_switch`).
**PCI-side seam**: once the paths are up and `ADP_PCIE_CS_0_PE` is set on both adapters, the tunneled downstream port's link trains and native PCIe hotplug takes over — `pciehp_ist()` drivers/pci/hotplug/pciehp_hpc.c:728 → `pciehp_handle_presence_or_link_change()` drivers/pci/hotplug/pciehp_ctrl.c:232 → `pciehp_check_link_status()` drivers/pci/hotplug/pciehp_hpc.c:291 → `pcie_wait_for_link()` drivers/pci/pci.c:4678. Unplug: hotplug branch tb.c:2461-2476 → `tb_free_invalid_tunnels` 1775 → `tb_deactivate_and_free_tunnel` 1722; PCI side sees Data Link Layer Link Active drop and runs the same `pciehp_ist` path.

**USB3 tunnels** — `tb_tunnel_discover_usb3` tunnel.c:2205, `tb_tunnel_alloc_usb3` 2310, `tb_usb3_max_link_rate` 2027 (S), `tb_usb3_pre_activate` 2044 (S), `tb_usb3_activate` 2054 (S), `tb_usb3_consumed_bandwidth` 2068 (S), `tb_usb3_release_unused_bandwidth` 2091 (S), `tb_usb3_reclaim_available_bandwidth` 2106 (S), `tb_usb3_init_credits` 2160 (S), `tb_usb3_init_path` 2178 (S). HW seams: `tb_usb3_port_is_enabled` switch.c:1352, `tb_usb3_port_enable` switch.c:1370, `usb4_usb3_port_max_link_rate` usb4.c:2204 (20000 or 10000 Mb/s from `ADP_USB3_CS_4_MSLR`), `usb4_usb3_port_allocated_bandwidth` usb4.c:2324, `usb4_usb3_port_allocate_bandwidth` usb4.c:2426, `usb4_usb3_port_release_bandwidth` usb4.c:2468, `usb4_usb3_port_cm_request` usb4.c:2223 (S). tb.c side: `tb_tunnel_usb3` 905 (S), `tb_create_usb3_tunnels` 997 (S), `tb_find_usb3_down` 479 (S, `usb4_switch_map_usb3_down` usb4.c:1048), `tb_find_first_usb3_tunnel` 508 (S), `tb_release_unused_usb3_bandwidth` 866 (S), `tb_reclaim_usb3_bandwidth` 876 (S).

**DP tunnels** — `tb_tunnel_discover_dp` tunnel.c:1589, `tb_tunnel_alloc_dp` 1690 (3 paths: VIDEO_PATH_OUT 0, AUX_PATH_OUT 1, AUX_PATH_IN 2). Helpers: `tb_dp_is_usb4` 618 (S, USB4 **or** Titan Ridge), `tb_dp_cm_handshake` 624 (S), `tb_dp_cap_get_rate` 664 / `_get_rate_ext` 687 / `_set_rate` 704 / `_get_lanes` 727 / `_set_lanes` 743 (all S inline), `tb_dp_is_uhbr_rate` 699 (S inline), `tb_dp_bandwidth` 764 (S), `tb_dp_reduce_bandwidth` 772 (S, 12-entry rate×lane ladder 776-790), `tb_dp_xchg_caps` 815 (S), `tb_dp_bandwidth_alloc_mode_enable` 914 (S), `tb_dp_pre_activate` 1016 (S), `tb_dp_post_deactivate` 1042 (S), `dprx_timeout_to_ktime` 1054 (S), `tb_dp_wait_dprx` 1060 (S), `tb_dp_dprx_work` 1088 (S), `tb_dp_dprx_start` 1114 (S), `tb_dp_dprx_stop` 1134 (S), `tb_dp_activate` 1144 (S), `tb_dp_bandwidth_mode_maximum_bandwidth` 1193 (S), `tb_dp_bandwidth_mode_consumed_bandwidth` 1227 (S), `tb_dp_allocated_bandwidth` 1263 (S), `tb_dp_alloc_bandwidth` 1301 (S), `tb_dp_read_cap` 1337 (S), `tb_dp_maximum_bandwidth` 1368 (S), `tb_dp_consumed_bandwidth` 1391 (S), `tb_dp_dump` 1536 (S). HW seams: `tb_dp_port_is_enabled/enable/set_hops/hpd_is_active/hpd_clear` switch.c:1505/1526/1471/1422/1443; usb4.c DP BW-mode block: `usb4_dp_port_set_cm_id` 2525, `_bandwidth_mode_supported` 2555, `_bandwidth_mode_enabled` 2581, `_set_cm_bandwidth_mode_supported` 2611, `_group_id` 2646, `_set_group_id` 2674, `_nrd` 2707, `_set_nrd` 2766, `_granularity` 2831, `_set_granularity` 2872, `_set_estimated_bandwidth` 2919, `_allocated_bandwidth` 2953, `_allocate_bandwidth` 3050, `_requested_bandwidth` 3098, `usb4_dp_port_wait_and_clear_cm_ack` 3001 (S). DP register block tb_regs.h:403-472 (`ADP_DP_CS_0/1/2/3/8`, `DP_LOCAL_CAP` 431, `DP_REMOTE_CAP` 432, `DP_STATUS_CTRL` 438, `DP_COMMON_CAP` 441, `DP_COMMON_CAP_DPRX_DONE` 468).
tb.c side: `tb_add_dp_resources` 111 (S), `tb_remove_dp_resources` 138 (S), `tb_discover_dp_resource` 157 (S), `tb_discover_dp_resources` 172 (S), `tb_find_dp_out` 1863 (S), `tb_dp_tunnel_active` 1906 (S, the DP activation callback), `tb_tunnel_one_dp` 1971 (S), `tb_tunnel_dp` 2063 (S), `tb_enter_redrive` 2104 / `tb_exit_redrive` 2129 / `tb_switch_enter_redrive` 2147 / `tb_switch_exit_redrive` 2159 (all S, gated on `QUIRK_KEEP_POWER_IN_DP_REDRIVE`), `tb_dp_resource_unavailable` 2178 (S), `tb_dp_resource_available` 2209 (S), `tb_disconnect_and_release_dp` 2231 (S), `tb_increase_tmu_accuracy` 281 (S) + `tb_increase_switch_tmu_accuracy` 254 (S), `tb_switch_query/alloc/dealloc_dp_resource` switch.c:3692/3709/3735 (→ `usb4_switch_query_dp_resource` usb4.c:900, `_alloc_` 933, `_dealloc_` 958).
**HPD relay**: DP OUT HPD seen during scan (tb.c:1299 `tb_dp_port_hpd_is_active`) → `tb_queue_hotplug` → hotplug branch tb.c:2514 → `tb_dp_resource_available` 2209 → `tb_tunnel_dp` 2063. `tb_dp_port_hpd_clear` is called exactly once, from `tb_dp_activate` deactivation (tunnel.c:1166). **GPU-side seam**: after tunnel-up, the GPU sees HPD on its own DP link and reads DPCD `DP_TUNNELING_OUI 0xe0000` (include/drm/display/drm_dp.h:1448) via `drm_dp_tunnel_detect()` drivers/gpu/drm/display/drm_dp_tunnel.c:761.
**DP BW-request flow**: DP IN raises `TB_CFG_ERROR_DP_BW` → `tb_handle_notification` tb.c:2885 → `tb_queue_dp_bandwidth_request` tb.c:2868 → `tb_handle_dp_bandwidth_request` tb.c:2736 → `usb4_dp_port_requested_bandwidth` → `tb_alloc_dp_bandwidth` tb.c:2538 → `tb_tunnel_alloc_bandwidth`; on success `tb_recalc_estimated_bandwidth` + `tb_tunnel_dp` (v7.2 addition).

**DMA tunnels** — `tb_tunnel_alloc_dma` tunnel.c:1903, `tb_tunnel_match_dma` 1981, `tb_dma_available_credits` 1754 (S), `tb_dma_reserve_credits` 1767 (S), `tb_dma_release_credits` 1858 (S), `tb_dma_destroy_path` 1870 (S), `tb_dma_destroy` 1878 (S). No `activate` callback — DMA tunnels are pure path plumbing. tb.c: `tb_approve_xdomain_paths` 2319 (S, `.approve_xdomain_paths`), `__tb_disconnect_xdomain_paths` 2368 (S), `tb_disconnect_xdomain_paths` 2400 (S).

**Credits** — `tb_usable_credits` tunnel.c:114 (S inline, `total_credits - ctl_credits`), `tb_available_credits` tunnel.c:127 (S), `tb_dma_available_credits` tunnel.c:1754 (S); per-protocol `tb_pci_init_credits` 391, `tb_dp_init_aux_credits` 1454, `tb_dp_init_video_credits` 1483, `tb_usb3_init_credits` 2160, `tb_dma_reserve_credits` 1767. Router side: `usb4_switch_credits_init` usb4.c:758 (`USB4_SWITCH_OP_BUFFER_ALLOC`, `enum usb4_ba_index` usb4.c:39: `USB4_BA_MAX_USB3 0x1` = baMaxUSB3, `USB4_BA_MIN_DP_AUX 0x2` = baMinDPaux, `USB4_BA_MIN_DP_MAIN 0x3` = baMinDPmain, `USB4_BA_MAX_PCIE 0x4` = baMaxPCIe, `USB4_BA_MAX_HI 0x5` = baMaxHI/DMA; masks `USB4_BA_LENGTH_MASK` 36, `USB4_BA_INDEX_MASK` 37, `USB4_BA_VALUE_MASK/SHIFT` 47/48; validation 821-865 falls back to hard-coded values on any missing field), `tb_switch_credits_init` switch.c:3256 (S, USB4 non-ICM only), `port->total_credits` from `ADP_CS_4_TOTAL_BUFFERS` switch.c:755, `port->ctl_credits` from hop entry 0 switch.c:743, `tb_port_do_update_credits` switch.c:1234 (S), `tb_port_update_credits` switch.c:1269 (called after lane bonding at switch.c:2919/2924 and 3177/3178 — bonding merges lane-1 buffers into lane 0 so `total_credits` grows).

**Bandwidth groups / asym (tb.c)** — `tb_init_bandwidth_groups` 1580 (S, index = i+1), `tb_bandwidth_group_attach_port` 1595 (S), `tb_find_free_bandwidth_group` 1607 (S), `tb_attach_bandwidth_group` 1621 (S), `tb_discover_bandwidth_group` 1658 (S, uses `usb4_dp_port_group_id`), `tb_detach_bandwidth_group` 1676 (S), `__release_group_bandwidth` 1532 (S), `__configure_group_sym` 1543 (S), `tb_bandwidth_group_release_work` 1567 (S), `tb_recalc_estimated_bandwidth_for_group` 1432 (S), `tb_recalc_estimated_bandwidth` 1515 (S), `tb_asym_supported` 675 (S), `tb_maximum_bandwidth` 707 (S), `tb_available_bandwidth` 815 (S), `tb_consumed_usb3_pcie_bandwidth` 551 (S), `tb_consumed_dp_bandwidth` 605 (S), `tb_configure_asym` 1039 (S), `tb_configure_sym` 1147 (S), `tb_configure_link` 1232 (S). NOTE: there is **no** function named `tb_bandwidth_group_reservation`; the reservation is the `group->reserved` field manipulated in `tb_alloc_dp_bandwidth` (tb.c:2632, 2710) and released by `tb_bandwidth_group_release_work`.

**tb.c tunnel management** — `tb_find_tunnel` 490 (S), `tb_switch_discover_tunnels` 376 (S), `tb_discover_tunnels` 1694 (S), `tb_deactivate_and_free_tunnel` 1722 (S), `tb_free_invalid_tunnels` 1775 (S), `tb_free_unplugged_children` 1790 (S — router removal only; the tunnel side runs earlier via `tb_free_invalid_tunnels`), `tb_find_unused_port` 460 (S), `tb_stop` 2941 (S), `tb_deinit` 2964 (S), `tb_start` 2995 (S), `tb_suspend_noirq` 3077, `tb_resume_noirq` 3141, `tb_runtime_suspend` 3232, `tb_remove_work` 3250, `tb_runtime_resume` 3263, `tb_cm_ops` 3287, `tb_probe` 3374.

**Consumers** — `tb_xdomain_enable_paths` xdomain.c:2439 (E) → `tb_domain_approve_xdomain_paths` domain.c:782 → `cm_ops->approve_xdomain_paths`; `tb_xdomain_disable_paths` xdomain.c:2470 (E) → domain.c:811. Declarations include/linux/thunderbolt.h:295/298 (+`tb_xdomain_disable_all_paths` inline :304).

#### 3. LIFECYCLE AND LOCKING
- **Domain lock** `tb->lock` (mutex) serializes everything in tb.c: `tb_handle_hotplug` tb.c:2432/2525, `tb_handle_dp_bandwidth_request` 2748/2860, `tb_dp_tunnel_active` 1912/1966, `tb_bandwidth_group_release_work` 1573/1577, `tb_approve_xdomain_paths` 2333/2356, `tb_disconnect_xdomain_paths` 2405/2409, `tb_remove_work` 3255, `tb_runtime_suspend/resume` 3236/3268. `tb_dp_dprx_work` takes it around each poll (tunnel.c:1094/1106) and drops it before invoking `tunnel->callback` (1109).
- **Tunnel refcount**: `kref_init` in `tb_tunnel_alloc` tunnel.c:192; `tb_tunnel_get` 197 / `tb_tunnel_put` 220 both wrap the kref in the file-static `tb_tunnel_lock` mutex (tunnel.c:112). The put that frees is `tb_tunnel_destroy` tunnel.c:204 (calls `->destroy`, frees each path, kfrees). Extra reference is taken only by `tb_dp_dprx_start` tunnel.c:1120 and dropped in `tb_dp_dprx_work` 1111 or `tb_dp_dprx_stop` 1140.
- **Path lifecycle**: `tb_path_alloc`/`tb_path_discover` → `tb_path_activate` (sets `activated`) → `tb_path_deactivate` (clears it) → `tb_path_free`. Double-activation is refused with `tb_WARN` (path.c:496); deactivating an inactive path also `tb_WARN`s (path.c:468). `tb_tunnel_activate` pre-deactivates any already-activated path (tunnel.c:2415-2420).
- **Tunnel state**: `TB_TUNNEL_INACTIVE` → `TB_TUNNEL_ACTIVATING` (set unconditionally at tunnel.c:2422) → `TB_TUNNEL_ACTIVE` via `tb_tunnel_set_active(true)` (2445, or from `tb_dp_dprx_work` 1104). `tb_dp_activate` returns `-EINPROGRESS` when a callback is registered, leaving the tunnel in ACTIVATING until DPRX completes. `tb_tunnel_deactivate` always ends at `tb_tunnel_set_active(false)` (2475).
- **DP flags**: `dprx_started` set in `tb_dp_dprx_start` 1122, cleared in `tb_dp_dprx_stop` 1137 which also sets `dprx_canceled` 1138 and cancels the work; `bw_mode` set in `tb_dp_alloc_bandwidth` 1332, cleared by `tb_handle_dp_bandwidth_request` tb.c:2779 when DPTX turns BW-alloc mode off.
- **Ownership**: tunnels live on `tcm->tunnel_list`; `tb_deactivate_and_free_tunnel` tb.c:1722 is the only place doing deactivate+`list_del`+detach-group+dealloc-DP-resource+configure-sym+rpm-put+`tb_tunnel_put`. `tb_stop` tb.c:2949 puts every tunnel (deactivating only DMA ones).

#### 4. HARD-CODED LIMITS
- `TB_PATH_MIN_HOPID 8` tb.h:450 (HopIDs 0-7 reserved) · `TB_PATH_MAX_HOPS (7 * 2)` = 14 tb.h:455
- `TB_PCI_HOPID 8` tunnel.c:19 · `TB_USB3_HOPID 8` :28 · `TB_DP_AUX_TX_HOPID 8` :37, `TB_DP_AUX_RX_HOPID 8` :38, `TB_DP_VIDEO_HOPID 9` :39
- Path indices: `TB_PCI_PATH_DOWN 0`/`UP 1` :21-22; `TB_USB3_PATH_DOWN 0`/`UP 1` :30-31; `TB_DP_VIDEO_PATH_OUT 0`/`AUX_PATH_OUT 1`/`AUX_PATH_IN 2` :41-43
- Priorities/weights: PCI 3/1 :24-25, USB3 3/2 :33-34, DP video 1/1 :45-46, DP aux 2/1 :48-49, DMA 5/1 :61-62
- `TB_MIN_PCIE_CREDITS 6U` :52 · `TB_DMA_CREDITS 14` :57 · `TB_MIN_DMA_CREDITS 1` :59
- `USB4_V2_PCI_MIN_BANDWIDTH (1500 * TB_PCI_WEIGHT)` = 1500 :70 · `USB4_V2_USB3_MIN_BANDWIDTH (1500 * TB_USB3_WEIGHT)` = 3000 :71
- `TB_DPRX_TIMEOUT 12000` ms :81 · `TB_DPRX_WAIT_TIMEOUT 25` ms :82 · `TB_DPRX_POLL_DELAY 50` ms :83
- `TB_TIMEOUT 100` ms tb.c:19 · `TB_RELEASE_BW_TIMEOUT 10000` ms tb.c:20 · `TB_BW_ALLOC_RETRIES 3` tb.c:26
- `TB_ASYM_MIN (40000 * 90 / 100)` = 36000 Mb/s tb.c:32 · `TB_ASYM_THRESHOLD 45000` tb.c:42 · `MAX_GROUPS 7` tb.c:44
- Bare literals: hop-drain timeout 500 ms + `usleep_range(10,20)` path.c:401,430 · LTSSM detect 500 ms + `fsleep(50)` tunnel.c:295,306 · CM handshake 3000 ms + `usleep_range(100,150)` tunnel.c:833,654 · DPRX poll `usleep_range(100,150)` tunnel.c:1081 · legacy PCIe credits 32/16/7 tunnel.c:409,411 · legacy USB3 credits 32/16/7 tunnel.c:2170,2172 · legacy DP video NFC `min(total_credits-2, 12U)` tunnel.c:1506 · legacy DP aux 1 tunnel.c:1462 · legacy DMA 14/6 tunnel.c:1790 · DP granularity search 250→1000 with 255-step ceiling tunnel.c:977 · DP encodings ×128/132 (UHBR) and ×8/10 tunnel.c:768-769 · UHBR threshold `rate >= 10000` tunnel.c:701 · rate ladder 8100/5400/2700/1620 × 4/2/1 tunnel.c:776-790 · USB3 isoch cap 90% tunnel.c:2122, 2328 · link-BW guard band 10% tb.c:787-788 · `available_up/down = 120000` seed tb.c:823 · low-BW USB3 notify threshold 1500 Mb/s tb.c:964 · BW-retry delay 50 ms tb.c:2836 · resume USB3 delay 500 ms tb.c:3172, post-restart `msleep(100)` tb.c:3193, `remove_work` delay 50 ms tb.c:3283 · default `ctl_credits = 2` switch.c:747 · `usb4_dp_port_wait_and_clear_cm_ack` 500 ms/`usleep_range(50,100)` usb4.c:3080,3022 · USB3 CM-request wait 1500 ms/`USB4_PORT_DELAY 50` usb4.c:2254, usb4.c:51 · USB3 max link rate 20000/10000 Mb/s usb4.c:2218.
- Module params: `dprx_timeout` tunnel.c:85-89, `dma_credits` tunnel.c:91-94, `bw_alloc_mode` tunnel.c:96-99, `asym_threshold` tb.c:46-50 (all 0444).

#### 5. VERSION-SPECIFIC FACTS (v7.2 vs widely-documented older kernels)
- `struct tb_path.hops` is a **flexible array** `__counted_by(path_length)` (tb.h:446); the old `struct tb_path_hop *hops` pointer and its separate `kzalloc_objs`/`kfree` are gone (c3e7cc8bc5ca).
- `struct tb_tunnel.paths` is a **flexible array** `__counted_by(npaths)` (tunnel.h:110); `tunnel->paths` is no longer separately allocated/freed (498c05821bb4).
- `tb_path_activate()` now programs hops **source → destination** (path.c:529); pre-v7.2 it iterated last→first. Rollback now deactivates from hop 0 (path.c:579).
- `tb_path_activate()` now **reads the hop entry before writing** and only programs `initial_credits`/`ingress_fc`/`ingress_shared_buffer` for lane adapters or pre-USB4 routers (path.c:536-570); `__tb_path_deactivate_hop` gained the same `tb_port_is_null()` condition (path.c:415) — commit 7e49bb89df86.
- New at v7.2: `tb_pci_pre_activate` / `tb_pci_port_ltssm_state_detect` (tunnel.c:312/293), `usb4_pci_port_ltssm_state` (usb4.c:3162), `enum tb_pcie_ltssm_state` + `ADP_PCIE_CS_0_LTSSM_MASK` (tb_regs.h:481/476) — commit 69a7b98770b7. PCIe tunnels now fail activation if either adapter is not in LTSSM Detect.
- `group_reserved[]` in `tb_consumed_dp_bandwidth` sized `MAX_GROUPS + 1` (tb.c:612) — fixes off-by-one that dropped group 7's reservation (d2ee4d47aacb).
- `tb_handle_dp_bandwidth_request` re-runs `tb_tunnel_dp()` after a successful allocation (tb.c:2853-2854) — new multi-display retry (afe9021d63b4).
- New file drivers/thunderbolt/stream.c (`CONFIG_USB4_STREAM`) and drivers/thunderbolt/configfs.c (`CONFIG_USB4_CONFIGFS`), both v7.2 (6db21d817b43, cba57ed6f1e7).
- Older-kernel symbols absent at v7.2: `tb_tunnel_restart()` (dropped v6.14, cab96faacf53), `tb_tunnel_free()` (renamed `tb_tunnel_put()` v6.14, d6d458d42e1e), `tb_path_switch_on_path()` (long gone).
- Print macros now take `(tb)->nhi->dev` rather than `&(tb)->nhi->pdev->dev` (tb.h:728-732) — `struct tb_nhi` no longer embeds `pci_device` (8c3ff7c5ae15).
- **ICM-only / out of scope**: `tb_cm_ops.disconnect_pcie_paths` (tb.h:531) is implemented only by `icm_disconnect_pcie_paths` icm.c:2236; the software CM (`tb_cm_ops` tb.c:3287) leaves it NULL, so `tb_domain_disconnect_pcie_paths` domain.c:756 returns 0 [orchestrator note 2026-09-04, refuted at write time (dma-tunnel.md): with the callback unset the function returns `-EPERM` (domain.c:758-759), so `tb_domain_disconnect_all_paths` returns before its XDomain sweep and `tb_xdomain_disable_all_paths` is unreachable under the software CM] there. `icm_fr_/icm_tr_approve_xdomain_paths` icm.c:582/1158 are the ICM twins of `tb_approve_xdomain_paths`.
- **Vendor-specific branches inside generic code** (flag when writing): `tb_dp_is_usb4()` treats Titan Ridge as USB4 (tunnel.c:618-622); LTTPR disable for Titan Ridge DP OUT (tunnel.c:905-908); hard-coded Cactus/Alpine/Falcon/Titan Ridge PCIe-down port indices (tb.c:1833-1839); `QUIRK_KEEP_POWER_IN_DP_REDRIVE` gates the whole redrive path (tb.c:2108, 2133, 2163); PCIe L1 enable "for Titan Ridge" (tb.c:2309).

#### 6. SUGGESTED PAGE TOPICS (one mechanism per page)
1. **Path config space layout** — `struct tb_regs_hop` tb_regs.h:517, `TB_CFG_HOPS` tb_msgs.h:16, the `2*hopid` stride, `tb_dump_hop` path.c:16.
2. **HopID allocation and the reserved 0-7 range** — `tb_port_alloc_hopid` switch.c:763, `TB_PATH_MIN_HOPID` tb.h:450, `in_hopids`/`out_hopids` idas, NHI exception.
3. **Walking a path: `tb_next_port_on_path`** — switch.c:860 + the two iterator macros tb.h:1141/1153, `tb_switch_is_reachable` switch.c:838.
4. **`tb_path_alloc()` and dual-link/bonded lane selection** — path.c:233, the `link_nr` rules 274-308.
5. **`tb_path_discover()`: reconstructing a path from hardware** — path.c:101, `tb_path_find_src_hopid` 65, `tb_path_find_dst_port` 34, incomplete paths.
6. **`tb_path_activate()`: the write sequence** — path.c:492, counters/NFC ordering, source→destination order, RsvdZ/VD read-modify-write.
7. **`tb_path_deactivate()` and hop draining** — path.c:378/451/466, `pending` poll, `clear_fc`.
8. **Flow control, shared buffers and the `tb_path_port` mask** — tb.h:400, path.c:548-568.
9. **Priority and weight scheduling across protocols** — the table in §2, tunnel.c:24-62.
10. **Credit model I: where credits come from** — `total_credits`/`ctl_credits` switch.c:743-757, `tb_port_update_credits` switch.c:1269 and lane bonding.
11. **Credit model II: USB4 buffer allocation** — `usb4_switch_credits_init` usb4.c:758, `enum usb4_ba_index` usb4.c:39, validation and fallback 821-886.
12. **Credit model III: `tb_available_credits()` arithmetic** — tunnel.c:127, DP-stream headroom, `tb_dma_available_credits` 1754.
13. **`struct tb_tunnel` and its callback vtable** — tunnel.h:73 + the fill table.
14. **Tunnel refcounting and destruction** — `tb_tunnel_alloc`/`get`/`put`/`destroy` tunnel.c:178/197/220/204, `tb_tunnel_lock` 112.
15. **`tb_tunnel_activate()` / `deactivate()` and `enum tb_tunnel_state`** — tunnel.c:2405/2458, tunnel.h:27, `-EINPROGRESS`.
16. **Tunnel uevents** — `tb_tunnel_event` tunnel.c:241, `enum tb_tunnel_event` tunnel.h:209, Documentation/admin-guide/thunderbolt.rst:319.
17. **PCIe tunnels end to end** — tunnel.c:452/532, tb.c:2275, the pciehp seam.
18. **PCIe LTSSM Detect precondition (new)** — tunnel.c:293/312, usb4.c:3162, tb_regs.h:481.
19. **PCIe extended encapsulation (USB4 v2 Gen 4)** — tunnel.c:327, usb4.c:3132.
20. **USB3 tunnels and their bandwidth model** — tunnel.c:2205/2310/2027/2068, usb4.c:2204-2500, the 90 % isoch rule.
21. **DP tunnel anatomy: three paths** — tunnel.c:1690/1589, video vs AUX TX/RX parameters.
22. **DP capability exchange and rate reduction** — `tb_dp_xchg_caps` tunnel.c:815, `tb_dp_reduce_bandwidth` 772, `tb_dp_cm_handshake` 624.
23. **DP bandwidth allocation mode handshake** — tunnel.c:914/1193/1227/1301, usb4.c:2514-3120.
24. **DPRX capability wait and asynchronous DP activation** — tunnel.c:1060/1088/1114/1134, tb.c:1906.
25. **`tb_dp_bandwidth()`: rate × lanes and the encoding factors** — tunnel.c:764, `tb_dp_is_uhbr_rate` 699.
26. **Bandwidth groups** — tb.h:238, tb.c:1580-1692, `MAX_GROUPS`.
27. **The 10-second group reservation** — tb.c:2616-2646, 1532/1543/1567, `TB_RELEASE_BW_TIMEOUT`.
28. **Estimated-bandwidth recalculation** — tb.c:1432/1515, `usb4_dp_port_set_estimated_bandwidth`.
29. **Available/maximum/consumed bandwidth along a path** — tb.c:551/605/707/815, guard band, 120000 seed.
30. **Asymmetric link configuration (USB4 v2)** — tb.c:675/1039/1147/1543, `TB_ASYM_MIN`, `asym_threshold`.
31. **The DP bandwidth request handler** — tb.c:2538/2736/2868, retries, `TB_BW_ALLOC_RETRIES`.
32. **DP resources, IN↔OUT pairing and DP OUT reuse** — tb.c:111-181/1863/1971/2063.
33. **DP redrive mode** — tb.c:2104-2176, `QUIRK_KEEP_POWER_IN_DP_REDRIVE`.
34. **DMA tunnels and XDomain path approval** — tunnel.c:1903/1981, tb.c:2319/2368, xdomain.c:2439/2470.
35. **DMA credit reservation and release** — tunnel.c:1754/1767/1858/1878, `port->dma_credits`.
36. **Tunnel discovery at probe and after hibernate** — tb.c:376/1694/3169.
37. **Tunnels across suspend/resume and runtime PM** — tb.c:2941/3077/3141/3232/3263.
38. **Tunnel teardown on unplug** — tb.c:1722/1775/1790, hotplug branch 2458-2502.
39. **TMU accuracy and CLx around DP tunnels** — tb.c:184/235/254/281, 1109-1129.
40. *(not in the request)* **`tb_tunnel_reserved_pci()`: the USB4 v2 PCIe bulk reserve** — tunnel.c:585, `USB4_V2_PCI_MIN_BANDWIDTH`.
41. *(not in the request)* **Path PM packet support (`pmps`) on USB4 v2** — tunnel.c:168, path.c:544.
42. *(not in the request)* **`tb_tunnel_match_dma()` and multi-tunnel XDomain connections** — tunnel.c:1981.
43. *(not in the request)* **The `/dev/tbstreamX` device model (USB4STREAM)** — stream.c, configfs.c.

#### 7. TRACING — VERIFIED NEGATIVE
`grep -rn "trace_\|tracepoint" drivers/thunderbolt/path.c drivers/thunderbolt/tunnel.c drivers/thunderbolt/tb.c` → **no matches**. The only tracepoints in the subsystem are control-packet events defined in drivers/thunderbolt/trace.h and emitted from drivers/thunderbolt/ctl.c only: `CREATE_TRACE_POINTS` ctl.c:18, `trace_tb_tx` ctl.c:388, `trace_tb_event` ctl.c:405, `trace_tb_rx` ctl.c:512. Path/tunnel/credit/bandwidth code has zero tracepoints; register traffic is observable only indirectly through the ctl.c tracepoints.

#### 8. DEBUG AND DIAGNOSTIC PRINTING
- Macros in play: `tb_dbg/tb_warn/tb_info/tb_err/tb_WARN` tb.h:728-732; `tb_sw_dbg/warn/info` via `__TB_SW_PRINT` tb.h:734; `tb_port_dbg/warn/info` via `__TB_PORT_PRINT` (tb.h, same block); `tb_tunnel_WARN/warn/info/dbg` via `__TB_TUNNEL_PRINT` tunnel.h:224/236/238/240/242 (prefix `"%llx:%u <-> %llx:%u (%s): "`). **There is no `tb_path_dbg`** — path.c uses `tb_dbg`, `tb_port_dbg`, `tb_port_warn`, `tb_warn`, `tb_WARN`.
- Per-file counts (v7.2): path.c — 11 dbg, 7 warn/info, 2 `tb_WARN`; tunnel.c — 32 dbg, 12 warn/info, 10 `WARN`/`WARN_ON`/`WARN_ON_ONCE`/`tb_tunnel_WARN`; tb.c — 72 dbg, 37 warn/info, 6 `WARN_ON`.
- Structured dumps: `tb_dump_hop` path.c:16 (called from `tb_path_discover` :199 and `tb_path_activate` :575); `tb_dp_dump` tunnel.c:1536 (DP IN/OUT/reduced bandwidth after discovery).
- Control knobs: `CONFIG_DYNAMIC_DEBUG` (everything is `dev_dbg`-backed), module params `dprx_timeout`/`dma_credits`/`bw_alloc_mode` (tunnel.c:86/92/97) and `asym_threshold` (tb.c:47), plus the debugfs `path`/`counters` files (see §10).

#### 9. ASYNCHRONOUS / DEFERRED / LAZY PROCESSING
- **`dprx_work`** (`struct delayed_work` tunnel.h:106): initialized `INIT_DELAYED_WORK(&tunnel->dprx_work, tb_dp_dprx_work)` tunnel.c:1721; queued with delay 0 from `tb_dp_dprx_start` tunnel.c:1126 and re-queued at `TB_DPRX_POLL_DELAY` (50 ms) from within the handler tunnel.c:1098; handler `tb_dp_dprx_work` tunnel.c:1088 runs on `tb->wq`, takes `tb->lock`, polls `DP_COMMON_CAP_DPRX_DONE` for `TB_DPRX_WAIT_TIMEOUT` (25 ms) per pass until `tunnel->dprx_timeout` (default 12 s); cancelled by `tb_dp_dprx_stop` tunnel.c:1139.
- **DP bandwidth request work** (`struct tb_hotplug_event.work`, tb.c:78): queued by `tb_queue_dp_bandwidth_request` tb.c:2868 (`queue_delayed_work(tb->wq, …, delay)`) from `tb_handle_notification` tb.c:2902 (delay 0, retry 0) and from the handler itself for retries (delay 50 ms, tb.c:2833-2836, up to `TB_BW_ALLOC_RETRIES`); handler `tb_handle_dp_bandwidth_request` tb.c:2736 on `tb->wq` under `tb->lock`.
- **Bandwidth-group `release_work`** (tb.h:243): `INIT_DELAYED_WORK(..., tb_bandwidth_group_release_work)` tb.c:1590; armed/rearmed via `mod_delayed_work(system_percpu_wq, &group->release_work, msecs_to_jiffies(TB_RELEASE_BW_TIMEOUT))` tb.c:2644 (10 s) — note it runs on `system_percpu_wq`, not `tb->wq`; handler tb.c:1567 takes `tb->lock`; cancelled at tb.c:1688 (`tb_detach_bandwidth_group`) and `cancel_delayed_work_sync` for all groups in `tb_deinit` tb.c:2971.
- **`tcm->remove_work`** (tb.h/tb.c:68): `INIT_DELAYED_WORK` tb.c:3393, queued 50 ms after runtime resume tb.c:3283, handler `tb_remove_work` tb.c:3250 (`tb_free_unplugged_children` under `tb->lock`), cancelled in `tb_stop` tb.c:2947.
- **Hotplug work** (reached, owned by another area): `tb_queue_hotplug` tb.c:93 → `tb_handle_hotplug` tb.c:2421 — the entry point for `tb_free_invalid_tunnels`, `tb_dp_resource_available/unavailable`, `tb_scan_port`.
- **Polling loops in this area**: hop drain 500 ms / `usleep_range(10,20)` path.c:401-431; PCIe LTSSM Detect 500 ms / `fsleep(50)` tunnel.c:295-307; DP CM handshake 3000 ms / `usleep_range(100,150)` tunnel.c:627-655; DPRX done poll (`tb_dp_wait_dprx`) caller-supplied timeout / `usleep_range(100,150)` tunnel.c:1062-1082; DPTX ack clear 500 ms / `usleep_range(50,100)` usb4.c:3012-3023; USB3 CM request `usb4_port_wait_for_bit` 1500 ms / 50 µs usb4.c:2253-2255.
- **Sleeps in the resume path**: `msleep(usb3_delay)` (500 ms) tb.c:3181, `msleep(100)` tb.c:3193.
- **Completions — verified negative**: `grep -n "completion\|complete(\|wait_for_completion" path.c tunnel.c tb.c` matches only `tb_complete()` tb.c:3219, which is the `cm_ops->complete` PM callback, not a `struct completion`. (`struct completion` in this area exists only in dma_test.c:108.)
- **Timers / hrtimers / RCU callbacks / tasklets — verified negative** in path.c, tunnel.c, tb.c.

#### 10. SUBSYSTEM-SPECIFIC DEBUGGING INFRASTRUCTURE
- **debugfs path dump**: `path_show_one` debugfs.c:2241, `path_show` debugfs.c:2261 (walks hop 0 for NHI/lane adapters, then `TB_PATH_MIN_HOPID..max_in_hop_id`), `DEBUGFS_ATTR_RW(path)` debugfs.c:2300, registered `debugfs_create_file("path", 0400, …)` debugfs.c:2443. Write side `path_write` debugfs.c:282 → `path_write_one` debugfs.c:207 (read-modify-write of the 2-dword entry), gated by `CONFIG_USB4_DEBUGFS_WRITE` (`#define path_write NULL` at debugfs.c:449 otherwise). Counters: `counters_show` debugfs.c:2324, `port_clear_all_counters` debugfs.c:1878, `DEBUGFS_ATTR_RW(counters)` debugfs.c:2354, `debugfs_create_file("counters", 0600, …)` debugfs.c:2446. `PATH_LEN 2` debugfs.c:36, `COUNTER_SET_LEN 3` debugfs.c:38.
- **Tunnel uevents**: `tb_tunnel_event()` tunnel.c:241 emits `TUNNEL_EVENT=` + `TUNNEL_DETAILS=` via `tb_domain_event`; call sites `tb_tunnel_set_active` tunnel.c:278/282, `tb_tunnel_changed` tunnel.c:289 (from `tb_tunnel_alloc_bandwidth` 2583), `tb_tunnel_usb3` tb.c:965 (`TB_TUNNEL_LOW_BANDWIDTH`), `tb_tunnel_one_dp` tb.c:2021 and `tb_alloc_dp_bandwidth` tb.c:2730 (NO_BANDWIDTH).
- **dma_test debugfs** (`CONFIG_USB4_DMA_TEST`, Kconfig:54, depends on DEBUG_FS): `DMA_TEST_DEBUGFS_ATTR` dma_test.c:361; files created in `dma_test_probe` dma_test.c:627-636 under `svc->debugfs_dir/dma_test`: `lanes`, `speed`, `packets_to_receive`, `packets_to_send`, `status` (0400), `test` (0200).
- **KUnit tests** (`CONFIG_USB4_KUNIT_TEST`, Kconfig:49, `depends on USB4 && KUNIT=y`), drivers/thunderbolt/test.c, case list `tb_test_cases[]` at test.c:3097ff:
  - *Path walking*: `tb_test_path_basic` :423, `_not_connected_walk` :440, `_single_hop_walk` :479, `_daisy_chain_walk` :533, `_simple_tree_walk` :592, `_complex_tree_walk` :655, `_max_length_walk` :739.
  - *Path allocation / lane selection*: `tb_test_path_not_connected` :842, `_not_bonded_lane0` :870, `_not_bonded_lane1` :928, `_not_bonded_lane1_chain` :990, `_not_bonded_lane1_chain_reverse` :1070, `_mixed_chain` :1150, `_mixed_chain_reverse` :1242.
  - *Tunnels*: `tb_test_tunnel_pcie` :1334, `_dp` :1389, `_dp_chain` :1427, `_dp_tree` :1473, `_dp_max_length` :1523, `_3dp` :1603, `_usb3` :1669, `_port_on_path` :1724, `_dma` :1790, `_dma_rx` :1833, `_dma_tx` :1870, `_dma_chain` :1907, `_dma_match` :1973.
  - *Credits*: `tb_test_credit_alloc_legacy_not_bonded` :2024, `_legacy_bonded` :2057, `_pcie` :2090, `_without_dp` :2123, `_dp` :2173, `_usb3` :2217, `_dma` :2250, `_dma_multiple` :2286, `_all` :2577.
  - (Property-parser tests :2667-3055 belong to another area.) v7.2 addition touching this area: 168479c9bf07 "test: Release third DP tunnel" fixes a leak in `tb_test_tunnel_3dp`.
- **ConfigFS** (`CONFIG_USB4_CONFIGFS`, Kconfig:21): configfs.c:35 `tb_configfs_register_group`, :45 unregister, :51/:58 init/exit; consumed by stream.c:1666.

#### 11. v7.0 → v7.2 DRIFT (`git log/diff --oneline v7.0..v7.2 -- <area paths>`)
Diffstat: path.c +65/-, tunnel.c 45, tunnel.h 5, tb.c 88, tb.h 26, tb_regs.h 19, usb4.c 35, switch.c 107, xdomain.c 325, dma_test.c 25, debugfs.c 18, test.c 249, stream.c 1698 (new), configfs.c 61 (new).

Area-relevant commits and what a v7.0-era page would now misstate:
- **c3e7cc8bc5ca** "Use kzalloc_flex() for struct tb_path allocation" — `struct tb_path.hops` moved from `struct tb_path_hop *hops` (tb.h v7.0:443) to `struct tb_path_hop hops[] __counted_by(path_length)` (tb.h:446); `path_length` is now assigned *before* the array is used; `tb_path_free()` no longer does `kfree(path->hops)` (path.c:362). A page saying "the path and its hop array are two allocations" is now wrong. [errata 2026-09-06, write time of tunnel/path-model.md: `git describe --contains c3e7cc8bc5ca` prints v7.1-rc1~82^2~10^2~1, so the flexible `hops[]` array and the single allocation first shipped in v7.1, inside this ledger's v7.0 → v7.2 window; a page states v7.1 as the landing version.]
- **498c05821bb4** "tunnel: Simplify allocation" — `struct tb_tunnel.paths` moved from `struct tb_path **paths` (tunnel.h v7.0:40) to `struct tb_path *paths[] __counted_by(npaths)` (tunnel.h:110); `tb_tunnel_alloc()` is a single `kzalloc_flex` (tunnel.c:183) and `tb_tunnel_destroy()` no longer frees `tunnel->paths` (tunnel.c:217). Field order in the kerneldoc moved `@paths` to last.
- **b69af182b556** "Activate path hops from source to destination" — `tb_path_activate()` loop reversed: `for (i = 0; i < path->path_length; i++)` (path.c:529) instead of `for (i = path_length-1; i >= 0; i--)`; rollback now `__tb_path_deactivate_hops(path, 0)` (path.c:579) instead of `(path, i)`; kerneldoc updated (path.c:487). Any page describing "hops are programmed last-first" is now wrong.
- **7e49bb89df86** "Avoid reserved fields in path config space for USB4 routers" — `tb_path_activate()` now reads the entry first (path.c:537-540) and skips `initial_credits`/`ingress_fc`/`ingress_shared_buffer` unless `tb_port_is_null(in_port) || !tb_switch_is_usb4(in_port->sw)` (path.c:564-570); `__tb_path_deactivate_hop()` gained the same `tb_port_is_null(port) ||` term (path.c:415, was `if (!tb_switch_is_usb4(port->sw))`). A page saying "the CM always writes Path Credits Allocated and IFC/ISE" is now wrong for USB4 protocol adapters.
- **69a7b98770b7** "Verify PCIe adapter in detect state before tunnel setup" — added `tb_pci_port_ltssm_state_detect` (tunnel.c:293), `tb_pci_pre_activate` (tunnel.c:312), wired as `tunnel->pre_activate` in `tb_tunnel_alloc_pci` only (tunnel.c:542, not in discover); added `usb4_pci_port_ltssm_state` (usb4.c:3162), prototype tb.h:1484, `enum tb_pcie_ltssm_state` tb_regs.h:481, `ADP_PCIE_CS_0_LTSSM_MASK` tb_regs.h:476. New failure mode: `tb_tunnel_pci` can now fail with `-ETIMEDOUT` before any path is programmed.
- **d2ee4d47aacb** "Fix bandwidth group reservation indexing" (Cc stable) — `int group_reserved[MAX_GROUPS + 1]` tb.c:612 (was `[MAX_GROUPS]`); before the fix group index 7 wrote one past the end and its reservation was never summed.
- **afe9021d63b4** "Improve multi-display DisplayPort tunnel allocation" — `tb_handle_dp_bandwidth_request()` now calls `tb_tunnel_dp(tb)` after `tb_recalc_estimated_bandwidth(tb)` on success (tb.c:2853-2854). Behavior change: a DP tunnel that previously failed for lack of bandwidth can be re-established when another display releases bandwidth.
- **6db21d817b43** "Add support for USB4STREAM" + **cba57ed6f1e7** "Add support for ConfigFS" — new DMA-tunnel consumer drivers/thunderbolt/stream.c and drivers/thunderbolt/configfs.c; new tb.h hooks `tb_configfs_init/exit` (tb.h:1562-1568); new Kconfig `USB4_CONFIGFS` (Kconfig:21) and `USB4_STREAM` (Kconfig:67); new ABI file Documentation/ABI/testing/configfs-thunderbolt_stream; new admin-guide section (thunderbolt.rst:376).
- **97b228e59674** "stream: Unmap buffers with mapped size", **168479c9bf07** "test: Release third DP tunnel" — bug fixes inside v7.2-new code.
- **7f35f42395fc** "dma_test: No need to store debugfs directory pointer" — `struct dma_test` lost its debugfs-dir member; `dma_test_probe` uses a local `debugfs_dir` (dma_test.c:627). A v7.0 page listing that field is stale.
- **cf0c38ee554c** "Don't create multiple DMA tunnels on firmware connection manager" — ICM-only, out of scope but adjacent to `tb_approve_xdomain_paths`.
- **c51777370ac2** "Let the service drivers configure interrupt throttling" — added `tb_ring_throttling()` usage in dma_test.c:158/186 and stream.c:584-585 (DMA-tunnel consumers).
- **No functional change** to the credit machinery, bandwidth groups (other than the indexing fix), asym/sym configuration, DP bandwidth allocation mode, or the DMA tunnel code between v7.0 and v7.2.

#### 12. DOCUMENTATION AND ABI
- Documentation/admin-guide/thunderbolt.rst:319 "Tunneling events" — documents `TUNNEL_EVENT=<EVENT>` / `TUNNEL_DETAILS=0:12 <-> 1:20 (USB3)` and all five event strings, and states TUNNEL_DETAILS is present only for the software CM (matches `tb_tunnel_event` tunnel.c:241 and `tb_event_names[]` tunnel.c:103).
- Documentation/admin-guide/thunderbolt.rst:352 "Networking over Thunderbolt cable" — the `thunderbolt-net` DMA-tunnel consumer.
- Documentation/admin-guide/thunderbolt.rst:376 "Streaming data directly over Thunderbolt cable" (new at v7.2) — `/sys/kernel/config/thunderbolt/stream`, `in_hopid`/`out_hopid` (`-1` = auto), `/dev/tbstreamX`.
- Documentation/ABI/testing/configfs-thunderbolt_stream (new at v7.2, 83 lines) — `<xdomain>.<service>` group, `$name` stream group, `index` (maps to `/dev/tbstreamX`), `in_hopid`, `out_hopid`, and the remaining attributes.
- Kerneldoc blocks in this area: **tb.h** — `struct tb_path_hop` :354, `enum tb_path_port` :392, `struct tb_path` :408, `struct tb_bandwidth_group` :222, `struct tb_port` :246 (credit/group fields), `struct tb_switch` credit fields :157-162, `tb_port_path_direction_downstream` :1113, `tb_for_each_port_on_path` :1133, `tb_for_each_upstream_port_on_path` :1145, `tb_path_for_each_hop` :1206. **tunnel.h** — `enum tb_tunnel_state` :21, `struct tb_tunnel` :33, `tb_tunnel_is_active` :142, `enum tb_tunnel_event` :199. **path.c** — `tb_path_discover` :80, `tb_path_alloc` :215, `tb_path_free` :339, `tb_path_deactivate_hop` :436, `tb_path_activate` :483, `tb_path_is_invalid` :592, `tb_path_port_on_path` :610. **tunnel.c** — `tb_available_credits` :119, `tb_tunnel_event` :227, `tb_tunnel_discover_pci` :441, `tb_tunnel_alloc_pci` :521, `tb_tunnel_reserved_pci` :570, `tb_dp_bandwidth_mode_maximum_bandwidth` :1185, `tb_tunnel_discover_dp` :1577, `tb_tunnel_alloc_dp` :1667, `tb_tunnel_alloc_dma` :1889, `tb_tunnel_match_dma` :1966, `tb_tunnel_discover_usb3` :2194, `tb_tunnel_alloc_usb3` :2295, `tb_tunnel_is_invalid` :2376, `tb_tunnel_activate` :2395, `tb_tunnel_deactivate` :2454, `tb_tunnel_port_on_path` :2478, `tb_tunnel_maximum_bandwidth` :2508, `tb_tunnel_allocated_bandwidth` :2531, `tb_tunnel_alloc_bandwidth` :2557, `tb_tunnel_consumed_bandwidth` :2590, `tb_tunnel_release_unused_bandwidth` :2632, `tb_tunnel_reclaim_available_bandwidth` :2657. **tb.c** — `struct tb_cm` :52, `tb_consumed_usb3_pcie_bandwidth` :535, `tb_consumed_dp_bandwidth` :586, `tb_maximum_bandwidth` :689, `tb_available_bandwidth` :794, `tb_configure_asym` :1022, `tb_configure_sym` :1134. **usb4.c** — `usb4_switch_credits_init` :748, `usb4_switch_query/alloc/dealloc_dp_resource` :889/:921/:950, `usb4_switch_map_pcie_down` :1004, `usb4_switch_map_usb3_down` :1037, `usb4_usb3_port_max_link_rate` :2197, `usb4_usb3_port_allocated/allocate/release_bandwidth` :2314/:2411/:2458, the `usb4_dp_port_*` block :2514-3120, `usb4_pci_port_set_ext_encapsulation` :3123, `usb4_pci_port_ltssm_state` :3155. **switch.c** — `tb_port_alloc_in/out_hopid` :790/:804, `tb_port_release_in/out_hopid` :818/:828, `tb_next_port_on_path` :845, `tb_port_update_credits` :1259, `tb_dp_port_hpd_clear` :1436, `tb_switch_query/alloc/dealloc_dp_resource` :3683/:3700/:3728. **dma_test.c** — `struct dma_test` :69. **stream.c** — `enum tbstream_frame_pdf` :78, `struct tbstream_frame` :90, `struct tbstream_ring` :106, `struct tbstream_dev` :120, `struct tbstream_group` :160, `struct tbstream` :179. **configfs.c** — `tb_configfs_register_group` :27, `tb_configfs_unregister_group` :41. **xdomain.c** — `tb_xdomain_enable_paths` :2425, `tb_xdomain_disable_paths` :2456. **domain.c** — `tb_domain_disconnect_pcie_paths` :748 (ICM-only in practice), `tb_domain_approve_xdomain_paths` :765, `tb_domain_disconnect_xdomain_paths` :794.

#### CONSUMER SUMMARIES

**dma_test.c** (`CONFIG_USB4_DMA_TEST`, tristate, `depends on DEBUG_FS`, Kconfig:54) — a `tb_service_driver` (`dma_test_driver` :696, id `TB_SERVICE("dma_test", 1)` :691) that loops DMA traffic between two hosts (or a crossed dongle). Object: `struct dma_test` :91 (svc, xd, `rx_ring`/`rx_hopid`, `tx_ring`/`tx_hopid`, packet counters, expected `link_speed`/`link_width`, `crc_errors`, `buffer_overflow_errors`, `result`, `error_code`, `struct completion complete`, `struct mutex lock`). Rings run in **frame mode**: `tb_ring_alloc_tx/rx(..., RING_FLAG_FRAME [| RING_FLAG_E2E])` :150/:176 with `tb_ring_throttling(ring, 128000)` :158/:186; SOF/EOF PDFs `DMA_TEST_PDF_FRAME_START/END` :22-25. Path setup is `tb_xdomain_enable_paths(dt->xd, tx_hopid, tx_ring->hop, rx_hopid, rx_ring->hop)` :197 and `tb_xdomain_disable_paths` :223 — i.e. it drives `tb_approve_xdomain_paths`/`tb_tunnel_alloc_dma`. Ring API: `tb_ring_alloc_tx/rx`, `tb_ring_start/stop/free`, `tb_ring_tx/rx`, `tb_ring_dma_device`, `tb_ring_throttling`. Control surface is debugfs only (`lanes`, `speed`, `packets_to_receive`, `packets_to_send`, `status`, `test`) created at :627-636. Limits: `DMA_TEST_TX_RING_SIZE 64`, `RX_RING_SIZE 256`, `FRAME_SIZE SZ_4K`, `MAX_PACKETS 1000` (:16-20).

**stream.c** (`CONFIG_USB4_STREAM`, tristate, `depends on USB4_CONFIGFS`, Kconfig:67; new at v7.2) — USB4STREAM: raw byte streams between two hosts over DMA tunnels, exposed as `/dev/tbstreamX` misc devices configured through ConfigFS. Objects: `struct tbstream` :187 (kref, `tb_service *svc`, list link — the physical connection), `struct tbstream_group` :172 (a `config_group` per remote host, `dev_list` of stream devices), `struct tbstream_dev` :140 (`config_group` + `struct miscdevice misc` + kref, `index`, `in_hopid`, `out_hopid`, `ring_size`, `throttling`, `users`, `closed`, `removed`, waitqueue, mutex, `tx_ring`/`rx_ring`), `struct tbstream_ring` :113 (`tb_ring *`, prod/cons, `frames[]`), `struct tbstream_frame` :98 (sdev, page, offset, completed, `struct ring_frame`). Device model: `config_group_init_type_name(&sdev->group, name, &tbstream_dev_type)` :1366, `misc.name = kasprintf("tbstream%d", index)` :1373 with `MISC_DYNAMIC_MINOR` :1374 and `tbstream_dev_fops` :889 (read_iter/write_iter/poll/open/release); root group registered via `tb_configfs_register_group(&tbstream_group)` :1666. Rings run in **frame mode**: `tb_ring_alloc_tx/rx(..., RING_FLAG_FRAME | RING_FLAG_E2E, e2e_tx_hop, sof_mask, eof_mask, ...)` :554/:568 with `sof_mask = BIT(TBSTREAM_FRAME_START)`, `eof_mask = BIT(TBSTREAM_DATA) | BIT(TBSTREAM_CLOSE)` :565-566; PDFs `enum tbstream_frame_pdf` :84. DMA tunnel setup `tb_xdomain_enable_paths(xd, out_hopid, tx_ring->hop, in_hopid, rx_ring->hop)` :577 / `tb_xdomain_disable_paths` :620. Ring API: `tb_ring_alloc_tx/rx`, `tb_ring_start/stop/flush/free`, `tb_ring_throttling`. Limits: `TBSTREAM_DEV_RING_SIZE 256`, `MIN 32`, `MAX 4096`, `THROTTLING 8192` ns, `MAX_THROTTLING 16776960` (:72-76).

### Area G: Power management, CLx, TMU, ACPI — COMPLETE (recorded 2026-09-04)

Scope note: software CM (`tb.c`) is the subject. ICM-only PM symbols are flagged **[ICM]**. Vendor/generation-specific material is flagged **[VENDOR]**.

#### 1. Core structs and fields

| Symbol | file:line | Role |
|---|---|---|
| `enum tb_switch_tmu_mode` | drivers/thunderbolt/tb.h:88 | 5 modes, ordered by accuracy (highest last): `OFF`, `LOWRES`, `HIFI_UNI`, `HIFI_BI`, `MEDRES_ENHANCED_UNI` (tb.h:89-93) |
| `struct tb_switch_tmu` | drivers/thunderbolt/tb.h:105 | Per-router TMU state; 4 fields only |
| `.cap` (int) | tb.h:106 | Offset of router TMU capability (`TB_SWITCH_CAP_TMU`), %0 if absent |
| `.has_ucap` (bool) | tb.h:107 | Router supports uni-directional mode (`TMU_RTR_CS_0_UCAP`) |
| `.mode` | tb.h:108 | Mode currently programmed in HW, relative to upstream link; don't-care for host router |
| `.mode_request` | tb.h:109 | Mode requested by `tb_switch_tmu_configure()`, applied by `tb_switch_tmu_enable()` |
| `sw->clx` (unsigned int) | tb.h:216 | CL-state mask on the router's **upstream link** (`TB_CL0S`/`TB_CL1`/`TB_CL2`); kerneldoc tb.h:163 |
| `sw->rpm` (bool) | tb.h:199 | Router supports runtime PM; gates `pm_runtime_enable()` in `tb_switch_add()` |
| `sw->rpm_complete` | tb.h:208 | Completion for runtime resume — **[ICM]** only (kerneldoc says so; used only in icm.c) |
| `sw->is_unplugged` | tb.h:193 | Set by `tb_sw_set_unplugged()`; short-circuits CLx disable and `tb_restore_children()` |
| `sw->quirks` | tb.h:209 | Holds `QUIRK_NO_CLX` / `QUIRK_KEEP_POWER_IN_DP_REDRIVE` / `QUIRK_FORCE_POWER_LINK_CONTROLLER` |
| `sw->cap_lp` | tb.h:192 | Low-power (CLx objection) cap offset — Titan Ridge **[VENDOR]** |
| `sw->cap_lc` / `sw->cap_vsec_tmu` | tb.h:191 / tb.h:190 | LC cap (wake/sleep) / TMU VSEC cap (pre-USB4 time-disruption + objections) |
| `port->redrive` (bool) | tb.h:304 | DP IN adapter is in redrive mode → holds a runtime-PM ref **[VENDOR: Barlow Ridge]** |
| `QUIRK_FORCE_POWER_LINK_CONTROLLER` | tb.h:24 | BIT(0) — keep LC awake during NVM update **[VENDOR: Dell WD19TB]** |
| `QUIRK_NO_CLX` | tb.h:26 | BIT(1) — disable CL states **[VENDOR: Intel Titan Ridge early FW, AMD YC/PS]** |
| `QUIRK_KEEP_POWER_IN_DP_REDRIVE` | tb.h:28 | BIT(2) — block RTD3 while in DP redrive **[VENDOR: Intel Barlow Ridge]** |
| `TB_WAKE_ON_CONNECT/DISCONNECT/USB4/USB3/PCIE/DP` | tb.h:458-463 | BIT(0)..BIT(5) wake-source mask |
| `TB_CL0S`/`TB_CL1`/`TB_CL2` | tb.h:466-468 | BIT(0)/BIT(1)/BIT(2) CL-state mask |
| `TB_AUTOSUSPEND_DELAY` | tb.h:550 | 15000 ms — single delay used by NHI, domain, router, USB4 port, retimer |
| `struct tb_cm` | drivers/thunderbolt/tb.c:64 | `.hotplug_active` (tb.c:67) gates hotplug work; `.remove_work` (tb.c:68) delayed cleanup after runtime resume |
| `struct tb_nhi` | include/linux/thunderbolt.h:518 | PM-relevant fields below |
| `nhi->going_away` | include/linux/thunderbolt.h:525 | Set in `nhi_resume_noirq()` when the controller vanished; makes ring start/stop no-ops (nhi.c:649, nhi.c:757) |
| `nhi->iommu_dma_protection` | include/linux/thunderbolt.h:526 | Set by `nhi_pci_check_iommu()`; exported as `domainX/iommu_dma_protection` |
| `nhi->domain_released` | include/linux/thunderbolt.h:530 | Completion waited on by `nhi_pci_remove()` (pci.c:492) — **new at v7.2** |
| `nhi->ops` | include/linux/thunderbolt.h:521 | `struct tb_nhi_ops` (nhi.h:56) with `.suspend_noirq/.resume_noirq/.runtime_suspend/.runtime_resume/.init/.shutdown` |
| `struct tb_nhi_pci` | drivers/thunderbolt/pci.c:31 | **New at v7.2** — wraps `tb_nhi` + `msix_ida`; PCI specifics live here |

#### 2. API families

**(S)** = static, **(E)** = extern within the module (no `EXPORT_SYMBOL` in this area except `tb_xdomain_type`).

##### CLx (drivers/thunderbolt/clx.c — file unchanged v7.0→v7.2)
| Symbol | file:line | Role / registers |
|---|---|---|
| `clx_enabled` module param `clx` | clx.c:14-16 | `bool 0444`, default true — global CLx kill switch |
| `clx_name()` (S) | clx.c:18 | Mask → "CL0s/CL1/CL2", "CL1/CL2", "CL0s/CL2", "CL0s/CL1", "CL0s", "disabled", "unknown" |
| `tb_port_pm_secondary_set()` (S) | clx.c:38 | RMW `LANE_ADP_CS_1_PMS` (BIT(30)) |
| `tb_port_pm_secondary_enable/disable()` (S) | clx.c:57 / clx.c:62 | Thin wrappers |
| `tb_port_clx_supported()` (S) | clx.c:68 | Refuses two single-lane links (`!bonded && dual_link_port`) and inter-domain (`port->xdomain`); then `usb4_port_clx_supported()` (USB4) or `tb_lc_is_clx_supported()` (TR); reads `LANE_ADP_CS_0_CL{0S,1,2}_SUPPORT` (BIT(26/27/28)) |
| `tb_port_clx_set()` (S) | clx.c:103 | RMW `LANE_ADP_CS_1_CL{0S,1,2}_ENABLE` (BIT(10/11/12)); `-EOPNOTSUPP` on empty mask |
| `tb_port_clx_disable/enable()` (S) | clx.c:132 / clx.c:137 | Wrappers |
| `tb_port_clx()` (S) | clx.c:142 | Read back enabled CL mask from `LANE_ADP_CS_1` |
| `tb_port_clx_is_enabled()` (E) | clx.c:173 | **No callers in-tree** (only prototype tb.h:1071) — dead API |
| `tb_switch_clx_is_supported()` (S) | clx.c:184 | `clx_enabled` && `!(quirks & QUIRK_NO_CLX)` && `!tb_switch_is_tiger_lake()` && (USB4 ‖ Titan Ridge) |
| `tb_switch_clx_init()` (E) | clx.c:211 | Reads current CL mask from both link ends into `sw->clx`; warns on mismatch; skips ICM and host router |
| `tb_switch_pm_secondary_resolve()` (S) | clx.c:240 | PMS set on upstream port, cleared on parent's downstream port |
| `tb_switch_mask_clx_objections()` (S) | clx.c:257 | **[VENDOR: Titan Ridge only]** — masks the other TBT port's objections via `sw->cap_lp + TB_LOW_PWR_C1_CL1`/`TB_LOW_PWR_C3_CL1` with `TB_LOW_PWR_C{0_PORT_B,1_PORT_A}_MASK` |
| `validate_mask()` (S) | clx.c:301 | CL1 requires CL0s |
| `tb_switch_clx_enable()` (E) | clx.c:321 | Full enable; CL2 requires `usb4_switch_version() >= 2` on **both** ends; rolls back on failure; sets `sw->clx \|= clx` |
| `tb_switch_clx_disable()` (E) | clx.c:398 | Disables all; **returns the disabled mask** (>0) so callers can restore; returns `clx` without touching HW if `sw->is_unplugged` |
| `tb_lc_is_clx_supported()` (E) | lc.c:259 | Pre-USB4 path: `TB_LC_LINK_ATTR_CPS` BIT(18) |
| `usb4_port_clx_supported()` (E) | usb4.c:1574 | USB4 path: `PORT_CS_18_CPS` BIT(10) |
| `quirk_clx_disable()` (S) | quirks.c:24 | **[VENDOR]** sets `QUIRK_NO_CLX` unless Titan Ridge NVM major ≥ 0x65; table entries quirks.c:69-70 (Intel TR DD bridge), quirks.c:113-116 (AMD 0x0438 0x0208–0x020b) |

##### CLx policy in tb.c
| Symbol | file:line | Role |
|---|---|---|
| `tb_enable_clx()` (S) | tb.c:184 | Walks up to **depth 1 only**; bails if a DMA tunnel crosses `tb_upstream_port(sw)`; tries `TB_CL0S\|TB_CL1\|TB_CL2` then falls back to `TB_CL0S\|TB_CL1`; `-EOPNOTSUPP` mapped to 0 |
| `tb_disable_clx()` (S) | tb.c:235 | Disables from `sw` up to host router; returns %true if anything was actually on |
| Call sites — disable | tb.c:1110 (`tb_configure_asym`), tb.c:1212 (`tb_configure_sym`), tb.c:2339 (`tb_approve_xdomain_paths`, DMA tunnel) [orchestrator note 2026-09-04: no such symbol at v7.2; the site is inside `tb_approve_xdomain_paths` (tb.c:2319), which takes `tb->lock` itself], switch.c:3653 (`tb_switch_suspend`), debugfs.c:1262 (lane margining) | Reasons: link-width transition, DMA/XDomain tunnel, suspend, margining [errata 2026-09-13, migration of clx-policy.md: the 2026-09-04 note spelled this `__tb_approve_xdomain_paths`, a name that occurs nowhere in the tree at v7.2, which is what kept the coverage rule firing on the row; the behaviour it names is covered under the undecorated symbol] |
| Call sites — enable | tb.c:1129, tb.c:1227, tb.c:1397 (`tb_scan_port`, skipped during discovery), tb.c:2362/2397 (XDomain DMA teardown) [errata 2026-09-10, write time of pm/clx-policy.md: only tb.c:2397 is the teardown, in `__tb_disconnect_xdomain_paths`; tb.c:2362 is the `err_clx` rollback of `tb_approve_xdomain_paths`], tb.c:3099 (`tb_restore_children`), debugfs.c:1310 | |

##### TMU (drivers/thunderbolt/tmu.c — file unchanged v7.0→v7.2)
| Symbol | file:line | Role / registers |
|---|---|---|
| `tmu_rates[]` (S) | tmu.c:14 | OFF=0, LOWRES=1000, HIFI_UNI=16, HIFI_BI=16, MEDRES_ENHANCED_UNI=16 |
| `tmu_params[]` (S) | tmu.c:22-38 | `{freq_meas_window, avg_const, delta_avg_const, repl_timeout, repl_threshold, repl_n, dirswitch_n}`; LOWRES `{30,4}`, HIFI_* `{800,8}`, ENHANCED `{800,4,0,3125,25,128,255}` |
| `tmu_mode_name()` (S) | tmu.c:40 | "off", "uni-directional, LowRes", "uni-directional, HiFi", "bi-directional, HiFi", "enhanced uni-directional, MedRes" |
| `tb_switch_tmu_enhanced_is_supported()` (S) | tmu.c:58 | `usb4_switch_version(sw) > 1` (USB4 v2) |
| `tb_switch_set_tmu_mode_params()` (S) | tmu.c:63 | `TMU_RTR_CS_0_FREQ_WIND_MASK`; `TMU_RTR_CS_15_{FREQ,DELAY,OFFSET,ERROR}_AVG_MASK`; v2 also `TMU_RTR_CS_18_DELTA_AVG_CONST_MASK` |
| `tb_switch_tmu_ucap_is_supported()` (S) | tmu.c:122 | `TMU_RTR_CS_0_UCAP` BIT(30) |
| `tb_switch_tmu_rate_read/write()` (S) | tmu.c:135 / tmu.c:149 | `TMU_RTR_CS_3_TS_PACKET_INTERVAL_MASK` GENMASK(31,16) |
| `tb_port_tmu_write()` (S) | tmu.c:166 | Generic RMW at `port->cap_tmu + offset` |
| `tb_port_tmu_set_unidirectional()` + `_enable/_disable` (S) | tmu.c:183, 195, 200 | `TMU_ADP_CS_3_UDM` BIT(29); no-op unless `sw->tmu.has_ucap` |
| `tb_port_tmu_is_unidirectional()` (S) | tmu.c:205 | Reads `TMU_ADP_CS_3_UDM` |
| `tb_port_tmu_is_enhanced()` (S) | tmu.c:218 | `TMU_ADP_CS_8_EUDM` BIT(15) |
| `tb_port_tmu_enhanced_enable()` (S) | tmu.c:232 | Sets/clears `TMU_ADP_CS_8_EUDM`; no-op on non-v2 |
| `tb_port_set_tmu_mode_params()` (S) | tmu.c:254 | `TMU_ADP_CS_8_REPL_{TIMEOUT,THRESHOLD}_MASK`, `TMU_ADP_CS_9_{REPL_N,DIRSWITCH_N}_MASK` |
| `tb_port_tmu_rate_write()` (S) | tmu.c:295 | `TMU_ADP_CS_9_ADP_TS_INTERVAL_MASK`; no-op on non-v2 |
| `tb_port_tmu_time_sync()` + `_enable/_disable` (S) | tmu.c:315, 322, 327 | `TMU_ADP_CS_6_DTS` BIT(1). **Note the inversion:** `_disable()` writes `time_sync=true` and `_enable()` writes `false` (DTS = *Disable* Time Sync) |
| `tb_switch_tmu_set_time_disruption()` (S) | tmu.c:332 | USB4: `TMU_RTR_CS_0_TD` BIT(27); pre-USB4: `sw->cap_vsec_tmu + TB_TIME_VSEC_3_CS_26`, bit `TB_TIME_VSEC_3_CS_26_TD` BIT(22) |
| `tmu_mode_init()` (S) | tmu.c:357 | Infers current mode from HW (enhanced ▸ ucap+rate ▸ any rate → HIFI_BI); seeds `mode_request = mode`, `has_ucap` |
| `tb_switch_tmu_init()` (E) | tmu.c:411 | Finds `TB_SWITCH_CAP_TMU` and per-port `TB_PORT_CAP_TIME1`; calls `tmu_mode_init()`; no HW writes; skips ICM |
| `tb_switch_tmu_post_time()` (E) | tmu.c:447 | Grandmaster time post; USB4 + non-host only; reads root `TMU_RTR_CS_1..3`, writes `TMU_RTR_CS_22/24/25`; brackets in time-disruption |
| `disable_enhanced()` (S) | tmu.c:540 | Rate 0 + EUDM clear on both ends; upstream errors ignored |
| `tb_switch_tmu_disable()` (E) | tmu.c:565 | Rate→0, DTS on both ends, per-mode teardown; host router only writes rate |
| `tb_switch_tmu_off()` (S) | tmu.c:627 | Rollback path when enabling fails |
| `tb_switch_tmu_enable_bidirectional()` (S) | tmu.c:668 | OFF → HIFI_BI |
| `tb_switch_tmu_disable_objections()` (S) | tmu.c:704 | **[VENDOR: Titan Ridge only]** — `TB_TIME_VSEC_3_CS_9_TMU_OBJ_MASK` + `TMU_ADP_CS_6_DISABLE_TMU_OBJ_CL1/CL2` |
| `tb_switch_tmu_enable_unidirectional()` (S) | tmu.c:732 | OFF → LOWRES/HIFI_UNI; writes **parent's** rate |
| `tb_switch_tmu_enable_enhanced()` (S) | tmu.c:775 | OFF → MEDRES_ENHANCED_UNI; router params, then up port, then down port |
| `tb_switch_tmu_change_mode()` / `_prev()` (S) | tmu.c:866 / tmu.c:820 | LOWRES/HIFI_UNI/HIFI_BI → other; rollback |
| `tb_switch_tmu_enable()` (E) | tmu.c:950 | Brackets everything in time-disruption set/clear; dispatches by (`mode`, `mode_request`); commits `sw->tmu.mode = mode_request` on success |
| `tb_switch_tmu_configure()` (E) | tmu.c:1034 | Validates mode vs `has_ucap` / v2-on-both-ends; sets `mode_request`; `-EOPNOTSUPP`/`-EINVAL` |
| `tb_switch_tmu_is_configured()` (inline) | tb.h:1052 | `sw->tmu.mode_request == mode` |
| `tb_switch_tmu_is_enabled()` (inline) | tb.h:1065 | `mode != OFF && mode == mode_request` |

##### TMU policy in tb.c
| Symbol | file:line | Role |
|---|---|---|
| `tb_increase_switch_tmu_accuracy()` (S) | tb.c:254 | Per-child: LOWRES → HIFI_UNI (if CL1 on) else HIFI_BI |
| `tb_increase_tmu_accuracy()` (S) | tb.c:281 | Called after DP tunnel creation (tb.c:389 discovery, tb.c:1943 setup); walks depth-1 children |
| `tb_switch_tmu_hifi_uni_required()` / `tb_tmu_hifi_uni_required()` (S) | tb.c:301 / tb.c:313 | Domain-wide scan for an existing HIFI_UNI requirement |
| `tb_enable_tmu()` (S) | tb.c:319 | Preference: `MEDRES_ENHANCED_UNI` → (CL1 on ? `HIFI_UNI`/`LOWRES` : `HIFI_BI`) → `HIFI_BI` fallback; then `disable → post_time → enable` |

##### System suspend
| Symbol | file:line | Role |
|---|---|---|
| `nhi_pm_ops` | nhi.c:1266 | **Non-static at v7.2**, declared nhi.h:39; consumed by `nhi_driver.driver.pm` (pci.c:597). Uses **explicit member init, not `SET_*_PM_OPS` macros** |
| `.suspend_noirq` → `nhi_suspend_noirq()` (S) | nhi.c:994 | `__nhi_suspend_noirq(dev, device_may_wakeup(dev))` |
| `__nhi_suspend_noirq()` (S) | nhi.c:975 | `tb_domain_suspend_noirq()` then `nhi->ops->suspend_noirq(nhi, wakeup)` |
| `.suspend` / `.poweroff` → `nhi_suspend()` (S) | nhi.c:1057 | `tb_domain_suspend()` → `cm_ops->suspend` — **[ICM] only**, `tb_cm_ops` has no `.suspend` |
| `.poweroff_noirq` → `nhi_poweroff_noirq()` (S) | nhi.c:1027 | `device_may_wakeup() && nhi_wake_supported()` |
| `nhi_wake_supported()` (S) | nhi.c:1013 | Reads `"WAKE_SUPPORTED"` device property; default true (S4 wake rail) |
| `tb_domain_suspend_noirq()` (E) | domain.c:528 | Under `tb->lock`: `cm_ops->suspend_noirq` then `tb_ctl_stop()` |
| `tb_suspend_noirq()` (S) | tb.c:3077 | `tb_disconnect_and_release_dp()` → `tb_switch_exit_redrive()` → `tb_switch_suspend(root, false)` → `hotplug_active = false` |
| `tb_disconnect_and_release_dp()` (S) | tb.c:2231 | Tears down **all DP tunnels** and drains `tcm->dp_resources`; PCIe/USB3/DMA tunnels are **kept** |
| `tb_switch_suspend()` (E) | switch.c:3641 | Per router (recursive, post-order): `tb_switch_clx_disable()` → `tb_plug_events_active(false)` → children → wake flags → `tb_switch_set_wake()` → `usb4_switch_set_sleep()` / `tb_lc_set_sleep()` |
| `tb_switch_set_wake()` (S) | switch.c:3492 | Dispatch: `usb4_switch_set_wake(sw, flags, runtime)` vs `tb_lc_set_wake(sw, flags)` |
| `usb4_switch_set_sleep()` (E) | usb4.c:507 | `ROUTER_CS_5_SLP` then waits `ROUTER_CS_6_SLPR`, 500 ms |
| `tb_lc_set_sleep()` (E) | lc.c:469 | **Pre-USB4 (gen ≥ 2)**: `TB_LC_SX_CTRL_SLP` BIT(31) per link controller |
| `nhi_shutdown()` (E) | nhi.c:1112 | `dev_WARN` on live rings, `nhi_disable_interrupts()`, `nhi->ops->shutdown` |
| `nhi_pci_shutdown()` (S) | pci.c:233 | Frees the MSI IRQ, flushes `interrupt_work`, `ida_destroy` |
| `nhi_driver.shutdown` | pci.c:596 | Aliased to `nhi_pci_remove` (pci.c:482), which does `pm_runtime_get_sync` + `dont_use_autosuspend` + `forbid`, `tb_domain_remove`, waits `domain_released`, `nhi_shutdown` |

##### System resume
| Symbol | file:line | Role |
|---|---|---|
| `.resume_noirq` / `.restore_noirq` → `nhi_resume_noirq()` (S) | nhi.c:1035 | If `!ops->is_present()` → `nhi->going_away = true`; else `ops->resume_noirq`; then `tb_domain_resume_noirq()` |
| `tb_domain_resume_noirq()` (E) | domain.c:556 | Under `tb->lock`: `tb_ctl_start()` then `cm_ops->resume_noirq` |
| `tb_resume_noirq()` (S) | tb.c:3141 | Non-USB4 host → `tb_switch_reset()`; `tb_switch_resume(root,false)`; `tb_free_invalid_tunnels`; `tb_free_unplugged_children`; `tb_free_unplugged_xdomains`; `tb_restore_children`; discover+tear-down firmware tunnels; re-activate own tunnels; `tb_switch_enter_redrive`; `hotplug_active = true` |
| `tb_switch_resume()` (E) | switch.c:3525 | UID re-check, `tb_switch_configure()`, `tb_switch_check_wakes()` (system only), `tb_switch_set_wake(sw,0,true)`, `tb_switch_tmu_init()`, per-port `tb_port_resume()` + `tb_wait_for_port(port,true)` + `tb_port_unlock()` + recurse |
| `tb_switch_check_wakes()` (S) | switch.c:3504 | Only when `device_may_wakeup(&sw->dev)` and router is USB4 |
| `usb4_switch_check_wakes()` (E) | usb4.c:163 | Reads `ROUTER_CS_6_WOPS/WOUS` (PCIe/USB3) and per-port `PORT_CS_18_WOU4S/WOCS/WODS`; calls `pm_wakeup_event()` on the USB4 port dev and the router dev |
| `tb_switch_configure()` (E) | switch.c:2607 | Rewrites `ROUTER_CS_1..4` (4 dwords), sets `plug_events_delay = 0xff`, then `usb4_switch_setup()` for USB4 |
| `usb4_switch_setup()` (E) | usb4.c:243 | `ROUTER_CS_5` UTO/PTO/HCO, clears `CNS`, then waits `ROUTER_CS_6_RR` 500 ms (**new at v7.2**) |
| `tb_restore_children()` (S) | tb.c:3091 | Skips unplugged; `tb_enable_clx()` → `tb_enable_tmu()` → `tb_switch_configuration_valid()` → per-port link width/`tb_switch_configure_link` → recurse; XDomain ports re-configured |
| `usb4_switch_configuration_valid()` (E) | usb4.c:316 | `ROUTER_CS_5_CV`, waits `ROUTER_CS_6_CR` 500 ms (was 50 ms at v7.0) |
| `tb_port_resume()` (S) | switch.c:1297 | `usb4_port_device_resume()` for USB4 ports; else `tb_port_start_lane_initialization()` |
| `usb4_port_device_resume()` (E) | usb4_port.c:363 | Re-applies offline mode only: `usb4->offline ? usb4_port_offline(usb4) : 0` |
| `usb4_port_offline()` (S) | usb4_port.c:76 | `tb_acpi_power_on_retimers` → `usb4_port_router_offline` → `tb_retimer_scan(port,false)` |
| `.complete` → `nhi_complete()` (S) | nhi.c:1064 | If runtime-suspended → `pm_runtime_resume(dev)`; else `tb_domain_complete()` |
| `tb_domain_complete()` (E) | domain.c:601 | → `cm_ops->complete` |
| `tb_complete()` (S) | tb.c:3219 | `tb_domain_unregister_unplugged_xdomains()`; if any, rescan under `scoped_guard(mutex, &tb->lock)` |
| Retimers | — | **No retimer resume callback.** `tb_retimer_scan()` is never called from a resume path (only tb.c:1332/1389/1410 scan, usb4_port.c:91/240). `tb_retimer_remove_all()` runs from `tb_free_unplugged_*`. `struct tb_retimer` has no `.pm` |

##### Freeze / thaw (hibernation)
| Symbol | file:line | Role |
|---|---|---|
| `nhi_freeze_noirq()` (S) | nhi.c:999 | → `tb_domain_freeze_noirq()`; comment at nhi.c:1269-1272: "we just disable hotplug, the pci-tunnels stay alive" |
| `nhi_thaw_noirq()` (S) | nhi.c:1006 | → `tb_domain_thaw_noirq()` |
| `tb_domain_freeze_noirq()` / `_thaw_noirq()` (E) | domain.c:574 / domain.c:588 | Under `tb->lock`: freeze = cm hook then `tb_ctl_stop()`; thaw = `tb_ctl_start()` then cm hook |
| `tb_freeze_noirq()` / `tb_thaw_noirq()` (S) | tb.c:3203 / tb.c:3211 | **Only toggle `tcm->hotplug_active`.** No router reset, no wake programming, no tunnel teardown |
| `.restore_noirq` | nhi.c:1274 | Aliased to `nhi_resume_noirq` — the full resume path handles firmware-created tunnels (tb.c:3163-3175) |

##### Runtime PM — NHI
| Symbol | file:line | Role |
|---|---|---|
| `nhi_runtime_suspend()` (S) | nhi.c:1079 | `tb_domain_runtime_suspend()` then `ops->runtime_suspend` |
| `nhi_runtime_resume()` (S) | nhi.c:1097 | `ops->runtime_resume` then `tb_domain_runtime_resume()` |
| `nhi_probe()` PM setup | nhi.c:1251-1256 | `device_wakeup_enable()`, `pm_runtime_allow()`, `set_autosuspend_delay(TB_AUTOSUSPEND_DELAY)`, `use_autosuspend()`, `put_autosuspend()` |
| `icl_nhi_suspend()` (S) | pci.c:374 | **[VENDOR: Ice Lake+]** — no-op if a device is connected; **[ICM]** LC mailbox handshake; then force-power off |
| `icl_nhi_suspend_noirq()` (S) | pci.c:397 | If `!pm_suspend_via_firmware()` → `icl_nhi_suspend()`; else **[ICM]** `ICL_LC_GO2SX` / `ICL_LC_GO2SX_NO_WAKE` |
| `icl_nhi_resume()` (S) | pci.c:413 | `icl_nhi_force_power(true)` + `icl_nhi_set_ltr()`; used as `.init`, `.resume_noirq`, `.runtime_resume` |
| `icl_nhi_force_power()` (S) | pci.c:283 | **[VENDOR]** `VS_CAP_22_FORCE_POWER` + DMA delay `0x22`; polls `VS_CAP_9_FW_READY` |
| `icl_nhi_set_ltr()` (S) | pci.c:362 | Copies `VS_CAP_16` max-LTR into snoop/no-snoop halves of `VS_CAP_15` |
| `icl_nhi_shutdown()` (S) | pci.c:425 | `nhi_pci_shutdown()` + force-power off |
| `icl_nhi_ops` | pci.c:432 | Bound to ICL/TGL/ADL/RPL/MTL/LNL/PTL/WCL device IDs (pci.c:537-577); **Barlow Ridge (pci.c:578-579) uses the default ops** |
| `pci_nhi_default_ops` | pci.c:254 | No PM hooks at all — generic USB4 hosts rely purely on the domain/CM path |

##### Runtime PM — domain
| Symbol | file:line | Role |
|---|---|---|
| `tb_domain_runtime_suspend()` (E) | domain.c:607 | `cm_ops->runtime_suspend` then `tb_ctl_stop()`. **Takes no lock** (the CM callback does) |
| `tb_domain_runtime_resume()` (E) | domain.c:618 | `tb_ctl_start()` then `cm_ops->runtime_resume` |
| `tb_runtime_suspend()` (S) | tb.c:3232 | Under `tb->lock`: `tb_disconnect_and_release_dp()` (DP resources only, for redrive re-entry) → `tb_switch_exit_redrive()` → `tb_switch_suspend(root, true)` → `hotplug_active = false` |
| `tb_runtime_resume()` (S) | tb.c:3263 | Under `tb->lock`: `tb_switch_resume(root,true)` → `tb_free_invalid_tunnels` → `tb_restore_children` → re-activate tunnels → `tb_switch_enter_redrive` → `hotplug_active = true`; then queues `remove_work` at 50 ms |
| `tb_remove_work()` (S) | tb.c:3250 | `tb_free_unplugged_children()` under lock, then `tb_free_unplugged_xdomains()` outside |
| `tb_domain_add()` PM setup | domain.c:476-483 | `device_init_wakeup(true)`, `pm_runtime_no_callbacks`, `set_active`, `enable`, `set_autosuspend_delay(15000)`, `mark_last_busy`, `use_autosuspend` |

##### Runtime PM — router / port / retimer
| Symbol | file:line | Role |
|---|---|---|
| `tb_switch_runtime_suspend()` / `_resume()` (S) | switch.c:2347 / switch.c:2358 | Thin shims to `cm_ops->runtime_suspend_switch` / `runtime_resume_switch` — **[ICM]-only hooks**; `tb_cm_ops` (tb.c:3287) does not set them, so these are no-ops for the software CM |
| `tb_switch_pm_ops` | switch.c:2368 | `SET_RUNTIME_PM_OPS(...)` — the **only** `SET_*_PM_OPS` macro in the router path |
| `tb_switch_type` | switch.c:2373 | `.pm = &tb_switch_pm_ops` |
| Router rpm policy — root | tb.c:3016 | `tb->root_switch->rpm = tb_switch_is_usb4(tb->root_switch)` ("All USB4 routers support runtime PM") |
| Router rpm policy — downstream | tb.c:1373 | `sw->rpm = sw->generation > 1` (TBT2 and later, i.e. routers with an LC) |
| Router rpm enable | switch.c:3400-3409 | `device_init_wakeup(true)` unconditionally; `pm_runtime_set_active()` always; the rest **only if `sw->rpm`**: autosuspend delay, `use_autosuspend`, `mark_last_busy`, `enable`, `pm_request_autosuspend` |
| Router rpm disable | switch.c:3436-3439 | `tb_switch_remove()`: if `sw->rpm` → `get_sync` + `disable` |
| `tb_enter_redrive()` / `tb_exit_redrive()` (S) | tb.c:2104 / tb.c:2129 | **[VENDOR: Barlow Ridge]** `pm_runtime_get(&sw->dev)` / `put()` to block RTD3 while a monitor is driven in redrive mode |
| `tb_switch_enter_redrive()` / `_exit_redrive()` (S) | tb.c:2147 / tb.c:2159 | Whole-router sweep; `exit` is the forced version used by suspend |
| `quirk_block_rpm_in_redrive()` (S) | quirks.c:49 | **[VENDOR]** sets `QUIRK_KEEP_POWER_IN_DP_REDRIVE` |
| USB4 port rpm | usb4_port.c:332-337 | `pm_runtime_no_callbacks`, `set_active`, `enable`, delay 15000, `mark_last_busy`, `use_autosuspend`; `device_set_wakeup_capable(true)` for non-upstream ports (usb4_port.c:329-330) |
| Retimer rpm | retimer.c:454-459 | Same six-call pattern; no `.pm` ops on `tb_retimer_type` |
| rpm ref pairs (sysfs/NVM/scan/hotplug) | switch.c:290, 1887, 2067; tb.c:1277, 1316, 1714, 2000, 2124, 2430, 2456, 2746; usb4_port.c:172, 226; retimer.c:46, 257; debugfs.c ×9 | All `get_sync … mark_last_busy + put_autosuspend` |

##### Wakes
| Symbol | file:line | Role |
|---|---|---|
| Runtime wake set | switch.c:3664-3668 | `CONNECT\|DISCONNECT\|USB4\|USB3\|PCIE\|DP` — **DP included** |
| System wake set | switch.c:3669-3672 | Gated on `device_may_wakeup(&sw->dev)`: `CONNECT\|DISCONNECT\|USB4\|USB3\|PCIE` — **DP excluded** |
| `usb4_switch_set_wake()` (E) | usb4.c:426 | Per lane-0 adapter: `PORT_CS_19_WOC/WOD/WOU4` (BIT(16/17/18)); upstream port always gets `WOU4`; downstream gates on `PORT_CS_19_PC` (configured) and per-port `device_may_wakeup` unless `runtime`. Device routers also `ROUTER_CS_5_WOP/WOU/WOD` (BIT(1/2/3)) |
| `usb4_switch_check_wakes()` (E) | usb4.c:163 | Status side: `ROUTER_CS_6_WOPS/WOUS`, `PORT_CS_18_WOCS/WODS/WOU4S` |
| `tb_lc_set_wake()` (E) | lc.c:428 | **Pre-USB4, gen ≥ 2, non-host only**; walks `nlc` link controllers from `TB_LC_DESC` |
| `tb_lc_set_wake_one()` (S) | lc.c:389 | `TB_LC_SX_CTRL` (0x96): `WOC`/`WOD` (both set by `TB_WAKE_ON_CONNECT`), `WOU4`, `WOP`, `WODPC\|WODPD`. **No LC status/check counterpart** |

##### LC (drivers/thunderbolt/lc.c — file unchanged v7.0→v7.2)
| Symbol | file:line | Role |
|---|---|---|
| `read_lc_desc()` (S) | lc.c:27 | `sw->cap_lc + TB_LC_DESC`; yields `NLC`, `SIZE`, `PORT_SIZE` for the per-LC stride |
| `tb_lc_set_wake()` / `tb_lc_set_sleep()` | lc.c:428 / lc.c:469 | See above; both require `sw->generation >= 2`; wake also requires `tb_route(sw)` |
| `tb_lc_force_power()` (E) | lc.c:712 | Writes 0xffff to `TB_LC_POWER` (0x740). **[VENDOR]** only reachable via `QUIRK_FORCE_POWER_LINK_CONTROLLER` → `nvm_authenticate_on_disconnect` sysfs (switch.c:2111, visibility switch.c:2270) |
| `tb_lc_configure_port()` / `_unconfigure_port()` | lc.c:141 / lc.c:154 | `TB_LC_SX_CTRL_L1C/L1D/L2C/L2D/UPSTREAM` — link state the LC needs for Sx, driven from link config not PM directly |
| `tb_lc_is_clx_supported()` | lc.c:259 | `TB_LC_LINK_ATTR_CPS` |
| LC register map used by PM | tb_regs.h:589-632 | `TB_LC_DESC` 0x02, `TB_LC_POWER` 0x740, `TB_LC_SX_CTRL` 0x96 (WOC/WOD/WODPC/WODPD/WOU4/WOP/L1C/L1D/L2C/L2D/SLI/UPSTREAM/SLP), `TB_LC_LINK_ATTR` 0x97 |

##### ACPI (drivers/thunderbolt/acpi.c — whole file behind `thunderbolt-${CONFIG_ACPI} += acpi.o`, Makefile:9)

[errata 2026-09-07, write time of adapter/usb4-port-device.md: the `acpi.o` line is drivers/thunderbolt/Makefile:8 on disk; line 9 is the `CONFIG_DEBUG_FS` line. The Context paragraph's Makefile citation of the build gates carries the same hint.]
| Symbol | file:line | Role |
|---|---|---|
| `tb_acpi_add_link()` (S) | acpi.c:14 | Per-node: `fwnode_find_reference(adev, "usb4-host-interface", 0)`; must resolve to `nhi->dev`; skips non-PCI (USB3 handled by USB core); accepts only `PCI_EXP_TYPE_ROOT_PORT`/`DOWNSTREAM`; `pm_runtime_get_sync` → `device_link_add(consumer=pdev, supplier=nhi->dev, AUTOREMOVE_SUPPLIER\|RPM_ACTIVE\|PM_RUNTIME)` → `pm_runtime_put` |
| `tb_acpi_add_links()` (E) | acpi.c:91 | `acpi_walk_namespace(ACPI_TYPE_DEVICE, ACPI_ROOT_OBJECT, 32, ...)`; caller tb.c:3403 (`tb_probe`, after `tb_apple_add_links`) |
| `tb_acpi_is_native()` (E) | acpi.c:122 | `osc_sb_native_usb4_support_confirmed && osc_sb_native_usb4_control`; caller nhi.c:1171 (`nhi_select_cm`) picks SW vs FW CM |
| `tb_acpi_may_tunnel_usb3/dp/pcie()` (E) | acpi.c:134 / 147 / 160 | `OSC_USB_USB3_TUNNELING` / `OSC_USB_DP_TUNNELING` / `OSC_USB_PCIE_TUNNELING`; return true when not native |
| `tb_acpi_is_xdomain_allowed()` (E) | acpi.c:173 | `OSC_USB_XDOMAIN`; callers xdomain.c:87 (`tb_xdomain_enabled &&`) and tunnel.c:137 |
| ACPI-core seam — `_OSC` support | drivers/acpi/bus.c:485-486, 508 | `OSC_SB_NATIVE_USB4_SUPPORT` (0x00040000, include/linux/acpi.h:611) offered only `IS_ENABLED(CONFIG_USB4)`; result → `osc_sb_native_usb4_support_confirmed` (bus.c:442, exported bus.c:443) |
| ACPI-core seam — USB4 `_OSC` control | drivers/acpi/bus.c:529-553 | UUID `23A0D13A-26AB-486C-9C5F-0FFA525A575A`; requests all four bits (bus.c:541-542); result → `osc_sb_native_usb4_control` (bus.c:517, exported bus.c:518); called from `acpi_bus_init()` at bus.c:1514 (after `acpi_bus_osc_negotiate_platform_control()` at bus.c:1513) |
| Bit definitions | include/linux/acpi.h:623-626 | `OSC_USB_USB3_TUNNELING` 0x1, `DP` 0x2, `PCIE` 0x4, `XDOMAIN` 0x8 |
| `retimer_dsm_guid` | acpi.c:181-183 | `e0053122-795b-4122-8a5e-57be1d26acb3`; functions 1 = `QUERY_ONLINE_STATE`, 2 = `SET_ONLINE_STATE` (acpi.c:185-186) |
| `tb_acpi_retimer_set_power()` (S) | acpi.c:188 | Gated on `usb4->can_offline`; `WARN_ON(!adev)`; query, compare, then `acpi_evaluate_dsm_typed()` with a 1-element package; `-EBUSY` means the Type-C port is in non-USB4/TBT mode |
| `tb_acpi_power_on_retimers()` / `_off_retimers()` (E) | acpi.c:263 / acpi.c:277 | Callers usb4_port.c:81, 87, 94, 105. **Uses `_DSM`, not `_PR3` / `acpi_device_power_add_dependent`** |
| `tb_acpi_bus_match()` (S) | acpi.c:282 | `tb_is_switch(dev) \|\| tb_is_usb4_port_device(dev)` |
| `tb_acpi_switch_find_companion()` (S) | acpi.c:287 | Device router: `acpi_find_child_by_adr(parent_sw companion, port->port)` then `acpi_find_child_device(port_adev, 0, false)`; host router: `acpi_find_child_device(ACPI_COMPANION(nhi->dev), 0, false)` |
| `tb_acpi_find_companion()` (S) | acpi.c:316 | Namespace shape documented acpi.c:319-329 (NHI ▸ HR `_ADR 0` ▸ DFP `_ADR = lane-0 adapter` ▸ DR `_ADR 0` ▸ UFP) |
| `tb_acpi_setup()` (S) | acpi.c:339 | `acpi_check_dsm()` for both retimer functions → `usb4->can_offline = true` |
| `tb_acpi_bus` | acpi.c:353 | `struct acpi_bus_type{ .name="thunderbolt", .match, .find_companion, .setup }` |
| `tb_acpi_init()` / `tb_acpi_exit()` (E) | acpi.c:360 / acpi.c:365 | `register_acpi_bus_type()` / `unregister_acpi_bus_type()`. **No ACPI notifier, no `_OSC` evaluation here** — `_OSC` is done entirely by the ACPI core. Callers domain.c:892, 906, 918 |
| `!CONFIG_ACPI` stubs | tb.h:1523-1536 | `tb_acpi_add_links` → false; `is_native`/`may_tunnel_*`/`is_xdomain_allowed` → **true**; `init` → 0; `exit`/`power_{on,off}_retimers` → 0 |
| DMA-protection seam | pci.c:68-109 | `nhi_pci_check_iommu_pdev()` (pci.c:68): `pdev->external_facing && device_iommu_capable(IOMMU_CAP_PRE_BOOT_PROTECTION)`; `nhi_pci_check_iommu()` (pci.c:77) walks the whole root bus, sets `nhi->iommu_dma_protection`; called at pci.c:475 |
| `ExternalFacingPort` seam | drivers/pci/pci-acpi.c:1416-1431 | `pci_acpi_set_external_facing()` reads the `"ExternalFacingPort"` property on root ports → `dev->external_facing = 1`; invoked from `pci_acpi_setup()` (drivers/pci/pci-acpi.c:1438). DT counterpart: `"external-facing"` at drivers/pci/of.c:61-62. IOMMU consumer: `has_external_pci()` at drivers/iommu/intel/iommu.c:2470-2481 |

#### 3. Lifecycle and locking

- **System suspend chain:** `nhi_pm_ops.suspend_noirq` (nhi.c:1267) → `nhi_suspend_noirq` (nhi.c:994) → `__nhi_suspend_noirq` (nhi.c:975) → `tb_domain_suspend_noirq` (domain.c:528, **takes `tb->lock`**) → `tb_cm_ops.suspend_noirq` = `tb_suspend_noirq` (tb.c:3077) → `tb_switch_suspend` (switch.c:3641, recursive, **called with `tb->lock` held**) → `tb_switch_set_wake` → `usb4_switch_set_sleep`/`tb_lc_set_sleep`. Back in domain.c: `tb_ctl_stop()`. Back in nhi.c: `nhi->ops->suspend_noirq(nhi, wakeup)`.
- **System resume chain:** `nhi_resume_noirq` (nhi.c:1035) → `ops->is_present` check (sets `going_away`) / `ops->resume_noirq` → `tb_domain_resume_noirq` (domain.c:556, **takes `tb->lock`**) → `tb_ctl_start()` → `tb_resume_noirq` (tb.c:3141) → `tb_switch_resume` (switch.c:3525) → `tb_restore_children` (tb.c:3091). Then `.complete` → `nhi_complete` (nhi.c:1064) → `tb_domain_complete` → `tb_complete` (tb.c:3219), which takes `tb->lock` itself via `scoped_guard`.
- **Runtime chain:** `nhi_runtime_suspend` (nhi.c:1079) → `tb_domain_runtime_suspend` (domain.c:607, **no lock**) → `tb_runtime_suspend` (tb.c:3232, **takes `tb->lock` itself**) → `tb_ctl_stop()`. Resume is the mirror: `ops->runtime_resume` → `tb_ctl_start()` → `tb_runtime_resume` (tb.c:3263, takes lock).
- **Lock asymmetry to document:** the `*_noirq` domain entries hold `tb->lock` around the CM callback; the runtime entries do not, so `tb_runtime_suspend`/`tb_runtime_resume` take it themselves.
- **pm_runtime reference model:** NHI is a supplier; ACPI device links (acpi.c:60) and Apple PCI links (tb.c:3355) make tunnelled PCIe root/downstream ports consumers with `DL_FLAG_PM_RUNTIME`, so NHI cannot RTD3 while a consumer is active. Within the domain: `tb->dev` has `pm_runtime_no_callbacks` (domain.c:478) and is bumped by the hotplug/DP-bandwidth workers (tb.c:2430, tb.c:2746). Router refs are taken around scan (tb.c:1277), hotplug (tb.c:2456), sysfs stores (switch.c:290/1887/2067), DP tunnel lifetime (tb.c:2000-2001 held until teardown at tb.c:2057-2060) and redrive (tb.c:2124/2142/2172).
- **CLx state machine:** `sw->clx` starts from HW at `tb_switch_clx_init` (clx.c:211, from `tb_switch_add` switch.c:3356). `tb_switch_clx_enable` ORs in (clx.c:383); `tb_switch_clx_disable` zeroes (clx.c:424) and **returns the previous mask** so `tb_configure_asym`/`tb_configure_sym` can restore. Suspend clears it (switch.c:3653), resume re-derives it via `tb_switch_clx_init` inside `tb_switch_add`? — no: on resume `sw->clx` is left at 0 by the suspend-time disable and re-established by `tb_enable_clx` from `tb_restore_children` (tb.c:3099).
- **TMU state machine:** `mode` (HW truth) and `mode_request` (target) are seeded equal by `tmu_mode_init` (tmu.c:395). `tb_switch_tmu_configure` only moves `mode_request` (tmu.c:1068). `tb_switch_tmu_enable` commits `mode = mode_request` on success (tmu.c:1013) and leaves them divergent on failure (so `tb_switch_tmu_is_enabled` reports false). `tb_switch_tmu_disable` forces `mode = OFF` (tmu.c:620) without touching `mode_request`.
- **Parent/child split:** uni-directional and enhanced modes program the **parent's** rate (tmu.c:739, tmu.c:882) and the child's upstream adapter; bi-directional programs the child's own rate (tmu.c:684, tmu.c:891). Host router only ever writes its own rate (tmu.c:1006) — its adapters are programmed as part of the child's configuration.
- **Ordering constraint:** `tb_switch_configuration_valid()` must run **after** TMU enable on the upstream port (comment tb.c:1403-1406, applied at tb.c:1407 and tb.c:3105).

#### 4. Hard-coded limits

| Value | file:line | Meaning |
|---|---|---|
| `15000` ms | tb.h:550 | `TB_AUTOSUSPEND_DELAY`, used at nhi.c:1254, domain.c:481, switch.c:3404, usb4_port.c:335, retimer.c:457 |
| `100` retries, `usleep_range(5, 10)` | tmu.c:453, tmu.c:521 | TMU post-time convergence poll (≈0.5–1 ms total) → `-ETIMEDOUT` (tmu.c:529) |
| `0xffffffff00000001ULL` | tmu.c:509 | Post Time Low=1 / High=0xffffffff magic write |
| `32` | acpi.c:103 | `acpi_walk_namespace` max depth |
| `500` ms | usb4.c:524 | `ROUTER_CS_6_SLPR` sleep-ready wait in `usb4_switch_set_sleep` |
| `500` ms | usb4.c:302 | `ROUTER_CS_6_RR` Router Ready wait (**new at v7.2**) |
| `500` ms | usb4.c:335 | `ROUTER_CS_6_CR` Configuration Ready wait (**was 50 ms at v7.0**) |
| `usleep_range(50, 100)` | switch.c:1739 | `tb_switch_wait_for_bit()` poll interval |
| 10 retries × `msleep(100)` | switch.c:500, 523, 548 | `tb_wait_for_port()` — 1 s link-up wait, used by `tb_switch_resume` (switch.c:3592) |
| `500` ms | tb.c:3172 | `usb3_delay` before re-activating the first USB3 tunnel on resume |
| `100` ms | tb.c:3193 | Post-tunnel-restart settle ("the pcie links need some time to get going") |
| `50` ms | tb.c:3283 | `remove_work` delay after runtime resume |
| `ICL_LC_MAILBOX_TIMEOUT 500` ms, `usleep_range(1000,1100)` | pci.c:266, pci.c:346-351 | **[VENDOR/ICM]** LC mailbox completion |
| `350` retries × `usleep_range(3000, 3100)` ≈ 1.05 s | pci.c:311, pci.c:319 | **[VENDOR]** force-power `VS_CAP_9_FW_READY` wait |
| `0x22` | pci.c:303 | **[VENDOR]** `VS_CAP_22` DMA delay field value |
| `msleep(100)` + 500 ms + `usleep_range(10,20)` | nhi.c:1148, 1150, 1157 | Host router reset in `nhi_reset()` (gated by `host_reset` module param, nhi.c:40) |
| `0xff` | switch.c:2620 | Notification Timeout (`plug_events_delay`) = 255 ms for all routers (**moved/changed at v7.2**) |
| `XDOMAIN_SHORT_TIMEOUT 100` ms | xdomain.c:23 | Delay used by `start_handshake()` (xdomain.c:741) on XDomain resume |
| TMU tuning constants | tmu.c:14-38 | Rates 0/1000/16/16/16; params `{30,4}`, `{800,8}`, `{800,4,0,3125,25,128,255}` |

#### 5. Version-specific facts at v7.2

- `struct tb_nhi` lost `pdev`; every PM/ACPI consumer now uses `nhi->dev` (`struct device *`). All `tb_err/tb_warn/tb_info/tb_dbg/tb_WARN` macros re-pointed (tb.h:728-732).
- `struct tb_nhi_pci` (pci.c:31) is new; `struct tb_nhi_ops` gained `.pre_nvm_auth`, `.post_nvm_auth`, `.request_ring_irq`, `.release_ring_irq`, `.is_present`, `.init_interrupts` (nhi.h:56-70).
- `nhi_pm_ops` became **non-static** (nhi.c:1266) and is declared in nhi.h:39; the `struct pci_driver` that consumes it now lives in pci.c:591-598.
- `nhi_probe()` / `nhi_shutdown()` are now module-internal exports (nhi.h:37-38) taking `struct tb_nhi *`; the PCI-side `nhi_pci_probe`/`nhi_pci_remove` are new (pci.c:447 / pci.c:482).
- `nhi_wake_supported()` signature changed `struct pci_dev *` → `struct device *` (nhi.c:1013).
- `nhi->domain_released` completion is new; `nhi_pci_remove()` and the `tb_domain_add()` failure path wait on it (pci.c:492, nhi.c:1245).
- `tb_domain_unregister_unplugged_xdomains()` is new (domain.c:874, prototype tb.h:796); `tb_complete()` uses it in place of the old in-tb.c `tb_free_unplugged_xdomains()` return count.
- `ROUTER_CS_6_RR` BIT(24) is new (tb_regs.h:218).
- `clx.c`, `tmu.c`, `lc.c`, `retimer.c` are **byte-identical** between v7.0 and v7.2.

#### 6. Suggested page topics (fine granularity, one mechanism per page)

**CLx**
1. *CL state model and `sw->clx`* — `TB_CL0S/CL1/CL2` (tb.h:466), `tb_switch_clx_is_enabled` (tb.h:1088), `clx_name` (clx.c:18), `validate_mask` (clx.c:301).
2. *Per-adapter CLx programming* — `tb_port_clx_supported/_set/_enable/_disable/tb_port_clx` (clx.c:68-163), `LANE_ADP_CS_0/1` bits (tb_regs.h:345-371).
3. *Router-level CLx enable/disable* — `tb_switch_clx_enable/_disable/_init` (clx.c:211-428), PM-secondary resolve, CL2-needs-v2 rule.
4. *When CLx is allowed and when it is torn down* — `tb_enable_clx`/`tb_disable_clx` (tb.c:184/235) and every call site with its reason (depth-1 rule, DMA tunnels, asym/sym transitions, suspend, margining).
5. *CLx suppression: quirks and platform gates* — `clx` module param (clx.c:14), `QUIRK_NO_CLX` (tb.h:26), `quirk_clx_disable` (quirks.c:24), Tiger Lake exclusion (clx.c:196), Titan Ridge objection masking (clx.c:257) **[VENDOR]**.

**TMU**
6. *TMU modes and the mode/mode_request pair* — `enum tb_switch_tmu_mode` (tb.h:88), `struct tb_switch_tmu` (tb.h:105), `tb_switch_tmu_is_configured/_is_enabled` (tb.h:1052/1065).
7. *TMU register map and tuning parameters* — `TMU_RTR_CS_*` / `TMU_ADP_CS_*` (tb_regs.h:245-336), `tmu_rates`/`tmu_params` (tmu.c:14-38), `tb_switch_set_tmu_mode_params` / `tb_port_set_tmu_mode_params`.
8. *TMU enable state machine* — `tb_switch_tmu_enable` (tmu.c:950) with `_enable_bidirectional`/`_unidirectional`/`_enhanced`/`_change_mode` and the `_off`/`_change_mode_prev` rollbacks.
9. *TMU discovery and teardown* — `tb_switch_tmu_init` (tmu.c:411), `tmu_mode_init` (tmu.c:357), `tb_switch_tmu_disable` (tmu.c:565), `disable_enhanced` (tmu.c:540).
10. *Time posting (grandmaster sync)* — `tb_switch_tmu_post_time` (tmu.c:447), `tb_switch_tmu_set_time_disruption` (tmu.c:332).
11. *TMU mode selection policy and the CLx/DP coupling* — `tb_enable_tmu` (tb.c:319), `tb_increase_tmu_accuracy` (tb.c:281), `tb_tmu_hifi_uni_required` (tb.c:313).

**System PM**
12. *The `nhi_pm_ops` callback table* — nhi.c:1266, every member, the freeze/thaw comment, the `restore_noirq` aliasing.
13. *System suspend, end to end* — `__nhi_suspend_noirq` → `tb_domain_suspend_noirq` → `tb_suspend_noirq` → `tb_switch_suspend`, plus what survives (PCIe/USB3/DMA) and what does not (DP).
14. *System resume, end to end* — `nhi_resume_noirq` → `tb_domain_resume_noirq` → `tb_resume_noirq` → `tb_switch_resume` → `tb_restore_children`, with the firmware-tunnel purge and the two sleeps.
15. *Hibernation: freeze, thaw, poweroff, restore* — nhi.c:999/1006/1027, tb.c:3203/3211, `nhi_wake_supported` and the `WAKE_SUPPORTED` property.
16. *Sleep-bit handshakes* — `usb4_switch_set_sleep` (usb4.c:507) vs `tb_lc_set_sleep` (lc.c:469).

**Runtime PM**
17. *NHI runtime PM and RTD3* — nhi.c:1079/1097, probe setup nhi.c:1251-1256, ACPI/Apple device links.
18. *Domain and CM runtime callbacks* — domain.c:607/618, tb.c:3232/3263, `remove_work` (tb.c:3250).
19. *Per-router runtime PM policy* — `sw->rpm` at tb.c:1373 and tb.c:3016, enable/disable at switch.c:3400-3409/3436-3439, `tb_switch_pm_ops` (switch.c:2368) and its ICM-only hooks.
20. *The runtime-PM reference discipline* — `get_sync`/`mark_last_busy`/`put_autosuspend` pairs across sysfs, NVM, scan, hotplug, DP tunnels; USB4-port and retimer devices.
21. *DP redrive mode and the RTD3 block* — tb.c:2104-2176, `QUIRK_KEEP_POWER_IN_DP_REDRIVE` **[VENDOR]**.

**Wakes**
22. *Wake source flags and the two wake sets* — tb.h:458-463, switch.c:3664-3672.
23. *USB4 wake programming and status* — `usb4_switch_set_wake` (usb4.c:426), `usb4_switch_check_wakes` (usb4.c:163), `PORT_CS_19`/`PORT_CS_18`/`ROUTER_CS_5`/`ROUTER_CS_6`.
24. *Pre-USB4 LC wake and sleep* — `tb_lc_set_wake`/`_set_wake_one`/`_set_sleep` (lc.c:389-513), `TB_LC_SX_CTRL` map **[VENDOR/gen ≥ 2]**.

**ACPI**
25. *`_OSC` USB4 negotiation and native control* — `tb_acpi_is_native` (acpi.c:122), the ACPI-core seam (drivers/acpi/bus.c:485-553), `nhi_select_cm` (nhi.c:1163).
26. *Per-protocol tunneling permission* — `tb_acpi_may_tunnel_usb3/dp/pcie`, `tb_acpi_is_xdomain_allowed` and all callers.
27. *The `usb4-host-interface` property and NHI device links* — `tb_acpi_add_link(s)` (acpi.c:14/91).
28. *ACPI companion binding for routers and USB4 ports* — `tb_acpi_bus` (acpi.c:353), `tb_acpi_find_companion`/`_switch_find_companion`/`_setup`, the `_ADR` hierarchy.
29. *Retimer power via `_DSM`* — `retimer_dsm_guid` (acpi.c:181), `tb_acpi_retimer_set_power` (acpi.c:188), `usb4->can_offline`.
30. *IOMMU DMA protection and `ExternalFacingPort`* — `nhi_pci_check_iommu` (pci.c:77), drivers/pci/pci-acpi.c:1416, admin-guide section.
31. *`!CONFIG_ACPI` behaviour* — tb.h:1523-1536, the "everything permitted" defaults.

**Vendor NHI PM**
32. *Ice Lake+ NHI force power and LC mailbox* — pci.c:266-445 **[VENDOR]**, with the ICM-only branches called out.

#### 7. Tracing integration

**Verified negative for this area.** The only tracepoints in `drivers/thunderbolt` are `trace_tb_tx` (ctl.c:388), `trace_tb_event` (ctl.c:405), `trace_tb_rx` (ctl.c:512), defined in drivers/thunderbolt/trace.h (`TRACE_SYSTEM thunderbolt`). Evidence: `grep -rn 'trace_\|tracepoint' drivers/thunderbolt/*.c` returns only those three lines; `clx.c`, `tmu.c`, `acpi.c`, `lc.c`, `pci.c`, and the PM callbacks in `nhi.c`/`domain.c`/`tb.c`/`switch.c`/`usb4.c` contain none. Control-channel traffic issued *during* suspend/resume (config reads/writes) is traced indirectly through ctl.c.

#### 8. Debug and diagnostic printing

- **Macros in play:** `tb_dbg/tb_warn/tb_info/tb_err/tb_WARN` (tb.h:728-732, all `dev_*` on `nhi->dev`); `tb_sw_dbg/warn/info/WARN` via `__TB_SW_PRINT` (tb.h:734-743, prefixes the route); `tb_port_dbg/warn/info/WARN` via `__TB_PORT_PRINT` (tb.h:745-758, prefixes route:port). ACPI and PCI code uses raw `dev_dbg`/`dev_warn`/`dev_err_probe`.
- **Per-file counts** (`_dbg(` / `_warn(` / `WARN*` / `_err(` / `_info(`): clx.c 5/1/0/0/0 · tmu.c 8/2/0/0/0 · acpi.c 2/5/1/0/0 · lc.c 4/0/0/0/0 · pci.c 1/0/0/0/0 · nhi.c 12/8/7/0/0 · domain.c 1/1/1/0/0 · tb.c 73/34/6/0/4 · switch.c 42/18/9/6/10 · usb4.c 12/7/4/0/0 · usb4_port.c 1/0/0/1/0 · retimer.c 5/2/0/2/2.
- **Control knobs:** everything is `dev_dbg`, so `CONFIG_DYNAMIC_DEBUG` per-file/per-line control (`dyndbg` module param on `thunderbolt`) or `-DDEBUG`. Module params that change PM/CLx behaviour and log output: `clx` (clx.c:15), `host_reset` (nhi.c:40), `xdomain` (xdomain.c:63). `dev_WARN` sites in nhi.c (nhi.c:1120/1123) fire on shutdown with live rings; the single ACPI `WARN_ON` is acpi.c:200 (`!adev` while `can_offline`).

#### 9. Asynchronous, deferred and lazy processing

- **`tcm->remove_work`** — `struct delayed_work`, declared tb.c:68, initialised tb.c:3393 (`INIT_DELAYED_WORK(..., tb_remove_work)`), queued **only** from `tb_runtime_resume` at tb.c:3283 with `msecs_to_jiffies(50)`, cancelled at tb.c:2947 (`tb_stop`). Handler `tb_remove_work` (tb.c:3250) runs on `tb->wq`; deferred precisely to avoid deadlock when device removal runtime-resumes the device.
- **`tb_handle_hotplug`** — delayed work queued at tb.c:106 with delay 0; gated by `tcm->hotplug_active`, which suspend clears (tb.c:3085, tb.c:3207, tb.c:3244) and resume sets (tb.c:3197, tb.c:3215, tb.c:3275). It takes a runtime-PM ref on `tb->dev` (tb.c:2430) so a hotplug wakes the domain.
- **`tb_handle_dp_bandwidth_request`** — delayed work queued tb.c:2882; same `hotplug_active` gate and same `pm_runtime_get_sync(&tb->dev)` at tb.c:2746.
- **`nhi->interrupt_work`** — `struct work_struct`, `INIT_WORK` at pci.c:133 (MSI fallback only), scheduled from `nhi_msi` (nhi.c:971), flushed by `nhi_pci_shutdown` (pci.c:244).
- **XDomain `state_work`** — restarted from `tb_xdomain_resume` (xdomain.c:2040) via `start_handshake` (xdomain.c:737) at `XDOMAIN_SHORT_TIMEOUT` = 100 ms; cancelled synchronously by `tb_xdomain_suspend` → `stop_handshake` (xdomain.c:752).
- **Completions:** `nhi->domain_released` — waited at pci.c:492 and nhi.c:1245, completed in `tb_domain_release()` (domain.c:329). `sw->rpm_complete` — **[ICM] only** (icm.c:657/700/2172/2179).
- **Polling loops:** `tb_switch_wait_for_bit` (switch.c:1723, `usleep_range(50,100)`, caller-supplied ms deadline) — used by sleep-ready, Router Ready, Configuration Ready. TMU post-time loop (tmu.c:520-526, 100 × 5-10 µs). `tb_wait_for_port` (switch.c:511-551, 10 × 100 ms). `nhi_reset` (nhi.c:1151-1158, 500 ms / 10-20 µs). **[VENDOR]** `icl_nhi_force_power` (pci.c:315-320) and `icl_nhi_lc_mailbox_cmd_complete` (pci.c:347-352).
- **Deferred CLx/TMU work: verified negative.** `grep -n 'work' drivers/thunderbolt/clx.c drivers/thunderbolt/tmu.c drivers/thunderbolt/acpi.c drivers/thunderbolt/lc.c` returns nothing — all four files are fully synchronous.

#### 10. Subsystem-specific debugging infrastructure

- **No dedicated sysfs attribute for TMU, CLx or wake state.** `tb_switch_type` exposes `authorized`, `boot`, `nvm_*`, etc. (switch.c:2260-2290); the only PM-adjacent one is `nvm_authenticate_on_disconnect`, visible only under `QUIRK_FORCE_POWER_LINK_CONTROLLER` (switch.c:2270) and reaching `tb_lc_force_power()` at switch.c:2111. `usb4_port` exposes `offline`/`rescan` gated on `usb4->can_offline` (usb4_port.c:252-274), i.e. on the ACPI retimer `_DSM`. `domainX/iommu_dma_protection` reflects `nhi->iommu_dma_protection`.
- **debugfs:** no TMU/CLx-specific file. TMU registers are visible only through the raw config-space dumps: router `regs` (debugfs.c:2425) using `SWITCH_CAP_TMU_LEN` = 26 (debugfs.c:33), adapter `regs` (debugfs.c:2441) using `PORT_CAP_TMU_V1_LEN` = 8 / `PORT_CAP_TMU_V2_LEN` = 10 (debugfs.c:28-29). Gate: `CONFIG_DEBUG_FS` (Makefile:10) [errata 2026-09-10, write time of pm/clx-policy.md: Makefile:9 on disk]; write access needs `CONFIG_USB4_DEBUGFS_WRITE` (Kconfig, `DEBUGFS_MODE`).
- **Lane margining ↔ CLx:** `margining_run_write` (debugfs.c:1226) calls `tb_switch_clx_disable` (debugfs.c:1262) before and `tb_switch_clx_enable` (debugfs.c:1310) after, bracketed by `pm_runtime_get_sync`/`put_autosuspend` (debugfs.c:1239/1314). Gate: `CONFIG_USB4_DEBUGFS_MARGINING` (depends on `DEBUG_FS` + `USB4_DEBUGFS_WRITE`).
- **KUnit: verified negative for this area.** `drivers/thunderbolt/test.c` has 45 `KUNIT_CASE` entries; `grep -n 'tmu\|clx\|suspend\|resume\|wake\|acpi' drivers/thunderbolt/test.c` returns nothing. Gate would be `CONFIG_USB4_KUNIT_TEST` (Kconfig; `thunderbolt-${CONFIG_USB4_KUNIT_TEST} += test.o`, Makefile:12).

#### 11. v7.0 → v7.2 drift ledger for this area

`git diff v7.0..v7.2 --stat` over the area paths: `acpi.c` 14 · `domain.c` 37 · `nhi.c` 606 · `pci.c` 622 (new file) · `switch.c` 107 · `tb.c` 88 · `tb.h` 26 · `tb_regs.h` 19 · `usb4.c` 35 · `usb4_port.c` 2 · `xdomain.c` 325 · `Documentation/admin-guide/thunderbolt.rst` 61. **`clx.c`, `tmu.c`, `lc.c`, `retimer.c` are unchanged.**

**Correction to the campaign brief:** the PM ops did **not** move from nhi.c to pci.c. `nhi_pm_ops` is still defined in nhi.c (v7.0 nhi.c:1444 → v7.2 nhi.c:1266); what changed is that it lost `static`, gained a declaration in nhi.h:39, and the `struct pci_driver` that references it moved to pci.c:591-598. All eleven `nhi_*` PM callbacks stayed in nhi.c.

| Change | Old → new | Commit |
|---|---|---|
| `nhi->pdev` removed; all PM/ACPI users take `nhi->dev` | acpi.c:31/60/65/69/96/106/308 rewritten (14 lines — **this is the v7.2 acpi.c change**) | 8c3ff7c5ae15 |
| `struct tb_nhi_pci` introduced | new, pci.c:31 | 8c3ff7c5ae15 |
| `tb_err/tb_warn/tb_info/tb_dbg/tb_WARN` re-pointed to `nhi->dev` | tb.h:725-729 → tb.h:728-732 | 8c3ff7c5ae15 |
| `nhi_pm_ops` `static` → extern | nhi.c:1444 → nhi.c:1266 + nhi.h:39 | e241d98e04ef |
| `struct pci_driver nhi_driver` moved | nhi.c:1556 → pci.c:591 | e241d98e04ef |
| `nhi_probe(pci_dev*, id)` → `nhi_pci_probe()` (pci.c:447) + `nhi_probe(struct tb_nhi*)` (nhi.c:1186) | nhi.c:1339 → split | e241d98e04ef |
| `nhi_remove()` → `nhi_pci_remove()` | nhi.c:1426 → pci.c:482 | e241d98e04ef |
| `nhi_shutdown()` `static` → extern | nhi.c:1140 → nhi.c:1112 + nhi.h:38 | e241d98e04ef |
| `nhi_check_quirks/_check_iommu/_check_iommu_pdev/_imr_valid/_init_msi` renamed with `nhi_pci_` prefix and moved | nhi.c:1169/1202/1193/1306/1265 → pci.c:41/77/68/148/111 | e241d98e04ef |
| `ring_request_msix`/`ring_release_msix` → `nhi_pci_ring_request_msix`/`_release_msix`, now behind `tb_nhi_ops` | nhi.c:462/496 → pci.c:184/220 | e241d98e04ef |
| **`nhi_ops.c` deleted**; Ice Lake PM folded into pci.c | nhi_ops.c:35/122/161/179 → pci.c:283/374/413/432 | e241d98e04ef |
| `nhi_pci_shutdown()` added as the default `.shutdown` op | new, pci.c:233 | e241d98e04ef |
| `nvm_authenticate_start_dma_port`/`_complete_dma_port` **removed** from switch.c; replaced by `nhi->ops->pre_nvm_auth`/`post_nvm_auth` = `nhi_pci_start_dma_port`/`nhi_pci_complete_dma_port` | switch.c:209-233 → pci.c:158/174 | e241d98e04ef |
| `nhi_wake_supported(struct pci_dev *)` → `(struct device *)` | nhi.c:1015 → nhi.c:1013 | 8c3ff7c5ae15 |
| `nhi_enable_int_throttling()` moved out of the PM neighbourhood and exported | nhi.c (near `nhi_poweroff_noirq`) → nhi.h:32 | c51777370ac2 |
| `nhi->domain_released` completion added; `nhi_pci_remove` and `nhi_probe` failure path wait on it | new, include/linux/thunderbolt.h:530; pci.c:492, nhi.c:1229/1245 | f5cc545f5969, 9cbc63400f7d (init moved before use) |
| `tb_free_unplugged_xdomains()` moved within tb.c and changed to `void` | tb.c:~3174 → tb.c:3123 | a8937f35cf39 |
| `tb_complete()` now calls `tb_domain_unregister_unplugged_xdomains()` (domain.c:874) instead of locking + `tb_free_unplugged_xdomains()` | tb.c:3219-3230 | a8937f35cf39 |
| `tb_remove_work()` now calls `tb_free_unplugged_xdomains()` **outside** `tb->lock` | tb.c:3255-3260 | a8937f35cf39 |
| `tb_resume_noirq()` gained a `tb_free_unplugged_xdomains()` call | tb.c:3160 | a8937f35cf39 |
| `tb_switch_resume()` gained the "XDomain replaced by a router" branch (`tb_cfg_get_upstream_port` on the XDomain route) | switch.c:3611-3625 | 2fb199dc6405 / 7c7345bcde6c neighbourhood |
| `usb4_switch_setup()` now waits for `ROUTER_CS_6_RR` (500 ms) — **new step on every resume** | usb4.c:301-302 | 062023c4364f |
| `usb4_switch_configuration_valid()` timeout 50 ms → 500 ms — affects `tb_restore_children` | usb4.c:335 | ba2cc3851101 |
| `ROUTER_CS_6_RR` BIT(24) added | tb_regs.h:218 | 062023c4364f |
| `plug_events_delay = 0xff` moved out of `tb_plug_events_active()` into `tb_switch_configure()`; the `0xa` non-USB4 case removed | switch.c:1755 → switch.c:2620 | e24f3c0df483 |
| `tb_switch_nvm_add()` split into `tb_switch_nvm_init()` + `tb_switch_nvm_add()` | switch.c:325 → switch.c:325/362 | 4573add760b8 |
| `tb_stop()` now sets `tb->root_switch = NULL` — resume paths must not assume it survives a stop | tb.c:2958 [errata 2026-09-10, write time of pm/system-suspend.md: tb.c:2960 on disk] | e56249d8a68e |
| `tb_queue_hotplug()` takes a domain reference (`tb_domain_get`), released in `tb_handle_hotplug()` | tb.c:101, tb.c:2533 (orchestrator note 2026-09-05: the planning pass wrote :2528, a blank line on disk; `tb_domain_put(tb)` is at :2533) | 138ec65b2c76 |
| `tb_configfs_init()`/`tb_configfs_exit()` added around `tb_acpi_init()`/`tb_acpi_exit()` in domain init/exit | domain.c:891/920 | cba57ed6f1e7 |
| `struct tb_path.hops` became a flexible array (`__counted_by`) | tb.h:443 → tb.h:445 | c3e7cc8bc5ca |
| admin-guide `thunderbolt.rst` +61 lines (USB4STREAM section) — no PM section changed | Documentation/admin-guide/thunderbolt.rst:376 | af8922ffb322 |

**Behaviour a v7.0-based page would now misstate:** (a) the PCI driver and the Ice Lake force-power code live in `pci.c`, not `nhi.c`/`nhi_ops.c`; (b) NVM-upgrade root-port D3cold blocking is now an NHI op, not a switch.c helper; (c) resume waits for Router Ready and uses a 10× longer Configuration Ready timeout; (d) `tb_complete` unregisters XDomains through a new domain helper and no longer holds `tb->lock` across the whole operation; (e) Notification Timeout is 255 ms for **all** routers including non-USB4.

#### 12. Kernel documentation and ABI

- **Documentation/admin-guide/thunderbolt.rst:437-445** — "Forcing power": the OEM WMI `force_power` attribute; points at `Documentation/ABI/testing/sysfs-platform-intel-wmi-thunderbolt`. Notes the state cannot be queried. This is the *platform* force-power, distinct from `tb_lc_force_power()` (lc.c:712) and from `icl_nhi_force_power()` (pci.c:283).
- **Documentation/admin-guide/thunderbolt.rst:179-197** — "DMA protection utilizing IOMMU": describes `/sys/bus/thunderbolt/devices/domainX/iommu_dma_protection`, backed by `nhi->iommu_dma_protection` set in `nhi_pci_check_iommu()` (pci.c:106).
- **Documentation/admin-guide/thunderbolt.rst:226** and **:234** — the only other PM mentions: the OEM "force power" note in the NVM-upgrade flow, and the controller "full power cycle" after NVM authentication.
- **No Documentation/ page mentions `usb4-host-interface`, `OSC_SB_NATIVE_USB4_SUPPORT`, or the USB4 `_OSC` UUID.** Verified: `grep -rn 'usb4-host-interface\|USB4 _OSC\|OSC_SB_NATIVE_USB4' Documentation/` returns nothing. `Documentation/firmware-guide/acpi/` has no USB4 entry; `Documentation/driver-api/usb/` has no usb4 file. This is a documentation gap the campaign can fill.
- **Kerneldoc blocks in this area:** `enum tb_switch_tmu_mode` (tb.h:78-87), `struct tb_switch_tmu` (tb.h:96-104), `struct tb_switch` incl. `@rpm`/`@rpm_complete`/`@clx`/`@quirks` (tb.h:112-170), `struct tb_cm_ops` PM members (tb.h:470-506), `struct tb_cm` `@hotplug_active`/`@remove_work` (tb.c:52-63), `struct tb_nhi` `@going_away`/`@iommu_dma_protection`/`@domain_released` (include/linux/thunderbolt.h:501-517), `struct tb_nhi_ops` (nhi.h:41-55), `struct tb_nhi_pci` (pci.c:26-30), `tb_switch_tmu_is_configured`/`_is_enabled` (tb.h:1042-1064), `tb_switch_clx_is_enabled` (tb.h:1077-1087).
- **Kerneldoc on functions:** clx.c:165 (`tb_port_clx_is_enabled`), clx.c:178 (`tb_switch_clx_is_supported`), clx.c:202 (`tb_switch_clx_init`), clx.c:309 (`tb_switch_clx_enable`, cites *CM Guide 1.0 section 8.1*), clx.c:389 (`tb_switch_clx_disable`); tmu.c:401 (`_init`), 439 (`_post_time`), 557 (`_disable`), 940 (`_enable`), 1020 (`_configure`); acpi.c:81/113/128/141/154/167/249/268; lc.c:250 (`tb_lc_is_clx_supported`), 419 (`tb_lc_set_wake`), 460 (`tb_lc_set_sleep`), 703 (`tb_lc_force_power`); usb4.c:157 (`_check_wakes`), 227 (`_setup`), 416 (`_set_wake`), 498 (`_set_sleep`), 1565 (`usb4_port_clx_supported`); switch.c:3512 (`tb_switch_resume`), 3631 (`tb_switch_suspend`), 1707 (`tb_switch_wait_for_bit`), 481 (`tb_wait_for_port`); usb4_port.c:355 (`usb4_port_device_resume`); domain.c:520 (`tb_domain_suspend_noirq`), 547 (`tb_domain_resume_noirq`), 835 (`tb_domain_disconnect_all_paths`). **Undocumented (no kerneldoc):** `tb_domain_suspend`, `tb_domain_freeze_noirq`, `tb_domain_thaw_noirq`, `tb_domain_complete`, `tb_domain_runtime_suspend`, `tb_domain_runtime_resume` (domain.c:569-627), `tb_acpi_init`/`tb_acpi_exit` (acpi.c:360/365).

### Sweep S1: tracing, debug printing, debugging infrastructure — COMPLETE (recorded 2026-09-04)

Tree confirmed: `git describe --tags` = **v7.2**, HEAD = 8d3ae59288f1e7d58d76558a6ee96d533bc5019f.

#### 7. Tracing integration

**Build gate — there is none of its own.** `trace.h` is pulled in by `ctl.c` only, and `ctl.o` is unconditional (`drivers/thunderbolt/Makefile:4`). The events exist whenever `CONFIG_USB4` is built and the kernel has tracepoints; `ccflags-y := -I$(src)` (`Makefile:2`) is what makes `TRACE_INCLUDE_PATH .` (`trace.h:190-191`) resolve. No `CONFIG_USB4_*` symbol gates tracing.

**Instantiation:** `#define CREATE_TRACE_POINTS` / `#include "trace.h"` at `drivers/thunderbolt/ctl.c:18-19`. `TRACE_SYSTEM thunderbolt` (`trace.h:10-11`); `TRACE_INCLUDE_FILE trace` (`trace.h:193-194`); `#include <trace/define_trace.h>` (`trace.h:197`).

**Pretty-printers (all `static inline`, guarded by `TB_TRACE_HELPERS` `trace.h:37-38`):**
- `tb_cfg_type_name` / `show_type_name` — `trace.h:21` / `trace.h:22-35`: `__print_symbolic` over all 12 `TB_CFG_PKG_*` types, including the three ICM ones.
- `show_data_read_write` `trace.h:39` (offset/len/port/config/seq); `show_data_error` `trace.h:52` (error/port/plug); `show_data_event` `trace.h:63` (port/unplug); `show_route` `trace.h:73`; dispatcher `show_data` `trace.h:83` — ICM types print a literal `route=0` (`trace.h:107-112`), then every packet dumps `data=[0x…, …]`.

**Event definitions:**

| kind | name | file:line | fields | TP_printk |
|---|---|---|---|---|
| `DECLARE_EVENT_CLASS` | `tb_raw` | `drivers/thunderbolt/trace.h:131` | `int index`, `u8 type`, `size_t size`, `__dynamic_array(u32, data, size/4)` (`:134-139`, assign `:140-145`) | `"type=%s, size=%zd, domain=%d, %s"` `:146-150` |
| `DEFINE_EVENT` | `tb_tx` | `drivers/thunderbolt/trace.h:153` | inherits `tb_raw` | inherits |
| `DEFINE_EVENT` | `tb_event` | `drivers/thunderbolt/trace.h:158` | inherits `tb_raw` | inherits |
| `TRACE_EVENT` | `tb_rx` | `drivers/thunderbolt/trace.h:163` | `tb_raw` fields **plus** `bool dropped` (`:166-172`) | `"type=%s, dropped=%u, size=%zd, domain=%d, %s"` `:180-185` |

**Call sites (all three in ctl.c, all fire per control packet):**
- `drivers/thunderbolt/ctl.c:388` `trace_tb_tx(ctl->index, type, data, len)` — inside `tb_ctl_tx()`, after the frame is prepared but **before** `cpu_to_be32_array()`, so payload is traced host-order.
- `drivers/thunderbolt/ctl.c:405` `trace_tb_event(ctl->index, type, pkg->buffer, size)` — inside `tb_ctl_handle_event()`, before `ctl->callback()`; carries both SW-CM plug events and `TB_CFG_PKG_ICM_EVENT`, so **not** ICM-only.
- `drivers/thunderbolt/ctl.c:512` `trace_tb_rx(pkg->ctl->index, frame->eof, pkg->buffer, frame->size, !req)` — inside the RX callback, after `tb_cfg_request_find()`; `dropped = !req` marks packets with no matching outstanding request.

**Verified negatives** (`grep -rn "trace_printk\|tracepoint_probe\|register_trace_\|ftrace" drivers/thunderbolt/ include/linux/thunderbolt.h` → no output; `grep -rn "#include <trace/" drivers/thunderbolt/` → only `trace.h:197`): no probes on other subsystems' tracepoints, no private ftrace instance, no `trace_printk` leftovers, no adjacent-subsystem event seam. The only cross-subsystem observability seam is the uevent path (item 10f), not tracing.

#### 8. Debug and diagnostic printing

##### 8.1 Macro hierarchy (every debug macro bottoms out in `dev_dbg`, hence all are dyndbg-controllable)

| macro family | definition | device printed against | prefix |
|---|---|---|---|
| `tb_err` / `tb_WARN` / `tb_warn` / `tb_info` / `tb_dbg` | `drivers/thunderbolt/tb.h:728` / `:729` / `:730` / `:731` / `:732` | `(tb)->nhi->dev` (the NHI PCI device) | none |
| `__TB_SW_PRINT` + `tb_sw_WARN/warn/info/dbg` | `drivers/thunderbolt/tb.h:734` + `:740`–`:743` | via `__sw->tb` → NHI dev | `"%llx: "` = `tb_route(sw)` |
| `__TB_PORT_PRINT` + `tb_port_WARN/warn/info/dbg` | `drivers/thunderbolt/tb.h:745` + `:751`–`:758` | via `__port->sw->tb` → NHI dev | `"%llx:%u: "` = route:port |
| `__TB_TUNNEL_PRINT` + `tb_tunnel_WARN/warn/info/dbg` | `drivers/thunderbolt/tunnel.h:224` + `:236`–`:243` | via `__tunnel->tb` → NHI dev | `"%llx:%u <-> %llx:%u (%s): "`, type via `tb_tunnel_type_name` (`tunnel.c:2682`, table `tb_tunnel_names[]` `tunnel.c:101`) |
| `tb_ctl_WARN/err/warn/info/dbg` + `tb_ctl_dbg_once` | `drivers/thunderbolt/ctl.c:58` / `:61` / `:64` / `:67` / `:70` / `:73` | `(ctl)->nhi->dev` | none |

**Verified negatives** (`grep -rn "^#define tb_" drivers/thunderbolt/*.c drivers/thunderbolt/*.h`): there is **no** `tb_sw_err`, `tb_port_err`, `tb_tunnel_err`, `tb_path_dbg`, `tb_xdomain_dbg`, `tb_retimer_dbg`, or `tb_usb4_port_dbg`. `path.c` prints through `tb_port_*`; `xdomain.c`, `retimer.c`, `usb4_port.c`, `nhi.c`, `pci.c`, `dma_test.c`, `stream.c` print through raw `dev_*` on their own device. Error level exists only as `tb_err` (domain) and `tb_ctl_err`.

**Dynamic debug:** `tb_dbg`, `tb_sw_dbg`, `tb_port_dbg`, `tb_tunnel_dbg`, `tb_ctl_dbg` all expand to `dev_dbg` on the NHI device, so `dyndbg="module thunderbolt +p"` (or `file drivers/thunderbolt/tb.c +p`) turns on the whole SW-CM narrative; `tb_ctl_dbg_once` → `dev_dbg_once` (controllable, fires once). No `pr_debug` anywhere; the only `pr_*` in the subsystem are `pr_warn("RX CRC error")` / `pr_warn("RX buffer overrun")` at `drivers/thunderbolt/stream.c:356` and `:358`.

##### 8.2 Dump helpers

| helper | file:line | what it prints | called from |
|---|---|---|---|
| `tb_dump_hop` | `drivers/thunderbolt/path.c:16` | 5 `tb_port_dbg` lines: in/out HopID + out port, weight/priority/credits/drop/PM, counter enable+index, flow control & shared buffer in/eg, unknown1..3 | `tb_path_discover` (`path.c:199`), `tb_path_activate` (`path.c:575`) |
| `tb_dump_port` | `drivers/thunderbolt/switch.c:442` | 5 `tb_dbg`: port#/vendor:device/revision/TB version/type, max in-out HopID, max counters, NFC credits, total/control credits | `tb_init_port` (`switch.c:759`) |
| `tb_dump_switch` | `drivers/thunderbolt/switch.c:1563` | 5 `tb_dbg`: generation name + vendor:device/revision/TB version, max port number, upstream port/depth/route/enabled/plug-events delay, unknown1/unknown4 | `tb_switch_alloc` (`switch.c:2485`) |
| `tb_dp_dump` | `drivers/thunderbolt/tunnel.c:1536` | 3 `tb_tunnel_dbg`: DP IN / DP OUT / DP remote max supported bandwidth, read from `DP_LOCAL_CAP` / `DP_REMOTE_CAP` | `tb_tunnel_discover_dp` (`tunnel.c:1654`) |
| `tb_cfg_print_error` | `drivers/thunderbolt/ctl.c:278` | severity map for `TB_CFG_ERROR_*`: `PORT_NOT_CONNECTED` silent (`:283-286`), `INVALID_CONFIG_SPACE` → `tb_ctl_dbg_once` (`:292`), `NO_SUCH_PORT`/`LOOP`/default → `tb_ctl_WARN` (`:301`,`:305`,`:314`), `LOCK` → `tb_ctl_warn` (`:309`) | `tb_cfg_get_error` (`ctl.c:1101`) |

There is **no** `tb_dump_path` and no `tb_ctl_print`.

##### 8.3 Per-file counts (`#define` lines excluded; `derr` folds in `dev_err_probe`; `xx_WARN` = `dev_WARN` and the `tb_*_WARN` wrappers; `WARN_ON` column = `WARN()`+`WARN_ON()`+`WARN_ON_ONCE()`)

```
file         | ddbg|dinfo|dwarn| derr|tb_dbg|tb_info|tb_warn|xx_WARN|WARN_ON
acpi.c       |    1|    0|    2|    0|     1|      0|      3|      0|      1
cap.c        |    0|    0|    0|    0|     1|      0|      0|      0|      0
clx.c        |    0|    0|    0|    0|     5|      0|      1|      0|      0
ctl.c        |    2|    1|    1|    1|     6|      0|      3|      7|     14
debugfs.c    |    0|    0|    0|    0|     2|      0|      5|      0|      0
dma_test.c   |    8|    0|    1|    5|     0|      0|      0|      0|      0
domain.c     |    0|    0|    0|    0|     1|      0|      1|      0|      1
eeprom.c     |    0|    0|    0|    0|     2|      0|     14|      0|      0
icm.c        |    3|    0|    2|    2|     6|      5|     13|      0|      1
lc.c         |    0|    0|    0|    0|     4|      0|      0|      0|      0
nhi.c        |   12|    0|    8|    7|     0|      0|      0|      6|      1
nvm.c        |    1|    0|    0|    0|     1|      0|      0|      0|      0
path.c       |    0|    0|    0|    0|    11|      0|      7|      2|      0
pci.c        |    1|    0|    0|    4|     0|      0|      0|      0|      0
property.c   |    0|    0|    0|    0|     0|      0|      0|      0|      1
quirks.c     |    0|    0|    0|    0|     6|      0|      0|      0|      0
retimer.c    |    2|    2|    0|    2|     3|      0|      2|      0|      0
stream.c     |    3|    0|    0|    0|     0|      0|      0|      0|      1
switch.c     |    0|    3|    1|    6|    42|      7|     17|      6|      3
tb.c         |    1|    0|    1|    3|    72|      4|     33|      0|      6
tmu.c        |    0|    0|    0|    0|     8|      0|      2|      0|      0
tunnel.c     |    0|    0|    0|    0|    32|      2|     10|      1|      9
usb4.c       |    0|    0|    0|    0|    12|      0|      7|      0|      4
usb4_port.c  |    0|    0|    0|    1|     1|      0|      0|      0|      0
xdomain.c    |   33|    3|    5|    6|     8|      0|      6|      0|      4
ctl.h        |    0|    0|    0|    0|     0|      0|      0|      0|      1
tb.h         |    0|    0|    0|    0|     0|      0|      0|      0|      2
```
Files with zero printing: `configfs.c`, `dma_port.c`, `test.c`, and the register headers. **`BUG`/`BUG_ON` appear nowhere** in `drivers/thunderbolt/` or `include/linux/thunderbolt.h` (`grep -rnE '\bBUG\(|\bBUG_ON\('` → no match).

##### 8.4 Load-bearing mechanisms (not per-site)

- **`check_header()` `drivers/thunderbolt/ctl.c:201-236`** — ten bare `WARN(...)` guards on every received control packet (size, eof, sof, `header->unknown`, route, `addr.zero`, space, offset, length). This one function accounts for most of ctl.c's 14 WARN lines and is the noisiest single mechanism in the subsystem; two more `WARN(1, "tb_cfg_read/write: %d")` at `ctl.c:1131`/`:1157`.
- **`tb.c` (72 dbg / 33 warn, zero WARN)** — the SW-CM narrative, in themes: DP IN/OUT resource availability, hotplug scan/unplug, tunnel create/teardown, bandwidth-group re-estimation and allocation requests, asymmetric↔symmetric link switching, DP redrive mode, suspend/resume. Turning on dyndbg for `tb.c` alone gives the full connection-manager story.
- **`switch.c` (42 dbg / 17 warn)** — enumeration: `tb_dump_switch` at alloc, `tb_dump_port` per port at init, plus link-attribute and credit-allocation lines.
- **`tunnel.c` (32 dbg)** — per-tunnel activation, credit/bandwidth accounting; `path.c` (11 dbg, 2 `tb_port_WARN`) — hop dumps at discovery and activation.
- **`eeprom.c` (14 `tb_sw_warn`)** — DROM parse/CRC failures, the classic "bad device" signal.
- **`nhi.c` (12 `dev_dbg`, 8 `dev_warn`, 7 `dev_err`/`dev_err_probe`, 6 `dev_WARN`)** — ring/interrupt layer; it sits under the domain and so has no `tb_*` wrapper.
- **`xdomain.c` (33 `dev_dbg` on `&xd->dev`)** — the host-to-host protocol handshake trace (UUID request, properties, retries).

##### 8.5 Control knobs

**Kconfig (`drivers/thunderbolt/Kconfig`):** `USB4` `:2`; `USB4_CONFIGFS` `:21` (`def_tristate USB4`); `USB4_DEBUGFS_WRITE` `:25` (marked DANGEROUS, points at `https://github.com/intel/tbtools` `:33`); `USB4_DEBUGFS_MARGINING` `:38` (depends on `DEBUG_FS` `:40` and `USB4_DEBUGFS_WRITE` `:41`); `USB4_KUNIT_TEST` `:49`; `USB4_DMA_TEST` `:54` (depends on `DEBUG_FS`); `USB4_STREAM` `:67`. Build wiring: `debugfs.o` under `CONFIG_DEBUG_FS` (`Makefile:9`), `configfs.o` `:10`, `test.o` `:11` (+`DISABLE_STRUCTLEAK_PLUGIN` `:12`), `thunderbolt_dma_test.o` `:14-15`, `thunderbolt_stream.o` `:17-18`, `acpi.o` under `CONFIG_ACPI` `:8`.

**Module parameters (all `0444` — settable only at load / on the cmdline as `thunderbolt.<name>=`; none is writable at runtime):** `clx` `drivers/thunderbolt/clx.c:15`; `host_reset` `nhi.c:40`; `dprx_timeout` `tunnel.c:86`; `dma_credits` `tunnel.c:92`; `bw_alloc_mode` `tunnel.c:97`; `asym_threshold` `tb.c:47`; `xdomain` `xdomain.c:63`; **`start_icm` `icm.c:50` — ICM-only**. Verified negative: no `__setup()`, `early_param()` or `core_param()` anywhere in the subsystem, and no entry in `Documentation/admin-guide/kernel-parameters.txt`.

**Sysfs knobs that change diagnostics:** none. Every sysfs attribute (item 10e) is functional, not a log/verbosity control. The only runtime diagnostic switch is dyndbg plus the debugfs write gate.

#### 10a. debugfs.c

**Root:** `tb_debugfs_init()` `drivers/thunderbolt/debugfs.c:2555` → `debugfs_create_dir("thunderbolt", NULL)` `:2557` (static `tb_debugfs_root` `:125`); `tb_debugfs_exit()` `:2560`. Callers: `tb_domain_init()` `drivers/thunderbolt/domain.c:891`, `tb_domain_exit()` `domain.c:919` (+ error path `domain.c:907`). **The tree is flat, not per-domain** — every object is a top-level dir named `dev_name()`.

**Object entry points and their callers:**

| entry point | file:line | caller |
|---|---|---|
| `tb_switch_debugfs_init` | `debugfs.c:2418` | `tb_switch_add` `switch.c:3411` |
| `tb_switch_debugfs_remove` | `debugfs.c:2462` | `tb_switch_remove` `switch.c:3434` |
| `tb_xdomain_debugfs_init` | `debugfs.c:2468` | `tb_xdomain_get_properties` `xdomain.c:1634` |
| `tb_xdomain_debugfs_remove` | `debugfs.c:2473` | `tb_xdomain_remove` `xdomain.c:2226` |
| `tb_service_debugfs_init` | `debugfs.c:2484` | `enumerate_services` `xdomain.c:1267` |
| `tb_service_debugfs_remove` | `debugfs.c:2496` | `__unregister_service` `xdomain.c:1154`, error path `xdomain.c:1270` |
| `tb_retimer_debugfs_init` | `debugfs.c:2533` | `tb_retimer_add` `retimer.c:461` |
| `tb_retimer_debugfs_remove` | `debugfs.c:2549` | `tb_retimer_remove` `retimer.c:468` |

Prototypes + `CONFIG_DEBUG_FS` no-op stubs: `drivers/thunderbolt/tb.h:1538-1560`.

**Files:**

| path | mode | show | write |
|---|---|---|---|
| `<switch>/regs` `:2425` | `DEBUGFS_MODE` | `switch_regs_show` `:2210` | `switch_regs_write` `:291` |
| `<switch>/drom` `:2428` (blob, only if `sw->drom`; wrapper filled at `eeprom.c:454`) | 0400 | `debugfs_create_blob` | — |
| `<switch>/portN/regs` `:2441` | `DEBUGFS_MODE` | `port_regs_show` `:2105` | `port_regs_write` `:273` |
| `<switch>/portN/path` `:2443` | 0400 | `path_show` `:2261` | `path_write` `:282` (compiled, but the 0400 mode makes it unreachable) |
| `<switch>/portN/counters` `:2446` (if `config.counters_support`) | 0600 | `counters_show` `:2324` | `counters_write` `:1895` |
| `<switch>/portN/sb_regs` `:2449` (if `port->usb4`) | `DEBUGFS_MODE` | `port_sb_regs_show` `:2386` | `port_sb_regs_write` `:381` |
| `<retimer>/sb_regs` `:2538` | `DEBUGFS_MODE` | `retimer_sb_regs_show` `:2502` | `retimer_sb_regs_write` `:414` |
| `<service>/` `:2486` | dir only | — | — (dma_test fills it) |

Port dirs are `portN` `:2439-2440`, skipping `port->disabled` and `TB_TYPE_INACTIVE` `:2434-2437`. **xdomain and usb4_port get no files of their own** — `tb_xdomain_debugfs_init` only calls `margining_xdomain_init`, and a USB4 port's `margining/` dir is hung under the parent switch's `portN` dir (`margining_port_init` `:1767`, `debugfs_lookup("portN", sw->debugfs_dir)` `:1776`).

**Write gate `CONFIG_USB4_DEBUGFS_WRITE`:** `#if IS_ENABLED(...)` `debugfs.c:201` … `#endif` `:454`. Inside: `path_write_one` `:207`, `regs_write` `:221`, `port_regs_write` `:273`, `path_write` `:282`, `switch_regs_write` `:291`, `parse_sb_line` `:300`, `sb_regs_write` `:330`, `port_sb_regs_write` `:381`, `retimer_sb_regs_write` `:414`, and `#define DEBUGFS_MODE 0600` `:446`. Outside: all five write pointers `#define`d to `NULL` `:448-452` and `DEBUGFS_MODE 0400` `:453`. The `DEBUGFS_ATTR(__space, __write)` macro `:104-117` stamps `.write = __write` into `<name>_fops`; `DEBUGFS_ATTR_RO` `:119`, `DEBUGFS_ATTR_RW` `:122`. Both write paths taint the kernel: `add_taint(TAINT_USER, LOCKDEP_STILL_OK)` at `:242` (`regs_write`) and `:339` (`sb_regs_write`). **Asymmetry worth documenting:** `counters_write` `:1895` sits *outside* the `#if` and its file is hardcoded 0600 `:2446`, so counter clearing is writable even with `USB4_DEBUGFS_WRITE=n`.

**Register-block dump format.** Header lines then fixed-width rows:
- switch/port regs: `"# offset relative_offset cap_id vs_cap_id value"` (`:2119`, `:2226` region), rows `"0x%04x %4d 0x%02x 0x%02x 0x%08x"` (`cap_show` `:1986`, `cap_show_by_dw` `:1960`).
- path: `"# offset relative_offset in_hop_id value"` `:2275`, row `:2254`.
- counters: `"# offset relative_offset counter_id value"` `:2338`, row `:2317`.
- sideband: `"# register value"` `:2362`, row `"0x%02x"` + bytes `:2377-2379`.

**Config spaces and read helpers:** `TB_CFG_SWITCH` via `tb_sw_read` (`:1979`, `switch_basic_regs_show` `:2188`); `TB_CFG_PORT` via `tb_port_read` (`:1976`, `port_basic_regs_show` `:2090/:2095`); `TB_CFG_HOPS` via `tb_port_read` (`path_show_one` `:2246`); `TB_CFG_COUNTERS` via `tb_port_read` (`counter_set_regs_show` `:2308`). Reads are chunked to `TB_MAX_CONFIG_RW_LENGTH` (`cap_show` `:1972`); on failure `cap_show` falls back to the per-dword `cap_show_by_dw` `:1942`, which prints `"<not accessible>"` `:1956` rather than aborting. Capability walks: `port_cap_show` `:1996` / `port_caps_show` `:2079`, `switch_cap_show` `:2137` / `switch_caps_show` `:2177`; fixed lengths at `:21-34`. Every show takes `pm_runtime_get_sync()` on the owning device and `mutex_lock_interruptible(&tb->lock)`.

**Sideband dump:** register tables `port_sb_regs[]` `:75-88` (12 entries; `USB4_SB_DEBUG` is 54 bytes, `USB4_SB_DATA` 64) and `retimer_sb_regs[]` `:91-102` (10 entries); `SB_MAX_SIZE 64` `:72`. Access is `usb4_port_sb_read` `:2370` / `usb4_port_sb_write` `:372`, with `USB4_SB_TARGET_ROUTER` (index 0) or `USB4_SB_TARGET_RETIMER` (`rt->index`). Write format is documented in the comment at `:341-348`: `reg b0 b1 b2…`, partial writes leave the tail untouched.

**v7.2 fixes in this file:**
- `c1bef05763c9` "debugfs: Fix sideband write size check" — `sb_regs_write` now bounds `bytes_read` against the *matched* entry (`debugfs.c:369-370`, `if (bytes_read > sb_reg->size) return -E2BIG;`) instead of the first table entry; previously rejected valid writes to `USB4_SB_DEBUG`/`USB4_SB_DATA`.
- `503c5ae1e72a` "debugfs: Fix margining error counter buffer leak" — `margining_error_counter_write` `:935` now `free_page()`s the temp page on the success path `:961` and via `err_free:` `:972-974`; leaked one page per write.
- `babaad95670d` "debugfs: Don't stop reading SB registers if just one fails" — `sb_regs_show` `:2356` prints `"0x%02x <not accessible>"` and `continue`s `:2372-2375` instead of returning `-EIO`; motivated by Parade PS8830 retimers not implementing the GEN4 TxFFE register.
- Adjacent: `4d5fc3f40685` moved service debugfs teardown into the unregister path (`xdomain.c:1270`); `7f35f42395fc` dropped the stored dentry in `dma_test.c` in favour of `debugfs_lookup_and_remove()`.

**ICM / vendor status:** nothing in `debugfs.c` is ICM-only or vendor-only. `grep -rn "debugfs" drivers/thunderbolt/icm.c` → **no match**: the firmware connection manager creates **no debugfs at all**. The debugfs tree is populated from `tb_switch_add`/`tb_retimer_add`, which run under both CMs, so the register/path/counter views work in firmware mode too.

**Margining (`CONFIG_USB4_DEBUGFS_MARGINING`, `debugfs.c:456`–`:1876`; stubs `:1869-1875`):** `struct tb_margining` `debugfs.c:489` (28 fields, kernel-doc `:457-488`: port/target/index/dev, `gen`, `asym_rx`, `caps[3]`, `results[3]`, lanes, BER min/max/current, voltage/time step counts and max offsets, dwell time, error counter mode, `software`/`time`/`right_high`/`upper_eye`). `margining_alloc` `:1650` reads `usb4_port_margining_caps` `:1677`, then creates `margining/` `:1720`.

| file | mode | created | show | write |
|---|---|---|---|---|
| `ber_level_contour` (hw only) | 0400 | `:1730` | `:670` | `:616` |
| `caps` | 0400 | `:1733` | `:681` | — |
| `lanes` | 0600 | `:1734` | `:853` | `:809` |
| `mode` | 0600 | `:1735` | `:1123` | `:1081` |
| `run` | 0600 | `:1736` | — (`DEFINE_DEBUGFS_ATTRIBUTE(margining_run_fops, NULL, …)` `:1319`) | `margining_run_write` `:1226` |
| `results` | 0600 | `:1737` | `:1416` | `:1322` |
| `test` | 0600 | `:1739` | `:1510` | `:1475` |
| `margin` (indep. H/L or L/R) | 0600 | `:1743` | `:1576` | `:1532` |
| `optional_voltage_offset` | `DEBUGFS_MODE` | `:1749` | `:1067` | `:1047` |
| `voltage_time_offset` (sw) | `DEBUGFS_MODE` | `:1753` | `:917` | `:884` |
| `error_counter` (sw) | `DEBUGFS_MODE` | `:1755` | `:977` | `:935` |
| `dwell_time` (sw) | `DEBUGFS_MODE` | `:1757` | `:1030` | `:1007` |
| `eye` (gen ≥ 4) | 0600 | `:1762` | `:1631` | `:1601` (private data is the `tb_port`, not the margining) |

Placement: `margining_port_init` `:1767` / `_remove` `:1782`; `margining_switch_init` `:1801` / `_remove` `:1818` (arms *both* ends of the link — upstream and the parent's downstream port); `margining_xdomain_init` `:1835` / `_remove` `:1846`; `margining_retimer_init` `:1856` / `_remove` `:1863`. Dwell bounds `MIN_DWELL_TIME`/`MAX_DWELL_TIME`/`DWELL_SAMPLE_INTERVAL` `:44-46`.

#### 10b. test.c (`CONFIG_USB4_KUNIT_TEST`, `Kconfig:49`, `Makefile:11`)

One suite: `tb_test_cases[]` `drivers/thunderbolt/test.c:3098` (45 `KUNIT_CASE` entries), `tb_test_suite` `:3147` (`.name = "thunderbolt"`), `kunit_test_suite(tb_test_suite)` `:3152`. No `.init`/`.exit`.

- **Path walking (7):** `tb_test_path_basic` `:423`, `_not_connected_walk` `:440`, `_single_hop_walk` `:479`, `_daisy_chain_walk` `:533`, `_simple_tree_walk` `:592`, `_complex_tree_walk` `:655`, `_max_length_walk` `:739`. Expectation structs `port_expectation` `:473`, `hop_expectation` `:862`.
- **Path allocation / lane bonding (7):** `tb_test_path_not_connected` `:842`, `_not_bonded_lane0` `:870`, `_not_bonded_lane1` `:928`, `_not_bonded_lane1_chain` `:990`, `_not_bonded_lane1_chain_reverse` `:1070`, `_mixed_chain` `:1150`, `_mixed_chain_reverse` `:1242`.
- **Tunnel alloc:** PCIe `tb_test_tunnel_pcie` `:1334`; DP `_dp` `:1389`, `_dp_chain` `:1427`, `_dp_tree` `:1473`, `_dp_max_length` `:1523`, `_3dp` `:1603`; USB3 `_usb3` `:1669`; DMA `_dma` `:1790`, `_dma_rx` `:1833`, `_dma_tx` `:1870`, `_dma_chain` `:1907`, `_dma_match` `:1973`; membership `tb_test_tunnel_port_on_path` `:1724`.
- **Credits (9):** `_legacy_not_bonded` `:2024`, `_legacy_bonded` `:2057`, `_pcie` `:2090`, `_without_dp` `:2123`, `_dp` `:2173`, `_usb3` `:2217`, `_dma` `:2250`, `_dma_multiple` `:2286`, `_all` `:2577` (uses the `TB_TEST_*` tunnel fixtures `:2383`, `:2413`, `:2450`, `:2487`, `:2517`, `:2547`).
- **Property parser/formatter (9):** `tb_test_property_parse` `:2667`, `_format` `:2727`, `_copy` `:2824`, `_parse_u32_wrap` `:2868`, `_parse_recursion` `:2899`, `_parse_dir_len_underflow` `:2939`, `_parse_zero_length` `:2979`, `_parse_rootdir_overflow` `:2999`, `_merge` `:3017`. Blob `root_directory[]` `:2607`, comparator `compare_dirs` `:2754`.
- **Fake-object helpers:** `__ida_init` `:15`, `__ida_destroy` `:24`, `kunit_ida_init` `:31`, `alloc_switch` `:36`, `alloc_host` `:72` (13-port 0x8086:0x9a1b host), `alloc_host_usb4` `:154`, `alloc_host_br` `:173` (third DP IN on port 10), `alloc_dev_default` `:190` (19-port device), `alloc_dev_with_dpin` `:340`, `alloc_dev_without_dp` `:361`, `alloc_dev_usb4` `:402`.
- **Not present at v7.2:** no wake tests and no bandwidth/DP-bandwidth tests (`grep -i 'wake\|bandwidth' drivers/thunderbolt/test.c` → no match). No `__ib_*` helpers exist anywhere in the subsystem.
- **v7.2 additions:** `c12b5ee30fb6` (XDomain property-parser regression tests: u32 wrap, recursion, dir-len underflow), `aa4999c0297a` (`tb_property_merge_dir()` test), `d73a08958e66` (property parser bounds: zero length, rootdir overflow), `168479c9bf07` (leak fix inside `tb_test_tunnel_3dp`, `tb_tunnel_put(tunnel3)` at `:1664` — no new test).

#### 10c. dma_test.c (`CONFIG_USB4_DMA_TEST`, `Kconfig:54`, `Makefile:14-15`) — the model

Objects: `struct dma_test` `drivers/thunderbolt/dma_test.c:91` (svc, xd, TX/RX `tb_ring` + HopIDs, packet counts, counters, `result`, `error_code`, completion, mutex); `struct dma_test_frame` `:27` wraps `struct ring_frame`; name tables `:45`, `:63`; 4 KB `dma_test_pattern` `:118`. Debugfs dir `"dma_test"` created under the *service* dir at `:627` (`dma_test_debugfs_init` `:623`, called from probe `:654`; removed with `debugfs_lookup_and_remove` `:664`), i.e. `<debugfs>/thunderbolt/<service>/dma_test/`. Files: `lanes` 0600 `:629`, `speed` 0600 `:630`, `packets_to_receive` 0600 `:631`, `packets_to_send` 0600 `:633` — all generated by `DMA_TEST_DEBUGFS_ATTR` `:361` (instantiated `:408`, `:432`, `:448`, `:465`); `status` 0400 `:635` (`status_show` `:596`, `DEFINE_SHOW_ATTRIBUTE` `:621`); `test` 0200 `:636` (`test_store` `:510`, `DEFINE_DEBUGFS_ATTRIBUTE` `:594`) — writing `1` runs the whole loopback test. Frames: `dma_test_submit_rx` `:264` → `tb_ring_rx` `:296`, callback `:233` counts `RING_DESC_CRC_ERROR`/`RING_DESC_BUFFER_OVERRUN` (`include/linux/thunderbolt.h:610`, `:613`); `dma_test_submit_tx` `:315` → `tb_ring_tx` `:355`, callback `:302`. Rings: `dma_test_start_rings` `:134` uses `tb_ring_alloc_tx` `:150` / `tb_ring_alloc_rx` `:176` with `RING_FLAG_FRAME` (+`RING_FLAG_E2E` when bidirectional), `tb_ring_throttling` `:158`/`:186`, `tb_ring_start` `:207`/`:209`; teardown `:214`, `:120`. Service driver: `dma_test_ids[] = { TB_SERVICE("dma_test", 1) }` `:690`, `struct tb_service_driver dma_test_driver` `:696` (`.probe` `:639`, `.remove` `:659`, `.pm` `:686`); registered from an explicit `module_init` `:749` / `module_exit` `:758` (not `module_tb_service_driver` — that helper does not exist in-tree) because init must also build the XDomain property directory and the pattern buffer first.

#### 10d. configfs.c and stream.c — features, not debug surfaces

Both are stated here as **product features**: `USB4_CONFIGFS` is `def_tristate USB4` (`Kconfig:21-23`, silently on whenever configfs is available, no DANGEROUS wording), and `USB4_STREAM` (`Kconfig:67-76`) describes user-facing functionality with documented ABI. Neither is gated on `DEBUG_FS` and neither carries a "only if you know what you are doing" warning, unlike `USB4_DEBUGFS_WRITE` `Kconfig:25` and `USB4_DMA_TEST` `Kconfig:54`.

- **configfs.c (61 lines)** — root subsystem plus a registration API only; **zero attributes of its own**. `tb_root_group_type` `:14` (empty item type), `tb_configfs` `:18` (`ci_namebuf = "thunderbolt"` `:21` → `/sys/kernel/config/thunderbolt/`), `tb_configfs_register_group` `:35` / `tb_configfs_unregister_group` `:45` (both `EXPORT_SYMBOL_GPL`, `:39`/`:49`), `tb_configfs_init` `:51` / `tb_configfs_exit` `:58` (called from `domain.c:890` and `domain.c:920`). Prototypes/stubs `tb.h:1562-1568`. The only in-tree consumer is stream.c.
- **stream.c configfs surface** — three levels: `tbstream_group` `:1471` (`"stream"`, ops `:1462`, type `:1466`, `make_group` `tbstream_make_group` `:1430`); the `<xdomain>.<service>` group type `:1423` with ops `:1405` (`tbstream_dev_make_group` `:1334`, `tbstream_dev_drop_item` `:1391`); the per-stream `$name` type `:1232` with `tbstream_dev_attrs[]` `:1210`. Attributes: `index` RO show `:905` (`CONFIGFS_ATTR_RO` `:912`); `in_hopid` RW `:914`/`:1084` (`:1108`); `out_hopid` RW `:1110`/`:1119` (`:1143`); `ring_size` RW `:1145`/`:1154` (`:1176`); `throttling` RW `:1178`/`:1187` (`:1208`). Char device: `struct miscdevice` `:143`, name `kasprintf("tbstream%d")` `:1373`, `misc_register` `:1377`, `misc_deregister` `:1224`, `tbstream_dev_fops` `:889`. Hook into configfs.c: `tb_configfs_register_group(&tbstream_group)` `:1666`, unregister `:1688`.

#### 10e. sysfs surfaces by object

**Domain — `domain.c`.** Array `domain_attrs[]` `:276`; group `domain_attr_group` `:301` (`.is_visible = domain_attr_is_visible` `:284`); groups `:306`; bound `tb->dev.groups` `:411`.

| attr | show / store | in array | visibility | CM | ABI line |
|---|---|---|---|---|---|
| `boot_acl` RW | `:121` / `:161` (`DEVICE_ATTR_RW` `:235`) | `:277` | `:290-296` needs `cm_ops->get/set_boot_acl` | **ICM-only** (ops only in `icm_ar_ops` `icm.c:2428-2429`, `icm_tr_ops` `icm.c:2450-2451`) | 1 |
| `deauthorization` RO | `:237` (`:251`) | `:278` | fallthrough `:298` | prints `!!cm_ops->disapprove_switch`, set **only** in `tb_cm_ops` `tb.c:3299` → always 0 under ICM | 24 |
| `iommu_dma_protection` RO | `:253` (`:261`) | `:279` | fallthrough | both | 33 |
| `security` RO | `:263` (`:274`) | `:280` | fallthrough | both; SW CM can only ever report `user`/`nopcie` (`tb.c:3384`, `:3386`) | 42 |

**Router/switch — `switch.c`.** `switch_attrs[]` `:2202`; `switch_group` `:2278` (`.is_visible = switch_attr_is_visible` `:2222`, safe-mode fallthrough `:2276`); groups `:2283`; bound `:2543` and `:2588`.

| attr | show / store (DEVICE_ATTR) | array | visibility branch | CM | ABI |
|---|---|---|---|---|---|
| `authorized` RW | `:1785` / `:1873` (`:1894`) | `:2203` | `:2228-2231` (hidden for nopcie/dponly) | **split**: `0` (de-auth) SW-CM-only; `1`+key and `2` (challenge) ICM-only (`add_switch_key`/`challenge_switch_key` only at `icm.c:2409/2410`, `:2431/2432`, `:2453/2454`) | 64 |
| `boot` RO | `:1896` (`:1903`) | `:2204` | `:2266-2269` | both (`icm.c:694/882/1314`, `tb.c:1706`) | 98 |
| `device` RO | `:1905` (`:1912`) | `:2205` | `:2232-2234` | both | 123 |
| `device_name` RO | `:1915` (`:1921`) | `:2206` | `:2235-2237` | both | 130 |
| `generation` RO | `:1924` (`:1930`) | `:2207` | fallthrough | both | 105 |
| `key` RW 0600 | `:1932` / `:1950` (`:1982`) | `:2208` | `:2244-2250` needs both security levels `secure` | **ICM-only** (`sw->security_level` assigned only at `icm.c:881`, `:1315`) | 113 |
| `nvm_authenticate` RW | `:2051` / `:2127` (`:2135`) | `:2209` | `:2257-2260` | both | 204 |
| `nvm_authenticate_on_disconnect` RW | `:2137` / `:2143` (`:2151`) | `:2210` | `:2269-2272` | both, quirk-gated (`quirks.c:10`, ids `:65-66`) | 232 |
| `nvm_version` RO | `:2153` (`:2173`) | `:2211` | `:2261-2263` | both | 195 |
| `rx_speed`/`tx_speed` RO | `speed_show` `:1984` (`:1996`, `:1997`) | `:2212`, `:2214` | `:2251-2256` | both | 144, 158 |
| `rx_lanes` RO | `:1999` (`:2023`) | `:2213` | `:2251-2256` | both | 151 |
| `tx_lanes` RO | `:2025` (`:2049`) | `:2215` | `:2251-2256` | both | 165 |
| `vendor` RO | `:2175` (`:2182`) | `:2216` | `:2238-2240` | both | 172 |
| `vendor_name` RO | `:2185` (`:2191`) | `:2217` | `:2241-2243` | both | 179 |
| `unique_id` RO | `:2193` (`:2200`) | `:2218` | fallthrough | both | 186 |

**Service — `xdomain.c`.** `tb_service_attrs[]` `:1092`; group `:1102` (**no** `.is_visible`); groups `:1106`; bound `tb_service_type.groups` `:1134`. `key` `:1026`/`:1037` (array `:1093`, ABI 246); `modalias` `:1045`/`:1054` (`:1094`, ABI 261); `prtcid` `:1056`/`:1063` (`:1095`, 268); `prtcvers` `:1065`/`:1072` (`:1096`, 275); `prtcrevs` `:1074`/`:1081` (`:1097`, 282); `prtcstns` `:1083`/`:1090` (`:1098`, 289). All CM-neutral.

**XDomain — `xdomain.c`.** `xdomain_attrs[]` `:1992`; group `:2006` (no `.is_visible` — all ten always present); groups `:2010`; bound `:2168`. `device` `:1863` (ABI 123), `device_name` `:1873` (130), `maxhopid` `:1887` (137), `rx_lanes` `:1940` (151), `rx_speed`/`tx_speed` `speed_show` `:1929` (144/158), `tx_lanes` `:1966` (165), `unique_id` `:1920` (186), `vendor` `:1896` (172), `vendor_name` `:1906` (179). No `authorized`/`key`/`boot`/`nvm_*` here.

**usb4_port — `usb4_port.c`.** Two groups on `usb4_port_device_type.groups` `:291` via `usb4_port_device_groups[]` `:276`: `common_group` `:72` (`common_attrs[]` `:67`, no visibility) and `service_group` `:271` (`service_attrs[]` `:252`, `.is_visible = service_attr_is_visible` `:258`, gate `usb4->can_offline` `:268`). `link` RO `:41`/`:65` (ABI 306); `offline` RW `:151`/`:159` (`:208`, ABI 313); `rescan` WO `:210` (`:250`, ABI 328); `connector` is a **symlink**, `sysfs_create_link` `:19` (+ reverse `:23`, teardown `:30-33`, `connector_ops` `:36`), ABI 296 — the only ABI entry lacking a `KernelVersion:`. Nothing here tests `cm_ops`/`tb_switch_is_icm`; the gate is platform/ACPI.

**Retimer — `retimer.c`.** `retimer_attrs[]` `:358`; group `:366` (`.is_visible = retimer_is_visible` `:345`, `no_nvm_upgrade` gate `:349-353`, fallthrough `:356`); groups `:371`; bound `tb_retimer_type.groups` `:385`. `device` `:169`/`:176` (ABI 339); `nvm_authenticate` `:178`/`:251` (`:315`, ABI 345); `nvm_version` `:317`/`:334` (ABI 360); `vendor` `:336`/`:343` (ABI 366). Both CMs.

**nvm.c — no sysfs attributes** (`grep -n "DEVICE_ATTR\|ATTRIBUTE_GROUPS\|is_visible\|attribute_group" drivers/thunderbolt/nvm.c` → zero matches). It contributes NVMEM children instead: `tb_nvm_add_active` `:433` (`name = "nvm_active"` `:439`, read-only `:442`) and `tb_nvm_add_non_active` `:503` (`"nvm_non_active"` `:509`, `root_only` `:511`) — **not documented as `What:` entries** in the ABI file (only referenced in prose at ABI lines 209 and 350 and `thunderbolt.rst:253`).

Subsystem-wide: `grep -rn "sysfs_create_link\|sysfs_create_group\|device_create_file" drivers/thunderbolt/*.c` matches **only** `usb4_port.c:19` and `:23`; every other attribute goes through `dev.groups` / `device_type.groups`.

#### 10f. uevents

- **`tb_tunnel_event()` `drivers/thunderbolt/tunnel.c:241`** (kernel-doc `:227-240`, enum `tb_tunnel_event` `tunnel.h:209-215`, decl `tunnel.h:217`). Builds `envp[0] = "TUNNEL_EVENT=%s"` `:253` from `tb_event_names[]` `:103` and `envp[1] = "TUNNEL_DETAILS=%llx:%u <-> %llx:%u (%s)"` `:258` (or the short `"TUNNEL_DETAILS=(%s)"` `:263` when ports are unknown), type names `tb_tunnel_names[] = { "PCI", "DP", "DMA", "USB3" }` `:101`; two `WARN_ON_ONCE` bounds checks `:248`, `:250`; delivered through `tb_domain_event()` `:268`.
- **`tb_domain_event()` `drivers/thunderbolt/tb.h:818`** → `kobject_uevent_env(&tb->dev.kobj, KOBJ_CHANGE, envp)` `:820` — the single domain-level notification funnel.
- Firing sites: SW CM — `tb_tunnel_set_active` `tunnel.c:278`/`:282`, `tb_tunnel_changed` `tunnel.c:289`, `tb.c:965` (`TB_TUNNEL_LOW_BANDWIDTH`, USB3), `tb.c:2021` and `tb.c:2730` (`NO_BANDWIDTH`, DP). **ICM** — `icm.c:392`/`:395` (DMA activated/deactivated) and `icm.c:401` (`TB_TUNNEL_CHANGED`, DP, with `NULL` ports so no `TUNNEL_DETAILS`), exactly as `tunnel.h:202-204` and `thunderbolt.rst:346-350` describe.
- **Service modalias/uevent — `xdomain.c`:** `get_modalias` `:1039`, `modalias_show` `:1045`, `tb_service_uevent` `:1111` → `add_uevent_var(env, "MODALIAS=%s")` `:1117`.
- **Other `kobject_uevent*` sites:** `switch.c:1813` (`AUTHORIZED=0` on disapprove), `switch.c:1865` (`AUTHORIZED=%u` on authorize), `switch.c:2309` `tb_switch_uevent` adding `USB4_VERSION=%u.0` `:2315` and `USB4_TYPE=%s` `:2338`, `switch.c:2890` (`KOBJ_CHANGE` from `tb_switch_update_link_attributes`), `tb.c:2988` (`KOBJ_ADD` from `tb_scan_finalize_switch`), `xdomain.c:1147` (service properties changed), `xdomain.c:1344` (`tb_xdomain_update_link_attributes`), `xdomain.c:1636` (properties obtained).

#### 10g. Fault injection, debuggers, dump/replay, in-tree tooling — verified negatives

`grep -rniE "fault_inject|should_fail|DECLARE_FAULT|kgdb|kdb|kmemleak|panic\(|dump_stack|print_hex_dump|error_inject|ALLOW_ERROR_INJECTION" drivers/thunderbolt/ include/linux/thunderbolt.h` returns exactly one hit, `test.c:2818` (`KUNIT_FAIL`). So: **no** fault/error injection, **no** in-kernel debugger hooks, **no** `dump_stack`/`print_hex_dump`, **no** panic path, **no** crash-dump or replay facility. `find tools/ samples/ -iname "*thunder*" -o -iname "*usb4*" -o -iname "*tbt*"` finds only `tools/perf/pmu-events/arch/arm64/cavium/thunderx2` (unrelated) — **no in-tree userspace tooling**. The only "replay-ish" surface is the debugfs register/sideband write path, which taints the kernel (`debugfs.c:242`, `:339`).

**External tools named in the docs (note them as external, not kernel-provided):** `fwupd` — `Documentation/admin-guide/thunderbolt.rst:206`, `:209` (`https://github.com/fwupd/fwupd`), `:218`, `:221`, `:230`, `:231`, `:239`, `:243`; LVFS `:207`; `ip` `:373`; the WMI `force_power` pointer `:443`. `tbtools` is **not** in `thunderbolt.rst` (grep → no hit); it appears in `drivers/thunderbolt/Kconfig:33` (`https://github.com/intel/tbtools`) and in `Documentation/ABI/testing/configfs-thunderbolt_stream:13`, `:15`, `:19`, `:49`, `:53`. `bolt`/`boltctl` is named nowhere.

#### 10h. Documentation surface

**`Documentation/admin-guide/thunderbolt.rst` — 13 headings (title + 12 sections; no sub-sections):** 4 "USB4 and Thunderbolt" (title); 24 "Security levels and how to use them"; 101 "Authorizing devices when security level is ``user`` or ``secure``"; 163 "De-authorizing devices"; 179 "DMA protection utilizing IOMMU"; 199 "Upgrading NVM on Thunderbolt device, host or retimer"; 241 "Upgrading firmware manually"; 279 "Upgrading on-board retimer NVM when there is no cable connected"; 308 "Upgrading NVM when host controller is in safe mode"; 319 "Tunneling events"; 352 "Networking over Thunderbolt cable"; 376 "Streaming data directly over Thunderbolt cable"; 437 "Forcing power".

**`Documentation/ABI/testing/sysfs-bus-thunderbolt` — 35 `What:` entries** (line → path → KernelVersion): 1 `domainX/boot_acl` 4.17; 24 `domainX/deauthorization` 5.12; 33 `domainX/iommu_dma_protection` 4.21; 42 `domainX/security` 4.13; 64 `authorized` 4.13; 98 `boot` 4.17; 105 `generation` 5.5; 113 `key` 4.13; 123 `device` 4.13; 130 `device_name` 4.13; 137 `maxhopid` 5.13 (XDomain only); 144 `rx_speed` 5.5; 151 `rx_lanes` 5.5; 158 `tx_speed` 5.5; 165 `tx_lanes` 5.5; 172 `vendor` 4.13; 179 `vendor_name` 4.13; 186 `unique_id` 4.13; 195 `nvm_version` 4.13; 204 `nvm_authenticate` 4.13; 232 `nvm_authenticate_on_disconnect` v5.9; 246 `<xdomain>.<service>/key` 4.15; 261 `…/modalias` 4.15; 268 `…/prtcid` 4.15; 275 `…/prtcvers` 4.15; 282 `…/prtcrevs` 4.15; 289 `…/prtcstns` 4.15; 296 `usb4_portX/connector` (**no KernelVersion**, `Date: April 2022`); 306 `usb4_portX/link` v5.14; 313 `usb4_portX/offline` v5.14; 328 `usb4_portX/rescan` v5.14; 339 retimer `device` v5.9; 345 retimer `nvm_authenticate` v5.9; 360 retimer `nvm_version` v5.9; 366 retimer `vendor` v5.9.

**`Documentation/ABI/testing/configfs-thunderbolt_stream` — 7 `What:` entries, all `Date: Sep 2026` / `KernelVersion: v7.2`:** 1 `stream/<xdomain>.<service>`; 21 `…/$name`; 30 `…/$name/index`; 39 `…/$name/in_hopid`; 58 `…/$name/out_hopid`; 69 `…/$name/ring_size` (32–4096, default 256); 77 `…/$name/throttling` (ns, default 8192).

Every `DEVICE_ATTR` in 10e maps to one of those `What:` lines (the per-object cross-reference is in the 10e table). The only undocumented sysfs surface is the two NVMEM children from `nvm.c`.

#### 10i. Vendor-named predicates and helpers — do-not-cite list

All in `drivers/thunderbolt/tb.h`, all matching on `PCI_VENDOR_ID_INTEL` + specific device IDs: `tb_switch_is_light_ridge` `:933`, `tb_switch_is_eagle_ridge` `:939`, `tb_switch_is_cactus_ridge` `:945`, `tb_switch_is_falcon_ridge` `:957`, `tb_switch_is_alpine_ridge` `:969`, `tb_switch_is_titan_ridge` `:984`, `tb_switch_is_tiger_lake` `:997`.

Also vendor-bearing and excluded from pages: the whole quirk table `tb_quirks[]` `drivers/thunderbolt/quirks.c:63-117` and its hooks `quirk_force_power_link` `:10` (Dell WD19TB), `quirk_dp_credit_allocation` `:16` (Intel Goshen Ridge), `quirk_clx_disable` `:24` (Intel Titan Ridge + AMD Yellow Carp/Pink Sardine `:113-116`), `quirk_usb3_maximum_bandwidth` `:33` (Intel ADL/RPL/MTL/Barlow Ridge), `quirk_block_rpm_in_redrive` `:49` (Intel Barlow Ridge) — plus `tb_check_quirks` `:125` whose `tb_sw_dbg(sw, "running %ps", q->hook)` `:141` prints the vendor hook name into the log.

**Safe to cite** (vendor-neutral, same naming shape): `tb_port_is_null` `tb.h:632`, `tb_port_is_nhi` `:637`, `tb_port_is_pcie_down` `:642`, `tb_port_is_pcie_up` `:647`, `tb_port_is_dpin` `:652`, `tb_port_is_dpout` `:657`, `tb_port_is_usb3_down` `:662`, `tb_port_is_usb3_up` `:667`, `tb_port_is_enabled` `:1176`, `tb_switch_is_usb4` `:1322`, and **`tb_switch_is_icm` `tb.h:1023`** (`return !sw->config.enabled;`) — the canonical CM-mode discriminator, which names a mode rather than a vendor part.

### Sweep S2: asynchronous, deferred and lazy processing, and the locking model — COMPLETE (recorded 2026-09-04)

**USB4/Thunderbolt async, deferred & lazy processing + locking model — v7.2 (8d3ae59288f1, `git describe --tags` = v7.2)**
Scope: all of `drivers/thunderbolt/` + `include/linux/thunderbolt.h`. ICM (firmware CM) items are marked ICM-only and not detailed. Kconfig gates from `drivers/thunderbolt/Kconfig`/`Makefile`: `CONFIG_USB4` (core), `CONFIG_ACPI`→acpi.o, `CONFIG_DEBUG_FS`→debugfs.o, `CONFIG_USB4_CONFIGFS`→configfs.o, `CONFIG_USB4_KUNIT_TEST`→test.o, `CONFIG_USB4_DMA_TEST`→dma_test.o, `CONFIG_USB4_STREAM`→stream.o, `CONFIG_USB4_DEBUGFS_WRITE`/`CONFIG_USB4_DEBUGFS_MARGINING` (debugfs features), `CONFIG_PM` (dev_pm_ops/pm_runtime). Note: there is no `CONFIG_USB4_DEBUGFS_*` other than WRITE/MARGINING.

#### 9a. Workqueues

Query: `grep -rn "alloc_workqueue\|alloc_ordered_workqueue\|create_.*workqueue\|destroy_workqueue\|flush_workqueue\|drain_workqueue" drivers/thunderbolt/ include/linux/thunderbolt.h`

- `drivers/thunderbolt/domain.c:400` — `tb->wq = alloc_ordered_workqueue("thunderbolt%d", 0, tb->index)`; name `thunderbolt<index>`, flags `0` (ordered ⇒ `WQ_UNBOUND|max_active=1`), owner `struct tb` (`include/linux/thunderbolt.h:87`, doc'd "Ordered workqueue for all domain specific work" at :74).
- Destroy: `drivers/thunderbolt/domain.c:418` (alloc error path) and `drivers/thunderbolt/domain.c:325` in `tb_domain_release()`; drain point `drivers/thunderbolt/domain.c:512` `flush_workqueue(tb->wq)` in `tb_domain_remove()` after `tb_ctl_stop()`.
- **Verified negative**: no other `alloc_workqueue`/`create_workqueue` in the subsystem. There is **no separate xdomain workqueue** — XDomain state/properties work runs on `tb->wq`, and the XDP request work runs on the **system** workqueue (`schedule_work`, `drivers/thunderbolt/xdomain.c:957`).
- **Verified negative**: `stream.c`, `dma_test.c`, `nhi.c`, `pci.c` allocate no workqueue; `nhi->interrupt_work`, `ring->work`, `ctl` request work all use `system_wq` via `schedule_work`; the DP bandwidth-group release work uses `system_percpu_wq` (`drivers/thunderbolt/tb.c:2644`).

#### 9b. Work items and delayed work

Query: `grep -rn "INIT_WORK\|INIT_DELAYED_WORK\|queue_work\|queue_delayed_work\|schedule_work\|schedule_delayed_work\|mod_delayed_work\|flush_work\|cancel_work\|cancel_delayed_work\|struct work_struct\|struct delayed_work" drivers/thunderbolt/ include/linux/thunderbolt.h`

**tb.c software CM**

- `tb_hotplug_event.work` — field `drivers/thunderbolt/tb.c:78`; `INIT_DELAYED_WORK(&ev->work, tb_handle_hotplug)` `tb.c:105`; queued `tb.c:106` `queue_delayed_work(tb->wq, &ev->work, 0)` (**delay 0**, no retry for hotplug); handler `tb_handle_hotplug` `tb.c:2421`, frees `ev` at end; ctx = `tb->wq` (ordered).
- `tb_hotplug_event` reused for DP BW requests — `INIT_DELAYED_WORK(&ev->work, tb_handle_dp_bandwidth_request)` `tb.c:2881`; `queue_delayed_work(tb->wq, &ev->work, delay)` `tb.c:2882`. First queue from notification path `tb.c:2902` with `retry=0, delay=0`; retry re-queue `tb.c:2833-2836` with `ev->retry+1` and `msecs_to_jiffies(50)` (**50 ms**), capped by `TB_BW_ALLOC_RETRIES` = **3** (`tb.c:26`). Handler `tb.c:2736`.
- `tb_cm.remove_work` — field `tb.c:68`; `INIT_DELAYED_WORK(&tcm->remove_work, tb_remove_work)` `tb.c:3393`; queued only from `tb_runtime_resume()` `tb.c:3283` with `msecs_to_jiffies(50)` (**50 ms**) on `tb->wq`; handler `tb_remove_work` `tb.c:3250`; cancel `cancel_delayed_work(&tcm->remove_work)` in `tb_stop()` `tb.c:2947` (non-sync).
- `tb_bandwidth_group.release_work` — field `drivers/thunderbolt/tb.h:243`; `INIT_DELAYED_WORK(..., tb_bandwidth_group_release_work)` `tb.c:1590`; **`mod_delayed_work(system_percpu_wq, ...)`** `tb.c:2644` with `msecs_to_jiffies(TB_RELEASE_BW_TIMEOUT)` = **10000 ms** (`tb.c:20`); handler `tb.c:1567`; cancels `cancel_delayed_work()` `tb.c:1688` (group emptied) and `cancel_delayed_work_sync()` for all `MAX_GROUPS` in `tb_deinit()` `tb.c:2971`.

**ctl.c control channel**

- `tb_cfg_request.work` — field `drivers/thunderbolt/ctl.h:93`; `INIT_WORK(&req->work, tb_cfg_request_work)` `ctl.c:555`; `schedule_work()` on **system_wq** at `ctl.c:516` (response matched in RX callback), `ctl.c:569` (no-response requests), `ctl.c:592` (cancel path); handler `ctl.c:524`; `flush_work(&req->work)` `ctl.c:634` in `tb_cfg_request_sync()`.

**nhi.c / pci.c DMA rings**

- `tb_ring.work` — field `include/linux/thunderbolt.h:574`; `INIT_WORK(&ring->work, ring_work)` `nhi.c:548`; `schedule_work()` from `__ring_interrupt()` `nhi.c:405` (system_wq, IRQ ctx) and from `tb_ring_stop()` `nhi.c:781`; handler `ring_work` `nhi.c:268`; flushes `nhi.c:782` (stop) and `nhi.c:835` (`tb_ring_free`, "ring->work can no longer be scheduled").
- `tb_nhi.interrupt_work` — field `include/linux/thunderbolt.h:527`; `INIT_WORK(&nhi->interrupt_work, nhi_interrupt_work)` **only in the MSI (non-MSI-X) fallback** `pci.c:133`; `schedule_work()` from `nhi_msi()` `nhi.c:971`; handler `nhi_interrupt_work` `nhi.c:918`; `flush_work()` `pci.c:244` in `nhi_pci_shutdown()`, deliberately after `devm_free_irq()` `pci.c:243` (comment `pci.c:239-240`).

**xdomain.c**

- `xdomain_request_work.work` — field `xdomain.c:56`; `INIT_WORK(&xw->work, tb_xdp_handle_request)` `xdomain.c:948`; `schedule_work()` `xdomain.c:957` on **system_wq** (not `tb->wq`); handler `xdomain.c:758`; no cancel/flush — lifetime guarded by `tb_domain_get()`/`tb_domain_put()` and by `xd->removing`.
- `xd->state_work` — field `include/linux/thunderbolt.h:278`; `INIT_DELAYED_WORK` `xdomain.c:2144`; handler `tb_xdomain_state_work` `xdomain.c:1720`; all queues on `xd->tb->wq`: `start_handshake` `xdomain.c:740` (`XDOMAIN_SHORT_TIMEOUT` = **100 ms**), request handlers `xdomain.c:815`, `:906` (100 ms, under `xd->lock` + `!xd->removing`), state queues `:1655`(100 ms) `:1663` `:1671` `:1687` `:1695` `:1703` `:1717` and failure `:1834` (`XDOMAIN_DEFAULT_TIMEOUT` = **1000 ms**), retry `:1716`/`retry_state` label (1000 ms). Cancel `cancel_delayed_work_sync()` `xdomain.c:754` (`stop_handshake`).
- `xd->properties_changed_work` — field `include/linux/thunderbolt.h:280`; `INIT_DELAYED_WORK` `xdomain.c:2145`; handler `tb_xdomain_properties_changed` `xdomain.c:1838`; queues `xdomain.c:1709` (100 ms), `:996` from `update_xdomain()` (**50 ms**, under `xd->lock`), self-retry `:1852-1854` (1000 ms). Cancel `cancel_delayed_work_sync()` `xdomain.c:747` (`__stop_handshake`).

**tunnel.c**

- `tb_tunnel.dprx_work` — field `drivers/thunderbolt/tunnel.h:106`; `INIT_DELAYED_WORK(&tunnel->dprx_work, tb_dp_dprx_work)` `tunnel.c:1721`; queued `tunnel.c:1126` with delay **0** from `tb_dp_dprx_start()`, re-queued `tunnel.c:1098-1099` with `msecs_to_jiffies(TB_DPRX_POLL_DELAY)` = **50 ms** (`tunnel.c:83`); handler `tunnel.c:1088`; cancel `cancel_delayed_work(&tunnel->dprx_work)` `tunnel.c:1139` in `tb_dp_dprx_stop()`, dropping the tunnel ref on success.

**Others**

- `stream.c` (CONFIG_USB4_STREAM): **verified negative** — no work_struct/delayed_work; completions handled in ring callbacks (which run in `ring_work` context) plus waitqueue wakeups.
- `dma_test.c` (CONFIG_USB4_DMA_TEST): **verified negative** — no work items; uses a completion.
- `retimer.c`, `nvm.c`, `switch.c`, `debugfs.c`, `usb4_port.c`, `configfs.c`, `acpi.c`, `path.c`, `clx.c`, `tmu.c`, `lc.c`, `eeprom.c`, `quirks.c`, `cap.c`, `test.c`: **verified negative** — no work_struct/delayed_work at all (no NVM or retimer worker exists; NVM authentication is fully synchronous in the writer's context).
- ICM-only (not detailed): `icm->rescan_work` (`icm.c:96`, `:2490`, `:2120`, queued `:348`/`:2160`, cancel `:2228`) and `icm_notification.work` (`icm.c:127`, `:1796`, `:1799`) — both on `tb->wq`.

#### 9c. Completions

Query: `grep -rn "struct completion\|init_completion\|reinit_completion\|complete_all\|wait_for_completion\|complete(" drivers/thunderbolt/ include/linux/thunderbolt.h`

- `tb_cfg_request_sync()` stack completion — `DECLARE_COMPLETION_ONSTACK(done)` `ctl.c:626`; signalled by `tb_cfg_request_complete()` `ctl.c:597-599`; `wait_for_completion_timeout(&done, timeout)` `ctl.c:631` with `timeout = msecs_to_jiffies(timeout_msec)` `ctl.c:620` — default per domain `TB_TIMEOUT` = **100 ms** (`tb.c:19`, `tb.c:3379`), ICM domains 5000 ms.
- `tb_nhi.domain_released` (**new in v7.2**) — field `include/linux/thunderbolt.h:530`; `init_completion()` `nhi.c:1229` (moved earlier by 9cbc63400f7d to fix an uninit-completion crash on `icm_probe()` failure); completed in `tb_domain_release()` `domain.c:330` after `destroy_workqueue`/`mutex_destroy`/`kfree(tb)`; waited **untimed** at `nhi.c:1245` (probe error path) and `pci.c:492` (`nhi_pci_remove`, before `nhi_shutdown`).
- `dma_test.complete` (CONFIG_USB4_DMA_TEST) — field `dma_test.c:108`; `init_completion()` `dma_test.c:651`; `reinit_completion()` `dma_test.c:559`; `complete()` from the RX ring callback when all packets arrive `dma_test.c:261`; `wait_for_completion_interruptible()` `dma_test.c:578` (**no timeout** — interruptible; suspend interaction documented `dma_test.c:673`).
- **Verified negative**: no completions in `xdomain.c` or `stream.c` (stream uses waitqueues only).
- ICM-only: `tb_switch.rpm_complete` (`tb.h:208`, `icm.c:657/700/2076/2172/2179`, 500 ms timeout).

#### 9d. Wait queues, timers, IRQ, RCU, notifiers, async, kref

Queries: `grep -rn "wait_queue\|wait_event\|wake_up\|init_waitqueue"`, `grep -rn "timer_setup\|mod_timer\|del_timer\|timer_delete\|hrtimer\|tasklet\|irq_work\|kthread_\|struct timer_list"`, `grep -rn "request_irq\|request_threaded_irq\|devm_request_irq\|pci_request_irq\|free_irq\|IRQF_"`, `grep -rn "rcu_read_lock\|call_rcu\|synchronize_rcu\|kfree_rcu\|srcu\|rcu_dereference"`, `grep -rn "notifier"`, `grep -rn "async_schedule\|task_work_add"`, `grep -rn "kref"` — all over `drivers/thunderbolt/` + `include/linux/thunderbolt.h`.

**Wait queues (4)**

- `tb_cfg_request_cancel_queue` — `DECLARE_WAIT_QUEUE_HEAD` `ctl.c:76` (file-global); `wake_up()` `ctl.c:164` when a canceled request is dequeued; `wait_event()` `ctl.c:593` in `tb_cfg_request_cancel()` (uninterruptible, no timeout).
- `tb_ring.wait` — `include/linux/thunderbolt.h:586`; `init_waitqueue_head()` `nhi.c:549`; `wake_up()` at end of `ring_work` `nhi.c:317`; `wait_event_timeout(ring->wait, tb_ring_empty(ring), msecs_to_jiffies(timeout_msec))` `nhi.c:730-731` in `tb_ring_flush()`.
- `tbstream_dev.wait` (CONFIG_USB4_STREAM) — `stream.c:153`; `init_waitqueue_head()` `stream.c:1361`; wakeups `stream.c:360` (RX, `EPOLLIN`), `:453` (TX, `EPOLLOUT`), `:1297` (stream attached), `:1324` and `:1401` (`EPOLLHUP|EPOLLERR` on detach/group removal); `wait_event_interruptible()` `stream.c:654` (read), `:746` (write), `:831` (open waits for a stream).
- **Verified negative**: no waitqueue in `xdomain.c`, `tb.c`, `switch.c`, `dma_test.c`.

**Timers / hrtimers / tasklets / irq_work / kthreads: verified negative** — zero hits for `timer_setup`, `mod_timer`, `timer_delete`, `hrtimer_*`, `tasklet_*`, `irq_work_*`, `kthread_*`, `struct timer_list` anywhere in the subsystem or header. All time-based deferral is `delayed_work` (jiffies timer inside the workqueue core) or `pm_runtime` autosuspend.

**IRQs (all in pci.c; hard IRQ only, no threaded IRQ)**

- `devm_request_irq(&pdev->dev, irq, nhi_msi, IRQF_NO_SUSPEND, "thunderbolt", nhi)` `pci.c:139-140` — single-MSI fallback; handler `nhi_msi()` `nhi.c:968` just does `schedule_work(&nhi->interrupt_work)`. Released `devm_free_irq()` `pci.c:243`.
- `request_irq(ring->irq, ring_msix, irqflags, "thunderbolt", ring)` `pci.c:208`, `irqflags = no_suspend ? IRQF_NO_SUSPEND : 0` `pci.c:207` — per-ring MSI-X (`MSIX_MIN_VECS`..`MSIX_MAX_VECS`, `pci_alloc_irq_vectors` `pci.c:126`); handler `ring_msix()` `nhi.c:444` takes `nhi->lock` then `ring->lock` and calls `__ring_interrupt()`. Released `free_irq()` `pci.c:227`.
- **Verified negative**: no `request_threaded_irq`, no `pci_request_irq`, no `IRQF_ONESHOT`/`IRQF_SHARED`.

**RCU/SRCU: verified negative** — no `rcu_read_lock`, `call_rcu`, `synchronize_rcu`, `kfree_rcu`, `*_rcu` list iteration, or SRCU anywhere in `drivers/thunderbolt/` or `include/linux/thunderbolt.h`.

**Notifier chains: verified negative** — no `*_notifier_*` registration or `notifier_call` in the subsystem. The nearest equivalents are synchronous callback vectors: `tb_ctl` `event_cb` (`ctl.c` → `tb_domain_event_cb` `domain.c:377` → `cm_ops->handle_event`), the `tb_protocol_handler` list (`xdomain.c:78`, register/unregister `xdomain.c:619-646` under `xdomain_lock`, dispatched synchronously from the ctl RX path), and `tb_cm_ops` — all dispatched synchronously in the caller's context. [orchestrator note 2026-09-04, review item 26: `tb_domain_event_cb` is defined at domain.c:338; domain.c:377 is `tb_domain_alloc`.]

**async_schedule / task_work: verified negative** — no `async_schedule*`, no `async_synchronize*`, no `task_work_add`.

**krefs (4)** — every other refcount here is a `struct device` refcount (`tb_switch_get/put`, `tb_domain_get/put`, `tb_xdomain_get/put`, `tb_service_get/put` — all `get_device()/put_device()`).

- `tb_cfg_request.kref` `ctl.h:78` — `kref_init` `ctl.c:96`, `get` `ctl.c:108`, `put` `ctl.c:129`, release `tb_cfg_request_destroy()` `ctl.c:112` → `kfree(req)`. get/put serialized by `tb_cfg_request_lock` (`ctl.c:78`).
- `tb_tunnel.kref` `tunnel.h:74` — `kref_init` `tunnel.c:192`, `get` `tunnel.c:200`, `put` `tunnel.c:223`, release `tb_tunnel_destroy()` `tunnel.c:204` → calls `tunnel->destroy`, frees all `tb_path`s and the tunnel. Serialized by `tb_tunnel_lock` (`tunnel.c:112`).
- `tbstream.kref` `stream.c:144` — `kref_init` `stream.c:1552`, release `tbstream_release()` `stream.c:212` → `tb_service_put()` + `kfree(stream)`; serialized by `tbstream_kref_lock` (`stream.c:200`).
- `tbstream_dev.kref` `stream.c:188` — `kref_init` `stream.c:1364`, release `tbstream_dev_release()` `stream.c:284`; serialized by `tbstream_dev_kref_lock` (`stream.c:203`).

**Atomics** — `atomic_t tb_xdomain.ntunnels` `include/linux/thunderbolt.h:284`: `atomic_set(...,0)` `xdomain.c:2147`, `atomic_inc` `xdomain.c:2450` (`tb_xdomain_enable_paths`), `atomic_dec` `xdomain.c:2481` (`tb_xdomain_disable_paths`); read only by ICM (`icm.c:590`, `:1166`). No `refcount_t` anywhere in the subsystem (verified negative).

#### 9e. pm_runtime (all gated by `CONFIG_PM`; stubs otherwise)

Query: `grep -rn "pm_runtime_" drivers/thunderbolt/ include/linux/thunderbolt.h`

**Autosuspend delay** — one constant, `TB_AUTOSUSPEND_DELAY` = **15000 ms** (`drivers/thunderbolt/tb.h:550`), used at every `pm_runtime_set_autosuspend_delay()` site:

| site | device |
|---|---|
| `drivers/thunderbolt/nhi.c:1254` | NHI (`nhi_probe`), paired with `pm_runtime_allow()` `nhi.c:1253`, `use_autosuspend` `:1255`, `put_autosuspend` `:1256` |
| `drivers/thunderbolt/domain.c:481` | `tb->dev` domain (`tb_domain_add`), `:478-483` block |
| `drivers/thunderbolt/switch.c:3404` | `sw->dev` router, only when `sw->rpm`; `pm_request_autosuspend()` `:3408` |
| `drivers/thunderbolt/retimer.c:457` | `rt->dev` retimer |
| `drivers/thunderbolt/usb4_port.c:335` | `usb4->dev` USB4 port |

**forbid/allow/dont_use** — `pm_runtime_allow(dev)` `nhi.c:1253`; `pm_runtime_forbid(&pdev->dev)` `pci.c:489` and `pm_runtime_dont_use_autosuspend()` `pci.c:488` in `nhi_pci_remove()`. No other forbid/allow sites (verified negative).

**Usage count per file** (counts of literal calls):

| file | get_sync | get_noresume | get | mark_last_busy | put_autosuspend | put | put_noidle | forbid+allow |
|---|---|---|---|---|---|---|---|---|
| tb.c | 9 | 0 | 1 | 9 | 9 | 2 | 0 | 0 |
| debugfs.c | 11 | 0 | 0 | 11 | 11 | 0 | 0 | 0 |
| icm.c (ICM-only) | 7 | 0 | 1 | 7 | 7 | 0 | 0 | 0 |
| switch.c | 4 | 0 | 0 | 4 | 3 | 0 | 0 | 0 |
| domain.c | 2 | 0 | 0 | 3 | 2 | 0 | 0 | 0 |
| retimer.c | 2 | 0 | 0 | 3 | 2 | 0 | 0 | 0 |
| usb4_port.c | 2 | 0 | 0 | 3 | 2 | 0 | 0 | 0 |
| pci.c | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 2 |
| acpi.c | 1 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| nhi.c | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| xdomain.c | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |

Notable asymmetric refs (deliberate long-lived pins): `pm_runtime_get_noresume(&xd->dev)` `xdomain.c:2180` (XDomain keeps DMA powered for its whole life; undone `xdomain.c:2242-2244` only when never registered); `pm_runtime_get(&sw->dev)` `tb.c:2124` / `put` `tb.c:2142`, `:2172` for DP "redrive" mode (`QUIRK_KEEP_POWER_IN_DP_REDRIVE`); `pm_runtime_get_sync()` on both DP tunnel ends `tb.c:2000-2001` and `tb.c:1714-1715` released at teardown `tb.c:2057-2060`, `tb.c:1751-1754`; `pm_runtime_get_noresume(&root_port->dev)` `pci.c:171` around host NVM authentication, released `pci.c:181`.

#### 9f. Polling loops

Query: `grep -rn "msleep\|usleep_range\|fsleep\|udelay\|read_poll_timeout\|ktime_get\|ktime_before\|time_before\|jiffies" drivers/thunderbolt/` (no `read_poll_timeout`/`readx_poll_timeout`/`readl_poll_timeout` users at all — verified negative; all loops are hand-rolled ktime/jiffies).

| file:line (loop body) | interval | timeout (const → value) | waits for |
|---|---|---|---|
| `ctl.c:1001` | `usleep_range(10,100)` | `TB_CTL_RETRIES` = 4 (`ctl.c:22`) | retry of a timed-out config-space **read** |
| `ctl.c:1077` | `usleep_range(10,100)` | `TB_CTL_RETRIES` = 4 | retry of a timed-out config-space **write** |
| `nhi.c:887` | `usleep_range(10,20)` | `NHI_MAILBOX_TIMEOUT` = 500 ms (`nhi.c:37`) | `REG_INMAIL_OP_REQUEST` clear (NHI mailbox done) |
| `nhi.c:1148` `msleep(100)` then `nhi.c:1157` | `usleep_range(10,20)` | 500 ms literal (`nhi.c:1150`) | `REG_RESET_HRR` clear (host router reset) |
| `pci.c:319` | `usleep_range(3000,3100)` | `retries = 350` (`pci.c:311`) ≈ 1.05 s | `VS_CAP_9_FW_READY` (ICL force-power FW up) |
| `pci.c:351` | `usleep_range(1000,1100)` | `ICL_LC_MAILBOX_TIMEOUT` = 500 ms (`pci.c:266`) | `VS_CAP_18_DONE` (ICL LC mailbox complete) |
| `dma_port.c:251` | `usleep_range(50,100)` | caller-supplied; `DMA_PORT_TIMEOUT` = 5000 ms (`dma_port.c:44`), `DMA_PORT_RETRIES` = 3 (`:45`) | `MAIL_IN_OP_REQUEST` clear (DMA port flash op) |
| `switch.c:206` | `msleep(500)` | `retries = 10` (`switch.c:169`) = 5 s | device NVM authentication status via DMA port |
| `switch.c:523` / `switch.c:548` | `msleep(100)` | `retries = 10` (`switch.c:500`) = 1 s | port reaches `TB_PORT_UP` (`tb_wait_for_port`) |
| `switch.c:1228` | `usleep_range(1000,2000)` | caller: 100 ms (`switch.c:2990,3030,3068,3106`), `XDOMAIN_BONDING_TIMEOUT` = 10000 ms (`xdomain.c:1519`, `:2308`), 100 ms (`xdomain.c:2338`) | link reaches requested width (lane bonding / asym) |
| `switch.c:1739` | `usleep_range(50,100)` | callers: 500 ms (`usb4.c:79,301,334,523`), 100 ms (`switch.c:3918`) | router CS bit: `ROUTER_CS_26_OV` (router op done), `_RR`, `_CR`, `_SLPR`, PCIe cmd ack |
| `usb4.c:1321` | `fsleep(delay_usec)` | caller-supplied | generic `usb4_port_wait_for_bit()` |
| `usb4.c:1381`, `usb4.c:1441` | `USB4_PORT_SB_DELAY` = 1000 µs (`usb4.c:52`) | 500 ms | `PORT_CS_1_PND` clear (sideband read/write pending) |
| `usb4.c:1498` | `fsleep(USB4_PORT_SB_DELAY)` = 1000 µs | caller-supplied `timeout_msec` | sideband **opcode** completion (`USB4_SB_OPCODE` != opcode) |
| `usb4.c:1688` | `USB4_PORT_DELAY` = 50 µs (`usb4.c:51`) | 1000 ms | `PORT_CS_19_START_ASYM` clear (asym transition started) |
| `usb4.c:1695` | `USB4_PORT_DELAY` = 50 µs | 5000 ms | `PORT_CS_18_TIP` clear (width transition complete) |
| `usb4.c:2253` | `USB4_PORT_DELAY` = 50 µs | 1500 ms | `ADP_USB3_CS_1_HCA` == CMR (USB3 CM request handshake) |
| `usb4.c:1195` | `fsleep(10000)` (single 10 ms) | — | after setting `PORT_CS_19_DPR` (downstream port reset) |
| `usb4.c:3022` | `usleep_range(50,100)` | caller `timeout_msec` | `ADP_DP_CS_8_DR` clear (DPTX request cleared) |
| `lc.c:85` | `fsleep(10000)` (single 10 ms) | — | LC `TB_LC_PORT_MODE_DPR` pulse |
| `retimer.c:153` | `usleep_range(100,150)` (single) | — | settle before reading retimer NVM auth status |
| `tmu.c:521` | `usleep_range(5,10)` | `retries = 100` (`tmu.c:453`) | TMU **post time** converges to 0 |
| `path.c:430` | `usleep_range(10,20)` | 500 ms literal (`path.c:401`) | `hop.pending` clear (path hop drained on deactivate) |
| `tunnel.c:306` | `fsleep(50)` | 500 ms literal (`tunnel.c:295`) | **PCIe LTSSM** reaches `USB4_PCIE_LTSSM_DETECT` |
| `tunnel.c:654` | `usleep_range(100,150)` | caller `timeout_msec` | `DP_STATUS_CTRL_CMHS` clear (DP CM handshake) |
| `tunnel.c:1081` | `usleep_range(100,150)` | `TB_DPRX_WAIT_TIMEOUT` = 25 ms from the worker (`tunnel.c:82`), else module param `dprx_timeout` default `TB_DPRX_TIMEOUT` = 12000 ms (`tunnel.c:81`, `:84`) | `DP_COMMON_CAP_DPRX_DONE` (**DPRX read done**) |
| `tb.c:3181` | `msleep(usb3_delay)` — 500 ms once if any USB3 tunnel | — | USB3 needs settle time before re-activation on resume |
| `tb.c:3193` | `msleep(100)` once | — | "pcie links need some time to get going" after resume |
| `debugfs.c:1188` | `fsleep(DWELL_SAMPLE_INTERVAL * USEC_PER_MSEC)` = 10 ms (`debugfs.c:46`) | `dwell_time` clamped `MIN_DWELL_TIME` 100 ms .. `MAX_DWELL_TIME` 500 ms (`debugfs.c:44-45`, `:1024`) | SW margining error-counter sampling (CONFIG_USB4_DEBUGFS_MARGINING) |
| `nvm.c:578` / `nvm.c:626` | no sleep, immediate `continue` | `USB4_DATA_RETRIES` = 3 (`usb4.c:18`), `DMA_PORT_RETRIES` = 3 | NVM block read/write retry |
| ICM-only | `icm.c:227` (50 ms/`ICM_TIMEOUT` 5000 ms), `:332`, `:632`, `:1230`, `:1519`, `:1729`, `:1830`, `:1883`, `:1939` | | mailbox / PCIe2CIO polling |

`eeprom.c`, `clx.c`, `cap.c`, `quirks.c`, `configfs.c`, `usb4_port.c`, `stream.c`, `dma_test.c`: **verified negative** — no delay/poll loops (eeprom.c bit-bangs with no sleeps).

#### 9g. Lazy / deferred designs

- **Hotplug is fully deferred, never retried.** `tb_queue_hotplug()` `tb.c:98-107` allocates an event, takes a domain ref, and queues at delay 0 on the ordered `tb->wq`; `tb_handle_hotplug()` `tb.c:2421` does all topology work under `tb->lock`. `tb_hotplug_event.retry` (`tb.c:83`) exists but is used **only** by the DP-BW path — the hotplug path leaves it uninitialised (`kmalloc_obj`, `tb.c:101`) and never reads it.
- **DP bandwidth-request retry.** `TB_CFG_ERROR_DP_BW` notification → `tb_queue_dp_bandwidth_request(tb, route, port, 0, 0)` `tb.c:2902`. On `-ENOTCONN` (tunnel not yet active because `tb_dp_tunnel_active()` has not run) it re-queues with `retry+1` and 50 ms (`tb.c:2827-2836`), up to `TB_BW_ALLOC_RETRIES` = 3, then gives up (`tb.c:2838-2840`).
- **Bandwidth-group lazy release (10 s).** Bandwidth a DPTX gives back is held in `group->reserved` and only returned to the pool 10 s later by `tb_bandwidth_group_release_work` (`tb.c:1567`), armed/postponed by `mod_delayed_work(system_percpu_wq, ..., TB_RELEASE_BW_TIMEOUT)` `tb.c:2644`; short-circuited by `cancel_delayed_work()` when the group empties `tb.c:1688`.
- **Delayed removal of unplugged routers after runtime resume.** `tb_runtime_resume()` `tb.c:3263` queues `tcm->remove_work` 50 ms later (`tb.c:3283`) explicitly "to avoid possible deadlock if the device removal runtime resumes the unplugged device" (`tb.c:3278-3281`); the worker `tb_remove_work` `tb.c:3250` frees unplugged children under `tb->lock` and unplugged XDomains outside it.
- **Deferred tunnel discovery at start.** `tb_start()` `tb.c:2995` only enumerates when `discover` is true (`tb.c:3050-3058`): `tb_scan_switch()` → `tb_discover_tunnels()` (`tb.c:1694`) → `tb_discover_dp_resources()`; skipped entirely after a host reset for USB4 routers so everything arrives later as synthetic hotplug.
- **XDomain discovery state machine.** 10 states (`xdomain.c:28-39`), one `state_work` step per queue; each state arms `state_retries = XDOMAIN_RETRIES` = 10 (`xdomain.c:26`) and re-queues on `-EAGAIN` at `XDOMAIN_DEFAULT_TIMEOUT` = 1000 ms (`xdomain.c:1830-1832`), decrementing at `xdomain.c:1361,1415,1462,1488,1551`. Entry `start_handshake()` at 100 ms (`xdomain.c:740`); failure → `XDOMAIN_STATE_ERROR` after 1000 ms (`xdomain.c:1832-1835`), which calls `__stop_handshake()` and parks; a later remote `UUID_REQUEST` restarts it (`xdomain.c:828-831`).
- **Deferred service registration / properties exchange.** Services are only created after `XDOMAIN_STATE_PROPERTIES` succeeds — `enumerate_services()` at the end of `tb_xdomain_get_properties()` (`xdomain.c:1639`), after `device_add(&xd->dev)` `xdomain.c:1624`. `properties_changed_work` pushes local changes with 10 retries at 1000 ms (`xdomain.c:1849-1856`); `tb_service_properties_changed()` bumps `xdomain_property_block_gen` and defers the actual push 50 ms (`xdomain.c:1013-1023` → `update_xdomain()` `xdomain.c:996-998`). The local property block itself is rebuilt **lazily** only when a remote asks and the generation is stale (`update_property_block()` `xdomain.c:674-683`).
- **DPRX timeout worker.** `tb_dp_dprx_start()` `tb.c`/`tunnel.c:1112` takes a tunnel ref and queues `dprx_work` at delay 0; each pass polls DPRX-done for at most 25 ms (`TB_DPRX_WAIT_TIMEOUT`) under `tb->lock`, then re-queues after 50 ms (`TB_DPRX_POLL_DELAY`) while `ktime_before(ktime_get(), tunnel->dprx_timeout)` — an overall 12 s budget (`TB_DPRX_TIMEOUT`, module param `dprx_timeout`, `-1` = forever). On success/expiry it calls `tunnel->callback` (`tb_dp_tunnel_active` `tb.c:1906`) **without `tb->lock`** (documented `tunnel.c:1686`) and drops the ref.
- **NVM authentication on disconnect.** `nvm_authenticate_on_disconnect` (`switch.c:2143-2151`) routes through `nvm_authenticate_sysfs(dev, buf, true)`, which writes the image now but replaces authentication with `tb_lc_force_power(sw)` (`switch.c:2110-2111`) — the authentication actually happens on the next power cycle, and its result is picked up lazily on re-enumeration via `dma_port_flash_update_auth_status()` / `usb4_switch_nvm_authenticate_status()` in `tb_switch_add()` (`switch.c:2752-2790`), cached across power cycles in `nvm_auth_status_cache` (`switch.c:34-35`).
- **Retimer NVM authentication deferral.** `tb_retimer_nvm_authenticate()` `retimer.c:138` fires the op, sleeps 100–150 µs (`retimer.c:153`) and then *expects* the status read to fail because the retimer is inaccessible mid-authentication (`retimer.c:155-157`); the real result surfaces on the next `tb_retimer_scan()`. Sideband is re-armed/disarmed around it (`tb_retimer_set_inbound_sbtx` `retimer.c:283`, unset `retimer.c:305`).
- **Domain release completion ordering (v7.2).** `tb_domain_remove()` stops the CM and ctl under `tb->lock`, drops it, then `flush_workqueue(tb->wq)` `domain.c:512` before `device_unregister()`. The final `put_device()` may be asynchronous, so `nhi_pci_remove()` blocks on `wait_for_completion(&nhi->domain_released)` `pci.c:492` before `nhi_shutdown()`; the completion is fired at the very end of `tb_domain_release()` `domain.c:330`. Fixed in v7.2 by 9cbc63400f7d, which moved `init_completion()` to `nhi.c:1229` (before `nhi_select_cm()`) so the `icm_probe()` failure path cannot complete an uninitialised completion.
- **Ring interrupt coalescing/throttling.** `tb_ring_throttling(ring, interval_nsec)` `nhi.c:850` stores `ring->interval_nsec` (ring must be stopped, `WARN_ON_ONCE(ring->running)`); applied only for MSI-X rings in `ring_interrupt_active()` `nhi.c:124-128` as `DIV_ROUND_UP(interval_nsec, 256)` into `REG_INT_THROTTLING_RATE` (256 ns granularity). Sole in-tree user: `stream.c:584-585`, default `TBSTREAM_DEV_THROTTLING` = 8192 ns (`stream.c:75`), max `16776960` (`stream.c:76`), configfs-settable only while `sdev->users == 0` (`stream.c:1202-1205`).
- **Ring polling mode.** `__ring_interrupt()` `nhi.c:399-405` masks the ring IRQ and calls `ring->start_poll()` instead of scheduling `ring->work` when the ring was allocated with a poll callback; the consumer re-arms via `tb_ring_poll_complete()` `nhi.c:416`. **No in-tree `drivers/thunderbolt` user** (thunderbolt-net is the consumer) — verified negative.
- **XDomain removal split (v7.2, a8937f35cf39).** `tb_xdomain_remove()` (topology teardown, `tb->lock` held, `xdomain.c:2229`) is now separate from `tb_xdomain_unregister()` (bus removal, must run **without** `tb->lock`, `xdomain.c:2257`), the latter driven by the deferred sweeper `tb_domain_unregister_unplugged_xdomains()` `domain.c:874`.

#### L. Locking model

##### L.1 Locks defined in the subsystem

Query: `grep -rn "DEFINE_MUTEX\|mutex_init\|DEFINE_SPINLOCK\|spin_lock_init\|DECLARE_RWSEM\|init_rwsem\|seqlock\|rwlock_init" drivers/thunderbolt/ include/linux/thunderbolt.h`

| lock | definition site | owner | protects |
|---|---|---|---|
| `tb->lock` (mutex) | `include/linux/thunderbolt.h:84`, init `domain.c:394`, destroyed `domain.c:326` | `struct tb` | **The big domain lock.** Every `struct tb_switch` / `struct tb_port` field, the topology tree, `tcm->tunnel_list`, `tcm->dp_resources`, bandwidth groups, `hotplug_active`. Documented `include/linux/thunderbolt.h:70-71` and `tb.h:167`. |
| `ctl->request_queue_lock` (mutex) | `ctl.c:46`, init `ctl.c:667` | `struct tb_ctl` | `ctl->request_queue`, `ctl->running`, and the `TB_CFG_REQUEST_ACTIVE`/`CANCELED` bits transitions (`ctl.c:136-166`). |
| `tb_cfg_request_lock` (static mutex) | `ctl.c:78` | file-global | Serializes `kref_get()`/`kref_put()` on every `tb_cfg_request` (`ctl.c:106-131`). |
| `nhi->lock` (spinlock) | `include/linux/thunderbolt.h:519`, init `nhi.c:1217` | `struct tb_nhi` | `nhi->tx_rings[]`/`rx_rings[]` slots, ring create/destroy, MSI-X clear. Doc: "Must be held during ring creation/destruction. Is acquired by interrupt_work" (`:502-503`). |
| `ring->lock` (spinlock) | `include/linux/thunderbolt.h:564`, init `nhi.c:545` | `struct tb_ring` | `ring->queue`, `ring->in_flight`, `head`/`tail`, `running`, `interval_nsec`. Doc: "**Must be acquired after nhi->lock**" (`:535-536`). |
| `xdomain_lock` (static mutex) | `xdomain.c:71` | file-global | `xdomain_property_dir`, `xdomain_property_block_gen`, `protocol_handlers`. Doc at `xdomain.c:67-70`: "**If you need to take both this lock and the struct tb_xdomain lock, take this one first.**" |
| `xd->lock` (mutex) | `include/linux/thunderbolt.h:260`, init `xdomain.c:2143` | `struct tb_xdomain` | `vendor_name`, `device_name`, `link_speed`/`width`, `remote_properties`, `local_property_block*`, and (v7.2) `xd->removing`. Doc `:209`, `:246-249`. |
| `svc->lock` (mutex) | `include/linux/thunderbolt.h:427`, init `xdomain.c:1264` | `struct tb_service` | `svc->local_properties` / `svc->remote_properties`. **Property-directory rule** (`:416-418`): service drivers may add dynamic properties to `local_properties` only while holding `svc->lock`. |
| `nvm_auth_status_lock` (static mutex) | `switch.c:36` | file-global | `nvm_auth_status_cache` list — per-router NVM authentication failure status that must survive power cycles (`switch.c:31-35`). |
| `tb_tunnel_lock` (static mutex) | `tunnel.c:112` | file-global | Serializes `kref_get()`/`put()` of `struct tb_tunnel` (`tunnel.c:198-224`). |
| `tbstream_lock` (static mutex) | `stream.c:196` | stream.c, CONFIG_USB4_STREAM | `tbstream_list`. |
| `tbstream_kref_lock` / `tbstream_dev_kref_lock` | `stream.c:200` / `stream.c:203` | stream.c | Serialize the two stream krefs. |
| `sdev->lock` (mutex) | `stream.c:154`, init `stream.c:1360` | `struct tbstream_dev` | Whole stream device: rings, hopids, `users`, `closed`, `stream` pointer. |
| `sg->lock` (mutex) | `stream.c:175`, init `stream.c:1445` | `struct tbstream_group` | `sg->dev_list`, `sg->stream`. |
| `dt->lock` (mutex) | `dma_test.c:109`, init `dma_test.c:650` | `struct dma_test`, CONFIG_USB4_DMA_TEST | Whole test state during a run and against debugfs removal (`dma_test.c:663-666`). |
| `tb_configfs.su_mutex` | `configfs.c:54` | configfs subsystem, CONFIG_USB4_CONFIGFS | ConfigFS subsystem mutex; taken from stream.c as `tbstream_group.cg_subsys->su_mutex` (`stream.c:1484`). |
| `icm->request_lock` | `icm.c:95`, init `icm.c:2491` | ICM-only | "only one message is sent to ICM at a time". |

**Verified negative**: no `DEFINE_SPINLOCK`, no rwsem (`DECLARE_RWSEM`/`init_rwsem`), no `seqlock`/`rwlock`, no semaphore (`DEFINE_SEMAPHORE`/`sema_init`) anywhere in the subsystem.

##### L.2 Lock ordering (proved from nesting)

1. **`nhi->lock` → `ring->lock`.** `ring_msix()` `nhi.c:447-451`, `nhi_interrupt_work()` `nhi.c:960-962`, `tb_ring_poll_complete()` `nhi.c:427-431`, `tb_ring_start()`/`tb_ring_stop()` (`nhi.c:707-708`, `:776-777`), `tb_ring_free()` `nhi.c:800-813`. Documented in `include/linux/thunderbolt.h:535-536`. Never the reverse; `ring_work()` releases `ring->lock` before invoking frame callbacks (`nhi.c:302-303`, comment "allow callbacks to schedule new work") so callbacks may re-enter `tb_ring_*`.
2. **`xdomain_lock` → `xd->lock`.** `update_property_block()` `xdomain.c:675-676` takes them in that order and drops them in reverse `xdomain.c:733-734`. Stated as the rule at `xdomain.c:67-70`.
3. **`tb->lock` → `svc->lock` / `xd->lock`.** Service and XDomain property updates run from `tb->wq` workers under `tb->lock` (`update_service()` `xdomain.c:1144`, `update_service_properties()` `xdomain.c:658`). No path takes `tb->lock` while holding `xd->lock`. [Orchestrator note 2026-09-04, refuted at write time (tb-domain.md): those workers do not hold `tb->lock`; xdomain.c has exactly one acquisition of it (`tb_xdp_handle_request`, xdomain.c:776). The `tb->lock` → `xd->lock` edge is proved instead by `tb_handle_hotplug` (tb.c:2432) calling `tb_xdomain_remove` (tb.c:2489), which takes `xd->lock` at xdomain.c:2228; the `svc->lock` edge by `xdomain_lock` → `xd->lock` → `svc->lock` at xdomain.c:676/677/699/658.]
4. **`tb->lock` → `nvm_auth_status_lock`.** `nvm_authenticate_sysfs()` holds `tb->lock` (`switch.c:2067`) and calls `nvm_clear_auth_status()` (`switch.c:2088`) → `nvm_auth_status_lock` (`switch.c:86`). Never reversed.
5. **`tb->lock` → `ctl->request_queue_lock` → `tb_cfg_request_lock`.** All config-space access under `tb->lock` funnels into `tb_cfg_request_sync()`, which enqueues under `request_queue_lock` (`ctl.c:139-148`) and refcounts under `tb_cfg_request_lock` (`ctl.c:106-131`). `tb_cfg_request_work` (system_wq) takes `request_queue_lock` then `tb_cfg_request_lock` and never `tb->lock`, which is what makes the sync wait safe.
6. **`tb->lock` and `nhi->lock`/`ring->lock` are disjoint** — `nhi.c` never takes `tb->lock`, and `tb.c`/`switch.c` never take `nhi->lock`. Coupling is one-way through `ring_work` → ctl RX → `tb_cfg_request_work` / `tb_domain_event_cb`.
7. **`tb->lock` is NOT held across bus device removal (v7.2 rule).** `tb_xdomain_unregister()` asserts `lockdep_assert_not_held(&xd->tb->lock)` `xdomain.c:2259`; `sg->lock`/`sdev->lock` in stream.c and `dt->lock` in dma_test.c may therefore be taken by service-driver `.remove()` callbacks without inverting against `tb->lock`.
8. **`sg->lock` → `sdev->lock`** in stream.c (`tbstream_dev_make_group` `stream.c:1368` then per-dev init; `tbstream_group_attach_stream` `stream.c:1500` iterates the list then locks each `sdev`).

##### L.3 Lockdep assertions

Query: `grep -rn "lockdep_assert_held\|lockdep_assert_not_held\|mutex_is_locked\|WARN_ON(!mutex" drivers/thunderbolt/ include/linux/thunderbolt.h`

- `drivers/thunderbolt/xdomain.c:2259` — `lockdep_assert_not_held(&xd->tb->lock)` in `tb_xdomain_unregister()`. **This is the only lockdep assertion in the entire subsystem** — no `lockdep_assert_held`, no `WARN_ON(!mutex_is_locked(...))`, no `mutex_is_locked()` anywhere (verified negative). Locking contracts are otherwise expressed only in kerneldoc (`xdomain.c:2222` "Called with @tb->lock held", `tunnel.c:1686` "@callback is called without @tb->lock held", `tb.h:167`, `tb.h:477` ".remove called without @tb->lock taken", `nhi.c:232` "ring->lock is held").

##### L.4 Places a lock is dropped/retaken (or deliberately not held) around a call

- **`tb->lock` dropped before XDomain bus removal (v7.2, a8937f35cf39).** `tb_handle_hotplug()` `tb.c:2470-2493` marks `xd->is_unplugged = true` and calls `tb_xdomain_remove()` under the lock, then after `mutex_unlock(&tb->lock)` `tb.c:2524` calls `tb_domain_unregister_unplugged_xdomains(tb)` `tb.c:2527` (→ `domain.c:874` → `tb_xdomain_unregister()` → `device_unregister()`) with the lock released. Comment `tb.c:2481-2487`: setting `is_unplugged` early "prevents deadlock if they call `tb_xdomain_disable_paths()`".
- Same split in `tb_complete()` `tb.c:3219-3229`: `tb_domain_unregister_unplugged_xdomains(tb)` runs lock-free, and only the follow-up rescan re-takes it via `scoped_guard(mutex, &tb->lock)` `tb.c:3227`.
- `tb_remove_work()` `tb.c:3250-3260`: frees unplugged children under `tb->lock`, then `mutex_unlock` and calls `tb_free_unplugged_xdomains()` `tb.c:3260` outside it.
- `tb_dp_dprx_work()` `tunnel.c:1088-1110`: takes `tb->lock` for the DPRX poll, unlocks (`tunnel.c:1105`) and only then invokes `tunnel->callback` — the callback (`tb_dp_tunnel_active` `tb.c:1906`) re-takes `tb->lock` itself and releases it at `tb.c:1967`. [Orchestrator note 2026-09-04, refuted at write time (tb-domain.md): the unlocks in `tb_dp_dprx_work` are at tunnel.c:1100 and :1106, the callback at :1110.]
- `ring_work()` `nhi.c:302-317`: drops `ring->lock` before running frame callbacks, then wakes `ring->wait` without re-taking it.
- `tb_ring_stop()` `nhi.c:776-783` / `tb_ring_free()` `nhi.c:800-835`: release `nhi->lock`+`ring->lock` before `schedule_work`/`flush_work(&ring->work)` — flushing under the ring locks would deadlock against `ring_work`.
- `tb_domain_remove()` `domain.c:505-517`: `tb->lock` is dropped before `flush_workqueue(tb->wq)` and before `device_unregister(&tb->dev)`, since the flushed workers take `tb->lock` themselves.
- `tb_domain_add()` `domain.c:474`: unlocks `tb->lock` deliberately ("This starts event processing") before enabling runtime PM.
- `tb_register_property_dir()` `xdomain.c:2703-2717` / `tb_unregister_property_dir()` `xdomain.c:2740-2744`: bump the generation under `xdomain_lock`, then unlock before `update_all_xdomains()` (which queues per-XDomain work under each `xd->lock`).
- **`mutex_trylock(&tb->lock)` + `restart_syscall()`** — sysfs/NVM paths never block on the big lock: `switch.c:294` (`nvm_read`), `switch.c:322` (`nvm_write`), `switch.c:2069` (`nvm_authenticate_sysfs`), `retimer.c:48` (`nvm_read`), `retimer.c:70` (`nvm_write`), `retimer.c:259` (`nvm_authenticate_store`); debugfs uses `scoped_guard(mutex_intr, &tb->lock)` (`debugfs.c:1637`) returning `-ERESTARTSYS`.
- `xd->removing` handshake (v7.2, 2c5d2d3c3f70): `tb_xdomain_remove()` sets `xd->removing = true` under `xd->lock` (`xdomain.c:2231-2233`) *before* `stop_handshake()`; every external queue site re-checks it under the same lock (`xdomain.c:813-818`, `:903-909`, `:993-999`) — this is the mutual exclusion that replaced the (now gone) serialization by `tb->wq`, since `tb_xdp_handle_request` moved to `system_wq`.

## Directory organization

All pages under `docs/usb4/`, thirteen groups (the two once-optional groups were confirmed at the checkpoint of 2026-09-04) (`adapter/` carries one sub-group, following the `docs/pci/` precedent for a third level):

```
docs/usb4/
├── router/       the router object, its config space, capabilities, operations, setup,
│                 lifecycle, device model, DROM, NVM, DMA port, security, reset (13)
├── domain/       the domain object, the bus, the CM ops vector, start/stop, scanning,
│                 hotplug, unplug, XDomain (object, discovery, protocol, properties), services (12)
├── adapter/      the adapter object, its config space and capabilities, lane adapters,
│   │             bonding, the USB4 port capability and device, HopIDs, the link controller (9)
│   └── protocol/ the PCIe, USB3 and DP adapter capabilities, the DP bandwidth-mode registers (4)
├── sideband/     sideband access, retimer enumeration, retimer NVM, the offline upgrade flow,
│                 lane margining (5)
├── host-if/      the NHI object, the PCI driver, MSI-X, rings, ring modes and DMA, the IOMMU
│                 DMA-protection signal (6)
├── control/      the control channel, the packet formats, configuration requests (3)
├── tunnel/       path config space, paths, activation, the tunnel model, discovery and restore,
│                 PCIe (mechanism + scenarios), USB3, DP (anatomy, bandwidth allocation, hotplug
│                 flow), DMA (12)
├── bandwidth/    credits, bandwidth groups, bandwidth accounting, asymmetric links (4)
├── pm/           the PM callback chain, system suspend, system resume, runtime PM (chain + policy),
│                 wakes, CLx (mechanism + policy), TMU (object + transitions + policy) (11)
├── acpi/         _OSC native USB4, host-interface device links, ACPI companions (3; the retimer
│                 _DSM is in sideband/, the IOMMU signal in host-if/, per the review)
├── debug/        the debugfs tree, the KUnit suite (2)
└── service/      USB4STREAM, the in-tree service driver with configfs (1)
```

Rationale: the layout follows the request's own headings (router, domains, adapters, lane adapters, protocol adapters, host interface, control traffic, tunneling with its three protocols, sideband, ACPI, PM, TMU) and the code's ownership (one file family per group). It keeps the nine group names of the June 2026 corpus where they still fit (router, domain, adapter, sideband, host-if, control, tunnel, pm) so a rewrite-in-place lands on familiar paths, splits the old `credit/` into a `bandwidth/` group because the v7.2 code carries four distinct bandwidth mechanisms (credits, groups, accounting, asymmetric links), adds `acpi/` because the request asks for curated ACPI pages and the material spans five mechanisms, and adds the two optional groups because the tree at v7.2 carries a new in-tree service driver and a debug surface the request's "curate" mandate reaches. Granularity calibrates against `docs/acpi` (43 pages, 640 to 2,620 lines each, one mechanism per page), the request's named reference: an object page per kernel construct, a mechanism page per register handshake or state machine, and a journey page per scenario the request names.

## Page catalog

Tags: [prompt] = explicitly in a prompt.md bullet (or a split of one); [curated] = gap-fill under the request's "curate new pages where you see fit" mandate and its three "curate pages for this" headings; [optional] = a curated row the checkpoint decided; all five were confirmed on 2026-09-04 and the tag no longer appears in the tables. Every anchor symbol carries a file:line hint from the Inventory findings above; all hints are re-verified on disk at write time (Execution & verification, write-time cautions). Paths are tree-relative, `drivers/thunderbolt/` implied for bare file names.

### router/

| page | scope (anchor symbols) | tag |
|---|---|---|
| tb-switch.md | `struct tb_switch` field by field (tb.h:171, kerneldoc :111-170): the embedded device, the cached header `config`, `ports`, identity (`uid`/`uuid`/`vendor`/`device` and the name strings), `generation`/`link_usb4`, the four cached VSE cap offsets, `is_unplugged`, `drom`, `nvm`/`no_nvm_upgrade`, `boot`/`rpm`/`authorized`, `quirks`, the six credit fields, `clx`, `tmu`; each with its writer and reader per the Area A digest; the ICM-only fields (`security_level`, `connection_id`/`connection_key`, `link`/`depth`, `rpm_complete`, `safe_mode`) named as ICM-only and not explained; the inline helpers `tb_switch_get`/`tb_switch_put` (tb.h:878/885), `tb_is_switch`/`tb_to_switch` (:890/895), `tb_switch_parent` (:902), `tb_switch_depth` (:928), `tb_switch_for_each_port` (:874), `tb_switch_is_icm` (:1023, the CM-mode discriminator), `tb_switch_is_usb4` (:1322), `usb4_switch_version` (:1311); `tb_sw_read`/`tb_sw_write` (:672/686) as the register seam; `tb_dump_switch` (switch.c:1563); the print macros `__TB_SW_PRINT` family (tb.h:734-743, corrected 2026-09-04 at write time) [errata 2026-09-13, migration of tb-switch.md: the row's `kerneldoc :111-170` hint overshoots: tb.h:111 is blank and the block runs :112-170] [errata 2026-09-17, fix pass of tb-switch.md: the untested `cap_lp` reader the Area A digest points at, clx.c:265 in `tb_switch_mask_clx_objections()`, stands behind a guard at clx.c:263-264 that names a vendor controller family the campaign bans, so the page reproduces the offset's use at clx.c:287-298 and states the early return without reproducing the guard; a rewrite that may show the guard is the user's call] | [prompt] |
| route-string.md | route strings as the router address: `tb_route()` (tb.h:583), `TB_ROUTE_SHIFT` (tb_regs.h:19), `tb_route_length()` (tb.h:1240), `tb_downstream_route()` (:1253), `tb_port_at()` (:588, corrected 2026-09-04 at write time), `tb_upstream_port()` (:565), `tb_switch_downstream_port()` (:915); the route in the header (`route_hi`/`route_lo` of `struct tb_regs_switch_header` tb_regs.h:166) and how `tb_switch_alloc` derives depth/route (switch.c:2487-2491) and `tb_switch_configure` uploads them (:2637-2651); the depth limits `TB_SWITCH_MAX_DEPTH`/`USB4_SWITCH_MAX_DEPTH` (tb.h:75/76) and `tb_switch_exceeds_max_depth` (switch.c:2425) with the `-EADDRNOTAVAIL` consequence at scan; `tb_switch_find_by_route()` (switch.c:3848) and the route inside every control packet (`tb_cfg_make_header` ctl.h:115, 22+32-bit split); the ICM-only lookups (`tb_switch_find_by_link_depth`/`_uuid`) named as ICM-only [errata 2026-09-13, migration of route-string.md: two spans do not hold their code. `switch.c:2487-2491` opens on the `/* configure switch */` comment and stops a line short, the five assignments running :2488-2492; and `:2637-2651` names neither write whole, the two `tb_sw_write()` calls standing at :2634-2635 and :2651-2652. The `tb_switch_find_by_link_depth`/`_uuid` shorthand also leaves `_uuid` unexpandable by any oracle] | [prompt] |
| router-config-space.md | the router configuration space on the wire: `struct tb_regs_switch_header` (tb_regs.h:166) dword by dword, the `ROUTER_CS_1..26` register map (tb_regs.h:195-228: `ROUTER_CS_3_V`, `ROUTER_CS_4` CMUV and `USB4_VERSION_MAJOR_MASK` :193, `ROUTER_CS_5` SLP/WOP/WOU/WOD/CV/UTO/PTO/HCO/CNS, `ROUTER_CS_6` SLPR/WOPS/WOUS/HCI/TNS/RR :218/CR, `ROUTER_CS_7` UID, `ROUTER_CS_9`/`_25`/`_26`), `TB_CFG_SWITCH` addressing (tb_msgs.h:15) through `tb_sw_read`/`tb_sw_write` (tb.h:672/686), `TB_MAX_CONFIG_RW_LENGTH` (tb_regs.h:26), `tb_switch_wait_for_bit()` (switch.c:1723) as the polling primitive, `usb4_switch_read_uid()` (usb4.c:347); the debugfs `regs` dump (`switch_regs_show` debugfs.c:2210) as the consumer that reads it all; register figures ([registers]) for the header dwords and CS_5/CS_6/CS_26 [errata 2026-09-13, migration of router-config-space.md: the router cluster's boundary statement gives this page `ROUTER_CS_0..26`, and there is no `ROUTER_CS_0` at this version, the offsets being 1, 3, 4, 5, 6, 7, 9, 25 and 26. The row itself says `ROUTER_CS_1..26`, which is right, and the page states the absence of both missing offsets] [errata 2026-09-13, census sweep of router-config-space.md: the page said a cached header value and a wire value can disagree and one reader needs the wire. Two sites read a header dword from the wire, `tb_switch_reset()` at switch.c:1661 and `switch_basic_regs_show()` at debugfs.c:2200, which prints them. The page now scopes the claim to the one decision that takes the hardware answer] [errata 2026-09-16, rewrite of router-config-space.md: the 2026-09-13 erratum above places the wire read of a header dword in `tb_switch_reset()` at switch.c:1661; that line is inside `tb_switch_enumerated()` (switch.c:1651-1666), which `tb_switch_reset()` calls at switch.c:1691. The two-site count stands] | [prompt] |
| router-capabilities.md | the router capability list: `enum tb_switch_cap` (tb_regs.h:28), `enum tb_switch_vse_cap` (:33), the three header shapes `struct tb_cap_basic`/`tb_cap_extended_short`/`tb_cap_extended_long` and `struct tb_cap_any` (tb_regs.h:62-107), `tb_switch_next_cap()` (cap.c:154), `tb_switch_find_cap()` (:198), `tb_switch_find_vse_cap()` (:234), `VSE_CAP_OFFSET_MAX`/`CAP_OFFSET_MAX` (cap.c:14-15), the four cached offsets and where `tb_switch_alloc` fills them (switch.c:2519-2534), the bodies behind them (`struct tb_cap_plug_events` :151, `struct tb_cap_link_controller` :117, the TMU cap found by `tb_switch_tmu_init` tmu.c:411), the debugfs `switch_caps_show` walk (debugfs.c:2177) [errata 2026-09-13, migration of router-capabilities.md: the row's `switch.c:2519-2534` span overshoots: the four-search fill block ends at switch.c:2533, :2534 is blank and :2535 opens an unrelated comment] | [prompt] |
| router-operations.md | USB4 router operations: `enum usb4_switch_op` (tb_regs.h:231) opcode by opcode, the mailbox registers `ROUTER_CS_9`/`_25`/`_26` with OV/ONS/STATUS/OPCODE (tb_regs.h:220-228), `usb4_native_switch_op()` (usb4.c:54: metadata, data, doorbell, 500 ms OV wait, status decode), `__usb4_switch_op()` (:109) with the `cm_ops->usb4_switch_op` proxy seam (tb.h:538) stated as unset by the software CM, `usb4_switch_op()`/`usb4_switch_op_data()` (:142/148), `USB4_DATA_DWORDS`/`USB4_DATA_RETRIES` (:18-19); the opcode-to-helper table: `usb4_switch_drom_read_block` (:352), the NVM family (:536-714), the DP resource family (:900-958), `usb4_switch_credits_init` (:758), with each helper's register-level treatment owned by its topic page | [prompt] |
| router-setup.md | the USB4 router configuration handshake and version detection: `tb_switch_configure()` (switch.c:2605: `enabled`, `plug_events_delay = 0xff` :2620, CMUV :2626-2631, the 4-dword `ROUTER_CS_1` write :2651, `tb_plug_events_active` :2658), `usb4_switch_setup()` (usb4.c:243: `link_is_usb4` :213 and `PORT_CS_18_TCM`, `ROUTER_CS_5` UTO/PTO/HCO/CNS, the Router Ready wait :301-302 new at v7.2), `tb_switch_configuration_valid()`/`usb4_switch_configuration_valid()` (switch.c:2669, usb4.c:316: CV then CR, 500 ms), `tb_switch_get_generation()` (switch.c:2380) as a mechanism (USB4 by version field, pre-USB4 by a device table whose rows are not documented), `tb_switch_generation_name` (:1547), `usb4_switch_version`/USB4 v2 detection (tb.h:1311), the three callers and their ordering (`tb_scan_port` tb.c:1407 after TMU, `tb_restore_children` :3105, `tb_start` :3001-3028) [errata 2026-09-11, write time of router/router-setup.md: on disk the three callers of `tb_switch_configure` are `tb_scan_port` tb.c:1344, `tb_start` tb.c:3018 and `tb_switch_resume` switch.c:3570; tb.c:1407 in `tb_scan_port` and tb.c:3105 in `tb_restore_children` are the two callers of `tb_switch_configuration_valid`, so `tb_restore_children` never calls `tb_switch_configure`; `tb_plug_events_active` is called at switch.c:2657, not :2658; `cap_plug_events` is set through `tb_switch_find_vse_cap` at switch.c:2519-2521] | [curated] |
| router-lifecycle.md | the router object lifecycle: `tb_switch_alloc()` (switch.c:2451: unlock the parent port, `tb_cfg_get_upstream_port`, the 5-dword header read, generation, depth check, `kzalloc_objs` ports with per-port IDAs, cap offsets, `device_initialize`), `tb_switch_alloc_safe_mode()` (:2570) named in one clause as ICM-only (its only caller is in icm.c) and never walked, `tb_switch_add()` (:3298) as the ordering contract (DMA port → `tb_switch_nvm_init` :328 → credits → DROM → uuid → `tb_init_port` per adapter → `tb_check_quirks` → link ports and attributes → CLx/TMU init → hotplug enable → `device_add` → USB4 ports → NVM add → wakeup and runtime PM :3400-3410 → debugfs) with the `err_ports`/`err_del` unwinds, `tb_switch_remove()` (:3430) and `tb_switch_release()` (:2288) with the put that frees, `tb_switch_set_uuid` (:2676), `tb_switch_add_dma_port` (:2722), `tb_switch_credits_init` (:3256), `tb_sw_set_unplugged` (:3471); the quirk table as a mechanism (`struct tb_quirk` quirks.c:55, `tb_check_quirks` :125, the three flag bits tb.h:24-28 and where each is tested) with no vendor row documented; the two creators (`tb_start` tb.c:3001, `tb_scan_port` :1325-1376) [errata 2026-09-13, census sweep of router-lifecycle.md: "the two creators" is the software connection manager's pair. `tb_switch_alloc()` has four call sites at v7.2, icm.c:645 and icm.c:2205 belonging to the firmware manager, and the page's lead stated the two unscoped, where it read as the tree-wide total and was false. The scoped sentence in the body is correct and stands] | [curated] |
| router-device-model.md | the router as a Linux device: `tb_switch_type` (switch.c:2373) and `tb_switch_release`, the name `%u-%llx` (:2544), `tb_switch_uevent` with `USB4_VERSION`/`USB4_TYPE` (:2309-2338), `tb_bus_type` (domain.c:311); the attribute group (`switch_attrs` :2202, `switch_attr_is_visible` :2222 as a decision table, `switch_groups` :2283) and every attribute's show/store (`authorized` :1894, `boot` :1903, `device` :1912, `device_name` :1921, `generation` :1930, `key` :1982 as ICM-only in practice, `nvm_authenticate` :2135, `nvm_authenticate_on_disconnect` :2151, `nvm_version` :2173, `rx_speed`/`tx_speed` :1996-1997, `rx_lanes`/`tx_lanes` :2023/2049, `vendor` :2182, `vendor_name` :2191, `unique_id` :2200), the safe-mode short circuit (:2275) named as ICM-only (`sw->safe_mode` is written only by the ICM-only `tb_switch_alloc_safe_mode`), the uevents `AUTHORIZED=` (:1813/1865) and `KOBJ_CHANGE` on link change (:2891) [errata 2026-09-10, write time of router/router-device-model.md: switch.c:2890 on disk, in `tb_switch_update_link_attributes` (switch.c:2863)], `KOBJ_ADD` from `tb_scan_finalize_switch` (tb.c:2988), the ABI file entries (sysfs-bus-thunderbolt:64-232); the NVM and security attributes are shown here at the attribute level and owned in depth by nvm.md and security-authorization.md | [curated] |
| drom.md | the DROM: acquisition (`tb_drom_read` eeprom.c:723, `tb_drom_host_read` :674, `tb_drom_device_read` :695, `tb_drom_copy_efi` :473, `tb_drom_copy_nvm` :503, `usb4_copy_drom` :543 via `usb4_switch_drom_read` usb4.c:386, `tb_drom_bit_bang` :564 with the `tb_eeprom_*` bit-bang family :18-168 as the pre-USB4 path), validation (`tb_crc8` :200, `tb_crc32` :212), parsing (`tb_drom_parse` :636 dispatching on `device_rom_revision`, `tb_drom_parse_v1` :592, `usb4_drom_parse` :620, `tb_drom_parse_entries` :416, `tb_drom_parse_entry_generic` :326, `tb_drom_parse_entry_port` :362 with the v7.2 bounds check :398-403), the structs (:221-284), `TB_DROM_*` sizes (:217-219), `tb_drom_read_uid_only` (:304), what the DROM feeds (vendor/device, names, uid, dual-link pairing, `port_disabled`), `sw->drom`/`drom_blob` and the debugfs blob (debugfs.c:2428); `tb_switch_drom_alloc`/`tb_switch_drom_free` (eeprom.c:447/460) on every acquisition path (:482/499/525/531/553/559/581/587/670) [amended 2026-09-04, review item 3] | [curated] |
| nvm.md | router NVM and firmware upgrade: `struct tb_nvm` (tb.h:52), `enum tb_nvm_write_ops` (:68), the nvm.c API (`tb_nvm_alloc` :289, `read_version` :359, `validate` :379, `write_headers` :414, `add_active` :433, `write_buf` :475, `add_non_active` :503, `free` :535, `read_data` :560, `write_data` :607, `tb_nvm_exit` :641) and the two nvmem devices, the vendor-ops table as a mechanism (`struct tb_nvm_vendor_ops` :37, `switch_nvm_vendors[]` :193, no row documented; `-EOPNOTSUPP` means no upgrade), `NVM_MIN_SIZE`/`NVM_MAX_SIZE`/`NVM_DATA_DWORDS` (:15-17), the router side (`tb_switch_nvm_init` switch.c:328 new at v7.2, `tb_switch_nvm_add` :358, `tb_switch_nvm_remove` :394, `nvm_read`/`nvm_write` :284/307, `tb_switch_nvm_read` :276, `nvm_validate_and_write` :99, `nvm_authenticate` :235, `nvm_authenticate_host_dma_port`/`_device_dma_port` :127/167, `nvm_readable`/`nvm_upgradeable` :212/228), the `nvm_auth_status` cache (:23-96), the sysfs flow (`nvm_authenticate_sysfs` :2061-2151, `nvm_authenticate_on_disconnect` and the `tb_lc_force_power` seam :2111, `nvm_version_show` :2153), the NHI hooks `pre_nvm_auth`/`post_nvm_auth` (switch.c:249-250, 2784-2802), the USB4 router-op NVM helpers reached from router-operations.md, the admin-guide sections (:199-307; :308-319 is the ICM-only safe-mode procedure, named as such and not documented) and ABI (:195-245); `tb_domain_disconnect_all_paths` (domain.c:845) called from the host-router DMA-port authentication path (switch.c:139) and its `-EPERM` under the software CM (`disconnect_pcie_paths` unset, domain.c:756-761), verified at write time [amended 2026-09-04] [errata 2026-09-13, migration of nvm.md: the row dates `tb_switch_nvm_init` as new at v7.2, and `git describe --contains 4573add760b8` answers v7.1-rc1. See the shorthand erratum of the same date] | [curated] |
| dma-port.md | the pre-USB4 DMA port mailbox used for router firmware access: `struct tb_dma_port` (dma_port.c:54), `DMA_PORT_CAP` (:16), the `MAIL_*` register protocol (:18-35), `dma_find_port` (:168, the NHI-port candidates), `dma_port_alloc`/`dma_port_free` (:203/227, the v7.2 flex-array change), `dma_port_read`/`dma_port_write` (:88/129), `dma_port_wait_for_completion` (:232) and `status_to_errno` (:257), `dma_port_request` (:271), `dma_port_flash_read`/`_write` (:353/373), `dma_port_flash_update_auth` (:396), `_update_auth_status` (:420), `dma_port_power_cycle` (:452), `DMA_PORT_TIMEOUT`/`DMA_PORT_RETRIES` (:44-45) and the 150 ms literals, dma_port.h (:18-29), the callers in switch.c (`tb_switch_add_dma_port` :2722, the NVM auth paths :127-233); stated as a pre-USB4 router mechanism | [curated] |
| security-authorization.md | authorization under the software CM: `enum tb_security_level` (include/linux/thunderbolt.h:58) and `tb_security_names` (domain.c:112), the level the software CM sets in `tb_probe` (tb.c:3384/3386 via `tb_acpi_may_tunnel_pcie`), `authorized_show`/`authorized_store` (switch.c:1785/1873), `tb_switch_set_authorized` (:1819) and `disapprove_switch` (:1794), `tb_domain_approve_switch`/`tb_domain_disapprove_switch` (domain.c:657/638) and their `cm_ops` seams (`approve_switch = tb_tunnel_pci` tb.c:2275, `disapprove_switch = tb_disconnect_pci` :2254), the members the software CM leaves unset (`add_switch_key`, `challenge_switch_key`, `get_boot_acl`/`set_boot_acl`) stated as unset with the `-EPERM`/hidden-attribute consequences (`key` visibility :2244-2250, `boot_acl` visibility domain.c:290-296), the domain attributes `security`/`deauthorization` (domain.c:263/237), the `AUTHORIZED=` uevents (:1813/1865), the admin-guide sections (:24-178) | [curated] |
| router-reset.md | resetting a router: `tb_switch_reset()` (switch.c:1682), `tb_switch_enumerated()` (:1651, `ROUTER_CS_3_V`), `tb_switch_reset_host()` (:1581, the per-adapter path-config cleanup and the v7.2 USB4 lane-1 rule :1601-1606, the protocol adapter disables :1607-1615), `tb_switch_reset_device()` (:1646) through `tb_port_reset()` (:685) dispatching to `usb4_port_reset()` (usb4.c:1175, `PORT_CS_19_DPR`, 10 ms) or `tb_lc_reset_port()` (lc.c:62), `tb_path_deactivate_hop` (path.c:446) as reached, the NHI-side host router reset `nhi_reset()` (nhi.c:1132) cited as the host-router path (host-if/tb-nhi.md owns it with `REG_RESET_HRR` and the `host_reset` parameter) and the callers (`tb_start` reset argument tb.c:2995/3050, `tb_resume_noirq` tb.c:3141 for a non-USB4 host) | [curated] |

### domain/

| page | scope (anchor symbols) | tag |
|---|---|---|
| tb-domain.md | `struct tb` field by field (include/linux/thunderbolt.h:82, kerneldoc :67): `dev`, `lock` as the big lock, `nhi`, `ctl`, `wq` (the ordered `thunderbolt%d` workqueue domain.c:400), `root_switch` (set tb.c:3001, cleared :2960 at v7.2), `cm_ops`, `index` and `tb_domain_ida` (domain.c:20), `security_level`, `nboot_acl` as ICM-only, `privdata` and `tb_priv()` (tb.h:545); `tb_domain_alloc()` (domain.c:377), `tb_domain_add()` (:439, the ctl-start → `driver_ready` → `device_add` → `start` → runtime-PM ordering :476-483), `tb_domain_remove()` (:503), `tb_domain_release()` (:319) with the `domain_released` completion (thunderbolt.h:530, `init_completion` nhi.c:1229, waits nhi.c:1245 and pci.c:492), `tb_domain_get`/`tb_domain_put` (tb.h:798/805), `TB_TIMEOUT` (tb.c:19) as the ctl timeout, the domain attributes (`boot_acl` domain.c:121-235 as ICM-only, `deauthorization` :237, `iommu_dma_protection` :253, `security` :263, visibility :284), `tb_domain_event()` (tb.h:818), the ABI entries (:1-63); the domain sysfs group (`domain_attrs`/`domain_attr_is_visible` domain.c:276/284: `deauthorization` :237, `iommu_dma_protection` :253, `security` :263, `boot_acl` named as ICM-only); the subsystem lock-order table from Sweep S2 (L.2) with `tb->lock` at its root [amended 2026-09-04] [errata 2026-09-13, migration of tb-domain.md: the ABI span `:1-63` overshoots: the domain's four entries end at :62, where :63 is blank and :64 opens a router attribute] | [prompt] |
| thunderbolt-bus.md | the `thunderbolt` bus and its device types: `tb_bus_type` (domain.c:311) with `tb_service_match`/`__tb_service_match`/`match_service_id` (:71/48/22), `tb_service_probe`/`_remove`/`_shutdown` (:76/88/98); the device types `tb_domain_type` (:333), `tb_switch_type` (switch.c:2373), `tb_xdomain_type` (xdomain.c:2050), `tb_service_type` (:1132), `usb4_port_device_type` (usb4_port.c:289), `tb_retimer_type` (retimer.c:383) as one taxonomy of what appears under `/sys/bus/thunderbolt/devices`; `tb_domain_init()`/`tb_domain_exit()` (domain.c:886/912) and the init order (configfs, debugfs, ACPI bus type, XDomain, bus registration); the module entry `nhi_init`/`nhi_unload` (pci.c:600/615, `rootfs_initcall` :621) as the seam that calls them; the uevents and modalias (`tb_service_uevent` xdomain.c:1111, `get_modalias` :1039) | [curated] |
| connection-manager-ops.md | the connection-manager vector: `struct tb_cm_ops` (tb.h:507, kerneldoc :470) callback by callback with its domain.c invoker (the Area B table), the software instance `tb_cm_ops` (tb.c:3287-3303) and its exact member list, the members it leaves unset and what each unset member means for the software CM, `tb_probe()` (tb.c:3374: `tb_domain_alloc` with `sizeof(struct tb_cm)`, the security level, `tb_acpi_add_links`, `tb_init_bandwidth_groups`, the `INIT_*` calls), `struct tb_cm` (tb.c:64) and `tcm_to_tb` (:72), `tb_priv`, the CM selection seam `nhi_select_cm()` (nhi.c:1163: `tb_acpi_is_native()` chooses the software CM; the firmware CM fallback is named in one sentence and not documented); the platform-specific link helper at tb.c:3312 is named as platform-specific and not documented | [prompt] |
| domain-start-stop.md | bringing the software CM up and down: `tb_start()` (tb.c:2995: the `reset` argument, the root router at route 0 with `dev_err_probe`, `no_nvm_upgrade`/`rpm` for the host router :3014-3016, discovery versus reset :3050-3058 through `tb_scan_switch`, `tb_discover_tunnels` :1694, `tb_discover_dp_resources` :172, `tb_create_usb3_tunnels` :997, `tb_add_dp_resources` :111, `hotplug_active` :3073), `tb_stop()` (:2941: tunnel puts, `remove_work` cancel, `tb_switch_remove` of the root and `root_switch = NULL` :2960), `tb_deinit()` (:2964: the group work cancels), `tb_scan_finalize_switch()` (:2974: `boot` → `authorized`, `KOBJ_ADD`), the `hotplug_active` gate and every writer of it, the callers `tb_domain_add`/`tb_domain_remove` (domain.c:467/506/514) and the lock each holds [errata 2026-09-13, migration of domain-start-stop.md: the `:3050-3058` span starts on a blank line and leaves out the reset test at tb.c:3045-3049, which is where the `discover` flag the span turns on is cleared] | [curated] |
| topology-scan.md | discovering routers: `tb_scan_switch()` (tb.c:1273) and `tb_scan_port()` (:1289) as one decision tree with every early exit (upstream port, DP OUT with HPD active :1299-1305, non-lane adapter, secondary lane, `tb_wait_for_port` :1318, existing remote, `tb_switch_alloc` failure → `tb_retimer_scan` → `tb_scan_xdomain` on `-EIO`/`-EADDRNOTAVAIL` :1332-1341, `tb_switch_configure` failure, pre-existing XDomain removal :1353-1357, uevent suppression during discovery :1364-1367, `sw->rpm` :1373, `tb_switch_add`), `tb_configure_link()` (:1232: both `remote` pointers, `tb_switch_set_link_width(DUAL)` :1250, the Gen-4 symmetric reconfiguration :1257-1263, `tb_switch_configure_link` :1267), the post-add sequence (retimer scans :1389/1410, CLx :1395, TMU :1400, `tb_switch_configuration_valid` :1407, USB3 tunnels :1418, DP resources :1421, recursion :1422), `tb_scan_xdomain()` (:431), the runtime-PM pairs on the router and the USB4 port (:1277/1282, :1316/1425), the depth limit consequence [errata 2026-09-13, migration of topology-scan.md: the `CLx :1395` anchor is an abbreviation no oracle expands] | [prompt] |
| router-hotplug.md | the plug journey from interrupt to device: the MSI-X vector firing `ring_msix` (nhi.c:444) and `ring_work` (:268) for ring 0 → `tb_ctl_rx_callback` (ctl.c:445) → `tb_ctl_handle_event` (:402) → `tb_domain_event_cb` (domain.c:338) → `tb_handle_event` (tb.c:2916: `cfg_event_pkg` tb_msgs.h:89, `tb_cfg_ack_plug` ctl.c:842) → `tb_queue_hotplug` (:93, `struct tb_hotplug_event` :77, the domain reference :101 new at v7.2) → `tb_handle_hotplug` (:2421) with the runtime-PM pairs (:2430/2456) and the `hotplug_active` gate → every plug branch (:2503-2517: a lane adapter → `tb_scan_port`; a DP adapter → `tb_dp_resource_available`; the other adapter types) → router enumeration (`tb_switch_alloc`/`configure`/`add`) → the domain additions (USB3 tunnels, DP resources); `tb_handle_notification` (:2885) for the `TB_CFG_ERROR_*` notifications that arrive on the same path; the hotplug-side uevents; the vendor-only port-0 helpers in that branch are named as vendor-only and not documented [errata 2026-09-13, migration of router-hotplug.md: the `configure` and `add` anchors are abbreviations no oracle expands] | [prompt] |
| router-unplug.md | the unplug journey: the unplug branch of `tb_handle_hotplug` (tb.c:2461-2476) in order (`tb_retimer_remove_all` retimer.c:592 → `tb_sw_set_unplugged` switch.c:3471 → `tb_free_invalid_tunnels` :1775 → `tb_remove_dp_resources` :138 → `tb_switch_tmu_disable` → `tb_switch_unconfigure_link` switch.c:3227 → `tb_switch_set_link_width(SINGLE)` → `tb_switch_remove` :3430 → clearing both `remote` pointers → `tb_recalc_estimated_bandwidth` :1515 and `tb_tunnel_dp` :2063), the XDomain unplug branch (:2477-2493: `is_unplugged` first, `tb_xdomain_remove`, `__tb_disconnect_xdomain_paths`, `tb_port_unconfigure_xdomain`) and the bus removal outside the lock (`tb_domain_unregister_unplugged_xdomains` domain.c:874 at tb.c:2527), the DP adapter unplug (`tb_dp_resource_unavailable` :2178), the cleanup that runs elsewhere (`tb_free_unplugged_children` :1790, `tb_free_unplugged_xdomains` :3123, `tb_remove_work` :3250 after runtime resume, `tb_complete` :3219), `tb_switch_resume`'s replaced-XDomain branch (switch.c:3611-3624); the adapter-0 branch's `tb_switch_xhci_disconnect` is named as vendor-only and not documented, as the router-hotplug row directs for the same helper pair (orchestrator note 2026-09-05, applied at the check pass) [errata 2026-09-13, migration of router-unplug.md: the `tb.c:2461-2476` span excludes the branch's own opening and the retimer removal at tb.c:2458-2459] | [prompt] |
| xdomain.md | the cross-domain object: `struct tb_xdomain` field by field (include/linux/thunderbolt.h:250, kerneldoc :198) with the v7.2 `removing` flag and the ICM-consumed `ntunnels`/`link`/`depth`; `tb_xdomain_alloc()` (xdomain.c:2121), `tb_xdomain_add()` (:2202), `tb_xdomain_remove()` (:2224) and the split-off `tb_xdomain_unregister()` (:2257, `lockdep_assert_not_held`), `tb_xdomain_release()` (:2015), get/put and the runtime-PM pin (:2179-2181), the lookups (`switch_find_xdomain` :2493, `tb_xdomain_find_by_uuid` :2545, `_by_route` :2607, the ICM-only `_by_link_depth` named), `tb_xdomain_link_init`/`_exit` (:2057/2074), `tb_scan_xdomain` (tb.c:431) and `tb_port_configure_xdomain`/`_unconfigure` (tb.c:416/423), the XDomain PM callbacks named at the seam only (`tb_xdomain_pm_ops` is xdomain-discovery.md's per rule 3 as amended 2026-09-04; row corrected 2026-09-04 at write time), the sysfs attributes (:1863-2013) and ABI, the `xdomain` module parameter and `tb_is_xdomain_enabled()` (:62-85), `xd->lock` and `xdomain_lock` (:71) with their ordering [errata 2026-09-13, migration of xdomain.md: the `tb_xdomain_link_init`/`_exit` shorthand leaves `_exit` unexpandable by any oracle; and the row asks for `_by_link_depth` to be named where the page locates it by its declaration and leaves the symbol off under the firmware-manager boundary] | [prompt] |
| xdomain-discovery.md | the XDomain discovery state machine: the state enum (xdomain.c:29-40) and names, `tb_xdomain_state_work()` (:1720) state by state (INIT, UUID, LINK_STATUS, LINK_STATE_CHANGE, LINK_STATUS2, BONDING_UUID_HIGH, BONDING_UUID_LOW, PROPERTIES, ENUMERATED, ERROR) with the transitions the Area B digest records, `start_handshake`/`stop_handshake`/`__stop_handshake` (:737/752/745), the per-state workers (`tb_xdomain_get_uuid`, `tb_xdomain_get_link_status`, `tb_xdomain_link_state_change` :1434, `tb_xdomain_bond_lanes_uuid_high` :1475, `tb_xdomain_get_properties` and its `enumerate_services` seam), `tb_xdomain_queue_bonding` (:1675), the USB4 v2 lane-bonding roles and `tb_xdomain_lane_bonding_enable`/`_disable` (:2277/2329) with `tb_port_wait_for_link_width`, `XDOMAIN_*` retries and timeouts (:23-27), `tb_xdomain_update_link_attributes` (:1317), the restart from ERROR on an inbound UUID request (:828-836), `xd->removing` guarding every queue site; `tb_xdomain_pm_ops` (xdomain.c:2046: `tb_xdomain_suspend`/`_resume` :2034/2040 stop and restart the handshake across system sleep) [amended 2026-09-04] [errata 2026-09-05 at write time: on disk `XDOMAIN_STATE_BONDING_UUID_LOW` is index 5 and `_HIGH` index 6, the ERROR restart is xdomain.c:830-836, the inbound link-state read at :853 is a two-dword read whose `ERROR_NOT_READY` comparison is at :873-880, and `xd->removing` guards the three queue sites reached from outside `state_work` (:814, :832, :904) and the properties-changed queue at :995, not the eight inside it] [errata 2026-09-13, migration of xdomain-discovery.md: the `:23-27` span overshoots: the handshake's four constants end at :26, and :27 defines `XDOMAIN_DEFAULT_MAX_HOPID`, which is neither a retry nor a timeout] | [curated] |
| xdomain-protocol.md | the XDomain protocol (XDP): `struct tb_xdomain_header` and the `TB_XDOMAIN_*` masks (tb_msgs.h:516-524), `enum tb_xdp_type` (:526), `struct tb_xdp_header` (:541), every request/response pair (`tb_xdp_uuid` :587/591, `tb_xdp_properties` :603/611 with `TB_XDP_PROPERTIES_MAX_*` :630-634, `tb_xdp_properties_changed` :636/641, `tb_xdp_link_state_status` :552/556, `tb_xdp_link_state_change` :570/577, `tb_xdp_error_response` :547), `enum tb_xdp_error` (:648); the transport (`__tb_xdomain_request`/`tb_xdomain_request` xdomain.c:180/225, `__tb_xdomain_response`/`tb_xdomain_response` :138/173, `tb_xdomain_match`/`tb_xdomain_copy`/`response_ready` :90/123/133, `tb_xdp_fill_header` :236, the sequence-number wrap), the message helpers (:271-593), inbound dispatch (`tb_xdomain_handle_request` :2620 from the ctl callback, `tb_xdp_schedule_request` :938 on the system workqueue with the domain reference, `tb_xdp_handle_request` :758 with the v7.2 size validations and the `root_switch` NULL check), protocol handlers (`tb_register_protocol_handler`/`_unregister` :619/640, `struct tb_protocol_handler` thunderbolt.h:385) [errata 2026-09-13, migration of xdomain-protocol.md: the `tb_xdp_schedule_request` anchor's hint `:938` is the `static bool` line, the identifier standing on :939] | [curated] |
| xdomain-properties.md | the property block: the on-wire entries (`struct tb_property_entry`/`_rootdir_entry`/`_dir_entry` property.c:17-32, `TB_PROPERTY_ROOTDIR_MAGIC`/`TB_PROPERTY_MAX_DEPTH` :37-38), `struct tb_property_dir`/`struct tb_property`/`enum tb_property_type` (include/linux/thunderbolt.h:114-139), parsing (`tb_property_parse_dir` :243, `__tb_property_parse_dir` :170, `tb_property_parse` :103, `tb_property_entry_valid` :55, `tb_property_key_valid` :82) with every v7.2 hardening, formatting (`tb_property_format_dir` :515, `__tb_property_format_dir` :373, `tb_property_dir_length` :334), create/free (:267/318), copy and merge (`tb_property_copy_dir` :611, `copy_dir` :531, `tb_property_copy` :557, `tb_property_merge_dir` :628), the add/remove/find family (:677-847) and `tb_property_for_each`; the host property directory (`xdomain_property_dir`/`xdomain_property_block_gen` xdomain.c:74-75, seeded in `tb_xdomain_init` :2748, `tb_register_property_dir`/`_unregister` :2693/2734, `update_property_block` :674 and its lazy rebuild, `tb_xdomain_properties_changed` :1838 and `update_all_xdomains` :2663), the KUnit property cases (test.c:2667-3055) [errata 2026-09-05 at write time: the nine case bodies span test.c:2667-3096; `tb_property_add_data` has no caller in the tree and is named without a usage excerpt] [errata 2026-09-13, migration of xdomain-properties.md: "with every v7.2 hardening" dates the parser wrong: `git describe --contains` puts 01deda015206, 928abe19fbf0 and de21b59c29e3 at v7.1-rc6 and cff8eb65d1ea and 65423079c742 at v7.1, and only `tb_property_merge_dir()` (7e6445d9d6f7) is v7.2-rc1. The phrase is the row's v7.0-to-v7.2 ledger window, not a release] [errata 2026-09-13, census sweep of xdomain-properties.md: two page claims were wrong. The tail of `update_property_block()` was said to install the block "in four assignments"; xdomain.c:724-729 holds three assignments and one `kfree()` of the previous block. And both in-tree callers of `tb_property_remove()` were said to release the child first; `remove_directory()` (xdomain.c:2675) leaves that to the registering driver, which releases it after unregistering] | [curated] |
| services.md | services and service drivers: `struct tb_service` (include/linux/thunderbolt.h:419) field by field, `struct tb_service_driver` (:466), `struct tb_service_id` (include/linux/device-id/tb.h:28, moved at v7.2) and `TB_SERVICE()` (include/linux/thunderbolt.h:474), `tb_register_service_driver`/`_unregister` (xdomain.c:969/982), the bus match and probe seams (domain.c:22-110), `enumerate_services` (:1219), `populate_service` (:1186), `find_service` (:1174), `update_service` (:1140), `remove_missing_service` (:1158), `__unregister_service`/`unregister_service` (:1150/2208), `tb_service_release` (:1120) and the XDomain reference a service holds (:1263/1129, new at v7.2), the service attributes (:1026-1109) and ABI (:246-295), service-supplied properties (`local_properties`, `svc->lock`, `update_service_properties` :648, `tb_service_properties_changed` :1013), `tb_service_get/put` and drvdata helpers; the network service driver (drivers/net/thunderbolt/main.c) cited as the driver example ([coverage.recency]) from its own source, with the DMA-test and stream drivers named | [curated] |

### adapter/

| page | scope (anchor symbols) | tag |
|---|---|---|
| tb-port.md | `struct tb_port` field by field (tb.h:280, kerneldoc :246) with each field's writer and reader per the Area C digest (`config`, `sw`, `remote`, `xdomain`, the four cap offsets, `usb4`, `port`, `disabled`, `bonded`, `dual_link_port`/`link_nr`, the two IDAs, `list`, the three credit fields, `group`/`group_list`, `max_bw`, `redrive`); adapter numbering (adapter 0 as the router's own control adapter, `max_port_number` tb_regs.h:173 sizing `sw->ports` at switch.c:2500-2521, the array index as the adapter number); `tb_init_port()` (switch.c:700: the 8-dword read, the cap discovery order, `ctl_credits` from hop entry 0 :739-747, `total_credits` :755, `-ENODEV` → `disabled`), `tb_dump_port` (:442), `tb_port_type` (:413); `tb_port_read`/`tb_port_write` (tb.h:700/714) as the register seam; the predicates and iterators (`tb_port_is_null`/`_nhi`/`_pcie_down`/`_pcie_up`/`_dpin`/`_dpout`/`_usb3_down`/`_usb3_up` tb.h:632-667, `tb_port_has_remote` :620, `tb_port_at` :588, `tb_switch_for_each_port` :874, `tb_upstream_port` :565, `tb_is_upstream_port` :577, `tb_switch_find_port` switch.c:3874, `tb_port_is_enabled` :1326); who sets and clears `remote` and `xdomain` (tb.c:1238-1242/451, tb.c:1805/2471, switch.c:3445/3449); the `__TB_PORT_PRINT` family (tb.h:745-758) [errata 2026-09-12, migration of tb-port.md: the row's three credit fields are `total_credits`, `ctl_credits` and `dma_credits`; `nfc_credits` is a fourth, written by the DROM parse] [errata 2026-09-13, census sweep of tb-port.md: the page said `bonded` is written in "three assignment pairs inside the router code". switch.c holds four pairs, at :1157/1158, :1182/1183, :2916/2918 and :2921/2923, because `tb_switch_link_init()` writes both ends of both adapters. The three citations name three functions, so the page now counts functions] [errata 2026-09-16, rewrite of tb-port.md: the 2026-09-12 erratum above is wrong. `struct tb_port` declares three credit members at tb.h:298-300, `total_credits`, `ctl_credits` and `dma_credits`; `nfc_credits` is a member of the cached header `struct tb_regs_port_header` at tb_regs.h:301, written by `tb_port_add_nfc_credits()` at switch.c:590-591 and `tb_port_do_update_credits()` at switch.c:1252, and eeprom.c carries no credit reference] | [prompt] |
| adapter-config-space.md | the adapter configuration space: `struct tb_regs_port_header` dword by dword (tb_regs.h:283) including which dwords are `ADP_CS_4` (NFC/total buffers/LCK :314-318) and `ADP_CS_5` (LCA and DHP :319-322; the max in/out HopID fields are header bitfields at :303-304), `enum tb_port_type` (:268), `TB_CFG_PORT` addressing (tb_msgs.h:15) through `tb_port_read`/`tb_port_write`, the writers of `ADP_CS_4`/`_5` (`tb_port_add_nfc_credits` switch.c:567, `usb4_port_unlock` usb4.c:1132, `usb4_port_hotplug_enable` :1154, `tb_port_do_update_credits` switch.c:1234); the counters configuration space as its section (`TB_CFG_COUNTERS`, the 3-dword sets and `tb_port_clear_counter` switch.c:604 as the only in-driver writer, `max_counters`/`counters_support`, the debugfs `counters` file debugfs.c:2324/1895/1878 as the only reader); the debugfs `regs` dump for a port (debugfs.c:2105/2090) as consumer; register figures ([registers]) for `ADP_CS_0..5` [errata 2026-09-12, migration of adapter-config-space.md: `_5` in the `ADP_CS_4`/`_5` shorthand expands to no symbol, and `tb_port_do_update_credits` reads `ADP_CS_4` at switch.c:1239 and writes only the cached `port->config.nfc_credits`] [errata 2026-09-16, rewrite of adapter-config-space.md: the row asks for register figures for `ADP_CS_0..5`, and only `ADP_CS_4` (tb_regs.h:314) and `ADP_CS_5` (tb_regs.h:319) exist as symbols at v7.2; the first four dwords are fields of `struct tb_regs_port_header` and are drawn as such] | [prompt] |
| adapter-capabilities.md | the adapter capability list: `enum tb_port_cap` (tb_regs.h:40) and which members the driver looks up, `tb_port_next_cap()` (cap.c:76), `__tb_port_find_cap()` (:91), `tb_port_find_cap()` (:124) with its legacy bracket `tb_port_enable_tmu`/`tb_port_dummy_read` (:18/47, `TMU_ACCESS_EN` :16) described as a mechanism for two pre-USB4 generations without naming them, the cached offsets `cap_phy`/`cap_adap`/`cap_usb4`/`cap_tmu` (tb.h:285-288) and their setters (switch.c:724-752, tmu.c:426-427), `struct tb_cap_phy` (tb_regs.h:129) as the legacy overlay of the lane registers, the debugfs `port_caps_show` walk (debugfs.c:2079, lengths :20-31) [errata 2026-09-12, migration of adapter-capabilities.md: the lengths span is debugfs.c:21-31, since :20 is blank, and tmu.c:426-427 covers the call and its guard with `cap_tmu` assigned at :428] | [prompt] |
| lane-adapter.md | the lane adapter: `LANE_ADP_CS_0`/`LANE_ADP_CS_1` bit by bit (tb_regs.h:339-372), the link state machine (`enum tb_port_state` :49, `tb_port_state` switch.c:467 reading `struct tb_cap_phy`, `tb_wait_for_port` :498 with its 10 × 100 ms budget), enable and disable (`__tb_port_enable` :631, `tb_port_enable`/`tb_port_disable` :667/680, `LANE_ADP_CS_1_LD`), `tb_port_unlock` (:620), why lane 0 is special (the USB4 port capability and device only on lane 0, the DROM pairing `dual_link_port`/`link_nr` eeprom.c:362-408 and `tb_switch_default_link_ports` switch.c:2821, `tb_port_has_remote` false for `link_nr == 1`, the v7.2 `tb_switch_reset_host` lane-1 rule), `tb_port_start_lane_initialization` (:1282) and `tb_port_resume` (:1297) for pre-USB4 lanes, the CL support bits as read by clx.c and the width/speed fields as read by lane-bonding.md (reached, owned there) | [prompt] |
| lane-bonding.md | link speed, width and lane bonding: `tb_port_get_link_speed`/`_generation`/`_width` (switch.c:905/941/966), `tb_port_width_supported` (:994), `tb_port_set_link_width` (:1031), `tb_port_set_lane_bonding` (:1085), `tb_port_lane_bonding_enable`/`_disable` (:1119/1177), `tb_port_wait_for_link_width` (:1203, the 100 ms and 10 s callers), `tb_port_update_credits` (:1269); the router level (`tb_switch_lane_bonding_possible` :2851 dispatching to `usb4_switch_lane_bonding_possible` usb4.c:402 or `tb_lc_lane_bonding_possible` lc.c:515, `tb_switch_update_link_attributes` :2863 with its `KOBJ_CHANGE`, `tb_switch_link_init` :2896, `tb_switch_lane_bonding_enable`/`_disable` :2950/3002 with the v7.2 `-EOPNOTSUPP`, `tb_switch_set_link_width` :3127), `enum tb_link_width` (include/linux/thunderbolt.h:191), `sw->link_speed`/`link_width`/`preferred_link_width`, the `rx_speed`/`tx_speed`/`rx_lanes`/`tx_lanes` attributes (switch.c:1984-2049) and ABI (:144-171), the scan-time caller `tb_configure_link` (tb.c:1232) and the XDomain caller reached; asymmetric widths are owned by bandwidth/asymmetric-links.md and named here | [prompt] |
| usb4-port-capability.md | the USB4 port capability of a lane-0 adapter: `PORT_CS_18`/`PORT_CS_19` bit by bit (tb_regs.h:384-401), `link_is_usb4` (usb4.c:213), `usb4_port_unlock` (:1132), `usb4_port_hotplug_enable` (:1154), `usb4_port_reset` (:1175), `usb4_port_set_configured`/`usb4_port_configure`/`_unconfigure` (:1208/1238/1251), `usb4_set_xdomain_configured`/`usb4_port_configure_xdomain`/`_unconfigure_xdomain` (:1256/1288/1300), `usb4_port_wait_for_bit` (:1305), `usb4_port_clx_supported` (:1574); the router-level users `tb_switch_configure_link`/`tb_switch_unconfigure_link` (switch.c:3198/3227, the downstream-first order that preserves wake-on-connect), `tb_switch_port_hotplug_enable` (:3266), `tb_port_configure_xdomain` (tb.c:416); the pre-USB4 counterpart for hotplug enablement, `tb_plug_events_active` (switch.c:1750) with `struct tb_cap_plug_events` (tb_regs.h:151) and the plug-events VSE registers (:560-578), its vendor branch named as vendor-only; the wake bits are named and owned by pm/wakes.md; router offline and margining are named and owned by sideband pages [errata 2026-09-12, migration of usb4-port-capability.md: the `PORT_CS_18`/`PORT_CS_19` span ends at tb_regs.h:400, the last define; :401 is past the family] | [prompt] |
| usb4-port-device.md | the USB4 port as a Linux device: `struct usb4_port` (tb.h:316), `usb4_port_device_add`/`_remove`/`_resume` (usb4_port.c:303/349/363), `usb4_port_device_type` (:289) and release (:282), `usb4_switch_add_ports`/`_remove_ports` (usb4.c:1078/1111), the `connector` symlink through the component framework (`connector_bind`/`_unbind`/`connector_ops` usb4_port.c:15-36) and the ACPI companion seam (`tb_acpi_find_companion` acpi.c:316, `tb_acpi_setup` :339 setting `can_offline`), the `link` attribute (:41-65), the `offline`/`rescan` attributes and `service_attr_is_visible` (:151-274) with `usb4_port_offline`/`usb4_port_online` (:76/100) reached (the flow is owned by sideband/retimer-offline-upgrade.md), `usb4_usb3_port_match()` (:118, the exported seam the USB core uses), wakeup capability and runtime PM (:329-337), `tb_is_usb4_port_device`/`tb_to_usb4_port_device`/`usb4_port_device_is_offline` (tb.h:1486-1503), the ABI entries (:296-337) [errata 2026-09-12, migration of usb4-port-device.md: `_remove` and `_resume` are shorthand for `usb4_port_device_remove` and `usb4_port_device_resume`, which the coverage oracle cannot expand from the bare tokens] | [curated] |
| hopid-allocation.md | HopID name spaces: the per-adapter IDAs `in_hopids`/`out_hopids` (tb.h:295-296, `ida_init` switch.c:2514-2515, `ida_destroy` :2296), `tb_port_alloc_hopid` (switch.c:763) with `TB_PATH_MIN_HOPID` (tb.h:450), the ceilings `max_in_hop_id`/`max_out_hop_id` (tb_regs.h:306-307) and the NHI-adapter exception (:779-781), `tb_port_alloc_in_hopid`/`_out_hopid`/`release_*` (:799-833) and their path.c callers (:181/188/279/311/354), the XDomain's own IDAs and helpers (`tb_xdomain_alloc_in_hopid`/`_out_hopid`/`release_*` xdomain.c:2364-2418, `local_max_hopid`/`remote_max_hopid`, `XDOMAIN_DEFAULT_MAX_HOPID`, the `maxhopid` attribute), the NHI-side ring HopID allocation `nhi_alloc_hop` (nhi.c:458, `RING_FIRST_USABLE_HOPID`/`RING_E2E_RESERVED_HOPID` :30/35) as the other end of every DMA path, HopID 0 reserved for control and the per-protocol fixed HopIDs (`TB_PCI_HOPID`, `TB_USB3_HOPID`, `TB_DP_*_HOPID` tunnel.c:19-39) | [curated] |
| link-controller.md | the pre-USB4 link controller capability: `cap_lc` (tb.h:191) found via `TB_VSE_CAP_LINK_CONTROLLER`, the `TB_LC_*` register map (tb_regs.h:589-632), `read_lc_desc` and `find_port_lc_cap` (lc.c:27/34) with the per-physical-port stride (`TB_LINKS_PER_PHY_PORT` include/linux/thunderbolt.h:100, `tb_phy_port_from_link`), `tb_lc_read_uuid` (:20), `tb_lc_reset_port` (:62), `tb_lc_configure_port`/`_unconfigure_port` (:141/154) and `tb_lc_configure_xdomain`/`_unconfigure_xdomain` (:199/210), `tb_lc_start_lane_initialization` (:225), `tb_lc_is_clx_supported` (:259), `tb_lc_lane_bonding_possible` (:515), the DP sink allocation `tb_lc_dp_sink_query`/`_alloc`/`_dealloc` (:588/618/667), `tb_lc_set_wake`/`tb_lc_set_wake_one` (:428/389), `tb_lc_set_sleep` (:469), `tb_lc_force_power` (:712); each with its generation gate; the xHCI-connect helpers (lc.c:283-390, switch.c:3980/4024) are named as vendor-only and not documented [errata 2026-09-12, migration of link-controller.md: the link-controller span ends at lc.c:387, the last of the five helpers; :389 opens `tb_lc_set_wake_one`] | [curated] |

### adapter/protocol/

| page | scope (anchor symbols) | tag |
|---|---|---|
| pcie-adapter.md | the PCIe adapter capability: `ADP_PCIE_CS_0` (`_PE`, `_LTSSM_MASK` new at v7.2) and `ADP_PCIE_CS_1` (`_EE`) (tb_regs.h:474-479), `enum tb_pcie_ltssm_state` (:481-493), `tb_pci_port_is_enabled`/`tb_pci_port_enable` (switch.c:1387/1405, the full-word write), `usb4_pci_port_set_ext_encapsulation` (usb4.c:3132), `usb4_pci_port_ltssm_state` (:3162), the tunnel-side users reached (`tb_pci_port_ltssm_state_detect`/`tb_pci_pre_activate` tunnel.c:293/312, `tb_pci_set_ext_encapsulation` :327, `tb_pci_activate` :361), `tb_port_is_pcie_up`/`_down` (tb.h:647/642), `usb4_switch_map_pcie_down` (usb4.c:1015) and `usb4_port_index` (:982), `tb_port_is_enabled` (switch.c:1326) as the dispatcher | [prompt] |
| usb3-adapter.md | the USB3 adapter capability: `ADP_USB3_CS_0..4` bit by bit (tb_regs.h:495-514), `tb_usb3_port_is_enabled`/`tb_usb3_port_enable` (switch.c:1352/1370, the V bit), `usb4_usb3_port_max_link_rate` (usb4.c:2204), `usb4_usb3_port_max_bandwidth` (:2188) and the `max_bw` cap as a mechanism, the CM request handshake `usb4_usb3_port_cm_request` (:2223, CMR/HCA, 1500 ms) with `set`/`clear_cm_request` (:2258/2263), the scaling arithmetic `usb3_bw_to_mbps`/`mbps_to_usb3_bw` (:2268/2276) and the scale search (:2368-2408), `usb4_usb3_port_read_allocated_bandwidth`/`_consumed` (:2285/2340), `usb4_usb3_port_allocated_bandwidth`/`_allocate_bandwidth`/`_release_bandwidth` (:2324/2426/2468, the 900 Mb/s floor), `usb4_switch_map_usb3_down` (:1048), `tb_port_is_usb3_up`/`_down` (tb.h:667/662); the tunnel-level bandwidth policy is owned by tunnel/usb3-tunnel.md [errata 2026-09-12, migration of usb3-adapter.md: `set`, `clear_cm_request` and `_consumed` are shorthand for `usb4_usb3_port_set_cm_request`, `usb4_usb3_port_clear_cm_request` and `usb4_usb3_port_read_consumed_bandwidth`, which the coverage oracle cannot expand; and usb4.c:2368-2408 is the definition of `usb4_usb3_port_write_allocated_bandwidth`, the scale search inside it being :2375-2385] | [prompt] |
| dp-adapter.md | the DP adapter capability: `ADP_DP_CS_0`/`_1` fields/`_2`/`_3`/`_8`, `DP_LOCAL_CAP`/`DP_REMOTE_CAP`/`DP_COMMON_CAP` with the shared `DP_COMMON_CAP_*` fields, `DP_STATUS`/`DP_STATUS_CTRL` (tb_regs.h:402-472), `tb_dp_port_set_hops` (switch.c:1471, the USB4 read-only short circuit), `tb_dp_port_is_enabled`/`tb_dp_port_enable` (:1505/1526), HPD (`tb_dp_port_hpd_is_active` :1422, `tb_dp_port_hpd_clear` :1443), `is_usb4_dpin` (usb4.c:2504), the capability accessors reached from tunnel.c (`tb_dp_cap_get_rate`/`_get_rate_ext`/`_set_rate`/`_get_lanes`/`_set_lanes` :664-743, `tb_dp_is_uhbr_rate` :699) and the rate/lane encodings, `tb_port_is_dpin`/`_dpout` (tb.h:652/657); DP resource ownership at the router level (`tb_switch_query`/`alloc`/`dealloc_dp_resource` switch.c:3692-3757 dispatching to `usb4_switch_*_dp_resource` usb4.c:900-958 or `tb_lc_dp_sink_*`) [errata 2026-09-12, migration of dp-adapter.md: the DP-resource span ends at switch.c:3749, the last line of the three dispatchers; :3751 opens `struct tb_sw_lookup`] | [prompt] |
| dp-adapter-bandwidth-mode.md | the DP IN adapter's bandwidth-allocation-mode registers: the `ADP_DP_CS_2` fields (NRD MLC/MLR, CA, GR, GROUP_ID, CM_ID, CMMS, ESTIMATED_BW) and `ADP_DP_CS_8` (REQUESTED_BW, DPME, DR), `DP_COMMON_CAP_BW_MODE`, `DP_STATUS_ALLOCATED_BW`; `usb4_dp_port_set_cm_id` (usb4.c:2525), `_bandwidth_mode_supported`/`_enabled` (:2555/2581), `_set_cm_bandwidth_mode_supported` (:2611), `_group_id`/`_set_group_id` (:2646/2674), `_nrd`/`_set_nrd` (:2707/2766), `_granularity`/`_set_granularity` (:2831/2872), `_set_estimated_bandwidth` (:2919), `_allocated_bandwidth` (:2953), `__usb4_dp_port_set_cm_ack`/`_set_cm_ack` (:2977/2996), `_wait_and_clear_cm_ack` (:3001), `_allocate_bandwidth` (:3050), `_requested_bandwidth` (:3098); the request/allocate/acknowledge cycle at the register level; the tunnel-side enabler `tb_dp_bandwidth_alloc_mode_enable` (tunnel.c:914) and the `bw_alloc_mode` parameter (:97) reached; the CM policy is owned by tunnel/dp-bandwidth-allocation.md | [curated] |

### sideband/

| page | scope (anchor symbols) | tag |
|---|---|---|
| sideband-access.md | sideband register access through the USB4 port: `PORT_CS_1`/`PORT_CS_2` (tb_regs.h:374-383) and the transaction encoding, `enum usb4_sb_target` (tb.h:1377), `usb4_port_sb_read`/`usb4_port_sb_write` (usb4.c:1359/1412) with `usb4_port_read_data`/`_write_data` (:1327/1336), `usb4_port_wait_for_bit` (:1305), the opcode handshake `usb4_port_sb_op` (:1473) and `usb4_port_sb_opcode_err_to_errno` (:1459), `usb4_port_retimer_op` (:1848), `enum usb4_sb_opcode` (sb_regs.h:21-39) as an opcode-to-user table, the `USB4_SB_*` register map (sb_regs.h:13-48) including the registers only debugfs touches, the opcodes written raw without the handshake (router offline :1514, enumerate retimers :1560, NVM authenticate :2088), `USB4_PORT_DELAY`/`USB4_PORT_SB_DELAY` (:51-52) and the 500 ms waits; router offline mode (`usb4_port_set_router_offline`/`usb4_port_router_offline`/`_online` :1504-1542) and inbound SBTX (`usb4_port_retimer_set_inbound_sbtx`/`_unset` :1866/1895, the first-command retry); the debugfs `sb_regs` files named in one sentence (debug/debugfs.md owns them) [errata 2026-09-13, census sweep of sideband-access.md: two page counts were wrong. Offline mode was said to be entered and left "by one caller apiece"; `usb4_port_router_offline()` has one call site, usb4_port.c:85, and `usb4_port_router_online()` has two, usb4_port.c:93 in the unwind and :104 in the enable path. And "four of the eight PORT_CS_1 field macros are a shift with no companion mask" is two, `PORT_CS_1_LENGTH_SHIFT` and `PORT_CS_1_RETIMER_INDEX_SHIFT`: `PORT_CS_1_TARGET_SHIFT` has its mask at tb_regs.h:376 and the other four are `BIT()` masks. The page's own figure and its post-fence paragraph both said two, so it contradicted itself] | [prompt] |
| retimer-enumeration.md | retimers as devices: `struct tb_retimer` (tb.h:339, kerneldoc :326), `tb_retimer_scan()` (retimer.c:510) step by step (`usb4_port_enumerate_retimers` usb4.c:1556, the status pre-read `tb_retimer_nvm_authenticate_status` retimer.c:197, inbound SBTX guarded by the offline state `tb_retimer_set_inbound_sbtx`/`_unset` :214/231, `usb4_port_retimer_is_last`/`_is_cable` usb4.c:1913/1939, `TB_MAX_RETIMER_INDEX` retimer.c:18/20), `tb_retimer_add()` (:389), `tb_retimer_remove()` (:465), `tb_retimer_release()` (:376), `tb_retimer_type` (:383), `retimer_match`/`tb_port_find_retimer` (:478/486), `remove_retimer`/`tb_retimer_remove_all` (:576/592, reverse order), the attributes `device`/`vendor`/`nvm_version`/`nvm_authenticate` and `retimer_is_visible` (:169-374) with ABI (:339-370), runtime PM (:454-459), debugfs init/remove seams (:461/468), the callers (tb.c:1332/1389/1410, usb4_port.c:91/240) and the removal seams; the absence of a resume path stated [errata 2026-09-13, migration of retimer-enumeration.md: the `tb_retimer_set_inbound_sbtx`/`_unset` shorthand resolves in the oracle to the family stem `tb_retimer_unset`, which is not a symbol; the symbol is `tb_retimer_unset_inbound_sbtx` at retimer.c:231. Nothing is missing from the page, and the row's spelling is what produces the finding] | [prompt] |
| retimer-nvm.md | retimer firmware over sideband: `usb4_port_retimer_nvm_sector_size` (usb4.c:1968), `_nvm_set_offset` (:1994), `_nvm_write_next_block`/`_nvm_write` (:2018/2052), `_nvm_authenticate` (:2079, written raw because the retimer loses its index), `_nvm_authenticate_status` (:2106), `_nvm_read_block`/`_nvm_read` (:2138/2179), `struct retimer_info` (:2013), the `USB4_NVM_*` masks (:21-34); the retimer.c side (`tb_retimer_nvm_add` :78, `nvm_read`/`nvm_write` :40/63, `tb_retimer_nvm_read` :34, `tb_retimer_nvm_validate_and_write` :116, `tb_retimer_nvm_authenticate` :138 and its deferred result, `nvm_authenticate_store` :251 as the `enum tb_nvm_write_ops` state machine, `auth_status`, `no_nvm_upgrade`), the `retimer_nvm_vendors` table as a mechanism (nvm.c:273), the `tb_nvm_read_data`/`_write_data` plumbing (nvm.c:560/607), the admin-guide section (:199-277) | [curated] |
| retimer-offline-upgrade.md | the no-cable retimer upgrade journey: `offline_store` (usb4_port.c:159) → `usb4_port_offline` (:76: `tb_acpi_power_on_retimers` acpi.c:263 → `usb4_port_router_offline` usb4.c:1529 → `tb_retimer_scan(port, false)`), `rescan_store` (:210), `usb4_port_online` (:100), `service_attr_is_visible` and `can_offline` (:258-274, acpi.c:350), the sideband opcode `USB4_SB_OPCODE_ROUTER_OFFLINE` (:1504-1542), the resume replay `usb4_port_device_resume` (:363), the `nvm_authenticate` step reached from retimer-nvm.md, the admin-guide procedure (:279-306) and ABI (:313-337); the ACPI retimer power mechanism, merged here from the drafted acpi/retimer-power.md (review item 12): `retimer_dsm_guid` (acpi.c:181-183), `RETIMER_DSM_QUERY_ONLINE_STATE`/`RETIMER_DSM_SET_ONLINE_STATE` (:185-186), `tb_acpi_retimer_set_power` (:188: the `can_offline` gate, the `WARN_ON(!adev)`, query then set through `acpi_evaluate_dsm_typed`, the `-EBUSY` meaning), `tb_acpi_power_on_retimers`/`_off_retimers` (:263/277) and their four callers (usb4_port.c:81/87/94/105), `usb4->can_offline` (tb.h:319, kerneldoc :311) set by `tb_acpi_setup` (acpi.c:339/350), the `!CONFIG_ACPI` stubs returning success | [curated] |
| lane-margining.md | receiver lane margining (gated by `CONFIG_USB4_DEBUGFS_MARGINING`, Kconfig:38): `usb4_port_margining_caps`/`usb4_port_hw_margin`/`usb4_port_sw_margin`/`usb4_port_sw_margin_errors` (usb4.c:1711/1739/1786/1834), `struct usb4_port_margining_params` (tb.h:1421), `enum usb4_margin_sw_error_counter`/`enum usb4_margining_lane` (tb.h:1395/1402), the `USB4_MARGIN_*` sideband fields (sb_regs.h), `struct tb_margining` (debugfs.c:489) and the margining file set (:1720-1763) with `margining_run_write` (:1226) bracketing CLx (:1262/1310), the dwell limits (:44-46), placement per port/switch/xdomain/retimer (:1767-1863), the `TB_MAX_RETIMER_INDEX` bump (retimer.c:17-21) | [curated] |

### host-if/

| page | scope (anchor symbols) | tag |
|---|---|---|
| tb-nhi.md | the host interface object: `struct tb_nhi` field by field (include/linux/thunderbolt.h:518, kerneldoc :500: `lock`, `dev`, `ops`, `iobase`, `tx_rings`/`rx_rings`, `going_away`, `iommu_dma_protection`, `interrupt_work`, `hop_count`, `quirks`, `domain_released`), `struct tb_nhi_ops` (nhi.h:56, kerneldoc :41) callback by callback with the mandatory `init_interrupts` (nhi.c:1192-1196) and the default instance `pci_nhi_default_ops` (pci.c:254; the second, vendor-only instance is named as vendor-only and not documented), the v7.2 split between nhi.c and pci.c, `nhi_probe()` (nhi.c:1186: ops validation, `REG_CAPS` hop count :1198, ring arrays :1201-1206, `nhi_reset`, `nhi_disable_interrupts` :157, `ops->init_interrupts`, the DMA mask :1219, `ops->init`, `domain_released`, `nhi_select_cm` :1163, `tb_domain_add`, runtime PM :1251-1256), `nhi_shutdown()` (:1112), `nhi_reset()` (:1132, `REG_RESET_HRR`, the `host_reset` parameter :39-41), `nhi_wake_supported` (:1013), the `QUIRK_AUTO_CLEAR_INT`/`QUIRK_E2E` bits (nhi.h:122-123) as a mechanism, the dead prototype `nhi_enable_int_throttling` (nhi.h:32) stated as a v7.2 leftover, `RING_TYPE` and the print surface (nhi.c:28); `nhi_mailbox_cmd`/`nhi_mailbox_mode` (nhi.c:870/907, `enum nhi_mailbox_cmd` nhi.h:21, `enum nhi_fw_mode` nhi.h:14) named in one clause as ICM-only (every caller is in icm.c) and never walked [amended 2026-09-04, review item 1] [errata 2026-09-13, census sweep of tb-nhi.md: the page said `RING_TYPE` names the ring direction "everywhere" and its catalog bullet called it the word every ring diagnostic prints. The shutdown loop at nhi.c:1118-1125 prints the direction as a literal string in both of its warnings, and the page reproduces that excerpt itself] | [prompt] |
| pci-driver.md | the PCI NHI driver: `struct tb_nhi_pci` (pci.c:31) and `nhi_to_pci` (:36), `nhi_pci_probe()` (:447: `pcim_enable_device`, `pcim_iomap_region` of BAR0, quirks, IOMMU check, `pci_set_master`, `nhi_probe`), `nhi_pci_remove()` (:482, also `.shutdown`: the `domain_released` wait :492 then `nhi_shutdown`), `nhi_pci_shutdown()` (:233), `nhi_pci_is_present` (:249), `nhi_pci_check_quirks` (:41) as a mechanism with no vendor row, `nhi_pci_imr_valid` (:148), `nhi_pci_start_dma_port`/`_complete_dma_port` (:158/174) as the `pre_nvm_auth`/`post_nvm_auth` hooks, the ID table shape `nhi_ids[]` (:496-585: class-pinned entries, `PCI_CLASS_SERIAL_USB_USB4` nhi.h:119 catch-all; vendor rows named as vendor-only), `nhi_driver` (:591) with `.driver.pm = &nhi_pm_ops` and `nhi_init`/`nhi_unload` (:600/615, `rootfs_initcall`); what the generic driver takes from PCI configuration space (the class code, BAR0, bus mastering, the MSI/MSI-X capability through `pci_alloc_irq_vectors`) with `docs/pci` named as the owner of the PCI core; the IOMMU detection (`nhi_pci_check_iommu`/`_pdev` :77/68) reached and owned by acpi/iommu-dma-protection.md [Orchestrator note 2026-09-04, refuted at write time (pci-driver.md): `nhi_pci_check_quirks` (pci.c:41-66) is an `if` on the vendor wrapping a `switch` on the device identity, not a table-driven match; the table-driven quirk mechanism in the driver is `tb_quirks[]` (quirks.c:63) for `sw->quirks`, which router/router-lifecycle.md owns. [errata 2026-09-13, migration of pci-driver.md: this note first wrote the member as `struct tb_switch.quirks`, a spelling that occurs nowhere in the tree, so no oracle could resolve it and the coverage rule reported it unnamed; the tree writes `sw->quirks`, at quirks.c:12, :29 and :51 and clx.c:189.]] | [prompt] |
| msi-msix.md | interrupts: `nhi_pci_init_msi()` (pci.c:111: `MSIX_MIN_VECS`/`MSIX_MAX_VECS` nhi.h:129-130, `pci_alloc_irq_vectors`, the `msix_ida`, the single-MSI fallback with `INIT_WORK(interrupt_work)` and `devm_request_irq(nhi_msi, IRQF_NO_SUSPEND)`), `nhi_pci_ring_request_msix`/`_release_msix` (:184/220) behind `ops->request_ring_irq`/`release_ring_irq` (nhi.c:571/582/816), `ring_msix()` (nhi.c:444) and `nhi_msi()` (:968) as the hard-IRQ handlers, `nhi_interrupt_work()` (:918) scanning the three `REG_RING_NOTIFY_BASE` bitfields, `ring_interrupt_index` (:43), `nhi_mask_interrupt`/`nhi_clear_interrupt` (:51/63) and the auto-clear quirk, `ring_interrupt_active()` (:76: the `REG_INT_VEC_ALLOC_BASE` nibble arithmetic, the throttling register, the enable bit), `__ring_interrupt_mask`/`__ring_interrupt` (:380/396), `ring_clear_msix` (:429), the registers `REG_RING_NOTIFY_BASE`/`REG_RING_INT_CLEAR`/`REG_RING_INTERRUPT_BASE`/`REG_RING_INTERRUPT_MASK_CLEAR_BASE`/`REG_INT_THROTTLING_RATE`/`REG_INT_VEC_ALLOC_*`/`REG_DMA_MISC` (nhi_regs.h:90-120), the IRQ release order in `nhi_pci_shutdown` (:239-244) | [prompt] |
| rings.md | the descriptor rings: `struct tb_ring` field by field (include/linux/thunderbolt.h:563, kerneldoc :533), `struct ring_desc` (nhi_regs.h:34) and what the hardware writes back, `enum ring_desc_flags` (thunderbolt.h:608), `struct ring_frame` (:627), the ring registers `REG_TX_RING_BASE`/`REG_RX_RING_BASE`/`REG_TX_OPTIONS_BASE`/`REG_RX_OPTIONS_BASE` (nhi_regs.h:52-82) with `ring_desc_base`/`ring_options_base` (nhi.c:171/179) and the `ring_iowrite*` helpers (:187-214), `ring_full`/`ring_empty`/`tb_ring_empty` (:219/224/712), `ring_write_descriptors` (:234), `ring_work` (:268) and the callback context, `__tb_ring_enqueue` (:320) with `tb_ring_rx`/`tb_ring_tx` (thunderbolt.h:682/703), the lifecycle `tb_ring_alloc` (:530) → `nhi_alloc_hop` (:458) → `tb_ring_alloc_tx`/`_rx` (:603/626) → `tb_ring_start` (:642) → `tb_ring_stop` (:751) → `tb_ring_free` (:796), `tb_ring_flush` (:728) with `ring->wait` (new at v7.2), `tb_ring_size`/`tb_ring_frame_size` (thunderbolt.h:648/641), `tb_ring_dma_device` (:724), the lock model (`nhi->lock` then `ring->lock`, the callback run unlocked), `hop_count` and `RING_NOTIFY_REG_COUNT`/`RING_INTERRUPT_REG_COUNT` (nhi_regs.h:91/100) [errata 2026-09-13, migration of rings.md: the allocator pair is written `tb_ring_alloc_tx`/`_rx`, and no oracle expands `_rx`, the same shorthand the domain and router clusters already record. The symbol is cataloged, excerpted and paired on the page] | [prompt] |
| ring-modes.md | raw mode, frame mode and DMA setup: `enum ring_flags` (nhi_regs.h:14) against the software flags `RING_FLAG_NO_SUSPEND`/`RING_FLAG_FRAME`/`RING_FLAG_E2E` (thunderbolt.h:590-594), the register programming in `tb_ring_start` per mode (:658-701: frame size 0/`TB_FRAME_SIZE`, `RING_FLAG_RAW`, the sof/eof masks, the E2E hop field `REG_RX_OPTIONS_E2E_HOP_*`), `TB_FRAME_SIZE`/`TB_MAX_FRAME_SIZE` (thunderbolt.h:638-639), PDF semantics carried in `sof`/`eof`, DMA ownership (the descriptor array `dma_alloc_coherent` :565-567 versus caller-mapped frame buffers: the control channel's `dma_pool` ctl.c:669, `dma_map_single` in the consumers), polling mode (`start_poll`, `tb_ring_poll`/`tb_ring_poll_complete` :348/416, `__ring_interrupt` :396), interrupt throttling (`tb_ring_throttling` :850, `interval_nsec`, the 256 ns units :124-128), the consumers as examples: the control channel (raw), the network service driver drivers/net/thunderbolt/main.c (frame mode with polling, cited from its own source per [coverage.recency]), dma_test.c (:134-186) and stream.c (:554-585) as frame-plus-E2E users [errata 2026-09-13, migration of ring-modes.md: the `dma_pool ctl.c:669` anchor overshoots its own location: that line holds the create call, the field stands at ctl.c:44, and the type is defined outside the directories the page cites] | [prompt] |
| iommu-dma-protection.md | how the domain learns whether the IOMMU protects it: `nhi_pci_check_iommu_pdev` (pci.c:68: `pdev->external_facing` and `device_iommu_capable(IOMMU_CAP_PRE_BOOT_PROTECTION)`), `nhi_pci_check_iommu` (:77: the walk over the NHI's root bus, `nhi->iommu_dma_protection` include/linux/thunderbolt.h:526 set at :106, called from `nhi_pci_probe` :475), the `domainX/iommu_dma_protection` attribute (domain.c:253-261, ABI line 33), the firmware seams that set `external_facing` (`pci_acpi_set_external_facing` reading the `ExternalFacingPort` property, drivers/pci/pci-acpi.c:1416-1431, from `pci_acpi_setup` :1438; the devicetree `external-facing` property drivers/pci/of.c:61-62), the IOMMU drivers' consumers of `external_facing` named at the seam only, the admin-guide section "DMA protection utilizing IOMMU" (Documentation/admin-guide/thunderbolt.rst:179-197) and its relation to the security levels owned by router/security-authorization.md | [curated] |

### control/

| page | scope (anchor symbols) | tag |
|---|---|---|
| tb-ctl.md | the control channel: `struct tb_ctl` (ctl.c:39, kerneldoc :24), ring 0 as the control channel (`tb_ctl_alloc` :653 allocating hop 0 TX and RX with raw-mode masks :674-679) and what HopID 0 means for a control packet that carries a route string, the frame pool (:669) and `rx_packets`/`TB_CTL_RX_PKG_COUNT` (:21), `tb_ctl_alloc`/`tb_ctl_free`/`tb_ctl_start`/`tb_ctl_stop` (:653/705/730/751) and the domain callers under `tb->lock`, the TX path (`tb_ctl_tx` :366: the size rules, `tb_ctl_pkg_alloc` :334, PDF = packet type, `cpu_to_be32_array`, `tb_crc` :320, `tb_ctl_tx_callback` :352), the RX path (`tb_ctl_rx_callback` :445 as a dispatch table: size check, CRC verify, `tb_async_error` :419, event types, request matching, always `tb_ctl_rx_submit` :409), `tb_ctl_handle_event` (:402) → `event_cb` → `tb_domain_event_cb` (domain.c:338) and its XDomain branch, the tracepoints `tb_tx`/`tb_event`/`tb_rx` (trace.h:131-186, `CREATE_TRACE_POINTS` ctl.c:18, sites :388/405/512) with the pretty-printers, the `tb_ctl_*` print macros (:58-73), `timeout_msec` from `TB_TIMEOUT` [errata 2026-09-13, census sweep of tb-ctl.md: two page counts were wrong. "The three sites in the error-decoding paths" undercounts: `tb_cfg_print_error()` at ctl.c:278-317 alone holds five log-macro sites, at :292, :301, :305, :309 and :314. And "the one entry point that starts the channel" is false: `tb_ctl_start()` has four call sites, domain.c:451, :561, :593 and :620] | [prompt] |
| control-packets.md | the control packet formats: `enum tb_cfg_pkg_type` (include/linux/thunderbolt.h:31) type by type (the three ICM types named as ICM-only), `struct tb_cfg_header` (tb_msgs.h:43: `route_hi`/`unknown`/`route_lo` and the reply bit), `struct tb_cfg_address` (:50: offset/length/port/space/seq/zero), `enum tb_cfg_space` (:15) as the four configuration spaces, `enum tb_cfg_error` (:22) code by code, `struct cfg_read_pkg`/`cfg_write_pkg`/`cfg_error_pkg`/`cfg_ack_pkg`/`cfg_event_pkg`/`cfg_reset_pkg` (:60-101) with `TB_CFG_ERROR_PG_*` (:85-86), `tb_cfg_make_header`/`tb_cfg_get_route` (ctl.h:110-115), the receive-side validators `check_header`/`check_config_address`/`parse_header`/`decode_error` (ctl.c:195-263), the transport header the host interface prepends stated as spec-defined and not modeled in the driver; register figures ([registers]) for the header, the address and each packet [errata 2026-09-13, migration of control-packets.md: the `:60-101` span overshoots its code: the six structures run tb_msgs.h:60 to :99, :100 is blank and :101 opens the firmware block this page does not own. Under the convention the row's other multi-symbol spans follow, first start to last start, the span is :60-97] | [prompt] |
| config-requests.md | configuration requests: `struct tb_cfg_request` (ctl.h:77, kerneldoc :52) with `struct tb_cfg_result` (:32) and `struct ctl_pkg` (:46), alloc/get/put/destroy (ctl.c:88-126, `tb_cfg_request_lock` :78), enqueue/dequeue/is_active/find (:133-173, `request_queue_lock`, the `ACTIVE`/`CANCELED` flags ctl.h:98-99), `tb_cfg_request` (:547), `tb_cfg_request_work` (:524), `tb_cfg_request_cancel` (:589, the cancel wait queue :76), `tb_cfg_request_complete` (:597), `tb_cfg_request_sync` (:616, the on-stack completion and timeout), `tb_cfg_match`/`tb_cfg_copy` (:856/883), the API (`tb_cfg_read_raw`/`tb_cfg_write_raw` :956/1030 with `TB_CTL_RETRIES` :22 and the `seq` field, `tb_cfg_read`/`tb_cfg_write` :1111/1137, `tb_cfg_reset` :911, `tb_cfg_ack_notification` :778, `tb_cfg_ack_plug` :842, `tb_cfg_get_upstream_port` :1173), error decoding (`tb_cfg_get_error` :1088, `tb_cfg_print_error` :278, the asynchronous versus synchronous error split), the wrappers `tb_sw_read`/`tb_sw_write`/`tb_port_read`/`tb_port_write` (tb.h:672-714) as the seam every other page crosses, `tb_xdomain_request` (xdomain.c:225) as the other user of the request machinery [errata 2026-09-13, migration of config-requests.md: the row names the two request flags as `ACTIVE`/`CANCELED`, where the tree defines `TB_CFG_REQUEST_ACTIVE` and `TB_CFG_REQUEST_CANCELED` at ctl.h:98-99; the bare second name resolves to nothing and is the engine's one unresolved span for this page. The row also calls the XDomain request the other user of the request machinery, where the tree has three: the XDomain pair, the DMA-port pair and a firmware-manager user] [errata 2026-09-17, rewrite of config-requests.md: the row's `tb_xdomain_request` (xdomain.c:225) "as the other user of the request machinery" resolves as a reach, not a catalog entry; the page excerpts it with `__tb_xdomain_request()`, its match and copy callbacks and its networking consumer, and rule 3 gives the XDP message path to xdomain-protocol.md] | [prompt] |

### tunnel/

| page | scope (anchor symbols) | tag |
|---|---|---|
| path-config-space.md | the path configuration space: `struct tb_regs_hop` bit by bit (tb_regs.h:517-542), `TB_CFG_HOPS` addressing and the `2 * hopid` stride (every `tb_port_read/write(.., TB_CFG_HOPS, 2 * hop, 2)` site in path.c and switch.c:743 for hop 0), the v7.2 reserved-field rule (read-modify-write, `initial_credits`/IFC/ISE only for lane adapters and pre-USB4 routers, path.c:536-570 and :415), `tb_dump_hop` (path.c:16), the debugfs `path` dump and write (debugfs.c:2241-2300, `path_write_one` :207 under the write gate); a register figure ([registers]) of the two dwords | [prompt] |
| path-model.md | paths and hops in the kernel: `struct tb_path_hop` (tb.h:381, kerneldoc :355), `enum tb_path_port` (:400), `struct tb_path` (:430, kerneldoc :408, the v7.2 flexible `hops[]`), `TB_PATH_MIN_HOPID`/`TB_PATH_MAX_HOPS` (:450/455), `tb_path_alloc()` (path.c:233: the port walk `tb_next_port_on_path` switch.c:860 with `tb_for_each_port_on_path`/`_upstream_` tb.h:1141/1153, `num_hops`, `kzalloc_flex`, HopID allocation per hop, the bonded/`link_nr` lane selection :274-308), `tb_path_discover()` (:101) with `tb_path_find_dst_port`/`tb_path_find_src_hopid` (:34/65) and incomplete paths, `tb_path_free()` (:345), `tb_path_is_invalid`/`tb_path_port_on_path` (:598/620), `tb_path_for_each_hop` (tb.h:1213), `tb_port_path_direction_downstream`/`tb_port_use_credit_allocation` (tb.h:1121/1128), the KUnit path cases (test.c:423-1333) as the in-tree exercise; `tb_switch_is_reachable` (switch.c:838) as the walk's containment test [amended 2026-09-04, review item 4] | [prompt] |
| path-activation.md | programming a path: `tb_path_activate()` (path.c:492: counters cleared in reverse, NFC credits added in reverse via `tb_port_add_nfc_credits` switch.c:567, hops written source to destination since v7.2, the double-activation guard, the rollback), `tb_path_deactivate()` (:466), `__tb_path_deactivate_hops`/`__tb_path_deactivate_hop` (:451/378: the `pending` drain with its 500 ms poll, `clear_fc`), `tb_path_deactivate_hop` (:446) for the reset paths, `__tb_path_deallocate_nfc` (:365), the flow-control and shared-buffer masks and how `enum tb_path_port` positions select them (:548-568), `tb_init_pm_support` (tunnel.c:168, `pmps`), the per-protocol path parameters as one table (`tb_pci_init_path` :418, `tb_usb3_init_path` :2178, `tb_dp_init_video_path`/`_aux_path` :1512/1465, `tb_dma_init_rx_path`/`_tx_path` :1800/1835, the priority/weight/HopID constants :19-62) | [prompt] |
| tunnel-model.md | the tunnel object: `struct tb_tunnel` field by field (tunnel.h:73, kerneldoc :33, the flexible `paths[]` [errata 2026-09-13, migration of tunnel-model.md: the row dated this member at v7.2; `git describe --contains 498c05821bb4` answers v7.1-rc1, so it arrived at v7.1]), `enum tb_tunnel_type` (:14), `enum tb_tunnel_state` (:27), the callback set and which protocol fills which (the Area F fill table), `tb_tunnel_alloc` (tunnel.c:178), `tb_tunnel_get`/`tb_tunnel_put`/`tb_tunnel_destroy` (:197/220/204, `tb_tunnel_lock` :112), `tb_tunnel_activate()` (:2405: pre_activate, per-path activation, the ACTIVATING → ACTIVE transition, `-EINPROGRESS`), `tb_tunnel_deactivate()` (:2458), `tb_tunnel_set_active`/`tb_tunnel_changed` (:274/287), `tb_tunnel_is_invalid` (:2382), `tb_tunnel_port_on_path` (:2486), `tb_tunnel_is_activated` (:2503), the predicates (tunnel.h:152-193), the print macros (:224-243), tunnel uevents (`tb_tunnel_event` :241, `enum tb_tunnel_event` tunnel.h:209, the `TUNNEL_EVENT`/`TUNNEL_DETAILS` strings, the admin-guide section :319), the domain's `tunnel_list` with `tb_find_tunnel` (tb.c:490) and `tb_deactivate_and_free_tunnel` (:1722) as the single teardown path [errata 2026-09-13, census sweep of tunnel-model.md: the page said the callback slots are filled in "thirty assignment lines". The ten slots take twenty-eight, all in tunnel.c; the search behind the thirty had `callback` and `callback_data` in its member list, which are not slots. The count is cut rather than corrected] [errata 2026-09-13, census sweep of tunnel-model.md: "the single teardown path" overstates the row. `tb_deactivate_and_free_tunnel()` is the path this page walks, and the unwind ladder at tb.c:2047-2060 hands the same claims back inline without entering it] | [prompt] |
| tunnel-discovery-and-restore.md | tunnels the CM did not create and tunnels it must bring back: `tb_switch_discover_tunnels` (tb.c:376) and `tb_discover_tunnels` (:1694) at start (`sw->boot`, `tb_tunnel_discover_pci`/`_dp`/`_usb3` tunnel.c:452/1589/2205), `tb_free_invalid_tunnels` (:1775), the resume sequence over `tunnel_list` (`tb_resume_noirq` tb.c:3141, the loop at :3163-3193: the firmware-tunnel purge, the USB3 settle delay, the PCIe settle sleep) and the runtime-resume sequence (:3273), what `tb_stop` does to tunnels (:2941), `tb_free_unplugged_children` (:1790) on the tunnel side; the per-protocol "maintained across suspend/resume" bullets of the request are answered here once and reached from each protocol page | [curated] |
| pcie-tunnel.md | PCIe tunnels: `tb_tunnel_alloc_pci`/`tb_tunnel_discover_pci` (tunnel.c:532/452), `tb_pci_init_path`/`tb_pci_init_credits` (:418/391, `TB_MIN_PCIE_CREDITS` :52, the legacy values), `tb_pci_pre_activate` and `tb_pci_port_ltssm_state_detect` (:312/293, new at v7.2), `tb_pci_set_ext_encapsulation` (:327, USB4 v2 Gen 4), `tb_pci_activate` (:361) and its enable/disable ordering, `tb_tunnel_reserved_pci` (:585, `USB4_V2_PCI_MIN_BANDWIDTH` :70); the software CM side `tb_tunnel_pci` (tb.c:2275, the `approve_switch` callback), `tb_find_pcie_down` (:1814) with `usb4_switch_map_pcie_down` (usb4.c:1015) and `tb_find_unused_port` (:460) as the generic paths (the per-controller index table named as vendor-only), `tb_disconnect_pci` (:2254, the `disapprove_switch` callback), `tb_domain_disconnect_pcie_paths` stated as ICM-only; the vendor-only post-activation helpers named and not documented; `authorized` as the trigger (reached); the post-activation steps of `tb_tunnel_pci` at tb.c:2309/2312 (`tb_switch_pcie_l1_enable` switch.c:3944, `tb_switch_xhci_connect`/`_disconnect` :3980/4024, and :2267 on disconnect) named in one clause as vendor-gated helpers whose bodies branch on do-not-cite predicates, walked by neither this page nor adapter/link-controller.md [amended 2026-09-04, review item 22] [errata 2026-09-13, census sweep of pcie-tunnel.md: the page said "Three assignments then make this a PCIe tunnel". The block at tunnel.c:542-545 holds four, setting `pre_activate`, `activate`, `src_port` and `dst_port`] | [prompt] |
| pcie-tunnel-scenarios.md | the three PCIe scenarios as journeys: (1) from `authorized` to a PCIe device: `tb_switch_set_authorized` → `tb_domain_approve_switch` → `tb_tunnel_pci` → `tb_tunnel_activate` (pre_activate LTSSM Detect, path activation, `tb_pci_port_enable` on both adapters) → the tunneled downstream port's link trains → native PCIe hotplug takes over at `pciehp_ist` (drivers/pci/hotplug/pciehp_hpc.c:728) → `pciehp_handle_presence_or_link_change` (pciehp_ctrl.c:232) → `pciehp_check_link_status` (pciehp_hpc.c:291) → `pcie_wait_for_link` (drivers/pci/pci.c:4678), each PCI-side symbol cited as a seam and not documented; (2) hot unplug: the unplug branch → `tb_free_invalid_tunnels` → `tb_deactivate_and_free_tunnel` → what the PCI side observes; (3) suspend and resume: which tunnels survive `tb_suspend_noirq`, the re-activation in `tb_resume_noirq` recapped in one paragraph (tunnel-discovery-and-restore.md owns the loop), the runtime variant, the NVM-authentication root-port pin (`nhi_pci_start_dma_port` pci.c:158) as the related PCI-side pin | [prompt] |
| usb3-tunnel.md | USB3 tunnels: `tb_tunnel_alloc_usb3`/`tb_tunnel_discover_usb3` (tunnel.c:2310/2205), `tb_usb3_init_path`/`tb_usb3_init_credits` (:2178/2160), `tb_usb3_max_link_rate` (:2027), `tb_usb3_pre_activate`/`tb_usb3_activate` (:2044/2054), the bandwidth callbacks (`tb_usb3_consumed_bandwidth` :2068, `_release_unused_bandwidth` :2091, `_reclaim_available_bandwidth` :2106, the 90 % rule :2122/2328, `USB4_V2_USB3_MIN_BANDWIDTH` :71); the software CM side (`tb_tunnel_usb3` tb.c:905, `tb_create_usb3_tunnels` :997, `tb_find_usb3_down` :479 with `usb4_switch_map_usb3_down`, `tb_find_first_usb3_tunnel` :508, `tb_release_unused_usb3_bandwidth`/`tb_reclaim_usb3_bandwidth` :866/876, the `TB_TUNNEL_LOW_BANDWIDTH` event :965), creation only while `hotplug_active` (:1418), suspend and resume (the settle delay tb.c:3172-3181, reached from tunnel-discovery-and-restore.md), the adapter-level helpers reached from adapter/protocol/usb3-adapter.md; the xHCI root port the tunnel feeds is docs/xhci territory and is named in one sentence | [prompt] |
| dp-tunnel.md | DP tunnel anatomy: `tb_tunnel_alloc_dp` (tunnel.c:1690) with its three paths (`TB_DP_VIDEO_PATH_OUT`/`AUX_PATH_OUT`/`AUX_PATH_IN` :41-43, `tb_dp_init_video_path`/`_aux_path` :1512/1465, `tb_dp_init_video_credits`/`_aux_credits` :1483/1454), `tb_tunnel_discover_dp` (:1589) and `tb_dp_dump` (:1536), the capability exchange (`tb_dp_xchg_caps` :815, `tb_dp_cm_handshake` :624, `tb_dp_read_cap` :1337, the LTTPR bit, the vendor-only branches named), `tb_dp_reduce_bandwidth` (:772) and the rate/lane ladder, `tb_dp_bandwidth` (:764) with the encoding factors, `tb_dp_pre_activate`/`tb_dp_activate`/`tb_dp_post_deactivate` (:1016/1144/1042), the DPRX capability wait (`tb_dp_wait_dprx` :1060, `tb_dp_dprx_start`/`_stop`/`_work` :1114/1134/1088, `TB_DPRX_*` :81-83, the `dprx_timeout` parameter, `dprx_started`/`dprx_canceled`) and the asynchronous activation through `tunnel->callback` = `tb_dp_tunnel_active` (tb.c:1906) called without the lock, `tb_dp_maximum_bandwidth`/`_allocated_bandwidth`/`_consumed_bandwidth` (:1368/1263/1391); the KUnit DP cases (test.c:1389-1603) | [prompt] |
| dp-bandwidth-allocation.md | DP bandwidth allocation as the CM performs it: `tb_dp_bandwidth_alloc_mode_enable` (tunnel.c:914) and the `bw_mode` flag, `tb_dp_bandwidth_mode_maximum_bandwidth`/`_consumed_bandwidth` (:1193/1227), `tb_dp_alloc_bandwidth` (:1301), the request flow (`TB_CFG_ERROR_DP_BW` → `tb_handle_notification` tb.c:2885 → `tb_queue_dp_bandwidth_request` :2868 → `tb_handle_dp_bandwidth_request` :2736 → `tb_alloc_dp_bandwidth` :2538 with every branch, the retries `TB_BW_ALLOC_RETRIES` :26 at 50 ms, the `TB_TUNNEL_NO_BANDWIDTH` event :2730, the v7.2 re-run of `tb_tunnel_dp` :2853), the group reservation and `tb_recalc_estimated_bandwidth` (:1515/1432) reached, the adapter-level helpers reached from adapter/protocol/dp-adapter-bandwidth-mode.md; the DPCD-side protocol and the DRM consumer are docs/dp territory and are named in one sentence [errata 2026-09-13, migration of dp-bandwidth-allocation.md: the row wrote this enumerator as `NO_BANDWIDTH`, a name the tree does not carry, so the coverage rule reported it unresolved; the member is `TB_TUNNEL_NO_BANDWIDTH` at tunnel.h:214 and the site the row cites, tb.c:2730, is right] | [prompt] |
| dp-hotplug-flow.md | DP hotplug and the relay to the graphics driver as a journey: DP IN and DP OUT plug events (the scan-time HPD check tb.c:1299, the hotplug branch :2514), `tb_dp_resource_available`/`_unavailable` (:2209/2178) and the `dp_resources` list (`tb_add_dp_resources`/`_remove_`/`_discover_` :111/138/157/172), `tb_tunnel_dp`/`tb_tunnel_one_dp` (:2063/1971) with `tb_find_dp_out` (:1863) and DP OUT reuse, the DP resource query/alloc at the router (reached), TMU accuracy and CLx around a DP tunnel (:254/281, :184/235), redrive mode (`tb_enter_redrive`/`tb_exit_redrive`/`tb_switch_enter_redrive`/`_exit_redrive` tb.c:2104-2176) as a quirk-gated mechanism with no vendor named, the relay: once the tunnel is active the GPU observes HPD on its own DP link and may read the DPCD tunneling region through `drm_dp_tunnel_detect` (drivers/gpu/drm/display/drm_dp_tunnel.c:761) — cited as the seam, owned by docs/dp; suspend and resume (`tb_disconnect_and_release_dp` :2231 at suspend, resources and re-tunneling at resume) [errata 2026-09-13, migration of dp-hotplug-flow.md: the `tb_add_dp_resources`/`_remove_`/`_discover_` shorthand gives three slugs for four line numbers, and `_discover_` covers two real names, `tb_discover_dp_resource` (tb.c:157) and `tb_discover_dp_resources` (tb.c:172); the page catalogs and excerpts both. Also recorded from this page: `tb_tunnel_one_dp()` drops a domain reference it never took when the bandwidth query fails, the jump at tb.c:2022 reaching the `tb_domain_put()` at tb.c:2051 ahead of the only `tb_domain_get()` at tb.c:2030. A driver defect, not a page one, introduced with d6d458d42e1e] | [prompt] |
| dma-tunnel.md | DMA tunnels for host-to-host traffic: `tb_tunnel_alloc_dma`/`tb_tunnel_match_dma` (tunnel.c:1903/1981), `tb_dma_init_rx_path`/`_tx_path` (:1800/1835), `tb_dma_available_credits`/`tb_dma_reserve_credits`/`tb_dma_release_credits` (:1754/1767/1858, `TB_DMA_CREDITS`/`TB_MIN_DMA_CREDITS` :57/59, the `dma_credits` parameter :92), `tb_dma_destroy_path`/`tb_dma_destroy` (:1870/1878), no activate callback; the software CM side `tb_approve_xdomain_paths`/`__tb_disconnect_xdomain_paths`/`tb_disconnect_xdomain_paths` (tb.c:2319/2368/2400) with the CLx disable around a DMA tunnel, the XDomain API `tb_xdomain_enable_paths`/`_disable_paths` (xdomain.c:2439/2470, `ntunnels`) through `tb_domain_approve_xdomain_paths`/`_disconnect_` (domain.c:782/811); the consumers: the network service driver (drivers/net/thunderbolt/main.c) as the driver example ([coverage.recency]), the DMA test driver (dma_test.c:134-223) described in one section, the stream driver named; the KUnit DMA cases (test.c:1790-1973); DOCUMENTATION carries the admin-guide section "Networking over Thunderbolt cable" (Documentation/admin-guide/thunderbolt.rst:352) as the consumer story [amended 2026-09-04, review item 2] | [curated] |

### bandwidth/

| page | scope (anchor symbols) | tag |
|---|---|---|
| credits.md | buffer credits: the adapter fields `total_credits`/`ctl_credits`/`dma_credits` (tb.h:298-300) and the router fields (`credit_allocation`, `max_usb3_credits`, `min_dp_aux_credits`, `min_dp_main_credits`, `max_pcie_credits`, `max_dma_credits` tb.h:210-215), `usb4_switch_credits_init` (usb4.c:758: `USB4_SWITCH_OP_BUFFER_ALLOC`, `enum usb4_ba_index` :39, the masks :36-48, validation and fallback :821-886) and `tb_switch_credits_init` (switch.c:3256), `tb_usable_credits`/`tb_available_credits` (tunnel.c:114/127), the per-protocol credit functions (`tb_pci_init_credits` :391, `tb_usb3_init_credits` :2160, `tb_dp_init_video_credits`/`_aux_credits` :1483/1454, `tb_dma_reserve_credits` :1767) and the constants (`TB_MIN_PCIE_CREDITS` :52, `TB_DMA_CREDITS` :57, `TB_MIN_DMA_CREDITS` :59, the legacy literals), `tb_port_update_credits`/`tb_port_do_update_credits` (switch.c:1269/1234) after bonding, `tb_port_add_nfc_credits` (:567), `ADP_CS_4` as the register source, the KUnit credit cases (test.c:2024-2660) [errata 2026-09-13, migration of credits.md: the KUnit hint `test.c:2024-2660` overshoots: the ninth credit case ends at test.c:2605, and test.c:2607 opens a property fixture no credit case reads] | [prompt] |
| bandwidth-groups.md | bandwidth groups for DP IN adapters: `struct tb_bandwidth_group` (tb.h:238, kerneldoc :222), `MAX_GROUPS` (tb.c:44), `tb_init_bandwidth_groups` (:1580), `tb_bandwidth_group_attach_port`/`tb_find_free_bandwidth_group`/`tb_attach_bandwidth_group`/`tb_discover_bandwidth_group`/`tb_detach_bandwidth_group` (:1595/1607/1622/1658/1676), the reservation (`group->reserved` written in `tb_alloc_dp_bandwidth` :2632/2710) and its 10-second release (`tb_bandwidth_group_release_work` :1567, `__release_group_bandwidth`/`__configure_group_sym` :1532/1543, `TB_RELEASE_BW_TIMEOUT` :20, `system_percpu_wq`), `tb_recalc_estimated_bandwidth`/`_for_group` (:1515/1432) and `usb4_dp_port_set_estimated_bandwidth` reached, the v7.2 `group_reserved[MAX_GROUPS + 1]` fix (:612), the group-id registers reached from adapter/protocol/dp-adapter-bandwidth-mode.md | [prompt] |
| bandwidth-accounting.md | bandwidth arithmetic along a path: `tb_maximum_bandwidth` (tb.c:707), `tb_available_bandwidth` (:815, the guard band :787-788, the seed :823), `tb_consumed_usb3_pcie_bandwidth` (:551), `tb_consumed_dp_bandwidth` (:605), `tb_asym_supported` (:675) as the input to asymmetric-links.md, the tunnel-level entry points `tb_tunnel_maximum_bandwidth`/`_allocated_bandwidth`/`_alloc_bandwidth`/`_consumed_bandwidth`/`_release_unused_bandwidth`/`_reclaim_available_bandwidth` (tunnel.c:2520-2668), `tb_release_unused_usb3_bandwidth`/`tb_reclaim_usb3_bandwidth` (tb.c:866/876), the low-bandwidth threshold (:964), `tb_dp_bandwidth` (tunnel.c:764) and the encoding factors, `TB_ASYM_MIN`/`TB_ASYM_THRESHOLD` and the `asym_threshold` parameter (:32-50) | [curated] |
| asymmetric-links.md | USB4 v2 asymmetric links: `tb_configure_asym`/`tb_configure_sym` (tb.c:1039/1147) and when the CM switches width (`TB_ASYM_MIN`, `asym_threshold`), the CLx disable and enable around the transition (:1110/1129/1212/1227), `tb_switch_asym_enable`/`_disable` (switch.c:3034/3077) through `tb_switch_set_link_width` (:3127) and `tb_port_set_link_width` (:1031), `usb4_port_asym_supported`/`_set_link_width`/`_start` (usb4.c:1595/1618/1666) with `PORT_CS_18_CSA`/`_TIP`, `PORT_CS_19_START_ASYM`, `LANE_ADP_CS_1_TARGET_WIDTH_ASYM_*` and the 1 s/5 s waits, `TB_LINK_WIDTH_ASYM_TX`/`_RX` (include/linux/thunderbolt.h:194-195), the Gen-4 symmetric reconfiguration at scan (tb.c:1257-1263), the activation delta ([facts.activation-delta]): what changes for bandwidth accounting and for the `rx_lanes`/`tx_lanes` attributes once a link is asymmetric [errata 2026-09-13, migration of asymmetric-links.md: the `usb4_port_asym_supported`/`_set_link_width`/`_start` shorthand leaves `_start` unexpandable by any oracle, where the symbol is `usb4_port_asym_start` at usb4.c:1666, the fifth cluster to carry that shape] | [curated] |

### pm/

| page | scope (anchor symbols) | tag |
|---|---|---|
| pm-ops-chain.md | the power-management callback chain from the PCI device down to the routers: `nhi_pm_ops` member by member (nhi.c:1266, non-static since v7.2 and declared in nhi.h:39, consumed by `nhi_driver.driver.pm` at pci.c:597; explicit member initialization), the eleven `nhi_*` callbacks that stay in nhi.c (`nhi_suspend_noirq`/`__nhi_suspend_noirq` :994/975, `nhi_resume_noirq` :1035, `nhi_freeze_noirq`/`nhi_thaw_noirq` :999/1006, `nhi_poweroff_noirq` :1027 with `nhi_wake_supported` :1013 and the `WAKE_SUPPORTED` device property, `nhi_suspend` :1057 as the `.suspend`/`.poweroff` hook whose domain leg `tb_domain_suspend` reaches `cm_ops->suspend`, which `tb_cm_ops` leaves unset, `nhi_complete` :1064, `nhi_runtime_suspend`/`_resume` :1079/1097, `.restore_noirq` aliased to `nhi_resume_noirq`), the PM hooks of `struct tb_nhi_ops` (`suspend_noirq`/`resume_noirq`/`runtime_suspend`/`runtime_resume`, nhi.h:56) and `pci_nhi_default_ops` (pci.c:254) carrying none of them, the domain entries `tb_domain_suspend_noirq`/`_resume_noirq`/`_freeze_noirq`/`_thaw_noirq`/`_complete`/`_runtime_suspend`/`_runtime_resume` (domain.c:528/556/574/588/601/607/618) with the lock asymmetry (the `*_noirq` entries hold `tb->lock` around the CM callback and bracket `tb_ctl_stop`/`tb_ctl_start`; the runtime entries take no lock, so `tb_runtime_suspend`/`_resume` take it themselves), the PM members of `struct tb_cm_ops` (tb.h:507) and which of them `tb_cm_ops` fills (tb.c:3287-3303), the hibernation legs `tb_freeze_noirq`/`tb_thaw_noirq` (tb.c:3203/3211: only `hotplug_active` toggles, the nhi.c:1269-1272 comment) against `.restore_noirq` running the full resume, the device-type PM ops `tb_switch_pm_ops` (switch.c:2368, `SET_RUNTIME_PM_OPS` onto `tb_switch_runtime_suspend`/`_resume` :2347/2358, which reach `cm_ops->runtime_suspend_switch`/`runtime_resume_switch`, both unset in `tb_cm_ops`) and `tb_xdomain_pm_ops` (xdomain.c:2046), the shutdown leg `nhi_shutdown` (nhi.c:1112) and `nhi_pci_shutdown` (pci.c:233); write-time tripwire (review item 15): if the page overruns, split at the domain boundary (this page keeps `nhi_pm_ops` and the `tb_domain_*` entries; a new pm/device-pm-ops.md takes `tb_switch_pm_ops`, `tb_xdomain_pm_ops` and the USB4 port and retimer PM setup) | [curated] |
| system-suspend.md | system suspend as a journey from `nhi_suspend_noirq` to sleeping routers: `tb_suspend_noirq` (tb.c:3077), `tb_disconnect_and_release_dp` (:2231: every DP tunnel torn down and `dp_resources` drained, PCIe, USB3 and DMA tunnels kept), `tb_switch_exit_redrive` (:2159), `tb_switch_suspend` (switch.c:3641: post-order recursion, `tb_switch_clx_disable` :3653, `tb_plug_events_active(sw, false)`, `tb_switch_set_wake` :3492 (the wake-set selection is owned by wakes.md), `usb4_switch_set_sleep` usb4.c:507 writing `ROUTER_CS_5_SLP` and waiting 500 ms for `ROUTER_CS_6_SLPR` against `tb_lc_set_sleep` lc.c:469 for pre-USB4 routers), `hotplug_active = false` (:3085), `tb_ctl_stop` (domain.c:539) [errata 2026-09-10, write time of pm/system-suspend.md: the call is at domain.c:541; :539 is the CM callback], `nhi->ops->suspend_noirq` with `device_may_wakeup`; what survives sleep (the tunnel objects on `tunnel_list`, `sw->clx` cleared, the programmed TMU mode) and what the resume page rebuilds; the XDomain leg `tb_xdomain_suspend` stopping the handshake (xdomain.c:2034); the hibernation legs are pm-ops-chain.md's alone | [curated] |
| system-resume.md | system resume as a journey from `nhi_resume_noirq` (nhi.c:1035: `ops->is_present` and `nhi->going_away`, `tb_domain_resume_noirq` domain.c:556 starting the control channel first) through `tb_resume_noirq` (tb.c:3141: `tb_switch_reset` for a non-USB4 host router, `tb_switch_resume(root, false)`, `tb_free_invalid_tunnels`, `tb_free_unplugged_children`, `tb_free_unplugged_xdomains` :3160, `tb_restore_children` :3091, the tunnel re-activation loop at :3163-3193 recapped in one paragraph (tunnel/tunnel-discovery-and-restore.md owns it), `tb_switch_enter_redrive`, `hotplug_active = true`); `tb_switch_resume` (switch.c:3525: the UID identity check, the v7.2 "XDomain replaced by a router" branch :3611-3625, `tb_switch_configure` :2605 with the Router Ready wait new at v7.2, `tb_switch_check_wakes` :3504, `tb_switch_set_wake(sw, 0, true)`, `tb_switch_tmu_init` :3580, per-port `tb_port_resume` :1297 with `tb_wait_for_port` :498 and `tb_port_unlock`, recursion); `tb_restore_children` re-applying CLx, TMU, `tb_switch_configuration_valid` and link width and re-configuring XDomain ports; `usb4_port_device_resume` (usb4_port.c:363) replaying offline mode; the `.complete` leg `nhi_complete` (nhi.c:1064) to `tb_domain_complete` to `tb_complete` (tb.c:3219) with `tb_domain_unregister_unplugged_xdomains` (domain.c:874) and the rescan under `scoped_guard`; the runtime-suspended case (`pm_runtime_resume` from `nhi_complete`); `tb_xdomain_resume` restarting the handshake (xdomain.c:2040); no retimer resume callback (verified negative) | [curated] |
| runtime-pm.md | the runtime PM callback chain and what it defers: `nhi_runtime_suspend`/`nhi_runtime_resume` (nhi.c:1079/1097: domain first on suspend, controller first on resume), `tb_domain_runtime_suspend`/`_resume` (domain.c:607/618: `tb_ctl_stop` after the CM callback, `tb_ctl_start` before it, no `tb->lock`), `tb_runtime_suspend` (tb.c:3232: DP resources released, redrive exited, `tb_switch_suspend(root, true)` with the runtime wake set, `hotplug_active = false`) and `tb_runtime_resume` (:3263: `tb_switch_resume(root, true)`, invalid tunnels freed, `tb_restore_children`, tunnels re-activated, redrive re-entered, `hotplug_active = true`), the deferred `tcm->remove_work` (tb.c:68, `INIT_DELAYED_WORK` :3393, queued at :3283 with 50 ms, `tb_remove_work` :3250 freeing unplugged children under `tb->lock` and unplugged XDomains outside it, cancelled in `tb_stop` :2947) and why removal is deferred (device removal runtime-resumes the device), `nhi->going_away` making ring start and stop no-ops after a vanished controller (nhi.c:649/757), the DP redrive block on RTD3 (`tb_enter_redrive`/`tb_exit_redrive` tb.c:2104/2129 taking and dropping a router runtime reference while a DP IN adapter drives a display without a tunnel, gated by the `QUIRK_KEEP_POWER_IN_DP_REDRIVE` bit tb.h:28 documented as a flag with no device named, `tb_switch_enter_redrive`/`_exit_redrive` :2147/2159, `port->redrive` tb.h:304), the contrast with system suspend (DP tunnels released for redrive re-entry, no `device_may_wakeup` gating) | [curated] |
| runtime-pm-policy.md | which objects run runtime PM and how references are held: the NHI probe setup (nhi.c:1251-1256: `device_wakeup_enable`, `pm_runtime_allow`, `TB_AUTOSUSPEND_DELAY` tb.h:550, `pm_runtime_use_autosuspend`, `pm_runtime_put_autosuspend`), the domain setup (`tb_domain_add` domain.c:476-483: `pm_runtime_no_callbacks`, `pm_runtime_set_active`, `pm_runtime_enable`, the autosuspend delay), the router policy `sw->rpm` (root router: `tb_switch_is_usb4` tb.c:3016; downstream routers: `sw->generation > 1` tb.c:1373), the enable block in `tb_switch_add` (switch.c:3400-3409: `device_init_wakeup` and `pm_runtime_set_active` unconditionally, the rest only when `sw->rpm`) and the disable block in `tb_switch_remove` (:3436-3439), the USB4 port device (usb4_port.c:329-337) and retimer (retimer.c:454-459) setups, the reference discipline (`pm_runtime_get_sync` then `pm_runtime_mark_last_busy` and `pm_runtime_put_autosuspend`) enumerated by site as a table: sysfs stores switch.c:290/1887/2067, the scan tb.c:1277/1316, the hotplug work tb.c:2430/2456, the DP bandwidth work tb.c:2746, the DP tunnel lifetime (tb.c:2000-2001 held until teardown at :2057-2060), XDomain paths tb.c:2124/2142/2172, usb4_port.c:172/226, retimer.c:46/257, the debugfs brackets; the domain reference taken by `tb_queue_hotplug` (tb.c:101) and dropped in `tb_handle_hotplug` (:2528); the supplier/consumer relation between the NHI and tunneled PCIe ports (the `DL_FLAG_PM_RUNTIME` device links `tb_acpi_add_link` creates, owned by acpi/host-interface-links.md and named here in one sentence); the ICM-only `sw->rpm_complete` named and not explained | [curated] |
| wakes.md | wake sources and their programming: the mask `TB_WAKE_ON_CONNECT`/`DISCONNECT`/`USB4`/`USB3`/`PCIE`/`DP` (tb.h:458-463), the runtime set (all six, switch.c:3664-3668) against the system set (no DP, gated on `device_may_wakeup(&sw->dev)`, :3669-3672), `tb_switch_set_wake` dispatch (switch.c:3492), `usb4_switch_set_wake` (usb4.c:426: per lane-0 adapter `PORT_CS_19_WOC`/`WOD`/`WOU4` tb_regs.h:393-400, the upstream adapter always armed for USB4 wake, downstream adapters gated on `PORT_CS_19_PC` and the USB4 port device's `device_may_wakeup` unless `runtime`; device routers also `ROUTER_CS_5_WOP`/`WOU`/`WOD`), the status side `usb4_switch_check_wakes` (usb4.c:163: `ROUTER_CS_6_WOPS`/`WOUS`, `PORT_CS_18_WOU4S`/`WOCS`/`WODS`, `pm_wakeup_event` on the port device and on the router) reached from `tb_switch_check_wakes` (switch.c:3504, system resume of USB4 routers only), the wakeup-capability setup per object (`device_init_wakeup` in `tb_domain_add` domain.c:476 and `tb_switch_add` switch.c:3400, `device_set_wakeup_capable` for non-upstream USB4 ports usb4_port.c:329-330), `nhi_wake_supported` and the `WAKE_SUPPORTED` property (nhi.c:1013) for the poweroff leg, the pre-USB4 path `tb_lc_set_wake`/`tb_lc_set_wake_one` (lc.c:428/389: the `TB_LC_SX_CTRL` bits WOC/WOD/WOU4/WOP/WODPC/WODPD per link controller, generation 2 and later, device routers only) with no status counterpart (verified negative) | [curated] |
| clx.md | CL states as the kernel tracks them: the mask `TB_CL0S`/`TB_CL1`/`TB_CL2` (tb.h:466-468) held in `sw->clx` for the router's upstream link (tb.h:216, kerneldoc :163), `tb_switch_clx_is_enabled` (tb.h:1088), `clx_name` (clx.c:18), the adapter side (`tb_port_clx_supported` clx.c:68 refusing two single-lane links and inter-domain links, `usb4_port_clx_supported` usb4.c:1574 reading `PORT_CS_18_CPS` against `tb_lc_is_clx_supported` lc.c:259 reading `TB_LC_LINK_ATTR_CPS`, the `LANE_ADP_CS_0_CL0S/CL1/CL2_SUPPORT` bits tb_regs.h:345-347, `tb_port_clx_set`/`_enable`/`_disable`/`tb_port_clx` clx.c:103/137/132/142 on `LANE_ADP_CS_1_CL0S/CL1/CL2_ENABLE`), the PM secondary bit (`tb_port_pm_secondary_set` clx.c:38 on `LANE_ADP_CS_1_PMS`, `tb_switch_pm_secondary_resolve` :240 setting it on the upstream adapter and clearing it on the parent's downstream adapter), the router side (`tb_switch_clx_is_supported` :184 with the `clx` module parameter :14 and the `QUIRK_NO_CLX` flag tb.h:26 as the two software gates, documented as gates with no device named; `tb_switch_clx_init` :211 reading both link ends into `sw->clx` and warning on mismatch; `validate_mask` :301, CL1 requires CL0s; `tb_switch_clx_enable` :321 with the CL2-needs-USB4-v2-on-both-ends rule and its rollback; `tb_switch_clx_disable` :398 returning the mask it cleared and skipping the hardware for an unplugged router), `tb_port_clx_is_enabled` (:173) as a verified dead export [errata 2026-09-09, write time of pm/clx.md: "dead export" reads "dead function with module-wide linkage"; clx.c carries no `EXPORT_SYMBOL`, and the digest's (E) means extern within the module], the vendor-only objection masking (clx.c:257) and the vendor exclusions inside `tb_switch_clx_is_supported` named as excluded code and never explained | [prompt] |
| clx-policy.md | when the connection manager enables CLx and when it tears it down: `tb_enable_clx` (tb.c:184: the depth-1 rule, the DMA-tunnel check on `tb_upstream_port(sw)`, CL0s+CL1+CL2 tried first and CL0s+CL1 second, `-EOPNOTSUPP` mapped to success) and `tb_disable_clx` (:235: up to the host router, returning whether anything was on), every call site with its reason as a table: link-width transitions (`tb_configure_asym` :1110/1129, `tb_configure_sym` :1212/1227), the scan (`tb_scan_port` :1397, skipped during discovery), DMA tunnels (`tb_approve_xdomain_paths` tb.c:2319 disabling at :2339, `__tb_disconnect_xdomain_paths` :2362/2397 re-enabling [errata 2026-09-10, write time of pm/clx-policy.md: tb.c:2362 is the `err_clx` rollback inside `tb_approve_xdomain_paths` (tb.c:2319-2366); `__tb_disconnect_xdomain_paths` begins at tb.c:2368 and its own re-enable is tb.c:2397]; the digest's `__tb_approve_xdomain_paths` does not exist at v7.2, corrected 2026-09-04 at write time), suspend (`tb_switch_suspend` switch.c:3653) and restore (`tb_restore_children` tb.c:3099), lane margining (debugfs.c:1262/1310); the coupling with TMU (`tb_enable_tmu` reads `sw->clx` to choose between the uni-directional and bi-directional modes, tb.c:319-360) and with DP tunnels (`tb_increase_switch_tmu_accuracy` tb.c:254); `sw->clx` as the state between the calls (set at init and enable, cleared at disable and at suspend, re-established on resume by `tb_restore_children`) | [curated] |
| tmu.md | the Time Management Unit as an object: `enum tb_switch_tmu_mode` (tb.h:88, kerneldoc :78, the five modes in accuracy order) and `struct tb_switch_tmu` (tb.h:105: `cap`, `has_ucap`, `mode`, `mode_request`) with the mode/mode_request pair as the state model (seeded equal by `tmu_mode_init` tmu.c:357, `mode_request` moved by `tb_switch_tmu_configure` :1034, `mode` committed by `tb_switch_tmu_enable` at :1013 and forced to OFF by `tb_switch_tmu_disable` at :620), `tb_switch_tmu_is_configured`/`_is_enabled` (tb.h:1052/1065), discovery (`tb_switch_tmu_init` tmu.c:411 finding `TB_SWITCH_CAP_TMU` and the per-adapter `TB_PORT_CAP_TIME1`, called from `tb_switch_add` switch.c:3360 and `tb_switch_resume` :3580; `tb_switch_tmu_ucap_is_supported` :122, `tb_switch_tmu_enhanced_is_supported` :58), the register map `TMU_RTR_CS_0/1/2/3/15/18/22/24/25` and `TMU_ADP_CS_3/6/8/9` (tb_regs.h:245-336) with the tuning tables `tmu_rates[]`/`tmu_params[]` (tmu.c:14-38) and the writers `tb_switch_set_tmu_mode_params` (:63), `tb_switch_tmu_rate_read`/`_write` (:135/149), `tb_port_tmu_write` (:166), `tb_port_tmu_set_unidirectional` (:183), `tb_port_tmu_is_enhanced`/`_enhanced_enable` (:218/232), `tb_port_set_tmu_mode_params` (:254), `tb_port_tmu_rate_write` (:295), `tb_port_tmu_time_sync` (:315, the DTS inversion: `_disable` writes 1), `tb_switch_tmu_set_time_disruption` (:332, `TMU_RTR_CS_0_TD` on USB4 routers against the VSEC register on pre-USB4 routers), `tmu_mode_name` (:40); the vendor-only objection code (tmu.c:704) named as excluded | [prompt] |
| tmu-enable.md | TMU mode transitions as the kernel performs them: `tb_switch_tmu_enable` (tmu.c:950: the time-disruption bracket, the dispatch on (`mode`, `mode_request`), `sw->tmu.mode = mode_request` on success and the pair left divergent on failure), the per-target enables `tb_switch_tmu_enable_bidirectional` (:668), `_unidirectional` (:732, the parent's rate written), `_enhanced` (:775, router then upstream then downstream adapter), `tb_switch_tmu_change_mode` (:866) and its rollback `_change_mode_prev` (:820), `tb_switch_tmu_off` (:627) as the enable-failure rollback, `tb_switch_tmu_disable` (:565) and `disable_enhanced` (:540), the parent/child split (uni-directional and enhanced modes program the parent's rate and the child's upstream adapter, bi-directional programs the child's own rate, the host router only ever writes its own rate :1006), time posting `tb_switch_tmu_post_time` (:447: `TMU_RTR_CS_1..3` read from the root, `TMU_RTR_CS_22/24/25` written, the 100 × 5-10 µs convergence poll :453/521, the post-time write :509), the caller sequence in `tb_enable_tmu` (disable, post time, enable, tb.c:365-373), the ordering constraint that `tb_switch_configuration_valid` runs after TMU enable on the upstream adapter (comment tb.c:1403-1406, sites tb.c:1407 and :3105) | [curated] |
| tmu-policy.md | which TMU mode the connection manager picks and when it re-decides: `tb_enable_tmu` (tb.c:319: enhanced uni-directional first, then uni-directional LOWRES or HIFI when CL1 is on, bi-directional HIFI otherwise, the host router's own LOWRES at `tb_start` :3035-3037), `tb_increase_switch_tmu_accuracy`/`tb_increase_tmu_accuracy` (:254/281, run after a DP tunnel is created at :389 and :1943, depth-1 children only), `tb_switch_tmu_hifi_uni_required`/`tb_tmu_hifi_uni_required` (:301/313), the disable on unplug (`tb_switch_tmu_disable` at tb.c:2466) and the re-enable from `tb_restore_children` (:3099-3101), the scan-time enable (`tb_scan_port` :1400); the coupling with CLx (`sw->clx` read at tb.c:338-356) and the seams to the asymmetric-link and DP bandwidth machinery named in one sentence each | [curated] |

### acpi/

| page | scope (anchor symbols) | tag |
|---|---|---|
| osc-native-usb4.md | how the platform hands USB4 to the kernel: the `_OSC` negotiation done by the ACPI core (`OSC_SB_NATIVE_USB4_SUPPORT` include/linux/acpi.h:611 offered only under `CONFIG_USB4`, drivers/acpi/bus.c:485-508; the USB4 `_OSC` UUID and the four control bits `OSC_USB_USB3_TUNNELING`/`OSC_USB_DP_TUNNELING`/`OSC_USB_PCIE_TUNNELING`/`OSC_USB_XDOMAIN` include/linux/acpi.h:623-626 requested at bus.c:529-553 from `acpi_bus_init` :1514), the two exported results `osc_sb_native_usb4_support_confirmed`/`osc_sb_native_usb4_control` (bus.c:442/517), `tb_acpi_is_native` (acpi.c:122) and its one caller `nhi_select_cm` (nhi.c:1163) choosing the software connection manager, the per-protocol gates `tb_acpi_may_tunnel_usb3`/`_dp`/`_pcie` (acpi.c:134/147/160) and `tb_acpi_is_xdomain_allowed` (:173) with every caller (tunnel.c:137, xdomain.c:87, the tb.c sites) and their permitted-when-not-native default, the `!CONFIG_ACPI` stubs (tb.h:1523-1536: everything permitted, `tb_acpi_add_links` false), the verified documentation gap (no `Documentation/` page names the USB4 `_OSC`) | [curated] |
| host-interface-links.md | the `usb4-host-interface` firmware reference and the device links it creates: `tb_acpi_add_link` (acpi.c:14: `fwnode_find_reference` on the `usb4-host-interface` property, the reference must resolve to `nhi->dev`, non-PCI consumers skipped, only root ports and downstream ports accepted, `device_link_add` with `DL_FLAG_AUTOREMOVE_SUPPLIER \| DL_FLAG_RPM_ACTIVE \| DL_FLAG_PM_RUNTIME` inside a `pm_runtime_get_sync`/`pm_runtime_put` bracket), `tb_acpi_add_links` (:91, `acpi_walk_namespace` to depth 32) and its caller in `tb_probe` (tb.c:3403, after the platform-specific link helper at tb.c:3312, which is vendor-named, never cited by name, and not documented), what the links mean at runtime (the NHI as supplier stays out of D3 while a tunneled port is active and is resumed by its consumers; the seam to pm/runtime-pm-policy.md), the v7.2 `nhi->dev` form of every check | [curated] |
| acpi-companions.md | ACPI companions for routers and USB4 ports: `tb_acpi_bus` (acpi.c:353, the `struct acpi_bus_type` with `.match`/`.find_companion`/`.setup`), `tb_acpi_bus_match` (:282: routers and USB4 port devices), `tb_acpi_find_companion` (:316) and `tb_acpi_switch_find_companion` (:287) walking the `_ADR` hierarchy the acpi.c:319-329 comment documents (the host router at `_ADR 0` under the NHI, downstream-facing ports at `_ADR` equal to the lane-0 adapter number, a device router at `_ADR 0` below its port, the upstream port below that), `tb_acpi_setup` (:339: `acpi_check_dsm` for the two retimer functions setting `usb4->can_offline`), `tb_acpi_init`/`tb_acpi_exit` (:360/365) registering the bus type from `tb_domain_init`/`tb_domain_exit` (domain.c:892/906/918), the consumers of the companion (the USB4 port `connector` symlink through the Type-C connector class named at the seam, the retimer `_DSM` owned by retimer-power.md) [errata 2026-09-12, write time of acpi/acpi-companions.md: the `connector` symlink is no consumer of the companion; `connector_bind` (usb4_port.c:15) creates it on a component match that `typec_link_ports` makes through `usb4_usb3_port_match` against the `usb4-host-interface` reference, and the page states that relation; retimer-power.md was merged into sideband/retimer-offline-upgrade.md by review item 12, which owns the retimer `_DSM`; the Area G ledger's `tb_configfs_init` at domain.c:891 is at :890 on disk, :891 being `tb_debugfs_init`] | [curated] |

### debug/

| page | scope (anchor symbols) | tag |
|---|---|---|
| debugfs.md | the debugfs tree: `tb_debugfs_init`/`_exit` (debugfs.c:2555/2560, the flat `thunderbolt/` root with one directory per `dev_name`), the per-object entry points and their callers (`tb_switch_debugfs_init` :2418 from switch.c:3411, `tb_xdomain_debugfs_init` :2468, `tb_service_debugfs_init` :2484, `tb_retimer_debugfs_init` :2533, the tb.h:1538-1560 stubs), the file set (router `regs` :2425 and `drom` blob :2428, adapter `portN/regs` :2441, `path` :2443, `counters` :2446, `sb_regs` :2449, retimer `sb_regs` :2538, the service directory :2486), the write gate `CONFIG_USB4_DEBUGFS_WRITE` (Kconfig:25, the `#if` :201-454, `DEBUGFS_MODE` :446/453, the `DEBUGFS_ATTR` macros :104-122, `add_taint` at :242/339, the `counters_write` :1895 asymmetry outside the gate), the dump format and the chunked reads with the per-dword fallback (`cap_show` :1965 with the chunking at :1972, `cap_show_by_dw` :1942), the readers per file (`switch_regs_show` :2210, `port_regs_show` :2105, `path_show` :2261, `counters_show` :2324, `port_sb_regs_show` :2386, `retimer_sb_regs_show` :2502) with their `pm_runtime_get_sync` and `tb->lock` brackets, the sideband tables `port_sb_regs[]`/`retimer_sb_regs[]` (:75-102) and the write syntax (:341-348), the three v7.2 fixes; lane margining named at the seam (`margining_port_init` :1767, owned by sideband/lane-margining.md); `dma_test` named at the seam (owned by tunnel/dma-tunnel.md) | [curated] |
| kunit-tests.md | the KUnit suite as executable documentation of the path, tunnel, credit and property mechanisms: `tb_test_suite`/`tb_test_cases[]` (test.c:3147/3098, `CONFIG_USB4_KUNIT_TEST` Kconfig:49, Makefile:11), the fake topology builders (`alloc_switch` :36, `alloc_host` :72, `alloc_host_usb4` :154, `alloc_host_br` :173, `alloc_dev_default` :190, `alloc_dev_with_dpin` :340, `alloc_dev_without_dp` :361, `alloc_dev_usb4` :402, `kunit_ida_init` :31) and what each fakes about a real router, the case groups (path walking :423-739 with `port_expectation`/`hop_expectation` :473/862, path allocation and bonding :842-1242, tunnel allocation :1334-1973, credits :2024-2577 with the `TB_TEST_*` fixtures, the property parser and formatter :2667-3017 with `root_directory[]` :2607 and `compare_dirs` :2754), each group stated as the mechanism it proves and the invariant it pins, the v7.2 additions (the property-parser regression cases), the verified negatives (no wake and no bandwidth cases); excerpts that carry vendor or device identifiers are elided with `...` under the vendor ban | [curated] |

### service/

| page | scope (anchor symbols) | tag |
|---|---|---|
| usb4-stream.md | USB4STREAM, the in-tree service driver that turns a DMA tunnel into a byte stream: the objects `struct tbstream` (stream.c:187), `struct tbstream_group` (:172), `struct tbstream_dev` (:140), `struct tbstream_ring` (:113), `struct tbstream_frame` (:98), `enum tbstream_frame_pdf` (:84), the limits (:72-76), the service driver (`tbstream_ids[]` :1631 with `TB_SERVICE("stream", 1)`, `tbstream_probe`/`_remove` :1543/1564, the driver struct :1643-1645), the configfs surface (`tbstream_group` :1471 registered through `tb_configfs_register_group` :1666, the `<xdomain>.<service>` group :1423/1334/1391, the per-stream `$name` group :1232 with `index`/`in_hopid`/`out_hopid`/`ring_size`/`throttling` :905-1208), the misc device (`tbstream%d` :1373, `tbstream_dev_fops` :889 with read_iter/write_iter/poll/open/release :635-869), the frame-mode rings (`tb_ring_alloc_tx`/`_rx` :554/568 with `RING_FLAG_FRAME \| RING_FLAG_E2E`, the SOF and EOF masks :565-566, `tb_ring_throttling` :584-585), the DMA tunnel request `tb_xdomain_enable_paths`/`_disable_paths` (:577/620), the flush timeout (:613-615), the waitqueue and the kref pairs and the lock order (`sg->lock` before `sdev->lock`, Sweep S2), `configfs.c` (`tb_configfs` :18 as `/sys/kernel/config/thunderbolt/`, `tb_configfs_register_group`/`_unregister_group` :35/45, init and exit :51/58 from domain.c:890/920), Documentation/ABI/testing/configfs-thunderbolt_stream and the admin-guide section (Documentation/admin-guide/thunderbolt.rst:376) [errata 2026-09-13, migration of usb4-stream.md: the driver-struct span `:1643-1645` names three of its members; `tbstream_driver` runs stream.c:1637-1646, and the page carries it whole. Two tree observations from the same pass: the ring-slot allocator raises its floor by one under a host-interface condition at nhi.c:463-464, which any page citing it as a consumer must scope; and the comment at stream.c:875-878 promises a close frame is sent twice if the first fails, where the helper at :537-545 sends one and retries nothing] [errata 2026-09-13, census sweep of usb4-stream.md: the page read the surplus of puts over gets as "the release paths, which drop a reference without having taken one in the same function". That does not hold. On the `tbstream` side `tbstream_remove()` at stream.c:1571 drops what `kref_init()` created in `tbstream_probe()` at :1552; on the device side the surplus is mostly error-path puts inside functions that did take a reference, at :817 and :864 against the get at :814 and at :1620 against the get at :1609. The reading was cut with the census it sat in] | [curated] |

### Fold-in adjudications (topics that do NOT get pages)

Every suggested topic from the Inventory findings that is not a row above is absorbed by the page named here (digest item numbers refer to each area's "Suggested page topics" list). A writer whose page is named as the absorber covers the topic exhaustively; nobody re-litigates these.

Area A (router): A.4 route upload and A.9 the Configuration Valid handshake and A.26 generation detection → router/router-setup.md; A.5 the capability walk → router/router-capabilities.md; A.7 the `usb4_switch_op` proxy seam → router/router-operations.md; A.11/A.12 add and remove ordering → router/router-lifecycle.md; A.13/A.14 device model and sysfs visibility → router/router-device-model.md; A.16 secure connect (the `key` attribute, the HMAC challenge) → FOLD OUT as ICM-only, named in one clause in router/security-authorization.md; A.17/A.18 → router/drom.md; A.19/A.20 → router/nvm.md, which also carries `tb_domain_disconnect_all_paths` (domain.c:845) and its `-EPERM` under the software CM (`disconnect_pcie_paths` unset, domain.c:756-761) as the reason host NVM authentication over the DMA port (switch.c:139) is a pre-USB4 path, verified at write time; A.21 the DMA port mailbox → router/dma-port.md (confirmed at the checkpoint); A.23 `tb_switch_wait_for_bit` → router/router-config-space.md; A.24/A.25 wake, sleep and resume re-enumeration → pm/wakes.md, pm/system-suspend.md, pm/system-resume.md; A.27 the quirk table → router/router-lifecycle.md as a MECHANISM (`tb_check_quirks`, the three flag bits, the match fields) with no table entry, device or vendor named; A.28 → bandwidth/credits.md; A.29 router-level DP resource operations → adapter/protocol/dp-adapter.md; A.30 → adapter/link-controller.md; A.31 the router debugfs surface → debug/debugfs.md; A.32 adapter-index mapping → adapter/protocol/pcie-adapter.md and usb3-adapter.md; A.33 lookup helpers → router/route-string.md; A.34 `tb_switch_is_icm` → router/tb-switch.md.

Area B (domain, CM, XDomain): B.3 `domain_released` → domain/tb-domain.md; B.5 domain sysfs → domain/tb-domain.md (row amended 2026-09-04); B.7 `tb_probe` and CM selection → domain/connection-manager-ops.md (with host-if/tb-nhi.md carrying `nhi_select_cm`); B.12 → domain/domain-start-stop.md and router/router-device-model.md; B.13 the event-to-work seam → domain/router-hotplug.md; B.15 → domain/router-unplug.md and pm/runtime-pm.md (`remove_work`); B.16 and B.26 → tunnel/dma-tunnel.md; B.20 XDomain lane bonding → domain/xdomain-discovery.md; B.22/B.23/B.24 → domain/xdomain-protocol.md; B.25 → adapter/hopid-allocation.md; B.28/B.29/B.30 → domain/xdomain-properties.md; B.32 service matching → domain/services.md (with domain/thunderbolt-bus.md carrying `match_service_id`); B.34 XDomain and service sysfs → domain/xdomain.md and domain/services.md; B.35 the authorization API split → router/security-authorization.md and domain/connection-manager-ops.md.

Area C (adapters): C.2 `tb_init_port` → adapter/tb-port.md; C.3 → adapter/adapter-config-space.md; C.5/C.6/C.7/C.8 the PHY overlay, the port state machine, lane enable and dual-link pairing → adapter/lane-adapter.md; C.11 link speed → adapter/lane-bonding.md; C.12 asymmetric links → bandwidth/asymmetric-links.md; C.13 → adapter/lane-bonding.md; C.14 the speed and lane attributes → router/router-device-model.md; C.15 → bandwidth/credits.md; C.17 the counters configuration space → adapter/adapter-config-space.md; C.18 legacy plug events → router/router-setup.md; C.20 → adapter/usb4-port-capability.md; C.22 → sideband/retimer-offline-upgrade.md; C.24 the `remote`/`xdomain` pointers → adapter/tb-port.md; C.25 → router/router-reset.md.

Area D (protocol adapters, sideband, retimers): D.1 → adapter/adapter-capabilities.md; D.3/D.4 → adapter/protocol/pcie-adapter.md; D.6/D.7/D.8 → adapter/protocol/usb3-adapter.md; D.10 → adapter/protocol/dp-adapter.md; D.11/D.12/D.15 → tunnel/dp-tunnel.md; D.13/D.14 → adapter/protocol/dp-adapter-bandwidth-mode.md; D.17/D.18 the opcode handshake and the sideband register map → sideband/sideband-access.md (the June corpus's separate sideband-registers page is merged here); D.19/D.20 → sideband/sideband-access.md and sideband/retimer-enumeration.md; D.22 the retimer device model → sideband/retimer-enumeration.md; D.24 → sideband/retimer-nvm.md; D.26 → sideband/retimer-offline-upgrade.md (the drafted acpi/retimer-power.md was merged into it, review item 12); D.28 → sideband/lane-margining.md; D.29 the sideband debugfs dump → debug/debugfs.md; D.30 `tb_port_is_enabled` → adapter/tb-port.md.

Area E (host interface, control channel): E.2 the nhi.c/pci.c split → host-if/tb-nhi.md and host-if/pci-driver.md; E.6/E.7/E.8 → host-if/msi-msix.md; E.10/E.15/E.16/E.17 ring lifecycle, flush, the lock model and DMA ownership → host-if/rings.md; E.12 → adapter/hopid-allocation.md and host-if/rings.md; E.13/E.14 polling and throttling → host-if/ring-modes.md; E.18 → host-if/iommu-dma-protection.md (moved from acpi/, review item 13); E.19/E.20 the quirk word and the PCI ID table → host-if/pci-driver.md as MECHANISMS (no device ID, vendor or code name named); E.21 → host-if/tb-nhi.md (owns `nhi_reset`, `REG_RESET`, `host_reset`; router/router-reset.md cites it as the host-router path, review item 11); E.23/E.24 → control/tb-ctl.md; E.25 to E.30 and E.32 → control/config-requests.md and control/control-packets.md; E.31 the event seam → domain/router-hotplug.md and control/tb-ctl.md; E.33 tracing → control/tb-ctl.md (the three tracepoints, the `tb_raw` class, the pretty-printers; verified as the subsystem's only tracepoints); E.34 PM ops wiring → pm/pm-ops-chain.md; E.35 module init order → domain/thunderbolt-bus.md; E.36 → domain/tb-domain.md; E.37 → domain/connection-manager-ops.md.

Area F (paths, tunnels, bandwidth): F.2 → adapter/hopid-allocation.md; F.3 → tunnel/path-model.md; F.7/F.8/F.9/F.41 deactivation, flow control, priority and weight, `pmps` → tunnel/path-activation.md; F.10/F.11/F.12 the three credit models → bandwidth/credits.md; F.16 tunnel uevents → tunnel/tunnel-model.md; F.18/F.19/F.40 → tunnel/pcie-tunnel.md; F.24/F.25 → tunnel/dp-tunnel.md; F.27 the reservation → bandwidth/bandwidth-groups.md; F.28/F.31 → tunnel/dp-bandwidth-allocation.md; F.32 → tunnel/dp-hotplug-flow.md; F.33 DP redrive → pm/runtime-pm.md (named at the seam in tunnel/dp-hotplug-flow.md); F.35/F.42 → tunnel/dma-tunnel.md; F.36/F.37 → tunnel/tunnel-discovery-and-restore.md; F.38 → domain/router-unplug.md and tunnel/pcie-tunnel-scenarios.md; F.39 → pm/tmu-policy.md and pm/clx-policy.md; F.43 → service/usb4-stream.md. [errata 2026-09-06, write time of tunnel/dp-hotplug-flow.md: F.33 landed the other way round. Row 3207 puts `tb_enter_redrive`/`tb_exit_redrive`/`tb_switch_enter_redrive`/`tb_switch_exit_redrive` and `QUIRK_KEEP_POWER_IN_DP_REDRIVE` on tunnel/dp-hotplug-flow.md, which catalogs and excerpts them as a quirk-gated mechanism with no vendor named; pm/runtime-pm.md cites that page for the runtime-PM reference redrive holds instead of re-walking it.]

Area G (PM, CLx, TMU, ACPI): G.1/G.2/G.3 → pm/clx.md; G.4/G.5 → pm/clx-policy.md (the suppression gates as MECHANISMS; the vendor-specific exclusions named as excluded code); G.6/G.7/G.9 → pm/tmu.md; G.8/G.10 → pm/tmu-enable.md; G.11 → pm/tmu-policy.md; G.12/G.15 → pm/pm-ops-chain.md; G.13/G.16 → pm/system-suspend.md; G.14 → pm/system-resume.md; G.17/G.18/G.21 → pm/runtime-pm.md; G.19/G.20 → pm/runtime-pm-policy.md; G.22/G.23/G.24 → pm/wakes.md; G.25/G.26/G.31 → acpi/osc-native-usb4.md; G.27 → acpi/host-interface-links.md; G.28 → acpi/acpi-companions.md; G.29 → sideband/retimer-offline-upgrade.md (review item 12); G.30 → host-if/iommu-dma-protection.md (review item 13); G.32 the vendor NHI force-power and LC mailbox code → FOLD OUT (vendor, ICM).

Sweeps: S1 tracepoints → control/tb-ctl.md; S1 debug-print macro hierarchy → the page of the object each macro prefixes (`__TB_SW_PRINT` router/tb-switch.md, `__TB_PORT_PRINT` adapter/tb-port.md, `__TB_TUNNEL_PRINT` tunnel/tunnel-model.md, `tb_ctl_dbg` control/tb-ctl.md), with the dynamic-debug control stated once per page that cites a `dev_dbg`-backed macro; S1 dump helpers → the page of the object dumped (`tb_dump_switch` router/tb-switch.md, `tb_dump_port` adapter/tb-port.md, `tb_dump_hop` tunnel/path-config-space.md, `tb_dp_dump` tunnel/dp-tunnel.md); S1 `dma_test` → tunnel/dma-tunnel.md as the in-tree DMA tunnel exerciser; S1 configfs → service/usb4-stream.md; S1 sysfs surfaces → each object's page (domain → domain/tb-domain.md, router → router/router-device-model.md, service → domain/services.md, XDomain → domain/xdomain.md, USB4 port → adapter/usb4-port-device.md, retimer → sideband/retimer-nvm.md and sideband/retimer-enumeration.md, the two NVMEM children → router/nvm.md); S1 uevents → tunnel/tunnel-model.md (`TUNNEL_EVENT`), router/router-device-model.md (`USB4_VERSION`, `USB4_TYPE`, `AUTHORIZED`), domain/thunderbolt-bus.md (`MODALIAS`), domain/topology-scan.md (the deferred `KOBJ_ADD`); S1 fault injection, debuggers, dump and replay → verified negative, no page; S1 external tools (`fwupd`, `tbtools`) → FOLD OUT, named only where the admin-guide names them; S1 the vendor-named predicates (10i) → the do-not-cite list carried into every writer brief. S2 asynchronous designs → the page of the owning object (`tb->wq` and the hotplug work → domain/router-hotplug.md, `remove_work` → pm/runtime-pm.md, `interrupt_work` → host-if/msi-msix.md, the XDomain `state_work` → domain/xdomain-discovery.md, the control request queue and callback → control/config-requests.md and control/tb-ctl.md, `dprx_work` → tunnel/dp-tunnel.md, the bandwidth release timer → bandwidth/bandwidth-groups.md, the completions → domain/tb-domain.md and control/config-requests.md, the polling loops → the page that owns each polled register); S2 locking model → `tb->lock` and the proved lock order (S2 L.2) are a table in domain/tb-domain.md, every other lock is owned by the page of the object that embeds it, and the single lockdep assertion (xdomain.c:2259) is cited by domain/xdomain.md.

Fold-outs (out of campaign scope under the request's constraints 4 and 9, recorded so nobody re-litigates): the firmware connection manager (`icm.c` in full, every `cm_ops` member only ICM fills, `tb_switch_is_icm` cited as the discriminator and nothing behind it explained; the NHI mailbox `nhi_mailbox_cmd`/`nhi_mailbox_mode` nhi.c:870/907 with `enum nhi_mailbox_cmd`/`enum nhi_fw_mode` nhi.h:21/14, ICM-only in every caller; the safe-mode router `tb_switch_alloc_safe_mode` switch.c:2570 and the admin-guide safe-mode procedure thunderbolt.rst:308-319); the admin-guide "Forcing power" section (thunderbolt.rst:437, a platform WMI attribute, vendor); the vendor controller code names and their NHI PM code (pci.c:266-445); the vendor-named router predicates (S1 10i); the quirk table entries (quirks.c:63-117); the NVM vendor-ops table entries (nvm.c) beyond the dispatch mechanism; the PCI ID table entries beyond the table's shape; Type-C link training, USB Power Delivery and the retimer ordered-set choreography (no kernel implementation, Corpus 2 audit); the out-of-tree `tbtools`; `drivers/net/thunderbolt/` (outside the Subsystem Map's kernel paths, cited as a driver example ([coverage.recency]) in tunnel/dma-tunnel.md and host-if/ring-modes.md); the DisplayPort protocol side of tunneling (docs/dp territory, campaigns/dp.md seam); the xHCI root port a USB3 tunnel feeds (docs/xhci territory); pciehp and the `bridge_d3` ladder (docs/pci territory).

### Projected total and tag census

85 rows after the adversarial review (86 drafted; acpi/retimer-power.md merged into sideband/retimer-offline-upgrade.md and acpi/iommu-dma-protection.md moved to host-if/): router/ 13, domain/ 12, adapter/ 9, adapter/protocol/ 4, sideband/ 5, host-if/ 6, control/ 3, tunnel/ 12, bandwidth/ 4, pm/ 11, acpi/ 3, debug/ 2, service/ 1. Five rows were drafted [optional] (router/dma-port.md, sideband/lane-margining.md, debug/debugfs.md, debug/kunit-tests.md, service/usb4-stream.md); the checkpoint of 2026-09-04 confirmed all five, so the catalog is 85 firm pages.

Tag census (post-review): 44 [prompt] (every bullet of the request's topic list maps to at least one row; the three "curate" headings map to pm/clx.md, pm/tmu.md and the acpi/ group), 41 [curated] (the five once-optional rows included). The census is re-derived by counting the tag column after the adversarial review and after the checkpoint, and the two counts are recorded as amendments if they move.

Mapping check against the request's topic list: Router (tb-switch, route-string, router-config-space, router-capabilities, router-operations, router-setup, router-lifecycle, router-device-model, drom, nvm, security-authorization, router-reset); Domains (tb-domain, thunderbolt-bus, connection-manager-ops, domain-start-stop, topology-scan, router-hotplug, router-unplug, xdomain, xdomain-discovery, xdomain-protocol, xdomain-properties, services); Adapters (tb-port, adapter-config-space, adapter-capabilities, hopid-allocation); Lane adapters (lane-adapter, lane-bonding, usb4-port-capability, usb4-port-device, link-controller); Protocol adapters (pcie-adapter, usb3-adapter, dp-adapter, dp-adapter-bandwidth-mode); Host interface (tb-nhi, pci-driver, msi-msix, rings, ring-modes, iommu-dma-protection); Control traffic (tb-ctl, control-packets, config-requests); General protocol tunneling (path-config-space, path-model, path-activation, tunnel-model, tunnel-discovery-and-restore, credits, bandwidth-accounting); PCIe tunneling (pcie-tunnel, pcie-tunnel-scenarios); USB3 tunneling (usb3-tunnel); DP tunneling (dp-tunnel, dp-bandwidth-allocation, dp-hotplug-flow, bandwidth-groups, asymmetric-links); the "across suspend/resume" bullets (tunnel-discovery-and-restore plus the per-protocol tunnel pages' suspend sections, and pm/system-suspend, pm/system-resume, pm/runtime-pm); Sideband (sideband-access, retimer-enumeration, retimer-nvm, retimer-offline-upgrade, lane-margining); ACPI aspects (the three acpi/ rows, the retimer `_DSM` inside sideband/retimer-offline-upgrade and the IOMMU signal inside host-if/iommu-dma-protection); Power management and CLx (pm-ops-chain, system-suspend, system-resume, runtime-pm, runtime-pm-policy, wakes, clx, clx-policy); TMU (tmu, tmu-enable, tmu-policy).

### Overlap boundary rules (seam symbols named)

A boundary statement is a floor: it says what a page covers exhaustively, never what a page may not touch. Any page reaches any symbol as far as its own narrative needs and stops where the code stops being about its subject; two pages citing one function is correct when one owns it and the other reaches it. No page takes a fact, a line number or an excerpt from another page; each re-derives from the tree.

1. Router cluster: tb-switch.md owns the object tour (every field, its writer and reader) and the inline helpers; route-string.md owns route encoding, the depth and port arithmetic and the lookup helpers; router-config-space.md owns `ROUTER_CS_0..26` field by field, `tb_sw_read`/`tb_sw_write` and `tb_switch_wait_for_bit`; router-capabilities.md owns the capability list walk and the cached offsets; router-operations.md owns the USB4 router-operation mailbox and every `usb4_switch_*` operation built on it; router-setup.md owns `tb_switch_configure`, `usb4_switch_setup`, the Configuration Valid handshake, generation and version detection and the Notification Timeout; router-lifecycle.md owns `tb_switch_alloc`/`tb_switch_add`/`tb_switch_remove`/`tb_switch_release` in order and the quirk mechanism; router-device-model.md owns the device type, naming, uevent variables and the sysfs group with its visibility rules; drom.md and nvm.md own their acquisition and parsing or their object and authentication flows; security-authorization.md owns levels, `authorized` and the domain approve seams; router-reset.md owns `tb_switch_reset` and `tb_port_reset`. Seams: `tb_switch_configure` (router-setup owns; router-lifecycle and pm/system-resume cite), `usb4_switch_setup` (router-setup owns; router-operations cites the register writes), `tb_switch_find_cap`/`tb_switch_find_vse_cap` (router-capabilities owns; every page that reads a capability cites), `tb_switch_add` (router-lifecycle owns the order; tb-switch, drom, nvm, adapter/usb4-port-device and pm/runtime-pm-policy cite their own step), `tb_switch_set_authorized` (security-authorization owns; tunnel/pcie-tunnel-scenarios walks it), `tb_switch_wait_for_bit` (router-config-space owns; router-setup and pm/system-suspend cite their waits).
2. Domain and connection-manager cluster: tb-domain.md owns `struct tb`, `tb_domain_alloc`/`_add`/`_remove`/`_release`, `domain_released`, the domain sysfs group, `tb->lock` and the subsystem lock-order table; thunderbolt-bus.md owns `tb_bus_type`, the four device types as bus members, matching, probe and remove for services, `MODALIAS` and the module init order; connection-manager-ops.md owns `struct tb_cm_ops` member by member with the software-CM fill table, `struct tb_cm`, `tb_probe` and `nhi_select_cm` from the CM side; domain-start-stop.md owns `tb_start`/`tb_stop`/`tb_deinit` and the discovery-vs-reset start; topology-scan.md owns `tb_scan_switch`/`tb_scan_port`/`tb_configure_link` and every early exit; router-hotplug.md owns the event-to-work chain and every branch of `tb_handle_hotplug`; router-unplug.md owns the unplug propagation and teardown. Seams: `tb_domain_event_cb` (router-hotplug owns the dispatch; control/tb-ctl owns the callback registration), `tb_handle_hotplug` (router-hotplug owns; router-unplug owns only the unplug branches; tunnel/dp-hotplug-flow owns only the DP branches), `tb_scan_port` (topology-scan owns; pm/clx-policy and pm/tmu-policy cite their calls; sideband/retimer-enumeration cites its scan calls), `tb_free_unplugged_children`/`tb_free_unplugged_xdomains` (router-unplug owns; pm/runtime-pm and pm/system-resume cite), `tb_cm_ops` (connection-manager-ops owns the table; pm/pm-ops-chain owns its PM members' chains).
3. XDomain cluster: xdomain.md owns `struct tb_xdomain`, creation, removal, `tb_xdomain_unregister` and the runtime-PM pinning; xdomain-discovery.md owns the state machine, `state_work`, lane bonding for XDomain links and the handshake start/stop including `tb_xdomain_pm_ops` (row amended 2026-09-04); xdomain-protocol.md owns XDP framing, the message set, inbound dispatch and protocol handlers; xdomain-properties.md owns the property block, parser, formatter, copy and merge, and the host directory; services.md owns `struct tb_service`, enumeration, matching, service-supplied properties and the service sysfs surface. Seams: `tb_xdomain_get_properties` (xdomain-discovery owns; services owns `enumerate_services` from there on), `tb_xdomain_handle_request` (xdomain-protocol owns; control/tb-ctl cites the hand-off), `tb_xdomain_enable_paths`/`_disable_paths` (tunnel/dma-tunnel owns; xdomain and services cite), `tb_xdomain_alloc_in_hopid`/`_out_hopid` (adapter/hopid-allocation owns; dma-tunnel cites), `tb_register_property_dir` (xdomain-properties owns; services cites).
4. Adapter cluster: tb-port.md owns `struct tb_port` field by field, `tb_init_port`, the type predicates and the `remote`/`xdomain` pointer invariants; adapter-config-space.md owns `ADP_CS_0..5` and `struct tb_regs_port_header`, `tb_port_read`/`tb_port_write`, the counters configuration space; adapter-capabilities.md owns `tb_port_find_cap`, `cap_phy`/`cap_adap`/`cap_usb4`/`cap_tmu` and the capability list rules; lane-adapter.md owns `LANE_ADP_CS_0/1`, the port state machine, lane enable and disable, dual-link pairing; lane-bonding.md owns bonding at port and router level, link speed and width, `tb_port_wait_for_link_width`; usb4-port-capability.md owns `PORT_CS_18/19` and port configured, unlock, hotplug enable and downstream port reset; usb4-port-device.md owns `struct usb4_port`, its device type, attributes and connector link; hopid-allocation.md owns the in and out HopID IDAs, `TB_PATH_MIN_HOPID`, the NHI exception and the XDomain HopID helpers; link-controller.md owns the LC capability window, `read_lc_desc`, port configured through the LC and the router-level LC registers. Seams: `tb_port_find_cap` (adapter-capabilities owns; every page reading an adapter capability cites), `tb_port_state`/`tb_wait_for_port` (lane-adapter owns; domain/topology-scan and pm/system-resume cite), `tb_switch_set_link_width` (lane-bonding owns; bandwidth/asymmetric-links owns only the asymmetric widths), `usb4_port_configure`/`tb_lc_configure_port` (usb4-port-capability and link-controller own their half; domain/topology-scan cites `tb_switch_configure_link`), `tb_port_alloc_hopid` (hopid-allocation owns; tunnel/path-model cites), `usb4_port_device_add` (usb4-port-device owns; router/router-lifecycle cites its step).
5. Protocol-adapter cluster against the tunnel cluster: pcie-adapter.md, usb3-adapter.md, dp-adapter.md and dp-adapter-bandwidth-mode.md own their capability structures bit by bit and every `tb_*_port_*`/`usb4_*_port_*` helper that reads or writes them; the tunnel pages own the tunnels built over them. Seams: `tb_pci_port_enable` (pcie-adapter owns; tunnel/pcie-tunnel cites the call), `usb4_pci_port_ltssm_state` (pcie-adapter owns the register; pcie-tunnel owns `tb_pci_pre_activate`), `usb4_usb3_port_cm_request` and the allocated-bandwidth writers (usb3-adapter owns; tunnel/usb3-tunnel owns the bandwidth callbacks that call them), `tb_dp_port_set_hops`/`tb_dp_port_enable` (dp-adapter owns; tunnel/dp-tunnel cites), `usb4_dp_port_*` bandwidth-mode helpers (dp-adapter-bandwidth-mode owns; tunnel/dp-bandwidth-allocation owns the request cycle that drives them), `tb_switch_alloc_dp_resource`/`_dealloc_dp_resource` (dp-adapter owns; tunnel/dp-hotplug-flow cites).
6. Sideband and retimer cluster: sideband-access.md owns the sideband transaction protocol, the opcode handshake, the register map, inbound SBTX, router offline and online and the sideband debugfs dump named in one sentence; retimer-enumeration.md owns `struct tb_retimer`, its device type, `tb_retimer_scan`, `usb4_port_enumerate_retimers`, `tb_retimer_remove_all`; retimer-nvm.md owns the retimer NVM object, read and write over sideband and the authentication state machine; retimer-offline-upgrade.md owns the offline flow end to end (sysfs `offline`/`rescan`, router offline, retimer power, rescan, resume replay); lane-margining.md owns the margining sideband API and the debugfs surface. Seams: `usb4_port_sb_op` (sideband-access owns; every retimer page cites), `tb_retimer_scan` (retimer-enumeration owns; domain/topology-scan and retimer-offline-upgrade cite), `tb_acpi_power_on_retimers` (retimer-offline-upgrade owns, review item 12; acpi/acpi-companions cites `tb_acpi_setup`), `usb4_port_router_offline` (sideband-access owns; retimer-offline-upgrade walks it), `tb_switch_clx_disable` around margining (pm/clx.md owns; lane-margining cites), `nvm_authenticate_store` (retimer.c:251; retimer-nvm owns it and the `nvm_authenticate`/`nvm_version` attributes end to end; retimer-enumeration owns `retimer_is_visible` and the identity attributes `device`/`vendor`), nvm.c (router/nvm.md owns; retimer-nvm cites `tb_nvm_read_data`/`tb_nvm_write_data`) [review item 10].
7. Host-interface cluster: tb-nhi.md owns `struct tb_nhi`, `struct tb_nhi_ops`, `nhi_probe`/`nhi_shutdown`, `nhi_select_cm` from the NHI side, `nhi_reset` with the `host_reset` parameter and the NHI registers `REG_CAPS`/`REG_RESET`; iommu-dma-protection.md owns the IOMMU signal (moved from acpi/, review item 13); pci-driver.md owns `struct tb_nhi_pci`, `nhi_pci_probe`/`_remove`/`_shutdown`, `nhi_ids[]` as a shape, the quirk word as a mechanism, the driver registration and the `.pm` pointer; msi-msix.md owns vector allocation, `REG_INT_VEC_ALLOC_BASE`, interrupt masking, the auto-clear quirk and `nhi_interrupt_work`; rings.md owns `struct tb_ring`, descriptors, the ring registers, alloc/start/stop/free, flush, the lock model and DMA ownership; ring-modes.md owns raw and frame modes, E2E, polling and throttling. Seams: `nhi_pci_init_msi` (msi-msix owns; pci-driver cites), `ring_interrupt_active` (msi-msix owns the vector and throttling programming; rings cites), `tb_ring_alloc_tx`/`_rx` (rings owns; ring-modes owns the flag semantics; control/tb-ctl and service/usb4-stream cite as consumers), `nhi_pci_check_iommu` (iommu-dma-protection owns; pci-driver cites), `nhi_pm_ops` (pm/pm-ops-chain owns; pci-driver cites the `.pm` pointer), `nhi_alloc_hop` (rings owns; adapter/hopid-allocation cites) [review item 18], `nhi_reset` (tb-nhi owns; router/router-reset cites) [review item 11].
8. Control cluster: tb-ctl.md owns `struct tb_ctl`, ring 0, TX with the CRC trailer, the RX callback dispatch, the tracepoints and the callback registration to the domain; control-packets.md owns every packet layout and the configuration-space and error enumerations; config-requests.md owns `struct tb_cfg_request`, the queue, sync and cancel, the retry loop, `tb_cfg_read_raw`/`_write_raw`, error decoding, acks and `tb_cfg_get_upstream_port`. Seams: `tb_ctl_rx_callback` (tb-ctl owns; config-requests owns the request-matching branch; domain/router-hotplug cites the event branch), `tb_cfg_request_sync` (config-requests owns; every config read cites through `tb_sw_read`/`tb_port_read`), `tb_cfg_ack_plug`/`tb_cfg_ack_notification` (config-requests owns; router-hotplug cites).
9. Path and tunnel cluster: path-config-space.md owns `struct tb_regs_hop` and the path configuration space addressing; path-model.md owns `struct tb_path`, `struct tb_path_hop`, `tb_path_alloc`, `tb_path_discover`, the walk helpers; path-activation.md owns `tb_path_activate`/`_deactivate`, credits and counters in the write sequence, flow control, priority and weight, `pmps`; tunnel-model.md owns `struct tb_tunnel`, the callback set, refcounting, activation state, uevents; tunnel-discovery-and-restore.md owns discovery at start, `tb_free_invalid_tunnels` and the resume sequence over `tunnel_list`; the per-protocol pages own their allocation, discovery, init and callbacks; pcie-tunnel-scenarios.md and dp-hotplug-flow.md are journeys; dma-tunnel.md owns DMA tunnels, credit reservation, XDomain path approval and the in-tree consumers. Seams: `tb_path_activate` (path-activation owns; tunnel-model cites through `tb_tunnel_activate`), `tb_tunnel_activate`/`_deactivate` (tunnel-model owns; every per-protocol page cites its callbacks), `tb_tunnel_alloc` (tunnel-model owns; per-protocol pages own their `tb_tunnel_alloc_*`), `tb_discover_tunnels` (tunnel-discovery-and-restore owns; domain/domain-start-stop cites), `tb_resume_noirq`'s `tunnel_list` loop at tb.c:3163-3193 (tunnel-discovery-and-restore owns; pm/system-resume, pm/runtime-pm and pcie-tunnel-scenarios recap it in one paragraph) [review item 6], the fixed per-protocol HopIDs and the priority/weight table (tunnel.c:19-62; path-activation owns; adapter/hopid-allocation and the per-protocol pages cite) [review item 18], `tb_tunnel_pci`/`tb_disconnect_pci` (pcie-tunnel owns; router/security-authorization and pcie-tunnel-scenarios cite), `tb_tunnel_dp`/`tb_tunnel_one_dp` (dp-hotplug-flow owns; dp-tunnel owns the tunnel anatomy those build), `tb_approve_xdomain_paths` (dma-tunnel owns; domain/xdomain cites).
10. Bandwidth cluster: credits.md owns the three credit models and every `*_init_credits` computation's inputs; bandwidth-groups.md owns `struct tb_bandwidth_group`, attach and detach, the reservation and its timer; bandwidth-accounting.md owns the arithmetic along a path and the tunnel-level entry points; asymmetric-links.md owns `tb_configure_asym`/`tb_configure_sym` and the width transitions. Seams: `tb_available_credits` (credits owns; per-protocol tunnel pages cite), `tb_available_bandwidth` (bandwidth-accounting owns; tunnel/dp-bandwidth-allocation and asymmetric-links cite), `tb_asym_supported` (bandwidth-accounting owns; asymmetric-links cites), `group->reserved` (bandwidth-groups owns; dp-bandwidth-allocation cites), `tb_switch_set_link_width` (adapter/lane-bonding owns; asymmetric-links owns the asymmetric widths), `tb_port_update_credits` (switch.c:1269; credits owns; adapter/lane-bonding cites the post-bonding re-read), `tb_recalc_estimated_bandwidth` (tb.c:1515; tunnel/dp-bandwidth-allocation owns per fold-in F.28; bandwidth-groups, domain/router-unplug and tunnel/dp-hotplug-flow cite) [review item 19].
11. PM cluster: pm-ops-chain.md owns the callback tables and the domain entries; system-suspend.md and system-resume.md are journeys that own `tb_suspend_noirq`/`tb_switch_suspend` and `tb_resume_noirq`/`tb_switch_resume`/`tb_restore_children`; runtime-pm.md owns the runtime chain, `remove_work` and redrive; runtime-pm-policy.md owns which objects run runtime PM and the reference discipline; wakes.md owns the wake masks, sets, programming and status; clx.md and clx-policy.md own the CLx mechanism and its policy; tmu.md, tmu-enable.md and tmu-policy.md own the TMU object, its transitions and its policy. Seams: `tb_switch_suspend` (system-suspend owns; runtime-pm cites the `runtime` argument's effect; wakes owns the wake-set selection inside it), `tb_switch_resume` (system-resume owns; runtime-pm cites), `tb_restore_children` (system-resume owns; clx-policy and tmu-policy cite their calls), `tb_switch_clx_enable`/`_disable` (clx owns; clx-policy owns every call site), `tb_enable_clx`/`tb_disable_clx` (clx-policy owns; bandwidth/asymmetric-links, tunnel/dma-tunnel and sideband/lane-margining cite), `tb_switch_tmu_enable` (tmu-enable owns; tmu owns the pair it commits), `tb_enable_tmu` (tmu-policy owns; tmu-enable cites the call sequence), `usb4_switch_set_wake`/`usb4_switch_check_wakes` (wakes owns; system-suspend and system-resume cite), `usb4_switch_set_sleep` (system-suspend owns; router/router-config-space owns the `ROUTER_CS_5`/`CS_6` bit layout), `nhi_pm_ops` (pm-ops-chain owns; host-if/pci-driver cites), `tb_domain_runtime_suspend` (runtime-pm owns; pm-ops-chain lists it in the table). Ownership inside the cluster (review item 7): pm-ops-chain owns the tables and the wiring (which pointer points at what, and which members are unset) and the hibernation legs alone (`nhi_freeze_noirq` nhi.c:999, `nhi_thaw_noirq` :1006, `nhi_poweroff_noirq` :1027, `tb_freeze_noirq` tb.c:3203, `tb_thaw_noirq` :3211, the `.restore_noirq` aliasing); every other callback body is owned by the journey page that runs it (`nhi_suspend_noirq`/`__nhi_suspend_noirq` by system-suspend, `nhi_resume_noirq`/`nhi_complete` by system-resume, `nhi_runtime_suspend`/`_resume` by runtime-pm); the wake-set selection inside `tb_switch_suspend` is wakes.md's (review item 8).
12. ACPI cluster: osc-native-usb4.md owns `_OSC`, the gates and the `!CONFIG_ACPI` defaults; host-interface-links.md owns the firmware reference and the device links; acpi-companions.md owns the bus type and companion lookup; the retimer `_DSM` is owned by sideband/retimer-offline-upgrade.md (review item 12) and the IOMMU signal by host-if/iommu-dma-protection.md (review item 13). Seams: `tb_acpi_is_native` (osc-native-usb4 owns; host-if/tb-nhi and domain/connection-manager-ops cite through `nhi_select_cm`), `tb_acpi_may_tunnel_*`/`tb_acpi_is_xdomain_allowed` (osc-native-usb4 owns; the tunnel pages and domain/xdomain cite their gate), `tb_acpi_add_links` (host-interface-links owns; domain/connection-manager-ops cites its `tb_probe` call), `tb_acpi_setup` (acpi-companions owns; sideband/retimer-offline-upgrade owns `can_offline`'s consumers), `nhi_pci_check_iommu` (host-if/iommu-dma-protection owns; host-if/pci-driver cites), `ACPI_COMPANION` consumers (acpi-companions owns; adapter/usb4-port-device cites the connector link).
13. Debug and service group (optional rows): debugfs.md owns the tree, the gate and the register dumps; kunit-tests.md owns the suite; usb4-stream.md owns the stream driver and configfs. Seams: `margining_port_init` (sideband/lane-margining owns; debugfs cites), `tb_switch_debugfs_init` (debugfs owns; router/router-lifecycle cites its step), `tb_ring_alloc_tx`/`_rx` and `tb_xdomain_enable_paths` (host-if/rings and tunnel/dma-tunnel own; usb4-stream cites as a consumer), `tb_configfs_register_group` (usb4-stream owns configfs.c; domain/thunderbolt-bus cites the init order).
14. Cross-subsystem boundary (applies to every row): ACPI-core code (drivers/acpi/) is cited at the named seams (`_OSC` in bus.c) and never documented beyond the call boundary; PCI-core machinery (config space, MSI capability internals, pciehp, PCI PM states, `bridge_d3`) is docs/pci territory and is named in one sentence at the seam (`pci_alloc_irq_vectors`, `pciehp_ist`, `pci_acpi_set_external_facing`); the DisplayPort protocol side of tunneling (DPCD, the DRM tunnel consumer) is docs/dp territory and is named in one sentence (campaigns/dp.md seam); the xHCI root port a USB3 tunnel feeds is docs/xhci territory; the IOMMU drivers are named only; driver-core device links and runtime PM are named as the API called, never documented.
15. House narrative rule: the journey pages (pcie-tunnel-scenarios, dp-hotplug-flow, router-hotplug, router-unplug, system-suspend, system-resume) recap any mechanism another page owns in at most one short paragraph and cite the owning mechanism's anchor symbol instead of re-walking it; every mechanism page states where its journey starts and ends in one sentence.

### Batch order (foundational → derived, ~5 pages per batch; the RECOMMENDED slicing, never a state machine)

- B1: router/tb-switch, router/route-string, router/router-config-space, router/router-capabilities, adapter/tb-port
- B2: adapter/adapter-config-space, adapter/adapter-capabilities, adapter/lane-adapter, control/control-packets, acpi/osc-native-usb4 (hoisted from B9, review item 16: it owns the software-CM gate every later page assumes)
- B3: control/tb-ctl, control/config-requests, host-if/tb-nhi, host-if/rings, host-if/ring-modes
- B4: host-if/pci-driver, host-if/msi-msix, host-if/iommu-dma-protection (moved from acpi/, review item 13), adapter/hopid-allocation (moved from B2 to follow host-if/rings, review item 18), router/router-operations
- B5: router/router-setup, adapter/usb4-port-capability, domain/tb-domain, domain/thunderbolt-bus, acpi/host-interface-links (hoisted from B9, review item 17)
- B6: domain/connection-manager-ops, router/router-device-model, router/router-lifecycle, router/drom, router/nvm
- B7: router/security-authorization, router/router-reset, router/dma-port, acpi/acpi-companions (hoisted from B9, review item 17), adapter/lane-bonding
- B8: adapter/link-controller, adapter/usb4-port-device, adapter/protocol/pcie-adapter, adapter/protocol/usb3-adapter, adapter/protocol/dp-adapter
- B9: adapter/protocol/dp-adapter-bandwidth-mode, sideband/sideband-access, sideband/retimer-enumeration, sideband/retimer-nvm, sideband/retimer-offline-upgrade
- B10: tunnel/path-config-space, tunnel/path-model, tunnel/path-activation, bandwidth/credits, tunnel/tunnel-model
- B11: domain/domain-start-stop, domain/topology-scan, domain/router-hotplug, domain/router-unplug, tunnel/tunnel-discovery-and-restore
- B12: tunnel/pcie-tunnel, tunnel/pcie-tunnel-scenarios, tunnel/usb3-tunnel, bandwidth/bandwidth-accounting, bandwidth/asymmetric-links
- B13: bandwidth/bandwidth-groups, tunnel/dp-tunnel, tunnel/dp-bandwidth-allocation, tunnel/dp-hotplug-flow
- B14: domain/xdomain, domain/xdomain-discovery, domain/xdomain-protocol, domain/xdomain-properties, domain/services
- B15: tunnel/dma-tunnel, pm/clx, pm/clx-policy, pm/tmu, pm/tmu-enable
- B16: pm/tmu-policy, pm/wakes, pm/pm-ops-chain, pm/runtime-pm-policy
- B17: pm/system-suspend, pm/system-resume, pm/runtime-pm, sideband/lane-margining
- B18: debug/debugfs, debug/kunit-tests, service/usb4-stream (the once-optional tail, confirmed at the checkpoint)

Ordering rationale (rewritten after review item 20): the router object, its config space and capabilities, and the adapter object first, because every other page names them; adapter config space, the lane adapter and the packet formats next, with the `_OSC` page beside them because it owns the software-CM gate (`tb_acpi_is_native`) every later page assumes; the control channel and the host interface in B3 so that every later page's register reads have a documented carrier (the B1 and B2 pages cite `tb_sw_read`/`tb_port_read` one batch ahead of their owner, the deliberate cycle-break boundary rule 8 records); the PCI driver, MSI-X, the IOMMU signal, HopIDs (after the rings that own `nhi_alloc_hop`) and router operations close the foundations; router setup, the USB4 port capability, the domain, the bus and the host-interface links before the CM ops table, the router lifecycle and the device model (a router is added to a domain and a bus, and `tb_probe` creates the links); DROM, NVM, security and reset before scanning (scan calls them); lane bonding, the companions, the USB4 port device and the protocol adapters before the tunnels built over them; sideband and the offline flow after the companions it needs; paths, credits and the tunnel model before the domain's start, scan and hotplug pages (which discover and build tunnels); the per-protocol tunnels and the bandwidth machinery next, DP last among them because it needs groups and accounting; XDomain after DMA credits and before the DMA tunnel page that approves its paths; CLx and TMU after the scan and tunnel pages that call them; the PM journeys last because they exercise everything; the five once-optional rows stay at the tails of their batches, where the draft put them.

### Adversarial review outcome (2026-09-04)

Reviewer (a fresh strong-model agent, read-only) checked about 250 anchors across all thirteen groups, confirmed that all 236 digest topics land in a row or a fold-in, that the tag census recomputes, and that every `EXPORT_SYMBOL_GPL` name is reachable from a row; 21 anchors were defective (nine wrong construct or wrong file, twelve off by a few lines) and every load-bearing v7.2-new anchor was exact. 27 items returned; disposition:

1. ACCEPTED — `nhi_mailbox_cmd`/`nhi_mailbox_mode` (nhi.c:870/907; the reviewer's :861 corrected on disk) recorded as ICM-only in the fold-outs and named in one clause in host-if/tb-nhi.md.
2. ACCEPTED — admin-guide :352 "Networking over Thunderbolt cable" assigned to tunnel/dma-tunnel.md; :437 "Forcing power" and :308-319 (safe mode) added to the fold-outs.
3. ACCEPTED — `tb_switch_drom_alloc`/`_free` (eeprom.c:447/460) added to router/drom.md.
4. ACCEPTED — `tb_switch_is_reachable` (switch.c:838) added to tunnel/path-model.md.
5. RECORDED — the cost of dropping debug/debugfs.md (debugfs.c, 2,563 lines, would lose every owner) stated in checkpoint question 2.
6. ACCEPTED — the resume tunnel loop (tb.c:3163-3193) is tunnel/tunnel-discovery-and-restore.md's; pm/system-resume.md and tunnel/pcie-tunnel-scenarios.md rescoped to a one-paragraph recap; the seam added to rule 9.
7. ACCEPTED — pm/pm-ops-chain.md owns the tables, the wiring and the hibernation legs alone; callback bodies belong to the journey that runs them; rule 11 extended; the "contrasts" clause removed from system-suspend.md.
8. ACCEPTED — the wake-set enumeration removed from system-suspend.md; `tb_switch_set_wake` cited as the seam.
9. ACCEPTED — sideband/sideband-access.md names the debugfs `sb_regs` files in one sentence; debug/debugfs.md owns them.
10. ACCEPTED — rule 6 gains the `nvm_authenticate_store` seam (retimer-nvm owns; retimer-enumeration owns the identity attributes; router/nvm.md owns nvm.c).
11. ACCEPTED — `nhi_reset` owned by host-if/tb-nhi.md; fold-in E.21, rule 7 and router/router-reset.md corrected.
12. ACCEPTED — acpi/retimer-power.md merged into sideband/retimer-offline-upgrade.md (the same 130 lines, two crossing seams removed); fold-ins D.26 and G.29 and rules 6 and 12 redirected.
13. ACCEPTED — acpi/iommu-dma-protection.md moved to host-if/ (its mechanism is pci.c and domain.c); fold-ins E.18 and G.30 and rules 7 and 12 redirected; batch B4.
14. RECORDED — adapter/adapter-capabilities.md named in checkpoint question 3 as a merge candidate (target adapter/adapter-config-space.md).
15. RECORDED — the pm-ops-chain split line (the domain boundary) written into the row as a write-time tripwire.
16. ACCEPTED — acpi/osc-native-usb4.md hoisted B9 → B2 (it precedes host-if/tb-nhi and domain/connection-manager-ops).
17. ACCEPTED — acpi/host-interface-links B9 → B5, acpi/acpi-companions B9 → B7, iommu-dma-protection B16 → B4.
18. ACCEPTED — adapter/hopid-allocation B2 → B4 (after host-if/rings); the `nhi_alloc_hop` seam added to rule 7 and the fixed protocol HopIDs seam to rule 9.
19. ACCEPTED — the `tb_port_update_credits` and `tb_recalc_estimated_bandwidth` seams added to rule 10.
20. ACCEPTED — the batch-order rationale rewritten; the B1/B2 forward cite of `tb_sw_read`/`tb_port_read` stated as the deliberate cycle-break rule 8 records.
21. ACCEPTED — the vendor-named link helper is referred to by location (tb.c:3312) in acpi/host-interface-links.md, never by name.
22. ACCEPTED — tunnel/pcie-tunnel.md names the two vendor-gated post-activation helpers in one clause and walks neither; the contradiction with adapter/link-controller.md removed.
23. ACCEPTED — the do-not-cite list extended with the nvm.c vendor-named statics (nvm.c:56-269) and the `nhi_ids[]` vendor rows (Execution & verification).
24. ACCEPTED — safe mode is ICM-only: router-lifecycle.md, router-device-model.md and nvm.md rescoped to one-clause mentions and the admin-guide :308-319 excluded.
25. ACCEPTED — all 21 anchor corrections applied (the two swapped ring helpers, the `TB_SERVICE()` file and the three cross-row inconsistencies included); `cap_show` recorded as :1965 with the chunking at :1972.
26. ACCEPTED — an orchestrator note on Sweep S2 §9d records `tb_domain_event_cb` at domain.c:338.
27. RECORDED — no-change verdicts: coverage complete against all 236 digest topics and the request's list; every v7.2-new anchor exact; the three behavioural claims (the activation order, the dead throttling prototype, the PM ops location) verified against source.

Post-review catalog: 85 rows (80 firm + 5 optional): router/ 13, domain/ 12, adapter/ 9, adapter/protocol/ 4, sideband/ 5, host-if/ 6, control/ 3, tunnel/ 12, bandwidth/ 4, pm/ 11, acpi/ 3, debug/ 2, service/ 1; tags 44 [prompt], 41 [curated] (5 then [optional], all confirmed at the checkpoint).

### Checkpoint questions (put to the user before any page is generated)

1. June 2026 corpus disposition (46 pages, v7.0, at the output root `docs/usb4/`): (a) delete the whole corpus before slice B1 runs, so the overwrite guard sees a clean root and every catalog row is a fresh write [recommended: the layout differs, 21 of its 46 pages would otherwise linger as stale v7.0 siblings under old paths and the other 25 collide by path with catalog rows, and its content is preserved in git history and in the Draft reuse map]; (b) overwrite in place, removing each superseded June page at the checkpoint of the slice that ships its replacement (the Draft reuse map's old-path to new-path mapping drives the removals); (c) keep it beside the new corpus until the campaign completes, then delete. The kernel-glossary-devel corpus at TREE_ROOT is never touched by this campaign.
2. Optional rows: which of router/dma-port.md (pre-USB4 firmware access, generic mechanism), sideband/lane-margining.md (debugfs-gated diagnostics over the sideband), debug/debugfs.md, debug/kunit-tests.md and service/usb4-stream.md (the largest v7.2 addition, an in-tree consumer of DMA tunnels) are in? Dropping debug/debugfs.md orphans debugfs.c (2,563 lines, the fourth-largest file in the subsystem): the write gate, the taint sites, the register dumps and the counters file would have no owner, and the two fold-ins that point at it collapse to one sentence each (review item 5). [recommended: all five except debug/kunit-tests.md, which documents tests rather than a kernel mechanism and carries vendor identifiers in its fixtures].
3. Catalog size: 80 firm rows at docs/acpi granularity under "deep and thorough" (the review already merged acpi/retimer-power into sideband/retimer-offline-upgrade). Confirm, or name merges (the natural ones are pm/tmu-enable into pm/tmu, pm/runtime-pm-policy into pm/runtime-pm, adapter/usb4-port-capability into adapter/usb4-port-device, and adapter/adapter-capabilities into adapter/adapter-config-space, the review's thinnest row at about 120 exclusive lines of cap.c), or name splits.
4. Draft pointers to writers ([facts.derived-pages]): (a) none, every page written fresh from the tree with the reuse map as orchestrator-side reference only [recommended for correctness: every June anchor is v7.0 and the reuse audit found 3/7 to 7/7 anchors drifted per page]; (b) the June corpus's B-verdict pages named in the writer brief as mining pointers for figures and register tables, under the re-derivation rule of [facts.derived-pages]; (c) both corpora as pointers.

## Execution & verification

- Pipeline: writer → orchestrator check per SKILL.md ("Modes"). The page is the writer's end to end (facts and prose, the mechanical QA steps run, the evidence persisted into the worksheet); the orchestrator re-runs the checks per `guidelines/checking.md` [check-pass] and stamps WRITTEN → LINTED at the slice checkpoint, recording `LINTED <date> page sha256: <digest>` in the worksheet's LINT; a page's pipeline ends at LINTED.
- Execution state is NOT recorded here (SKILL.md: a spec records no execution state; state is the catalog-vs-`docs/usb4/` diff, and run events live in the machine-local run log).
- Draft posture: decided at the user checkpoint of 2026-09-04 (Scope decisions, "User-confirmed decisions", decision 4): NONE, amended the same day for Corpus 2's register-layout figures only (the amendment under decision 4 states the reusable set, the section-D pointer a brief carries, and the re-verification a reused figure undergoes; code-flow figures are never reused from either corpus). Otherwise writers research only the v7.2 tree, and no writer brief names a page of either corpus. The two corpora remain audit inputs only: the Draft reuse map records what each page is good for, and no writer brief carries a pointer into either corpus. Whatever the decision, every symbol, line number, excerpt and claim a writer takes from a draft is re-found on the v7.2 tree first ([facts.derived-pages]; the drift ledgers in Inventory findings list what moved).
- Per-page procedure: the four passes of SKILL.md ("The passes"), read by phase per its reading routes, with the writer brief of `guidelines/campaign.md` [briefs] and the check pass of `guidelines/checking.md` [check-pass] [errata 2026-09-11: until this date the line named `guidelines/passes/` (at commit 1bea4ac, before the compaction), a directory that no longer exists, which broke this contract's promise of execution from the spec on any machine; the section numbers cited below were likewise renamed to the guidelines' slugs]; every writer brief carries this file's boundary statements (its cluster's rules plus the cross-subsystem rules), the project bans below, the write-time cautions below, the drift ledger of the page's area, and, for a page whose Corpus 2 counterpart carries a register-layout figure listed in the Draft reuse map's section D, that figure's source path and verification note under the amendment of 2026-09-04 (Scope decisions, decision 4).
- Project-specific writing bans (from the request, on top of the style table): (1) no vendor mentions in authored text: no vendor names (Intel, NVIDIA, AMD, Apple, ASMedia and the like), no controller code names (the "Ridge" series and their successors), no PCI device IDs, no per-device quirk bits; the quirk table, the NVM vendor-ops table and the PCI ID table are documented as MECHANISMS without naming any vendor row, and a vendor-named symbol that a mechanism excerpt unavoidably shows is neither cataloged nor discussed (the xhci campaign's rulings of 2026-09-02 and 2026-09-03 apply: the ban binds authored prose, headings, figures and excerpt selection; it does not reach inside a citation URL such as a mailing-list message-ID domain, and a symbol name inside a verbatim excerpt is not a vendor mention); (2) no firmware-connection-manager content: icm.c and every icm_* symbol, the ICM message structs, the NHI mailbox and firmware-mode code are out of scope; the one licensed mention is the seam where the domain selects its connection manager, stated in one sentence, and a tb_cm_ops callback the software CM leaves unset is named as unset, never explained through its ICM implementation; (3) no hedging wordings (the style table's hedge row governs the sweep); (4) semcode is mandatory for research (an agent on a machine without an index falls back to Grep/Read against the pinned tree and says so in the worksheet); (5) figures are never the "code enumerating flow graph" the request names, which is the banned function-flow shape of figures.md [shapes]. The do-not-cite list carried into every writer brief is Sweep S1 item 10i plus (review item 23) the vendor-named statics of nvm.c (nvm.c:56-269: the `*_switch_nvm_*` and `*_retimer_nvm_*` helpers behind the vendor-ops tables) and the vendor rows of `nhi_ids[]` (pci.c:496-585); a page documents the dispatch table and the row shape, never a vendor row or a vendor helper body.
- Mandatory page features (from the request and the rules): every helper function mentioned gets a concrete usage excerpt cited as a fenced block in DETAILS ([sections.details], [excerpts.catalog-completeness]); REGISTERS is section 6 (Subsystem Map) and carries the config-space and MMIO registers the page's mechanism touches (router CS, adapter CS, lane adapter CS, protocol adapter CS, path CS, counters CS, NHI ring and interrupt registers, sideband registers) with register figures ([registers]) where a word partitions into named bit ranges; the scenario rows (hotplug, unplug, PCIe tunnel to PCIe hotplug, DP HPD relay and bandwidth request, system suspend and resume, runtime suspend and resume) are journey pages organized in run order ([purpose.spine]); every activatable mechanism (CLx, a TMU mode, lane bonding and asymmetric width, DP bandwidth allocation mode, router offline mode, plug events, runtime PM, XDomain paths) carries its activation-delta facet ([facts.activation-delta]); a cited path behind a CONFIG gate names the gate in one sentence; the sysfs and debugfs surfaces of an object are named on the object's page at the attribute level with the ABI file cited in DOCUMENTATION.
- Write-time cautions (line numbers in this file are hints; re-verify on disk). The per-area drift ledgers (Inventory findings, item 11 of each digest) are binding, and every writer brief carries the items below:
  - (1) Both draft corpora predate v7.2: every symbol taken from either is re-found by name on disk, and a symbol that does not survive `git grep` at v7.2 is reported in the worksheet, never written around.
  - (2) The NHI split: the PCI driver is `drivers/thunderbolt/pci.c` (`nhi_pci_probe`/`nhi_pci_remove`/`nhi_pci_shutdown`, `nhi_pci_init_msi`, `nhi_pci_check_quirks`, `nhi_pci_check_iommu`, `nhi_pci_ring_request_msix`/`_release_msix`, `struct tb_nhi_pci`); `nhi.c` keeps the rings, `nhi_probe(struct tb_nhi *)` and `nhi_shutdown`; `nhi_ops.c` does not exist; `struct tb_nhi` carries `dev` and no `pdev`; `nhi->ops` is mandatory (`init_interrupts` required); `nhi->domain_released` is new; `nhi_pm_ops` STAYS in nhi.c (non-static, declared in nhi.h:39) and only the `struct pci_driver` that points at it moved to pci.c.
  - (3) `stream.c` and `configfs.c` exist only at v7.2 and later; `tb_ring_flush`, `tb_ring_size`, `tb_ring_frame_size` and `tb_ring_throttling` are new; `nhi_enable_int_throttling` is a dead prototype (nhi.h:32) with no definition.
  - (4) Paths: hops are activated from source to destination (commit b69af182b556); reserved path fields are skipped on USB4 routers by read-modify-write (7e49bb89df86); `struct tb_path.hops` and `struct tb_tunnel.paths` are flexible arrays allocated with `kzalloc_flex`; allocation idioms are the `kzalloc_obj`/`kzalloc_flex` family where the diff introduced them, so excerpts must match disk bytes and never remembered `kzalloc(sizeof)` forms.
  - (5) PCIe tunnels verify the adapter's LTSSM Detect state before activation (`tb_pci_pre_activate`, `usb4_pci_port_ltssm_state`, commit 69a7b98770b7).
  - (6) Router enumeration and resume wait for Router Ready (`ROUTER_CS_6_RR`, 500 ms, in `usb4_switch_setup`); Configuration Ready waits 500 ms (was 50 ms); the Notification Timeout is 0xff for every router and is written by `tb_switch_configure`, no longer by `tb_plug_events_active`.
  - (7) XDomain: removal runs outside `tb->lock` (`tb_xdomain_unregister`, the subsystem's only lockdep assertion at xdomain.c:2259); `tb_domain_unregister_unplugged_xdomains` is new; services hold an XDomain reference; the property parser carries bounds checks and `tb_property_merge_dir`/`tb_property_copy` are new; `struct tb_service_id` and `TB_SERVICE()` are in include/linux/device-id/tb.h.
  - (8) `tb_switch_nvm_add` is split into `tb_switch_nvm_init` and `tb_switch_nvm_add`; the DMA-port NVM authentication helpers moved behind `nhi->ops->pre_nvm_auth`/`post_nvm_auth`; `tb_stop` sets `tb->root_switch` to NULL.
  - (9) Symbols verified ABSENT at v7.2 (never cite): `tb_tunnel_restart`, `tb_path_switch_on_path`, `tb_bandwidth_group_reservation`, `TB_CFG_DEFAULT_TIMEOUT`, `TB_CTL_RX_PKG_SIZE`, `usb4_usb3_port_actual_link_rate`, `usb4_port_is_offline`, `tb_path_dbg`, `nvm_authenticate_start_dma_port`, `nvm_authenticate_complete_dma_port`, `module_tb_service_driver`, `ring_request_msix`, `ring_release_msix`.
  - (10) `clx.c`, `tmu.c`, `lc.c` and `retimer.c` are byte-identical between v7.0 and v7.2; their June-corpus anchors are the only ones expected to survive unchanged, and they are still re-verified on disk.
  - (11) The kerneldoc of `struct tb_nhi` (include/linux/thunderbolt.h:500) and `struct tb_nhi_ops` (nhi.h:41) changed with the split; excerpts of either come from disk, never from a June page.
  - (12) Function-level diff v7.0 → v7.2 over `drivers/thunderbolt/*.c` (definitions only; derived at planning time by listing every C function definition in each file at both tags with `git show <tag>:<path>` through the awk filter below, then diffing the name sets; re-derivable on any checkout). Definitions REMOVED at v7.2 (11; a page never cites one as live code): `nhi_check_iommu`, `nhi_check_iommu_pdev`, `nhi_check_quirks`, `nhi_enable_int_throttling`, `nhi_imr_valid`, `nhi_init_msi`, `nhi_remove`, `nvm_authenticate_complete_dma_port`, `nvm_authenticate_start_dma_port`, `ring_release_msix`, `ring_request_msix`. Definitions ADDED at v7.2 (88; each is an activation-delta candidate ([facts.activation-delta]) and none exists in either draft corpus): `copy_dir`, `nhi_pci_check_iommu`, `nhi_pci_check_iommu_pdev`, `nhi_pci_check_quirks`, `nhi_pci_complete_dma_port`, `nhi_pci_imr_valid`, `nhi_pci_init_msi`, `nhi_pci_is_present`, `nhi_pci_probe`, `nhi_pci_remove`, `nhi_pci_ring_release_msix`, `nhi_pci_ring_request_msix`, `nhi_pci_shutdown`, `nhi_pci_start_dma_port`, `nhi_to_pci`, `service_get_hopids`, `service_remove_properties`, `service_update_properties`, `tb_configfs_exit`, `tb_configfs_init`, `tb_configfs_register_group`, `tb_configfs_unregister_group`, `tb_domain_unregister_unplugged_xdomains`, `tb_pci_port_ltssm_state_detect`, `tb_pci_pre_activate`, `tb_property_copy`, `tb_property_merge_dir`, `tb_ring_empty`, `tb_ring_flush`, `tb_ring_frame_size`, `tb_ring_size`, `tb_ring_throttling`, `tb_service_properties_changed`, `tbstream_dev_alloc_in_hopid`, `tbstream_dev_alloc_out_hopid`, `tbstream_dev_alloc_rx_buffers`, `tbstream_dev_alloc_tx_buffers`, `tbstream_dev_closed`, `tbstream_dev_consume_rx`, `tbstream_dev_detach_stream`, `tbstream_dev_fops_open`, `tbstream_dev_fops_release`, `tbstream_dev_get`, `tbstream_dev_index_show`, `tbstream_dev_in_hopid_show`, `tbstream_dev_item_release`, `tbstream_dev_out_hopid_show`, `tbstream_dev_put`, `tbstream_dev_release`, `tbstream_dev_removed`, `tbstream_dev_ring_size_show`, `tbstream_dev_send_close`, `tbstream_dev_start`, `tbstream_dev_stop`, `tbstream_dev_throttling_show`, `tbstream_dev_update_properties`, `tbstream_dev_valid`, `tbstream_dev_xdomain`, `tbstream_exit`, `tbstream_get`, `tbstream_group_attach_stream`, `tbstream_group_detach_stream`, `tbstream_group_find`, `tbstream_init`, `tbstream_item_release`, `tbstream_probe`, `tbstream_put`, `tbstream_release`, `tbstream_remove`, `tbstream_resume`, `tbstream_ring_available`, `tbstream_ring_free`, `tbstream_suspend`, `tbstream_valid`, `tb_switch_nvm_init`, `tb_test_property_merge`, `tb_test_property_parse_dir_len_underflow`, `tb_test_property_parse_recursion`, `tb_test_property_parse_rootdir_overflow`, `tb_test_property_parse_u32_wrap`, `tb_test_property_parse_zero_length`, `tb_xdomain_unregister`, `to_tbstream_dev`, `__unregister_service`, `unregister_unplugged_xdomain`, `update_service`, `update_service_properties`, `usb4_pci_port_ltssm_state`. Renames are the `nhi_*` → `nhi_pci_*` family, `ring_request_msix`/`ring_release_msix` → `nhi_pci_ring_request_msix`/`nhi_pci_ring_release_msix`, and `nvm_authenticate_start_dma_port`/`_complete_dma_port` → `nhi_pci_start_dma_port`/`nhi_pci_complete_dma_port` behind `tb_nhi_ops`.

    ```
    # every C function definition in <path> at <tag>, printed as "path:line name"
    git show "$tag:$path" | awk -v p="$path" '
      /^[A-Za-z_][A-Za-z0-9_ \t\*]*[ \t\*]+[A-Za-z_][A-Za-z0-9_]*\(/ && !/;[ \t]*$/ && !/^(static |)(struct|enum|union) [a-z_]+ \{/ && !/^#/ && !/=/ {
        line=$0; sub(/\(.*/, "", line); n=split(line, a, /[ \t\*]+/); name=a[n];
        if (name != "" && name !~ /^(if|for|while|switch|return|sizeof)$/) print p ":" NR " " name
      }'
    ```
- Save policy: pages land only under `docs/usb4/<group>/` at their catalog paths. The June 2026 corpus on disk is deleted before slice B1's first writer is dispatched (`git rm -r docs/usb4/` at SKILL_DIR, committed with B1's pages at the user's commit go), per the checkpoint decision of 2026-09-04 recorded in Scope decisions. No `SUMMARY.md` or `mkdocs.yml` edits. No git commits without an explicit user go.

- [errata 2026-09-11, the catalog form] The engine now checks kernel.md [sections.coverage-form] (the structure assert `catalog-entry-form`): every bullet under COVERAGE must be a catalog entry in the quoted form `'\<name\>':'path'` with one backslash before `<` and `>`. Found at the write of pm/pm-ops-chain.md, whose 36 bullets carried a double backslash the catalog parser never read, so every catalog-dependent check had passed on an empty catalog; the page was fixed in place by the check pass. The same sweep over the pages on disk found 203 deviating bullets on 28 pages: 100 in the plain form `- [`NAME`](url)`, which the parser catalogs, and 103 in a quoted form without brackets or with a member declaration, which the parser drops, so on those pages completeness, scope closure and catalog anchors have been checked against a partial catalog. User decision 2026-09-11: keep the rule strict and defer the corpus. Those pages report FAIL under the current rules and count as WRITTEN until a later slice rewrites their bullets (the name and file of a plain or bracket-less entry derive from its URL; a member-declaration entry needs a per-page decision between the member's own symbol and a prose link); new pages are held to the form now. The pages, with their plain and unread counts: adapter/adapter-capabilities (10 plain); adapter/adapter-config-space (7 plain); adapter/hopid-allocation (0 plain, 4 unread); adapter/lane-bonding (0 plain, 11 unread); adapter/link-controller (12 plain); adapter/protocol/pcie-adapter (5 plain); adapter/protocol/usb3-adapter (18 plain); adapter/usb4-port-capability (6 plain); adapter/usb4-port-device (0 plain, 7 unread); bandwidth/asymmetric-links (0 plain, 9 unread); bandwidth/bandwidth-accounting (7 plain, 1 unread); bandwidth/bandwidth-groups (0 plain, 8 unread); bandwidth/credits (0 plain, 8 unread); control/config-requests (0 plain, 5 unread); control/tb-ctl (8 plain); domain/domain-start-stop (0 plain, 1 unread); domain/router-hotplug (0 plain, 5 unread); domain/router-unplug (0 plain, 2 unread); domain/tb-domain (0 plain, 20 unread); domain/xdomain-discovery (0 plain, 4 unread); domain/xdomain-protocol (0 plain, 3 unread); host-if/pci-driver (3 plain, 3 unread); host-if/rings (8 plain); pm/clx (0 plain, 7 unread); router/router-capabilities (3 plain); router/router-config-space (13 plain); tunnel/pcie-tunnel-scenarios (0 plain, 1 unread); tunnel/usb3-tunnel (0 plain, 4 unread).

- [errata 2026-09-13, the suffix shorthand] A scope cell that names a pair as `tb_foo_init`/`_exit` or `tb_register_x`/`_unregister` cannot be closed mechanically: `plugins/coverage.py` resolves the second half against the tree as the bare token, which the tree-wide oracle answers for, so no expansion is attempted and the symbol is reported absent. The domain cluster's migration hit it on five rows, xdomain.md (`tb_xdomain_link_init`/`_exit`), xdomain-discovery.md (`tb_xdomain_suspend`/`_resume`), xdomain-properties.md (`tb_register_property_dir`/`_unregister`), xdomain-protocol.md (`tb_register_protocol_handler`/`_unregister`) and services.md (`tb_register_service_driver`/`_unregister`), each time on a symbol its page defines and excerpts. Spelling both halves out in the row clears the note; no page invented a location for one.

- [errata 2026-09-13, the "new at v7.2" shorthand] The phrase appears 32 times in this file and means new since v7.0, which is the ledger window this spec was planned over, not a release. Inside a catalog row it reads as a release claim and a writer copies it as one: router-device-model.md dated commit 4573add760b8 at this version where `git describe --contains` answers v7.1-rc1, and xdomain-properties.md dated five parser-hardening commits at v7.2 where three are v7.1-rc6 and two are v7.1. A row that means the window says so; a row that means a release names it.

## Draft reuse map

[errata 2026-09-05: both corpora below are archived under tags of this repository and are retrievable from any branch without a checkout: Corpus 1 at `archive/usb4-2026-06-v7.0` (`git show archive/usb4-2026-06-v7.0:docs/usb4/<path>`; `git ls-tree -r --name-only archive/usb4-2026-06-v7.0 -- docs/usb4` lists the 47 files), Corpus 2 at `archive/kernel-glossary-devel-v6.19` with its full history under `refs/archive/kernel-glossary-devel` (`git show archive/kernel-glossary-devel-v6.19:docs/usb4/<path>`; 50 files; its own remote is git@github.com:0xFF07A1/kernel-glossary-devel.git, branch archive/kernel-glossary-devel-to-kmemo at 83bf2f4). The kernel-glossary-devel directory at TREE_ROOT was removed on 2026-09-05; every path in this map that names it resolves through the tag. A brief that licenses a section-D figure names the tag and the path.]

Two corpora were audited read-only on 2026-09-04 by dedicated agents ([facts.derived-pages], `guidelines/campaign.md` "Deriving from prior drafts and pages"); the maps are recorded verbatim below, with orchestrator notes in bracketed paragraphs. Every symbol, line and excerpt in these maps is an audit finding about the corpus, never a citation for a page; a writer that reuses anything re-finds it on the v7.2 tree. Whether writers receive pointers into either corpus is the user's checkpoint decision (Scope decisions). Corpus paths in the maps are relative to each corpus root; kernel locations are tree-relative.

### Corpus 1: the skill's own `docs/usb4/` (46 pages, v7.0) — audit recorded 2026-09-04

**Method.** Corpus read-only. Prose view built per checking.md [sweeps] (fences dropped, markdown links resolved to their text, bare URLs and code spans masked); raw-file greps used for boldface, headings and fence walks. Symbol checks: catalog `'\<sym\>':'path'` entries parsed out of the COVERAGE sections, resolved against a full definition index of `drivers/thunderbolt/` + `include/linux/thunderbolt.h` built at v7.2 (working tree) and at v7.0 (`git show v7.0:`), with every non-trivial result confirmed through `find_function` / `find_type` at 8d3ae59288f1. Excerpts byte-compared with `git show v7.0:<path> | sed -n`.

**Headline.** The corpus is stylistically clean (0 em dashes, 0 boldface outside `/**` kerneldoc inside fences, 4 hedges in 36,945 lines) and its symbol base is intact: 315/322 spot-checked symbols still exist in the same file at v7.2. What has decayed is line anchoring (149/315 drifted), the NHI pages (the pci.c split), and shape: ~40% of pages run DETAILS as one section per symbol in catalog order, and 6 of 115 figures are in the banned shapes of figures.md [shapes].

#### A. Per-page inventory and verdict

`c` = fenced ```c blocks; `fig` = non-c fences; `elx` = Elixir links. Verdicts: **B** backbone-reusable, **M** mine-sections-only. No page is `ignore` — every one carries at least a register table or figure worth taking.

| page | lines | c | fig | elx | verdict | reason |
|---|---|---|---|---|---|---|
| adapter/adapter.md | 651 | 19 | 2 | 233 | B | Model spine (object → type → numbering → pairing → HopID spaces), only 1/7 headings symbol-led. |
| adapter/common-adapter-config.md | 553 | 13 | 4 | 204 | M | 4/5 headings are symbol names; the four DWord-layout figures and the header table are the value. |
| adapter/lane-adapter.md | 1005 | 25 | 4 | 305 | B | Link-state model plus LANE_ADP_CS_0/1 decode; needs the v7.2 asymmetric-width rework layered on. |
| adapter/protocol/dp-adapter.md | 706 | 18 | 6 | 264 | B | Six register windows fully decoded, the densest register material in the corpus. |
| adapter/protocol/pcie-adapter.md | 545 | 16 | 3 | 140 | B | Shortest adapter page, clean PE/EE framing; missing the whole LTSSM surface at v7.2. |
| adapter/protocol/usb3-adapter.md | 768 | 20 | 5 | 199 | B | CMR/HCA handshake is a real state sequence; four CS windows decoded. |
| adapter/retimer.md | 784 | 23 | 1 | 210 | B | Lifecycle spine (add → scan → NVM → remove_all); only one figure, needs more. |
| adapter/usb4-port.md | 637 | 18 | 3 | 192 | B | Offline-mode and `can_offline` coverage exists nowhere else; PORT_CS_18/19 decoded. |
| control/config-access.md | 797 | 27 | 2 | 219 | M | 13 sections, 9 symbol-led, and four of them are one-call-site walks; request object and space table are keepers. |
| control/control-messages.md | 760 | 25 | 5 | 213 | M | 8/8 headings are `struct X ...` in catalog order; the five packet-layout figures are gold. |
| control/tb-ctl.md | 804 | 30 | 2 | 194 | B | Ownership model (rings + pool + queue) then lifecycle; 30 excerpts, highest density. |
| credit/bandwidth-groups.md | 705 | 24 | 2 | 204 | B | Group/reservation/release-timer model is a genuine state set with a timer edge. |
| credit/credit-allocation.md | 833 | 25 | 2 | 219 | M | 9/11 headings symbol-led (five near-identical per-protocol `*_init_credits` sections); the budget figure is the keeper. |
| domain/acpi-integration.md | 807 | 24 | 1 | 179 | B | _OSC → granted bits → four gates is a clean derivation chain; only one figure. |
| domain/connection-manager.md | 1005 | 34 | 2 | 304 | B | Best vtable-and-privdata treatment in the corpus; 3/10 symbol-led. Worst label-colon load (13). |
| domain/router-hotplug.md | 900 | 22 | 2 | 271 | B | Producer/consumer staging across the workqueue is the model, 2/8 symbol-led. |
| domain/router-unplug.md | 666 | 23 | 1 | 190 | B | Propagation-then-teardown spine; lower half of its one figure is a call tree. |
| domain/tb-domain.md | 643 | 20 | 1 | 229 | B | Object + lifecycle + bus registration; needs `domain_released` and the `root_switch` NULLing added. |
| domain/xdomain.md | 1305 | 33 | 2 | 262 | B | Largest page; discovery state machine is the spine. Heaviest v7.2 drift in the corpus. |
| host-if/dma-and-msix.md | 738 | 24 | 3 | 169 | M | 6/6 headings symbol-led and 3 of its 7 checked symbols were renamed into pci.c; interrupt-register figures survive. |
| host-if/rings.md | 860 | 21 | 3 | 344 | B | Head/tail ring model with descriptor and MMIO partitions; highest Elixir density (344). |
| host-if/tb-nhi.md | 734 | 19 | 3 | 231 | M | Only 3/7 checked symbols survive in place; probe/quirks/IOMMU half is now pci.c. Ring-table figure and REG_CAPS/REG_RESET survive. |
| pm/clx.md | 811 | 25 | 2 | 162 | B | Gate-then-program model with both link ends; lowest Elixir density (162), so link-out work needed. |
| pm/runtime-resume.md | 630 | 17 | 2 | 216 | M | Spine is the call chain and the lead figure is a banned flow graph; the deferred-cleanup split is the one idea worth keeping. |
| pm/runtime-suspend.md | 611 | 24 | 2 | 195 | B | The `rpm` flag and the scan-reference interlock are real policy; lead figure needs redrawing. |
| pm/system-resume.md | 902 | 23 | 3 | 220 | M | 11 sections, 7 symbol-led, plus a "Where the resume vector is reached" call-site section; the two-pass tunnel rediscovery survives. |
| pm/system-suspend.md | 699 | 21 | 3 | 232 | B | Ordering model (DP → tree → hotplug → ctl) with the freeze variant as a contrast. |
| pm/tmu.md | 913 | 20 | 3 | 233 | B | Mode set with an ordering (`OFF < LOWRES < HIFI_UNI < HIFI_BI < MEDRES_ENHANCED_UNI`) and the request/current pair. |
| pm/wake-and-link-controller.md | 777 | 20 | 3 | 287 | M | 10/11 headings symbol-led; the mask-to-two-register-families mapping is what to mine. |
| router/drom.md | 939 | 29 | 2 | 269 | M | 12 sections, 9 symbol-led, four parallel read paths as four sections; the blob figure and CRC spans are gold. |
| router/interoperability.md | 797 | 22 | 3 | 217 | B | Version → generation → feature-branch derivation is the only page organized as a taxonomy. Worst negative-construction load (7). |
| router/nvm.md | 1074 | 31 | 2 | 277 | M | 13 sections, 11 symbol-led; the staging-buffer partition figure and the active/non-active pair survive intact. |
| router/route-string.md | 525 | 21 | 3 | 146 | B | Shortest page, tightest model; three figures for 525 lines. Every one of its 7 symbols drifted by 1-2 lines. |
| router/router-capabilities.md | 748 | 26 | 3 | 230 | B | Three header shapes and one walker is a taxonomy; 4/10 symbol-led. All 7 checked symbols at unchanged lines. |
| router/router-config-space.md | 692 | 14 | 4 | 295 | B | Register-window spine; lowest ```c count (14) against 295 links, so excerpt work needed. Lead figure is a banned table. |
| router/router-operations.md | 580 | 14 | 2 | 216 | B | Mailbox handshake as a state machine; opcode table is the reference. Worst placement-verb load (10). |
| router/security-authorization.md | 789 | 26 | 2 | 247 | B | Policy model (level → authorized → tunnel) 2/10 symbol-led; carries 8 "firmware connection manager" prose mentions. |
| router/tb-switch.md | 720 | 17 | 2 | 209 | B | Object-mirrors-the-wire framing plus alloc/add/remove lifecycle. |
| sideband/sideband-ops.md | 650 | 19 | 2 | 234 | B | The transaction flowchart with its retry back-edge is the best figure in the corpus. |
| sideband/sideband-registers.md | 589 | 19 | 2 | 222 | M | Shares 7/7 spot-check symbols with sideband-ops.md; fold the register-window and FourCC material into that page. |
| tunnel/dma-tunneling.md | 1093 | 35 | 2 | 256 | M | 8/9 headings symbol-led, most ```c blocks of any page (35); the XDomain-path and dma_test consumers are the keepers. |
| tunnel/dp-tunneling.md | 1443 | 30 | 2 | 351 | B | Longest page, lifecycle spine (0/5 symbol-led), most Elixir links (351). Bandwidth-allocation section is unmatched. |
| tunnel/path-model.md | 938 | 23 | 2 | 248 | B | Path/hop model plus the on-wire `tb_regs_hop` partition; both v7.2-critical facts changed here. |
| tunnel/pcie-tunneling.md | 988 | 26 | 3 | 283 | B | Lifecycle spine 0/5 symbol-led; already has a "Reserved bandwidth" section for USB4 v2 gen-4. |
| tunnel/tunnel-model.md | 823 | 28 | 1 | 300 | B | Generic container + per-type vtable + three-state machine; the model page the four protocol pages hang off. |
| tunnel/usb3-tunneling.md | 1008 | 25 | 1 | 241 | B | Lifecycle spine 0/5 symbol-led; only one figure for 1008 lines. |

**Totals:** 1,058 ```c blocks, 115 figures, 10,761 Elixir links, all pointing at `/linux/v7.0/source/` (every link needs rewriting).

#### B. Symbol spot checks against v7.2

7 definition-anchored catalog symbols per page (322 total), each with ≥1 struct/enum and ≥2 functions. Resolved on the v7.2 working tree; `find_function`/`find_type` at 8d3ae59288f1 confirmed every move, rename and zero-drift surprise.

**Totals: 315/322 survive in the same file (97.8%); 149 drifted line; 8 renamed-and-moved; 1 removed; 0 truly deleted symbols beyond the NHI split.**

| page | result |
|---|---|
| adapter/adapter.md | 7/7; drifted: tb_port_is_null 631→632, tb_port_is_nhi 636→637, tb_port_is_pcie_down 641→642, struct ida 245→263 |
| adapter/common-adapter-config.md | 7/7; drifted: tb_port_read 699→700, tb_port_write 713→714 |
| adapter/lane-adapter.md | 7/7; drifted: tb_init_port 704→700, enum tb_link_width 187→191 (gained the asymmetric members) |
| adapter/protocol/dp-adapter.md | 7/7; drifted: tb_init_port 704→700, tb_port_is_dpin 651→652, tb_port_is_dpout 656→657, tb_dp_port_is_enabled 1509→1505, tb_dp_port_hpd_is_active 1426→1422, tb_dp_port_hpd_clear 1447→1443 |
| adapter/protocol/pcie-adapter.md | 7/7; drifted: tb_port_is_pcie_down 641→642, tb_port_is_pcie_up 646→647, tb_init_port 704→700 |
| adapter/protocol/usb3-adapter.md | 7/7; drifted: tb_port_is_usb3_down 661→662, tb_port_is_usb3_up 666→667, usb4_usb3_port_max_link_rate 2199→2204, usb4_usb3_port_max_bandwidth 2184→2189, usb3_bw_to_mbps 2263→2268 |
| adapter/retimer.md | 7/7; drifted: none (retimer.c untouched between the two tags at these anchors) |
| adapter/usb4-port.md | 7/7; drifted: usb4_switch_add_ports 1073→1078, usb4_port_configure 1233→1238 |
| control/config-access.md | 7/7; drifted: none |
| control/control-messages.md | 7/7; drifted: enum tb_cfg_pkg_type 30→31 |
| control/tb-ctl.md | 7/7; drifted: struct ring_frame 601→627 (thunderbolt.h grew above it) |
| credit/bandwidth-groups.md | 7/7; drifted: none |
| credit/credit-allocation.md | 7/7; drifted: tb_switch_credits_init 3255→3256, usb4_switch_credits_init 753→758, tb_init_port 704→700, tb_pci_init_credits 363→391 |
| domain/acpi-integration.md | 7/7; drifted: struct tb_nhi 497→518 (members changed), nhi_select_cm 1316→1163, tb_probe 3366→3374 |
| domain/connection-manager.md | 7/7; drifted: tb_cm_ops 3280→3287, struct tb_cm_ops 506→507, tb_priv 544→545, tb_probe 3366→3374, tb_start 2986→2995 |
| domain/router-hotplug.md | 7/7; drifted: none (tb_handle_hotplug confirmed still tb.c:2421-2536 via find_function) |
| domain/router-unplug.md | 7/7; drifted: tb_handle_event 2908→2916, tb_sw_set_unplugged 3466→3471 |
| domain/tb-domain.md | 7/7; drifted: struct tb 81→82, tb_domain_alloc 374→377, tb_domain_add 436→439, tb_domain_remove 500→503, tb_priv 544→545 |
| domain/xdomain.md | 7/7; drifted: struct tb_xdomain 243→250, tb_xdomain_alloc 1965→2121, tb_xdomain_add 2045→2202, tb_xdomain_remove 2065→2224, struct tb_service 403→419, struct tb_property_dir 113→114, struct tb_property 138→139 — every one moved, the largest per-page shift in the corpus |
| host-if/dma-and-msix.md | 4/7; drifted: nhi_disable_interrupts 163→157, ring_interrupt_active 87→76, ring_interrupt_index 54→43, nhi_mask_interrupt 62→51; renamed: nhi_init_msi → pci.c:111 nhi_pci_init_msi, ring_request_msix → pci.c:184 nhi_pci_ring_request_msix, ring_release_msix → pci.c:220 nhi_pci_ring_release_msix |
| host-if/rings.md | 7/7; drifted: struct tb_ring 539→563 (gained `interval_nsec`, `wait`), tb_ring_alloc_tx 648→603, tb_ring_alloc_rx 671→626, enum ring_desc_flags 582→608, struct ring_frame 601→627 |
| host-if/tb-nhi.md | 3/7; drifted: struct tb_nhi 497→518, nhi_probe 1339→1186, struct tb_nhi_ops 42→56; renamed: nhi_imr_valid → pci.c:148, nhi_check_quirks → pci.c:41, nhi_check_iommu → pci.c:77, nhi_check_iommu_pdev → pci.c:68 (all `nhi_pci_*`) |
| pm/clx.md | 7/7; drifted: none |
| pm/runtime-resume.md | 7/7; drifted: struct tb_cm_ops 506→507, tb_runtime_resume 3256→3263, tb_domain_runtime_resume 615→618, nhi_runtime_resume 1123→1097, tb_switch_resume 3520→3525, tb_switch_set_wake 3487→3492 |
| pm/runtime-suspend.md | 7/7; drifted: struct tb_cm_ops 506→507, nhi_runtime_suspend 1104→1079, nhi_probe 1339→1186, tb_domain_runtime_suspend 604→607, tb_runtime_suspend 3225→3232 |
| pm/system-resume.md | 7/7; drifted: struct tb_cm_ops 506→507, tb_resume_noirq 3113→3141, tb_thaw_noirq 3204→3211, tb_complete 3212→3219, tb_domain_resume_noirq 553→556, tb_domain_thaw_noirq 585→588 |
| pm/system-suspend.md | 7/7; drifted: struct tb_cm_ops 506→507, tb_domain_suspend_noirq 525→528, tb_domain_freeze_noirq 571→574, __nhi_suspend_noirq 974→975 |
| pm/tmu.md | 7/7; drifted: none |
| pm/wake-and-link-controller.md | 7/7; drifted: tb_switch_set_wake 3487→3492, tb_switch_suspend 3622→3641, tb_switch_check_wakes 3499→3504, usb4_switch_set_wake 421→426, usb4_switch_set_sleep 502→507 |
| router/drom.md | 7/7; drifted: tb_drom_read 716→723, tb_drom_parse 629→636 |
| router/interoperability.md | 7/7; drifted: usb4_switch_version 1308→1311, tb_switch_is_usb4 1319→1322, tb_switch_get_generation 2385→2380, tb_switch_configure 2610→2605, nvm_readable 236→212 |
| router/nvm.md | 7/7; drifted: none at the checked anchors (nvm.c stable; note tb_switch_nvm_init is new in switch.c:328 and uncataloged) |
| router/route-string.md | 7/7; drifted: tb_route 582→583, tb_route_length 1238→1240, tb_downstream_route 1251→1253, tb_port_at 587→588, tb_switch_downstream_port 913→915, tb_switch_parent 900→902 — 6/7 drifted, all by 1-2 |
| router/router-capabilities.md | 7/7; drifted: none |
| router/router-config-space.md | 7/7; drifted: tb_sw_read 671→672, tb_sw_write 685→686, tb_switch_wait_for_bit 1721→1723, tb_switch_configure 2622→2605 |
| router/router-operations.md | 7/7; drifted: struct tb_cm_ops 506→507, tb_switch_wait_for_bit 1721→1723 |
| router/security-authorization.md | 7/7; drifted: tb_probe 3366→3374, enum tb_security_level 57→58, tb_switch_set_authorized 1824→1819, tb_domain_approve_switch 654→657, tb_domain_disapprove_switch 635→638 |
| router/tb-switch.md | 7/7; drifted: tb_switch_alloc 2456→2451, tb_switch_configure 2610→2605 |
| sideband/sideband-ops.md | 7/7; drifted: usb4_port_sb_read 1354→1359, usb4_port_sb_write 1407→1412, usb4_port_wait_for_bit 1300→1305, usb4_port_read_data 1322→1327, usb4_port_write_data 1331→1336, usb4_port_sb_op 1468→1473 (uniform +5) |
| sideband/sideband-registers.md | 7/7; same six as above plus usb4_port_sb_opcode_err_to_errno 1454→1459 |
| tunnel/dma-tunneling.md | 7/7; drifted: tb_tunnel_is_dma 182→183, tb_tunnel_alloc_dma 1874→1903, tb_path_alloc 238→233; moved: tb_xdomain_enable_paths / tb_xdomain_disable_paths definitions now at xdomain.c:2439 / :2470 |
| tunnel/dp-tunneling.md | 7/7; drifted: tb_tunnel_alloc_dp 1661→1690, tb_dp_init_video_path 1483→1512, tb_dp_init_aux_path 1436→1465, tb_path_alloc 238→233 |
| tunnel/path-model.md | 7/7; drifted: tb_path_alloc 238→233, tb_next_port_on_path 864→860, struct tb_regs_hop 502→517, tb_port_alloc_hopid 767→763 — but struct tb_path itself changed shape (see C) |
| tunnel/pcie-tunneling.md | 7/7; drifted: tb_tunnel_alloc_pci 504→532, tb_pci_init_path 390→418, tb_pci_init_credits 363→391, tb_tunnel_activate 2376→2405 |
| tunnel/tunnel-model.md | 7/7; drifted: tb_tunnel_is_activated 2474→2503, tb_tunnel_is_pci 172→173 |
| tunnel/usb3-tunneling.md | 7/7; drifted: tb_tunnel_alloc_usb3 2281→2310, tb_usb3_init_path 2149→2178, tb_usb3_init_credits 2131→2160 |

**Removed outright:** `nhi_enable_int_throttling` — the `nhi.h:32` prototype survives but the definition is gone (confirmed with `find_function`). Cited by host-if/dma-and-msix.md and host-if/tb-nhi.md, and dma-and-msix.md has a whole DETAILS section on it.

**Full-corpus resolution over all 864 catalog entries** (not just the 322 sampled): 848 same-file, 2 moved, 14 unresolved-by-name, of which 8 are the pci.c renames, 1 is the removal above, 2 (`event_cb`, `tb_cm_ops`) are indexer misses confirmed present, and 2 are the xdomain path helpers.

#### C. Excerpt verbatimness spot check

16 pages across all nine groups, 2 fenced ```c blocks each, 32 provenance units compared byte for byte (tabs included) against `git show v7.0:<path> | sed -n 'LINE,+Np'`.

**At v7.0: 29/32 exact, 0 wrong-line, 3 not-verbatim.** All three are the same [provenance.form] failure — a leading `/* ... */` comment reproduced above the cited line, so the unit does not begin where it claims:

- `adapter/adapter.md:188` cites `drivers/thunderbolt/tb_regs.h:283` but the unit begins at 282 (`/* Present on every port in TB_CF_PORT at address zero. */`). Off by one.
- `domain/router-hotplug.md:246` cites `drivers/thunderbolt/ctl.c:402` but begins at 399, and inserts a blank line between the kerneldoc block and the signature that is not in the file. Off by three plus an undeclared insertion.
- `router/tb-switch.md:215` cites `drivers/thunderbolt/tb_regs.h:165` but begins at 164, and silently drops the four-line trailing comment on `u32 plug_events_delay:8;` with no `...` elision. Off by one plus an undeclared deletion inside a unit.

**At v7.2 the same 32 units:** 15 still exact at the cited line, 9 match verbatim at a shifted line (re-anchoring alone fixes them), 8 no longer match.

Re-anchorable (content unchanged, line moved): `switch.c:704→700` (×2, lane-adapter and dp-adapter), `switch.c:3255→3256`, `thunderbolt.h:138→139`, `tb.h:1086→1088`, `usb4.c:1354→1359`, `usb4.c:1300→1305`, `tunnel.c:1661→1690`, `tunnel.c:1483→1512`.

Genuinely changed at v7.2 (content, not just position):
- `tunnel/path-model.md:189` — `struct tb_path` no longer holds `struct tb_path_hop *hops;`. `tb_path_alloc` now uses `kzalloc_flex(*path, hops, num_hops)`, so `hops[]` is a flexible array member and `path_length` moved ahead of it. The excerpt and the paragraph beside it are both wrong at v7.2.
- `host-if/rings.md:247` — `struct tb_ring` at `thunderbolt.h:563` gained `interval_nsec` and `wait` (per-ring throttling and `tb_ring_flush`).
- `domain/xdomain.md:169` — `struct tb_xdomain` at `thunderbolt.h:250`, kerneldoc and members both changed.
- `pm/system-resume.md:171` and `:193` — `nhi_pm_ops` and `nhi_resume_noirq` regions in nhi.c rewritten by the pci.c split.
- Plus the three v7.0 failures above, which stay failures.

#### D. Defect classes

Greps stated per class; prose counts exclude fenced blocks, and markdown links are resolved to their text with bare URLs and code spans masked before the sweep.

**(1) Em dashes** — `grep -c '—'` on prose view, and separately over non-c fences. **0 in prose, 0 in figures, 0 in the raw files.** Clean corpus-wide.

**(2) Boldface `**` outside fences** — `grep -n '\*\*'` on the raw file, fence-walked. **0.** 21 files match the raw grep; every hit is a `/**` kerneldoc opener inside a ```c fence, which the style table exempts.

**(3) Hedges** — `grep -inE '(?<![-\w])(usually|typically|generally|often|normally|commonly|mostly|in practice|tends to|simply|essentially|basically|arguably)(?![-\w])'` on prose view. **4 total.** `adapter/retimer.md:59` "normally"; `host-if/dma-and-msix.md:712` "often"; `router/interoperability.md:165` "mostly", `:624` "simply". One more, `router/router-operations.md`, has "nonzero usually maps to" inside a figure fence, which the style table exempts.

**(4) Placement verbs** — `grep -oiE '\b(lives?|lived|living|sits?|sat|sitting|hangs?|hung|hanging|wants?|wanted|wanting)\b'`. **195 total**, dominated by `lives` (69) and `sits` (24). Per page: router-operations 10, lane-adapter 11, pcie-adapter 9, router-unplug 9, usb3-tunneling 8, router-capabilities 7, tb-ctl 7, usb4-port 7, route-string 6, tmu 6, tunnel-model 6, sideband-registers 6, usb3-adapter 6, wake-and-link-controller 6, credit-allocation 5, acpi-integration 5, tb-domain 5, tb-nhi 5, then 4 or fewer on the rest. `domain/xdomain.md` is the only page at 0.

**(5) Negative constructions** — `grep -oiE '(rather than|instead of|,\s+not\s|\s+and not\s)'`. **79 total** (`rather than` 53, `instead of` 15, `, not ` 11). Worst: interoperability 7, xdomain 6, nvm 5, sideband-ops 5, acpi-integration 4, drom 4, router-capabilities 4, router-unplug 3, router-config-space 3. Some are exempt under the style table (a denied alternative the reader could otherwise assume, e.g. the pre-USB4 path), but each needs adjudicating.

**(6) Label-colon prose** — `grep -oE '[^:;.!?]{3,90}:\s+[A-Za-z0-9]'` on prose lines only, excluding headings, table rows, blockquotes, `- `/`* ` catalog bullets, double-quoted text, and the paragraph-final colon that introduces the next fence. **122 total.** Worst: connection-manager 13 ("wires the two together: i..."), drom 8 ("The blob is self-describing: t..."), router-unplug 7, clx 7 ("Two opt-outs apply: t..."), sideband-ops 7 ("mirrors the read, with two differences: i..."), dp-adapter 5, config-access 5, interoperability 5, dma-tunneling 5, dp-tunneling 5, pcie-tunneling 5. Related banned words also present: `contract` at `router/interoperability.md:365`, `canonical` at `:470`.

**(7) Vendor and ICM mentions in prose** — `grep -oE '(Intel|Ridge|Alpine|Titan|Falcon|Ice Lake|Tiger Lake|Alder Lake|Meteor Lake|Raptor Lake|Maple Ridge|Goshen|Barlow|Apple|NVIDIA|icm_|ICM|firmware connection manager)'`. **19 total across 5 pages, zero silicon codenames.** security-authorization 8 (all "firmware connection manager"), connection-manager 6 (4 phrase + 2 `ICM`), acpi-integration 3, credit-allocation 1 (`ICM`), tb-ctl 1 (`ICM`). Low and easy to strip.

**(8) Count-led openers ([purpose.openers])** — first sentence of the lead and of every `##`/`###` section (catalog sections excluded), deletion test applied. 144 sentences carry a number in the first clause; **27 fail the test** (nothing survives deleting the number):

pm/tmu 3 — "The TMU spans two register windows."; "`struct tb_switch_tmu` is four fields."; "`TMU_RTR_CS_0` is the first router TMU register…". lane-adapter 2 — "The two lane adapter control registers sit at…"; "The pairing of two lane adapters…". usb4-port 2 — "The three wake-status bits in the 18:16 range…"; "The first member of `struct usb4_port` is the embedded `struct device`…". interoperability 2 — "The first member of `struct tb_switch` is…"; "The second forward-compatibility mechanism is…". One each: adapter/adapter, common-adapter-config, usb3-adapter ("The two high bits are the only defined fields."), retimer, config-access, control-messages ("`struct tb_cfg_header` is two dwords."), acpi-integration ("The four helpers share one shape."), connection-manager ("The five system-PM slots and two runtime-PM slots…"), tb-domain, xdomain, rings ("Each hop owns a 16-byte descriptor block…"), tb-nhi, clx ("Three flows take CLx down."), system-resume ("Two tunnel passes run back to back."), router-capabilities ("Three header structs describe the on-wire entries."), router-config-space ("The five header DWords are…"), router-operations ("The mailbox uses three router control registers."), tb-switch.

The recurring template "The first member of X is the embedded `struct device`, so …" opens the object section on seven pages (adapter, retimer, usb4-port, tb-domain, xdomain, tb-switch, interoperability) — one rewrite fixes all seven.

**(9) Banned figure shapes ([shapes])** — every one of the 115 figure fences inspected. **6 fail outright (5%), 2 more are half-banned.**

- *Plain table redrawn in box characters* — 2. `router/router-config-space.md:9` "TB_CFG_SWITCH register window at the router" (offset / name / contents records under column rules, no partition asserted) and `router/security-authorization.md:128` "Authorization and security fields in struct tb_switch" (offset / field / meaning records, zero box characters at all). Both belong in Markdown tables.
- *Plain function-flow graph* — 4. All in `pm/`: `runtime-resume.md:9` "Runtime resume call path and the deferred cleanup split", `runtime-suspend.md:9` "Runtime suspend: PCI runtime PM core down to the router tree", `system-suspend.md:9` "System (Sx) suspend ordering, noirq phase" (a `├─` bullet tree of call sites, named explicitly by [shapes.banned]), `system-resume.md:9` "System resume noirq phases" (two lanes but one is a single arrow, so it is the banned shape wearing lanes). The `pm/` group is the worst offender by a wide margin.
- *Half-banned* — 2. `tunnel/dp-tunneling.md:9`: the top three stacked boxes are a call chain, the lower DPRX poll loop is a real state machine with a back-edge; keep the bottom, cut the top. `domain/router-unplug.md:9`: the upper propagation tree is genuine (a subtree flagged from the top down), the lower `remove(A) ├─ remove(B)` block is a call tree.
- *Struct-member box nothing exits* — **0 confirmed.** Three candidates have no arrows (`pm/clx.md:9`, `pm/wake-and-link-controller.md:9`, `router/drom.md:9`) but each asserts a partition or a two-ended pairing and survives the strip test.
- *Plain text in a fence* — 1, `router/security-authorization.md:128` (also counted above).
- **Exempt and healthy:** ~78 of the 115 are register bit-layout grids (`bit 3 3 2 2 …` over a `┌─┬─┐` word). [shapes.banned] explicitly blesses these — the cells partition a word into bit ranges — and they are the corpus's most reusable asset.

**(10) ASCII `+---+` figures** — `grep -E '\+-{2,}\+'` inside every figure fence. **0.** All 115 figures use Unicode box drawing (`─│┌┐└┘├┤┬┴┼`) with `▶◀▲▼` arrowheads. No conversion work needed.

#### E. Section-to-topic pointers

| page | strongest sections / tables / figures → request topic |
|---|---|
| adapter/adapter.md | "Adapter numbering follows the array index" + "Each adapter owns two HopID name spaces" + fig "Logical adapter numbers map to physical lane ports" → Adapters; Path/tunnel model |
| adapter/common-adapter-config.md | "tb_init_port reads the header and computes the buffer count" + the four DWord figures → Adapters; Credits |
| adapter/lane-adapter.md | "The PHY capability carries the link state" + "tb_port_lane_bonding_enable" + LANE_ADP_CS_0/1 figures → Lane adapters; PM/CLx |
| adapter/protocol/dp-adapter.md | Six ADP_DP_CS_* register figures + "The bandwidth-allocation-mode fields" → Protocol adapters; DP tunneling |
| adapter/protocol/pcie-adapter.md | "The PE bit and its register definitions" + "The EE bit and its read-modify-write helper" → Protocol adapters; PCIe tunneling |
| adapter/protocol/usb3-adapter.md | "usb4_usb3_port_cm_request runs the CMR/HCA handshake" + CS_0..CS_3 figures → Protocol adapters; USB3 tunneling; Bandwidth |
| adapter/retimer.md | "tb_retimer_scan enumerates the retimers" + "nvm_authenticate_store" → Sideband/retimers; NVM |
| adapter/usb4-port.md | "Offline mode takes the port out of the live topology" + "can_offline gates the offline controls" + PORT_CS_18/19 → Sideband/retimers; ACPI; PM |
| control/config-access.md | "The request object carries the buffers, the callbacks, and the result" + "The four config spaces" table → Control channel; Router config space |
| control/control-messages.md | The five packet-layout figures + "enum tb_cfg_pkg_type tags every packet" → Control channel/packets; Hotplug |
| control/tb-ctl.md | "The control channel owns the rings, the pool, and the request queue" + "Ring 0 and HopID 0 are the reserved control lane" → Control channel; Host interface rings |
| credit/bandwidth-groups.md | "reserved holds bandwidth one tunnel gives back" + "release_work returns unclaimed reserved bandwidth after ten seconds" → Credits/bandwidth; DP tunneling |
| credit/credit-allocation.md | "tb_available_credits budgets the pool across protocols" + fig "Router preferences → per-path hop credits" + ADP_CS_4 → Credits/bandwidth |
| domain/acpi-integration.md | "The four permission gates" + "tb_acpi_add_links walks the namespace" + the _OSC figure → ACPI; Domain |
| domain/connection-manager.md | "The operations vector is the connection-manager interface" + "The privdata trailer" + kzalloc-layout figure → Domain; Hotplug |
| domain/router-hotplug.md | "The hotplug event object crosses the stage boundary" + "tb_scan_port discovers the newly plugged router" + cfg_event_pkg figure → Hotplug; Control channel |
| domain/router-unplug.md | "tb_sw_set_unplugged marks the subtree from the top down" + "tb_free_invalid_tunnels" → Unplug; Tunnel model |
| domain/tb-domain.md | "The domain object embeds a device and ends with a private trailer" + "The domain registers on tb_bus_type" → Domain |
| domain/xdomain.md | "tb_xdomain_state_work walks the discovery state machine" + "enumerate_services" + the handshake figure → XDomain; DMA tunneling |
| host-if/dma-and-msix.md | "ring_interrupt_active enables a bit and writes the vector nibble" + REG_RING_INTERRUPT_BASE / REG_INT_VEC_ALLOC_BASE figures → Host interface rings; DMA/MSI-X |
| host-if/rings.md | "Enqueue posts frames into descriptors and advances head" + ring_desc and MMIO-quad figures → Host interface rings; DMA |
| host-if/tb-nhi.md | "REG_CAPS supplies the hop count that sizes the ring tables" + sparse ring-table figure + "nhi_reset issues the host router reset" → Host interface rings; Domain |
| pm/clx.md | "tb_switch_clx_enable validates the request and programs both ends" + "The secondary-link power state is resolved before enable" → PM/CLx; TMU |
| pm/runtime-resume.md | "The deferred remove_work frees routers unplugged during sleep" + "Runtime resume differs from system resume" → PM; Unplug |
| pm/runtime-suspend.md | "The rpm flag decides which routers run the autosuspend cycle" + "The scan path takes references" → PM; Router |
| pm/system-resume.md | "Tunnel rediscovery tears down strays and re-activation restores ours" + "tb_restore_children re-applies CLx, TMU, and link state" → PM; Tunnels; TMU |
| pm/system-suspend.md | "tb_switch_suspend recurses children before parents" + ROUTER_CS_5/CS_6 figures → PM; Router config space |
| pm/tmu.md | "tb_switch_tmu_enable writes the request under the time-disruption guard" + the mode-ordering line + TMU_RTR_CS_0 / TMU_ADP_CS_8 → TMU; CLx |
| pm/wake-and-link-controller.md | "tb_switch_set_wake dispatches by generation" + PORT_CS_19 and TB_LC_SX_CTRL figures → PM; Router ops |
| router/drom.md | "Each entry begins with a length-tagged header" + "tb_drom_parse_entry_port derives lane pairing" + the blob figure → DROM; Lane adapters |
| router/interoperability.md | "tb_switch_get_generation maps the version onto a single integer" + "Reserved __unknown fields" + "The capability linked list skips unknown IDs" → Router; Capabilities |
| router/nvm.md | "tb_nvm_validate splits the staged blob" + "enum tb_nvm_write_ops" + the staging-buffer figure → NVM/security |
| router/route-string.md | "tb_route assembles the 64-bit value" + "tb_route_length counts the adapter digits" + both route figures → Route strings; Router |
| router/router-capabilities.md | "The list mixes basic, extended-short, and extended-long headers" + the linked-list figure + the plug-events body → Capabilities; Router config space |
| router/router-config-space.md | "The header maps the first five DWords" + ROUTER_CS_5 / CS_6 / CS_26 figures → Router config space; Router ops |
| router/router-operations.md | "usb4_native_switch_op drives the mailbox handshake" + the mailbox flowchart + the opcode table → Router ops |
| router/security-authorization.md | "enum tb_security_level defines the domain policy" + "How PCIe tunneling is gated on authorization at level USER" → Security; PCIe tunneling |
| router/tb-switch.md | "tb_switch_alloc reads the header and sizes the ports array" + "tb_switch_add reads DROM, initializes adapters, and registers" → Router; DROM |
| sideband/sideband-ops.md | "usb4_port_sb_op runs the opcode handshake and maps the status" + the transaction flowchart + "usb4_port_router_offline" → Sideband/retimers |
| sideband/sideband-registers.md | "The target selector picks router, partner, or an indexed retimer" + PORT_CS_1 figure → Sideband/retimers |
| tunnel/dma-tunneling.md | "tb_dma_init_rx_path and tb_dma_init_tx_path set flow control and credits" + "tb_approve_xdomain_paths" → DMA tunneling; XDomain; Credits |
| tunnel/dp-tunneling.md | "Bandwidth allocation" + "HPD handling and relay to the graphics driver" + the DPRX poll loop figure → DP tunneling; Bandwidth |
| tunnel/path-model.md | "struct tb_regs_hop is the on-wire form of one hop" + "tb_path_discover rebuilds a path from hardware" + the hop-register figure → Path/tunnel model |
| tunnel/pcie-tunneling.md | "Tunnel setup" + "Reserved bandwidth" + ADP_PCIE_CS_0/CS_1 figures → PCIe tunneling; Bandwidth |
| tunnel/tunnel-model.md | "The tunnel separates a generic container from a per-type vtable" + "The state machine has three states" → Tunnel model |
| tunnel/usb3-tunneling.md | "Credit and bandwidth management" + "Suspend and resume" → USB3 tunneling; Credits |

#### F. Coverage gaps

**Absent entirely** (zero occurrences corpus-wide, verified by grep):

1. **`stream.c` / USB4STREAM** — 1,698 new lines at v7.2, a whole `/dev/tbstreamX` character-device protocol built on `CONFIG_USB4_STREAM`. Not one mention. Largest single gap.
2. **`configfs.c` / `CONFIG_USB4_CONFIGFS`** — new 61-line file, `tb_configfs_init`/`tb_configfs_exit` called from `domain.c`. Absent.
3. **`tb_ring_flush`, `tb_ring_size`, `tb_ring_frame_size`, per-ring throttling** — `struct tb_ring` gained `interval_nsec` and `wait` at `thunderbolt.h:563`; `tb_ring_flush` is new at `nhi.c:728`. host-if/rings.md covers none of it, and `nhi_enable_int_throttling` (the old global mechanism it replaced) still has a DETAILS section.
4. **`tb_property_merge_dir` / `tb_property_copy` and the hardened parser** — `property.c` grew 192 lines at v7.2; `tb_property_merge_dir` is at `property.c:628`. domain/xdomain.md documents the old parser only.
5. **`domain_released` completion** — new member of `struct tb_nhi`; `domain.c` now calls `complete(&nhi->domain_released)` on release. domain/tb-domain.md and host-if/tb-nhi.md both miss it, as they miss `tb->dev.parent = nhi->dev` replacing `&nhi->pdev->dev`.
6. **`tb_switch_nvm_init`** — new at `switch.c:328`, and the two DMA-port helpers it displaced (`nvm_authenticate_start_dma_port` / `nvm_authenticate_complete_dma_port`) moved out of switch.c. router/nvm.md documents the old shape.
7. **`tb_domain_unregister_unplugged_xdomains`** — new `domain.c` helper with its own `unregister_context`; domain/router-unplug.md and pm/system-resume.md both describe the old inline sweep.
8. **KUnit tests** — `test.c` grew 249 lines at v7.2. Zero mentions of `kunit`/`KUnit` anywhere in the corpus.
9. **`pci.c` as a file** — the 622-line new PCI driver is never named; host-if/tb-nhi.md still presents `nhi_probe`/`nhi_remove` as the PCI entry points and `nhi_ops.c` (deleted at v7.2) as a live file.

**Covered only thinly (a paragraph or less):**

10. **PCIe LTSSM detect check** — one page mentions "ltssm" once. `tb_pci_pre_activate` (tunnel.c:312) now calls `tb_pci_port_ltssm_state_detect` on both ends and refuses setup unless the state is `USB4_PCIE_LTSSM_DETECT`; `usb4_pci_port_ltssm_state` is at usb4.c:3162 with `ADP_PCIE_CS_0_LTSSM_MASK`. Neither adapter/protocol/pcie-adapter.md nor tunnel/pcie-tunneling.md has this.
11. **Path activation order and USB4 reserved fields** — tunnel/path-model.md states the v7.0 rule ("starting with the last hop and iterating backwards"). At v7.2 `tb_path_activate` runs first hop to last, reads the hop config space before writing it, and programs `initial_credits`/`ingress_fc`/`ingress_shared_buffer` only for pre-USB4 and lane adapters because those bits are vendor-defined on USB4 protocol adapters. Also `__tb_path_deactivate_hops(path, 0)` on error, not `(path, i)`.
12. **XDomain v2 lane bonding** — domain/xdomain.md has the state machine but not the `XDOMAIN_STATE_BONDING_UUID_HIGH` width negotiation that reads `LANE_ADP_CS_0` supported width/speed and `LANE_ADP_CS_1` target width, nor `xd->target_link_width`, nor the removal path no longer holding `tb->lock`, nor services taking an XDomain reference.
13. **USB4 v2 asymmetric links** — "asymmetric" appears on 8 pages but `TB_LINK_WIDTH_ASYM_*` on only one; `enum tb_link_width` drifted 187→191 because the asymmetric members landed there. adapter/lane-adapter.md and credit/bandwidth-groups.md both need this as a first-class state.
14. **Counters config space** — `TB_CFG_COUNTERS` is named in the four-space table on 7 pages and explained on none ("`TB_CFG_COUNTERS` is the counter block"). No register layout, no consumer.
15. **debugfs surfaces** — `debugfs` appears on 11 pages, always as a `struct dentry *debugfs_dir` member or a `#ifdef`. Only one DETAILS section anywhere ("The debugfs dumper walks the whole router list"). `debugfs.c` changed at v7.2.
16. **Lane margining** — 5 pages mention it, all as `#ifdef CONFIG_USB4_DEBUGFS_MARGINING` around a `struct tb_margining *` member or the retimer-index bump. `usb4_port_margining*` never appears. No page owns the topic.
17. **Router Ready bit and the grown timeouts** — router enumeration now verifies Router Ready, and `switch.c` sets Notification Timeout to 255 ms for all routers. "Router Ready" appears on one page; the timeout change appears nowhere.
18. **`nhi->ops` now mandatory** — host-if/tb-nhi.md documents `struct tb_nhi_ops` (drifted 42→56) as an optional hook set by `nhi_ops.c`; at v7.2 the file is deleted and the ops pointer is required, filled by pci.c.

#### G. Figure inventory worth redrawing

Twenty figures that carry real structure and survive the strip test of [shapes.strip-test] after redrawing in house style. (Separately: the ~78 register bit-layout grids are a reusable class in their own right — each partitions a 32-bit word into named bit ranges, exactly what [shapes.banned] blesses.)

| page | figure | structure it shows |
|---|---|---|
| router/route-string.md:9 | Route string: one adapter digit per hop | Positional partition — depth on an axis, one 8-bit digit per level, host at 0 |
| router/route-string.md:125 | Route value as 8-bit-per-hop adapter digits | The 63-bit word partitioned into per-depth digit slots |
| host-if/rings.md:9 | A frame's path across struct tb_ring (TX) | Producer → queue → descriptor array with head and tail chasing, hardware reaping, back to done |
| host-if/rings.md:193 | Per-ring MMIO descriptor block and options word | Index-space partition: hop number scaling two register strides (×16 and ×32) |
| host-if/tb-nhi.md:9 | struct tb_nhi sparse ring tables indexed by hop | An index space with holes, each occupied slot dropping a pointer to a per-hop MMIO block |
| router/drom.md:9 | DROM blob: fixed header then a variable entry chain | Byte-offset partition with two CRC spans bracketing it and a movable header boundary (16 vs 22) |
| router/router-capabilities.md:9 | Router capability linked list over TB_CFG_SWITCH | A chain where each link's own header shape decides how the next offset is read (u8 vs u16) |
| router/router-operations.md:9 | USB4 router operation mailbox | State machine: stage metadata/data, ring the OV doorbell, poll with a back-edge, three typed exits |
| sideband/sideband-ops.md:9 | The generic sideband transaction | State machine with a retry back-edge, a timeout exit, and a status-to-errno mapping exit |
| adapter/adapter.md:9 | Two tb_port adapters joined by a link, with lane pairing | Two-router topology with `remote` crossing the link and `dual_link_port` closing the pair locally |
| adapter/adapter.md:41 | Logical adapter numbers map to physical lane ports | Index-space partition: `ports[]` slots grouped into physical connectors by a divide |
| credit/credit-allocation.md:9 | Router preferences → per-path hop credits | Five preference sources feeding a per-protocol transform, two of them through a `min()` against a pool |
| domain/connection-manager.md:130 | Memory layout from one kzalloc | One allocation partitioned in two, with the pointer conversion running each way across the seam |
| tunnel/tunnel-model.md:9 | struct tb_tunnel owns N unidirectional tb_path | Containment fan-out: one field dropping trunks to a variable-length array |
| tunnel/path-model.md:9 | struct tb_path and its hop array threading two routers | A path threaded through adapters across routers, each hop an ingress/egress pair |
| domain/xdomain.md:9 | XDomain discovery handshake (host A → host B) | Time running down across two separate actors, each cell naming the state that actor reaches |
| domain/router-hotplug.md:9 | Plug path: producer → tb->wq → hotplug worker | Two actors with a queue between them; redraw keeping the queue and the stage boundary, dropping the two call chains |
| router/nvm.md:9 | struct tb_nvm staging buffer and the NVMem pair | A buffer partitioned at `hdr_size`, with the split moving after validate, feeding two device views |
| pm/tmu.md:9 | struct tb_switch_tmu and the two register windows | One object addressing two distinct register spaces through two cached offsets, plus an ordered mode set |
| domain/acpi-integration.md:9 | _OSC permission negotiation feeds the tunnel gates | Grant flow: two negotiated globals fanning into four per-protocol gates and one CM selection |
| tunnel/dp-tunneling.md:9 (lower half only) | The DPRX poll loop | State machine with a 50 ms requeue back-edge and a timeout branch that tears the tunnel down |

#### H. Enhancement backlog, three per group

**adapter/** — (1) USB4 v2 asymmetric link widths as a first-class state on lane-adapter.md: the `TB_LINK_WIDTH_ASYM_*` members that pushed `enum tb_link_width` to tb.h:191, and who requests each direction. (2) The PCIe adapter LTSSM surface: `ADP_PCIE_CS_0_LTSSM_MASK`, `usb4_pci_port_ltssm_state` (usb4.c:3162), and the `USB4_PCIE_LTSSM_DETECT` precondition. (3) Locking and lifetime for the `usb4_port` device and its retimer children, which no adapter page states.

**control/** — (1) The `TB_CFG_COUNTERS` space, named on 7 pages and explained on none: layout, who reads it, what it costs. (2) The ctl.c changes at v7.2 (16 lines) folded into tb-ctl.md's rx/tx paths. (3) Merge control-messages.md's eight `struct X` sections into a packet-taxonomy spine so the page stops being catalog order with figures attached.

**credit/** — (1) Asymmetric-link bandwidth accounting in bandwidth-groups.md, absent today. (2) The DP bandwidth-allocation-mode reservation indexing change, which credit-allocation.md predates. (3) Collapse the five near-identical `*_init_credits` sections into one table plus one worked example, per [purpose.spine].

**domain/** — (1) `domain_released`, `tb->dev.parent = nhi->dev`, and `root_switch` NULLed on stop, none of which tb-domain.md has. (2) configfs registration (`tb_configfs_init`/`tb_configfs_exit`) as a domain-lifecycle facet. (3) XDomain v2: the `XDOMAIN_STATE_BONDING_UUID_HIGH` width negotiation, `tb_property_merge_dir`, removal without `tb->lock`, and services holding an XDomain reference — xdomain.c grew 325 lines and property.c 192.

**host-if/** — (1) Rewrite tb-nhi.md around the nhi.c/pci.c split: ring code stays, `nhi_pci_*` owns probe/quirks/IOMMU/MSI-X/shutdown, `nhi_ops.c` is gone and `nhi->ops` is now mandatory. (2) `tb_ring_flush`, `tb_ring_size`, `tb_ring_frame_size` and per-ring throttling (`interval_nsec`, `wait`) on rings.md, replacing the removed `nhi_enable_int_throttling` section. (3) A stream.c page or section: 1,698 lines of new USB4STREAM protocol riding these rings, with its `/dev/tbstreamX` interface.

**pm/** — (1) Redraw all four lead figures; every one is a banned function-flow graph, and the group has no other structural figure. (2) Merge runtime-resume.md and system-resume.md's overlapping tree-restore material into one restore model with a resume-kind axis, cutting the "Where the resume vector is reached" call-site section. (3) Lane margining and the debugfs surfaces as owned topics rather than `#ifdef` mentions.

**router/** — (1) Router Ready verification plus the grown Configuration Ready and Notification (255 ms) timeouts in tb-switch.md's add path. (2) `tb_switch_nvm_init` (switch.c:328) and the DMA-port start/complete helpers leaving switch.c, on nvm.md. (3) Replace router-config-space.md's banned lead table and security-authorization.md's banned field table with Markdown tables, and give each page a real structural figure.

**sideband/** — (1) Merge sideband-registers.md into sideband-ops.md: the two share 7/7 spot-check symbols and 19 ```c blocks each. (2) Lane margining over sideband, the one large sideband consumer the pages never reach. (3) Retimer NVM and offline-mode sequencing stated as an ordered protocol with its failure exits, not as per-function sections.

**tunnel/** — (1) path-model.md's two v7.2 corrections: `struct tb_path` with its flexible `hops[]` (`kzalloc_flex`), and activation running source to destination with a read-before-write and USB4 reserved fields skipped. (2) The `tb_pci_pre_activate` LTSSM gate as a setup precondition on pcie-tunneling.md. (3) Multi-display DP allocation and bandwidth-group reservation indexing on dp-tunneling.md, plus lifecycle and locking for the DPRX work item, which the page shows but never bounds.

### Corpus 2: `kernel-glossary-devel/docs/usb4/` at TREE_ROOT (50 files, v6.19) — audit recorded 2026-09-04

[Orchestrator note 2026-09-04: by the user's amendment under Scope decisions, decision 4, the figures in section D below (register-layout figures) are the only Corpus 2 material a writer brief may point at, each redrawn and re-verified against the v7.2 defines; the section E figures and every code-flow figure are drawn fresh from the tree.]

Corpus paths relative to `docs/usb4/`. Kernel locations tree-relative.
Corpus-wide: 45 ` ```c ` blocks, 246 non-c fences, 379 Elixir links (285 line-anchored, 81 distinct anchors), all pinned at v6.19.

#### A. Per-file table

| file | lines | ```c | fig | elixir | verdict | reason |
|---|---|---|---|---|---|---|
| switch/cfg-router.md | 371 | 3 | 11 | 20 | backbone-reusable | Full Router CS DW0-26 map + `tb_regs_switch_header` + `tb_sw_read`; spine of the router-config page |
| switch/cfg-router-cs.md | 251 | 2 | 9 | 10 | mine-sections-only | Duplicates cfg-router's figures verbatim; no DETAILS section; keep only ROUTER_CS_5/6 defines + `usb4_switch_setup` |
| switch/cfg-router-ops.md | 152 | 2 | 2 | 11 | backbone-reusable | `usb4_native_switch_op` excerpt is verbatim-exact at v7.2; OV doorbell protocol stated |
| switch/cap.md | 86 | 2 | 0 | 7 | backbone-reusable | Both capability walkers (`tb_switch_find_cap`, `tb_port_find_cap`) with the required/optional split |
| switch/topology-id.md | 190 | 3 | 9 | 13 | backbone-reusable | Route-string level encoding + `tb_route()`; one stale excerpt attribution |
| port/adapters.md | 180 | 2 | 9 | 10 | backbone-reusable | `struct tb_port` + `enum tb_port_type` + adapter-numbering rules |
| port/cfg-adapter.md | 151 | 2 | 3 | 9 | backbone-reusable | Adapter CS DW0-DW8 map + `tb_regs_port_header` + ADP_CS_4/5 defines |
| port/cfg-adapter-lane.md | 438 | 2 | 18 | 10 | backbone-reusable | Largest register file: TMU/Lane/USB4-Port capability structures, all three defines blocks |
| port/cfg-adapter-counter.md | 134 | 1 | 4 | 6 | backbone-reusable | Only corpus source for Counter CS layout and CCS/MaxCounterSets |
| port/cfg-adapter-dp.md | 141 | 1 | 1 | 3 | mine-sections-only | Defines block is accurate; body is one long vendor tbdump with no prose |
| port/cfg-adapter-pcie.md | 44 | 1 | 1 | 3 | mine-sections-only | Defines block plus one tbdump; no DETAILS |
| port/cfg-adapter-usb3.md | 70 | 1 | 1 | 3 | mine-sections-only | Defines block plus one tbdump; no DETAILS |
| tunnel/cfg-adapter-path.md | 283 | 3 | 10 | 15 | backbone-reusable | `tb_regs_hop`/`tb_path_hop`/`tb_path` + per-adapter path-offset rules + hop-field bit map |
| sb_regs/sideband-regs.md | 299 | 3 | 6 | 12 | backbone-reusable | SB address map, opcode enum, `usb4_port_sb_read`, PORT_CS_1 indirection |
| host-if/host-if.md | 172 | 2 | 6 | 16 | backbone-reusable | `struct tb_ring`/`struct tb_ctl` + ring-to-HopID model; NHI probe restructured at v7.2 |
| host-if/ring.md | 246 | 2 | 11 | 24 | backbone-reusable | MMIO base registers, `ring_desc`, ring_full/empty; 5 C excerpts in unmarked fences |
| host-if/ctl.md | 186 | 2 | 7 | 16 | backbone-reusable | Control-channel lifecycle + `tb_cfg_header`/`cfg_read_pkg` + packet traces |
| host-if/raw.md | 40 | 1 | 0 | 7 | mine-sections-only | `enum ring_flags` + RAW semantics; one paragraph of DETAILS |
| host-if/raw-rx.md | 16 | 0 | 0 | 3 | ignore | Stub: two catalog bullets, empty SPECIFICATIONS, no DETAILS |
| host-if/raw-tx.md | 16 | 0 | 0 | 3 | ignore | Stub: two catalog bullets, empty SPECIFICATIONS, no DETAILS |
| host-if/frame-rx.md | 33 | 1 | 0 | 3 | mine-sections-only | One REG_RX_OPTIONS_BASE excerpt; folds into a raw-vs-frame section |
| host-if/frame-tx.md | 33 | 1 | 0 | 4 | mine-sections-only | One `ring_desc` excerpt; folds into a raw-vs-frame section |
| host-if/rx.md | 94 | 0 | 4 | 4 | mine-sections-only | Spec RX descriptor + depleted-descriptor figures; C in unmarked fences |
| host-if/tx.md | 70 | 0 | 3 | 4 | mine-sections-only | Spec TX descriptor figure; C in unmarked fences |
| tlp/tlp.md | 93 | 1 | 1 | 6 | mine-sections-only | TLP 1-DW header figure is spec-only (kernel defines no TLP header struct) |
| tlp/tlp-ctrl.md | 245 | 2 | 9 | 12 | backbone-reusable | Control packet format + PDF taxonomy + request/response traces |
| clx/cl1-cl2-suspend.md | 302 | 2 | 14 | 10 | backbone-reusable | `tb_switch_clx_enable` + CLx support/enable bits; CLx entry handshake |
| clx/cl1-cl2-exit.md | 45 | 0 | 1 | 4 | mine-sections-only | One short exit sequence; no kernel excerpt |
| clx/cl1-cl2-exit-retimer.md | 234 | 1 | 10 | 6 | ignore | Nine retimer CL_WAKE swimlanes; no kernel implementation of any of it |
| lt/link-train-1-1.md | 231 | 0 | 8 | 34 | ignore | USB-C CC/Rp/Rd/Ra electrical detection; all 34 links are bogus (see C) |
| lt/link-train-1-2.md | 155 | 0 | 9 | 0 | ignore | USB PD Source_Capabilities/PDO/RDO; zero kernel links |
| lt/link-train-1-3.md | 225 | 0 | 11 | 0 | ignore | PD Discover_Identity SOP' VDOs; zero kernel links |
| lt/link-train-1-4.md | 45 | 0 | 1 | 2 | ignore | UFP VDO1/VDO2; both links bogus |
| lt/link-train-1-5.md | 44 | 0 | 2 | 0 | ignore | Enter_USB EUDO; COVERAGE section says the driver is not involved |
| lt/link-train-2.md | 92 | 0 | 3 | 4 | mine-sections-only | PORT_CS_18 Router Detected bit; the only phase-2 kernel touchpoint |
| lt/link-train-3.md | 49 | 0 | 1 | 5 | mine-sections-only | Phase-3 decision list; LINK_CONF figure duplicated from 3-1 |
| lt/link-train-3-1.md | 62 | 0 | 2 | 5 | mine-sections-only | Carries the canonical USB4_SB_LINK_CONF 24-bit field map |
| lt/link-train-3-2.md | 80 | 0 | 3 | 6 | mine-sections-only | Bonding decision; LINK_CONF figure is a duplicate |
| lt/link-train-3-3.md | 100 | 0 | 4 | 6 | mine-sections-only | Lane-speed decision + LANE_ADP_CS_1 Current Link Speed |
| lt/link-train-3-4.md | 75 | 0 | 3 | 6 | mine-sections-only | RS-FEC decision; LINK_CONF figure is a duplicate |
| lt/link-train-4-1.md | 142 | 0 | 6 | 3 | mine-sections-only | Retimer enumeration; ties to USB4_SB_OPCODE_ENUMERATE_RETIMERS |
| lt/link-train-4-2.md | 87 | 0 | 2 | 3 | mine-sections-only | SLOS1/LT_Resume; hardware-only, one usable sentence |
| lt/link-train-5-lock1.md | 125 | 0 | 2 | 2 | ignore | TxFFE negotiation in PHY hardware; identical COVERAGE body to lock2/ts1/ts2 |
| lt/link-train-5-lock2.md | 46 | 0 | 1 | 2 | ignore | Near-duplicate stub of lock1 |
| lt/link-train-5-ts1.md | 46 | 0 | 1 | 2 | ignore | Near-duplicate stub of lock1 |
| lt/link-train-5-ts2.md | 46 | 0 | 1 | 2 | ignore | Near-duplicate stub of lock1 |
| host.md | 256 | 2 | 8 | 22 | mine-sections-only | `struct tb_switch`/`struct tb_nhi` excerpts are keepable; 6 dmesg blocks are one machine |
| hub.md | 253 | 0 | 13 | 7 | mine-sections-only | UP/DOWN adapter subtype rule is worth keeping; 10 dmesg blocks, zero C |
| peripheral.md | 184 | 0 | 11 | 5 | ignore | 9 dmesg blocks of one OWC enclosure; zero C; nothing not in hub.md |
| tools/cfg-tbtools.md | 89 | 0 | 4 | 9 | ignore | External out-of-tree tool; no SPECIFICATIONS section |

#### B. What each file IS, and the campaign topic it feeds

- **switch/cfg-router.md, cfg-router-cs.md** — spec register layout (Router CS 0-26) plus observed traces → **Router config space**. cfg-router-cs is a partial clone; merge into one page.
- **switch/cfg-router-ops.md** — spec register layout (Data/Metadata/Opcode) + the OV doorbell sequence → **Router ops**.
- **switch/cap.md** — capability-list walk model → **Capabilities**.
- **switch/topology-id.md** — route-string bit layout + device examples → **Route strings**.
- **port/adapters.md, cfg-adapter.md** — adapter taxonomy and Adapter CS layout → **Adapters / router config space**.
- **port/cfg-adapter-lane.md** — three capability register layouts (TMU, Lane, USB4 Port) → **Lane adapters** and **TMU**.
- **port/cfg-adapter-dp.md, -pcie.md, -usb3.md** — protocol-adapter register layouts (tool dumps) → **Protocol adapters**.
- **port/cfg-adapter-counter.md** — Counter CS layout + CCS discovery → **Counters**.
- **tunnel/cfg-adapter-path.md** — Path Entry Structure layout + per-adapter offsets → **Path config space**.
- **sb_regs/sideband-regs.md** — sideband register map + port-operation model → **Sideband registers**.
- **host-if/host-if.md, ring.md, rx.md, tx.md, raw*.md, frame*.md** — ring/descriptor layout and ring operation modes → **Host interface rings / raw vs frame mode**.
- **host-if/ctl.md, tlp/tlp.md, tlp/tlp-ctrl.md** — TLP and control-packet header formats → **Control packets**.
- **clx/cl1-cl2-suspend.md, cl1-cl2-exit.md** — CLx entry/exit sequences → **CLx / PM**.
- **clx/cl1-cl2-exit-retimer.md** — retimer CL_WAKE ordered-set choreography → **fold out**: no kernel implementation; the driver only reads/writes retimer sideband registers, it never observes ordered sets.
- **lt/link-train-1-1 … 1-5** — USB-C connector and USB PD message formats → **fold out**: this is USB Type-C/PD, handled by `drivers/usb/typec`, not thunderbolt; the corpus itself states the driver is uninvolved.
- **lt/link-train-2, 3, 3-1 … 3-4** — link-training phase descriptions → **fold in as bits, not phases**: the only kernel surface is what `USB4_SB_LINK_CONF`, `PORT_CS_18` and `LANE_ADP_CS_0/1` expose; feed **Lane adapters** and **Sideband registers**.
- **lt/link-train-4-1, 4-2** — retimer enumeration and transmit start → feed **Sideband registers** (the ENUM opcode); the rest is hardware sequencing.
- **lt/link-train-5-lock1/lock2/ts1/ts2** — PHY training substates → **fold out**: four near-identical stubs, no kernel implementation beyond the TxFFE register offset.
- **host.md, hub.md, peripheral.md** — device examples (dumps of one AMD host, one Dell/Intel JHL8540 dock, two OWC JHL6540 enclosures) → **fold out the dumps**; keep only `struct tb_switch`, `struct tb_nhi` and the UP/DOWN subtype rule for **Router** and **Adapters**.
- **tools/cfg-tbtools.md** — external tool usage → **fold out**: `tbtools` is an out-of-tree userspace tool; `drivers/thunderbolt/debugfs.c` is the in-tree equivalent.

#### C. Symbol spot checks against v7.2

Totals: 285 line-anchored links — **153 land on the same line, 96 drifted, 36 bogus**; 94 file-only links all resolve. **Every symbol name in every ` ```c ` block and every link title still exists at v7.2**; nothing was renamed or removed. Line-only drift dominates, as expected from the v6.19 pin.

Bogus links (wrong symbol entirely, not drift):
- `lt/link-train-1-1.md` — 34 links: `CC1`/`CC2` (USB-C configuration channel pins) point at `include/linux/mfd/stm32-timers.h#L49/50`, which at v7.2 is `TIM_DIER_CC1IE`/`TIM_DIER_CC2IE`.
- `lt/link-train-1-4.md` — 2 links: the English words `USB2`/`USB4` point at `include/dt-bindings/usb/pd.h#L366/367`, which is the body of `VDO_PCABLE`/`VDO_ACABLE1`.

Anchors that survive exactly (spot-checked): `tb_regs_switch_header` `drivers/thunderbolt/tb_regs.h:166`; `enum tb_port_type` `tb_regs.h:268`; `tb_regs_port_header` `tb_regs.h:283`; `ADP_CS_4` `tb_regs.h:314`; `LANE_ADP_CS_0/1` `tb_regs.h:339`/`348`; `PORT_CS_1/2/18/19` `tb_regs.h:374`/`383`/`384`/`393`; `ADP_DP_CS_0` `tb_regs.h:403`; `ADP_PCIE_CS_0` `tb_regs.h:475`; `ROUTER_CS_7/9/25/26` `tb_regs.h:220`-`223`; `struct tb_switch` `tb.h:171`; `struct tb_port` `tb.h:280`; `struct tb_path_hop` `tb.h:381`; `struct tb_path` `tb.h:430`; `tb_cfg_header` `tb_msgs.h:43`; `cfg_read_pkg` `tb_msgs.h:60`; `tb_ctl` `ctl.c:39`; `tb_ctl_alloc/start/stop` `ctl.c:653`/`730`/`751`; `tb_cfg_request` `ctl.h:77`; `enum ring_flags` `nhi_regs.h:14`; `RING_FLAG_RAW` `nhi_regs.h:18`; `ring_desc` `nhi_regs.h:34`; `REG_TX/RX_RING_BASE`, `REG_TX/RX_OPTIONS_BASE` `nhi_regs.h:52`/`62`/`70`/`80`; `tb_port_find_cap` `cap.c:124`; `tb_switch_find_cap` `cap.c:198`; `tb_switch_clx_enable` `clx.c:321`; `usb4_native_switch_op` `usb4.c:54`; `usb4_switch_setup` `usb4.c:243`; all five `sb_regs.h` anchors; `tb_tunnel` `tunnel.h:73`.

Drifted (old→new, all same file):
`tb_regs.h` ROUTER_CS_4 199→198, ROUTER_CS_5 203→202, ROUTER_CS_6 213→212, ADP_USB3_CS_0 481→496, `tb_regs_hop` 502→517. `tb.h` `tb_route` 582→583, `tb_sw_read` 671→672, `tb_sw_write` 685→686, `enum usb4_sb_target` 1374→1377. `include/linux/thunderbolt.h` `enum tb_cfg_pkg_type` 30→31, `struct tb_nhi` 497→518, `struct tb_ring` 539→563. `nhi_regs.h` `REG_CAPS` 113→114. `nhi.c` `ring_desc_base` 177→171, `ring_options_base` 185→179, `ring_full` 225→219, `ring_empty` 230→224, `nhi_probe` 1365→1186. `switch.c` `tb_switch_alloc` 2455→2451, `tb_switch_add` 3297→3298, `tb_switch_match` 3740→3759, `tb_switch_find_by_route` 3829→3848. `path.c` `tb_path_activate` 505→492. `usb4.c` `usb4_switch_read_uid` 342→347, `usb4_port_sb_read` 1354→1359, `usb4_port_sb_write` 1407→1412. `ctl.c#L750` labelled `tb_cfg_read` is mislabelled: at v7.2 `tb_cfg_read` is `drivers/thunderbolt/ctl.c:1111`, and line 751 is `tb_ctl_stop`.

Excerpt content that drifted (the C blocks themselves, not the links):
- `host-if/ring.md` quotes `nhi_probe(struct pci_dev *pdev, const struct pci_device_id *id)`. **Signature changed**: at v7.2 it is `int nhi_probe(struct tb_nhi *nhi)` at `drivers/thunderbolt/nhi.c:1186` — the NHI is no longer a PCI-probed object. Every "NHI is probed as a PCI device" claim in `host-if/host-if.md` and `host.md` must be rewritten.
- `switch/cfg-router-cs.md` `usb4_switch_setup` excerpt ends `return tb_sw_write(...)`. At v7.2 (`usb4.c:243-303`) it also clears `xhci` when USB3 tunnelling wins and ends `tb_switch_wait_for_bit(sw, ROUTER_CS_6, ROUTER_CS_6_RR, ...)`; the CV bit moved to `usb4_switch_configuration_valid()` `usb4.c:316`. The page's "programs ROUTER_CS_5 ... mark the configuration as valid (CV)" is now wrong.
- `switch/topology-id.md` attributes `sw->config.depth = tb_route_length(route);` to `tb_switch_alloc()`. At v7.2 that line is `switch.c:2579` inside `tb_switch_alloc_safe_mode()`; `tb_switch_alloc()` uses `sw->config.depth = depth;` at `switch.c:2489`.
- `host-if/host-if.md` `struct tb_ring` excerpt is missing `interval_nsec` and `wait` (`include/linux/thunderbolt.h:563-587`).
- `sb_regs/sideband-regs.md` `enum usb4_sb_opcode` shows 13 of the 17 members at `sb_regs.h:21`; missing `QUERY_CABLE_RETIMER`, `GET_NVM_SECTOR_SIZE`, `NVM_SET_OFFSET`, `NVM_BLOCK_WRITE`.
- `switch/cfg-router.md` ROUTER_CS defines block omits `ROUTER_CS_1`, `ROUTER_CS_5_WOP/WOU/WOD`, `ROUTER_CS_6_WOPS/WOUS/RR`, `ROUTER_CS_4_CMUV_V1`, and the `ROUTER_CS_26_*` masks that do exist at `tb_regs.h:195`-`228`.

#### D. Register-layout figure inventory ([registers] candidates)

Every figure below is ASCII `+---+`/`|`, so all need Unicode redraw. "Kernel" names the v7.2 symbol family.

| figure (file) | draws | kernel family at v7.2 | verification |
|---|---|---|---|
| Router CS DW0-DW26 (cfg-router.md ×2, cfg-router-cs.md ×2, cfg-router-ops.md ×2) | Router CS 0-26 | `tb_regs_switch_header` `tb_regs.h:166`; `ROUTER_CS_*` `tb_regs.h:195-228` | DW0/DW1/DW4 exact. **DW3 mismatch**: figure has TIDV[31]/Rsvd[30:24]/TopologyID High[23:0]; kernel has `route_hi:31` (30:0) + `enabled:1` (31). DW26 OV/ONS/STATUS/OPCODE all match the macros. |
| Router CS "device information" / "enumeration" / "control" cutaways (cfg-router.md ×3, cfg-router-cs.md ×1, cfg-router-ops.md ×1) | subsets of the same DW0-26 | same | Redundant re-draws of the master figure with cells blanked; keep one. |
| TopologyID two-DW route string (topology-id.md, tlp-ctrl.md) | Route String DW1/DW2, CM bit + 7 level IDs | `route_lo`/`route_hi` in `tb_regs_switch_header`; `tb_route()` `tb.h:583` | Kernel defines no per-level 6-bit macros; the level split is spec-only. CM bit = the high bit of `tb_cfg_header.unknown` `tb_msgs.h:43`. |
| Adapter CS DW0-DW8 (cfg-adapter.md, full and protocol-adapter cutaway) | Adapter CS 0-8 | `tb_regs_port_header` `tb_regs.h:283`; `ADP_CS_4/5` `tb_regs.h:314-322` | DW4 (NFC[9:0], Total[29:20], LCK[31]) and DW5 (Max In HopID[10:0], Max Out[21:11], LCA[28:22], DHP[31]) match. **DW1 mismatch**: figure marks [31:20] reserved, kernel has `revision:8` at 31:24. **DW2 mismatch**: figure marks [31:24] reserved, kernel has `thunderbolt_version:8`. **Kernel defines nothing** for SBC[31], FCEE[30], HEE[29] (DW3), Plug[30] (DW4), or DW6/7/8 (HEC/Invalid-HopID/ECC errors — the struct stops at DW7 with `__unknown5/6`). DW3/DW5 both label FCEE/HEE — internally inconsistent. |
| TMU Adapter Capability, 8 DW (cfg-adapter-lane.md appendix) | TMU_ADP_CS 0-7 | `TMU_ADP_CS_3/6/8/9` `tb_regs.h:325-336` | UDM[29] and DTS[1] match. **Kernel defines nothing** for IDTI[31], IDTR[30], the TSNOS/packet/lost/bad counters. Figure omits TMU_ADP_CS_8/9 (REPL_TIMEOUT, EUDM, REPL_THRESHOLD, REPL_N, DIRSWITCH_N, ADP_TS_INTERVAL) that the kernel does define. |
| Lane Adapter Capability, 3 DW (cfg-adapter-lane.md appendix) | LANE_ADP_CS 0-2 | `LANE_ADP_CS_0/1` `tb_regs.h:339-372` | Supported Speeds[19:16], CL0s/CL1/CL2 Support[26/27/28], Target Speed[3:0], Target Width[5:4], CL0s/CL1/CL2 Enable[10/11/12], LD[14], LB[15], Current Speed[19:16], Current Width[25:20], PMS[30] all match. **SLW mismatch**: figure draws [21:20], kernel `SUPPORTED_WIDTH_MASK` is GENMASK(25,20). **Kernel defines nothing** for G4AS[23:22], Adapter State[29:26], or any of LANE_ADP_CS_2. Geometry is broken: CL2[28] is drawn between G4AS[23:22] and SLW[21:20]. |
| USB4 Port PORT_CS_18 / PORT_CS_19 (cfg-adapter-lane.md ×4, link-train-2.md, 3-2, 3-4) | PORT_CS_18, PORT_CS_19 | `PORT_CS_18_*` `tb_regs.h:384-392`, `PORT_CS_19_*` `tb_regs.h:393-401` | BE[8], TCM[9], CPS[10], CSA[22], TIP[24], DPR[0], PC[3], PID[4] and the wake bits [16:18] all match. **Kernel defines nothing** for Cable USB4 Version[7:0], RE2[11], RE3[12], RD[13], CG3[20], CG4[21], CSC[23], RS2[1], RS3[2], ILR[30], ELR[31]. |
| PORT_CS_1 sideband command (sideband-regs.md, cfg-adapter-lane.md) | PORT_CS_1 | `PORT_CS_1_*` `tb_regs.h:374-382` | LENGTH_SHIFT 8, TARGET_MASK GENMASK(18,16), RETIMER_INDEX_SHIFT 20, WNR_WRITE[24], NR[25], RC[26], PND[31] — all match; the figure's Address[7:0] has no kernel mask. |
| DP adapter CS 0-8 (cfg-adapter-dp.md, one tbdump) | ADP_DP_CS 0-8 + DP_LOCAL/REMOTE/COMMON_CAP | `ADP_DP_CS_*` `tb_regs.h:403-446` | Video HopID[26:16], AE[30], VE[31], AUX TX/RX HopID, NRD_MLC[2:0], HPD[6], NRD_MLR[9:7], CA[10], GR[12:11], CMMS[20], Estimated BW[31:24], HPDC[9], DPME[30], DR[31] all match. Kernel has **no `ADP_DP_CS_1` offset define** (only its masks) — correct as the corpus shows it. The DP_LOCAL/REMOTE/COMMON_CAP field lists are DPCD-level, no kernel macros. |
| PCIe adapter CS 0 (cfg-adapter-pcie.md) | ADP_PCIE_CS_0 | `ADP_PCIE_CS_0/1` `tb_regs.h:475-479` | PE[31] and EE[0] match. **Kernel defines nothing** for Link[16], TX EI[17], RX EI[18], RST[19], LTSSM[28:25]. |
| USB3 adapter CS 0-4 (cfg-adapter-usb3.md) | ADP_USB3_CS 0-4 | `ADP_USB3_CS_*` `tb_regs.h:496-514` | V[30], PE[31], CUBW[11:0], CDBW[23:12], HCA[31], AUBW/ADBW, CMR[31], Scale[5:0], MSLR[18:12] all match. Corpus uses tbdump's `ADP_USB3_GX_CS_n` naming; the kernel name is `ADP_USB3_CS_n`. Actual Link Rate[6:0] and ULV[7] and PLS[11:8] have no kernel macros. |
| Path Entry Structure PATH_CS_0/PATH_CS_1 (cfg-adapter-path.md, cfg-adapter-counter.md) | Path CS, 2 DW | `tb_regs_hop` `tb_regs.h:517`; no `PATH_CS_*` macros exist | Output Adapter[16:11]=`out_port:6`, Credits[23:17]=`initial_credits:7`, Valid[31]=`enable`, Weight[3:0], Priority[10:8], Counter ID[22:12]=`counter:11`, CE[23], IFC[24], EFC[25], ISE[26], ESE[27], PP[28] all match. **Mismatch**: the tbdump decode says Output HopID **[00:06]** while `next_hop` is 11 bits (10:0) — and the same file's own "Mapping Hop Fields" block says [10:0]. Internally inconsistent; adjudicate against the spec before redrawing. |
| Counter Config Set, 3 DW (cfg-adapter-counter.md) | Counters CS[n] | no macros; `tb_port_clear_counter()` `switch.c:604` writes 3 DWORDs at `3 * counter` in `TB_CFG_COUNTERS` | 3-DW stride confirmed by the kernel. **Third DW label is wrong**: figure says "Dropped Packets **High**" where "Received Packets High" precedes it; there is no Low. |
| Sideband register map, 0x00-0x12 (sideband-regs.md ×2) | SB register space | `sb_regs.h:13-48`; sizes in `debugfs.c:75-87` `port_sb_regs[]` | Offsets and sizes match `port_sb_regs[]` except: figure says Debug Data 0x06 is **4 bytes**, kernel says **54**; figure marks 0x02-0x04 "(Reserved)" but the kernel defines `USB4_SB_FW_VERSION = 0x02`. Typo `0c0F` for `0x0F` in both copies. |
| SB 0x0C Link Configuration, 24 bits (sideband-regs.md, link-train-3.md, 3-1, 3-2, 3-3, 3-4 — 6 copies) | USB4_SB_LINK_CONF | `USB4_SB_LINK_CONF 0x0c` `sb_regs.h:43`; 3-byte size in `debugfs.c:83` | Register size (3 bytes = 24 bits) confirmed. **Kernel defines no bit macros at all** — every one of the 16 named fields is spec-only and unverifiable from the tree. Deduplicate to one figure. |
| SB 0x0D TxFFE, 32 bits (sideband-regs.md) | USB4_SB_GEN23_TXFFE | `USB4_SB_GEN23_TXFFE 0x0d` `sb_regs.h:44`; 4-byte size in `debugfs.c:84` | Size confirmed. **No bit macros in the kernel**; all 16 per-lane fields are spec-only. |
| TX descriptor, 4 DW (host-if/tx.md) | Transmit Descriptor | `struct ring_desc` `nhi_regs.h:34`; `enum ring_desc_flags` `include/linux/thunderbolt.h:608` | DW0/DW1 = `phys`; DW2 = `length:12`(11:0), `eof:4`(15:12), `sof:4`(19:16), `flags:12`(31:20); DW3 = `time`. Figure's IE = `RING_DESC_INTERRUPT` (bit 23), DD = `RING_DESC_COMPLETED` (21), RS = `RING_DESC_POSTED` (22). Figure's "Offset" field (31:24) has no kernel name. |
| RX descriptor + depleted RX descriptor, 4 DW each (host-if/rx.md) | Receive Descriptor | same | Same mapping; depleted form's BOD = `RING_DESC_BUFFER_OVERRUN` (22), CRC = `RING_DESC_CRC_ERROR` (20). Kernel uses one struct for both directions, so the two figures collapse into one annotated pair. |
| TLP 1-DW header (tlp/tlp.md) and Control Packet header (tlp/tlp-ctrl.md) | TLP DW0: PDF[31:28], SuppID[27], HopID[22:16], Length[15:8], HEC[7:0] | `enum tb_cfg_pkg_type` `include/linux/thunderbolt.h:31`; `tb_cfg_header` `tb_msgs.h:43` | **The kernel defines no struct or macro for DW0** — the NHI prepends it, the driver only supplies PDF via `enum tb_cfg_pkg_type`. Entirely spec-derived; the two figures disagree on DW1/DW2 route ordering (tlp-ctrl puts Low first, cfg-router traces put High first). Reconcile before redrawing. |
| PD Message Header / VDM Header / VDO / EUDO (lt/1-3, 1-4, 1-5) | USB PD packet fields | none in `drivers/thunderbolt` | Out of scope; belongs to `drivers/usb/typec`. |

#### E. Other figures worth redrawing ([shapes] prognosis)

| figure (file) | shows | strip-test prognosis |
|---|---|---|
| Descriptor ring → data buffers (host-if/ring.md) | ring array with per-descriptor pointers dropping to separate buffers | **survives** — containment plus pointers leaving the boxes; the one figure in the corpus that is unambiguously worth keeping as-is (redrawn in Unicode). |
| Domain topology tree (14 files, byte-identical) | host router → dock → two enclosures, with port pairs on the edges | **survives** as a parent/child tree with labelled links, but it is one vendor machine repeated 14 times. Redraw once as a generic depth-0/1/2 topology with adapter-number roles, no device names. |
| CL1/CL2 entry: DFP/UFP port block pair (clx/cl1-cl2-suspend.md, 5 near-identical variants) | two routers' lane pairs, sideband pins, CC/VBUS, with CLx_REQ / CLy_ACK / CL_OFF crossing between them | **survives** — two containers with directed signals across a boundary; the five variants differ only in which arrow is labelled, so collapse to one figure with a legend, or to a state table. |
| CL1/CL2 exit: Router A ↔ Router B LFPS/Idle/SLOS1 (clx/cl1-cl2-exit.md) | time-ordered exchange between two actors | **survives as a swimlane** (time down, two actors) but is only 8 rows; a three-sentence paragraph carries it. Fold into prose. |
| Retimer CL_WAKE swimlanes (clx/cl1-cl2-exit-retimer.md, 9 figures) | six actors across the link, ordered sets propagating outward then inward | **survives the strip test** (time down, six actors, position on the lane axis carries the propagation), but the content has no kernel counterpart — cut with the file. |
| Sideband channel SBTX/SBRX bit exchange (lt/link-train-3-1.md) | one SB register block with two directed lanes | **fails**: two boxes, two arrows, all meaning is in the labels. Fold into prose. |
| PD Source/Sink message ladder (lt/link-train-1-2.md), Discover_Identity ladder (1-3), UFP ladder (1-4) | request/response order between two actors | **survives as swimlanes** but is USB PD, out of scope. |
| Type-C receptacle pinout, A1-A12/B1-B12 (lt/link-train-1-1.md) | physical pin positions in two rows | **survives** — position on an axis is the fact — and is the only genuinely spatial figure in the `lt/` tree; still out of scope. |
| Rp/Rd/Ra divider and Vsense tables (lt/link-train-1-1.md, 4 figures) | resistor networks and measured voltages | **fails as text in boxes** for the tables; the divider schematics survive but are electrical, not kernel. |

#### F. Defect classes, counts per file

Corpus-wide: **YAML front matter 50/50**; **`verification-needed` tag 50/50**; **SUMMARY present 4/50** (host-if/host-if.md, host.md, switch/cfg-router.md, tools/cfg-tbtools.md); **SPECIFICATIONS missing 2** (clx/cl1-cl2-suspend.md, tools/cfg-tbtools.md) **and empty in 14 more**; **DOCUMENTATION present 1/50** (host.md); **OTHER SOURCES present 15/50** (7 files instead use a non-house `## OTHER INFORMATION`); **REGISTERS present 18/50**; **DETAILS missing 5** (host-if/raw-rx.md, raw-tx.md, port/cfg-adapter-pcie.md, port/cfg-adapter-usb3.md, switch/cfg-router-cs.md). **Boldface: 2 files** (host.md ×1 pair, lt/link-train-2.md ×1 pair). **Em dashes: 0 files.** The nav in `docs/SUMMARY.md:287-348` lists 40 of the 50 files, all at flat `usb4/*.md` paths that do not match the subdirectory layout, names `usb4/cfg-cap.md` for what is `switch/cap.md`, and omits all 10 `host-if/` files.

Per-file counts — columns: **ASCII-fig** (non-c fence using `+--`/`|`/`/`/`\` as box drawing) · **tbdump** (tool dump fence) · **dmesg** (observed-trace fence) · **C-in-plain-fence** · **hedge** · **label-colon prose** (front-matter `topics:` line excluded) · **vendor/ICM mentions**:

| file | ASCII | tbdump | dmesg | C-plain | hedge | lbl-colon | vendor |
|---|---|---|---|---|---|---|---|
| clx/cl1-cl2-exit.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| clx/cl1-cl2-exit-retimer.md | 9 | 0 | 0 | 0 | 1 | 0 | 0 |
| clx/cl1-cl2-suspend.md | 6 | 2 | 5 | 0 | 1 | 3 | 19 |
| host-if/ctl.md | 5 | 0 | 6 | 0 | 0 | 2 | 18 |
| host-if/frame-rx.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| host-if/frame-tx.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| host-if/host-if.md | 1 | 0 | 5 | 0 | 0 | 1 | 17 (incl. ICM) |
| host-if/raw.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| host-if/raw-rx.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| host-if/raw-tx.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| host-if/ring.md | 3 | 0 | 4 | 5 | 0 | 1 | 15 |
| host-if/rx.md | 4 | 0 | 0 | 2 | 0 | 0 | 0 |
| host-if/tx.md | 3 | 0 | 0 | 2 | 0 | 0 | 0 |
| host.md | 5 | 0 | 6 | 0 | 2 | 14 | 17 |
| hub.md | 5 | 0 | 10 | 0 | 1 | 10 | 23 |
| lt/link-train-1-1.md | 4 | 0 | 0 | 0 | 2 | 8 | 0 |
| lt/link-train-1-2.md | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-1-3.md | 11 | 0 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-1-4.md | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| lt/link-train-1-5.md | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-2.md | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-3-1.md | 2 | 0 | 0 | 0 | 1 | 0 | 0 |
| lt/link-train-3-2.md | 1 | 1 | 0 | 0 | 0 | 2 | 0 |
| lt/link-train-3-3.md | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-3-4.md | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-3.md | 1 | 0 | 0 | 0 | 0 | 4 | 0 |
| lt/link-train-4-1.md | 5 | 0 | 0 | 0 | 1 | 0 | 0 |
| lt/link-train-4-2.md | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-5-lock1.md | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-5-lock2.md | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-5-ts1.md | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| lt/link-train-5-ts2.md | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| peripheral.md | 4 | 0 | 9 | 0 | 0 | 7 | 24 |
| port/adapters.md | 7 | 0 | 8 | 0 | 0 | 4 | 16 |
| port/cfg-adapter-counter.md | 1 | 3 | 0 | 0 | 0 | 0 | 0 |
| port/cfg-adapter-dp.md | 1 | 1 | 0 | 0 | 0 | 2 | 0 |
| port/cfg-adapter-lane.md | 7 | 9 | 6 | 0 | 0 | 5 | 19 |
| port/cfg-adapter.md | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| port/cfg-adapter-pcie.md | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| port/cfg-adapter-usb3.md | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| sb_regs/sideband-regs.md | 4 | 2 | 0 | 0 | 0 | 0 | 0 |
| switch/cap.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| switch/cfg-router-cs.md | 5 | 2 | 4 | 0 | 0 | 1 | 17 |
| switch/cfg-router.md | 8 | 2 | 4 | 0 | 0 | 1 | 20 |
| switch/cfg-router-ops.md | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| switch/topology-id.md | 4 | 0 | 7 | 0 | 0 | 4 | 18 |
| tlp/tlp-ctrl.md | 7 | 0 | 6 | 0 | 0 | 3 | 22 |
| tlp/tlp.md | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| tools/cfg-tbtools.md | 1 | 3 | 0 | 0 | 0 | 0 | 1 |
| tunnel/cfg-adapter-path.md | 3 | 5 | 3 | 0 | 2 | 9 | 22 |

Observed machine-specific data that cannot be reproduced from the tree: **14 files** carry the identical Dell/AMD/Intel-JHL8540/OWC-JHL6540 topology preamble and figure, and **93 dmesg or packet-trace fences** across 15 files quote real route strings (0x2, 0x502, 0x702), PCI addresses (0000:c7:00.5/.6, 0000:00:01.1/.2), vendor/device IDs (0x438:0x20e, 0x8087:0xb26, 0x8086:0x15c0, 0x5a:0xde34) and firmware versions. All of it is v6.19.0-rc6 output with `thunderbolt.dyndbg=+pt`, not reproducible from v7.2 source. `host-if/host-if.md` additionally names "ICM (Intel Connection Manager)" in prose.

Factual defects found while auditing: `port/cfg-adapter-lane.md` says "The driver reads PORT_CS_18[3:0] to obtain this value" for the adapter state — at v7.2 `tb_port_state()` (`drivers/thunderbolt/switch.c:467`) reads `struct tb_cap_phy` at `port->cap_phy` and returns `phy.state`, an `enum tb_port_state` (`tb_regs.h:49`), not PORT_CS_18 and not LANE_ADP_CS_1. `host-if/host-if.md` names a register `ROUTER_ADP_CS_1` twice; no such symbol exists (the upstream-adapter field is `upstream_port_number` in `tb_regs_switch_header`, and the register is `ROUTER_CS_1` `tb_regs.h:195`). `port/cfg-adapter-usb3.md` uses tbdump's `ADP_USB3_GX_CS_n` names, not the kernel's `ADP_USB3_CS_n`.

#### G. Specification references (deduplicated, grouped by topic)

| topic | citation as the corpus states it | carried by |
|---|---|---|
| Devices | USB4 Specification, section 2.1.1.5: Host | host.md |
| Devices | USB4 Specification, section 2.1.1.4.2: USB4 Hub | hub.md |
| Devices | USB4 Specification, section 2.1.1.4.1: USB4 Peripheral Device | peripheral.md |
| Router addressing | 6.2 Router Addressing | switch/topology-id.md |
| Router addressing | Figure 6-1. Example of TopologyID Assignment | switch/topology-id.md |
| Router addressing | CONNECTION MANAGER NOTE, 8.2.1.1 Basic Configuration Registers | switch/topology-id.md |
| Router config space | USB4 Specification, section 8.2.1: Router Configuration Space | switch/cfg-router.md, switch/cfg-router-ops.md |
| Router config space | 8.2.1 Router Configuration Space | switch/cap.md |
| Router config space | USB4 Specification, section 8.2.1.1: Basic Configuration Registers | switch/cfg-router-cs.md |
| Adapter config space | USB4 Specification, section 8.2.2: Adapter Configuration Space | port/adapters.md, port/cfg-adapter.md |
| Adapter config space | 8.2.2 Adapter Configuration Space | switch/cap.md |
| Adapter config space | USB4 Specification, section 8.2.2.2: TMU Adapter Configuration Capability | port/cfg-adapter-lane.md |
| Adapter config space | USB4 Specification, section 8.2.2.3: Lane Adapter Configuration Capability | port/cfg-adapter-lane.md |
| Adapter config space | USB4 Specification, section 8.2.2.4: USB4 Port Capability | port/cfg-adapter-lane.md, sb_regs/sideband-regs.md |
| Adapter config space | USB4 Specification, section 8.2.2.6: DP Adapter Configuration Capabilities | port/cfg-adapter-dp.md |
| Adapter config space | USB4 Specification, section 8.2.2.7: PCIe Adapter Configuration Capability | port/cfg-adapter-pcie.md |
| Adapter config space | USB4 Specification, section 8.2.2.8: USB3 Adapter Configuration Capability | port/cfg-adapter-usb3.md |
| Path config space | USB4 Specification, section 8.2.3: Path Configuration Space | tunnel/cfg-adapter-path.md |
| Counters | USB4 Specification, section 8.2.4: Counter Configuration Space | port/cfg-adapter-counter.md |
| Sideband / port ops | USB4 Specification, section 4.1.1.3.3: SB Register Definitions | sb_regs/sideband-regs.md |
| Sideband / port ops | USB4 Specification, section 8.3.2: Port Operations | sb_regs/sideband-regs.md |
| Sideband / port ops | USB4 Specification, Table 8-64: List of Port Operations | sb_regs/sideband-regs.md |
| TLP | USB4 Specification, section 5.1: Transport Layer Packets | tlp/tlp.md |
| TLP | USB4 Specification, section 5.1.3: Transport Layer Packet Types | tlp/tlp.md |
| Control packets | USB4 Specification, section 6.4: Control Packet Protocol | tlp/tlp-ctrl.md |
| Host interface | USB4 Specification, section 12.2: Ring Operation Modes | host-if/raw.md |
| Host interface | USB4 Specification, section 12.3.1: Transmit Descriptor Structure | host-if/ctl.md |
| Host interface | 12.3.1 Transmit Descriptor Structure | host-if/host-if.md, host-if/tx.md |
| Host interface | USB4 Specification, section 12.4.1: Receive Descriptor Structure | host-if/ctl.md |
| Host interface | 12.4.1 Receive Descriptor Structure | host-if/host-if.md |
| Host interface | 12.6.2 Registers Summary | host-if/host-if.md |
| Host interface | 12.6.3 Registers Description | host-if/ring.md |
| Host interface | 12.6.3.2 Transmit Descriptor Rings | host-if/tx.md |
| Host interface | 12.6.3.3 Receive Descriptor Rings | host-if/rx.md |
| Host interface | Table 12-10. Summary of Memory BAR Registers | host-if/host-if.md |
| Host interface | Figure 2-37. Descriptor Ring and Data Buffers | host-if/ring.md |
| CLx / PM | USB4 Specification, section 4.2.1.6: Low Power States (CL0s, CL1, and CL2) | clx/cl1-cl2-exit-retimer.md |
| CLx / PM | USB4 Specification, section 4.2.1.6.5: Exit from State | clx/cl1-cl2-exit-retimer.md |
| CLx / PM | USB4 Specification, section 4.2.1.6.5.2: Gen 2 and Gen 3 Exit flow from CL1 or CL2 state (No Re-timers on the Link) | clx/cl1-cl2-exit.md |
| CLx / PM | USB4 Specification, section C.1.2.2: Example: Exit from CL2 (or CL1) State | clx/cl1-cl2-exit-retimer.md |
| Link training | 4.1.2.2 Router Detection | lt/link-train-2.md |
| Link training | 4.1.2.3 Phase 3 - Determination of USB4 Port Characteristics | lt/link-train-3.md, 3-1, 3-2, 3-3, 3-4 |
| Link training | 4.1.2.4 Phase 4 - Lane Parameters Synchronization and Transmit Start | lt/link-train-4-1.md, 4-2 |
| USB PD (out of scope) | *C.1.1 Discover Identity Command request*, Universal Serial Bus Power Delivery Specification, Revision 3.2, Version 1.1, 2024-10 | lt/link-train-1-3.md |
| USB PD (out of scope) | *8.3.2.14.1.1 Initiator to Responder Discover Identity (ACK)*, Universal Serial Bus Power Delivery Specification, Revision 3.2, Version 1.1, 2024-10 | lt/link-train-1-3.md |
| USB PD (out of scope) | *6.4.8 Enter_USB Message*, Universal Serial Bus Power Delivery Specification, Revision 3.2, Version 1.1, 2024-10 | lt/link-train-1-5.md |

There is also `Documentation/admin-guide/thunderbolt.rst` (present at v7.2, 18,989 bytes), the corpus's only DOCUMENTATION entry, cited from host.md.

#### H. Coverage the kernel-focused rewrite must carry over

1. **Counter config space** — the corpus is the only source for the 3-DWORD-per-set layout and the CCS/Max-Counter-Sets discovery path. Kernel side: `tb_port_clear_counter()` `drivers/thunderbolt/switch.c:604` writes three zero DWORDs at `3 * counter` in `TB_CFG_COUNTERS` (`drivers/thunderbolt/tb_msgs.h:19`); `counter:11` / `counter_enable:1` in `struct tb_regs_hop` `drivers/thunderbolt/tb_regs.h:534`; `in_counter_index` in `struct tb_path_hop` `drivers/thunderbolt/tb.h:385`, written at `drivers/thunderbolt/path.c:555`. The kernel never reads the counters; `drivers/thunderbolt/debugfs.c:2308` is the only reader.
2. **Sideband register map** — offsets, widths and the "no config space for PHYs" indirection. Kernel side: `drivers/thunderbolt/sb_regs.h:13-48`; the authoritative width table is `port_sb_regs[]` / `retimer_sb_regs[]` `drivers/thunderbolt/debugfs.c:75-102`; access path `usb4_port_sb_read()` `drivers/thunderbolt/usb4.c:1359` and `usb4_port_sb_write()` `usb4.c:1412` through `PORT_CS_1` `tb_regs.h:374`; target selection `enum usb4_sb_target` `drivers/thunderbolt/tb.h:1377`.
3. **Router-operation opcode table** — the corpus supplies the OV doorbell protocol; the kernel supplies the opcodes the corpus omits. Kernel side: `enum usb4_switch_op` `drivers/thunderbolt/tb_regs.h:231-242` (QUERY/ALLOC/DEALLOC_DP_RESOURCE 0x10-0x12, NVM_WRITE/AUTH/READ/SET_OFFSET 0x20-0x23, DROM_READ 0x24, NVM_SECTOR_SIZE 0x25, BUFFER_ALLOC 0x33), driven by `usb4_native_switch_op()` `drivers/thunderbolt/usb4.c:54`, with `ROUTER_CS_9/25/26` and the `ROUTER_CS_26_*` masks at `tb_regs.h:221-228`.
4. **Control packet formats** — the DW0 PDF/HopID/Length/HEC header the kernel never models, plus the request/response distinction. Kernel side: `enum tb_cfg_pkg_type` `include/linux/thunderbolt.h:31`; `struct tb_cfg_header` `drivers/thunderbolt/tb_msgs.h:43` (the reply flag is the high bit of `unknown`); `struct tb_cfg_address` `tb_msgs.h:50`; `cfg_read_pkg`/`cfg_write_pkg`/`cfg_error_pkg`/`cfg_ack_pkg`/`cfg_event_pkg`/`cfg_reset_pkg` `tb_msgs.h:60-101`; `enum tb_cfg_space` `tb_msgs.h:15`; `enum tb_cfg_error` `tb_msgs.h:22`; issued via `tb_cfg_read()` `drivers/thunderbolt/ctl.c:1111`; frame cap `TB_FRAME_SIZE` `include/linux/thunderbolt.h:638`.
5. **Ring descriptor layout and ring operation modes** — the four-DWORD descriptor and the raw-vs-frame distinction. Kernel side: `struct ring_desc` `drivers/thunderbolt/nhi_regs.h:34`; `enum ring_desc_flags` `include/linux/thunderbolt.h:608`; `enum ring_flags` `nhi_regs.h:14` with `RING_FLAG_RAW` at `nhi_regs.h:18`; MMIO bases `REG_TX_RING_BASE` `nhi_regs.h:52`, `REG_RX_RING_BASE` `nhi_regs.h:62`, `REG_TX_OPTIONS_BASE` `nhi_regs.h:70`, `REG_RX_OPTIONS_BASE` `nhi_regs.h:80`, `REG_RING_INTERRUPT_BASE` `nhi_regs.h:99`, `REG_CAPS` `nhi_regs.h:114`; strides in `ring_desc_base()` `drivers/thunderbolt/nhi.c:171` (16 bytes) and `ring_options_base()` `nhi.c:179` (32 bytes). Note the v7.2 restructure: `nhi_probe()` `nhi.c:1186` now takes `struct tb_nhi *`, not a `struct pci_dev *`.
6. **CLx entry/exit sequencing** — the CLx_REQ / CLy_ACK / CL_NAK / CL_OFF handshake and the both-ends-must-support rule. Kernel side: `tb_switch_clx_enable()` `drivers/thunderbolt/clx.c:321`, `tb_switch_clx_disable()` `clx.c:398`, `tb_switch_clx_init()` `clx.c:211`, `tb_port_clx_supported()` `clx.c:68`, `tb_port_clx_set()` `clx.c:103`, `tb_switch_pm_secondary_resolve()` `clx.c:240`, `tb_switch_mask_clx_objections()` `clx.c:257`; register bits `LANE_ADP_CS_0_CL0S/CL1/CL2_SUPPORT` `drivers/thunderbolt/tb_regs.h:344-346` and `LANE_ADP_CS_1_CL0S/CL1/CL2_ENABLE` `tb_regs.h:361-363`, `LANE_ADP_CS_1_PMS` `tb_regs.h:372`. The CL2-needs-v2-routers gate at `clx.c:342` has no counterpart in the corpus.
7. **Lane adapter register bits** — supported/target/current speed and width, bonding, lane disable. Kernel side: `LANE_ADP_CS_0` `drivers/thunderbolt/tb_regs.h:339-346` and `LANE_ADP_CS_1` `tb_regs.h:348-372`, including the asymmetric-width members (`TARGET_WIDTH_ASYM_MASK` GENMASK(7,6), `..._ASYM_TX/RX/DUAL`) and `CURRENT_SPEED_GEN4` that the corpus's defines block drops. Link state itself comes from `tb_port_state()` `drivers/thunderbolt/switch.c:467` reading `struct tb_cap_phy` `tb_regs.h:129`, returning `enum tb_port_state` `tb_regs.h:49` — this is where the corpus's "Adapter State" prose must be re-anchored.
8. **TMU, present in the corpus only as a register figure** — kernel side is much larger: `enum tb_switch_tmu_mode` `drivers/thunderbolt/tb.h:88`, `struct tb_switch_tmu` `tb.h:103`, `TMU_RTR_CS_0/1/2/3/15/18/22/24/25` `drivers/thunderbolt/tb_regs.h:245-266`, `TMU_ADP_CS_3/6/8/9` `tb_regs.h:325-336`. The corpus's TMU figure covers only the adapter capability, so a TMU page must be written mostly fresh.
9. **Capability discovery**, which the corpus covers well and a structure-first page would skip: required-then-optional ordering, `first_cap_offset` in DW1. Kernel side: `tb_switch_find_cap()` `drivers/thunderbolt/cap.c:198`, `tb_port_find_cap()` `cap.c:124` (with its `tb_port_enable_tmu()` `cap.c:18` / `tb_port_dummy_read()` `cap.c:47` bracket), `tb_switch_next_cap()` `drivers/thunderbolt/tb.h:1173`, `enum tb_port_cap` / `TB_PORT_CAP_USB4` `tb_regs.h:46`.
10. **Path-space addressing conventions** the register defines do not carry: paths 1-7 reserved so protocol adapters start at offset 0x10, Path 0 has a distinct entry shape, HopID `n` maps to path entry offset `2n`, DP adapters carry two path entries. Kernel side: `tb_path_activate()` `drivers/thunderbolt/path.c:492` (programs hops last-first), `struct tb_regs_hop` `drivers/thunderbolt/tb_regs.h:517`, `struct tb_path` `drivers/thunderbolt/tb.h:430`, `struct tb_tunnel` `drivers/thunderbolt/tunnel.h:73`. The kernel defines no `PATH_CS_0`/`PATH_CS_1` names at all, so the corpus's naming must be marked as tbtools/spec vocabulary if it is kept.

[Orchestrator note, 2026-09-04: item H.10 of the Corpus 2 audit says `tb_path_activate()` "programs hops last-first". That is the v7.0 behaviour. At v7.2 commit b69af182b556 reversed the loop and hops are programmed source to destination (path.c:529); the Area F digest and the tree are authoritative. Item H.10's "paths 1-7 reserved so protocol adapters start at offset 0x10" and "Path 0 has a distinct entry shape" are corpus claims not verified by the audit against the tree; a writer treats them as unverified until re-derived.]
