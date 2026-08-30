# numa campaign: physical memory model, nodes/zones, and the page allocator — page catalog and plan

> MIGRATED 2026-07-18 to the campaigns/ layout (SKILL.md, "The three artifacts and the three states"): this file is now the committed, execution-free campaign SPEC. Its former Status section moved to the machine-local run log `progress/numa/log.md` on the machine that ran it; execution state is derived (catalog vs `docs/`), and runs happen only as user-invoked slices under the overwrite guard. This spec predates the machine-portability rule — any absolute path remaining in it is historical record to re-derive from the local environment at dispatch time, and where its older wording conflicts with current `guidelines/`, the guidelines govern.

## Context

- Campaign short name: `numa`. Workspace: the campaign file `campaigns/numa.md` plus the artifact directory `progress/numa/` (the per-page dossiers, `<slug>.dossier.md`, land there and nothing else; parity, lint, and verify records are sections of each dossier).
- Request source: `prompt.md` at the kernel tree root; its constraints and topic list are recorded verbatim below.
- Documented tree: the local Linux checkout, tag `v7.0` (git describe confirmed), commit pin `028ef9c96e96197026887c0f092424679298aae8`. elixir.bootlin.com carries the `v7.0` tag (checked 2026-07-12 against mm/page_alloc.c); every Elixir URL in the campaign embeds `v7.0`.
- Subsystem Map entry: Memory Management → dir `mm`, tag `mm`, section6_heading `none` (pages carry H1, caution blockquote, lead summary, SUMMARY, SPECIFICATIONS, LINUX KERNEL, KERNEL DOCUMENTATION, OTHER SOURCES, DETAILS), kernel_paths per `guidelines/reference/subsystems.md`.
- Output root: `${SKILL_DIR}/docs/mm/`, where `${SKILL_DIR}` is the kernel-glossary skill checkout root (sub-agent briefs carry it as an absolute path at dispatch). The directory exists; the `vma/` group there belongs to an earlier campaign and stays untouched; new group directories must not collide with it.
- Explicitly NOT inputs: prior `progress/` runs (`pagecache`, `reclaim`, `swap`, `vma`, `writeback` — name-availability listing only, nothing read inside); the existing `docs/mm/vma/` pages (neither mined nor modified); `guidelines/reference/samples/*` (style/structure/depth calibration only, never facts); semcode index output (hints only — the on-disk tree at v7.0 is ground truth, rules 7e/7o).
- No prior draft corpus is named by the request → the Draft reuse map section below records "none".

### Request constraints (verbatim from prompt.md)

- "Focus on x86-64 architecture, but don't explicitly mention x86-64 unless it's a detail specific to x86-64"
- "Although the SKILL files require you to find examples in drivers, page cache is a core kernel mechanism and may not be used directly by drivers. So don't bother finding one."
- "For all the behaviors mentioned in the topic list, you must point out all the places in the linux kernel that match the behavior, and cite the source code accordingly. Cite as many and as complete as possible."
- "Make sure to cover as many kernel's internal data structures and helper functions and helper functions to access/maintain those architectural constructs."
- "Also, pay extra attention to things about the life cycle of these objects, like allocation, freeing, locking and reference count for all these objects."
- "Pay extra attention to any asynchronous behaviors, like notifications, work deferring, sleeps, completion, deferring by marking things dirty and processing later. Lazy processing etc."
- "Pay extra attention for state transitions"
- "Pay extra attention to synchronization, mechanism to prevent/avoid race conditions, and locking between page cache and its backing block devices."
- "Ground yourself with local kernel source code. This is from 7.0 and some of the information may have drifted."
- "The pages you're going to create should focus on how Linux kernel internally tracking / representing some of the major constructs. Make sure for every generic mm structures in mm/ and headers they include are covered."
- "You can decide the granularity of pages. Prefer finer granularity whenever possible."
- "Make sure you provide enough context when cross-referencing between source code. Make sure each page is self-contained."
- "!!!IMPORTANT!!!: Don't limit yourself to 100-400 lines per page. There's no bound to how long a page is. Do as detailed as you can."
- "Use semcode tools for planning and research, but do note that semcode isn't always accurate. So when writing final pages, verify things on disk."
- "This topic list is very rough. Curate new pages where you see fit."
- "Make sure to cover all the possible state transitions and semantics of callbacks of each ops structure."

### Topic list (verbatim from prompt.md)

- Physical memory model: Sections; PFN and PFN validity; Converting between PFN and sections; Pageblock and pageblock flags; Migrate types; Look up struct page/struct folio from PFN and vise versa; Sparsemem and flatmem; vmemmap
- Nodes and Zones: pglist_data; Zone watermarks; zonelist, zoneref; one page for each ZONE_* (DMA, DMA32, NORMAL, MOVABLE); lowmem reserves and total reserved pages; PCP lists
- Migrate types: One page for each of the migrate type; You curate this
- GFP flags: You curate this; Pay extra attention to the flags combination for different context (e.g. atomic context, file systems); Also pay extra attention for flags that make the allocation more "forgivable" to watermark limits
- Memalloc flags: You curate this
- The Buddy allocator: PFN and buddy PFN: find_buddy_page_pfn, page_is_buddy and friends; Free lists: struct free_area; PCP of a zone: struct per_cpu_pages
- Page allocator fast path: __alloc_pages; How parameters translates to struct alloc_context; ALLOC_* flags and their meaning. Pay extra attention to which context (e.g. atomic, FS, OOM) needs which flag combination; get_page_from_freelist; details the logic of how it fallbacks to different nodes, zones and migrate types; The effects of watermarks in here; The rmqueue family; Logic of sealing pages; rmqueue_pcplist; Pay extreme attention to the allocation fallback logics and state transitions; Detailed the logic of defrag; Detailed the behavior of stealing pages from other migrate types; Detailed walkthrough of expand(), where it split pages into smaller buddy; Preparation for new pages
- Page freeing path: free_unref_folio; FPI flags; __free_one_page; merging to buddy; detail the logic of the decision to free back to which zone/migrate type/node, in batch or in single pages.

### Request-noted gaps → curation obligations

- Three headings are explicitly delegated: "Migrate types — You curate this", "GFP flags — You curate this", "Memalloc flags — You curate this"; plus the global "This topic list is very rough. Curate new pages where you see fit." Each is a curation obligation, not an omission to mirror.
- Interpretation notes (to confirm at the user checkpoint):
  - "Logic of sealing pages" is read as the migratetype block-claiming/page-stealing logic of the fast path (there is no page-sealing concept in the allocator; mseal is VMA-side and out of scope). It sits next to "stealing pages from other migrate types" in the same bullet list.
  - "free_unref_folio" is read as the PCP freeing entry family; the exact v7.0 spellings come from inventory (the name may have drifted, per the request's own drift warning).
  - The page-cache bullet is generalized: core-mm mechanisms in this campaign need no driver-usage example hunt; call-site censuses still come from wherever the callers live.
  - The "locking between page cache and its backing block devices" bullet is page-cache-specific wording from a sibling campaign's prompt; its live content for this campaign is the general synchronization emphasis (zone->lock vs pcp locks, seqcounts, RCU, isolation vs allocation races).
- Writing consequence of the x86-64 rule: unlike the earlier mm campaign, pages do NOT carry x86-64 in names or prose unless the detail is arch-specific (for example SECTION_SIZE_BITS, vmemmap layout, ZONE_DMA extents).

## Re-entry contract (retrofitted 2026-07-18)

Standing instructions to any executor, on any machine, cold or warm:

1. Confirm the tree: a Linux kernel checkout at tag `v7.0`, commit `028ef9c96e96` (`git describe --tags` at the tree root prints `v7.0`). A different tree voids every anchor in this spec — stop and surface it.
2. Derive campaign state: diff this catalog's 82 (8 groups) rows against their own output paths. The output root `docs/mm/` is SHARED with other mm-area campaigns — never derive state by listing the directory; other campaigns' groups sit beside this one's. A row's page on disk is done (presumed to have completed its writing run's check pass); a missing page is open. There is no shared execution log to consult.
3. Create or reuse the machine-local workspace `progress/numa/` (run log `log.md`, dossiers). It is never committed.
4. Execute ONLY the slice the invoker named — a batch from this spec's batch order (its recommended slicing), or an explicit page list. Given a bare "run numa" with no slice: report the derived state and ask; never pick a slice autonomously. Overwrite guard: a catalog page that already exists on disk is never overwritten silently — stop and surface it.
5. Run the slice per SKILL.md "Modes": one writer per page, briefed per `guidelines/passes/02-write.md` with the page's catalog row, its cluster's boundary rules, and the project-specific bans and write-time cautions from this spec's Execution & verification section; then the orchestrator check per page (`guidelines/passes/03-check.md`); events go to the run log.
6. Promote anything durable — a spec claim the tree refuted, a user amendment, a settled adjudication — into this spec as a dated amendment (or surface it for the waivers files). The run log does not travel.
7. Verification: no cadence is recorded in this spec (it predates the standing checkpoint question), so the skill default applies — `numa-verify` runs only on an explicit user request (`guidelines/passes/04-verify.md`), and its CERTIFIED stamps land in the verify run's log, not in this spec (any older "mirrors into Status" wording is superseded).

## Scope decisions (user-confirmed, checkpoint 2026-07-12)

1. SLOWPATH — FULL SET (user chose "Full slowpath set" over the recommended single overview): alloc/slowpath-overview.md is superseded by five rows — alloc/slowpath.md (the retry state machine), alloc/retry-gates.md, alloc/direct-reclaim.md, alloc/direct-compaction.md, alloc/oom-entry.md. The vmscan/compaction/oom_kill interiors remain out of campaign scope; these pages own the page_alloc.c side only (boundary rule 20).
2. ZONE_DEVICE — PAGE PLUS MACHINERY (user's own wording: "Add this, but also details its machinery"): two rows — zone/zone-device.md (the zone itself) and zone/dev-pagemap.md (struct dev_pagemap / dev_pagemap_ops machinery, callback semantics per the request's ops-structure rule). Anchors verified on disk 2026-07-12 (memremap.h:133/77/68; memremap.c:112/266/374/401/416; mm_init.c:1108; mmzone.h:2006-2019).
3. "Logic of sealing pages" = the migratetype block-claiming/stealing logic (alloc/fallback-claim-steal.md) — confirmed via catalog approval; no page-sealing concept exists in the allocator (mseal is VMA-side, out of scope).
4. Curated extras — KEEP ALL FOUR: free/page-reporting.md, alloc/alloc-nolock.md, alloc/bulk-alloc.md, alloc/compaction-capture.md.
5. CATALOG APPROVED, GENERATION ON HOLD (user chose "Approve catalog, hold generation"): the catalog as amended by decisions 1-4 is approved; no page is generated until the user gives a separate explicit go. Once given, batches run ~5 pages each through the write pipeline (writer with the mechanical exit suite, then the per-page orchestrator check), pages save to docs/mm/ without per-page asks, and git commits still require their own user go.

## Inventory findings (Phase 1)

One compact digest per area, recorded verbatim from the inventory agents. Every line number below is a hint to re-verify on disk at write time, never a citation (semcode indexes can lag; the on-disk tree at v7.0 is ground truth). Version-specific renames/removals get their own prominence.

### Area A: physical memory model (agent A, complete)

#### 1. Core structs

- `struct mem_section` — root per-section descriptor: `section_mem_map` (encoded page* + present/early/online/vmemmap-preinit/zone-device flags), `usage` ptr, optional `page_ext`. `include/linux/mmzone.h:1917-1945`.
- `struct mem_section_usage` — per-section `rcu_head rcu` (RCU-deferred free) + `subsection_map` bitmap (VMEMMAP only) + flexible `pageblock_flags[]` (pageblock migratetype/skip bits live here on SPARSEMEM). `include/linux/mmzone.h:1904-1911`.
- `mem_section[][]` root table — 2-level `struct mem_section **mem_section` (SPARSEMEM_EXTREME, always true on x86-64) vs flat array otherwise; defined `mm/sparse.c:26-32`, extern decl `include/linux/mmzone.h:1957-1960`.
- `memdesc_flags_t` — new 1-word wrapper `{ unsigned long f; }` that is now the type of `page->flags`/`folio->flags`. `include/linux/mm_types.h:38-40`.
- `struct page` — `flags` field is `memdesc_flags_t` (was raw `unsigned long`). `include/linux/mm_types.h:79-80`.
- `struct folio` — mirrors page's first word; `flags` at `include/linux/mm_types.h:401-446` (field 406).
- `struct zone` (relevant fields) — `pageblock_flags` only `#ifndef CONFIG_SPARSEMEM` (`mmzone.h:914-920`, unused on x86-64); `zone_start_pfn`/`spanned_pages`/`present_pages` (`mmzone.h:923,968-969`); `span_seqlock` seqlock_t guarding span fields (`mmzone.h:990`); `contiguous` bool (`mmzone.h:1054`).
- `pg_data_t` (relevant fields) — `first_deferred_pfn` deferred-init cursor (`mmzone.h:1470`), `node_size_lock` spinlock (`mmzone.h:1416`, nests above `zone->lock`/`span_seqlock`).
- `struct vmem_altmap` — reserve/free/align/alloc bookkeeping for device-provided PFNs used to back vmemmap. `include/linux/memremap.h:21-28`.
- `enum pageblock_bits` / `enum migratetype` — bit and type namespaces for pageblock storage. `include/linux/pageblock-flags.h:17-35`; `include/linux/mmzone.h:64-90`.

#### 2. API families

**Model selection & raw PFN↔page (asm-generic/memory_model.h):** `__pfn_to_page`/`__page_to_pfn` — FLATMEM uses `mem_map+`, SPARSEMEM_VMEMMAP uses `vmemmap +/-` pointer arithmetic (the x86-64 path), classic SPARSEMEM decodes via `__pfn_to_section`; `page_to_pfn`/`pfn_to_page` alias these. `include/asm-generic/memory_model.h:18-20,46-47,54-64,73-74`.
**Section/PFN conversions:** `pfn_to_section_nr`/`section_nr_to_pfn` (`mmzone.h:1876-1883`), `__pfn_to_section`/`__nr_to_section` (`mmzone.h:2112-2115`, `1968-1980`), `subsection_map_index`/`pfn_section_valid`/`pfn_section_first_valid` (`mmzone.h:2119-2163`).
**Validity:** `pfn_valid()` (`mmzone.h:2168-2210`, RCU-sched read of section flags), `first_valid_pfn`/`next_valid_pfn`/`for_each_valid_pfn` (`mmzone.h:2212-2261`), `pfn_in_present_section` (`mmzone.h:2265-2270`), `pfn_to_online_page()` (`mm/memory_hotplug.c:346-384`, adds online+zone-device slow path atop `pfn_valid`).
**page/folio ↔ flags-derived metadata:** `memdesc_section/zonenum/nid/is_zone_device` low-level helpers over `memdesc_flags_t` (`include/linux/mm.h:2237-2246`, `mmzone.h:1183-1254`), thin wrappers `page_zonenum`/`folio_zonenum` (`mmzone.h:1189,1194`), `page_to_nid`/`folio_nid` (`mm.h:1990,1995`), `page_zone`/`page_pgdat`/`folio_zone`/`folio_pgdat` (`mm.h:2210-2228`).
**page/folio ↔ pfn:** `folio_pfn`/`pfn_folio` (`mm.h:2257-2265`), `page_folio` macro via `_Generic` (`include/linux/page-flags.h:306-308`), `folio_page` macro (`page-flags.h:319`).
**sparse init / memmap population (mm/sparse.c, mm/sparse-vmemmap.c):** `sparse_init` (`mm/sparse.c:594-625`) → `memblocks_present`/`memory_present` (`244-261`, `217-237`) → `sparse_init_nid` (`532-588`) → `__populate_section_memmap` (VMEMMAP variant `mm/sparse-vmemmap.c:561-582`) → `sparse_init_early_section`/`sparse_init_one_section` (`sparse.c:497-505,289-297`); hotplug: `sparse_add_section`/`section_activate`/`section_deactivate`/`sparse_remove_section` (`933-966,870-912,817-868,968-977`).
**vmemmap page-table walk:** `vmemmap_pte/pmd/pud/p4d/pgd_populate`, `vmemmap_populate_basepages`, `vmemmap_populate_hugepages` (PMD-huge path) (`mm/sparse-vmemmap.c:154-247,299-303,416-466`); HVO variants `vmemmap_populate_hvo`/`vmemmap_undo_hvo`/`vmemmap_wrprotect_hvo` (`386-403,319-356,369-379`); ZONE_DEVICE dedup `vmemmap_populate_compound_pages`/`reuse_compound_section` (`479-557`).
**x86-64 vmemmap arch hooks:** `vmemmap_populate()` entry (chooses PSE huge vs basepages) (`arch/x86/mm/init_64.c:1558-1579`), `vmemmap_set_pmd`/`vmemmap_check_pmd` (`1518-1556`), `vmemmap_free`→`remove_pagetable` (`1273-1280`), `register_page_bootmem_memmap` (`1582-1644`).
**pageblock get/set (mm/page_alloc.c):** `get_pageblock_bitmap`/`pfn_to_bitidx`/`get_pfnblock_bitmap_bitidx` (`363-408`), lock-free `__get_/__set_pfnblock_flags_mask` (READ_ONCE/try_cmpxchg) (`420-436,493-508`), public `get_pfnblock_bit`/`set_pfnblock_bit`/`clear_pfnblock_bit`/`get_pfnblock_migratetype` (`446-483,516-548`), `set_pageblock_order()` (`mm/mm_init.c:1507-1540`).
**deferred/boot memmap init (mm/mm_init.c):** `memmap_init()`→`memmap_init_zone_range`→`memmap_init_range` (`966-1001,941-964,872-939`), `init_unavailable_range` (`845-861`), `overlap_memmap_init` (`801-820`), `reserve_bootmem_region` (`781-798`), `free_area_init` (`1808-1933`), deferred: `deferred_init_memmap`/`deferred_init_memmap_chunk`/`deferred_grow_zone`/`page_alloc_init_late` (`2111-2170,2058-2094,2183-2229,2312+`).
**boot memblock→buddy handoff (mm/memblock.c):** `memmap_init_reserved_pages` (`2243-2290`), `free_low_memory_core_early`/`__free_memory_core`/`__free_pages_memory` (`2292-2312,2226-2241,2200-2224`), `memblock_free_all` (`2340-2350`), `free_unused_memmap` (no-op under VMEMMAP) (`2149-2198`).

#### 3. Lifecycle and locking

- Boot order: `free_area_init()` → `sparse_init()` (allocs `mem_section[]`/usage/memmap via `memblock_alloc*`, marks `SECTION_MARKED_PRESENT`→`SECTION_HAS_MEM_MAP|SECTION_IS_EARLY`) → `memmap_init()` (per-pfn `__init_single_page`, `mm/mm_init.c:581-597`) → `memblock_free_all()` hands non-reserved pages to buddy → `page_alloc_init_late()` runs deferred kthreads.
- Hotplug add: `sparse_add_section` → `section_activate` (usage via `kzalloc(GFP_KERNEL)`, unlike boot's `memblock_alloc`) → `populate_section_memmap`; serialized by `mem_hotplug_lock` (comment, `sparse.c:92`) and `pgdat_resize_lock`/`node_size_lock` (`include/linux/memory_hotplug.h:238-250`, `mmzone.h:1416`).
- Hotplug remove: `section_deactivate` clears `SECTION_HAS_MEM_MAP` first, then `kfree_rcu(ms->usage, rcu)` (`sparse.c:846-849`); readers (`pfn_valid`, `pfn_section_valid`) take `rcu_read_lock_sched()` — no blocking lock on the fast path (`mmzone.h:2196-2209`).
- Zone span reads: `zone_spans_pfn` racing hotplug uses `zone_span_seqbegin/seqretry` over `zone->span_seqlock` (`mm/page_alloc.c:612-616`).
- Deferred struct-page init (`CONFIG_DEFERRED_STRUCT_PAGE_INIT`): static key `deferred_pages` (default true) gates `deferred_pages_enabled()` (`mm/page_alloc.c:332-336`); `defer_init()` sets `pgdat->first_deferred_pfn` once > `PAGES_PER_SECTION` early pages initialized (`mm_init.c:708-743`); `page_alloc_init_late()` spawns one `kthread_run(deferred_init_memmap, …, "pgdatinit%d")` per online node (`mm_init.c:2317-2323`), each thread fans work out via `padata_do_multithreaded(deferred_init_memmap_job)` over `PAGES_PER_SECTION`-aligned chunks (`2149-2160`); completion tracked with `atomic_t pgdat_init_n_undone` + `pgdat_init_all_done_comp`, boot blocks on `wait_for_completion` then `static_branch_disable(&deferred_pages)` permanently (`2017-2025,2326-2332`). `deferred_grow_zone()` does a synchronous top-up under `pgdat_resize_lock` if an allocation outruns the kthread (`2183-2229`).
- VMEMMAP preinit (HVO) hooks: `sparse_vmemmap_init_nid_early()`/`_late()` (`mmzone.h:2085-2099`, impl `mm/sparse-vmemmap.c:592-606`) call into `hugetlb_vmemmap_init_early/late`; sections they claim get `SECTION_IS_VMEMMAP_PREINIT` and are skipped by the generic populate loop in `sparse_init_nid` (`sparse.c:547,556-570`).
- Reserved-page marking: `memmap_init_reserved_pages()`/`reserve_bootmem_region()` set `PageReserved` for memblock reserved/NOMAP regions before the buddy allocator sees memory (`mm/memblock.c:2243-2290`, `mm/mm_init.c:781-798`).

#### 4. Hard-coded limits

- `SECTION_SIZE_BITS = 27` (128 MiB/section, x86-64), `MAX_PHYSMEM_BITS = pgtable_l5_enabled() ? 52 : 46`. `arch/x86/include/asm/sparsemem.h:28-29`.
- `MAX_POSSIBLE_PHYSMEM_BITS = 52`. `arch/x86/include/asm/pgtable_64_types.h:62`.
- `SECTIONS_SHIFT = MAX_PHYSMEM_BITS - SECTION_SIZE_BITS` → 19 (4-level) / 25 (5-level); `NR_MEM_SECTIONS = 1UL<<SECTIONS_SHIFT` → 524,288 / 33,554,432. `include/linux/page-flags-layout.h:31`; `include/linux/mmzone.h:1864`.
- `PFN_SECTION_SHIFT = SECTION_SIZE_BITS-PAGE_SHIFT = 15`; `PAGES_PER_SECTION = 32768`. `mmzone.h:1861-1867`.
- `SUBSECTION_SHIFT = 21` (2 MiB); `PAGES_PER_SUBSECTION = 512`; `SUBSECTIONS_PER_SECTION = 64`. `mmzone.h:1888-1898` (a subsection is exactly one pageblock-worth on x86-64).
- `SECTIONS_PER_ROOT = PAGE_SIZE/sizeof(struct mem_section)` (SPARSEMEM_EXTREME); `NR_SECTION_ROOTS = DIV_ROUND_UP(NR_MEM_SECTIONS,SECTIONS_PER_ROOT)`. `mmzone.h:1948,1954`.
- `MAX_PAGE_ORDER = 10` (no `ARCH_FORCE_MAX_ORDER` on x86); `MAX_ORDER_NR_PAGES=1024`; `NR_PAGE_ORDERS=11`. `mmzone.h:29-38`.
- `PAGE_BLOCK_MAX_ORDER` = `MAX_PAGE_ORDER` (10) unless `CONFIG_PAGE_BLOCK_MAX_ORDER` set. `mmzone.h:41-45`; Kconfig `mm/Kconfig:1081-1099`.
- `pageblock_order` = compile-time `MIN_T(HUGETLB_PAGE_ORDER=9, PAGE_BLOCK_MAX_ORDER=10) = 9` on x86-64 (no `HUGETLB_PAGE_SIZE_VARIABLE`, only PowerPC selects it: `mm/Kconfig:657,300`(ppc)); `pageblock_nr_pages = 512` (2 MiB). `include/linux/pageblock-flags.h:47-75`.
- `NR_PAGEBLOCK_BITS = roundup_pow_of_two(__NR_PAGEBLOCK_BITS)` = 4 (no isolation) or 8 (`CONFIG_MEMORY_ISOLATION`), asserted by `BUILD_BUG_ON` in `mm/page_alloc.c:396-398`; `pageblock-flags.h:17-37`.
- `PAGE_ALLOC_COSTLY_ORDER = 3`. `mmzone.h:62`.
- x86-64 paging: `P4D_SHIFT=39`,`PUD_SHIFT=30`,`PMD_SHIFT=21`,`PTRS_PER_PGD=512`; `HPAGE_SHIFT=PMD_SHIFT`,`HUGETLB_PAGE_ORDER=9`. `arch/x86/include/asm/pgtable_64_types.h:56-80`; `arch/x86/include/asm/page_types.h:20-23`.
- `MAXMEM = 1UL<<MAX_PHYSMEM_BITS`; vmemmap VA bases `__VMEMMAP_BASE_L4/L5`. `pgtable_64_types.h:96,113-114,118`.
- `DIRECT_MAP_PHYSMEM_END` generic fallback `(1ULL<<MAX_PHYSMEM_BITS)-1`. `include/linux/mm.h:103-108`.
- `NODES_SHIFT` default 6 for X86_64 (10 if `MAXSMP`). `arch/x86/Kconfig:1559-1564`.
- `PAGE_SHIFT = CONFIG_PAGE_SHIFT`, `PAGE_SIZE = 1UL<<CONFIG_PAGE_SHIFT`. `include/vdso/page.h:13-15`.

#### 5. Version-specific facts (vs. widely-documented older kernels)

- `page->flags`/`folio->flags` are now `memdesc_flags_t` (struct-wrapped), not a raw `unsigned long`; all bit-shift accessors were pushed behind a new `memdesc_*` layer (`memdesc_section/zonenum/nid/is_zone_device`) shared by page and folio. `mm_types.h:38-40,79-80`; `mm.h:1982-2246`; `mmzone.h:1183-1254`. The old `page_to_section()` function is gone (only a stale comment reference remains, `include/linux/mm_inline.h:648`).
- New Kconfig `CONFIG_PAGE_BLOCK_MAX_ORDER` decouples pageblock order's max from `MAX_PAGE_ORDER`/`ARCH_FORCE_MAX_ORDER`; uses uppercase `MIN_T()` macro. `mm/Kconfig:1081-1099`; `mmzone.h:41-45`; `pageblock-flags.h:60,66,71`.
- `pageblock_bits` restructured: `MIGRATE_ISOLATE` is now a standalone `PB_migrate_isolate` bit (`MIGRATETYPE_AND_ISO_MASK`) instead of an overloaded migratetype value; public API renamed to `get_pfnblock_bit`/`set_pfnblock_bit`/`clear_pfnblock_bit`/`get_pfnblock_migratetype` with `__get_/__set_pfnblock_flags_mask` demoted to file-static lock-free helpers. `pageblock-flags.h:17-45,84-91`; `page_alloc.c:411-548`.
- `CONFIG_SPARSEMEM_VMEMMAP_PREINIT` + `SECTION_IS_VMEMMAP_PREINIT` + `sparse_vmemmap_init_nid_early/_late()` hooks are new: x86-64 opts in via `ARCH_WANT_HUGETLB_VMEMMAP_PREINIT` (`arch/x86/Kconfig:149-151`) wired through `HUGETLB_PAGE_OPTIMIZE_VMEMMAP` (`fs/Kconfig:276-280`). `mmzone.h:2008-2100`.
- HVO (`vmemmap_populate_hvo`, `vmemmap_undo_hvo`, `vmemmap_wrprotect_hvo`) is now integrated directly into the generic vmemmap population file. `mm/sparse-vmemmap.c:319-403`.
- `struct mem_section_usage` gained `struct rcu_head rcu` for RCU-deferred freeing of the pageblock/subsection bitmap; `pfn_valid()` correspondingly reads under `rcu_read_lock_sched()` rather than a spinlock. `mmzone.h:1904-1911,2196-2209`; `sparse.c:846-849`.
- New memmap-overhead accounting hooks `memmap_pages_add()`/`memmap_boot_pages_add()` (`mm/vmstat.c:1037,1042`) instrumented throughout `sparse.c`, `mm_init.c`, `hugetlb_vmemmap.c`, `page_ext.c`.
- `memblock_alloc_or_panic()`/`__memblock_alloc_or_panic()` consolidates the old "`alloc; if(!ptr) panic()`" boilerplate seen in `sparse.c`/`mm_init.c`. `include/linux/memblock.h:431-435`; `mm/memblock.c:1744`.
- Kexec HandOver (KHO) now touches the boot memmap path: `memblock_clear_kho_scratch_only()` called from `memblock_free_all()`, plus `memmap_init_kho_scratch_pages()`. `mm/memblock.c:2340-2350`; `include/linux/memblock.h:615-621`.
- `for_each_valid_pfn()`/`first_valid_pfn()`/`next_valid_pfn()` is a new (sub)section-aware PFN-validity iterator replacing per-pfn `pfn_valid()` polling in loops like `reserve_bootmem_region()`. `mmzone.h:2212-2261`.
- `page_folio()` is implemented via C11 `_Generic()` to preserve const-correctness, rather than a plain inline. `include/linux/page-flags.h:306-308`.
- `PAGE_SHIFT`/`PAGE_SIZE` now derive from `CONFIG_PAGE_SHIFT` rather than an arch-hardcoded literal. `include/vdso/page.h:13-15`.

#### 6. Suggested page topics (agent A)

- HugeTLB Vmemmap Optimization (HVO) — `vmemmap_populate_hvo`/`vmemmap_undo_hvo`/`vmemmap_wrprotect_hvo` (`mm/sparse-vmemmap.c`) plus `mm/hugetlb_vmemmap.c`; ties directly into the new `SPARSEMEM_VMEMMAP_PREINIT` bit this campaign must document anyway.
- ZONE_DEVICE compound-page vmemmap dedup — `vmemmap_populate_compound_pages`/`reuse_compound_section`/`vmemmap_can_optimize` (`mm/sparse-vmemmap.c:479-582`, `mm.h:4551-4576`); Documentation/mm/vmemmap_dedup.rst is the canonical companion doc.
- memdesc/folio flags unification — `memdesc_flags_t`, `memdesc_section/zonenum/nid/is_zone_device` (`mm_types.h:38-40`, `mm.h`, `mmzone.h`); a standalone page would explain the page→folio descriptor-abstraction direction this rename signals.
- Memory hotplug section lifecycle — `sparse_add_section`/`section_activate`/`section_deactivate`/`online_mem_sections` (`mm/sparse.c:627-978`); deep dive on RCU-freed usage maps and subsection (de)activation bitmaps.
- Deferred struct-page init & padata — `deferred_init_memmap`, `padata_do_multithreaded`, `deferred_grow_zone` (`mm/mm_init.c:1985-2231`); the campaign explicitly stresses async behavior and this is the richest example.
- Kexec HandOver (KHO) scratch memory — `memblock_clear_kho_scratch_only`, `memmap_init_kho_scratch_pages`, `kho_scratch_only` (`mm/memblock.c:118,2340-2350`); a genuinely new boot-memmap wrinkle worth its own page.
- SPARSEMEM_EXTREME two-level indexing — `sparse_index_alloc`/`sparse_index_init`/`SECTION_NR_TO_ROOT` (`mm/sparse.c:63-104`; `mmzone.h:1947-1980`); explains why `mem_section` is `**` on x86-64.
- CMA pageblocks — `MIGRATE_CMA`, `init_cma_reserved_pageblock` (`mm/mm_init.c:2233+`); natural follow-on from the MIGRATE_* enum census requested here.

### Area B: nodes and zones (agent B, complete)

#### 1. Core structs

- `struct zone` — watermarks/lowmem_reserve/span/pcp pointers/free_area/locks/flags/compaction+CMA fields/vmstat — `include/linux/mmzone.h:879`.
- `struct pglist_data` (`pg_data_t`) — node_zones[]/node_zonelists[]/nr_zones/node_start_pfn/spanned+present pages/totalreserve_pages/kswapd+kcompactd fields/per-node locks/vmstat — `include/linux/mmzone.h:1381`.
- `struct free_area` — `free_list[MIGRATE_TYPES]` + `nr_free`, one per order — `include/linux/mmzone.h:138`.
- `struct zoneref` — `{zone*, zone_idx}`, one zonelist entry — `include/linux/mmzone.h:1310`.
- `struct zonelist` — `_zonerefs[MAX_ZONES_PER_ZONELIST+1]`, ordered fallback list — `include/linux/mmzone.h:1329`.
- `struct per_cpu_pages` — lock/count/high/high_min/high_max/batch/flags/alloc_factor/expire(NUMA)/free_count/`lists[NR_PCP_LISTS]` — `include/linux/mmzone.h:744`.
- `struct per_cpu_zonestat` — `vm_stat_diff[]`+`stat_threshold`(SMP), `vm_numa_event[]`(NUMA) — `include/linux/mmzone.h:762`.
- `struct per_cpu_nodestat` — `stat_threshold` + `vm_node_stat_diff[]` — `include/linux/mmzone.h:777`.
- `enum zone_type` — DMA/DMA32/NORMAL/HIGHMEM/MOVABLE/DEVICE, `__MAX_NR_ZONES` sentinel — `include/linux/mmzone.h:784`.
- `struct numa_memblk`/`struct numa_meminfo` — {start,end,nid} and `blk[NR_NODE_MEMBLKS]` array used by early NUMA parsing — `include/linux/numa_memblks.h:13`,`:19`.
- `nodemask_t` (via `node_states[NR_NODE_STATES]`) — per-property node bitmaps (N_POSSIBLE…N_GENERIC_INITIATOR) — `include/linux/nodemask.h:384` (array decl `:404`).

#### 2. API families

Node/NODE_DATA: `NODE_DATA()` macro → `node_data[]` (NUMA) `include/linux/numa.h:25-26`; non-NUMA `contig_page_data`/`NODE_DATA` `include/linux/mmzone.h:1677-1681`; `alloc_node_data()` allocates pgdat from local memblock `mm/numa.c:12`; `alloc_offline_node_data()` `mm/numa.c:35`.
Node iteration: `for_each_online_node`/`for_each_node`/`for_each_node_state` `include/linux/nodemask.h:510-512`; `nr_node_ids`/`nr_online_nodes` externs `:441-442`, updated in `node_set_online/offline` `:444-454`; `first_online_pgdat`/`next_online_pgdat`/`for_each_online_pgdat` `mm/mmzone.c:13-25` + `include/linux/mmzone.h:1689-1700`.
Zone helpers: `populated_zone`/`managed_zone`/`zone_end_pfn`/`zone_spans_pfn`/`zone_is_initialized`/`zone_is_empty` `include/linux/mmzone.h:1610-1135` region (1610,1117,1122,1127,1132); watermark accessors `min/low/high/promo_wmark_pages` + `wmark_pages` `:1077-1101`.
free_area_init pipeline: `free_area_init()` top-level driver `mm/mm_init.c:1820`; `free_area_init_node()` per-node `:1714`; `calculate_node_totalpages()` `:1336`; `zone_spanned_pages_in_node()` `:1266`; `zone_absent_pages_in_node()` `:1221`; `free_area_init_core()` `:1593`; `init_currently_empty_zone()` sets `zone->initialized=1` `:1446`; `alloc_node_mem_map()` (FLATMEM) `:1644`; hotplug counterpart `free_area_init_core_hotplug()` `:1550`.
ZONE_MOVABLE sizing: `find_usable_zone_for_movable()` `mm/mm_init.c:335`; `find_zone_movable_pfns_for_nodes()` implements kernelcore=/movablecore=/movable_node `:357-579`; cmdline parsers `cmdline_parse_kernelcore`/`cmdline_parse_movablecore` `:285`,`:302`.
Zonelists: `build_zonerefs_node()` `mm/page_alloc.c:5551`; `find_next_best_node()` (distance+load balancing) `:5616`; `build_zonelists()` NUMA `:5704` / UMA `:5760`; `build_thisnode_zonelists()` (__GFP_THISNODE) `:5692`; `__build_all_zonelists()`/`build_all_zonelists()` entry points `:5797`,`:5889` (only caller of the latter is `mm_core_init()` `mm/mm_init.c:2694`, plus memory-hotplug call sites `mm/memory_hotplug.c:1220,1279,2086`); lookup helpers `first_zones_zonelist`/`next_zones_zonelist`/`__next_zones_zonelist` `include/linux/mmzone.h:1781,1755,1736` (impl `mm/mmzone.c:56`); iterators `for_each_zone_zonelist(_nodemask)` `:1822,1800`; `zonelist_zone`/`zonelist_zone_idx`/`zonelist_node_idx` `:1721-1734`.
Watermark setup chain: `boost_watermark()` `mm/page_alloc.c:2193`; `calculate_min_free_kbytes()` (sqrt formula) `:6545`; `__setup_per_zone_wmarks()`/`setup_per_zone_wmarks()` `:6433`,`:6504`; `init_per_zone_wmark_min()` (`postcore_initcall`) `:6561` (line `:6577`).
Lowmem reserve: `setup_per_zone_lowmem_reserve()` `mm/page_alloc.c:6388`; `calculate_totalreserve_pages()` `:6338`.
PCP sizing: `zone_batchsize()` `:5922`; `zone_highsize()` `:5970`; `zone_set_pageset_high_and_batch()`/`__zone_set_pageset_high_and_batch()` `:6082`,`:6066`; `setup_zone_pageset()` (per-zone alloc) `:6114`; `zone_pcp_init()` (boot-time stub wiring) `:6209`; `setup_per_cpu_pageset()` (post-percpu-up real allocation) `:6181`; `order_to_pindex`/`pindex_to_order` `:684`,`:703`.
NUMA memblks/distance: `numa_add_memblk()`/`numa_add_reserved_memblk()` `mm/numa_memblks.c:200`,`:222`; `numa_cleanup_meminfo()` `:237`; `numa_register_meminfo()` (sets `node_possible_map`) `:398`; `numa_memblks_init()` top-level `:445`; `numa_set_distance()`/`__node_distance()`/`numa_reset_distance()` `:105`,`:127`,`:40`; `numa_fill_memblks()` `:509`; ACPI SLIT feeds it via `drivers/acpi/numa/srat.c:348`.
Topology/distance macros: `node_distance()` generic default `include/linux/topology.h:50`, x86-64 override → `__node_distance` `arch/x86/include/asm/topology.h:80-81`; `for_each_node_numadist()` `include/linux/topology.h:307`; `RECLAIM_DISTANCE`/`node_reclaim_distance` `:59,73`.

#### 3. Lifecycle and locking

- Boot order (x86-64): ACPI SRAT/SLIT → `numa_memblks_init()` (`mm/numa_memblks.c:445`) → `numa_register_meminfo()` sets `node_possible_map` (`:398`) → `arch/x86/mm/numa.c:146` loops nodes calling `alloc_node_data()`+`node_set_online()` → `mm_core_init_early()` (`mm/mm_init.c:2683`) calls `free_area_init()` (`:1820`, per-node via `free_area_init_node` `:1714`) → `mm_core_init()` (`:2694`) calls `build_all_zonelists(NULL)` then `memblock_free_all()` (populates `managed_pages`/buddy) → `setup_per_cpu_pageset()` swaps `boot_pageset`/`boot_zonestats` for real per-zone percpu sets → `postcore_initcall(init_per_zone_wmark_min)` (`mm/page_alloc.c:6577`) computes watermarks/reserves.
- Deferred struct-page init: `CONFIG_DEFERRED_STRUCT_PAGE_INIT` (depends SPARSEMEM+64BIT, `mm/Kconfig:1131`) satisfied on x86-64; `defer_init()` marks `pgdat->first_deferred_pfn` `mm/mm_init.c:709`; `page_alloc_init_late()` spawns one `pgdatinit%d` kthread per `N_MEMORY` node running `deferred_init_memmap()` via `padata_do_multithreaded` `:2312`,`:2112`; completion tracked by `pgdat_init_n_undone`/`pgdat_init_all_done_comp` `:2019-2031`; `deferred_grow_zone()` lazily grows a zone under `pgdat_resize_lock` when an allocation stalls `:2183`.
- Locks: `zone->lock` (spinlock) guards `free_area` `include/linux/mmzone.h:1013`; `zone->span_seqlock` guards `zone_start_pfn`/`spanned_pages` `:990`; `pgdat->node_size_lock` via `pgdat_resize_lock/unlock/init()` guards node extents + `first_deferred_pfn`, nests above zone->lock/span_seqlock `include/linux/memory_hotplug.h:238-251`; `pgdat->kswapd_lock` (mutex) guards `pgdat->kswapd` `:164-177`; `zonelist_update_seq` (seqlock) guards zonelist rebuild during hot-remove `mm/page_alloc.c:4391`; `pcp->lock` guards pcp lists `include/linux/mmzone.h:745`; `pcp_batch_high_lock` (mutex) serializes batch/high recompute `mm/page_alloc.c:94`.
- State fields/transitions: `zone->initialized` boot→initialized, set once in `init_currently_empty_zone()` `include/linux/mmzone.h:993`/`mm/mm_init.c:1465`; `zone->contiguous` set by `set_zone_contiguous()` during `page_alloc_init_late()` `mm/mm_init.c:2264`; `node_states[]` transitions: `N_POSSIBLE` at `numa_register_meminfo` boot, `N_ONLINE` at `node_set_online()`, `N_MEMORY`/`N_NORMAL_MEMORY`/`N_HIGH_MEMORY` set in `check_for_memory()`+`free_area_init()` loop `mm/mm_init.c:1749,1917-1920`.
- Async/deferred behaviors: watermark boost set in `boost_watermark()`+`ZONE_BOOSTED_WATERMARK` bit `mm/page_alloc.c:2193-2228,2335-2336`; boost cleared and kswapd woken lazily on next `rmqueue()` `:3429-3432`; boost decayed only after a boosted reclaim pass completes in `balance_pgdat()` (record `:6977-6982`, decay `:7133-7145` — reclaim's turf, mention only) `mm/vmscan.c:6950`; `ZONE_RECLAIM_ACTIVE` brackets kswapd scanning and throttles pcp `nr_pcp_high()` `:2826`; `ZONE_BELOW_HIGH` adaptively shrinks/grows the pcp high mark `:2836,2941,3902` (part of PCP auto-tuning, async per allocation/free); `pgdat->kswapd_failures` "hopeless" state machine — `kswapd_clear_hopeless`/`kswapd_try_clear_hopeless`/`kswapd_test_hopeless` `mm/vmscan.c:7406,7419,7427` (mention only, reclaim turf).

#### 4. Hard-coded limits

- `MAX_PAGE_ORDER`=10, `NR_PAGE_ORDERS`=11, `PAGE_ALLOC_COSTLY_ORDER`=3 — `include/linux/mmzone.h:30,38,62`.
- `NR_LOWORDER_PCP_LISTS`=16, `NR_PCP_THP`=2, `NR_PCP_LISTS`=18(THP)/16 — `include/linux/mmzone.h:722-727`. [NOTE, orchestrator: agent D computed NR_LOWORDER_PCP_LISTS=12/NR_PCP_LISTS=14 from the same macros — re-derive on disk at write time; conflicting hint.]
- `MAX_ZONES_PER_ZONELIST` = MAX_NUMNODES×MAX_NR_ZONES; `MAX_ZONELISTS`=2 (`BUILD_BUG_ON` enforced `mm/mm_init.c:2699`) — `include/linux/mmzone.h:1292,1295-1304`.
- x86-64 `NODES_SHIFT` default 6 → `MAX_NUMNODES`=64 — `arch/x86/Kconfig:1559-1568`, `include/linux/nodemask_types.h:13`.
- `NR_NODE_MEMBLKS` = MAX_NUMNODES×2 (=128 default) — `include/linux/numa_memblks.h:8`.
- x86-64 zone extents: `MAX_DMA_PFN`=16MiB>>PAGE_SHIFT `arch/x86/include/asm/dma.h:74`; `MAX_DMA32_PFN`=4GiB>>PAGE_SHIFT `:77`; wired in `arch_zone_limits_init()` `arch/x86/mm/init.c:999`.
- `min_free_kbytes` default 1024, clamped [128,262144] — `mm/page_alloc.c:302,6554`.
- `watermark_boost_factor` default 15000/10000 (150%) — `:304`; `watermark_scale_factor` default 10, sysctl range [1,3000] — `:305,6766-6767`.
- `sysctl_lowmem_reserve_ratio[]` defaults {DMA:256, DMA32:256, NORMAL:32, MOVABLE:0} — `:258-270`.
- `MIN_PERCPU_PAGELIST_HIGH_FRACTION`=8 — `:95`; `CONFIG_PCP_BATCH_SCALE_MAX` default 5, range 0-6 — `mm/Kconfig:670-673`.
- `zone_batchsize()` cap = min(managed_pages>>12, 256KiB/PAGE_SIZE); pageset high floor = batch×4 — `mm/page_alloc.c:5933,6011`.
- `DEF_PRIORITY`=12 — `include/linux/mmzone.h:1289`.
- `LOCAL_DISTANCE`=10, `REMOTE_DISTANCE`=20, `RECLAIM_DISTANCE`=30 — `include/linux/topology.h:46-59`.
- `MAX_RECLAIM_RETRIES`=16 bounds `kswapd_failures` hopeless state — `mm/internal.h:610`.
- `sysctl_min_unmapped_ratio` default 1%, `sysctl_min_slab_ratio` default 5% — `mm/vmscan.c:7567,7573`.
- `SWAP_CLUSTER_MAX`=32, used as watermark floor for highmem/movable — `include/linux/swap.h:222`, `mm/page_alloc.c:6465`.

#### 5. Version-specific facts (v7.0 vs. older widely-documented kernels)

- Generic NUMA memblk infra is new: `mm/numa.c`+`mm/numa_memblks.c` didn't exist before ~Aug 2024 ("mm: introduce numa_memblks", commits `0e8b67982b48`/`87482708210f`/`46bcce503197`); `node_data[]`, `NODE_DATA()`, `alloc_node_data()`, `numa_add_memblk()`, `numa_set_distance()` used to be x86-only (`arch/x86/mm/numa.c`) — now shared with arm64/riscv. x86-64 no longer defines its own `NODE_DATA`/`asm/mmzone.h` override.
- `mm_core_init()`/`mm_core_init_early()` (`mm/mm_init.c:2694,2683`) are the renamed/relocated boot entry points; older kernels called `mm_init()` from `init/main.c` (renamed by commit `b7ec1bf3e7b9`, ~v6.4).
- `WMARK_PROMO` (memory tiering) exists since ~v6.0, but its `promo_wmark_pages()` accessor (`include/linux/mmzone.h:1098`) is newer (commit `03790c51a475`, 2024) — many watermark write-ups only show MIN/LOW/HIGH.
- `ZONE_BELOW_HIGH` flag and the whole adaptive `per_cpu_pages` machinery (`high_min`/`high_max`/`free_count`/`alloc_factor`, `include/linux/mmzone.h:748-756`) postdate the "PCP high auto-tuning" framework (commit `90b41691b988`, ~v6.7-6.8); classic docs describing a single static `pcp->high`/`pcp->batch` are stale.
- `zone->trylock_free_pages` (`include/linux/mmzone.h:1016`) is new (~2025, commit `8c57b687e833`, `free_pages_nolock()` for BPF/NMI-safe freeing).
- `page_zonenum()` now routes through `memdesc_zonenum()`/`memdesc_flags_t` (`include/linux/mmzone.h:1183`) — part of the very recent (Aug 2025) memdesc refactor decoupling flag accessors from `struct page`.
- `pgdat->kswapd_failures` gained a formal wrapper — `kswapd_clear_hopeless()`/`kswapd_try_clear_hopeless()`/`kswapd_test_hopeless()` + `enum kswapd_clear_hopeless_reason` (`include/linux/mmzone.h:1544-1556`, `mm/vmscan.c:7406-7430`) — landed Jan 2026 (commit `a45088376d8a`), just before v7.0, replacing scattered `atomic_set(&pgdat->kswapd_failures,0)` call sites.
- `node_stat_item` gained `NR_BALLOON_PAGES`, `NR_KERNEL_FILE_PAGES`, `PGDEMOTE_PROACTIVE`, `PGPROMOTE_CANDIDATE_NRL` (`include/linux/mmzone.h:242-263`) — absent from older `/proc/vmstat` documentation.

#### 6. Suggested page topics (agent B)

- Per-CPU page allocator internals — `struct per_cpu_pages`, `zone_batchsize/zone_highsize`, `nr_pcp_high/nr_pcp_free`, `PCPF_*` flags (`include/linux/mmzone.h:744`, `mm/page_alloc.c:5922-6017,2804,2779`): large enough sub-mechanism (autotuning, drain, cacheinfo scaling) to deserve its own page.
- Zonelist fallback ordering & node distance — `build_zonelists`, `find_next_best_node`, `node_distance` (`mm/page_alloc.c:5616,5704`, `include/linux/topology.h:50`): the NUMA fallback-order algorithm is dense enough to merit standalone treatment.
- NUMA memblks & distance table — `mm/numa_memblks.c` (`numa_meminfo`, `numa_set_distance`, `numa_emulation`, `numa_fill_memblks`): recently genericized subsystem worth documenting as the canonical boot-time NUMA description layer.
- Deferred struct-page initialization — `deferred_init_memmap`, `padata_do_multithreaded`, `deferred_grow_zone`, `first_deferred_pfn` (`mm/mm_init.c:2112,2183`): boot-scaling mechanism with its own locking/threading model.
- Watermark boosting & reclaim urgency flags — `boost_watermark`, `ZONE_BOOSTED_WATERMARK`/`ZONE_RECLAIM_ACTIVE`/`ZONE_BELOW_HIGH`, decay in `balance_pgdat` (`mm/page_alloc.c:2193`, `mm/vmscan.c:6950`): bridges alloc/reclaim; boost decay is under-documented.
- kswapd "hopeless node" state machine — `kswapd_failures`, `MAX_RECLAIM_RETRIES`, `kswapd_clear_hopeless` family (`mm/vmscan.c:7406-7430`, `mm/internal.h:610`): brand-new in the v7.0 cycle.
- Memory tiering & node-distance-based promotion — `WMARK_PROMO`, `pglist_data->nbp_rl_*`/`nbp_th_*`, `memtier` (`include/linux/mmzone.h:1477-1491,1516`): ties node/zone structures to NUMA-balancing tier promotion, orthogonal to classic reclaim docs.

### Area C: allocation-context flags — GFP, memalloc scopes, ALLOC_* (agent C, complete)

All anchors read directly off the checkout per the agent; lines remain hints at write time.

#### 1. Core structs/flag sets

| Group | Symbol(s) | Role | Anchor |
|---|---|---|---|
| Raw bit enum | `enum {___GFP_DMA_BIT...___GFP_LAST_BIT}` | positional bit indices backing every `___GFP_*` mask | include/linux/gfp_types.h:26-60 |
| Raw bit masks | `___GFP_DMA` … `___GFP_NO_OBJ_EXT` (`BIT(n)`, do-not-use-directly) | plain-int values before the `__force gfp_t` cast | include/linux/gfp_types.h:63-99 |
| Zone modifiers | `__GFP_DMA/HIGHMEM/DMA32/MOVABLE`, `GFP_ZONEMASK` | low 4 bits select zone | include/linux/gfp_types.h:108-112 |
| Mobility/placement | `__GFP_RECLAIMABLE,__GFP_WRITE,__GFP_HARDWALL,__GFP_THISNODE,__GFP_ACCOUNT,__GFP_NO_OBJ_EXT` | pageblock grouping / cpuset wall / no-fallback node / kmemcg / slab-obj-ext skip | include/linux/gfp_types.h:114-150 |
| Watermark modifiers | `__GFP_HIGH,__GFP_MEMALLOC,__GFP_NOMEMALLOC` | reserve-forgiveness triad | include/linux/gfp_types.h:152-178 |
| Reclaim control | `__GFP_IO,__GFP_FS,__GFP_DIRECT_RECLAIM,__GFP_KSWAPD_RECLAIM,__GFP_RECLAIM,__GFP_RETRY_MAYFAIL,__GFP_NOFAIL,__GFP_NORETRY` | how hard/whether to reclaim | include/linux/gfp_types.h:180-262 |
| Action modifiers | `__GFP_NOWARN,__GFP_COMP,__GFP_ZERO,__GFP_ZEROTAGS,__GFP_SKIP_ZERO,__GFP_SKIP_KASAN,__GFP_NOLOCKDEP` | post-alloc behavior | include/linux/gfp_types.h:264-296 |
| Bit-count consts | `__GFP_BITS_SHIFT=___GFP_LAST_BIT`, `__GFP_BITS_MASK` | width of the public GFP bitspace | include/linux/gfp_types.h:299-300 |
| Composite recipes | `GFP_ATOMIC…GFP_TRANSHUGE` | see recipes below | include/linux/gfp_types.h:376-389 |
| Derived masks | `GFP_RECLAIM_MASK,GFP_BOOT_MASK,GFP_CONSTRAINT_MASK,GFP_SLAB_BUG_MASK` | mm-internal filters | mm/internal.h:74-86 |
| `struct alloc_context` | `zonelist,nodemask,preferred_zoneref,migratetype,highest_zoneidx,spread_dirty_pages` | per-call allocation params threaded through the allocator | mm/internal.h:657-675 |
| `ALLOC_*` (internal, non-gfp) | full census below | mm/internal.h:1346-1385 |
| `PF_MEMALLOC*` task flags | census below | include/linux/sched.h:1752-1785 |

___GFP_* bit census (x86-64: `CONFIG_KASAN_HW_TAGS` is unreachable — arm64/MTE-only — so `SKIP_ZERO`/`SKIP_KASAN` always compile to `0`; `NOLOCKDEP`/`NO_OBJ_EXT` shift down 2 bits when `CONFIG_KASAN_HW_TAGS` is off, and `NOLOCKDEP` itself is `0` unless `CONFIG_LOCKDEP=y`):

| bit | flag | hex (x86-64, `CONFIG_LOCKDEP=y`) | meaning | line |
|---|---|---|---|---|
|0|`__GFP_DMA`|0x01|use `ZONE_DMA` (≤16M on x86-64)|108|
|1|`__GFP_HIGHMEM`|0x02|use highmem (no-op zone on x86-64, no `ZONE_HIGHMEM`)|109|
|2|`__GFP_DMA32`|0x04|use `ZONE_DMA32`|110|
|3|`__GFP_MOVABLE`|0x08|zone-selector + mobility hint (`ZONE_MOVABLE` allowed)|111|
|4|`__GFP_RECLAIMABLE`|0x10|slab pages reclaimable via shrinkers|145|
|5|`__GFP_HIGH`|0x20|high priority, dip into reserves (→`ALLOC_MIN_RESERVE`)|176|
|6|`__GFP_IO`|0x40|may start physical IO|255|
|7|`__GFP_FS`|0x80|may recurse into filesystem|256|
|8|`__GFP_ZERO`|0x100|return zeroed page|290|
|9|(unused)|0x200|explicitly reserved, unused|gfp_types.h:36,72|
|10|`__GFP_DIRECT_RECLAIM`|0x400|caller may enter direct reclaim|257|
|11|`__GFP_KSWAPD_RECLAIM`|0x800|kswapd may be woken|258|
|12|`__GFP_WRITE`|0x1000|caller will dirty page → dirty-spreading|146|
|13|`__GFP_NOWARN`|0x2000|suppress alloc-failure splat|288|
|14|`__GFP_RETRY_MAYFAIL`|0x4000|try hard, still may fail, no OOM kill|260|
|15|`__GFP_NOFAIL`|0x8000|must not fail, retry forever|261|
|16|`__GFP_NORETRY`|0x10000|fail fast, no OOM kill|262|
|17|`__GFP_MEMALLOC`|0x20000|access to all memory reserves|177|
|18|`__GFP_COMP`|0x40000|compound-page metadata|289|
|19|`__GFP_NOMEMALLOC`|0x80000|explicitly forbid reserves (wins over MEMALLOC)|178|
|20|`__GFP_HARDWALL`|0x100000|enforce cpuset wall|147|
|21|`__GFP_THISNODE`|0x200000|only requested node, no fallback|148|
|22|`__GFP_ACCOUNT`|0x400000|charge to kmemcg|149|
|23|`__GFP_ZEROTAGS`|0x800000|zero MTE tags together with zeroing|291|
|24|`__GFP_NOLOCKDEP`|0x1000000 (0 if `!CONFIG_LOCKDEP`)|opt out of fs_reclaim lockdep tracking|296|
|25|`__GFP_NO_OBJ_EXT`|0x2000000|slab alloc has no object-extension / codetag|150|
|26|`___GFP_LAST_BIT`→`__GFP_BITS_SHIFT`|26 (25 w/o LOCKDEP)|width marker, not a flag|299|

`__GFP_ATOMIC` does not exist in this tree (see facts below).

Composite `GFP_*` recipes (all gfp_types.h:376-389):
- `GFP_ATOMIC = __GFP_HIGH|__GFP_KSWAPD_RECLAIM` (376) — non-sleeping, atomic/IRQ/BH context, no NMI/raw-spinlock/PREEMPT_RT-preempt-disabled context (doc at gfp_types.h:312-317).
- `GFP_KERNEL = __GFP_RECLAIM|__GFP_IO|__GFP_FS` (377) — default, sleepable, process context.
- `GFP_KERNEL_ACCOUNT = GFP_KERNEL|__GFP_ACCOUNT` (378) — untrusted/userspace-triggered kernel allocs.
- `GFP_NOWAIT = __GFP_KSWAPD_RECLAIM|__GFP_NOWARN` (379) — atomic context, no reserve access (no `__GFP_HIGH`).
- `GFP_NOIO = __GFP_RECLAIM` (380) — reclaim ok, no IO; prefer `memalloc_noio_save` scope instead.
- `GFP_NOFS = __GFP_RECLAIM|__GFP_IO` (381) — reclaim+IO ok, no FS recursion; prefer `memalloc_nofs_save`.
- `GFP_USER = __GFP_RECLAIM|__GFP_IO|__GFP_FS|__GFP_HARDWALL` (382) — userspace, kernel-accessible, cpuset-enforced.
- `GFP_DMA/GFP_DMA32` (383-384) — legacy hardware-addressing-limited allocs.
- `GFP_HIGHUSER = GFP_USER|__GFP_HIGHMEM` (385) — userspace, not kernel-mapped, not movable.
- `GFP_HIGHUSER_MOVABLE = GFP_HIGHUSER|__GFP_MOVABLE|__GFP_SKIP_KASAN` (386) — userspace, movable/reclaimable.
- `GFP_TRANSHUGE_LIGHT = (GFP_HIGHUSER_MOVABLE|__GFP_COMP|__GFP_NOMEMALLOC|__GFP_NOWARN) & ~__GFP_RECLAIM` (387-388) — THP page-fault path, fails fast, no kswapd wake.
- `GFP_TRANSHUGE = GFP_TRANSHUGE_LIGHT|__GFP_DIRECT_RECLAIM` (389) — khugepaged path, will reclaim/compact. Selection logic: mm/huge_memory.c:1422-1446 (`vma_thp_gfp_mask`), mm/khugepaged.c:856.

ALLOC_* census (mm/internal.h, non-GFP, page-allocator-internal alloc_flags bitmap):
| flag | value | meaning | line |
|---|---|---|---|
|`ALLOC_WMARK_MIN/LOW/HIGH`|0/1/2 (=`WMARK_*`, mmzone.h:709-712)|index into `zone->_watermark[]`|1347-1349|
|`ALLOC_NO_WATERMARKS`|0x04|skip watermark check entirely|1350|
|`ALLOC_WMARK_MASK`|`ALLOC_NO_WATERMARKS-1`=0x03|extract the watermark index|1353|
|`ALLOC_OOM`|0x08 (=`ALLOC_NO_WATERMARKS` if `!CONFIG_MMU`)|OOM-victim reserve access|1355-1364|
|`ALLOC_NON_BLOCK`|0x10|non-blocking caller: 25% of min wmark, or 62.5% if combined w/ `__GFP_HIGH`|1366-1369|
|`ALLOC_MIN_RESERVE`|0x20|`__GFP_HIGH` set: 50% of min wmark|1370-1372|
|`ALLOC_CPUSET`|0x40|enforce cpuset check|1373|
|`ALLOC_CMA`|0x80|allow `MIGRATE_CMA` pages|1374|
|`ALLOC_NOFRAGMENT`|0x100 (0 if `!CONFIG_ZONE_DMA32`)|avoid mixing pageblock types|1375-1379|
|`ALLOC_HIGHATOMIC`|0x200|allow `MIGRATE_HIGHATOMIC` pageblocks|1380|
|`ALLOC_TRYLOCK`|0x400|only `spin_trylock` — NMI/any-context path|1381|
|`ALLOC_KSWAPD`|0x800|wake kswapd (`==__GFP_KSWAPD_RECLAIM`)|1382|
|`ALLOC_RESERVES`|`NON_BLOCK|MIN_RESERVE|HIGHATOMIC|OOM`|"below min watermark" flag group|1385|

PF_MEMALLOC* task-flag census (include/linux/sched.h):
- `PF_MEMALLOC` 0x00000800 — "allocating memory to free memory", see `memalloc_noreclaim_save()` (1763).
- `PF_KSWAPD` 0x00020000 — this task is kswapd (1769).
- `PF_MEMALLOC_NOFS` 0x00040000 — all allocs inherit `GFP_NOFS` (1770).
- `PF_MEMALLOC_NOIO` 0x00080000 — all allocs inherit `GFP_NOIO` (1771).
- `PF_MEMALLOC_PIN` 0x10000000 — allocs constrained off `ZONE_MOVABLE` (1781-1782).

#### 2. API families

Zone/migratetype resolution:
- `gfp_zone(gfp_t)` — bit-table zone lookup — include/linux/gfp.h:156-165; driven by `GFP_ZONE_TABLE`/`GFP_ZONE_BAD` (128-154), `OPT_ZONE_{HIGHMEM,DMA,DMA32}` (66-82), `GFP_ZONES_SHIFT` (117-122; x86-64 selects `ZONE_DMA` default-y + `select ZONE_DMA32` in arch/x86/Kconfig:37, no `ZONE_HIGHMEM`).
- `gfp_migratetype(gfp_t)` — `GFP_MOVABLE_MASK=(__GFP_RECLAIMABLE|__GFP_MOVABLE)`, `GFP_MOVABLE_SHIFT=3` — gfp.h:21-38.
- `gfp_zonelist()`, `node_zonelist()` — NUMA zonelist selection (`__GFP_THISNODE`→`ZONELIST_NOFALLBACK`) — gfp.h:174-181, 217-220.

Reclaim-permission accessors:
- `gfpflags_allow_blocking()` = `gfp & __GFP_DIRECT_RECLAIM` — gfp.h:42-45.
- `gfpflags_allow_spinning()` = `gfp & __GFP_RECLAIM` — stricter than NOWAIT/ATOMIC, used to gate `alloc_pages_nolock()` — gfp.h:47-64.
- `gfp_has_flags/gfp_has_io_fs/gfp_compaction_allowed()` — gfp.h:418-435.

alloc_flags derivation (mm/page_alloc.c):
- `gfp_to_alloc_flags(gfp_mask, order)` — fast-path base flags (`ALLOC_WMARK_MIN|ALLOC_CPUSET` + HIGH/KSWAPD/NON_BLOCK/HIGHATOMIC/MIN_RESERVE via `BUILD_BUG_ON` bit-identity tricks; RT/DL tasks get `ALLOC_MIN_RESERVE`) — 4495-4545.
- `gfp_to_alloc_flags_cma(gfp_mask, alloc_flags)` — adds `ALLOC_CMA` iff `gfp_migratetype()==MIGRATE_MOVABLE`; comment: "must be called after `current_gfp_context()`" — 3792-3801.
- `alloc_flags_nofragment(zone, gfp_mask)` — adds `ALLOC_NOFRAGMENT` when preferred zone is `ZONE_NORMAL` and `ZONE_DMA32` is populated (or unconditionally under `defrag_mode`) — 3755-3790.
- `__gfp_pfmemalloc_flags(gfp_mask)` / `gfp_pfmemalloc_allowed()` — decides `ALLOC_NO_WATERMARKS` vs `ALLOC_OOM` vs 0 from `__GFP_MEMALLOC`/`PF_MEMALLOC`/`oom_reserves_allowed()` — 4562-4587.
- `oom_reserves_allowed(tsk)` = `tsk_is_oom_victim(tsk)` (+ `TIF_MEMDIE` gate if `!CONFIG_MMU`) — 4547-4560; `tsk_is_oom_victim()` = `tsk->signal->oom_mm` — include/linux/oom.h:74-77.
- `__zone_watermark_ok()`/`zone_watermark_ok()`/`zone_watermark_fast()` — the actual carve-out math — 3602-3726.
- `reserve_highatomic_pageblock()`/`unreserve_highatomic_pageblock()` — 1%-of-zone `MIGRATE_HIGHATOMIC` reservation for `ALLOC_HIGHATOMIC` — 3444-3536.

Allocation entry points:
- `__alloc_pages_noprof()`→`__alloc_frozen_pages_noprof()` — masks `gfp_allowed_mask`, applies `current_gfp_context()`, calls `prepare_alloc_pages()`, fast path via `get_page_from_freelist()`, else `__alloc_pages_slowpath()` — 5214-5289.
- `prepare_alloc_pages()` — sets `ac->migratetype/highest_zoneidx/zonelist`, adds `__GFP_HARDWALL`/`ALLOC_CPUSET` for cpusets, `ac->spread_dirty_pages=(gfp&__GFP_WRITE)`, calls `gfp_to_alloc_flags_cma()` — 4996-5042.
- `__alloc_pages_slowpath()` — full retry state machine: `nofail`, `costly_order`, compaction-first, `should_reclaim_retry()`, `should_compact_retry()`, `__alloc_pages_may_oom()` — 4709-4994.
- `alloc_pages_nolock_noprof()`/`alloc_frozen_pages_nolock_noprof()` — any-context (incl. NMI) opportunistic alloc using `ALLOC_TRYLOCK`, forces `__GFP_NOWARN|__GFP_ZERO|__GFP_NOMEMALLOC|__GFP_COMP`, rejects everything but `__GFP_ACCOUNT` — 7759-7856.
- `free_pages_nolock()`/`free_frozen_pages_nolock()` — `FPI_TRYLOCK`-based free usable from NMI/hardirq/raw-spinlock context, deferred to per-zone llist under `PREEMPT_RT`+NMI/hardirq — 5377-5380, 2998-3021.
- `cond_accept_memory()` — bails out under `ALLOC_TRYLOCK` since accepting unaccepted memory needs a real lock — 7681-7718.

Scope-tracking / lockdep:
- `fs_reclaim_acquire()/fs_reclaim_release()` + `__fs_reclaim_map` (`STATIC_LOCKDEP_MAP_INIT`) + `__need_reclaim()` (skips if `PF_MEMALLOC` or `__GFP_NOLOCKDEP`) — 4326-4383.
- `warn_alloc()`/`warn_alloc_show_mem()` — OOM-victim/`PF_MEMALLOC`/`PF_EXITING` filter node-dump noise — 4005-4023.

#### 3. Lifecycle and locking

Boot transitions of `gfp_allowed_mask`:
- Static init: `gfp_t gfp_allowed_mask __read_mostly = GFP_BOOT_MASK` — mm/page_alloc.c:238; `GFP_BOOT_MASK = __GFP_BITS_MASK & ~(__GFP_RECLAIM|__GFP_IO|__GFP_FS)` — mm/internal.h:80.
- Unlock at scheduler-ready boot stage: `gfp_allowed_mask = __GFP_BITS_MASK` in `kernel_init_freeable()` — init/main.c:1663-1666.
- Applied at every allocation: `gfp &= gfp_allowed_mask` — page_alloc.c:5116 (bulk), 5229 (`__alloc_frozen_pages_noprof`); also slab: mm/slub.c:3465,4487,4505; memcg: mm/memcontrol.c:3213.
- Hibernation temporary restriction: `pm_restrict_gfp_mask()`/`pm_restore_gfp_mask()` — save/mask off `__GFP_IO|__GFP_FS`, refcounted via `saved_gfp_count`, must hold `system_transition_mutex` — kernel/power/main.c:36-65; called from kernel/power/hibernate.c:463,486,876 and kernel/power/user.c:119,300,312. `pm_suspended_storage()` gate checked in OOM path (page_alloc.c:4126).

`current_gfp_context()` — applies `PF_MEMALLOC_NOIO`→strip `__GFP_IO|__GFP_FS`, else `PF_MEMALLOC_NOFS`→strip `__GFP_FS`; `PF_MEMALLOC_PIN`→strip `__GFP_MOVABLE` — include/linux/sched/mm.h:249-267. Confirmed call sites (13 total): `__alloc_frozen_pages_noprof` (page_alloc.c:5237), `alloc_contig_frozen_range_noprof` (page_alloc.c:7020), `fs_reclaim_acquire/release` (page_alloc.c:4358,4375), `pcpu_alloc_noprof` (mm/percpu.c:1751), `try_to_free_pages`/`try_to_free_mem_cgroup_pages`/`node_reclaim`/`user_proactive_reclaim` (mm/vmscan.c:6572,6662,7665,7747≈), `__folio_split` (mm/huge_memory.c:4006), `memalloc_retry_wait` (sched/mm.h:295), `nfs_io_gfp_mask`/`nfs_release_folio` (fs/nfs/internal.h:690, fs/nfs/file.c:511).

Scope save/restore APIs (all include/linux/sched/mm.h), all built on the generic primitive:
- Generic: `memalloc_flags_save(flags)`/`memalloc_flags_restore(flags)` — adds/removes arbitrary `PF_*` bits, returns only the bits that changed (so restore is a no-op if the flag was already set — nesting-safe) — 333-343.
- `memalloc_noio_save/restore` → `PF_MEMALLOC_NOIO` — 357-373.
- `memalloc_nofs_save/restore` → `PF_MEMALLOC_NOFS` — 387-403.
- `memalloc_noreclaim_save/restore` → `PF_MEMALLOC` (implicit `__GFP_MEMALLOC`); doc explicitly says not safe from interrupt context — 405-444.
- `memalloc_pin_save/restore` → `PF_MEMALLOC_PIN` (implicit `~__GFP_MOVABLE`) — 446-472.
- Nesting rule (Documentation/core-api/gfp_mask-from-fs-io.rst:50-53): save/restore pairs nest safely; NOIO treated as strictly stronger than NOFS by `current_gfp_context()`.
- Newest/generic variant: `memalloc_apply_gfp_scope(gfp_mask)`/`memalloc_restore_scope(flags)` in include/linux/vmalloc.h:335-336, defined mm/vmalloc.c:3804-3825 — auto-picks noreclaim (if `!gfpflags_allow_blocking`), else nofs (if IO-only), else noio, for page-table allocs inside `__vmalloc_area_node()` (used at mm/vmalloc.c:3912/3919). New in v7.0.
- `set_active_memcg()` — analogous scope for `__GFP_ACCOUNT` charge target — sched/mm.h:474-512.

Who sets `PF_MEMALLOC` itself: kswapd — `tsk->flags |= PF_MEMALLOC|PF_KSWAPD` on entry, cleared on exit — mm/vmscan.c:7299,7349. Softirq handling masks it out for the duration of `handle_softirqs()` and restores via `current_restore_flags(old_flags, PF_MEMALLOC)` — kernel/softirq.c:590-594,651; `current_restore_flags()` sched.h:1877-1882. Also set directly by swap-over-network I/O consumers: net/sunrpc/{sched,xprt,xprtsock}.c, net/sunrpc/xprtrdma/transport.c, fs/xfs/libxfs/xfs_btree.c:3021.

Async/atomic/NMI/IRQ-context rules:
- `GFP_ATOMIC`/`GFP_NOWAIT` doc: no NMI support, no `raw_spin_lock()`/plain `preempt_disable()` context under `PREEMPT_RT` — gfp_types.h:312-317.
- `gfpflags_allow_spinning()` is the real "safe from any context" test — gfp.h:47-64; only `alloc_pages_nolock()`/`ALLOC_TRYLOCK` path satisfies it.
- `alloc_pages_nolock()` — "safe to call from any context (atomic, NMI, reentrant)" but on `PREEMPT_RT` explicitly bails if `in_nmi()||in_hardirq()` (rt_spin_trylock/PI) — page_alloc.c:7789-7830.
- `free_pages_nolock()` — "can be called while holding raw_spin_lock or from IRQ and NMI"; defers to per-zone lockless list when `PREEMPT_RT && (in_nmi()||in_hardirq())` — page_alloc.c:5373-5380, 2998-3002.
- `might_alloc()` skips `might_sleep_if()` entirely when `current->flags & PF_MEMALLOC` — sched/mm.h:315-324.

#### 4. Hard-coded limits

- `PAGE_ALLOC_COSTLY_ORDER = 3` — include/linux/mmzone.h:62 (order>3 is "costly": implicitly failable, no OOM kill unless `__GFP_RETRY_MAYFAIL`+compaction).
- `MAX_RECLAIM_RETRIES = 16` — mm/internal.h:610 (used by `should_reclaim_retry`, page_alloc.c:4618).
- `MAX_COMPACT_RETRIES = 16` — mm/page_alloc.c:4160.
- High-atomic reserve cap: min(1% of zone_managed_pages, ≥1 pageblock), else 0 — page_alloc.c:3450-3458.
- `ALLOC_MIN_RESERVE` carve-out: `min -= min/2` (50% access) — page_alloc.c:3617-3618.
- `ALLOC_NON_BLOCK` stacked with MIN_RESERVE (`GFP_ATOMIC`): further `min -= min/4` → net 62.5% access; alone (no `__GFP_HIGH`) → 25% access — page_alloc.c:3620-3628 + mm/internal.h:1366-1369 comment.
- `ALLOC_OOM` carve-out: additional `min -= min/2` — page_alloc.c:3637-3638.
- `sysctl_lowmem_reserve_ratio[]` defaults on x86-64: DMA=256, DMA32=256, NORMAL=32, MOVABLE=0 — page_alloc.c:258-270 (feeds `z->lowmem_reserve[highest_zoneidx]` term in `__zone_watermark_ok`, line 3646).
- `min_free_kbytes` default 1024, clamped [128, 262144], formula `sqrt(lowmem_kbytes*16)` — page_alloc.c:302,6545-6557.
- `watermark_scale_factor` default 10, `watermark_boost_factor` default 15000 — page_alloc.c:304-305.
- `ALLOC_WMARK_MASK = ALLOC_NO_WATERMARKS-1 = 0x03`, with `BUILD_BUG_ON(ALLOC_NO_WATERMARKS < NR_WMARK)` (`NR_WMARK=4`) — mm/internal.h:1350,1353; mmzone.h:709-713; page_alloc.c:3932.
- `GFP_ZONES_SHIFT` build check: `16*GFP_ZONES_SHIFT > BITS_PER_LONG` → compile error — include/linux/gfp.h:124-126.
- `__GFP_BITS_SHIFT` = 25 or 26 depending on `CONFIG_LOCKDEP` (x86-64 KASAN_HW_TAGS bits never counted) — gfp_types.h:26-60,299.

#### 5. Version-specific facts (vs. widely-documented older kernels)

- `__GFP_ATOMIC` is gone. Commit `2973d8229b78` "mm: discard `__GFP_ATOMIC`" (first in v6.3) removed the bit; `GFP_ATOMIC` is purely `(__GFP_HIGH|__GFP_KSWAPD_RECLAIM)`.
- `ALLOC_HARDER` is gone, split into `ALLOC_MIN_RESERVE`+`ALLOC_NON_BLOCK` (commits `ab3508854353`/`eb2e2b425c69`, first in v6.3).
- `try_alloc_pages()`/`free_pages_nolock()` are new (commits `97769a53f117`/`8c57b687e833`, first in v6.15) — BPF-motivated NMI-safe allocation; `ALLOC_TRYLOCK` new alongside.
- `try_alloc_pages()` renamed to `alloc_pages_nolock()` (commit `2aad4edf6e10`, first in v6.16) — grep for `try_alloc_pages` in v7.0 finds nothing.
- `memalloc_apply_gfp_scope()`/`memalloc_restore_scope()` are new (commit `8da89ba18ed4`, first in v6.19) — first generic auto-selecting memalloc-scope helper, currently vmalloc-internal.
- `__GFP_NO_OBJ_EXT` is a recent slab/codetag addition, used only in mm/slub.c.
- "Frozen pages" naming layer (`__alloc_frozen_pages_noprof`, `free_frozen_pages[_nolock]`) is a recent internal split (commits `49249a2a5eeb`, `d7242af86434`) underneath the stable `alloc_pages()`/`__free_pages()` API.
- v7.0 is the direct continuation of mainline numbering after v6.19; all "first release" tags above are v6.x.

#### 6. Suggested page topics (agent C)

- NMI/BPF-safe page allocation — `alloc_pages_nolock`/`free_pages_nolock`/`ALLOC_TRYLOCK`/`FPI_TRYLOCK`, PREEMPT_RT llist-deferred free (page_alloc.c:7759-7856, 2998-3021, 5377-5380) — big and novel enough (v6.15+) for its own page.
- Watermark/reserve sysctl tuning — `min_free_kbytes`, `watermark_scale_factor`, `watermark_boost_factor`, `sysctl_lowmem_reserve_ratio` (page_alloc.c:258-305,6545-6789).
- cpuset/GFP interaction — `__GFP_HARDWALL`, `ALLOC_CPUSET`, `cpuset_current_mems_allowed`, `cpusets_insane_config()` (page_alloc.c:3831-3834,4788-4794,5006-5016).
- kmemcg accounting — `__GFP_ACCOUNT`, `GFP_KERNEL_ACCOUNT`, `set_active_memcg()` (sched/mm.h:474-512), `__memcg_kmem_charge_page()` call sites (page_alloc.c:5266,7822).
- OOM-killer reserve interplay — `ALLOC_OOM`, `oom_reserves_allowed`, `tsk_is_oom_victim`, `__alloc_pages_may_oom` (page_alloc.c:4080-4154).
- THP allocation policy — `vma_thp_gfp_mask`, `GFP_TRANSHUGE` vs `_LIGHT`, defrag sysctl (huge_memory.c:1413-1446, khugepaged.c:856).
- CMA/ALLOC_CMA path — `gfp_to_alloc_flags_cma`, `MIGRATE_CMA`, `alloc_contig_range`/`ACR_FLAGS_CMA`, `__alloc_contig_verify_gfp_mask` (page_alloc.c:3792-3801,6927-6960).
- PM/hibernation GFP restriction — `pm_restrict_gfp_mask`/`pm_restore_gfp_mask`, `saved_gfp_count` refcounting (kernel/power/main.c:36-65).

### Area D: buddy allocator and allocation path (agent D, complete)

All anchors reported as confirmed on disk by the agent (line numbers remain hints at write time).

#### 1. Core structs

- `struct free_area` — `free_list[MIGRATE_TYPES]` (per-migratetype list_head) + `nr_free` (unsigned long). include/linux/mmzone.h:138-141.
- `struct zone` (relevant fields) — `_watermark[NR_WMARK]`, `watermark_boost`, `nr_reserved_highatomic`, `nr_free_highatomic`, `lowmem_reserve[MAX_NR_ZONES]`, `per_cpu_pageset` (percpu `per_cpu_pages`), `free_area[NR_PAGE_ORDERS]`, `flags` (ZONE_* bits), `lock` (spinlock_t, "Primarily protects free_area"), `trylock_free_pages` (llist for trylock-path deferred frees), `compact_cached_*` fields. include/linux/mmzone.h:879 (struct start); watermark/reserve fields ~882-895; `free_area[]` at 999; `lock` at ~1029; zone_flags enum at 1069-1075 (ZONE_BOOSTED_WATERMARK, ZONE_RECLAIM_ACTIVE, ZONE_BELOW_HIGH).
- `struct per_cpu_pages` — `lock` (spinlock_t, own PCP lock, distinct from zone->lock), `count`, `high`/`high_min`/`high_max`, `batch`, `flags` (PCPF_*), `alloc_factor`, `free_count`, `lists[NR_PCP_LISTS]`. include/linux/mmzone.h:744-758ish (struct body per find_type).
- `struct alloc_context` — `zonelist`, `nodemask`, `preferred_zoneref`, `migratetype`, `highest_zoneidx`, `spread_dirty_pages`; comment states nodemask/migratetype/highest_zoneidx set once in `__alloc_pages()` and immutable thereafter, zonelist/preferred_zone/highest_zoneidx set in fast path and only preferred_zoneref/nodemask mutate in slowpath. mm/internal.h:657-675.
- `struct capture_control` — `{ struct compact_control *cc; struct page *page; }`, used by direct-compaction "give me the freed page directly" hook. mm/internal.h:994-997.
- `enum migratetype` — UNMOVABLE, MOVABLE, RECLAIMABLE, `MIGRATE_PCPTYPES` (=3, sentinel), HIGHATOMIC=PCPTYPES, [CMA], [ISOLATE], MIGRATE_TYPES (total). include/linux/mmzone.h:64-90.
- `enum rmqueue_mode` — NORMAL/CMA/CLAIM/STEAL, threaded through `__rmqueue()` calls inside `rmqueue_bulk()`'s locked loop so repeated calls remember where fallback last succeeded. mm/page_alloc.c:2466-2471.
- Page fields backing the above (mm_types.h): anonymous union `lru`/`buddy_list`/`pcp_list` (include/linux/mm_types.h:96/99/100) — a free/buddy page's list node reuses the LRU slot; `page_type` (mm_types.h:169) backs `PageBuddy`; `private` (via `page_private`/`set_page_private`) backs `buddy_order`.

#### 2. API families

Free-list helpers (mm/page_alloc.c):
- `add_to_free_list` 7497-7503 / `__add_to_free_list` 832-851 — insert page into `free_area[order].free_list[mt]` (head or tail), bump `nr_free`, `NR_FREE_PAGES_BLOCKS` stat if order≥pageblock_order; outer wrapper also calls `account_freepages`.
- `move_to_free_list` 858-880 — move within-zone between migratetypes (always to tail), updates freepage accounting and `NR_FREE_PAGES_BLOCKS`.
- `del_page_from_free_list`/`__del_page_from_free_list` 904-909 / 882-902 — unlink, `__ClearPageBuddy`, `set_page_private(0)`, `nr_free--`.
- `get_page_from_free_area` 911-916 — `list_first_entry_or_null` on `area->free_list[mt]`.
- `account_freepages` 814-829 — `lockdep_assert_held(&zone->lock)`; updates `NR_FREE_PAGES`, `NR_FREE_CMA_PAGES`, or `zone->nr_free_highatomic`; no-op for MIGRATE_ISOLATE.
- `free_area_empty` mm/internal.h:1035-1038 — `list_empty` accessor used throughout fallback scanning.

Buddy encoding/math:
- `PageBuddy`/`__SetPageBuddy`/`__ClearPageBuddy` generated by `PAGE_TYPE_OPS(Buddy, buddy, buddy)` include/linux/page-flags.h:1003, atop `enum pagetype { PGTY_buddy = 0xf0, ... }` (page-flags.h:925-939) — encoded in top 8 bits of `page->page_type` (not a bitflag; `page_type` doubles as overflow-mapcount storage, see `page_type_has_type()` page-flags.h:941-944).
- `buddy_order` mm/internal.h:685-689 / `buddy_order_unsafe` (READ_ONCE macro) internal.h:702 / `set_buddy_order` mm/page_alloc.c:752-756 — order stored in `page_private(page)`, valid only under `zone->lock` (buddy_order) or via READ_ONCE+manual validation (buddy_order_unsafe).
- `__find_buddy_pfn` mm/internal.h:756-759 — `page_pfn ^ (1 << order)`.
- `find_buddy_page_pfn` mm/internal.h:775-788 — computes buddy pfn/page and calls `page_is_buddy` to validate.
- `page_is_buddy` mm/internal.h:717-736 — buddy valid iff (guard-or-PageBuddy) && same order && same `page_zone_id`; zone-hole check must be done by caller before invocation.

Allocation entry points (include/linux/gfp.h unless noted; "_noprof" is the real body, public name is an `alloc_hooks()`-wrapping macro for CONFIG_MEM_ALLOC_PROFILING, see include/linux/alloc_tag.h:262-266):
- `alloc_pages`/`alloc_pages_noprof` gfp.h:349 / 329-332 → `alloc_pages_node_noprof(numa_node_id(),...)`. `alloc_page(gfp)` = `alloc_pages(gfp,0)` (gfp.h:354).
- `alloc_pages_node`/`alloc_pages_node_noprof` gfp.h:319 / 310-317 → `__alloc_pages_node_noprof` → `__alloc_pages_noprof(...,nid,NULL)`.
- `folio_alloc`/`folio_alloc_noprof` gfp.h:350 / 333-336 → `__folio_alloc_node_noprof` → `__folio_alloc_noprof` (mm/page_alloc.c:5291-5297): calls `__alloc_pages_noprof(gfp|__GFP_COMP,...)` then `page_rmappable_folio(page)` — refcounted page in, refcounted folio out.
- `__get_free_pages`/`get_free_pages_noprof` gfp.h:369 / mm/page_alloc.c:5305-5313 → `alloc_pages_noprof()` then `page_address()`; forbids `__GFP_HIGHMEM`.
- `get_zeroed_page`/`get_zeroed_page_noprof` gfp.h:372 / mm/page_alloc.c:5316-5319 → `get_free_pages_noprof(gfp|__GFP_ZERO,0)`.
- Bulk family: `alloc_pages_bulk`/`alloc_pages_bulk_node`/`alloc_pages_bulk_mempolicy` macros gfp.h:249/262-263/245-246, all funnel to `alloc_pages_bulk_noprof` mm/page_alloc.c:5065-5208 — order-0 only; locates one zone via watermark scan, then loops `__rmqueue_pcplist()` under one `pcp_spin_trylock`; on empty array or n=1 or memcg-accounted or `page_owner`-instrumented, falls back to single-page `__alloc_pages_noprof`.
- `alloc_pages_exact`/`alloc_pages_exact_noprof` gfp.h:375 / mm/page_alloc.c:5435-5445 — `get_order(size)` → `get_free_pages_noprof` → `make_alloc_exact` trims to exact byte size (frees the excess tail pages).
- Frozen variants: `__alloc_frozen_pages_noprof` mm/page_alloc.c:5214-5276 is "the heart of the zoned buddy allocator" — does the real fast-path+prepare work and returns a page with `_refcount==0` ("frozen"); `__alloc_pages_noprof` mm/page_alloc.c:5279-5288 is a thin wrapper that calls it then `set_page_refcounted(page)` (mm/internal.h:578-583, sets `_refcount=1`). `alloc_frozen_pages`/`alloc_frozen_pages_noprof` mm/internal.h:911-912/905-908 (single-node convenience, no refcount set). `alloc_pages_bulk_noprof` sets refcount itself inline after `prep_new_page()` in its loop (mm/page_alloc.c ~5185). Non-blocking/NMI-safe sibling: `alloc_pages_nolock`/`alloc_pages_nolock_noprof` mm/page_alloc.c:7847-7855 wraps `alloc_frozen_pages_nolock_noprof` (7759-7830, forces `ALLOC_TRYLOCK`, `__GFP_ZERO|__GFP_COMP|__GFP_NOWARN|__GFP_NOMEMALLOC`, no slowpath at all) + `set_page_refcounted`.
- `alloc_contig_frozen_pages`/`alloc_contig_pages` (CONFIG_CONTIG_ALLOC) gfp.h:456-464 — adjacent family, out of core scope but same frozen convention.

Context construction:
- `prepare_alloc_pages` mm/page_alloc.c:4996-5042 — sets `ac->highest_zoneidx=gfp_zone(gfp)`, `ac->zonelist=node_zonelist(nid,gfp)`, `ac->nodemask`, `ac->migratetype=gfp_migratetype(gfp)`; if `cpusets_enabled()`, sets `__GFP_HARDWALL`, and either substitutes `&cpuset_current_mems_allowed` (task context, no explicit nodemask) or sets `ALLOC_CPUSET` (non-task/irq context); calls `might_alloc()`; calls `should_fail_alloc_page(gfp,order)` fault injection unless `ALLOC_TRYLOCK` (avoids `get_random_u32()`/printk under trylock-only contexts) — mm/fail_page_alloc.c:26-45 real body, include/linux/fault-inject.h:119-122 no-op stub; sets `ALLOC_CMA` via `gfp_to_alloc_flags_cma`; sets `spread_dirty_pages = gfp & __GFP_WRITE`; computes initial `preferred_zoneref` via `first_zones_zonelist`.

#### 3. Lifecycle, locking, async behavior

- Fast path (`__alloc_frozen_pages_noprof`, mm/page_alloc.c:5214-5276): order sanity check (`order > MAX_PAGE_ORDER` → WARN+NULL) → `current_gfp_context()` scoping → `prepare_alloc_pages()` → OR-in `alloc_flags_nofragment()` → one `get_page_from_freelist()` attempt at `ALLOC_WMARK_LOW`. On success, `goto out` (memcg charge, tracepoints). On failure, reset `spread_dirty_pages=false` and restore original `nodemask`, then call `__alloc_pages_slowpath()` — this call (mm/page_alloc.c:5262) is the fast/slow boundary.
- Slowpath entry `__alloc_pages_slowpath` mm/page_alloc.c:4710-4994: computes `gfp_to_alloc_flags()`, re-derives `preferred_zoneref`; loop phases in order: `retry:` wake kswapd if `ALLOC_KSWAPD` → `get_page_from_freelist` retry → relax reserves/cpuset once → direct reclaim (`__alloc_pages_direct_reclaim`) and/or direct compaction (`__alloc_pages_direct_compact`, costly/non-movable orders try compaction first) → `should_reclaim_retry`/`should_compact_retry` gating further `retry` → drop `ALLOC_NOFRAGMENT` if `defrag_mode` set → OOM kill (`__alloc_pages_may_oom`) → `nopage:`/`fail:` (warn_alloc) or nofail-loop.
- kswapd wakeup: `wake_all_kswapds()` mm/page_alloc.c:4470-4493, called at top of every slowpath `retry:` iteration while `ALLOC_KSWAPD` is set; reclaim order is `max(order, pageblock_order)` when `defrag_mode` (asks kswapd to defragment, not just free order-0 pages). Also fired from `rmqueue()` mm/page_alloc.c:3427-3432 (`wakeup_kswapd(zone,0,0,...)`) when a `ZONE_BOOSTED_WATERMARK` bit is observed and `ALLOC_KSWAPD` set, clearing the boost bit — this is the "boost → kswapd" async close-the-loop.
- kswapd/kcompactd from compaction stay a seam here: `__alloc_pages_direct_compact` mm/page_alloc.c:4165-4221 calls `try_to_compact_pages()` (mm/compaction.c, out of scope) which may populate `*capture` directly (`current->capture_control`/`task_capc()`/`compaction_capture()` mm/page_alloc.c:759-798, consumed inside `__free_one_page` 978-1064) — the "page capture hook" in the alloc path is this compaction-capture short-circuit, prepped via `prep_new_page()` at line ~4195 without going through `get_page_from_freelist` again.
- Lock domains: `zone->lock` (spinlock) guards `free_area[]`/buddy merges/splits — taken in `rmqueue_buddy` (mm/page_alloc.c:3239-3282, `spin_lock_irqsave`, or `spin_trylock_irqsave` if `ALLOC_TRYLOCK`, failing → NULL, no blocking fallback) and in `rmqueue_bulk` (2547-2582, same trylock-or-block choice) and in `reserve_highatomic_pageblock`/`unreserve_highatomic_pageblock`. `pcp->lock` (separate per-CPU spinlock) guards `per_cpu_pages.lists[]` — always accessed via `pcp_spin_trylock`/`pcp_spin_unlock` macros (mm/page_alloc.c:153-167), which pin the task to a CPU (`preempt_disable`/`migrate_disable`) then `spin_trylock` (never a blocking spin_lock) — trylock, not a hard lock, is the pcp-path default everywhere, with fallback-to-NULL propagating up (`rmqueue_pcplist` returns NULL on failed trylock, forcing caller to fall through to `rmqueue_buddy`). IRQ rule: pcp trylock uses `local_irq_save` only on UP/non-RT (`pcp_trylock_prepare`, line 105-111); zone->lock users use explicit `_irqsave`.
- Refcount/frozen semantics: pages come off the buddy/pcp with `_refcount==0` ("frozen") — the natural invariant (`VM_BUG_ON_PAGE(page_count(buddy)!=0,...)` in `page_is_buddy`). `check_new_pages`/`rmqueue_buddy`'s retry-on-bad-page loop and `prep_new_page`/`post_alloc_hook` never touch refcount. Refcount is set to 1 explicitly and only by the outermost entry points: `__alloc_pages_noprof` (after `__alloc_frozen_pages_noprof`), `alloc_pages_bulk_noprof` (inline, per page), `alloc_pages_nolock_noprof` (after the nolock/frozen variant). This split is what "frozen pages" means at v7.0.
- State transitions: buddy-free (`PageBuddy` set, on `free_area[order].free_list[mt]`, `_refcount=0`) → (a) bulk-refilled onto a pcp list via `rmqueue_bulk`→`__rmqueue`, still `_refcount=0`, now on `pcp->lists[pindex]`; → (b) handed to caller via `__rmqueue_pcplist`/`__rmqueue_smallest` (`page_del_and_expand`: `__del_page_from_free_list` clears `PageBuddy`+private, then `expand()` re-inserts split remainders) → `check_new_pages` sanity → `prep_new_page`(`post_alloc_hook` + optional `prep_compound_page`) → refcount set to 1 by the entry point → allocated. Migratetype can change mid-path: claim/steal (`try_to_claim_block`, `__rmqueue_steal`) reassigns the pageblock's migratetype (`set_pageblock_migratetype`/`change_pageblock_range`) before/while pulling the page off, and `ALLOC_HIGHATOMIC` success triggers `reserve_highatomic_pageblock` which converts the whole surrounding pageblock to `MIGRATE_HIGHATOMIC` after the allocation succeeds.

#### 4. Hard-coded limits

- `MAX_PAGE_ORDER` = 10 unless `CONFIG_ARCH_FORCE_MAX_ORDER` set. include/linux/mmzone.h:30/:32. x86-64 never defines `ARCH_FORCE_MAX_ORDER` (confirmed: no such Kconfig symbol under arch/x86 — only arc/arm/arm64/loongarch/m68k/mips/nios2/powerpc/sh/sparc/xtensa define it), so on x86-64 `MAX_PAGE_ORDER` is unconditionally 10 (1024 pages = 4 MiB @ 4K pages).
- `MAX_ORDER_NR_PAGES` = `1 << MAX_PAGE_ORDER` = 1024 on x86-64. mmzone.h:34.
- `NR_PAGE_ORDERS` = `MAX_PAGE_ORDER + 1` = 11 (valid orders 0..10). mmzone.h:38.
- `PAGE_ALLOC_COSTLY_ORDER` = 3. mmzone.h:62.
- `PAGE_BLOCK_MAX_ORDER` = `MAX_PAGE_ORDER` unless `CONFIG_PAGE_BLOCK_MAX_ORDER` set (range 1-10, default 10 on x86). mmzone.h:41-45; must satisfy `PAGE_BLOCK_MAX_ORDER <= MAX_PAGE_ORDER` (build-time `#error` mmzone.h:52-54).
- `pageblock_order` — variable only if `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE` (powerpc-only, arch/powerpc/Kconfig:300); on x86-64 it's a compile-time macro `MIN_T(HUGETLB_PAGE_ORDER, PAGE_BLOCK_MAX_ORDER)` when `CONFIG_HUGETLB_PAGE` (typical x86-64 config), else `MIN_T(HPAGE_PMD_ORDER, PAGE_BLOCK_MAX_ORDER)`. include/linux/pageblock-flags.h:47-73 (effectively 9, i.e. 2 MiB, on stock x86-64).
- `MIGRATE_PCPTYPES` = 3 (UNMOVABLE/MOVABLE/RECLAIMABLE only ride the pcp lists). mmzone.h:68.
- `NR_LOWORDER_PCP_LISTS` = `MIGRATE_PCPTYPES * (PAGE_ALLOC_COSTLY_ORDER+1)` = 12; `NR_PCP_THP` = 2 if `CONFIG_TRANSPARENT_HUGEPAGE` else 0; `NR_PCP_LISTS` = 14 on typical x86-64. mmzone.h:721-727.
- `MAX_RECLAIM_RETRIES` = 16 (no-progress reclaim retry cap in `should_reclaim_retry`). mm/internal.h:610.
- `ALLOC_*` flag bit values: `ALLOC_NO_WATERMARKS`=0x04, `ALLOC_OOM`=0x08 (or aliased to NO_WATERMARKS if `!CONFIG_MMU`), `ALLOC_NON_BLOCK`=0x10, `ALLOC_MIN_RESERVE`=0x20, `ALLOC_CPUSET`=0x40, `ALLOC_CMA`=0x80, `ALLOC_NOFRAGMENT`=0x100 (0 if no `CONFIG_ZONE_DMA32`), `ALLOC_HIGHATOMIC`=0x200, `ALLOC_TRYLOCK`=0x400, `ALLOC_KSWAPD`=0x800. mm/internal.h:1347-1382. `ALLOC_RESERVES` = NON_BLOCK|MIN_RESERVE|HIGHATOMIC|OOM (internal.h:1385).
- `watermark_boost_factor` default 15000 (150% scaling, mult_frac/10000), `watermark_scale_factor` default 10, `min_free_kbytes` default 1024. mm/page_alloc.c:302-306.
- `defrag_mode` sysctl bounded `[0,1]` (SYSCTL_ZERO/SYSCTL_ONE). mm/page_alloc.c:6769-6777.
- `reserve_highatomic_pageblock` cap: min 1 pageblock, max ~1% of zone managed pages (`ALIGN(managed/100, pageblock_nr_pages)`), skipped entirely if 1% < one pageblock. mm/page_alloc.c:3456-3462.
- `try_to_claim_block` whole-block claim threshold: `free_pages + alike_pages >= 1 << (pageblock_order - 1)` (≥50% of block). mm/page_alloc.c:2368-2369.
- `should_try_claim_block` order thresholds: always claim if `order >= pageblock_order` or `order >= pageblock_order/2`. mm/page_alloc.c:2249-2256.
- `fallbacks[MIGRATE_PCPTYPES][MIGRATE_PCPTYPES-1]` table: UNMOVABLE→{RECLAIMABLE,MOVABLE}; MOVABLE→{RECLAIMABLE,UNMOVABLE}; RECLAIMABLE→{UNMOVABLE,MOVABLE}. mm/page_alloc.c:1951-1955.

#### 5. Version-specific facts (v7.0 vs. widely-documented older kernels)

- Claim/steal split is a full rename, not additive: `can_steal_fallback()`/`steal_suitable_fallback()`/`__rmqueue_fallback()` (the names in most existing write-ups) do not exist in this tree at all — replaced by `should_try_claim_block()` (mm/page_alloc.c:2235), `try_to_claim_block()` (2312), `__rmqueue_claim()` (2387), `__rmqueue_steal()` (2442), dispatched via the new `enum rmqueue_mode` state machine (2466) inside `__rmqueue()` (2478) so repeated `rmqueue_bulk()` iterations remember the successful fallback mode instead of re-scanning from NORMAL every time.
- `ALLOC_HIGH` → `ALLOC_MIN_RESERVE`, `ALLOC_HARDER` retired: the 50%/25%/62.5%-of-min-watermark reserve logic is now split across `ALLOC_MIN_RESERVE` + `ALLOC_NON_BLOCK` (mm/internal.h:1366-1372, `__zone_watermark_ok` mm/page_alloc.c:3617-3632).
- `ALLOC_TRYLOCK` + trylock-first locking discipline: `rmqueue_buddy`/`rmqueue_bulk` now branch spin_trylock vs spin_lock on `ALLOC_TRYLOCK`; pcp access is always `pcp_spin_trylock` (never a blocking pcp lock). This underpins the new `alloc_pages_nolock()`/`alloc_frozen_pages_nolock()` API (mm/page_alloc.c:7847, 7759) for NMI/hardirq-safe allocation — absent from older-generation allocator descriptions where `rmqueue()` unconditionally did `spin_lock_irqsave(&zone->lock,...)`.
- "Frozen pages" as a first-class concept: `__alloc_frozen_pages_noprof`/`alloc_frozen_pages`/`free_frozen_pages` (mm/internal.h:895-917, mm/page_alloc.c:5214) formalize the previously-implicit fact that buddy/pcp pages have `_refcount==0`; `set_page_refcounted()` is now a distinct, explicitly-called step rather than baked into `rmqueue()`.
- `alloc_hooks()`/`_noprof` naming split: every public entry point is now a macro expanding to `alloc_hooks(<name>_noprof(...))` for `CONFIG_MEM_ALLOC_PROFILING` code-tagging (include/linux/alloc_tag.h:262-266) — the real implementation always lives in a `_noprof`-suffixed function.
- `defrag_mode` sysctl: new global `/proc/sys/vm/defrag_mode` (mm/page_alloc.c:306, 6769) forces `ALLOC_NOFRAGMENT` unconditionally (`alloc_flags_nofragment` 3756-3790, `gfp_to_alloc_flags` 4536-4537) and raises kswapd's reclaim order to `pageblock_order` (`wake_all_kswapds` 4479-4482) — a stronger, global anti-fragmentation knob beyond the older per-allocation, DMA32-only `ALLOC_NOFRAGMENT` heuristic.
- THP-aware pcp lists: `order_to_pindex`/`pindex_to_order` (mm/page_alloc.c:684-715) special-case `HPAGE_PMD_ORDER` into two extra pcp lists (`NR_LOWORDER_PCP_LISTS`/`NR_PCP_THP`, mmzone.h:721-727) — older docs describe pcp lists as order-0-only or costly-order-only.
- `ZONE_BELOW_HIGH` fast-path caching: `get_page_from_freelist` now skips the high-watermark `zone_watermark_fast()` recheck via a cached zone flag bit (mm/page_alloc.c:3893-3899).
- "Unaccepted memory" (`cond_accept_memory`/`_deferred_grow_zone` alongside deferred struct-page init) appears directly inline in `get_page_from_freelist`'s watermark-failure handling (mm/page_alloc.c:3925-3944) — a Confidential-Computing-guest concept (lazily "accepting" hypervisor-donated memory).
- `zonelist_iter_begin`/`check_retry_zonelist` (mm/page_alloc.c:4393-4407, a seqlock over `CONFIG_MEMORY_HOTREMOVE` zonelist rebuilds) is a second, independent retry-cookie mechanism alongside the older `cpuset_mems_cookie`/`read_mems_allowed_begin`.

#### 6. Suggested page topics (agent D)

- `alloc_pages_nolock()` / frozen-pages-nolock family — built entirely around `ALLOC_TRYLOCK`, `alloc_frozen_pages_nolock_noprof` (mm/page_alloc.c:7759), and the "no slowpath, ever" contract; a genuinely new, self-contained API worth its own page.
- PCP sizing/adaptation (`nr_pcp_alloc`, `pcp->high_min/high_max/alloc_factor`, `decay_pcp_high`) — mm/page_alloc.c:3284-3332 and mmzone.h:744-758; the batch/high auto-scaling logic is intricate enough (and shared with the freeing-path seam `decay_pcp_high`) to deserve independent treatment from the base rmqueue walkthrough.
- Watermark/reserve arithmetic (`__zone_watermark_ok`, `__zone_watermark_unusable_free`, boosted watermarks) — mm/page_alloc.c:3575-3678, 2193-2228; enough ALLOC_*-flag interaction (RESERVES/MIN_RESERVE/NON_BLOCK/OOM/HIGHATOMIC/CMA all separately subtracted/added) to merit a dedicated reference page.
- Fragmentation-avoidance policy knobs (`defrag_mode`, `alloc_flags_nofragment`, page_group_by_mobility_disabled, claim-vs-steal thresholds) — ties together mm/page_alloc.c:2235-2464 and 3756-3790; a "why does the allocator fragment/defragment" narrative page distinct from the mechanical rmqueue anchors.
- Compaction-capture handshake (`capture_control`/`task_capc`/`compaction_capture`) — mm/internal.h:994, mm/page_alloc.c:759-812/978-1064; small but subtle cross-cutting mechanism between the alloc-side compaction call and the free-side `__free_one_page`, worth documenting as its own seam page given it straddles both areas.
- Freeing-path seam anchors (for cross-linking, authored by area E): `free_frozen_pages` (mm/page_alloc.c:3014), `__free_frozen_pages` (2964), `__free_one_page` (978), `free_pages_prepare`/`__free_pages_prepare` (1476), `decay_pcp_high` (2588), `drain_zone_pages`/`drain_all_pages`/`drain_local_pages` (gfp.h:398-400 declarations).

### Area E: freeing path, PCP dynamics, migrate-type runtime (agent E, complete)

Agent read every reported line on disk (not from index hints); lines remain hints at write time.

#### 1. Core structs

- `struct page` free-path fields: `flags` (now `memdesc_flags_t`, `.f` member), union `{lru|buddy_list|pcp_list|pcp_llist}`, `private` (buddy order / pcp_llist order stash) — include/linux/mm_types.h:79-116 (union 88-116).
- `memdesc_flags_t` — 1-word flags wrapper, replaces bare `unsigned long flags` — include/linux/mm_types.h:38-40.
- `struct free_area` — `free_list[MIGRATE_TYPES]` + `nr_free`, per order — include/linux/mmzone.h:138-141.
- `struct per_cpu_pages` — `lock` (real spinlock)/`count`/`high`/`high_min`/`high_max`/`batch`/`flags`(u8)/`alloc_factor`/`expire`(NUMA)/`free_count`/`lists[NR_PCP_LISTS]` — include/linux/mmzone.h:744-760.
- `struct per_cpu_zonestat`/`per_cpu_nodestat` — per-cpu vmstat diff accumulators folded by vmstat work — include/linux/mmzone.h:762-780.
- `struct zone` free-relevant fields — `free_area[NR_PAGE_ORDERS]` (999), `lock` (1013), `trylock_free_pages` llist_head (1016, new), `per_cpu_pageset`/`per_cpu_zonestats` (904-905), `pageset_high_min/high_max/pageset_batch` (910-912), `nr_reserved_highatomic`/`nr_free_highatomic` (886-887), `cma_pages` (974), `nr_isolate_pageblock` (985) — include/linux/mmzone.h:879-1040.
- `enum migratetype` + `MIGRATE_TYPES` census, `MIGRATE_PCPTYPES`/`MIGRATE_HIGHATOMIC` alias — include/linux/mmzone.h:64-90.
- `enum pageblock_bits` (PB_migrate_0..2, PB_compact_skip, PB_migrate_isolate) — include/linux/pageblock-flags.h:17-35.
- `struct capture_control` (compaction page-capture handoff) — mm/internal.h:994-997.
- `struct alloc_context` (seam struct, used by highatomic reserve/unreserve) — mm/internal.h:657-675.
- `struct cma` / `struct cma_memrange` — CMA area + multi-range descriptor, `nranges`/`ranges[CMA_MAX_RANGES]` — mm/cma.h:26-65.
- `fpi_t` — free-page-internal flags bitmask type — mm/page_alloc.c:63.
- `enum pb_isolate_mode` (MEM_OFFLINE/CMA_ALLOC/OTHER) — include/linux/page-isolation.h:50-54.
- `enum meminit_context` (MEMINIT_EARLY/MEMINIT_HOTPLUG) — include/linux/mmzone.h:1562-1565.
- `acr_flags_t`/`ACR_FLAGS_NONE`/`ACR_FLAGS_CMA` — include/linux/gfp.h:441-443.

#### 2. API families

Free entry points (refcount semantics):
- `__free_pages`/`free_pages`/`__free_page`/`free_page` macros — declared include/linux/gfp.h:389-394; defined mm/page_alloc.c:5322 (`___free_pages`), 5367, 5391.
- `free_pages_nolock` (trylock variant) — gfp.h:390; def page_alloc.c:5377-5389.
- `put_page`→`folio_put`(`folio_put_testzero`)/`folio_put_refs`(`folio_ref_sub_and_test`) — include/linux/mm.h:1879,1814-1818,1834-1838; last-ref drop detected here, hands off to `__folio_put`.
- `__folio_put` — mm/swap.c:97-114; routes zone-device/hugetlb/generic (generic → `free_frozen_pages`).
- `folios_put`/`folios_put_refs` (batch last-ref detection via `folio_ref_sub_and_test`) — include/linux/mm.h:1874,1840; def mm/swap.c:951-1004.
- `release_pages` — include/linux/mm.h:1859; def mm/swap.c:1018-1044 (packs into `folio_batch`, calls `folios_put_refs`→`free_unref_folios`).
- `free_frozen_pages`/`free_frozen_pages_nolock` — declared mm/internal.h:899,917 (mm-internal only, no public header); def page_alloc.c:3014-3022, thin wrappers of `__free_frozen_pages` with FPI_NONE/FPI_TRYLOCK.
- `free_unref_folios` — mm/internal.h:900; def page_alloc.c:3027-3118, batch free for LRU reclaim/`release_pages`.
- `free_contig_range`/`free_contig_frozen_range` — include/linux/gfp.h:466-467; def page_alloc.c:7368-7376 (loops `__free_page`)/7343-7359 (compound-aware, calls `free_frozen_pages` or per-pfn loop).
- `__free_pages_core` — decl mm/internal.h:815-816; def page_alloc.c:1618-1664, boot/hotplug entry: zeroes refcount, then `__free_pages_ok(…, FPI_TO_TAIL)`.
- `__putback_isolated_page`/`__isolate_free_page` — decl mm/internal.h:811-813; def page_alloc.c:3200-3210 (re-adds via `__free_one_page` FPI_SKIP_REPORT_NOTIFY|FPI_TO_TAIL) / 3150-3190.
- `put_page_back_buddy` — hwpoison take-off rollback, calls `__free_one_page` directly — page_alloc.c:3574-3589ish.

Free-prep / buddy internals:
- `free_pages_prepare`(public)/`__free_pages_prepare` — decl mm/internal.h:891; def page_alloc.c:1476-1479 / 1342-1474 (bad-page checks, PAGE_FLAGS_CHECK_AT_FREE, cpupid reset, init_on_free, kasan/kmsan, page_table_check_free, arch_free_page, reset_page_owner — all inline below).
- `free_tail_page_prepare` — page_alloc.c:1129-1219.
- `__free_one_page` (merge loop) — page_alloc.c:978-1064.
- `free_one_page` (locking wrapper) — page_alloc.c:1572-1606.
- `split_large_buddy` — page_alloc.c:1540-1561.
- `free_pcppages_bulk` — page_alloc.c:1486-1537.
- `add_page_to_zone_llist` — page_alloc.c:1563-1570.
- `move_to_free_list`/`__add_to_free_list`/`__del_page_from_free_list`/`del_page_from_free_list`/`get_page_from_free_area` — page_alloc.c:832-916.
- `buddy_merge_likely`/`find_buddy_page_pfn`/`page_is_buddy`/`__find_buddy_pfn` — page_alloc.c:926-941; mm/internal.h:775-788,717-736,755-759.
- `change_pageblock_range` — page_alloc.c:943-952.
- `compaction_capture`/`task_capc` — page_alloc.c:758-812.

PCP dynamics:
- `pcp_spin_trylock`/`pcp_spin_unlock`/`pcpu_spin_trylock`/`pcpu_spin_unlock` — page_alloc.c:134-167.
- `pcp_spin_lock_maybe_irqsave`/`_unlock_maybe_irqrestore` — page_alloc.c:177-194.
- `order_to_pindex`/`pindex_to_order`/`pcp_allowed_order` — page_alloc.c:684-726.
- `free_frozen_page_commit` (v7.0 name for the old "free_unref_page_commit") — page_alloc.c:2859-2959.
- `nr_pcp_free`/`nr_pcp_high` — page_alloc.c:2779-2850.
- `decay_pcp_high` — page_alloc.c:2588-2620.
- `drain_zone_pages` (NUMA remote-pageset expiry) — page_alloc.c:2628-2640.
- `drain_pages_zone`/`drain_pages`/`drain_local_pages` — page_alloc.c:2646-2689.
- `__drain_all_pages`/`drain_all_pages` — page_alloc.c:2701-2777.
- `zone_pcp_disable`/`zone_pcp_enable`/`zone_pcp_reset` — page_alloc.c:7387-7418.
- `zone_batchsize`/`zone_highsize`/`pageset_update`/`__zone_set_pageset_high_and_batch`/`zone_set_pageset_high_and_batch` — page_alloc.c:5922-6110.
- `setup_pcp_cacheinfo`/`zone_pcp_update_cacheinfo` (PCPF_FREE_HIGH_BATCH setter) — page_alloc.c:6146-6175.

Migratetype/pageblock accessors:
- `get_pfnblock_migratetype` — page_alloc.c:470-483; decl include/linux/pageblock-flags.h:84-85.
- `__get_pfnblock_flags_mask`/`__set_pfnblock_flags_mask` (static, v7.0 underlying helpers) — page_alloc.c:420-436,493-508.
- `get_pfnblock_bit`/`set_pfnblock_bit`/`clear_pfnblock_bit` (standalone-bit API) — page_alloc.c:446-548; decl pageblock-flags.h:86-91.
- `set_pageblock_migratetype`/`init_pageblock_migratetype` — page_alloc.c:555-601; decl page-isolation.h:56-58.
- `get/set/clear_pageblock_isolate` macros — include/linux/page-isolation.h:14-19.
- `get/clear/set_pageblock_skip` macros — include/linux/pageblock-flags.h:95-112.
- `is_migrate_isolate`/`is_migrate_isolate_page`/`is_migrate_cma`/`is_migrate_movable`/`migratetype_is_mergeable` — mmzone.h:96-124; page-isolation.h:6-13.
- `gfp_migratetype` — include/linux/gfp.h:24-38.

Isolation API:
- `start_isolate_page_range`/`undo_isolate_page_range`/`test_pages_isolated` — decl page-isolation.h:63-69; def mm/page_isolation.c:486-527/536-551/608-654.
- `set_migratetype_isolate`/`unset_migratetype_isolate` (static, internal) — page_isolation.c:165-221/223-284.
- `isolate_single_pageblock`/`has_unmovable_pages`/`page_is_unmovable`/`find_large_buddy` — page_isolation.c:324-448/127-158/18-110; `find_large_buddy` also at page_alloc.c:2073-2100.
- `pageblock_isolate_and_move_free_pages`/`pageblock_unisolate_and_move_free_pages`/`__move_freepages_block_isolate` — decl page-isolation.h:60-61; def page_alloc.c:2181-2189/2129-2179.
- `move_freepages_block`/`__move_freepages_block`/`prep_move_freepages_block` — page_alloc.c:2055-2069/1972-2003/2005-2053.

Highatomic / CMA / boot init:
- `reserve_highatomic_pageblock`/`unreserve_highatomic_pageblock` — page_alloc.c:3444-3485/3496-3573.
- `init_cma_reserved_pageblock`/`init_cma_pageblock` — mm/mm_init.c:2234-2252/2256-2261; decl mm/internal.h:1007.
- `cma_alloc`/`cma_alloc_frozen`/`__cma_alloc_frozen`/`cma_range_alloc` — mm/cma.c:943-953/918-924/860-916/~798-858.
- `cma_release`/`cma_release_frozen`/`__cma_release_frozen` — mm/cma.c:1012-1032/1034-1046/989-1000.
- `alloc_contig_range`/`alloc_contig_frozen_range`(`_noprof`) — include/linux/gfp.h:446-454; def page_alloc.c:7148-7161/6991-7129.
- `ALLOC_CMA` gate — mm/internal.h:1374; used page_alloc.c:2489,2514,3164,3589,3667,3798.
- `memmap_init_range`/`memmap_init_zone_range` (boot migratetype assignment) — mm/mm_init.c:872-939/941-964.

Free-page reporting / vmstat async chain:
- `page_reporting_notify_free` — mm/page_reporting.h:33-45.
- `__page_reporting_notify`/`__page_reporting_request`/`page_reporting_process`/`page_reporting_register` — mm/page_reporting.c:87-102/60-84/307-347/352-394.
- `refresh_cpu_vm_stats` — mm/vmstat.c:799-863.
- `vmstat_update`/`vmstat_shepherd`/`start_shepherd_timer`/`quiet_vmstat`/`refresh_vm_stats` — mm/vmstat.c:2034-2046/2117-2151/2153-2173/2082-2100/1970-1973.

Allocation-side seam symbols only (area D's turf): `__rmqueue` (page_alloc.c:2477-2540, "Call me with the zone->lock already held"), `enum rmqueue_mode` (2466-2470), `__rmqueue_smallest`/`__rmqueue_claim`/`__rmqueue_steal`/`__rmqueue_cma_fallback`, `find_suitable_fallback` (2283), `get_page_from_freelist` (3808), `__alloc_pages_slowpath` (4710), `alloc_frozen_pages*`/`__alloc_frozen_pages*` (mm/internal.h:895-917), `ALLOC_TRYLOCK` (mm/internal.h:1381).

#### 3. Lifecycle and locking

- Master lock: `zone->lock` spinlock serializes buddy mutation and pageblock-isolation flips; `account_freepages()` asserts it (`lockdep_assert_held`, page_alloc.c:817). `move_freepages_block`/`__isolate_free_page` do NOT take it themselves — callers must hold it (page_alloc.c:3462,3517).
- pcp lock: `per_cpu_pages.lock` is a real embedded spinlock (mmzone.h:745), not a `local_lock` — lets one CPU safely lock another CPU's pcp for remote drains.
- Refcounting: last ref drop is `folio_put_testzero`/`folio_ref_sub_and_test` (mm.h:1814-1838, mm/swap.c:951-1004); on hitting zero, hands to `__folio_put`/`folios_put_refs` → `free_frozen_pages`/`free_unref_folios`. CMA/contig alloc leave pages "frozen" (refcount 0) until `set_pages_refcounted()` publishes them (mm/cma.c:950, page_alloc.c:7158-7160).
- order>0 non-compound frees: `__free_pages_prepare`'s tail loop (page_alloc.c:1394-1414) still validates/clears `PAGE_FLAGS_CHECK_AT_PREP` on every subpage, but skips `free_tail_page_prepare` (compound-only bookkeeping) when `!PageCompound`; the whole run is then freed as one `order`-sized block via `__free_one_page`/`split_large_buddy`, not page-by-page.
- FPI_TRYLOCK deferred free (new): if `free_one_page`'s `spin_trylock_irqsave(&zone->lock)` fails, the page is pushed onto `zone->trylock_free_pages` (llist_head) via `add_page_to_zone_llist` (page_alloc.c:1579-1583,1563-1570) and only drained the next time a non-trylock free reacquires `zone->lock` (1588-1601).
- PCP trylock fallback: `__free_frozen_pages`/`free_unref_folios` call `pcp_spin_trylock`; on failure (or isolated migratetype) they fall straight to `free_one_page` (page_alloc.c:2990-3011,3070-3096); on PREEMPT_RT + nmi/hardirq the pcp trylock is skipped altogether in favor of the zone llist (2998-3002).
- State fields/transitions: `pcp->flags` bits `PCPF_PREV_FREE_HIGH_ORDER`/`PCPF_FREE_HIGH_BATCH` flip per free in `free_frozen_page_commit` (page_alloc.c:2888-2896); `pcp->free_count` grows on consecutive frees, capped at `batch<<CONFIG_PCP_BATCH_SCALE_MAX` (2897-2898); `pcp->alloc_factor >>= 1` decays every free (2875); `zone->flags` `ZONE_BELOW_HIGH`/`ZONE_RECLAIM_ACTIVE` read in `nr_pcp_high` (2826,2836) and `ZONE_BELOW_HIGH` cleared + `kswapd_clear_hopeless()` fired from the free-commit path (2941-2956).
- Async/deferred #1 — vmstat decay chain: `shepherd` deferrable work (mm/vmstat.c:2110) fires every `sysctl_stat_interval` (HZ, 1966) → `vmstat_shepherd` (2117) queues per-cpu `vmstat_work` on cpus with `need_update()` (2052,2141-2142) → `vmstat_update` (2034) → `refresh_cpu_vm_stats(true)` (2036) → per zone calls `decay_pcp_high()` (830) and, under CONFIG_NUMA, `drain_zone_pages()` once `pcp->expire` counts down from 3 (822,840-860); `vmstat_update` reschedules itself while `changed==true`. `quiet_vmstat()` (NOHZ) calls `refresh_cpu_vm_stats(false)` — folds stat diffs only, skips decay/drain.
- Async/deferred #2 — remote drains: `drain_all_pages`/`__drain_all_pages` (2701-2777) drain every other online CPU's pcplist in-line from the calling CPU via that CPU's own `pcp->lock` (no IPI, no per-cpu work item), serialized process-wide by `pcpu_drain_mutex` (page_alloc.c:214) with `mutex_trylock` fast path for concurrent non-full drains (2716-2720).
- Async/deferred #3 — free-page reporting: `page_reporting_notify_free()` (inline, called from `__free_one_page`) → `__page_reporting_notify` → `__page_reporting_request` schedules `prdev->work` after `PAGE_REPORTING_DELAY` (2*HZ) → `page_reporting_process` walks zones, isolates pages under `zone->lock`, hands to driver `report()`, reschedules itself if still requested (mm/page_reporting.c:50-102,307-347).
- Isolation locking: `set_migratetype_isolate`/`unset_migratetype_isolate`/`test_pages_isolated` each take `spin_lock_irqsave(&zone->lock,…)` around the flag flip / free-page scan (page_isolation.c:176,232,644); the pre-scan in `test_pages_isolated` (631-635) is intentionally lock-free/racy, matching `__get_pfnblock_flags_mask`'s documented racy-read contract (page_alloc.c:429-433).
- Where a freed page goes: `page_zone`/`page_zonenum`/`page_to_nid` all decode `page->flags.f` bit-fields set once at `__init_single_page`→`set_page_links` (mm/mm_init.c:581,585) and never touched by the free-prep masks — zone/node are immutable at free (mm.h:2210-2213,1990-1993; mmzone.h:1189-1192). Migratetype is re-read fresh via `get_pfnblock_migratetype` at every free site (page_alloc.c:1524,1553,2989,3066); an isolated pageblock forces the isolated/bypass path in `__free_frozen_pages`/`free_unref_folios` (2990-2994,3070-3096).

#### 4. Hard-coded limits

- `PAGE_ALLOC_COSTLY_ORDER` = 3 — mmzone.h:62.
- `MAX_PAGE_ORDER` = 10 default (or `CONFIG_ARCH_FORCE_MAX_ORDER`); `NR_PAGE_ORDERS`=MAX_PAGE_ORDER+1; `MAX_ORDER_NR_PAGES`=1<<MAX_PAGE_ORDER — mmzone.h:30-38.
- `PAGE_BLOCK_MAX_ORDER` = MAX_PAGE_ORDER (or `CONFIG_PAGE_BLOCK_MAX_ORDER`); `pageblock_order` derives from it (HUGETLB/THP/plain cases) — mmzone.h:42-44; include/linux/pageblock-flags.h:47-73.
- `CONFIG_PCP_BATCH_SCALE_MAX`: default 5, range 0-6 — mm/Kconfig:670-673.
- `NR_LOWORDER_PCP_LISTS`=MIGRATE_PCPTYPES*(PAGE_ALLOC_COSTLY_ORDER+1); `NR_PCP_THP`=2 (THP)/0; `NR_PCP_LISTS`=sum — mmzone.h:721-727.
- `BOOT_PAGESET_BATCH` = 1 — page_alloc.c:5793.
- `MIN_PERCPU_PAGELIST_HIGH_FRACTION` = 8 — page_alloc.c:95.
- `zone_batchsize()`: batch=min(managed_pages>>12, SZ_256K/PAGE_SIZE), rounded down to 2^n−1 — page_alloc.c:5922-5950.
- `zone_highsize()`: high=max(total_pages/nr_split_cpus, batch*4) — page_alloc.c:5970-6013.
- MIGRATE_HIGHATOMIC reserve cap: ~1% of zone managed pages, min 1 pageblock — page_alloc.c:3450-3458.
- `watermark_boost_factor` default 15000 (÷10000 scale), `watermark_scale_factor` default 10 — page_alloc.c:304-305.
- `sysctl_lowmem_reserve_ratio` defaults {DMA:256, DMA32:256, NORMAL:32, HIGHMEM:0, MOVABLE:0} — page_alloc.c:258-270.
- `PAGE_REPORTING_CAPACITY` = 32 sg entries — include/linux/page_reporting.h:9; `PAGE_REPORTING_DELAY` = 2*HZ — mm/page_reporting.c:50.
- `CMA_MAX_RANGES` = 8 — mm/cma.h:37; `CMA_MAX_NAME` = 64 — include/linux/cma.h:13.
- `sysctl_stat_interval` default HZ — mm/vmstat.c:1966; NUMA remote-pcp `expire` window = 3 refresh cycles — mm/vmstat.c:822.
- `ALLOC_CMA`=0x80, `ALLOC_HIGHATOMIC`=0x200, `ALLOC_TRYLOCK`=0x400 — mm/internal.h:1374,1380-1381.

#### 5. Version-specific facts

- `free_unref_page` (single page) → renamed `free_frozen_pages`, wrapping `__free_frozen_pages(FPI_NONE)`; new nolock twin `free_frozen_pages_nolock`/`FPI_TRYLOCK` — page_alloc.c:3014-3022.
- `free_unref_page_list` is gone; the sole surviving `free_unref_*` name is the folio_batch API `free_unref_folios` (page_alloc.c:3027), reused by mm/vmscan.c and mm/swap.c.
- `free_unref_page_commit` → renamed `free_frozen_page_commit` — page_alloc.c:2859.
- `FPI_TRYLOCK` is new: never blocks on `zone->lock`; failure defers onto `zone->trylock_free_pages` llist, drained by the next ordinary free — page_alloc.c:63-91,1563-1601; mmzone.h:1016 (new field); mm_types.h:99-101 (`pcp_llist` union member, new).
- "Frozen pages" convention (post-alloc refcount left at 0, published via `set_pages_refcounted()`) now spans alloc (`__alloc_frozen_pages*`, `alloc_contig_frozen_range*`) and free (`free_frozen_pages*`, `free_contig_frozen_range`) — mm/internal.h:895-917; page_alloc.c:6991-7161,7343-7376; mm/cma.c:918-953.
- `alloc_contig_range`/`free_contig_range` are now thin wrappers around `alloc_contig_frozen_range`/`free_contig_frozen_range` plus an explicit refcount publish — page_alloc.c:7148-7161,7368-7376.
- `page->flags` is no longer a bare `unsigned long`: it is `memdesc_flags_t{f}`; zone/node/lru-gen accessors were rewritten around `memdesc_zonenum`/`memdesc_nid` helpers — mm_types.h:38-40,80; mmzone.h:1183-1197; mm.h:1976-1993.
- Pageblock isolation uses a dedicated `PB_migrate_isolate` bit plus standalone `get/set/clear_pfnblock_bit`, instead of overloading the migratetype value — pageblock-flags.h:17-35,86-112; page-isolation.h:14-19.
- `get/set_pageblock_migratetype` are layered on file-static `__get_pfnblock_flags_mask`/`__set_pfnblock_flags_mask` (double-underscore) rather than one non-static get/set pair — page_alloc.c:420-436,493-508,470-483,555-575.
- `set_migratetype_isolate`/`has_unmovable_pages` now take `enum pb_isolate_mode` (MEM_OFFLINE/CMA_ALLOC/OTHER) instead of ad hoc bool/flags args; new `isolate_single_pageblock`+`find_large_buddy` explicitly split multi-pageblock buddies straddling a boundary — page_isolation.c:18-158,165-221,324-448.
- Isolation-time freelist move is split into `pageblock_isolate_and_move_free_pages`/`__move_freepages_block_isolate` (calls `split_large_buddy` when a buddy spans blocks) rather than reusing plain `move_freepages_block` — page_alloc.c:2102-2189.
- `split_large_buddy()` is a new helper used by both `free_one_page` (trylock-llist flush) and pageblock unisolation to stop a merge crossing a migratetype/isolation boundary — page_alloc.c:1540-1561.
- `PCPF_PREV_FREE_HIGH_ORDER`/`PCPF_FREE_HIGH_BATCH` pcp->flags bits plus cache-topology-aware `zone_pcp_update_cacheinfo`/`setup_pcp_cacheinfo` are new tuning layered on the older single free-factor heuristic — mmzone.h:729-742; page_alloc.c:6146-6175.
- `pcp->high` is now split into `high_min`/`high_max` with zone-level `pageset_high_min/high_max` caches, replacing a single `pcp->high` tunable — mmzone.h:747-749,910-912.
- `drain_all_pages`/`__drain_all_pages` drain remote CPUs' pcplists in-line via each remote `per_cpu_pages`'s own spinlock, not IPI/`on_each_cpu_mask` — page_alloc.c:2646,2701-2767 — enabled by `pcp->lock` being a genuine per-CPU spinlock (mmzone.h:745).
- `acr_flags_t`/`ACR_FLAGS_CMA` formalizes the CMA-vs-plain distinction into `alloc_contig_*range` instead of an implicit bool — gfp.h:441-443.
- `ALLOC_TRYLOCK` (alloc side) mirrors `FPI_TRYLOCK` (free side) for `alloc_pages_nolock()` — mm/internal.h:1381 (seam only).

#### 6. Suggested page topics (agent E)

- Free-page-reporting subsystem end-to-end (virtio-balloon-style inflate): state machine IDLE/REQUESTED/ACTIVE, scatterlist batching — mm/page_reporting.c:50-102,260-394; mm/page_reporting.h:33-45.
- PCP cache-topology-aware tuning (`PCPF_FREE_HIGH_BATCH`, `setup_pcp_cacheinfo`) as its own page — page_alloc.c:6146-6175; mmzone.h:736-742.
- kswapd "hopeless node" tracking and its coupling to the pcp free-commit path — page_alloc.c:2941-2956; mmzone.h:1544-1556; mm/vmscan.c:7406.
- `memdesc_flags_t`/struct-page flags-layout rework and its ripple into zone/node/lru-gen accessors — mm_types.h:38-40,80; mmzone.h:1183-1197; mm.h:1976-1993.
- Unaccepted memory (TDX/SEV-SNP lazy accept) interaction with `__free_pages_core` and page isolation — page_alloc.c:319-322,1652-1657,7626-7720; mm/page_isolation.c:173-174.
- alloc_contig/CMA pageblock-isolation internals: `isolate_single_pageblock` straddling-buddy handling — mm/page_isolation.c:302-448; page_alloc.c:2073-2100.
- The "frozen pages" refcount convention as a cross-cutting theme spanning alloc/free/CMA/contig — mm/internal.h:895-917; mm/cma.c:918-953; page_alloc.c:6991-7161.
- Memory-allocation-profiling (`pgalloc_tag`) hooks on the free path — page_alloc.c:1269-1340,1377,1435.
- `zone->trylock_free_pages` llist as a general "deferred free" pattern (compare/contrast with RCU-freed pages) — page_alloc.c:1563-1601; mmzone.h:1016.

## Directory organization (proposed)

All pages under `${SKILL_DIR}/docs/mm/`, two levels deep, matching the house layout. Eight new groups beside the pre-existing `vma/` (untouched):

```
docs/mm/
├── physmem/      the physical memory model: sections, sparsemem/vmemmap, PFN, page->flags layout, memmap init
├── zone/         nodes and zones: pglist_data, struct zone, zonelists, watermarks, reserves, per-zone types
├── migratetype/  migrate types: semantics, one page per type, isolation, contiguous allocation
├── gfp/          allocation-context flags seen by callers: GFP bits, recipes, memalloc scopes, PF_MEMALLOC
├── buddy/        the buddy allocator's data structures: free_area, buddy math, PageBuddy encoding
├── pcp/          per-CPU page lists: the structure, sizing, adaptive tuning, drains
├── alloc/        the allocation path: entry points through get_page_from_freelist, rmqueue, fallback, prep
└── free/         the freeing path: entry points, free-prep, PCP free, buddy merge, placement
```

Rationale: the request's eight H3 headings map onto these groups nearly one-to-one; the two deliberate reshapes are (a) `pcp/` pulled out as its own group because the prompt places PCP bullets under both "Nodes and Zones" and "The Buddy allocator" while the machinery (sizing, adaptive tuning, drains) is one coherent object neither heading owns, and (b) "GFP flags" + "Memalloc flags" fused into `gfp/` because memalloc scope flags exist only to rewrite GFP masks (`current_gfp_context`) and separating them would force each group to recap the other. Boot-time construction gets no group of its own: each construction page lives beside the object it constructs (`physmem/memmap-init`, `physmem/deferred-init`, `zone/free-area-init`, `zone/numa-memblks`, `physmem/section-lifecycle`), so a reader of an object page finds its lifecycle beside it.

## Page catalog

Tags: [prompt] = realizes an explicit prompt.md bullet; [curated] = gap-fill under the prompt's "curate new pages where you see fit" / "you curate this" mandates. Line numbers are digest hints, to re-verify on disk at write time.

### physmem/ (12 pages)

| page | scope (anchor symbols) | tag |
|---|---|---|
| memory-models.md | FLATMEM vs SPARSEMEM vs SPARSEMEM_VMEMMAP/_EXTREME selection and what each changes: memory_model.h dispatch of __pfn_to_page/__page_to_pfn (memory_model.h:18-74), Kconfig plumbing (mm/Kconfig sparsemem block; arch/x86 always SPARSEMEM), per-model cost/precision tradeoffs, MAX_PHYSMEM_BITS/SECTION_SIZE_BITS inputs (arch/x86/include/asm/sparsemem.h:28-29) | [prompt] |
| sections.md | struct mem_section (mmzone.h:1917-1945) + struct mem_section_usage (:1904-1911), the two-level root table mem_section[][] (mm/sparse.c:26-32) + SPARSEMEM_EXTREME indexing (SECTION_NR_TO_ROOT/__nr_to_section, mmzone.h:1947-1980), section_mem_map pointer+flag encoding (SECTION_MARKED_PRESENT/HAS_MEM_MAP/IS_ONLINE/IS_EARLY/IS_VMEMMAP_PREINIT/MAP_LAST_BIT) and coded-mem_map arithmetic, subsection_map bitmap, section state bits as a state machine | [prompt] |
| section-lifecycle.md | boot: sparse_init (sparse.c:594-625) → memblocks_present/memory_present → sparse_init_nid (:532-588) → sparse_init_early_section/sparse_init_one_section; hotplug: sparse_add_section/section_activate/section_deactivate/sparse_remove_section (:817-977), usage alloc (memblock vs kzalloc), kfree_rcu(usage) + RCU reader contract, online_mem_sections, locks (mem_hotplug_lock, pgdat resize) | [curated] |
| pfn.md | the PFN as the physical index: pfn.h macros (PFN_UP/DOWN/PHYS/ALIGN), pfn_valid() RCU-sched contract (mmzone.h:2168-2210), pfn_section_valid/pfn_section_first_valid (:2119-2163), first/next/for_each_valid_pfn iterators (:2212-2261), pfn_in_present_section, pfn_to_online_page (memory_hotplug.c:346-384) | [prompt] |
| pfn-section-conversion.md | pfn_to_section_nr/section_nr_to_pfn (mmzone.h:1876-1883), __pfn_to_section/__nr_to_section (:2112-2115, :1968-1980), subsection_map_index, PFN_SECTION_SHIFT/PAGES_PER_SECTION/SUBSECTION constants (:1861-1898) with worked bit arithmetic | [prompt] |
| pfn-page-conversion.md | page_to_pfn/pfn_to_page over __page_to_pfn/__pfn_to_page per memory model (memory_model.h:18-74; vmemmap pointer arithmetic on the SPARSEMEM_VMEMMAP path), folio_pfn/pfn_folio (mm.h:2257-2265), page_folio/_Generic + folio_page (page-flags.h:306-319), validity preconditions | [prompt] |
| page-flags-layout.md | the page->flags bit budget: page-flags-layout.h widths (SECTIONS/NODES/ZONES/LAST_CPUPID; SECTIONS_WIDTH=0 under VMEMMAP), memdesc_flags_t (mm_types.h:38-40), memdesc_section/zonenum/nid/is_zone_device (mm.h:2237-2246, mmzone.h:1183-1254), page_zonenum/page_to_nid/page_zone/page_pgdat + folio twins, page_zone_id, set_page_links seam (mm_init.c:585) | [curated] |
| vmemmap.md | the virtual memmap: VMEMMAP_START/__VMEMMAP_BASE_L4/L5 (pgtable_64_types.h:113-118), vmemmap_populate arch entry (init_64.c:1558-1579) + vmemmap_set_pmd/vmemmap_check_pmd, vmemmap_populate_basepages/hugepages + vmemmap_pte..pgd_populate chain (sparse-vmemmap.c:154-466), struct vmem_altmap (memremap.h:21-28), vmemmap_free/remove_pagetable, register_page_bootmem_memmap | [prompt] |
| vmemmap-optimizations.md | HVO: vmemmap_populate_hvo/vmemmap_undo_hvo/vmemmap_wrprotect_hvo (sparse-vmemmap.c:319-403); SECTION_IS_VMEMMAP_PREINIT + sparse_vmemmap_init_nid_early/late hooks (mmzone.h:2008-2100); ZONE_DEVICE compound dedup vmemmap_populate_compound_pages/reuse_compound_section (:479-557) + vmemmap_can_optimize; hugetlb policy itself out of scope | [curated] |
| pageblock.md | pageblock_order/pageblock_nr_pages derivation (pageblock-flags.h:47-75; MIN_T(HUGETLB_PAGE_ORDER, PAGE_BLOCK_MAX_ORDER)=9), PAGE_BLOCK_MAX_ORDER Kconfig (mmzone.h:41-45), enum pageblock_bits incl. standalone PB_migrate_isolate (pageblock-flags.h:17-35), NR_PAGEBLOCK_BITS, storage in mem_section_usage->pageblock_flags, bitidx math (get_pageblock_bitmap/pfn_to_bitidx page_alloc.c:363-408), lock-free __get/__set_pfnblock_flags_mask cmpxchg contract (:420-436,493-508), get/set/clear_pfnblock_bit + get_pfnblock_migratetype/set_pageblock_migratetype/init_pageblock_migratetype (:446-601), set_pageblock_order (mm_init.c:1507-1540) | [prompt] |
| memmap-init.md | boot struct-page init: memmap_init→memmap_init_zone_range→memmap_init_range (mm_init.c:872-1001) with enum meminit_context MEMINIT_EARLY vs MEMINIT_HOTPLUG gating (mmzone.h:1562-1565), __init_single_page/set_page_links (:581-597), init_unavailable_range, overlap_memmap_init, reserve_bootmem_region + memmap_init_reserved_pages (PageReserved), boot-time pageblock migratetype assignment, memblock_free_all→__free_pages_memory→__free_pages_core handoff (memblock.c:2200-2350), KHO scratch note | [curated] |
| deferred-init.md | CONFIG_DEFERRED_STRUCT_PAGE_INIT end-to-end: deferred_pages static key (page_alloc.c:332-336), defer_init/first_deferred_pfn (mm_init.c:708-743), page_alloc_init_late → pgdatinit kthreads → padata_do_multithreaded chunks (:2058-2332), completion tracking, deferred_grow_zone synchronous top-up under pgdat_resize_lock | [curated] |

### zone/ (15 pages)

| page | scope (anchor symbols) | tag |
|---|---|---|
| pglist-data.md | struct pglist_data field-group tour (mmzone.h:1381), NODE_DATA/node_data (numa.h:25-26), alloc_node_data/alloc_offline_node_data (mm/numa.c:12/35), node_start_pfn/spanned/present, totalreserve_pages, per-node locks (node_size_lock, kswapd_lock as mention), init via free_area_init_node (mm_init.c:1714); reclaim/compaction daemon fields are mentions only (other campaigns' turf) | [prompt] |
| node-states.md | node_states[] N_POSSIBLE→N_ONLINE→N_MEMORY transitions (nodemask.h:384-404; mm_init.c:1749,1917-1920), node_set_online/offline + nr_node_ids/nr_online_nodes (:441-454), for_each_node(_state)/for_each_online_node, first/next_online_pgdat + for_each_online_pgdat (mmzone.c:13-25) | [curated] |
| numa-memblks.md | boot NUMA description: struct numa_memblk/numa_meminfo (numa_memblks.h:13-19), numa_add_memblk/numa_cleanup_meminfo/numa_register_meminfo/numa_memblks_init (numa_memblks.c:200-445), numa_set_distance/__node_distance/numa_reset_distance (:40-127), SRAT/SLIT feed (srat.c:348), node_distance + LOCAL/REMOTE/RECLAIM_DISTANCE (topology.h:46-73) | [curated] |
| zone.md | struct zone complete field-group tour (mmzone.h:879-1075), spanned/present/present_early/managed/cma_pages + accessors, zone_is_initialized/contiguous/empty, populated_zone/managed_zone, zone_end_pfn/zone_spans_pfn, zone->lock (:1013) vs span_seqlock (:990), enum zone_flags (ZONE_BOOSTED_WATERMARK/ZONE_RECLAIM_ACTIVE/ZONE_BELOW_HIGH, :1069-1075) as a state census | [curated] |
| free-area-init.md | zone/node construction: free_area_init (mm_init.c:1820) pipeline — calculate_node_totalpages/zone_spanned/absent_pages_in_node (:1221-1336), free_area_init_core (:1593), init_currently_empty_zone (:1446), check_for_memory (:1749), mm_core_init_early/mm_core_init ordering (:2683/2694: build_all_zonelists → memblock_free_all → setup_per_cpu_pageset → init_per_zone_wmark_min postcore_initcall), set_zone_contiguous (:2264), free_area_init_core_hotplug | [curated] |
| watermarks.md | _watermark[NR_WMARK] + watermark_boost fields, min/low/high/promo_wmark_pages + wmark_pages accessors (mmzone.h:1077-1101), setup chain: calculate_min_free_kbytes sqrt formula (page_alloc.c:6545) → init_per_zone_wmark_min (:6561) → __setup_per_zone_wmarks (:6433, SWAP_CLUSTER_MAX floor), sysctls min_free_kbytes/watermark_scale_factor/watermark_boost_factor, boost lifecycle: boost_watermark set (:2193) → lazy clear + kswapd wake in rmqueue (:3427-3432) → decay in balance_pgdat (mention only, reclaim turf); WMARK_PROMO role note | [prompt] |
| lowmem-reserves.md | lowmem_reserve[] semantics with worked example, sysctl_lowmem_reserve_ratio defaults (page_alloc.c:258-270), setup_per_zone_lowmem_reserve math (:6388), calculate_totalreserve_pages (:6338) + totalreserve_pages consumers | [prompt] |
| zonelist.md | struct zoneref/zonelist (mmzone.h:1310/1329), MAX_ZONES_PER_ZONELIST/MAX_ZONELISTS, ZONELIST_FALLBACK vs NOFALLBACK, build_all_zonelists/__build_all_zonelists (:5797/5889) + hotplug rebuild under zonelist_update_seq (:4391) + zonelist_iter_begin/check_retry_zonelist, build_zonelists + find_next_best_node distance ordering (:5616/5704), build_thisnode_zonelists, iteration API first/next_zones_zonelist (mmzone.c:56) + for_each_zone_zonelist(_nodemask) + zonelist_zone/zone_idx/node_idx | [prompt] |
| zone-dma.md | ZONE_DMA role + 16 MiB extent (MAX_DMA_PFN dma.h:74; arch_zone_limits_init init.c:999), GFP_DMA population, protection via lowmem_reserve, modern users census | [prompt] |
| zone-dma32.md | ZONE_DMA32 role + 4 GiB extent (MAX_DMA32_PFN dma.h:77), GFP_DMA32 users, ALLOC_NOFRAGMENT relationship | [prompt] |
| zone-normal.md | ZONE_NORMAL as the default kernel zone, direct-map relationship, what may only live here, fallback position in zonelists | [prompt] |
| zone-movable.md | ZONE_MOVABLE sizing (find_zone_movable_pfns_for_nodes mm_init.c:357-579, kernelcore=/movablecore=/movable_node parsing :285-302), only-movable-allocations invariant, gfp_zone routing of __GFP_MOVABLE|__GFP_HIGHMEM, hotplug affinity, CMA mimicry note | [prompt] |
| percpu-vmstat.md | per_cpu_zonestat/per_cpu_nodestat (mmzone.h:762-780), stat_threshold, zone_page_state vs zone_page_state_snapshot, refresh_cpu_vm_stats fold (vmstat.c:799-863), shepherd deferrable work chain vmstat_shepherd→vmstat_update (:2034-2151), quiet_vmstat, consumers: watermark-fast drift recheck, decay_pcp_high/drain_zone_pages hooks | [curated] |
| zone-device.md | ZONE_DEVICE as a zone (user-directed, decision 2): enum placement + why it sits outside the buddy allocator (never on free lists, no watermarks), memdesc_is_zone_device/page-flags behavior, pfn_to_online_page exclusion + SECTION_TAINT_ZONE_DEVICE section taint (mmzone.h:2006-2019), memmap_init_zone_device (mm_init.c:1108), present/spanned accounting for device ranges | [curated] |
| dev-pagemap.md | the ZONE_DEVICE machinery (user-directed, decision 2): struct dev_pagemap (memremap.h:133) field-by-field + enum memory_type census (:68: PRIVATE/COHERENT/FS_DAX/GENERIC/PCI_P2PDMA), struct dev_pagemap_ops (:77) with complete callback semantics (page_free, migrate_to_ram) per the request's ops-structure rule, memremap_pages/devm_memremap_pages/memunmap_pages lifecycle (memremap.c:266/374/112), get_dev_pagemap (:401), device-folio free path free_zone_device_folio (:416), vmem_altmap backing seam (physmem/vmemmap.md owns altmap mechanics) | [curated] |

### migratetype/ (9 pages)

| page | scope (anchor symbols) | tag |
|---|---|---|
| overview.md | enum migratetype on-disk census (mmzone.h:64-90: UNMOVABLE/MOVABLE/RECLAIMABLE/PCPTYPES=3/HIGHATOMIC=PCPTYPES/CMA/ISOLATE/TYPES), migratetype_names, gfp_migratetype (gfp.h:24-38), fallbacks[] table (page_alloc.c:1951-1955), is_migrate_* predicates + migratetype_is_mergeable (mmzone.h:96-124), page_group_by_mobility_disabled, boot-time initial assignment, the type-flip primitive: prep_move_freepages_block/__move_freepages_block/move_freepages_block (:1972-2069) + change_pageblock_range (:943) | [curated] |
| unmovable.md | MIGRATE_UNMOVABLE: which gfp masks land here, typical owners (kernel/slab/page tables), fallback order {RECLAIMABLE,MOVABLE}, why unmovable pollution of movable blocks is the fragmentation hazard, claim/steal interplay | [prompt] |
| movable.md | MIGRATE_MOVABLE: __GFP_MOVABLE population (user/LRU pages), why movability enables compaction/CMA/offline, fallback order, relation to ZONE_MOVABLE and CMA eligibility | [prompt] |
| reclaimable.md | MIGRATE_RECLAIMABLE: __GFP_RECLAIMABLE (SLAB_RECLAIM_ACCOUNT slabs, dcache/inode caches), fallback order, shrinker connection at census level | [prompt] |
| highatomic.md | MIGRATE_HIGHATOMIC lifecycle: reserve_highatomic_pageblock trigger on ALLOC_HIGHATOMIC success (page_alloc.c:3444-3485) with the 1%-of-zone cap, unreserve_highatomic_pageblock from the slowpath (:3496-3573), nr_reserved_highatomic/nr_free_highatomic accounting, watermark subtraction seam, ALLOC_HIGHATOMIC access rules | [prompt] |
| cma.md | MIGRATE_CMA lifecycle: struct cma/cma_memrange (cma.h:26-65), init_cma_reserved_pageblock/init_cma_pageblock (mm_init.c:2234-2261), cma_alloc/cma_alloc_frozen/__cma_alloc_frozen/cma_range_alloc (cma.c:798-953), cma_release(_frozen) (:989-1046), ALLOC_CMA gate + gfp_to_alloc_flags_cma, __rmqueue_cma_fallback seam, NR_FREE_CMA_PAGES accounting, only-movable invariant | [prompt] |
| isolate.md | MIGRATE_ISOLATE state machine and API: PB_migrate_isolate standalone bit + get/set/clear_pageblock_isolate (page-isolation.h:14-19), set/unset_migratetype_isolate (page_isolation.c:165-284), start/undo_isolate_page_range/test_pages_isolated (:486-654), enum pb_isolate_mode, has_unmovable_pages/page_is_unmovable, users (offline, alloc_contig/CMA), nr_isolate_pageblock, zone->lock rules + racy pre-scan contract; free-page movement is the seam (pageblock_isolate_and_move_free_pages, opened by isolate-freepage-move.md) | [prompt] |
| isolate-freepage-move.md | moving free pages across an isolation flip: pageblock_isolate_and_move_free_pages/pageblock_unisolate_and_move_free_pages/__move_freepages_block_isolate (page_alloc.c:2102-2189), isolate_single_pageblock (page_isolation.c:324-448), find_large_buddy (page_alloc.c:2073-2100), split_large_buddy interaction at isolation boundaries, __isolate_free_page/__putback_isolated_page take-off/put-back primitives (internal.h:811-812; page_alloc.c:3150-3210) | [curated; split of isolate.md per plan review] |
| alloc-contig.md | alloc_contig_frozen_range walkthrough (page_alloc.c:6991-7129: isolate→migrate→test_pages_isolated→take), acr_flags_t/ACR_FLAGS_CMA (gfp.h:441-443), __alloc_contig_verify_gfp_mask, alloc_contig_range/alloc_contig_pages wrappers (:7148-7161), free_contig_range/free_contig_frozen_range (:7343-7376), consumers (CMA, hugetlb gigantic, virtio-mem; offline as mention); live-page migration treated as a black-box seam | [curated] |

### gfp/ (8 pages; realizes the "GFP flags" and "Memalloc flags" prompt headings, both marked "you curate this")

| page | scope (anchor symbols) | tag |
|---|---|---|
| flag-census.md | every ___GFP_*/__GFP_* bit with hex value, meaning, and key check sites (gfp_types.h:26-300 incl. the bit-9 hole, LOCKDEP/KASAN_HW_TAGS conditionals on x86-64), GFP_RECLAIM_MASK/GFP_BOOT_MASK/GFP_CONSTRAINT_MASK/GFP_SLAB_BUG_MASK internal filters (mm/internal.h:74-86), __GFP_BITS_SHIFT/MASK | [curated] |
| zone-selection.md | __GFP_DMA/DMA32/HIGHMEM/MOVABLE + GFP_ZONEMASK, gfp_zone + GFP_ZONE_TABLE/GFP_ZONE_BAD bit-table decode with worked example (gfp.h:117-165), OPT_ZONE_* on x86-64 (no HIGHMEM), gfp_zonelist/node_zonelist + __GFP_THISNODE→NOFALLBACK, gfp_migratetype (seam to migratetype/overview) | [curated] |
| reclaim-policy.md | __GFP_IO/__GFP_FS/__GFP_DIRECT_RECLAIM/__GFP_KSWAPD_RECLAIM/__GFP_RECLAIM semantics, __GFP_NORETRY/__GFP_RETRY_MAYFAIL/__GFP_NOFAIL policies + costly-order interaction (PAGE_ALLOC_COSTLY_ORDER), gfpflags_allow_blocking/gfpflags_allow_spinning (gfp.h:42-64), gfp_compaction_allowed, fs_reclaim_acquire/release lockdep map + __GFP_NOLOCKDEP + might_alloc (page_alloc.c:4326-4383; sched/mm.h:315-324) | [curated] |
| watermark-modifiers.md | the reserve-forgiveness triad __GFP_HIGH/__GFP_MEMALLOC/__GFP_NOMEMALLOC (gfp_types.h:152-178): what each grants, caller doctrine, __gfp_pfmemalloc_flags/gfp_pfmemalloc_allowed (page_alloc.c:4562-4587), oom_reserves_allowed/tsk_is_oom_victim, the resulting privilege outcomes in one line each (the reserve-depth arithmetic and its percentages belong to alloc/watermark-check.md, seam __zone_watermark_ok); translation is the other seam (gfp_to_alloc_flags, one-paragraph recap; alloc/alloc-flags.md owns it) | [curated] |
| composite-recipes.md | every GFP_* recipe (gfp_types.h:376-389) with the caller-facing recipe↔context matrix (atomic/IRQ/BH vs process vs fs/io-constrained vs userspace vs THP — which GFP_* a caller must pass; the internal context↔ALLOC_* matrix belongs to alloc/alloc-flags.md): GFP_ATOMIC/NOWAIT/KERNEL(_ACCOUNT)/NOIO/NOFS/USER/HIGHUSER(_MOVABLE)/DMA(32)/TRANSHUGE(_LIGHT), vma_thp_gfp_mask worked example (huge_memory.c:1422-1446), NMI/RT caveats (gfp_types.h:312-317) | [curated] |
| gfp-allowed-mask.md | gfp_allowed_mask lifecycle: GFP_BOOT_MASK static init (page_alloc.c:238; internal.h:80) → full unlock in kernel_init_freeable (init/main.c:1663-1666), application sites (page/slab/memcg), hibernation pm_restrict/restore_gfp_mask + saved_gfp_count refcount + system_transition_mutex (kernel/power/main.c:36-65), pm_suspended_storage OOM gate | [curated] |
| memalloc-scopes.md | memalloc_flags_save/restore primitive + nesting contract (sched/mm.h:333-343), memalloc_noio/nofs/noreclaim/pin_save/restore (:357-472) with per-scope rules (noreclaim not from interrupt context), NOIO-stronger-than-NOFS ordering, memalloc_apply_gfp_scope/memalloc_restore_scope (vmalloc.c:3804-3825, v7.0-new), scope-over-GFP_NOFS doctrine (Documentation/core-api/gfp_mask-from-fs-io.rst), set_active_memcg analogue note | [curated] |
| pf-memalloc.md | PF_MEMALLOC/PF_KSWAPD/PF_MEMALLOC_NOFS/NOIO/PIN census (sched.h:1752-1785), current_gfp_context stripping rules + complete application-site census (sched/mm.h:249-267; 13 sites incl. page_alloc/vmscan/percpu/huge_memory/nfs), who sets PF_MEMALLOC (kswapd vmscan.c:7299/7349, softirq mask-out softirq.c:590-651, sunrpc/xfs direct setters), __GFP_MEMALLOC relation, might_alloc/PF_MEMALLOC interplay | [curated] |

### buddy/ (3 pages)

| page | scope (anchor symbols) | tag |
|---|---|---|
| free-area.md | struct free_area (mmzone.h:138-141), per-migratetype free_list + nr_free, the helper family __add_to_free_list/add_to_free_list/move_to_free_list/__del_page_from_free_list/del_page_from_free_list/get_page_from_free_area (page_alloc.c:832-916), account_freepages (:814-829) + NR_FREE_PAGES/NR_FREE_CMA_PAGES/nr_free_highatomic/NR_FREE_PAGES_BLOCKS accounting, free_area_empty, zone->lock domain, NR_PAGE_ORDERS/MAX_PAGE_ORDER | [prompt] |
| buddy-pfn.md | __find_buddy_pfn XOR math (internal.h:756-759), find_buddy_page_pfn (:775-788), page_is_buddy predicate (order + page_zone_id + PageBuddy; :717-736), buddy_order vs buddy_order_unsafe contracts (:685-702), caller-side zone-hole responsibility, worked bit examples | [prompt] |
| page-buddy-encoding.md | how a free page is marked: PGTY_buddy in the page_type top byte (page-flags.h:925-1003, PAGE_TYPE_OPS), mapcount overlay rule (page_type_has_type), set_buddy_order via page->private (page_alloc.c:752-756), the lru/buddy_list/pcp_list/pcp_llist union (mm_types.h:88-116), the _refcount==0 invariant on free pages | [curated] |

### pcp/ (4 pages)

| page | scope (anchor symbols) | tag |
|---|---|---|
| per-cpu-pages.md | struct per_cpu_pages field-by-field (mmzone.h:744-760), NR_PCP_LISTS math (on-disk verified: MIGRATE_PCPTYPES=3 → NR_LOWORDER_PCP_LISTS=12, +NR_PCP_THP=2 → 14), PCPF_PREV_FREE_HIGH_ORDER/PCPF_FREE_HIGH_BATCH (:729-742), order_to_pindex/pindex_to_order/pcp_allowed_order (page_alloc.c:684-726), pcp->lock as a real spinlock + pcp_spin_trylock discipline (:134-194, UP/RT variants), relation to per_cpu_zonestat | [prompt] |
| sizing.md | boot_pageset (BOOT_PAGESET_BATCH=1) → setup_per_cpu_pageset swap (page_alloc.c:6181), zone_pcp_init (:6209), zone_batchsize (:5922) / zone_highsize (:5970) formulas, pageset_update/__zone_set_pageset_high_and_batch (:6066-6110) under pcp_batch_high_lock (:94), percpu_pagelist_high_fraction sysctl + MIN_PERCPU_PAGELIST_HIGH_FRACTION, cache-topology tuning setup_pcp_cacheinfo/zone_pcp_update_cacheinfo (:6146-6175), zone_pcp_disable/enable/reset (:7387-7418) | [curated] |
| adaptive-tuning.md | the runtime auto-tuning state machine: high vs high_min/high_max, alloc_factor doubling/decay, free_count growth + batch<<CONFIG_PCP_BATCH_SCALE_MAX cap, nr_pcp_alloc (:3284-3332), nr_pcp_free/nr_pcp_high (:2779-2850), ZONE_BELOW_HIGH set/clear + ZONE_RECLAIM_ACTIVE throttle couplings, PCPF flag flips in free_frozen_page_commit (seam), kswapd_clear_hopeless coupling as mention | [curated] |
| drains-and-decay.md | decay_pcp_high (:2588-2620) + its vmstat-shepherd trigger (recap; zone/percpu-vmstat.md owns the work machinery), drain_zone_pages NUMA expire counter (:2628-2640), drain_pages_zone/drain_pages/drain_local_pages (:2646-2689), __drain_all_pages/drain_all_pages remote-drain design (no IPI; remote pcp->lock) + pcpu_drain_mutex (:2701-2777, :214), caller census (reclaim, isolation, offline, CMA), zone_pcp_disable coupling | [curated] |

### alloc/ (21 pages)

| page | scope (anchor symbols) | tag |
|---|---|---|
| entry-points.md | the public allocation API census and wrapper topology: alloc_pages(_node)/alloc_page/folio_alloc/__folio_alloc_node/__get_free_pages/get_zeroed_page/alloc_pages_exact (gfp.h:245-394; page_alloc.c:5291-5445), the alloc_hooks/_noprof macro layer (alloc_tag.h:262-266), __alloc_pages_noprof as set_page_refcounted wrapper over __alloc_frozen_pages_noprof (page_alloc.c:5279-5288), who-calls-what census | [curated] |
| frozen-pages.md | the _refcount==0 convention: alloc_frozen_pages(_noprof) (internal.h:895-917), set_page_refcounted/set_pages_refcounted (internal.h:578-583), free_frozen_pages symmetry, contig/CMA frozen variants, page_is_buddy refcount invariant, why the split exists (speculative refs, folio conversion), publish points census | [curated] |
| alloc-context.md | struct alloc_context field-by-field (internal.h:657-675) + prepare_alloc_pages walkthrough (page_alloc.c:4996-5042): gfp_zone/node_zonelist/nodemask + cpuset substitution rules (__GFP_HARDWALL, ALLOC_CPUSET, cpuset_current_mems_allowed), spread_dirty_pages=__GFP_WRITE, might_alloc, should_fail_alloc_page fault injection + ALLOC_TRYLOCK exemption, first_zones_zonelist preferred_zoneref | [prompt] |
| alloc-flags.md | ALLOC_* census with values (internal.h:1346-1385) and the full translation chain: gfp_to_alloc_flags (page_alloc.c:4495-4545, incl. BUILD_BUG_ON bit-identity tricks + RT-task MIN_RESERVE), gfp_to_alloc_flags_cma (:3792-3801), alloc_flags_nofragment (:3755-3790), __gfp_pfmemalloc_flags (:4562-4587), ALLOC_RESERVES group; the internal matrix: which context (atomic, FS, OOM victim, RT, NMI/trylock) ends up with which ALLOC_* combination (the caller-facing GFP-recipe matrix belongs to gfp/composite-recipes.md) | [prompt] |
| pipeline.md | __alloc_frozen_pages_noprof top-level walkthrough (page_alloc.c:5214-5276): order guard, gfp_allowed_mask, current_gfp_context, prepare_alloc_pages, alloc_flags_nofragment OR-in, single WMARK_LOW get_page_from_freelist attempt, out: epilogue (memcg charge, kmsan, tracepoint), slowpath handoff boundary (:5262) + nodemask/spread_dirty_pages restore | [prompt] |
| get-page-from-freelist.md | the zonelist scan (:3808+): for_each_zone_zonelist_nodemask resume semantics, cpuset_zone_allowed, dirty-limit spreading last_pgdat_dirty_ok, ZONE_BELOW_HIGH cached shortcut (:3893-3899), watermark check + failure paths: node_reclaim/zone_allows_reclaim NUMA hook, deferred-grow (_deferred_grow_zone) + cond_accept_memory (:3925-3944), try_this_zone→rmqueue, no_fallback/ALLOC_NOFRAGMENT retry-without dance, the reserve_highatomic_pageblock call site (:3969, one line — reserve mechanics belong to migratetype/highatomic.md), NUMA_HIT/zone_statistics | [prompt] |
| watermark-check.md | the admission arithmetic: zone_watermark_fast (order-0 shortcut + lowmem_reserve skip logic), __zone_watermark_ok (page_alloc.c:3602-3726): reserve ladder per ALLOC_* (MIN_RESERVE/NON_BLOCK/OOM math on `min`), lowmem_reserve[highest_zoneidx] addition, __zone_watermark_unusable_free (CMA/HIGHATOMIC/isolated subtraction), high-order per-order per-migratetype free_area scan + ALLOC_CMA/ALLOC_HIGHATOMIC acceptance, NR_FREE_PAGES drift + zone_page_state_snapshot recheck, boost effect on the LOW mark | [prompt] |
| rmqueue.md | rmqueue dispatch (:3410+ incl. ZONE_BOOSTED_WATERMARK lazy kswapd wake ~:3430), rmqueue_buddy loop (:3239-3282: zone->lock irqsave vs ALLOC_TRYLOCK trylock, check_new_pages retry, HIGHATOMIC fallback order), __rmqueue dispatch + enum rmqueue_mode state machine (:2466-2540) + CMA-first heuristic, __rmqueue_smallest order scan handing off at page_del_and_expand (:1760, named in one line — the split interior belongs to expand-split.md), per-step page state transitions (PageBuddy clear, private clear, accounting) | [prompt] |
| rmqueue-pcplist.md | rmqueue_pcplist/__rmqueue_pcplist: pcp_spin_trylock + NULL fallback to buddy, order_to_pindex recap, rmqueue_bulk refill under one zone->lock session (:2547-2582) with rmqueue_mode persistence, nr_pcp_alloc batch/high adaptation (seam to pcp/adaptive-tuning), alloc_factor doubling, list_first_entry consumption | [prompt] |
| fallback-claim-steal.md | the migratetype fallback machinery ("stealing"; the prompt's "sealing" bullet is read as this logic): fallbacks[] order (:1951-1955), find_suitable_fallback (:2283), should_try_claim_block criteria (:2235-2256), try_to_claim_block whole-block conversion (:2312-2385: free+alike counting, ≥50% threshold, set_pageblock_migratetype, boost_watermark trigger), __rmqueue_claim (:2387) vs __rmqueue_steal single-page (:2442), rmqueue_mode memory across rmqueue_bulk iterations, state transitions of block ownership | [prompt] |
| defrag.md | anti-fragmentation policy: ALLOC_NOFRAGMENT + alloc_flags_nofragment DMA32 condition (:3755-3790), defrag_mode sysctl (:306, :6769-6777) — unconditional NOFRAGMENT (gfp_to_alloc_flags :4536), kswapd woken at pageblock_order (wake_all_kswapds :4479-4482), slowpath NOFRAGMENT drop point, no_fallback retry in get_page_from_freelist, page_group_by_mobility_disabled, claim-threshold philosophy tie-in | [prompt] |
| expand-split.md | splitting large buddies at allocation — this page owns the walkthrough the prompt demands: expand() interior (:1732) + page_del_and_expand (:1760) mechanics (halving loop, set_buddy_order, tail placement into free lists, __add_to_free_list accounting), guard-page interaction if configured, worked order-N→order-M example, NR_FREE accounting per step | [prompt] |
| prep-new-page.md | new-page preparation: check_new_pages/check_new_page bad-page screen, post_alloc_hook step-by-step (arch_alloc_page, kernel_init_pages/want_init_on_alloc, kasan relevance on x86-64, kmsan, set_page_owner, page_table_check_alloc, pgalloc_tag), prep_new_page + prep_compound_page for __GFP_COMP, pfmemalloc marking, refcount publish seam (frozen-pages page owns the convention) | [prompt] |
| slowpath.md | the __alloc_pages_slowpath retry state machine (:4710-4994; full set per decision 1): gfp_to_alloc_flags re-derivation + preferred_zoneref re-derivation, wake_all_kswapds at each retry (:4470-4493), can_direct_reclaim/costly_order branching (compaction-first for costly/non-movable), reserve/cpuset relaxation step, alloc_flags evolution across the loop, defrag_mode NOFRAGMENT drop point, the retry cookies (cpuset_mems_cookie + zonelist_iter_begin/check_retry_zonelist :4393-4407), the nofail loop, nopage:/fail: exits + warn_alloc | [curated; decision 1] |
| retry-gates.md | the retry predicates: should_reclaim_retry (:4600: no-progress accounting, MAX_RECLAIM_RETRIES=16, per-zone rescue test against min watermark + reclaimable estimate, memalloc_retry_wait) and should_compact_retry (:4224: MAX_COMPACT_RETRIES=16, compact_result classification, costly-order __GFP_RETRY_MAYFAIL rules, priority escalation) | [curated; decision 1] |
| direct-reclaim.md | the direct-reclaim attempt wrapper: __alloc_pages_direct_reclaim (:4437) + __perform_reclaim glue (PF_MEMALLOC via memalloc_noreclaim scope, fs_reclaim bracketing, cpuset cookie), drain_all_pages + unreserve_highatomic_pageblock on no-progress, oneshot drained retry; try_to_free_pages interior out of scope (reclaim turf) | [curated; decision 1] |
| direct-compaction.md | the direct-compaction attempt wrapper: __alloc_pages_direct_compact (:4165-4221: psi/delay accounting, prio, capture consumption via current->capture_control — seam to compaction-capture.md, prep_new_page on captured page, COMPACT_* result handling), compaction_deferred interplay at census level; try_to_compact_pages interior out of scope (compaction turf) | [curated; decision 1] |
| oom-entry.md | the allocator's OOM entry: __alloc_pages_may_oom (:4070-4154: oom_lock trylock, last get_page_from_freelist at ALLOC_WMARK_HIGH, the no-OOM exclusions — costly order, non-sleepable, __GFP_RETRY_MAYFAIL/NORETRY, pm_suspended_storage), out_of_memory call boundary + ALLOC_OOM victim retry, __GFP_NOFAIL interaction; oom_kill.c victim selection out of scope | [curated; decision 1] |
| alloc-nolock.md | any-context allocation: alloc_pages_nolock(_noprof)/alloc_frozen_pages_nolock_noprof (:7759-7856), forced gfp set, ALLOC_TRYLOCK contract end-to-end (prepare exemption, rmqueue trylocks, no slowpath), gfpflags_allow_spinning gate, PREEMPT_RT NMI/hardirq bail, free_pages_nolock seam, cond_accept_memory bail, BPF/tracing consumers | [curated] |
| bulk-alloc.md | alloc_pages_bulk_noprof (:5065-5208) + alloc_pages_bulk(_node/_mempolicy) wrappers: single-zone watermark choice, one pcp_spin_trylock session loop, per-page prep+refcount inline, fallback-to-single conditions (memcg/page_owner/n==1), caller census | [curated] |
| compaction-capture.md | the direct-compaction capture handshake: struct capture_control (internal.h:994-997), task_capc/compaction_capture acceptance rules (page_alloc.c:759-812), consumption inside __free_one_page (:978+), prep at __alloc_pages_direct_compact (:4165-4221), why captured pages skip the freelists | [curated] |

### free/ (10 pages)

| page | scope (anchor symbols) | tag |
|---|---|---|
| entry-points.md | the freeing API census and refcount semantics: ___free_pages/__free_pages/free_pages + __free_page/free_page (gfp.h:389-394; page_alloc.c:5322-5391), put_page/folio_put(_refs)/folios_put(_refs) last-ref detection (mm.h:1814-1879; swap.c:951-1044), __folio_put routing (swap.c:97-114), release_pages, free_frozen_pages (internal-only), free_pages_exact (gfp.h:377; page_alloc.c:5481, the alloc_pages_exact counterpart), free_contig(_frozen)_range, __free_pages_core boot/hotplug entry (:1618-1664), free_pages_nolock, order>0 non-compound behavior; NAMING NOTE: the prompt's "free_unref_folio" maps at v7.0 to free_unref_folios (batch) + free_frozen_pages (single) after the free_unref_page* renames | [curated] |
| free-pages-prepare.md | free_pages_prepare/__free_pages_prepare checklist (:1342-1479): PageHWPoison short-circuit, bad-page screen (PAGE_FLAGS_CHECK_AT_FREE/free_page_is_bad), free_tail_page_prepare (:1129-1219), page_cpupid reset, init_on_free zeroing, kasan/kmsan poison, page_table_check_free, arch_free_page, reset_page_owner, pgalloc_tag; mirror-image relationship to post_alloc_hook | [curated] |
| free-frozen-pages.md | the single-page PCP free: free_frozen_pages/__free_frozen_pages (:2964-3022), pcp_allowed_order gate (non-eligible orders route via __free_pages_ok :2974 — free-one-page.md owns that layer), migratetype re-read + isolated bypass, pcp_spin_trylock failure → free_one_page, PREEMPT_RT/NMI llist deferral, free_frozen_page_commit (:2859-2959): high computation, PCPF flag flips, free_count/alloc_factor updates, free_pcppages_bulk trigger, ZONE_BELOW_HIGH clear + kswapd_clear_hopeless fire | [prompt] |
| free-unref-folios.md | the batch free: free_unref_folios (:3027-3118) over folio_batch, feeders folios_put_refs/release_pages (swap.c:951-1044) and reclaim lists, per-folio pcp eligibility (order, hugetlb exclusion), zone/pcp lock switching across a heterogeneous batch, isolated handling, relation to lru_add_drain caller patterns at census level | [prompt] |
| fpi-flags.md | fpi_t census (:63-91): FPI_NONE, FPI_SKIP_REPORT_NOTIFY (+ where reporting is skipped and why), FPI_TO_TAIL (+ every user), FPI_TRYLOCK (deferred-free contract), flag composition at each free_one_page/__free_one_page call site | [prompt] |
| page-reporting.md | free-page reporting async chain: page_reporting_notify_free from __free_one_page (page_reporting.h:33-45), __page_reporting_request + PAGE_REPORTING_DELAY work scheduling, page_reporting_process zone walk under zone->lock using the __isolate_free_page/__putback_isolated_page take-off/put-back primitives (internal.h:811-812; page_alloc.c:3150-3210), PAGE_REPORTING_CAPACITY scatterlist, IDLE/REQUESTED/ACTIVE state machine, page_reporting_register/unregister; virtio-balloon driver side out of scope | [curated] |
| free-one-page.md | the non-PCP buddy-free layer: __free_pages_ok prep+dispatch (:1608, reached from __free_frozen_pages non-pcp orders, __free_pages_core, make_alloc_exact tail, unaccepted memory), free_one_page locking wrapper (:1572-1606): spin_trylock_irqsave under FPI_TRYLOCK → add_page_to_zone_llist deferral (:1563-1570) → flush of zone->trylock_free_pages on next ordinary free, split_large_buddy for pageblock-crossing frees (:1540-1561), isolated-pageblock forcing, zone/node immutability recap (page_zone from flags) | [prompt] |
| buddy-merge.md | __free_one_page interior (:978-1064): the merge loop (find_buddy_page_pfn → page_is_buddy → del buddy → order climb), stop conditions (MAX_PAGE_ORDER, migratetype/isolation rules at ≥pageblock_order), compaction_capture check, to-tail decision (buddy_merge_likely :926-941, shuffle_pick_tail if configured, FPI_TO_TAIL), page_reporting_notify_free exit hook, accounting per step | [prompt] |
| free-pcppages-bulk.md | free_pcppages_bulk (:1486-1537): count/pindex round-robin across pcp lists, batch scaling, per-page free_one_page handoff under one zone->lock session, callers (free_frozen_page_commit high trigger, drains, decay) | [curated] |
| placement-decision.md | the synthesis the prompt demands ("which zone/migrate type/node, in batch or in single pages"): zone+node immutable from page->flags (set_page_links seam), migratetype re-read at free time (get_pfnblock_migratetype) + isolation override + highatomic/CMA accounting consequences, pcp-vs-direct-buddy decision tree (order eligibility, trylock outcomes, context, FPI flags), batch (free_pcppages_bulk/free_unref_folios) vs single-page paths; decision-tree figure | [prompt] |

### Fold-in adjudications (suggested or surfaced topics that do NOT get pages)

- HVO + ZONE_DEVICE compound vmemmap dedup (agent A) → physmem/vmemmap-optimizations.md (one page for both optimization families).
- memdesc_flags_t unification (agents A/E) → physmem/page-flags-layout.md.
- Memory-hotplug section add/remove (agent A) → physmem/section-lifecycle.md; the wider hotplug flow (online_pages/offline_pages) stays out of campaign scope, mentions only.
- KHO scratch memory (agent A) → one section inside physmem/memmap-init.md.
- SPARSEMEM_EXTREME two-level indexing (agent A) → physmem/sections.md.
- CMA pageblock boot init (agent A) → migratetype/cma.md.
- Deferred init & padata (agents A/B) → physmem/deferred-init.md.
- PCP allocator internals (agent B) → the pcp/ group.
- Zonelist ordering & node distance (agent B) → zone/zonelist.md (+ zone/numa-memblks.md for the distance table).
- NUMA memblks (agent B) → zone/numa-memblks.md.
- Watermark boosting (agent B) → zone/watermarks.md (lifecycle) + alloc/fallback-claim-steal.md (trigger); balance_pgdat decay is reclaim turf, mention only.
- kswapd hopeless-node machinery (agents B/E) → mentions in pcp/adaptive-tuning.md and zone/watermarks.md; owned by the reclaim area, no page.
- Memory tiering/WMARK_PROMO machinery (agent B) → zone/watermarks.md notes the mark + accessor; memtier out of scope.
- NMI/BPF-safe allocation (agents C/D) → alloc/alloc-nolock.md (page granted; free side split across free/free-one-page.md + free/entry-points.md).
- Watermark sysctl tuning (agent C) → zone/watermarks.md.
- cpuset/GFP interaction (agent C) → alloc/alloc-context.md section + gfp/flag-census.md entries; cpuset subsystem out of scope.
- kmemcg accounting (agent C) → gfp/flag-census.md (__GFP_ACCOUNT) + alloc/pipeline.md (charge point); memcg machinery out of scope.
- OOM reserve interplay (agent C) → gfp/watermark-modifiers.md + alloc/alloc-flags.md (ALLOC_OOM) + alloc/oom-entry.md; oom_kill.c victim selection out of scope.
- THP allocation policy (agent C) → gfp/composite-recipes.md worked example.
- CMA/ALLOC_CMA path (agent C) → migratetype/cma.md.
- PM/hibernation GFP restriction (agent C) → gfp/gfp-allowed-mask.md.
- PCP sizing/adaptation (agent D) → pcp/sizing.md + pcp/adaptive-tuning.md.
- Watermark/reserve arithmetic (agent D) → alloc/watermark-check.md.
- Fragmentation-avoidance knobs (agent D) → alloc/defrag.md.
- Compaction-capture handshake (agents D/E) → alloc/compaction-capture.md (page granted; consumed in free/buddy-merge.md as a check).
- Free-page reporting (agent E) → free/page-reporting.md (page granted).
- PCP cacheinfo tuning (agent E) → pcp/sizing.md.
- Unaccepted memory (agent E) → bounded sections in alloc/get-page-from-freelist.md and physmem/memmap-init.md (__free_pages_core note); CoCo guest machinery out of scope, no page.
- alloc_contig/CMA isolation internals (agent E) → migratetype/isolate.md + migratetype/alloc-contig.md.
- Frozen-pages theme (agent E) → alloc/frozen-pages.md (page granted).
- pgalloc_tag / allocation profiling hooks (agent E) → mentions in alloc/prep-new-page.md + free/free-pages-prepare.md + the alloc_hooks layer in alloc/entry-points.md; profiling subsystem out of scope.
- zone->trylock_free_pages deferred-free llist (agent E) → free/free-one-page.md + alloc/alloc-nolock.md.
- PB_compact_skip bit → named in physmem/pageblock.md; compaction semantics out of scope.
- MIGRATE_PCPTYPES sentinel → migratetype/overview.md + pcp/per-cpu-pages.md; not a type, no page.

### Projected total and tag census

82 pages, final (post-review, post-checkpoint): 12 physmem + 15 zone + 9 migratetype + 8 gfp + 3 buddy + 4 pcp + 21 alloc + 10 free. Tag census: 41 [prompt] (physmem 7, zone 8, migratetype 6, buddy 2, pcp 1, alloc 11, free 6), 41 [curated]. The gfp/ group's 8 curated rows jointly realize the two prompt headings explicitly delegated to curation ("GFP flags", "Memalloc flags"); the six migratetype per-type rows realize "one page for each of the migrate type" with the type set fixed by the on-disk enum; isolate-freepage-move.md is the plan review's split of isolate.md; the five slowpath rows and the two ZONE_DEVICE rows are user-directed (scope decisions 1-2).

### Overlap boundary rules (seam symbols named)

Self-contained pages overlap by design; these statements fix each page's mission so siblings recap in at most one short paragraph instead of duplicating walkthroughs.

1. zone/watermarks.md owns the marks at rest (fields, accessors, setup chain, boost lifecycle); alloc/watermark-check.md owns the admission arithmetic per allocation attempt. Seam: the `zone->_watermark[]` accessors (`wmark_pages`); the boost trigger itself belongs to alloc/fallback-claim-steal.md (`boost_watermark` called from `try_to_claim_block`).
2. gfp/watermark-modifiers.md owns the caller-facing reserve-privilege model of __GFP_HIGH/__GFP_MEMALLOC/__GFP_NOMEMALLOC; alloc/alloc-flags.md owns the ALLOC_* bit census and the translation chain. Seam: `gfp_to_alloc_flags` (recapped one paragraph on the gfp side, opened on the alloc side).
3. PCP cluster: pcp/per-cpu-pages.md owns the structure; pcp/sizing.md owns capacity policy at rest; pcp/adaptive-tuning.md owns the runtime high/batch calculus; pcp/drains-and-decay.md owns emptying machinery; alloc/rmqueue-pcplist.md owns the dequeue path; free/free-frozen-pages.md owns the enqueue path; free/free-pcppages-bulk.md owns the flush. Seams: `nr_pcp_alloc` (tuning↔dequeue), `nr_pcp_high` (tuning↔enqueue), `free_pcppages_bulk` (enqueue/drains↔flush).
4. physmem/pageblock.md owns pageblock-flag storage and the accessor contracts; migratetype/overview.md owns migratetype semantics and the type-flip primitive (`__move_freepages_block`). Seam: `get_pfnblock_migratetype`/`set_pageblock_migratetype`.
5. Fallback cluster: alloc/rmqueue.md owns the dispatch machine (`__rmqueue`, rmqueue_mode); alloc/fallback-claim-steal.md owns block conversion (claim/steal); alloc/defrag.md owns the policy knobs; migratetype/highatomic.md and migratetype/overview.md own type lifecycles. Seams: `__rmqueue` (dispatch→conversion), `try_to_claim_block` (conversion→policy/boost).
6. Free cluster: free/free-one-page.md owns the non-PCP layer (`__free_pages_ok` prep+dispatch, `free_one_page` locking wrapper, trylock llist, split_large_buddy, isolation forcing); free/buddy-merge.md owns the __free_one_page interior; free/placement-decision.md is the synthesis page and opens nothing new. Seam: `__free_one_page`.
7. Isolation cluster: migratetype/isolate.md owns the isolation state machine and API; migratetype/isolate-freepage-move.md owns the free-page movement across an isolation flip (straddling buddies, take-off/put-back primitives); migratetype/alloc-contig.md owns the contiguous-allocation pipeline that drives both; migratetype/cma.md owns the CMA area lifecycle above alloc_contig. Seams: `start_isolate_page_range` (contig→isolate), `pageblock_isolate_and_move_free_pages` (isolate→freepage-move), `alloc_contig_frozen_range` (cma→contig).
8. Boot cluster: physmem/memmap-init.md owns per-page init and the memblock→buddy handoff; physmem/deferred-init.md owns the deferred half; zone/free-area-init.md owns node/zone construction and boot ordering; physmem/section-lifecycle.md owns section population. Seams: `memmap_init` (free-area-init→memmap-init), `sparse_init` (free-area-init→section-lifecycle), `deferred_init_memmap` (memmap-init→deferred-init).
9. Entry censuses: alloc/entry-points.md owns the wrapper topology and stops at `__alloc_frozen_pages_noprof`, which alloc/pipeline.md opens; free/entry-points.md owns refcount-drop routing and stops at `free_frozen_pages`/`free_unref_folios`, which free/free-frozen-pages.md and free/free-unref-folios.md open.
10. vmstat: zone/percpu-vmstat.md owns the counter fold and shepherd work machinery; pcp/drains-and-decay.md and alloc/watermark-check.md consume it (decay trigger, snapshot recheck) with one-paragraph recaps. Seam: `refresh_cpu_vm_stats`.
11. Slowpath entry: alloc/pipeline.md stops at the `__alloc_pages_slowpath` call, which alloc/slowpath.md opens (see rule 20 for the cluster's interior boundaries).
12. zone/zone.md owns the struct-at-rest tour; zone/watermarks.md, zone/lowmem-reserves.md, and the pcp/ group own their fields' mechanisms; zone/zone.md points at them without opening them.
13. alloc/frozen-pages.md owns the refcount convention and its invariants; every entry-point page states per-API refcount behavior in one line and defers the model to it.
14. buddy/ pages are structure-at-rest: buddy/free-area.md (lists+accounting), buddy/buddy-pfn.md (math), buddy/page-buddy-encoding.md (descriptor marking); the paths that mutate them (alloc/rmqueue.md, alloc/expand-split.md, free/buddy-merge.md) recap structure in one paragraph. Seam: `__add_to_free_list`/`__del_page_from_free_list`.
15. House rule: every alloc/ and free/ path page recaps the entry chain (public entry → frozen core) in at most one short paragraph; the two entry-points pages own the full census.
16. (Plan review am. 1) alloc/rmqueue.md names `page_del_and_expand` in one line and stops; alloc/expand-split.md owns the split interior. Seam: `page_del_and_expand`.
17. (Plan review am. 2) gfp/composite-recipes.md owns the caller-facing GFP-recipe↔context matrix; alloc/alloc-flags.md owns the internal context↔ALLOC_* matrix. Seam: `gfp_to_alloc_flags` (shared with rule 2; the two matrices never repeat each other's rows).
18. (Plan review am. 3) alloc/get-page-from-freelist.md states the `reserve_highatomic_pageblock` call site in one line; migratetype/highatomic.md owns cap, accounting, and unreserve. Seam: `reserve_highatomic_pageblock`.
19. (Plan review am. 4) alloc/watermark-check.md owns the reserve-depth arithmetic and percentages; gfp/watermark-modifiers.md states each modifier's outcome in one line. Seam: `__zone_watermark_ok`.
20. (Scope decision 1) Slowpath cluster: alloc/slowpath.md owns the retry loop and its evolving state (alloc_flags, cookies, nofail); alloc/retry-gates.md owns the two gate predicates; alloc/direct-reclaim.md and alloc/direct-compaction.md own the attempt wrappers; alloc/oom-entry.md owns __alloc_pages_may_oom. The vmscan, compaction, and oom_kill interiors stay out of campaign scope on every page. Seams: `__alloc_pages_slowpath` (pipeline→slowpath), `should_reclaim_retry`/`should_compact_retry` (slowpath→gates), `__alloc_pages_direct_reclaim`/`__alloc_pages_direct_compact` (slowpath→attempts), `__alloc_pages_may_oom` (slowpath→oom-entry); direct-compaction consumes capture via rule seam `compaction_capture` (alloc/compaction-capture.md owns the mechanism).
21. (Scope decision 2) zone/zone-device.md owns the zone semantics, section taint, and memmap_init_zone_device; zone/dev-pagemap.md owns the dev_pagemap object, ops callbacks, and memremap/memunmap lifecycle; physmem/vmemmap.md keeps altmap mechanics. Seams: `memmap_init_zone_device` (dev-pagemap→zone-device), `struct vmem_altmap` (dev-pagemap→vmemmap).

### Adversarial review outcome (2026-07-12)

Adversarial plan review (fresh strong-model agent) returned 14 amendments; orchestrator adjudication: ACCEPTED 1-5, 7-12 (four ownership rescopes with new seams: page_del_and_expand, the two context matrices, reserve_highatomic_pageblock, __zone_watermark_ok; split of migratetype/isolate.md into isolate.md + isolate-freepage-move.md; two batch reorders: buddy/ before migratetype/overview, highatomic+cma before the alloc batches; four coverage fold-ins: __free_pages_ok, free_pages_exact, __isolate_free_page/__putback_isolated_page, enum meminit_context). REJECTED 6 (splitting get-page-from-freelist's failure-recovery tail: it is control flow of a single function; the hooks are already bounded one-liners, and splitting one function's walkthrough across pages costs self-containment more than length saves). RECORDED 13 (no thin rows warrant merging — granularity review complete both directions) and 14 (pcp/drains → free_pcppages_bulk forward reference stays a one-paragraph recap under boundary rule 3). Reviewer's anchor ledger: 60+ symbols verified present on disk across all eight groups; all digest-flagged retired names (free_unref_page*, steal_suitable_fallback, __rmqueue_fallback, can_steal_fallback, try_alloc_pages, ALLOC_HARDER/HIGH, __GFP_ATOMIC) confirmed ABSENT. The catalog was updated in place; post-review baseline 76 pages (the checkpoint decisions then took it to 82).

## Execution & verification

### Per-page procedure (skill-mandated)

1. Before the first batch: writers read `guidelines/reference/TEMPLATE-FULL.md` for section order and calibrate depth/structure against the closest `guidelines/reference/samples/page-*.md` archetype (samples are style/structure/depth guidance only, never facts).
2. Research with semcode (find_function/find_type/find_callers/find_callchain/grep_functions) plus Grep/Read; every cited line number and every reproduced code block is confirmed against the on-disk v7.0 file before it lands in a page. Dossier per page at `progress/numa/<slug>.dossier.md` (`guidelines/passes/dossier.md`), kept current as research proceeds.
3. Pages land at `${SKILL_DIR}/docs/mm/<group>/<slug>.md`. mm's section-6 heading is "none" → pages carry exactly: H1, caution blockquote, lead summary (+diagram where earned), SUMMARY, SPECIFICATIONS (empty body allowed), LINUX KERNEL, KERNEL DOCUMENTATION, OTHER SOURCES, DETAILS.
4. Elixir links: every symbol mention outside fenced blocks links to `https://elixir.bootlin.com/linux/v7.0/source/<path>#L<line>`; struct/enum keyword kept.

### Project-specific writing rules (from prompt.md, on top of skill gates)

- x86-64 focus, but "x86-64" is named only where the detail is arch-specific; no other-arch code paths.
- No driver-example hunt for core-mm mechanisms; call-site censuses still required ("point out all the places ... cite as many and as complete as possible").
- Extra attention mandated: object lifecycle (allocation/freeing/locking/refcount), all state transitions, asynchronous behaviors (notifications, deferred work, lazy processing, dirty-and-process-later), synchronization/race avoidance, and complete callback semantics for any ops structure encountered.
- No page-length ceiling; depth over brevity ("Do as detailed as you can").
- Coverage obligation: every generic mm structure in the areas' mm/ files and the headers they include is either covered by a page or adjudicated into a fold-in.

### Gate ownership (pipeline)

Per SKILL.md ("Modes") and the pass files under `guidelines/passes/`. the five waivers files under `guidelines/rules/` (one `<PREFIX>-WAIVERS.md` per rule directory) are every agent's mandatory first read; rule IDs resolve via `guidelines/rules/INDEX.md`.

- Writer (strongest available model; brief in `guidelines/passes/02-write.md`): owns the page end to end, facts AND prose. It researches with semcode plus Grep/Read, keeps the page dossier current, writes under every rule, and runs the mechanical exit suite before reporting: excerpts byte-compared, anchors printed and confirmed (persisted as the dossier's machine-emitted LINKS table), the PARITY table closed (fill-or-decatalog), every count re-derived on a differently-shaped second basis, span closure against LINKS, and the Gate A prose and figure sweeps (3c) with every candidate adjudicated against the waivers into the dossier's LINT section. It fixes what the suite finds and re-runs the suite over what it touched. Page state: WRITTEN.
- Orchestrator check, per page (`guidelines/passes/03-check.md`; never delegated): re-runs the writer's procedures against ground truth and compares the answers — Gate A reproduction, the figure sweep, span-closure re-derivation with the same extractor, excerpt and anchor spot-checks, figure geometry, counts on a third basis. The orchestrator adjudicates every residual finding itself against the waivers; an exactly-specified fix is applied directly, volume goes to a fixer in fix-list mode (`guidelines/passes/03-lint-fixlist.md` — it applies an adjudicated list exactly, sweeps nothing, decides nothing), and factual findings return to the writer while its transcript lives. Page state: LINTED.
- Certification: a separate verify campaign (`numa-verify`, planned and run per `guidelines/passes/04-verify.md`) stamps CERTIFIED at zero unadjudicated findings and mirrors the stamp into this file's Status.
- Batches of ~5 pages, one writer per page, hard checkpoint between batches; fixers may trail into the following batch. A dead writer is resumed ("do not redo the research; write the page now from what you have"); a fresh writer starts from the dossier plus this file only after two failed resumes.

### Write-time cautions

- Every line number in this plan (digests included) is a hint; re-verify on disk at write time. Known drift examples found so far: agent B's NR_LOWORDER_PCP_LISTS=16/NR_PCP_LISTS=18 were wrong (on-disk: 12/14, orchestrator-verified against mmzone.h's enum migratetype at :64-90 and the list math at :721-728); the rmqueue boost-wake block is at ~page_alloc.c:3430 (function starts :3410), not the digest's :3427-3432; struct per_cpu_pages spans mmzone.h:744-760 (agent D's "758ish" was low).
- The reviewer's anchor ledger (see "Adversarial review outcome" under Page catalog) carries verified locations for 60+ symbols — still hints, but the freshest ones.
- Retired names must never appear as live symbols in pages: free_unref_page(_list/_commit), steal_suitable_fallback, __rmqueue_fallback, can_steal_fallback, try_alloc_pages, ALLOC_HARDER, ALLOC_HIGH, __GFP_ATOMIC, page_to_section (each may appear only in explicitly-historical rename notes).
- x86-64 CONFIG baseline per page where relevant: SPARSEMEM_VMEMMAP(+EXTREME), ZONE_DMA+ZONE_DMA32, TRANSPARENT_HUGEPAGE (NR_PCP_LISTS=14), CMA, MEMORY_ISOLATION, DEFERRED_STRUCT_PAGE_INIT, NUMA; KASAN_HW_TAGS never (arm64-only), HIGHMEM never.

### Batch order (foundational → derived, ~5 pages per batch, one writer per page, hard checkpoint between batches; revised per plan-review amendments 7-8)

Ordering rationale: encodings and structures before the paths that mutate them; physmem first (every later page uses page->flags accessors and PFN math), zones second (the structures the allocator scans), buddy structures before migratetype/overview (its type-flip primitive mutates free_area — review am. 7), flag vocabulary next, pcp structures plus the highatomic/cma lifecycles before the allocation path that triggers them (review am. 8), allocation path before freeing path (the free pages reference rmqueue/claim machinery), isolation cluster last (it consumes both paths, incl. split_large_buddy from B15).

- B1: physmem/memory-models, sections, pfn, pfn-section-conversion, page-flags-layout
- B2: physmem/pfn-page-conversion, vmemmap, vmemmap-optimizations, section-lifecycle, pageblock
- B3: zone/pglist-data, zone, node-states, numa-memblks, zonelist
- B4: zone/watermarks, lowmem-reserves, percpu-vmstat, free-area-init; physmem/memmap-init
- B5: physmem/deferred-init; zone/zone-dma, zone-dma32, zone-normal, zone-movable
- B6: zone/zone-device, dev-pagemap; buddy/free-area, buddy-pfn, page-buddy-encoding
- B7: gfp/flag-census, zone-selection, reclaim-policy, watermark-modifiers, composite-recipes
- B8: gfp/gfp-allowed-mask, memalloc-scopes, pf-memalloc; migratetype/overview, unmovable
- B9: migratetype/movable, reclaimable; pcp/per-cpu-pages, sizing, adaptive-tuning
- B10: pcp/drains-and-decay; migratetype/highatomic, cma; alloc/entry-points, frozen-pages
- B11: alloc/alloc-context, alloc-flags, pipeline, watermark-check, get-page-from-freelist
- B12: alloc/rmqueue, rmqueue-pcplist, fallback-claim-steal, defrag, expand-split
- B13: alloc/prep-new-page, bulk-alloc, alloc-nolock, compaction-capture
- B14: alloc/slowpath, retry-gates, direct-reclaim, direct-compaction, oom-entry
- B15: free/entry-points, free-pages-prepare, free-frozen-pages, free-unref-folios, fpi-flags
- B16: free/free-pcppages-bulk, free-one-page, buddy-merge, placement-decision, page-reporting
- B17: migratetype/isolate, isolate-freepage-move, alloc-contig

(16 batches of 5 plus B13 of 4 and B17 of 3 = 82.) Additional ordering constraints honored: dev-pagemap after vmemmap/altmap (B2) and the zone basics; compaction-capture (B13) before direct-compaction (B14), which consumes it; the slowpath batch (B14) after watermark-check/gpff (B11) and the drain machinery (B10) it references.

Superseded orders, kept for reference: (a) the pre-review order — migratetype/overview+per-type in B6 before buddy/*, gfp split across B6-B8, highatomic/cma in the final batch; superseded because migratetype/overview preceded buddy/free-area (review am. 7) and highatomic/cma trailed the alloc path that defers to them (am. 8). (b) The post-review order of 16 batches with alloc/slowpath-overview in B13 and zone-device provisional in B5; superseded by checkpoint decisions 1-2 (full slowpath set → new B14; zone-device+dev-pagemap → B6).

### User amendments (dated; supersede whatever they name)

1. [2026-07-12, checkpoint] Slowpath coverage expanded from one overview page to the five-page set (scope decision 1) — supersedes the catalog's alloc/slowpath-overview.md row and the post-review batch order.
2. [2026-07-12, checkpoint] ZONE_DEVICE covered as two pages including the dev_pagemap machinery (scope decision 2, user's own wording "Add this, but also details its machinery") — supersedes the provisional bounded-page row.
3. [2026-07-12, checkpoint] Generation is HELD after catalog approval (scope decision 5): batches start only on a further explicit user go.

### Save and commit policy

Pages land only under `${SKILL_DIR}/docs/mm/`. No SUMMARY.md or mkdocs.yml edits. No git commits without an explicit user go. Existing `docs/mm/vma/` pages and all prior `progress/` runs stay untouched.

## Draft reuse map

None. The request names no prior draft corpus and directs no reuse; every page is written fresh from the v7.0 tree. (The existing `docs/mm/vma/` pages belong to an earlier campaign: not mined, not modified, not evidence.)
