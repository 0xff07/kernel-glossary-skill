# struct mm_struct

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) is the per-process address-space descriptor of the Linux kernel, defined in [`include/linux/mm_types.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123). One instance describes one user address space; every thread created with [`CLONE_VM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/sched.h#L11) shares the same instance through [`task_struct->mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958), and kernel threads borrow a foreign instance through [`task_struct->active_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L959). The structure aggregates state owned by many subsystems (the VMA maple tree and its locks for the mm core, the [`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150) root for the x86-64 paging hardware, RSS and virtual-size accounting for `/proc` and rlimits, plus per-subsystem fields for futexes, uprobes, KSM, MGLRU, NUMA balancing, membarrier, AIO, IOMMU PASIDs and the scheduler's concurrency IDs) and ends in a flexible array that is sized at boot for the machine's CPU count. The figure below maps the field groups in declaration order, with each group's owning subsystem and serialization on the right.

```
    Where struct mm_struct sits in memory (include/linux/mm_types.h:1123)
    ─────────────────────────────────────────────────────────────────────
    (offset 0 at the left; the three regions differ in how the compiler
     is allowed to place what is inside them)

    offset 0                                              sizeof(mm_struct)
    ┌──────────────┬───────────────────────────────────┬─────────────────┐
    │ mm_count     │ one anonymous struct marked       │ flexible_array  │
    │ alone on its │ __randomize_layout: every other   │ tail, sized at  │
    │ own cache    │ field group, in an order the      │ boot rather     │
    │ line         │ compiler may permute              │ than at compile │
    └──────┬───────┴─────────────────┬─────────────────┴────────┬────────┘
           │                         │                          │
           ▼                         ▼                          ▼
    ____cacheline_          declaration order is not     three bitmaps
    aligned_in_smp,         address order here, so       carved out by
    with padding after      no field group may be        accessors, one
    it only                 reached by offset            after another
                                                                │
      the mm_count read and         ┌─────────────────┬─────────┴───────┐
      written by every context      ▼                 ▼                 ▼
      switch is kept off the   mm_cpumask()   mm_cpus_allowed()  mm_cidmask()
      line the read-mostly
      fields share

    commit c1753fd02a00 moved mm_count to the first field for exactly this
    reason, so the padding it needs is added once, after it, rather than
    on both sides
```

The field-group census the layout permutes is a member-meaning-construct set, so it is carried as a table (7t) rather than redrawn in box characters (7v).

| field group | owning subsystem | serializing discipline |
|---|---|---|
| `mm_count` | lifetime reference count | atomic; `mmgrab()` / `mmdrop()` |
| `mm_mt`, `mmap_base`, `mmap_legacy_base`, `task_size`, `pgd`, `membarrier_state` | address space, mm core | `mmap_lock`; `switch_mm` reads |
| `mm_users`, `mm_cid`, `pgtables_bytes`, `map_count`, `page_table_lock` | users reference count, scheduler CIDs, page-table counts | atomic; `page_table_lock` |
| `mmap_lock`, `mmlist` | the top-level VMA-tree lock, the swapoff walk | `rw_semaphore`; `mmlist_lock` |
| `vma_writer_wait`, `mm_lock_seq` | per-VMA locks (`PER_VMA_LOCK`) | sequence count plus wait queue |
| `futex_hash_lock`, `futex_phash`, `futex_phash_new`, `futex_batches`, `futex_rcu`, `futex_atomic`, `futex_ref` | the private futex hash (`FUTEX_PRIVATE_HASH`) | RCU plus per-CPU references |
| `hiwater_rss`, `hiwater_vm`, `total_vm`, `locked_vm`, `pinned_vm`, `data_vm`, `exec_vm`, `stack_vm`, `def_flags` | VM accounting, mm core | `mmap_lock` write side; `pinned_vm` is `atomic64_t` |
| `write_protect_seq` | fork COW against GUP-fast | sequence count |
| `arg_lock`, `start_code` through `end_data`, `start_brk`, `brk`, `start_stack`, the arg and env ranges, `saved_auxv` | the exec image, binfmt and prctl | `arg_lock` guards the ranges; `saved_auxv` is lockless |
| `rss_stat[NR_MM_COUNTERS]`, `binfmt`, `context`, `flags` | percpu RSS counters, the loader reference, x86-64 TLB and LDT state, the 64 MMF bits | percpu; atomic bitmap accessors |
| `ioctx_lock`, `ioctx_table`, `owner`, `user_ns`, `exe_file`, `notifier_subscriptions` | in-flight AIO contexts, identity references, MMU notifiers | `ioctx_lock`; RCU |
| `numa_next_scan`, `numa_scan_offset`, `numa_scan_seq`, `tlb_flush_pending`, `tlb_flush_batched` | the NUMA-balancing scanner, flush against PTL ordering | atomic |
| `uprobes_state`, `hugetlb_usage`, `async_put_work`, `iommu_mm`, the KSM counters, `lru_gen`, `mm_id` | uprobes XOL, hugetlb pages, the deferred put, PASID, KSM, MGLRU, the folio owner | per-subsystem |
| `flexible_array[]` | the per-CPU bitmaps reached through `mm_cpumask()`, `mm_cpus_allowed()` and `mm_cidmask()` | sized at boot; accessor-only |

## SUMMARY

[`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) is allocated from the [`mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) slab created by [`mm_cache_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L3002), and the slab object is larger than `sizeof(struct mm_struct)` because the trailing [`flexible_array`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1380) member is sized at boot to `cpumask_size() + mm_cid_size()` for the CPU bitmap returned by [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432) and the two scheduler bitmaps returned by [`mm_cpus_allowed()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1521) and [`mm_cidmask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1532). Two descriptors reach [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) during normal operation. [`mm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1154) zeroes a fresh object for `execve(2)`, and [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) [`memcpy`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/string_64.h#L18)s the parent's object for `fork(2)`, so every field either survives the copy, is re-initialized by [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072), or is filtered on inheritance (the [`mm_flags_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1117) bitmap through [`mmf_init_legacy_flags()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1933), [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) through [`VM_INIT_DEF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L572)).

The descriptor carries two reference counts with distinct meanings. [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) counts users of the address-space contents (threads, plus temporary holders via [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131)), and its final [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) unmaps everything. [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) counts references to the descriptor itself (taken with [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35)), and its final [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) frees the structure through [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718). Because context switches write [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) constantly, the field is placed alone in the first cache line of the structure under [`____cacheline_aligned_in_smp`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cache.h#L65), separated from the read-mostly fields that follow.

The remaining fields fall into groups owned by different subsystems, and this page tours them in declaration order. The [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) maple tree indexes every VMA under [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) with RCU readers. The per-VMA-lock fields ([`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222), [`vma_writer_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1204), [`CONFIG_PER_VMA_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1403)=y) let page faults lock a single VMA without touching [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). The address-layout group ([`mmap_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1142), [`task_size`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1149), the code/data/brk/stack/arg/env boundaries and [`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259)) is written by `execve(2)` and read back through `/proc`. The accounting group spans the [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) percpu counters, the high-water marks and the `_vm` page counts checked against rlimits. The remaining fields serve exactly one subsystem each and receive one paragraph apiece in DETAILS, as does the statically initialized instance [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32). Locking rules, refcount lifecycle, teardown ordering, MMF flag semantics and counter mechanics each receive only field-level treatment on this page.

## SPECIFICATIONS

## LINUX KERNEL

Kernel v7.0. On x86-64 the assumed configuration is [`CONFIG_MMU`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L355)=y, [`CONFIG_PER_VMA_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1403)=y, [`CONFIG_MEMCG`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1048)=y, [`CONFIG_NUMA_BALANCING`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L996)=y, [`CONFIG_KSM`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L688)=y, [`CONFIG_TRANSPARENT_HUGEPAGE`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L794)=y, [`CONFIG_FUTEX_PRIVATE_HASH`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1815)=y, [`CONFIG_SCHED_MM_CID`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1179)=y, [`CONFIG_LRU_GEN_WALKS_MMU`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1395)=y, [`CONFIG_MM_ID`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L791)=y, [`CONFIG_MEMBARRIER`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1921)=y, [`CONFIG_AIO`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1870)=y, [`CONFIG_UPROBES`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L182)=y and [`CONFIG_IOMMU_MM_DATA`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1416)=y.

### Descriptor and layout (include/linux/mm_types.h)

- [`'\<struct mm_struct\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123): the per-process address-space descriptor; one anonymous [`__randomize_layout`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_types.h#L476) struct plus a flexible tail
- [`'\<mm_flags_t\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1117): opaque 64-bit MMF flag bitmap type held in the [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1273) field
- [`NUM_MM_FLAG_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1116): size of the MMF bitmap, 64 bits
- [`MM_MT_FLAGS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1413): maple-tree flags for [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) (`MT_FLAGS_ALLOC_RANGE | MT_FLAGS_LOCK_EXTERN | MT_FLAGS_USE_RCU`)
- [`MM_STRUCT_FLEXIBLE_ARRAY_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1417): static initializer for the flexible tail, `sizeof(cpumask_t) + MM_CID_STATIC_SIZE` zero bytes
- [`'\<mm_init_cpumask\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1423): clears the CPU bitmap in the flexible tail
- [`'\<mm_cpumask\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432): returns the CPU bitmap at the start of the flexible tail
- [`'\<mm_cpus_allowed\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1521): returns the union-of-affinities cpumask behind [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432) ([`CONFIG_SCHED_MM_CID`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1179))
- [`'\<mm_cidmask\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1532): returns the concurrency-ID allocation bitmap at the end of the tail
- [`MM_CID_STATIC_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1566): static tail reservation for the CID masks, `2 * sizeof(cpumask_t)`
- [`AT_VECTOR_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L31): element count of [`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259), `2*(AT_VECTOR_SIZE_ARCH + AT_VECTOR_SIZE_BASE + 1)`
- [`'\<mm_id_t\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L329): per-mm identifier type stored in [`mm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1372) and in [`folio->_mm_id[]`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L462) ([`CONFIG_MM_ID`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L791))
- [`NR_MM_COUNTERS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L31): number of [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) percpu counters, 4
- [`'\<mmf_init_legacy_flags\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1933): filters the first MMF word on fork
- [`MMF_INIT_LEGACY_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1922): the MMF bits a child inherits
- [`'\<lru_gen_init_mm\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1454): resets the [`lru_gen`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1369) group at init ([`CONFIG_LRU_GEN_WALKS_MMU`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1395))
- [`'\<lru_gen_use_mm\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1463): marks the mm recently used for MGLRU walkers
- [`'\<struct mm_mm_cid\>':'include/linux/rseq_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rseq_types.h#L171): per-mm concurrency-ID state embedded as [`mm_cid`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1174) ([`CONFIG_SCHED_MM_CID`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1179))

### x86-64 context and address layout (arch/x86)

- [`'\<mm_context_t\>':'arch/x86/include/asm/mmu.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L84): x86 MMU state embedded as the [`context`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1271) field
- [`INIT_MM_CONTEXT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L86): static [`context`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1271) initializer used by [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32)
- [`'\<arch_pick_mmap_layout\>':'arch/x86/mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L122): computes [`mmap_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1142), [`mmap_legacy_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1143) and the compat bases at exec
- [`'\<get_mmap_base\>':'arch/x86/mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L146): selects the stored base by syscall width and legacy mode
- [`SIZE_128M`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L60): lower clamp of the stack gap below [`mmap_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1142), 128 MiB
- [`TASK_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L64): value stored into [`task_size`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1149) at exec
- [`DEFAULT_MAP_WINDOW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L54): 47-bit default mapping ceiling, `(1UL << 47) - PAGE_SIZE`
- [`'\<switch_mm_irqs_off\>':'arch/x86/mm/tlb.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L783): loads [`mm->pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150) into CR3 and maintains [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432)
- [`'\<pgd_alloc\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L322): allocates the page-global directory stored in [`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150)

### Allocation, initialization and release (kernel/fork.c, mm/init-mm.c)

- [`'\<mm_cache_init\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L3002): creates the [`mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) slab with the boot-sized tail and a usercopy window over [`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259)
- [`allocate_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L649): slab allocation wrapper used by [`mm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1154) and [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515)
- [`'\<mm_init\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072): initializes every dynamic field and allocates [`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150), [`mm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1372), [`context`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1271), CIDs and [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266)
- [`'\<mm_alloc\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1154): zeroed allocation for exec
- [`'\<dup_mm\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515): [`memcpy`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/string_64.h#L18) duplication for fork followed by [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) and [`dup_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732)
- [`'\<mm_alloc_pgd\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L575): fills [`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150) from [`pgd_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L322)
- [`'\<mm_alloc_id\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L595): allocates [`mm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1372) from an IDA in [MM_ID_MIN, MM_ID_MAX]
- [`'\<check_mm\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L622): verifies [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266), [`pgtables_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1177) and [`pmd_huge_pte`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1300) are zero at free
- [`'\<__mmdrop\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718): frees the descriptor when [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reaches zero
- [`'\<mmput\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193): drops [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) and runs [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) on the last user
- [`'\<mmput_async\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211): defers the [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) slow path onto [`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333)
- [`'\<mmdrop_async\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749): defers [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) onto [`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333) for softirq-unsafe contexts
- [`'\<set_mm_exe_file\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1234): installs the [`exe_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1295) reference and denies writes to it
- [`'\<futex_mm_init\>':'kernel/futex/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1719): initializes the futex hash fields from [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072)
- [`'\<futex_hash_free\>':'kernel/futex/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1731): frees [`futex_ref`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1232), [`futex_phash`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1226) and [`futex_phash_new`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1227)
- [`'\<init_mm\>':'mm/init-mm.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32): the statically initialized kernel instance rooted at [`swapper_pg_dir`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L27)
- [`'\<setup_initial_init_mm\>':'mm/init-mm.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L54): records the kernel image boundaries into [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32)

### Reference-count helpers (include/linux/sched/mm.h)

- [`'\<mmgrab\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35): pins the descriptor by incrementing [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137)
- [`'\<mmdrop\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47): releases [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) and calls [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) at zero
- [`'\<mmget\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131): pins the address space by incrementing [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171)
- [`'\<mmget_not_zero\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136): conditional [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) pin that fails after teardown began

### Field accessors (include/linux/mm.h, mm_inline.h, mmap_lock.h, hugetlb.h, ksm.h)

- [`'\<mm_flags_test\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L877): tests one MMF bit atomically
- [`'\<mm_flags_clear_all\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L902): zeroes the whole MMF bitmap
- [`'\<get_mm_counter\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3063): approximate positive read of one [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) counter
- [`'\<add_mm_counter\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3075): batched percpu add to one [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) counter
- [`'\<get_mm_rss\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3111): sums the three resident-page counters
- [`'\<update_hiwater_rss\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3135): raises [`hiwater_rss`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1235) before RSS shrinks
- [`'\<update_hiwater_vm\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3143): raises [`hiwater_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1236) before [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238) shrinks
- [`'\<mm_pgtables_bytes\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3273): reads the page-table byte count
- [`DEFAULT_MAX_MAP_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L209): default bound on [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179), `USHRT_MAX - 5` = 65530
- [`VM_INIT_DEF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L572): [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) bits a child inherits, [`VM_NOHUGEPAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L441)
- [`'\<init_tlb_flush_pending\>':'include/linux/mm_inline.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L453): zeroes [`tlb_flush_pending`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1321) at init
- [`'\<inc_tlb_flush_pending\>':'include/linux/mm_inline.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L458): opens a batched-flush window ordered by the PTL
- [`'\<mm_tlb_flush_pending\>':'include/linux/mm_inline.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L512): tests for an open flush window under the PTL
- [`'\<mmap_write_lock\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L533): takes [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) for writing and begins the [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222) write section
- [`'\<vma_end_write_all\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L569): ends the [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222) section, releasing all per-VMA write locks
- [`'\<mm_lock_seqcount_begin\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L123): raw seqcount write begin on [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222)
- [`'\<mmap_lock_speculate_try_begin\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L134): opens a speculative lockless read section against [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222)
- [`'\<vma_refcount_put\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L210): drops a VMA read lock and wakes [`vma_writer_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1204)
- [`MMAP_LOCK_INITIALIZER`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L17): static [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) initializer used by [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32)
- [`'\<hugetlb_count_add\>':'include/linux/hugetlb.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/hugetlb.h#L1035): adds to the [`hugetlb_usage`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1331) counter
- [`'\<mm_ksm_zero_pages\>':'include/linux/ksm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ksm.h#L51): reads the [`ksm_zero_pages`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1353) counter

### Consumers across subsystems

- [`'\<copy_page_range\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1504): fork page-table copy; write side of [`write_protect_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1251)
- [`'\<gup_fast\>':'mm/gup.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/gup.c#L3129): lockless page pinning; read side of [`write_protect_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1251)
- [`'\<vm_stat_account\>':'mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1360): updates [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238), [`exec_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1242), [`stack_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1243), [`data_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1241)
- [`'\<may_expand_vm\>':'mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1335): checks [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238)/[`data_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1241) growth against RLIMIT_AS and RLIMIT_DATA
- [`'\<do_brk_flags\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866): brk expansion; reads [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) and the [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) bound
- [`'\<apply_mlockall_flags\>':'mm/mlock.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mlock.c#L704): sets [`VM_LOCKED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L420)/[`VM_LOCKONFAULT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L426) in [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) for `mlockall(MCL_FUTURE)`
- [`'\<set_tlb_ubc_flush_pending\>':'mm/rmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L742): advances the pending generation in [`tlb_flush_batched`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1324)
- [`'\<flush_tlb_batched_pending\>':'mm/rmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L810): flushes when the pending and flushed generations differ
- [`'\<try_to_unuse\>':'mm/swapfile.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/swapfile.c#L2399): swapoff walk over the [`mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198) chain rooted at [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32)
- [`'\<lru_gen_add_mm\>':'mm/vmscan.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2903): enqueues the descriptor on the MGLRU per-memcg mm list
- [`'\<mm_init_cid\>':'kernel/sched/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L10846): resets [`mm_cid`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1174) and the two tail masks
- [`'\<mm_update_next_owner\>':'kernel/exit.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L487): re-points [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1290) when the owning task exits ([`CONFIG_MEMCG`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1048))
- [`'\<task_numa_work\>':'kernel/sched/fair.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3363): NUMA-balancing scanner driven by [`numa_next_scan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1308)/[`numa_scan_offset`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1311)/[`numa_scan_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1314)
- [`'\<sync_runqueues_membarrier_state\>':'kernel/sched/membarrier.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/membarrier.c#L438): propagates [`membarrier_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1159) into each runqueue
- [`'\<proc_mem_open\>':'fs/proc/base.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L837): `/proc/[pid]/mem` open path pairing [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) with [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193)
- [`'\<get_mm_cmdline\>':'fs/proc/base.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L291): reads the arg/env ranges under [`arg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1253)
- [`'\<auxv_read\>':'fs/proc/base.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L1081): serves [`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259) as `/proc/[pid]/auxv`
- [`'\<proc_pid_ksm_stat\>':'fs/proc/base.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L3262): reports the three KSM counters
- [`'\<task_mem\>':'fs/proc/task_mmu.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L37): renders the accounting fields as `/proc/[pid]/status`
- [`'\<struct uprobes_state\>':'include/linux/uprobes.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uprobes.h#L187): per-mm uprobes state embedded as [`uprobes_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1326)
- [`'\<struct iommu_mm_data\>':'include/linux/iommu.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/iommu.h#L1138): PASID and SVA domain list referenced by [`iommu_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1336)
- [`'\<struct futex_private_hash\>':'kernel/futex/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L66): the hash object referenced by [`futex_phash`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1226)

## KERNEL DOCUMENTATION

- [`Documentation/mm/active_mm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/active_mm.rst): Linus Torvalds' 1999 explanation of [`mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958) versus [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L959), with the current note that lazy references use [`mmgrab_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88)/[`mmdrop_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L94) under [`CONFIG_MMU_LAZY_TLB_REFCOUNT`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L553)=n; the file the [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171)/[`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) kernel-doc comments point at
- [`Documentation/core-api/mm-api.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/core-api/mm-api.rst): the mm API reference, which pulls the kernel-doc from [`include/linux/mm_types.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) (including the [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137), [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171), [`membarrier_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1159) and [`write_protect_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1251) field comments) into the rendered documentation

## OTHER SOURCES

- [mm: move mm_count into its own cache line (Mathieu Desnoyers, May 2023)](https://lkml.kernel.org/r/20230515143536.114960-1-mathieu.desnoyers@efficios.com)
- [mm: start tracking VMAs with maple tree (Liam R. Howlett, September 2022)](https://lkml.kernel.org/r/20220906194824.2110408-9-Liam.Howlett@oracle.com)
- [mm: convert mm's rss stats into percpu_counter (Shakeel Butt, October 2022)](https://lkml.kernel.org/r/20221024052841.3291983-1-shakeelb@google.com)
- [mm: convert mm_lock_seq to a proper seqcount (Suren Baghdasaryan, November 2024)](https://lkml.kernel.org/r/20241122174416.1367052-2-surenb@google.com)
- [mm: replace vm_lock and detached flag with a reference count (Suren Baghdasaryan, February 2025)](https://lkml.kernel.org/r/20250213224655.1680278-13-surenb@google.com)
- [futex: Add basic infrastructure for local task local hash (Sebastian Andrzej Siewior, April 2025)](https://lore.kernel.org/r/20250416162921.513656-13-bigeasy@linutronix.de)
- [mm: add bitmap mm->flags field (Lorenzo Stoakes, August 2025)](https://lkml.kernel.org/r/9de8dfd9de8c95cd31622d6e52051ba0d1848f5a.1755012943.git.lorenzo.stoakes@oracle.com)
- [mm/gup: prevent gup_fast from racing with COW during fork (Jason Gunthorpe, December 2020)](https://lkml.kernel.org/r/2-v4-908497cf359a+4782-gup_fork_jgg@nvidia.com)

## DETAILS

### mm_cache_init creates a slab whose objects exceed sizeof(struct mm_struct)

Every dynamically allocated descriptor comes from the [`mm_cachep`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L479) slab, created once at boot by [`mm_cache_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L3002). The object size adds [`cpumask_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cpumask.h#L1018) and [`mm_cid_size()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1559) to `sizeof(struct mm_struct)`, so the flexible tail holds exactly the bitmaps the booted machine needs (both helpers scale with [`nr_cpu_ids`](https://elixir.bootlin.com/linux/v7.0/source/kernel/smp.c#L981) and [`num_possible_cpus()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cpumask.h#L1220) rather than the compile-time [`NR_CPUS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/threads.h#L21)). The [`kmem_cache_create_usercopy()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L412) call whitelists only the [`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259) window for hardened usercopy, because `/proc/[pid]/auxv` copies that array straight to userspace. [`ARCH_MIN_MMSTRUCT_ALIGN`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L2991) is 0 on x86-64, leaving [`SLAB_HWCACHE_ALIGN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/slab.h#L94) in charge of alignment.

```c
/* kernel/fork.c:2990 */
#ifndef ARCH_MIN_MMSTRUCT_ALIGN
#define ARCH_MIN_MMSTRUCT_ALIGN 0
#endif

/* kernel/fork.c:3002 */
void __init mm_cache_init(void)
{
	unsigned int mm_size;

	/*
	 * The mm_cpumask is located at the end of mm_struct, and is
	 * dynamically sized based on the maximum CPU number this system
	 * can have, taking hotplug into account (nr_cpu_ids).
	 */
	mm_size = sizeof(struct mm_struct) + cpumask_size() + mm_cid_size();

	mm_cachep = kmem_cache_create_usercopy("mm_struct",
			mm_size, ARCH_MIN_MMSTRUCT_ALIGN,
			SLAB_HWCACHE_ALIGN|SLAB_PANIC|SLAB_ACCOUNT,
			offsetof(struct mm_struct, saved_auxv),
			sizeof_field(struct mm_struct, saved_auxv),
			NULL);
}
```

[`mm_core_init()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mm_init.c#L2694) calls it during early boot at [`mm/mm_init.c:2741`](https://elixir.bootlin.com/linux/v7.0/source/mm/mm_init.c#L2741), and [`allocate_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L649)/[`free_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L650) wrap the cache for the two allocation paths.

```c
/* mm/mm_init.c:2694 */
void __init mm_core_init(void)
{
	...
	kmsan_init_runtime();
	mm_cache_init();
	execmem_init();
}

/* kernel/fork.c:649 */
#define allocate_mm()	(kmem_cache_alloc(mm_cachep, GFP_KERNEL))
#define free_mm(mm)	(kmem_cache_free(mm_cachep, (mm)))
```

### The flexible_array tail carries mm_cpumask and the two CID masks

The struct closes with a comment explaining the tail placement and a byte array aligned like `unsigned long`. According to the comment, "The mm_cpumask needs to be at the end of mm_struct, because it is dynamically sized based on nr_cpu_ids."

```c
/* include/linux/mm_types.h:1376 */
	/*
	 * The mm_cpumask needs to be at the end of mm_struct, because it
	 * is dynamically sized based on nr_cpu_ids.
	 */
	char flexible_array[] __aligned(__alignof__(unsigned long));
};
```

Three accessors carve the tail into consecutive bitmaps. [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432) returns the leading CPU mask that tracks which CPUs may hold TLB entries for this address space, [`mm_cpus_allowed()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1521) ([`CONFIG_SCHED_MM_CID`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1179)=y) skips past it to the grow-only union of all threads' affinity masks, and [`mm_cidmask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1532) skips both cpumasks to reach the concurrency-ID allocation bitmap. [`mm_init_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1423) clears the first mask through the same offset arithmetic, and [`MM_STRUCT_FLEXIBLE_ARRAY_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1417) zeroes `sizeof(cpumask_t) + MM_CID_STATIC_SIZE` bytes for the one static instance, [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32), whose tail is sized for the compile-time worst case ([`MM_CID_STATIC_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1566) reserves `2 * sizeof(cpumask_t)`, per its comment "Use 2 * NR_CPUS as worse case for static allocation").

```c
/* include/linux/mm_types.h:1417 */
#define MM_STRUCT_FLEXIBLE_ARRAY_INIT				\
{								\
	[0 ... sizeof(cpumask_t) + MM_CID_STATIC_SIZE - 1] = 0	\
}

/* Pointer magic because the dynamic array size confuses some compilers. */
static inline void mm_init_cpumask(struct mm_struct *mm)
{
	unsigned long cpu_bitmap = (unsigned long)mm;

	cpu_bitmap += offsetof(struct mm_struct, flexible_array);
	cpumask_clear((struct cpumask *)cpu_bitmap);
}

/* Future-safe accessor for struct mm_struct's cpu_vm_mask. */
static inline cpumask_t *mm_cpumask(struct mm_struct *mm)
{
	return (struct cpumask *)&mm->flexible_array;
}

/* include/linux/mm_types.h:1517 */
#ifdef CONFIG_SCHED_MM_CID
/*
 * mm_cpus_allowed: Union of all mm's threads allowed CPUs.
 */
static inline cpumask_t *mm_cpus_allowed(struct mm_struct *mm)
{
	unsigned long bitmap = (unsigned long)mm;

	bitmap += offsetof(struct mm_struct, flexible_array);
	/* Skip cpu_bitmap */
	bitmap += cpumask_size();
	return (struct cpumask *)bitmap;
}

/* Accessor for struct mm_struct's cidmask. */
static inline unsigned long *mm_cidmask(struct mm_struct *mm)
{
	unsigned long cid_bitmap = (unsigned long)mm_cpus_allowed(mm);

	/* Skip mm_cpus_allowed */
	cid_bitmap += cpumask_size();
	return (unsigned long *)cid_bitmap;
}

/* include/linux/mm_types.h:1559 */
static inline unsigned int mm_cid_size(void)
{
	/* mm_cpus_allowed(), mm_cidmask(). */
	return cpumask_size() + bitmap_size(num_possible_cpus());
}

/* Use 2 * NR_CPUS as worse case for static allocation. */
# define MM_CID_STATIC_SIZE	(2 * sizeof(cpumask_t))
```

The x86-64 context switch is the main consumer of [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432). [`switch_mm_irqs_off()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L783) sets the current CPU's bit before loading CR3 so the CPU receives TLB-invalidation IPIs for this address space, and the flush paths iterate the mask to target only CPUs that ever ran it.

```c
/* arch/x86/mm/tlb.c:909 */
		/*
		 * Indicate that CR3 is about to change. nmi_uaccess_okay()
		 * and others are sensitive to the window where mm_cpumask(),
		 * CR3 and cpu_tlbstate.loaded_mm are not all in sync.
		 */
		this_cpu_write(cpu_tlbstate.loaded_mm, LOADED_MM_SWITCHING);
		...
/* arch/x86/mm/tlb.c:935 */
		if (next != &init_mm && !cpumask_test_cpu(cpu, mm_cpumask(next)))
			cpumask_set_cpu(cpu, mm_cpumask(next));
		else
			smp_mb();
```

### mm_init fills a zeroed or copied descriptor in a fixed order

[`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) is the single initialization function both allocation paths funnel through, and it shows where every dynamic field's starting value comes from. The infallible first half resets in place (tree flags, both refcounts to 1, the seqcounts, locks, list heads, counters and pointers), then a fallible second half allocates the external resources ([`futex_mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1719), [`mm_alloc_pgd()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L575), [`mm_alloc_id()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L595), [`init_new_context()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L150), [`mm_alloc_cid()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1551), [`percpu_counter_init_many()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/percpu_counter.h#L37)) and unwinds them in reverse on failure. The flags inheritance branch distinguishes fork from the first kernel-spawned process. When [`current->mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958) exists, the first word of the parent's bitmap passes through [`mmf_init_legacy_flags()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1933) and [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) is masked with [`VM_INIT_DEF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L572); otherwise the flags start from the boot-configurable [`default_dump_filter`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1017) and [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) starts at 0.

```c
/* kernel/fork.c:1072 */
static struct mm_struct *mm_init(struct mm_struct *mm, struct task_struct *p,
	struct user_namespace *user_ns)
{
	mt_init_flags(&mm->mm_mt, MM_MT_FLAGS);
	mt_set_external_lock(&mm->mm_mt, &mm->mmap_lock);
	atomic_set(&mm->mm_users, 1);
	atomic_set(&mm->mm_count, 1);
	seqcount_init(&mm->write_protect_seq);
	mmap_init_lock(mm);
	INIT_LIST_HEAD(&mm->mmlist);
	mm_pgtables_bytes_init(mm);
	mm->map_count = 0;
	mm->locked_vm = 0;
	atomic64_set(&mm->pinned_vm, 0);
	memset(&mm->rss_stat, 0, sizeof(mm->rss_stat));
	spin_lock_init(&mm->page_table_lock);
	spin_lock_init(&mm->arg_lock);
	mm_init_cpumask(mm);
	mm_init_aio(mm);
	mm_init_owner(mm, p);
	mm_pasid_init(mm);
	RCU_INIT_POINTER(mm->exe_file, NULL);
	mmu_notifier_subscriptions_init(mm);
	init_tlb_flush_pending(mm);
#if defined(CONFIG_TRANSPARENT_HUGEPAGE) && !defined(CONFIG_SPLIT_PMD_PTLOCKS)
	mm->pmd_huge_pte = NULL;
#endif
	mm_init_uprobes_state(mm);
	hugetlb_count_init(mm);

	mm_flags_clear_all(mm);
	if (current->mm) {
		unsigned long flags = __mm_flags_get_word(current->mm);

		__mm_flags_overwrite_word(mm, mmf_init_legacy_flags(flags));
		mm->def_flags = current->mm->def_flags & VM_INIT_DEF_MASK;
	} else {
		__mm_flags_overwrite_word(mm, default_dump_filter);
		mm->def_flags = 0;
	}

	if (futex_mm_init(mm))
		goto fail_mm_init;

	if (mm_alloc_pgd(mm))
		goto fail_nopgd;

	if (mm_alloc_id(mm))
		goto fail_noid;

	if (init_new_context(p, mm))
		goto fail_nocontext;

	if (mm_alloc_cid(mm, p))
		goto fail_cid;

	if (percpu_counter_init_many(mm->rss_stat, 0, GFP_KERNEL_ACCOUNT,
				     NR_MM_COUNTERS))
		goto fail_pcpu;

	mm->user_ns = get_user_ns(user_ns);
	lru_gen_init_mm(mm);
	return mm;

fail_pcpu:
	mm_destroy_cid(mm);
fail_cid:
	destroy_context(mm);
fail_nocontext:
	mm_free_id(mm);
fail_noid:
	mm_free_pgd(mm);
fail_nopgd:
	futex_hash_free(mm);
fail_mm_init:
	free_mm(mm);
	return NULL;
}
```

Fields absent from [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) get their values from the caller. On the exec path they stay zero until [`arch_pick_mmap_layout()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L122), [`setup_arg_pages()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L598) and the ELF loader fill them; on the fork path they survive the [`memcpy`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/string_64.h#L18) from the parent (the address-layout fields, [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238), [`data_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1241), [`exec_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1242), [`stack_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1243), [`binfmt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1268), [`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259) and the arg/env ranges all copy across, while [`hiwater_rss`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1235)/[`hiwater_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1236) are re-seeded by [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) after [`dup_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732) finishes).

### mm_alloc and dup_mm feed mm_init from exec and fork

[`mm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1154) zeroes the whole object first, so on the exec path every field not touched by [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) starts at 0. [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) instead copies the parent wholesale, runs [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) to replace everything that must be private, duplicates the VMA tree with [`dup_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732), then re-seeds the high-water marks from the freshly copied counters and takes a module reference on the inherited [`binfmt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1268).

```c
/* kernel/fork.c:1151 */
/*
 * Allocate and initialize an mm_struct.
 */
struct mm_struct *mm_alloc(void)
{
	struct mm_struct *mm;

	mm = allocate_mm();
	if (!mm)
		return NULL;

	memset(mm, 0, sizeof(*mm));
	return mm_init(mm, current, current_user_ns());
}

/* kernel/fork.c:1515 */
static struct mm_struct *dup_mm(struct task_struct *tsk,
				struct mm_struct *oldmm)
{
	struct mm_struct *mm;
	int err;

	mm = allocate_mm();
	if (!mm)
		goto fail_nomem;

	memcpy(mm, oldmm, sizeof(*mm));

	if (!mm_init(mm, tsk, mm->user_ns))
		goto fail_nomem;

	uprobe_start_dup_mmap();
	err = dup_mmap(mm, oldmm);
	if (err)
		goto free_pt;
	uprobe_end_dup_mmap();

	mm->hiwater_rss = get_mm_rss(mm);
	mm->hiwater_vm = mm->total_vm;

	if (mm->binfmt && !try_module_get(mm->binfmt->module))
		goto free_pt;

	return mm;

free_pt:
	/* don't put binfmt in mmput, we haven't got module yet */
	mm->binfmt = NULL;
	mm_init_owner(mm, NULL);
	mmput(mm);
	if (err)
		uprobe_end_dup_mmap();

fail_nomem:
	return NULL;
}
```

[`bprm_mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L256) calls [`mm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1154) at the start of `execve(2)`, and [`copy_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1556) either shares the parent's descriptor with [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131) for [`CLONE_VM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/sched.h#L11) or duplicates it with [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515).

```c
/* fs/exec.c:261 */
	bprm->mm = mm = mm_alloc();

/* kernel/fork.c:1579 */
	if (clone_flags & CLONE_VM) {
		mmget(oldmm);
		mm = oldmm;
	} else {
		mm = dup_mm(tsk, current->mm);
		if (!mm)
			return -ENOMEM;
	}

	tsk->mm = mm;
	tsk->active_mm = mm;
	return 0;
}
```

### mm_count opens the structure from its own cache line

The structure begins with a nested anonymous struct holding nothing but [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137), marked [`____cacheline_aligned_in_smp`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cache.h#L65). According to the comment above it, "Fields which are often written to are placed in a separate cache line", and the kernel-doc on the field states that [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) as a whole counts as a single reference here and that the structure is freed when the count reaches 0.

```c
/* include/linux/mm_types.h:1121 */
struct kioctx_table;
struct iommu_mm_data;
struct mm_struct {
	struct {
		/*
		 * Fields which are often written to are placed in a separate
		 * cache line.
		 */
		struct {
			/**
			 * @mm_count: The number of references to &struct
			 * mm_struct (@mm_users count as 1).
			 *
			 * Use mmgrab()/mmdrop() to modify. When this drops to
			 * 0, the &struct mm_struct is freed.
			 */
			atomic_t mm_count;
		} ____cacheline_aligned_in_smp;
```

The placement comes from commit `c1753fd02a00` ("mm: move mm_count into its own cache line"), whose message explains the measured motive.

```
commit c1753fd02a0058ea43cbb31ab26d25be2f6cfe08
    mm: move mm_count into its own cache line

    The mm_struct mm_count field is frequently updated by mmgrab/mmdrop
    performed by context switch.  This causes false-sharing for surrounding
    mm_struct fields which are read-mostly.
    ...
    Move mm_count to the first field of mm_struct to minimize the amount of
    padding required: rather than adding padding before and after the mm_count
    field, padding is only added after mm_count.
```

[`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) and [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) are the only sanctioned modifiers. The comment inside [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) records that the full barrier implied by [`atomic_dec_and_test()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-instrumented.h#L1380) is part of the membarrier syscall's ordering scheme.

```c
/* include/linux/sched/mm.h:35 */
static inline void mmgrab(struct mm_struct *mm)
{
	atomic_inc(&mm->mm_count);
}
...
/* include/linux/sched/mm.h:47 */
static inline void mmdrop(struct mm_struct *mm)
{
	/*
	 * The implicit full barrier implied by atomic_dec_and_test() is
	 * required by the membarrier system call before returning to
	 * user-space, after storing to rq->curr.
	 */
	if (unlikely(atomic_dec_and_test(&mm->mm_count)))
		__mmdrop(mm);
}
```

[`proc_mem_open()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L837) shows the two counts used side by side. It converts the [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) reference returned by [`mm_access()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1393) into a descriptor-only pin, so an open `/proc/[pid]/mem` file keeps the structure readable without keeping the address space populated.

```c
/* fs/proc/base.c:845 */
	mm = mm_access(task, mode | PTRACE_MODE_FSCREDS);
	put_task_struct(task);

	if (IS_ERR(mm))
		return mm == ERR_PTR(-ESRCH) ? NULL : mm;

	/* ensure this mm_struct can't be freed */
	mmgrab(mm);
	/* but do not pin its memory */
	mmput(mm);

	return mm;
}
```

On [`CONFIG_PREEMPT_RT`](https://elixir.bootlin.com/linux/v7.0/source/kernel/Kconfig.preempt#L92) kernels a companion field, [`delayed_drop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1328), gives [`mmdrop_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L74) an [`rcu_head`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/types.h#L250) so the scheduler can push the final free out of the context-switch tail through [`call_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/rcu/tree.c#L3249); on the assumed non-RT x86-64 configuration the field is compiled out and [`mmdrop_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L81) collapses to [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47).

### mm_users counts address-space users and gates __mmput

[`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) is declared after the hot read-mostly fields with a kernel-doc comment tying it to [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131)/[`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) and to the chained release of [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137).

```c
/* include/linux/mm_types.h:1162 */
		/**
		 * @mm_users: The number of users including userspace.
		 *
		 * Use mmget()/mmget_not_zero()/mmput() to modify. When this
		 * drops to 0 (i.e. when the task exits and there are no other
		 * temporary reference holders), we also release a reference on
		 * @mm_count (which may then free the &struct mm_struct if
		 * @mm_count also drops to 0).
		 */
		atomic_t mm_users;
```

[`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131) increments unconditionally and [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) refuses to resurrect a count that already hit zero, which is what asynchronous walkers such as the swapoff loop rely on.

```c
/* include/linux/sched/mm.h:131 */
static inline void mmget(struct mm_struct *mm)
{
	atomic_inc(&mm->mm_users);
}

static inline bool mmget_not_zero(struct mm_struct *mm)
{
	return atomic_inc_not_zero(&mm->mm_users);
}
```

[`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) runs [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) on the final decrement, which empties the address space and then drops the [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference that [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) collectively held. Several fields toured below have their release hook here ([`ksm_exit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ksm.h#L77), [`khugepaged_exit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/khugepaged.h#L29), [`exit_aio()`](https://elixir.bootlin.com/linux/v7.0/source/fs/aio.c#L891), the [`mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198) unlink, the [`binfmt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1268) module put, [`lru_gen_del_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2930) and [`futex_hash_free()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1731)); the ordering details are teardown-lifecycle material beyond this page's field-level scope.

```c
/* kernel/fork.c:1167 */
static inline void __mmput(struct mm_struct *mm)
{
	VM_BUG_ON(atomic_read(&mm->mm_users));

	uprobe_clear_state(mm);
	exit_aio(mm);
	ksm_exit(mm);
	khugepaged_exit(mm); /* must run before exit_mmap */
	exit_mmap(mm);
	mm_put_huge_zero_folio(mm);
	set_mm_exe_file(mm, NULL);
	if (!list_empty(&mm->mmlist)) {
		spin_lock(&mmlist_lock);
		list_del(&mm->mmlist);
		spin_unlock(&mmlist_lock);
	}
	if (mm->binfmt)
		module_put(mm->binfmt->module);
	lru_gen_del_mm(mm);
	futex_hash_free(mm);
	mmdrop(mm);
}

/* kernel/fork.c:1190 */
/*
 * Decrement the use count and release all resources for an mm.
 */
void mmput(struct mm_struct *mm)
{
	might_sleep();

	if (atomic_dec_and_test(&mm->mm_users))
		__mmput(mm);
}
```

The exiting task drops its own user reference in [`exit_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L550), which also hands the MEMCG [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1290) forward first.

```c
/* kernel/exit.c:572 */
	smp_mb__after_spinlock();
	local_irq_disable();
	current->mm = NULL;
	membarrier_update_current_mm(NULL);
	enter_lazy_tlb(mm, current);
	local_irq_enable();
	task_unlock(current);
	mmap_read_unlock(mm);
	mm_update_next_owner(mm);
	mmput(mm);
```

### __mmdrop frees the structure and check_mm audits the counters

[`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) runs when [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reaches zero. It evicts lazy-TLB borrowers via [`cleanup_lazy_tlbs()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L670) (which IPIs the CPUs still set in [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432) under [`CONFIG_MMU_LAZY_TLB_SHOOTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L568)), releases the resources [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) allocated in reverse order, and returns the object to the slab.

```c
/* kernel/fork.c:713 */
/*
 * Called when the last reference to the mm
 * is dropped: either by a lazy thread or by
 * mmput. Free the page directory and the mm.
 */
void __mmdrop(struct mm_struct *mm)
{
	BUG_ON(mm == &init_mm);
	WARN_ON_ONCE(mm == current->mm);

	/* Ensure no CPUs are using this as their lazy tlb mm */
	cleanup_lazy_tlbs(mm);

	WARN_ON_ONCE(mm == current->active_mm);
	mm_free_pgd(mm);
	mm_free_id(mm);
	destroy_context(mm);
	mmu_notifier_subscriptions_destroy(mm);
	check_mm(mm);
	put_user_ns(mm->user_ns);
	mm_pasid_drop(mm);
	mm_destroy_cid(mm);
	percpu_counter_destroy_many(mm->rss_stat, NR_MM_COUNTERS);

	free_mm(mm);
}
```

[`check_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L622) is the exit audit for three field groups toured below. Every [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) counter, the [`pgtables_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1177) total and the [`pmd_huge_pte`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1300) deposit must be zero by the time the structure is freed, and a nonzero value prints the "Bad rss-counter state" diagnostic.

```c
/* kernel/fork.c:622 */
static void check_mm(struct mm_struct *mm)
{
	int i;

	BUILD_BUG_ON_MSG(ARRAY_SIZE(resident_page_types) != NR_MM_COUNTERS,
			 "Please make sure 'struct resident_page_types[]' is updated as well");

	for (i = 0; i < NR_MM_COUNTERS; i++) {
		long x = percpu_counter_sum(&mm->rss_stat[i]);

		if (unlikely(x)) {
			pr_alert("BUG: Bad rss-counter state mm:%p type:%s val:%ld Comm:%s Pid:%d\n",
				 mm, resident_page_types[i], x,
				 current->comm,
				 task_pid_nr(current));
		}
	}

	if (mm_pgtables_bytes(mm))
		pr_alert("BUG: non-zero pgtables_bytes on freeing mm: %ld\n",
				mm_pgtables_bytes(mm));

#if defined(CONFIG_TRANSPARENT_HUGEPAGE) && !defined(CONFIG_SPLIT_PMD_PTLOCKS)
	VM_BUG_ON_MM(mm->pmd_huge_pte, mm);
#endif
}
```

### mm_mt roots the VMA maple tree under three MM_MT_FLAGS

[`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) is the embedded [`struct maple_tree`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L222) that indexes every VMA by its virtual-address range; the older linked list and rbtree were removed when the tree took over in v6.1 (commit `763ecb035029`, "mm: remove the vma linked list").

```c
/* include/linux/mm_types.h:1140 */
		struct maple_tree mm_mt;
```

[`MM_MT_FLAGS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1413) fixes the tree's operating mode. [`MT_FLAGS_ALLOC_RANGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L171) makes the tree track free gaps so [`get_unmapped_area()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3868) searches can find holes, [`MT_FLAGS_LOCK_EXTERN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L178) declares that an outside lock (the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) field) serializes writers instead of the tree's internal spinlock, and [`MT_FLAGS_USE_RCU`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L172) enables lockless RCU readers, which is what the per-VMA-lock fault path walks.

```c
/* include/linux/maple_tree.h:171 */
#define MT_FLAGS_ALLOC_RANGE	0x01
#define MT_FLAGS_USE_RCU	0x02
...
#define MT_FLAGS_LOCK_EXTERN	0x300

/* include/linux/mm_types.h:1413 */
#define MM_MT_FLAGS	(MT_FLAGS_ALLOC_RANGE | MT_FLAGS_LOCK_EXTERN | \
			 MT_FLAGS_USE_RCU)
```

[`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) applies the flags and registers [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) as the external lock in its first two statements (shown in full above); [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) reaches the same state statically through [`MTREE_INIT_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L252).

```c
/* kernel/fork.c:1075 */
	mt_init_flags(&mm->mm_mt, MM_MT_FLAGS);
	mt_set_external_lock(&mm->mm_mt, &mm->mmap_lock);
```

Iteration over the tree goes through [`struct vma_iterator`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1497), whose [`VMA_ITERATOR`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1501) initializer and [`vma_iter_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1511) helper point a maple-tree cursor at [`mm->mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140).

```c
/* include/linux/mm_types.h:1497 */
struct vma_iterator {
	struct ma_state mas;
};

#define VMA_ITERATOR(name, __mm, __addr)				\
	struct vma_iterator name = {					\
		.mas = {						\
			.tree = &(__mm)->mm_mt,				\
			.index = __addr,				\
			.node = NULL,					\
			.status = ma_start,				\
		},							\
	}

static inline void vma_iter_init(struct vma_iterator *vmi,
		struct mm_struct *mm, unsigned long addr)
{
	mas_init(&vmi->mas, &mm->mm_mt, addr);
}
```

The `brk(2)` syscall shows the iterator against the tree together with the [`brk`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1256) and [`start_brk`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1256) layout fields and the [`stack_guard_gap`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L939) clearance (256 pages, 1 MiB with 4 KiB pages).

```c
/* mm/mmap.c:188 */
	vma_iter_init(&vmi, mm, oldbrk);
	next = vma_find(&vmi, newbrk + PAGE_SIZE + stack_guard_gap);
	if (next && newbrk + PAGE_SIZE > vm_start_gap(next))
		goto out;

	brkvma = vma_prev_limit(&vmi, mm->start_brk);
	/* Ok, looks good - let it rip. */
	if (do_brk_flags(&vmi, brkvma, oldbrk, newbrk - oldbrk, 0) < 0)
		goto out;

	mm->brk = brk;

/* mm/mmap.c:938 */
/* enforced gap between the expanding stack and other mappings. */
unsigned long stack_guard_gap = 256UL<<PAGE_SHIFT;
```

### map_count is bounded by sysctl_max_map_count, default 65530

[`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) is the plain-`int` running count of VMAs in the tree, incremented and decremented at every insert, split, merge and removal under the write-locked [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) (for example [`mm/vma.c:357`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L357) and [`mm/vma.c:1318`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1318)). Its declaration follows the page-table byte counter.

```c
/* include/linux/mm_types.h:1176 */
#ifdef CONFIG_MMU
		atomic_long_t pgtables_bytes;	/* size of all page tables */
#endif
		int map_count;			/* number of VMAs */

		spinlock_t page_table_lock; /* Protects page tables and some
					     * counters
					     */
```

The bound is `vm.max_map_count`, whose default [`DEFAULT_MAX_MAP_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L209) is `USHRT_MAX - MAPCOUNT_ELF_CORE_MARGIN` = 65535 - 5 = 65530, the margin reserving ELF core-dump section slots per the comment above [`MAPCOUNT_ELF_CORE_MARGIN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L208).

```c
/* include/linux/mm.h:208 */
#define MAPCOUNT_ELF_CORE_MARGIN	(5)
#define DEFAULT_MAX_MAP_COUNT	(USHRT_MAX - MAPCOUNT_ELF_CORE_MARGIN)

extern int sysctl_max_map_count;

/* mm/util.c:755 */
int sysctl_max_map_count __read_mostly = DEFAULT_MAX_MAP_COUNT;
```

[`do_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L335) rejects new mappings once the count exceeds the sysctl, and [`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866) applies the same check on the brk path (shown later with [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244)).

```c
/* mm/mmap.c:377 */
	/* Too many mappings? */
	if (mm->map_count > sysctl_max_map_count)
		return -ENOMEM;
```

### pgd and membarrier_state share the cache line switch_mm touches

[`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150) points at the top-level page table the hardware walks, and [`membarrier_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1159) is declared immediately after it because, per its kernel-doc, the field "is close to @pgd to hopefully fit in the same cache-line, which needs to be touched by switch_mm()".

```c
/* include/linux/mm_types.h:1149 */
		unsigned long task_size;	/* size of task vm space */
		pgd_t * pgd;

#ifdef CONFIG_MEMBARRIER
		/**
		 * @membarrier_state: Flags controlling membarrier behavior.
		 *
		 * This field is close to @pgd to hopefully fit in the same
		 * cache-line, which needs to be touched by switch_mm().
		 */
		atomic_t membarrier_state;
#endif
```

[`mm_alloc_pgd()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L575) fills the field from [`pgd_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L322), which on x86-64 allocates the 4 KiB page-global directory and copies the kernel half from [`swapper_pg_dir`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L27); [`mm_free_pgd()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L583) returns it in [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718).

```c
/* kernel/fork.c:574 */
#ifdef CONFIG_MMU
static inline int mm_alloc_pgd(struct mm_struct *mm)
{
	mm->pgd = pgd_alloc(mm);
	if (unlikely(!mm->pgd))
		return -ENOMEM;
	return 0;
}

static inline void mm_free_pgd(struct mm_struct *mm)
{
	pgd_free(mm, mm->pgd);
}
#else
#define mm_alloc_pgd(mm)	(0)
#define mm_free_pgd(mm)
#endif /* CONFIG_MMU */
```

The consumer is the context switch. [`switch_mm_irqs_off()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L783) feeds [`next->pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150) through [`build_cr3()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L161), which combines the PGD's physical address with the ASID's PCID bits and the LAM mask before the CR3 write.

```c
/* arch/x86/mm/tlb.c:161 */
static inline unsigned long build_cr3(pgd_t *pgd, u16 asid, unsigned long lam)
{
	unsigned long cr3 = __sme_pa(pgd) | lam;

	if (static_cpu_has(X86_FEATURE_PCID)) {
		cr3 |= kern_pcid(asid);
	} else {
		VM_WARN_ON_ONCE(asid != 0);
	}

	return cr3;
}

/* arch/x86/mm/tlb.c:945 */
reload_tlb:
	new_lam = mm_lam_cr3_mask(next);
	if (ns.need_flush) {
		VM_WARN_ON_ONCE(is_global_asid(ns.asid));
		this_cpu_write(cpu_tlbstate.ctxs[ns.asid].ctx_id, next->context.ctx_id);
		this_cpu_write(cpu_tlbstate.ctxs[ns.asid].tlb_gen, next_tlb_gen);
		load_new_mm_cr3(next->pgd, ns.asid, new_lam, true);

		trace_tlb_flush(TLB_FLUSH_ON_TASK_SWITCH, TLB_FLUSH_ALL);
	} else {
		/* The new ASID is already up to date. */
		load_new_mm_cr3(next->pgd, ns.asid, new_lam, false);

		trace_tlb_flush(TLB_FLUSH_ON_TASK_SWITCH, 0);
```

[`membarrier_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1159) holds the registered-and-ready bits of the `membarrier(2)` syscall, an anonymous enum in [`include/linux/sched/mm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L515) with eight `1U << n` values from [`MEMBARRIER_STATE_PRIVATE_EXPEDITED_READY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L516) (bit 0) to [`MEMBARRIER_STATE_PRIVATE_EXPEDITED_RSEQ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L523) (bit 7). Registration ORs a state bit in and calls [`sync_runqueues_membarrier_state()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/membarrier.c#L438) to mirror the value into every runqueue that currently runs this mm, so the context-switch fast path can test [`rq->membarrier_state`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/sched.h#L1230) instead of dereferencing the descriptor.

```c
/* kernel/sched/membarrier.c:438 */
static int sync_runqueues_membarrier_state(struct mm_struct *mm)
{
	int membarrier_state = atomic_read(&mm->membarrier_state);
	cpumask_var_t tmpmask;
	int cpu;

	if (atomic_read(&mm->mm_users) == 1 || num_online_cpus() == 1) {
		this_cpu_write(runqueues.membarrier_state, membarrier_state);

/* kernel/sched/membarrier.c:502 */
	if (atomic_read(&mm->membarrier_state) &
	    MEMBARRIER_STATE_GLOBAL_EXPEDITED_READY)
		return 0;
	atomic_or(MEMBARRIER_STATE_GLOBAL_EXPEDITED, &mm->membarrier_state);
	ret = sync_runqueues_membarrier_state(mm);
	if (ret)
		return ret;
	atomic_or(MEMBARRIER_STATE_GLOBAL_EXPEDITED_READY,
		  &mm->membarrier_state);
```

### page_table_lock and pgtables_bytes cover the page-table backing

[`page_table_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1181) (declared in the excerpt two sections up, with the comment "Protects page tables and some counters") serializes upper-level page-table installation and the fields that split PTE/PMD locks do not cover. [`pgtables_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1177) counts the bytes of all page-table pages backing the address space; [`mm_pgtables_bytes_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3268) zeroes it in [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072), helpers like [`mm_inc_nr_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3278) add `PTRS_PER_PTE * sizeof(pte_t)` (4 KiB) per PTE table, [`mm_pgtables_bytes()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3273) feeds `VmPTE` in `/proc/[pid]/status` and the oom-killer's badness score, and [`check_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L622) (shown above) demands it be zero at free.

```c
/* include/linux/mm.h:3267 */
#ifdef CONFIG_MMU
static inline void mm_pgtables_bytes_init(struct mm_struct *mm)
{
	atomic_long_set(&mm->pgtables_bytes, 0);
}

static inline unsigned long mm_pgtables_bytes(const struct mm_struct *mm)
{
	return atomic_long_read(&mm->pgtables_bytes);
}

static inline void mm_inc_nr_ptes(struct mm_struct *mm)
{
	atomic_long_add(PTRS_PER_PTE * sizeof(pte_t), &mm->pgtables_bytes);
}
```

### mmap_lock guards the tree and documents its own placement

[`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) is the [`struct rw_semaphore`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rwsem.h#L48) that serializes all VMA-tree writers and the readers that opt out of per-VMA locking. Its declaration carries a layout warning that constrains this entire region of the struct. According to the comment, "Typically the current mmap_lock's offset is 56 bytes from the last cacheline boundary, which is very optimal, as its two hot fields 'count' and 'owner' sit in 2 different cachelines", followed by "So please be careful with adding new fields before mmap_lock, which can easily push the 2 fields into one cacheline."

```c
/* include/linux/mm_types.h:1184 */
		/*
		 * Typically the current mmap_lock's offset is 56 bytes from
		 * the last cacheline boundary, which is very optimal, as
		 * its two hot fields 'count' and 'owner' sit in 2 different
		 * cachelines, and when mmap_lock is highly contended, both
		 * of the 2 fields will be accessed frequently, current layout
		 * will help to reduce cache bouncing.
		 *
		 * So please be careful with adding new fields before
		 * mmap_lock, which can easily push the 2 fields into one
		 * cacheline.
		 */
		struct rw_semaphore mmap_lock;
```

The lock's wrappers in [`include/linux/mmap_lock.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L533) couple every write acquisition and release to the [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222) seqcount covered in the next section, and [`MMAP_LOCK_INITIALIZER`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L17) provides the static form used by [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32).

```c
/* include/linux/mmap_lock.h:17 */
#define MMAP_LOCK_INITIALIZER(name) \
	.mmap_lock = __RWSEM_INITIALIZER((name).mmap_lock),

/* include/linux/mmap_lock.h:533 */
static inline void mmap_write_lock(struct mm_struct *mm)
{
	__mmap_lock_trace_start_locking(mm, true);
	down_write(&mm->mmap_lock);
	mm_lock_seqcount_begin(mm);
	__mmap_lock_trace_acquire_returned(mm, true, true);
}
...
/* include/linux/mmap_lock.h:575 */
static inline void mmap_write_unlock(struct mm_struct *mm)
{
	__mmap_lock_trace_released(mm, true);
	vma_end_write_all(mm);
	up_write(&mm->mmap_lock);
}
```

A representative writer is `mprotect(2)`, which takes the lock around its VMA walk at [`mm/mprotect.c:974`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L974) with [`mmap_write_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L533); the fork-time tree duplication in [`dup_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732) and the exec-time stack move in [`setup_arg_pages()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L598) use the killable variant [`mmap_write_lock_killable()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L549).

### mm_lock_seq and vma_writer_wait implement the per-VMA lock handshake

With [`CONFIG_PER_VMA_LOCK`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1403)=y, two fields let page faults take a single VMA's lock without touching [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222) is a [`seqcount_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/seqlock_types.h#L38) whose long declaration comment defines its lock-like semantics, and [`vma_writer_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1204) is the [`struct rcuwait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/types.h#L269) a write-locker sleeps on while VMA readers drain.

```c
/* include/linux/mm_types.h:1203 */
#ifdef CONFIG_PER_VMA_LOCK
		struct rcuwait vma_writer_wait;
		/*
		 * This field has lock-like semantics, meaning it is sometimes
		 * accessed with ACQUIRE/RELEASE semantics.
		 * Roughly speaking, incrementing the sequence number is
		 * equivalent to releasing locks on VMAs; reading the sequence
		 * number can be part of taking a read lock on a VMA.
		 * Incremented every time mmap_lock is write-locked/unlocked.
		 * Initialized to 0, therefore odd values indicate mmap_lock
		 * is write-locked and even values that it's released.
		 *
		 * Can be modified under write mmap_lock using RELEASE
		 * semantics.
		 * Can be read with no other protection when holding write
		 * mmap_lock.
		 * Can be read with ACQUIRE semantics if not holding write
		 * mmap_lock.
		 */
		seqcount_t mm_lock_seq;
#endif
```

The seqcount advances in lockstep with the rwsem. [`mmap_write_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L533) (shown above) calls [`mm_lock_seqcount_begin()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L123) after acquiring the rwsem, and [`vma_end_write_all()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L569) calls [`mm_lock_seqcount_end()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L128) directly before the rwsem is released or downgraded, which is what invalidates every per-VMA write lock at once (a VMA is write-locked by storing the current sequence into its [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958), so bumping the mm-wide sequence unlocks them all).

```c
/* include/linux/mmap_lock.h:118 */
static inline void mm_lock_seqcount_init(struct mm_struct *mm)
{
	seqcount_init(&mm->mm_lock_seq);
}

static inline void mm_lock_seqcount_begin(struct mm_struct *mm)
{
	do_raw_write_seqcount_begin(&mm->mm_lock_seq);
}

static inline void mm_lock_seqcount_end(struct mm_struct *mm)
{
	ASSERT_EXCLUSIVE_WRITER(mm->mm_lock_seq);
	do_raw_write_seqcount_end(&mm->mm_lock_seq);
}

/* include/linux/mmap_lock.h:561 */
/*
 * Drop all currently-held per-VMA locks.
 * This is called from the mmap_lock implementation directly before releasing
 * a write-locked mmap_lock (or downgrading it to read-locked).
 * This should normally NOT be called manually from other places.
 * If you want to call this manually anyway, keep in mind that this will release
 * *all* VMA write locks, including ones from further up the stack.
 */
static inline void vma_end_write_all(struct mm_struct *mm)
{
	mmap_assert_write_locked(mm);
	mm_lock_seqcount_end(mm);
}
```

Because odd values mean "write-locked", the seqcount doubles as a lockless snapshot facility. [`mmap_lock_speculate_try_begin()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L134) opens a speculative section that fails immediately while a writer holds the lock, and [`mmap_lock_speculate_retry()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L145) detects a writer that slipped in. The private-futex key lookup uses exactly this pair to resolve a uaddr's node without taking any mm lock.

```c
/* include/linux/mmap_lock.h:134 */
static inline bool mmap_lock_speculate_try_begin(struct mm_struct *mm, unsigned int *seq)
{
	/*
	 * Since mmap_lock is a sleeping lock, and waiting for it to become
	 * unlocked is more or less equivalent with taking it ourselves, don't
	 * bother with the speculative path if mmap_lock is already write-locked
	 * and take the slow path, which takes the lock.
	 */
	return raw_seqcount_try_begin(&mm->mm_lock_seq, *seq);
}

static inline bool mmap_lock_speculate_retry(struct mm_struct *mm, unsigned int seq)
{
	return read_seqcount_retry(&mm->mm_lock_seq, seq);
}

/* kernel/futex/core.c:365 */
static int futex_key_to_node_opt(struct mm_struct *mm, unsigned long addr)
{
	int seq, node;

	guard(rcu)();

	if (!mmap_lock_speculate_try_begin(mm, &seq))
		return -EBUSY;

	node = __futex_key_to_node(mm, addr);

	if (mmap_lock_speculate_retry(mm, seq))
		return -EAGAIN;

	return node;
}
```

[`vma_writer_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1204) is the sleep side of writer-versus-reader exclusion on one VMA. [`__vma_start_exclude_readers()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L105) (called under write [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) from [`__vma_start_write()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L139)) parks on the rcuwait until the VMA's [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) shows all readers gone, and [`vma_refcount_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L210) wakes it when the last reader drops out. [`mmap_init_lock()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1063) initializes the rcuwait via [`rcuwait_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rcuwait.h#L12) next to the rwsem and seqcount.

```c
/* mm/mmap_lock.c:126 */
	err = rcuwait_wait_event(&vma->vm_mm->vma_writer_wait,
		   refcount_read(&vma->vm_refcnt) == tgt_refcnt,
		   ves->state);

/* include/linux/mmap_lock.h:210 */
static inline void vma_refcount_put(struct vm_area_struct *vma)
{
	/* Use a copy of vm_mm in case vma is freed after we drop vm_refcnt. */
	struct mm_struct *mm = vma->vm_mm;
	int newcnt;

	__vma_lockdep_release_read(vma);
	newcnt = __vma_refcount_put_return(vma);

	/*
	 * __vma_start_exclude_readers() may be sleeping waiting for readers to
	 * drop their reference count, so wake it up if we were the last reader
	 * blocking it from being acquired.
	 *
	 * We may be raced by other readers temporarily incrementing the
	 * reference count, though the race window is very small, this might
	 * cause spurious wakeups.
	 */
	if (newcnt && __vma_are_readers_excluded(newcnt))
		rcuwait_wake_up(&mm->vma_writer_wait);
}

/* kernel/fork.c:1063 */
static void mmap_init_lock(struct mm_struct *mm)
{
	init_rwsem(&mm->mmap_lock);
	mm_lock_seqcount_init(mm);
#ifdef CONFIG_PER_VMA_LOCK
	rcuwait_init(&mm->vma_writer_wait);
#endif
}
```

The read-lock fast path in [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) closes the loop by comparing the VMA's [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) against [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222) with ACQUIRE semantics and backing out through [`vma_refcount_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L210) when the VMA is write-locked.

```c
/* mm/mmap_lock.c:262 */
	if (unlikely(vma->vm_lock_seq == raw_read_seqcount(&mm->mm_lock_seq))) {
		vma_refcount_put(vma);
		vma = NULL;
		goto err;
	}
```

### mmlist strings swap-touched descriptors off init_mm

[`mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198) is a [`struct list_head`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/types.h#L204) linking every descriptor that may hold swap entries into one global chain anchored at [`init_mm.mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198), protected by the global [`mmlist_lock`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1015).

```c
/* include/linux/mm_types.h:1198 */
		struct list_head mmlist; /* List of maybe swapped mm's.	These
					  * are globally strung together off
					  * init_mm.mmlist, and are protected
					  * by mmlist_lock
					  */

/* kernel/fork.c:1015 */
__cacheline_aligned_in_smp DEFINE_SPINLOCK(mmlist_lock);
```

Enrollment happens the first time an anonymous page of the mm is unmapped to swap. [`try_to_unmap_one()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L1978) adds the descriptor with a double-checked [`list_empty()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/list.h#L379) before it converts the PTE to a swap entry (also moving one page of accounting from [`MM_ANONPAGES`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L28) to [`MM_SWAPENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L29)), and the fork path in [`copy_nonpresent_pte()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L938) enrolls the child when it copies a swap PTE.

```c
/* mm/rmap.c:2299 */
			if (list_empty(&mm->mmlist)) {
				spin_lock(&mmlist_lock);
				if (list_empty(&mm->mmlist))
					list_add(&mm->mmlist, &init_mm.mmlist);
				spin_unlock(&mmlist_lock);
			}
			dec_mm_counter(mm, MM_ANONPAGES);
			inc_mm_counter(mm, MM_SWAPENTS);

/* mm/memory.c:953 */
		/* make sure dst_mm is on swapoff's mmlist. */
		if (unlikely(list_empty(&dst_mm->mmlist))) {
			spin_lock(&mmlist_lock);
			if (list_empty(&dst_mm->mmlist))
				list_add(&dst_mm->mmlist,
						&src_mm->mmlist);
			spin_unlock(&mmlist_lock);
		}
```

The consumer is `swapoff(2)`. [`try_to_unuse()`](https://elixir.bootlin.com/linux/v7.0/source/mm/swapfile.c#L2399) walks the chain from [`init_mm.mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198), pinning each descriptor with [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) so a concurrently exiting process is skipped rather than resurrected, and dropping each with [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) after its pages are brought back. [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) (shown above) unlinks the descriptor at teardown.

```c
/* mm/swapfile.c:2418 */
	prev_mm = &init_mm;
	mmget(prev_mm);

	spin_lock(&mmlist_lock);
	p = &init_mm.mmlist;
	while (swap_usage_in_pages(si) &&
	       !signal_pending(current) &&
	       (p = p->next) != &init_mm.mmlist) {

		mm = list_entry(p, struct mm_struct, mmlist);
		if (!mmget_not_zero(mm))
			continue;
		spin_unlock(&mmlist_lock);
		mmput(prev_mm);
		prev_mm = mm;
		retval = unuse_mm(mm, type);
```

### arch_pick_mmap_layout computes mmap_base, mmap_legacy_base and task_size

Four fields describe where mappings go. [`mmap_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1142) is the ceiling the default top-down [`get_unmapped_area()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3868) search descends from, [`mmap_legacy_base`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1143) is the floor for bottom-up legacy layout, the two `mmap_compat_*` variants repeat both for the other syscall width (x86-64 selects [`CONFIG_HAVE_ARCH_COMPAT_MMAP_BASES`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L1258) so a 64-bit process gets sane 32-bit-syscall placements and vice versa), and [`task_size`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1149) records the address-space size the process runs with.

```c
/* include/linux/mm_types.h:1142 */
		unsigned long mmap_base;	/* base of mmap area */
		unsigned long mmap_legacy_base;	/* base of mmap area in bottom-up allocations */
#ifdef CONFIG_HAVE_ARCH_COMPAT_MMAP_BASES
		/* Base addresses for compatible mmap() */
		unsigned long mmap_compat_base;
		unsigned long mmap_compat_legacy_base;
#endif
		unsigned long task_size;	/* size of task vm space */
```

All four bases plus the layout direction are chosen once per exec. [`setup_new_exec()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L1315) calls [`arch_pick_mmap_layout()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L122) and then stores [`TASK_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L64) into [`task_size`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1149); on x86-64 [`TASK_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L64) resolves to [`task_size_max()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64.h#L138) for a 64-bit task (2^47 - 4096 bytes without LA57, 2^56 - 4096 with it) and [`IA32_PAGE_OFFSET`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L59) for a TIF_ADDR32 task.

```c
/* fs/exec.c:1315 */
void setup_new_exec(struct linux_binprm * bprm)
{
	/* Setup things that can depend upon the personality */
	struct task_struct *me = current;

	arch_pick_mmap_layout(me->mm, &bprm->rlim_stack);

	arch_setup_new_exec();

	/* Set the new mm task size. We have to do that late because it may
	 * depend on TIF_32BIT which is only updated in flush_thread() on
	 * some architectures like powerpc
	 */
	me->mm->task_size = TASK_SIZE;
	up_write(&me->signal->exec_update_lock);
	mutex_unlock(&me->signal->cred_guard_mutex);
}

/* arch/x86/include/asm/page_64_types.h:53 */
#define TASK_SIZE_MAX		task_size_max()
#define DEFAULT_MAP_WINDOW	((1UL << 47) - PAGE_SIZE)

/* This decides where the kernel will search for a free chunk of vm
 * space during mmap's.
 */
#define IA32_PAGE_OFFSET	((current->personality & ADDR_LIMIT_3GB) ? \
					0xc0000000 : 0xFFFFe000)

#define TASK_SIZE_LOW		(test_thread_flag(TIF_ADDR32) ? \
					IA32_PAGE_OFFSET : DEFAULT_MAP_WINDOW)
#define TASK_SIZE		(test_thread_flag(TIF_ADDR32) ? \
					IA32_PAGE_OFFSET : TASK_SIZE_MAX)
```

The x86 implementation stores the layout direction as the [`MMF_TOPDOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1919) bit in [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1273) and computes both bases per width. The top-down base subtracts the stack rlimit (padded by [`stack_maxrandom_size()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L41) plus [`stack_guard_gap`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L939), and clamped between [`SIZE_128M`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L60), 128 MiB, and 5/6 of the task size) and an ASLR offset from the top; the legacy base is [`__TASK_UNMAPPED_BASE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/processor.h#L677) (one third of the task size) plus the same ASLR offset.

```c
/* arch/x86/mm/mmap.c:60 */
#define SIZE_128M    (128 * 1024 * 1024UL)

/* arch/x86/mm/mmap.c:82 */
static unsigned long mmap_base(unsigned long rnd, unsigned long task_size,
			       const struct rlimit *rlim_stack)
{
	unsigned long gap = rlim_stack->rlim_cur;
	unsigned long pad = stack_maxrandom_size(task_size) + stack_guard_gap;

	/* Values close to RLIM_INFINITY can overflow. */
	if (gap + pad > gap)
		gap += pad;

	/*
	 * Top of mmap area (just below the process stack).
	 * Leave an at least ~128 MB hole with possible stack randomization.
	 */
	gap = clamp(gap, SIZE_128M, (task_size / 6) * 5);

	return PAGE_ALIGN(task_size - gap - rnd);
}

static unsigned long mmap_legacy_base(unsigned long rnd,
				      unsigned long task_size)
{
	return __TASK_UNMAPPED_BASE(task_size) + rnd;
}

/* arch/x86/include/asm/processor.h:677 */
#define __TASK_UNMAPPED_BASE(task_size)	(PAGE_ALIGN(task_size / 3))

/* arch/x86/mm/mmap.c:111 */
static void arch_pick_mmap_base(unsigned long *base, unsigned long *legacy_base,
		unsigned long random_factor, unsigned long task_size,
		const struct rlimit *rlim_stack)
{
	*legacy_base = mmap_legacy_base(random_factor, task_size);
	if (mmap_is_legacy())
		*base = *legacy_base;
	else
		*base = mmap_base(random_factor, task_size, rlim_stack);
}

void arch_pick_mmap_layout(struct mm_struct *mm, const struct rlimit *rlim_stack)
{
	if (mmap_is_legacy())
		mm_flags_clear(MMF_TOPDOWN, mm);
	else
		mm_flags_set(MMF_TOPDOWN, mm);

	arch_pick_mmap_base(&mm->mmap_base, &mm->mmap_legacy_base,
			arch_rnd(mmap64_rnd_bits), task_size_64bit(0),
			rlim_stack);

#ifdef CONFIG_HAVE_ARCH_COMPAT_MMAP_BASES
	/*
	 * The mmap syscall mapping base decision depends solely on the
	 * syscall type (64-bit or compat). This applies for 64bit
	 * applications and 32bit applications. The 64bit syscall uses
	 * mmap_base, the compat syscall uses mmap_compat_base.
	 */
	arch_pick_mmap_base(&mm->mmap_compat_base, &mm->mmap_compat_legacy_base,
			arch_rnd(mmap32_rnd_bits), task_size_32bit(),
			rlim_stack);
#endif
}
```

[`get_mmap_base()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L146) reads the stored bases back, picking the compat pair inside a 32-bit syscall, and the unmapped-area searches in [`arch/x86/kernel/sys_x86_64.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/sys_x86_64.c#L167) use it as their search limit.

```c
/* arch/x86/mm/mmap.c:146 */
unsigned long get_mmap_base(int is_legacy)
{
	struct mm_struct *mm = current->mm;

#ifdef CONFIG_HAVE_ARCH_COMPAT_MMAP_BASES
	if (in_32bit_syscall()) {
		return is_legacy ? mm->mmap_compat_legacy_base
				 : mm->mmap_compat_base;
	}
#endif
	return is_legacy ? mm->mmap_legacy_base : mm->mmap_base;
}

/* arch/x86/kernel/sys_x86_64.c:207 */
	info.high_limit = get_mmap_base(0);
```

### The segment boundaries and argument ranges serialize under arg_lock

Eleven `unsigned long` fields snapshot the exec image, and the dedicated spinlock [`arg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1253) (initialized in [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072)) serializes updates to them, per its comment "protect the below fields".

```c
/* include/linux/mm_types.h:1253 */
		spinlock_t arg_lock; /* protect the below fields */

		unsigned long start_code, end_code, start_data, end_data;
		unsigned long start_brk, brk, start_stack;
		unsigned long arg_start, arg_end, env_start, env_end;

		unsigned long saved_auxv[AT_VECTOR_SIZE]; /* for /proc/PID/auxv */

#ifdef CONFIG_ARCH_HAS_ELF_CORE_EFLAGS
		/* the ABI-related flags from the ELF header. Used for core dump */
		unsigned long saved_e_flags;
#endif
```

The ELF loader writes the code and data boundaries after mapping the segments, and places the brk area. [`load_elf_binary()`](https://elixir.bootlin.com/linux/v7.0/source/fs/binfmt_elf.c#L833) computes [`start_code`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1255)/[`end_code`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1255)/[`start_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1255)/[`end_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1255) from the executable's program headers, records [`start_stack`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1256), and seeds [`start_brk`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1256)/[`brk`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1256) past the loaded image (page-aligned, moved into the [`ELF_ET_DYN_BASE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/elf.h#L235) region for static PIE, then randomized by [`arch_randomize_brk()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/process.c#L1026) under [`PF_RANDOMIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L1775)).

```c
/* fs/binfmt_elf.c:1302 */
	mm = current->mm;
	mm->end_code = end_code;
	mm->start_code = start_code;
	mm->start_data = start_data;
	mm->end_data = end_data;
	mm->start_stack = bprm->p;
	...
/* fs/binfmt_elf.c:1331 */
	mm->start_brk = mm->brk = ELF_PAGEALIGN(elf_brk);
	...
		mm->brk = mm->start_brk = arch_randomize_brk(mm);
```

The argument and environment ranges are written twice on the exec path. [`setup_arg_pages()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L598) sets a provisional [`arg_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1257) when it relocates the stack VMA, and [`create_elf_tables()`](https://elixir.bootlin.com/linux/v7.0/source/fs/binfmt_elf.c#L165) finalizes all four boundaries while it writes the argv/envp pointer arrays onto the new stack.

```c
/* fs/exec.c:644 */
	bprm->p -= stack_shift;
	mm->arg_start = bprm->p;

/* fs/binfmt_elf.c:330 */
	/* Populate list of argv pointers back to argv strings. */
	p = mm->arg_end = mm->arg_start;
	while (argc-- > 0) {
		size_t len;
		if (put_user((elf_addr_t)p, sp++))
			return -EFAULT;
		len = strnlen_user((void __user *)p, MAX_ARG_STRLEN);
		if (!len || len > MAX_ARG_STRLEN)
			return -EINVAL;
		p += len;
	}
	if (put_user(0, sp++))
		return -EFAULT;
	mm->arg_end = p;

	/* Populate list of envp pointers back to envp strings. */
	mm->env_end = mm->env_start = p;
```

After exec, `prctl(PR_SET_MM_MAP)` is the one writer, and it takes [`arg_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1253) around the batch update (with [`mmap_read_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L589) held to exclude `brk(2)`, per the comment at [`kernel/sys.c:2121`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sys.c#L2121)). Readers such as [`get_mm_cmdline()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L291) (behind `/proc/[pid]/cmdline`) take the same lock to see a consistent set of boundaries.

```c
/* kernel/sys.c:2138 */
	spin_lock(&mm->arg_lock);
	mm->start_code	= prctl_map.start_code;
	mm->end_code	= prctl_map.end_code;
	mm->start_data	= prctl_map.start_data;
	mm->end_data	= prctl_map.end_data;
	mm->start_brk	= prctl_map.start_brk;
	mm->brk		= prctl_map.brk;
	mm->start_stack	= prctl_map.start_stack;
	mm->arg_start	= prctl_map.arg_start;
	mm->arg_end	= prctl_map.arg_end;
	mm->env_start	= prctl_map.env_start;
	mm->env_end	= prctl_map.env_end;
	spin_unlock(&mm->arg_lock);

/* fs/proc/base.c:302 */
	spin_lock(&mm->arg_lock);
	arg_start = mm->arg_start;
	arg_end = mm->arg_end;
	env_start = mm->env_start;
	env_end = mm->env_end;
	spin_unlock(&mm->arg_lock);
```

[`saved_e_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1263) preserves the ELF header's [`e_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/elf.h#L242) for core dumps behind [`CONFIG_ARCH_HAS_ELF_CORE_EFLAGS`](https://elixir.bootlin.com/linux/v7.0/source/fs/Kconfig.binfmt#L187); only riscv selects that option in v7.0, so the field is compiled out on x86-64.

### saved_auxv snapshots the ELF auxiliary vector in AT_VECTOR_SIZE words

[`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259) keeps the auxiliary vector the loader handed to userspace, so `/proc/[pid]/auxv` can reproduce it later. Its size, [`AT_VECTOR_SIZE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L31), is `2*(AT_VECTOR_SIZE_ARCH + AT_VECTOR_SIZE_BASE + 1)` words (two words per entry plus the [`AT_NULL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/auxvec.h#L9) terminator pair). [`AT_VECTOR_SIZE_BASE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/auxvec.h#L7) is 24 and x86-64's [`AT_VECTOR_SIZE_ARCH`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/uapi/asm/auxvec.h#L15) is 3 with [`CONFIG_IA32_EMULATION`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L3134)=y (2 without), giving 56 words, 448 bytes.

```c
/* include/linux/mm_types.h:28 */
#ifndef AT_VECTOR_SIZE_ARCH
#define AT_VECTOR_SIZE_ARCH 0
#endif
#define AT_VECTOR_SIZE (2*(AT_VECTOR_SIZE_ARCH + AT_VECTOR_SIZE_BASE + 1))

/* include/linux/auxvec.h:7 */
#define AT_VECTOR_SIZE_BASE 24 /* NEW_AUX_ENT entries in auxiliary table */
  /* number of "#define AT_.*" above, minus {AT_NULL, AT_IGNORE, AT_NOTELF} */

/* arch/x86/include/uapi/asm/auxvec.h:14 */
#if defined(__KERNEL__) && (defined(CONFIG_IA32_EMULATION) || !defined(CONFIG_X86_64))
# define AT_VECTOR_SIZE_ARCH 3
#else /* else it's non-compat x86-64 */
# define AT_VECTOR_SIZE_ARCH 2
#endif
```

[`create_elf_tables()`](https://elixir.bootlin.com/linux/v7.0/source/fs/binfmt_elf.c#L165) builds the vector directly inside the array through its [`NEW_AUX_ENT`](https://elixir.bootlin.com/linux/v7.0/source/fs/binfmt_elf.c#L235) macro and then copies the populated prefix onto the userspace stack, so the kernel copy and the process's copy match by construction.

```c
/* fs/binfmt_elf.c:232 */
	/* Create the ELF interpreter info */
	elf_info = (elf_addr_t *)mm->saved_auxv;
	/* update AT_VECTOR_SIZE_BASE if the number of NEW_AUX_ENT() changes */
#define NEW_AUX_ENT(id, val) \
	do { \
		*elf_info++ = id; \
		*elf_info++ = val; \
	} while (0)
...
/* fs/binfmt_elf.c:360 */
	/* Put the elf_info on the stack in the right place.  */
	if (copy_to_user(sp, mm->saved_auxv, ei_index * sizeof(elf_addr_t)))
		return -EFAULT;
```

[`auxv_read()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L1081) serves the field to `/proc/[pid]/auxv` readers, scanning in entry pairs until the [`AT_NULL`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/auxvec.h#L9) terminator; this is the copy-to-user path the [`mm_cache_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L3002) usercopy whitelist covers. `prctl(PR_SET_MM_MAP)` may also overwrite the array (its [`BUILD_BUG_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/build_bug.h#L50) at [`kernel/sys.c:2067`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sys.c#L2067) pins the size), and the comment at [`kernel/sys.c:2152`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sys.c#L2152) records that this update is deliberately lockless, so a concurrent `/proc` reader may observe a partially updated vector.

```c
/* fs/proc/base.c:1081 */
static ssize_t auxv_read(struct file *file, char __user *buf,
			size_t count, loff_t *ppos)
{
	struct mm_struct *mm = file->private_data;
	unsigned int nwords = 0;

	if (!mm)
		return 0;
	do {
		nwords += 2;
	} while (mm->saved_auxv[nwords - 2] != 0); /* AT_NULL */
	return simple_read_from_buffer(buf, count, ppos, mm->saved_auxv,
				       nwords * sizeof(mm->saved_auxv[0]));
}

/* kernel/sys.c:2067 */
	BUILD_BUG_ON(sizeof(user_auxv) != sizeof(mm->saved_auxv));
```

### rss_stat counts resident pages in four percpu counters

[`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) is an array of [`NR_MM_COUNTERS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L31) (4) [`struct percpu_counter`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/percpu_counter.h#L22) objects, one per resident-page class; the enum in [`include/linux/mm_types_task.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L26) names the indices. The counters became percpu in v6.2 (commit `f1a7941243c1`, "mm: convert mm's rss stats into percpu_counter"), replacing the earlier per-thread SPLIT_RSS_COUNTING cache.

```c
/* include/linux/mm_types_task.h:22 */
/*
 * When updating this, please also update struct resident_page_types[] in
 * kernel/fork.c
 */
enum {
	MM_FILEPAGES,	/* Resident file mapping pages */
	MM_ANONPAGES,	/* Resident anonymous pages */
	MM_SWAPENTS,	/* Anonymous swap entries */
	MM_SHMEMPAGES,	/* Resident shared memory pages */
	NR_MM_COUNTERS
};

/* include/linux/mm_types.h:1266 */
		struct percpu_counter rss_stat[NR_MM_COUNTERS];
```

[`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) allocates the percpu storage with [`percpu_counter_init_many()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/percpu_counter.h#L37) and [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) destroys it (both shown above). The accessors expose the two precision levels of a percpu counter. [`get_mm_counter()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3063) reads the batched approximation, [`get_mm_counter_sum()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3068) folds in every CPU's delta, the modifiers wrap `percpu_counter_add/inc/dec` and fire the [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) tracepoint through [`mm_trace_rss_stat()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L180), and [`mm_counter()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3104)/[`mm_counter_file()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3097) map a folio to its index.

```c
/* include/linux/mm.h:3060 */
/*
 * per-process(per-mm_struct) statistics.
 */
static inline unsigned long get_mm_counter(struct mm_struct *mm, int member)
{
	return percpu_counter_read_positive(&mm->rss_stat[member]);
}

static inline unsigned long get_mm_counter_sum(struct mm_struct *mm, int member)
{
	return percpu_counter_sum_positive(&mm->rss_stat[member]);
}

void mm_trace_rss_stat(struct mm_struct *mm, int member);

static inline void add_mm_counter(struct mm_struct *mm, int member, long value)
{
	percpu_counter_add(&mm->rss_stat[member], value);

	mm_trace_rss_stat(mm, member);
}

static inline void inc_mm_counter(struct mm_struct *mm, int member)
{
	percpu_counter_inc(&mm->rss_stat[member]);

	mm_trace_rss_stat(mm, member);
}

static inline void dec_mm_counter(struct mm_struct *mm, int member)
{
	percpu_counter_dec(&mm->rss_stat[member]);

	mm_trace_rss_stat(mm, member);
}

/* Optimized variant when folio is already known not to be anon */
static inline int mm_counter_file(struct folio *folio)
{
	if (folio_test_swapbacked(folio))
		return MM_SHMEMPAGES;
	return MM_FILEPAGES;
}

static inline int mm_counter(struct folio *folio)
{
	if (folio_test_anon(folio))
		return MM_ANONPAGES;
	return mm_counter_file(folio);
}
```

Fault and unmap paths move pages between the classes; [`do_swap_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4706) transfers a swapped-in range from [`MM_SWAPENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L29) back to [`MM_ANONPAGES`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L28) in one paired [`add_mm_counter()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3075) call, and the [`try_to_unmap_one()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L1978) excerpt above performs the reverse move. `/proc/[pid]/status` sums the precise variants in [`task_mem()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L37).

```c
/* mm/memory.c:5002 */
	add_mm_counter(vma->vm_mm, MM_ANONPAGES, nr_pages);
	add_mm_counter(vma->vm_mm, MM_SWAPENTS, -nr_pages);

/* fs/proc/task_mmu.c:42 */
	anon = get_mm_counter_sum(mm, MM_ANONPAGES);
	file = get_mm_counter_sum(mm, MM_FILEPAGES);
	shmem = get_mm_counter_sum(mm, MM_SHMEMPAGES);
```

### hiwater_rss and hiwater_vm latch peaks before shrink operations

The two high-water marks are plain fields updated only when a value is about to drop, which keeps them off the fault fast path. [`update_hiwater_rss()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3135) latches [`get_mm_rss()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3111) (the sum of the three resident classes, excluding [`MM_SWAPENTS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types_task.h#L29)) and [`update_hiwater_vm()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3143) latches [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238); the `get_mm_hiwater_*` readers take the max of the latch and the live value.

```c
/* include/linux/mm_types.h:1235 */
		unsigned long hiwater_rss; /* High-watermark of RSS usage */
		unsigned long hiwater_vm;  /* High-water virtual memory usage */

/* include/linux/mm.h:3111 */
static inline unsigned long get_mm_rss(struct mm_struct *mm)
{
	return get_mm_counter(mm, MM_FILEPAGES) +
		get_mm_counter(mm, MM_ANONPAGES) +
		get_mm_counter(mm, MM_SHMEMPAGES);
}
...
/* include/linux/mm.h:3125 */
static inline unsigned long get_mm_hiwater_rss(struct mm_struct *mm)
{
	return max(mm->hiwater_rss, get_mm_rss(mm));
}

static inline unsigned long get_mm_hiwater_vm(struct mm_struct *mm)
{
	return max(mm->hiwater_vm, mm->total_vm);
}

static inline void update_hiwater_rss(struct mm_struct *mm)
{
	unsigned long _rss = get_mm_rss(mm);

	if (data_race(mm->hiwater_rss) < _rss)
		data_race(mm->hiwater_rss = _rss);
}

static inline void update_hiwater_vm(struct mm_struct *mm)
{
	if (mm->hiwater_vm < mm->total_vm)
		mm->hiwater_vm = mm->total_vm;
}
```

The zap path latches RSS before tearing down PTEs, and the munmap completion path latches virtual size before subtracting from [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238); [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) (shown above) re-seeds both after fork so the child's peaks restart from its own baseline. According to the comment in [`task_mem()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L37), "mm maintains hiwater_vm and hiwater_rss only when about to *lower* total_vm or rss", so `/proc` collectors take the max themselves.

```c
/* mm/memory.c:2201 */
	update_hiwater_rss(vma->vm_mm);

/* mm/vma.c:1326 */
	vms_clear_ptes(vms, mas_detach, !vms->unlock);
	/* Update high watermark before we lower total_vm */
	update_hiwater_vm(mm);
	/* Stat accounting */
	WRITE_ONCE(mm->total_vm, READ_ONCE(mm->total_vm) - vms->nr_pages);
```

### The _vm counters and def_flags account and bound address-space usage

Six counters and one flag template complete the accounting group. [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238) counts all mapped pages, [`locked_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1239) counts [`VM_LOCKED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L420) pages, [`pinned_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1240) is an [`atomic64_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/types.h#L195) counting long-term pins taken by drivers, and [`data_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1241)/[`exec_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1242)/[`stack_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1243) partition mappings by the flag combinations named in their comments. [`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) is the [`vm_flags_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L691) template ORed into every new mapping.

```c
/* include/linux/mm_types.h:1238 */
		unsigned long total_vm;	   /* Total pages mapped */
		unsigned long locked_vm;   /* Pages that have PG_mlocked set */
		atomic64_t    pinned_vm;   /* Refcount permanently increased */
		unsigned long data_vm;	   /* VM_WRITE & ~VM_SHARED & ~VM_STACK */
		unsigned long exec_vm;	   /* VM_EXEC & ~VM_WRITE & ~VM_STACK */
		unsigned long stack_vm;	   /* VM_STACK */
		vm_flags_t def_flags;
```

[`vm_stat_account()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1360) is the single classifier that moves [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238) and the three partitions on every map, unmap and expansion, and [`may_expand_vm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1335) is the admission check comparing [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238) against [`RLIMIT_AS`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/asm-generic/resource.h#L39) and [`data_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1241) against [`RLIMIT_DATA`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/asm-generic/resource.h#L18) (with a Valgrind workaround for a zero soft limit, overridable by the [`ignore_rlimit_data`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L77) boot option).

```c
/* mm/mmap.c:1360 */
void vm_stat_account(struct mm_struct *mm, vm_flags_t flags, long npages)
{
	WRITE_ONCE(mm->total_vm, READ_ONCE(mm->total_vm)+npages);

	if (is_exec_mapping(flags))
		mm->exec_vm += npages;
	else if (is_stack_mapping(flags))
		mm->stack_vm += npages;
	else if (is_data_mapping(flags))
		mm->data_vm += npages;
}

/* mm/mmap.c:1331 */
/*
 * Return true if the calling process may expand its vm space by the passed
 * number of pages
 */
bool may_expand_vm(struct mm_struct *mm, vm_flags_t flags, unsigned long npages)
{
	if (mm->total_vm + npages > rlimit(RLIMIT_AS) >> PAGE_SHIFT)
		return false;

	if (is_data_mapping(flags) &&
	    mm->data_vm + npages > rlimit(RLIMIT_DATA) >> PAGE_SHIFT) {
		/* Workaround for Valgrind */
		if (rlimit(RLIMIT_DATA) == 0 &&
		    mm->data_vm + npages <= rlimit_max(RLIMIT_DATA) >> PAGE_SHIFT)
			return true;

		pr_warn_once("%s (%d): VmData %lu exceed data ulimit %lu. Update limits%s.\n",
			     current->comm, current->pid,
			     (mm->data_vm + npages) << PAGE_SHIFT,
			     rlimit(RLIMIT_DATA),
			     ignore_rlimit_data ? "" : " or use boot option ignore_rlimit_data");

		if (!ignore_rlimit_data)
			return false;
	}

	return true;
}
```

The mremap accounting helper shows both [`total_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1238) (via [`vm_stat_account()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1360)) and [`locked_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1239) moving together when a locked mapping grows.

```c
/* mm/mremap.c:1019 */
static void vrm_stat_account(struct vma_remap_struct *vrm,
			     unsigned long bytes)
{
	unsigned long pages = bytes >> PAGE_SHIFT;
	struct mm_struct *mm = current->mm;
	struct vm_area_struct *vma = vrm->vma;

	vm_stat_account(mm, vma->vm_flags, pages);
	if (vma->vm_flags & VM_LOCKED)
		mm->locked_vm += pages;
}
```

[`pinned_vm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1240) is atomic because drivers charge it without [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). The InfiniBand core (in [`drivers/infiniband/core/umem.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/infiniband/core/umem.c), the memory-registration layer every RDMA hardware driver goes through) enforces [`RLIMIT_MEMLOCK`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/asm-generic/resource.h#L35) against it in [`ib_umem_get()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/infiniband/core/umem.c#L165), and io_uring charges its registered buffers through [`io_account_mem()`](https://elixir.bootlin.com/linux/v7.0/source/io_uring/rsrc.c#L69).

```c
/* drivers/infiniband/core/umem.c:220 */
	lock_limit = rlimit(RLIMIT_MEMLOCK) >> PAGE_SHIFT;

	new_pinned = atomic64_add_return(npages, &mm->pinned_vm);
	if (new_pinned > lock_limit && !capable(CAP_IPC_LOCK)) {
		atomic64_sub(npages, &mm->pinned_vm);
		ret = -ENOMEM;
		goto out;
	}

/* io_uring/rsrc.c:80 */
	if (mm_account)
		atomic64_add(nr_pages, &mm_account->pinned_vm);
```

[`def_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1244) has two writers. [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) inherits the parent's value masked with [`VM_INIT_DEF_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L572) ([`VM_NOHUGEPAGE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L441) alone survives fork), and [`apply_mlockall_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mlock.c#L704) sets or clears [`VM_LOCKED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L420)/[`VM_LOCKONFAULT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L426) so `mlockall(MCL_FUTURE)` reaches mappings created later. [`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866) shows the template consumed, along with the [`may_expand_vm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1335) and [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) admission checks.

```c
/* include/linux/mm.h:571 */
/* This mask defines which mm->def_flags a process can inherit its parent */
#define VM_INIT_DEF_MASK	VM_NOHUGEPAGE

/* mm/mlock.c:710 */
	current->mm->def_flags &= ~VM_LOCKED_MASK;
	if (flags & MCL_FUTURE) {
		current->mm->def_flags |= VM_LOCKED;

		if (flags & MCL_ONFAULT)
			current->mm->def_flags |= VM_LOCKONFAULT;

		if (!(flags & MCL_CURRENT))
			goto out;
	}

/* mm/vma.c:2866 */
int do_brk_flags(struct vma_iterator *vmi, struct vm_area_struct *vma,
		 unsigned long addr, unsigned long len, vm_flags_t vm_flags)
{
	struct mm_struct *mm = current->mm;

	/*
	 * Check against address space limits by the changed size
	 * Note: This happens *after* clearing old mappings in some code paths.
	 */
	vm_flags |= VM_DATA_DEFAULT_FLAGS | VM_ACCOUNT | mm->def_flags;
	vm_flags = ksm_vma_flags(mm, NULL, vm_flags);
	if (!may_expand_vm(mm, vm_flags, len >> PAGE_SHIFT))
		return -ENOMEM;

	if (mm->map_count > sysctl_max_map_count)
		return -ENOMEM;
```

### write_protect_seq lets GUP-fast detect a concurrent fork

[`write_protect_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1251) is a [`seqcount_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/seqlock_types.h#L38) introduced by commit `57efa1fe5957` ("mm/gup: prevent gup_fast from racing with COW during fork"). Its kernel-doc names the writer.

```c
/* include/linux/mm_types.h:1246 */
		/**
		 * @write_protect_seq: Locked when any thread is write
		 * protecting pages mapped by this mm to enforce a later COW,
		 * for instance during page table copying for fork().
		 */
		seqcount_t write_protect_seq;
```

The write side is the fork copy. [`copy_page_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1504) enters the seqcount write section only for COW mappings (the case where parent PTEs are being write-protected), using the raw API because, per the in-function comment, the read side never spins on it; [`copy_hugetlb_page_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/hugetlb.c#L4885) brackets its hugetlb equivalent the same way at [`mm/hugetlb.c:4907`](https://elixir.bootlin.com/linux/v7.0/source/mm/hugetlb.c#L4907).

```c
/* mm/memory.c:1530 */
	if (is_cow) {
		mmu_notifier_range_init(&range, MMU_NOTIFY_PROTECTION_PAGE,
					0, src_mm, addr, end);
		mmu_notifier_invalidate_range_start(&range);
		/*
		 * Disabling preemption is not needed for the write side, as
		 * the read side doesn't spin, but goes to the mmap_lock.
		 *
		 * Use the raw variant of the seqcount_t write API to avoid
		 * lockdep complaining about preemptibility.
		 */
		vma_assert_write_locked(src_vma);
		raw_write_seqcount_begin(&src_mm->write_protect_seq);
	}
	...
/* mm/memory.c:1559 */
	if (is_cow) {
		raw_write_seqcount_end(&src_mm->write_protect_seq);
		mmu_notifier_invalidate_range_end(&range);
	}
```

The read side is [`gup_fast()`](https://elixir.bootlin.com/linux/v7.0/source/mm/gup.c#L3129), which pins pages with only interrupts disabled. For [`FOLL_PIN`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1538) requests it samples the seqcount before the walk and retries through the slow path if a fork's write-protect pass overlapped, unpinning whatever it grabbed; the comment at the recheck states the purpose ("there could be a concurrent write protect from fork() via copy_page_range()"). [`gup_fast_fallback()`](https://elixir.bootlin.com/linux/v7.0/source/mm/gup.c#L3175) is the caller that falls back to [`__gup_longterm_locked()`](https://elixir.bootlin.com/linux/v7.0/source/mm/gup.c#L2465) when the fast path returns short.

```c
/* mm/gup.c:3140 */
	if (gup_flags & FOLL_PIN) {
		if (!raw_seqcount_try_begin(&current->mm->write_protect_seq, seq))
			return 0;
	}
	...
/* mm/gup.c:3160 */
	/*
	 * When pinning pages for DMA there could be a concurrent write protect
	 * from fork() via copy_page_range(), in this case always fail GUP-fast.
	 */
	if (gup_flags & FOLL_PIN) {
		if (read_seqcount_retry(&current->mm->write_protect_seq, seq)) {
			gup_fast_unpin_user_pages(pages, nr_pinned);
			return 0;
		} else {
			sanity_check_pinned_pages(pages, nr_pinned);
		}
	}
	return nr_pinned;
}
```

### flags packs 64 MMF bits behind atomic bitmap accessors

[`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1273) has the opaque type [`mm_flags_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1117), a [`__private`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/compiler_types.h#L60) [`NUM_MM_FLAG_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1116)-bit (64-bit) bitmap that replaced the old bare `unsigned long` in v6.18 (commit `bb6525f2f8c4`, "mm: add bitmap mm->flags field") so the flag space can grow past one machine word.

```c
/* include/linux/mm_types.h:1112 */
/*
 * Opaque type representing current mm_struct flag state. Must be accessed via
 * mm_flags_xxx() helper functions.
 */
#define NUM_MM_FLAG_BITS (64)
typedef struct {
	DECLARE_BITMAP(__mm_flags, NUM_MM_FLAG_BITS);
} __private mm_flags_t;

/* include/linux/mm_types.h:1273 */
		mm_flags_t flags; /* Must use mm_flags_* hlpers to access */
```

The accessors in [`include/linux/mm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L877) wrap the atomic bitop family over the private bitmap, and a parallel `__mm_flags_*` word family in [`include/linux/mm_types.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1384) gives the fork path non-atomic access to the first 64-bit word.

```c
/* include/linux/mm.h:877 */
static inline bool mm_flags_test(int flag, const struct mm_struct *mm)
{
	return test_bit(flag, ACCESS_PRIVATE(&mm->flags, __mm_flags));
}
...
/* include/linux/mm.h:892 */
static inline void mm_flags_set(int flag, struct mm_struct *mm)
{
	set_bit(flag, ACCESS_PRIVATE(&mm->flags, __mm_flags));
}

static inline void mm_flags_clear(int flag, struct mm_struct *mm)
{
	clear_bit(flag, ACCESS_PRIVATE(&mm->flags, __mm_flags));
}

static inline void mm_flags_clear_all(struct mm_struct *mm)
{
	bitmap_zero(ACCESS_PRIVATE(&mm->flags, __mm_flags), NUM_MM_FLAG_BITS);
}
```

The MMF bit indices are defined at the bottom of [`include/linux/mm_types.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1854), and their semantics are out of scope here beyond the layout. Bits 0-1 ([`MMF_DUMPABLE_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1860) = 2) hold the coredump mode, bits 2-10 ([`MMF_DUMP_FILTER_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1874) = 9) hold the coredump filter, and bits 16-31 name per-subsystem states from [`MMF_VM_MERGEABLE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1887) (16, KSM) through [`MMF_TOPDOWN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1919) (31, the mmap search direction set by [`arch_pick_mmap_layout()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L122) above). On fork, [`mmf_init_legacy_flags()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1933) keeps only [`MMF_INIT_LEGACY_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1922) and drops MDWE bits when [`MMF_HAS_MDWE_NO_INHERIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1914) asks for that, as the [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) excerpt above shows; a [`static_assert`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/build_bug.h#L79) pins the legacy set inside 32 bits.

```c
/* include/linux/mm_types.h:1922 */
#define MMF_INIT_LEGACY_MASK	(MMF_DUMPABLE_MASK | MMF_DUMP_FILTER_MASK |\
				 MMF_DISABLE_THP_MASK | MMF_HAS_MDWE_MASK |\
				 MMF_VM_MERGE_ANY_MASK | MMF_TOPDOWN_MASK)

/* Legacy flags must fit within 32 bits. */
static_assert((u64)MMF_INIT_LEGACY_MASK <= (u64)UINT_MAX);

/*
 * Initialise legacy flags according to masks, propagating selected flags on
 * fork. Further flag manipulation can be performed by the caller.
 */
static inline unsigned long mmf_init_legacy_flags(unsigned long flags)
{
	if (flags & (1UL << MMF_HAS_MDWE_NO_INHERIT))
		flags &= ~((1UL << MMF_HAS_MDWE) |
			   (1UL << MMF_HAS_MDWE_NO_INHERIT));
	return flags & MMF_INIT_LEGACY_MASK;
}
```

A reader example is `/proc/[pid]/ksm_stat`, where [`proc_pid_ksm_stat()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L3262) tests [`MMF_VM_MERGE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1916) with [`mm_flags_test()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L877) (excerpt in the KSM section below); the [`arch_pick_mmap_layout()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mmap.c#L122) excerpt above shows [`mm_flags_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L892)/[`mm_flags_clear()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L897) as writers.

### context embeds the x86-64 mm_context_t

[`context`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1271) is the architecture's private extension, typed [`mm_context_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L84) and initialized by [`init_new_context()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L150) from [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) and torn down by [`destroy_context()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L175) from [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718). The x86-64 definition follows with one-line roles per field; the TLB-generation and ASID machinery it drives is out of scope here.

```c
/* include/linux/mm_types.h:1268 */
		struct linux_binfmt *binfmt;

		/* Architecture-specific MM context */
		mm_context_t context;

/* arch/x86/include/asm/mmu.h:22 */
/*
 * x86 has arch-specific MMU state beyond what lives in mm_struct.
 */
typedef struct {
	/*
	 * ctx_id uniquely identifies this mm_struct.  A ctx_id will never
	 * be reused, and zero is not a valid ctx_id.
	 */
	u64 ctx_id;

	/*
	 * Any code that needs to do any sort of TLB flushing for this
	 * mm will first make its changes to the page tables, then
	 * increment tlb_gen, then flush.  This lets the low-level
	 * flushing code keep track of what needs flushing.
	 *
	 * This is not used on Xen PV.
	 */
	atomic64_t tlb_gen;

	unsigned long next_trim_cpumask;

#ifdef CONFIG_MODIFY_LDT_SYSCALL
	struct rw_semaphore	ldt_usr_sem;
	struct ldt_struct	*ldt;
#endif

	unsigned long flags;

#ifdef CONFIG_ADDRESS_MASKING
	/* Active LAM mode:  X86_CR3_LAM_U48 or X86_CR3_LAM_U57 or 0 (disabled) */
	unsigned long lam_cr3_mask;

	/* Significant bits of the virtual address. Excludes tag bits. */
	u64 untag_mask;
#endif

	struct mutex lock;
	void __user *vdso;			/* vdso base address */
	const struct vdso_image *vdso_image;	/* vdso image in use */

	atomic_t perf_rdpmc_allowed;	/* nonzero if rdpmc is allowed */
#ifdef CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS
	/*
	 * One bit per protection key says whether userspace can
	 * use it or not.  protected by mmap_lock.
	 */
	u16 pkey_allocation_map;
	s16 execute_only_pkey;
#endif

#ifdef CONFIG_BROADCAST_TLB_FLUSH
	/*
	 * The global ASID will be a non-zero value when the process has
	 * the same ASID across all CPUs, allowing it to make use of
	 * hardware-assisted remote TLB invalidation like AMD INVLPGB.
	 */
	u16 global_asid;

	/* The process is transitioning to a new global ASID number. */
	bool asid_transition;
#endif
} mm_context_t;
```

In brief, [`ctx_id`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L30) is the never-reused identity the TLB code compares in [`switch_mm_irqs_off()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L783) (visible in the `reload_tlb` excerpt above), [`tlb_gen`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L40) is the flush generation counter read there as [`next->context.tlb_gen`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L40), [`next_trim_cpumask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L42) schedules periodic [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432) trimming, [`ldt_usr_sem`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L45)/[`ldt`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L46) carry `modify_ldt(2)` state, [`flags`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L49) holds the `MM_CONTEXT_*` bits defined at the top of [`arch/x86/include/asm/mmu.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L11) ([`MM_CONTEXT_UPROBE_IA32`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L12) bit 0 through [`MM_CONTEXT_NOTRACK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L20) bit 4), the [`CONFIG_ADDRESS_MASKING`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L2193) pair holds the LAM CR3 mask and untag mask, [`vdso`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L60)/[`vdso_image`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L61) locate the mapped vDSO, [`perf_rdpmc_allowed`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L63) gates user RDPMC, the pkey pair tracks protection-key allocation, and the [`CONFIG_BROADCAST_TLB_FLUSH`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig.cpu#L361) pair manages INVLPGB global ASIDs. [`INIT_MM_CONTEXT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L86) statically seeds `ctx_id = 1` for [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32).

```c
/* arch/x86/include/asm/mmu.h:86 */
#define INIT_MM_CONTEXT(mm)						\
	.context = {							\
		.ctx_id = 1,						\
		.lock = __MUTEX_INITIALIZER(mm.context.lock),		\
	}
```

### owner, user_ns and exe_file hold identity references

Three pointers tie the address space to identities outside mm. [`owner`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1290) ([`CONFIG_MEMCG`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1048)=y) is the task whose memory cgroup charges this mm, with the declaration comment spelling out the four conditions a change must satisfy.

```c
/* include/linux/mm_types.h:1279 */
#ifdef CONFIG_MEMCG
		/*
		 * "owner" points to a task that is regarded as the canonical
		 * user/owner of this mm. All of the following must be true in
		 * order for it to be changed:
		 *
		 * current == mm->owner
		 * current->mm != mm
		 * new_owner->mm == mm
		 * new_owner->alloc_lock is held
		 */
		struct task_struct __rcu *owner;
#endif
		struct user_namespace *user_ns;

		/* store ref to file /proc/<pid>/exe symlink points to */
		struct file __rcu *exe_file;
```

[`mm_init_owner()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1048) points it at the forking task, and [`mm_update_next_owner()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L487), called from [`exit_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L550) (excerpt above), hands ownership to another user of the same mm (children first, then siblings, then a whole-process scan) or leaves NULL when none remains.

```c
/* kernel/exit.c:484 */
/*
 * A task is exiting.   If it owned this mm, find a new owner for the mm.
 */
void mm_update_next_owner(struct mm_struct *mm)
{
	struct task_struct *g, *p = current;

	/*
	 * If the exiting or execing task is not the owner, it's
	 * someone else's problem.
	 */
	if (mm->owner != p)
		return;
	/*
	 * The current owner is exiting/execing and there are no other
	 * candidates.  Do not leave the mm pointing to a possibly
	 * freed task structure.
	 */
	if (atomic_read(&mm->mm_users) <= 1) {
		WRITE_ONCE(mm->owner, NULL);
		return;
	}
```

[`user_ns`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1292) pins the [`struct user_namespace`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/user_namespace.h#L76) that permission checks against this mm (ptrace-style access through `/proc`) evaluate capabilities in; [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) takes the reference with [`get_user_ns()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/user_namespace.h#L176) and [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) drops it, and `execve(2)` may re-point it at a parent namespace in [`would_dump()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L1293) when the executable is unreadable in the current one.

[`exe_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1295) is the RCU-managed file behind the `/proc/[pid]/exe` symlink. [`begin_new_exec()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L1091) installs the new binary with [`set_mm_exe_file()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1234) before the mm becomes visible, [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) clears it at teardown (both call sites in excerpts above), `prctl(PR_SET_MM_EXE_FILE)` swaps it through [`prctl_set_mm_exe_file()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sys.c#L1966), and [`get_mm_exe_file()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1322) is the RCU-safe reader. The setter also arbitrates write access, keeping a deny-write claim on the running binary.

```c
/* kernel/fork.c:1234 */
int set_mm_exe_file(struct mm_struct *mm, struct file *new_exe_file)
{
	struct file *old_exe_file;

	/*
	 * It is safe to dereference the exe_file without RCU as
	 * this function is only called if nobody else can access
	 * this mm -- see comment above for justification.
	 */
	old_exe_file = rcu_dereference_raw(mm->exe_file);

	if (new_exe_file) {
		/*
		 * We expect the caller (i.e., sys_execve) to already denied
		 * write access, so this is unlikely to fail.
		 */
		if (unlikely(exe_file_deny_write_access(new_exe_file)))
			return -EACCES;
		get_file(new_exe_file);
	}
	rcu_assign_pointer(mm->exe_file, new_exe_file);
	if (old_exe_file) {
		exe_file_allow_write_access(old_exe_file);
		fput(old_exe_file);
	}
	return 0;
}

/* fs/exec.c:1130 */
	/*
	 * Must be called _before_ exec_mmap() as bprm->mm is
	 * not visible until then. Doing it here also ensures
	 * we don't race against replace_mm_exe_file().
	 */
	retval = set_mm_exe_file(bprm->mm, bprm->file);
```

### The NUMA-balancing triple paces task_numa_work

With [`CONFIG_NUMA_BALANCING`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L996)=y, three fields carry the automatic-balancing scanner's cursor. Their declaration comments state the roles directly.

```c
/* include/linux/mm_types.h:1302 */
#ifdef CONFIG_NUMA_BALANCING
		/*
		 * numa_next_scan is the next time that PTEs will be remapped
		 * PROT_NONE to trigger NUMA hinting faults; such faults gather
		 * statistics and migrate pages to new nodes if necessary.
		 */
		unsigned long numa_next_scan;

		/* Restart point for scanning and remapping PTEs. */
		unsigned long numa_scan_offset;

		/* numa_scan_seq prevents two threads remapping PTEs. */
		int numa_scan_seq;
#endif
```

The one consumer is [`task_numa_work()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3363), the task-work callback registered per task at [`kernel/sched/fair.c:3645`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3645). It seeds [`numa_next_scan`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1308) with [`sysctl_numa_balancing_scan_delay`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L1521) (1000 ms) on first use, and only one thread of the process wins the [`try_cmpxchg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-instrumented.h#L4873) that moves the deadline forward, so the whole thread group scans at the process rate. [`numa_scan_offset`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1311) is the address where the previous pass stopped and resets to 0 whenever a pass completes and [`numa_scan_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1314) increments (at [`kernel/sched/fair.c:3316`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3316)); tasks compare their private copy of the sequence in [`task_numa_placement()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L2952) at [`kernel/sched/fair.c:2968`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L2968) to notice a completed pass.

```c
/* kernel/sched/fair.c:1520 */
/* Scan @scan_size MB every @scan_period after an initial @scan_delay in ms */
unsigned int sysctl_numa_balancing_scan_delay = 1000;

/* kernel/sched/fair.c:3400 */
	if (!mm->numa_next_scan) {
		mm->numa_next_scan = now +
			msecs_to_jiffies(sysctl_numa_balancing_scan_delay);
	}

	/*
	 * Enforce maximal scan/migration frequency..
	 */
	migrate = mm->numa_next_scan;
	if (time_before(now, migrate))
		return;

	if (p->numa_scan_period == 0) {
		p->numa_scan_period_max = task_scan_max(p);
		p->numa_scan_period = task_scan_start(p);
	}

	next_scan = now + msecs_to_jiffies(p->numa_scan_period);
	if (!try_cmpxchg(&mm->numa_next_scan, &migrate, next_scan))
		return;

/* kernel/sched/fair.c:3316 */
	WRITE_ONCE(p->mm->numa_scan_seq, READ_ONCE(p->mm->numa_scan_seq) + 1);
	p->mm->numa_scan_offset = 0;

/* kernel/sched/fair.c:3645 */
	init_task_work(&p->numa_work, task_numa_work);
```

### tlb_flush_pending orders PTE changes against concurrent flushes

[`tlb_flush_pending`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1321) is an always-present [`atomic_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/types.h#L188) counting operations that have modified PTEs but not yet flushed the TLB. Its declaration comment names the rule the readers depend on.

```c
/* include/linux/mm_types.h:1316 */
		/*
		 * An operation with batched TLB flushing is going on. Anything
		 * that can move process memory needs to flush the TLB when
		 * moving a PROT_NONE mapped page.
		 */
		atomic_t tlb_flush_pending;
```

[`init_tlb_flush_pending()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L453) zeroes it in [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072), [`inc_tlb_flush_pending()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L458) opens the window (its long comment lays out the `inc -> ptl lock -> PTE change -> ptl unlock -> flush -> dec` ordering that makes the increment visible to anyone who saw the PTE change), [`dec_tlb_flush_pending()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L499) closes it after the flush, and [`mm_tlb_flush_pending()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L512)/[`mm_tlb_flush_nested()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L525) are the PTL-protected readers.

```c
/* include/linux/mm_inline.h:453 */
static inline void init_tlb_flush_pending(struct mm_struct *mm)
{
	atomic_set(&mm->tlb_flush_pending, 0);
}

static inline void inc_tlb_flush_pending(struct mm_struct *mm)
{
	atomic_inc(&mm->tlb_flush_pending);
	/*
	 * The only time this value is relevant is when there are indeed pages
	 * to flush. And we'll only flush pages after changing them, which
	 * requires the PTL.
	 *
	 * So the ordering here is:
	 *
	 *	atomic_inc(&mm->tlb_flush_pending);
	 *	spin_lock(&ptl);
	 *	...
	 *	set_pte_at();
	 *	spin_unlock(&ptl);
	 *
	 *				spin_lock(&ptl)
	 *				mm_tlb_flush_pending();
	 *				....
	 *				spin_unlock(&ptl);
	 *
	 *	flush_tlb_range();
	 *	atomic_dec(&mm->tlb_flush_pending);
	 *
	 * Where the increment if constrained by the PTL unlock, it thus
	 * ensures that the increment is visible if the PTE modification is
	 * visible. After all, if there is no PTE modification, nobody cares
	 * about TLB flushes either.
	 *
	 * This very much relies on users (mm_tlb_flush_pending() and
	 * mm_tlb_flush_nested()) only caring about _specific_ PTEs (and
	 * therefore specific PTLs), because with SPLIT_PTE_PTLOCKS and RCpc
	 * locks (PPC) the unlock of one doesn't order against the lock of
	 * another PTL.
	 *
	 * The decrement is ordered by the flush_tlb_range(), such that
	 * mm_tlb_flush_pending() will not return false unless all flushes have
	 * completed.
	 */
}
...
/* include/linux/mm_inline.h:512 */
static inline bool mm_tlb_flush_pending(const struct mm_struct *mm)
{
	/*
	 * Must be called after having acquired the PTL; orders against that
	 * PTLs release and therefore ensures that if we observe the modified
	 * PTE we must also observe the increment from inc_tlb_flush_pending().
	 *
	 * That is, it only guarantees to return true if there is a flush
	 * pending for _this_ PTL.
	 */
	return atomic_read(&mm->tlb_flush_pending);
}
```

The window opener in the mmu_gather path is [`__tlb_gather_mmu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmu_gather.c#L408) (via [`tlb_gather_mmu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmu_gather.c#L443) at [`mm/mmu_gather.c:432`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmu_gather.c#L432)), and a representative reader is the write-fault path, which flushes a PROT_NONE-visible page before reuse when a batched flush is still pending.

```c
/* mm/memory.c:4179 */
		/*
		 * Userfaultfd write-protect can defer flushes. Ensure the TLB
		 * is flushed in this case before copying.
		 */
		if (unlikely(userfaultfd_wp(vmf->vma) &&
			     mm_tlb_flush_pending(vmf->vma->vm_mm)))
			flush_tlb_page(vmf->vma, vmf->address);
```

### tlb_flush_batched tracks reclaim's deferred flushes in two 15-bit generations

[`tlb_flush_batched`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1324) exists behind [`CONFIG_ARCH_WANT_BATCHED_UNMAP_TLB_FLUSH`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L952), which x86 selects at [`arch/x86/Kconfig:142`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L142). Reclaim unmaps pages under the PTL and defers the IPI flush; this field records how far the deferral has gotten so a later mprotect/munmap can flush before trusting the page tables.

```c
/* include/linux/mm_types.h:1322 */
#ifdef CONFIG_ARCH_WANT_BATCHED_UNMAP_TLB_FLUSH
		/* See flush_tlb_batched_pending() */
		atomic_t tlb_flush_batched;
#endif
```

The word packs two generation counters. According to the comment in [`mm/rmap.c`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L732), "Bits 0-14 of mm->tlb_flush_batched record pending generations" and "Bits 16-30 of mm->tlb_flush_batched bit record flushed generations", with [`TLB_FLUSH_BATCH_FLUSHED_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L736) = 16, [`TLB_FLUSH_BATCH_PENDING_MASK`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L737) = `(1 << 15) - 1` = 32767 and the overflow threshold [`TLB_FLUSH_BATCH_PENDING_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L739) = 16383 (half the mask). [`set_tlb_ubc_flush_pending()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L742) advances the pending generation each time [`try_to_unmap_one()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L1978) defers a flush (call site at [`mm/rmap.c:2176`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L2176)), resetting the pair to 1/0 when pending nears the flushed field.

```c
/* mm/rmap.c:732 */
/*
 * Bits 0-14 of mm->tlb_flush_batched record pending generations.
 * Bits 16-30 of mm->tlb_flush_batched bit record flushed generations.
 */
#define TLB_FLUSH_BATCH_FLUSHED_SHIFT	16
#define TLB_FLUSH_BATCH_PENDING_MASK			\
	((1 << (TLB_FLUSH_BATCH_FLUSHED_SHIFT - 1)) - 1)
#define TLB_FLUSH_BATCH_PENDING_LARGE			\
	(TLB_FLUSH_BATCH_PENDING_MASK / 2)

/* mm/rmap.c:759 */
	barrier();
	batch = atomic_read(&mm->tlb_flush_batched);
retry:
	if ((batch & TLB_FLUSH_BATCH_PENDING_MASK) > TLB_FLUSH_BATCH_PENDING_LARGE) {
		/*
		 * Prevent `pending' from catching up with `flushed' because of
		 * overflow.  Reset `pending' and `flushed' to be 1 and 0 if
		 * `pending' becomes large.
		 */
		if (!atomic_try_cmpxchg(&mm->tlb_flush_batched, &batch, 1))
			goto retry;
	} else {
		atomic_inc(&mm->tlb_flush_batched);
	}

/* mm/rmap.c:2175 */
			if (should_defer_flush(mm, flags))
				set_tlb_ubc_flush_pending(mm, pteval, address, end_addr);
			else
				flush_tlb_range(vma, address, end_addr);
```

[`flush_tlb_batched_pending()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L810) is the catch-up side, called under the PTL from paths that are about to rely on the TLB being clean ([`zap_pte_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1895) at [`mm/memory.c:1919`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1919), the mprotect PTE walk at [`mm/mprotect.c:235`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L235)); it flushes the whole mm when the generations differ and advances the flushed field to match.

```c
/* mm/rmap.c:810 */
void flush_tlb_batched_pending(struct mm_struct *mm)
{
	int batch = atomic_read(&mm->tlb_flush_batched);
	int pending = batch & TLB_FLUSH_BATCH_PENDING_MASK;
	int flushed = batch >> TLB_FLUSH_BATCH_FLUSHED_SHIFT;

	if (pending != flushed) {
		flush_tlb_mm(mm);
		/*
		 * If the new TLB flushing is pending during flushing, leave
		 * mm->tlb_flush_batched as is, to avoid losing flushing.
		 */
		atomic_cmpxchg(&mm->tlb_flush_batched, batch,
			       pending | (pending << TLB_FLUSH_BATCH_FLUSHED_SHIFT));
	}
}

/* mm/memory.c:1919 */
	flush_tlb_batched_pending(mm);
```

### uprobes_state caches the per-process XOL area

[`uprobes_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1326) embeds [`struct uprobes_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uprobes.h#L187) (empty without [`CONFIG_UPROBES`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L182)), whose [`xol_area`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uprobes.h#L188) points to the per-mm execute-out-of-line page where uprobes place displaced instructions, plus an x86-64-only hash list of uretprobe trampolines. [`mm_init_uprobes_state()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1055) nulls it from [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072), [`uprobe_clear_state()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/events/uprobes.c#L1820) frees it from [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167), and [`get_xol_area()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/events/uprobes.c#L1796) creates the [`struct xol_area`](https://elixir.bootlin.com/linux/v7.0/source/kernel/events/uprobes.c#L109) on first demand.

```c
/* include/linux/mm_types.h:1326 */
		struct uprobes_state uprobes_state;
#ifdef CONFIG_PREEMPT_RT
		struct rcu_head delayed_drop;
#endif

/* include/linux/uprobes.h:187 */
struct uprobes_state {
	struct xol_area		*xol_area;
#ifdef CONFIG_X86_64
	struct hlist_head	head_tramps;
#endif
};

/* kernel/events/uprobes.c:1796 */
static struct xol_area *get_xol_area(void)
{
	struct mm_struct *mm = current->mm;
	struct xol_area *area;

	if (!mm->uprobes_state.xol_area)
		__create_xol_area(0);

	/* Pairs with xol_add_vma() smp_store_release() */
	area = READ_ONCE(mm->uprobes_state.xol_area); /* ^^^ */
	return area;
}
```

### The KSM counters surface merge statistics in /proc

With [`CONFIG_KSM`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L688)=y, three counters record how same-page merging affects this address space, each with a declaration comment stating what it counts. [`ksm_merging_pages`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1343) counts this process's pages currently merged into KSM stable-tree pages, [`ksm_rmap_items`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1348) counts the rmap items ksmd allocated to track scanned pages (decremented at [`mm/ksm.c:575`](https://elixir.bootlin.com/linux/v7.0/source/mm/ksm.c#L575) when items are freed), and the atomic [`ksm_zero_pages`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1353), read through [`mm_ksm_zero_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ksm.h#L51), counts empty pages that [`use_zero_pages`](https://elixir.bootlin.com/linux/v7.0/source/mm/ksm.c#L3632) mode folded onto the kernel zero page.

```c
/* include/linux/mm_types.h:1338 */
#ifdef CONFIG_KSM
		/*
		 * Represent how many pages of this process are involved in KSM
		 * merging (not including ksm_zero_pages).
		 */
		unsigned long ksm_merging_pages;
		/*
		 * Represent how many pages are checked for ksm merging
		 * including merged and not merged.
		 */
		unsigned long ksm_rmap_items;
		/*
		 * Represent how many empty pages are merged with kernel zero
		 * pages when enabling KSM use_zero_pages.
		 */
		atomic_long_t ksm_zero_pages;
#endif /* CONFIG_KSM */

/* include/linux/ksm.h:51 */
static inline long mm_ksm_zero_pages(struct mm_struct *mm)
{
	return atomic_long_read(&mm->ksm_zero_pages);
}
```

`/proc/[pid]/ksm_stat` prints all three plus the profit estimate, and tests the [`MMF_VM_MERGE_ANY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1916) flag bit from the section above.

```c
/* fs/proc/base.c:3262 */
static int proc_pid_ksm_stat(struct seq_file *m, struct pid_namespace *ns,
				struct pid *pid, struct task_struct *task)
{
	struct mm_struct *mm;
	int ret = 0;

	mm = get_task_mm(task);
	if (mm) {
		seq_printf(m, "ksm_rmap_items %lu\n", mm->ksm_rmap_items);
		seq_printf(m, "ksm_zero_pages %ld\n", mm_ksm_zero_pages(mm));
		seq_printf(m, "ksm_merging_pages %lu\n", mm->ksm_merging_pages);
		seq_printf(m, "ksm_process_profit %ld\n", ksm_process_profit(mm));
		seq_printf(m, "ksm_merge_any: %s\n",
				mm_flags_test(MMF_VM_MERGE_ANY, mm) ? "yes" : "no");
```

### hugetlb_usage counts hugetlb pages outside rss_stat

With [`CONFIG_HUGETLB_PAGE`](https://elixir.bootlin.com/linux/v7.0/source/fs/Kconfig#L272)=y, [`hugetlb_usage`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1331) is an [`atomic_long_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-long.h#L13) counting this mm's mapped hugetlb pages in base-page units, kept separate from [`rss_stat`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1266) because hugetlb memory is reserved and accounted by hstate rather than reclaimable RSS. [`hugetlb_count_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/hugetlb.h#L1030) zeroes it in [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072), [`hugetlb_count_add()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/hugetlb.h#L1035)/[`hugetlb_count_sub()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/hugetlb.h#L1040) move it as hugetlb faults map pages (for example the fault path at [`mm/hugetlb.c:5897`](https://elixir.bootlin.com/linux/v7.0/source/mm/hugetlb.c#L5897) and the fork copy at [`mm/hugetlb.c:5050`](https://elixir.bootlin.com/linux/v7.0/source/mm/hugetlb.c#L5050)), and [`hugetlb_report_usage()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/hugetlb.h#L1028) renders it as `HugetlbPages` in `/proc/[pid]/status`.

```c
/* include/linux/mm_types.h:1330 */
#ifdef CONFIG_HUGETLB_PAGE
		atomic_long_t hugetlb_usage;
#endif

/* include/linux/hugetlb.h:1030 */
static inline void hugetlb_count_init(struct mm_struct *mm)
{
	atomic_long_set(&mm->hugetlb_usage, 0);
}

static inline void hugetlb_count_add(long l, struct mm_struct *mm)
{
	atomic_long_add(l, &mm->hugetlb_usage);
}

/* mm/hugetlb.c:5897 */
	hugetlb_count_add(pages_per_huge_page(h), mm);
```

### lru_gen enrolls the descriptor in MGLRU page-table walks

With [`CONFIG_LRU_GEN_WALKS_MMU`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1395)=y (the MGLRU walk support on x86-64), the anonymous [`lru_gen`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1369) group links the descriptor into a per-memcg FIFO ([`struct lru_gen_mm_list`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1439)) that reclaim's aging walkers iterate, carries a [`bitmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1364) hinting whether the mm ran since a walker last cleared it, and caches the owner's memcg.

```c
/* include/linux/mm_types.h:1355 */
#ifdef CONFIG_LRU_GEN_WALKS_MMU
		struct {
			/* this mm_struct is on lru_gen_mm_list */
			struct list_head list;
			/*
			 * Set when switching to this mm_struct, as a hint of
			 * whether it has been used since the last time per-node
			 * page table walkers cleared the corresponding bits.
			 */
			unsigned long bitmap;
#ifdef CONFIG_MEMCG
			/* points to the memcg of "owner" above */
			struct mem_cgroup *memcg;
#endif
		} lru_gen;
#endif /* CONFIG_LRU_GEN_WALKS_MMU */
```

[`lru_gen_init_mm()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1454) resets the group at the end of [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072), and [`lru_gen_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1463) writes -1 into the bitmap on every switch to the mm (its comment states the reclaim-side meaning).

```c
/* include/linux/mm_types.h:1454 */
static inline void lru_gen_init_mm(struct mm_struct *mm)
{
	INIT_LIST_HEAD(&mm->lru_gen.list);
	mm->lru_gen.bitmap = 0;
#ifdef CONFIG_MEMCG
	mm->lru_gen.memcg = NULL;
#endif
}

static inline void lru_gen_use_mm(struct mm_struct *mm)
{
	/*
	 * When the bitmap is set, page reclaim knows this mm_struct has been
	 * used since the last time it cleared the bitmap. So it might be worth
	 * walking the page tables of this mm_struct to clear the accessed bit.
	 */
	WRITE_ONCE(mm->lru_gen.bitmap, -1);
}
```

[`lru_gen_add_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2903) appends the descriptor to the memcg's FIFO (updating each node's walk tail pointer when the list was drained), [`lru_gen_del_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2930) unlinks it from [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167), and [`lru_gen_migrate_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2970) moves it when the owner changes memcg. Enrollment happens where an mm gains a running user, [`exec_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L837) for exec (paired with [`lru_gen_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1463) directly after) and [`kernel/fork.c:2680`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L2680) for fork.

```c
/* mm/vmscan.c:2903 */
void lru_gen_add_mm(struct mm_struct *mm)
{
	int nid;
	struct mem_cgroup *memcg = get_mem_cgroup_from_mm(mm);
	struct lru_gen_mm_list *mm_list = get_mm_list(memcg);

	VM_WARN_ON_ONCE(!list_empty(&mm->lru_gen.list));
#ifdef CONFIG_MEMCG
	VM_WARN_ON_ONCE(mm->lru_gen.memcg);
	mm->lru_gen.memcg = memcg;
#endif
	spin_lock(&mm_list->lock);

	for_each_node_state(nid, N_MEMORY) {
		struct lruvec *lruvec = get_lruvec(memcg, nid);
		struct lru_gen_mm_state *mm_state = get_mm_state(lruvec);

		/* the first addition since the last iteration */
		if (mm_state->tail == &mm_list->fifo)
			mm_state->tail = &mm->lru_gen.list;
	}

	list_add_tail(&mm->lru_gen.list, &mm_list->fifo);

	spin_unlock(&mm_list->lock);
}

/* fs/exec.c:885 */
	lru_gen_add_mm(mm);
	task_unlock(tsk);
	lru_gen_use_mm(mm);
```

### mm_cid gives rseq compact per-mm concurrency IDs

With [`CONFIG_SCHED_MM_CID`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1179)=y, [`mm_cid`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1174) embeds [`struct mm_mm_cid`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rseq_types.h#L171), the bookkeeping that hands every running thread of the process a concurrency ID in `[0, max_cids)` for [`rseq`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/rseq.h#L102)'s [`mm_cid`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/rseq.h#L182) field (userspace per-CPU data indexed by something denser than CPU number). The struct groups hot read-mostly members (the [`struct mm_cid_pcpu`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rseq_types.h#L149) percpu slots, [`mode`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rseq_types.h#L174), [`max_cids`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rseq_types.h#L175)) apart from the rarely used lock, mutex, work items and the low-frequency counters; the kernel-doc block above it documents each member, including [`users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rseq_types.h#L187), which counts CID-sharing tasks separately from [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) "as that is modified by mmget()/mm_put() by other entities which do not actually share the MM".

```c
/* include/linux/mm_types.h:1173 */
		/* MM CID related storage */
		struct mm_mm_cid mm_cid;

/* include/linux/rseq_types.h:171 */
struct mm_mm_cid {
	/* Hotpath read mostly members */
	struct mm_cid_pcpu	__percpu *pcpu;
	unsigned int		mode;
	unsigned int		max_cids;

	/* Rarely used. Moves @lock and @mutex into the second cacheline */
	struct irq_work		irq_work;
	struct work_struct	work;

	raw_spinlock_t		lock;
	struct mutex		mutex;
	struct hlist_head	user_list;

	/* Low frequency modified */
	unsigned int		nr_cpus_allowed;
	unsigned int		users;
	unsigned int		pcpu_thrs;
	unsigned int		update_deferred;
} ____cacheline_aligned;
```

[`mm_alloc_cid()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1551) (called from [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072)) allocates the percpu slots and delegates to [`mm_init_cid()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L10846), which resets every member and seeds the two flexible-tail masks from the first task's affinity; [`mm_destroy_cid()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1553) frees the percpu slots from [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718).

```c
/* include/linux/mm_types.h:1543 */
static inline int mm_alloc_cid_noprof(struct mm_struct *mm, struct task_struct *p)
{
	mm->mm_cid.pcpu = alloc_percpu_noprof(struct mm_cid_pcpu);
	if (!mm->mm_cid.pcpu)
		return -ENOMEM;
	mm_init_cid(mm, p);
	return 0;
}

/* kernel/sched/core.c:10846 */
void mm_init_cid(struct mm_struct *mm, struct task_struct *p)
{
	mm->mm_cid.max_cids = 0;
	mm->mm_cid.mode = 0;
	mm->mm_cid.nr_cpus_allowed = p->nr_cpus_allowed;
	mm->mm_cid.users = 0;
	mm->mm_cid.pcpu_thrs = 0;
	mm->mm_cid.update_deferred = 0;
	raw_spin_lock_init(&mm->mm_cid.lock);
	mutex_init(&mm->mm_cid.mutex);
	mm->mm_cid.irq_work = IRQ_WORK_INIT_HARD(mm_cid_irq_work);
	INIT_WORK(&mm->mm_cid.work, mm_cid_work_fn);
	INIT_HLIST_HEAD(&mm->mm_cid.user_list);
	cpumask_copy(mm_cpus_allowed(mm), &p->cpus_mask);
	bitmap_zero(mm_cidmask(mm), num_possible_cpus());
}
```

### The futex fields anchor the private hash and its RCU retirement

With [`CONFIG_FUTEX_PRIVATE_HASH`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1815)=y (added for v6.16 by the series around commit `80367ad01d93`, "futex: Add basic infrastructure for local task local hash"), seven fields give each process its own futex hash table instead of the global one, ending the cross-process cache-line contention of shared buckets. [`futex_phash`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1226) is the RCU-visible current [`struct futex_private_hash`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L66), [`futex_phash_new`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1227) stages a pending replacement until waiters drain, [`futex_hash_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1225) serializes resizing, and the [`futex_batches`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1229)/[`futex_rcu`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1230)/[`futex_atomic`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1231)/[`futex_ref`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1232) quartet implements the RCU-based per-CPU reference scheme that retires an old hash.

```c
/* include/linux/mm_types.h:1224 */
#ifdef CONFIG_FUTEX_PRIVATE_HASH
		struct mutex			futex_hash_lock;
		struct futex_private_hash	__rcu *futex_phash;
		struct futex_private_hash	*futex_phash_new;
		/* futex-ref */
		unsigned long			futex_batches;
		struct rcu_head			futex_rcu;
		atomic_long_t			futex_atomic;
		unsigned int			__percpu *futex_ref;
#endif

/* kernel/futex/core.c:66 */
struct futex_private_hash {
	int		state;
	unsigned int	hash_mask;
	struct rcu_head	rcu;
	void		*mm;
	bool		custom;
	struct futex_hash_bucket queues[];
};
```

[`futex_mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1719) is the [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) hook that nulls the pointers and seeds [`futex_batches`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1229) from the RCU state counter, and [`futex_hash_free()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1731), called from [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) (and from the [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) unwind path), releases all three allocations. The retirement machinery also reuses two fields from other groups, taking [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) pins that it drops with [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) at [`kernel/futex/core.c:1605`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1605), and probing [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222) through the speculative helpers shown earlier.

```c
/* kernel/futex/core.c:1719 */
int futex_mm_init(struct mm_struct *mm)
{
	mutex_init(&mm->futex_hash_lock);
	RCU_INIT_POINTER(mm->futex_phash, NULL);
	mm->futex_phash_new = NULL;
	/* futex-ref */
	mm->futex_ref = NULL;
	atomic_long_set(&mm->futex_atomic, 0);
	mm->futex_batches = get_state_synchronize_rcu();
	return 0;
}

void futex_hash_free(struct mm_struct *mm)
{
	struct futex_private_hash *fph;

	free_percpu(mm->futex_ref);
	kvfree(mm->futex_phash_new);
	fph = rcu_dereference_raw(mm->futex_phash);
	if (fph)
		kvfree(fph);
}
```

### iommu_mm binds the address space to a PASID

With [`CONFIG_IOMMU_MM_DATA`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L1416)=y, [`iommu_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1336) points to a [`struct iommu_mm_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/iommu.h#L1138) carrying the process address-space ID (PASID) that shared-virtual-addressing devices attach with, plus the list of SVA domains bound to this mm. [`mm_pasid_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/iommu.h#L1605) nulls the pointer in [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) (its comment explains that a forked child would otherwise inherit the parent's pointer through the [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) [`memcpy`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/string_64.h#L18) and double-free it), the first [`iommu_sva_bind_device()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/iommu/iommu-sva.c#L72) allocates it, and [`mm_pasid_drop()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/iommu/iommu-sva.c#L207) frees it from [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718).

```c
/* include/linux/mm_types.h:1335 */
#ifdef CONFIG_IOMMU_MM_DATA
		struct iommu_mm_data *iommu_mm;
#endif

/* include/linux/iommu.h:1138 */
struct iommu_mm_data {
	u32			pasid;
	struct mm_struct	*mm;
	struct list_head	sva_domains;
	struct list_head	mm_list_elm;
};

/* include/linux/iommu.h:1604 */
#ifdef CONFIG_IOMMU_MM_DATA
static inline void mm_pasid_init(struct mm_struct *mm)
{
	/*
	 * During dup_mm(), a new mm will be memcpy'd from an old one and that makes
	 * the new mm and the old one point to a same iommu_mm instance. When either
	 * one of the two mms gets released, the iommu_mm instance is freed, leaving
	 * the other mm running into a use-after-free/double-free problem. To avoid
	 * the problem, zeroing the iommu_mm pointer of a new mm is needed here.
	 */
	mm->iommu_mm = NULL;
}
```

### async_put_work defers both put paths off the fast path

[`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333) is a [`struct work_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue_types.h#L16) that two release paths initialize on demand (never both at once, since one runs at [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) 0 and the other at [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) 0). [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) queues [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) for callers that hold a user reference in atomic context (the futex retirement above is one), and [`mmdrop_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749) queues [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) from [`free_signal_struct()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L757) because, per its comment, "__mmdrop is not safe to call from softirq context on x86 due to pgd_dtor so postpone it to the async context".

```c
/* include/linux/mm_types.h:1333 */
		struct work_struct async_put_work;

/* kernel/fork.c:1211 */
void mmput_async(struct mm_struct *mm)
{
	if (atomic_dec_and_test(&mm->mm_users)) {
		INIT_WORK(&mm->async_put_work, mmput_async_fn);
		schedule_work(&mm->async_put_work);
	}
}

/* kernel/fork.c:749 */
static void mmdrop_async(struct mm_struct *mm)
{
	if (unlikely(atomic_dec_and_test(&mm->mm_count))) {
		INIT_WORK(&mm->async_put_work, mmdrop_async_fn);
		schedule_work(&mm->async_put_work);
	}
}

/* kernel/fork.c:757 */
static inline void free_signal_struct(struct signal_struct *sig)
{
	taskstats_tgid_free(sig);
	sched_autogroup_exit(sig);
	/*
	 * __mmdrop is not safe to call from softirq context on x86 due to
	 * pgd_dtor so postpone it to the async context
	 */
	if (sig->oom_mm)
		mmdrop_async(sig->oom_mm);
	kmem_cache_free(signal_cachep, sig);
}
```

### mm_id tags folios with a per-mm identifier for mapcount tracking

With [`CONFIG_MM_ID`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L791)=y (64-bit only), [`mm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1372) holds a [`mm_id_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L329) drawn from a global IDA so large folios can record, in [`folio->_mm_id[]`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L462), which one or two address spaces map them (the basis for the per-folio "mapped exclusively" tracking). The type reserves its top bit for folio-side flags, so valid IDs run from [`MM_ID_MIN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L338) (1) to [`MM_ID_MAX`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L346) (`(1U << 31) - 1` on 64-bit, since [`MM_ID_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L344) is one less than the 32-bit type width), with [`MM_ID_DUMMY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L337) (0) reserved for descriptors that never rmap pages, per its comment "We implicitly use the dummy ID for init-mm etc. where we never rmap pages".

```c
/* include/linux/mm_types.h:326 */
#ifdef CONFIG_64BIT
typedef int mm_id_mapcount_t;
#define MM_ID_MAPCOUNT_MAX		INT_MAX
typedef unsigned int mm_id_t;
#else /* !CONFIG_64BIT */
typedef short mm_id_mapcount_t;
#define MM_ID_MAPCOUNT_MAX		SHRT_MAX
typedef unsigned short mm_id_t;
#endif /* CONFIG_64BIT */

/* We implicitly use the dummy ID for init-mm etc. where we never rmap pages. */
#define MM_ID_DUMMY			0
#define MM_ID_MIN			(MM_ID_DUMMY + 1)

/*
 * We leave the highest bit of each MM id unused, so we can store a flag
 * in the highest bit of each folio->_mm_id[].
 */
#define MM_ID_BITS			((sizeof(mm_id_t) * BITS_PER_BYTE) - 1)
#define MM_ID_MASK			((1U << MM_ID_BITS) - 1)
#define MM_ID_MAX			MM_ID_MASK

/* include/linux/mm_types.h:1371 */
#ifdef CONFIG_MM_ID
		mm_id_t mm_id;
#endif /* CONFIG_MM_ID */
	} __randomize_layout;
```

[`mm_alloc_id()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L595) allocates from the IDA in [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) and [`mm_free_id()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L606) returns the ID in [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718), resetting the field to the dummy value first.

```c
/* kernel/fork.c:592 */
#ifdef CONFIG_MM_ID
static DEFINE_IDA(mm_ida);

static inline int mm_alloc_id(struct mm_struct *mm)
{
	int ret;

	ret = ida_alloc_range(&mm_ida, MM_ID_MIN, MM_ID_MAX, GFP_KERNEL);
	if (ret < 0)
		return ret;
	mm->mm_id = ret;
	return 0;
}

static inline void mm_free_id(struct mm_struct *mm)
{
	const mm_id_t id = mm->mm_id;

	mm->mm_id = MM_ID_DUMMY;
	if (id == MM_ID_DUMMY)
		return;
	if (WARN_ON_ONCE(id < MM_ID_MIN || id > MM_ID_MAX))
		return;
	ida_free(&mm_ida, id);
}
```

### Four conditional pointers cover AIO, MMU notifiers, THP deposits and the loader

The remaining fields hold one pointer or lock each. [`ioctx_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1276) and the RCU pointer [`ioctx_table`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1277) ([`CONFIG_AIO`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig#L1870)=y) index the process's in-flight [`struct kioctx_table`](https://elixir.bootlin.com/linux/v7.0/source/fs/aio.c#L80) of `io_setup(2)` contexts; [`mm_init_aio()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1031) initializes the pair and [`exit_aio()`](https://elixir.bootlin.com/linux/v7.0/source/fs/aio.c#L891) drains it from [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167). [`notifier_subscriptions`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1297) ([`CONFIG_MMU_NOTIFIER`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L684)=y) points to the [`struct mmu_notifier_subscriptions`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmu_notifier.c#L39) that fan invalidation events out to secondary MMUs (KVM, SVA); it starts NULL via [`mmu_notifier_subscriptions_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmu_notifier.h#L483) and is destroyed in [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718). [`pmd_huge_pte`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1300) is the THP page-table deposit slot compiled in only when [`CONFIG_TRANSPARENT_HUGEPAGE`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L794)=y and [`CONFIG_SPLIT_PMD_PTLOCKS`](https://elixir.bootlin.com/linux/v7.0/source/mm/Kconfig#L579)=n; SMP x86-64 configurations use split PMD locks, so the deposit rides in each PMD page instead and this field is absent. [`binfmt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1268) points to the [`struct linux_binfmt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/binfmts.h#L89) that loaded the image, with [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) taking the module reference and [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) putting it (both excerpts above).

```c
/* include/linux/mm_types.h:1275 */
#ifdef CONFIG_AIO
		spinlock_t			ioctx_lock;
		struct kioctx_table __rcu	*ioctx_table;
#endif
...
/* include/linux/mm_types.h:1296 */
#ifdef CONFIG_MMU_NOTIFIER
		struct mmu_notifier_subscriptions *notifier_subscriptions;
#endif
#if defined(CONFIG_TRANSPARENT_HUGEPAGE) && !defined(CONFIG_SPLIT_PMD_PTLOCKS)
		pgtable_t pmd_huge_pte; /* protected by page_table_lock */
#endif

/* kernel/fork.c:1031 */
static void mm_init_aio(struct mm_struct *mm)
{
#ifdef CONFIG_AIO
	spin_lock_init(&mm->ioctx_lock);
	mm->ioctx_table = NULL;
#endif
}
```

### init_mm is the statically initialized kernel descriptor

[`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) is the one instance that never passes through [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072); its initializer in [`mm/init-mm.c`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) covers exactly the fields boot code touches before slab exists. It roots the tree with [`MTREE_INIT_EXT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L252) under the same [`MM_MT_FLAGS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1413), points [`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150) at [`swapper_pg_dir`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L27) (the kernel's boot page tables, [`init_top_pgt`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L25) on x86-64), starts [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) at 2 and [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) at 1 so neither release path can ever fire ([`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) even has `BUG_ON(mm == &init_mm)`), anchors the global [`mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198) chain, and seeds `ctx_id = 1` through [`INIT_MM_CONTEXT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu.h#L86) (shown above). The comment above the initializer states why the tail differs from the slab case; per the comment, "Since there is only one init_mm in the entire system, keep it simple and size this cpu_bitmask to NR_CPUS", which is what [`MM_STRUCT_FLEXIBLE_ARRAY_INIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1417) provides.

```c
/* mm/init-mm.c:22 */
/*
 * For dynamically allocated mm_structs, there is a dynamically sized cpumask
 * at the end of the structure, the size of which depends on the maximum CPU
 * number the system can see. That way we allocate only as much memory for
 * mm_cpumask() as needed for the hundreds, or thousands of processes that
 * a system typically runs.
 *
 * Since there is only one init_mm in the entire system, keep it simple
 * and size this cpu_bitmask to NR_CPUS.
 */
struct mm_struct init_mm = {
	.mm_mt		= MTREE_INIT_EXT(mm_mt, MM_MT_FLAGS, init_mm.mmap_lock),
	.pgd		= swapper_pg_dir,
	.mm_users	= ATOMIC_INIT(2),
	.mm_count	= ATOMIC_INIT(1),
	.write_protect_seq = SEQCNT_ZERO(init_mm.write_protect_seq),
	MMAP_LOCK_INITIALIZER(init_mm)
	.page_table_lock =  __SPIN_LOCK_UNLOCKED(init_mm.page_table_lock),
	.arg_lock	=  __SPIN_LOCK_UNLOCKED(init_mm.arg_lock),
	.mmlist		= LIST_HEAD_INIT(init_mm.mmlist),
#ifdef CONFIG_PER_VMA_LOCK
	.vma_writer_wait = __RCUWAIT_INITIALIZER(init_mm.vma_writer_wait),
	.mm_lock_seq	= SEQCNT_ZERO(init_mm.mm_lock_seq),
#endif
	.user_ns	= &init_user_ns,
#ifdef CONFIG_SCHED_MM_CID
	.mm_cid.lock = __RAW_SPIN_LOCK_UNLOCKED(init_mm.mm_cid.lock),
#endif
	.flexible_array	= MM_STRUCT_FLEXIBLE_ARRAY_INIT,
	INIT_MM_CONTEXT(init_mm)
};
```

[`setup_initial_init_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L54) backfills the kernel image's code, data and brk boundaries; x86-64 calls it from [`setup_arch()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/setup.c#L884) with the linker symbols.

```c
/* mm/init-mm.c:54 */
void setup_initial_init_mm(void *start_code, void *end_code,
			   void *end_data, void *brk)
{
	init_mm.start_code = (unsigned long)start_code;
	init_mm.end_code = (unsigned long)end_code;
	init_mm.end_data = (unsigned long)end_data;
	init_mm.brk = (unsigned long)brk;
}

/* arch/x86/kernel/setup.c:968 */
	setup_initial_init_mm(_text, _etext, _edata, (void *)_brk_end);
```

Two other static instances follow the same pattern on x86-64, [`tboot_mm`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/tboot.c#L97) for the Intel TXT shutdown path and [`efi_mm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/firmware/efi/efi.c#L68) for EFI runtime-services calls; both initialize only the tree, [`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150), refcounts, locks and list fields, which is a compact confirmation of the minimum field set a bare descriptor needs. Kernel threads never own any of these; they run with `task_struct->mm == NULL` and borrow whatever [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) or user descriptor is loaded, the [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L959) scheme [`Documentation/mm/active_mm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/active_mm.rst) documents.
