# mm knowledge-base: curated page catalog and directory plan (rebuild)

> MIGRATED 2026-07-18 to the campaigns/ layout (SKILL.md, "The three artifacts and the two states"): this file is now the committed, execution-free campaign SPEC. Its former Status section moved to the machine-local run log `progress/vma/log.md` on the machine that ran it; execution state is derived (catalog vs `docs/`), and runs happen only as user-invoked slices under the overwrite guard. This spec predates the machine-portability rule — any absolute path remaining in it is historical record to re-derive from the local environment at dispatch time, and where its older wording conflicts with current `guidelines/`, the guidelines govern.

## Context

- Campaign short name: `vma` (renamed `mm` -> `virtual-memory` -> `vma`, both renames on 2026-07-12 by user instruction; no collision in `progress/`). Workspace: `campaigns/vma.md` (this file, the campaign file) + artifact directory `progress/vma/` (the per-page dossiers land there and nothing else). Skill root: the kernel-glossary skill checkout (sub-agent briefs carry it as an absolute path at dispatch). The rename is workspace-only: the output root stays `docs/mm/` and the subsystem-map entry stays `mm` (tag `mm`), per the Subsystem Map. The campaign name `vma` is distinct from the catalog group `docs/mm/vma/` (one of the ten groups).
- Request: `prompt.md` at the documented tree's root is the plan file of a prior, partially executed mm campaign produced by an earlier model. The user's instruction for this run: read prompt.md and plan; the prior plan is untrusted, the inventory must be REDONE from scratch against the tree, and the catalog must cover most of the user-space VMA/mmap/page-fault topics.
- The original TOPIC LIST prompt (four H3 areas: mm_struct, vm_area_struct, User Space Page Faults, Reverse mapping; numbered bullets, one blank; "This topic list is very rough. Curate new pages where you see fit.") is no longer on disk. Its bullet-to-page mapping is reconstructed from prompt.md's `[prompt N]` tags and carried forward unchanged, so the requested-vs-curated tags stay meaningful.
- Documented tree: the local Linux checkout at tag `v7.0`, commit `028ef9c96e96197026887c0f092424679298aae8` ("Linux 7.0"). semcode index: Completed at 028ef9c9 (line numbers remain hints; the on-disk tree is ground truth). Elixir carries the v7.0 tag (the frozen sample pages cite it link-by-link).
- Output root: `docs/mm/` under the skill root. mm subsystem-map entry: tag `mm`, section6_heading none.
- Prior material on disk: 10 pages under `docs/mm/vma/` (adjust, insertion, insertion-algorithm, maple-tree, merge, merge-existing, modify-spine, split, traversal, traversal-algorithm; 10,262 lines total), output of the prior campaign. They are adjudicated in the Draft reuse map section after an audit, not silently adopted.
- NOT inputs: prompt.md's inventory digests, line numbers, and status claims (hints at best; its Status section contradicts the disk, claiming pgtable/folio pages exist that do not); the frozen sample pages under `guidelines/reference/samples/` (style/structure/depth calibration only, never kernel knowledge, per the samples README); other runs under `progress/` (pagecache, reclaim, swap, writeback); the `drafts/` and `kernel-glossary-devel/` corpora named by the old plan (verified absent from disk on 2026-07-11).
- Sibling-campaign boundaries: pagecache, reclaim, swap, and writeback have their own runs under `progress/`. Pages in this campaign stop at those subsystems' API seams; the boundary rules name the seam per page (e.g. fault/swap-in stops at the swap-cache/readahead API, fault/file-read stops at the filemap/readahead API, rmap/folio-referenced stops at the vmscan handoff).

## Re-entry contract (retrofitted 2026-07-18)

Standing instructions to any executor, on any machine, cold or warm:

1. Confirm the tree: a Linux kernel checkout at tag `v7.0`, commit `028ef9c96e96` (`git describe --tags` at the tree root prints `v7.0`). A different tree voids every anchor in this spec — stop and surface it.
2. Derive campaign state: diff the 89 base rows (up to 99 if the pending P2-P4 inclusion decisions land as include) against their own output paths; the `docs/mm/` root is SHARED with other mm-area campaigns — never derive state by listing the directory. Known pre-existing state: 10 base rows already exist from a prior run (`docs/mm/vma/`, dispositioned in the Draft reuse map) and 5 rows were produced ahead of order under the 2026-07-16 PARTIAL GO amendment (map/mmap.md, fault/x86-64-entry.md, rmap/anon-vma.md, rmap/anon-vma-chain.md, fault/handle-mm-fault.md) — all 15 count as done.
3. Create or reuse the machine-local workspace `progress/vma/` (run log `log.md`, dossiers). It is never committed.
4. Execute ONLY the slice the invoker named — a batch from this spec's batch order (its recommended slicing), or an explicit page list. Given a bare "run vma" with no slice: report the derived state and ask; never pick a slice autonomously. Overwrite guard: a catalog page that already exists on disk is never overwritten silently — stop and surface it. A slice naming a pending-decision row (P2/P3/P4) whose inclusion decision is unrecorded → ask for the decision first.
5. Run the slice per SKILL.md "Modes": one writer per page, briefed per `guidelines/passes/02-write.md` with the page's catalog row, its cluster's boundary rules, and the project-specific bans and write-time cautions from this spec's Execution & verification section; then the orchestrator check per page (`guidelines/passes/03-check.md`); events go to the run log.
6. Promote anything durable — a spec claim the tree refuted, a user amendment, a settled adjudication — into this spec as a dated amendment (or surface it for the waivers files). The run log does not travel.
7. Verification: a page's pipeline ends at LINTED. Verification campaigns and the CERTIFIED state were removed from the skill on 2026-08-31; do not plan, dispatch, or stamp one.

## Scope decisions

Carried over from the prior campaign's user-confirmed set (recorded in prompt.md; carried as standing decisions, not re-litigated):

1. Two supporting construct groups beyond the four prompt areas: x86-64 page tables (PTE/PMD bit encoding, non-present/softleaf encoding, table allocation + locking) and the folio side (mapping encoding, refcount vs mapcount model).
2. Full VMA-operation syscall set beyond mmap/munmap: brk, mremap, mprotect, mlock, madvise (one page each).
3. Every catalog row tagged `[prompt]` (explicit original bullet) or `[curated]` (gap-fill).
4. x86-64 only throughout; per-page CONFIG assumptions stated where relevant.
5. GUP (get_user_pages / pin_user_pages) is its own group; fault-in-without-pages material lives there.
6. Style leadership: pages follow the template section order, caution block, self-containment, verbatim on-disk citation, Elixir linking, and every writing/diagram gate (rules 7, 7a-7r); each page's DETAILS is architected to fit its material at or above the sample-page bar (`guidelines/reference/samples/`), with no obligation to mirror any one sample's prose rhythm or diagram choices.
7. Project-specific wording ban: "arm" never describes a union case or code branch (use branch, case, side, leg); the rule-7c hedge list applies.

Phase 3 checkpoint decisions (user-answered 2026-07-11 via the four-question checkpoint):

8. P1 — the 10 existing `docs/mm/vma/` pages: REBUILD FROM SCRATCH. The user chose rebuild over both adopt options despite the clean audit. Consequences: the adopt-with-fixes verdicts and 5-item fix list in the Draft reuse map are superseded; B5/B6 are normal writing batches; writers of those 10 rows MUST NOT read the old on-disk pages (anchoring risk from the untrusted generation) — pages are overwritten at their batch slot; the audit's enhancement-backlog items E1 (config-fallback paragraph) and E2 (worked numeric examples) become writer-brief inputs for these rows.
9. P2 — proc/ observability group (maps-smaps, pagemap): INCLUDE, both pages now [curated] base rows.
10. P3 — fault/userfaultfd-api.md: INCLUDE, now a [curated] base row.
11. P4 — msync, mincore, mempolicy, secretmem, process-madvise: INCLUDE (now [curated] base rows). pkeys and shadow-stack: EXCLUDE as pages — fold back per the conditional fold-ins: pkey mechanism (pkey_alloc/free, PKRU, execute-only) returns to map/mprotect.md (boundary rule 18 lapses; mprotect.md is accepted as a heavy page); map_shadow_stack + VM_SHADOW_STACK fold across vma/flags.md (mapping side), fault/x86-64-entry.md (X86_PF_SHSTK), pgtable/x86-64-entries.md (CET saved-dirty encoding) (boundary rule 13 lapses).

FINAL CATALOG: 97 pages = 89 base + 2 (P2) + 1 (P3) + 5 (P4 accepted). Tag census: 38 [prompt], 59 [curated].

## Inventory findings (Phase 1)

(One compact digest per area, recorded verbatim when the agents return. Every line number is a hint to re-verify at write time.)

### mm_struct area (agent complete, verified on disk at 028ef9c96e96)

1. Core mm_struct field groups (include/linux/mm_types.h:1123-1381 unless noted):
- Tree/pgtable root: `mm_mt` maple_tree (VMA tree) :1140; `pgd`/`pgtables_bytes`(atomic_long_t,CONFIG_MMU)/`map_count` :1150,1177,1179.
- Refcounts: `mm_count` atomic_t :1137 (own cacheline); `mm_users` atomic_t :1171.
- RSS/VM counters: `rss_stat[NR_MM_COUNTERS]` struct percpu_counter :1266; `hiwater_rss/hiwater_vm/total_vm/locked_vm/data_vm/exec_vm/stack_vm` unsigned long, `pinned_vm` atomic64_t, `def_flags` vm_flags_t :1235-1244.
- Layout: `mmap_base/mmap_legacy_base(+_compat_* under CONFIG_HAVE_ARCH_COMPAT_MMAP_BASES)/task_size` :1142-1149; `start_code..env_end` under `arg_lock` spinlock_t + `saved_auxv[AT_VECTOR_SIZE]` :1253-1259.
- Locks/seq: `mmap_lock` rw_semaphore :1196; `page_table_lock` spinlock_t :1181; `write_protect_seq` seqcount_t :1251; `vma_writer_wait` rcuwait + `mm_lock_seq` seqcount_t (CONFIG_PER_VMA_LOCK) :1204,1222.
- Oddballs: `mm_cid` struct mm_mm_cid :1174 (type in include/linux/rseq_types.h:171); futex block `futex_hash_lock/futex_phash/futex_phash_new/futex_batches/futex_rcu/futex_atomic/futex_ref` (CONFIG_FUTEX_PRIVATE_HASH) :1224-1233; `membarrier_state` atomic_t :1159; `mm_id` mm_id_t (CONFIG_MM_ID) :1372; `lru_gen{list,bitmap,memcg}` :1356-1369; `ksm_merging_pages/ksm_rmap_items/ksm_zero_pages` :1343-1353; `tlb_flush_pending/tlb_flush_batched` :1321,1324.
- Flags/context: `flags` mm_flags_t :1273 (bitmap, see 5a); `context` mm_context_t :1271; trailing `flexible_array[]` (dynamic mm_cpumask + mm_cid percpu region) :1380.
- x86-64 `mm_context_t` (arch/x86/include/asm/mmu.h:25-84): `ctx_id` u64 :30; `tlb_gen` atomic64_t :40; `next_trim_cpumask` :42; `ldt_usr_sem`/`ldt` (CONFIG_MODIFY_LDT_SYSCALL) :45-46; `flags` unsigned long :49 (MM_CONTEXT_* bits 0-4, :12-20); `lam_cr3_mask`/`untag_mask` (CONFIG_ADDRESS_MASKING) :53,56; `lock` mutex :59; `vdso`/`vdso_image` :60-61; `perf_rdpmc_allowed` :63; `pkey_allocation_map`/`execute_only_pkey` (CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS) :69-70; `global_asid`/`asid_transition` (CONFIG_BROADCAST_TLB_FLUSH) :79,82.

2. API families:
- mmap_lock core (include/linux/mmap_lock.h): `mmap_read_lock` :589, `_killable` :596, `mmap_read_trylock` :606 (only read has trylock — no mmap_write_trylock anywhere in tree), `mmap_read_unlock`(_non_owner) :616,625, `mmap_write_lock`(_nested) :533,541, `_killable` :549, `mmap_write_unlock` :575, `mmap_write_downgrade` :582, `mmap_assert_locked/write_locked` :69,74, `mmap_lock_is_contended` :631, `DEFINE_GUARD(mmap_read_lock,...)` :622.
- Per-VMA lock-seq/writer machinery: `mm_lock_seqcount_init/begin/end` mmap_lock.h:118-132; `mmap_lock_speculate_try_begin/retry` :134-148; `vma_start_write`/`_killable` :298-326 calling `__vma_start_write` (mm/mmap_lock.c:139); `vma_end_write_all` mmap_lock.h:569; `vma_refcount_put`/`vma_mark_attached`/`vma_mark_detached` :210,443,452, waking `mm->vma_writer_wait`.
- mm flag helpers: `mm_flags_test/_and_set/_and_clear/set/clear/clear_all` include/linux/mm.h:877-905 (ACCESS_PRIVATE-gated); internal word ops `__mm_flags_get_word/_bitmap/_overwrite_word/_set_mask_bits_word` mm_types.h:1384-1411.
- RSS/hiwater: `get_mm_counter`/`_sum`, `add/inc/dec_mm_counter` mm.h:3063-3094 (percpu_counter_* backed); `get_mm_rss`/`_sum`, `get/update/reset/setmax_mm_hiwater_rss`, `get/update_mm_hiwater_vm` mm.h:3111-3161.
- Refcounting: `mmget`/`mmget_not_zero` sched/mm.h:131-139, `mmput` fork.c:1193 / `mmput_async` fork.c:1211 vs `mmgrab`/`mmgrab_lazy_tlb` sched/mm.h:35,88, `mmdrop`/`mmdrop_lazy_tlb`(_sched) sched/mm.h:47,94,107, `__mmdrop` fork.c:718.
- kthread borrowing: `kthread_use_mm` kernel/kthread.c:1615, `kthread_unuse_mm` :1662 (mmgrab/mmdrop_lazy_tlb pair + switch_mm_irqs_off/enter_lazy_tlb).
- `mm_take_all_locks`/`mm_drop_all_locks` mm/vma.c:2197,2293 (declared mm.h:3842-3843) — locks all i_mmap/anon_vma rwsems + attached VMAs under caller-held mmap write lock, serialized by `mm_all_locks_mutex`.

3. Lifecycle/locking chain:
- `mm_alloc` fork.c:1154 -> `mm_init` fork.c:1072 (mm_users=1, mm_count=1, mm_flags_clear_all, futex_mm_init, mm_alloc_pgd, mm_alloc_id, init_new_context, mm_alloc_cid, percpu_counter_init_many(rss_stat)).
- fork: `copy_mm` fork.c:1556 — CLONE_VM: `mmget(oldmm)`; else `dup_mm` fork.c:1515 (mm_init + `dup_mmap` mm/mmap.c:1732, write-locks oldmm then new mm nested SINGLE_DEPTH_NESTING, `__mt_dup`s maple tree, `arch_dup_mmap`).
- `mmput` fork.c:1193: `atomic_dec_and_test(&mm->mm_users)` -> `__mmput` fork.c:1167 (uprobe/aio/ksm/khugepaged teardown, `exit_mmap`, `set_mm_exe_file(NULL)`, mmlist removal, `mmdrop`).
- `exit_mmap` mm/mmap.c:1275: mmu_notifier_release, arch_exit_mmap, unmap_vmas/free_pgtables under `mmap_write_lock`, sets `MMF_OOM_SKIP` mid-teardown, `__mt_destroy`, `vm_unacct_memory`.
- `mmdrop`->`__mmdrop` fork.c:718 (mm_count->0): `cleanup_lazy_tlbs`, `mm_free_pgd`, `mm_free_id`, `destroy_context`, notifier/user_ns/pasid/cid teardown, `percpu_counter_destroy_many(rss_stat)`, `free_mm`.
- Contract (mm_types.h:1131-1171 doc comments): `mm_users`=real address-space users (mmget/mmget_not_zero/mmput), hitting 0 drops one `mm_count` ref; `mm_count`=mm_struct pins incl. lazy-TLB borrowers (mmgrab/mmdrop), hitting 0 frees the struct.
- Lazy-TLB/active_mm on x86-64: kthread with `tsk->mm==NULL` borrows `tsk->active_mm`; `mmgrab_lazy_tlb`/`mmdrop_lazy_tlb`(_sched) sched/mm.h:87-113 gated by CONFIG_MMU_LAZY_TLB_REFCOUNT; `enter_lazy_tlb`/`switch_mm_irqs_off`/`activate_mm`/`deactivate_mm` arch/x86/include/asm/mmu_context.h:139,184,188,195; IPI `cleanup_lazy_tlbs`/`do_shoot_lazy_tlb` fork.c:652-711 for CONFIG_MMU_LAZY_TLB_SHOOTDOWN; documented Documentation/mm/active_mm.rst:5-9,61-71.

4. Hard-coded limits:
- `NR_MM_COUNTERS`=4 mm_types_task.h:26-32. `AT_VECTOR_SIZE_BASE`=24 include/linux/auxvec.h:7; x86 `AT_VECTOR_SIZE_ARCH`=3(IA32_EMULATION||!X86_64)/2 arch/x86/include/uapi/asm/auxvec.h:15,17 -> `saved_auxv[]`=54 or 56 words, mm_types.h:31,1259.
- `NUM_MM_FLAG_BITS`=64 mm_types.h:1116; MMF_* bits 0-30 (highest `MMF_VM_MERGE_ANY`) :1860-1917; `MMF_DUMPABLE_BITS`=2, `MMF_DUMP_FILTER_BITS`=9 :1860,1874.
- `DEFAULT_MAX_MAP_COUNT`=USHRT_MAX-`MAPCOUNT_ELF_CORE_MARGIN`(5)=65530, bounds `map_count` via `sysctl_max_map_count` mm.h:208-209, mm/mmap.c:378.
- `MM_CID_STATIC_SIZE`=2*sizeof(cpumask_t) mm_types.h:1566; `mm_id_t`(64-bit)=unsigned int, `MM_ID_BITS`=31, `MM_ID_MAX`=0x7FFFFFFF, ida range [`MM_ID_MIN`=1,MM_ID_MAX] :320-346, fork.c:593-599.
- `init_mm.mm_users`=2 / `mm_count`=1 vs fresh `mm_init()` giving `mm_users=mm_count=1`, mm/init-mm.c:35-36, fork.c:1077-1078.
- x86 `mm_context_t.flags` bits `MM_CONTEXT_UPROBE_IA32`=0..`MM_CONTEXT_NOTRACK`=4 mmu.h:12-20; default `pkey_allocation_map`=0x1, `execute_only_pkey`=-1, mmu_context.h:162,164.
- `mm_cachep` size = sizeof(mm_struct)+cpumask_size()+mm_cid_size(), SLAB_HWCACHE_ALIGN|SLAB_PANIC|SLAB_ACCOUNT, fork.c:3011-3017.
- VMA writer-exclusion: `VM_REFCNT_EXCLUDE_READERS_BIT`=30, `VM_REFCNT_LIMIT`=2^30-1, mm_types.h:764-766 (couples per-VMA refcount to mm_lock_seq protocol).

5. Version-specific checks (confirmed on-disk at 028ef9c96e96):
(a) CONFIRMED: `flags` is `mm_flags_t`={DECLARE_BITMAP(__mm_flags,64)}`__private` mm_types.h:1116-1119,1273, comment mandates `mm_flags_*` helpers mm.h:877-905 — not a plain unsigned long.
(b) CONFIRMED: `rss_stat` is `struct percpu_counter rss_stat[NR_MM_COUNTERS]` mm_types.h:1266, read via `percpu_counter_read_positive`/`_sum_positive`; no per-thread rss-cache batching left (`sync_mm_rss` absent from tree) mm.h:3063-3094.
(c) CONFIRMED: `seqcount_t mm_lock_seq` + `struct rcuwait vma_writer_wait` under CONFIG_PER_VMA_LOCK mm_types.h:1204,1222, driving `__vma_start_write`/writer-wait in mm/mmap_lock.c.
(d) CONFIRMED: `struct mm_mm_cid mm_cid` (mm_types.h:1174, type in rseq_types.h:171) and full futex-private-hash block (`futex_phash` etc., mm_types.h:1224-1233) both present.
(e) CONFIRMED: x86-64 `mm_context_t` has `ctx_id`, `tlb_gen`, `ldt_usr_sem`/`ldt`, `pkey_allocation_map`/`execute_only_pkey`, `lam_cr3_mask`/`untag_mask` — mmu.h:25-84; also carries newer `global_asid`/`asid_transition` (INVLPGB broadcast-flush) not in the prompt's list.
- Extra: `mm_cid` is redesigned vs older simple embedded-cidmask docs — now a dedicated `struct mm_mm_cid` (rseq_types.h:144-194) with a dynamically-allocated per-CPU `pcpu` block, `irq_work`/`work_struct` for affinity-mode switching, and hlist `user_list`.

6. Suggested extra page topics (beyond struct/locking/refcounting):
- RSS/VM accounting internals (percpu_counter rss_stat, hiwater family, `check_mm` underflow WARN) — mm.h:3063-3161, fork.c:622-647.
- `mm_flags_t`/MMF_* bitmap semantics incl. dump filter — mm_types.h:1113-1119,1857-1917; mm.h:877-905.
- Per-VMA lock-seq writer-exclusion protocol (`mm_lock_seq`, `vma_writer_wait`, `__vma_start_write`) — mmap_lock.h, mm/mmap_lock.c.
- `mm_cid` scheduler-ID subsystem (per-CPU vs per-task mode, affinity-triggered irq_work) — rseq_types.h:125-194, kernel/sched/core.c:10462+.
- x86-64 `mm_context_t`/TLB machinery: ASID/`tlb_gen`, global-ASID INVLPGB path, LAM tagging, LDT, protection keys — mmu.h, mmu_context.h.
- Lazy-TLB `active_mm` borrowing + `kthread_use_mm`/`unuse_mm` + shootdown vs refcount modes — sched/mm.h:87-113, kthread.c:1615-1689, Documentation/mm/active_mm.rst.
- `mm_take_all_locks`/`mm_drop_all_locks` whole-address-space lock ordering (mmu-notifier registration) — mm/vma.c:2160-2293.
- Futex private-hash lifecycle embedded in mm (`futex_phash`/`futex_ref`/RCU teardown) — mm_types.h:1224-1233, fork.c:1113,1145,1186.
- `mm_id`/mm_struct allocation sizing: ida-allocated `mm_id`, flexible trailing cpumask+mm_cid array — fork.c:593-620,3011-3017; mm_types.h:300-346,1417-1435.
### vma-object area (agent complete, verified on disk at 028ef9c96e96)

1. Core structs
- `struct vm_area_struct` — include/linux/mm_types.h:913. Groups: range/freeptr union `{vm_start,vm_end}` vs `freeptr_t vm_freeptr` (SLAB_TYPESAFE_BY_RCU) :917-923; flags union `const vm_flags_t vm_flags`/`vma_flags_t flags` :939-940; per-VMA-lock `vm_lock_seq` :958, `refcount_t vm_refcnt ____cacheline_aligned_in_smp` :1030, `vmlock_dep_map` (CONFIG_DEBUG_LOCK_ALLOC) :1032; file/anon `anon_vma_chain`/`anon_vma` :966-968, `vm_ops` :971, `vm_pgoff`/`vm_file`/`vm_private_data` :974-977; shared/interval-tree anon struct `{rb_node rb; rb_subtree_last;} shared` :1040-1043; oddballs `anon_name` :1050 (CONFIG_ANON_VMA_NAME), `vm_policy` :986 (CONFIG_NUMA), `numab_state` :989 (CONFIG_NUMA_BALANCING), `vm_userfaultfd_ctx` :1052, `pfnmap_track_ctx` :1054 (`__HAVE_PFNMAP_TRACKING`).
- `struct vma_iterator { struct ma_state mas; }` — mm_types.h:1497; built via `VMA_ITERATOR()` macro :1501.
- Merge descriptor `struct vma_merge_struct` — mm/vma.h:69 (prev/middle/next/target, range/pgoff/vm_flags, anon_vma/policy/uffd_ctx/anon_name, internal `__adjust_*`/`__remove_*` bits); init'd via `VMG_STATE`/`VMG_VMA_STATE` (mm/vma.h:236).
- Munmap descriptors: `struct vma_munmap_struct` — mm/vma.h:34 (gather-phase: prev/next/uf/range/vma_count/accounting); separate `struct unmap_desc` — mm/vma.h:158 (pagetable-teardown only: mas/first/pg_start/pg_end/vma_start/vma_end/tree_end/tree_reset/mm_wr_locked), consumed by `unmap_region()` (mm/vma.c:478).
- Adjunct descriptors: `struct vma_prepare` (mm/vma.h:13, prepare/complete lock+link bookkeeping); `struct mmap_state` (mm/vma.c:10, embeds a `vma_munmap_struct`+detach maple tree, drives `mmap_region()`).

2. API families
- Flags decl+mutate: `vma_flag_t` (`int __bitwise`) bit-ids via `DECLARE_VMA_BIT`/`_ALIAS` enum (mm.h:290-397, ~50 bits incl. aliased arch bits, SEALED=42); storage `vma_flags_t`=`DECLARE_BITMAP(NUM_VMA_FLAG_BITS=BITS_PER_LONG)` (mm_types.h:866-869). Mutators `vm_flags_{init,reset,reset_once,set,clear,mod}()` (mm.h:919-992) -> `vma_flags_{overwrite_word,set_word,clear_word}()` (mm_types.h:1070-1103); readers `vma_flags_test[_all]()` macros (mm.h:1080,1098). Direct assignment blocked: struct exposes only `const vm_flags_t vm_flags` aliasing real `vma_flags_t flags` (mm_types.h:939-940).
- Allocation: `vm_area_alloc/vm_area_dup/vm_area_free` (mm/vma_init.c:28,121,144); `vma_state_init()` creates `vm_area_cachep = kmem_cache_create("vm_area_struct", sizeof(vm_area_struct), &args, SLAB_HWCACHE_ALIGN|SLAB_PANIC|SLAB_TYPESAFE_BY_RCU|SLAB_ACCOUNT)` with `args={.use_freeptr_offset=true,.freeptr_offset=offsetof(vm_freeptr),.sheaf_capacity=32}` (mm/vma_init.c:14-26).
- Per-VMA-lock: readers `vma_start_read()` (mmap_lock.c:212, internal, backs RCU lookups), `vma_start_read_locked[_nested]()` (mmap_lock.h:238,257), release `vma_end_read()`->`vma_refcount_put()` (mmap_lock.h:262,210); writers `vma_start_write()`/`_killable()` (mmap_lock.h:298,320)->`__vma_start_write()` (mmap_lock.c:139, no per-VMA release — bulk-released mm-wide by `vma_end_write_all()` mmap_lock.h:569 at unlock/downgrade); attach/detach `vma_mark_attached()`/`vma_mark_detached()` (mmap_lock.h:443,452)->`__vma_exclude_readers_for_detach()` (mmap_lock.c:172).
- Lookup: `find_vma`/`find_vma_prev`/`find_vma_intersection`/`vma_lookup` (mm/mmap.c:902,925,883; mm.h:3957); `vma_find/vma_next/vma_prev` over `mas_find/mas_next/mas_prev` (mm.h:1312-1336); `for_each_vma`/`for_each_vma_range` (mm.h:1378,1382); lockless `lock_vma_under_rcu()` (mmap_lock.c:296) and iterator-based `lock_next_vma()` (mmap_lock.c:369, +mmap-lock fallback `lock_next_vma_under_mmap_lock` :344).
- Insertion: `vma_link()` (mm/vma.c:1824: VMA_ITERATOR+prealloc+`vma_iter_store_new`+`vma_link_file`+map_count++) underlies `insert_vm_struct()` (mm/vma.c:3273); internal mmap path builds `struct vm_area_desc` (mm_types.h:880) via `mmap_state` in `__mmap_setup`/`__mmap_new_vma` (mm/vma.c:2392,2506), storing directly with `vma_iter_store_new` (mm/vma.h:610).
- Removal: `do_vmi_munmap()`/`do_vmi_align_munmap()` (mm/vma.c:1611,1564) drive `vms_gather_munmap_vmas()`->`vms_complete_munmap_vmas()` (mm/vma.c:1379,1311), or `vms_abort_munmap_vmas()` (mm/vma.c:2340) on error; `unmap_region()` (mm/vma.c:478)->`unmap_vmas()`/`free_pgtables()` (declared mm/internal.h:201,515) over an `mmu_gather`.
- Split: `__split_vma()`/`split_vma()` (mm/vma.c:497,590; bypasses `sysctl_max_map_count`, comment :492).
- Merge: `vma_merge_new_range()` (mm/vma.c:1046) and `vma_merge_existing_range()` (mm/vma.c:805) both funnel into commit helper `commit_merge()` (mm/vma.c:728).
- Expand/shrink/copy/relocate: `vma_expand()` (mm/vma.c:1151), `vma_shrink()` (mm/vma.c:1228), `copy_vma()` (mm/vma.c:1844, mremap-move), `relocate_vma_down()` (mm/vma_exec.c:19, exec-only).
- Modification spine: `vma_prepare()`/`vma_complete()` (mm/vma.c:288,335) wrap `struct vma_prepare`; core `vma_modify()` (mm/vma.c:1649) wrapped by `vma_modify_flags/_name/_policy/_flags_uffd` (mm/vma.c:1689,1714,1726,1738; decl mm/vma.h:355,379,403,430).
- Fork: `dup_mmap()` (mm/mmap.c:1732) write-locks both mms, `__mt_dup()` whole-tree-clones `mm_mt` (mm/mmap.c:1758), then `for_each_vma()` loop hooks: `vm_area_dup`, `vma_dup_policy`, `dup_userfaultfd`, `anon_vma_fork`, `hugetlb_dup_vma_private`, `vma_iter_bulk_store()` (mm/mmap.c:1787-1817).
- Stack growth: `expand_upwards()`/`expand_downwards()` (mm/vma.c:3090,3176) enforce `stack_guard_gap`; exec-time `create_init_stack_vma()` (mm/vma_exec.c:107) places a temporary max-address VMA later moved by `relocate_vma_down()`.

3. Lifecycle and locking
- States encoded in `vm_refcnt`: 0=detached, 1=attached unlocked-or-write-locked, >1=read-locked (mm_types.h:998-1023); `VM_REFCNT_EXCLUDE_READERS_BIT=30`/`_FLAG`/`VM_REFCNT_LIMIT` (mm_types.h:764-766) mark writer-exclusion in progress.
- `SLAB_TYPESAFE_BY_RCU` (set vma_init.c:24) lets `rcu_read_lock()` readers dereference a possibly-reused VMA safely; only fields marked "Unstable RCU readers are allowed" (`vm_mm`, `vm_refcnt`) are pre-validation-safe (mm_types.h:907,927); `vma_start_read()`/`lock_vma_under_rcu()` re-check `vma->vm_mm==mm` and `vm_lock_seq` post-refcount (mmap_lock.c:248,262).
- Tree-shape writes (`mm->mm_mt`, mm_types.h:1140) are single-writer, serialized by `mmap_lock` write mode; per-field writes require `vma_start_write()` (needs mmap write lock, asserted by `vma_assert_write_locked` mmap_lock.h:332); `anon_vma_chain`/`anon_vma` "Serialized by mmap_lock & page_table_lock" (mm_types.h:966-968 comment).

4. Hard-coded limits
- `DEFAULT_MAX_MAP_COUNT = USHRT_MAX - MAPCOUNT_ELF_CORE_MARGIN(5)` = 65530; runtime `sysctl_max_map_count` (mm.h:208-211).
- `stack_guard_gap = 256UL<<PAGE_SHIFT` (1MiB on x86-64), overridable via `stack_guard_gap=` cmdline (mm/mmap.c:939-952).
- Maple tree (64-bit): `MAPLE_NODE_SLOTS=31`, `MAPLE_RANGE64_SLOTS=16`, `MAPLE_ARANGE64_SLOTS=10`, `MAPLE_ALLOC_SLOTS=30`, 256B node (maple_tree.h:27-32).
- `vm_area_cachep` `sheaf_capacity=32` (vma_init.c:19); `unlink_vma_file_batch.vmas[8]` fixed batch (mm/vma.h:28); `NUM_VMA_FLAG_BITS=BITS_PER_LONG`(64) per bitmap word before spillover (mm_types.h:866).

5. Version-specific facts (all CONFIRMED on disk)
- (a) `vma_flags_t` is `DECLARE_BITMAP` wrapper (mm_types.h:867-869) union'd with `const vm_flags_t vm_flags` view (:939-940); `DECLARE_VMA_BIT`/`_ALIAS` enum (mm.h:292-397).
- (b) `vm_refcnt` `refcount_t` field (mm_types.h:1030) with `VM_REFCNT_EXCLUDE_READERS_BIT=30` (mm_types.h:764).
- (c) `kmem_cache_args{use_freeptr_offset=true, freeptr_offset=offsetof(vm_freeptr), sheaf_capacity=32}`, `vm_freeptr` union member (mm_types.h:922), `SLAB_TYPESAFE_BY_RCU` (vma_init.c:16-25).
- (d) `vma_merge_struct` (mm/vma.h:69) threaded through `vma_merge_new_range`/`_existing_range`/`commit_merge`.
- (e) `vma_munmap_struct` (mm/vma.h:34) + `vms_gather/complete/abort_munmap_vmas` (mm/vma.c:1379,1311,2340) is distinct from `struct unmap_desc` (mm/vma.h:158), used only for `unmap_region`'s pagetable teardown.
- (f) `dup_mmap()` in mm/mmap.c:1732 uses `__mt_dup()` (mm/mmap.c:1758) + `vma_iter_bulk_store()` (mm/mmap.c:1817) bulk insert.
- (g) `anon_name` (mm_types.h:1050, CONFIG_ANON_VMA_NAME) and `pfnmap_track_ctx` (mm_types.h:1054, `__HAVE_PFNMAP_TRACKING`) both present.
- (h) `VM_SEALED` bit 42 (mm.h:358); mm/mseal.c implements `do_mseal()`/`mseal_apply()`; gate helper `vma_is_sealed()` at mm/vma.h:662 (CONFIG_64BIT only, else stub `false`).

6. Suggested missing page topics (not implied by the given bullet list)
1. Descriptor/state-object pattern threading multi-step ops (`vma_merge_struct`, `vma_munmap_struct`, `unmap_desc`, `mmap_state`, `vma_prepare`) — mm/vma.h:34,69,158; mm/vma.c:10,13.
2. mmap_lock<->per-VMA-lock interplay/speculation: `mm_lock_seqcount_begin/end`, `mmap_lock_speculate_try_begin/retry`, bulk-invalidate `vma_end_write_all` — mmap_lock.h:118-149,569.
3. Address-space gap search (`get_unmapped_area`/`vm_unmapped_area`/`unmapped_area[_topdown]`/`vma_iter_area_lowest/highest` over `mas_empty_area[_rev]`) — mm/vma.c:2947,3004; mm/vma.h:550,556.
4. mseal()/VM_SEALED as its own page (whole mm/mseal.c syscall + `vma_is_sealed` gate cutting across mmap/mprotect/munmap/mremap).
5. `dup_mmap()`'s whole-tree clone + per-VMA fixup loop deserves separate treatment from generic "allocation" — mm/mmap.c:1732.
6. exec-time stack construction/relocation (`create_init_stack_vma`+`relocate_vma_down`+`PAGETABLE_MOVE`) as a special-cased single-VMA path outside ordinary split/merge/adjust — mm/vma_exec.c:19,107.
7. `vm_area_desc`/`.mmap_prepare` driver contract — mutable pre-link descriptor distinct from `vm_operations_struct` and from "insertion" — mm_types.h:880; mm/vma.c:2729.
### map-syscalls + user-space surface area (agent complete, verified on disk at 028ef9c96e96)

1. Syscall entry anchors
- mmap: arch/x86/kernel/sys_x86_64.c:82 SYSCALL_DEFINE6(mmap) -> ksys_mmap_pgoff mm/mmap.c:567 -> vm_mmap_pgoff mm/util.c:565 -> do_mmap mm/mmap.c:335 -> mmap_region mm/vma.c:2818 (-> __mmap_region mm/vma.c:2720).
- munmap: mm/mmap.c:1075 -> __vm_munmap mm/vma.c:3251 -> do_vmi_munmap mm/vma.c:1611 -> do_vmi_align_munmap mm/vma.c:1564.
- brk: mm/mmap.c:116 SYSCALL_DEFINE1(brk), self-contained -> grow: do_brk_flags mm/vma.c:2866; shrink: do_vmi_align_munmap mm/vma.c:1564.
- mremap: mm/mremap.c:1965 -> do_mremap mm/mremap.c:1915 -> mremap_to mm/mremap.c:1367 / mremap_at mm/mremap.c:1554 -> move_vma mm/mremap.c:1270.
- mprotect: mm/mprotect.c:948 -> do_mprotect_pkey mm/mprotect.c:801 -> mprotect_fixup mm/mprotect.c:695. pkey_mprotect: mm/mprotect.c:956 (same do_mprotect_pkey, pkey!=-1). pkey_alloc/pkey_free: mm/mprotect.c:962/992 -> mm_pkey_alloc/free + arch_set_user_pkey_access.
- mlock/mlock2: mm/mlock.c:659/664 -> do_mlock mm/mlock.c:611 -> apply_vma_lock_flags mm/mlock.c:514 -> __mm_populate mm/gup.c:1925. munlock: mm/mlock.c:677 -> apply_vma_lock_flags. mlockall/munlockall: mm/mlock.c:745/774 -> apply_mlockall_flags mm/mlock.c:722 -> mlock_fixup (per VMA).
- madvise: mm/madvise.c:2035 -> do_madvise mm/madvise.c:2013 -> madvise_do_behavior -> madvise_vma_behavior mm/madvise.c:1345. process_madvise: mm/madvise.c:2107 -> vector_madvise mm/madvise.c:2042 -> same madvise_do_behavior; requires PTRACE_MODE_READ_FSCREDS + CAP_SYS_NICE for remote mm.
- mseal: mm/mseal.c:187 -> do_mseal mm/mseal.c:139 -> range_contains_unmapped mm/mseal.c:39 -> mseal_apply mm/mseal.c:55.
- msync: mm/msync.c:32 SYSCALL_DEFINE3, self-contained (per-VMA vfs_fsync_range on dirty file ranges).
- mincore: mm/mincore.c:292 -> do_mincore mm/mincore.c -> walk_page_range w/ mincore_walk_ops.
- remap_file_pages: mm/mmap.c:1085, deprecated emulation (pr_warn_once), no longer true nonlinear mapping.
- mbind: mm/mempolicy.c:1827 -> do_mbind mm/mempolicy.c:1486 (invokes migrate_pages internally for MPOL_MF_MOVE*). set_mempolicy: mm/mempolicy.c:1854 -> do_set_mempolicy mm/mempolicy.c:1067 (task policy, not VMA). set_mempolicy_home_node: mm/mempolicy.c:1760, per-VMA -> mbind_range mm/mempolicy.c:1039. get_mempolicy: mm/mempolicy.c:1983. Adjacent-but-page-migration: move_pages SYSCALL_DEFINE6 mm/migrate.c:2601, migrate_pages SYSCALL_DEFINE4 mm/mempolicy.c:1946 (physical placement, not VMA policy).
- map_shadow_stack: arch/x86/kernel/shstk.c:546 -> alloc_shstk shstk.c:100 -> do_mmap shstk.c:111.
- memfd_create: mm/memfd.c:505 -> memfd_alloc_file. memfd_secret: mm/secretmem.c:224 -> secretmem_file_create.
- shmat: ipc/shm.c:1693 -> do_shmat -> do_mmap ipc/shm.c:1662, installs shm_vm_ops ipc/shm.c:683 over the file's vma.
- MAP_POPULATE/MAP_LOCKED: do_mmap sets *populate=len (mm/mmap.c:560-563) after can_do_mlock/mlock_future_ok gate (mmap.c:401,420); actual fault-in via mm_populate()->__mm_populate() mm/gup.c:1925, called from vm_mmap_pgoff mm/util.c:586.
- MAP_HUGETLB: handled pre-do_mmap in ksys_mmap_pgoff mm/mmap.c:567-604 (hstate_sizelog + hugetlb_file_setup for anon, len ALIGN for file-backed); reservation later in hugetlbfs_file_mmap_prepare fs/hugetlbfs/inode.c:105 -> hugetlb_reserve_pages :160.

2. Address-space layout (x86-64)
- arch_pick_mmap_layout: arch/x86/mm/mmap.c:122; legacy-vs-topdown: mmap_is_legacy() mmap.c:62 (ADDR_COMPAT_LAYOUT personality bit or sysctl_legacy_va_layout).
- mmap_base randomization: arch_rnd() mmap.c:70 (gated on PF_RANDOMIZE), mmap_base() mmap.c:82 (stack-gap-based topdown base), mmap_legacy_base() mmap.c:101; get_mmap_base() mmap.c:146.
- get_unmapped_area dispatch: __get_unmapped_area mm/mmap.c:812 — file hook file->f_op->get_unmapped_area (mmap.c:828), else shmem_get_unmapped_area for anon MAP_SHARED (mmap.c:835), else THP hook thp_get_unmapped_area_vmflags mm/huge_memory.c:1234 (anon, no hint, PMD-aligned len), else mm_get_unmapped_area_vmflags mmap.c:801 -> arch_get_unmapped_area/_topdown (x86 overrides: arch/x86/kernel/sys_x86_64.c:127/167).
- Gap-search primitive: vm_unmapped_area() mm/mmap.c:664 (VM_UNMAPPED_AREA_TOPDOWN flag drives direction).
- TASK_SIZE/LA57/DEFAULT_MAP_WINDOW: DEFAULT_MAP_WINDOW=(1<<47)-PAGE_SIZE fixed (arch/x86/include/asm/page_64_types.h:54); TASK_SIZE_MAX=task_size_max() page_64_types.h:53 -> page_64.h:138 (ALTERNATIVE: (1<<47)-PAGE_SIZE, or (1<<56)-PAGE_SIZE if X86_FEATURE_LA57); hint addr>DEFAULT_MAP_WINDOW required to get full 56-bit window (sys_x86_64.c:111-115 find_start_end, mmap_address_hint_valid arch/x86/mm/mmap.c:197).

3. Accounting/limits
- Overcommit: __vm_enough_memory mm/util.c:930 (via security_vm_enough_memory_mm security/security.c:710); sysctl_overcommit_memory default OVERCOMMIT_GUESS=0 (mm/util.c:752; modes 0/1/2 include/uapi/linux/mman.h:13-15); vm_commit_limit() mm/util.c:875 uses sysctl_overcommit_ratio default 50 (util.c:753) or sysctl_overcommit_kbytes.
- may_expand_vm mm/mmap.c:1335: RLIMIT_AS check mmap.c:1337; RLIMIT_DATA check mmap.c:1341 (+ check_data_rlimit mmap.c:150 for brk).
- RLIMIT_MEMLOCK: can_do_mlock mm/mlock.c:40; lock_limit checks mlock.c:626(mlock),757(mlockall),798(user_shm_lock); locked_vm include/linux/mm_types.h:1239 (mlock.c:495,633) vs pinned_vm mm_types.h:1240 (separate longterm-GUP pin counter).
- VM_ACCOUNT/security hooks: charge at mmap_region mm/vma.c:2429-2439 (security_vm_enough_memory_mm), brk growth vma.c:2875-2883, stack expand vma.c:3079, uncharge on unmap vma.c:3281-3303; security_mmap_file mm/util.c:575 & mm/mmap.c:1142; security_mmap_addr mmap.c:862.
- max_map_count: default DEFAULT_MAX_MAP_COUNT=USHRT_MAX-margin (include/linux/mm.h:209); gates mm/mmap.c:378(mmap), vma.c:593(__split_vma), vma.c:1397(munmap split), vma.c:2880(brk), mremap.c:1047/1820.
- mlock_future_ok mm/mmap.c:229, used at mmap.c:420(mmap), mremap.c:1743(expand), vma.c:3066(stack grow), mm/secretmem.c:129(secretmem).

4. vm_operations_struct census
- generic_file_vm_ops mm/filemap.c:3982 — fault, map_pages, page_mkwrite.
- shmem_vm_ops mm/shmem.c:5309 — fault, map_pages, set_policy/get_policy (CONFIG_NUMA); shmem_anon_vm_ops mm/shmem.c:5318 — same, used for MAP_SHARED anon (shmem_zero_setup).
- hugetlb_vm_ops mm/hugetlb.c:4828 — fault, open, close, may_split, pagesize.
- shm_vm_ops ipc/shm.c:683 — open, close, fault, may_split, pagesize, set_policy/get_policy; overlays hugetlb/shmem vm_ops for SysV shm segments.
- special_mapping_vmops mm/mmap.c:1416 — close, fault, mremap, name, may_split, access=NULL; generic backing for vdso/vvar via __install_special_mapping.
- secretmem_vm_ops mm/secretmem.c:111 — fault only.
- amdgpu_gem_vm_ops drivers/gpu/drm/amd/amdgpu/amdgpu_gem.c:148 — fault, open(ttm_bo_vm_open), close(ttm_bo_vm_close), access(ttm_bo_vm_access).
- vma_dummy_vm_ops mm/init-mm.c:20 — empty stub, assigned as placeholder (mm/internal.h:177,196) before real vm_ops is set.

5. Version-specific facts
- (a) CONFIRMED: mmap_prepare/vm_area_desc remodel exists. struct vm_area_desc include/linux/mm_types.h:880; dispatch in __mmap_region mm/vma.c:2720/2726 -> call_mmap_prepare vma.c:2638 -> vfs_mmap_prepare include/linux/fs.h:2073 -> f_op->mmap_prepare(). Adopted by shmem (shmem.c:2959,5226), hugetlbfs (fs/hugetlbfs/inode.c:105,1241), generic_file_mmap_prepare mm/filemap.c:4001; legacy f_op->mmap still parallel-supported (vma.c:2465) via compat shim mm/util.c:1141-1193.
- (b) CONFIRMED: mseal exists (mm/mseal.c). Sealing checked: mprotect mm/mprotect.c:706; munmap/MAP_FIXED-replace mm/vma.c:1403,1423; mremap mm/mremap.c:1665-1666; destructive madvise on sealed anon r-o mapping mm/madvise.c:1297-1334 can_madvise_modify.
- (c) CONFIRMED: guard regions exist. MADV_GUARD_INSTALL=102/REMOVE=103 include/uapi/asm-generic/mman-common.h:82-83; madvise_guard_install mm/madvise.c:1121, madvise_guard_remove mm/madvise.c:1250; behavior-descriptor struct = struct madvise_behavior mm/madvise.c:66 (+madvise_behavior_range :61).
- (d) CONFIRMED: map_shadow_stack exists, arch/x86/kernel/shstk.c:546.
- (e) CONFIRMED, but only for plain /proc/pid/maps: fs/proc/task_mmu.c:159 branches on m->op==&proc_pid_maps_op -> rcu_read_lock()+lock_next_vma() (mm/mmap_lock.c:369) instead of mmap_lock; smaps/smaps_rollup/numa_maps still take full mmap_read_lock (page-table walk).
- (f) CONFIRMED: PAGEMAP_SCAN ioctl exists, include/uapi/linux/fs.h:446 -> do_pagemap_scan fs/proc/task_mmu.c:3021, dispatched task_mmu.c:3100.
- (g) UFFDIO set: API/REGISTER/UNREGISTER/WAKE/COPY/ZEROPAGE/MOVE/WRITEPROTECT/CONTINUE/POISON all defined include/uapi/linux/userfaultfd.h:86-104, dispatched fs/userfaultfd.c:2046-2073 — both MOVE and POISON exist.
- (h) CONFIRMED: remap_file_pages still present, mm/mmap.c:1085, deprecated pr_warn_once emulation only (no true nonlinear mapping).

6. Coverage-sweep verdicts
- msync: mm/msync.c:32. Page-worthy (small, standalone POSIX call).
- mincore: mm/mincore.c:292. Page-worthy (small, standalone).
- process_madvise: mm/madvise.c:2107. Page-worthy (distinct pidfd/CAP_SYS_NICE remote semantics) though shares do_madvise machinery — cross-link to madvise.
- VMA NUMA policy (mbind/set_mempolicy/get_mempolicy + vm_ops get_policy/set_policy mm/mempolicy.c:2018-2065, mbind_range mm/mempolicy.c:1039): page-worthy, substantial distinct subsystem.
- accounting/overcommit: mm/util.c:930, mm/mmap.c:1335. Page-worthy (cross-cuts every syscall in this digest; deserves its own overview).
- /proc/pid/maps+smaps+smaps_rollup: fs/proc/task_mmu.c:463,1370,1397. Page-worthy (major introspection API).
- /proc/pid/pagemap+soft-dirty/clear_refs+PAGEMAP_SCAN: task_mmu.c:2308,1768,3021. Page-worthy (large, distinct binary ABI).
- numa_maps: show_numa_map fs/proc/task_mmu.c:3297. Fold into VMA NUMA policy (pure display facet of get_vma_policy()).
- userfaultfd fd API+registration+UFFDIO resolve ops (fs/userfaultfd.c:1261,2186; mm/userfaultfd.c mfill_atomic_copy:868 etc.): page-worthy, large distinct subsystem, keep separate from fault-time interception (handle_userfault, outside searched set).
- remap_file_pages: mm/mmap.c:1085. Fold into mmap (deprecated legacy emulation, small subsection only).
- map_shadow_stack: arch/x86/kernel/shstk.c:546. Page-worthy (CET shadow-stack ABI is substantial, x86-specific).
- memfd_create: mm/memfd.c:505. Page-worthy (widely used, sealing/MFD_* flag surface).
- memfd_secret: mm/secretmem.c:224. Page-worthy (distinct no-kernel-mapping security mechanism), cross-link from memfd_create.
- prctl PR_SET_VMA anon-naming: kernel/sys.c:2409-2415 prctl_set_vma/PR_SET_VMA_ANON_NAME. Fold into /proc/pid/maps (its only observable effect is the `[anon:...]` name field there).
- personality flags affecting layout (ADDR_NO_RANDOMIZE, ADDR_COMPAT_LAYOUT): arch/x86/mm/mmap.c:62-64,72 (PF_RANDOMIZE/mmap_is_legacy gates). Fold into Address-space-layout topic.
- core-dump VMA filtering (coredump_filter): VMA-side toggle is MADV_DONTDUMP/DODUMP -> VM_DONTDUMP mm/madvise.c:1407-1414; the /proc/pid/coredump_filter file itself lives in fs/coredump.c, outside searched scope. Fold into madvise.
- OTHER found not in list: PROCMAP_QUERY ioctl (fs/proc/task_mmu.c:654,824; include/uapi/linux/fs.h:507) — new fast VMA-lookup ioctl; page-worthy, fold alongside /proc/pid/maps. PR_SET_MDWE "Memory-Deny-Write-Execute" (kernel/sys.c:2445,2811; enforced via map_deny_write_exec mm/vma.c:2828 and mm/mprotect.c:905) — page-worthy, distinct W^X-policy prctl mechanism. Protection keys pkey_mprotect/pkey_alloc/pkey_free (mm/mprotect.c:956-992) — fold into mprotect topic. MAP_DROPPABLE/VM_DROPPABLE new mmap flag (mm/mmap.c:504-532) — fold into mmap topic.
### fault area (agent complete, verified on disk at 028ef9c96e96)

1. Entry chain / arch layer
- `exc_page_fault` (arch/x86/mm/fault.c:1483, `DEFINE_IDTENTRY_RAW_ERRORCODE`) -> `handle_page_fault` (1461) -> `fault_in_kernel_space` (1115) branches to `do_kern_addr_fault` (1133, kernel-address case — out of scope) or `do_user_addr_fault` (1206).
- `do_user_addr_fault` (1206-1449): fast path `lock_vma_under_rcu` (mm/mmap_lock.c:296) -> `handle_mm_fault(...|FAULT_FLAG_VMA_LOCK)` at fault.c:1334; fallback `lock_mm_and_find_vma` (mm/mmap_lock.c:496, non-MMU stub 558) -> `handle_mm_fault` at fault.c:1385.
- X86_PF_* bits: arch/x86/include/asm/trap_pf.h:20-30 (PROT/WRITE/USER/RSVD/INSTR/PK/SHSTK/SGX/RMP).
- `access_error` (fault.c:1048-1113): X86_PF_PK->err (1059); X86_PF_SGX->err (1071); `arch_vma_access_permitted` pkey check (1079); shadow-stack VM_SHADOW_STACK checks (1087-1093); write/VM_WRITE (1095-1102); read/`vma_is_accessible` (1104-1112).
- Retry loop: `retry:` label fault.c:1356-1411, bounded by `fault_signal_pending()` (checked 1347,1387; impl include/linux/sched/signal.h:424), `VM_FAULT_COMPLETED` short-circuit (1400), else `goto retry` with FAULT_FLAG_TRIED (1408-1410) on VM_FAULT_RETRY — no hard iteration cap; underlying block/retry primitive is `folio_lock_or_retry` (include/linux/pagemap.h:1208, impl mm/filemap.c:1753).
- Signal delivery: `fault_signal_pending` (sched/signal.h:424); `bad_area_nosemaphore`/`__bad_area_nosemaphore` (fault.c:826/776) -> `force_sig_fault`/`force_sig_pkuerr` (820-823); `do_sigbus` (906, handles VM_FAULT_HWPOISON[_LARGE]).
- vsyscall hook: `is_vsyscall_vaddr`/`emulate_vsyscall` fault.c:1316-1319 (impl arch/x86/entry/vsyscall/vsyscall_64.c:114), run before VMA lookup.
- Kernel-extable fixup: `fixup_exception()` called fault.c:726 inside `kernelmode_fixup_or_oops`; impl arch/x86/mm/extable.c:299.

2. mm-side descent
- `handle_mm_fault` (mm/memory.c:6589-6654): `sanitize_fault_flags` (6547-6580, validates UNSHARE/WRITE and VMA_LOCK+RETRY_NOWAIT combos) -> `arch_vma_access_permitted` -> `mem_cgroup_enter_user_fault` (6617, memcg-OOM) -> `lru_gen_enter_fault` -> hugetlb divert `if (is_vm_hugetlb_page(vma))` mm/memory.c:6621-6622 -> `hugetlb_fault()` else `__handle_mm_fault()` (6624) -> `mm_account_fault` (6650, accounting).
- `__handle_mm_fault` (6355-6456): PUD: `create_huge_pud`(6181)/`wp_huge_pud`(6195) called 6383/6397, `huge_pud_set_accessed`(huge_memory.c:2004) called 6401. PMD: `create_huge_pmd`(6139) called 6417; device-private `do_huge_pmd_device_private`(huge_memory.c:1375) called 6430; migration wait `pmd_migration_entry_wait`(mm/migrate.c:549) called 6433; THP branch: NUMA `do_huge_pmd_numa_page`(huge_memory.c:2185) called 6438, wp `wp_huge_pmd`(6150) called 6442, set-accessed `huge_pmd_set_accessed`(huge_memory.c:2018)+`fix_spurious_fault(PGTABLE_LEVEL_PMD)` at 6447-6448; fallback -> `handle_pte_fault` (6455).
- `handle_pte_fault` (6273-6347) dispatch: `!vmf->pte`(pmd_none/pte_none) -> `do_pte_missing`(4472 -> `do_anonymous_page`(5217) if `vma_is_anonymous` else `do_fault`(5903)), called 6317; `!pte_present` -> `do_swap_page`(4706), called 6320; `pte_protnone && vma_is_accessible` -> `do_numa_page`(6048), called 6323; write/unshare && `!pte_write` -> `do_wp_page`(4149), called 6333; fallthrough: `pte_mkyoung`+`ptep_set_access_flags`+`update_mmu_cache_range` else `fix_spurious_fault(PGTABLE_LEVEL_PTE)` (6337-6343).

3. Per-handler anchors
- `do_anonymous_page` (mm/memory.c:5217-5330): zero-page for reads (`my_zero_pfn`) else `vmf_anon_prepare`+`alloc_anon_folio`; order-selection helper `alloc_anon_folio` (5127-5210) uses `thp_vma_allowable_orders`/`thp_vma_suitable_orders` capped `BIT(PMD_ORDER)-1`, walks down via `highest_order`/`next_order` picking largest fully-`pte_range_none()` order; `userfaultfd_missing`->`handle_userfault` at 5256/5306.
- `do_fault`(5903-5945) dispatches: no `->fault`->SIGBUS/NOPAGE; `!FAULT_FLAG_WRITE`->`do_read_fault`(5779); `!VM_SHARED`->`do_cow_fault`(5811); else `do_shared_fault`(5853). `__do_fault`(5337-5391) invokes `vma->vm_ops->fault`. Fault-around: `should_fault_around`(5766)/`do_fault_around`(5733-5763); default `fault_around_pages=65536>>PAGE_SHIFT`=16 pages/64KB (5673-5674), clamped to [PAGE_SIZE, PTRS_PER_PTE=512 pages/2MB x86-64] and rounded to pow2 in `fault_around_bytes_set` (5687-5700).
- `finish_fault`(5556-5671)/`set_pte_range`(5497-5531)/`do_set_pmd`: two definitions — THP body mm/memory.c:5407-5481 vs `#else` stub returning `VM_FAULT_FALLBACK` at 5483-5486.
- `do_wp_page`(4149-4242): `userfaultfd_pte_wp`->`handle_userfault` at 4161 (VM_UFFD_WP); reuse if `PageAnonExclusive` or `wp_can_reuse_anon_folio`(4086)->`wp_page_reuse`(3664); shared VMA (`VM_SHARED|VM_MAYSHARE`)->`wp_pfn_shared`(3950)/`wp_page_shared`(3972); else copy->`wp_page_copy`(3758).
- `do_swap_page`(4706-5113): classifies via `softleaf_t` (`softleaf_from_pte` 4725, header include/linux/leafops.h); non-swap branch (4726-4777): migration->`migration_entry_wait`, device-exclusive->`remove_device_exclusive_entry`(4375), device-private->`migrate_to_ram` (VMA-lock bail 4734-4742), hwpoison->VM_FAULT_HWPOISON, marker->`handle_pte_marker`(4496: PTE_MARKER_POISONED/GUARD->SIGBUS-class, uffd-wp->`pte_marker_handle_uffd_wp`(4484)->`do_pte_missing`/`handle_userfault`); genuine swap-in (4780+): `get_swap_device`->`swap_cache_get_folio`/`swapin_readahead` or (SWP_SYNCHRONOUS_IO) `alloc_swap_folio`+`swapin_folio`->`folio_lock_or_retry`->`ksm_might_need_to_copy`->ptl recheck->rmap+`set_ptes`.
- `do_numa_page`(6048-6137): `pte_modify`/writable-upgrade check->`numa_migrate_check`(5947)->`mpol_misplaced`->`migrate_misplaced_folio`. PMD analogue `do_huge_pmd_numa_page`(huge_memory.c:2185-2259).
- THP PMD faults (mm/huge_memory.c): `do_huge_pmd_anonymous_page`(1461) — huge-zero-page inline path (`handle_userfault` at 1500) else falls to `__do_huge_pmd_anonymous_page`(1323, real-folio alloc, `handle_userfault` at 1354); wp `do_huge_pmd_wp_page`(2060, zero-pmd copy via `do_huge_zero_wp_pmd` 2028, reuse via PageAnonExclusive else `__split_huge_pmd` fallback); numa `do_huge_pmd_numa_page`(2185); device-private `do_huge_pmd_device_private`(1375).
- `hugetlb_fault`(mm/hugetlb.c:5972-6161)/`hugetlb_no_page`(5722-5946)/`hugetlb_wp`(5450-...): fault-mutex table sized mm/hugetlb.c:4187-4194 `num_fault_mutexes = roundup_pow_of_two(8*num_possible_cpus())` (SMP) else 1; hash `hugetlb_fault_mutex_hash`(5949-5970, jhash2 over {mapping,idx}); reservation consumption via `vma_needs_reservation`/`vma_end_reservation` at 6075-6082 (hugetlb_fault) and 5869-5876 (hugetlb_no_page), `restore_reserve_on_error` on backout (5941).
- `vmf_insert_*` family: `insert_pfn`(2626, static)/`vmf_insert_pfn_prot`(2710)/`vmf_insert_pfn`(2757)/`vmf_insert_page_mkwrite`(2824)/`vmf_insert_mixed`(2844)/`vmf_insert_mixed_mkwrite`(2856) in mm/memory.c; huge variants for drivers' `->huge_fault`: `vmf_insert_pfn_pmd`(huge_memory.c:1607)/`vmf_insert_folio_pmd`(1633)/`vmf_insert_pfn_pud`(1715)/`vmf_insert_folio_pud`(1749).

4. Fault contract / lock protocols
- `struct vm_fault`: include/linux/mm.h:698-742 (const {vma,gfp_mask,pgoff,address,real_address}; `flags`; `pmd`/`pud`; union `orig_pte`/`orig_pmd`; `cow_page`/`page`; ptl-scoped `pte`/`ptl`/`prealloc_pte`).
- `enum fault_flag`: include/linux/mm_types.h:1735-1749; legal-retry-combo comment block: mm_types.h:1712-1730 (a: ALLOW_RETRY&&!TRIED, b: ALLOW_RETRY&&TRIED, c: !ALLOW_RETRY&&!TRIED).
- `enum vm_fault_reason`/VM_FAULT_* codes: mm_types.h:1618-1633; `VM_FAULT_ERROR` mask 1639-1641.
- Per-VMA-lock path: RCU lookup `lock_vma_under_rcu` (mm/mmap_lock.c:296-342, wraps `vma_start_read` 212); mmap_lock fallback `lock_mm_and_find_vma` (mm/mmap_lock.c:496-549 MMU; non-MMU stub 558-568).
- Bail-out-to-mmap_lock sites (per-VMA-lock fault -> VM_FAULT_RETRY back to mmap_lock retry): 4 distinct guards, 10 call sites: (1) `vmf_can_call_fault` mm/memory.c:3698-3706 [no `->map_pages`] <- do_read_fault:5795, do_cow_fault:5817, do_shared_fault:5859; (2) `vmf_anon_prepare`/`__vmf_anon_prepare` mm/internal.h:500-507 + mm/memory.c:3723-3739 [missing anon_vma, trylock fails] <- wp_page_copy:3775, do_anonymous_page:5262, do_cow_fault:5819, hugetlb_wp mm/hugetlb.c:5588, hugetlb_no_page mm/hugetlb.c:5787; (3) do_swap_page device-private mm/memory.c:4734-4742; (4) do_huge_pmd_device_private mm/huge_memory.c:1384-1387.
- userfaultfd interception — `handle_userfault()` (fs/userfaultfd.c:381), 10 call sites: mm/huge_memory.c:1354, mm/huge_memory.c:1500, mm/hugetlb.c:5702 (inside `hugetlb_handle_userfault` wrapper 5688, itself reached from hugetlb_no_page:5782 and :5858), mm/hugetlb.c:6098, mm/memory.c:4161, mm/memory.c:5256, mm/memory.c:5306, mm/memory.c:6161, mm/shmem.c:2495, mm/shmem.c:2544.

5. Hard-coded limits
- Fault-around: default `fault_around_pages=65536>>PAGE_SHIFT`=16 pages/64KB (mm/memory.c:5673-5674); clamp [PAGE_SIZE, PTRS_PER_PTE=512 pages/2MB on x86-64] rounddown-to-pow2 in `fault_around_bytes_set` (5687-5700).
- hugetlb fault-mutex table: `num_fault_mutexes = roundup_pow_of_two(8*num_possible_cpus())` under CONFIG_SMP else 1 (mm/hugetlb.c:4187-4194).
- THP order thresholds: `PMD_ORDER`=9/2MB, `PUD_ORDER`=18/1GB on x86-64 (include/linux/pgtable.h:8-9, from PMD_SHIFT=21/PUD_SHIFT=30 in arch/x86/include/asm/pgtable_64_types.h:67,74); anon large-folio search in `alloc_anon_folio` capped at `BIT(PMD_ORDER)-1` (mm/memory.c:5150).
- x86-64 PTRS_PER_PTE=512 (arch/x86/include/asm/pgtable_64_types.h:80) — doubles as the fault-around and PMD-mapped-folio page-table-index bound (finish_fault, 5628-5637).

6. Version-specific facts (v7.0 vs older) / extra topic suggestions
- `softleaf_t`/include/linux/leafops.h non-present-entry classifier is new in v6.19 (commit 68aa2fdbf57f "mm: introduce leaf entry type..."), replacing scattered `swp_entry_t`+`is_migration_entry()`/`pte_to_swp_entry()` checks in do_swap_page, hugetlb.c, huge_memory.c.
- `do_huge_pmd_device_private` (huge_memory.c:1375) is new in v6.19 (commit 4964099163d0 "mm/memory/fault: add THP fault handling for zone device private pages") — PMD-granularity device-private faults didn't exist before.
- `fix_spurious_fault`'s `enum pgtable_level` param was `enum rmap_level` before v6.18 (rename commit b22cc9a9c7ff).
- Per-VMA-lock exclusion bit renamed `VMA_LOCK_OFFSET`->`VM_REFCNT_EXCLUDE_READERS_FLAG` and reworked into `__vma_start/end_exclude_readers()` (mm/mmap_lock.c) in the v7.0 cycle itself (commit 25faccd69977, not yet in v6.19).
- Extra doc topics beyond the 11 requested, each with anchors: per-VMA-lock RCU fault path & bailout matrix (`lock_vma_under_rcu`, `FAULT_FLAG_VMA_LOCK`); userfaultfd interception map (`handle_userfault`); softleaf/leafops classifier (`softleaf_type`, leafops.h); THP PMD fault family (`do_huge_pmd_*`); hugetlb fault path & mutex table (`hugetlb_fault`/`hugetlb_no_page`/`hugetlb_wp`); fault-around mechanism (`do_fault_around`); `vmf_insert_pfn/mixed/folio` driver-facing API; PTE-marker dispatch for uffd-wp/poison/guard (`handle_pte_marker`).
### rmap + folio area (agent complete, verified on disk at 028ef9c96e96)

1. Core structs
- `struct anon_vma` — include/linux/rmap.h:32-68: root, rwsem, refcount(atomic_t), num_children/num_active_vmas(unsigned long, reuse accounting), parent, rb_root(rb_root_cached; LSB stolen by mm_take_all_locks()).
- `struct anon_vma_chain` — rmap.h:83-92: vma, anon_vma, same_vma(list_head — vma's chain, mmap_lock+ptl), rb(rb_node — anon_vma's interval tree, anon_vma->rwsem), rb_subtree_last, cached_vma_start/last(CONFIG_DEBUG_VM_RB).
- `struct rmap_walk_control` — rmap.h:951-965: arg, try_lock/contended(bool), rmap_one()/done()/anon_lock()/invalid_vma() callbacks.
- `struct page_vma_mapped_walk` — rmap.h:864-874: pfn,nr_pages,pgoff,vma,address,pmd,pte,ptl,flags. PVMW_SYNC=1<<0, PVMW_MIGRATION=1<<1 (rmap.h:855,857); result flag PVMW_PGTABLE_CROSSED=1<<16 (rmap.h:862, set page_vma_mapped.c:316).
- folio mapcount/pin cluster — include/linux/mm_types.h: `_mapcount`(atomic_t,430)/`_mapcount_1`(469, tail-page1 union); `_large_mapcount`(454), `_nr_pages_mapped`(455), `_entire_mapcount`(457 64-bit / 486 32-bit), `_pincount`(458/487), `_mm_id_mapcount[2]`(460, mm_id_mapcount_t), `_mm_id[2]`/`_mm_ids`(462-463, mm_id_t/unsigned long), `_nr_pages`(473, NR_PAGES_IN_LARGE_FOLIO).
- `rmap_t` — rmap.h:320-329: `typedef int __bitwise`; RMAP_NONE=0, RMAP_EXCLUSIVE=BIT(0) (only bit currently defined).

2. API families (anchors + caller counts via semcode/grep)
- anon_vma alloc/free+refcount+lock: anon_vma_alloc/free (rmap.c:90,110), anon_vma_chain_alloc/free(140,145); get_anon_vma/put_anon_vma/__put_anon_vma (mm/internal.h:205-216, rmap.c:2905); lock helpers anon_vma_lock/unlock_{write,read}(+trylock) all in mm/internal.h:218-246, operating on `anon_vma->root->rwsem`.
- chain link/assign+interval tree: anon_vma_chain_assign(rmap.c:150); anon_vma_interval_tree_insert/remove+iter_first/next (mm/interval_tree.c:75-103, INTERVAL_TREE_DEFINE :71-73); vma_interval_tree_insert/insert_after(:23-59).
- setup/teardown: __anon_vma_prepare/anon_vma_prepare (mm/internal.h:261-270, rmap.c:185-233, first-fault prepare); find_mergeable_anon_vma (mm/vma.c:2003, via reusable_anon_vma/anon_vma_compatible :1951-1993); anon_vma_clone(dst,src,enum vma_operation)(mm/internal.h:258-259,rmap.c:320-371, callers mm/vma.c:533,631,1910 + rmap.c:404); maybe_reuse_anon_vma reuse heuristic (rmap.c:270-288: num_active_vmas==0 && num_children<=1); anon_vma_fork(rmap.c:378-442, 1 caller dup_mmap); unlink_anon_vmas teardown(rmap.c:479-541, 2 callers: free_pgtables, dontunmap_complete).
- folio add/remove rmap: folio_add_new_anon_rmap(rmap.c:1636); folio_add_anon_rmap_ptes/pmd(1589/1610; ptes has 2 callers: __split_huge_pmd_locked, do_swap_page); folio_add_file_rmap_ptes/pmd/pud(1723/1739/1759; ptes 1 caller set_pte_range); folio_remove_rmap_ptes/pmd/pud(1891/1907/1927; ptes 4 callers); folio_move_anon_rmap(1434); hugetlb_add_anon_rmap/hugetlb_add_new_anon_rmap(3120/3134); hugetlb_try_dup_anon_rmap/hugetlb_try_share_anon_rmap/hugetlb_add_file_rmap/hugetlb_remove_rmap(rmap.h:435-490, inline); fork-time dup/share inlines folio_try_dup_anon_rmap_{ptes,pte,pmd}, folio_dup_file_rmap_{ptes,pte,pmd}, folio_try_share_anon_rmap_{pte,pmd}(rmap.h:492-840, all take `enum pgtable_level`).
- mapping-encoding: FOLIO_MAPPING_ANON=0x1/ANON_KSM=0x2/KSM/FLAGS(page-flags.h:717-720); setters __folio_set_anon(rmap.c:1457-1480) and folio_move_anon_rmap(rmap.c:1434-1448); folio_test_anon/PageAnon/folio_test_ksm(page-flags.h:722-748); linear_page_index(include/linux/pagemap.h:1068-1075), folio_pgoff/page_pgoff(pagemap.h:1063,1035).
- mapcount readers: folio_mapcount(mm.h:1594), folio_mapped(mm.h:1613), folio_entire_mapcount/folio_large_mapcount(mm.h:1560/1568), folio_maybe_mapped_shared "maybe-shared" predicate(mm.h:2613-2637, tests FOLIO_MM_IDS_SHARED_BITNUM).
- rmap_walk+backends: rmap_walk/rmap_walk_locked(rmap.c:3093/3104, dispatch ksm->anon->file); rmap_walk_anon+rmap_walk_anon_lock(2956/2914); __rmap_walk_file/rmap_walk_file(3023/3075); rmap_walk_ksm(mm/ksm.c:3152, declared include/linux/ksm.h:97) honors the same try_lock/contended/rmap_one/done contract via anon_vma_interval_tree_foreach over stable_node->hlist.
- page_vma_mapped_walk+wrappers: core mm/page_vma_mapped.c:180-335 (check_pte:107, check_pmd:140, map_pte:16); DEFINE_FOLIO_VMA_WALK / page_vma_mapped_walk_done / _restart(rmap.h:876-917); page_mapped_in_vma(page_vma_mapped.c:348, 1 caller memory-failure.c, CONFIG_MEMORY_FAILURE); page_address_in_vma(rmap.c:856); 6 direct callers of page_vma_mapped_walk (KSM, DAMON x2, page_idle, migrate, page_mapped_in_vma).
- consumers: folio_referenced(rmap.c:1059,+folio_referenced_one:917; 2 callers: shrink_active_list, folio_check_references); try_to_unmap(rmap.c:2386,+try_to_unmap_one:1978; 5 callers) — TTU flags(rmap.h:94-105): TTU_USE_SHARED_ZEROPAGE=0x2, TTU_SPLIT_HUGE_PMD=0x4, TTU_IGNORE_MLOCK=0x8, TTU_SYNC=0x10, TTU_HWPOISON=0x20, TTU_BATCH_FLUSH=0x40, TTU_RMAP_LOCKED=0x80; try_to_migrate(rmap.c:2731,+try_to_migrate_one:2407; 4 callers); migration-PTE restore remove_migration_pte/ptes(mm/migrate.c:346/455, rmap_walk-driven); folio_mkclean(rmap.c:1193;4 callers)+mapping_wrprotect_range(1267)+pfn_mkclean_range(1304); device-exclusive make_device_exclusive(rmap.c:2808-2902, CONFIG_DEVICE_PRIVATE)+restore_exclusive_pte(mm/memory.c:881, reverse path — no dedicated helper lives in migrate.c itself); mlock hooks mlock_vma_folio/munlock_vma_folio(mm/internal.h:1111/1127)->mlock_folio/munlock_folio(mm/mlock.c:242/290); unmap_mapping_folio/pages/range(mm/memory.c:4283/4318/4354; unmap_mapping_range has 33 direct callers); hugetlb pmd sharing huge_pmd_share/unshare/_flush(mm/hugetlb.c:6878/6939/6973, under i_mmap_lock_read+vma_interval_tree_foreach; active on x86-64 via `select ARCH_WANT_HUGE_PMD_SHARE if X86_64`, arch/x86/Kconfig:147).

3. Lifecycle and locking
- anon_vma slab: `SLAB_TYPESAFE_BY_RCU|SLAB_PANIC|SLAB_ACCOUNT` via anon_vma_ctor(rmap.c:543-556) — enables lockless folio_get_anon_vma race safety.
- refcount vs num_children/num_active_vmas: refcount=lifetime pin; num_children=# anon_vmas parented here (reuse decision); num_active_vmas=# live VMAs pointing here (rmap.h:44-53; maybe_reuse_anon_vma rmap.c:270-288).
- root-rwsem rule: all locking of an anon_vma tree goes through `anon_vma->root->rwsem` (mm/internal.h:218-246; anon_vma_fork rmap.c:420-424).
- RCU contracts: folio_get_anon_vma(rmap.c:587-623, rcu_read_lock+atomic_inc_not_zero, re-check folio_mapped) vs folio_lock_anon_vma_read(rmap.c:633-702, adds down_read_trylock fast path before falling back to refcount+sleep).
- Lock-ordering comment block: mm/rmap.c:21-52 (inode->i_rwsem > mmap_lock > invalidate_lock > folio_lock > hugetlbfs_i_mmap_rwsem_key > vma_start_write > i_mmap_rwsem > anon_vma->rwsem > page_table_lock/pte_lock > swap_lock > ...).
- TLB batching: CONFIG_ARCH_WANT_BATCHED_UNMAP_TLB_FLUSH selected unconditionally by x86(arch/x86/Kconfig:142); mm/rmap.c:704-748 try_to_unmap_flush/try_to_unmap_flush_dirty/set_tlb_ubc_flush_pending; struct tlbflush_unmap_batch(include/linux/mm_types_task.h:68, as task_struct.tlb_ubc, sched.h:1412); arch_tlbbatch_flush(arch/x86/include/asm/tlbflush.h:358).

4. Constants
- ENTIRELY_MAPPED=0x800000, FOLIO_PAGES_MAPPED=ENTIRELY_MAPPED-1 (mm/internal.h:107-112, chosen above 16GB-hugetlb-as-PTEs max of 0x400000).
- MM_ID_MAPCOUNT_MAX=INT_MAX(64-bit)/SHRT_MAX(32-bit) (mm_types.h:328/332); MM_ID_DUMMY=0, MM_ID_MIN=1, MM_ID_MASK=MM_ID_MAX=(1<<MM_ID_BITS)-1 (mm_types.h:337-346).
- GUP_PIN_COUNTING_BIAS=1<<10 (mm.h:1919, small-folio pin-saturation bias used by folio_maybe_dma_pinned).
- PGTY_mapcount_underflow=0xff, PGTY_buddy..PGTY_large_kmalloc=0xf0-0xf8 (page-flags.h:925-950) — page_type/`_mapcount` union encoding via page_mapcount_is_type().
- PG_anon_exclusive = PG_owner_2 (page-flags.h:146), aliases PG_mappedtodisk(:152); only valid on anon folios, tail-page-only for PTE-mapped THP (comment :139-145).

5. Version-specific facts, confirmed on disk
a. CONFIRMED: macros are `FOLIO_MAPPING_ANON`/`ANON_KSM`/`KSM`/`FLAGS` (page-flags.h:717-720); no `PAGE_MAPPING_*` remains anywhere.
b. CONFIRMED: `anon_vma_clone(dst,src,enum vma_operation)`(mm/internal.h:258-259); `enum vma_operation {VMA_OP_SPLIT, VMA_OP_MERGE_UNFAULTED, VMA_OP_REMAP, VMA_OP_FORK}`(mm/internal.h:251-256).
c. CONFIRMED: CONFIG_MM_ID exists (mm/Kconfig:791 def_bool n, selected by TRANSPARENT_HUGEPAGE :799) — fields folio->_mm_id[2]/_mm_ids/_mm_id_mapcount[2](mm_types.h:460-464); bit-spinlock via folio_lock/unlock_large_mapcount on FOLIO_MM_IDS_LOCK_BITNUM(rmap.h:112-120); predicate folio_maybe_mapped_shared() tests FOLIO_MM_IDS_SHARED_BITNUM(mm.h:2613-2637); IDs from `ida_alloc_range(&mm_ida,...)` in mm_alloc_id/mm_free_id(kernel/fork.c:595-619).
d. CONFIRMED: `enum pgtable_level {PGTABLE_LEVEL_PTE=0, PMD, PUD, P4D, PGD}`(include/linux/pgtable.h:2169-2174); rmap add/remove/dup/share APIs consume only PTE/PMD/PUD.
e. CONFIRMED: `_large_mapcount`, `_nr_pages_mapped`, `_entire_mapcount` all present(mm_types.h:454-458/486-487). New: `folio_nr_pages_mapped()` returns -1 under new CONFIG_NO_PAGE_MAPCOUNT(mm/Kconfig:954, EXPERIMENTAL); CONFIG_PAGE_MAPCOUNT=`!NO_PAGE_MAPCOUNT`(mm/Kconfig:970-971) now gates per-page `_mapcount`/`_nr_pages_mapped` maintenance (`IS_ENABLED(CONFIG_PAGE_MAPCOUNT)` guards, e.g. rmap.c:1665-1681).
f. CONFIRMED: `page_referenced`/`page_mkclean`/`page_add_anon_rmap`/`page_remove_rmap`/`page_move_anon_rmap` are absent tree-wide (grep clean) — replaced by folio_referenced/folio_mkclean/folio_add_*_rmap_*/folio_remove_rmap_*/folio_move_anon_rmap. Also `folio_likely_mapped_shared` is gone, renamed `folio_maybe_mapped_shared`(mm.h:2613).

6. Suggested page topics beyond {anon_vma; anon_vma_chain; setup/teardown; file rmap}
- Folio mapcount & MM-ID encoding — mm_types.h `_large_mapcount`/`_mm_id*` cluster + ENTIRELY_MAPPED + CONFIG_MM_ID bit-spinlock protocol(rmap.h:112-317).
- page_vma_mapped_walk infrastructure — mm/page_vma_mapped.c + PVMW_* flags, shared by KSM/DAMON/idle-tracking/migration/hwpoison callers.
- TTU family (try_to_unmap/try_to_migrate) — rmap.c:1978-2767, enum ttu_flags, mlock/TLB-batch interplay.
- rmap_walk dispatch (anon/file/KSM) — rmap.c:3093-3101 + mm/ksm.c:3152, shared rmap_walk_control contract.
- folio_mkclean/mapping_wrprotect_range/pfn_mkclean_range — writeback+DAX cleaning family, rmap.c:1193-1345+.
- PageAnonExclusive & GUP-fast races — folio_try_dup/share_anon_rmap_*, PG_owner_2 aliasing, rmap.h:567-840.
- hugetlb rmap + PMD sharing — hugetlb_add_anon_rmap family + huge_pmd_share/unshare over i_mmap_rwsem, mm/hugetlb.c:6878-7002.
- mlock/munlock folio hooks — mm/mlock.c + mm/internal.h:1111-1141, folio->mlock_count field.
- device-exclusive memory — make_device_exclusive()/restore_exclusive_pte(), rmap.c:2769-2903, mm/memory.c:881+.
- unmap_mapping_range/pages i_mmap truncation path — mm/memory.c:4244-4390+, 33 callers.
### gup + pgtable area (agent complete, verified on disk at 028ef9c96e96)

PART A — GUP / pin_user_pages (mm/gup.c)

A1. API surface (all `mm/gup.c`, CONFIG_MMU)
GUP family: `get_user_pages_remote` 2603/EXPORT 2618, `get_user_pages` 2644/2655, `get_user_pages_unlocked` 2672/2684, `get_user_pages_fast_only` 3242/EXPORT_GPL 3258, `get_user_pages_fast` 3276/3289.
PUP family: `pin_user_pages_fast` 3310/EXPORT_GPL 3317, `pin_user_pages_remote` 3342/EXPORT 3356, `pin_user_pages` 3376/3386, `pin_user_pages_unlocked` 3396/3408 — no `pin_user_pages_fast_only` exists.
Unpin: `unpin_user_page` 185, `unpin_folio` 199(GPL), `unpin_user_pages_dirty_lock` 284, `unpin_user_page_range_dirty_lock` 354, `unpin_user_pages` 401, `unpin_user_folio` 434, `unpin_folios` 449(GPL).
Memfd pinning: `memfd_pin_folios()` 3436/EXPORT_GPL 3533; `folio_add_pins()` 3551/3557 adds pins to an already-FOLL_PIN'd folio. `get_dump_page()` 2187 (CONFIG_ELF_CORE) -> `__get_user_pages_locked` with FOLL_FORCE|FOLL_DUMP|FOLL_GET.
Validation: `is_valid_gup_args()` gup.c:2500 — rejects caller-set INTERNAL_GUP_FLAGS (internal.h:1547); FOLL_GET^FOLL_PIN exclusive; FOLL_LONGTERM implies FOLL_PIN; FOLL_GET|FOLL_PIN require pages[]; FOLL_LONGTERM+FOLL_PCI_P2PDMA exclusive; `locked!=NULL` forces FOLL_UNLOCKABLE.

A2. Paths
Slow: `__get_user_pages()` 1354 loop — vma lookup `gup_vma_lookup()`1265->`vma_lookup()`; `check_vma_flags()`1200 (VM_IO/PFNMAP, anon, fsdax+LONGTERM, secretmem, write=>VM_WRITE||FORCE+is_cow_mapping); descent `follow_page_mask()`1007->`follow_pud_mask()`942->`follow_pmd_mask()`898->`follow_page_pte()`802; COW/unshare gate: `follow_page_pte` returns -EMLINK, fed as `unshare` bool into `faultin_page()`1087 (sets FAULT_FLAG_UNSHARE); gate area `in_gate_area()`+`get_gate_page()`1030; retry machine in `__get_user_pages_locked()`1649 loops on VM_FAULT_RETRY/-EBUSY and VM_FAULT_COMPLETED/-EAGAIN.
Fast: `gup_fast_fallback()`3175->`gup_fast()`3129: FOLL_PIN uses `raw_seqcount_try_begin`/`read_seqcount_retry` on `mm->write_protect_seq` (3141,3165, fork-vs-pin guard); `local_irq_save/restore`3156-58 around `gup_fast_pgd_range`3092->p4d3069->pud3043->pmd3011->leaf handlers `gup_fast_pmd_leaf`2924/`gup_fast_pte_range`2829 (CONFIG_ARCH_HAS_PTE_SPECIAL); folio filter `gup_fast_folio_allowed()`2738 used in all leaf handlers; grab via `try_grab_folio_fast()`517.
Lock regime: mmap_lock only (`mmap_read_lock_killable`1667); no per-VMA-lock GUP (zero hits for lock_vma_under_rcu/vma_start_read in gup.c).

A3. Pinning mechanics
Bias `GUP_PIN_COUNTING_BIAS = 1U<<10` mm.h:1919; separate `folio->_pincount` (mm_types.h:458,487) used iff `folio_has_pincount()`mm.h:2323 (large folios/CONFIG_64BIT); predicate `folio_maybe_dma_pinned()`mm.h:2355.
Grab/put: `try_grab_folio()`gup.c:140, `try_grab_folio_fast()`517, `gup_put_folio`/unpin family (A1).
Unshare rule: `gup_must_unshare()` internal.h:1571 — true when FOLL_PIN set w/o FOLL_WRITE on non-exclusive anon, or R/O FOLL_LONGTERM on a writable-private(COW) file mapping; 6 enforcement sites: `follow_page_pte`802, `follow_huge_pmd`701, `follow_huge_pud`649, `gup_fast_pte_range`2829, `gup_fast_pmd_leaf`2924, `gup_fast_pud_leaf`2967.
Fork/COW: sticky `MMF_HAS_PINNED` mm_types.h:1909 ("never cleared"), set by `mm_set_has_pinned_flag()`gup.c:479; `mm->write_protect_seq` raw seqcount bumped by fork's copy_page_range, checked by GUP-fast (A2). Sanity: `sanity_check_pinned_pages()`gup.c:29 (DEBUG_VM) asserts pinned anon pages are PageAnonExclusive.

A4. Longterm + fault-in
`folio_is_longterm_pinnable()`mm.h:2413/2441; driving struct `pages_or_folios`gup.c:2207 feeds `collect_longterm_unpinnable_folios()`2265 + `migrate_longterm_unpinnable_folios()`2321, orchestrated by `check_and_migrate_movable_pages_or_folios()`2386 inside `__gup_longterm_locked()`2465 (one migrate-then-retry pass).
Fault-in-only: `fixup_user_fault()`1564/EXPORT_GPL 1618; `populate_vma_page_range()`1813 backs mlock/MAP_POPULATE via `__mm_populate()`1925; `faultin_page_range()`1887 backs MADV_POPULATE_READ/WRITE (mm/madvise.c:974, FOLL_MADV_POPULATE); `fault_in_writeable`2046/`fault_in_subpage_writeable`2080/`fault_in_safe_writeable`2115/`fault_in_readable`2147, all exported.

A5. Version facts
`follow_page()` public API is gone entirely (zero declarations/definitions repo-wide); single-address lookups now use `folio_walk_start()`/`folio_walk_end()` (pagewalk.h:196-205, impl mm/pagewalk.c:902) — CONFIRMED removed.
`try_grab_page()` is gone (zero hits); only folio-based `try_grab_folio()`/`try_grab_folio_fast()` remain — CONFIRMED folio-only.
Devmap/DAX special-casing absent from mm/gup.c (zero hits devmap/pte_devmap/is_zone_device_page) — CONFIRMED gone; handled via leafops/rmap now.
Fast-path folio filter is named `gup_fast_folio_allowed()` gup.c:2738.
Consumers verified: lib/iov_iter.c:1091,1763; io_uring/memmap.c,zcrx.c; drivers/vfio/vfio_iommu_type1.c; drivers/iommu/iommufd/pages.c; drivers/infiniband/core/umem.c:236; virt/kvm/kvm_main.c:2874,2908; kernel/futex/core.c:638; mm/process_vm_access.c:106; drivers/dma-buf/udmabuf.c:335.

PART B — x86-64 page tables

B1. Entry encoding
Types: `pte_t`/`pmd_t` wrap pteval_t/pmdval_t pgtable_64_types.h:21-22; pud_t/p4d_t/pgd_t pgtable_types.h:295,342,368.
Bits pgtable_types.h:10-143: PRESENT=0,RW=1,USER=2,PWT=3,PCD=4,ACCESSED=5,DIRTY=6,PSE/PAT=7,GLOBAL=8,SOFTW1-3=9-11,PAT_LARGE=12,SOFTW4=57,SOFTW5=58,PKEY0-3=59-62,NX=63; SPECIAL=SOFTW1, UFFD_WP=SOFTW2, SOFT_DIRTY=SOFTW3, SAVED_DIRTY=SOFTW5(64b); PROTNONE reuses GLOBAL bit (line 49, only when PRESENT=0); swap-PTE reuses `_PAGE_SWP_SOFT_DIRTY=_PAGE_RW`, `_PAGE_SWP_UFFD_WP=_PAGE_USER` (108-118).
Prot chain: `protection_map[16]` arch/x86/mm/pgprot.c:8 -> `vm_get_page_prot()`:35(EXPORT); `mk_pte()` now lives in include/linux/mm.h:2268; `pfn_pte()` pgtable.h:738.
Accessors/mk: `pte_present`967, `pmd_present`985, `pte_huge`238, `pte_wrprotect`409, `pte_mkclean/mkdirty`438/453, `pte_mkwrite_shstk`460 (CET shadow-stack), `pte_mkyoung`467, `pte_mkhuge/pmd_mkhuge/pud_mkhuge`481/577/642.
4K/2M/1G: PSE bit (shared w/ PAT bit7) marks huge leaves; `pmd_leaf()`298, `pud_leaf()`1066 both test `_PAGE_PSE`; large-page PAT uses PAT_LARGE(bit12) not PAT(bit7).

B2. Non-present ("soft leaf") encoding
Classified in `include/linux/leafops.h` (exists): `softleaf_t` + `enum softleaf_type` leafops.h:19-35 (NONE/SWAP/MIGRATION_READ/_READ_EXCLUSIVE/_WRITE/DEVICE_PRIVATE_READ/_WRITE/DEVICE_EXCLUSIVE/HWPOISON/MARKER); `softleaf_from_pte/pmd()`55/94, `softleaf_type()`140 dispatches via swp_type() vs MAX_SWAPFILES/SWP_MIGRATION_*/SWP_DEVICE_*/SWP_HWPOISON/SWP_PTE_MARKER; predicates 188-309.
swp_entry_t split swapops.h:27-42: `SWP_TYPE_SHIFT = BITS_PER_XA_VALUE(63) - MAX_SWAPFILES_SHIFT(5) = 58`; `SWP_OFFSET_MASK=(1<<58)-1`; `SWP_PFN_BITS` = min(MAX_PHYSMEM_BITS-PAGE_SHIFT, SWP_TYPE_SHIFT); `SWP_PFN_MASK`.
PTE markers swapops.h:281-300: `pte_marker` typedef; `PTE_MARKER_UFFD_WP=BIT(0)`, `PTE_MARKER_POISONED=BIT(1)`(UFFDIO_POISON), `PTE_MARKER_GUARD=BIT(2)` — exactly 3 kinds.
A/D in migration entries: `SWP_MIG_YOUNG_BIT`/`SWP_MIG_DIRTY_BIT` swapops.h:62-67, gated by `migration_entry_supports_ad()`:191, read via `softleaf_is_migration_young/dirty()` leafops.h:477,496.

B3. Table lifecycle + locking
Descriptor: `struct ptdesc` mm_types.h:572, static_assert-aliased onto struct page (610,623).
Alloc/free: asm-generic/pgalloc.h chain — `pte_alloc_one(_kernel)`43,97 / `pmd_alloc_one`136 / `pud_alloc_one`204 / `p4d_alloc_one`252 / `__pgd_alloc`277, each via `pagetable_alloc_noprof()`+ level ctor (`pagetable_pte_ctor`mm.h:3540, `_pmd_ctor`3631, `_pud_ctor`3660, `_p4d_ctor`3665, `_pgd_ctor`3670); dtor `pagetable_dtor()`/`_free()`3525/3534. mm/memory.c: `__pte_alloc`464, `__pud_alloc`6684, `__pmd_alloc`6707. x86 overrides `pgd_alloc()` arch/x86/mm/pgtable.c:322 (+`preallocate_pmds()`176 for PAE/user-pgd).
Split lock: `CONFIG_SPLIT_PTE_PTLOCKS` mm/Kconfig:567 gates `ALLOC_SPLIT_PTLOCKS` mm.h:3442; `CONFIG_ARCH_ENABLE_SPLIT_PMD_PTLOCK` mm/Kconfig:576 (x86 selects it, Kconfig:73, when PGTABLE_LEVELS>2 && X86_64||X86_PAE); accessors `ptlock_ptr`/`pte_lockptr` mm.h:3448,3472, `pmd_lockptr`3598; doc Documentation/mm/split_page_table_lock.rst.
Lockless pte_offset_map_*: `__pte_offset_map()` mm/pgtable-generic.c:283 takes `rcu_read_lock()` + `pmdp_get_lockless()` (IRQ-off pairing under CONFIG_GUP_GET_PXX_LOW_HIGH SMP/PREEMPT_RCU, 258-281) — RCU+matching-irqoff (as in GUP-fast) is what protects a concurrently-freed mapped PTE table (comment 260-266); `pte_offset_map_lock/_ro_nolock/_rw_nolock` 309-398.
Levels: `CONFIG_PGTABLE_LEVELS` default 5 for X86_64 arch/x86/Kconfig:428; runtime `pgtable_l5_enabled()` pgtable_64_types.h:31/36 tests X86_FEATURE_LA57; `PGDIR_SHIFT` is runtime var `pgdir_shift` (39 or 48) :42,50 vs fixed P4D_SHIFT=39/PUD_SHIFT=30/PMD_SHIFT=21.
TLB table-free: `tlb_remove_table()` mm/mmu_gather.c:363 / `struct mmu_table_batch`, RCU- or IPI-synced free (`tlb_remove_table_rcu`289 / `tlb_remove_table_sync_one`277).

B4. Hard limits
`MAX_SWAPFILES_SHIFT=5` (32 swap types) include/linux/swap.h:49; `GUP_PIN_COUNTING_BIAS=1<<10` mm.h:1919; `__PHYSICAL_MASK_SHIFT=52` page_64_types.h:50; `__VIRTUAL_MASK_SHIFT=pgtable_l5_enabled()?56:47` :51; `MAX_PHYSMEM_BITS=pgtable_l5_enabled()?52:46` sparsemem.h:29; `PGDIR_SHIFT` runtime 39/48, `P4D_SHIFT=39`, `PUD_SHIFT=30`, `PMD_SHIFT=21`, `PTRS_PER_*=512`.

B5. Suggested page topics
(GUP) "memfd/guest-memfd folio pinning" — `memfd_pin_folios()`/`folio_add_pins()` gup.c:3436,3551 is a distinct CoCo/guest_memfd pin surface, separate from generic pin_user_pages.
(GUP) "Longterm-unpinnable collect/migrate machinery" — `pages_or_folios`-driven `collect_/migrate_longterm_unpinnable_folios()` gup.c:2265,2321 is substantial enough (CMA/movable-zone interplay) for its own page.
(GUP) "GUP consumer flag survey" — spot-checked call sites (iov_iter/io_uring/vfio/iommufd/RDMA umem/KVM/futex/process_vm_access/udmabuf) pick materially different flag combos (LONGTERM, remote, fast-vs-slow); a comparison page adds real value.
(pgtable) "softleaf_t non-present-entry abstraction" — leafops.h is a new unifying layer over swap/migration/device/hwpoison/marker entries, distinct from raw swp_entry_t bit-math (B2).
(pgtable) "5-level paging / LA57 runtime switch" — PGDIR_SHIFT, PTRS_PER_PGD, MAX_PHYSMEM_BITS all become runtime values keyed off `pgtable_l5_enabled()`, a genuinely x86-64-specific mechanism (pgtable_64_types.h).
(pgtable) "CET shadow-stack PTE encoding" — `pte_mkwrite_shstk`/_PAGE_DIRTY_BITS/_PAGE_SAVED_DIRTY (pgtable_types.h:137-139, pgtable.h:460) repurpose the dirty bit for x86 shadow stacks.

## Directory organization

All pages under `docs/mm/` of the skill root, two levels deep, matching the house layout. Ten groups (the prior campaign's nine plus `proc/`):

```
docs/mm/
├── mm-struct/    the per-process address-space object
├── vma/          vm_area_struct: the object, its indexes, tree operations
├── vma-ops/      vm_operations_struct + concrete instances
├── map/          address-space syscalls + the accounting that gates them
├── fault/        the page-fault surface, one page per case, + userfaultfd + the PTE install/uninstall engines
├── gup/          get_user_pages / pin_user_pages: software-initiated access
├── rmap/         reverse mapping
├── pgtable/      x86-64 entry encodings + table lifecycle
├── folio/        the folio-side counters/encoding faults and rmap manipulate
└── proc/         the /proc/<pid> address-space observability ABI
```

Rationale: the request's four H3 areas map to mm-struct, vma(+vma-ops+map), fault, rmap; vma splits three ways because its bullets mix three kinds of page (the object, the ops structure with driver examples, the syscalls); pgtable/folio/gup are the user-approved supporting groups; proc/ is new — the redone inventory showed the observability ABI (maps/smaps/pagemap/PAGEMAP_SCAN/PROCMAP_QUERY) is a distinct, user-space-facing surface that belongs to none of the nine existing groups (pending user decision P2).

## Curated page catalog

Tags: [prompt] = explicit original bullet (numbering reconstructed from prompt.md's tags); [curated] = gap-fill. Rows additionally marked (P2)/(P3)/(P4) exist only if the matching pending user decision lands as include. Every line number is a hint from the 2026-07-11 inventory digests, to re-verify at write time.

### mm-struct/ (7)

| page | scope (anchor symbols) | tag |
|---|---|---|
| overview.md | struct mm_struct field-group tour (mm_types.h:1123-1381): mm_mt/pgd/map_count, mm_users vs mm_count cachelines, rss_stat, layout fields + arg_lock + saved_auxv, write_protect_seq, mm_lock_seq + vma_writer_wait; oddballs noted one-line each (mm_cid, futex_phash block, membarrier_state, lru_gen, ksm counters, mm_id, flexible_array tail + cachep sizing fork.c:3011) | [prompt] |
| locking.md | mmap_lock API (mmap_lock.h:533-631: read/write/killable, read-only trylock, downgrade, asserts, DEFINE_GUARD), mm_lock_seq seqcount + vma_end_write_all (:569), speculation helpers mmap_lock_speculate_try_begin/retry (:134-148) with consumers, lock-ordering blocks (rmap.c:21-52), mm_take_all_locks/mm_drop_all_locks (vma.c:2197/2293) | [prompt] |
| refcount.md | mm_users vs mm_count contract (mm_types.h:1131-1171), mmget/mmget_not_zero/mmput/mmput_async vs mmgrab/mmdrop (+lazy variants sched/mm.h:35-113), lazy-TLB borrowing incl. MMU_LAZY_TLB_REFCOUNT vs SHOOTDOWN (cleanup_lazy_tlbs fork.c:652-711), kthread_use_mm/unuse_mm (kthread.c:1615/1662), active_mm doc | [prompt] |
| lifecycle.md | mm_alloc/mm_init (fork.c:1154/1072: futex_mm_init, mm_alloc_pgd/id/cid, percpu_counter_init_many), copy_mm/dup_mm (fork.c:1556/1515), __mmput teardown order (:1167), exit_mmap (mm/mmap.c:1275, MMF_OOM_SKIP), __mmdrop (:718), init_mm counts (init-mm.c:35-36) | [curated] |
| flags.md | mm_flags_t bitmap (mm_types.h:1116-1119,1273), mm_flags_* helpers (mm.h:877-905) + private word ops (mm_types.h:1384-1411), MMF_* census (:1857-1917) incl. dump filter, MMF_TOPDOWN, MMF_HAS_PINNED, MMF_OOM_SKIP, MDWE flags | [curated] |
| counters.md | rss_stat percpu counters (mm_types.h:1266, NR_MM_COUNTERS=4 mm_types_task.h:26), get/add/inc/dec_mm_counter + get_mm_rss (mm.h:3063-3111), hiwater family (:3111-3161), total/locked/pinned/data/exec/stack_vm fields (:1235-1244) + vm_stat_account, check_mm (fork.c:622-647) | [curated] |
| arch-context.md | x86-64 mm_context_t (asm/mmu.h:25-84): ctx_id/tlb_gen, MM_CONTEXT_* flags, LDT, pkey_allocation_map/execute_only_pkey defaults (mmu_context.h:162-164), LAM lam_cr3_mask/untag_mask, global_asid/asid_transition (INVLPGB), vdso fields; switch_mm level only | [curated] |

### vma/ (19)

| page | scope (anchor symbols) | tag |
|---|---|---|
| overview.md | struct vm_area_struct tour (mm_types.h:913-1057): range/vm_freeptr union, flags union, per-VMA-lock fields (vm_lock_seq :958, vm_refcnt :1030), file/anon fields, shared.rb, anon_name + vm_policy + numab_state + vm_userfaultfd_ctx + pfnmap_track_ctx noted | [prompt 1] |
| allocation.md | vm_area_alloc/vm_area_dup/vm_area_free + init helpers (mm/vma_init.c:28-144), vma_init + vma_dummy_vm_ops placeholder contract (internal.h:177,196) | [prompt 2] |
| slab-rcu.md | vma_state_init (vma_init.c:14-26): kmem_cache_args{use_freeptr_offset, freeptr_offset=vm_freeptr, sheaf_capacity=32}, SLAB_TYPESAFE_BY_RCU reuse semantics for lockless readers, which fields are pre-validation-safe (mm_types.h:907,927) | [prompt 9] |
| refcount-locking.md | vm_refcnt state encoding (mm_types.h:998-1023: 0=detached/1=attached/>1=read-locked), VM_REFCNT_EXCLUDE_READERS_BIT=30 (:764-766), vma_start_read (mmap_lock.c:212) /_read_locked, vma_end_read/vma_refcount_put, vma_start_write(_killable) -> __vma_start_write (:139), attach/detach + __vma_exclude_readers_for_detach (:172), rcuwait writer wait, asserts | [prompt 8] |
| flags.md | vma_flag_t DECLARE_VMA_BIT/_ALIAS enum (mm.h:290-397, VM_SEALED=42, VM_SHADOW_STACK, VM_DROPPABLE), vma_flags_t bitmap + const vm_flags union view (mm_types.h:866-869,939-940), mutators vm_flags_init/reset/set/clear/mod (mm.h:919-992) + readers, why direct assignment is blocked | [prompt 10] |
| maple-tree.md | mm_mt + MM_MT_FLAGS, struct vma_iterator (mm_types.h:1497), vma_iter_* families (mm.h:1312-1382, mm/vma.h:277-637) mapped to mas_* calls, __mt_dup, validate_mm; API-and-contracts only, no node anatomy | [prompt 6] |
| insertion.md | the generic register-a-new-VMA surface: vma_link/vma_link_file (vma.c:1824), insert_vm_struct (:3273), vma_iter_store_new/bulk_store (vma.h:610), map_count + sysctl_max_map_count gate sites; __mmap_new_vma referenced as a caller only (owned by map/mmap.md per review amendment 4) | [prompt 3a] |
| insertion-algorithm.md | maple-tree store under the iterator: prealloc sizing, wr_mas store paths (slot store/split/spanning), RCU-safe node replacement; bounded to paths reachable from vma_iter_store/prealloc | [prompt 3b] |
| removal.md | do_vmi_munmap/do_vmi_align_munmap (vma.c:1611/1564), struct vma_munmap_struct (vma.h:34), vms_gather/complete/abort_munmap_vmas (vma.c:1379/1311/2340), remove_vma, unlink_vma_file_batch (vma.h:28, batch of 8) | [prompt 4a] |
| removal-algorithm.md | unmap_region (vma.c:478) + struct unmap_desc (vma.h:158), maple NULL-store/erase, mmu_gather / tlb_gather_mmu / unmap_vmas / free_pgtables (internal.h:201,515), tlb_remove_table (mmu_gather.c:363) one-line | [prompt 4b] |
| traversal.md | find_vma/find_vma_prev/find_vma_intersection (mmap.c:902/925/883), vma_lookup, vma_find/next/prev, for_each_vma(_range), lock_vma_under_rcu (mmap_lock.c:296) + lock_next_vma (:369) as lookup API | [prompt 5a] |
| traversal-algorithm.md | mas_walk/mas_find node descent, RCU reader protocol, gap search (vma_iter_area_lowest/highest -> mas_empty_area(_rev)); bounded to the read half; own node-anatomy primer | [prompt 5b] |
| split.md | __split_vma/split_vma (vma.c:497/590), may_split veto census, max_map_count gate, vma_adjust_trans_huge/hugetlb_split boundary fixups | [prompt 13] |
| merge.md | struct vma_merge_struct + VMG_STATE/VMG_VMA_STATE (vma.h:69/236), vma_merge_new_range (vma.c:1046), new/unfaulted-range merge for mmap/brk/expand | [prompt 14] |
| merge-existing.md | vma_merge_existing_range (vma.c:805) + commit_merge (:728): left/right/both case matrix driven by vma_modify_* callers | [curated; split of 14] |
| adjust.md | vma_expand/vma_shrink (vma.c:1151/1228), copy_vma (:1844), relocate_vma_down (vma_exec.c:19) | [prompt 15] |
| modify-spine.md | init_(multi_)vma_prep/vma_prepare/vma_complete (vma.c:288/335), vma_modify (:1649) + vma_modify_flags/_name/_policy/_flags_uffd (:1689-1738); one-paragraph note on the descriptor-object pattern (vmg/vms/unmap_desc/mmap_state/vma_prepare) | [curated; fills blank bullet 7] |
| fork-dup.md | dup_mmap (mmap.c:1732): dual write-lock, __mt_dup (:1758) + vma_iter_bulk_store (:1817), per-VMA hooks (:1787-1817: vm_area_dup, vma_dup_policy, dup_userfaultfd, anon_vma_fork, hugetlb_dup_vma_private), copy_page_range + write_protect_seq, VM_WIPEONFORK | [curated] |
| stack-growth.md | expand_upwards/expand_downwards (vma.c:3090/3176), expand_stack, stack_guard_gap (256 pages = 1 MiB, mmap.c:939-952), VM_GROWSDOWN/UP, create_init_stack_vma (vma_exec.c:107) | [curated] |

### vma-ops/ (7)

| page | scope | tag |
|---|---|---|
| vm-operations.md | struct vm_operations_struct (mm.h:749) callback-by-callback with invocation sites, mapped onto the VMA lifecycle; instance census incl. shm_vm_ops (ipc/shm.c:683) and vma_dummy_vm_ops; contrast with the pre-link vm_area_desc/.mmap_prepare contract | [prompt 11] |
| amdgpu-gem.md | amdgpu_gem_vm_ops (amdgpu_gem.c:148): GEM mmap lifecycle, fault via TTM helpers, open/close refcounting, access | [prompt 12.1] |
| hugetlb.md | hugetlb_vm_ops (hugetlb.c:4828: fault, open/close reservation lifecycle, may_split alignment, pagesize) + hugetlbfs_file_mmap_prepare (fs/hugetlbfs/inode.c:105) + hugetlb_reserve_pages (:160); states there is a .fault (v7.0) and where the handle_mm_fault divert bypasses handle_pte_fault | [prompt 12.2] |
| generic-file.md | generic_file_vm_ops (filemap.c:3982): filemap_fault/filemap_map_pages/filemap_page_mkwrite; generic_file_mmap_prepare (:4001) | [curated; realizes 12.3] |
| special-mapping.md | special_mapping_vmops (mmap.c:1416) + struct vm_special_mapping, _install_special_mapping, x86-64 vdso/vvar installers, get_gate_vma | [curated] |
| shmem.md | shmem_vm_ops/shmem_anon_vm_ops (shmem.c:5309/5318), shmem_fault, MAP_SHARED-anonymous via shmem_zero_setup, mmap_prepare adoption (shmem.c:2959); memfd_create noted one-line as a shmem-file producer | [curated] |
| secretmem.md | secretmem_vm_ops (secretmem.c:111: fault only), memfd_secret(2) mapping constraints (mlock_future_ok secretmem.c:129, no GUP-fast via gup_fast_folio_allowed cross-ref), fault + zeroing semantics | [curated] (P4) |

### map/ (14 after Phase 3: pkeys and shadow-stack rows removed, their scopes folded)

| page | scope | tag |
|---|---|---|
| mmap.md | end-to-end pipeline: SYSCALL_DEFINE6 (sys_x86_64.c:82) -> ksys_mmap_pgoff (mmap.c:567, MAP_HUGETLB pre-handling :567-604) -> vm_mmap_pgoff (util.c:565) -> do_mmap (mmap.c:335, MAP_POPULATE/LOCKED populate handoff :560) -> mmap_region/__mmap_region (vma.c:2818/2720), struct mmap_state (vma.c:10), __mmap_setup/__mmap_new_vma/__mmap_complete, call_mmap_prepare (:2638) + struct vm_area_desc + legacy .mmap shim (util.c:1141-1193); MAP_DROPPABLE (:504-532) and remap_file_pages emulation (:1085) one-section each; address selection + tree store as handoffs | [prompt 16] |
| address-space-layout.md | arch_pick_mmap_layout (x86 mmap.c:122), mmap_is_legacy (:62) + personality bits, arch_rnd/mmap_base (:70/:82), __get_unmapped_area dispatch (mmap.c:812: file hook, shmem anon-shared, THP hook huge_memory.c:1234, arch fallbacks sys_x86_64.c:127/167), vm_unmapped_area (mmap.c:664), TASK_SIZE/LA57/DEFAULT_MAP_WINDOW (page_64_types.h:53-54) + hint rule (sys_x86_64.c:111, x86 mmap.c:197) | [curated] |
| munmap.md | munmap syscall (mmap.c:1075) -> __vm_munmap (vma.c:3251) over the vms_* machinery as a black box, MAP_FIXED-driven unmap, sealing checks (vma.c:1403/1423), userfaultfd unmap notification | [prompt 17] |
| brk.md | sys_brk (mmap.c:116), do_brk_flags (vma.c:2866), check_data_rlimit (mmap.c:150), brk fast path vs full mmap | [curated] |
| mremap.md | sys_mremap (mremap.c:1965) -> do_mremap (:1915), struct vma_remap_struct, mremap_to (:1367)/mremap_at (:1554), move_vma (:1270) + move_page_tables + pagetable_move_control, MREMAP_DONTUNMAP, sealing (:1665) | [curated] |
| mprotect.md | sys_mprotect/pkey_mprotect (mprotect.c:948/956), do_mprotect_pkey (:801), mprotect_fixup (:695), change_protection walk, full x86 pkey mechanism (pkey_alloc/free :962/992, mm_pkey_* map + execute_only_pkey mmu_context.h:162-164, arch_set_user_pkey_access/PKRU, X86_PF_PK cross-ref), MDWE map_deny_write_exec (vma.c:2828, mprotect.c:905) + PR_SET_MDWE, sealing (:706); accepted heavy page per Phase 3 decision 11 (pkeys split declined) | [curated] |
| mlock.md | mlock/mlock2/munlock/mlockall/munlockall (mlock.c:659-798), do_mlock (:611), apply_vma_lock_flags (:514)/apply_mlockall_flags (:722)/mlock_fixup, can_do_mlock (:40) + RLIMIT_MEMLOCK sites, VM_LOCKED/VM_LOCKONFAULT, populate handoff; folio-side mlock state machine (mlock.c:242/290, internal.h:1111-1141, mlock_count) | [curated] |
| madvise.md | madvise(2) behavior engine (madvise.c:2035/2013), struct madvise_behavior(_range) (:66/:61), madvise_vma_behavior (:1345), behavior classes (VMA-changing vs page-acting), guard regions MADV_GUARD_INSTALL/REMOVE (:1121/:1250), can_madvise_modify + sealing (:1297-1334), MADV_DONTDUMP/coredump fold, MADV_POPULATE handoff to gup/faultin; process_madvise one-line pointer | [curated] |
| process-madvise.md | remote madvise (review amendment 11, sweep-rated page-worthy): process_madvise (madvise.c:2107) + vector_madvise (:2042), pidfd + PTRACE_MODE_READ_FSCREDS + CAP_SYS_NICE model, iovec loop semantics, which behaviors are remote-legal, shared machinery deferred to madvise.md (seam madvise_do_behavior) | [curated] (P4) |
| mseal.md | sys_mseal (mseal.c:187), do_mseal (:139), mseal_apply (:55), range_contains_unmapped (:39), vma_is_sealed (vma.h:662), check-site census across mprotect/munmap/mremap/madvise | [curated] |
| msync.md | sys_msync (msync.c:32): MS_SYNC/ASYNC/INVALIDATE semantics, per-VMA walk + vfs_fsync_range dispatch, VM_LOCKED interaction; writeback internals out of scope (sibling campaign) | [curated] (P4) |
| mincore.md | sys_mincore (mincore.c:292), do_mincore + mincore_walk_ops pagewalk, swap/pagecache residency probes, permission model | [curated] (P4) |
| mempolicy.md | VMA policy surface: mbind (mempolicy.c:1827)/do_mbind (:1486), set_mempolicy (:1854), set_mempolicy_home_node (:1760) + mbind_range (:1039), get_mempolicy (:1983), vm_ops get_policy/set_policy (:2018-2065) + policy at fault/alloc handoff, numa_maps display (task_mmu.c:3297); move_pages/migrate_pages out of scope (page migration) | [curated] (P4) |
| accounting.md | what gates the syscalls: __vm_enough_memory (util.c:930) + security_vm_enough_memory_mm, overcommit sysctls + vm_commit_limit (:875), may_expand_vm (mmap.c:1335) + RLIMIT_AS/DATA, RLIMIT_MEMLOCK + locked_vm vs pinned_vm (mm_types.h:1239-1240), VM_ACCOUNT charge/uncharge sites (vma.c:2429-3303), mlock_future_ok (mmap.c:229), max_map_count gate census | [curated; promoted from P4 per review amendment 12 — base pages defer their gate mechanics here, so it cannot be optional] |
(shadow-stack.md removed per Phase 3 decision 11: map_shadow_stack/VM_SHADOW_STACK fold across vma/flags.md, fault/x86-64-entry.md, pgtable/x86-64-entries.md)

### fault/ (21)

| page | scope | tag |
|---|---|---|
| x86-64-entry.md | exc_page_fault (fault.c:1483) -> handle_page_fault (:1461) -> do_user_addr_fault (:1206), X86_PF_* (trap_pf.h:20-30), access_error (:1048-1113: pkeys, SGX, shadow stack), retry loop (:1356-1411) + fault_signal_pending, signal delivery (:776-906), vsyscall emulation (:1316) + extable fixup (:726) one-section each; do_kern_addr_fault one-sentence scope note | [prompt] |
| vma-lock-path.md | lock_vma_under_rcu (mmap_lock.c:296) lookup-and-revalidate over vma_start_read (:212), lock_mm_and_find_vma fallback (:496), sanitize_fault_flags combos, COMPLETE bail catalog: 4 guards / 10 sites (vmf_can_call_fault memory.c:3698 x3, __vmf_anon_prepare :3723 x5, device-private :4734, huge-pmd device-private huge_memory.c:1384) | [curated] |
| handle-mm-fault.md | handle_mm_fault (memory.c:6589-6654: sanitize, memcg enter, lru_gen, hugetlb divert :6621-6622, mm_account_fault :6650) + __handle_mm_fault (:6355-6456) full PUD/PMD branch census (huge create/wp/set-accessed, device-private, migration wait, fix_spurious_fault); stops at the handle_pte_fault call | [prompt] |
| pte-dispatch.md | handle_pte_fault (:6273-6347): predicate->handler table, orig_pte snapshot rules, access-dirty fallthrough + fix_spurious_fault(PGTABLE_LEVEL_PTE) | [curated] |
| vm-fault.md | struct vm_fault field-by-field (mm.h:698-742), enum fault_flag (mm_types.h:1735-1749), retry-combo comment block (:1712-1730), vm_fault_reason codes (:1618-1641) | [prompt; absorbs flags-codes scope] |
| anonymous.md | do_anonymous_page (:5217-5330), alloc_anon_folio mTHP order walk (:5127-5210), zero-page read case, uffd-missing sites | [prompt] |
| file-dispatch.md | do_fault (:5903-5945) router + __do_fault (:5337), no->fault SIGBUS path, vmf_can_call_fault | [prompt] |
| file-read.md | do_read_fault (:5779) + fault-around (should_/do_fault_around :5733-5766, default 16 pages/64 KiB, clamp [1 page, 512 pages], pow2 rounding :5687-5700), filemap_map_pages handoff | [prompt] |
| file-cow.md | do_cow_fault (:5811), cow_page prealloc, copy_mc poison handling, VM_FAULT_DONE_COW | [prompt] |
| file-shared.md | do_shared_fault (:5853), do_page_mkwrite protocol, fault_dirty_shared_page/dirty throttle handoff | [prompt] |
| finish-fault.md | finish_fault (:5556-5671), set_pte_range (:5497), do_set_pmd THP body (:5407) vs stub (:5483), large-folio fitting (:5628-5637) | [curated] |
| wp.md | do_wp_page (:4149-4242): uffd intercept (:4161), PageAnonExclusive fast reuse, wp_can_reuse_anon_folio (:4086), wp_page_reuse (:3664) vs wp_page_copy (:3758) vs wp_page_shared (:3972)/wp_pfn_shared (:3950) | [prompt] |
| swap-in.md | do_swap_page (:4706-5113): softleaf classification of non-present entries (:4725-4777) with one-table early-exit summary (migration wait, device-exclusive :4375, device-private + VMA-lock bail, hwpoison, handle_pte_marker :4496 incl. guard/poison/uffd-wp re-dispatch), then the genuine swap-in path (swapcache lookup, readahead vs SWP_SYNCHRONOUS_IO, mTHP, ksm copy, exclusivity restore); swap-cache/readahead internals = sibling-campaign seam | [prompt] |
| numa.md | do_numa_page (:6048-6137), numa_migrate_check (:5947), mpol_misplaced/migrate_misplaced_folio handoffs, PTE rebuild; PMD analogue do_huge_pmd_numa_page (huge_memory.c:2185-2259) as its own section (review amendment 8: absorbed, too thin to stand alone) | [prompt] |
| thp-anon.md | do_huge_pmd_anonymous_page (huge_memory.c:1461), __do_huge_pmd_anonymous_page (:1323), huge zero page path, uffd sites | [curated] |
| thp-wp.md | do_huge_pmd_wp_page (:2060), do_huge_zero_wp_pmd (:2028), reuse vs __split_huge_pmd fallback | [curated] |
| zap.md | the per-PTE uninstall engine (review amendment 1): zap_pte_range (memory.c:1895), zap_pmd/pud/p4d levels, unmap_page_range (:2076), zap_page_range_single (:2229), struct zap_details, per-PTE duties (folio_remove_rmap_ptes, softleaf/swap-entry freeing, RSS/dirty accounting, TLB batching, uffd-wp marker retention), driver census (munmap via unmap_vmas, MADV_DONTNEED/FREE madvise.c:1201, truncation memory.c:4248, OOM reaper oom_kill.c:563) | [curated] |
| hugetlb.md | hugetlb_fault (hugetlb.c:5972)/hugetlb_no_page (:5722)/hugetlb_wp (:5450), fault-mutex table (num_fault_mutexes = roundup_pow_of_two(8*ncpus), :4187-4194) + hash (:5949), reservation consumption + restore_reserve_on_error, divert point identical wording with handle-mm-fault/vma-ops pages | [curated] |
| userfaultfd.md | handle_userfault (fs/userfaultfd.c:381) trap protocol (sleep/wake, VM_FAULT_RETRY contract) + ALL 10 interception sites (memory.c x4, huge_memory.c x2, hugetlb.c x2 via wrapper :5688, shmem.c x2), uffd-wp marker re-dispatch | [curated] |
| userfaultfd-api.md | the fd/API side: userfaultfd(2) + ctx lifecycle, UFFDIO_API/REGISTER/UNREGISTER (fs/userfaultfd.c:1261+, dispatch :2046-2073) + vma_modify_flags_uffd path, resolve ops UFFDIO_COPY/ZEROPAGE/CONTINUE/POISON/WRITEPROTECT/MOVE (mfill_atomic family mm/userfaultfd.c:868+, move_pages_pte), minor faults; registration-visible VMA flag effects | [curated] (P3) |
| pfn-mapping.md | driver-installed mappings, both timings (review amendment 2): mmap-time remap_pfn_range (memory.c:3147)/io_remap_pfn_range/vm_insert_page(s)/vm_map_pages/vm_iomap_memory, fault-time vmf_insert_pfn(_prot)/vmf_insert_page_mkwrite/vmf_insert_mixed(_mkwrite) (:2626-2856), PFNMAP vs MIXEDMAP + pfnmap_track_ctx cross-ref, huge variants vmf_insert_pfn_pmd/folio_pmd/pfn_pud/folio_pud (huge_memory.c:1607/1633/1715/1749) for drivers' huge_fault | [curated] |

### gup/ (8)

| page | scope | tag |
|---|---|---|
| overview.md | API census: get_user_pages family (gup.c:2603-3289) vs pin_user_pages family (:3310-3408, no pin_fast_only), unpin family (:185-449), memfd_pin_folios (:3436) + folio_add_pins (:3551), get_dump_page (:2187), get-vs-pin semantics + per-consumer population table (iov_iter, io_uring, vfio, iommufd, RDMA umem, KVM, futex, process_vm_access, udmabuf — verified sites) | [curated] |
| foll-flags.md | public FOLL_* (mm_types.h) + internal FOLL_* (internal.h:1547), is_valid_gup_args (gup.c:2500) rule table (GET^PIN, LONGTERM=>PIN, LONGTERM+P2PDMA illegal, FOLL_UNLOCKABLE), fast-path accepted mask | [curated] |
| slow-path.md | __get_user_pages (:1354): gup_vma_lookup (:1265), check_vma_flags (:1200), follow_page_mask descent (:1007->:942->:898->:802), -EMLINK unshare feed into faultin_page, get_gate_page (:1030), __get_user_pages_locked retry machine (:1649); mmap_lock-only regime (no per-VMA-lock GUP at v7.0) | [curated] |
| fast-path.md | gup_fast_fallback (:3175)/gup_fast (:3129): irq-off constraints, write_protect_seq raw-seqcount fork-vs-pin guard (:3141/:3165), descent (:3092-2829) with lockless reads + split-race re-reads, gup_fast_folio_allowed (:2738: secretmem/dirty-file rejects), x86-64 sync story (IRQ-off vs RCU/IPI table free) | [curated] |
| pinning.md | GUP_PIN_COUNTING_BIAS=1<<10 (mm.h:1919) vs _pincount + folio_has_pincount (:2323), try_grab_folio (:140)/try_grab_folio_fast (:517)/gup_put_folio, folio_maybe_dma_pinned (:2355), gup_must_unshare (internal.h:1571) + all 6 enforcement sites, fork+COW story (MMF_HAS_PINNED gup.c:479, write_protect_seq), sanity_check_pinned_pages (:29); gup_test noted | [curated] |
| longterm.md | folio_is_longterm_pinnable (mm.h:2413), struct pages_or_folios (gup.c:2207), collect/migrate_longterm_unpinnable_folios (:2265/:2321), check_and_migrate orchestration (:2386/:2465) + retry semantics, CMA/movable interplay, device-coherent + FOLL_PCI_P2PDMA, memfd_pin_folios interaction | [curated] |
| faultin.md | fault-in-without-pages surface: faultin_page (:1087, FOLL->FAULT_FLAG translation), faultin_page_range (:1887, MADV_POPULATE), populate_vma_page_range (:1813) + __mm_populate (:1925) (mlock/MAP_POPULATE), fixup_user_fault (:1564), fault_in_writeable/readable family (:2046-2147) | [curated] |
| folio-walk.md | folio_walk_start/end (pagewalk.h:196-205, pagewalk.c:902), struct folio_walk + levels, the follow_page() replacement story, caller census (ksm/migrate/rmap/huge_memory) | [curated] |

### rmap/ (12)

| page | scope | tag |
|---|---|---|
| anon-vma.md | struct anon_vma (rmap.h:32-68), slab SLAB_TYPESAFE_BY_RCU (rmap.c:543-556), alloc/free (:90/:110), refcount API (internal.h:205-216), lock API (internal.h:218-246, root-rwsem), folio_get_anon_vma (:587) vs folio_lock_anon_vma_read (:633) RCU contracts | [prompt] |
| anon-vma-chain.md | struct anon_vma_chain (rmap.h:83-92): same_vma list vs rb interval-tree membership, avc slab, assign/link (:150), interval tree (interval_tree.c:75-103) | [prompt] |
| anon-setup.md | __anon_vma_prepare (:185-233), find_mergeable_anon_vma (vma.c:2003), anon_vma_clone + enum vma_operation (internal.h:251-259, rmap.c:320-371), maybe_reuse_anon_vma (:270-288), anon_vma_fork (:378-442), unlink_anon_vmas two-pass teardown (:479-541) with per-operation caller census | [prompt] |
| file-rmap.md | i_mmap interval tree + i_mmap_rwsem API (fs.h), vma_interval_tree_* (interval_tree.c:23-59), unmap_mapping_folio/pages/range (memory.c:4283-4354, 33 callers), hugetlb huge_pmd_share/unshare over i_mmap (hugetlb.c:6878-6973, x86-64 active) | [prompt] |
| add-remove.md | folio_add_new_anon_rmap (:1636), folio_add_anon_rmap_ptes/pmd (:1589/:1610), folio_add_file_rmap_ptes/pmd/pud (:1723+), folio_remove_rmap_* (:1891+), hugetlb variants (:3120+ and rmap.h:435-490), dup/share inlines (rmap.h:492-840, enum pgtable_level), folio_move_anon_rmap (:1434), rmap_t/RMAP_EXCLUSIVE, caller sites | [curated] |
| walk.md | rmap_walk(_locked) dispatch (:3093/:3104), rmap_walk_control callbacks (rmap.h:951-965), anon backend + lock (:2914/:2956), file backend (:3023/:3075), rmap_walk_ksm at dispatch-contract level (ksm.c:3152) | [curated] |
| pvmw.md | struct page_vma_mapped_walk + PVMW_SYNC/MIGRATION + PVMW_PGTABLE_CROSSED result flag (rmap.h:855-874), core walk (page_vma_mapped.c:180-335), softleaf migration matching, hugetlb short-circuit, page_mapped_in_vma (:348), caller census (6) | [curated] |
| try-to-unmap.md | try_to_unmap(_one) (:2386/:1978), TTU_* flags (rmap.h:94-105), batched unmap + TLB flush batching (rmap.c:704-748, tlbflush_unmap_batch, x86-64 always on), lazyfree | [curated] |
| try-to-migrate.md | try_to_migrate(_one) (:2731/:2407), migration entries + A/D preservation, remove_migration_pte/ptes (migrate.c:346/455), make_device_exclusive (:2808-2902) + restore_exclusive_pte (memory.c:881) | [curated] |
| folio-referenced.md | folio_referenced(_one) (:1059/:917), folio_referenced_arg, vmscan callers; reclaim decisions out of scope (sibling campaign) | [curated] |
| mkclean.md | folio_mkclean (:1193), page_vma_mkclean_one, mapping_wrprotect_range (:1267), pfn_mkclean_range (:1304); writeback consumers named, internals out of scope | [curated] |
| locking.md | rmap.c:21-52 lock-ordering block explained item-by-item, root-rwsem rule, RCU freeing in anon_vma_free, interaction with vma_start_write ordering | [curated] |

### pgtable/ (4)

| page | scope | tag |
|---|---|---|
| x86-64-entries.md | _PAGE_BIT_*/_PAGE_* census (pgtable_types.h:10-143 incl. PROTNONE=GLOBAL-when-not-present, soft-dirty, SAVED_DIRTY/CET, PKEY bits, NX), swap-PTE bit reuse (:108-118), protection_map/vm_get_page_prot (pgprot.c:8/:35), mk/accessor families (mk_pte now mm.h:2268), PSE/PAT leaf encoding, pte_mkwrite_shstk | [curated] |
| softleaf.md | leafops.h softleaf_t + enum softleaf_type (:19-35) full classification (swap, migration r/o-excl/w, device-private r/w, device-exclusive, hwpoison, marker), softleaf_from_pte/pmd, swp_entry_t type/offset split (swapops.h:27-42, SWP_TYPE_SHIFT=58), the 3 PTE markers (UFFD_WP/POISONED/GUARD, swapops.h:281-300), migration A/D bits (:62-67); encoding only, no fault behavior | [curated] |
| paging-levels.md | 4-vs-5-level x86-64 paging as a runtime property (review amendment 9): pgtable_l5_enabled (pgtable_64_types.h:31/36), runtime pgdir_shift/ptrs_per_p4d vs fixed P4D/PUD/PMD shifts (:42-80), __VIRTUAL_MASK_SHIFT/MAX_PHYSMEM_BITS alternatives (page_64_types.h:51, sparsemem.h:29), TASK_SIZE_MAX/task_size_max()/DEFAULT_MAP_WINDOW (page_64_types.h:53-54, page_64.h:138), the level-folding helpers; boot-time LA57 selection one paragraph | [curated] |
| alloc-locking.md | struct ptdesc (mm_types.h:572), pgalloc chain + level ctors/dtors (asm-generic/pgalloc.h, mm.h:3525-3670), x86 pgd_alloc (pgtable.c:322), split PTE/PMD ptlock configs + accessors (mm/Kconfig:567/576, mm.h:3442-3598), pte_offset_map_* lockless rules (pgtable-generic.c:258-398), tlb_remove_table one-line; level-count constants deferred to paging-levels.md | [curated] |

### folio/ (3)

| page | scope | tag |
|---|---|---|
| mapping-encoding.md | FOLIO_MAPPING_ANON/ANON_KSM/KSM/FLAGS (page-flags.h:717-720), pointer packing in __folio_set_anon (rmap.c:1457-1480), folio_test_anon/ksm, folio->index + linear_page_index (pagemap.h:1068) | [curated] |
| refcount-mapcount.md | the counter cluster (mm_types.h:430-487: _mapcount/_large_mapcount/_nr_pages_mapped/_entire_mapcount/_pincount), folio_mapcount/folio_mapped (mm.h:1594/1613), ENTIRELY_MAPPED (internal.h:107-112), PageAnonExclusive=PG_owner_2 (page-flags.h:139-152) + rules, page_type/PGTY encoding (:925-950), new CONFIG_PAGE_MAPCOUNT vs CONFIG_NO_PAGE_MAPCOUNT split (mm/Kconfig:954-971); counters-at-rest + invariants only | [curated] |
| mm-id.md | CONFIG_MM_ID (mm/Kconfig:791, selected by THP): _mm_id[2]/_mm_ids/_mm_id_mapcount[2], bit-spinlock protocol (rmap.h:112-120), folio_maybe_mapped_shared (mm.h:2613-2637), mm_alloc_id/mm_free_id ida (fork.c:595-619), MM_ID_* constants | [curated] |

### proc/ (2)

| page | scope | tag |
|---|---|---|
| maps-smaps.md | /proc/<pid>/maps seq machinery + per-VMA-lock lockless iteration (task_mmu.c:159 branch -> lock_next_vma mmap_lock.c:369; smaps still mmap_read_lock), show_map fields incl. [anon:...] naming (+ prctl PR_SET_VMA fold), smaps/smaps_rollup page-walk aggregation (:1370/:1397), PROCMAP_QUERY ioctl (:654/:824, uapi fs.h:507) | [curated] (P2) |
| pagemap.md | /proc/<pid>/pagemap read ABI + entry encoding (task_mmu.c:2308+), soft-dirty tracking + clear_refs (:1768), PAGEMAP_SCAN ioctl (do_pagemap_scan :3021, dispatch :3100) incl. uffd-async-wp use; soft-dirty PTE bit encoding owned by pgtable/x86-64-entries (seam: pte_soft_dirty helpers) | [curated] (P2) |

### Fold-in adjudications (topics that do NOT get pages, with their absorbing page)

mm_cid, futex_phash block, membarrier_state, lru_gen fields, ksm counters -> mm-struct/overview.md field tour. mm_take_all_locks + speculation helpers -> mm-struct/locking.md. global_asid/INVLPGB, LAM -> mm-struct/arch-context.md. mm_id allocation -> folio/mm-id.md (+ lifecycle one-line). anon_vma_name struct -> vma/overview.md + proc/maps-smaps.md display. pfnmap_track_ctx -> vma/overview.md + fault/pfn-insert.md. descriptor-object pattern -> one paragraph in vma/modify-spine.md. vm_area_desc/.mmap_prepare remodel -> map/mmap.md (pipeline) + vma-ops/vm-operations.md (contract contrast). gap search write half -> map/address-space-layout.md; read-side mas_empty_area -> vma/traversal-algorithm.md. copy_page_range/write_protect_seq -> vma/fork-dup.md (fork side) + gup/pinning.md (GUP side). create_init_stack_vma/relocate_vma_down -> vma/stack-growth.md + vma/adjust.md. unlink_vma_file_batch -> vma/removal.md. mmu_gather -> vma/removal-algorithm.md. shm_vm_ops/shmat, secretmem_vm_ops, vma_dummy_vm_ops -> instance census in vma-ops/vm-operations.md (secretmem additionally its own page if P4). memfd_create -> one-line producer note in vma-ops/shmem.md; fd/sealing side out of scope — RATIONALE (review amendment 3, overriding the sweep's page-worthy rating): memfd_create is fd creation, not an address-space operation; every mapping-side behavior it produces is owned by vma-ops/shmem.md and vma-ops/hugetlb.md. remap_file_pages, MAP_DROPPABLE, MAP_HUGETLB pre-handling, MAP_POPULATE handoff -> map/mmap.md. personality layout bits -> map/address-space-layout.md. PR_SET_MDWE/map_deny_write_exec -> map/mprotect.md (+ mmap mention). pkey syscalls -> map/pkeys.md if P4 lands, else fold back into map/mprotect.md. process_madvise -> map/process-madvise.md if P4 lands, else fold back into map/madvise.md. coredump filter/MADV_DONTDUMP -> map/madvise.md. numa_maps -> map/mempolicy.md. PROCMAP_QUERY -> proc/maps-smaps.md. prctl PR_SET_VMA -> proc/maps-smaps.md + vma/overview.md. do_huge_pmd_device_private -> fault/handle-mm-fault.md branch census + device-private cross-ref in fault/swap-in.md. vsyscall emulation + extable fixup -> fault/x86-64-entry.md. fault accounting/mm_account_fault + memcg-OOM -> fault/handle-mm-fault.md. PTE guard/poison/uffd-wp markers -> pgtable/softleaf.md (encoding) + fault/swap-in.md (dispatch) + fault/userfaultfd.md (uffd-wp protocol) + map/madvise.md (guard install/remove). memfd_pin_folios -> gup/overview.md + gup/longterm.md. gup_test -> gup/pinning.md + gup/longterm.md. memalloc_pin_save -> gup/longterm.md. KSM rmap backend -> dispatch-contract level in rmap/walk.md. TLB unmap-flush batching -> rmap/try-to-unmap.md (+ fault/zap.md names the batch producer). device-exclusive -> rmap/try-to-migrate.md. page_mapped_in_vma -> rmap/pvmw.md. mlock folio machinery + mlock_count -> map/mlock.md. hugetlb PMD sharing -> rmap/file-rmap.md. unmap_mapping_range family -> rmap/file-rmap.md (per-PTE mechanics deferred to fault/zap.md). CET PTE encoding -> pgtable/x86-64-entries.md (+ map/shadow-stack.md if P4). CONFIG_NO_PAGE_MAPCOUNT split -> folio/refcount-mapcount.md. do_huge_pmd_numa_page -> section of fault/numa.md (review amendment 8; thp-anon/thp-wp stay separate pages — rejected 8b, each mirrors a substantial base handler). remap_pfn_range/vm_insert_page family -> fault/pfn-mapping.md row (supersedes any fold). LA57 runtime constants -> pgtable/paging-levels.md row (supersedes the alloc-locking fold; address-space-layout defers via task_size_max()).

### Projected totals (post-review)

Base catalog: 89 pages (87 carried rows - thp-numa merged into numa + fault/zap + pgtable/paging-levels + accounting promoted to base). Pending-decision rows: +2 (P2 proc), +1 (P3 uffd-api), +7 (P4: msync, mincore, mempolicy, shadow-stack, secretmem, pkeys, process-madvise) = 99 at full inclusion. Tag census at full inclusion: 38 [prompt], 61 [curated]. Ten of the 89 base rows already exist on disk (docs/mm/vma/, see Draft reuse map).

### Overlap boundary rules (one statement per sibling cluster; seam symbols named)

1. map/munmap.md owns the syscall surface treating vms_* as a black box; vma/removal.md owns the vms_* object pipeline (gather/complete/abort); vma/removal-algorithm.md owns the physical orchestration (maple NULL-store, unmap_region + unmap_desc, mmu_gather setup/finish, free_pgtables); fault/zap.md owns the per-PTE uninstall engine every driver funnels into. Seams: vms_clear_ptes/unmap_region (removal -> removal-algorithm), unmap_page_range/zap_page_range_single (removal-algorithm, map/madvise, rmap/file-rmap -> fault/zap).
2. vma-ops/hugetlb.md owns mapping-time callbacks + reservation setup; fault/hugetlb.md owns the fault path and reservation consumption; the handle_mm_fault divert (memory.c:6621-6622) reads identically in handle-mm-fault.md, fault/hugetlb.md, vma-ops/hugetlb.md — vma-ops/hugetlb.md (written first, B12) is the canonical wording the other two copy verbatim (review amendment 14).
3. vma/refcount-locking.md owns the vm_refcnt mechanism (encoding, acquire/release, exclude-readers, rcuwait); fault/vma-lock-path.md owns the consumer protocol (lookup-and-revalidate, fallback, bail catalog); vma/traversal.md lists lock_vma_under_rcu/lock_next_vma as lookup API only. Seam: vma_start_read (mmap_lock.c:212).
4. vma/maple-tree.md is API-and-contracts only, no node anatomy; insertion-algorithm.md owns the write half of node anatomy bounded to vma_iter_store/prealloc-reachable paths; traversal-algorithm.md owns the read half bounded to mas_walk/mas_find/mas_empty_area(_rev); each algorithm page carries its own primer.
5. pgtable/softleaf.md owns non-present encoding/classification only; fault/swap-in.md owns runtime dispatch + genuine swap-in; fault/userfaultfd.md owns the uffd trap protocol; fault/userfaultfd-api.md (P3) owns the fd/ioctl surface. Seams: softleaf_from_pte (encoding->dispatch), handle_userfault (trap), userfaultfd_register/mfill_atomic (API).
6. folio/refcount-mapcount.md owns counters-at-rest + invariants; folio/mm-id.md owns the sharedness mechanism; rmap/add-remove.md owns the mutation API with locking preconditions and caller inventories. Seam: folio_add_anon_rmap_ptes.
7. mm-struct/locking.md owns concurrency (mmap_lock, mm_lock_seq, ordering); refcount.md owns liveness (mm_users/mm_count, lazy TLB); lifecycle.md owns construction/teardown ordering. Seam: mmput -> __mmput.
8. map/mmap.md owns the one-syscall pipeline including __mmap_setup/__mmap_new_vma/__mmap_complete (review amendment 4) and is the canonical walkthrough of the call_mmap_prepare/vm_area_desc contract (review amendment 13, vma-ops/vm-operations.md contrasts and cites without re-walking); map/address-space-layout.md owns where mappings go; vma/insertion.md owns the generic register-a-new-VMA surface and references __mmap_new_vma as a caller only. Seams: __get_unmapped_area, __mmap_new_vma, vma_iter_store_new.
9. fault/handle-mm-fault.md stops at the handle_pte_fault call; fault/pte-dispatch.md owns handle_pte_fault itself. The three do_*_fault pages (file-read/file-cow/file-shared) stop at the finish_fault call; fault/finish-fault.md opens it (seam: finish_fault/set_pte_range; review amendment 6). House rule for fault/ pages: the entry-chain recap is at most one short paragraph per page.
10. map/accounting.md (P4) owns the gate mechanisms (__vm_enough_memory, may_expand_vm, RLIMIT/locked_vm/pinned_vm, VM_ACCOUNT); every map/ syscall page names its own gates in one line and defers mechanics here. Seam: security_vm_enough_memory_mm.
11. map/mempolicy.md (P4) owns the VMA policy surface incl. numa_maps display; fault/numa.md owns fault-time NUMA hinting. Seam: mpol_misplaced. move_pages/migrate_pages are out of scope for both (page migration).
12. proc/maps-smaps.md (P2) owns the textual/ioctl VMA listing ABI; proc/pagemap.md (P2) owns the per-page binary ABI + soft-dirty/PAGEMAP_SCAN; pgtable/x86-64-entries.md owns the soft-dirty bit encoding. Seams: lock_next_vma (listing), pte_soft_dirty (encoding).
13. map/shadow-stack.md (P4) owns the mapping+fault surface of CET shadow stacks; pgtable/x86-64-entries.md owns the PTE bit mechanics. Seam: pte_mkwrite_shstk. Token/signal ABI out of scope.
14. vma-ops/secretmem.md (P4) owns secretmem mapping semantics; gup/fast-path.md owns the gup_fast_folio_allowed reject mechanics. Seam: gup_fast_folio_allowed.
15. Sibling-campaign seams: fault/swap-in.md stops at the swap-cache/readahead API; fault/file-read.md and vma-ops/generic-file.md stop at filemap/readahead internals; rmap/folio-referenced.md and mkclean.md stop at the vmscan/writeback handoff (pagecache, reclaim, swap, writeback campaigns own those interiors).
16. fault/vma-lock-path.md owns the consolidated per-VMA-lock bail matrix (4 guards / 10 sites) and the FAULT_FLAG_VMA_LOCK retry contract; every per-handler fault page states its own local bail in a single line and defers the matrix (seam: FAULT_FLAG_VMA_LOCK / vmf_can_call_fault; review amendment 5).
17. vma/modify-spine.md owns the vma_modify mechanics; syscall pages (mprotect, madvise, mlock, mseal, mempolicy, userfaultfd-api) name their vma_modify_* wrapper in one line and defer the spine (seam: vma_modify; review amendment 7).
18. map/pkeys.md (P4) owns the protection-keys mechanism; map/mprotect.md keeps the pkey_mprotect entry point in one line (seam: arch_set_user_pkey_access). If P4-pkeys is rejected, the mechanism folds back into mprotect.md and this rule lapses.
19. map/process-madvise.md (P4) owns the remote/iovec/permission surface; map/madvise.md owns the behavior engine both share (seam: madvise_do_behavior). If rejected, folds back into madvise.md.
20. pgtable/paging-levels.md owns the 4-vs-5-level runtime constants; pgtable/alloc-locking.md defers level counts to it (seam: pgtable_l5_enabled); map/address-space-layout.md cites task_size_max()/DEFAULT_MAP_WINDOW from it (seam: task_size_max).

### Adversarial review outcome (2026-07-11)

Adversarial plan review (strong-model fresh agent; 55/55 anchor spot-checks OK, zero missing symbols) returned 14 amendments; 13 accepted + 1 sub-option rejected: (1) ADD fault/zap.md (per-PTE uninstall engine); (2) pfn-insert widened+renamed fault/pfn-mapping.md (adds remap_pfn_range/vm_insert_page family); (3) memfd_create fold rationale recorded; (4) __mmap_new_vma assigned to map/mmap.md, insertion.md rescoped; (5-7) new boundary rules 16 (bail matrix), 9-ext (finish_fault seam), 17 (vma_modify seam); (8a) thp-numa merged into numa.md — (8b) thp-anon+thp-wp merge REJECTED, each mirrors a substantial base handler; (9) pgtable/paging-levels.md split out; (10) map/pkeys.md split out (P4); (11) map/process-madvise.md split out (P4); (12) accounting promoted P4->base; (13) mmap.md canonical for the vm_area_desc contract wording; (14) vma-ops/hugetlb.md canonical for the divert wording. Catalog moved to 89 base + 10 pending = 99 max and the batch order was reworked to B1-B21 (the Phase 3 checkpoint then fixed the final catalog at 97 pages).

## Execution & verification

### Per-page procedure (skill-mandated)

1. Before the first batch: prep pass per `guidelines/passes/00-prep.md`; writers read `guidelines/reference/TEMPLATE-FULL.md` and calibrate against the closest sample under `guidelines/reference/samples/` (structure/depth only, never facts). mm's section-6 heading is none: pages carry exactly H1, caution blockquote, lead summary (+diagram where earned), SUMMARY, SPECIFICATIONS (body may state none applies), LINUX KERNEL, KERNEL DOCUMENTATION, OTHER SOURCES, DETAILS.
2. Research with semcode (find_function/find_type/find_callers/find_callchain/grep_functions; find_commit + dig/lore for OTHER SOURCES) plus Grep/Read; every cited line and reproduced block confirmed against the on-disk tree before it lands. Dossier per page at `progress/vma/<slug>.dossier.md` (`guidelines/passes/dossier.md`).
3. Write to `docs/mm/<group>/<slug>.md`. Elixir links: `https://elixir.bootlin.com/linux/v7.0/source/<path>#L<line>`, every symbol mention outside fenced blocks linked (7m), struct/enum keyword kept.
4. LINUX KERNEL catalog bullet display form follows the samples: `'\<symbol\>':'path'` inside the link text (settled; see LESSON 2026-07-11 below).

### Pipeline and gate ownership

Per SKILL.md ("Modes") and the pass files under `guidelines/passes/`. the five waivers files under `guidelines/rules/` (one `<PREFIX>-WAIVERS.md` per rule directory) are every agent's mandatory first read; rule IDs resolve via `guidelines/rules/INDEX.md`.

- Writer (strongest available model; brief in `guidelines/passes/02-write.md`): owns the page end to end, facts AND prose. It researches with semcode plus Grep/Read, keeps the page dossier current, writes under every rule, and runs the mechanical exit suite before reporting: excerpts byte-compared, anchors printed and confirmed (persisted as the dossier's machine-emitted LINKS table), the PARITY table closed (fill-or-decatalog), every count re-derived on a differently-shaped second basis, span closure against LINKS, and the Gate A prose and figure sweeps (3c) with every candidate adjudicated against the waivers into the dossier's LINT section. It fixes what the suite finds and re-runs the suite over what it touched. Page state: WRITTEN.
- Orchestrator check, per page (`guidelines/passes/03-check.md`; never delegated): re-runs the writer's procedures against ground truth and compares the answers — Gate A reproduction, the figure sweep, span-closure re-derivation with the same extractor, excerpt and anchor spot-checks, figure geometry, counts on a third basis. The orchestrator adjudicates every residual finding itself against the waivers; an exactly-specified fix is applied directly and volume the same way at scale, and factual findings return to the writer while its transcript lives. Page state: LINTED.
- Batches of ~5 pages, one writer per page, hard checkpoint between batches. A dead writer is resumed ("do not redo the research; write the page now from what you have"); a fresh writer starts from the dossier plus this file only after two failed resumes.

### Project-specific writing bans (carried from the request)

- "arm" never describes a union case or code branch (branch/case/side/leg instead); settled exemptions: architecture names, verbatim kernel-comment quotes.
- No hedging (7c list); no editorializing "is what makes / matters" constructions (three residuals of this class were found in the existing pages — treat as a hot class).
- x86-64 only; per-page CONFIG assumptions stated (baseline: PER_VMA_LOCK, TRANSPARENT_HUGEPAGE, MM_ID, NUMA_BALANCING, SPLIT_PTE_PTLOCKS on; the sample overview page's config-enumeration form is the model).
- Extra attention mandated: object lifecycle (alloc/free/locking/refcount), all state transitions, complete callback semantics for every ops struct.

### Write-time rules (from the redone inventory)

- Every line number in this plan is a hint, never a citation; re-grep/re-read the on-disk file at write time. semcode indexes can lag: agent A of the prior campaign hit stale lines, and this campaign's digests already carry one internal variance (do_user_addr_fault reported at fault.c:1206; prior plan said :1207 — settle on disk).
- memory.c has two do_set_pmd definitions (THP :5407, stub :5483); finish-fault.md anchors the CONFIG_TRANSPARENT_HUGEPAGE one.
- The two maple-tree algorithm pages stay bounded to vma_iter_/mas_walk/mas_find/mas_empty_area-reachable paths; lib/maple_tree.c beyond them is out of scope.
- amdgpu-gem.md is the only page whose research leaves mm/ (TTM helpers); budget as heavy, TTM coverage limited to what the callbacks need.
- The hugetlb divert (memory.c:6621-6622) reads identically in its three host pages (boundary rule 2).
- fault/ pages: entry-chain recap at most one short paragraph (house rule, boundary rule 9).
- Useful OTHER SOURCES leads found by inventory: leafops.h introduced v6.19 (68aa2fdbf57f), do_huge_pmd_device_private v6.19 (4964099163d0), pgtable_level rename v6.18 (b22cc9a9c7ff), exclude-readers rework in v7.0 cycle (25faccd69977) — re-verify hashes before citing.

### Batch order (post-review; foundational -> derived, ~5 pages per batch; rows for unapproved P2/P3/P4 decisions drop out silently)

- B1: pgtable/x86-64-entries, softleaf, paging-levels, alloc-locking; folio/mapping-encoding (5)
- B2: folio/refcount-mapcount, mm-id; mm-struct/overview, flags, counters (5)
- B3: mm-struct/refcount, locking, lifecycle, arch-context; vma/overview (5)
- B4: vma/flags, allocation, slab-rcu, refcount-locking (4)
- B5: vma/maple-tree, traversal, traversal-algorithm, insertion, insertion-algorithm (5 — REBUILD batch per Phase 3 decision 8: fresh writes overwriting the old pages; writers must not read the old files)
- B6: vma/split, merge, merge-existing, adjust, modify-spine (5 — REBUILD batch, same rule)
- B7: vma/removal, removal-algorithm, fork-dup, stack-growth (4)
- B8: map/accounting, address-space-layout, mmap, munmap, brk (5)
- B9: map/mremap, mprotect, mlock, madvise (4)
- B10: map/process-madvise, mseal, msync, mincore, mempolicy (5)
- B11: vma-ops/vm-operations, generic-file, shmem, secretmem (4)
- B12: vma-ops/special-mapping, hugetlb, amdgpu-gem; rmap/anon-vma, anon-vma-chain (5)
- B13: rmap/anon-setup, file-rmap, locking, add-remove; fault/vm-fault (5)
- B14: fault/x86-64-entry, vma-lock-path, handle-mm-fault, pte-dispatch, anonymous (5)
- B15: fault/file-dispatch, file-read, file-cow, file-shared, finish-fault (5)
- B16: fault/wp, swap-in, numa, thp-anon, thp-wp (5)
- B17: fault/zap, hugetlb, userfaultfd, userfaultfd-api(P3), pfn-mapping (5)
- B18: gup/overview, foll-flags, slow-path, fast-path, pinning (5)
- B19: gup/longterm, faultin, folio-walk; proc/maps-smaps(P2), pagemap(P2) (5)
- B20: rmap/walk, pvmw, folio-referenced, mkclean (4)
- B21: rmap/try-to-unmap, try-to-migrate (2)

(5+5+5+4+5+5+4+5+4+5+4+5+5+5+5+5+5+5+5+4+2 = 97 final.) The ten B5/B6 rows exist on disk from the prior campaign; per Phase 3 decision 8 they are REBUILT fresh (old pages overwritten at their batch slot, not read by writers). Dependency notes honored: accounting (B8) precedes the syscall pages that defer to it; fault/zap (B17) follows mmu_gather (B7) and rmap/add-remove (B13); numa.md carries its PMD-analogue section. Remaining P2/P3/P4 markers in rows above are historical; all surviving marked rows are confirmed base rows per Phase 3.

### Save/commit policy

Pages land only under `docs/mm/` of the skill root. No SUMMARY.md or mkdocs.yml edits. No git commits without an explicit user go. `progress/` artifacts stay out of git. prompt.md at the tree root stays untouched.

### User amendments

1. [2026-07-12] RENAME (user): campaign renamed `mm` -> `virtual-memory`; supersedes the name recorded at campaign start. Workspace entries moved to `progress/virtual-memory.md` + `progress/virtual-memory/`; every future sub-agent brief carries the new artifact directory. Output root `docs/mm/` and subsystem tag `mm` are unchanged.
2. [2026-07-12] RENAME (user): campaign renamed `virtual-memory` -> `vma`; supersedes amendment 1's name. Workspace entries moved to `campaigns/vma.md` + `progress/vma/`. Output root and tag still unchanged; the name coincides with the `docs/mm/vma/` group but denotes the whole campaign.
3. [2026-07-16] PARTIAL GO + SCOPE NARROWING (user): five catalog rows pulled ahead of their planned batches and produced sequentially (see the dated Status entry): map/mmap.md, fault/x86-64-entry.md, rmap/anon-vma.md, rmap/anon-vma-chain.md, fault/handle-mm-fault.md. Depth exclusion for these pages: SGX, RDMA, pkeys, cryptography, and similar virtualization/security side topics are named at code level only where a walked function touches them, never expanded; supersedes, for these rows, any fold-in that would pull such material deeper into the page.

## Draft reuse map

SUPERSEDED BY PHASE 3 DECISION 8 (2026-07-11): the user chose REBUILD FROM SCRATCH for all 10 pages. The audit below stays as the record that motivated the recommendation, but its verdicts and fix list are moot: the 10 rows are written fresh at B5/B6, writers must not read the old files, and the old pages are overwritten at their batch slot. The audit's enhancement items E1 (config-fallback paragraphs) and E2 (worked numeric examples) transfer into the B5/B6 writer briefs. The LESSON at the bottom (samples define the catalog-bullet form) remains binding for every lint brief.

Prior material: the 10 live pages under `docs/mm/vma/` (10,262 lines), audited 2026-07-11 by a read-only agent (structure, Gate A candidate sweep, 8-link + 3-excerpt + 5-parity spot checks per page against the tree).

Audit table (as reported):

| page | lines | structure | gate-A resid. | links pass/8 | excerpts verbatim/3 | parity miss/5 | verdict |
|---|---|---|---|---|---|---|---|
| adjust.md | 703 | OK | 0 | 8/8 | 3/3 | 1/5 | ADOPT-WITH-FIXES |
| insertion.md | 730 | OK | 0 | 8/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |
| insertion-algorithm.md | 1945 | OK | 0 | 8/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |
| maple-tree.md | 1241 | OK | 0 | 8/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |
| merge.md | 844 | OK | 1 | 8/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |
| merge-existing.md | 987 | OK | 1 | 8/8 | 3/3 | 1/5 | ADOPT-WITH-FIXES |
| modify-spine.md | 792 | OK | 0 | 7/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |
| split.md | 694 | OK | 0 | 8/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |
| traversal.md | 853 | OK | 0 | 8/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |
| traversal-algorithm.md | 1473 | OK | 1 | 8/8 | 3/3 | 0/5 | ADOPT-WITH-FIXES |

ORCHESTRATOR CORRECTION (2026-07-11): the audit's largest reported defect class — "malformed catalog-bullet link text (`'\<NAME\>':'path'` as display text) on 242/314 LINUX KERNEL bullets" — is a FALSE POSITIVE. Both frozen samples (`guidelines/reference/samples/page-encoding-pgtable-entries.md`, `page-overview-mm-struct.md`) use exactly this display form on their LINUX KERNEL bullets; it is the house convention, and the existing pages match it. Verified directly against the samples on 2026-07-11. No bullet rewrites happen.

Real fix list (all verdicts stand as ADOPT-WITH-FIXES, now narrow):
1. merge.md:759, merge-existing.md:385 — reword the "is what makes" editorializing constructions.
2. traversal-algorithm.md:425 — reword "The usage that matters...".
3. modify-spine.md:86 — re-anchor the vmg.anon_name link from mm/vma.h#L69 to the field's own line (#L106; re-verify on disk).
4. adjust.md — extend the relocate_vma_down excerpt to open at the signature line (mm/vma_exec.c:19).
5. merge-existing.md — extend the vma_merge_existing_range first excerpt to open at the signature line (mm/vma.c:805).
6. Settled-exempt raw hits confirmed exempt (no action): insertion.md:369 "Arm" (arch name), modify-spine.md:249 "arm/parisc" (verbatim kernel comment), split.md:409 "__read_mostly" (hyphenated compound).

Excerpt spot checks: 30/30 verbatim. Link spot checks: 79/80 (the one miss is fix 3). Structure: 10/10 conform (caution block, section order, declarative headings).

Enhancement backlog (post-campaign, not blocking adoption):
- E1: each existing page states its CONFIG baseline but not what changes under the mmap_lock-only fallback; add one-paragraph fallback notes when pages are next touched.
- E2: worked end-to-end numeric examples exist only on merge-existing.md; candidates: merge.md, split.md, insertion-algorithm.md, traversal-algorithm.md.
- E3: (from audit item 4) a cross-page index is disallowed by the no-internal-.md-links rule; not actionable, recorded as adjudicated N/A.

LESSON (2026-07-11): audit/lint briefs for this knowledge base MUST name the frozen samples as the reference for the LINUX KERNEL bullet display form (and any other catalog-form questions), or a fresh agent will misread the house convention as corruption. Folded into every future lint brief.
