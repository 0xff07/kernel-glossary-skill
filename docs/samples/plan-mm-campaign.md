# mm knowledge-base: curated page catalog and directory plan

## Context

`prompt.md` at the repo root requests an in-depth, fine-grained documentation set on Linux kernel memory management (x86-64 only) for the kernel-glossary skill, output under `docs/mm/` of the skill checkout (`${CLAUDE_SKILL_DIR}/docs/mm/`). Its TOPIC LIST names four areas — mm_struct, vm_area_struct, User Space Page Faults, Reverse mapping — but the bullet lists under those headings are incomplete (one bullet is literally blank), and the prompt itself says "This topic list is very rough. Curate new pages where you see fit."

The user asked for a planning pass first: fill the gaps by curating pages for topics that belong to the four areas but are not yet in the bullets, mark which pages are prompt-listed vs newly curated, and propose a better file/directory organization. The stale prior-generation draft corpus and an older devel checkout beside the tree are explicitly NOT inputs; curation is grounded in the v7.0 kernel source itself (semcode index at HEAD 028ef9c9).

## Status

Living, dated checklist. An entry is appended the moment a phase completes, a batch lands, a user amendment arrives, or a lesson is learned; after any interruption, a session resumes from this section plus the pages on disk. The entries below are shape illustrations with <placeholders>, not a real log; a live campaign accumulates entries of these shapes, newest appended last:

- [x] Phase 1: inventory agents complete; one digest per area recorded under Inventory findings
- [x] Phase 2: catalog + directory layout designed; adversarial plan review applied (<n> merges, <n> splits, <n> scope amendments, <n> new fold-ins, boundary statements, batch order)
- [x] Phase 3: user scope decisions taken (recorded under Scope decisions); explicit go received
- [x] <batch id> GENERATED + LINTED + VERIFIED (<done>/<total> pages): <page> (<lines> ln), <page> (<lines> ln), ... <links> links and <blocks> code blocks disk-verified across the batch. Post-lint fixes: <defect classes with counts>. Residual verifier flags: <n>, all adjudicated false positives (<classes>).
- [ ] <batch id> IN FLIGHT: <one writer per page; which pages; lint trailing which batch>
- [<date>] AMENDMENT: \<the user's instruction, verbatim where short, and what it supersedes; mirrored in the amendments section under Execution & verification\>
- [<date>] CORRECTION: <an earlier recorded claim> is wrong; <the re-verified fact and the measurement that established it>
- [<date>] LESSON: <a verifier false-positive class, a settled linking adjudication, a pipeline fix; folded into future briefs>

## Scope decisions (user-confirmed)

1. Include two supporting construct groups beyond the four prompt areas:
   - x86-64 page tables: PTE/PMD bit encoding, swap/non-present (softleaf) entry encoding, page-table allocation + locking (ptdesc, split ptlocks)
   - folio/page side: folio->mapping anon encoding, folio refcount vs mapcount model
2. Curate the full VMA-operation syscall set beyond mmap/munmap: brk, mremap, mprotect, mlock, madvise (one page each).
3. Catalog must mark every page as [prompt] (explicitly in prompt.md bullets) or [curated] (gap-fill).
4. x86-64 only throughout; the stale draft corpus and the older devel checkout are not inputs.
5. GUP (get_user_pages / pin_user_pages) added as its own group (user request); topics curated from a dedicated v7.0 inventory; fault/gup-faultin.md relocates into it.
6. Style leadership: the user explicitly released the strict imitate-docs/acpi-golden-pages rule ("Do what you think is most suitable. You can do better."). What stays mandatory: the template section order, the caution block, self-containment, verbatim on-disk code citation, Elixir linking, and every writing/diagram gate (7a-7k incl. the "arm" ban). What is released: mirroring the acpi pages' specific prose rhythm, diagram choices, and DETAILS architecture — each page's DETAILS is architected to fit its material (dispatch tables, state-transition figures, per-callback matrices, lifecycle walks) at or above the golden-page bar.

## Inventory findings (Phase 1)

### Fault area (agent B, complete)

Verified at HEAD 028ef9c9. Key structure for curation:

- Entry chain: `exc_page_fault` → `handle_page_fault` → `do_user_addr_fault` (arch/x86/mm/fault.c:1483/1461/1206); X86_PF_* bits (trap_pf.h:21-29); access_error incl. pkeys + shadow stack; per-VMA-lock attempt (`lock_vma_under_rcu` mm/mmap_lock.c:296) then `lock_mm_and_find_vma` fallback (mm/mmap_lock.c:496); unbounded retry loop gated on signals only.
- `__handle_mm_fault` descent (mm/memory.c:6355): pgd→p4d→pud (huge-PUD create/wp = DAX only) → pmd (create_huge_pmd/wp_huge_pmd/do_huge_pmd_numa_page/device-private/migration-wait) → `handle_pte_fault` (mm/memory.c:6273).
- `handle_pte_fault` dispatch: none→`do_pte_missing` (anon: `do_anonymous_page` mm/memory.c:5217; file: `do_fault` :5903 → read/cow/shared); !present→`do_swap_page` :4706 (softleaf classification: migration, device-exclusive, device-private, hwpoison, markers); protnone→`do_numa_page` :6048; write/unshare→`do_wp_page` :4149 (reuse/copy/shared+mkwrite).
- Completion machinery: `__do_fault` :5337, `finish_fault` :5556, `set_pte_range` :5497, `do_set_pmd` :5407; fault-around `do_fault_around` :5733 (default 64 KiB, clamps documented).
- hugetlb: `hugetlb_fault` :5972 / `hugetlb_no_page` :5722 / `hugetlb_wp` :5450, own mutex table + vma lock + reservation consumption.
- THP anon: `do_huge_pmd_anonymous_page` huge_memory.c:1461 (huge zero page), `do_huge_pmd_wp_page` :2060, `do_huge_pmd_numa_page` :2185, `do_huge_pmd_device_private` :1375.
- uffd interception sites enumerated (7 sites); PTE markers (UFFD_WP/POISONED/GUARD swapops.h:283-299).
- vm_fault struct mm.h:698; fault_flag enum mm_types.h:1735; VM_FAULT_* mm_types.h:1618; retry-combo rules :1712-1729.
- Complete FAULT_FLAG_VMA_LOCK bail-site list: `vmf_can_call_fault` :3698, `__vmf_anon_prepare` :3723, do_swap_page device-private :4734, huge-pmd device-private, sanitize_fault_flags SIGSEGV combo, hugetlb releases.
- Driver-service helpers: `filemap_fault`/`filemap_map_pages` (generic_file_vm_ops filemap.c:3982), `shmem_fault` :2749, `vmf_insert_pfn/mixed/page_mkwrite` family memory.c:2710-2856.
- Agent-suggested extras: GUP fault-in (`faultin_page` gup.c:1087, `fixup_user_fault` :1564), per-VMA-lock internals page, softleaf/leafops.h layer page, memcg-OOM-at-fault, vsyscall emulation, kernel-extable fixup.

### rmap area (agent C, complete)

Verified at HEAD. Key v7.0 facts: anon_vma lock/refcount helpers live in mm/internal.h; FOLIO_MAPPING_* (renamed from PAGE_MAPPING_*); CONFIG_MM_ID per-MM mapcount (_mm_id/_mm_ids, folio_maybe_mapped_shared mm.h:2613); anon_vma_clone takes enum vma_operation {SPLIT, MERGE_UNFAULTED, REMAP, FORK} (mm/internal.h:251).

- struct anon_vma rmap.h:32 (root/rwsem/refcount/num_children/num_active_vmas/parent/rb_root); slab SLAB_TYPESAFE_BY_RCU (rmap.c:555); alloc/free rmap.c:90/110; lock API internal.h:218-246; folio_get_anon_vma rmap.c:587, folio_lock_anon_vma_read :633.
- struct anon_vma_chain rmap.h:83; avc slab; assign/link rmap.c:150; interval tree mm/interval_tree.c:71-103.
- Setup/teardown: __anon_vma_prepare rmap.c:185 (first fault); find_mergeable_anon_vma mm/vma.c:2003; anon_vma_clone rmap.c:320 + maybe_reuse_anon_vma :270 (reuse iff num_active_vmas==0 && num_children<=1); anon_vma_fork :378; unlink_anon_vmas :479 (two-pass teardown); callers enumerated per vma_operation.
- Add/remove API with full caller lists: folio_add_new_anon_rmap :1636, folio_add_anon_rmap_ptes/pmd :1589/1610, folio_add_file_rmap_* :1723+, folio_remove_rmap_* :1891+, hugetlb_* variants :3120+, dup/share inlines rmap.h:492-830, folio_move_anon_rmap :1434.
- Mapcount model: _mapcount/_large_mapcount/_entire_mapcount/_nr_pages_mapped/_pincount + _mm_id fields (mm_types.h:430-464); ENTIRELY_MAPPED internal.h:111; PageAnonExclusive = PG_owner_2 (page-flags.h:146) with full set/clear site list; folio_mapcount mm.h:1594.
- mapping encoding: FOLIO_MAPPING_ANON/ANON_KSM/KSM page-flags.h:717-720; packing in __folio_set_anon rmap.c:1477; folio->index via linear_page_index.
- Walking: rmap_walk_control rmap.h:951 (all callbacks); rmap_walk anon/file/ksm dispatch rmap.c:3093; page_vma_mapped_walk page_vma_mapped.c:180 + PVMW_ flags.
- Consumers with caller lists: folio_referenced :1059, try_to_unmap :2386 (+TTU_* rmap.h:94-105), try_to_migrate :2731, folio_mkclean :1193 (+mapping_wrprotect_range :1267, pfn_mkclean_range :1304), remove_migration_ptes migrate.c:455, mlock_vma_folio/munlock_vma_folio internal.h:1111/1127.
- File side: i_mmap interval tree + i_mmap_rwsem API fs.h:488-540; unmap_mapping_range/pages memory.c:4318/4354; hugetlb huge_pmd_share over i_mmap hugetlb.c:6878.
- Locking: rmap.c:20-53 ordering block; root-rwsem rule; RCU contracts.
- Agent-suggested extras: KSM rmap backend (ksm_rmap_item), TLB unmap-flush batching (try_to_unmap_flush, rmap.c:711-810, active on x86-64), per-MM mapcount (_mm_id) page, device-exclusive (make_device_exclusive rmap.c:2808), page_mapped_in_vma, softleaf use inside pvmw.

### GUP area (agent D, complete)

Verified on disk at HEAD. v7.0-specific: follow_page() removed (folio_walk replaces it for non-GUP users); no devmap/DAX follow paths; no per-VMA-lock GUP (slow path is mmap_lock-only); gup_fast guards FOLL_PIN with raw_seqcount on mm->write_protect_seq against fork; gup_fast_folio_allowed is the folio_fast_pin_allowed successor; try_grab_page gone (folio-only grabs); pofs (pages_or_folios) drives longterm migration with unbounded -EAGAIN retry. Full API/flag/descent/pinning/longterm anchors are embedded in the gup/ catalog rows. Docs: Documentation/core-api/pin_user_pages.rst (286 lines). Consumers with verified sites: iov_iter (lib/iov_iter.c:1091/1763/1814), io_uring (memmap.c:63, rsrc.c:107/701, zcrx.c:211), vfio (type1.c:598/486), iommufd (pages.c:940/2311/839), RDMA umem (umem.c:236/62/253), KVM (kvm_main.c:2874/2908/3091), futex (core.c:638/790), process_vm_access (:106/127), udmabuf (:335).

### mm_struct + VMA area (agent A, complete)

Verified at HEAD (agent noted semcode index returned some stale line numbers; on-disk tree is ground truth — carry this caveat into execution). v7.0-specific: mm_struct.flags is mm_flags_t bitmap (mm_types.h:1273) with mm_flags_* helpers; rss_stat percpu counters :1266; mm_lock_seq + vma_writer_wait for per-VMA-lock writers; VMA flags are vma_flags_t bitmap with const vm_flags union view (DECLARE_VMA_BIT mm.h:296-397, mutators mm.h:919-987); vm_refcnt with VM_REFCNT_EXCLUDE_READERS_BIT(30) mm_types.h:764; vm_area_cachep with freeptr_offset(vm_freeptr) + sheaf_capacity=32 + SLAB_TYPESAFE_BY_RCU (mm/vma_init.c:14); merge via struct vma_merge_struct/VMG_STATE (mm/vma.h:69/236); munmap via struct vma_munmap_struct + vms_* (mm/vma.h:34, mm/vma.c:1256-1379) + struct unmap_desc (mm/vma.h:158); mmap via struct mmap_state (mm/vma.c:10) + __mmap_setup/__mmap_new_vma/__mmap_complete + call_mmap_prepare/vm_area_desc; mseal present (mm/mseal.c); vm_operations_struct at mm.h:749 with find_normal_page (replaces find_special_page); legacy_special_mapping_vmops removed; instances: generic_file_vm_ops filemap.c:3982, shmem_vm_ops/shmem_anon_vm_ops shmem.c:5309/5318, hugetlb_vm_ops hugetlb.c:4828, special_mapping_vmops mmap.c:1416, secretmem_vm_ops secretmem.c:111, vma_dummy_vm_ops init-mm.c:20, amdgpu_gem_vm_ops amdgpu_gem.c:148. Limits: sysctl_max_map_count default 65530 (util.c:755), stack_guard_gap 1 MB (mmap.c:939), sysctl_legacy_va_layout (mmap.c:1517). Full lifecycle/locking API anchors captured (fork.c mm_alloc:1154/mm_init:1072/dup_mm:1515/mmput:1193/__mmput:1167; mmap_lock.h read/write API; kthread_use_mm kthread.c:1615).

## Directory organization (proposed)

All pages under `${CLAUDE_SKILL_DIR}/docs/mm/`, two levels deep, matching the house layout used by every other subsystem (`docs/acpi/ec/…`, `docs/pci/bus/…`). Nine groups:

```
docs/mm/
├── mm-struct/    the per-process address-space object
├── vma/          vm_area_struct: the object, its indexes, tree operations
├── vma-ops/      vm_operations_struct + concrete instances
├── map/          address-space syscalls that create/reshape/destroy VMAs
├── fault/        the page-fault surface, one page per case
├── gup/          get_user_pages / pin_user_pages: software-initiated page access
├── rmap/         reverse mapping
├── pgtable/      x86-64 entry encodings + table lifecycle (user-approved group)
└── folio/        the folio side faults/rmap manipulate (user-approved group)
```

Rationale: prompt.md's four H3 areas map to mm-struct, vma(+vma-ops+map), fault, rmap; vma splits three ways because its bullet list mixes three kinds of page (the object itself, the ops structure with driver examples, and the syscalls that drive tree operations), and a single 25-page directory would bury the structure the prompt's own numbering implies.

## Curated page catalog

Tags: [prompt] = explicitly in a prompt.md bullet; [curated] = gap-fill for topics that belong to the area but are absent from the bullets. Fault/rmap/pgtable/folio groups are final (inventoried); mm-struct/vma/vma-ops/map symbol anchors pending agent A.

### fault/ (from inventory B)

| page | scope (anchor symbols) | tag |
|---|---|---|
| x86-64-entry.md | exc_page_fault → do_user_addr_fault, X86_PF_* bits, access_error (pkeys, shadow stack), retry loop, signal delivery; one-sentence scoping note that do_kern_addr_fault (kernel addresses) is outside this set | [prompt] |
| handle-mm-fault.md | handle_mm_fault wrapper (sanitize, lru_gen, memcg-OOM, mm_account_fault, hugetlb divert at memory.c:6622) + __handle_mm_fault descent with every PUD/PMD branch: huge create/wp, set-accessed, the retry_pud loop, pmd_migration_entry_wait, device-private, fix_spurious_fault; stops at the handle_pte_fault call | [prompt] |
| pte-dispatch.md | handle_pte_fault decision structure, orig_pte snapshot rules, spurious-fault fixup | [curated] |
| vm-fault.md | the fault contract: struct vm_fault field-by-field (mm.h:698), enum fault_flag (mm_types.h:1735), vm_fault_reason codes (:1618), legal ALLOW_RETRY/TRIED combos | [prompt; absorbs the curated flags-codes scope] |
| anonymous.md | do_anonymous_page, zero-page read case, alloc_anon_folio mTHP order selection | [prompt] |
| file-dispatch.md | do_fault + __do_fault + vmf_can_call_fault, no-\>fault SIGBUS path | [prompt] |
| file-read.md | do_read_fault + fault-around (do_fault_around, 64 KiB default, clamps) | [prompt] |
| file-cow.md | do_cow_fault, cow_page prealloc, copy_mc_user_highpage | [prompt] |
| file-shared.md | do_shared_fault, do_page_mkwrite protocol, fault_dirty_shared_page | [prompt] |
| finish-fault.md | finish_fault, set_pte_range, do_set_pmd file-THP, large-folio fitting | [curated] |
| wp.md | do_wp_page: uffd intercept, wp_page_reuse vs wp_page_copy vs wp_page_shared/wp_pfn_shared, anon-exclusive reuse tests | [prompt] |
| swap-in.md | do_swap_page as the !pte_present handler: one-table summary of the non-swap softleaf early exits (incl. handle_pte_marker :4496, each with its home page elsewhere), then the genuine swap-in path in full: swapcache, readahead vs SWP_SYNCHRONOUS_IO, mTHP order, ksm copy, exclusivity restore | [prompt] |
| numa.md | do_numa_page, numa_migrate_check, migrate_misplaced_folio, rebuild | [prompt] |
| thp-anon.md | do_huge_pmd_anonymous_page, huge zero folio, __do_huge_pmd_anonymous_page | [curated] |
| thp-wp.md | do_huge_pmd_wp_page, do_huge_zero_wp_pmd, reuse vs split fallback | [curated] |
| thp-numa.md | do_huge_pmd_numa_page | [curated] |
| hugetlb.md | hugetlb_fault / hugetlb_no_page / hugetlb_wp, fault-mutex table, reservations at fault | [curated] |
| userfaultfd.md | handle_userfault + all 7 interception sites + uffd-wp PTE markers | [curated] |
| vma-lock-path.md | lock_vma_under_rcu, lock_mm_and_find_vma, complete FAULT_FLAG_VMA_LOCK bail-site catalog, VMA_LOCK_SUCCESS/RETRY stats | [curated] |
| pfn-insert.md | vmf_insert_pfn/mixed/page_mkwrite family, PFNMAP vs MIXEDMAP, wp_pfn_shared/pfn_mkwrite, and the huge service helpers vmf_insert_pfn_pmd/vmf_insert_folio_pmd/vmf_insert_folio_pud (huge_memory.c:1607/1633/1749) where DAX huge_fault callbacks land | [curated] |
(gup-faultin.md relocated to the gup/ group as gup/faultin.md — see below)

Folded rather than paged: fault accounting/instrumentation (into handle-mm-fault.md), PTE guard/poison markers (into pgtable/softleaf.md + userfaultfd.md), device-private migrate_to_ram (noted inside swap-in.md and thp pages), vsyscall emulation + kernel extable fixup (noted inside x86-64-entry.md).

### gup/ (user-requested group; from inventory D, all anchors on-disk verified)

| page | scope (anchor symbols) | tag |
|---|---|---|
| overview.md | the API surface and its rules: get_user_pages/_remote/_unlocked/_fast(_only) (gup.c:2644/2603/2672/3276/3242) vs pin_user_pages family (:3376/3342/3396/3310), memfd_pin_folios :3436, the unpin family (:185-449, folio_add_pin(s)), get-vs-pin semantics + per-API caller populations (iov_iter, io_uring, vfio/iommufd, RDMA umem, KVM, futex, process_vm_access, udmabuf — sites inventoried); get_dump_page :2187 | [curated] |
| foll-flags.md | public FOLL_* (mm_types.h:1809-1852) + internal FOLL_* (internal.h:1530-1545) with values/meanings, INTERNAL_GUP_FLAGS, is_valid_gup_args (gup.c:2500) rules (GET^PIN, LONGTERM⇒PIN, LONGTERM+PCI_P2PDMA illegal, FOLL_UNLOCKABLE), fast-path accepted mask :3183 | [curated] |
| slow-path.md | __get_user_pages :1354 walkthrough: gup_vma_lookup :1265, check_vma_flags :1200, writable_file_mapping_allowed :1182, follow_page_mask :1007 descent (follow_p4d/pud/pmd_mask, follow_page_pte :802, follow_huge_pud/pmd :649/:701 — no devmap at v7.0), can_follow_write_* FORCE-COW gates, no_page_table/FOLL_DUMP, get_gate_page :1030, __get_user_pages_locked :1649 retry machine + gup_signal_pending; mmap_lock-only (no per-VMA-lock GUP at v7.0) | [curated] |
| fast-path.md | gup_fast_fallback :3175 + gup_fast :3129: irq-off + no-mmap_lock constraints, write_protect_seq raw_seqcount for PIN vs fork, gup_fast_pgd→pte_range descent with lockless pXd reads, leaf handlers + split-race re-reads, gup_fast_folio_allowed :2738 (secretmem/dirty-tracked-file rejects), x86-64 synchronization story (HAVE_GUP_FAST + MMU_GATHER_RCU_TABLE_FREE, IRQ-off vs IPI/RCU table free) | [curated] |
| pinning.md | FOLL_PIN mechanics: _pincount + folio_has_pincount (mm.h:2323) vs GUP_PIN_COUNTING_BIAS=1<<10 (mm.h:1919), try_grab_folio :140 / try_grab_folio_fast :517 / gup_put_folio :102, folio_maybe_dma_pinned mm.h:2355, sanity_check_pinned_pages :31, gup_must_unshare (internal.h:1571) with all 6 enforcement sites, fork+GUP COW story (folio_needs_cow_for_dma mm.h:2378, MMF_HAS_PINNED sticky flag, write_protect_seq); gup_test diagnostics noted | [curated] |
| longterm.md | FOLL_LONGTERM: folio_is_longterm_pinnable mm.h:2413, struct pages_or_folios :2207, collect/migrate_longterm_unpinnable_folios :2265/:2320, check_and_migrate_* :2385-2454, unbounded -EAGAIN retry under memalloc_pin_save, device-coherent + FOLL_PCI_P2PDMA cases, hugetlb/memfd interaction | [curated] |
| faultin.md | the fault-in-without-returning-pages surface: faultin_page :1087 (FOLL_→FAULT_FLAG translation, VM_FAULT handling), faultin_page_range :1887 (MADV_POPULATE), populate_vma_page_range :1813 + __mm_populate :1925 (mlock/MAP_POPULATE), fixup_user_fault :1564 (futex/KVM), fault_in_writeable/readable family :2046-2169 | [curated; relocated from fault/] |
| folio-walk.md | folio_walk_start/end (pagewalk.h:196/200, struct folio_walk :177, enum folio_walk_level :160): the single-address folio lookup that replaced follow_page() at v7.0 for non-GUP users, with its ksm/migrate/rmap/huge_memory callers | [curated] |

### rmap/ (from inventory C)

| page | scope (anchor symbols) | tag |
|---|---|---|
| anon-vma.md | struct anon_vma fields, slab + SLAB_TYPESAFE_BY_RCU, alloc/free, refcount API, folio_get_anon_vma / folio_lock_anon_vma_read RCU contracts | [prompt] |
| anon-vma-chain.md | struct anon_vma_chain, same_vma list vs rb interval-tree membership, avc slab, interval-tree insert/remove | [prompt] |
| anon-setup.md | __anon_vma_prepare first-fault, find_mergeable_anon_vma, anon_vma_clone + enum vma_operation, maybe_reuse_anon_vma heuristic, anon_vma_fork, unlink_anon_vmas two-pass teardown | [prompt] |
| file-rmap.md | i_mmap interval tree, i_mmap_rwsem API, vma_interval_tree_*, unmap_mapping_range/pages, hugetlb huge_pmd_share over i_mmap | [prompt] |
| add-remove.md | folio_add_new/ptes/pmd anon + file add/remove API with caller sites, rmap_t RMAP_EXCLUSIVE, dup/share inlines for fork+swapout, folio_move_anon_rmap | [curated] |
| walk.md | rmap_walk + rmap_walk_control callbacks, anon/file backends, lock modes; rmap_walk_ksm at dispatch-contract level only (just enough ksm_rmap_item/stable-node structure to explain dispatch; KSM proper out of scope) | [curated] |
| pvmw.md | struct page_vma_mapped_walk, PVMW_SYNC/MIGRATION/PGTABLE_CROSSED, softleaf migration-entry matching under PVMW_MIGRATION, hugetlb short-circuit, page_mapped_in_vma wrapper (page_vma_mapped.c:348) | [curated] |
| try-to-unmap.md | try_to_unmap(_one), TTU_* flags, folio_unmap_pte_batch, TLB unmap-flush batching (rmap.c:711-810) | [curated] |
| try-to-migrate.md | try_to_migrate(_one), migration entries, remove_migration_ptes; sibling convert-to-non-present operation make_device_exclusive (rmap.c:2808, folio_walk-based at v7.0) | [curated] |
| folio-referenced.md | folio_referenced(_one), folio_referenced_arg, vmscan callers | [curated] |
| mkclean.md | folio_mkclean, page_vma_mkclean_one, mapping_wrprotect_range, pfn_mkclean_range | [curated] |
| locking.md | rmap.c:20-53 lock-ordering block, root-rwsem rule, RCU freeing sync in anon_vma_free | [curated] |

### pgtable/ (user-approved supporting group)

| page | scope | tag |
|---|---|---|
| x86-64-entries.md | pte_t/pmd_t/pud_t bit layout (_PAGE_* incl. _PAGE_PROTNONE), accessor/mk helpers, NX/dirty/soft-dirty on x86-64 | [curated] |
| softleaf.md | leafops.h softleaf_* classification of non-present entries: swap, migration, device-private/exclusive, hwpoison, PTE markers (UFFD_WP/POISONED/GUARD) | [curated] |
| alloc-locking.md | page-table allocation/free (ptdesc), split PTE/PMD locks, pte_offset_map_* lockless rules, x86-64 paging levels | [curated] |

### folio/ (user-approved supporting group)

| page | scope | tag |
|---|---|---|
| mapping-encoding.md | FOLIO_MAPPING_ANON/ANON_KSM/KSM bits, anon_vma pointer packing in __folio_set_anon, folio->index / linear_page_index | [curated] |
| refcount-mapcount.md | _refcount vs _mapcount/_large_mapcount/_entire_mapcount/_nr_pages_mapped, folio_mapcount/folio_mapped, PageAnonExclusive, ENTIRELY_MAPPED | [curated] |
| mm-id.md | CONFIG_MM_ID per-MM mapcount: _mm_id/_mm_ids bit-spinlock + SHARED bit protocol, folio_maybe_mapped_shared | [curated] |

### mm-struct/ (from inventory A)

| page | scope (anchor symbols) | tag |
|---|---|---|
| overview.md | struct mm_struct field-group tour (mm_types.h:1123): mm_mt, pgd, counts, layout fields, write_protect_seq, mm_cid/futex_phash/flexible_array noted | [prompt] |
| locking.md | mmap_lock API (mmap_lock.h read/write/killable/trylock/downgrade/assert), mm_lock_seq + vma_end_write_all, speculation helpers, tracepoints, lock-ordering blocks (rmap.c:21, filemap.c:81), mm_take_all_locks | [prompt] |
| refcount.md | mm_users vs mm_count, mmget/mmget_not_zero/mmput/mmput_async/__mmput vs mmgrab/mmdrop, async_put_work, and the active_mm/lazy-TLB borrowing story incl. kthread_use_mm/kthread_unuse_mm (kthread.c:1615/1662, Documentation/mm/active_mm.rst) | [prompt] |
| lifecycle.md | mm_alloc/mm_init (fork.c:1154/1072), dup_mm :1515, __mmput teardown order :1167, exit_mmap (mm/mmap.c:1275) | [curated] |
| flags.md | mm_flags_t bitmap (mm_types.h:1273, :1854-1938), mm_flags_* helpers (mm.h:877-905), notable MMF_* incl. MMF_TOPDOWN, MMF_INIT_LEGACY_MASK | [curated] |
| counters.md | rss_stat percpu counters (mm_types_task.h:26, mm_types.h:1266), get/add/inc/dec_mm_counter, get_mm_rss, hiwater family (mm.h:3063-3154), vm_stat_account | [curated] |
| arch-context.md | x86-64 mm_context_t (arch/x86/include/asm/mmu.h:84): ctx_id/tlb_gen, LDT, pkeys, LAM/untag_mask, PCID at switch_mm level | [curated] |

### vma/ (from inventory A)

| page | scope (anchor symbols) | tag |
|---|---|---|
| overview.md | struct vm_area_struct tour (mm_types.h:913): vm_start/end + vm_freeptr union, flags union, per-VMA-lock fields, shared.rb, anon fields, anon_name + pfnmap_track_ctx noted | [prompt 1] |
| allocation.md | vm_area_alloc/vm_area_init_from/vm_area_dup/vm_area_free (mm/vma_init.c:28-144), vma_init + vma_dummy_vm_ops | [prompt 2] |
| slab-rcu.md | vma_state_init (vma_init.c:14): kmem_cache_args freeptr_offset=vm_freeptr, sheaf_capacity=32, SLAB_TYPESAFE_BY_RCU reuse semantics for lockless readers, how SLUB uses the freepointer | [prompt 9] |
| refcount-locking.md | vm_refcnt encoding + VM_REFCNT_EXCLUDE_READERS_BIT (mm_types.h:764), vma_start_read/_locked/vma_end_read, vma_start_write(_killable)/__vma_start_write, attach/detach, exclude-readers machinery (mm/mmap_lock.c:50-212), rcuwait writer wait, asserts | [prompt 8] |
| flags.md | vma_flags_t bitmap + const vm_flags union view, DECLARE_VMA_BIT enum (mm.h:296-397), VM_* masks incl. VM_SEALED/VM_SHADOW_STACK/VM_SPECIAL/VM_ACCESS_FLAGS, mutators vm_flags_init/reset/set/clear/mod (mm.h:919-987) and why the const view forces them | [prompt 10] |
| maple-tree.md | mm_mt + MM_MT_FLAGS, struct vma_iterator (mm_types.h:1497), vma_iter_* families (mm.h:1312-1382, mm/vma.h:277-637) mapped to underlying mas_* calls, __mt_dup, validate_mm | [prompt 6] |
| insertion.md | insertion API surface: vma_link/vma_link_file (vma.c:1824/1810), insert_vm_struct :3273, __mmap_new_vma :2506, vma_iter_store_new/store_gfp/bulk_store, map_count + sysctl_max_map_count | [prompt 3a] |
| insertion-algorithm.md | maple-tree store walkthrough under the iterator: prealloc, wr_mas store paths, RCU-safe node replacement | [prompt 3b] |
| removal.md | removal API surface: do_vmi_munmap/do_vmi_align_munmap (vma.c:1611/1564), struct vma_munmap_struct (vma.h:34), vms_gather/complete/clear_ptes/clean_up_area, remove_vma, unlink_vma_file_batch | [prompt 4a] |
| removal-algorithm.md | maple-tree erase + page-table teardown: unmap_region (vma.c:478), struct unmap_desc (vma.h:158), struct mmu_gather / tlb_gather_mmu / unmap_vmas / free_pgtables / tlb_finish_mmu | [prompt 4b] |
| traversal.md | lookup API: find_vma/find_vma_prev/find_vma_intersection (mmap.c:902/925/883), vma_lookup, vma_find/next/prev, for_each_vma(_range), lock_vma_under_rcu + lock_next_vma (/proc maps RCU iteration) | [prompt 5a] |
| traversal-algorithm.md | maple-tree lookup walkthrough: mas_walk/mas_find node descent, RCU read protocol, gap search (vma_iter_area_lowest/highest → unmapped_area) | [prompt 5b] |
| split.md | __split_vma/split_vma (vma.c:497/590), may_split callback, max_map_count gate, vma_adjust_trans_huge | [prompt 13] |
| merge.md | the vmg contract: struct vma_merge_struct + enum vma_merge_state (vma.h:69/56), VMG_STATE/VMG_VMA_STATE, vma_merge_new_range :1046 + vma_merge_extend :1757 (new/unfaulted-range merge, used by mmap/brk/expand) | [prompt 14] |
| merge-existing.md | vma_merge_existing_range :805 + commit_merge :728: the left/right/both case matrix driven by mprotect/madvise/mremap via vma_modify_* | [curated; split of 14] |
| adjust.md | vma_expand/vma_shrink (vma.c:1151/1228), copy_vma :1844, relocate_vma_down (exec) | [prompt 15] |
| modify-spine.md | the shared modification spine: init_multi_vma_prep/init_vma_prep :142/:413, vma_prepare :288, vma_complete :335, vma_modify_flags/_name/_policy/_flags_uffd | [curated; fills blank bullet 7] |
| fork-dup.md | dup_mmap (mmap.c:1732): __mt_dup + vma_iter_bulk_store, per-VMA dup (vm_area_dup, anon_vma_fork hook, copy_page_range + write_protect_seq), VM_WIPEONFORK | [curated] |
| stack-growth.md | expand_upwards/expand_downwards (vma.c:3090/3176), expand_stack_locked (mmap.c:955), stack_guard_gap (1 MB, mmap.c:939), VM_GROWSDOWN/UP, exec-time create_init_stack_vma (vma_exec.c) | [curated] |

### vma-ops/ (from inventory A)

| page | scope | tag |
|---|---|---|
| vm-operations.md | struct vm_operations_struct (mm.h:749) callback-by-callback with invocation sites (open/close/may_split/mremap/mprotect/fault/huge_fault/map_pages/pagesize/page_mkwrite/pfn_mkwrite/access/name/set_policy/get_policy/find_normal_page), mapped onto the VMA lifecycle mmap→fault→wp→split/move→unmap | [prompt 11] |
| amdgpu-gem.md | amdgpu_gem_vm_ops (drivers/gpu/drm/amd/amdgpu/amdgpu_gem.c:148): GEM object mmap lifecycle, .fault via TTM, open/close refcounting | [prompt 12.1] |
| hugetlb.md | hugetlb_vm_ops (hugetlb.c:4828): pagesize, open/close reservation lifecycle, may_split alignment | [prompt 12.2] |
| generic-file.md | generic_file_vm_ops (filemap.c:3982): filemap_fault/filemap_map_pages/filemap_page_mkwrite as the generic page-cache mechanism | [curated; realizes 12.3] |
| special-mapping.md | special_mapping_vmops (mmap.c:1416) + struct vm_special_mapping (mm_types.h:1658), _install_special_mapping :1505, x86-64 vdso/vvar (arch/x86/entry/vdso/vma.c), get_gate_vma (vsyscall_64.c:303) | [curated] |
| shmem.md | shmem_vm_ops + shmem_anon_vm_ops (shmem.c:5309/5318): shmem_fault, MAP_SHARED anonymous via shmem_zero_setup | [curated] |

### map/ (from inventory A)

| page | scope | tag |
|---|---|---|
| mmap.md | end-to-end syscall pipeline: sys_mmap chain (mmap.c:612/567, util.c:565), do_mmap :335, mmap_region/__mmap_region (vma.c:2818/2720), struct mmap_state (vma.c:10), __mmap_setup/__mmap_new_vma/__mmap_complete, call_mmap_prepare + struct vm_area_desc; address selection and tree store treated as one-line handoffs | [prompt 16] |
| address-space-layout.md | where mappings go on x86-64: arch_pick_mmap_layout (arch/x86/mm/mmap.c:122), mmap_is_legacy + sysctl_legacy_va_layout, mmap_base randomization, MMF_TOPDOWN, get_unmapped_area dispatch (file + thp_get_unmapped_area_vmflags hooks), vm_unmapped_area gap search, TASK_SIZE/DEFAULT_MAP_WINDOW under LA57 | [curated] |
| munmap.md | munmap syscall surface (mmap.c:1075/1069, vma.c:3251) over the vms_* machinery, MAP_FIXED-driven unmap, sealing checks | [prompt 17] |
| brk.md | sys_brk (mmap.c:116), do_brk_flags (vma.c:2866), the brk fast path vs full mmap | [curated] |
| mremap.md | sys_mremap (mremap.c:1965), struct vma_remap_struct :50, mremap_to :1367, move_vma + move_page_tables :795, pagetable_move_control | [curated] |
| mprotect.md | sys_mprotect/pkey_mprotect (mprotect.c:948/956), do_mprotect_pkey :801, mprotect_fixup, x86-64 pkeys | [curated] |
| mlock.md | mlock family syscalls, apply_vma_lock_flags (mlock.c:514), mlock_fixup :466, VM_LOCKED/VM_LOCKONFAULT, RLIMIT_MEMLOCK, plus the folio-side mlock state machine (mlock_vma_folio/munlock_vma_folio internal.h:1111/1127, mlock_folio_batch machinery mlock.c:180-303) | [curated] |
| madvise.md | madvise entry structure: struct madvise_behavior/_range (madvise.c:66/61), madvise_vma_behavior :1345, which behaviors split/merge VMAs vs act on pages | [curated] |
| mseal.md | sys_mseal (mseal.c:187), do_mseal :139, mseal_apply :55, vma_is_sealed (vma.h:662), VM_SEALED gates across map/ operations | [curated] |

### Fold-in adjudications (agent-A suggested extras that do NOT get pages)

mm_cid, futex_phash, membarrier_state → noted in mm-struct/overview.md field tour only. mm_take_all_locks → mm-struct/locking.md. anon_vma_name struct → vma/overview.md field tour. pfnmap_track_ctx → vma/overview.md + fault/pfn-insert.md. mmap_prepare/vm_area_desc remodel → map/mmap.md. shadow-stack VMAs → vma/flags.md + fault/x86-64-entry.md. copy_page_range/write_protect_seq → vma/fork-dup.md. create_init_stack_vma/relocate_vma_down → vma/stack-growth.md + vma/adjust.md. unlink_vma_file_batch → vma/removal.md. mmu_gather → vma/removal-algorithm.md. secretmem_vm_ops/vma_dummy_vm_ops → instance list in vma-ops/vm-operations.md. make_device_exclusive → rmap/try-to-migrate.md. page_mapped_in_vma → rmap/pvmw.md. KSM rmap backend → dispatch-contract level in rmap/walk.md only. kthread_use_mm/active_mm → mm-struct/refcount.md (standalone page merged away per review). fault flags + VM_FAULT_* codes → fault/vm-fault.md (standalone page merged away per review). mlock folio-side machinery → map/mlock.md. Address-space layout selection + sysctl_legacy_va_layout → map/address-space-layout.md. gup_test debugfs/selftests → diagnostics notes in gup/pinning.md + gup/longterm.md. memalloc_pin_save/restore → gup/longterm.md. device-coherent/p2pdma pin semantics → gup/longterm.md + gup/foll-flags.md. A dedicated "GUP pins vs fork/COW" page is not needed: gup/pinning.md owns the GUP side (folio_needs_cow_for_dma, MMF_HAS_PINNED, write_protect_seq) and vma/fork-dup.md owns the fork side (copy_page_range early-COW).

Projected total (post-review, +GUP): 87 pages (7 mm-struct + 19 vma + 6 vma-ops + 9 map + 20 fault + 8 gup + 12 rmap + 3 pgtable + 3 folio). Tag census: 38 [prompt], 49 [curated]. mm-struct locking + refcount jointly realize the single "locking and refcount rules" bullet, split for granularity; vm-fault.md carries the merged flags/codes scope; merge-existing.md and address-space-layout.md are [curated] splits.

### Overlap boundary rules (review-confirmed focus statements)

Content overlap between self-contained pages is expected; these rules fix each page's mission so siblings don't duplicate walkthroughs.

- munmap.md owns the syscall surface treating vms_* as a black box; vma/removal.md owns the vms_* VMA-object pipeline (gather/complete, failure/undo); vma/removal-algorithm.md owns the physical side (maple range replacement, unmap_region + unmap_desc, mmu_gather/TLB, free_pgtables clamping). vms_clear_ptes (vma.c:1256) is the seam: removal.md names it as a phase, removal-algorithm.md opens it.
- vma-ops/hugetlb.md owns mapping-time callback + reservation-setup behavior and states explicitly there is no .fault; fault/hugetlb.md owns the fault path that bypasses handle_pte_fault (divert at memory.c:6622) and reservation consumption. All three hugetlb-touching pages (incl. handle-mm-fault.md) state the divert point identically.
- vma/refcount-locking.md owns the vm_refcnt mechanism (state encoding incl. the table at mm_types.h:995-1023, acquire/release, exclude-readers, rcuwait); fault/vma-lock-path.md owns the consumer protocol (lock_vma_under_rcu lookup-and-revalidate, fallback, bail sites, stats). vma/traversal.md lists lock_vma_under_rcu/lock_next_vma as lookup API only.
- vma/maple-tree.md is API-and-contracts only, NO node anatomy; insertion-algorithm.md owns the write half of node anatomy (prealloc sizing, wr_mas slot store/split/spanning store, RCU node replacement), bounded to paths reachable from vma_iter_store/prealloc; traversal-algorithm.md owns the read half (mas_walk/mas_find descent, RCU reader protocol, gap search via mas_empty_area{,_rev} into unmapped_area), bounded likewise. Each algorithm page carries its own node-anatomy primer.
- pgtable/softleaf.md owns encoding/classification only (no fault behavior); fault/swap-in.md owns runtime dispatch + the genuine swap-in path; fault/userfaultfd.md owns the uffd protocol (sleep/wake, 7 sites, marker re-dispatch), registration/ioctl side out of scope.
- folio/refcount-mapcount.md owns counters-at-rest + invariants (no mutation walkthroughs); folio/mm-id.md owns the sharedness-tracking mechanism and its update sites; rmap/add-remove.md owns the mutation API with locking preconditions and complete caller inventories.
- mm-struct/locking.md owns concurrency (mmap_lock rules, mm_lock_seq interplay, ordering blocks); refcount.md owns liveness (mm_users vs mm_count contracts + lazy-TLB borrowing); lifecycle.md owns construction/teardown ordering (mm_alloc → dup_mm → mmput → __mmput → exit_mmap → mmdrop and why each step precedes the next).
- map/mmap.md owns the one-syscall end-to-end pipeline with address selection and tree store as handoffs; map/address-space-layout.md owns where mappings go; vma/insertion.md owns the cross-cutting register-a-new-VMA surface every producer uses (mmap, brk, stack, special mappings, exec).
- fault/handle-mm-fault.md stops at the handle_pte_fault call; fault/pte-dispatch.md owns handle_pte_fault itself (preamble + orig_pte snapshot rules, five-way dispatch, access-dirty fallthrough).
- House rule for fault/ pages: the standard entry-chain recap (exc_page_fault → … → handle_pte_fault) is at most one short paragraph per page.

## Execution & verification

### Per-page procedure (skill-mandated)

1. Before the first batch: read `docs/templates/TEMPLATE-FULL.md` for section order and skim one or two `docs/acpi/` pages once for baseline calibration only. Per user decision 6, the strict imitate-the-closest-acpi-page rule is released: each page's DETAILS is architected to best fit its material (dispatch tables, state-transition figures, per-callback matrices, lifecycle walks, coverage tables), holding or exceeding the golden-page quality bar. Template section order, caution block, self-containment, verbatim code citation, Elixir linking, and all writing/diagram gates remain mandatory.
2. Research with semcode (find_function/find_type/find_callers/find_callchain/grep_functions; find_commit + dig for spec/LKML context in OTHER SOURCES) plus Grep/Read. CAVEAT from inventory: the semcode index returned stale line numbers for some symbols — every cited line number and every reproduced code block must be confirmed against the on-disk file before it lands in a page.
3. Write to `${CLAUDE_SKILL_DIR}/docs/mm/<group>/<slug>.md`. mm's section-6 heading is "none" per the subsystem map → pages carry exactly: H1, caution blockquote, lead summary (+diagram where earned), SUMMARY, SPECIFICATIONS (empty body allowed), LINUX KERNEL, KERNEL DOCUMENTATION, OTHER SOURCES, DETAILS.
4. Elixir links: every symbol mention outside fenced blocks links to `https://elixir.bootlin.com/linux/v7.0/source/<path>#L<line>`; struct/enum keyword kept.

### Project-specific writing bans (from prompt.md, on top of skill gates)

- The word "arm" must never describe a union case or code branch — use "branch", "case", "side", or "leg".
- No hedging words (the skill's 7c list applies).
- x86-64 only: no other-arch code paths; CONFIG assumptions stated per page where relevant (PER_VMA_LOCK, TRANSPARENT_HUGEPAGE, MM_ID, NUMA_BALANCING on).
- Extra attention mandated: object lifecycle (allocation/free/locking/refcount), all state transitions, and complete callback semantics for every ops struct.

### Gates before every save

- Gate A mechanical grep sweep (em-dash, boldface-in-prose, colon idioms, editorializing/superlatives, banned words + "arm", hedges, question headings, internal .md links) — must be zero-hit outside fenced blocks.
- Gate B evidence pass per page: every LINUX KERNEL symbol has both a definition code block and a usage code block in DETAILS; every ```c block diffed against the on-disk file; every Elixir link target spot-verified; DETAILS headings declarative; diagram junction/width checks; coverage sign-off (all sites cited or spread + count stated; limits named with values).
- Tooling: the skill's advisory verifier (`scripts/verify_page.py`) that (a) parses every Elixir link and checks path exists + symbol appears at/near the cited line in the local tree, and (b) extracts every fenced ```c block and fuzzy-diffs it against its cited file. Run on each batch; hand-fix drift.

### Batching & checkpoints

### USER AMENDMENTS (supersede the original order below)

1. PRIORITY REORDER (user): remaining groups generate in this order: vma (highest) → map → fault → rmap → then unlisted remainders (mm-struct leftovers, gup) → vma-ops (lowest, absolutely last).
2. DRAFT MINING (user): before creating any vma/map/fault/rmap/vma-ops page, consult the stale prior-generation drafts in the corpus at `<drafts root>`. A drafts→pages reuse map lives in the "Draft reuse map" section below (built once by read-only research agents; do not re-read all drafts). Reusable material may be collected across multiple drafts into one page, MUST be extended to the current depth standard (B1-level: provenance code blocks, def+usage per symbol, full site enumeration), and MUST be re-verified against the v7.0 tree symbol-by-symbol (drafts contain ~187 banned "arm" usages and possibly stale symbols/lines — never copy blindly).
3. LINT PIPELINE (user): writer agents no longer run their own Gate A/B verification loops. Flow per page: a strongest-model writer researches + writes (following conventions while composing) → a lint agent on a different, cheaper model runs verify_page.py + the Gate A sweeps + Gate-B mechanical checks and fixes violations in place → the orchestrator runs the final verifier. LESSON (from the first lint pass): lint briefs must demand the EXHAUSTIVE bare-span link pass (every occurrence of every kernel symbol linked, per the strict skill rule), not a 15-sample spot-check; known verifier false-positive classes to adjudicate: Elixir directory links (fixed in script), designated-initializer citations, hyphenated compounds matching hedge words ("read-mostly"), wildcard-family links FOO_* (fixed in script), syscall-name(2) links anchored at mm-lifecycle entry points. Lint agents must use UNIQUE scratchpad filenames (two agents collided on a shared scan-script name). Exemption list for bare spans, settled: error/literal values, C keywords, /proc and sysctl path strings, Kconfig syntax fragments (=y), locals/params/goto labels, tracepoint field names, wildcard families whose members are linked, and symbols verified absent from the tree. NON-exempt (settled after a lint agent tried to cite in-family precedent): CONFIG_* options (→ Kconfig config line), generic primitives (READ_ONCE/memcpy/rcu_read_lock/etc. → their x86-64-relevant definition lines), and ops-struct hook names when prose references the specific member. In-family precedent never overrides the rule; both overview pages were retro-fixed.

4. BATCHING (user): pages are generated in batches of about five, one writer per page dispatched together, with a hard checkpoint between batches; lint agents may trail into the next batch. (An earlier amendment briefly switched to one page at a time after a session rate limit killed several parallel writers; it was superseded by ~5-page batching once resume-from-transcript recovery proved cheap. A superseded amendment stays recorded like this rather than being deleted.)

### Revised batch order (post-amendment)

- B2: mm-struct/overview, flags, counters, refcount, locking
- B3a (user-ordered): vma/overview ALONE
- B4: vma/maple-tree, traversal, traversal-algorithm, insertion, insertion-algorithm
- B5: vma/split, merge, merge-existing, adjust, modify-spine
- B6: vma/removal, removal-algorithm, fork-dup, stack-growth
- B3b (user-ordered, closes the vma group): vma/flags, allocation, slab-rcu, refcount-locking
- B7: map/address-space-layout, mmap, munmap, brk
- B8: map/mremap, mprotect, mlock, madvise, mseal
- B9: fault/vm-fault, x86-64-entry, vma-lock-path, handle-mm-fault, pte-dispatch
- B10: fault/anonymous, file-dispatch, file-read, file-cow, file-shared
- B11: fault/finish-fault, wp, swap-in, numa
- B12: fault/thp-anon, thp-wp, thp-numa, hugetlb, userfaultfd
- B13: fault/pfn-insert; rmap/anon-vma, anon-vma-chain, anon-setup, locking
- B14: rmap/file-rmap, add-remove, walk, pvmw
- B15: rmap/try-to-unmap, try-to-migrate, folio-referenced, mkclean
- B16: mm-struct/lifecycle, arch-context; gup/overview, foll-flags, faultin
- B17: gup/slow-path, fast-path, pinning, longterm, folio-walk
- B18: vma-ops/vm-operations, generic-file, shmem
- B19: vma-ops/special-mapping, hugetlb, amdgpu-gem

(6 done in B1 + 81 above = 87.)

## Draft reuse map

(Corpus root: `<drafts root>`, a prior-generation output tree kept beside the kernel tree; file names below are relative to it.)

### fault/ drafts (agent report complete)

HEADLINE: all 17 drafts/fault/*.md are SYMBOL-ACCURATE against v7.0 (5-9 spot-checks each, zero stale symbols) and already softleaf-aware (they document the pte_to_swp_entry/is_swap_pte → leafops.h replacement as provenance). Every file carries a LINUX KERNEL catalog. Systematic defects: "arm/arms" branch-metaphor prose (counts below; worst: do-fault-dispatch ~60, do-fault 26, thp-wp 25, cow 23, wp 17, finish-fault 16; zero in vm-fault/x86-64-entry/handle-mm-fault/anonymous/swap-in/thp-anon/thp-numa) and single-excerpt provenance comments only (one /* path:line */ per block, no interior delimiters for stitched excerpts; re-verify each and add delimiters on reuse). All drafts REUSE-BACKBONE for their namesake pages, with these specifics:

- vm-fault.md → fault/vm-fault: backbone incl. FIELDS table, fault_flag table, vm_fault_reason table, retry combos. Trim its thin GUP + vmf_insert material.
- x86-64-entry.md → fault/x86-64-entry backbone; ALSO the richest mine for vma-lock-path (two-lookup-regime table, lock_mm_and_find_vma/lock_vma_under_rcu sections). Route out do_kern_addr_fault + vsyscall depth (out of catalog scope; keep one-sentence scoping note).
- handle-mm-fault.md → fault/handle-mm-fault backbone; mine its per-VMA-lock bailout section for vma-lock-path; trim the present-entry paragraph (pte-dispatch turf); mm_account_fault stays here (fold accounting into this page).
- handle-pte-fault.md → fault/pte-dispatch backbone (six-outcomes dispatch table, softleaf_type table); mine marker/uffd-wp sections for userfaultfd; 8 arms.
- anonymous.md → fault/anonymous backbone (46 blocks; mTHP order selection; zero-page; RMAP_EXCLUSIVE); mine userfaultfd_missing gate.
- do-fault-dispatch.md + do-fault.md → MERGE into fault/file-dispatch (router half + __do_fault half); DROP their per-branch deep sections (lines ~391-618 / ~403-614) which duplicate file-read/cow/shared; heaviest arm scrub.
- file-read.md → fault/file-read backbone (fault-around window + tunables, filemap_map_pages batch install); 4 arms.
- cow.md → fault/file-cow backbone (copy_mc poison path, VM_FAULT_DONE_COW); trim tail cross-sections; 23 arms.
- shared-writable.md → fault/file-shared backbone (four-stage table, mkwrite protocol, dirty throttle); 1 arm.
- finish-fault.md → fault/finish-fault backbone (large-folio clamp, do_set_pmd, pmd_install); trim per-branch caller sections; 16 arms.
- wp.md → fault/wp backbone (reuse/copy/mkwrite decision table, wp_can_reuse predicates, folio_needs_cow_for_dma); 17 arms.
- swap-in.md → fault/swap-in backbone (softleaf early-exit table, exclusivity decision, swap-free policy); mine uffd-wp branch; 0 arms.
- numa.md → fault/numa backbone for the do_numa_page half; the scanner/mprotect-marking half (task_numa_work/change_prot_numa/change_pte_range, lines ~196-435) is scope-adjacent: compress to a short upstream-context section.
- thp-anon.md → fault/thp-anon backbone (huge-zero path, deposit/withdraw, current _folio/_pf spellings verified).
- thp-wp.md → fault/thp-wp backbone (PMD reuse decision table, split fallback); dedupe PTE-sibling sections against wp; 25 arms.
- thp-numa.md → fault/thp-numa backbone; same scanner-side compression as numa.md.

NO DRAFT FEED (fresh writes): fault/hugetlb (drafts only note the divergence point), fault/pfn-insert, gup/faultin. ASSEMBLE-BY-MINING (no dedicated draft but rich scatter): fault/vma-lock-path (x86-64-entry + handle-mm-fault sections + bail sites catalogued across 12 drafts), fault/userfaultfd (interception notes across 7 drafts + the fully-worked marker path in handle-pte-fault.md).

UNMAPPED DRAFT DEPTH (keep out or footnote): do_kern_addr_fault path, vsyscall emulation depth, memcg reentrancy tangent, NUMA scanner machinery (upstream of fault), vmf_insert_pfn-as-translator.

### vma/ + map/ drafts (agent report complete)

HEADLINE: all 23 drafts/vma/*.md (incl. vm-ops/) are symbol-EXACT at v7.0 (45+ spot-checks, zero misses — generated against this tree). Universal traits: one /* path:line */ provenance comment per block (single-excerpt form only; re-verify on reuse and add interior delimiters where excerpts get stitched), caution banner present (keep). "arm" counts are LOW in this family and several flagged hits are exempt (CPU-architecture names in arch tables, quoted kernel comments) — lint must reword only branch/union-case senses. All drafts REUSE-BACKBONE for their namesake pages:

- overview.md → vma/overview (field tour + outward-pointers figure; 0 arms).
- flags.md → vma/flags (two-view union, per-bit VM_* incl. x86 pkeys/shadow-stack, 2 figures, extra FIELDS section — fold into DETAILS per template; 0 arms). Mine mlock-bits + child-clear notes for map/mlock + vma/fork-dup.
- allocation.md → vma/allocation (vma_state_init, member-by-member vm_area_init_from, alloc call-site census; 4 banned arms). Mine dup_mmap section (§962) for vma/fork-dup.
- slab-rcu.md → vma/slab-rcu (freeptr overlay, TYPESAFE semantics, deep sheaves/barn treatment; 6 banned arms). Sheaf/barn depth exceeds page scope: compress, keep the "other TYPESAFE caches" enumeration.
- refcount-locking.md → vma/refcount-locking (vm_refcnt encoding + state machine figures; 0 arms). Definitive.
- maple-tree.md → vma/maple-tree (vma_iter_*→mas_* wrapper map, MM_MT_FLAGS; 0 arms).
- traversal.md → vma/traversal (three-lookup figure, consumer census; 0 arms).
- traversal-algorithm.md → vma/traversal-algorithm (node geometry, descent walkthrough; 0 arms). Generic maple internals overflow scope: keep bounded to read-path.
- insertion.md → vma/insertion (vma_link three-step, i_mmap link, caller census; 0 arms). Mine dup_mmap bulk-store (§676) for fork-dup.
- insertion-algorithm.md → vma/insertion-algorithm (store_type dispatch, prealloc math, split/spanning, RCU replace; 1 verb-sense arm @1280 reword).
- merge.md → BOTH vma/merge AND vma/merge-existing (split at the vma_merge_existing_range H3; 0 arms).
- adjust.md → vma/adjust (expand/shrink, __adjust_* helpers; 0 arms). Mine copy_vma/vma_merge_copied_range (§950) + relocate_vma_down (§546) for map/mremap.
- split.md → vma/split (may_split veto census, unwind; 1 banned arm @732). Mine mprotect/madvise/mbind fixup subsections for map pages.
- modify-spine.md → vma/modify-spine (three-trees-three-phases figure; 2 arms both inside quoted kernel comment = exempt).
- removal.md → vma/removal (vms_* pipeline, rollback, 2 figures; 0 arms). Mine vm_brk_flags (§951) for map/brk.
- removal-algorithm.md → vma/removal-algorithm (NULL-store, rebalance, gap update + pgtable teardown; 2 banned arms @341/386).
- munmap.md → map/munmap (syscall surface + DEEP mmu_gather/free_pgtables treatment; 0 arms). The mmu_gather depth feeds vma/removal-algorithm's physical half (boundary rule applies: munmap page keeps vms as black box).
- mmap.md → SPLIT: map/mmap (pipeline half) + map/address-space-layout (§§510-753: get_unmapped_area/vm_unmapped_area/arch_pick_mmap_layout/mmap_base); 2 banned arms @592/@1182.
- stack-growth.md → vma/stack-growth (guard gap, expand paths, unique 16-arch table; 2 arms = arch names, exempt).
- vm-operations.md → vma-ops/vm-operations (16-callback catalog + per-phase figure; 0 arms). Its fault-dispatch depth duplicates fault/ pages: keep callback-side only.
- vm-ops/amdgpu-gem.md → vma-ops/amdgpu-gem (TTM fault helpers, unplug fencing; 0 arms).
- vm-ops/hugetlb.md → vma-ops/hugetlb (5-slot ops, resv_map lifecycle; ~4 banned arms incl. figure caption).
- vm-ops/special-mapping.md → vma-ops/special-mapping (x86 vDSO installers, unique 17-arch descriptor table; 11 arms ALL arch-names = exempt).

NO-FEED pages with mining pointers: vma/fork-dup (allocation §962 + insertion §676 + flags §1033), map/brk (munmap §291, removal §951, merge §700), map/mremap (adjust §950, insertion §630, vm-operations §718, special-mapping §376), map/mprotect (merge §1067, split §878, flags §927, vm-operations §749), map/mlock (flags mlock bits, stack-growth §723), map/madvise (flags §946, split §953, traversal §784), map/mseal (fully fresh), vma-ops/generic-file (vm-operations tables, mmap §1134, overview §983), vma-ops/shmem (mmap §1165 + vm-operations refs).

UNMAPPED DEPTH (route per boundary rules, no new pages): mmu_gather/TLB-batching internals + page-table teardown (munmap.md §§314-927, removal-algorithm.md §§964-1257) → vma/removal-algorithm owns it per the boundary statement; generic maple-tree internals → bounded into the two algorithm pages; SLUB sheaves/barn → compressed into vma/slab-rcu; fault-dispatch depth in vm-operations/amdgpu → fault/ pages own it; anon_vma scatter → rmap pages own it; the three high-value enumerations (TYPESAFE cache list, 17-arch special-mapping table, 16-arch stack table) stay on their host pages.

### rmap/ + mm_struct/ + page/ + pgtable/ drafts (agent report complete)

HEADLINE: all 15 drafts symbol-EXACT at v7.0 (60+ spot-checks). The feared staleness classes did NOT materialize (drafts already use FOLIO_MAPPING_*, anon_vma_clone(dst,src,enum vma_operation)/VMA_OP_*, folio_add_anon_rmap_* naming, _mm_id machinery). ONE genuine staleness: drafts/rmap/anon-rmap-setup.md lines ~132 and ~425 still say `enum rmap_level`/`RMAP_LEVEL_PTE/PMD`, renamed at v7.0 to `enum pgtable_level`/`PGTABLE_LEVEL_*` (pgtable.h:2169-2171) — fix on reuse. Provenance comments are the single-excerpt form corpus-wide (re-verify on reuse; add interior delimiters for stitched blocks).

- anon-vma.md → rmap/anon-vma backbone + primary mine for rmap/anon-setup (prepare/clone/reuse/fork/unlink all detailed).
- anon-vma-chain.md → rmap/anon-vma-chain backbone (dual-threading, interval tree, check_anon_vma_clone state table, cleanup_partial_anon_vmas); overlaps anon-vma.md on the setup material — dedupe when both feed rmap/anon-setup.
- anon-rmap-setup.md → NAME CLASH: despite the name it is the folio-side ADD path → feeds rmap/add-remove (anon half) with rmap_t/RMAP_EXCLUSIVE flow, mapcount seeding, 12 first-mapping call sites; fix the rmap_level leftovers.
- file-rmap.md → rmap/file-rmap backbone + file half of rmap/add-remove. GAP: catalog wants hugetlb huge_pmd_share over i_mmap — draft has 1 passing mention; write that section fresh. Its "arm" hits are the ARM arch (exempt).
- folio-referenced.md → rmap/folio-referenced backbone (MGLRU look-around, VM_LOCKED bail). Reclaim-decision spillover stays out (vmscan has no page).
- rmap-walk.md → rmap/walk backbone + THE mine for rmap/pvmw (deep pvmw coverage at draft lines ~515-865) + partial mkclean. page_mapped_in_vma barely mentioned (catalog scope adds it).
- try-to-unmap.md → rmap/try-to-unmap backbone (TTU flags, TLB-batch, lazyfree) + partial try-to-migrate. 10 "arms" concentrated here incl. editorial branch-counting prose — re-verify against actual branch structure while rewording. GAP: make_device_exclusive has no section (fresh for try-to-migrate).
- mm_struct/lifecycle.md → mm-struct/lifecycle backbone (goto-ladder unwind, __mt_dup clone loop, mmput_async/mmdrop_async, init_mm BUG_ON).
- mm_struct/locking-refcount.md → cross-check corroboration for the two live B2 pages (locking + refcount); contributes scattered notes to rmap/locking.
- mm_struct/overview.md → cross-check for live overview; MINE its context section (~L493) for mm-struct/arch-context and rss/hiwater section for counters.
- page/*.md + pgtable/*.md → IGNORE as backbones (pages already written); enhancement candidates recorded below.

FRESH-OR-ASSEMBLED rmap pages: add-remove (assemble: anon-rmap-setup + file-rmap + mapcount-refcount internals), anon-setup (assemble: anon-vma + anon-vma-chain, dedupe), pvmw (mine rmap-walk + add page_mapped_in_vma), mkclean (thin feed; largely fresh: folio_mkclean L1193 + mapping_wrprotect_range L1267 + pfn_mkclean_range L1304), locking (fresh; no draft reproduces rmap.c:20-53), try-to-migrate (mine try-to-unmap sibling section + fresh make_device_exclusive). mm-struct/flags and arch-context: thin feed, mostly fresh.

### B1 enhancement backlog (draft-suggested gaps in already-written pages; revisit AFTER vma-ops)

- folio/mapping-encoding: add address_space alignment guarantee (why low bits are free), __page_check_anon_rmap validation, folio_get_anon_vma vs folio_lock_anon_vma_read RCU split contrast.
- folio/refcount-mapcount: deepen COW-reuse decision chain (wp_can_reuse_anon_folio family), folio_precise_page_mapcount (/proc), __folio_put internals.
- pgtable/x86-64-entries: PAT cache-mode 3-bit slot detail, PAGE_* named-protection constants + protection_map/vm_get_page_prot 16-entry table, set_ptes/pte_advance_pfn, fault-path PTE construction examples.
- pgtable/softleaf: migration entries carrying A/D bits in spare offset bits, migration_entry_wait blocking, explicit SWP_OFFSET_SHIFT=14 decode arithmetic, pte_swp_clear_flags.
- pgtable/alloc-locking: winner/loser race figure + pagetable_pmd_ctor THP-deposit note (minor).

### Original order (superseded, kept for reference)

Batches of 5-6 pages; after each batch, checkpoint: report pages done/remaining, run the verifier, fix, then continue. Order (review-designed, foundational → derived: encodings/counters first, container objects, tree mechanics before syscalls, syscalls before ops instances, rmap structure before fault, fault in dispatch order, rmap walkers/consumers last):

- B1: pgtable/x86-64-entries, pgtable/softleaf, pgtable/alloc-locking, folio/mapping-encoding, folio/refcount-mapcount, folio/mm-id
- B2: mm-struct/overview, flags, counters, refcount, locking
- B3: mm-struct/lifecycle, arch-context; vma/overview, flags, allocation, slab-rcu
- B4: vma/refcount-locking, maple-tree, traversal, traversal-algorithm, insertion, insertion-algorithm
- B5: vma/split, merge, merge-existing, adjust, modify-spine (one research pass over vma.c:497-1250 serves all five)
- B6: vma/removal, removal-algorithm, fork-dup, stack-growth; map/address-space-layout, map/mmap
- B7: map/munmap, brk, mremap, mprotect, mlock
- B8: map/madvise, mseal; vma-ops/vm-operations, generic-file, shmem
- B9: vma-ops/special-mapping, hugetlb, amdgpu-gem; rmap/anon-vma, anon-vma-chain
- B10: rmap/anon-setup, file-rmap, locking, add-remove; fault/vm-fault
- B11: fault/x86-64-entry, vma-lock-path, handle-mm-fault, pte-dispatch, anonymous
- B12: fault/file-dispatch, file-read, file-cow, file-shared, finish-fault
- B13: fault/wp, swap-in, numa, thp-anon, thp-wp
- B14: fault/thp-numa, hugetlb, userfaultfd, pfn-insert
- B15: gup/overview, foll-flags, slow-path, fast-path, pinning, longterm
- B16: gup/faultin, gup/folio-walk; rmap/walk, pvmw, folio-referenced, mkclean
- B17: rmap/try-to-unmap, try-to-migrate (the two heaviest rmap pages, final batch)

(6+5+6+6+5+6+5+5+5+5+5+5+5+4+6+6+2 = 87)

### Write-time rules (from review risks)

- Every line number in this plan is a hint, never a citation: re-grep/re-read the on-disk file at write time; the tree is ground truth. Known drifts already found: do_user_addr_fault is fault.c:1207, handle_page_fault :1462, DECLARE_VMA_BIT block starts mm.h:292, PG_owner_2 declared page-flags.h:105, struct pagetable_move_control is in mm/internal.h:46 (mremap.c:50 is vma_remap_struct).
- memory.c has two do_set_pmd definitions (:5407 THP, :5483 stub); finish-fault.md anchors the CONFIG_TRANSPARENT_HUGEPAGE one.
- The two maple-tree algorithm pages are bounded to paths reachable from vma_iter_store/prealloc and mas_walk/mas_find/mas_empty_area{,_rev}; lib/maple_tree.c beyond those paths is out of scope.
- amdgpu-gem.md is the only page whose research leaves mm/ (TTM: ttm_bo_vm_*); budget it as a heavy page, TTM coverage limited to what the callbacks need.
- The hugetlb divert point (memory.c:6622) must read identically in handle-mm-fault.md, fault/hugetlb.md, vma-ops/hugetlb.md.
- fault/ pages: entry-chain recap ≤ 1 short paragraph (house rule).

### Save/commit policy

Pages land only under `${CLAUDE_SKILL_DIR}/docs/mm/`. No SUMMARY.md or mkdocs.yml edits. No git commits without an explicit user go; the branching workflow stays with the user. The draft corpus and any other checkout remain untouched.
