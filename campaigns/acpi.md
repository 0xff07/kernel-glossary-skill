# ACPI kernel-internals knowledge-base campaign: plan

## Context

Campaign short name: `acpi`. Spec: `campaigns/acpi.md` (this file — committed, execution-free, machine-portable). Workspace: `progress/acpi/` (machine-local run log and dossiers; never committed). Name-collision check run 2026-07-19 against `campaigns/` and `progress/` (entries: bluetooth, dp, drm, networking, numa, pagecache, pci, pgtable, reclaim, sound, swap, v4l2, vma, writeback, xhci) — `acpi` free in both.

Request source: two untracked local files at the documented tree's root on the planning machine, `prompts/prompt.md` (the request) and `prompts/plan.md` (a stale prior plan; adjudicated below). Every constraint they impose is extracted into this file's Context, Scope decisions, and Stale-input reuse map, so the campaign resumes on any machine without them. The request asks for an ACPI documentation set covering six areas — the ACPI event model, device object notification, device configuration (identification and configuration objects), the base ACPI hierarchy as the kernel represents it, device power management, and the embedded controller — with the emphasis in the request's own words: "The pages you're going to create should focus not only the generic ACPI concepts, but more importantly how Linux kernel internally tracking/representing some of the major ACPI constructs." Fine granularity is requested ("You can decide divisions of pages. I'd prefer finer granularity"), calibrated against the PCI campaign's catalog granularity (one mechanism, method, or object per page; see `campaigns/pci.md` for the model the request points at).

The invocation that commissioned this plan adds four standing enumeration mandates, verbatim: "make sure to explicitly mention and enumerate all tracepoint, any places where any debug message is printed, any async event handling/lazy processing/deferred work/any design where things are handled asynchronously, and all subsystem-specific debugging infrastructure." These mandates shape the inventory (two dedicated subsystem-wide sweep areas plus per-area enumeration items), the catalog (a dedicated cross-cutting group), and a standing per-page write rule (Execution & verification).

Documented tree: a Linux kernel checkout identified by tag `v7.0`, commit `028ef9c96e96` ("Linux 7.0") — the tag+commit pin, never a filesystem path, is the tree's identity; a machine resuming this campaign locates its own checkout and confirms `git describe --tags` prints `v7.0` before any pass runs. semcode index confirmed present at that commit at planning time (2026-07-19); re-confirm the local index on whatever machine dispatches agents. Elixir tag confirmed live (v7.0 `drivers/acpi/ec.c` fetched 2026-07-19); all links use `https://elixir.bootlin.com/linux/v7.0/source/...`.

Subsystem Map entry ACPI (`guidelines/reference/subsystems.md`): dir `acpi`, tag `acpi`, kernel_paths `drivers/acpi/`, `include/acpi/`, `include/linux/acpi.h`, spec "ACPI Specification", section6_heading METHODS. Campaign delta to kernel_paths (the Map lists search-first paths; this catalog's seams require more): `drivers/gpio/gpiolib-acpi-core.c` + `drivers/gpio/gpiolib-acpi.h` (_AEI/GPIO-signaled events), `drivers/pnp/pnpacpi/` (_PRS/_SRS consumption), `drivers/pci/hotplug/acpiphp_glue.c` (Bus Check/Device Check consumer example), `drivers/pci/pci-acpi.c` (_DSM consumer example), `include/linux/mod_devicetable.h` (`struct acpi_device_id`), `tools/power/acpi/` (in-tree debug tooling), `include/ras/ras_event.h` + `drivers/ras/ras.c` and `include/trace/events/power.h` (tracepoint seams), `Documentation/firmware-guide/acpi/` + `Documentation/admin-guide/acpi/` (KERNEL DOCUMENTATION sections).

Stale-session inputs (hints only, never evidence): `prompts/plan.md`, a 43-page ACPI plan produced by an earlier session for a retired skill layout ("kmemo-devel"). Its topic divisions and high-level structure are minable; its details are stale by declaration of the commissioning invocation ("The materials contains staled information. You may reuse high-level concept but must take great care with its details"), it embeds machine-local absolute paths, and it references two draft corpora (`drafts/`, `kernel-glossary-devel/docs/acpi/`) that were verified ABSENT on the planning machine (2026-07-19) — those corpora are not inputs anywhere, and no agent searches for them. Full adjudication in the Stale-input reuse map at the end of this file; every stale anchor consumed by this plan was re-verified by the Phase 1 inventory (each area digest carries a claim-verification item).

NOT inputs: other campaigns' workspaces under `progress/` (isolation per SKILL.md, "The three artifacts and the three states"); `guidelines/reference/samples/` pages (style/depth calibration only, never kernel facts); the absent draft corpora named above.

Output root: `docs/acpi/` (does not exist before this campaign; every row is a NEW page). No `SUMMARY.md`/`mkdocs.yml` edits. No git commits without an explicit user go.

## Re-entry contract

Standing instructions to any executor, on any machine, cold or warm:

1. Confirm the tree: a Linux kernel checkout at tag `v7.0`, commit `028ef9c96e96` (`git describe --tags` at the tree root prints `v7.0`). A different tree voids every anchor in this spec — stop and surface it. Confirm the Elixir tag v7.0 resolves before writing links.
2. Derive campaign state: diff this catalog's rows against `docs/acpi/`. All rows are NEW (no prior `docs/acpi/` exists); a file already on disk at a catalog path means another slice produced it — existence is completion unless this machine's run log says otherwise.
3. Create or reuse the machine-local workspace `progress/acpi/` (run log `log.md`, one dossier per page). It is never committed.
4. Execute ONLY the slice the invoker named — a batch from this spec's batch order (its recommended slicing), or an explicit page list. Given a bare "run acpi" with no slice: report the derived state and ask; never pick a slice autonomously. Overwrite guard: a catalog page that already exists on disk is never overwritten silently — stop and surface it ("already exists — repair, skip, or rewrite?").
5. Run the slice per SKILL.md "Modes": one writer per page, briefed per `guidelines/passes/02-write.md` with the page's catalog row, its cluster's boundary rules, and the project-specific bans and write-time rules from this spec's Execution & verification section (including the per-page instrumentation/async enumeration rule); then the orchestrator check per page (`guidelines/passes/03-check.md`); events go to the run log. Sub-agent briefs get absolute paths composed at dispatch time from the local environment; this spec never carries them.
6. Promote anything durable — a spec claim the tree refuted, a user amendment, a settled adjudication — into this spec as a dated amendment (or surface it for the waivers files). The run log does not travel.
7. Verification cadence: per the checkpoint decision recorded under Scope decisions (pending below until the user answers).

## Scope decisions

### Hard constraints from the request (prompts/prompt.md, verbatim or near-verbatim)

1. Kernel-correspondence mandate: pages cover "not only the generic ACPI concepts, but more importantly how Linux kernel internally tracking/representing some of the major ACPI constructs". Standing rule restated for writers in Execution & verification: no spec-concept paragraph without its kernel representation named.
2. Granularity: "You can decide divisions of pages. I'd prefer finer granularity." Calibration target: the PCI campaign catalog (one mechanism/method/object per page).
3. The six topic areas with their explicit bullets (each mapped to catalog rows below): ACPI Event Model (one page each for GPE, Fixed events, SCI, GPIO-Signaled events, Interrupt-Signaled events, _Lxx, _Exx, _EVT, _AEI, plus a relationship diagram spanning GPE/Fixed events, SCI, _Lxx/_Exx, ASL Notify(), kernel notifiers); Device Object Notification (a Notify() overview with generic types, a handler-lifecycle page, one page per concrete type — Bus Check, Device Check, Device Wake, "Add more if you see fit"); Device Configuration (identification: _ADR, _HID, _CID, _UID, "Add more if you see fit"; configuration objects: _PRS, _CRS, _SRS, _DSM, _DSD); Base ACPI hierarchy (basic data types and their kernel correspondence e.g. `union acpi_object`; how the kernel interacts with them, e.g. `acpi_evaluate_object` and variants; ASL resource-description macros/ResourceTemplates and `struct acpi_resource`; how the kernel calls a method and parses results); Device Power Management (ACPI D-states, _PSx, _PRx, how the kernel represents and builds those resources); EC (overview; usage model EC_CMD/EC_SC/EC_DATA/IBF/OBF; Burst Enable; EC command set; EC interrupt model IBF/OBF/SCI_EVT; _Qxx).
4. "Draw ASCII diagram to illustrate, but do not just draw the code enumerating flow graph." (rules 7g-7i: structural/spatial/temporal figures only, never call-graph enumerations)
5. "You must use semcode tools." (research toolchain; per-page procedure in Execution & verification)
6. "You must not use hedging wordings."
7. "You must not include vendor-specific thigns (e.g. Intel, NVIDIA)" [sic]. Interpretation, mirroring the PCI campaign's settled reading: no vendor-specific mechanism or vendor-driver policy documented as the mechanism; concrete usage examples come from vendor-neutral in-tree consumers (drivers/acpi/ itself: battery.c, ac.c, thermal.c, button.c, fan_core.c, hed.c, dock.c, evged.c; plus subsystem-neutral consumers such as drivers/pci/pci-acpi.c and acpiphp). To be confirmed at the checkpoint.

### Constraints from the commissioning invocation (verbatim or near-verbatim)

8. Stale-material posture: "The materials contains staled information. You may reuse high-level concept but must take great care with its details." Consequence: prompts/plan.md contributes topic structure as hints; every symbol, line number, and behavioral claim taken from it was re-verified by the Phase 1 inventory before entering this catalog, and writers never consult it (it may be absent on their machine).
9. Machine portability (hard requirement on this spec): "make the plan file so that it doesn't include any information about the local environments (e.g. absolute paths), so that an agent with this agent skill on another machine can start the plan independently without being confused." The tree is identified by tag+commit only; all paths in this file are tree-relative or skill-relative; absolute paths enter only sub-agent briefs composed at dispatch time.
10. The four enumeration mandates: "explicitly mention and enumerate all tracepoint, any places where any debug message is printed, any async event handling/lazy processing/deferred work/any design where things are handled asynchronously, and all subsystem-specific debugging infrastructure." Landed in three places: (a) Inventory findings — Areas G (async/deferred sweep) and H (debug/trace/infrastructure sweep) enumerate subsystem-wide, and every per-area digest carries tracepoint/debug-print/async items for its own paths; (b) Page catalog — a dedicated cross-cutting group documents the async work model and the debugging infrastructure; (c) Execution & verification — a standing per-page rule: every page explicitly enumerates the tracepoints, debug-print sites, and asynchronous handoffs of the flows it documents, stating a verified negative ("no tracepoint fires on this path") where the enumeration is empty.

### User-confirmed decisions (checkpoint answers, 2026-07-19)

1. Catalog: "Approve all 65 rows" — the full catalog stands (40 [request] / 5 [request+] / 13 [args] / 7 [curated]); the merge-eligible pair core/evaluate-object.md + core/evaluation-helpers.md (review #11) stays split.
2. Vendor-neutrality: the settled PCI-campaign reading confirmed — no vendor-specific mechanism or vendor-driver policy documented as the mechanism; concrete usage examples come from vendor-neutral in-tree consumers (Scope decisions #7 stands as written).
3. Section-6 heading: REGISTERS on the four EC protocol pages (ec/registers.md, ec/command-set.md, ec/burst-enable.md, ec/interrupt-model.md); METHODS everywhere else per the Subsystem Map. The deviation is recorded as a dated note in the Map's ACPI entry (`guidelines/reference/subsystems.md`).
4. Verification cadence: on demand only — no scheduled `acpi-verify`; pages end this campaign at LINTED, and CERTIFIED stamps arrive only from a user-invoked verify campaign.

Explicit go: received 2026-07-19 via the checkpoint answers (decision 1 approves the catalog). The go approves the CATALOG; execution starts only when the user names a slice (recommended first slice: B1). Per campaign mode, pages of an invoked slice save without per-page asks; git commits require a separate user go.

## Inventory findings

(One compact digest per area, recorded verbatim from the read-only inventory agents, dispatched 2026-07-19. Every line number in a digest is a hint to re-verify on disk at write time, never a citation.)

### Area A: event model core (GPE, fixed events, SCI, GPE methods, GED, _AEI) — COMPLETE (recorded 2026-07-19)

#### 1. Core structs
- `acpi_gpe_event_info` — drivers/acpi/acpica/aclocal.h:448 — per-GPE record: `dispatch` union, `register_info` backpointer, `flags`, `gpe_number`, `runtime_count` (refcount), `disable_for_dispatch`.
- `acpi_gpe_dispatch_info` (union) — aclocal.h:438 — one of `method_node` / `handler` / `notify_list`.
- `acpi_gpe_handler_info` — aclocal.h:419 — installed-handler dispatch: address/context, saved `method_node`, `original_flags`, `originally_enabled`.
- `acpi_gpe_notify_info` — aclocal.h:429 — linked list of wake-notify device nodes (implicit notify).
- `acpi_gpe_register_info` — aclocal.h:466 — one status/enable register pair: `status_address`/`enable_address` (`acpi_gpe_address`), `base_gpe_number`, `enable_for_wake/run`, `mask_for_run`, `enable_mask`.
- `acpi_gpe_address` — aclocal.h:459 — space_id + 64-bit register address.
- `acpi_gpe_block_info` — aclocal.h:480 — one GPE0/GPE1/Block-Device register block: node, prev/next, `xrupt_block` backpointer, `register_info[]`/`event_info[]`, address, register_count, gpe_count, block_base_number, initialized.
- `acpi_gpe_xrupt_info` — aclocal.h:497 — one per GPE interrupt level: prev/next, `gpe_block_list_head`, `interrupt_number`.
- `acpi_gpe_walk_info` — aclocal.h:504 — context for the `_Lxx`/`_Exx` namespace walk (gpe_device/gpe_block/count/owner_id).
- `acpi_gpe_device_info` — aclocal.h:512 — context for index→device GPE lookup walk.
- `acpi_sci_handler_info` — aclocal.h:411 — linked-list node for host-installed SCI handlers.
- `acpi_fixed_event_handler` — aclocal.h:526 — handler+context per fixed event; array `acpi_gbl_fixed_event_handlers[ACPI_NUM_FIXED_EVENTS]` (acglobal.h:243-244).
- `acpi_fixed_event_info` — aclocal.h:531 — status/enable register-id + bitmask; table instance (5 entries: PMTIMER/GLOBAL/POWER_BUTTON/SLEEP_BUTTON/RTC) at drivers/acpi/acpica/utglobal.c:168.
- `acpi_gpe_block_status_context` — drivers/acpi/acpica/hwgpe.c:517 — local helper for "any GPE status set" walk.
- `acpi_ged_event` — drivers/acpi/evged.c:48 — Linux GED per-IRQ record: node, dev, gsi, irq, acpi `handle` (`_EVT` or `_Lxx`/`_Exx`).
- `acpi_ged_device` — evged.c:43 — per platform-device state: dev + `event_list`.
- `acpi_gpio_event` — drivers/gpio/gpiolib-acpi-core.c:39 — GPIO-signaled-event record: node, handle, handler fn, pin, irq, irqflags, irq_is_wake/requested, desc.
- `acpi_gpio_chip` — gpiolib-acpi-core.c:57 — per gpio_chip ACPI state incl. `events` list + `deferred_req_irqs_list_entry`.

#### 2. API families
- GPE enable/disable/wake (drivers/acpi/acpica/evxfgpe.c): `acpi_update_all_gpes`:43, `acpi_enable_gpe`:92/export:131, `acpi_disable_gpe`:148, `acpi_set_gpe`:199 (unconditional, bypasses refcount), `acpi_mask_gpe`:259, `acpi_mark_gpe_for_wake`:306, `acpi_setup_gpe_for_wake`:351, `acpi_set_gpe_wake_mask`:492, `acpi_clear_gpe`:568, `acpi_get_gpe_status`:610, `acpi_dispatch_gpe`:653, `acpi_finish_gpe`:678, `acpi_disable_all_gpes`:717, `acpi_enable_all_runtime_gpes`:748, `acpi_enable_all_wakeup_gpes`:779, `acpi_any_gpe_status_set`:811, `acpi_install_gpe_block`:852, `acpi_remove_gpe_block`:952, `acpi_get_gpe_device`:1017. Handler install: `acpi_install_gpe_handler`/`acpi_install_gpe_raw_handler`/`acpi_remove_gpe_handler` — drivers/acpi/acpica/evxface.c:839/873/904, internal `acpi_ev_install_gpe_handler` (static) at evxface.c:715. Internal engine (drivers/acpi/acpica/evgpe.c): `acpi_ev_add/remove_gpe_reference`:158/205, `acpi_ev_enable_gpe`:78, `acpi_ev_mask_gpe`:103, `acpi_ev_update_gpe_enable_mask`:36, `acpi_ev_get_gpe_event_info`:291, `acpi_ev_low_get_gpe_info`:251. Hardware layer (drivers/acpi/acpica/hwgpe.c): `acpi_hw_low_set_gpe`:134, `acpi_hw_clear_gpe`:210, `acpi_hw_gpe_read/write`:43/81, `acpi_hw_get_gpe_register_bit`:110, `acpi_hw_get_gpe_status`:250, `acpi_hw_disable_all_gpes`:588, `acpi_hw_enable_all_runtime/wakeup_gpes`:610/632, `acpi_hw_check_all_gpes`:657.
- Fixed-event install/dispatch: `acpi_install_fixed_event_handler` — evxface.c:583; `acpi_remove_fixed_event_handler` — evxface.c:652; `acpi_install_global_event_handler` — evxface.c:533. Core (drivers/acpi/acpica/evevent.c): `acpi_ev_fixed_event_initialize` (static):126, `acpi_ev_fixed_event_detect`:167, `acpi_ev_fixed_event_dispatch` (static):236, `acpi_any_fixed_event_status_set`:280. Enable/disable/clear (drivers/acpi/acpica/evxfevnt.c): `acpi_enable_event`:142, `acpi_disable_event`:205, `acpi_clear_event`:265, `acpi_get_event_status`:309, plus `acpi_enable`/`acpi_disable`:31/96.
- SCI install/handling: `acpi_install_sci_handler`/`acpi_remove_sci_handler` — evxface.c:389/463. Core (drivers/acpi/acpica/evsci.c): `acpi_ev_install_sci_handler`:150, `acpi_ev_remove_all_sci_handlers`:182, `acpi_ev_sci_dispatch`:31 (fans out to host-installed handler list), `acpi_ev_sci_xrupt_handler` (static):76 (hard-irq: fixed-detect + gpe-detect + sci_dispatch), `acpi_ev_gpe_xrupt_handler`:120 (non-SCI GPE-block-device interrupt). Linux glue: `acpi_os_install/remove_interrupt_handler` — drivers/acpi/osl.c:556/592; `acpi_irq` (Linux threaded-irq entry) — osl.c:545.
- GED probe/dispatch (drivers/acpi/evged.c): `ged_probe`:141, `ged_remove`:176, `ged_shutdown`:163, `acpi_ged_request_interrupt`:68 (walks `_CRS`, resolves per-GSI `_Lxx`/`_Exx` else falls back to `_EVT`, `request_threaded_irq`), `acpi_ged_irq_handler`:56.
- `_AEI` walk / GPIO event path (drivers/gpio/gpiolib-acpi-core.c): `acpi_gpiochip_request_interrupts`:460 (walks `METHOD_NAME__AEI`), `acpi_gpiochip_alloc_event`:343, `acpi_gpiochip_request_irqs`/`_irq`:246/218, `acpi_gpio_irq_handler`:152 (plain `_Lxx`/`_Exx`, `acpi_evaluate_object`), `acpi_gpio_irq_handler_evt`:161 (`_EVT`, `acpi_execute_simple_method`), `acpi_gpiochip_free_interrupts`:497, `acpi_gpio_process_deferred_list`:533. Deferred/quirk plumbing (drivers/gpio/gpiolib-acpi-quirks.c): `acpi_gpio_add/remove_from_deferred_list`:47/60, `acpi_gpio_need_run_edge_events_on_boot`:68, `acpi_gpio_handle_deferred_request_irqs`:121 (`late_initcall_sync`:131).
- `_EVT` evaluation helper: `acpi_execute_simple_method` — drivers/acpi/utils.c:676.

#### 3. Lifecycle & locking
- Init order: `acpi_bus_init` (drivers/acpi/bus.c:1390) → `acpi_load_tables` → `acpi_enable_subsystem(ACPI_NO_ACPI_ENABLE)` (bus.c:1415 → drivers/acpi/acpica/utxfinit.c:110) → `acpi_enable()` (hw ACPI mode) → `acpi_ev_initialize_events` (utxfinit.c:170 call → evevent.c:34): `acpi_ev_fixed_event_initialize` disables all fixed events, then `acpi_ev_gpe_initialize` (evgpeinit.c:56) builds GPE0/1 blocks from FADT via `acpi_ev_create_gpe_block` (evgpeblk.c:295) — GPEs created disabled → `acpi_ev_install_xrupt_handlers` (utxfinit.c:184 call → evevent.c:80) installs the SCI handler (evsci.c:150) + global-lock handler. Then `acpi_bus_init` runs `acpi_initialize_objects` (bus.c:1421, `_STA`/`_INI`/`_REG`). GPE enablement at scan completion: `acpi_scan_init` (drivers/acpi/scan.c:2819) calls `acpi_gpe_apply_masked_gpes()` then `acpi_update_all_gpes()` (scan.c:2856-2857) before `acpi_bus_scan`, which walks every block via `acpi_ev_walk_gpe_list(acpi_ev_initialize_gpe_block,...)` (evgpeblk.c:417) auto-enabling every `_Lxx`/`_Exx`-backed, non-wake GPE (`ACPI_GPE_AUTO_ENABLED`). Dynamic table loads re-walk via `acpi_ev_update_gpes` (evgpeinit.c:203) → `acpi_ev_match_gpe_method` (evgpeinit.c:291).
- Locks: `acpi_gbl_gpe_lock` (`acpi_spinlock`, acglobal.h:87) guards GPE data structs AND GPE hardware registers — comment at evgpe.c:369 notes the separate hw lock is not needed for GPE I/O; `acpi_gbl_hardware_lock` (`acpi_raw_spinlock`, acglobal.h:88) guards non-GPE ACPI h/w (PM1/PM2) only. `ACPI_MTX_EVENTS` (mutex #3, aclocal.h:49) guards handler install/remove and GPE-block topology; `ACPI_MTX_NAMESPACE` (aclocal.h:47) guards block create/delete + the `_Lxx`/`_Exx` walk.
- Firing→completion: `acpi_irq` (osl.c:545) → `acpi_ev_sci_xrupt_handler` (evsci.c:76) → `acpi_ev_fixed_event_detect`(evevent.c:167) + `acpi_ev_gpe_detect`(evgpe.c:347) + `acpi_ev_sci_dispatch`(evsci.c:31), all under `acpi_gbl_gpe_lock`. `acpi_ev_detect_gpe` (evgpe.c:625) reads status/enable, calls `acpi_ev_gpe_dispatch` (evgpe.c:747) which always disables the GPE first (evgpe.c:765), clears status now iff edge-triggered (evgpe.c:776-787), sets `disable_for_dispatch=TRUE` (evgpe.c:789), then either runs an installed handler inline at interrupt level (re-enable only if it returns `ACPI_REENABLE_GPE`, evgpe.c:812) or queues `acpi_ev_asynch_execute_gpe_method` via `acpi_os_execute(OSL_GPE_HANDLER,...)` (evgpe.c:823). That function (evgpe.c:455) evaluates the method/queues implicit Notify, then unconditionally requeues `acpi_ev_asynch_enable_gpe` via `OSL_NOTIFY_HANDLER` (evgpe.c:526) → `acpi_ev_finish_gpe` (evgpe.c:578) clears (iff level-triggered) and conditionally re-enables.

#### 4. Hard-coded limits
- `ACPI_GPE_REGISTER_WIDTH` = 8 — include/acpi/actypes.h:370 — GPEs per status/enable register.
- `ACPI_MAX_GPE_BLOCKS` = 2 — actypes.h:366 — FADT GPE0/GPE1 block count.
- `ACPI_NAMESEG_SIZE` = 4 — actypes.h:378 — fixes `_Lxx`/`_Exx` to exactly 2 hex digits after L/E.
- `ACPI_NUM_FIXED_EVENTS` = `ACPI_EVENT_MAX`+1 = 5 — actypes.h:727 (`ACPI_EVENT_MAX`=4, :726).
- `ACPI_UINT8_MAX` (0xFF) — actypes.h:30 — cap on `gpe_event_info->runtime_count` (evgpe.c:166, returns `AE_LIMIT` past it).
- GSI/pin bound 0-255 for per-index `_Lxx`/`_Exx` lookup — drivers/acpi/evged.c:103 (`case 0 ... 255:`) and drivers/gpio/gpiolib-acpi-core.c:362 (`if (pin <= 255)`); above that only `_EVT` fallback is tried.
- `gpe_count`/`block_base_number` are `u16`, `register_count` is `u32` — aclocal.h:488-490 — no separate compile-time max-GPEs-per-block beyond `register_count*8`.
- `flags` in `acpi_gpe_event_info` is one `u8` (aclocal.h:451) — dispatch-type mask uses bits 0-2, xrupt-type bit 3, CAN_WAKE/AUTO_ENABLED/INITIALIZED bits 4-6 (actypes.h:776-790); bit 7 unused.
- `ACPI_MAX_SYS_NOTIFY` = 0x7F — actypes.h:806 — System- vs Device-handler-list split used by the implicit-notify path (evmisc.c:86).

#### 5. Version-specific facts
- drivers/gpio/gpiolib-acpi.c no longer exists. Split 2025-05-13 (commit 92dc572852dd, "gpiolib: acpi: Move quirks to a separate file") into drivers/gpio/gpiolib-acpi-core.c (core, incl. `acpi_gpiochip_request_interrupts`) + drivers/gpio/gpiolib-acpi-quirks.c (DMI quirks, ignore-lists, deferred-list plumbing) + drivers/gpio/gpiolib-acpi.h. Any doc citing "gpiolib-acpi.c:<line>" is stale for v7.0.
- drivers/acpi/osl.c:1697-1698 now creates `kacpid_wq`/`kacpi_notify_wq` with the `WQ_PERCPU` flag, added by commit ec4291f524a3 (2025-10-30) as part of the treewide unbound-by-default workqueue migration; older docs show `alloc_workqueue()` with `0`/`WQ_MEM_RECLAIM` only.
- gpiolib-acpi-core.c:406 uses the new `kzalloc_obj()` allocator and gpiolib-acpi-core.c:140 uses `__free(gpio_device_put)` scope-based cleanup — both from a 2026-02 treewide alloc_obj/cleanup.h modernization (commits 69050f8d6d07, bf4afc53b77a), not present in pre-v7.0 snapshots.
- `acpi_gpio_need_run_edge_events_on_boot()`/`run_edge_events_on_boot` module param (gpiolib-acpi-quirks.c:19,68, added 2025-05-13) gates the boot-time edge-IRQ replay in `acpi_gpiochip_request_irq` (gpiolib-acpi-core.c:236-243) — not in older docs.
- Core struct/function names (`acpi_gpe_event_info`, `acpi_ev_gpe_detect`/`dispatch`, `acpi_ev_fixed_event_detect`/`dispatch`, `acpi_install_sci_handler`, evged.c's probe/IRQ-handler shape) are unchanged from v4.x-v6.x ACPICA — no renames found in the mechanism itself.

#### 6. Suggested extra page topics
- GPE blocks & GPE Block Devices — `acpi_gpe_block_info`, `acpi_ev_create_gpe_block` (evgpeblk.c:295), `acpi_install_gpe_block`/`acpi_remove_gpe_block` (evxfgpe.c:852/952) — FADT GPE0/1 vs auxiliary Block-Device model warrants its own page.
- GPE wake vs runtime & implicit notify — `enable_for_run`/`enable_for_wake`/`mask_for_run` triple (aclocal.h:466), `acpi_setup_gpe_for_wake`, `acpi_gpe_notify_info`, `acpi_ev_queue_notify_request` (evmisc.c:67) — the S3/S0ix wake path is large enough to split out.
- ACPI OS glue: `acpi_os_execute` and the ACPI workqueues — `kacpid_wq`/`kacpi_notify_wq`, `OSL_GPE_HANDLER`/`OSL_NOTIFY_HANDLER` (osl.c:1092), `acpi_os_wait_events_complete` (osl.c:1164) — shared deferred-execution substrate under GPE, fixed-event and notify handling alike.
- Raw GPE handlers & GPE polling mode — `ACPI_GPE_DISPATCH_RAW_HANDLER`, `acpi_install_gpe_raw_handler`/`acpi_set_gpe` (evxfgpe.c:199, evxface.c:873) — a distinct, less-documented dispatch mode.
- `/sys/firmware/acpi/interrupts` counters — drivers/acpi/sysfs.c `gpe_count`/`fixed_event_count`/`acpi_global_event_handler` (sysfs.c:611/625/637) — the userspace diagnostic surface for this whole area.
- ACPI GPIO quirks & deferred `_AEI` IRQ requests — gpiolib-acpi-quirks.c DMI ignore-lists + deferred_req_irqs list + `late_initcall_sync` — boundary/operational quirk handling distinct from the core GPIO-events page.

#### 7. Tracepoints
- Negative finding. No `TRACE_EVENT` definitions and no `trace_*()` ftrace call sites in any searched file. Evidence: grep over drivers/acpi/acpica/ev*.c, hwgpe.c, evged.c, gpiolib-acpi-core.c, gpiolib-acpi.h, osl.c, bus.c, sysfs.c matches only drivers/acpi/sysfs.c, and those hits (sysfs.c:22-25,154-179) are ACPICA's unrelated AML-execution-tracing module params (`trace_method_name` etc.), not ftrace. `find include/trace/events -iname "*acpi*" -o -iname "*gpe*"` returns nothing.

#### 8. Debug/diagnostic printing
- All acpica files here set `_COMPONENT ACPI_EVENTS` except hwgpe.c, which sets `ACPI_HARDWARE` (hwgpe.c:14). `ACPI_DEBUG_PRINT` counts: evgpeinit.c 5, evxface.c 3, evglock.c 3, evxfevnt.c 3, evgpe.c 2, evmisc.c 2, evevent.c 1, evgpeblk.c 1, (evsci.c/evgpeutil.c/hwgpe.c/evxfgpe.c 0). `ACPI_ERROR` counts: evgpeblk.c 5, evxfevnt.c 5, evgpeinit.c 2, evevent.c 1, evgpe.c 1, hwgpe.c 1, evxfgpe.c 1. `ACPI_EXCEPTION` counts: evgpe.c 4, evevent.c 4, evgpeinit.c 3, evgpeblk.c 1. `ACPI_WARNING`: evxface.c 3 (only file in-scope with any). Load-bearing sites: unhandled GPE — `ACPI_ERROR("No handler or method for GPE %02X, disabling event")` evgpe.c:839; unhandled fixed event — `ACPI_ERROR("No installed handler for fixed event...")` evevent.c:255; async method failure — `ACPI_EXCEPTION("while evaluating GPE method [%4.4s]")` evgpe.c:511; queue failure — `ACPI_EXCEPTION("Unable to queue handler for GPE %02X...")` evgpe.c:827. Linux glue: evged.c uses `dev_err`/`dev_err_once`/`dev_dbg` (7 sites; load-bearing: "IRQ method execution failed" evged.c:63, "cannot locate _EVT method" evged.c:114); gpiolib-acpi-core.c uses `dev_err`/`dev_info`/`dev_dbg` (19 sites); drivers/acpi/bus.c uses `acpi_handle_debug`/`acpi_handle_err` (notify-type logging bus.c:574-609) among 22 `pr_*`-family sites; drivers/acpi/osl.c uses `pr_err`/`pr_info` (16 sites, e.g. "SCI (IRQ%d) allocation failed" osl.c:583); drivers/acpi/sysfs.c uses `pr_debug`/`pr_warn` (10 sites, e.g. "GPE event 0x%02x" sysfs.c:642).

#### 9. Async/deferred/lazy processing
- SCI→method: `acpi_ev_gpe_dispatch` queues `acpi_ev_asynch_execute_gpe_method` via `acpi_os_execute(OSL_GPE_HANDLER,...)` (evgpe.c:823) → osl.c:1137-1145 `queue_work_on(0, kacpid_wq,...)` (pinned to CPU0 to avoid SMI corruption, per comment) → runs in workqueue context (evgpe.c:455), evaluating `_Lxx`/`_Exx` or queuing implicit Notify.
- Re-enable companion: unconditionally requeues `acpi_ev_asynch_enable_gpe` via `acpi_os_execute(OSL_NOTIFY_HANDLER,...)` (evgpe.c:526) → osl.c:1134-1135 `queue_work(kacpi_notify_wq,...)` → `acpi_ev_finish_gpe` (evgpe.c:578-592).
- Implicit-notify: `acpi_ev_queue_notify_request` (evmisc.c:67) → `acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_ev_notify_dispatch,...)` (evmisc.c:139) → `kacpi_notify_wq` → `acpi_ev_notify_dispatch` (static, evmisc.c:161) invokes installed handlers (e.g. `acpi_bus_notify`, bus.c).
- Drain on teardown: `acpi_remove_gpe_handler` (evxface.c:991) and shutdown call `acpi_os_wait_events_complete()` (osl.c:1164): `synchronize_hardirq(acpi_sci_irq)` then `flush_workqueue(kacpid_wq)`/`flush_workqueue(kacpi_notify_wq)`.
- GED: `request_threaded_irq(irq, NULL, acpi_ged_irq_handler,...)` (evged.c:130) — primary handler is `NULL`, so GED is always genuinely threaded; `_EVT`/`_Lxx`/`_Exx` evaluation never runs in hard-irq context.
- GPIO events: same threaded-only pattern, `request_threaded_irq(event->irq, NULL, event->handler,...)` (gpiolib-acpi-core.c:224); IRQ request itself can be lazily deferred — `acpi_gpiochip_request_interrupts` (gpiolib-acpi-core.c:460) defers via `acpi_gpio_add_to_deferred_list` (gpiolib-acpi-quirks.c:47) for chips registered before late_init, flushed once by `late_initcall_sync(acpi_gpio_handle_deferred_request_irqs)` (gpiolib-acpi-quirks.c:121,131) → `acpi_gpio_process_deferred_list` (gpiolib-acpi-core.c:533).
- Boot-time edge replay: `acpi_gpiochip_request_irq` (gpiolib-acpi-core.c:236-243) synchronously re-invokes the handler once at request time for edge IRQs when `acpi_gpio_need_run_edge_events_on_boot()` says so.
- Polling fallback (non-default): `acpi_enable_gpe`/`acpi_remove_gpe_handler` synchronously call `acpi_ev_detect_gpe` right after (re-)enabling (evxfgpe.c:118, evxface.c:980) when `ACPI_GPE_IS_POLLING_NEEDED` (acevents.h:19-25, compile-time `FALSE` unless `ACPI_USE_GPE_POLLING`).

#### 10. Stale-plan claim verification
- (a) Confirmed — drivers/acpi/acpica/aclocal.h:448, per-GPE record.
- (b) Confirmed — `acpi_ev_gpe_detect` evgpe.c:347, `acpi_ev_gpe_dispatch` evgpe.c:748; detect calls dispatch via `acpi_ev_detect_gpe` (evgpe.c:723) for non-raw-handler GPEs.
- (c) Confirmed — `acpi_enable_gpe` evxfgpe.c:92 (export :131), `acpi_mark_gpe_for_wake` evxfgpe.c:306 (export :331); both public/exported.
- (d) Confirmed — evevent.c:167 and evevent.c:236 (static).
- (e) Confirmed — evxface.c:583.
- (f) Confirmed — `acpi_ev_sci_xrupt_handler` static at evsci.c:76; Linux-side handler is `acpi_irq` at osl.c:545 (`request_threaded_irq`, osl.c:581), invoked as `acpi_irq_handler` set by `acpi_os_install_interrupt_handler`.
- (g) Confirmed — evxface.c:389.
- (h) Confirmed — evgpeinit.c:291-292, decodes `name[1]` 'L'→`ACPI_GPE_LEVEL_TRIGGERED`/'E'→`ACPI_GPE_EDGE_TRIGGERED` (evgpeinit.c:333-342) plus 2-hex-digit number.
- (i) Confirmed — edge cleared before dispatch inside `acpi_ev_gpe_dispatch` (evgpe.c:776-787); level cleared only in `acpi_ev_finish_gpe` (evgpe.c:578-592) called post-completion via `acpi_ev_asynch_enable_gpe` (evgpe.c:552) or directly for `ACPI_REENABLE_GPE` handlers (evgpe.c:812-814).
- (j) Confirmed-with-caveat — function exists in drivers/gpio/gpiolib-acpi-core.c and walks `METHOD_NAME__AEI` (:480-481), but its definition is at line 460, not 491; also the file itself is new (was gpiolib-acpi.c pre-2025, see item 5).
- (k) Confirmed — evged.c: `ged_probe`:141, `acpi_ged_request_interrupt`:68, `acpi_ged_irq_handler`:56, `struct acpi_ged_event`:48.
- (l) Confirmed — `_EVT`/per-GSI `_Lxx`/`_Exx` via `acpi_execute_simple_method` from evged.c:61 (`acpi_ged_irq_handler`) and from gpiolib-acpi-core.c:165 (`acpi_gpio_irq_handler_evt`); plain `_Lxx`/`_Exx` GPIO path instead uses `acpi_evaluate_object` (gpiolib-acpi-core.c:156).

### Area B: device notification and hotplug — COMPLETE (recorded 2026-07-19)

#### 1. Core structs & constant families
- `acpi_notify_handler` typedef (handler sig): `include/acpi/actypes.h:1061`
- `struct acpi_global_notify_handler {handler,context}` — root/global handler storage: `drivers/acpi/acpica/aclocal.h:660-663`; storage array `acpi_gbl_global_notify[2]`: `drivers/acpi/acpica/acglobal.h:121`
- `struct acpi_notify_info` (deferred-dispatch payload: node/value/handler_list_id/global): `drivers/acpi/acpica/aclocal.h:669-675`
- `ACPI_COMMON_NOTIFY_INFO` macro → `notify_list[2]` per-object handler heads: `drivers/acpi/acpica/acobject.h:188-189`
- `ACPI_SYSTEM_NOTIFY`0x1/`ACPI_DEVICE_NOTIFY`0x2/`ACPI_ALL_NOTIFY`/`ACPI_MAX_NOTIFY_HANDLER_TYPE`0x3/`ACPI_NUM_NOTIFY_TYPES`2: `include/acpi/actypes.h:800-804`
- `ACPI_MAX_SYS_NOTIFY`0x7F: `actypes.h:806`; `ACPI_SYSTEM_HANDLER_LIST`0/`ACPI_DEVICE_HANDLER_LIST`1: `actypes.h:809-810`
- `ACPI_NOTIFY_BUS_CHECK`..`DISCONNECT_RECOVER` (0x00-0x0F): `actypes.h:615-630`
- `ACPI_GENERIC_NOTIFY_MAX`0x0F: `actypes.h:632`; `ACPI_SPECIFIC_NOTIFY_MAX`0x84: `actypes.h:633`; `ACPI_MAX_DEVICE_SPECIFIC_NOTIFY`0xBF: `actypes.h:807`
- `struct acpi_hotplug_profile {kobj, scan_dependent, notify_online, enabled:1, demand_offline:1}`: `include/acpi/acpi_bus.h:117-122`
- `struct acpi_hotplug_context {self, notify(acpi_hp_notify), uevent, fixup}`: `acpi_bus.h:148-157`
- `struct acpi_device_ops {add, remove, notify(acpi_op_notify)}`: `acpi_bus.h:168-172` — void(*)(acpi_device*,u32) shape
- `struct acpi_device_flags` `hotplug_notify:1`, `is_dock_station:1`: `acpi_bus.h:203-219`
- `struct acpi_scan_handler {ids, match, attach, detach, post_eject, bind, unbind, hotplug}`: `acpi_bus.h:131-141`
- OST codes: `include/linux/acpi.h:679-704` (`ACPI_OST_EC_OSPM_SHUTDOWN`0x100/`_EJECT`0x103/`_INSERTION`0x200; `ACPI_OST_SC_*` 0x0-0x84, reused per-context)
- `ACPI_SB_NOTIFY_SHUTDOWN_REQUEST`0x81 (local #define, `\_SB`-specific): `drivers/acpi/bus.c:684` — do not confuse with reserved `ACPI_NOTIFY_SHUTDOWN_REQUEST`0x0C at `actypes.h:627`

#### 2. API families
- AML→dispatch: `AML_NOTIFY_OP`0x86 (`drivers/acpi/acpica/amlcode.h:76`) reached via `acpi_gbl_op_type_dispatch[]` table `drivers/acpi/acpica/dswexec.c:29-40` → `acpi_ex_opcode_2A_0T_0R` (`drivers/acpi/acpica/exoparg2.c:55-107`, case at `:68`) → `acpi_ev_queue_notify_request(node,value)` call at `exoparg2.c:96` → `drivers/acpi/acpica/evmisc.c:68-146` picks system/device list, calls `acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_ev_notify_dispatch, info)` at `evmisc.c:141` → `acpi_ev_notify_dispatch` (`evmisc.c:161-191`) invokes global handler then walks per-object list.
- Install/remove (ACPICA): `acpi_install_notify_handler` `drivers/acpi/acpica/evxface.c:56-190`; `acpi_remove_notify_handler` `evxface.c:210-329`; global iff `device==ACPI_ROOT_OBJECT`, else only `ACPI_TYPE_DEVICE/PROCESSOR/THERMAL` nodes gate via `acpi_ev_is_notify_object` `evmisc.c:35-51`.
- Install/remove (Linux): `acpi_dev_install_notify_handler` `drivers/acpi/bus.c:658-670`; `acpi_dev_remove_notify_handler` `bus.c:673-679` (thin wrappers, always call `acpi_os_wait_events_complete()`).
- Separate API `acpi_install_global_event_handler` `evxface.c:533-584` is for GPE/SCI events, not Notify — global Notify reuses `acpi_install_notify_handler` w/ `ACPI_ROOT_OBJECT` sentinel.
- Hotplug path: `acpi_bus_notify` (`bus.c:568-621`, the global `ACPI_SYSTEM_NOTIFY` handler installed at `bus.c:1466` inside `acpi_bus_init`) → `acpi_hotplug_schedule` (`drivers/acpi/osl.c:1192-1218`) → `acpi_hotplug_work_fn` (`osl.c:1183-1190`) → `acpi_device_hotplug` (`drivers/acpi/scan.c:442-499`) → `acpi_generic_hotplug_event` (`scan.c:422-440`): BUS_CHECK→`acpi_scan_bus_check` (`scan.c:415-420`), DEVICE_CHECK→`acpi_scan_device_check` (`scan.c:387-413`), EJECT_REQUEST/`ACPI_OST_EC_OSPM_EJECT`→`acpi_scan_hot_remove` (`scan.c:323-369`, `_EJ0` via `acpi_evaluate_ej0`).
- _OST: `acpi_evaluate_ost` `drivers/acpi/utils.c:541-562`; 8 callers: `acpi_generic_hotplug_event`(scan.c:422), `acpi_device_hotplug`(scan.c:442), `sb_notify_work`(bus.c:687), `acpi_bus_notify`(bus.c:568), `acpi_processor_ppc_ost`(processor_perflib.c:116), `eject_store`(device_sysfs.c:366), `acpi_pad_handle_notify`(acpi_pad.c:382), `acpi_send_edr_status`(pci/pcie/edr.c:132).

#### 3. Lifecycle & locking
- `acpi_scan_lock` (`DEFINE_MUTEX`, `scan.c:42`) held across `acpi_device_hotplug` body (`scan.c:448,497`); guards `adev->handle` validity vs concurrent removal.
- `lock_device_hotplug()`/`unlock_device_hotplug()` (`drivers/base/core.c:2343-2352`) wrap `acpi_device_hotplug` (`scan.c:446,497`) — shared global device-model hotplug lock, not ACPI-private.
- `acpi_hp_context_lock` (`scan.c:46`) via `acpi_lock_hp_context`/`acpi_unlock_hp_context` (`scan.c:68-76`) separately guards `adev->hp`/`hp->notify` reads (`scan.c:465-467`).
- Two workqueue hops = two execution contexts: `acpi_ev_notify_dispatch` runs on `kacpi_notify_wq` (`osl.c:1698`,`1135`); `acpi_device_hotplug` runs on `kacpi_hotplug_wq` (`osl.c:1699`,`1213`) — never caller/interrupt context.
- Removal ordering: `acpi_remove_notify_handler` unlinks under `ACPI_MTX_NAMESPACE` then itself calls `acpi_os_wait_events_complete()`; `acpi_dev_remove_notify_handler` (`bus.c:673-679`) calls it again — flushes `kacpi_notify_wq`/`kacpid_wq` (`osl.c:1164-1174`) so the handler fn-ptr can't fire post-removal.
- Caveat: that wait does not flush `kacpi_hotplug_wq` — a hotplug work item already handed off before handler teardown is instead protected by `acpi_scan_lock` + `acpi_get_acpi_dev`/`acpi_put_acpi_dev` refcounting (`scan.c:677-680`) + `INVALID_ACPI_HANDLE` check (`scan.c:452`).

#### 4. Hard-coded limits
- 0x00-0x0F "common": `ACPI_GENERIC_NOTIFY_MAX`0x0F `actypes.h:632` (names `actypes.h:615-630`).
- Real system/device routing boundary is 0x7F: `ACPI_MAX_SYS_NOTIFY` `actypes.h:806`, used in `evmisc.c:89` and `acpi_ut_get_notify_name` `drivers/acpi/acpica/utdecode.c:475`.
- 0x80-0x84 per-object-type: `ACPI_SPECIFIC_NOTIFY_MAX`0x84 `actypes.h:633`; name tables `utdecode.c:440-462`.
- 0x84-0xBF "device-specific": `ACPI_MAX_DEVICE_SPECIFIC_NOTIFY`0xBF `actypes.h:807`.
- 0xC0-0xFF: kernel labels this "Hardware-Specific" (`utdecode.c:504-506`), never "OEM" — and this whole 0x84/0xBF/0xC0 tier split is debug-name-only, not a routing/behavior boundary.
- Object-type gate: only `ACPI_TYPE_DEVICE/PROCESSOR/THERMAL` may receive Notify — `acpi_ev_is_notify_object`, `evmisc.c:35-51`.
- OST constants: `include/linux/acpi.h:679-704` (listed in item 1).
- Queue bounds: none found (negative finding) — each notify heap-allocates one `acpi_generic_state` (`evmisc.c:120`)/`acpi_hp_work` (`osl.c:1177`); workqueues unbounded beyond normal WQ concurrency.

#### 5. Version-specific facts
- `acpi_dev_install_notify_handler`/`remove` (`bus.c:658,673`) match the claimed modern thin-wrapper shape exactly — nothing renamed.
- `hotplug_event(u32,struct acpiphp_context*)` (`drivers/pci/hotplug/acpiphp_glue.c:783-835`) is a helper, not the registered callback; the actual `acpi_hp_notify` is `acpiphp_hotplug_notify` (`acpiphp_glue.c:837-846`), which calls `hotplug_event()`.
- `/sys/firmware/acpi/hotplug/force_remove` is neutered: `force_remove_store` (`drivers/acpi/sysfs.c:1006-1022`) unconditionally rejects `val==1` ("not supported anymore") — historically it forced removal bypassing checks.
- `container.c`/`acpi_memhotplug.c` register no `acpi_op_notify`/`acpi_hp_notify` in v7.0 (confirmed full-file read) — they rely on `acpi_scan_init_hotplug()` setting `adev->flags.hotplug_notify=true` for any ID match (`scan.c:2058-2066`), routing purely through generic `acpi_generic_hotplug_event`.
- Two parallel notify-callback shapes coexist by design: `acpi_hp_notify` `int(*)(acpi_device*,u32)` (`acpi_bus.h:148`) for hotplug-context devices vs `acpi_op_notify` `void(*)(acpi_device*,u32)` (`acpi_bus.h:166-171`) for classic `acpi_driver` devices.

#### 6. Suggested extra pages
- Device-class Notify code reference (0x80-0x89): `include/acpi/battery.h:10-12`, `drivers/acpi/ac.c:27`, `drivers/acpi/thermal.c:39-43`, `drivers/acpi/button.c:28-29`, `include/acpi/video.h:34-43`.
- _OST reference (spans every hotplug type, not just eject): `drivers/acpi/utils.c:541`, `include/linux/acpi.h:679-704`.
- Dock-station hotplug (own BUS/DEVICE/EJECT state machine, special-cased ahead of the generic path): `drivers/acpi/dock.c:410-471`, `scan.c:459-460`.
- `/sys/firmware/acpi/hotplug` sysfs knobs page (per-profile `enabled`, `eject`, deprecated `force_remove`): `drivers/acpi/sysfs.c:945-1038`, `drivers/acpi/device_sysfs.c:366-395`.
- PNP0C33 hardware-error notify as minimal/degenerate pattern (value ignored, pure notifier-chain fanout): `drivers/acpi/hed.c:46-49` — good contrast for the overview page.
- Observability page for Notify/hotplug (debug idioms + absence of tracepoints, per items 7/8).

#### 7. Tracepoints
- Negative finding: no `TRACE_EVENT`/`DEFINE_EVENT` for Notify or hotplug anywhere (`find include/trace/events -iname "*acpi*"` → empty). Only ACPI-adjacent `trace_*` call in `drivers/acpi/` is generic PM `trace_suspend_resume("acpi_suspend",...)` `drivers/acpi/sleep.c:604,621` (unrelated). The area's only "tracer" is ACPICA's AML method/opcode execution tracer (`acpi_ex_trace_point` `drivers/acpi/acpica/extrace.c:131`, `acpi_trace_point` `acpica/utdebug.c:607`), driven by `/sys/module/acpi/parameters/trace_*` (`drivers/acpi/sysfs.c:154-267`) — not a ftrace event, not notify-value-specific.

#### 8. Debug/diagnostic printing
- `evmisc.c`: 2 `ACPI_DEBUG_PRINT` (`:109` "No notify handler...ignoring", `:132` "Dispatching Notify on...").
- `evxface.c`: 1 notify-specific `ACPI_DEBUG_PRINT` (`:249` "Removing global notify handler"); 2 more (`:627,684`) belong to fixed-event-handler code, unrelated.
- `bus.c`: `acpi_bus_notify`'s switch = 9 `acpi_handle_debug`/`_err` sites (`:574-609`), incl. load-bearing default `"Unknown event type 0x%x\n"` at `bus.c:609`; file's other 13 sites are `_OSC`-related, unrelated.
- `scan.c`: hotplug-path sites `"Still not enumerated"` `dev_dbg` `:271`, `"Ejecting"` `acpi_handle_debug` `:339`, `"Already enumerated"` `dev_dbg` `:404`; remaining ~8 sites cover `_DEP`/backlight/attach, unrelated.
- `osl.c`: `"Scheduling hotplug event %u for deferred handling\n"` `acpi_handle_debug` `:1196` — single site.
- `dock.c`: 5 `acpi_handle_{info,err}` sites (`:307,316,394,443,633`), no `acpi_handle_debug`.
- Driver "Unsupported event" idiom (one default-branch log per driver): `ac.c:127`, `thermal.c:688`, `button.c:429`(lid)/`453`(button), `acpi_video.c:1568,1640` — all `acpi_handle_debug(...,"Unsupported event [0x%x]\n",event)`; `battery.c`'s `acpi_battery_notify` (`:1063`) has no such default branch (handles all events generically).

#### 9. Async/deferred/lazy processing
- Hop 1: `acpi_ev_queue_notify_request` (`evmisc.c:68`) → `acpi_os_execute(OSL_NOTIFY_HANDLER,...)` `evmisc.c:141` → `queue_work(kacpi_notify_wq,...)` `osl.c:1134-1136` → `acpi_ev_notify_dispatch` (`evmisc.c:161-191`) runs on `kacpi_notify_wq` kworker.
- Hop 2: `acpi_bus_notify` (running inside hop-1's worker) → `acpi_hotplug_schedule` `osl.c:1192` → `queue_work(kacpi_hotplug_wq,...)` `osl.c:1213` → `acpi_hotplug_work_fn` `osl.c:1183-1190` (calls `acpi_os_wait_events_complete()` then `acpi_device_hotplug` `scan.c:442`).
- Same hop-2 queue reachable directly from userspace, bypassing AML: `eject_store` `drivers/acpi/device_sysfs.c:366` calls `acpi_hotplug_schedule` with `src=ACPI_OST_EC_OSPM_EJECT`.
- `acpi_queue_hotplug_work` (`osl.c:1220-1223`) exposes `kacpi_hotplug_wq` generically for other work_structs needing hotplug-safe deferral.
- Button double-deferral: `acpi_button_event` (`drivers/acpi/button.c:481-484`) itself calls `acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_button_notify_run,...)` — a driver-owned second hand-off onto `kacpi_notify_wq` for its GPE-direct path.
- Dock: no separate workqueue — `dock_notify` (`drivers/acpi/dock.c:410-471`) runs synchronously inside the hop-2 `kacpi_hotplug_wq` worker via `acpi_device_hotplug`'s `is_dock_station` branch (`scan.c:459-460`); no `schedule_work`/`queue_work`/`INIT_WORK` in `dock.c` (grep empty).
- Teardown wait `acpi_os_wait_events_complete` (`osl.c:1164-1174`) flushes `kacpid_wq`+`kacpi_notify_wq` only (not `kacpi_hotplug_wq`) — called from `acpi_remove_notify_handler` and again from `acpi_dev_remove_notify_handler` (`bus.c:679`).

#### 10. Stale-plan claim verification
- (a) Confirmed — `drivers/acpi/acpica/exoparg2.c:55-107`, case `AML_NOTIFY_OP` `:68`, call to `acpi_ev_queue_notify_request` at `:96`; reached via dispatch table `acpica/dswexec.c:29-40`.
- (b) Confirmed — `evmisc.c:89-93` routes by `notify_value<=ACPI_MAX_SYS_NOTIFY` into `ACPI_SYSTEM_HANDLER_LIST`/`ACPI_DEVICE_HANDLER_LIST` (`actypes.h:809-810`); `evxface.c` install/remove mirror the split via handler_type bitmask.
- (c) Confirmed exactly — `drivers/acpi/bus.c:658`.
- (d) Confirmed — `evmisc.c:141` `acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_ev_notify_dispatch, info)`.
- (e) Confirmed — `scan.c:422-440`: BUS_CHECK→`acpi_scan_bus_check`(`:415`), DEVICE_CHECK→`acpi_scan_device_check`(`:387`).
- (f) Confirmed-with-caveat — `hotplug_event` exists exactly as named (`acpiphp_glue.c:783-835`), but the registered `acpi_hp_notify` callback is `acpiphp_hotplug_notify` (`:837-846`), which internally calls `hotplug_event()`.
- (g) Confirmed-with-caveat — `acpi_pm_notify_handler` (`drivers/acpi/device_pm.c:529-557`) gates on `ACPI_NOTIFY_DEVICE_WAKE`, installed via `acpi_add_pm_notifier` (`device_pm.c:570-598`, registers `ACPI_SYSTEM_NOTIFY` since 0x02≤0x7F); but it calls `pm_wakeup_ws_event()`, not `acpi_pm_wakeup_event()` — the latter (`device_pm.c:523-526`) is a sibling helper called from battery/button/lid/chromeos_tbmc, not from this handler.
- (h) Confirmed-with-caveat — `acpi_generic_hotplug_event` (`scan.c:422-440`) handles eject with `_EJ0`(`acpi_evaluate_ej0` inside `acpi_scan_hot_remove` `scan.c:323-369`) and `_OST`; the "gate" is the inline field check `adev->handler->hotplug.enabled` (`scan.c:430-433`), not a call to `acpi_scan_hotplug_enabled` — that symbol (`scan.c:1995-2005`) is only the sysfs setter for the same field.
- (i) Confirmed-with-caveat — boundary values match kernel constants (`ACPI_GENERIC_NOTIFY_MAX`0x0F `actypes.h:632`, `ACPI_SPECIFIC_NOTIFY_MAX`0x84 `actypes.h:633`, `ACPI_MAX_DEVICE_SPECIFIC_NOTIFY`0xBF `actypes.h:807`), but real system/device routing splits at 0x7F (`ACPI_MAX_SYS_NOTIFY`), and the kernel's own name for 0xC0-0xFF is "Hardware-Specific" (`utdecode.c:504-506`), never "OEM".

### Area C: namespace, handles, data types, evaluation — COMPLETE (recorded 2026-07-19)

#### 1. Core structs
- struct acpi_namespace_node — `drivers/acpi/acpica/aclocal.h:133-156`. Groups: payload (`object` ptr to union acpi_operand_object), shared-layout tag (`descriptor_type`+`type`, must align with the union below), name (`union acpi_name_union name`, 4 chars), tree linkage (`parent`/`child`/`peer`), lifecycle (`owner_id` for bulk delete on table unload), debugger-only fields gated by `ACPI_LARGE_NAMESPACE_NODE`. `acpi_handle` is `void *` (`include/acpi/actypes.h:424`) that literally IS a node pointer: `acpi_ns_validate_handle` (`drivers/acpi/acpica/nsutils.c:528-546`, called from every nsxf*.c entry point) special-cases NULL/`ACPI_ROOT_OBJECT`→`acpi_gbl_root_node`, else checks `ACPI_GET_DESCRIPTOR_TYPE(handle)==ACPI_DESC_TYPE_NAMED` and `ACPI_CAST_PTR`s it.
- union acpi_operand_object — `drivers/acpi/acpica/acobject.h:404-437`: giant tagged union (~24 arms) sharing `ACPI_OBJECT_COMMON_HEADER` (`next_object`/`descriptor_type`/`type`/`reference_count`/`flags`, acobject.h:46-51) and embedding `struct acpi_namespace_node node` (:436) so handle/object code paths converge; discriminated from a node via `ACPI_DESC_TYPE_OPERAND`(0x0E) vs `ACPI_DESC_TYPE_NAMED`(0x0F) (acobject.h:460-461, `union acpi_descriptor` at :469-474).
- union acpi_object `include/acpi/actypes.h:908-951` (external ABI shape: type tag + integer/string/buffer/package/reference/processor/power_resource payload) + struct acpi_object_list `actypes.h:956-959` (count + `union acpi_object *pointer`, caller-allocated args, no ownership transfer) + struct acpi_buffer `actypes.h:978-981` (length+pointer). Ownership: `ACPI_ALLOCATE_BUFFER` sentinel `actypes.h:973` (`(acpi_size)(-1)`) in `buffer.length` tells ACPICA to allocate the return; caller frees via `ACPI_FREE()`→`acpi_os_free()` (`actypes.h:350`), e.g. `drivers/acpi/utils.c:336,390,524,840`.
- struct acpi_device `include/acpi/acpi_bus.h:471-497`. Identity: `handle` (:474, comment "no handle for fixed hardware"), `pnp` (bus_id/_UID/_HID+_CID list, :251-260), `pld_crc`. Hierarchy: embedded `struct device dev` (:491) whose `dev.parent` is derived from `acpi_find_parent_acpi_dev()` in `acpi_init_device_object` (`drivers/acpi/scan.c:1807-1812`); plus `wakeup_list`/`del_list`/`physical_node_list`+`physical_node_lock` (glue.c domain). Status/flags: `acpi_device_status` (:192-199) / `acpi_device_flags` (:203-219). Power/wakeup: `acpi_device_power`/`acpi_device_wakeup`.
- fwnode embedding: `struct fwnode_handle fwnode;` is embedded by value, not a pointer (`acpi_bus.h:475`); `acpi_fwnode_handle()` (`acpi_bus.h:556-559`) just returns `&adev->fwnode`.

#### 2. API families
- Handle lookup: `acpi_get_handle` `drivers/acpi/acpica/nsxfname.c:46`; `acpi_get_parent` `nsxfobj.c:83`; `acpi_get_next_object` `nsxfobj.c:149`; `acpi_get_type` `nsxfobj.c:31`; `acpi_get_name`/`acpi_get_object_info` `nsxfname.c:124,226`.
- Namespace walking: `acpi_walk_namespace` `nsxfeval.c:554` (locks `acpi_gbl_namespace_rw_lock` reader + `ACPI_MTX_NAMESPACE`) → `acpi_ns_walk_namespace` `drivers/acpi/acpica/nswalk.c:150`. `acpi_get_devices` `nsxfeval.c:771` is a device-type-filtering wrapper (`_STA`-gated) over the same primitive. Linux side: `acpi_bus_scan` `drivers/acpi/scan.c:2721` drives `acpi_walk_namespace` with `acpi_bus_check_add_1`; `acpi_dev_for_each_child`/`_reverse` `drivers/acpi/bus.c:1200,1211` (decl `acpi_bus.h:597,599`) instead walk the Linux device model via `device_for_each_child()`, not AML namespace — a distinct, non-ACPICA traversal.
- Evaluation: `acpi_evaluate_object` `nsxfeval.c:163`; `acpi_evaluate_object_typed` `nsxfeval.c:44` (enforces `return_type`, frees ACPI_ALLOCATE_BUFFER'd buffer on mismatch, :108-134).
- `drivers/acpi/utils.c` helper family: `acpi_evaluate_integer` :247, `acpi_evaluate_reference` :343 (returns `struct acpi_handle_list`, decl `acpi_bus.h:20-23`), `acpi_execute_simple_method` :676, `acpi_has_method` :668, `acpi_evaluate_ost` :541, `acpi_evaluate_reg` :740, `acpi_evaluate_dsm` :771 → _DSM is owned by this same file (`drivers/acpi/utils.c`, not property.c), `acpi_check_dsm` :821.
- Handle↔device mapping: `acpi_fetch_acpi_dev` `drivers/acpi/scan.c:655` (no refcount) / `acpi_get_acpi_dev` `scan.c:677` (refcounted, pairs with `acpi_dev_put`), both via internal `handle_to_device()` `scan.c:633` → `acpi_get_data_full` (attached namespace-node data). `acpi_bus_get_device` is fully absent at v7.0 (0 hits tree-wide). `ACPI_COMPANION`/`ACPI_HANDLE`/`ACPI_HANDLE_FWNODE` macros `include/linux/acpi.h:58-63`; `acpi_bind_one`/`acpi_unbind_one` `drivers/acpi/glue.c:228,319`.
- Status handling: `ACPI_SUCCESS`/`ACPI_FAILURE` `include/acpi/acexcep.h:57-58`; `acpi_format_exception` `drivers/acpi/acpica/utexcep.c:30` (→`acpi_ut_validate_exception` :65, table-class dispatch on `AE_CODE_MASK`).

#### 3. Lifecycle and locking
- Namespace lock: `ACPI_MTX_NAMESPACE`=1 `drivers/acpi/acpica/aclocal.h:47`, acquired via `acpi_ut_acquire_mutex` `drivers/acpi/acpica/utmutex.c:187`. Second tier: `acpi_gbl_namespace_rw_lock` (created `utmutex.c:74`) — reader taken by `acpi_walk_namespace` (`nsxfeval.c:583-615`) so long walks can't race a table-unload writer (`drivers/acpi/acpica/tbdata.c:777-783`, guarding `acpi_ns_delete_namespace_by_owner`).
- Namespace build/mutate: table load happens in `acpi_bus_init` (`drivers/acpi/bus.c:1390`) via `acpi_load_tables()`→…→`acpi_ns_load_table` (`drivers/acpi/acpica/nsload.c:41`, parses AML into nodes under the namespace mutex); device population happens separately in `acpi_scan_init` (`drivers/acpi/scan.c:2819`) → `acpi_bus_scan(ACPI_ROOT_OBJECT)` (`scan.c:2869`), invoked from `subsys_initcall(acpi_init)` (`bus.c:1534`→1493).
- struct acpi_device creation→registration→release: `acpi_add_single_object` `scan.c:1859` → `acpi_init_device_object` `scan.c:1804` (sets `dev.parent`, `fwnode_init`, `device_initialize`) → `acpi_tie_acpi_dev` `scan.c:710` (attaches device to the NS node via `acpi_attach_data`) → `acpi_device_add` `scan.c:738` (`device_add(&device->dev)` :793) → `acpi_device_add_finalize` `scan.c:1847`. Teardown: `acpi_device_del` `scan.c:527` (`device_del`), `acpi_device_release` `scan.c:517` (dev `.release`, frees props/pnp/power lists then `kfree`).
- Refcounting: `acpi_dev_get`/`acpi_dev_put` (`acpi_bus.h:976,981`) just wrap `get_device`/`put_device` on the embedded `dev` — standard driver-core kobject refcount, no separate atomic/kref field.

#### 4. Hard-coded limits
- `ACPI_NAMESEG_SIZE`=4 `include/acpi/actypes.h:378` (used directly in `drivers/acpi/acpica/nsaccess.c:717`); `ACPI_PATH_SEGMENT_LENGTH`=5 `actypes.h:379` (4+separator). No fixed max path length — computed dynamically as `ACPI_NAMESEG_SIZE * num_segments` (`drivers/acpi/acpica/nsutils.c:181`).
- `ACPI_METHOD_NUM_ARGS`=7 `include/acpi/acconfig.h:128`, enforced in `acpi_evaluate_object` (`nsxfeval.c:233-240`, excess args warned+truncated).
- Object-type counts: `ACPI_TYPE_EXTERNAL_MAX`=0x10, `ACPI_NUM_TYPES`=17 (`actypes.h:664-665`); `ACPI_TYPE_NS_NODE_MAX`=0x1B, `ACPI_TOTAL_TYPES`=28 (:687-688); `ACPI_TYPE_INVALID`=0x1E, `ACPI_NUM_NS_TYPES`=31 (:701,704).
- Buffer sentinel: `ACPI_ALLOCATE_BUFFER`=`(acpi_size)(-1)` `actypes.h:973` (non-`ACPI_NO_MEM_ALLOCATIONS` build); `ACPI_ALLOCATE_LOCAL_BUFFER`=-2 (:974, internal only).
- `ACPI_MAX_STRING`=80 exists only at `include/acpi/acpi_drivers.h:12` and is unused anywhere in the tree — dead/vestigial, not part of this area's real limits.
- `ACPI_OWNER_ID_MAX`=0xFFF (4095) `actypes.h:446`.

#### 5. Version-specific facts (v7.0 vs older)
- `acpi_bus_get_device()` is completely gone (0 hits); replaced by `acpi_fetch_acpi_dev()`, introduced v5.17 (`e3c963c49887`), old API eliminated in v5.18 (`ac2a3feefad5`).
- `acpi_bus_get_acpi_device()`/`acpi_bus_put_acpi_device()` (old refcounted lookup) were renamed to `acpi_get_acpi_dev()`/`acpi_dev_put()` in v6.1 (`45e9aa1fdbb2`) — both names now live at `include/acpi/acpi_bus.h:987-988`.
- `acpi_evaluation_failure_warn()` (`drivers/acpi/utils.c:653-659`) is a helper added 2021, present and load-bearing at v7.0.
- Minor v7.0-local churn: `acpi_add_single_object`/`acpi_device_add` now use `kzalloc_obj(...)`-style typed allocators (`scan.c:761,866`) instead of `kzalloc(sizeof(*x), GFP_KERNEL)`, from a tree-wide allocator-macro conversion landed in this v7.0 cycle.

#### 6. Suggested page topics
- acpi_status/error-model page — justify: dedicated header `acexcep.h`, exception-class dispatch (`utexcep.c:30-123`), and ACPI_ERROR/ACPI_EXCEPTION are the single heaviest diagnostic idiom across every ns file. Accept.
- namespace-walk page — justify: `acpi_walk_namespace`/`acpi_ns_walk_namespace` implement a non-trivial lock-drop-per-callback DFS (`nswalk.c:221-255`) genuinely distinct from simple handle lookup, plus the Linux-side split between AML-walk (`acpi_bus_scan`) vs device-model-walk (`acpi_dev_for_each_child`) is a common confusion worth its own page. Accept.
- companion/glue page — justify: `acpi_bind_one`/`acpi_unbind_one` (`glue.c:228-350`), multi-physical-node-per-device model, sysfs `firmware_node`/`physical_node` links, `ACPI_COMPANION_SET`. Enough independent material from the `acpi_device` struct page. Accept.
- operand-object internals page — reject as a standalone page: `union acpi_operand_object` (`acobject.h:404-437`) is ACPICA-interpreter-internal plumbing with no Linux driver-facing API; only surfaces transiently in `acpi_ns_resolve_references` (`nsxfeval.c:472-518`) before conversion to `union acpi_object`. Fold as a footnote into the data-types page instead.
- Extra suggestions not listed: device lifecycle/refcounting page, justified by the async-delete quirk at `acpi_scan_drop_device` (`scan.c:606-629`, deferred to avoid deadlocking under ACPICA's namespace mutex) plus the full add/del chain in item 3 — meatier than a subsection. Table-load/namespace-mutation page, justified by `acpi_ns_load_table` (`nsload.c:41`), `acpi_tb_notify_table` (`tbdata.c:1089`), and the deferred rescan `acpi_scan_table_notify`→workqueue (`scan.c:2930-2952`) — currently nothing in the planned 6 pages covers when the namespace changes after boot.

#### 7. Tracepoints
- Negative finding: no `TRACE_EVENT`/`DECLARE_EVENT_CLASS` anywhere under `drivers/acpi/` (`grep -rl TRACE_EVENT drivers/acpi/` → empty) and no `trace_*()` call sites in any of the ns/scan/bus/glue/utils/property files searched. This area has zero ftrace tracepoint instrumentation; all "tracing" is ACPICA's own `ACPI_FUNCTION_TRACE`/`ACPI_DEBUG_PRINT` entry-exit logging (see item 8), not kernel tracepoints.

#### 8. Debug and diagnostic printing
- ACPICA layer, per-file counts of `ACPI_DEBUG_PRINT`/`ACPI_ERROR`/`ACPI_WARNING`/`ACPI_FUNCTION_TRACE`: `nsaccess.c` 11/4/1/2 (heaviest hitter — lookup hot path, e.g. `nsaccess.c:67,127,224,331,436,696`); `nsxfeval.c` 3/3/2/4 (`:100,114,210,213,234,283,293,343,407`); `nswalk.c` 0/0/0/1+2 `ACPI_FUNCTION_ENTRY`; `nsxfname.c`/`nsxfobj.c` 0 across the board (thin validation wrappers). Layer/component constants: `ACPI_NAMESPACE`=0x10, `ACPI_UTILITIES`=0x1 (`include/acpi/acoutput.h:21,25`), levels `ACPI_DB_INFO`/`ACPI_DB_NAMES` (:117,130).
- Linux side, `acpi_handle_{debug,err,warn,info}` macros (`include/linux/acpi.h:1254-1285`, built on `acpi_handle_printk`→`acpi_handle_path`, `drivers/acpi/utils.c:571-612`) counts: `bus.c` 15 debug/5 err; `utils.c` 6 debug/7 warn (incl. `acpi_evaluation_failure_warn` :653-659, the canonical "log + acpi_format_exception" helper); `scan.c` 7 debug/5 warn/2 info; `property.c` 5 debug/4 warn; `glue.c` 1 debug. Load-bearing site: `acpi_util_eval_error` (`utils.c:26-29`) is the single choke point most `utils.c` helpers funnel failures through.

#### 9. Asynchronous/deferred/lazy processing
- Evaluation is fully synchronous in caller context: `acpi_evaluate_object`→`acpi_ns_evaluate` (`drivers/acpi/acpica/nseval.c:42`) runs the AML interpreter inline; no `schedule_work`/`queue_work`/`kthread` anywhere in `nseval.c`, `psparse.c`, or any of the nsxf*/nsaccess/nswalk files (grep confirms zero).
- Deferred `acpi_device` teardown: `acpi_scan_drop_device` (`scan.c:606-629`) is invoked synchronously from ACPICA's `acpi_ns_delete_node`, but explicitly defers `acpi_device_del()` to the ordered ACPI hotplug workqueue (`acpi_device_del_work_fn`, `scan.c:563-591`) "to avoid running acpi_device_del() under the ACPICA's namespace mutex."
- Deferred namespace rescan on table load: `acpi_tb_notify_table(ACPI_TABLE_EVENT_LOAD,...)` (`tbdata.c:980,1089`) synchronously calls `acpi_bus_table_handler` (`bus.c:1382-1388`) → `acpi_scan_table_notify()` (`scan.c:2939-2952`), which `schedule_work()`s `acpi_table_events_fn` (`scan.c:2930-2937`) to re-run `acpi_bus_scan(ACPI_ROOT_OBJECT)` off the table-load call stack.

#### 10. Stale-plan claim verification
- (a) Confirmed — `acpi_get_handle` `nsxfname.c:46`, `acpi_walk_namespace` `nsxfeval.c:554`; caveat: `acpi_get_parent`/`acpi_get_next_object` (`nsxfobj.c:83,149`) and `acpi_get_devices`/`acpi_dev_for_each_child` round out a larger lookup/walk family.
- (b) Confirmed-with-caveat — `ACPI_ROOT_OBJECT` `actypes.h:458` is a sentinel pointer value (`ACPI_TO_POINTER(ACPI_MAX_PTR)`), not literally `&acpi_gbl_root_node`; every consumer (`nsutils.c:535`, `nsxfobj.c:44,95`, `nswalk.c:170`) special-cases it before resolving to the real root node.
- (c) Confirmed — `scan.c:655-658`.
- (d) Confirmed — `linux/acpi.h:58,61`; `ACPI_COMPANION` expands to `to_acpi_device_node((dev)->fwnode)` (`acpi_bus.h:523-531`), which calls `is_acpi_device_node` (`property.c:1771-1776`).
- (e) Confirmed — signature at `nsxfeval.c:163-166`; `ACPI_ALLOCATE_BUFFER` checked `nsxfeval.c:63` / defined `actypes.h:973`; caller-owned free demonstrated repeatedly in `utils.c` (kfree/ACPI_FREE, both ultimately `acpi_os_free`→kfree).
- (f) Confirmed — `nsxfeval.c:44-139`, type mismatch → `AE_TYPE` + conditional buffer free.
- (g) Confirmed — `acexcep.h:57-58,60`; `utexcep.c:30-48`.
- (h) Confirmed — all six present in `drivers/acpi/utils.c`: `acpi_evaluate_integer` :247, `acpi_evaluate_reference` :343, `acpi_execute_simple_method` :676, `acpi_has_method` :668, `acpi_evaluate_ost` :541, `acpi_evaluate_reg` :740.

### Area D: enumeration, identification, configuration, resources — COMPLETE (recorded 2026-07-19)

#### 1. Core structs
- `struct acpi_device_pnp` — include/acpi/acpi_bus.h:251-259. Per-device cached identity: `bus_id[8]`, `instance_no`, `acpi_pnp_type` bitfield (acpi_bus.h:243-249), `bus_address` (_ADR), `unique_id` (_UID), `ids` list (_HID+_CID), `device_name`/`device_class`.
- `struct acpi_hardware_id` — acpi_bus.h:238-241. One linked-list node (`{list, const char *id}`) per _HID/_CID string, hung off `pnp.ids`.
- `struct acpi_device_id` — include/linux/mod_devicetable.h:217-222 (`ACPI_ID_LEN`=16 at :215). `{id[16], driver_data, cls, cls_msk}`; match contract: string `strcmp` OR PCI-class `cls`/`cls_msk` match; array terminated by an `id[0]==0 && cls==0` sentinel entry (enforced in the match loop, bus.c:952).
- `struct acpi_resource` — include/acpi/acrestyp.h:678-682. Common `{type, length, union acpi_resource_data data}` descriptor record.
- `union acpi_resource_data` — acrestyp.h:639-677. Master union of all payload types (irq/dma/memory/io/address/gpio/serialbus/pin*/clock_input/common address).
- `ACPI_RESOURCE_TYPE_*` set — acrestyp.h:609-635 (26 values, `ACPI_RESOURCE_TYPE_MAX`=25): IRQ(0), DMA(1), START_DEPENDENT(2), END_DEPENDENT(3), IO(4), FIXED_IO(5), VENDOR(6), END_TAG(7), MEMORY24(8), MEMORY32(9), FIXED_MEMORY32(10), ADDRESS16(11), ADDRESS32(12), ADDRESS64(13), EXTENDED_ADDRESS64(14), EXTENDED_IRQ(15), GENERIC_REGISTER(16), GPIO(17), FIXED_DMA(18), SERIAL_BUS(19), PIN_FUNCTION(20), PIN_CONFIG(21), PIN_GROUP(22), PIN_GROUP_FUNCTION(23), PIN_GROUP_CONFIG(24), CLOCK_INPUT(25).
- `struct resource_win` — include/linux/resource_ext.h:14-17. `{struct resource res; resource_size_t offset}`; load-bearing in `acpi_dev_resource_address_space`/`acpi_dev_resource_ext_address_space` (resource.c:290,319) and `acpi_dev_process_resource` (resource.c:908-945) for bridge-window translation.
- `struct acpi_resource_gpio` — acrestyp.h:355-371. GpioIo/GpioInt payload (pin table, triggering/polarity/drive_strength/debounce); load-bearing for drivers/gpio/gpiolib-acpi-core.c GPIO decode.
- `struct acpi_device_data` — acpi_bus.h:369-374. _DSD storage: `{pointer, properties list, of_compatible, subnodes list}`.
- `struct acpi_data_node` — acpi_bus.h:500-508. Non-device _DSD subnode: `acpi_device_data` + `fwnode_handle` + `kobject` + `kobj_done` completion.

#### 2. API families
- Identification executors (all in drivers/acpi/acpica/utids.c, header explicitly says "HID, UID, CID, SUB, CLS"):
  - `acpi_ut_execute_HID` utids.c:35-92, `acpi_ut_execute_UID` utids.c:113-170, `acpi_ut_execute_CID` utids.c:196-313, `acpi_ut_execute_CLS` utids.c:335-402 — each runs one control method, marshals into `struct acpi_pnp_device_id(_list)`.
  - Real call path: all four are invoked only from `acpi_get_object_info()` (drivers/acpi/acpica/nsxfname.c:226-457, calls at :288/296/304/317), which ORs `ACPI_VALID_{HID,UID,CID,CLS}` (include/acpi/actypes.h:1203-1207) into `info->valid`. `acpi_set_pnp_ids` (drivers/acpi/scan.c:1388-1473) calls `acpi_get_object_info` once and tests `info->valid` at scan.c:1408/1412/1417/1421/1424 — scan.c never calls `acpi_ut_execute_*` directly.
  - Also reused internally by acpica/nsxfeval.c:679/694 (HID/CID filter for `acpi_get_devices`) and acpica/evrgnini.c:323/337 (PCI-root-bridge detection for opregion setup).
  - `acpi_set_pnp_ids` scan.c:1388-1473 / `acpi_add_id` scan.c:1329-1345 — build `pnp.ids` list, add synthetic HIDs (video/bay/dock/IBM-SMBus/LNXSYBUS) when firmware IDs are absent.
- _STA (status): `acpi_bus_get_status` bus.c:95-135 → `acpi_bus_get_status_handle` bus.c:77-92 (defaults to PRESENT|ENABLED|UI|FUNCTIONING, `ACPI_STA_*` actypes.h:1212-1217, when `_STA` absent). Real override quirks: `acpi_device_override_status` drivers/acpi/x86/utils.c:180 (generic stub acpi_bus.h:767-771). Gating consumers: `__acpi_match_device` bus.c:936-976 (`!device->status.present` → no match), `acpi_bus_attach` scan.c:2348-2355 (re-runs `_STA` and bails via `acpi_dev_ready_for_enumeration`).
- _ADR: accessor is the macro `acpi_device_adr(d)` = `(d)->pnp.bus_address` (acpi_bus.h:263), populated via `acpi_ut_evaluate_numeric_object(METHOD_NAME__ADR,...)` inside `acpi_get_object_info`. `acpi_find_child_device` glue.c:205-209 → `acpi_find_child` glue.c:187-203 → `check_one_child` glue.c:136-179 compares `acpi_device_adr(adev)==address`. PCI dev/fn encoding caller: `acpi_pci_find_companion` drivers/pci/pci-acpi.c:1318-1345, `addr=(PCI_SLOT(devfn)<<16)|PCI_FUNC(devfn)` at :1340.
- Resource walking: acpica core `acpi_walk_resources` acpica/rsxface.c:593-628 (buffer via `acpi_rs_get_method_data` then `acpi_walk_resource_buffer` rsxface.c:505-570); `acpi_get_current_resources` rsxface.c:166-184 (_CRS), `acpi_get_possible_resources` rsxface.c:208-226 (_PRS), `acpi_set_current_resources` rsxface.c:247-271 (_SRS). Linux glue: `acpi_dev_get_resources` resource.c:1000-1006 → `__acpi_dev_get_resources` resource.c:947-974 → `acpi_walk_resources(...,"_CRS",acpi_dev_process_resource,...)` at :966. Per-type converters: `acpi_dev_resource_memory` resource.c:107-138, `acpi_dev_resource_io` resource.c:180-204, `acpi_dev_resource_address_space` resource.c:290-302, `acpi_dev_resource_ext_address_space` resource.c:319-333, `acpi_dev_resource_interrupt` resource.c:828-870. AML⇄struct bridge: `acpi_rs_convert_aml_to_resources` acpica/rslist.c:29 (forward), `acpi_rs_create_resource_list` acpica/rscreate.c:102 (wraps it), `acpi_rs_create_aml_resources` acpica/rscreate.c:403 (reverse, for _SRS).
- _SRS: `acpi_set_current_resources` rsxface.c:247-271 → `acpi_rs_set_srs_method_data` acpica/rsutils.c:690 (builds AML via `acpi_rs_create_aml_resources`, invokes `_SRS`). Caller: `pnpacpi_set_resources` drivers/pnp/pnpacpi/core.c:49-88 (gated on `acpi_has_method(handle,"_SRS")` :67; template via `pnpacpi_build_resource_template` rsparser.c:622-657 + `pnpacpi_encode_resources` rsparser.c:877; `acpi_set_current_resources` call at core.c:78).
- _DSM: `acpi_evaluate_dsm` drivers/acpi/utils.c:771-807 (4-arg call: 16-byte guid buffer, `rev` u64, `func` u64, `argv4`); `acpi_evaluate_dsm_typed` acpi_bus.h:64-77 (type-checked wrapper); `acpi_check_dsm` utils.c:821-850 (function-0 bitmap query, up to 64 functions per doc comment). Vendor-neutral caller: `pci_acpi_dsm_guid` drivers/pci/pci-acpi.c:30-32, used at :136, :1233-1234 (rev 3, `DSM_PCI_POWER_ON_RESET_DELAY`), :1394.
- _DSD: `acpi_init_properties` property.c:585-638 → `acpi_evaluate_object_typed(...,"_DSD",...)` at :609 → `acpi_extract_properties` property.c:537, `acpi_enumerate_nondev_subnodes` property.c:257, `acpi_init_of_compatible` property.c:342 (PRP0001 path), `acpi_tie_nondev_subnodes`/`acpi_untie_nondev_subnodes` property.c:415/401. `acpi_dev_get_property` property.c:748-752 → `acpi_data_get_property` property.c:701 → `device_property_*` bridge via `acpi_device_fwnode_ops`/`acpi_data_fwnode_ops` (property.c:1767-1768, built by `DECLARE_ACPI_FWNODE_OPS` macro :1738-1765), consumed generically by drivers/base/property.c:44+. GUID ABI: 6 "properties" GUIDs in `prp_guids[]` (property.c:40-59), `ads_guid` subnode GUID (:61-64), `buffer_prop_guid` (:66-69). PRP0001=`ACPI_DT_NAMESPACE_HID` drivers/acpi/internal.h:303.
- Default enumeration: `acpi_default_enumeration` scan.c:2245-2282 (system-dev deferral / video-bus / `acpi_create_platform_device`); `acpi_create_platform_device` drivers/acpi/acpi_platform.c:110-195 (`forbidden_id_list` :26-34); `acpi_is_pnp_device` drivers/acpi/acpi_pnp.c:374-378. Callers: `acpi_bus_attach` scan.c:2336(→2386-2388), `acpi_generic_device_attach` scan.c:2289 (PRP0001 path), `acpi_bus_add_fixed_device_object` scan.c:2783, `acpi_bus_register_early_device` scan.c:2769.

#### 3. Lifecycle and locking
- `acpi_add_single_object` scan.c:1859-1916 order: (1) `acpi_init_device_object` scan.c:1804-1828 → `acpi_set_device_status(ACPI_STA_DEFAULT)`, `acpi_device_get_busid` scan.c:1163-1202 (bus_id local buf is `char[4+nul]`, struct field is `char[8]`), `acpi_set_pnp_ids` (_HID/_CID/_UID/_CLS/_ADR), `acpi_init_properties` (_DSD), `acpi_bus_get_flags`; (2) if `dep_init`, `acpi_scan_dep_init` scan.c:1832-1845 under `acpi_dep_list_lock` sets `dep_unmet`/`honor_deps`; (3) `acpi_scan_init_status` scan.c:1853-1857 → `acpi_bus_get_status` (_STA; battery devices short-circuited to status=0 while `dep_unmet`, bus.c:~108); (4) power/wakeup flags → `acpi_tie_acpi_dev` → `acpi_device_add` → `acpi_device_add_finalize` (KOBJ_ADD uevent).
- Cached vs re-evaluated: `pnp.ids`/_DSD/_ADR/_UID evaluated once at object creation, cached in `device->pnp`/`device->data` for the device's life. `_STA` is re-evaluated every `acpi_bus_attach()` pass (scan.c:2348) — first pass, second (postponed) pass, and any later reprobe. sysfs `cid` attribute independently re-evaluates _HID/_UID/_CID/_CLS live via `acpi_get_object_info` at read time (device_sysfs.c:406-430); `hid`/`uid`/`adr` sysfs attrs read the cached pnp fields (device_sysfs.c:397-404,433-452).
- Resource buffers: `_CRS`/`_PRS` always re-evaluated per call (`ACPI_ALLOCATE_LOCAL_BUFFER`, freed inside `acpi_walk_resources` itself, rsxface.c:615-624); callers of `acpi_dev_get_resources` own only the post-conversion `resource_entry` list, freed via `acpi_dev_free_resource_list` resource.c:877-880. `_SRS` buffer is caller-allocated/freed (`pnpacpi_build_resource_template`/`kfree(buffer.pointer)`, core.c:70-82).

#### 4. Hard-coded limits
- `ACPI_ID_LEN`=16 mod_devicetable.h:215; `PNP_ID_LEN`=8, `PNP_MAX_DEVICES`=8 mod_devicetable.h:237-238.
- `acpi_bus_id` = `char[8]` acpi_bus.h:233 (raw ACPI object names are 4 chars).
- `ACPI_EISAID_STRING_SIZE`=8 actypes.h:1153, `ACPI_PCICLS_STRING_SIZE`=7 actypes.h:1161, `ACPI_MAX64_DECIMAL_DIGITS`=20 actypes.h:450 — size HID/CLS/UID string buffers utids.c allocates.
- `ACPI_MAX_SUB_BUF_SIZE`=9 drivers/acpi/utils.c:303 bounds `_SUB`; no `ACPI_MAX_CID` exists anywhere in-tree (grep-confirmed) — CID list is a dynamic linked list, size unbounded.
- `ACPI_RS_SIZE_NO_DATA`=8, `ACPI_RS_SIZE_MIN`, `ACPI_RS_SIZE(type)` macros acrestyp.h:688-690; `ACPI_RESOURCE_TYPE_MAX`=25 acrestyp.h:635 is the sanity bound `acpi_walk_resource_buffer` checks (rsxface.c:534).
- PNP ID format: `ispnpidacpi()` drivers/pnp/pnpacpi/core.c:29-41 — 3 uppercase letters + 4 hex digits + NUL (7 chars).
- `_DSM` ABI: fixed 4-arg call (16-byte guid, rev u64, func u64, argv4) utils.c:771-807; `acpi_check_dsm` caps at 64 requestable functions (u64 bitmap) utils.c:821-830.

#### 5. Version-specific facts
- `acpi_get_object_info()` explicitly dropped `_STA` support (02/2018) and `_SUB` support (11/2015) per its own comment (nsxfname.c:218-221); `ACPI_VALID_*` today has only ADR/HID/UID/CID/CLS/SXDS/SXWS bits (actypes.h:1202-1208), no STA/SUB/COMPATIBLE_IDS bit. `_SUB` is now Linux-side only via `acpi_get_subsystem_id()` (utils.c:306-340, direct `"_SUB"` evaluation).
- `_UID` matching gained a C11 `_Generic`-dispatch layer: `acpi_dev_uid_match`/`acpi_dev_hid_uid_match` (acpi_bus.h:916-939) auto-select `acpi_str_uid_match` vs `acpi_int_uid_match` (acpi_bus.h:883-895) by argument type, layered on `acpi_dev_uid_to_integer` (utils.c:862-874) plus the long-standing `acpi_device_uid` macro (acpi_bus.h:265) — not present in older/simpler trees.
- Allocation idiom modernized: `acpi_add_id`/`acpi_scan_add_dep`/`acpi_create_platform_device` use type-inferring `kmalloc_obj`/`kzalloc_obj`/`kzalloc_objs` (include/linux/slab.h:1008-1041) instead of `kmalloc(sizeof(*x), GFP_KERNEL)`.
- `acpi_find_child_by_adr` glue.c:212-217 is a newer sibling of `acpi_find_child_device` that skips the `_STA` check (`check_sta=false`).

#### 6. Suggested extra page topics
1. Modalias/driver-match — `__acpi_match_device` bus.c:936-976, `acpi_bus_match` bus.c:1101-1108, `acpi_driver_match_device` bus.c:1044-1054 (shared by platform/i2c/spi/serdev/cpu match ops), `create_pnp_modalias`/`create_of_modalias` device_sysfs.c:136-238. All ID machinery converges here for actual driver binding across 5+ subsystems.
2. _SUB / _HRV — `acpi_get_subsystem_id` utils.c:306-340, `_HRV` via `acpi_evaluate_integer` utils.c:929, device_sysfs.c:524/588. Real, actively-consumed id objects (5 in-tree drivers) despite no longer flowing through `acpi_get_object_info`.
3. _DEP / deferred enumeration — `acpi_scan_check_dep` scan.c:2071-2101, `acpi_scan_add_dep` scan.c:2007-2048, `acpi_scan_postponed`(+`_branch`) scan.c:2570-2624, `acpi_dev_ready_for_enumeration` scan.c:2533-2540, `acpi_dev_clear_dependencies` scan.c:2519-2523 (17 in-tree callers). A full two-pass/async subsystem, absent from the requested page list entirely.
4. acpi_platform/acpi_pnp default enumeration — already in the file list but not the page list; anchors in item 2 above.
5. GPIO/serial-bus resource specializations — `struct acpi_resource_gpio` acrestyp.h:355-371 + drivers/gpio/gpiolib-acpi-core.c; `i2c_serial_bus`/`spi_serial_bus`/`uart_serial_bus` + drivers/i2c/i2c-core-acpi.c, drivers/spi/spi.c, drivers/tty/serdev/core.c. Distinct decode path from `acpi_dev_resource_memory/io/interrupt`.
6. fwnode/device_property bridge — `acpi_device_fwnode_ops`/`acpi_data_fwnode_ops` property.c:1738-1768 + drivers/base/property.c generic callers; the mechanism non-ACPI-aware drivers actually use to read _DSD data.

#### 7. Tracepoints
- None. `grep -rn "trace_acpi\|TRACE_EVENT"` over scan.c/bus.c/resource.c/property.c/utils.c/device_sysfs.c/pnpacpi/{core,rsparser}.c/acpica/{utids,rsxface}.c returns no hits; no `include/trace/events/acpi.h` exists in the tree. Negative finding — the only "tracing" here is ACPICA's own `ACPI_FUNCTION_TRACE`/`ACPI_DEBUG_PRINT` layer (gated by `acpi_dbg_level`/`acpi_dbg_layer`), unrelated to Linux ftrace `TRACE_EVENT`.

#### 8. Debug/diagnostic printing
- Per-file call-site counts (`acpi_handle_{debug,info,warn,err}` / `pr_*` / `dev_*`): scan.c 31, bus.c 46, utils.c 28, property.c 13, resource.c 5 (`pr_debug`×3, `pr_warn`×2), device_sysfs.c 2, pnpacpi/rsparser.c 14 (`dev_err`×9, `dev_warn`×5), pnpacpi/core.c 6 (`dev_dbg`), acpi_platform.c 2, acpi_pnp.c 0, acpica/utids.c 0, acpica/rsxface.c 0. Notable sites: property parse failures `acpi_handle_warn` at property.c:455,487,498,508 (buffer-prop malformed) and :128/624 (invalid _DSD, `acpi_handle_debug`); resource validation warnings `pr_debug`/`pr_warn` resource.c:67,223,236,246 (invalid/unassigned resource, bad address-space min/max, non-CPU-addressable window) and :789 (IRQ override). ACPICA-side `ACPI_DEBUG_PRINT`/`ACPI_EXCEPTION` counts: rscreate.c 14, rslist.c 9, utids.c/rsxface.c/nsxfname.c/rsutils.c 0 (these rely solely on `ACPI_FUNCTION_TRACE` entry/exit tracing).

#### 9. Async/deferred/lazy processing
- `_DEP` is the real deferred-enumeration mechanism (no other lazy paths found for _CRS/_DSM/_DSD, which are synchronous single-evaluate calls):
  - Queue/flag: `acpi_scan_check_dep` scan.c:2071-2101 (skips PCI/USB-port nodes via `_HID` check) called from `acpi_bus_check_add` first pass scan.c:2109-2182; if deps found, returns `AE_CTRL_DEPTH` to skip the whole subtree in pass 1. `acpi_scan_add_dep` scan.c:2007-2048 records `acpi_dep_data{supplier,consumer,honor_dep}` in global `acpi_dep_list`, filtered by `acpi_ignore_dep_ids`/`acpi_honor_dep_ids` tables scan.c:848-864.
  - Second pass: `acpi_bus_scan` scan.c:2721-2753 does Pass 1 (`acpi_bus_check_add_1`) then `acpi_scan_postponed` scan.c:2589-2624 (Pass 2) → `acpi_scan_postponed_branch` scan.c:2570-2587 creates the deferred device objects (`dep_init=true` → `acpi_scan_dep_init` populates `dep_unmet`).
  - Resolution: driver calls `acpi_dev_clear_dependencies(supplier)` scan.c:2519-2523 (EXPORT_SYMBOL_GPL, 17 in-tree callers, e.g. drivers/acpi/ec.c:1745, drivers/acpi/pci_link.c:762, drivers/gpio/gpiolib-acpi-core.c:1325) → `acpi_walk_dep_device_list` → `acpi_scan_clear_dep` scan.c:2463-2479 decrements `dep_unmet`; when it hits 0, `acpi_scan_clear_dep_queue` scan.c:2438-2456 uses `async_schedule_dev_nocall(acpi_scan_clear_dep_fn,...)` (kernel/async.c-backed) → `acpi_scan_clear_dep_fn` scan.c:2427-2436 re-runs `acpi_bus_attach()` under `acpi_scan_lock`, i.e. genuinely asynchronous reprobe.
  - Consumption gate: `acpi_dev_ready_for_enumeration` scan.c:2533-2540 (`honor_deps && dep_unmet` ⇒ not ready).
  - Also deferred (not _DEP-related): `acpi_reserve_motherboard_resources` scan.c:2686-2705 is an `fs_initcall` (later than the `subsys_initcall`-level `acpi_bus_scan`), deliberately reserving `acpi_scan_system_dev_list` resources after PCI claims BARs.

#### 10. Stale-plan claim verification
- (a) Confirmed-with-caveat: `acpi_ut_execute_HID/CID/UID` exist in utids.c (35-92 / 196-313 / 113-170), but none are called directly from scan.c — only from `acpi_get_object_info()` (nsxfname.c), which scan.c calls.
- (b) Confirmed exactly: `acpi_ut_execute_CLS` is at utids.c:335 (span 335-402); gate is `ACPI_VALID_CLS` (actypes.h:1206), tested in scan.c:1424, not in utids.c itself.
- (c) Confirmed: `acpi_set_pnp_ids` scan.c:1388-1473 and `acpi_add_id` scan.c:1329-1345 build `pnp.ids`.
- (d) Confirmed: PRP0001 (`ACPI_DT_NAMESPACE_HID`, internal.h:303) enables device-property matching via `generic_device_ids`/`acpi_generic_device_attach` scan.c:2284-2298 and the OF-compatible fallback in `__acpi_match_device` bus.c:964-967.
- (e) Confirmed: `acpi_dev_uid_to_integer` utils.c:862-874 and `acpi_device_uid` macro acpi_bus.h:265 both exist.
- (f) Confirmed: `acpi_bus_get_status` bus.c:95-135 backs `_STA`; `ACPI_STA_*` actypes.h:1212-1217 gate enumeration via `acpi_dev_ready_for_enumeration`/`__acpi_match_device`/`acpi_bus_attach`.
- (g) Confirmed: `_ADR` flows through the `acpi_device_adr` macro (acpi_bus.h:263) and `acpi_find_child_device` (glue.c:205-209); PCI dev/fn encoding at drivers/pci/pci-acpi.c:1340 (`(PCI_SLOT<<16)|PCI_FUNC`).
- (h) Confirmed: `_CRS` raw buffers consumed via `acpi_walk_resources` (rsxface.c:593) and `acpi_dev_get_resources`/`__acpi_dev_get_resources` (resource.c:1000/947, calling `acpi_walk_resources` at :966).
- (i) Confirmed: `_PRS` `StartDependentFn`/`EndDependentFn` grouping consumed at `pnpacpi_option_resource` rsparser.c:471-493 (`ACPI_RESOURCE_TYPE_START/END_DEPENDENT`), driven by `pnpacpi_parse_resource_option_data` rsparser.c:550-571.
- (j) Confirmed: `_SRS` buffer construction goes through `acpi_set_current_resources` (rsxface.c:247-271) with `pnpacpi_set_resources` (pnpacpi/core.c:49-88, call at :78) as caller.
- (k) Confirmed: `acpi_evaluate_dsm`(`_typed`) and `acpi_check_dsm` implement `_DSM` with a guid/rev/func ABI (utils.c:771-850, acpi_bus.h:64-77).
- (l) Confirmed: `acpi_init_properties` and `acpi_dev_get_property` implement `_DSD` with `device_property_*` (drivers/base/property.c) as the bridge via `fwnode_operations` (property.c:1738-1768).

### Area E: device power management — COMPLETE (recorded 2026-07-19)

#### Core structs
1. `struct acpi_device_power` — include/acpi/acpi_bus.h:292-297 — top-level per-device power state: `state` (current), `flags`, `states[ACPI_D_STATE_COUNT]` (fixed array, size 5), `state_for_enumeration` (from `_DSC`).
   - `struct acpi_device_power_state` — include/acpi/acpi_bus.h:281-290 — per-D-state: `resources` list, `flags.valid`/`flags.explicit_set` (`_PSx` present), `power` (%, default -1, D0 forced 100 at drivers/acpi/scan.c:1125), `latency` (µs, default -1 at drivers/acpi/scan.c:1085). Neither `power` nor `latency` is ever read back anywhere in device_pm.c/power.c/scan.c — write-only metadata (grep-confirmed, no consumer).
   - `struct acpi_device_power_flags` — include/acpi/acpi_bus.h:271-279 — 6 bits: `explicit_get`(`_PSC`), `power_resources`, `inrush_current`(`_IRC`), `power_removed`, `ignore_parent`, `dsw_present`(`_DSW`).
2. `struct acpi_power_resource` — drivers/acpi/power.c:51-60 — Confirmed, still holds exactly as the stale plan says: embeds `struct acpi_device device`; `system_level`(u32,:54), `order`(u32,:55), `ref_count`(:56), `state`(:57), `resource_lock`(mutex,:58), `dependents`(list,:59). One struct per ACPI PowerResource object.
3. `struct acpi_device_wakeup` — include/acpi/acpi_bus.h:342-352 — `gpe_device`,`gpe_number`,`sleep_state`,`resources`,`flags`,`context`,`ws`(wakeup_source),`prepare_count`,`enable_count`.
   - `struct acpi_device_wakeup_flags` — acpi_bus.h:332-335 — `valid:1` (can enable wakeup), `notifier_present:1`.
   - `struct acpi_device_wakeup_context` — acpi_bus.h:337-340 — `func`, `dev`, invoked from `acpi_pm_notify_handler`.
4. `struct acpi_device_flags` — acpi_bus.h:203-219 — includes `power_manageable:1` (acpi_bus.h:207), the master enable bit for all D-state APIs.
5. `ACPI_STATE_D0..D3_COLD` — include/acpi/actypes.h:590-597 — `D0`=0,`D1`=1,`D2`=2,`D3_HOT`=3,`D3`=4, `D3_COLD` is a `#define` alias of `D3` (:595) — D3hot/D3cold are the same raw encoding, distinguished only by kernel-side flags/logic, not by the constant itself. `ACPI_D_STATES_MAX`=`ACPI_STATE_D3`(:596), `ACPI_D_STATE_COUNT`=5(:597).

#### API families
- Power-flag construction: `acpi_bus_get_power_flags` drivers/acpi/scan.c:1088 — gates on `_PS0`|`_PR0`→`power_manageable`; sets `explicit_get`(`_PSC`),`inrush_current`(`_IRC`),`dsw_present`(`_DSW`),`state_for_enumeration`(`_DSC`); loops D0..D3hot calling `acpi_bus_init_power_state` (scan.c:1053, evaluates `_PRx`→`acpi_extract_power_resources`, checks `_PSx`→`explicit_set`); forces D0/D3hot valid, derives `power_resources`/D3cold-valid from D0/D3hot resource-list emptiness (scan.c:1121-1141); calls `acpi_bus_init_power` (scan.c:1143). Called from `acpi_add_single_object` (scan.c:1891) and re-derived in `acpi_bus_attach` (scan.c:2362-2365).
- State read: `_PSC` via static `acpi_dev_pm_explicit_get` drivers/acpi/device_pm.c:48; `acpi_device_get_power` device_pm.c:75 (combines `acpi_power_get_inferred_state` + `_PSC`; declared only in drivers/acpi/internal.h:159, not in acpi_bus.h, and has no `EXPORT_SYMBOL`).
- State set: static `acpi_dev_pm_explicit_set` device_pm.c:141 (builds `"_PS0".."_PS3"` by char arithmetic); `acpi_device_set_power` device_pm.c:162 (`EXPORT_SYMBOL` :294) — the ordering/validation engine; `acpi_bus_set_power` device_pm.c:296 (`EXPORT_SYMBOL`); `acpi_bus_init_power`/`acpi_device_update_power` device_pm.c:307/413.
- Power resources: `acpi_extract_power_resources` power.c:152 (parses `ACPI_TYPE_LOCAL_REFERENCE` package elements from `start` into a list, dedup via `acpi_power_resource_is_dup` :135); ref-count core `__acpi_power_on`/`__acpi_power_off` (`_ON`/`_OFF`, power.c:367/426) wrapped by `acpi_power_on`/`acpi_power_off` (power.c:416/465, ref_count++/-- at :405/:454); `acpi_power_transition` power.c:852 (D-state driver: refs target-state list ON first, then derefs old-state list OFF — comment :866-870); `acpi_power_get_inferred_state` power.c:810 (`_STA`-based, via `__get_state` :192); `acpi_resume_power_resources` power.c:1031 (CONFIG_ACPI_SLEEP, confirmed present, re-ONs any resource that's OFF-but-referenced after resume); `acpi_turn_off_unused_power_resources` power.c:1135 (OFFs any resource that's ON-but-unreferenced).
- Wakeup: `_PRW` parsed by `acpi_bus_extract_wakeup_device_power_package` scan.c:922 (gpe_device/gpe_number, sleep_state, resources via `acpi_extract_power_resources(pkg,2,...)`); `acpi_wakeup_gpe_init` scan.c:1003 calls `acpi_setup_gpe_for_wake` (drivers/acpi/acpica/evxfgpe.c:352); `acpi_bus_get_wakeup_device_flags` scan.c:1025 orchestrates and sets `wakeup.flags.valid`; `acpi_pm_set_device_wakeup` device_pm.c:948 (confirmed, exact v7.0 name, `EXPORT_SYMBOL_GPL`) toggles via `__acpi_device_wakeup_enable`/`acpi_device_wakeup_disable` (device_pm.c:848/925); notify chain `acpi_pm_notify_handler` device_pm.c:529 → `acpi_pm_wakeup_event` device_pm.c:523 (`pm_wakeup_dev_event`) and/or `context.func` (typically `acpi_pm_notify_work_func` device_pm.c:836 → `pm_wakeup_event`+`pm_request_resume`).
- PM-domain glue: `acpi_dev_pm_attach` device_pm.c:1443 (`EXPORT_SYMBOL_GPL` :1476, called only from `dev_pm_domain_attach` drivers/base/power/common.c:103,110); `acpi_general_pm_domain` device_pm.c:1370 — confirmed exact name, `static struct dev_pm_domain`, not exported, `.detach=acpi_dev_pm_detach` set in the initializer itself (:1390); `acpi_subsys_*` family device_pm.c:1067-1366 (runtime_suspend/resume, prepare/complete, suspend/suspend_late/suspend_noirq, resume/resume_early/resume_noirq, freeze/restore_early, poweroff family) wrapping `pm_generic_*`.

#### Lifecycle & locking
- Global list `acpi_power_resource_list` (power.c:70) + `power_resource_list_lock` mutex (power.c:71) — all PowerResource objects system-wide; walked by `acpi_resume_power_resources`/`acpi_turn_off_unused_power_resources`.
- Per-resource `resource->resource_lock` (power.c:58, init at :955) guards `ref_count`/`state` in every on/off/get-state path.
- Per-device lists: `device->power.states[i].resources` and `device->wakeup.resources` — no dedicated lock; protected transitively by `acpi_device_lock` (drivers/acpi/scan.c:44, extern via sleep.h:8) / `acpi_scan_lock` (scan.c:42) during setup/teardown.
- `acpi_wakeup_lock` device_pm.c:846 (static) guards `wakeup.enable_count` + GPE arm/disarm pairing in `__acpi_device_wakeup_enable`/`acpi_device_wakeup_disable`; bounded at `INT_MAX` with `acpi_handle_info` guard (device_pm.c:889-892).
- `wakeup.prepare_count` (confirmed field, acpi_bus.h:350) counted in power.c `acpi_enable_wakeup_device_power`/`acpi_disable_wakeup_device_power` (:728/:779) under `acpi_device_lock` — separate counter/lock from `enable_count`, i.e. two independent nested refcounts (power-resources+`_DSW` vs GPE arming).
- `acpi_pm_notifier_lock`+`acpi_pm_notifier_install_lock` device_pm.c:520-521 guard `wakeup.context`/`wakeup.ws`/`notifier_present`.
- Deliberate asymmetry: drivers/acpi/wakeup.c:24-28 comment states `acpi_device_lock` is intentionally not taken in `acpi_enable/disable_wakeup_devices` (suspend path, no concurrent hotplug), whereas proc.c:25,104 do take it (user-context iteration).

#### Hard-coded limits
- `ACPI_D_STATE_COUNT`=5, `ACPI_D_STATES_MAX`=`ACPI_STATE_D3`=4 — include/acpi/actypes.h:596-597.
- `_PRx`/`_PSx` build loop: `ACPI_STATE_D0..ACPI_STATE_D3_HOT` (0..3, i.e. 4 packages `_PR0.._PR3`) — scan.c:1118-1119; D3cold (index 4) gets no own `_PRx`, only an empty `INIT_LIST_HEAD` (scan.c:1121) and inferred validity.
- sysfs `attr_groups[ACPI_STATE_D0..D3_HOT]` — power.c:517-534, 4-entry array ("power_resources_D0".."D3hot").
- S-state side (for `_SxD`/`_SxW`): `ACPI_S_STATES_MAX`=`ACPI_STATE_S5`=5, `ACPI_S_STATE_COUNT`=6 — actypes.h:587-588.
- No separate global "state-validity table"; validity is per-device via `power.states[i].flags.valid`, computed at scan time (scan.c:1080-1082,1124,1126,1139-1140).

#### Version-specific facts (v7.0 vs older/widely-documented kernels)
- `acpi_bus_get_power(acpi_handle,int*)` (old handle-based getter) does not exist in v7.0 (grep-confirmed absent tree-wide) — fully superseded by `acpi_device_get_power`+`acpi_bus_update_power`.
- `acpi_general_pm_domain.detach` is now set inline in the struct initializer (device_pm.c:1390); commit `4a89166ee075` moved this out of a runtime `dev->pm_domain->detach = acpi_dev_pm_detach;` assignment previously done inside `acpi_dev_pm_attach` — older-kernel docs showing that runtime assignment are stale for v7.0.
- `acpi_dev_pm_attach` briefly gained (commit `88fad6ce090b`) then reverted (`00fd9aad55e7`, this cycle) a "skip devices without ACPI PM/wakeup" check; v7.0 attaches the domain to any first-physical-node device matching an ACPI companion except `ACPI_FAN_DEVICE_IDS`.
- `acpi_subsys_prepare`/`acpi_subsys_complete` now call `dev_pm_set_strict_midlayer(dev,true/false)` (device_pm.c:1121,1152) — added by commit `325e3778eac3`, not present in older kernels.
- `acpi_add_pm_notifier` now registers the wakeup source under the target `dev`, not `&adev->dev` (device_pm.c:589) — commit `057edc58aa59` changed sysfs placement of wakeup sources.
- `acpi_turn_off_unused_power_resources` quirk table grew two new DMI entries this cycle (`0467ed880a17`, `cd7ef20ba8c6`), plus a new `acpi_power_resources_init()` (power.c:1159, added by `3bc3dc166dd2`) centralizing the `dmi_check_system` calls.

#### Suggested pages beyond the request's list
- Device-wakeup page (`_PRW`+wake-GPE+notify chain) — justified: rich, distinct anchor set (scan.c:922,1003,1025; device_pm.c:523,529,570,604,836,948; wakeup.c:38,63; proc.c:18 /proc/acpi/wakeup) not reducible to the D-state or PowerResource pages.
- ACPI PM-domain / `acpi_dev_pm_attach` page — justified: distinct "glue to driver core" story (device_pm.c:1370,1405,1443; drivers/base/power/common.c:103) plus the whole `acpi_subsys_*` callback family — separate concern from raw D-state get/set.
- `_SxD`/`_SxW` target-state page — justified: self-contained algorithm in static `acpi_dev_pm_get_state` (device_pm.c:667) and `acpi_pm_device_sleep_state` (device_pm.c:788) plus `_S0W` (device_pm.c:507), mapping system sleep state → device D-state, orthogonal to `_PSx`/`_PRx` internals.

#### Tracepoints
- Negative finding: no `TRACE_EVENT` defined and no `trace_*()` calls in drivers/acpi/device_pm.c, power.c, scan.c, wakeup.c, or proc.c (grep evidence recorded). drivers/acpi/sleep.c includes trace/events/power.h (:24) and calls `trace_suspend_resume()` twice (sleep.c:604,621) but only inside `acpi_suspend_enter()` (S1/S3 low-level entry) — outside the device-wakeup/`acpi_pm_wakeup_event` chain.

#### Debug/diagnostic printing
- Per-file counts: device_pm.c — `acpi_handle_debug` ×12, `acpi_handle_info` ×1, `dev_dbg` ×6, 0 `dev_err`/`WARN`. power.c — `acpi_handle_debug` ×8, `acpi_handle_info` ×3, `acpi_handle_notice` ×1, `dev_dbg` ×7, `dev_err` ×2, `pr_debug` ×1. wakeup.c/proc.c — none. No `ACPI_DEBUG_PRINT`, `WARN_ON`, or `BUG_ON` anywhere in these five files (grep-confirmed).
- Load-bearing sites: device_pm.c:191 `acpi_handle_debug` "Power state %s not supported" gates the `-ENODEV` reject in `acpi_device_set_power`; device_pm.c:892 `acpi_handle_info` "Wakeup enable count out of bounds!" guards `enable_count` overflow; power.c:733/798 `dev_err` "Cannot turn on/off wakeup power resources" precede clearing `wakeup.flags.valid`; power.c:1013 `acpi_handle_notice` marks the HP EliteBook `_ON`/`_OFF` quirk path.

#### Asynchronous / deferred processing
- Wakeup-notify dispatch is asynchronous at the ACPICA/OSL layer: `acpi_install_notify_handler(...,ACPI_SYSTEM_NOTIFY, acpi_pm_notify_handler,...)` (device_pm.c:583) is invoked by ACPICA via `acpi_os_execute(OSL_NOTIFY_HANDLER,...)` (drivers/acpi/osl.c:1092,1134-1135) which `queue_work()`s onto the dedicated `kacpi_notify_wq` (osl.c:67,1698) — so `acpi_pm_notify_handler`/`acpi_pm_wakeup_event` execute in workqueue context, not SCI-interrupt context.
- `acpi_pm_notify_work_func` (device_pm.c:836, the `context.func` set by `acpi_dev_pm_attach` at :1467) further defers via `pm_request_resume(dev)`, which queues onto `pm_wq` (drivers/base/power/runtime.c:537 et al.) — genuine second-stage deferral into runtime-PM.
- Device-removal power teardown is deferred: `acpi_scan_drop_device` (scan.c:606, called synchronously from ACPICA namespace-node deletion) `DECLARE_WORK`s `acpi_device_del_work_fn` (scan.c:608) and queues it via `acpi_queue_hotplug_work` (scan.c:624, ACPI hotplug workqueue, explicitly to avoid running under ACPICA's namespace mutex per comment :601-604); the work function calls `acpi_power_transition(adev, ACPI_STATE_D3_COLD)` (scan.c:588) to drop power-resource refs.
- By contrast, `acpi_power_on`/`acpi_power_off`/`acpi_power_transition`/`acpi_resume_power_resources`/`acpi_turn_off_unused_power_resources` themselves are fully synchronous — no `INIT_WORK`/`schedule_work`/`queue_work` anywhere in power.c or device_pm.c (grep-confirmed; only the dependent-device nudge `pm_request_resume(dep->dev)` at power.c:395 inside `__acpi_power_on` is itself async, via the runtime-PM queue above).

#### Stale-plan claim verification
- (a) Confirmed — include/acpi/actypes.h:590-596 (`D3_COLD` is a `#define` alias of `D3`, i.e. same raw value as D3hot; distinction is purely how kernel code treats "hot" vs "cold" via flags, not the constant).
- (b) Confirmed-with-caveat — `states[ACPI_D_STATE_COUNT]` (fixed array of 5, acpi_bus.h:295) is populated by `acpi_bus_get_power_flags` (scan.c:1088) via its per-state helper `acpi_bus_init_power_state` (scan.c:1053), not a dynamically-sized `[]`.
- (c) Confirmed — `acpi_device_get_power` device_pm.c:75, `acpi_device_set_power` device_pm.c:162.
- (d) Confirmed — `acpi_device_set_power` (device_pm.c:209-274): for D0 target, `acpi_power_transition` runs before `acpi_dev_pm_explicit_set`(`_PS0`) (:245,273); for deeper targets, `acpi_dev_pm_explicit_set`(`_PSx`) runs before `acpi_power_transition` (:234,239-240) — matches the ordering comment at :209-215.
- (e) Confirmed — `acpi_bus_init_power_state` (scan.c:1053-1073) evaluates `"_PR0".."_PR3"` and hands the package to `acpi_extract_power_resources` (power.c:152) into `ps->resources`.
- (f) Confirmed — drivers/acpi/power.c:51-60, fields `system_level`(:54) and `order`(:55) present exactly as the stale plan states.
- (g) Confirmed — `ref_count` field (power.c:56) incremented/decremented in `acpi_power_on_unlocked`/`acpi_power_off_unlocked` (:405,454), driven by `acpi_power_transition` (power.c:852).
- (h) Confirmed — `_ON` power.c:373, `_OFF` power.c:431, `_STA` power.c:198, all via `acpi_evaluate_object`/`acpi_evaluate_integer`.

### Area F: embedded controller — COMPLETE (recorded 2026-07-19)

Tree: the documented checkout @ v7.0 (028ef9c96e96). All paths tree-relative.

#### 1. Core structs
- `struct acpi_ec` — drivers/acpi/internal.h:194-216 — core EC device object.
  - identity/regs: `handle,gpe,irq,command_addr,data_addr,global_lock` (internal.h:195-200)
  - state/flags: `flags` (EC_FLAGS_* bitmask), `reference_count`, `event_state`, `events_to_process`, `events_in_progress`, `queries_in_progress`, `busy_polling`, `polling_guard`, `timestamp` (internal.h:201-215)
  - locks/queues: `mutex`, `wait` (waitqueue), `list` (query-handler list), `curr` (active transaction ptr), `lock` (spinlock), `work` (event work item) (internal.h:203-208)
- `enum acpi_ec_event_state` — internal.h:188-192 — 3-state machine: EC_EVENT_READY/IN_PROGRESS/COMPLETE.
- `struct transaction` — drivers/acpi/ec.c:155-165 — one in-flight command: wdata/rdata + wi/ri cursors, wlen/rlen, command, irq_count, flags (POLL/COMPLETE bits).
- `struct acpi_ec_query_handler` — ec.c:146-153 — registered _Qxx/native callback (query_bit, handle, func, data, kref); name unchanged at v7.0.
- `struct acpi_ec_query` — ec.c:167-172 — per-dispatch container: embeds transaction + work_struct + handler + ec back-pointer.
- `struct acpi_table_ecdt` — include/acpi/actbl1.h:1266-1273 — ECDT firmware table: `control`/`data` (acpi_generic_address), `uid`, `gpe`, `id[]` namepath; `ACPI_SIG_ECDT` actbl1.h:41.

#### 2. API families
- Probe/attach chain:
  - `acpi_ec_ecdt_probe()` ec.c:2013, called drivers/acpi/bus.c:1413 (pre-AML, before acpi_initialize_objects) — parses ECDT.
  - `acpi_ec_dsdt_probe()` ec.c:1809, called bus.c:1448 — namespace PNP0C09 walk; no-op if boot_ec already set (ec.c:1821-1822) — i.e. ECDT wins if present.
  - `acpi_ec_ecdt_start()` ec.c:1870, called from `acpi_ec_init()` ec.c:2379 (after acpi_scan_init) — resolves ECDT EC's namespace handle, registers ACPI_BUS_TYPE_ECDT_EC early device (scan.c:2769).
  - `acpi_ec_probe()` ec.c:1680 (.probe of `acpi_ec_driver` ec.c:2265) — matches `ec_device_ids`={"PNP0C09","LNXEC"/ACPI_ECDT_HID,""} ec.c:1798-1802 (HID at include/acpi/acpi_drivers.h:29); fast-path reuse of boot_ec by handle/HID (ec.c:1689-1692); else merges duplicate EC objects: DSDT handle wins, ECDT GPE wins unless EC_FLAGS_TRUST_DSDT_GPE quirk (ec.c:1706-1722).
- Register access (real v7.0 names): `acpi_ec_read_status()` ec.c:277, `acpi_ec_read_data()` ec.c:292, `acpi_ec_write_cmd()` ec.c:301, `acpi_ec_write_data()` ec.c:308 — all `inb`/`outb` on command_addr/data_addr.
- Transaction engine: `acpi_ec_transaction_unlocked()` ec.c:783 (real unlocked core: submit_flushable_request→set curr→start_transaction→ec_poll→complete_request); `acpi_ec_transaction()` ec.c:821 (mutex_lock + optional ACPI global lock, wraps unlocked); `advance_transaction()` ec.c:660 (poll/interrupt step, IBF/OBF handling, SCI_EVT→submit_event); mode select via `ec->busy_polling` in `ec_guard()`/`ec_poll()` ec.c:725/760.
- Public accessors: `ec_read()` ec.c:913, `ec_write()` ec.c:931, `ec_transaction()` ec.c:940, `ec_get_handle()` ec.c:956 — operate on global `first_ec` ec.c:178 (EXPORT_SYMBOL, not GPL).
- Command set: `enum ec_command` ec.c:81-87 — ACPI_EC_COMMAND_READ=0x80, ACPI_EC_COMMAND_WRITE=0x81, ACPI_EC_BURST_ENABLE=0x82, ACPI_EC_BURST_DISABLE=0x83, ACPI_EC_COMMAND_QUERY=0x84 (0x80-0x84 verified). RD_EC/WR_EC/BE_EC/BD_EC/QR_EC are only debug mnemonics from `acpi_ec_cmd_string()` ec.c:316-331 (DEBUG||CONFIG_DYNAMIC_DEBUG gated).
- Burst mode: `acpi_ec_burst_enable()` ec.c:847, `acpi_ec_burst_disable()` ec.c:857 (checks ACPI_EC_FLAG_BURST=0x10 ec.c:45 first); no ack-byte value is ever checked in code (grep-confirmed, no 0x90 anywhere) — response byte is read into a local and discarded.
- Event/query chain: `advance_transaction()` ec.c:660 sees SCI_EVT (status&ACPI_EC_FLAG_SCI) → `acpi_ec_submit_event()` ec.c:447 → `queue_work(ec_wq,&ec->work)` ec.c:475 → `acpi_ec_event_handler()` ec.c:1247 → `acpi_ec_submit_query()` ec.c:1193 (runs QR_EC) → `acpi_ec_get_query_handler_by_value()` ec.c:1064 (not "_get_query_handler") → `queue_work(ec_query_wq,&q->work)` ec.c:1235 → `acpi_ec_event_processor()` ec.c:1152 (evaluates _Qxx via `acpi_evaluate_object` ec.c:1163, or native `handler->func` ec.c:1161).
- Opregion handler: `acpi_ec_space_handler()` ec.c:1345-1405, installed via `acpi_install_address_space_handler_no_reg(...,ACPI_ADR_SPACE_EC,...)` ec.c:1544 (ACPI_ADR_SPACE_EC=3, include/acpi/actypes.h:819); `acpi_execute_reg_methods()` called separately ec.c:1556 when `call_reg`.
- GPE vs GpioInt: `install_gpe_event_handler()` ec.c:1494 (`acpi_install_gpe_raw_handler`, ACPI_GPE_EDGE_TRIGGERED) vs `install_gpio_irq_event_handler()` ec.c:1510 (`request_threaded_irq`, IRQF_SHARED|IRQF_ONESHOT — not plain request_irq); chosen in `ec_install_handlers()` ec.c:1586-1589 by `ec->gpe>=0` else `ec->irq` (from `acpi_dev_gpio_irq_get()` ec.c:1565).

#### 3. Lifecycle and locking
- `ec->mutex` — serializes whole transactions (`acpi_ec_transaction` ec.c:829), opregion burst+multi-byte sequences (`acpi_ec_space_handler` ec.c:1361), and `ec->list` query-handler mutation (ec.c:1111,1126); never held from GPE/IRQ context.
- `ec->lock` (spinlock) — protects curr/flags/event_state/events_to_process/events_in_progress/queries_in_progress/reference_count; taken `_irqsave`/`_irq` since `acpi_ec_handle_interrupt()` ec.c:1317 runs it from GPE/IRQ context.
- EC_FLAGS_* bits (enum ec.c:96-105, 8 total): QUERY_ENABLED, EVENT_HANDLER_INSTALLED, EC_HANDLER_INSTALLED, EC_REG_CALLED, QUERY_METHODS_INSTALLED, STARTED, STOPPED, EVENTS_MASKED.
- Separate quirk ints (similarly named but not in the `ec->flags` bitmask): `EC_FLAGS_CORRECT_ECDT`/`TRUST_DSDT_GPE`/`CLEAR_ON_RESUME` ec.c:186-188, set via DMI table `ec_dmi_table` ec.c:1946.
- Suspend/resume: `acpi_ec_suspend()` ec.c:2095 (disable_event if ec_freeze_events), `acpi_ec_suspend_noirq/resume_noirq()` ec.c:2104/2121 (busy-poll switch via `acpi_ec_enter/leave_noirq` ec.c:1016/1027), `acpi_ec_resume()` ec.c:2134; wired in `acpi_ec_pm` ec.c:2221-2224.
- `acpi_ec_block/unblock_transactions()` ec.c:1038/1051 — called from sleep.c: freeze at sleep.c:438 (`acpi_pm_freeze`), unblock at sleep.c:490 (`acpi_pm_finish`), 665 (`acpi_suspend_enter`), 977/982 (`acpi_hibernation_leave`/`acpi_pm_thaw`).
- `acpi_ec_flush_work()` ec.c:565 (flushes ec_wq+ec_query_wq, ec.c:544-547) — called from drivers/acpi/sleep.c:828 (`acpi_s2idle_restore`) and internally ec.c:2206 (`acpi_ec_dispatch_gpe` loop); not called from drivers/acpi/x86/s2idle.c (see item 10).

#### 4. Hard-coded limits (all drivers/acpi/ec.c)
- `ACPI_EC_DELAY`=500ms poll timeout, ec.c:89; module param `ec_delay` ec.c:111-113 defaults to it.
- `ACPI_EC_UDELAY_GLK`=1000µs global-lock wait, ec.c:90.
- `ACPI_EC_UDELAY_POLL`=550µs poll guard, ec.c:91; module param `ec_polling_guard` ec.c:123-125 defaults to it.
- `ACPI_EC_CLEAR_MAX`=100 (max events drained by `acpi_ec_clear`), ec.c:92-93.
- `ACPI_EC_MAX_QUERIES`=16, ec.c:94; module param `ec_max_queries` ec.c:115-117 defaults to it, feeds `ec_query_wq` max_active ec.c:2292-2294.
- `ec_storm_threshold`=8 default, module param ec.c:134-136 — storm detection in `acpi_ec_spurious_interrupt()` ec.c:650-658.
- `ec_poll()` retries: literal `repeat=5` restart attempts, ec.c:763 (no named macro).
- Bool params default false: `ec_busy_polling`/`ec_freeze_events`/`ec_no_wakeup` ec.c:119-121/138-140/142-144.
- `ec_event_clearing` — `module_param_call` ec.c:2261-2263, default `ACPI_EC_EVT_TIMING_QUERY`=0x01 ec.c:127.

#### 5. Version-specific facts
- Event handling is the modern 3-state machine (`event_state` + events_to_process/events_in_progress/queries_in_progress counters, internal.h:188,211-213); no `nr_pending_queries` symbol anywhere in the tree (grep-confirmed) — the old single-counter shape is gone.
- Real lookup name is `acpi_ec_get_query_handler_by_value()` ec.c:1064, not "acpi_ec_get_query_handler".
- GpioInt-based EC interrupts supported for ACPI Reduced-Hardware platforms lacking `_GPE` (`install_gpio_irq_event_handler` ec.c:1510, `acpi_dev_gpio_irq_get` fallback ec.c:1563-1574).
- Opregion install uses the split `acpi_install_address_space_handler_no_reg()` + `acpi_execute_reg_methods()` pair (drivers/acpi/acpica/evxfregn.c:110,121; include/acpi/acpixf.h:662,668) instead of one auto-_REG call.
- `ec_query_wq` allocated with explicit `WQ_PERCPU` flag (ec.c:2293; include/linux/workqueue.h:405 "bound to a specific cpu") — an explicit opt-in not needed in older per-CPU-by-default workqueue APIs.
- All EC allocations use `kzalloc_obj()` helper (include/linux/slab.h:1039) at ec.c:1103,1180,1425, not raw `kzalloc(sizeof(*x))`.
- `acpi_ec_no_wakeup[]` DMI quirk table ec.c:2303-2357 lists current-era models — actively maintained, not stale.

#### 6. Suggested extra pages
- EC operation-region page — `acpi_ec_space_handler` ec.c:1345, ACPI_ADR_SPACE_EC actypes.h:819, 0xFF/256-byte bound ec.c:1355 & ec_sys.c:26.
- ECDT/boot-EC precedence page — ec.c:2013,1809,1870, `struct acpi_table_ecdt` actbl1.h:1266, `boot_ec`/`boot_ec_is_ecdt` ec.c:181-182 (rich, non-obvious precedence rules per item 2).
- EC suspend/s2idle interplay page — `acpi_ec_dispatch_gpe` ec.c:2160, `acpi_ec_flush_work` ec.c:565, `acpi_ec_mark_gpe_for_wake` ec.c:2142 (called from drivers/acpi/x86/s2idle.c:508), `acpi_ec_set_gpe_wake_mask` ec.c:2149 (sleep.c:745,838).
- ec_sys debugfs page — drivers/acpi/ec_sys.c whole file (144 lines); `acpi_ec_add_debugfs` ec_sys.c:110, `write_support` param ec_sys.c:21-24, debugfs nodes gpe/use_global_lock/io ec_sys.c:122-128.
- EC-hosted SMBus (SBS) HC boundary note — drivers/acpi/sbshc.c is a pure consumer of the public EC API (`ec_read`/`ec_write` sbshc.c:92,97; `acpi_ec_add_query_handler` sbshc.c:269) keyed off the `_EC` integer method (sbshc.c:248,266-267); never touches `struct acpi_ec` internals.
- EC module-parameter reference page — 8 tunables (ec_delay, ec_max_queries, ec_busy_polling, ec_polling_guard, ec_storm_threshold, ec_freeze_events, ec_no_wakeup, ec_event_clearing) ec.c:111-144,2261-2263 warrant one consolidated table.

#### 7. Tracepoints
- Negative finding: zero `TRACE_EVENT` defs and zero `trace_*()` calls in ec.c, ec_sys.c, sbshc.c, or drivers/acpi/x86/s2idle.c (grep-confirmed). drivers/acpi/sleep.c has two `trace_suspend_resume()` calls (sleep.c:604,621) but these are generic PM tracepoints, not EC-specific.

#### 8. Debug/diagnostic printing
- `pr_fmt` "ACPI: EC: " ec.c:17 (sbshc.c uses "ACPI: " sbshc.c:8; ec_sys.c has no pr_fmt override).
- Macro family ec.c:212-232: `ec_log_raw`/`ec_dbg_raw` (raw pr_info/pr_debug sinks), `ec_log`/`ec_dbg` (add EC_DBG_SEP+filter marker, markers EC_DBG_DRV/STM/REQ/EVT are DEBUG-only strings, ec.c:198-210), `ec_log_drv`/`ec_dbg_drv` (driver lifecycle, 7/5 call sites), `ec_dbg_stm` (state-machine step, 1 site ec.c:666), `ec_dbg_req` (txn start/stop, ec.c:802,811), `ec_dbg_evt` (event/query lifecycle, 10 sites: ec.c:460,487,696,1158,1165,1230,1251,1275,1289), `ec_dbg_ref` (refcount deltas, 5 sites e.g. ec.c:799,815,974,1006).
- `acpi_ec_cmd_string()` ec.c:316-331 — RD_EC/WR_EC/BE_EC/BD_EC/QR_EC mnemonics feeding ec_dbg_req/evt, gated on DEBUG||CONFIG_DYNAMIC_DEBUG else "UNDEF".
- Load-bearing sites: `ec_poll()` timeout-restart `pr_debug` ec.c:775 "controller reset, restart transaction"; storm counting `acpi_ec_spurious_interrupt()` ec.c:650-658 → `acpi_ec_mask_events()` logs "Polling enabled" ec.c:410 / `acpi_ec_unmask_events()` "Polling disabled" ec.c:424; `acpi_ec_clear()` stale-event report `pr_warn`/`pr_info` ec.c:524,526.

#### 9. Async/deferred/lazy processing
- GPE upcall: `acpi_ec_gpe_handler()` ec.c:1328 (installed ec.c:1498) → `acpi_ec_handle_interrupt()` ec.c:1317 → `clear_gpe_and_advance_transaction()` ec.c:1297 → `advance_transaction(ec,true)` ec.c:660 (call at 1314).
- GpioInt upcall: `acpi_ec_irq_handler()` ec.c:1335 (installed ec.c:1512, threaded) → same chain.
- Event work: `acpi_ec_submit_event()` ec.c:447 → `queue_work(ec_wq,&ec->work)` ec.c:475 onto `ec_wq=alloc_ordered_workqueue("kec",0)` ec.c:2290 → runs `acpi_ec_event_handler()` ec.c:1247.
- Query work: `acpi_ec_submit_query()` ec.c:1193 (called synchronously inside the event-handler loop, ec.c:1258) builds `struct acpi_ec_query` (`acpi_ec_create_query` ec.c:1175, INIT_WORK ec.c:1184) → `queue_work(ec_query_wq,&q->work)` ec.c:1235 onto `ec_query_wq=alloc_workqueue("kec_query",WQ_PERCPU,ec_max_queries)` ec.c:2292-2294 → runs `acpi_ec_event_processor()` ec.c:1152.
- Poll-mode delay: `ec_guard()` ec.c:725 — busy_polling branch does `udelay()` ec.c:736; else `wait_event_timeout(ec->wait,...)` ec.c:751; `ec_poll()` ec.c:760 bounds each restart to `ec_delay` ms.
- Completion waits on `ec->wait` (internal.h:204): woken by `acpi_ec_complete_request()` ec.c:399 and `advance_transaction()` interrupt path ec.c:716; consumed by `acpi_ec_stop()`'s `wait_event()` ec.c:1001 (drain before stopping).
- s2idle deferred GPE dispatch: `acpi_ec_dispatch_gpe()` ec.c:2160, called only from drivers/acpi/sleep.c:794 (`acpi_s2idle_wake`) — services EC GPE in-band under `ec->lock` (`clear_gpe_and_advance_transaction` ec.c:2193), then loops `acpi_ec_flush_work()` ec.c:2206 until drained or real wakeup pending.

#### 10. Stale-plan claim verification
- (a) Confirmed — `ec_device_ids[]` ec.c:1798-1802 (match table ec.c:2270) + standalone `acpi_ec_ecdt_probe()` ec.c:2013.
- (b) Confirmed — `struct acpi_ec` internal.h:194; `acpi_ec_space_handler()` ec.c:1345 installed for ACPI_ADR_SPACE_EC ec.c:1544-1547.
- (c) Confirmed — `ec_parse_device()` evaluates `_GPE` ec.c:1478; ECDT path uses `ecdt_ptr->gpe` ec.c:2071 instead.
- (d) Confirmed-with-caveat — real field names are `command_addr`/`data_addr` (internal.h:198-199); "EC_SC"/"EC_DATA" appear only in `ec_dbg_raw` log strings (ec.c:281,297,303,310). ACPI_EC_FLAG_IBF=0x02/OBF=0x01 confirmed ec.c:42-43.
- (e) Confirmed — `acpi_ec_read_status` ec.c:277, `acpi_ec_write_cmd` ec.c:301, `acpi_ec_read_data` ec.c:292 (plus `acpi_ec_write_data` ec.c:308, uncited 4th accessor).
- (f) Confirmed-with-caveat — values 0x80-0x84 match; RD_EC/WR_EC/BE_EC/BD_EC/QR_EC are debug-string mnemonics only (`acpi_ec_cmd_string` ec.c:316-331); real names are `ACPI_EC_COMMAND_READ/WRITE/BURST_ENABLE/BURST_DISABLE/COMMAND_QUERY`, enum ec.c:81-87.
- (g) Confirmed — `struct transaction` ec.c:155; `acpi_ec_transaction()` ec.c:821 (+ real core `acpi_ec_transaction_unlocked()` ec.c:783).
- (h) Refuted — `acpi_ec_burst_enable()` begins at ec.c:847, not 850 (850 is mid-body struct init); no 0x90 ack-byte check exists anywhere in the EC code (grep-confirmed) — the response byte is read and discarded.
- (i) Confirmed-with-caveat — `advance_transaction()` is at ec.c:660, but handlers reach it via two hops: `acpi_ec_gpe_handler`/`acpi_ec_irq_handler` (ec.c:1328/1335) → `acpi_ec_handle_interrupt()` ec.c:1317 → `clear_gpe_and_advance_transaction()` ec.c:1297 → `advance_transaction()`.
- (j) Confirmed — chain `acpi_ec_submit_event`→`acpi_ec_submit_query()` ec.c:1193→`acpi_ec_get_query_handler_by_value()` ec.c:1064 (not "...get_query_handler")→`acpi_ec_event_processor()` ec.c:1152; query value 0 → `-ENODATA`, handler not invoked (ec.c:1212-1215), matching "0 reserved/ignored".

### Area G: asynchronous/deferred/lazy designs, subsystem-wide sweep — COMPLETE (recorded 2026-07-19)

Scope note: `drivers/acpi/arm64/` (9 files) and `drivers/acpi/riscv/` (8 files) exist but are excluded per campaign x86 scope (arm64 has its own GHES SEA/SDEI hooks that parallel what's covered here via shared `apei/ghes.c`). No other exclusions — all remaining files under `drivers/acpi/**` plus `include/acpi/acpiosxf.h` were swept with the full grep matrix (workqueue alloc, INIT_WORK family, queue/schedule/flush, timers, irq_work/tasklet/kthread, async_schedule/RCU, completions, irq/task_work/waitqueue, kfifo/gen_pool/llist) and every hit was traced to a real definition. Nothing was dropped for length.

#### 1. Workqueues owned by the subsystem

| wq var | name string | flags/ordering/max_active | created at | runs | flush/drain |
|---|---|---|---|---|---|
| `kacpid_wq` | `"kacpid"` | `WQ_PERCPU`, max_active=1 | drivers/acpi/osl.c:1697 | GPE method/handler dispatch (`OSL_GPE_HANDLER`), pinned CPU0 via `queue_work_on(0,...)` | drivers/acpi/osl.c:1172 (`acpi_os_wait_events_complete`); destroyed osl.c:1725 |
| `kacpi_notify_wq` | `"kacpi_notify"` | `WQ_PERCPU`, max_active=0 (unbounded) | drivers/acpi/osl.c:1698 | Notify() dispatch (`OSL_NOTIFY_HANDLER`), incl. GPE re-enable (`acpi_ev_asynch_enable_gpe`) | osl.c:1173; destroyed osl.c:1726 |
| `kacpi_hotplug_wq` | `"kacpi_hotplug"` | `alloc_ordered_workqueue`, flags=0 (unbound, max_active=1) | drivers/acpi/osl.c:1699 | `acpi_hotplug_work_fn`, `acpi_device_del_work_fn`, any caller of `acpi_queue_hotplug_work` | never `flush_workqueue`'d — relies on ordering + `acpi_scan_lock`; destroyed osl.c:1727 |
| `ec_wq` | `"kec"` | `alloc_ordered_workqueue(...,0)` | drivers/acpi/ec.c:2290 | `acpi_ec_event_handler` (per-EC event pump) | drivers/acpi/ec.c:546 (`__acpi_ec_flush_work`) |
| `ec_query_wq` | `"kec_query"` | `WQ_PERCPU`, max_active=`ec_max_queries` (module param, default 16) | ec.c:2293 | `acpi_ec_event_processor` (one per `_Qxx`) | ec.c:547, ec.c:1148 (`acpi_ec_remove_query_handler`) |
| `acpi_thermal_pm_queue` | `"acpi_thermal_pm"` | `WQ_HIGHPRI\|WQ_MEM_RECLAIM\|WQ_PERCPU`, max_active=0 | drivers/acpi/thermal.c:1040 | `acpi_thermal_check_fn` | thermal.c:893,908,917; destroyed thermal.c:1058 |
| `nfit_wq` | `"nfit"` | `create_singlethread_workqueue` → unbound ordered, max_active=1 | drivers/acpi/nfit/core.c:3523 | `acpi_nfit_scrub` (ARS) | nfit/core.c:3335, 3434 |

OSL dispatch table (`acpi_os_execute`, drivers/acpi/osl.c:1092): switch at osl.c:1133 handles only `OSL_NOTIFY_HANDLER`→`kacpi_notify_wq` (osl.c:1135) and `OSL_GPE_HANDLER`→`queue_work_on(0, kacpid_wq,...)` (osl.c:1145); `OSL_DEBUGGER_MAIN_THREAD` bypasses workqueues entirely via `acpi_debugger_create_thread`→kthread (osl.c:1102-1108, thread body drivers/acpi/acpi_dbg.c:383/427). `OSL_GLOBAL_LOCK_HANDLER`, `OSL_EC_POLL_HANDLER`, `OSL_EC_BURST_HANDLER` are declared in the enum (include/acpi/acpiosxf.h:21,26-27) but never dispatched — hitting them falls to the `default:` error at osl.c:1147-1149 (dead ABI surface; EC/global-lock don't route through `acpi_os_execute` in Linux).
acpica core (`drivers/acpi/acpica/*.c`) never touches Linux workqueue/timer APIs directly — all its async plumbing funnels through `acpi_os_execute`/`acpi_os_wait_events_complete`, keeping OS-specific code confined to osl.c/ec.c/thermal.c/nfit.

#### 2. Work items and pipelines (11 total, by file)

| handler | INIT at | lands on | queued by (file:line) | completes/re-arms |
|---|---|---|---|---|
| `acpi_os_execute_deferred` | osl.c:1126 | kacpid_wq/kacpi_notify_wq | osl.c:1135/1145 (`acpi_os_execute`) | runs `dpc->function(dpc->context)` then `kfree(dpc)` |
| `acpi_hotplug_work_fn` | osl.c:1204 | kacpi_hotplug_wq | osl.c:1213 (`acpi_hotplug_schedule`) | calls `acpi_device_hotplug`, frees `hpw` |
| `acpi_ec_event_handler` | ec.c:1433 (`acpi_ec_alloc`) | ec_wq | ec.c:475 (`acpi_ec_submit_event`) | drains `events_to_process`, re-arms via `acpi_ec_close_event`/`acpi_ec_complete_event` |
| `acpi_ec_event_processor` | ec.c:1184 (`acpi_ec_create_query`) | ec_query_wq | ec.c:1235 (`acpi_ec_submit_query`) | runs `_Qxx` handler, decrements `queries_in_progress`, frees query |
| `sb_notify_work` (`DECLARE_WORK acpi_sb_work`) | bus.c:709 | system default wq (`schedule_work`) | bus.c:713 (`acpi_sb_notify`, `\_SB` shutdown notify) | infinite loop evaluating `_OST` every 10s (`ACPI_SB_INDICATE_INTERVAL`) until poweroff |
| `acpi_device_del_work_fn` (`DECLARE_WORK work`) | scan.c:608 | kacpi_hotplug_wq | scan.c:624 (`acpi_scan_drop_device`, called from `acpi_ns_delete_node`) | drains `acpi_device_del_list`, calls `acpi_device_del`+`acpi_power_transition` per device |
| `acpi_table_events_fn` | scan.c:2950 | system default wq (`schedule_work`) | scan.c:2951 (`acpi_scan_table_notify`) | `acpi_bus_scan(ACPI_ROOT_OBJECT)` under `acpi_scan_lock`, frees work |
| `acpi_thermal_check_fn` | thermal.c:880 | acpi_thermal_pm_queue | thermal.c:326 (`acpi_queue_thermal_check`, guarded by `work_pending`) | re-evaluates trips via `acpi_thermal_trips_update` |
| `acpi_video_switch_brightness` (delayed) | acpi_video.c:1153 | system default delayed-wq (`schedule_delayed_work`) | acpi_video.c:1592, HZ/10 debounce | reads `_BQC`, cancelled acpi_video.c:241/1956 |
| `ghes_vendor_record_work_func` | apei/ghes.c:724 | system default wq (`schedule_work`) | apei/ghes.c:725 (`ghes_defer_non_standard_event`) | calls vendor-record notifier chain, `gen_pool_free`s entry |
| `acpi_nfit_scrub` (delayed) | nfit/core.c:3283 | nfit_wq | nfit/core.c:2907 `__sched_ars` (queue_delayed_work), nfit/core.c:1299 (`mod_delayed_work`, HZ retry) | reschedules self via `tmo*HZ` until ARS completes; cancelled nfit/core.c:3325 |

#### 3. Interrupt-to-process handoffs
- SCI→GPE: `request_threaded_irq(irq,NULL,acpi_irq,IRQF_SHARED|IRQF_ONESHOT,"acpi",...)` osl.c:581, installed via `acpi_os_install_interrupt_handler` osl.c:557←`acpi_ev_install_sci_handler` acpica/evsci.c:150,157 registers `acpi_ev_sci_xrupt_handler` acpica/evsci.c:76 → `acpi_ev_gpe_detect` acpica/evsci.c:98/acpica/evgpe.c:347 → per-GPE `acpi_ev_detect_gpe` acpica/evgpe.c:625 → `acpi_ev_gpe_dispatch` acpica/evgpe.c:748 → `acpi_os_execute(OSL_GPE_HANDLER, acpi_ev_asynch_execute_gpe_method,...)` acpica/evgpe.c:823 (kacpid_wq CPU0) → acpica/evgpe.c:455 runs `_Lxx/_Exx` or implicit-notify loop `acpi_ev_queue_notify_request` acpica/evgpe.c:482 → defers re-enable `acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_ev_asynch_enable_gpe,...)` acpica/evgpe.c:526 (kacpi_notify_wq) → acpica/evgpe.c:552→`acpi_ev_finish_gpe` acpica/evgpe.c:578.
- Notify: `acpi_ev_queue_notify_request` acpica/evmisc.c:67 → `acpi_os_execute(OSL_NOTIFY_HANDLER, acpi_ev_notify_dispatch,...)` acpica/evmisc.c:139 (kacpi_notify_wq) → `acpi_ev_notify_dispatch` acpica/evmisc.c:161 invokes global+per-object handler list.
- EC GPE/IRQ: raw GPE handler `acpi_install_gpe_raw_handler(...,acpi_ec_gpe_handler,...)` ec.c:1498 or GPIO-IRQ `request_threaded_irq(...,acpi_ec_irq_handler,IRQF_SHARED|IRQF_ONESHOT,...)` ec.c:1512-1513 → both call `acpi_ec_handle_interrupt` ec.c:1317 → `clear_gpe_and_advance_transaction`→`advance_transaction` ec.c:660 (runs synchronously in SCI thread, not queued) → on SCI bit set, `acpi_ec_submit_event` ec.c:447 → `queue_work(ec_wq,&ec->work)` ec.c:475 → `acpi_ec_event_handler`→`acpi_ec_submit_query` ec.c:1193 (sync EC transaction) →`queue_work(ec_query_wq,&q->work)` ec.c:1235→`acpi_ec_event_processor`.
- GED: `request_threaded_irq(irq,NULL,acpi_ged_irq_handler,IRQF_ONESHOT[|IRQF_SHARED],...)` drivers/acpi/evged.c:130, handler evged.c:56 calls `acpi_execute_simple_method` directly, fully synchronous — no workqueue hop (contrast with EC/SCI).
- GHES: notify-type dispatch installed apei/ghes.c:1711-1760: `ACPI_HEST_NOTIFY_POLLED`→`timer_setup(&ghes->timer,ghes_poll_func,0)` ghes.c:1713+`ghes_add_timer` ghes.c:1183; `ACPI_HEST_NOTIFY_EXTERNAL`→`request_irq(...,ghes_irq_func,IRQF_SHARED,...)` ghes.c:1724; `ACPI_HEST_NOTIFY_SCI/GSIV/GPIO`→`register_acpi_hed_notifier(&ghes_notifier_hed)` ghes.c:1738 (bridged from drivers/acpi/hed.c PNP0C33 Notify→`blocking_notifier_call_chain` hed.c:48, itself dispatched via the Notify chain above on kacpi_notify_wq); `ACPI_HEST_NOTIFY_SEA`→`ghes_sea_add` ghes.c:1488 (NMI-safe list, `ghes_notify_sea` ghes.c:1473); `ACPI_HEST_NOTIFY_NMI`→`ghes_nmi_add` ghes.c:1545 (`register_nmi_handler(NMI_LOCAL,ghes_notify_nmi,...)` ghes.c:1555); `ACPI_HEST_NOTIFY_SOFTWARE_DELEGATED`→`apei_sdei_register_ghes` ghes.c:1628 (`sdei_register_ghes`, normal/critical callbacks ghes.c:1600/1614). All NMI/SEA/SDEI paths call `ghes_in_nmi_queue_one_entry` ghes.c:1319 (`gen_pool_alloc`+`llist_add` ghes.c:1371) then `irq_work_queue(&ghes_proc_irq_work)` ghes.c:1396/1592 (init ghes.c:1585) → `ghes_proc_in_irq` ghes.c:1260 drains `ghes_estatus_llist` (`llist_del_all`+`llist_reverse_order` ghes.c:1268/1273) in true IRQ context, `gen_pool_free` per node. Memory-failure escalation: `ghes_do_memory_failure` ghes.c:505 uses `task_work_add(current,&twcb->twork,TWA_RESUME)` ghes.c:523 (gen_pool-backed `ghes_task_work`) → `memory_failure_cb` ghes.c:489 runs at return-to-userspace.

#### 4. Hotplug deferral

| symbol | file:line | notes |
|---|---|---|
| `acpi_hotplug_schedule` | osl.c:1192 | allocs `acpi_hp_work`, `INIT_WORK`+`queue_work(kacpi_hotplug_wq,...)` osl.c:1204-1213; runs `acpi_os_wait_events_complete()` first inside `acpi_hotplug_work_fn` osl.c:1187 |
| `acpi_queue_hotplug_work` | osl.c:1220 | thin wrapper, used by `acpi_scan_drop_device` scan.c:624 and by device-specific callers |
| `lock_device_hotplug`/`unlock_device_hotplug` | scan.c:447/498 | sole choke point, wraps `acpi_device_hotplug` scan.c:442, held with `acpi_scan_lock` |
| Callers of `acpi_hotplug_schedule` | bus.c:615 (generic Notify path), device_sysfs.c:385 (`ACPI_OST_EC_OSPM_EJECT` sysfs eject) | both fall through to synchronous OST failure eval if queuing fails |
| Dock deferred handling | dock.c:410 `dock_notify`, invoked from `acpi_device_hotplug` scan.c:458-459 (`adev->flags.is_dock_station`) | runs on kacpi_hotplug_wq; post-dock re-init `acpi_update_all_gpes()` dock.c:451 |
| Container/memhotplug/pci_root hotplug | container.c:94-97, acpi_memhotplug.c:40/350, pci_root.c:53/1067 | all register `.hotplug` ops via `acpi_scan_add_handler_with_hotplug`, consumed through the same `acpi_device_hotplug` path — no private wq |

#### 5. Timers, delayed work, and polling

| mechanism | period source | file:line |
|---|---|---|
| EC busy/wait polling (`ec_guard`/`ec_poll`) | `ec->polling_guard` (default `ACPI_EC_UDELAY_POLL`=550us) via `usecs_to_jiffies`; `ec_delay`=500ms module param, 5 restarts | ec.c:725,760 |
| EC storm-threshold masking | `ec_storm_threshold` module param (default 8 IRQs) | ec.c:650 (`acpi_ec_spurious_interrupt`) |
| GHES poll mode | `generic->notify.poll_interval` (ms, from HEST) | apei/ghes.c:1183 (`ghes_add_timer`), 1198 (`ghes_poll_func`, `timer_setup` ghes.c:1713), teardown `timer_shutdown_sync` ghes.c:1797 |
| NFIT ARS scrub reschedule | `acpi_desc->scrub_tmo*HZ`, retried on `-EBUSY`/busy bit | nfit/core.c:1292-1299 (`mod_delayed_work`), 2899 (`__sched_ars`), 2907 |
| AC notify debounce | `ac_sleep_before_get_state_ms` module param, firmware-race quirk | ac.c:140-141 (`acpi_ac_notify`) |
| Battery notify debounce | `battery_notification_delay_ms` (DMI quirk, e.g. 1000ms) + fixed `msleep(20)` | battery.c:1078-1079, battery.c:1204 |
| Video brightness switch debounce | fixed `HZ/10` | acpi_video.c:1592 |
| PCC OpRegion handler wait | `pcc_chan->latency * PCC_CMD_WAIT_RETRIES_NUM(500)` via `wait_for_completion_timeout` | acpi_pcc.c:119 (handler acpi_pcc.c:97) |
| IPMI OpRegion handler wait | `IPMI_TIMEOUT` (ipmi core) + unbounded `wait_for_completion` | acpi_ipmi.c:570-575 (`acpi_ipmi_space_handler` acpi_ipmi.c:524) |
| EINJ firmware-completion poll | `SLEEP_UNIT_MIN/MAX` busy loop | apei/einj-core.c:237-244 (`einj_timedout`) |
| ERST firmware stall opcodes | AML-supplied stall value, capped `FIRMWARE_MAX_STALL` | apei/erst.c:190-205 (`erst_exec_stall`), :207 (`erst_exec_stall_while_true`) |
| Power-resource HP-EB quirk delay | fixed `msleep(200)` | power.c:1011-1028 (`acpi_resume_on_eb_gp12pxp`) |
| LPSS D3-delay quirk | device-specific `delay` | x86/lpss.c:864 |
| PMIC xpower regulator settle | fixed `usleep_range(6000,10000)` | pmic/intel_pmic_xpower.c:251 |
| ACPI PAD idle kthreads busy/sleep loop | `round_robin_time`(1s)/`idle_pct`(5%) module params | acpi_pad.c:144-215 (`power_saving_thread`) |

#### 6. Lazy and deferred initialization/enumeration designs

| design | file:line |
|---|---|
| Deferred full GPE enable | `acpi_update_all_gpes` acpica/evxfgpe.c:43, called once at scan start scan.c:2857 (right before `acpi_bus_scan`), and again post-dock dock.c:451; polls already-triggered GPEs via `acpi_ev_gpe_detect` evxfgpe.c:71 if `is_polling_needed` |
| EC wake-GPE deferral | `ec_no_wakeup` module param (ec.c:142) gates `acpi_ec_mark_gpe_for_wake`/`acpi_ec_set_gpe_wake_mask` ec.c:2142,2149 and noirq GPE mask/unmask ec.c:2112,2127; `acpi_ec_dispatch_gpe` ec.c:2160 consulted from s2idle wake loop |
| `_DEP`-deferred enumeration | `dep_unmet` counter include/acpi/acpi_bus.h:493, incremented scan.c:1842; cleared via `acpi_dev_clear_dependencies`→`acpi_walk_dep_device_list`→`acpi_scan_clear_dep` scan.c:2463,2519,2493; re-attach deferred with `async_schedule_dev_nocall(acpi_scan_clear_dep_fn,...)` scan.c:2454 (barrier: `async_synchronize_full()` per comment scan.c:2448); gate `acpi_dev_ready_for_enumeration` scan.c:2533, consumers: `acpi_bus_attach` scan.c:2350 and external `drivers/i2c/i2c-core-acpi.c:145` |
| Deferred table load | AML `Load`/`LoadTable`: acpica/exoparg1.c:194/352 (`acpi_ex_load_op`), acpica/exoparg6.c:272 (`acpi_ex_load_table_op`) → `acpi_tb_load_table` acpica/tbdata.c:946 → `acpi_tb_notify_table(ACPI_TABLE_EVENT_LOAD,...)` tbdata.c:980 → registered handler `acpi_bus_table_handler` bus.c:1382 (installed bus.c:1438) → `acpi_scan_table_notify` scan.c:2939 → `schedule_work(acpi_table_events_fn)` scan.c:2950-2951 → `acpi_bus_scan` under `acpi_scan_lock` |
| Reconfig notifier chain | `acpi_reconfig_chain` (`BLOCKING_NOTIFIER_HEAD`) scan.c:558; fired scan.c:580 (`ACPI_RECONFIG_DEVICE_REMOVE`, from `acpi_device_del_work_fn`) and scan.c:2252 (`ACPI_RECONFIG_DEVICE_ADD`, `acpi_default_enumeration`); register/unregister scan.c:2954/2960; consumer `acpi_platform_notifier` acpi_platform.c:70,199 |
| initrd table upgrade timing | `acpi_table_upgrade` tables.c:421 (called pre-ACPI-init from arch setup, e.g. arch/x86/kernel/setup.c:1175) stages cpio tables into `acpi_initrd_files[]`; per-table substitution via `acpi_os_physical_table_override`→`acpi_table_initrd_override` tables.c:664/546; leftover new tables installed later by `acpi_table_initrd_scan` tables.c:604, invoked from `acpi_table_init_complete` tables.c:751-753 |
| `_REG` deferral (lazy op-region setup) | `acpi_ev_initialize_region` acpica/evrgnini.c:528 "saves [`_REG`] for execution at a later time" (doc evrgnini.c:500-501); deferred run at `acpi_ev_initialize_op_regions` acpica/evregion.c:44, called once from `acpi_ns_initialize_objects` acpica/nsinit.c:200; handler-install path can also force immediate `_REG` via `acpi_ev_execute_reg_methods` acpica/evxfregn.c:85,298 |
| Module init ordering | `subsys_initcall(acpi_init)` bus.c:1534 → `acpi_bus_init()` bus.c:1510 (installs table handler) → `acpi_ghes_init()` bus.c:1521 → `acpi_scan_init()` bus.c:1523 (GPE update + `acpi_bus_scan`) → `acpi_ec_init()` bus.c:1524 (EC driver registers after namespace scan) |

#### 7. RCU/SRCU and deferred destruction

| chain | file:line |
|---|---|
| `acpi_os_map_iomem`/`acpi_os_unmap_iomem` list | RCU-protected `acpi_ioremaps` list (`list_add_tail_rcu`/`list_for_each_entry_rcu`/`list_del_rcu`) osl.c:228,271,368,398, refcount under `acpi_ioremap_lock` mutex |
| Deferred unmap-then-free | `acpi_os_drop_map_ref` osl.c:393: on last ref, `INIT_RCU_WORK(&map->track.rwork, acpi_os_map_remove)` + `queue_rcu_work(system_percpu_wq,...)` osl.c:400-401 → `acpi_os_map_remove` osl.c:382 does the real `iounmap`/`kunmap`+`kfree` after an RCU grace period, off a kernel-global wq, not an ACPI-owned one |
| GHES estatus-cache RCU replace | `ghes_estatus_cache_add` apei/ghes.c:1082: `xchg_release` swap ghes.c:1124 + `call_rcu(&victim->rcu, ghes_estatus_cache_rcu_free)` ghes.c:1135, free fn ghes.c:1070 |
| GHES hed-list / NMI-list teardown | `synchronize_rcu()` after `list_del_rcu` at ghes.c:1509 (SEA-adjacent list removal path), 1576 (hed unregister), 1811 (nmi remove: "ghes can only be freed after NMI handler finishes") |
| SRCU | none found anywhere in drivers/acpi/ (grep for `srcu_read_lock`/`DEFINE_SRCU`/`synchronize_srcu` returned zero hits) |

#### 8. Sleep/resume asynchrony

| item | file:line |
|---|---|
| `acpi_os_wait_events_complete` fences kacpid_wq+kacpi_notify_wq (+SCI hardirq sync) | defined osl.c:1164; callers: button.c:694, bus.c:655,678, osl.c:1187 (hotplug work), sbshc.c:198,281, tiny-power-button.c:71, sleep.c:437,752,799,827,829,1090, acpica evxface.c:259 (`acpi_remove_notify_handler` global), 319 (per-object), 991 (`acpi_remove_gpe_handler`) |
| `acpi_ec_flush_work` | ec.c:565→`__acpi_ec_flush_work` ec.c:544 (flushes ec_wq+ec_query_wq); called from sleep.c:828 (`acpi_s2idle_restore`) |
| s2idle wake loop `acpi_s2idle_wake` | defined in drivers/acpi/sleep.c:758 (not x86/s2idle.c) — loops `pm_wakeup_pending()`, checks `acpi_any_fixed_event_status_set` sleep.c:779, `acpi_check_wakeup_handlers` sleep.c:785, `acpi_ec_dispatch_gpe()` sleep.c:794, then `acpi_os_wait_events_complete()` sleep.c:799 before rearming SCI wake-irq sleep.c:812-815; wired into ops as `.wake = acpi_s2idle_wake` at drivers/acpi/x86/s2idle.c:642 |
| `acpi_ec_dispatch_gpe` | ec.c:2160, checks `acpi_any_gpe_status_set` + `acpi_ec_work_in_progress` ec.c:2155 |
| Wakeup-event delivery seam | `acpi_pm_wakeup_event` device_pm.c:523 → `pm_wakeup_dev_event(dev,0,acpi_s2idle_wakeup())` (drivers/base/power seam); callers button.c:401,458, battery.c:1038 |
| Wake-Notify → generic wakeup-context callback | `acpi_pm_notify_handler` device_pm.c:529 (dispatched via the normal Notify chain, i.e. on kacpi_notify_wq) invokes `adev->wakeup.context.func()` device_pm.c:550 → e.g. `acpi_pm_notify_work_func` device_pm.c:836 (misleading name — no separate wq, runs inline on kacpi_notify_wq) |
| Suspend-time wq freezing assumptions | none of the 7 ACPI-owned workqueues use `WQ_FREEZABLE` (grep confirms zero hits) — suspend correctness relies entirely on explicit `flush_workqueue`/`acpi_os_wait_events_complete`/`acpi_ec_flush_work` calls at the right PM phases, not on the workqueue freezer |

#### 9. Completions and waits bridging async (load-bearing)

| site | fenced by | file:line |
|---|---|---|
| EC transaction wait | `wait_event_timeout(ec->wait, ec_transaction_completed(ec), guard)` in `ec_guard` | ec.c:751 |
| EC stop wait | `wait_event(ec->wait, acpi_ec_stopped(ec))` | ec.c:1001 |
| PCC OpRegion completion | `wait_for_completion_timeout(&data->done,...)`, completed by `pcc_rx_callback` | acpi_pcc.c:119 / :45 |
| IPMI OpRegion completion | `wait_for_completion(&tx_msg->tx_complete)` (unbounded), completed by `ipmi_msg_handler` or `ipmi_flush_tx_msg` | acpi_ipmi.c:575 / :431,349 |
| CPPC/PCC doorbell ordering | `wait_event(pcc_ss_data->pcc_write_wait_q, write_cmd_id != pcc_write_cnt)`, signalled `wake_up_all` in `send_pcc_cmd` | cppc_acpi.c:1863 / :376 |
| ACPI AML debugger command sync | `wait_event(acpi_aml_io.wait,...)` x2 | acpi_dbg.c:550,558 |
| AML `Wait` opcode (ACPI Event objects, not Linux completions) | `acpi_ex_system_wait_event` | acpica/exsystem.c:232, invoked acpica/exoparg2.c:517 |
| sysfs kobj-release rendezvous | `wait_for_completion(&dn->kobj_done)` / `complete(&dn->kobj_done)` | property.c:665 / device_sysfs.c:78 |
| EC handler-removal fence | `acpi_os_wait_events_complete()` before freeing raw GPE handler | acpica/evxface.c:991 |

#### 10. Everything else async — enumerate or state absence (per primitive)

| primitive | present? | evidence |
|---|---|---|
| tasklets | absent | `grep -rn tasklet drivers/acpi/` → zero hits |
| hrtimer_* API | absent (direct) | zero `hrtimer_*` calls; only a comment justifying `usleep_range`'s internal hrtimer use at osl.c:613 in `acpi_os_sleep` |
| kthreads | present, 2 sites | `acpi_pad.c:227` (`kthread_run`, per-CPU power-saving idle threads, "acpi_pad/%d"); `acpi_dbg.c:427` (`kthread_create`+`wake_up_process` acpi_dbg.c:436, "aml" AML-debugger thread backing `OSL_DEBUGGER_MAIN_THREAD`) |
| `async_schedule*` | present, 1 site (+documented barrier) | `async_schedule_dev_nocall(acpi_scan_clear_dep_fn,...)` scan.c:2454; boot-time drain via `async_synchronize_full()` referenced in comment scan.c:2448 (no other call site in tree) |
| `task_work_add` | present, 1 site | `apei/ghes.c:523` (`ghes_do_memory_failure`→`memory_failure_cb`, TWA_RESUME) |
| `llist_*` | present, 1 file only | `apei/ghes.c` (`ghes_estatus_llist` ghes.c:1257, add/del/reverse at 1268,1273,1371) — no other file in the tree uses `llist_` |
| `kfifo`/`gen_pool` | present, 1 file only | `apei/ghes.c` — CXL CPER fifos (`cxl_cper_fifo`, `cxl_cper_prot_err_fifo`) ghes.c:730,796 and `ghes_estatus_pool` ghes.c:174 backing nearly every allocation in the NMI/task-work paths; no other driver uses either primitive |
| SRCU | absent | (see item 7) |
| `call_rcu`/`synchronize_rcu` | present, ghes.c + osl.c only (osl.c uses `queue_rcu_work` instead of raw `call_rcu`) | see item 7 |
| `flush_work()` (singular, non-wq) | absent | `grep '[^_]flush_work('` → zero hits; only `flush_workqueue` used tree-wide |
| `notifier_block` chains (blocking/atomic) | present, many | `event.c` (global ACPI notifier + genetlink), `hed.c` (HED chain, feeds GHES), `device_pm.c` (PM wakeup notifier), `sleep.c:57` (reboot `tts_notifier`), `nfit/mce.c:87` (MCE decode chain), `acpi_extlog.c:288` (MCE decode chain), `x86/lpss.c:1295` (platform-bus notifier), `processor_driver.c:235` (cpufreq notifier), `ac.c`/`battery.c` (cross-notify via `acpi_notifier_call_chain`), `scan.c:558` (reconfig chain), `acpi_video.c:169`/`battery.c:99` (pm_nb) — all synchronous call-chain dispatch, no queuing of their own |

#### 11. Version-specific facts (v7.0 vs older/widely-documented kernels)

| fact | evidence |
|---|---|
| `WQ_PERCPU` explicitly added to `kacpid_wq`/`kacpi_notify_wq` | commit ec4291f524a3 "ACPI: OSL: Add WQ_PERCPU to alloc_workqueue() users", 2025-11-03, osl.c:1697-1698 — reflects a kernel-wide workqueue-API default flip (per-CPU is no longer implicit for `alloc_workqueue`); `kacpi_hotplug_wq`/`ec_wq`/`nfit_wq` were unaffected because they already use `alloc_ordered_workqueue`/`create_singlethread_workqueue` (inherently `WQ_UNBOUND`) |
| Same migration applied per-driver same day | commit 87c21e240659 "ACPI: EC: Add WQ_PERCPU..." (ec_query_wq, ec.c:2293) and 2817e6fa84ac "ACPI: thermal: Add WQ_PERCPU..." (acpi_thermal_pm_queue, thermal.c:1041), both 2025-11-03 |
| `kacpi_notify_wq` concurrency widened | commit e2ffcda16290 "ACPI: OSL: Allow Notify() handlers to run on all CPUs" (2023-12-06) changed max_active 1→0 at osl.c:1698 — older/widely-documented kernels serialize all Notify() dispatch to one worker at a time; v7.0 allows concurrent Notify handlers |
| GHES NMI/SEA status-check path recently refactored | commits feb2d38013dd, f2edc1fb9c81, b73cf7eaa6ee (all 2026, i.e. within months of v7.0) introduced `ghes_has_active_errors`/`ghes_map_error_status`/`ghes_unmap_error_status` (ghes.c:1411,1434,1458) as a pre-check gate before the NMI-unsafe spool path — not present in older documented GHES writeups |
| RCU-deferred iomem unmap via `rcu_work` | commit 1757659d022b "ACPI: OSL: Implement deferred unmapping of ACPI memory" (2020) — predates v7.0 by years but postdates most "how osl.c works" documentation, which still describes immediate `iounmap` under the mutex; osl.c:382-402 is the current (RCU+workqueue) design |
| EC dual-workqueue (`ec_wq`+`ec_query_wq`) split | introduced by e1191bd4f62d "ACPI / EC: Work around method reentrancy limit in ACPICA for _Qxx" (~2015-era EC "v3" redesign, ec.c file header still says "(v3)") — older docs describing a single EC workqueue are stale; `OSL_EC_POLL_HANDLER`/`OSL_EC_BURST_HANDLER` in acpiosxf.h are leftovers from before that split and are dead in Linux's OSL |

#### 12. Suggested page topics

| page | anchor symbols |
|---|---|
| OSL workqueue & `acpi_os_execute` dispatch | `kacpid_wq`/`kacpi_notify_wq`/`kacpi_hotplug_wq` (osl.c:1697-1699), `acpi_os_execute` osl.c:1092, `acpi_os_wait_events_complete` osl.c:1164 |
| SCI→GPE→Notify async chain | `acpi_ev_sci_xrupt_handler` evsci.c:76, `acpi_ev_gpe_dispatch` evgpe.c:748, `acpi_ev_asynch_execute_gpe_method`/`acpi_ev_asynch_enable_gpe` evgpe.c:455,552, `acpi_ev_notify_dispatch` evmisc.c:161 |
| EC async transaction/event model | `advance_transaction` ec.c:660, `acpi_ec_submit_event`/`acpi_ec_event_handler`/`acpi_ec_event_processor` ec.c:447,1247,1152, `ec_wq`/`ec_query_wq` ec.c:2290,2293 |
| GHES/APEI error-reporting pipeline (NMI/SEA/SDEI/irq_work/gen_pool/kfifo) | `ghes_proc_in_irq` ghes.c:1260, `ghes_notify_nmi` ghes.c:1525, `ghes_estatus_pool`/`ghes_estatus_llist` ghes.c:174,1257, `ghes_do_memory_failure`+`task_work_add` ghes.c:505,523 |
| Hotplug deferral & device-removal ordering | `acpi_hotplug_schedule` osl.c:1192, `acpi_scan_drop_device`/`acpi_device_del_work_fn` scan.c:608,563, `lock_device_hotplug` scan.c:447 |
| Deferred enumeration (`_DEP`, table Load, `_REG`) | `acpi_dev_ready_for_enumeration` scan.c:2533, `acpi_scan_clear_dep_fn` scan.c:2427, `acpi_scan_table_notify` scan.c:2939, `acpi_ev_initialize_op_regions` evregion.c:44 |
| Sleep/resume synchronization fences | `acpi_s2idle_wake` sleep.c:758, `acpi_ec_flush_work` ec.c:565, `acpi_os_wait_events_complete` call sites (item 8) |
| Address-space-handler firmware rendezvous (PCC/IPMI/EINJ/ERST) — cross-reference from EC/GHES pages rather than a standalone page, since each already has a per-area home | `acpi_pcc_address_space_handler` acpi_pcc.c:97, `acpi_ipmi_space_handler` acpi_ipmi.c:524, `einj_timedout` einj-core.c:237, `erst_exec_stall` erst.c:190 |

### Area H: tracepoints, debug output, debugging infrastructure, subsystem-wide sweep — COMPLETE (recorded 2026-07-19)

#### 1. Linux tracepoints — definitions (negative result, confirmed)
- No ACPI-named tracepoint header exists: `find include/trace/events -iname '*acpi*'` → empty; `grep -rl acpi include/trace/events/` → empty.
- No `TRACE_EVENT`/`DECLARE_EVENT_CLASS`/`DEFINE_EVENT`/`CREATE_TRACE_POINTS` anywhere under `drivers/acpi/**`: grep → 0 hits.
- Conclusion: ACPI owns zero Linux tracepoint definitions. All ACPI-relevant tracepoints are defined in other subsystems' headers (see item 3) or generic ones (item 2).

#### 2. Linux tracepoint call sites under drivers/acpi/**
Full sweep `grep -rn "trace_[a-z_]*(" drivers/acpi/` yields exactly two real ftrace tracepoint calls; everything else matching that regex is ACPICA's own internal AML method/opcode tracer (item 8), not a Linux tracepoint.

| Call site | Enclosing function | Tracepoint header | CONFIG gate |
|---|---|---|---|
| `drivers/acpi/acpi_extlog.c:232` `trace_extlog_mem_event(...)` | `extlog_print()` (line 183) | `include/ras/ras_event.h:26` (`TRACE_EVENT(extlog_mem_event,...)`) | `CONFIG_ACPI_EXTLOG` (Kconfig: `drivers/acpi/Kconfig:494`, depends `X86_MCE && X86_LOCAL_APIC && EDAC`, selects `ACPI_APEI`+`ACPI_APEI_GHES`) |
| `drivers/acpi/sleep.c:604` and `:621` `trace_suspend_resume(TPS("acpi_suspend"), acpi_state, true/false)` | `acpi_suspend_enter()` (line 598) | `include/trace/events/power.h:267` (generic PM tracepoint, `#include` at `sleep.c:24`) | No ACPI-specific config; built whenever core tracing is compiled (`CREATE_TRACE_POINTS` in `kernel/trace/power-traces.c`); function itself needs `CONFIG_ACPI_SYSTEM_POWER_STATES_SUPPORT` (sleep.o gated in `drivers/acpi/Makefile`) |

Not dropped, but explicitly re-classified: the other ~25 `trace_`-prefixed identifiers found by the same grep (`acpi_ex_trace_point`, `acpi_ut_trace_ptr/str`, `acpi_trace_point`, `acpi_ex_start/stop_trace_method/opcode`, plus `sysfs.c` param plumbing for `trace_state`/`trace_method_name`) are ACPICA's private execution-trace facility — covered fully in item 8, not Linux tracepoints.

#### 3. Tracepoint seams one hop out (NOT ACPI-owned — observability lives in the adjacent subsystem)
All five below share one header: `include/ras/ras_event.h` (`TRACE_EVENT`: `extlog_mem_event:26`, `mc_event:97`, `arm_event:176`, `non_standard_event:257`, `aer_event:337`); sole `CREATE_TRACE_POINTS` instantiation is `drivers/ras/ras.c:44-46`.

| Chain | ACPI-side call | Adjacent-subsystem trace fire |
|---|---|---|
| GHES→RAS generic | `drivers/acpi/apei/ghes.c:947` in `ghes_do_proc()` (line 894) → `log_non_standard_event()` | `drivers/ras/ras.c:48` → `trace_non_standard_event` at `ras.c:52` |
| GHES→RAS ARM | `drivers/acpi/apei/ghes.c:567` in `ghes_handle_arm_hw_error()` (line 554) → `log_arm_hw_error()` | `drivers/ras/ras.c:56` → `trace_arm_event` at `ras.c:97` |
| GHES(mem)→EDAC | `drivers/acpi/apei/ghes.c:919` in `ghes_do_proc()` → `atomic_notifier_call_chain(&ghes_report_chain,...)`; chain registered via `ghes_register_report_chain()` (`ghes.c:1925`, called from `drivers/edac/ghes_edac.c:492`) | notifier `ghes_edac_report_mem_error` (`drivers/edac/ghes_edac.c:270`) → `edac_raw_mc_handle_error()` (call at `ghes_edac.c:376`, def `drivers/edac/edac_mc.c:917`) → `trace_mc_event` at `edac_mc.c:930` |
| GHES→AER | `drivers/acpi/apei/ghes.c:669` in `ghes_handle_aer()` (line 640, `#ifdef CONFIG_ACPI_APEI_PCIEAER`) → `aer_recover_queue()` (`drivers/pci/pcie/aer.c:1265`) | queues `aer_recover_work_func` (`aer.c:1220`) → `pci_print_aer()` (`aer.c:926`) → `trace_aer_event` at `aer.c:955` |
| ACPI thermal→thermal core | `drivers/acpi/thermal.c:762` in `acpi_thermal_check_fn()` (line 744) → `thermal_zone_device_update()` | `drivers/thermal/thermal_core.c:408` `trace_thermal_zone_trip`, `:640` `trace_thermal_temperature` (defined `drivers/thermal/thermal_trace.h`, not `include/trace/events/`) |
| ACPI cpuidle→cpuidle core | `drivers/acpi/processor_idle.c` registers `acpi_idle_driver` via `cpuidle_register_driver()` (line 1385); core calls back into `acpi_idle_enter*` (lines 616/678/707) | `drivers/cpuidle/cpuidle.c:248` and `:283` `trace_cpu_idle` bracket the ACPI callback — direction is core-calls-into-ACPI, not ACPI-calls-out |
| ACPI cpufreq | no seam found: `grep cpufreq drivers/acpi/cppc_acpi.c drivers/acpi/processor_perflib.c drivers/acpi/processor_throttling.c` → 0 hits | `trace_cpu_frequency` fires only in `drivers/cpufreq/*` (out of `drivers/acpi` tree); CPPC/_PSS data reaches it only via data plumbing, no call chain |
| ACPI battery→power_supply | `drivers/acpi/battery.c:715,762,1089` call `power_supply_changed()` | not a tracepoint — uevent/netlink notification mechanism, explicitly noted so its absence from this list isn't silent truncation |

#### 4. ACPICA debug-output machinery
- `ACPI_DEBUG_PRINT`/`ACPI_DEBUG_PRINT_RAW`: defined 3x under different build modes in `include/acpi/acoutput.h:295-296` (non-COMPILER_VA_MACRO), `:310-319` (VA_MACRO helper form), `:441-442` (non-debug stub, no-op).
- Backing functions: `acpi_debug_print` (`drivers/acpi/acpica/utdebug.c:134-207`), `acpi_debug_print_raw` (`:226-246`); function-entry/exit trace helpers `acpi_ut_trace*`/`acpi_ut_*_exit` (`utdebug.c:263-579`).
- Component IDs (`ACPI_UTILITIES`…`ASL_PREPROCESSOR`): `acoutput.h:21-44` (`ACPI_ALL_COMPONENTS=0x1FFFF` at :43; drivers reserved `0xFFFF0000` at :48).
- Raw levels `ACPI_LV_*`: `acoutput.h:53-102` (exception 53-58, verbosity1 62-77, verbosity2 81-86, verbosity3 90-94, verbose/full 98-102).
- Debug-level macros `ACPI_DB_*` (wrap `ACPI_LV_*` via `ACPI_DEBUG_LEVEL()`): `acoutput.h:115-149`.
- `ACPI_DEBUG_DEFAULT` composition: `acoutput.h:153-155` = `ACPI_LV_INIT | ACPI_LV_DEBUG_OBJECT | ACPI_LV_EVALUATION | ACPI_LV_REPAIR`.
- `CONFIG_ACPI_DEBUG`: `drivers/acpi/Kconfig:396-406` (bool, default y, "~50K" size note, points at acpi.debug_layer/level + debug.rst); build effect is `ccflags-$(CONFIG_ACPI_DEBUG) += -DACPI_DEBUG_OUTPUT` (`drivers/acpi/Makefile:6`), which is the `#ifdef ACPI_DEBUG_OUTPUT` gate in `acoutput.h:234/436`.
- `acpi_dbg_level`/`acpi_dbg_layer` globals declared `include/acpi/acpixf.h:253-254`; module knobs `module_param_cb(debug_layer/debug_level, ...)` at `drivers/acpi/sysfs.c:151-152` (whole block `#ifdef CONFIG_ACPI_DEBUG`, `sysfs.c:17-269`) → `/sys/module/acpi/parameters/debug_layer` and `.../debug_level` (files under `acpi.` param namespace per `drivers/acpi/Makefile:27` comment) → boot params `acpi.debug_layer=`/`acpi.debug_level=`.
- Doc: `Documentation/firmware-guide/acpi/debug.rst` (lists layer/level tables mirroring `acoutput.h`).
- Site counts (`grep -rc ACPI_DEBUG_PRINT`): acpica/ = 394 raw source hits, but 12 of those sit in files never compiled (see item 9 dead-code finding: `nsdumpdv.c`=3, `utcache.c`=1, `uttrack.c`=8, all gated by the always-undefined `ACPI_FUTURE_USAGE` make var) → 382 actually build. Rest of drivers/acpi/ = 8, all in `osl.c` (no other Linux-side file uses this ACPICA macro directly).

#### 5. ACPICA error/warning/info output
- Macros: `ACPI_INFO/WARNING/WARNING_ONCE/EXCEPTION/ERROR/ERROR_ONCE/BIOS_WARNING/BIOS_EXCEPTION/BIOS_ERROR` — `include/acpi/acoutput.h:203-227` (real forms 203-212 under `#ifndef ACPI_NO_ERROR_MESSAGES`, no-op forms 218-227).
- Implementations, all in `drivers/acpi/acpica/utxferror.c` (264 lines): `acpi_error:35`, `acpi_exception:68`, `acpi_warning:109`, `acpi_bios_error:170`, `acpi_bios_exception:204`, `acpi_bios_warning:247`. (`uterror.c` holds lower-level formatting helpers; the public-API entry points are all in `utxferror.c`.)
- Sink: all funnel through `acpi_os_printf()` (`drivers/acpi/osl.c:143`) → `acpi_os_vprintf()` (`osl.c:152`), which is the actual `printk`/`vprintk` landing point.
- Site-count totals (`grep -rc`, acpica vs rest of drivers/acpi): `ACPI_ERROR` 298/0, `ACPI_WARNING` 36/0, `ACPI_INFO` 19/0, `ACPI_EXCEPTION` 72/0, `ACPI_BIOS_ERROR` 7/0, `ACPI_BIOS_WARNING` 9/0, `ACPI_BIOS_EXCEPTION` 2/0 — these macros are 100% acpica-internal; no Linux-side ACPI driver file uses them (they use `acpi_handle_*`/`dev_*`/`pr_*` instead, item 6).

#### 6. Linux-side print helpers
- `acpi_handle_<level>` family: `include/linux/acpi.h:1254-1284` (`emerg/alert/crit/err/warn/notice/info` all wrap `acpi_handle_printk`, lines 1254-1267; `acpi_handle_debug` has a 3-way branch at 1269-1284: `DEBUG` defined → direct printk; else `CONFIG_DYNAMIC_DEBUG` → `_dynamic_func_call(..., __acpi_handle_debug,...)`; else → compiled-out `if(0)` stub, zero cost).
- Backing impl: `acpi_handle_printk()` — `drivers/acpi/utils.c:596`; `__acpi_handle_debug()` (the ddebug-descriptor path) — `utils.c:627`, `EXPORT_SYMBOL` (utils.c:644); both declared `include/linux/acpi.h:1231-1232,1245`.
- `acpi_evaluation_failure_warn()`: declared `include/linux/acpi.h:1233-1234`; defined `drivers/acpi/utils.c:653-659`, `EXPORT_SYMBOL_GPL`; called from `pci_link.c:259,347`, `processor_perflib.c:71,236,328`, `processor_throttling.c:281,414,498,576`.
- Dynamic-debug interplay: only `acpi_handle_debug` participates (per-callsite toggle via `/sys/kernel/debug/dynamic_debug/control`, same mechanism as `pr_debug`); the emerg/alert/crit/err/warn/notice/info variants are always-on `printk`, never dynamic-debug.
- Top files by `acpi_handle_{err,warn,notice,info,debug,emerg,alert,crit}(` count (271 total in tree): `pci_link.c`30, `bus.c`22, `acpi_video.c`21, `x86/s2idle.c`19, `processor_throttling.c`17, `mipi-disco-img.c`16, `scan.c`15, `utils.c`14, `acpi_processor.c`14, `device_pm.c`13.
- Top files by `pr_debug(`: `cppc_acpi.c`45, `tables.c`11, `pptt.c`11, `acpi_dbg.c`10, `utils.c`9, `numa/srat.c`9, `processor_idle.c`8, `arm64/mpam.c`8, `numa/hmat.c`6, `ec.c`6.
- Top files by `dev_dbg(`: `nfit/core.c`35, `pfr_update.c`22, `acpi_processor.c`12, `power.c`7, `pfr_telemetry.c`7, `pci_irq.c`6, `device_pm.c`6, `fan_core.c`5, `scan.c`4, `x86/lpss.c`2 (tied with several at 2).
- `pr_fmt` conventions: 55 of ~85 `.c` files define one: `"ACPI: "` (bare, most common — `bus.c`,`scan.c`,`osi.c`,`sysfs.c`,`tables.c`,`processor_*.c`…), `"ACPI: <subsys>: "` (`ac.c`→AC, `battery.c`, `button.c`, `ec.c`→EC, `video.c`, `watchdog.c`), all-caps table-name style (`"BERT: "`,`"EINJ: "`,`"ERST: "`,`"ACPI PPTT: "`,`"ACPI CPPC: "`,`"ACPI FPDT: "`,`"ACPI MPAM: "`), `"PM: "` (`device_pm.c`), and `KBUILD_MODNAME ": "` (`pci_slot.c`, `platform_profile.c`).

#### 7. AML-visible debug output (Debug object)
- Path: `drivers/acpi/acpica/exdebug.c`, single function `acpi_ex_do_debug_object()` (whole file, ~260 lines, `#ifndef ACPI_NO_ERROR_MESSAGES`).
- Enable gate: fires if `acpi_gbl_enable_aml_debug_object` is set or `ACPI_LV_DEBUG_OBJECT` (`0x00000002`) is set in `acpi_dbg_level` — `ACPI_LV_DEBUG_OBJECT` is part of `ACPI_DEBUG_DEFAULT` (item 4), so `Store(x, Debug)` output is on by default whenever `CONFIG_ACPI_DEBUG=y` (its default).
- Runtime toggle: `acpi_gbl_enable_aml_debug_object` is the `aml_debug_output` module param — `drivers/acpi/sysfs.c:272-275` → `/sys/module/acpi/parameters/aml_debug_output`.
- Output format: literal `"ACPI Debug: "` prefix (optionally `"ACPI Debug: T=0x%8.8X "` timer prefix if `acpi_gbl_display_debug_timer`), then type-formatted value (integer/buffer/string/package/reference), all via `acpi_os_printf()`; macro entry point `ACPI_DEBUG_OBJECT()` = `acoutput.h:212` → `acpi_ex_do_debug_object`.
- Method-tracing interplay: none direct — Debug-object output is independent of the `trace_state` method tracer (item 8), though both ultimately print via `acpi_os_printf`.

#### 8. ACPICA method/opcode tracing (distinct from items 1-3 Linux tracepoints)
- Module params, all in `drivers/acpi/sysfs.c` (under `#ifdef CONFIG_ACPI_DEBUG`, block `154-268`): `trace_method_name` (154, `param_set/get_trace_method_name` 156/199) → `module_param_cb` `214`; `trace_debug_layer`/`trace_debug_level` → `module_param_cb` `215-216` (backed by globals `acpi_gbl_trace_dbg_layer/level`, `include/acpi/acpixf.h:245-246`); `trace_state` → `module_param_call` `267-268` (`param_set_trace_state` `218`, accepts `enable/disable/method/method-once/opcode/opcode-once`).
- `acpi_debug_trace()` ACPICA entry: defined `drivers/acpi/acpica/psxface.c:41-56` (declared `include/acpi/acpixf.h:548-550`); sets `acpi_gbl_trace_method_name/flags/dbg_level/dbg_layer` under the namespace mutex. Also called from `acpica/dbcmds.c:1202` (debugger `trace` command).
- `ACPI_TRACE_POINT(a,b,c,d)` macro = `acpi_trace_point()` (`acoutput.h:434`, no-op at `:457` when `!ACPI_DEBUG_OUTPUT`); `acpi_trace_point()` def `drivers/acpi/acpica/utdebug.c:607-617` → calls `acpi_ex_trace_point()` (`drivers/acpi/acpica/extrace.c:130-148`, prints via `ACPI_DEBUG_PRINT((ACPI_DB_TRACE_POINT,...))`, i.e. lands in the normal debug-print pipe, not a separate sink) and, only `#ifdef ACPI_USE_SYSTEM_TRACER` (never defined anywhere in this tree — `grep -rn ACPI_USE_SYSTEM_TRACER` hits only its own guard at `utdebug.c:614`), the unimplemented `acpi_os_trace_point()` OSL hook (declared `include/acpi/acpiosxf.h:368-371`, no Linux definition exists) — dead branch on Linux.
- Producers of trace points: `acpi_ex_start/stop_trace_method` (`extrace.c:216-313`, called from `acpica/dsmethod.c:304,850` and `dsdebug.c:144`) and `acpi_ex_start/stop_trace_opcode` (`extrace.c:329-369`, called from `acpica/psloop.c:371` and `psparse.c:117`); filtering logic in `acpi_ex_interpreter_trace_enabled()` (`extrace.c:40-75`).
- Output: `"Method Begin/End [\path] execution."` / `"Opcode Begin/End [0xAML] execution."` at `ACPI_DB_TRACE_POINT` level, plus argument dump via `acpi_ex_trace_args()` (`extrace.c:163-199`). Documented in `Documentation/firmware-guide/acpi/method-tracing.rst`.

#### 9. In-kernel AML debugger
- `CONFIG_ACPI_DEBUGGER`: `drivers/acpi/Kconfig:69-76` (bool, `select ACPI_DEBUG`). `CONFIG_ACPI_DEBUGGER_USER`: `Kconfig:80-86` (tristate, `depends on DEBUG_FS`, inside `if ACPI_DEBUGGER`/`endif` block `78-87`; help text names `/sys/kernel/debug/acpi/acpidbg`).
- `drivers/acpi/acpi_dbg.c` (785 lines, builds only as `CONFIG_ACPI_DEBUGGER_USER` — `drivers/acpi/Makefile:108`): circular-FIFO reader/writer core (`acpi_aml_read/write_kern`, `:250-330`; `_user`, `:572-669`); `struct acpi_debugger_ops acpi_aml_debugger` instance at `:733-739` wired to `{create_thread, write_log, read_cmd, wait_command_ready, notify_command_complete}`; registered via `acpi_register_debugger(THIS_MODULE, &acpi_aml_debugger)` at `:759`; debugfs file created at `:754` — `debugfs_create_file("acpidbg", ..., acpi_debugfs_dir, ...)`.
- `struct acpi_debugger`/`struct acpi_debugger_ops` defined `include/linux/acpi.h:141-153`; glue implemented in `drivers/acpi/osl.c` (not `acpi_dbg.c`): `acpi_register_debugger`/`unregister` (`osl.c:887,907`), `acpi_debugger_create_thread` (`:918`), `_wait_command_ready` (`:1008`), `_notify_command_complete` (`:1039`); actual static instance `struct acpi_debugger acpi_debugger` at `osl.c:884`.
- ACPICA debugger core: 14 `db*.c` source files exist in `drivers/acpi/acpica/`, but the Makefile (`drivers/acpi/acpica/Makefile:191-212`) wires only 13 into the build under `acpi-$(CONFIG_ACPI_DEBUGGER)` — `dbcmds, dbconvert, dbdisply, dbexec, dbhistry, dbinput, dbmethod, dbnames, dbobject, dbstats, dbutils, dbxface` + `rsdump.o`. `dbfileio.c` and `dbtest.c` exist but are never compiled — gated by `acpi-$(ACPI_FUTURE_USAGE)` (`Makefile:206-212`), and `ACPI_FUTURE_USAGE` is not a Kconfig symbol anywhere — permanently dead source, kept only for upstream-ACPICA parity. (Same block also disables `utcache.c/utprint.c/uttrack.c/utuuid.c` and, elsewhere, `hwtimer.c:88`/`nsdumpdv.c:113` — relevant back-reference to the item-4 count caveat.)
- Command-loop entry: `acpi_db_user_commands()` — `drivers/acpi/acpica/dbinput.c:1232` (invoked `:1215`); init/teardown `acpi_initialize_debugger`/`acpi_terminate_debugger` — `drivers/acpi/acpica/dbxface.c:395,476` (declared `include/acpi/acpixf.h:968,970`).
- Userspace client: `tools/power/acpi/tools/acpidbg/acpidbg.c` (opens `/sys/kernel/debug/acpi/acpidbg`, interactive REPL). Doc: `Documentation/firmware-guide/acpi/aml-debugger.rst`.

#### 10. debugfs surfaces — exhaustive (`grep -rl debugfs_create drivers/acpi` = exactly these 5 files, nothing else)

| File | dir/parent | Files created |
|---|---|---|
| `drivers/acpi/debugfs.c` (18 lines) | `acpi_debugfs_dir = debugfs_create_dir("acpi", NULL)` at `:18` (extern'd `internal.h:66`) | none itself — dir is a shared root; only consumer is `acpi_dbg.c` (confirmed: `grep -rn acpi_debugfs_dir drivers/acpi` hits only debugfs.c + acpi_dbg.c:756) |
| `drivers/acpi/acpi_dbg.c` | under `acpi_debugfs_dir` | `acpidbg` (`:754`) → `/sys/kernel/debug/acpi/acpidbg` |
| `drivers/acpi/ec_sys.c` (CONFIG_ACPI_EC_DEBUGFS, Kconfig `144-160`) | own top-level dir `debugfs_create_dir("ec", NULL)` (`:112`, sibling of "acpi", not under it) | per-EC subdir `ec<N>/{gpe (x32 RO), use_global_lock (bool RO), io (rw file, mode 0400 or 0600 if `write_support` param set, `:22`)}` — `EC_SPACE_SIZE`=256 byte R/W to EC address space |
| `drivers/acpi/apei/apei-base.c` | own top-level dir `apei_get_debugfs_dir()` = `debugfs_create_dir("apei", NULL)` (`:751-761`, lazy-init static `dapei`, also a sibling, not under "acpi") | dir only; consumed by einj-core.c |
| `drivers/acpi/apei/einj-core.c` (CONFIG_ACPI_APEI_EINJ, `depends on ACPI_APEI && DEBUG_FS`) | `einj_debug_dir` under `apei_get_debugfs_dir()/"einj"` (`:1068`) | `available_error_type`(RO), `error_type`(0600), `error_inject`(0200), and if param-extension/ACPI5: `flags`,`param1..4`,`notrigger` (all RW), EINJv2 `component_id<N>`/`component_syndrome<N>` pairs (`setup_einjv2_component_files():1020-1038`), plus conditional `vendor`(blob,RO), `vendor_flags`(RW), `oem_error`(blob,0600) |

- `einj-cxl.c` is NOT a separate debugfs seam — `drivers/acpi/apei/einj-cxl.c` exports plain functions (`einj_cxl_available_error_type_show`, `einj_cxl_inject_error`, `einj_cxl_inject_rch_error`, `einj_cxl_is_initialized`, all `EXPORT_SYMBOL_NS_GPL(..., "CXL")`) consumed by the CXL core's own debugfs, gated by `CONFIG_ACPI_APEI_EINJ_CXL` (`apei/Kconfig:64-73`, default = `ACPI_APEI_EINJ`).
- `drivers/acpi/apei/erst-dbg.c` is NOT debugfs — it registers a miscdevice `erst_dbg` (`:194-197`) → `/dev/erst_dbg`, not `/sys/kernel/debug/apei/erst-dbg`; `read`/`write`/`unlocked_ioctl` (`APEI_ERST_CLEAR_RECORD`, `APEI_ERST_GET_RECORD_COUNT`) file_ops at `:180-186`. This has been true since the file's introduction (2010, commit `2ff729d506e8`) — confirmed via full `git log -p` scan for "debugfs" in this file's history (no hits). Consistent corroboration: `CONFIG_ACPI_APEI_ERST_DEBUG` (`apei/Kconfig:77-84`) has no `DEBUG_FS` dependency, unlike EINJ.
- `custom_method.c` does NOT exist at v7.0 — `find drivers/acpi -iname '*custom_method*'` → empty; `grep -rl custom_method drivers/acpi Documentation` → empty. Removed by commit `0cc46f1a52b4` "ACPI: Drop the custom_method debugfs interface" (2024-02-16), well before v7.0.

#### 11. sysfs diagnostic surfaces

| Surface | file:line | Notes |
|---|---|---|
| `/sys/firmware/acpi/` root kobj | `drivers/acpi/bus.c:1488,1502` | `acpi_kobj = kobject_create_and_add("acpi", firmware_kobj)` |
| `/sys/firmware/acpi/tables/` + `.../tables/data/` + `.../tables/dynamic/` | `drivers/acpi/sysfs.c:299-522` | `acpi_table_attr_init`(342), bin-file per table (379); `data/` holds `acpi_bert_data_init`(445), `acpi_ccel_data_init`(461) special payload dumps |
| `/sys/firmware/acpi/interrupts/` counters | `sysfs.c:567-931` | `sci`,`sci_not`,`gpe_all`,`gpeXX`,`ff_*` fixed events, `error` — `counter_show`(675)/`counter_set`(732); write cmds on GPE files: `enable`/`disable`/`clear`/`mask`/`unmask` (`:753-767`); global reset via writing `sci` |
| `acpi_mask_gpe=` boot param | `sysfs.c:824-839` (`__setup`) | populates `acpi_masked_gpes_map`, applied at boot by `acpi_gpe_apply_masked_gpes()` (`:841`); interacts with same-named runtime `mask`/`unmask` sysfs commands above |
| `pm_profile` | `sysfs.c:938-943` | `__ATTR_RO`, exposes FADT `Preferred_PM_Profile` |
| `hotplug/<profile>/enabled`,`force_remove` | `sysfs.c:945-1042` | per hotplug-profile kobj (container/memory/etc.), `acpi_sysfs_add_hotplug_profile()` (`:978`) |
| debug/trace module params | `sysfs.c:17-296` | see items 4/8 (`debug_layer`,`debug_level`,`trace_*`,`aml_debug_output`,`acpica_version`) |
| `/sys/firmware/acpi/bgrt/image` (+fields) | `drivers/acpi/bgrt.c:32,76,82` (CONFIG_ACPI_BGRT) | `BIN_ATTR_SIMPLE_RO(image)`, boot splash dump |
| `/sys/firmware/acpi/fpdt/{boot,s3_suspend,s3_resume}_ns` | `drivers/acpi/acpi_fpdt.c:81-105,216-285` (CONFIG_ACPI_FPDT) | FPDT firmware boot/suspend/resume timing records |
| per-device attrs (`path`,`modalias`,`status`,`eject`,`hid`,`cid`,`uid`,`adr`,`sun`,`hrv`,`description`,`real_power_state`,`power_state`) | `drivers/acpi/device_sysfs.c:337-545` | one `DEVICE_ATTR_*` each; `data_node` variants for `_DSD` subnodes (`:45-61`) |
| `pfr_telemetry` (misc device, not sysfs) | `drivers/acpi/pfr_telemetry.c` | ioctl-driven log-level (`PFRT_LOG_ERR/WARN/INFO/VERB`) + telemetry fetch via `/dev/pfrt_log*`, seam-level only |

#### 12. Table injection/override facilities
- `CONFIG_ACPI_TABLE_UPGRADE`: `drivers/acpi/Kconfig:376-384` (depends `BLK_DEV_INITRD && ARCH_HAS_ACPI_TABLE_UPGRADE`, default y); `CONFIG_ACPI_TABLE_OVERRIDE_VIA_BUILTIN_INITRD`: `Kconfig:386-394`.
- Chain: `acpi_table_upgrade()` def `drivers/acpi/tables.c:421-479` (whole feature `#ifdef CONFIG_ACPI_TABLE_UPGRADE`, `:383-665`) → `acpi_table_initrd_scan()`(`:604`)/`acpi_table_initrd_override()`(`:546`) → hooked as `acpi_os_table_override`/`acpi_os_physical_table_override` (`:668-753`); called from arch boot code, outside `drivers/acpi`: `arch/x86/kernel/setup.c:1175`, `arch/arm64/kernel/setup.c:336`, `arch/loongarch/kernel/setup.c:361`. Doc: `Documentation/admin-guide/acpi/initrd_table_override.rst`.
- `acpi_force_table_verification=` — `drivers/acpi/tables.c:784-790` (`early_param`).
- `drivers/acpi/acpi_configfs.c` (286 lines, CONFIG_ACPI_CONFIGFS, `Kconfig:519-525`) confirmed present at v7.0: registers configfs subsystem "acpi" with `table` default group (`:199-212`); `acpi_table_aml_write()` (`:26`) validates SSDT signature and calls `acpi_load_table()` — userspace writes an AML blob to `/config/acpi/table/<name>/aml` to inject an SSDT. Companion doc `Documentation/admin-guide/acpi/ssdt-overlays.rst:168-173`.
- Boot params found by exhaustive `__setup`/`early_param` sweep of `drivers/acpi/*.c` (bus.c itself has none of these — only calls `acpi_debugfs_init()` at `bus.c:1525`):
  - `acpi_rev_override` — `drivers/acpi/osl.c:505-515` (`#ifdef CONFIG_ACPI_REV_OVERRIDE_POSSIBLE`, Kconfig `Kconfig:116-135`).
  - `acpi_no_static_ssdt` — `osl.c:1650-1657` (sets `acpi_gbl_disable_ssdt_table_install`).
  - `acpi_force_table_verification` — `tables.c:784-790`.
  - Adjacent table/parse knobs also in this sweep: `acpi_apic_instance`(`tables.c:782`), `acpi_force_32bit_fadt_addr`(`tables.c:799`), `acpi_rsdp=`(`osl.c:183`), `acpica_no_return_repair`(`osl.c:1667`, disables auto-repair), `acpi_os_name=`(`osl.c:1427`), `acpi_no_auto_serialize`(`osl.c:1443`), `acpi_enforce_resources=`(`osl.c:1482`).
- `osi.c` `acpi_osi=` machinery in two lines: boot cmdline `acpi_osi=` (`osi_setup()`, `drivers/acpi/osi.c:224-239`, `__setup`) and DMI quirks (`acpi_osi_setup_darwin/linux`, `:118-181`) feed a table of enable/disable strings (`acpi_osi_handler()`, `:48-66`) that answer the AML `_OSI` method — pure firmware-compat shim, not itself a debug facility but frequently used as one (`acpi_osi=!*` / `acpi_osi=Linux` for bisecting BIOS bugs).

#### 13. Kconfig census — debug/diagnostic/injection options

| CONFIG | File:line | Purpose |
|---|---|---|
| `ACPI_DEBUG` | `drivers/acpi/Kconfig:396` | Enable `ACPI_DEBUG_PRINT` output (`-DACPI_DEBUG_OUTPUT`) |
| `ACPI_DEBUGGER` | `Kconfig:69` | Build ACPICA in-kernel AML debugger core |
| `ACPI_DEBUGGER_USER` | `Kconfig:80` | Userspace `/sys/kernel/debug/acpi/acpidbg` access |
| `ACPI_EC_DEBUGFS` | `Kconfig:144` | Raw EC address-space R/W via debugfs |
| `ACPI_APEI_EINJ` | `apei/Kconfig:56` | Hardware error injection (EINJ) via debugfs |
| `ACPI_APEI_EINJ_CXL` | `apei/Kconfig:64` | CXL protocol error injection extension to EINJ |
| `ACPI_APEI_ERST_DEBUG` | `apei/Kconfig:77` | ERST persistent-store read/write/clear test interface (miscdevice) |
| `ACPI_CONFIGFS` | `Kconfig:519` | Runtime SSDT injection via `/config/acpi` |
| `ACPI_TABLE_UPGRADE` | `Kconfig:376` | Initrd-based ACPI table override |
| `ACPI_TABLE_OVERRIDE_VIA_BUILTIN_INITRD` | `Kconfig:386` | Same, from built-in initramfs |
| `ARCH_HAS_ACPI_TABLE_UPGRADE` | `Kconfig:373` | Arch enablement bool for the above |
| `ACPI_REV_OVERRIDE_POSSIBLE` | `Kconfig:116` | Allows `acpi_rev_override` cmdline switch (X86 only) |
| `ACPI_CUSTOM_DSDT_FILE`/`ACPI_CUSTOM_DSDT` | `Kconfig:357,369` | Link a replacement DSDT into the kernel image |
| `ACPI_FPDT` | `Kconfig:97` | Firmware boot/suspend/resume timing table exposure |
| `ACPI_BGRT` | `Kconfig:463` | Boot splash image exposure (diagnostic/cosmetic) |
| `ACPI_EXTLOG` | `Kconfig:494` | Enhanced MCA logging + `trace_extlog_mem_event` |
| `ACPI_PFRUT` | `Kconfig:527` | Firmware runtime update + telemetry (misc-device diagnostics) |
| No `ACPI_PICK_*` symbol exists | — | verified negative: grep → 0 hits |

#### 14. Userspace tooling in-tree (`tools/power/acpi/` — complete inventory, 18 files)

| Path | Purpose |
|---|---|
| `tools/power/acpi/tools/acpidump/{apmain,apdump,apfiles}.c` | `acpidump` — dump system ACPI tables to file/stdout (man: `man/acpidump.8`) |
| `tools/power/acpi/tools/acpidbg/acpidbg.c` | `acpidbg` — client for `/sys/kernel/debug/acpi/acpidbg` AML debugger |
| `tools/power/acpi/tools/ec/ec_access.c` | `ec_access` — raw EC byte read/write test tool (pairs with `ec_sys.c`) |
| `tools/power/acpi/tools/pfrut/pfrut.c` | `pfrut` — Platform FW Runtime Update/Telemetry tool via `/dev/pfr_update`,`/dev/pfr_telemetry` (man: `man/pfrut.8`) |
| `tools/power/acpi/os_specific/service_layers/{oslinuxtbl,osunixdir,osunixmap,osunixxf}.c` | Linux OSL shims shared by the tools above (table-lookup, dir, mmap, misc) |
| `tools/power/acpi/common/{cmfsize,getopt}.c` | Shared helper utilities |
| `Makefile`, `Makefile.config`, `Makefile.rules`, `.gitignore` | Build glue (invoked via `tools/Makefile` `make acpi`) |

#### 15. Version-specific facts (v7.0 vs widely-documented older kernels)
- `custom_method.c` removed (2024-02-16, `0cc46f1a52b4`) — long gone by v7.0; any doc referencing `/sys/kernel/debug/acpi/custom_method` is stale.
- `erst-dbg.c` was never debugfs-based (miscdevice since 2010 inception) — a common documentation misconception this digest explicitly corrects (see item 10).
- ACPICA debugger core is 13 compiled files, not 14 — `dbfileio.c`/`dbtest.c` (plus `utcache.c`,`utprint.c`,`uttrack.c`,`utuuid.c`,`hwtimer.c`,`nsdumpdv.c`) are dead source gated by the never-set `ACPI_FUTURE_USAGE`; affects item 4's raw grep counts (394 vs 382 actually built).
- EINJ CXL support is new: `einj-cxl.c` added 2024-03-11 (CXL protocol error injection); EINJ core also gained EINJv2 component-id/syndrome debugfs files and now probes via the newer `struct faux_device` bus (`einj_probe(struct faux_device *)`) rather than a platform_device.
- `acpi_mrrm.c` (Memory Range and Region Mapping table) is very recent — added 2025-05-05, essentially new-in-tree relative to v7.0.
- PFR telemetry/update (`pfr_telemetry.c`, `pfr_update.c`) added 2021-12-22 — post-dates most "classic" ACPI debugging write-ups.
- `acpi_fpdt.c` added 2021-01-29 — likewise a newer diagnostic sysfs surface.
- debugfs is NOT unified: despite `drivers/acpi/debugfs.c` existing since 2010, it backs only `acpi_dbg.c`'s `acpidbg` file; `ec_sys.c` and `apei/apei-base.c` each create their own top-level `debugfs_create_dir(..., NULL)` (`ec/`, `apei/`), so `/sys/kernel/debug/{acpi,ec,apei}/` are three independent trees, not one nested hierarchy — worth calling out explicitly since it's easy to assume otherwise.

#### 16. Suggested page topics (anchor symbols justify each split)

| Page | Anchors |
|---|---|
| ACPICA debug output (`debug_layer`/`debug_level`) | `acoutput.h` `ACPI_DEBUG_PRINT`/`ACPI_DB_*`, `acpixf.h:253-254` globals, `sysfs.c:38-152`, `CONFIG_ACPI_DEBUG`, `debug.rst` |
| ACPICA error/warning/exception reporting | `utxferror.c` (`acpi_error`,`acpi_warning`,`acpi_bios_*`), `acoutput.h:203-227`, `acpi_os_printf` |
| Linux-side `acpi_handle_*`/dynamic-debug | `include/linux/acpi.h:1231-1284`, `utils.c:596-659`, per-file counts (item 6) |
| Method/opcode tracing (`trace_state` et al.) | `sysfs.c:154-268`, `psxface.c:41`, `extrace.c`, `method-tracing.rst` |
| AML Debug object | `exdebug.c:acpi_ex_do_debug_object`, `aml_debug_output` param, `ACPI_LV_DEBUG_OBJECT` |
| In-kernel AML debugger | `acpi_dbg.c`, `osl.c:884-1039` glue, `db*.c` core (13 files), `acpidbg` tool, `aml-debugger.rst` |
| debugfs + sysfs diagnostic surfaces | `debugfs.c`, `ec_sys.c`, `sysfs.c` (tables/interrupts/hotplug), `bgrt.c`, `acpi_fpdt.c`, `device_sysfs.c` |
| Tracepoint-seam page (explicitly "not ACPI's own") | GHES↔RAS/EDAC/AER chains (item 3), `ras_event.h`, thermal/cpuidle seams |
| Table injection & overrides | `ACPI_TABLE_UPGRADE` chain, `acpi_configfs.c`, `osi.c`, boot params (item 12) |
| APEI error-injection/debug (EINJ/ERST) | `einj-core.c`+`einj-cxl.c`, `erst-dbg.c` (miscdevice correction), `apei/Kconfig` |
| EC debugfs (small enough to fold into "debugfs+sysfs" page, or standalone if campaign wants device-class granularity) | `ec_sys.c`, `write_support` param, `CONFIG_ACPI_EC_DEBUGFS` |

Scope note (no silent truncation): every numbered section above reflects a full sweep of `drivers/acpi/**` (including `acpica/`, `apei/`), `include/acpi/`, `include/linux/acpi.h`, both Kconfig files, both Documentation directories, and `tools/power/acpi/`. The only intentional compressions: (a) items 4/5 report `grep -c` totals rather than each of the ~800 individual call sites; (b) item 6's `pr_fmt` list is a representative sample of the 55 files found; (c) item 6's per-file heaviest lists show the top 10-15 by count. Nothing else was dropped.

## Directory organization

Two-level layout `docs/acpi/<group>/`, one group per concern. The six request areas map onto seven content groups (identification split from configuration for row clarity, mirroring the request's own sub-headings), and the invocation's enumeration mandates add two cross-cutting groups:

```
docs/acpi/
├── event/    GPE, fixed events, SCI, GED, GPIO-signaled, _Lxx/_Exx/_EVT/_AEI, relationship overview (10)
├── notify/   Notify() machinery, handler lifecycle, per-value pages, device-class values (7)
├── id/       _ADR/_HID/_CID/_UID/_STA/_CLS, match/modalias (7)
├── config/   _CRS/_PRS/_SRS/_DSM/_DSD (5)
├── core/     namespace/handles/walks, data types, evaluation, errors, acpi_device, glue, enumeration, resource templates (10)
├── pm/       D-states, _PSx, _PRx, power resources, wakeup, PM domain, target states (7)
├── ec/       embedded controller (6)
├── async/    the asynchronous work model: OSL queues, subsystem async census, hotplug deferral, deferred enumeration, sleep fences (5)
└── debug/    tracepoints, debug output, print helpers, method tracing, Debug object, AML debugger, surfaces, injection (8)
```

Rationale: groups follow the request's six areas so every prompt bullet lands in an obvious directory; `async/` and `debug/` exist because the invocation demands the four enumerations as first-class documentation, and burying them as sections of event/EC pages would fragment exactly what was asked to be enumerated in one place. Per-page rules still force every page to enumerate its own tracepoints/debug-prints/async handoffs; the cross-cutting pages own the mechanisms and the subsystem-wide inventories.

## Page catalog

Tags: [request] = a named bullet in prompts/prompt.md; [request+] = added under a prompt "Add more if you see fit" license; [args] = mandated by the commissioning invocation's enumeration requirements; [curated] = campaign-added gap-fill from the Phase 1 digests. Every row is NEW (no docs/acpi/ exists). Anchor file:line values are digest hints — re-verify on disk at v7.0 at write time.

### event/

| page | scope (anchor symbols) | tag |
|---|---|---|
| gpe.md | GPE object model + engine: struct acpi_gpe_event_info (acpica/aclocal.h:448) with dispatch union/flags, acpi_gpe_register_info/block_info/xrupt_info, detection loop acpi_ev_gpe_detect (evgpe.c:347)→acpi_ev_detect_gpe (:625)→acpi_ev_gpe_dispatch (:748) incl. disable-first/edge-clear/level-defer ordering, refcounted enable API (acpi_enable_gpe evxfgpe.c:92, acpi_ev_add/remove_gpe_reference, ACPI_UINT8_MAX cap), hw layer hwgpe.c, acpi_gbl_gpe_lock discipline, GPE Block Devices (acpi_install_gpe_block evxfgpe.c:852), raw handlers + polling fallback (acpi_install_gpe_raw_handler, ACPI_GPE_IS_POLLING_NEEDED), lifecycle from acpi_ev_gpe_initialize to acpi_update_all_gpes at scan start (scan.c:2857); enumerates all three dispatch-union arms incl. ACPI_GPE_DISPATCH_NOTIFY (actypes.h:779) with the implicit-notify producer cited to pm/wakeup.md (review #1); owns the dispatch-time disable/edge-clear/level-defer decision (evgpe.c:772-789 — lxx/exx cite it, review #3); wake API named at seam only (pm/wakeup.md owns wake semantics and the implicit-notify machinery) | [request] |
| fixed-events.md | The 5 fixed events: acpi_fixed_event_info table (utglobal.c:168), ACPI_NUM_FIXED_EVENTS=5, acpi_ev_fixed_event_detect/dispatch (evevent.c:167/236), install acpi_install_fixed_event_handler (evxface.c:583), enable/clear/status API (evxfevnt.c:142-309), boot-time disable-all, unhandled-event ACPI_ERROR (evevent.c:255), ff_* counters cited to debug/diagnostic-surfaces.md | [request] |
| sci.md | SCI end to end: FADT sci_interrupt → acpi_os_install_interrupt_handler (osl.c:556) → request_threaded_irq acpi_irq (osl.c:545,581), acpi_ev_sci_xrupt_handler (evsci.c:76) triple fan-out (fixed detect + GPE detect + acpi_ev_sci_dispatch), host SCI handler list (acpi_install_sci_handler evxface.c:389, acpi_sci_handler_info), acpi_ev_gpe_xrupt_handler for non-SCI GPE interrupts, teardown acpi_ev_remove_all_sci_handlers, sci/sci_not counters cited | [request] |
| lxx.md | _Lxx methods: name decode acpi_ev_match_gpe_method (evgpeinit.c:291, 'L'→ACPI_GPE_LEVEL_TRIGGERED, 2-hex-digit rule from ACPI_NAMESEG_SIZE), level semantics: status cleared only after method completion in acpi_ev_finish_gpe (evgpe.c:578), method-evaluation leg of acpi_ev_asynch_execute_gpe_method (evgpe.c:455) + deferred re-enable via acpi_ev_asynch_enable_gpe | [request] |
| exx.md | _Exx methods: 'E'→ACPI_GPE_EDGE_TRIGGERED decode, the edge consequences on the method leg (no post-method status clear — acpi_ev_finish_gpe's level-only branch), dispatch-type flag bits (actypes.h:776-790), dynamic re-walk on table load acpi_ev_update_gpes (evgpeinit.c:203); the dispatch-time edge clear itself is event/gpe.md's walk (evgpe.c:772-789), cited in one sentence (review #3) | [request] |
| gpio-signaled.md | GPIO-signaled events: acpi_gpiochip_request_interrupts (gpiolib-acpi-core.c:460) walking METHOD_NAME__AEI, struct acpi_gpio_event/acpi_gpio_chip (:39/:57), threaded-only IRQ (request_threaded_irq :224), handler split acpi_gpio_irq_handler (_Lxx/_Exx via acpi_evaluate_object :152) vs acpi_gpio_irq_handler_evt (:161), pin≤255 bound (:362), deferred request list + late_initcall_sync replay and boot-time edge replay (gpiolib-acpi-quirks.c:47-131) | [request] |
| interrupt-signaled.md | Interrupt-signaled (GED, ACPI0013): evged.c whole driver — ged_probe (:141), acpi_ged_request_interrupt (:68) _CRS walk + per-GSI _Lxx/_Exx (case 0...255 :103) with _EVT fallback, struct acpi_ged_event (:48), always-threaded acpi_ged_irq_handler (:56, primary NULL), remove/shutdown ordering | [request] |
| evt.md | _EVT method: index-argument contract, both in-tree callers — GED (evged.c:61) and GPIO events (gpiolib-acpi-core.c:165) — via acpi_execute_simple_method (utils.c:676); when _EVT is chosen over _Lxx/_Exx on each path | [request] |
| aei.md | _AEI as a namespace object (review #5): the method-object-vs-_CRS distinction (event pins declared for the OS to claim), wake-capability flagging, per-pin _Lxx/_Exx/_EVT designation rules; the consuming walk is event/gpio-signaled.md's (acpi_gpiochip_request_interrupts) and the GpioInt descriptor encoding core/resource-templates.md's (struct acpi_resource_gpio, acrestyp.h:355-371) — both cited, not re-walked | [request] |
| overview.md | The requested relationship figure (GPE/fixed events → SCI → _Lxx/_Exx → Notify() → kernel notifiers, plus GPIO-signaled and GED lanes) with a compact recap of each lane; written after its nine siblings; owns no mechanism | [request] |

### notify/

| page | scope (anchor symbols) | tag |
|---|---|---|
| notify.md | Notify() overview: AML_NOTIFY_OP (amlcode.h:76) → acpi_ex_opcode_2A_0T_0R (exoparg2.c:68,96) → acpi_ev_queue_notify_request (evmisc.c:68); value taxonomy paired with kernel constants: ACPI_NOTIFY_* 0x00-0x0F (actypes.h:615-632), the real 0x7F system/device routing boundary ACPI_MAX_SYS_NOTIFY (:806, evmisc.c:89), 0x80-0x84/0xBF/0xC0 debug-name tiers with the kernel's own "Hardware-Specific" label (utdecode.c:440-506); object-type gate acpi_ev_is_notify_object (evmisc.c:35); both entry points into acpi_ev_queue_notify_request named — the AML opcode and the implicit wake notify from the GPE path (evgpe.c:467-486; machinery owned by pm/wakeup.md, review #1) | [request] |
| handlers.md | Handler lifecycle: acpi_install/remove_notify_handler (evxface.c:56/210), ACPI_SYSTEM/DEVICE_NOTIFY lists + ACPI_ROOT_OBJECT global handlers (acpi_gbl_global_notify), struct acpi_notify_info payload, Linux wrappers acpi_dev_install/remove_notify_handler (bus.c:658/673), dispatch context (kacpi_notify_wq via acpi_os_execute — mechanism cited to async/work-model.md), the two callback shapes acpi_op_notify vs acpi_hp_notify (acpi_bus.h:148/168), removal fencing via acpi_os_wait_events_complete (fence mechanism owned by async/work-model.md, cited — review #7) + the not-flushed kacpi_hotplug_wq caveat, userspace fanout section (acpi_bus_generate_netlink_event in event.c, acpi_notifier_call_chain) | [request] |
| bus-check.md | 0x00 Bus Check: ACPI_NOTIFY_BUS_CHECK → acpi_scan_bus_check (scan.c:415), rescan semantics vs Device Check, acpiphp consumer example (acpiphp_hotplug_notify → hotplug_event, acpiphp_glue.c:837/783) | [request] |
| device-check.md | 0x01 Device Check: acpi_scan_device_check (scan.c:387), enumerated-vs-new decision (dev_dbg "Already enumerated"), relation to _STA | [request] |
| device-wake.md | 0x02 Device Wake, value semantics and routing only (review #4): the ACPI_NOTIFY_DEVICE_WAKE gate inside acpi_pm_notify_handler (device_pm.c:529 — which calls pm_wakeup_ws_event :545, NOT acpi_pm_wakeup_event), what a wake notify means per device class, its emitters (implicit wake notify + AML), consumers; the handler body, wakeup-source accounting, and context.func dispatch are pm/wakeup.md's machinery, cited in one paragraph | [request] |
| eject-request.md | 0x03 Eject Request + the _OST protocol: acpi_generic_hotplug_event eject branch (scan.c:422-440) gated by adev->handler->hotplug.enabled (:430; acpi_scan_hotplug_enabled is only the sysfs setter :1995), acpi_scan_hot_remove (:323) with _EJ0 via acpi_evaluate_ej0, acpi_evaluate_ost (utils.c:541) + OST source/status codes (linux/acpi.h:679-704) + full _OST caller census, sysfs eject_store userspace lane (device_sysfs.c:366) | [request+] |
| device-class-values.md | 0x80+ device-class values in vendor-neutral consumers: battery 0x80/0x81 (include/acpi/battery.h:10-12, battery.c:1063 no-default-branch design), AC (ac.c:27,127), thermal 0x81/0x82 (thermal.c:39-43,688), button/lid (button.c:28-29,429,453), video (include/acpi/video.h:34-43), hed.c PNP0C33 degenerate pattern (value-agnostic notifier fanout, hed.c:46-49); the per-driver "Unsupported event" acpi_handle_debug idiom | [request+] |

### id/

| page | scope (anchor symbols) | tag |
|---|---|---|
| adr.md | _ADR: acpi_device_adr macro (acpi_bus.h:263) + pnp.bus_address population via acpi_get_object_info, acpi_find_child_device/check_one_child (glue.c:205/136), acpi_find_child_by_adr no-_STA variant (:212), PCI dev/fn encoding consumer (pci-acpi.c:1340) | [request] |
| hid.md | _HID: acpi_ut_execute_HID (utids.c:35) reached only via acpi_get_object_info (nsxfname.c:226 — the single-call architecture, ACPI_VALID_* bits), acpi_set_pnp_ids/acpi_add_id (scan.c:1388/1329) incl. synthetic HIDs, struct acpi_hardware_id + pnp.ids list, struct acpi_device_id contract (mod_devicetable.h:217, ACPI_ID_LEN=16) | [request] |
| cid.md | _CID: acpi_ut_execute_CID (utids.c:196), unbounded CID list (no ACPI_MAX_CID — verified absent), CID position in match order, PRP0001/ACPI_DT_NAMESPACE_HID special case (internal.h:303, scan.c:2284-2298) | [request] |
| uid.md | _UID: acpi_ut_execute_UID (utids.c:113), acpi_dev_uid_to_integer (utils.c:862), the C11 _Generic match layer acpi_dev_uid_match/acpi_dev_hid_uid_match (acpi_bus.h:883-939), sysfs uid attr | [request] |
| sta.md | _STA: acpi_bus_get_status(_handle) (bus.c:95/77), ACPI_STA_* bits (actypes.h:1212-1217), default-when-absent rule, re-evaluation on every acpi_bus_attach pass (scan.c:2348), enumeration gating (__acpi_match_device presence check, acpi_dev_ready_for_enumeration), x86 override quirk hook acpi_device_override_status | [request+] |
| cls.md | _CLS: acpi_ut_execute_CLS (utids.c:335-402), ACPI_VALID_CLS (actypes.h:1206, tested scan.c:1424), PCI-class matching via acpi_device_id cls/cls_msk (bus.c match loop :952) | [request+] |
| match-modalias.md | Where all ids converge: __acpi_match_device (bus.c:936-976), acpi_bus_match (:1101), acpi_driver_match_device (:1044) shared across bus types, modalias generation create_pnp_modalias/create_of_modalias (device_sysfs.c:136-238); folds in the remaining id objects _SUB (acpi_get_subsystem_id utils.c:306, ACPI_MAX_SUB_BUF_SIZE=9) and _HRV (utils.c:929) with their sysfs attrs | [curated] |

### config/

| page | scope (anchor symbols) | tag |
|---|---|---|
| crs.md | _CRS: acpi_get_current_resources (rsxface.c:166), acpi_walk_resources (:593) + acpi_walk_resource_buffer, Linux acpi_dev_get_resources/__acpi_dev_get_resources (resource.c:1000/947) + per-type converters acpi_dev_resource_memory/io/address_space/ext_address_space/interrupt, struct resource_win translation, buffer lifecycle (ACPI_ALLOCATE_LOCAL_BUFFER freed by the walker; acpi_dev_free_resource_list), validation warnings (resource.c:67-246) | [request] |
| prs.md | _PRS: acpi_get_possible_resources (rsxface.c:208), StartDependentFn/EndDependentFn grouping (ACPI_RESOURCE_TYPE_START/END_DEPENDENT), PNP option building pnpacpi_parse_resource_option_data/pnpacpi_option_resource (rsparser.c:550/471) | [request] |
| srs.md | _SRS: acpi_set_current_resources (rsxface.c:247), acpi_rs_set_srs_method_data (rsutils.c:690), reverse encoding acpi_rs_create_aml_resources (rscreate.c:403), caller pnpacpi_set_resources (pnpacpi/core.c:49-88) + template build (rsparser.c:622,877), acpi_has_method gate | [request] |
| dsm.md | _DSM: acpi_evaluate_dsm (utils.c:771-807, guid/rev/func/argv4 ABI), acpi_evaluate_dsm_typed (acpi_bus.h:64-77), acpi_check_dsm function-0 bitmap (utils.c:821, 64-function cap), vendor-neutral caller pci_acpi_dsm_guid (pci-acpi.c:30,136,1233) | [request] |
| dsd.md | _DSD: acpi_init_properties (property.c:585-638), the GUID families prp_guids/ads_guid/buffer_prop_guid (:40-69), acpi_extract_properties, subnodes acpi_enumerate_nondev_subnodes + struct acpi_data_node (+kobj_done rendezvous), acpi_dev_get_property/acpi_data_get_property (:748/701), PRP0001 + acpi_init_of_compatible, the fwnode ops bridge DECLARE_ACPI_FWNODE_OPS/acpi_device_fwnode_ops (:1738-1768) into device_property_* | [request] |

### core/

| page | scope (anchor symbols) | tag |
|---|---|---|
| namespace-handle.md | acpi_handle identity: void* ≡ struct acpi_namespace_node* (actypes.h:424, aclocal.h:133-156 field groups incl. owner_id), acpi_ns_validate_handle (nsutils.c:528) + ACPI_ROOT_OBJECT sentinel (actypes.h:458 — pointer value, not the root node address), descriptor-type discrimination (ACPI_DESC_TYPE_NAMED vs OPERAND), lookup family acpi_get_handle/acpi_get_parent/acpi_get_next_object/acpi_get_type/acpi_get_name (nsxfname.c:46/124, nsxfobj.c), name geometry (ACPI_NAMESEG_SIZE=4, dynamic path length), namespace locks (ACPI_MTX_NAMESPACE + acpi_gbl_namespace_rw_lock) | [request] |
| namespace-walk.md | Traversal: acpi_walk_namespace (nsxfeval.c:554, reader lock + mutex discipline) → acpi_ns_walk_namespace lock-drop-per-callback DFS (nswalk.c:150,221-255), acpi_get_devices _STA-gated wrapper (:771), the Linux-side contrast: acpi_bus_scan AML walk (scan.c:2721) vs device-model walks acpi_dev_for_each_child (bus.c:1200) | [curated] |
| data-types.md | External object ABI: union acpi_object (actypes.h:908-951) arm by arm with ACPI_TYPE_* counts (:664-704), struct acpi_object_list (:956), struct acpi_buffer (:978), ACPI_ALLOCATE_BUFFER=-1 sentinel + ACPI_FREE/acpi_os_free ownership rules; union acpi_operand_object interior representation as a bounded footnote (acobject.h:404-437, converges with node via embedded struct) | [request] |
| evaluate-object.md | acpi_evaluate_object (nsxfeval.c:163): argument marshaling (ACPI_METHOD_NUM_ARGS=7 truncation :233-240), return-buffer protocol, acpi_evaluate_object_typed (:44, AE_TYPE + conditional free), the synchronous-in-caller-context execution fact (no queuing — verified), acpi_ns_evaluate seam | [request] |
| status-errors.md | The acpi_status error model: acexcep.h class encoding (AE_CODE_MASK families), ACPI_SUCCESS/ACPI_FAILURE (:57-58), acpi_format_exception/acpi_ut_validate_exception (utexcep.c:30/65), Linux-side funnels acpi_util_eval_error (utils.c:26) and acpi_evaluation_failure_warn (:653) with caller census | [curated] |
| acpi-device.md | struct acpi_device (acpi_bus.h:471-497): field groups (handle, pnp, status/flags, power/wakeup pointers, dev embedding, BY-VALUE fwnode :475), creation chain acpi_add_single_object → acpi_init_device_object → acpi_tie_acpi_dev → acpi_device_add → finalize (scan.c:1859/1804/710/738/1847), release path acpi_device_del/acpi_device_release (:527/517), refcount = embedded device kobject (acpi_dev_get/put), handle↔device mapping acpi_fetch_acpi_dev vs refcounted acpi_get_acpi_dev (:655/677 via acpi_attach_data), deferred deletion named at seam (async/hotplug-work.md owns the queue) | [request] |
| companion-glue.md | struct device ↔ acpi_device binding: ACPI_COMPANION/ACPI_COMPANION_SET/ACPI_HANDLE/ACPI_HANDLE_FWNODE (linux/acpi.h:58-63, expansion through to_acpi_device_node/is_acpi_device_node), acpi_bind_one/acpi_unbind_one (glue.c:228/319), multi-physical-node model + physical_node_list/lock, firmware_node/physical_node sysfs links | [curated] |
| default-enumeration.md | What a matched-but-driverless acpi_device becomes: acpi_default_enumeration (scan.c:2245-2282), acpi_create_platform_device (acpi_platform.c:110-195 + forbidden_id_list :26), acpi_is_pnp_device (acpi_pnp.c:374), fixed/early device registration (scan.c:2769/2783), ACPI_RECONFIG_DEVICE_ADD consumers (acpi_platform_notifier) | [curated] |
| evaluation-helpers.md | drivers/acpi/utils.c wrapper family: acpi_evaluate_integer (:247), acpi_evaluate_reference + struct acpi_handle_list (:343), acpi_execute_simple_method (:676), acpi_has_method (:668), acpi_evaluate_reg (:740), acpi_get_subsystem_id pointer, handle-path helpers backing acpi_handle_printk; acpi_evaluate_ost named at seam (notify/eject-request.md owns the protocol); merge-eligible into evaluate-object.md if the checkpoint trims page count (review #11) | [request] |
| resource-templates.md | Consolidated end-to-end mapping (single page by design): ASL ResourceTemplate macros (Interrupt, GpioInt, I2cSerialBus, Memory32Fixed, ...) → AML descriptor encodings → ACPI_RESOURCE_TYPE_* full 26-value set (acrestyp.h:609-635) → struct acpi_resource + union acpi_resource_data (:678/639) → struct resource conversion (acpi_dev_process_resource, resource.c:908); AML⇄struct bridges acpi_rs_convert_aml_to_resources/acpi_rs_create_resource_list/acpi_rs_create_aml_resources (rslist.c:29, rscreate.c:102/403); GpioInt walked end to end; serial-bus/pin descriptor families named with consumers | [request] |

### pm/

| page | scope (anchor symbols) | tag |
|---|---|---|
| d-states.md | D-state model: ACPI_STATE_D0..D3_COLD with the D3_COLD≡D3 alias fact (actypes.h:590-597), struct acpi_device_power/_state/_flags (acpi_bus.h:271-297, write-only power/latency fields fact), construction acpi_bus_get_power_flags (scan.c:1088) + acpi_bus_init_power_state (:1053), validity rules incl. D3cold inference (:1121-1141), power_manageable gate, state_for_enumeration (_DSC) | [request] |
| psx.md | _PSx/_PSC: acpi_dev_pm_explicit_set/_get (device_pm.c:141/48), the ordering/validation engine acpi_device_set_power (:162-294, resources-before-_PS0 on power-up vs _PSx-before-resources on power-down :209-274), acpi_device_get_power (:75, internal-only), acpi_bus_set_power/acpi_bus_init_power/acpi_device_update_power (:296/307/413) | [request] |
| prx.md | _PRx packages: per-state evaluation loop (scan.c:1118, D0..D3hot only), acpi_extract_power_resources (power.c:152) with reference-type filtering + dedup, per-state resources lists, wakeup-package variant (scan.c:922 pointer to pm/wakeup.md) | [request] |
| power-resources.md | PowerResource objects: struct acpi_power_resource (power.c:51-60, embeds acpi_device; system_level/order/ref_count/state/resource_lock/dependents), global acpi_power_resource_list + lock (:70), refcount engine acpi_power_on/off(_unlocked) (:405-465), _ON/_OFF/_STA evaluation (:373/431/198), acpi_power_transition target-first ordering (:852,866), resume re-sync acpi_resume_power_resources (:1031) + acpi_turn_off_unused_power_resources (:1135) + quirk table, sysfs power_resources_D0..D3hot groups (:517-534) | [request] |
| wakeup.md | Device wakeup: _PRW parse acpi_bus_extract_wakeup_device_power_package (scan.c:922), wake GPE init acpi_wakeup_gpe_init→acpi_setup_gpe_for_wake (scan.c:1003, evxfgpe.c:352), struct acpi_device_wakeup(+flags,+context) (acpi_bus.h:332-352), the two independent refcounts (prepare_count under acpi_device_lock in power.c:728/779 vs enable_count under acpi_wakeup_lock in device_pm.c:846-925), acpi_pm_set_device_wakeup (:948), notify plumbing acpi_add_pm_notifier/acpi_pm_notify_handler→context.func (:570/529; the handler calls pm_wakeup_ws_event :545 — review-confirmed), acpi_pm_wakeup_event sibling helper (:523, called from battery/button/lid, not from the handler), the implicit-notify producer path (review #1: acpi_gpe_notify_info aclocal.h:429, ACPI_GPE_DISPATCH_NOTIFY actypes.h:779, the notify loop in acpi_ev_asynch_execute_gpe_method evgpe.c:467-486, setup in acpi_setup_gpe_for_wake evxfgpe.c:358-455), /proc/acpi/wakeup + wakeup.c suspend-path asymmetry comment | [request+] |
| pm-domain.md | ACPI PM domain glue: acpi_general_pm_domain (device_pm.c:1370, inline .detach), acpi_dev_pm_attach (:1443) + sole caller dev_pm_domain_attach (drivers/base/power/common.c:103), the acpi_subsys_* callback family (:1067-1366) wrapping pm_generic_*, fan exclusion, strict-midlayer calls (:1121/1152) | [curated] |
| target-states.md | System-sleep target mapping: _SxD/_SxW via acpi_dev_pm_get_state (device_pm.c:667), acpi_pm_device_sleep_state (:788), _S0W (:507), ACPI_S_STATE bounds (actypes.h:587-588), who consumes the result (PCI/PM callers named as examples) | [curated] |

### ec/

| page | scope (anchor symbols) | tag |
|---|---|---|
| overview.md | EC architecture: struct acpi_ec (internal.h:194-216 field groups), probe chains + precedence (acpi_ec_ecdt_probe bus.c:1413/ec.c:2013, acpi_ec_dsdt_probe ec.c:1809 no-op-if-boot_ec, acpi_ec_ecdt_start ec.c:1870, acpi_ec_probe merge rules ec.c:1680-1722 incl. EC_FLAGS_TRUST_DSDT_GPE), struct acpi_table_ecdt (actbl1.h:1266), EmbeddedControl opregion acpi_ec_space_handler (ec.c:1345) + split no-reg install/_REG call (:1544/1556, ACPI_ADR_SPACE_EC), _GPE vs GpioInt binding selection (ec_install_handlers :1586), first_ec + public ec_read/ec_write/ec_transaction/ec_get_handle (:913-956), 8-tunable module-param table, sbshc.c consumer boundary note | [request] |
| registers.md | Usage model: command_addr/data_addr (the "EC_SC"/"EC_DATA" names exist only in log strings — internal.h:198, ec.c:281-310), accessors acpi_ec_read_status/read_data/write_cmd/write_data (ec.c:277-308), status flag bits ACPI_EC_FLAG_OBF 0x01/IBF 0x02/BURST 0x10/SCI 0x20 (ec.c:42-45) with a 7h register figure, IBF/OBF handshake rules | [request] |
| command-set.md | Command set: enum ec_command ACPI_EC_COMMAND_READ 0x80/WRITE 0x81/BURST_ENABLE 0x82/BURST_DISABLE 0x83/QUERY 0x84 (ec.c:81-87; RD_EC/WR_EC/BE_EC/BD_EC/QR_EC are debug mnemonics only, acpi_ec_cmd_string :316), struct transaction (:155-165, cursors/flags), engine acpi_ec_transaction_unlocked/acpi_ec_transaction (:783/821) with mutex + optional global lock, ec_guard/ec_poll timing (:725/760, ec_delay + 5 restarts) | [request] |
| burst-enable.md | Burst mode: acpi_ec_burst_enable/disable (ec.c:847/857), ACPI_EC_FLAG_BURST gate, the discarded response byte (no 0x90 ack check exists — verified), burst use inside acpi_ec_space_handler multi-byte sequences (:1361), ACPI_EC_UDELAY_GLK | [request] |
| interrupt-model.md | Interrupt flow: acpi_ec_gpe_handler/acpi_ec_irq_handler (ec.c:1328/1335) → acpi_ec_handle_interrupt (:1317) → clear_gpe_and_advance_transaction (:1297) → advance_transaction (:660) IBF/OBF stepping + SCI_EVT detection, enum acpi_ec_event_state 3-state machine + events/queries counters (internal.h:188-215), spurious-IRQ storm detection → polling fallback (acpi_ec_spurious_interrupt :650, ec_storm_threshold, mask/unmask events :410/424), busy_polling/polling_guard mode | [request] |
| qxx.md | _Qxx pipeline: SCI_EVT → acpi_ec_submit_event (:447) → ec_wq "kec" event pump acpi_ec_event_handler (:1247) → acpi_ec_submit_query QR_EC (:1193) → acpi_ec_get_query_handler_by_value (:1064) → ec_query_wq "kec_query" → acpi_ec_event_processor (:1152) evaluating _Qxx via acpi_evaluate_object; struct acpi_ec_query(+handler) (:146-172), handler registration acpi_ec_add/remove_query_handler, query 0 → -ENODATA rule (:1212), ec_event_clearing timing modes, ACPI_EC_MAX_QUERIES concurrency | [request] |

### async/

| page | scope (anchor symbols) | tag |
|---|---|---|
| work-model.md | The OSL execution substrate (mechanism only, per review #8): kacpid_wq/kacpi_notify_wq/kacpi_hotplug_wq creation (osl.c:1697-1699, WQ_PERCPU + max_active facts), acpi_os_execute dispatch switch (:1092,1133) incl. dead OSL_GLOBAL_LOCK/EC_* enum entries and the debugger-thread bypass, acpi_os_execute_deferred (:1126), CPU0 pinning of GPE work (queue_work_on(0,...) :1145), acpi_os_wait_events_complete fence (:1164) with full caller census, no-WQ_FREEZABLE fact | [args] |
| work-census.md | The subsystem-wide asynchronous-design inventory the invocation demands (review #8; every entry points at the page that owns its internals, never re-walking a mechanism): the 7-workqueue table and 11-work-item pipeline census (Area G items 1-2), the interrupt-to-process handoff map at pointer level (item 3), every timer/delayed-work/polling loop (item 5: EC guard/poll, GHES poll timer, NFIT ARS reschedule, AC/battery/video debounce, PAD round-robin, quirk delays), RCU-deferred destruction (item 7: acpi_os_map_remove/queue_rcu_work osl.c:382-402, GHES estatus-cache call_rcu, synchronize_rcu teardowns), load-bearing completions/waits (item 9: EC ec.c:751/1001, PCC acpi_pcc.c:119, IPMI acpi_ipmi.c:575, CPPC doorbell cppc_acpi.c:1863, debugger acpi_dbg.c:550), the per-primitive presence/absence table (item 10: acpi_pad kthreads acpi_pad.c:227, async_schedule scan.c:2454, task_work ghes.c:523, llist/gen_pool/kfifo ghes.c, notifier chains, and the verified negatives — no tasklets, no hrtimers, no SRCU, no bare flush_work), and the PCC/IPMI/EINJ/ERST firmware-rendezvous seam notes | [args] |
| hotplug-work.md | Hotplug deferral and removal ordering: acpi_hotplug_schedule (osl.c:1192) + acpi_hp_work, acpi_hotplug_work_fn (:1183), acpi_queue_hotplug_work (:1220), acpi_device_hotplug (scan.c:442-499) under lock_device_hotplug + acpi_scan_lock + acpi_hp_context_lock, the sysfs eject lane (device_sysfs.c:385), deferred device deletion acpi_scan_drop_device/acpi_device_del_work_fn (scan.c:606/563, namespace-mutex deadlock avoidance), dock_notify inline handling (dock.c:410, no private wq) + post-dock acpi_update_all_gpes, container/memhotplug/pci_root generic routing, the handler-teardown protection story (refcount + INVALID_ACPI_HANDLE) | [args] |
| deferred-enumeration.md | Deferred and lazy enumeration: the _DEP machinery end to end (acpi_scan_check_dep/acpi_scan_add_dep scan.c:2071/2007, ignore/honor tables :848-864, AE_CTRL_DEPTH subtree skip, two-pass acpi_bus_scan + acpi_scan_postponed(_branch) :2721/2589/2570, dep_unmet + acpi_scan_dep_init :1832, resolution acpi_dev_clear_dependencies→acpi_scan_clear_dep :2519/2463, async reprobe async_schedule_dev_nocall(acpi_scan_clear_dep_fn) :2454/2427, gate acpi_dev_ready_for_enumeration :2533 + consumers); deferred table load (Load/LoadTable ops → acpi_tb_notify_table → acpi_bus_table_handler bus.c:1382 → acpi_scan_table_notify → schedule_work(acpi_table_events_fn) scan.c:2939-2951); acpi_reconfig_chain (:558,580,2252); _REG deferral (evrgnini.c:528, evregion.c:44); initrd staging timing (tables.c:421,604,751); fs_initcall motherboard-resource reservation (:2686); subsys_initcall(acpi_init) ordering chain (bus.c:1510-1534) | [args] |
| sleep-fences.md | Sleep/resume synchronization of the async machinery: acpi_s2idle_wake loop (sleep.c:758 — defined in sleep.c, wired at x86/s2idle.c:642) with acpi_any_fixed_event_status_set/acpi_check_wakeup_handlers/acpi_ec_dispatch_gpe/acpi_os_wait_events_complete sequence (:779-815), acpi_ec_flush_work (ec.c:565) from acpi_s2idle_restore (sleep.c:828), EC transaction block/unblock at sleep stages (sleep.c:438,490,665,977,982), acpi_ec_dispatch_gpe in-band GPE service + flush loop (ec.c:2160-2206), ec_no_wakeup + wake-mask deferrals (ec.c:2142/2149), the explicit-flush-not-freezer design fact, wakeup-event seam acpi_pm_wakeup_event→pm_wakeup_dev_event | [args] |

### debug/

| page | scope (anchor symbols) | tag |
|---|---|---|
| tracepoints.md | The authoritative tracepoint enumeration: zero ACPI-owned TRACE_EVENT definitions (grep evidence), exactly two call sites under drivers/acpi — trace_extlog_mem_event (acpi_extlog.c:232, ras_event.h:26, CONFIG_ACPI_EXTLOG) and trace_suspend_resume ×2 (sleep.c:604/621, power.h:267); the seam table one hop out: GHES→RAS (log_non_standard_event/log_arm_hw_error → ras.c:52/97), GHES→EDAC (ghes_report_chain → ghes_edac.c:270 → trace_mc_event edac_mc.c:930), GHES→AER (aer_recover_queue → trace_aer_event aer.c:955), thermal and cpuidle bracket seams, the explicit non-example (battery→power_supply uevent); observing ACPI without tracepoints (dynamic debug, function tracer, method tracing pointer) | [args] |
| acpica-debug-output.md | ACPI_DEBUG_PRINT machinery: acoutput.h triple definition (:295/310/441), acpi_debug_print(_raw) (utdebug.c:134/226), component IDs (:21-48) with the per-file _COMPONENT map for major directories, ACPI_LV_*/ACPI_DB_* levels (:53-149), ACPI_DEBUG_DEFAULT (:153), CONFIG_ACPI_DEBUG + -DACPI_DEBUG_OUTPUT (Makefile:6), acpi_dbg_layer/acpi_dbg_level globals + debug_layer/debug_level params (sysfs.c:151-152) + boot params + debug.rst; site counts (394 raw/382 built acpica, 8 osl.c, dead-file caveat); the ACPICA error family ACPI_ERROR/WARNING/INFO/EXCEPTION/BIOS_* (acoutput.h:203-227, utxferror.c:35-247, 100%-acpica-internal fact) and the acpi_os_printf→acpi_os_vprintf sink (osl.c:143/152) | [args] |
| linux-print-helpers.md | Linux-side printing: acpi_handle_emerg..info wrapping acpi_handle_printk (linux/acpi.h:1254-1267, utils.c:596), acpi_handle_debug 3-way branch (DEBUG/dynamic-debug/if(0), :1269-1284, __acpi_handle_debug utils.c:627), dynamic-debug control interplay, acpi_evaluation_failure_warn (utils.c:653) + caller census, per-file heavy-hitter counts (acpi_handle_* 271 total; pr_debug; dev_dbg tables from Area H item 6), pr_fmt convention families, the EC ec_dbg_*/ec_log_* macro family pointer (ec pages own details) | [args] |
| method-tracing.md | ACPICA method/opcode tracing: trace_state/trace_method_name/trace_debug_layer/trace_debug_level params (sysfs.c:154-268 incl. accepted trace_state values), acpi_debug_trace (psxface.c:41), producers acpi_ex_start/stop_trace_method/opcode (extrace.c:216-369) + filter (:40), ACPI_TRACE_POINT→acpi_trace_point→acpi_ex_trace_point chain (acoutput.h:434, utdebug.c:607, extrace.c:130) with the dead ACPI_USE_SYSTEM_TRACER/acpi_os_trace_point branch fact, output formats, method-tracing.rst | [args] |
| aml-debug-object.md | The ASL Debug object: acpi_ex_do_debug_object (exdebug.c), enable gate acpi_gbl_enable_aml_debug_object OR ACPI_LV_DEBUG_OBJECT with the on-by-default composition fact, aml_debug_output param (sysfs.c:272), "ACPI Debug:" output format per type, ACPI_DEBUG_OBJECT macro (acoutput.h:212), independence from method tracing | [args] |
| aml-debugger.md | In-kernel AML debugger: CONFIG_ACPI_DEBUGGER/_USER (Kconfig:69/80), acpi_dbg.c FIFO core + struct acpi_debugger_ops instance (:733) + debugfs acpidbg file (:754), osl.c glue (acpi_register_debugger :887, create_thread :918, wait/notify :1008/1039, OSL_DEBUGGER_MAIN_THREAD kthread), ACPICA db*.c command core (13-of-14-compiled fact, dead dbfileio/dbtest via ACPI_FUTURE_USAGE; entry acpi_db_user_commands dbinput.c:1232; acpi_initialize/terminate_debugger dbxface.c:395/476), tools/power/acpi acpidbg client, aml-debugger.rst | [args] |
| diagnostic-surfaces.md | The user-visible diagnostic surfaces: /sys/firmware/acpi/ (acpi_kobj created bus.c:1502; var def :1488 — review drift fix) — tables(+data/,dynamic/) (sysfs.c:299-522), interrupts/ counter set + GPE write commands + acpi_mask_gpe= (sysfs.c:567-931,824), pm_profile, hotplug profiles (+neutered force_remove :1006); per-device attrs (device_sysfs.c:337-545); the THREE independent debugfs trees fact — /sys/kernel/debug/acpi (debugfs.c:18, sole consumer acpidbg), /sys/kernel/debug/ec (acpi_ec_add_debugfs ec_sys.c:110, dir create :117 — review drift fix; io/gpe/use_global_lock + write_support), /sys/kernel/debug/apei (apei-base.c:751 + einj-core.c file set); erst-dbg = miscdevice /dev/erst_dbg correction (erst-dbg.c:194); bgrt + fpdt sysfs; the debug-Kconfig census table; tools/power/acpi inventory (acpidump/acpidbg/ec_access/pfrut) | [args] |
| table-injection.md | Table override/injection: CONFIG_ACPI_TABLE_UPGRADE initrd chain (tables.c:421-753, arch call sites, initrd_table_override.rst), configfs SSDT injection acpi_configfs.c (:26,199, /config/acpi/table/<name>/aml, ssdt-overlays.rst), CONFIG_ACPI_CUSTOM_DSDT build-time replacement, the boot-param set (acpi_rev_override osl.c:505, acpi_no_static_ssdt :1650, acpi_force_table_verification tables.c:784, + adjacent knobs acpi_rsdp/acpi_apic_instance/acpica_no_return_repair/acpi_no_auto_serialize/acpi_enforce_resources), acpi_osi= machinery (osi.c:48-239), custom_method removal fact (0cc46f1a52b4) | [args] |

### Fold-in adjudications (topics that do NOT get pages)

union acpi_operand_object internals → core/data-types.md footnote (digest C rejection adopted). fwnode-ops bridge → config/dsd.md section (basics also in core/companion-glue.md). _SUB/_HRV id objects → id/match-modalias.md section. GPE Block Devices, raw GPE handlers, GPE polling mode → event/gpe.md sections. GPE wake-vs-runtime split → event/gpe.md owns register mechanics (enable_for_run/wake masks), pm/wakeup.md owns wake semantics. /sys/firmware/acpi/interrupts counters → debug/diagnostic-surfaces.md (event pages cite). GPIO deferred-request quirks → event/gpio-signaled.md section. EC operation region, ECDT/boot-EC precedence, EC module-param table, sbshc boundary → ec/overview.md sections. EC suspend/s2idle interplay → async/sleep-fences.md (EC pages cite). ec_sys debugfs → debug/diagnostic-surfaces.md. Dock station handling → async/hotplug-work.md section (notify pages cite dock_notify). _OST protocol → notify/eject-request.md owns it; other emitters cite. Hotplug sysfs knobs → debug/diagnostic-surfaces.md. Netlink/acpi_notifier_call_chain userspace fanout → notify/handlers.md section. Device lifecycle/refcounting page suggestion → core/acpi-device.md owns it. Table-load/namespace-mutation page suggestion → async/deferred-enumeration.md owns it. Notify observability page suggestion → debug/tracepoints.md + debug/linux-print-helpers.md own it. Error-model-in-evaluate-object → split kept: core/status-errors.md standalone. PCC/IPMI/EINJ/ERST firmware-rendezvous waits → async/work-census.md seam notes (digest G recommendation adopted; moved by review #8). acpi_pad kthreads, thermal/nfit workqueues, battery/AC/video debounce timers, RCU-deferred iomem unmap, load-bearing completions → enumerated in async/work-census.md with one-line roles and owner pointers only (review #2/#8).

Fold-OUTs (out of campaign scope, recorded so nobody re-litigates): APEI/GHES internals (HEST/BERT/ERST/EINJ mechanics, CPER decode, estatus pipeline) beyond (a) the async enumeration entries in async/work-model.md, (b) the tracepoint seams in debug/tracepoints.md, and (c) the EINJ/erst-dbg debugfs facts in debug/diagnostic-surfaces.md — a future apei campaign owns the rest. drivers/acpi/arm64/ + riscv/ (x86 scope). Driver internals of thermal.c/battery.c/ac.c/button.c/acpi_video.c/fan/processor_*/cppc/nfit/dptf/pmic beyond their roles as vendor-neutral notify/async examples. sleep.c S-state entry mechanics beyond the async fences (pm subsystem campaign territory; Subsystem Map has a separate pm entry). PRM (prmt.c), platform_profile.c, pfr_update/pfr_telemetry beyond one-line mentions in the relevant enumeration tables. gpiolib internals beyond the ACPI event path. pnpacpi beyond _PRS/_SRS consumption. i2c/spi/serdev serial-bus consumers beyond named examples in core/resource-templates.md.

### Projected total and tag census

65 pages: event 10, notify 7, id 7, config 5, core 10, pm 7, ec 6, async 5, debug 8. (64 at first draft; async/work-census.md added by review #8.)
Tag census: 40 [request] (named bullets), 5 [request+] (sta, cls, eject-request, device-class-values, wakeup — added under the request's "Add more if you see fit" licenses), 13 [args] (async 5 + debug 8, mandated by the invocation's enumerations), 7 [curated] (match-modalias, namespace-walk, status-errors, companion-glue, default-enumeration, pm-domain, target-states).

### Overlap boundary rules (seam symbols named)

1. Event core: sci.md owns the interrupt entry and the acpi_ev_sci_xrupt_handler fan-out; gpe.md owns GPE data structures, the detect/dispatch engine, enable refcounting, and the hardware layer (seam: acpi_ev_gpe_detect — sci.md stops where it is called; acpi_ev_gpe_dispatch is gpe.md's); lxx.md and exx.md own the trigger-type decode and the per-trigger-type method legs from acpi_ev_asynch_execute_gpe_method plus the post-method clear/re-enable in acpi_ev_finish_gpe, while the dispatch-time disable/edge-clear decision (evgpe.c:772-789) stays gpe.md's (review #3; seams: acpi_ev_gpe_dispatch for dispatch-time, acpi_ev_finish_gpe for post-method); fixed-events.md owns the fixed-event table and dispatch; overview.md owns only the relationship figure and recaps in one paragraph per lane.
2. GPIO/GED lane: aei.md owns the _AEI object concept only — the consuming walk is gpio-signaled.md's and the descriptor encoding resource-templates.md's (review #5; seams: acpi_gpiochip_request_interrupts, struct acpi_resource_gpio); gpio-signaled.md owns request/dispatch (seam: acpi_gpiochip_request_interrupts); interrupt-signaled.md owns GED (seam: acpi_ged_request_interrupt); evt.md owns _EVT evaluation for both callers (seam: acpi_execute_simple_method applied to the _EVT handle).
3. Notify: notify.md owns opcode-to-queue and the value taxonomy (seam: acpi_ev_queue_notify_request); handlers.md owns install/remove/dispatch context and userspace fanout (seams: acpi_ev_notify_dispatch, acpi_dev_install_notify_handler); per-value pages own semantics and consumers; device-class-values.md owns the 0x80+ catalog; the hotplug legs bus-check.md/device-check.md/eject-request.md own scan semantics (seams: acpi_scan_bus_check, acpi_scan_device_check, acpi_scan_hot_remove); async/hotplug-work.md owns queue and lock machinery (seams: acpi_hotplug_schedule, acpi_device_hotplug).
4. Identification: hid.md owns id-list building and the acpi_get_object_info single-call architecture (seam: acpi_set_pnp_ids); cid.md/uid.md/cls.md recap that architecture in one sentence each; sta.md owns status semantics and gating; adr.md owns address matching (seam: acpi_find_child_device); match-modalias.md owns matching and uevent surfaces (seam: __acpi_match_device).
5. Configuration/resources: core/resource-templates.md owns descriptor encodings, struct acpi_resource, and the converter helpers (seams: struct acpi_resource, acpi_dev_process_resource); crs.md owns the _CRS evaluation/walk flow (seam: acpi_walk_resources); prs.md/srs.md own their methods plus PNP consumers (seam: acpi_set_current_resources for srs.md); dsm.md owns the GUID ABI; dsd.md owns property storage/lookup and the fwnode bridge (seam: acpi_init_properties).
6. Core: namespace-handle.md owns node/handle identity and lookup (seam: acpi_ns_validate_handle); namespace-walk.md owns traversal (seam: acpi_ns_walk_namespace); evaluate-object.md owns the evaluation ABI (seam: acpi_evaluate_object); status-errors.md owns the acpi_status model (seam: acpi_format_exception); evaluation-helpers.md owns the utils.c wrappers (seam: acpi_evaluate_integer and family); acpi-device.md owns struct acpi_device and its lifecycle (seam: acpi_add_single_object); companion-glue.md owns dev↔acpi_device binding (seam: acpi_bind_one); default-enumeration.md owns platform/PNP device creation (seam: acpi_default_enumeration).
7. Power: d-states.md owns encoding and flag construction (seam: acpi_bus_get_power_flags); psx.md owns the explicit-method legs and the ordering engine (seam: acpi_device_set_power — d-states.md cites it in one sentence); prx.md owns package parsing (seam: acpi_extract_power_resources); power-resources.md owns the object, refcounting, and transitions (seam: acpi_power_transition); wakeup.md owns _PRW, GPE arming, the implicit-notify producer (acpi_gpe_notify_info list + the notify loop in acpi_ev_asynch_execute_gpe_method — review #1), and the notify-to-PM plumbing including the acpi_pm_notify_handler body; notify/device-wake.md owns only the notify-value semantics and routing (review #4; seams: acpi_setup_gpe_for_wake, acpi_pm_notify_handler); pm-domain.md owns driver-core glue (seam: acpi_dev_pm_attach); target-states.md owns _SxD/_SxW (seam: acpi_dev_pm_get_state).
8. EC: overview.md owns the struct, probe/precedence, opregion, and params (seams: acpi_ec_probe, acpi_ec_space_handler); registers.md owns port accessors and status bits; command-set.md owns the transaction engine (seam: acpi_ec_transaction); burst-enable.md owns burst commands; interrupt-model.md owns the upcall chain, event-state machine, and storm handling (seam: advance_transaction); qxx.md owns the query pipeline (seam: acpi_ec_submit_query).
9. Async: work-model.md owns queue creation, dispatch, and fences (seams: acpi_os_execute, acpi_os_wait_events_complete); work-census.md owns the subsystem-wide async inventories, each entry citing its owning page and never re-walking a mechanism (review #8); hotplug-work.md owns the hotplug queue and deferred deletion (seam: acpi_queue_hotplug_work); deferred-enumeration.md owns _DEP, table-load, _REG, and init-order deferral (seams: acpi_dev_ready_for_enumeration, acpi_scan_table_notify); sleep-fences.md owns PM-time ordering (seam: acpi_s2idle_wake). Every other page enumerates its own handoffs and cites the owning async/ page by seam symbol, never re-walking the queue mechanics.
10. Debug: tracepoints.md owns the tracepoint truth and seams; acpica-debug-output.md owns ACPI_DEBUG_PRINT and the ACPICA error macros; linux-print-helpers.md owns acpi_handle_*/dynamic debug; method-tracing.md owns the trace_state facility; aml-debug-object.md owns Store-to-Debug; aml-debugger.md owns the debugger; diagnostic-surfaces.md owns sysfs/debugfs/tools; table-injection.md owns overrides. method-tracing.md and aml-debug-object.md cite acpica-debug-output.md for the shared print pipe (ACPI_DEBUG_PRINT/acpi_os_printf) and the ACPI_DEBUG_DEFAULT composition instead of re-documenting them (review #6). The standing per-page instrumentation rule (Execution & verification) cites these pages' mechanisms by symbol.
11. Cross-subsystem boundary (fixed, applies to every row): gpiolib internals beyond the ACPI event path stay in the GPIO subsystem; pnpacpi beyond _PRS/_SRS consumption stays in PNP; PCI consumers appear as usage examples only; the GHES→RAS/EDAC/AER and thermal/cpuidle tracepoint chains are documented at seam level in debug/tracepoints.md with both endpoints cited; drivers/base/power internals are out of scope (pm-domain.md stops at dev_pm_domain_attach). No internal .md cross-links (7f) — ownership is expressed by citing the owning page's anchor symbol.

### Batch order (foundational → derived, ~5 pages per batch; recommended slicing, not a state machine; amended per review #8/#12)

- B1: core/namespace-handle, core/data-types, core/evaluate-object, core/status-errors, core/evaluation-helpers
- B2: core/namespace-walk, core/acpi-device, core/companion-glue, core/default-enumeration, debug/acpica-debug-output
- B3: debug/linux-print-helpers, debug/tracepoints, async/work-model, async/work-census, event/sci
- B4: event/gpe, event/fixed-events, event/lxx, event/exx, core/resource-templates
- B5: event/aei, event/evt, event/gpio-signaled, event/interrupt-signaled, notify/notify
- B6: notify/handlers, async/hotplug-work, event/overview, notify/bus-check, notify/device-check
- B7: notify/eject-request, notify/device-class-values, id/hid, id/cid, id/uid
- B8: id/adr, id/sta, id/cls, id/match-modalias, config/crs
- B9: config/prs, config/srs, config/dsm, config/dsd, async/deferred-enumeration
- B10: pm/d-states, pm/psx, pm/prx, pm/power-resources, pm/wakeup
- B11: notify/device-wake, pm/target-states, pm/pm-domain, ec/overview, ec/registers
- B12: ec/command-set, ec/burst-enable, ec/interrupt-model, ec/qxx, async/sleep-fences
- B13: debug/method-tracing, debug/aml-debug-object, debug/aml-debugger, debug/diagnostic-surfaces, debug/table-injection

Ordering rationale: core vocabulary first (every later page evaluates methods, handles buffers, and touches struct acpi_device); the debug-output pages and the async work-model/census early in B2-B3 because every subsequent page's mandated instrumentation/async enumerations cite their mechanisms; core/resource-templates moved to B4 (review #12) ahead of event/aei and event/gpio-signaled, which consume its descriptor model, and still ahead of config/crs; events before notify (Notify traffic arrives via the GPE/SCI paths); event/overview.md in B6, strictly after all nine siblings (B3-B5); notify/handlers and async/hotplug-work before the hotplug value pages; identification before configuration (matching consumes ids); pm after config; notify/device-wake opens B11, directly after pm/wakeup closes B10 (its seam partner, wakeup first — review #14b); EC late (uses event, notify, and async vocabulary); the remaining debug pages last (they reference everything before them). Review #13 (pull the four mechanism pages into B1) DECLINED: ownership is cited by seam symbol, never by page link (7f), so B1-B2 pages lose nothing by preceding them; the reviewer rated it low-severity and its alternative — an explicit note that citations are by symbol — is adopted in this sentence.

### Adversarial review outcome (2026-07-19)

Reviewer read the full spec and verified 46 anchors on disk across all nine groups: 44 OK (on or within one line), 2 minor drifts (both in diagnostic-surfaces.md: acpi_kobj create site is bus.c:1502 not the :1488 var def; ec debugfs dir create is ec_sys.c:117 with the function at :110) — both corrected in the row. The reverse request-bullet-to-row check PASSED (every named bullet maps). Mandate-compliance verdict: tracepoints and debug mandates satisfied as drafted; the async mandate required amendments #1 and #8, both accepted, and is now satisfied. Fourteen amendments; dispositions:

1. ACCEPTED — implicit-notify producer path (acpi_gpe_notify_info, ACPI_GPE_DISPATCH_NOTIFY, evgpe.c:467-486, acpi_setup_gpe_for_wake) was unowned; deeded to pm/wakeup.md, enumerated as the third dispatch arm in event/gpe.md, named as the second entry point in notify/notify.md, and required in the event/overview.md figure.
2. ACCEPTED — resolved by #8: the mandated timer/RCU/kthread/completion enumerations now live in async/work-census.md's scope.
3. ACCEPTED — dispatch-time edge-clear (evgpe.c:772-789) deeded to event/gpe.md; lxx/exx rescoped to decode + method leg + post-method acpi_ev_finish_gpe (boundary rule 1 updated with both seams).
4. ACCEPTED — notify/device-wake.md rescoped to value semantics/routing; pm/wakeup.md owns the handler body; the pm_wakeup_ws_event-not-acpi_pm_wakeup_event fact pinned in both rows (supersedes the Area E digest's contrary wording).
5. ACCEPTED — event/aei.md rescoped to the object concept; walk and descriptor encoding cited to their owners (boundary rule 2 updated).
6. ACCEPTED — boundary rule 10 gains the shared-print-pipe/ACPI_DEBUG_DEFAULT citation seam for method-tracing.md and aml-debug-object.md.
7. ACCEPTED — notify/handlers.md cites async/work-model.md for the removal fence, not just dispatch context.
8. ACCEPTED — async/work-model.md split: mechanism page + NEW async/work-census.md carrying the subsystem-wide inventory (Area G items 1,2,3,5,7,9,10). Catalog 64→65 rows; async 4→5; [args] 12→13.
9. ACCEPTED-AS-NOTED — event/evt.md and event/aei.md stay (named [request] bullets, distinct concepts); aei rescoped per #5.
10. ACCEPTED-AS-NOTED — debug/aml-debug-object.md stays ([args] first-class facility; subtle enable gate).
11. ACCEPTED-AS-NOTED — core/ stays at 10 rows; core/evaluate-object.md + core/evaluation-helpers.md recorded as the merge-eligible pair for the checkpoint (row annotated).
12. ACCEPTED — core/resource-templates.md moved B8→B4, ahead of event/aei and event/gpio-signaled.
13. DECLINED — reasoning recorded in the ordering rationale (citations are by seam symbol; no page-link dependency exists; reviewer's fallback note adopted).
14. No action — two ordering confirmations (acpica-debug-output in B2 correct; device-wake-after-wakeup correct given #4).

## Execution & verification

- Pipeline: writer → orchestrator check per SKILL.md ("Modes") and `guidelines/passes/02-write.md`/`03-check.md`; the page is the writer's end to end (facts and prose; parity table closed, mechanical exit suite run, evidence persisted into the dossier); fixers run only in fix-list mode (`guidelines/passes/03-lint-fixlist.md`); the orchestrator adjudicates escalations at batch checkpoints and stamps WRITTEN → LINTED in the run log. Certification happens in a separate verify campaign (`acpi-verify`, per `guidelines/passes/04-verify.md`); cadence is a checkpoint question.
- Batches of about five pages, one writer per page, hard checkpoint between batches; writer deaths resume the same agent ("do not redo the research; write the page now from what you have"), fresh writer from the dossier after two failed resumes. Every page gets a dossier at `progress/acpi/<slug>.dossier.md`.
- Model tiers: writers on the strongest available model; fixers mid-tier; inventory mid-tier; adjudication and sign-off never delegated.
- Project-specific writing bans (from the request, on top of Gate A/3a): no hedging wordings; no vendor-specific mechanisms or examples (interpretation under Scope decisions #7); figures per 7g-7i only — never a call-graph/flow-enumeration figure (Scope decisions #4); every ACPI construct named in prose is paired with its kernel representation (Scope decisions #1).
- Section-6 heading (checkpoint decision 3): METHODS on every page except ec/registers.md, ec/command-set.md, ec/burst-enable.md, and ec/interrupt-model.md, which use REGISTERS; the deviation is also noted in the Subsystem Map's ACPI entry.
- Standing per-page instrumentation/async rule (Scope decisions #10): every page enumerates, for the flows it documents, (a) the tracepoints that can fire (for ACPI at v7.0 this is usually a verified negative plus the adjacent-subsystem seams — see Area H), (b) where debug and diagnostic messages print (the ACPI_DEBUG_PRINT component/level for ACPICA paths, the acpi_handle_*/dev_dbg/pr_debug sites for Linux paths, with the enabling knobs), and (c) every asynchronous handoff (which workqueue/IRQ/timer, queued where, executed where). An empty class is stated as a verified negative, never omitted silently.
- Depth: `guidelines/reference/measured-criteria.md` governs (definition-plus-usage per symbol, full site enumeration with verified counts, every hard-coded limit with value and file:line, lifecycle/locking in full). Rule 7e/7j restated by the request: every helper the page catalogs gets a fenced, provenance-stamped excerpt AND a concrete in-tree usage example in DETAILS.
- Write-time rules: every line number in this spec (digests and catalog) is a hint — re-verify on disk at v7.0 at write time. Known drift ledger (facts the Phase 1 inventory established against the stale plan and against widely-documented older kernels; the full verdicts live in each digest's claim-verification item):
  1. EC: no burst "ack 0x90" check exists anywhere (response byte read and discarded); `acpi_ec_burst_enable` begins at ec.c:847, not 850; RD_EC/WR_EC/BE_EC/BD_EC/QR_EC are debug-log mnemonics only (real enum `ACPI_EC_COMMAND_*`); "EC_SC"/"EC_DATA" appear only in log strings (fields are `command_addr`/`data_addr`); the query lookup is `acpi_ec_get_query_handler_by_value` (no `acpi_ec_get_query_handler`); interrupt handlers reach `advance_transaction` through `acpi_ec_handle_interrupt`→`clear_gpe_and_advance_transaction`; no `nr_pending_queries` anywhere (3-state `event_state` machine instead).
  2. Events: `drivers/gpio/gpiolib-acpi.c` no longer exists (split 2025 into gpiolib-acpi-core.c + gpiolib-acpi-quirks.c); `acpi_gpiochip_request_interrupts` is at gpiolib-acpi-core.c:460 (stale plan said :491).
  3. Notify: the system-vs-device routing boundary is 0x7F (`ACPI_MAX_SYS_NOTIFY`), not 0x0F (0x0F is only `ACPI_GENERIC_NOTIFY_MAX` naming); the kernel calls 0xC0-0xFF "Hardware-Specific", never "OEM"; acpiphp's registered callback is `acpiphp_hotplug_notify` (`hotplug_event` is its helper); `acpi_pm_notify_handler` calls `pm_wakeup_ws_event` (device_pm.c:545), not `acpi_pm_wakeup_event` (review-confirmed on disk; supersedes the Area E digest's contrary wording); the eject gate is the inline `adev->handler->hotplug.enabled` check (`acpi_scan_hotplug_enabled` is the sysfs setter); `/sys/firmware/acpi/hotplug/force_remove` is neutered (rejects 1).
  4. Core: `acpi_bus_get_device()` is gone (v5.18); refcounted lookup is `acpi_get_acpi_dev`/`acpi_dev_put`; `ACPI_ROOT_OBJECT` is a sentinel pointer value, not the root node's address; `struct acpi_device` embeds `fwnode` by value; the four `acpi_ut_execute_{HID,CID,UID,CLS}` are reached only via `acpi_get_object_info` (never directly from scan.c); `acpi_get_object_info` dropped _STA (2018) and _SUB (2015) support.
  5. PM: `ACPI_STATE_D3_COLD` is a `#define` alias of `ACPI_STATE_D3` (same raw value as D3hot's successor index — the hot/cold distinction is kernel-side logic); `power.states[]` is a fixed `ACPI_D_STATE_COUNT`=5 array; `struct acpi_power_resource` at power.c:51 CONFIRMED unchanged; `acpi_general_pm_domain.detach` set in the initializer (no runtime assignment).
  6. Async/OSL: `kacpid_wq`/`kacpi_notify_wq` carry `WQ_PERCPU` (2025 flag-migration) and GPE work is pinned to CPU0; `kacpi_notify_wq` allows concurrent Notify handlers since 2023 (max_active 1→0) — older docs describing serialized Notify are stale; `OSL_GLOBAL_LOCK_HANDLER`/`OSL_EC_POLL_HANDLER`/`OSL_EC_BURST_HANDLER` are dead enum entries; `acpi_os_wait_events_complete` flushes kacpid+kacpi_notify only (never kacpi_hotplug_wq); iomem unmap is RCU-deferred via `queue_rcu_work` (2020 redesign); `acpi_s2idle_wake` is defined in sleep.c:758 (x86/s2idle.c only wires it as .wake).
  7. Debug: `custom_method.c` removed 2024 (`0cc46f1a52b4`); `erst-dbg` is a miscdevice `/dev/erst_dbg`, never a debugfs file; `/sys/kernel/debug/{acpi,ec,apei}` are three independent top-level trees; `dbfileio.c`/`dbtest.c` (+utcache/utprint/uttrack/utuuid/hwtimer/nsdumpdv) are never-compiled dead source under `ACPI_FUTURE_USAGE`; `acpi_os_trace_point` has no Linux implementation (`ACPI_USE_SYSTEM_TRACER` never defined).
  8. Tree-wide idiom: allocation sites use `kzalloc_obj`/`kmalloc_obj` typed allocators (2026 conversion) — do not "correct" them to `kzalloc(sizeof(*x))` in prose or expect the old idiom in excerpts.
- Save policy: pages land only under `docs/acpi/<group>/`; no `SUMMARY.md`/`mkdocs.yml` edits; no git commits without an explicit user go.

### Checkpoint (asked and answered 2026-07-19)

The four questions (catalog scope, vendor-neutrality interpretation, section-6 heading, verification cadence) were presented with concrete options and answered; the decisions are recorded verbatim under Scope decisions ("User-confirmed decisions"). Standing consequences: 65-row catalog final; vendor reading per Scope decisions #7; section-6 heading is METHODS on every page EXCEPT ec/registers.md, ec/command-set.md, ec/burst-enable.md, and ec/interrupt-model.md, which use REGISTERS (decision 3 — writer briefs for those four rows carry the override); `acpi-verify` on demand only, so pages end this campaign at LINTED. Production runs only as user-invoked slices under the overwrite guard.

### User amendments (dated; supersede what they name)

(none yet)

## Stale-input reuse map

Sources adjudicated 2026-07-19. There is no prior page corpus for ACPI in this skill (no `docs/acpi/` exists) and no dossier inheritance; rule 7p therefore applies only in its hints-never-evidence sense — no page is derived from a draft, and writers consult none of the sources below.

- `prompts/prompt.md` (the request; untracked local file on the planning machine): not stale — it is the requirements source, extracted verbatim into Scope decisions above. This spec does not depend on the file surviving.
- `prompts/plan.md` (stale 43-page plan for the retired kmemo-devel skill layout): verdict STRUCTURE-MINABLE, DETAILS-UNTRUSTED. What survives as hints: the six-area topic division; the 43 topic slugs and their groupings (event/notify/id/config/core/pm/ec); the consolidated-resource-templates-page instinct; the kernel-correspondence and usage-example mandates (which restate this skill's 7e/7j); the vendor-neutral example set; the batch-ordering instinct (events → notify → id/config → core → pm → EC). What is discarded: its output layout, front-matter and section conventions (superseded wholesale by `guidelines/`), its absolute paths and machine-local references, its draft-corpus pointers (corpora verified absent), its per-page anchor file:line values (hints only; each area digest's claim-verification item records Confirmed/Confirmed-with-caveat/Refuted verdicts, and the refuted ones join the write-time drift ledger). Defect classes observed in it: machine-local absolute paths throughout; anchor line numbers of unknown vintage; section conventions from a dead layout; en-dash/label-colon shapes this skill bans.
- `drafts/` and `kernel-glossary-devel/docs/acpi/` (referenced by the stale plan): ABSENT on the planning machine (verified 2026-07-19). Not inputs; do not search for them on any machine.
