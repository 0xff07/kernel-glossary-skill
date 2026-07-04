# struct vm_area_struct

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`struct vm_area_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L913) (the VMA) is the kernel's record of one contiguous range of a process address space that shares a single set of properties, the half-open interval `[vm_start, vm_end)` together with its permissions, its backing store, and the operations that service its page faults. According to the comment on the type, "A VM area is any part of the process virtual memory space that has a special rule for the page-fault handlers (ie a shared library, the executable area etc)". Every VMA belongs to exactly one address space, reached through its [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) back-pointer to the owning [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123), and that address space stores every one of its VMAs as a slot in the [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) maple tree keyed by the address range. A file-backed VMA names the mapped file in [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) and the file offset in [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974), and it links itself into that file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) interval tree through the [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1041) node; an anonymous VMA has a NULL [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) and instead links to a [`struct anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) through [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) and [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) for reverse mapping. The [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) pointer selects the [`struct vm_operations_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L749) that handles faults for the range, and a NULL [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) is the marker for an anonymous mapping.

Access to a VMA is governed by two locks. The [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) reader-writer semaphore on the owning [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) serializes the whole tree, while the per-VMA [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) reference count (paired with the [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) sequence stamp, both present under `CONFIG_PER_VMA_LOCK`, which x86-64 selects) lets a page fault take a lightweight read lock on a single VMA under RCU without touching the shared semaphore. According to the comment on the type, "Only explicitly marked struct members may be accessed by RCU readers before getting a stable reference", and only [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958), and [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) carry that marking. This page treats allocation and caching, per-VMA-lock mechanics, flag semantics, and tree operations at field level only, as the properties and access rules of the struct members themselves.

```
    struct vm_area_struct: the VMA and its outward pointers
    ────────────────────────────────────────────────────────

    struct mm_struct  (the owner)
    ┌────────────────────────────┐
    │ mm_mt : maple tree of VMAs │
    └─────────────┬──────────────┘
                  │ one slot per VMA, keyed by [vm_start, vm_end)
                  ▼
    struct vm_area_struct
    ┌──────────────────────────────────┐
    │  vm_start .. vm_end     (range)  │
    │  vm_flags / flags       (bitmap) │
    │  vm_page_prot           (PTE)    │
    │  vm_lock_seq  vm_refcnt (locks)  │
    │                                  │
    │  vm_mm ──────────────────────────┼──▶ struct mm_struct  (owner)
    │  vm_ops ─────────────────────────┼──▶ struct vm_operations_struct
    │  anon_vma ───────────────────────┼──▶ struct anon_vma
    │  vm_file ────────────────────────┼──▶ struct file
    │  shared.rb ──────────────────────┼──▶ address_space.i_mmap (rb)
    │  vm_private_data ────────────────┼──▶ driver-owned state
    └──────────────────────────────────┘

    Legend
    ──────
    mm_mt      the VMA occupies one slot; a range lookup returns the
               VMA whose [vm_start, vm_end) interval holds an address
    vm_mm      back-pointer to the owner (RCU readers may read early)
    vm_ops     &vma_dummy_vm_ops after vma_init(); NULL == anonymous
    anon_vma   installed by __anon_vma_prepare() on first anon fault
    vm_file    the mapped file (NULL for anonymous/stack/brk VMAs)
    shared.rb  file VMAs link into file->f_mapping->i_mmap (rb tree)
    lifetime   vm_area_alloc() from vm_area_cachep, vm_area_free()
               after vma_mark_detached() and the last reader's put
```

## SUMMARY

A VMA is allocated from the [`vm_area_cachep`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L12) slab by [`vm_area_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28), which runs [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) to zero the object, set [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), point [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) at the shared [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20), and initialize the [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list. The mapping path fills in the range and file offset with [`vma_set_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620), sets the flag bitmap with [`vm_flags_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L919), and for a file mapping assigns [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) and lets the file's `mmap` or `mmap_prepare` operation install [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971), as [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) does inside [`__mmap_region()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2720); the `mmap_prepare` variant works on a [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880) rather than the VMA itself. The finished VMA is inserted into the owner's [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) with [`vma_iter_store_new()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610) (which marks it attached by setting [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) to 1) and, when file-backed, linked into the file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree with [`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810). A duplicate for `fork` is produced by [`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121), which copies each member through [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41); the type comment warns that this copy list is the reason new members must be added there. The number of VMAs an address space may hold is counted in [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) and bounded by [`sysctl_max_map_count`](https://elixir.bootlin.com/linux/v7.0/source/mm/util.c#L755), whose default [`DEFAULT_MAX_MAP_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L209) is 65530.

The flag bitmap is read through the [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) view and changed only through the [`vm_flags_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L958), [`vm_flags_clear()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L965), and [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987) accessors, which take the per-VMA write lock before writing. Whether a VMA is anonymous is derived from [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) by [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235), and [`vma_set_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230) writes the NULL marker. A page fault reaches a VMA without the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) through [`lock_vma_under_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296), whose core is [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212); it reads [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958), takes a bounded increment on [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030), and re-checks [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), the three members the type comment marks RCU-readable. The [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) pointer is populated lazily by [`__anon_vma_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185) on the first anonymous fault into the range, driven from [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217). A VMA is released by [`remove_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L463), which runs the `close` operation, drops the [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) reference with `fput()`, puts the [`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986), and hands the detached object to [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) for return to the slab.

## SPECIFICATIONS

## LINUX KERNEL

### Core type and embedded state (mm_types.h)

- [`'\<struct vm_area_struct\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L913): one mapped range of an address space; the object this page describes
- [`'\<vm_flags_t\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L691): `unsigned long` type of the read-only [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) view
- [`'\<vma_flags_t\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L867): bitmap type of the writable [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L940) view, accessed only via helpers
- [`'\<freeptr_t\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L697): SLUB freelist pointer overlaid on [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919)/[`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920) as [`vm_freeptr`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L922)
- [`'\<struct vma_numab_state\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L768): NUMA-balancing scan bookkeeping pointed at by [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989)
- [`'\<struct pfnmap_track_ctx\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L805): refcounted PFN-range tracking context pointed at by [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054)
- [`'\<struct anon_vma_name\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L728): refcounted name string pointed at by [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050)
- [`'\<struct vm_userfaultfd_ctx\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L720): the userfaultfd context embedded as [`vm_userfaultfd_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1052)
- [`'\<struct vm_area_desc\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880): the mutable pre-VMA description a `mmap_prepare` hook fills in
- [`'\<struct mmap_action\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L823): follow-up action embedded in [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880)
- [`'\<enum mmap_action_type\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L813): the three action selectors `MMAP_NOTHING`, `MMAP_REMAP_PFN`, `MMAP_IO_REMAP_PFN`

### Referenced types

- [`'\<struct mm_struct\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123): the owning address space reached through [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), holding [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140), [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179), and the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196)
- [`'\<struct vm_operations_struct\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L749): the function pointer struct selected by [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971)
- [`'\<struct anon_vma\>':'include/linux/rmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) / [`'\<struct anon_vma_chain\>':'include/linux/rmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83): the reverse-mapping root and the chain node linking a VMA to it
- [`'\<struct file\>':'include/linux/fs.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1259) / [`'\<struct address_space\>':'include/linux/fs.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L470): the mapped file and its page cache, whose [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree holds the [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1041) node
- [`'\<struct mempolicy\>':'include/linux/mempolicy.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mempolicy.h#L47): the NUMA policy pointed at by [`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986)
- [`'\<pgprot_t\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293): the x86-64 protection-bit type held in [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930)
- [`'\<struct maple_tree\>':'include/linux/maple_tree.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L222): the range-keyed store that [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) is an instance of

### Allocation, init, and free (vma_init.c, mm.h, internal.h)

- [`'\<vma_state_init\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L14): creates the [`vm_area_cachep`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L12) slab with the [`vm_freeptr`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L922) free-pointer offset
- [`'\<vm_area_alloc\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28): allocates one VMA and runs [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909)
- [`'\<vm_area_dup\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121): duplicates a VMA for `fork`, split, and `mremap` through [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41)
- [`'\<vm_area_init_from\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41): member-by-member copy the type comment warns must track new members
- [`'\<vm_area_free\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144): returns a detached VMA to the slab
- [`'\<vma_init\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909): zeroes a VMA and points [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) at [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20)
- [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20): the empty operations struct a fresh non-anonymous VMA points at
- [`'\<vma_close\>':'mm/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L187): runs the `close` operation and re-points [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) at the dummy struct
- [`'\<mmap_file\>':'mm/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L165): calls the file `mmap` operation and installs the dummy struct on error

### Field accessors (mm.h, mm_types.h, internal.h)

- [`'\<vma_set_range\>':'mm/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620): writes [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919), [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920), and [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) together
- [`'\<vm_flags_init\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L919): overwrites the flag bitmap without locking (pre-tree use)
- [`'\<vm_flags_reset\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L932): full overwrite that asserts the write lock is already held
- [`'\<vm_flags_set\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L958) / [`'\<vm_flags_clear\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L965) / [`'\<vm_flags_mod\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987): OR, AND-NOT, and combined flag edits under the per-VMA write lock
- [`'\<vma_flags_overwrite_word\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1070) / [`'\<vma_flags_set_word\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1091) / [`'\<vma_flags_clear_word\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1099): the low-level bitmap writers the accessors call
- [`'\<vma_set_anonymous\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230) / [`'\<vma_is_anonymous\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235): write and read the NULL-[`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) anonymous marker

### Predicates keyed off fields (mm.h, mmap.c)

- [`'\<vma_is_initial_heap\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1244): compares the range against the owner's `start_brk`/`brk`
- [`'\<vma_is_initial_stack\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1254): compares the range against the owner's `start_stack`
- [`'\<vma_is_temporary_stack\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1265): tests the `VM_GROWSDOWN`/`VM_GROWSUP` and `VM_STACK_INCOMPLETE_SETUP` flag bits
- [`'\<vma_is_foreign\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1279): compares [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) against `current->mm`
- [`'\<vma_is_accessible\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1290): tests [`VM_ACCESS_FLAGS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L545) in [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939)
- [`'\<vma_is_shared_maywrite\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1306): tests [`VM_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L405) and [`VM_MAYWRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L407) together
- [`'\<vma_is_special_mapping\>':'mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1489): matches [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) and [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) against a special mapping

### Per-VMA lock state (mmap_lock.h, mmap_lock.c, vma.h)

- [`'\<vma_lock_init\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L150): seeds [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) with `UINT_MAX` and optionally zeroes [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030)
- [`'\<__is_vma_write_locked\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L282): compares [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) with the owner's [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222)
- [`'\<vma_start_write\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L298) / [`'\<__vma_start_write\>':'mm/mmap_lock.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L139): write-lock a VMA by stamping [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) after excluding readers
- [`'\<__vma_start_exclude_readers\>':'mm/mmap_lock.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L105): adds [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765) to [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) and waits out readers
- [`'\<vma_mark_attached\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L443) / [`'\<vma_mark_detached\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L452): drive [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) between 0 (detached) and 1 (attached)
- [`'\<vma_start_read\>':'mm/mmap_lock.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) / [`'\<lock_vma_under_rcu\>':'mm/mmap_lock.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296): take a per-VMA read lock under RCU for the fault path
- [`'\<vma_iter_store_new\>':'mm/vma.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610): marks a VMA attached and stores it into [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140)

### Mapping path and field writers (vma.c, filemap.c, rmap.c, memory.c, ...)

- [`'\<mmap_region\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2818) / [`'\<__mmap_region\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2720): create a mapping, allocating or merging a VMA
- [`'\<__mmap_new_vma\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) / [`'\<__mmap_new_file_vma\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2455): fill a freshly allocated VMA and drive the file `mmap` operation
- [`'\<call_mmap_prepare\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2638) / [`'\<set_vma_user_defined_fields\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2665): the `mmap_prepare` path that copies [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) and [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) onto the VMA
- [`'\<vfs_mmap_prepare\>':'include/linux/fs.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2073): invokes the file's `mmap_prepare` operation on a [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880)
- [`'\<generic_file_mmap\>':'mm/filemap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L3990) / [`'\<generic_file_mmap_prepare\>':'mm/filemap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L4001): filesystem `mmap`/`mmap_prepare` handlers that install the page-cache [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971)
- [`'\<vma_link\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1824) / [`'\<vma_link_file\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810) / [`'\<__vma_link_file\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L227): insert a VMA into [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) and its [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1041) node into the file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree
- [`'\<vma_interval_tree_insert\>':'mm/interval_tree.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/interval_tree.c#L23): the interval-tree primitive keyed on [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974), generated by `INTERVAL_TREE_DEFINE`
- [`'\<__anon_vma_prepare\>':'mm/rmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185): allocate or reuse an [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) and attach it to the VMA
- [`'\<__vmf_anon_prepare\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3723) / [`'\<vmf_anon_prepare\>':'mm/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L500): the fault-side wrapper that upgrades from the per-VMA lock before attaching
- [`'\<do_anonymous_page\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217): the anonymous fault that triggers [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) attachment
- [`'\<vma_set_page_prot\>':'mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L81): recomputes [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) from the current flags
- [`'\<vma_replace_policy\>':'mm/mempolicy.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L1009) / [`'\<vma_dup_policy\>':'mm/mempolicy.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L2802): set and duplicate [`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986)
- [`'\<task_numa_work\>':'kernel/sched/fair.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3363): lazily allocates [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989) during a NUMA scan
- [`'\<swap_update_readahead\>':'mm/swap_state.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/swap_state.c#L440): updates the [`swap_readahead_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L980) window on swap-in
- [`'\<userfaultfd_set_ctx\>':'mm/userfaultfd.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/userfaultfd.c#L1956): writes [`vm_userfaultfd_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1052) under the per-VMA write lock
- [`'\<remap_pfn_range_track\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3058): allocates and installs [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054) for a full-VMA PFN remap
- [`'\<anon_vma_name\>':'mm/madvise.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/madvise.c#L110) / [`'\<replace_anon_vma_name\>':'mm/madvise.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/madvise.c#L117): read and replace [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050)

### Lifecycle drivers (fork, brk, unmap)

- [`'\<dup_mmap\>':'mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732): the `fork` loop that duplicates every VMA into the child
- [`'\<do_brk_flags\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866): extends or creates the anonymous brk VMA
- [`'\<insert_vm_struct\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L3273): inserts a pre-built VMA, seeding an anonymous [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974)
- [`'\<remove_vma\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L463): closes, unreferences, and frees one VMA

### Hard limits and layout markers

- [`VM_REFCNT_EXCLUDE_READERS_BIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L764) / [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765): bit 30 of [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) that excludes new readers, value `1U << 30`
- [`VM_REFCNT_LIMIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L766): the ceiling `VM_REFCNT_EXCLUDE_READERS_FLAG - 1` a reader increment may not cross
- [`NUM_VMA_FLAG_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L866): width of the [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L940) bitmap, `BITS_PER_LONG` (64 on x86-64)
- [`sysctl_max_map_count`](https://elixir.bootlin.com/linux/v7.0/source/mm/util.c#L755): the per-address-space VMA count limit, tunable as `vm.max_map_count`
- [`DEFAULT_MAX_MAP_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L209) / [`MAPCOUNT_ELF_CORE_MARGIN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L208): the default `USHRT_MAX - 5` = 65530 and its ELF-coredump margin of 5

## KERNEL DOCUMENTATION

- [`Documentation/mm/process_addrs.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/process_addrs.rst): the address-space locking model, the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196), and per-VMA locking over the VMA tree
- [`Documentation/core-api/maple_tree.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/core-api/maple_tree.rst): the maple tree that [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) uses to store every VMA by range
- [`Documentation/admin-guide/sysctl/vm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/sysctl/vm.rst): the `vm.max_map_count` sysctl that bounds the per-process VMA count

## OTHER SOURCES

- [mm: start tracking VMAs with maple tree (commit d4af56c5c7c6)](https://lkml.kernel.org/r/20220906194824.2110408-9-Liam.Howlett@oracle.com)
- [mm: add per-VMA lock and helper functions to control it (commit 5e31275cc997)](https://lkml.kernel.org/r/20230227173632.3292573-13-surenb@google.com)
- [mm: replace vm_lock and detached flag with a reference count (commit f35ab95ca0af)](https://lkml.kernel.org/r/20250213224655.1680278-13-surenb@google.com)
- [mm: make vma cache SLAB_TYPESAFE_BY_RCU (commit 3104138517fc)](https://lkml.kernel.org/r/20250213224655.1680278-18-surenb@google.com)
- [mm: add basic VMA flag operation helper functions (commit bae0ba7c7c0a)](https://lkml.kernel.org/r/885d4897d67a6a57c0b07fa182a7055ad752df11.1769097829.git.lorenzo.stoakes@oracle.com)
- [mm/vma: document possible vma->vm_refcnt values and reference comment (commit ef4c0cea1e15)](https://lkml.kernel.org/r/d462e7678c6cc7461f94e5b26c776547d80a67e8.1769198904.git.lorenzo.stoakes@oracle.com)

## DETAILS

### struct vm_area_struct is defined in mm_types.h with config-gated regions

The full definition is a single structure whose members are ordered by how a page fault reaches them, opening with the address range that the maple tree keys on and closing with optional per-feature pointers, the whole thing wrapped in `__randomize_layout`. The first segment covers the tree-walking fields and the flag word:

```c
/* include/linux/mm_types.h:901 */
/*
 * This struct describes a virtual memory area. There is one of these
 * per VM-area/task. A VM area is any part of the process virtual memory
 * space that has a special rule for the page-fault handlers (ie a shared
 * library, the executable area etc).
 *
 * Only explicitly marked struct members may be accessed by RCU readers before
 * getting a stable reference.
 *
 * WARNING: when adding new members, please update vm_area_init_from() to copy
 * them during vm_area_struct content duplication.
 */
struct vm_area_struct {
	/* The first cache line has the info for VMA tree walking. */

	union {
		struct {
			/* VMA covers [vm_start; vm_end) addresses within mm */
			unsigned long vm_start;
			unsigned long vm_end;
		};
		freeptr_t vm_freeptr; /* Pointer used by SLAB_TYPESAFE_BY_RCU */
	};

	/*
	 * The address space we belong to.
	 * Unstable RCU readers are allowed to read this.
	 */
	struct mm_struct *vm_mm;
	pgprot_t vm_page_prot;          /* Access permissions of this VMA. */

	/*
	 * Flags, see mm.h.
	 * To modify use vm_flags_{init|reset|set|clear|mod} functions.
	 * Preferably, use vma_flags_xxx() functions.
	 */
	union {
		/* Temporary while VMA flags are being converted. */
		const vm_flags_t vm_flags;
		vma_flags_t flags;
	};
```

The second segment holds the lock stamp, the reverse-map linkage, the operations pointer, the backing store, and the first block of config-gated members:

```c
/* include/linux/mm_types.h:943 */
#ifdef CONFIG_PER_VMA_LOCK
	/*
	 * Can only be written (using WRITE_ONCE()) while holding both:
	 *  - mmap_lock (in write mode)
	 *  - vm_refcnt bit at VM_REFCNT_EXCLUDE_READERS_FLAG is set
	 * Can be read reliably while holding one of:
	 *  - mmap_lock (in read or write mode)
	 *  - vm_refcnt bit at VM_REFCNT_EXCLUDE_READERS_BIT is set or vm_refcnt > 1
	 * Can be read unreliably (using READ_ONCE()) for pessimistic bailout
	 * while holding nothing (except RCU to keep the VMA struct allocated).
	 *
	 * This sequence counter is explicitly allowed to overflow; sequence
	 * counter reuse can only lead to occasional unnecessary use of the
	 * slowpath.
	 */
	unsigned int vm_lock_seq;
#endif
	/*
	 * A file's MAP_PRIVATE vma can be in both i_mmap tree and anon_vma
	 * list, after a COW of one of the file pages.	A MAP_SHARED vma
	 * can only be in the i_mmap tree.  An anonymous MAP_PRIVATE, stack
	 * or brk vma (with NULL file) can only be in an anon_vma list.
	 */
	struct list_head anon_vma_chain; /* Serialized by mmap_lock &
					  * page_table_lock */
	struct anon_vma *anon_vma;	/* Serialized by page_table_lock */

	/* Function pointers to deal with this struct. */
	const struct vm_operations_struct *vm_ops;

	/* Information about our backing store: */
	unsigned long vm_pgoff;		/* Offset (within vm_file) in PAGE_SIZE
					   units */
	struct file * vm_file;		/* File we map to (can be NULL). */
	void * vm_private_data;		/* was vm_pte (shared mem) */

#ifdef CONFIG_SWAP
	atomic_long_t swap_readahead_info;
#endif
#ifndef CONFIG_MMU
	struct vm_region *vm_region;	/* NOMMU mapping region */
#endif
#ifdef CONFIG_NUMA
	struct mempolicy *vm_policy;	/* NUMA policy for the VMA */
#endif
#ifdef CONFIG_NUMA_BALANCING
	struct vma_numab_state *numab_state;	/* NUMA Balancing state */
#endif
```

The third segment holds the reference count on its own cache line, the file interval-tree node, and the remaining per-feature members:

```c
/* include/linux/mm_types.h:991 */
#ifdef CONFIG_PER_VMA_LOCK
	/*
	 * Used to keep track of firstly, whether the VMA is attached, secondly,
	 * if attached, how many read locks are taken, and thirdly, if the
	 * VM_REFCNT_EXCLUDE_READERS_FLAG is set, whether any read locks held
	 * are currently in the process of being excluded.
	 *
	 * This value can be equal to:
	 *
	 * 0 - Detached. IMPORTANT: when the refcnt is zero, readers cannot
	 * increment it.
	 *
	 * 1 - Attached and either unlocked or write-locked. Write locks are
	 * identified via __is_vma_write_locked() which checks for equality of
	 * vma->vm_lock_seq and mm->mm_lock_seq.
	 *
	 * >1, < VM_REFCNT_EXCLUDE_READERS_FLAG - Read-locked or (unlikely)
	 * write-locked with other threads having temporarily incremented the
	 * reference count prior to determining it is write-locked and
	 * decrementing it again.
	 *
	 * VM_REFCNT_EXCLUDE_READERS_FLAG - Detached, pending
	 * __vma_end_exclude_readers() completion which will decrement the
	 * reference count to zero. IMPORTANT - at this stage no further readers
	 * can increment the reference count. It can only be reduced.
	 *
	 * VM_REFCNT_EXCLUDE_READERS_FLAG + 1 - A thread is either write-locking
	 * an attached VMA and has yet to invoke __vma_end_exclude_readers(),
	 * OR a thread is detaching a VMA and is waiting on a single spurious
	 * reader in order to decrement the reference count. IMPORTANT - as
	 * above, no further readers can increment the reference count.
	 *
	 * > VM_REFCNT_EXCLUDE_READERS_FLAG + 1 - A thread is either
	 * write-locking or detaching a VMA is waiting on readers to
	 * exit. IMPORTANT - as above, no further readers can increment the
	 * reference count.
	 *
	 * NOTE: Unstable RCU readers are allowed to read this.
	 */
	refcount_t vm_refcnt ____cacheline_aligned_in_smp;
#ifdef CONFIG_DEBUG_LOCK_ALLOC
	struct lockdep_map vmlock_dep_map;
#endif
#endif
	/*
	 * For areas with an address space and backing store,
	 * linkage into the address_space->i_mmap interval tree.
	 *
	 */
	struct {
		struct rb_node rb;
		unsigned long rb_subtree_last;
	} shared;
#ifdef CONFIG_ANON_VMA_NAME
	/*
	 * For private and shared anonymous mappings, a pointer to a null
	 * terminated string containing the name given to the vma, or NULL if
	 * unnamed. Serialized by mmap_lock. Use anon_vma_name to access.
	 */
	struct anon_vma_name *anon_name;
#endif
	struct vm_userfaultfd_ctx vm_userfaultfd_ctx;
#ifdef __HAVE_PFNMAP_TRACKING
	struct pfnmap_track_ctx *pfnmap_track_ctx;
#endif
} __randomize_layout;
```

On an x86-64 build with `CONFIG_MMU` and `CONFIG_PER_VMA_LOCK` on, the `#ifndef CONFIG_MMU` member [`vm_region`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L983) is compiled out, and the `CONFIG_PER_VMA_LOCK`, `CONFIG_SWAP`, `CONFIG_NUMA`, `CONFIG_NUMA_BALANCING`, `CONFIG_ANON_VMA_NAME`, and [`__HAVE_PFNMAP_TRACKING`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L528) members are all present ([`__HAVE_PFNMAP_TRACKING`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L528) is defined unconditionally by the x86 headers). The [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) member carries `____cacheline_aligned_in_smp`, so it starts a fresh cache line and the reader-increment path does not contend with the range and flag fields above it, which are read far more than written; the [`vmlock_dep_map`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1032) beside it exists only under `CONFIG_DEBUG_LOCK_ALLOC` and feeds lockdep. The type comment states two rules a reader has to honor. According to the comment "Only explicitly marked struct members may be accessed by RCU readers before getting a stable reference", only the three members annotated in the definition, [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) ("Unstable RCU readers are allowed to read this."), [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) ("Can be read unreliably (using READ_ONCE()) for pessimistic bailout while holding nothing (except RCU to keep the VMA struct allocated)."), and [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) ("NOTE: Unstable RCU readers are allowed to read this."), may be touched by a lockless reader before it has pinned the VMA; every other member requires either the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) or a stable per-VMA reference. According to the comment "WARNING: when adding new members, please update vm_area_init_from() to copy them during vm_area_struct content duplication", the duplication routine [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41) is the maintenance point that pairs with the field list here.

The members group by role, and this catalog names each field, its type, and what it records:

| Field | Type | Role |
|---|---|---|
| [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919) / [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920) (union with [`vm_freeptr`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L922)) | `unsigned long` / `freeptr_t` | the half-open range `[vm_start, vm_end)`; while free in the slab the same bytes hold the SLUB free pointer |
| [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) | `struct mm_struct *` | back-pointer to the owning address space (RCU-readable) |
| [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) | `pgprot_t` | the PTE protection bits applied to pages faulted into the range |
| [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) / [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L940) (union) | `const vm_flags_t` / `vma_flags_t` | the VMA property bitmap ([`VM_READ`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L402), [`VM_WRITE`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L403), [`VM_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L405), ...), read through the const view and written through helpers |
| [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) | `unsigned int` | the owner write-lock generation this VMA was last write-locked at (RCU-readable) |
| [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) | `struct list_head` | list of [`struct anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83) links to every [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) this VMA belongs to |
| [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) | `struct anon_vma *` | the reverse-map root for anonymous pages, attached lazily |
| [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) | `const struct vm_operations_struct *` | the fault/open/close operations; NULL marks an anonymous VMA |
| [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) | `unsigned long` | offset into [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) in `PAGE_SIZE` units (the virtual page offset for an anonymous VMA) |
| [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) | `struct file *` | the mapped file, NULL for anonymous, stack, and brk VMAs |
| [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) | `void *` | per-mapping state owned by the driver or filesystem behind [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) |
| [`swap_readahead_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L980) | `atomic_long_t` | the per-VMA swap readahead window (last fault address, window, hits) |
| [`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986) | `struct mempolicy *` | the NUMA allocation policy for pages in the range |
| [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989) | `struct vma_numab_state *` | NUMA-balancing scan bookkeeping, allocated on first scan |
| [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) | `refcount_t` | attachment state plus per-VMA read-lock count (RCU-readable) |
| [`vmlock_dep_map`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1032) | `struct lockdep_map` | lockdep tracking for the per-VMA lock (`CONFIG_DEBUG_LOCK_ALLOC` only) |
| [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1041) (+ [`rb_subtree_last`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1042)) | `struct rb_node` + `unsigned long` | interval-tree node linking a file VMA into `address_space->i_mmap`, with the augmented subtree bound |
| [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) | `struct anon_vma_name *` | the name assigned to an anonymous mapping, or NULL |
| [`vm_userfaultfd_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1052) | `struct vm_userfaultfd_ctx` | the userfaultfd context registered on the range, if any |
| [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054) | `struct pfnmap_track_ctx *` | refcounted tracking of a PFN-mapped range's cache attributes |

### The vm_start and vm_end union overlaps a slab free pointer

The first member is a union between the address range and a single free-list pointer, whose type is defined a few lines above the struct:

```c
/* include/linux/mm_types.h:916 */
	union {
		struct {
			/* VMA covers [vm_start; vm_end) addresses within mm */
			unsigned long vm_start;
			unsigned long vm_end;
		};
		freeptr_t vm_freeptr; /* Pointer used by SLAB_TYPESAFE_BY_RCU */
	};
...
/* include/linux/mm_types.h:693 */
/*
 * freeptr_t represents a SLUB freelist pointer, which might be encoded
 * and not dereferenceable if CONFIG_SLAB_FREELIST_HARDENED is enabled.
 */
typedef struct { unsigned long v; } freeptr_t;
```

While the VMA is live, [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919) and [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920) are the inclusive start and exclusive end of the mapped range, and the whole VMA occupies the maple-tree slot spanning exactly `[vm_start, vm_end)`. When the VMA is freed back to its slab, the same bytes are reused by SLUB as the free-list pointer [`vm_freeptr`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L922) of type [`freeptr_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L697). This overlap is possible because [`vma_state_init()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L14) creates the slab with the free-pointer offset pinned to this union, so a freed object stores its free pointer where a live object stores its range:

```c
/* mm/vma_init.c:11 */
/* SLAB cache for vm_area_struct structures */
static struct kmem_cache *vm_area_cachep;

void __init vma_state_init(void)
{
	struct kmem_cache_args args = {
		.use_freeptr_offset = true,
		.freeptr_offset = offsetof(struct vm_area_struct, vm_freeptr),
		.sheaf_capacity = 32,
	};

	vm_area_cachep = kmem_cache_create("vm_area_struct",
			sizeof(struct vm_area_struct), &args,
			SLAB_HWCACHE_ALIGN|SLAB_PANIC|SLAB_TYPESAFE_BY_RCU|
			SLAB_ACCOUNT);
}
```

[`vma_state_init()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L14) is called once at boot from [`mmap_init()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1568), right after the sysctl table for `vm.max_map_count` is registered:

```c
/* mm/mmap.c:1568 */
void __init mmap_init(void)
{
	int ret;

	ret = percpu_counter_init(&vm_committed_as, 0, GFP_KERNEL);
	VM_BUG_ON(ret);
#ifdef CONFIG_SYSCTL
	register_sysctl_init("vm", mmap_table);
#endif
	vma_state_init();
}
```

The `SLAB_TYPESAFE_BY_RCU` flag on this cache keeps lockless VMA lookup sound. A freed VMA object can be handed out again immediately, but the memory itself is not returned to the page allocator until an RCU grace period passes, so a reader that found a VMA under `rcu_read_lock()` can safely read the RCU-marked fields even if the VMA was concurrently freed and recycled, and then detects the recycle through the [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) and [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) re-checks in [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212). The `.sheaf_capacity = 32` argument gives each CPU a 32-object sheaf of ready VMAs in front of the shared slab, and `SLAB_ACCOUNT` charges every allocation to the memory cgroup of the mapping process.

### vm_mm points back at the owning address space

Every VMA belongs to one address space, named by the back-pointer that the type comment marks RCU-readable:

```c
/* include/linux/mm_types.h:925 */
	/*
	 * The address space we belong to.
	 * Unstable RCU readers are allowed to read this.
	 */
	struct mm_struct *vm_mm;
	pgprot_t vm_page_prot;          /* Access permissions of this VMA. */
```

The owning [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) carries the state a VMA's users reach through this pointer, the [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) tree, the [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) running count of VMAs, the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196), the [`vma_writer_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1204) rcuwait a write-locker sleeps on, and the [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222) generation counter that [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) is compared against:

```c
/* include/linux/mm_types.h:1123 */
struct mm_struct {
	struct {
		...
/* include/linux/mm_types.h:1140 */
		struct maple_tree mm_mt;
		...
/* include/linux/mm_types.h:1179 */
		int map_count;			/* number of VMAs */
		...
/* include/linux/mm_types.h:1196 */
		struct rw_semaphore mmap_lock;
		...
/* include/linux/mm_types.h:1203 */
#ifdef CONFIG_PER_VMA_LOCK
		struct rcuwait vma_writer_wait;
		...
/* include/linux/mm_types.h:1222 */
		seqcount_t mm_lock_seq;
#endif
```

[`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) is written in two places. [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) sets it when a fresh VMA is allocated, and the `fork` path overwrites it, because [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41) copies the parent's pointer and [`dup_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732) then redirects the clone at the child address space before attaching it:

```c
/* mm/mmap.c:1787 */
		tmp = vm_area_dup(mpnt);
		if (!tmp)
			goto fail_nomem;
		retval = vma_dup_policy(mpnt, tmp);
		if (retval)
			goto fail_nomem_policy;
		tmp->vm_mm = mm;
```

Fault, unmap, and reverse-map code all reach the owning [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) through this field for the page-table root, the resident-set counters, and the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). Because it is RCU-readable, [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) re-reads it after taking a reference and bails out if `vma->vm_mm != mm`, which is how the fault path detects a VMA that was freed and recycled onto a different address space under it.

### vm_page_prot caches the page-table protection bits for the range

[`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) holds the [`pgprot_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293) protection bits (the `_PAGE_*` flags on x86-64) that the fault handlers stamp into every PTE they create for pages in this range. On x86-64 the type is a one-member wrapper around the raw PTE flag word:

```c
/* arch/x86/include/asm/pgtable_types.h:293 */
typedef struct pgprot { pgprotval_t pgprot; } pgprot_t;
```

The field is a cache derived from the VMA flags, recomputed by [`vma_set_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L81) whenever the flags change so that the fault path can install a PTE without re-deriving the protection each time:

```c
/* mm/mmap.c:80 */
/* Update vma->vm_page_prot to reflect vma->vm_flags. */
void vma_set_page_prot(struct vm_area_struct *vma)
{
	vm_flags_t vm_flags = vma->vm_flags;
	pgprot_t vm_page_prot;

	vm_page_prot = vm_pgprot_modify(vma->vm_page_prot, vm_flags);
	if (vma_wants_writenotify(vma, vm_page_prot)) {
		vm_flags &= ~VM_SHARED;
		vm_page_prot = vm_pgprot_modify(vm_page_prot, vm_flags);
	}
	/* remove_protection_ptes reads vma->vm_page_prot without mmap_lock */
	WRITE_ONCE(vma->vm_page_prot, vm_page_prot);
}
```

According to the comment "remove_protection_ptes reads vma->vm_page_prot without mmap_lock", the write is a `WRITE_ONCE()` because a reader can observe [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) without the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). When [`vma_wants_writenotify()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2085) reports that the VMA needs write-notification (for dirty tracking on a shared writable file mapping), the shared bit is dropped from the cached protection so that the first write faults and takes the `page_mkwrite` path. Two of its callers show when the recompute happens. [`__mmap_complete()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2580) runs it as the final step of every new mapping, and [`userfaultfd_set_vm_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/userfaultfd.c#L1941) reruns it whenever the `VM_UFFD_WP` bit changes on a shared mapping:

```c
/* mm/vma.c:2610 */
	if (pgtable_supports_soft_dirty())
		vm_flags_set(vma, VM_SOFTDIRTY);

	vma_set_page_prot(vma);
...
/* mm/userfaultfd.c:1941 */
static void userfaultfd_set_vm_flags(struct vm_area_struct *vma,
				     vm_flags_t vm_flags)
{
	const bool uffd_wp_changed = (vma->vm_flags ^ vm_flags) & VM_UFFD_WP;

	vm_flags_reset(vma, vm_flags);
	/*
	 * For shared mappings, we want to enable writenotify while
	 * userfaultfd-wp is enabled (see vma_wants_writenotify()). We'll simply
	 * recalculate vma->vm_page_prot whenever userfaultfd-wp changes.
	 */
	if ((vma->vm_flags & VM_SHARED) && uffd_wp_changed)
		vma_set_page_prot(vma);
}
```

### The vm_flags union holds the VMA flag bitmap

The flag word is presented as a union of a read-only scalar view and a writable bitmap view:

```c
/* include/linux/mm_types.h:932 */
	/*
	 * Flags, see mm.h.
	 * To modify use vm_flags_{init|reset|set|clear|mod} functions.
	 * Preferably, use vma_flags_xxx() functions.
	 */
	union {
		/* Temporary while VMA flags are being converted. */
		const vm_flags_t vm_flags;
		vma_flags_t flags;
	};
```

Reading `vma->vm_flags` yields a `const` [`vm_flags_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L691) (an `unsigned long`), so code can test bits like `vma->vm_flags & VM_WRITE` directly but cannot assign to the field. Writes go through the accessor family named in the comment, which operate on the [`vma_flags_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L867) bitmap view. Both types are declared just above the struct, and the bitmap is [`NUM_VMA_FLAG_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L866) wide, `BITS_PER_LONG` = 64 on x86-64:

```c
/* include/linux/mm_types.h:691 */
typedef unsigned long vm_flags_t;
...
/* include/linux/mm_types.h:862 */
/*
 * Opaque type representing current VMA (vm_area_struct) flag state. Must be
 * accessed via vma_flags_xxx() helper functions.
 */
#define NUM_VMA_FLAG_BITS BITS_PER_LONG
typedef struct {
	DECLARE_BITMAP(__vma_flags, NUM_VMA_FLAG_BITS);
} vma_flags_t;
```

The `const` qualifier on [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) is what forces every writer to route through [`vm_flags_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L958) and its siblings, which take the per-VMA write lock before touching the bitmap. According to the comment "Temporary while VMA flags are being converted", the two-view union is an in-progress migration from a plain `unsigned long` to the opaque bitmap type.

### The vm_flags accessors mediate every flag change

Because [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) is `const`, the flag bitmap is edited only through the accessor family. The unlocked initializer is used before the VMA is visible in the tree:

```c
/* include/linux/mm.h:918 */
/* Use when VMA is not part of the VMA tree and needs no locking */
static inline void vm_flags_init(struct vm_area_struct *vma,
				 vm_flags_t flags)
{
	VM_WARN_ON_ONCE(!pgtable_supports_soft_dirty() && (flags & VM_SOFTDIRTY));
	vma_flags_clear_all(&vma->flags);
	vma_flags_overwrite_word(&vma->flags, flags);
}
```

According to the comment, [`vm_flags_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L919) is for a VMA that "is not part of the VMA tree and needs no locking", which is exactly how [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) uses it on a freshly allocated, still-unpublished VMA:

```c
/* mm/vma.c:2521 */
	vma_iter_config(vmi, map->addr, map->end);
	vma_set_range(vma, map->addr, map->end, map->pgoff);
	vm_flags_init(vma, map->vm_flags);
	vma->vm_page_prot = map->page_prot;
```

Once a VMA is published, edits must take the per-VMA write lock, and the set/clear pair does exactly that before delegating to the word-level writers:

```c
/* include/linux/mm.h:958 */
static inline void vm_flags_set(struct vm_area_struct *vma,
				vm_flags_t flags)
{
	vma_start_write(vma);
	vma_flags_set_word(&vma->flags, flags);
}

static inline void vm_flags_clear(struct vm_area_struct *vma,
				  vm_flags_t flags)
{
	VM_WARN_ON_ONCE(!pgtable_supports_soft_dirty() && (flags & VM_SOFTDIRTY));
	vma_start_write(vma);
	vma_flags_clear_word(&vma->flags, flags);
}
```

[`__mmap_complete()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2580) exercises both sides on a just-inserted mapping, clearing the mlock bits from mappings that must not stay locked and setting [`VM_SOFTDIRTY`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L435) on the new range:

```c
/* mm/vma.c:2590 */
	vm_stat_account(mm, vma->vm_flags, map->pglen);
	if (vm_flags & VM_LOCKED) {
		if ((vm_flags & VM_SPECIAL) || vma_is_dax(vma) ||
					is_vm_hugetlb_page(vma) ||
					vma == get_gate_vma(mm))
			vm_flags_clear(vma, VM_LOCKED_MASK);
		else
			mm->locked_vm += map->pglen;
	}
...
/* mm/vma.c:2610 */
	if (pgtable_supports_soft_dirty())
		vm_flags_set(vma, VM_SOFTDIRTY);
```

The full-overwrite form [`vm_flags_reset()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L932) asserts that the caller already holds the write lock instead of taking it, which fits callers like [`userfaultfd_set_vm_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/userfaultfd.c#L1941) (shown above) that locked the VMA earlier in the same operation:

```c
/* include/linux/mm.h:932 */
static inline void vm_flags_reset(struct vm_area_struct *vma,
				  vm_flags_t flags)
{
	VM_WARN_ON_ONCE(!pgtable_supports_soft_dirty() && (flags & VM_SOFTDIRTY));
	vma_assert_write_locked(vma);
	vm_flags_init(vma, flags);
}
```

The combined form [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987) applies a set and a clear in one locked section:

```c
/* include/linux/mm.h:983 */
/*
 * Use only when the order of set/clear operations is unimportant, otherwise
 * use vm_flags_{set|clear} explicitly.
 */
static inline void vm_flags_mod(struct vm_area_struct *vma,
				vm_flags_t set, vm_flags_t clear)
{
	vma_start_write(vma);
	__vm_flags_mod(vma, set, clear);
}
```

[`mmap_vmcore()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/vmcore.c#L591), the `mmap` handler of `/proc/vmcore`, uses it to mark its mapping [`VM_MIXEDMAP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L439) while stripping the may-write and may-exec bits in one call:

```c
/* fs/proc/vmcore.c:606 */
	vm_flags_mod(vma, VM_MIXEDMAP, VM_MAYWRITE | VM_MAYEXEC);
```

All of these delegate to the low-level bitmap writers defined next to the type, which operate on the first system word of the bitmap:

```c
/* include/linux/mm_types.h:1064 */
/*
 * Copy value to the first system word of VMA flags, non-atomically.
 *
 * IMPORTANT: This does not overwrite bytes past the first system word. The
 * caller must account for this.
 */
static inline void vma_flags_overwrite_word(vma_flags_t *flags, unsigned long value)
{
	unsigned long *bitmap = flags->__vma_flags;

	bitmap[0] = value;
}
...
/* include/linux/mm_types.h:1090 */
/* Update the first system word of VMA flags setting bits, non-atomically. */
static inline void vma_flags_set_word(vma_flags_t *flags, unsigned long value)
{
	unsigned long *bitmap = flags->__vma_flags;

	*bitmap |= value;
}

/* Update the first system word of VMA flags clearing bits, non-atomically. */
static inline void vma_flags_clear_word(vma_flags_t *flags, unsigned long value)
{
	unsigned long *bitmap = flags->__vma_flags;

	*bitmap &= ~value;
}
```

A grep across `mm/`, `fs/`, `kernel/`, `drivers/`, `arch/x86/`, and `include/` at this tree finds 119 call sites of [`vm_flags_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L958), [`vm_flags_clear()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L965), and [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987) outside their definitions, so the locked accessor family is the single choke point for post-publication flag edits.

### vm_lock_seq stamps the VMA with the mm write-lock generation

The per-VMA lock is built from a sequence stamp and a reference count. The stamp records the owner's write-lock generation at which this VMA was last write-locked, and its access rules are spelled out in the field comment reproduced in the struct above. The value is compared against the owner's [`mm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1222); a VMA is considered write-locked exactly when its [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) equals the current generation, which is why write-locking a VMA is a single stamp assignment and why a bump of the owner's sequence at [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) write-unlock instantly marks every VMA unlocked at once. [`vma_lock_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L150) seeds the stamp with `UINT_MAX` so a fresh VMA never accidentally equals a live generation, and [`__is_vma_write_locked()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L282) performs the comparison:

```c
/* include/linux/mmap_lock.h:150 */
static inline void vma_lock_init(struct vm_area_struct *vma, bool reset_refcnt)
{
#ifdef CONFIG_DEBUG_LOCK_ALLOC
	static struct lock_class_key lockdep_key;

	lockdep_init_map(__vma_lockdep_map(vma), "vm_lock", &lockdep_key, 0);
#endif
	if (reset_refcnt)
		refcount_set(&vma->vm_refcnt, 0);
	vma->vm_lock_seq = UINT_MAX;
}
...
/* include/linux/mmap_lock.h:276 */
/*
 * Determine whether a VMA is write-locked. Must be invoked ONLY if the mmap
 * write lock is held.
 *
 * Returns true if write-locked, otherwise false.
 */
static inline bool __is_vma_write_locked(struct vm_area_struct *vma)
{
	/*
	 * current task is holding mmap_write_lock, both vma->vm_lock_seq and
	 * mm->mm_lock_seq can't be concurrently modified.
	 */
	return vma->vm_lock_seq == __vma_raw_mm_seqnum(vma);
}
```

Every field writer shown on this page calls [`vma_start_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L298) first. It short-circuits when the VMA already carries the current stamp and otherwise delegates to [`__vma_start_write()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L139), which excludes readers, writes the stamp with `WRITE_ONCE()`, and releases the exclusion:

```c
/* include/linux/mmap_lock.h:293 */
/*
 * Begin writing to a VMA.
 * Exclude concurrent readers under the per-VMA lock until the currently
 * write-locked mmap_lock is dropped or downgraded.
 */
static inline void vma_start_write(struct vm_area_struct *vma)
{
	if (__is_vma_write_locked(vma))
		return;

	__vma_start_write(vma, TASK_UNINTERRUPTIBLE);
}
...
/* mm/mmap_lock.c:139 */
int __vma_start_write(struct vm_area_struct *vma, int state)
{
	const unsigned int mm_lock_seq = __vma_raw_mm_seqnum(vma);
	struct vma_exclude_readers_state ves = {
		.vma = vma,
		.state = state,
	};
	int err;

	err = __vma_start_exclude_readers(&ves);
	if (err) {
		WARN_ON_ONCE(ves.detached);
		return err;
	}

	/*
	 * We should use WRITE_ONCE() here because we can have concurrent reads
	 * from the early lockless pessimistic check in vma_start_read().
	 * We don't really care about the correctness of that early check, but
	 * we should use WRITE_ONCE() for cleanliness and to keep KCSAN happy.
	 */
	WRITE_ONCE(vma->vm_lock_seq, mm_lock_seq);

	if (ves.exclusive) {
		__vma_end_exclude_readers(&ves);
		/* VMA should remain attached. */
		WARN_ON_ONCE(ves.detached);
	}

	return 0;
}
```

According to the field comment, the counter "is explicitly allowed to overflow; sequence counter reuse can only lead to occasional unnecessary use of the slowpath", so the design tolerates wraparound by paying an occasional false-locked result that only costs a fault-path retry. A lockless reader is allowed to read this field, but only with `READ_ONCE()` and only as a pessimistic early check.

### vm_refcnt encodes attach state and the per-VMA read-lock count

The companion reference count is the second half of the per-VMA lock, and its long comment (reproduced in the struct above) enumerates the exact values it can hold. A value of 0 means the VMA is detached and no reader may increment it. A value of 1 means the VMA is attached and either unlocked or write-locked (the two are distinguished by the [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) comparison). Values above 1 but below [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765) count concurrent read locks. The exclude-readers flag and the values at and above it are transient states used while a writer or a detacher is draining existing readers. Those thresholds are defined just above the helper structs:

```c
/* include/linux/mm_types.h:755 */
/*
 * While __vma_enter_locked() is working to ensure are no read-locks held on a
 * VMA (either while acquiring a VMA write lock or marking a VMA detached) we
 * set the VM_REFCNT_EXCLUDE_READERS_FLAG in vma->vm_refcnt to indiciate to
 * vma_start_read() that the reference count should be left alone.
 *
 * See the comment describing vm_refcnt in vm_area_struct for details as to
 * which values the VMA reference count can be.
 */
#define VM_REFCNT_EXCLUDE_READERS_BIT	(30)
#define VM_REFCNT_EXCLUDE_READERS_FLAG	(1U << VM_REFCNT_EXCLUDE_READERS_BIT)
#define VM_REFCNT_LIMIT			(VM_REFCNT_EXCLUDE_READERS_FLAG - 1)
```

[`VM_REFCNT_EXCLUDE_READERS_BIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L764) is bit 30, so [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765) is `1U << 30` and [`VM_REFCNT_LIMIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L766) is that value minus one, so a reader's bounded increment fails as soon as a writer has pushed the count to or above the flag. [`__vma_start_exclude_readers()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L105) is the writer-side user of the flag; it adds the flag to the count and then sleeps on the owner's [`vma_writer_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1204) until the last reader's put brings the count back to the target:

```c
/* mm/mmap_lock.c:105 */
static int __vma_start_exclude_readers(struct vma_exclude_readers_state *ves)
{
	struct vm_area_struct *vma = ves->vma;
	unsigned int tgt_refcnt = get_target_refcnt(ves);
	int err = 0;

	mmap_assert_write_locked(vma->vm_mm);

	/*
	 * If vma is detached then only vma_mark_attached() can raise the
	 * vm_refcnt. mmap_write_lock prevents racing with vma_mark_attached().
	 *
	 * See the comment describing the vm_area_struct->vm_refcnt field for
	 * details of possible refcnt values.
	 */
	if (!refcount_add_not_zero(VM_REFCNT_EXCLUDE_READERS_FLAG, &vma->vm_refcnt)) {
		ves->detached = true;
		return 0;
	}

	__vma_lockdep_acquire_exclusive(vma);
	err = rcuwait_wait_event(&vma->vm_mm->vma_writer_wait,
		   refcount_read(&vma->vm_refcnt) == tgt_refcnt,
		   ves->state);
	if (err) {
		__vma_end_exclude_readers(ves);
		return err;
	}

	__vma_lockdep_stat_mark_acquired(vma);
	ves->exclusive = true;
	return 0;
}
```

The attach and detach transitions are single refcount edges. [`vma_mark_attached()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L443) releases the count from 0 to 1, and [`vma_mark_detached()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L452) drops it back, waiting out any spurious reader that raced in:

```c
/* include/linux/mmap_lock.h:443 */
static inline void vma_mark_attached(struct vm_area_struct *vma)
{
	vma_assert_write_locked(vma);
	vma_assert_detached(vma);
	refcount_set_release(&vma->vm_refcnt, 1);
}

void __vma_exclude_readers_for_detach(struct vm_area_struct *vma);

static inline void vma_mark_detached(struct vm_area_struct *vma)
{
	vma_assert_write_locked(vma);
	vma_assert_attached(vma);

	/*
	 * The VMA still being attached (refcnt > 0) - is unlikely, because the
	 * vma has been already write-locked and readers can increment vm_refcnt
	 * only temporarily before they check vm_lock_seq, realize the vma is
	 * locked and drop back the vm_refcnt. That is a narrow window for
	 * observing a raised vm_refcnt.
	 *
	 * See the comment describing the vm_area_struct->vm_refcnt field for
	 * details of possible refcnt values.
	 */
	if (likely(!__vma_refcount_put_return(vma)))
		return;
```

[`vma_mark_attached()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L443) is invoked from exactly one place, the tree-store helper [`vma_iter_store_new()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610), so a VMA becomes reader-visible in the same operation that publishes it into [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140):

```c
/* mm/vma.h:610 */
static inline void vma_iter_store_new(struct vma_iterator *vmi,
				      struct vm_area_struct *vma)
{
	vma_mark_attached(vma);
	vma_iter_store_overwrite(vmi, vma);
}
```

[`vma_mark_detached()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L452) runs on the removal side, from [`vma_complete()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L335) when a merge absorbs a neighbor, from [`vms_gather_munmap_vmas()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1379) when `munmap` isolates a range, and from the `exit_mmap` teardown loop in [`tear_down_vmas()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1252), which also shows the [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) consistency check:

```c
/* mm/mmap.c:1252 */
unsigned long tear_down_vmas(struct mm_struct *mm, struct vma_iterator *vmi,
		struct vm_area_struct *vma, unsigned long end)
{
	unsigned long nr_accounted = 0;
	int count = 0;

	mmap_assert_write_locked(mm);
	vma_iter_set(vmi, vma->vm_end);
	do {
		if (vma->vm_flags & VM_ACCOUNT)
			nr_accounted += vma_pages(vma);
		vma_mark_detached(vma);
		remove_vma(vma);
		count++;
		cond_resched();
		vma = vma_next(vmi);
	} while (vma && vma->vm_end <= end);

	VM_WARN_ON_ONCE(count != mm->map_count);
```

### vma_start_read pins one VMA under RCU for the fault path

The point of the per-VMA lock fields is to let a page fault proceed without the address-space-wide [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). The read-side core is [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212), and every field it touches before the reference is stable is one of the three RCU-marked members:

```c
/* mm/mmap_lock.c:200 */
/*
 * Try to read-lock a vma. The function is allowed to occasionally yield false
 * locked result to avoid performance overhead, in which case we fall back to
 * using mmap_lock. The function should never yield false unlocked result.
 * False locked result is possible if mm_lock_seq overflows or if vma gets
 * reused and attached to a different mm before we lock it.
 * Returns the vma on success, NULL on failure to lock and EAGAIN if vma got
 * detached.
 *
 * IMPORTANT: RCU lock must be held upon entering the function, but upon error
 *            IT IS RELEASED. The caller must handle this correctly.
 */
static inline struct vm_area_struct *vma_start_read(struct mm_struct *mm,
						    struct vm_area_struct *vma)
{
	struct mm_struct *other_mm;
	int oldcnt;

	RCU_LOCKDEP_WARN(!rcu_read_lock_held(), "no rcu lock held");
	/*
	 * Check before locking. A race might cause false locked result.
	 * We can use READ_ONCE() for the mm_lock_seq here, and don't need
	 * ACQUIRE semantics, because this is just a lockless check whose result
	 * we don't rely on for anything - the mm_lock_seq read against which we
	 * need ordering is below.
	 */
	if (READ_ONCE(vma->vm_lock_seq) == READ_ONCE(mm->mm_lock_seq.sequence)) {
		vma = NULL;
		goto err;
	}

	/*
	 * If VM_REFCNT_EXCLUDE_READERS_FLAG is set,
	 * __refcount_inc_not_zero_limited_acquire() will fail because
	 * VM_REFCNT_LIMIT is less than VM_REFCNT_EXCLUDE_READERS_FLAG.
	 *
	 * Acquire fence is required here to avoid reordering against later
	 * vm_lock_seq check and checks inside lock_vma_under_rcu().
	 */
	if (unlikely(!__refcount_inc_not_zero_limited_acquire(&vma->vm_refcnt, &oldcnt,
							      VM_REFCNT_LIMIT))) {
		/* return EAGAIN if vma got detached from under us */
		vma = oldcnt ? NULL : ERR_PTR(-EAGAIN);
		goto err;
	}

	__vma_lockdep_acquire_read(vma);

	if (unlikely(vma->vm_mm != mm))
		goto err_unstable;

	/*
	 * Overflow of vm_lock_seq/mm_lock_seq might produce false locked result.
	 * False unlocked result is impossible because we modify and check
	 * vma->vm_lock_seq under vma->vm_refcnt protection and mm->mm_lock_seq
	 * modification invalidates all existing locks.
	 *
	 * We must use ACQUIRE semantics for the mm_lock_seq so that if we are
	 * racing with vma_end_write_all(), we only start reading from the VMA
	 * after it has been unlocked.
	 * This pairs with RELEASE semantics in vma_end_write_all().
	 */
	if (unlikely(vma->vm_lock_seq == raw_read_seqcount(&mm->mm_lock_seq))) {
		vma_refcount_put(vma);
		vma = NULL;
		goto err;
	}

	return vma;
err:
	rcu_read_unlock();

	return vma;
err_unstable:
	/*
	 * If vma got attached to another mm from under us, that mm is not
	 * stable and can be freed in the narrow window after vma->vm_refcnt
	 * is dropped and before rcuwait_wake_up(mm) is called. Grab it before
	 * releasing vma->vm_refcnt.
	 */
	other_mm = vma->vm_mm; /* use a copy as vma can be freed after we drop vm_refcnt */

	/* __mmdrop() is a heavy operation, do it after dropping RCU lock. */
	rcu_read_unlock();
	mmgrab(other_mm);
	vma_refcount_put(vma);
	mmdrop(other_mm);

	return NULL;
}
```

The function first reads [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) with `READ_ONCE()` and bails out (returning NULL) if it equals the owner's current write-lock generation, the pessimistic early check the field comment sanctions. It then takes a bounded increment on [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) capped at [`VM_REFCNT_LIMIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L766); a detached VMA (count 0) yields `-EAGAIN`, and one whose writer set [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765) fails the increment and yields NULL. It re-reads [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) to detect a VMA that was recycled onto a different address space, and finally re-checks the sequence with acquire semantics now that the reference pins the stamp. The public entry point [`lock_vma_under_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296) pairs the maple-tree lookup with this read lock:

```c
/* mm/mmap_lock.c:291 */
/*
 * Lookup and lock a VMA under RCU protection. Returned VMA is guaranteed to be
 * stable and not isolated. If the VMA is not found or is being modified the
 * function returns NULL.
 */
struct vm_area_struct *lock_vma_under_rcu(struct mm_struct *mm,
					  unsigned long address)
{
	MA_STATE(mas, &mm->mm_mt, address, address);
	struct vm_area_struct *vma;

retry:
	rcu_read_lock();
	vma = mas_walk(&mas);
	if (!vma) {
		rcu_read_unlock();
		goto inval;
	}

	vma = vma_start_read(mm, vma);
	if (IS_ERR_OR_NULL(vma)) {
		/* Check if the VMA got isolated after we found it */
		if (PTR_ERR(vma) == -EAGAIN) {
			count_vm_vma_lock_event(VMA_LOCK_MISS);
			/* The area was replaced with another one */
			mas_set(&mas, address);
			goto retry;
		}

		/* Failed to lock the VMA */
		goto inval;
	}
	/*
	 * At this point, we have a stable reference to a VMA: The VMA is
	 * locked and we know it hasn't already been isolated.
	 * From here on, we can access the VMA without worrying about which
	 * fields are accessible for RCU readers.
	 */
	rcu_read_unlock();

	/* Check if the vma we locked is the right one. */
	if (unlikely(address < vma->vm_start || address >= vma->vm_end)) {
		vma_end_read(vma);
		goto inval;
	}

	return vma;

inval:
	count_vm_vma_lock_event(VMA_LOCK_ABORT);
	return NULL;
}
```

[`lock_vma_under_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296) looks up the covering VMA in [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) with [`mas_walk()`](https://elixir.bootlin.com/linux/v7.0/source/lib/maple_tree.c#L4592) under `rcu_read_lock()`, hands it to [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212), and retries the whole lookup on `-EAGAIN` (the VMA was isolated under it). According to the comment "From here on, we can access the VMA without worrying about which fields are accessible for RCU readers", once the read lock is held the caller may touch any field, and it then confirms the address still falls inside `[vm_start, vm_end)` before returning. The x86-64 page-fault handler [`do_user_addr_fault()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L1207) is the consumer; it tries the per-VMA path first and falls back to the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) when the lock or the fault does not complete:

```c
/* arch/x86/mm/fault.c:1322 */
	if (!(flags & FAULT_FLAG_USER))
		goto lock_mmap;

	vma = lock_vma_under_rcu(mm, address);
	if (!vma)
		goto lock_mmap;

	if (unlikely(access_error(error_code, vma))) {
		bad_area_access_error(regs, error_code, address, NULL, vma);
		count_vm_vma_lock_event(VMA_LOCK_SUCCESS);
		return;
	}
	fault = handle_mm_fault(vma, address, flags | FAULT_FLAG_VMA_LOCK, regs);
	if (!(fault & (VM_FAULT_RETRY | VM_FAULT_COMPLETED)))
		vma_end_read(vma);
```

The read lock is dropped by [`vma_end_read()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L262), whose [`vma_refcount_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L210) decrement wakes the [`vma_writer_wait`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1204) rcuwait when the departing reader was the one a writer was waiting out.

### anon_vma_chain and anon_vma tie the VMA to reverse mapping

An anonymous mapping needs a way for the reclaim and migration code to find every page table entry that maps a given anonymous page, and that is what the two anon-vma members provide:

```c
/* include/linux/mm_types.h:960 */
	/*
	 * A file's MAP_PRIVATE vma can be in both i_mmap tree and anon_vma
	 * list, after a COW of one of the file pages.	A MAP_SHARED vma
	 * can only be in the i_mmap tree.  An anonymous MAP_PRIVATE, stack
	 * or brk vma (with NULL file) can only be in an anon_vma list.
	 */
	struct list_head anon_vma_chain; /* Serialized by mmap_lock &
					  * page_table_lock */
	struct anon_vma *anon_vma;	/* Serialized by page_table_lock */
```

[`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) points at the [`struct anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) that owns the interval tree of VMAs mapping the same anonymous pages:

```c
/* include/linux/rmap.h:32 */
struct anon_vma {
	struct anon_vma *root;		/* Root of this anon_vma tree */
	struct rw_semaphore rwsem;	/* W: modification, R: walking the list */
	/*
	 * The refcount is taken on an anon_vma when there is no
	 * guarantee that the vma of page tables will exist for
	 * the duration of the operation. A caller that takes
	 * the reference is responsible for clearing up the
	 * anon_vma if they are the last user on release
	 */
	atomic_t refcount;

	/*
	 * Count of child anon_vmas. Equals to the count of all anon_vmas that
	 * have ->parent pointing to this one, including itself.
	 *
	 * This counter is used for making decision about reusing anon_vma
	 * instead of forking new one. See comments in function anon_vma_clone.
	 */
	unsigned long num_children;
	/* Count of VMAs whose ->anon_vma pointer points to this object. */
	unsigned long num_active_vmas;

	struct anon_vma *parent;	/* Parent of this anon_vma */

	/*
	 * NOTE: the LSB of the rb_root.rb_node is set by
	 * mm_take_all_locks() _after_ taking the above lock. So the
	 * rb_root must only be read/written after taking the above lock
	 * to be sure to see a valid next pointer. The LSB bit itself
	 * is serialized by a system wide lock only visible to
	 * mm_take_all_locks() (mm_all_locks_mutex).
	 */

	/* Interval tree of private "related" vmas */
	struct rb_root_cached rb_root;
};
```

[`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) is the list head threading the [`struct anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83) links that connect this VMA to every [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) it participates in (its own and, after `fork`, its ancestors'):

```c
/* include/linux/rmap.h:70 */
/*
 * The copy-on-write semantics of fork mean that an anon_vma
 * can become associated with multiple processes. Furthermore,
 * each child process will have its own anon_vma, where new
 * pages for that process are instantiated.
 *
 * This structure allows us to find the anon_vmas associated
 * with a VMA, or the VMAs associated with an anon_vma.
 * The "same_vma" list contains the anon_vma_chains linking
 * all the anon_vmas associated with this VMA.
 * The "rb" field indexes on an interval tree the anon_vma_chains
 * which link all the VMAs associated with this anon_vma.
 */
struct anon_vma_chain {
	struct vm_area_struct *vma;
	struct anon_vma *anon_vma;
	struct list_head same_vma;   /* locked by mmap_lock & page_table_lock */
	struct rb_node rb;			/* locked by anon_vma->rwsem */
	unsigned long rb_subtree_last;
#ifdef CONFIG_DEBUG_VM_RB
	unsigned long cached_vma_start, cached_vma_last;
#endif
};
```

According to the field comment, a private file VMA can appear in both the [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree and an [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) list once a copy-on-write has produced a private page, a shared VMA appears only in the [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree, and an anonymous, stack, or brk VMA appears only in an [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) list. The [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list is initialized empty by [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) and stays empty until the first anonymous fault attaches an [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32).

That attachment is lazy. The anonymous fault handler [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217), reached when [`do_pte_missing()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4472) sees an anonymous VMA, prepares the reverse map before allocating the page:

```c
/* mm/memory.c:4472 */
static vm_fault_t do_pte_missing(struct vm_fault *vmf)
{
	if (vma_is_anonymous(vmf->vma))
		return do_anonymous_page(vmf);
	else
		return do_fault(vmf);
}
...
/* mm/memory.c:5261 */
	/* Allocate our own private page. */
	ret = vmf_anon_prepare(vmf);
	if (ret)
		return ret;
	/* Returns NULL on OOM or ERR_PTR(-EAGAIN) if we must retry the fault */
	folio = alloc_anon_folio(vmf);
```

[`vmf_anon_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L500) wraps [`__vmf_anon_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3723) and drops the per-VMA read lock when a retry is required:

```c
/* mm/internal.h:499 */
vm_fault_t __vmf_anon_prepare(struct vm_fault *vmf);
static inline vm_fault_t vmf_anon_prepare(struct vm_fault *vmf)
{
	vm_fault_t ret = __vmf_anon_prepare(vmf);

	if (unlikely(ret & VM_FAULT_RETRY))
		vma_end_read(vmf->vma);
	return ret;
}
...
/* mm/memory.c:3723 */
vm_fault_t __vmf_anon_prepare(struct vm_fault *vmf)
{
	struct vm_area_struct *vma = vmf->vma;
	vm_fault_t ret = 0;

	if (likely(vma->anon_vma))
		return 0;
	if (vmf->flags & FAULT_FLAG_VMA_LOCK) {
		if (!mmap_read_trylock(vma->vm_mm))
			return VM_FAULT_RETRY;
	}
	if (__anon_vma_prepare(vma))
		ret = VM_FAULT_OOM;
	if (vmf->flags & FAULT_FLAG_VMA_LOCK)
		mmap_read_unlock(vma->vm_mm);
	return ret;
}
```

[`__vmf_anon_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3723) returns immediately when [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) already exists, and otherwise, if the fault holds only the per-VMA lock, acquires the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) for read before calling [`__anon_vma_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185). According to its kernel-doc, "__anon_vma_prepare() will look at adjacent VMAs to determine if this VMA can share its anon_vma, and that's not safe to do with only the per-VMA lock held for this VMA". The attach itself installs the pointer under the page-table lock:

```c
/* mm/rmap.c:185 */
int __anon_vma_prepare(struct vm_area_struct *vma)
{
	struct mm_struct *mm = vma->vm_mm;
	struct anon_vma *anon_vma, *allocated;
	struct anon_vma_chain *avc;

	mmap_assert_locked(mm);
	might_sleep();

	avc = anon_vma_chain_alloc(GFP_KERNEL);
	if (!avc)
		goto out_enomem;

	anon_vma = find_mergeable_anon_vma(vma);
	allocated = NULL;
	if (!anon_vma) {
		anon_vma = anon_vma_alloc();
		if (unlikely(!anon_vma))
			goto out_enomem_free_avc;
		anon_vma->num_children++; /* self-parent link for new root */
		allocated = anon_vma;
	}

	anon_vma_lock_write(anon_vma);
	/* page_table_lock to protect against threads */
	spin_lock(&mm->page_table_lock);
	if (likely(!vma->anon_vma)) {
		vma->anon_vma = anon_vma;
		anon_vma_chain_assign(vma, avc, anon_vma);
		anon_vma_interval_tree_insert(avc, &anon_vma->rb_root);
		anon_vma->num_active_vmas++;
		allocated = NULL;
		avc = NULL;
	}
	spin_unlock(&mm->page_table_lock);
	anon_vma_unlock_write(anon_vma);

	if (unlikely(allocated))
		put_anon_vma(allocated);
	if (unlikely(avc))
		anon_vma_chain_free(avc);

	return 0;

 out_enomem_free_avc:
	anon_vma_chain_free(avc);
 out_enomem:
	return -ENOMEM;
}
```

[`__anon_vma_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185) either reuses an adjacent mergeable [`struct anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) or allocates a new one, then sets the VMA's [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) pointer, links a [`struct anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83) onto the VMA's [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list, and inserts that chain node into the [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32)'s interval tree, bumping `num_active_vmas`. The write is guarded by the page-table lock, which is the serialization the [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) field comment names, and the `if (likely(!vma->anon_vma))` re-check makes a concurrent preparer's allocation harmless.

### vm_ops points at the operations struct for the mapping

The behavior of a VMA under a page fault is selected by its operations pointer:

```c
/* include/linux/mm_types.h:970 */
	/* Function pointers to deal with this struct. */
	const struct vm_operations_struct *vm_ops;
```

[`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) selects a [`struct vm_operations_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L749), whose function pointers the core mm calls to service the range:

```c
/* include/linux/mm.h:744 */
/*
 * These are the virtual MM functions - opening of an area, closing and
 * unmapping it (needed to keep files on disk up-to-date etc), pointer
 * to the functions called when a no-page or a wp-page exception occurs.
 */
struct vm_operations_struct {
	void (*open)(struct vm_area_struct * area);
	/**
	 * @close: Called when the VMA is being removed from the MM.
	 * Context: User context.  May sleep.  Caller holds mmap_lock.
	 */
	void (*close)(struct vm_area_struct * area);
	/* Called any time before splitting to check if it's allowed */
	int (*may_split)(struct vm_area_struct *area, unsigned long addr);
	int (*mremap)(struct vm_area_struct *area);
	/*
	 * Called by mprotect() to make driver-specific permission
	 * checks before mprotect() is finalised.   The VMA must not
	 * be modified.  Returns 0 if mprotect() can proceed.
	 */
	int (*mprotect)(struct vm_area_struct *vma, unsigned long start,
			unsigned long end, unsigned long newflags);
	vm_fault_t (*fault)(struct vm_fault *vmf);
	vm_fault_t (*huge_fault)(struct vm_fault *vmf, unsigned int order);
	vm_fault_t (*map_pages)(struct vm_fault *vmf,
			pgoff_t start_pgoff, pgoff_t end_pgoff);
	unsigned long (*pagesize)(struct vm_area_struct * area);

	/* notification that a previously read-only page is about to become
	 * writable, if an error is returned it will cause a SIGBUS */
	vm_fault_t (*page_mkwrite)(struct vm_fault *vmf);

	/* same as page_mkwrite when using VM_PFNMAP|VM_MIXEDMAP */
	vm_fault_t (*pfn_mkwrite)(struct vm_fault *vmf);
	...
	const char *(*name)(struct vm_area_struct *vma);

#ifdef CONFIG_NUMA
	...
	int (*set_policy)(struct vm_area_struct *vma, struct mempolicy *new);
	...
	struct mempolicy *(*get_policy)(struct vm_area_struct *vma,
					unsigned long addr, pgoff_t *ilx);
#endif
	...
};
```

The `fault` handler is invoked when a page in the range is accessed and no PTE resolves it, `map_pages` pre-populates PTEs around a fault, `page_mkwrite` gates the transition of a read-only page to writable, and `open`/`close` run when the VMA is split, merged, or torn down. A NULL [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) is the sole marker that a VMA is anonymous, and the marker has one writer and one reader:

```c
/* include/linux/mm.h:1230 */
static inline void vma_set_anonymous(struct vm_area_struct *vma)
{
	vma->vm_ops = NULL;
}

static inline bool vma_is_anonymous(struct vm_area_struct *vma)
{
	return !vma->vm_ops;
}
```

[`vma_set_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230) writes the NULL marker, and [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235) reports true when [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) is NULL. The [`do_pte_missing()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4472) dispatcher shown earlier is the fault-path reader, routing an anonymous fault to [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217) and everything else to the `fault` operation, and a grep across `mm/`, `fs/`, `kernel/`, `drivers/`, `arch/x86/`, and `include/` finds 47 call sites of [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235) at this tree.

### vma_init points a fresh VMA at vma_dummy_vm_ops

Every VMA passes through one initializer that establishes the invariants the rest of the code relies on:

```c
/* include/linux/mm.h:907 */
extern const struct vm_operations_struct vma_dummy_vm_ops;

static inline void vma_init(struct vm_area_struct *vma, struct mm_struct *mm)
{
	memset(vma, 0, sizeof(*vma));
	vma->vm_mm = mm;
	vma->vm_ops = &vma_dummy_vm_ops;
	INIT_LIST_HEAD(&vma->anon_vma_chain);
	vma_lock_init(vma, false);
}
```

[`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) zeroes the whole object, sets the owner [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), initializes the empty [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list, and seeds the per-VMA lock with [`vma_lock_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L150). It points [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) at the shared placeholder [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20), a single zero-initialized operations struct whose only definition is one line:

```c
/* mm/init-mm.c:20 */
const struct vm_operations_struct vma_dummy_vm_ops;
```

Pointing a fresh VMA at [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20) rather than leaving [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) NULL keeps [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235) from reporting a partially built VMA as anonymous before the mapping path has decided what it is. The same dummy struct is re-installed at two later points where the real operations become unsafe to invoke. [`vma_close()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L187) installs it after the `close` operation runs, and [`mmap_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L165) installs it when the file's `mmap` operation fails partway:

```c
/* mm/internal.h:182 */
/*
 * If the VMA has a close hook then close it, and since closing it might leave
 * it in an inconsistent state which makes the use of any hooks suspect, clear
 * them down by installing dummy empty hooks.
 */
static inline void vma_close(struct vm_area_struct *vma)
{
	if (vma->vm_ops && vma->vm_ops->close) {
		vma->vm_ops->close(vma);

		/*
		 * The mapping is in an inconsistent state, and no further hooks
		 * may be invoked upon it.
		 */
		vma->vm_ops = &vma_dummy_vm_ops;
	}
}
...
/* mm/internal.h:165 */
static inline int mmap_file(struct file *file, struct vm_area_struct *vma)
{
	int err = vfs_mmap(file, vma);

	if (likely(!err))
		return 0;

	/*
	 * OK, we tried to call the file hook for mmap(), but an error
	 * arose. The mapping is in an inconsistent state and we must not invoke
	 * any further hooks on it.
	 */
	vma->vm_ops = &vma_dummy_vm_ops;
```

### vm_pgoff and vm_file describe the backing store

The backing-store members say what a fault should read into a newly mapped page:

```c
/* include/linux/mm_types.h:973 */
	/* Information about our backing store: */
	unsigned long vm_pgoff;		/* Offset (within vm_file) in PAGE_SIZE
					   units */
	struct file * vm_file;		/* File we map to (can be NULL). */
	void * vm_private_data;		/* was vm_pte (shared mem) */
```

[`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) is the mapped [`struct file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1259), whose `f_mapping` names the [`struct address_space`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L470) that the [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1041) node links into:

```c
/* include/linux/fs.h:1259 */
struct file {
	spinlock_t			f_lock;
	fmode_t				f_mode;
	const struct file_operations	*f_op;
	struct address_space		*f_mapping;
	void				*private_data;
	struct inode			*f_inode;
	...
};
```

[`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) is the offset (in page units) into that file at which the range starts, so the file page backing a virtual address `addr` is `vm_pgoff + ((addr - vm_start) >> PAGE_SHIFT)`. For an anonymous VMA, [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) is NULL and [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) holds the virtual page offset of the range instead (`vm_start >> PAGE_SHIFT`); the kernel-doc of [`mmap_region()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2818) describes the parameter as "If @file is specified, the page offset into the file, if not then the virtual page offset in memory of the anonymous mapping". [`insert_vm_struct()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L3273) seeds exactly that value for a pre-built anonymous VMA, and its comment explains why the seemingly irrelevant field is set at all:

```c
/* mm/vma.c:3285 */
	/*
	 * The vm_pgoff of a purely anonymous vma should be irrelevant
	 * until its first write fault, when page's anon_vma and index
	 * are set.  But now set the vm_pgoff it will almost certainly
	 * end up with (unless mremap moves it elsewhere before that
	 * first wfault), so /proc/pid/maps tells a consistent story.
	 *
	 * By setting it to reflect the virtual start address of the
	 * vma, merges and splits can happen in a seamless way, just
	 * using the existing file pgoff checks and manipulations.
	 * Similarly in do_mmap and in do_brk_flags.
	 */
	if (vma_is_anonymous(vma)) {
		BUG_ON(vma->anon_vma);
		vma->vm_pgoff = vma->vm_start >> PAGE_SHIFT;
	}
```

[`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866) applies the same convention when it builds a fresh brk VMA, passing `addr >> PAGE_SHIFT` as the offset:

```c
/* mm/vma.c:2911 */
	vma_set_range(vma, addr, addr + len, addr >> PAGE_SHIFT);
```

Assigning [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) takes a counted reference on the file (`get_file()` in [`__mmap_new_file_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2455), shown below), and [`remove_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L463) drops that reference with `fput()` when the VMA is destroyed.

### vm_private_data carries per-mapping driver state

The third backing-store member is opaque to the core mm. [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) is a `void *` that the driver or filesystem behind [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) uses to hang per-mapping state, and its comment "was vm_pte (shared mem)" records that the slot was once used by System V shared memory. The core mm never dereferences it; it copies it on duplication and lets the owning subsystem interpret it. The special-mapping installer that places the vdso and vvar ranges into every process writes both driver-facing fields together:

```c
/* mm/mmap.c:1451 */
static struct vm_area_struct *__install_special_mapping(
	struct mm_struct *mm,
	unsigned long addr, unsigned long len,
	vm_flags_t vm_flags, void *priv,
	const struct vm_operations_struct *ops)
{
	int ret;
	struct vm_area_struct *vma;

	vma = vm_area_alloc(mm);
	if (unlikely(vma == NULL))
		return ERR_PTR(-ENOMEM);

	vma_set_range(vma, addr, addr + len, 0);
	vm_flags |= mm->def_flags | VM_DONTEXPAND;
	if (pgtable_supports_soft_dirty())
		vm_flags |= VM_SOFTDIRTY;
	vm_flags_init(vma, vm_flags & ~VM_LOCKED_MASK);
	vma->vm_page_prot = vm_get_page_prot(vma->vm_flags);

	vma->vm_ops = ops;
	vma->vm_private_data = priv;

	ret = insert_vm_struct(mm, vma);
```

Because those two fields identify the mapping, [`vma_is_special_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1489) recognizes a special mapping by comparing both of them:

```c
/* mm/mmap.c:1489 */
bool vma_is_special_mapping(const struct vm_area_struct *vma,
	const struct vm_special_mapping *sm)
{
	return vma->vm_private_data == sm &&
		vma->vm_ops == &special_mapping_vmops;
}
```

The x86-64 vdso code uses this predicate in [`map_vdso_once()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/entry/vdso/vma.c#L197) to refuse a second vdso blob in the same address space:

```c
/* arch/x86/entry/vdso/vma.c:211 */
	for_each_vma(vmi, vma) {
		if (vma_is_special_mapping(vma, &vdso_mapping) ||
				vma_is_special_mapping(vma, &vdso_vvar_mapping) ||
				vma_is_special_mapping(vma, &vvar_vclock_mapping)) {
			mmap_write_unlock(mm);
			return -EEXIST;
		}
	}
```

A `mmap_prepare` filesystem fills [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) indirectly, through the `private_data` member of the [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880) it is handed, and [`set_vma_user_defined_fields()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2665) copies both it and [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) onto the finished VMA.

### vma_set_range writes the address range and file offset together

The three fields that place a VMA in both trees are written by one helper so they stay consistent:

```c
/* mm/internal.h:1620 */
static __always_inline void vma_set_range(struct vm_area_struct *vma,
					  unsigned long start, unsigned long end,
					  pgoff_t pgoff)
{
	vma->vm_start = start;
	vma->vm_end = end;
	vma->vm_pgoff = pgoff;
}
```

[`vma_set_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620) writes [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919), [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920), and [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) in one call, keeping the maple-tree key and the file-offset key from drifting apart. Seven call sites use it at this tree, six in [`mm/vma.c`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c) (VMA merge at [`mm/vma.c:717`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L717) and [`mm/vma.c:761`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L761), relocation at [`mm/vma.c:1250`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1250), the `mremap` copy in [`copy_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1844) at [`mm/vma.c:1907`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1907), the new mapping in [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) at [`mm/vma.c:2522`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2522), and the brk extension in [`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866) at [`mm/vma.c:2911`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2911)), plus the special-mapping installer at [`mm/mmap.c:1464`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1464). The split path is the exception that proves the offset arithmetic. [`__split_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L497) duplicates the VMA and then adjusts the copy's boundary fields directly, recomputing [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) by hand for the tail half:

```c
/* mm/vma.c:513 */
	new = vm_area_dup(vma);
	if (!new)
		return -ENOMEM;

	if (new_below) {
		new->vm_end = addr;
	} else {
		new->vm_start = addr;
		new->vm_pgoff += ((addr - vma->vm_start) >> PAGE_SHIFT);
	}
```

### swap_readahead_info records the per-VMA swap readahead window

Under `CONFIG_SWAP`, each VMA remembers how well swap readahead has been predicting its access pattern:

```c
/* include/linux/mm_types.h:979 */
#ifdef CONFIG_SWAP
	atomic_long_t swap_readahead_info;
#endif
```

[`swap_readahead_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L980) packs the last faulting address, the current readahead window size, and a hit counter into one `atomic_long_t`, laid out by a macro family that reuses the sub-page bits of the address:

```c
/* mm/swap_state.c:46 */
#define SWAP_RA_ORDER_CEILING	5

#define SWAP_RA_WIN_SHIFT	(PAGE_SHIFT / 2)
#define SWAP_RA_HITS_MASK	((1UL << SWAP_RA_WIN_SHIFT) - 1)
#define SWAP_RA_HITS_MAX	SWAP_RA_HITS_MASK
#define SWAP_RA_WIN_MASK	(~PAGE_MASK & ~SWAP_RA_HITS_MASK)

#define SWAP_RA_HITS(v)		((v) & SWAP_RA_HITS_MASK)
#define SWAP_RA_WIN(v)		(((v) & SWAP_RA_WIN_MASK) >> SWAP_RA_WIN_SHIFT)
#define SWAP_RA_ADDR(v)		((v) & PAGE_MASK)

#define SWAP_RA_VAL(addr, win, hits)				\
	(((addr) & PAGE_MASK) |					\
	 (((win) << SWAP_RA_WIN_SHIFT) & SWAP_RA_WIN_MASK) |	\
	 ((hits) & SWAP_RA_HITS_MASK))

/* Initial readahead hits is 4 to start up with a small window */
#define GET_SWAP_RA_VAL(vma)					\
	(atomic_long_read(&(vma)->swap_readahead_info) ? : 4)
```

On x86-64 with `PAGE_SHIFT` = 12, the low 6 bits hold the hit count (capped at 63 by `SWAP_RA_HITS_MAX`), bits 6 to 11 hold the window, and the page-aligned address occupies the rest; according to the comment, a zero-initialized field reads back as an initial hit count of 4 "to start up with a small window". On a swap-cache hit, [`swap_update_readahead()`](https://elixir.bootlin.com/linux/v7.0/source/mm/swap_state.c#L440) recomputes the packed value and stores it back atomically:

```c
/* mm/swap_state.c:440 */
void swap_update_readahead(struct folio *folio, struct vm_area_struct *vma,
			   unsigned long addr)
{
	bool readahead, vma_ra = swap_use_vma_readahead();

	/*
	 * At the moment, we don't support PG_readahead for anon THP
	 * so let's bail out rather than confusing the readahead stat.
	 */
	if (unlikely(folio_test_large(folio)))
		return;

	readahead = folio_test_clear_readahead(folio);
	if (vma && vma_ra) {
		unsigned long ra_val;
		int win, hits;

		ra_val = GET_SWAP_RA_VAL(vma);
		win = SWAP_RA_WIN(ra_val);
		hits = SWAP_RA_HITS(ra_val);
		if (readahead)
			hits = min_t(int, hits + 1, SWAP_RA_HITS_MAX);
		atomic_long_set(&vma->swap_readahead_info,
				SWAP_RA_VAL(addr, win, hits));
	}
```

The caller is the swap fault path; [`do_swap_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4706) reports every swap-cache hit against the faulting VMA and address:

```c
/* mm/memory.c:4785 */
	folio = swap_cache_get_folio(entry);
	if (folio)
		swap_update_readahead(folio, vma, vmf->address);
```

The packed value is read by the VMA-based swap readahead code to decide how many neighboring swap slots to prefetch (never more than `1 << SWAP_RA_ORDER_CEILING` = 32 pages), growing the window on hits and shrinking it on misses. Because it is a single `atomic_long_t`, updates need no lock and the field is outside the protection of the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196).

### vm_policy holds the NUMA memory policy for the range

Under `CONFIG_NUMA`, a VMA can carry a memory policy that overrides the task default for allocations in its range:

```c
/* include/linux/mm_types.h:985 */
#ifdef CONFIG_NUMA
	struct mempolicy *vm_policy;	/* NUMA policy for the VMA */
#endif
```

[`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986) points at a refcounted [`struct mempolicy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mempolicy.h#L47) that `mbind()` installs:

```c
/* include/linux/mempolicy.h:47 */
struct mempolicy {
	atomic_t refcnt;
	unsigned short mode; 	/* See MPOL_* above */
	unsigned short flags;	/* See set_mempolicy() MPOL_F_* above */
	nodemask_t nodes;	/* interleave/bind/preferred/etc */
	int home_node;		/* Home node to use for MPOL_BIND and MPOL_PREFERRED_MANY */

	union {
		nodemask_t cpuset_mems_allowed;	/* relative to these nodes */
		nodemask_t user_nodemask;	/* nodemask passed by user */
	} w;
	struct rcu_head rcu;
};
```

The field is written by [`vma_replace_policy()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L1009), which asserts the per-VMA write lock, offers the change to a driver `set_policy` operation, and then swaps the pointer:

```c
/* mm/mempolicy.c:1009 */
static int vma_replace_policy(struct vm_area_struct *vma,
				struct mempolicy *pol)
{
	int err;
	struct mempolicy *old;
	struct mempolicy *new;

	vma_assert_write_locked(vma);

	new = mpol_dup(pol);
	if (IS_ERR(new))
		return PTR_ERR(new);

	if (vma->vm_ops && vma->vm_ops->set_policy) {
		err = vma->vm_ops->set_policy(vma, new);
		if (err)
			goto err_out;
	}

	old = vma->vm_policy;
	WRITE_ONCE(vma->vm_policy, new); /* protected by mmap_lock */
	mpol_put(old);

	return 0;
 err_out:
	mpol_put(new);
	return err;
}
```

According to the comment "protected by mmap_lock", the swap is a `WRITE_ONCE()` under the write lock, and the old policy's reference is dropped afterward. Its caller is [`mbind_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L1040), which splits or merges the VMA as needed and then applies the new policy at [`mm/mempolicy.c:1063`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L1063). On `fork`, [`vma_dup_policy()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L2802) deep-copies the policy into the child VMA so the two do not share a mutable [`struct mempolicy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mempolicy.h#L47), and [`dup_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732) calls it right after [`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121) (shown earlier at [`mm/mmap.c:1790`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1790)):

```c
/* mm/mempolicy.c:2802 */
int vma_dup_policy(struct vm_area_struct *src, struct vm_area_struct *dst)
{
	struct mempolicy *pol = mpol_dup(src->vm_policy);

	if (IS_ERR(pol))
		return PTR_ERR(pol);
	dst->vm_policy = pol;
	return 0;
}
```

[`remove_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L463) drops the reference with [`mpol_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mempolicy.h#L67) when the VMA dies.

### numab_state tracks NUMA balancing scan progress

Under `CONFIG_NUMA_BALANCING`, the scheduler's NUMA scanner keeps per-VMA state so it can decide which ranges to sample:

```c
/* include/linux/mm_types.h:988 */
#ifdef CONFIG_NUMA_BALANCING
	struct vma_numab_state *numab_state;	/* NUMA Balancing state */
#endif
```

[`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989) points at a [`struct vma_numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L768) recording when the VMA should next be scanned and which PIDs recently faulted in it:

```c
/* include/linux/mm_types.h:768 */
struct vma_numab_state {
	/*
	 * Initialised as time in 'jiffies' after which VMA
	 * should be scanned.  Delays first scan of new VMA by at
	 * least sysctl_numa_balancing_scan_delay:
	 */
	unsigned long next_scan;

	/*
	 * Time in jiffies when pids_active[] is reset to
	 * detect phase change behaviour:
	 */
	unsigned long pids_active_reset;

	/*
	 * Approximate tracking of PIDs that trapped a NUMA hinting
	 * fault. May produce false positives due to hash collisions.
	 *
	 *   [0] Previous PID tracking
	 *   [1] Current PID tracking
	 *
	 * Window moves after next_pid_reset has expired approximately
	 * every VMA_PID_RESET_PERIOD jiffies:
	 */
	unsigned long pids_active[2];

	/* MM scan sequence ID when scan first started after VMA creation */
	int start_scan_seq;

	/*
	 * MM scan sequence ID when the VMA was last completely scanned.
	 * A VMA is not eligible for scanning if prev_scan_seq == numa_scan_seq
	 */
	int prev_scan_seq;
};
```

The pointer is NULL until the first scan touches the VMA. [`task_numa_work()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3363), the deferred task-work that [`init_numa_balancing()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3620) registers on every task with `init_task_work(&p->numa_work, task_numa_work)` at [`kernel/sched/fair.c:3645`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3645), skips inaccessible VMAs via [`vma_is_accessible()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1290) and allocates the state with a `cmpxchg` so concurrent scanners install it exactly once:

```c
/* kernel/sched/fair.c:3478 */
		if (!vma_is_accessible(vma)) {
			trace_sched_skip_vma_numa(mm, vma, NUMAB_SKIP_INACCESSIBLE);
			continue;
		}

		/* Initialise new per-VMA NUMAB state. */
		if (!vma->numab_state) {
			struct vma_numab_state *ptr;

			ptr = kzalloc_obj(*ptr);
			if (!ptr)
				continue;

			if (cmpxchg(&vma->numab_state, NULL, ptr)) {
				kfree(ptr);
				continue;
			}

			vma->numab_state->start_scan_seq = mm->numa_scan_seq;

			vma->numab_state->next_scan = now +
				msecs_to_jiffies(sysctl_numa_balancing_scan_delay);
```

The scan sequence fields let the balancer skip a VMA that was already scanned in the current pass, and `next_scan` delays the first scan of a new VMA by at least `sysctl_numa_balancing_scan_delay` (1000 ms by default). The allocation is released by [`vma_numab_state_free()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L836), a plain `kfree()` of the pointer that [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) invokes, and [`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121) resets the clone's pointer with [`vma_numab_state_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L832) so scan state is never shared across a `fork`.

### The shared.rb node links a file VMA into the i_mmap interval tree

A file-backed VMA is a member of two trees at once, the owner's [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) and the file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480). The embedded node for the second is the [`shared`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) sub-struct reproduced in the definition above, an rb-node plus the [`rb_subtree_last`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1042) augmentation. The tree it lands in belongs to the mapped file's [`struct address_space`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L470), which also carries the rwsem that serializes it:

```c
/* include/linux/fs.h:470 */
struct address_space {
	struct inode		*host;
	struct xarray		i_pages;
	struct rw_semaphore	invalidate_lock;
	gfp_t			gfp_mask;
	atomic_t		i_mmap_writable;
	...
	struct rb_root_cached	i_mmap;
	unsigned long		nrpages;
	pgoff_t			writeback_index;
	const struct address_space_operations *a_ops;
	unsigned long		flags;
	errseq_t		wb_err;
	spinlock_t		i_private_lock;
	struct list_head	i_private_list;
	struct rw_semaphore	i_mmap_rwsem;
	void *			i_private_data;
} __attribute__((aligned(sizeof(long)))) __randomize_layout;
```

The interval-tree operations on [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1041), including [`vma_interval_tree_insert()`](https://elixir.bootlin.com/linux/v7.0/source/mm/interval_tree.c#L23), are generated by `INTERVAL_TREE_DEFINE`, keyed on the file-offset interval derived from [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) and [`vma_pages()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3997):

```c
/* mm/interval_tree.c:13 */
static inline unsigned long vma_start_pgoff(struct vm_area_struct *v)
{
	return v->vm_pgoff;
}

static inline unsigned long vma_last_pgoff(struct vm_area_struct *v)
{
	return v->vm_pgoff + vma_pages(v) - 1;
}

INTERVAL_TREE_DEFINE(struct vm_area_struct, shared.rb,
		     unsigned long, shared.rb_subtree_last,
		     vma_start_pgoff, vma_last_pgoff, /* empty */, vma_interval_tree)
```

That tree is how the kernel finds every VMA mapping a given file range when the file is truncated or a shared page is unmapped, the file-backed counterpart to the [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) interval tree (which keys on the same [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) values through its chain nodes). Insertion happens through [`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810) and its inner helper:

```c
/* mm/vma.c:1810 */
static void vma_link_file(struct vm_area_struct *vma, bool hold_rmap_lock)
{
	struct file *file = vma->vm_file;
	struct address_space *mapping;

	if (file) {
		mapping = file->f_mapping;
		i_mmap_lock_write(mapping);
		__vma_link_file(vma, mapping);
		if (!hold_rmap_lock)
			i_mmap_unlock_write(mapping);
	}
}
...
/* mm/vma.c:227 */
static void __vma_link_file(struct vm_area_struct *vma,
			    struct address_space *mapping)
{
	if (vma_is_shared_maywrite(vma))
		mapping_allow_writable(mapping);

	flush_dcache_mmap_lock(mapping);
	vma_interval_tree_insert(vma, &mapping->i_mmap);
	flush_dcache_mmap_unlock(mapping);
}
```

When [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) is set, [`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810) takes the mapping's `i_mmap_rwsem` for write and [`__vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L227) inserts the node, first bumping the mapping's writable count when [`vma_is_shared_maywrite()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1306) reports a shared, possibly-writable mapping:

```c
/* include/linux/mm.h:1301 */
static inline bool is_shared_maywrite(const vma_flags_t *flags)
{
	return vma_flags_test_all(flags, VMA_SHARED_BIT, VMA_MAYWRITE_BIT);
}

static inline bool vma_is_shared_maywrite(const struct vm_area_struct *vma)
{
	return is_shared_maywrite(&vma->flags);
}
```

[`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810) is called from [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) for a new mapping (shown below) and from [`vma_link()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1824) for other insertions, always after [`vma_start_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L298) has write-locked the VMA and [`vma_iter_store_new()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610) has placed it in [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140):

```c
/* mm/vma.c:1824 */
static int vma_link(struct mm_struct *mm, struct vm_area_struct *vma)
{
	VMA_ITERATOR(vmi, mm, 0);

	vma_iter_config(&vmi, vma->vm_start, vma->vm_end);
	if (vma_iter_prealloc(&vmi, vma))
		return -ENOMEM;

	vma_start_write(vma);
	vma_iter_store_new(&vmi, vma);
	vma_link_file(vma, /* hold_rmap_lock= */false);
	mm->map_count++;
	validate_mm(mm);
	return 0;
}
```

[`vma_link()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1824) is the insertion helper behind [`insert_vm_struct()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L3273), and it increments [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) as part of the same operation. The unlink side runs under the same rwsem; [`__remove_shared_vm_struct()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L241) mirrors the insert with [`vma_interval_tree_remove()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3791):

```c
/* mm/vma.c:241 */
static void __remove_shared_vm_struct(struct vm_area_struct *vma,
				      struct address_space *mapping)
{
	if (vma_is_shared_maywrite(vma))
		mapping_unmap_writable(mapping);

	flush_dcache_mmap_lock(mapping);
	vma_interval_tree_remove(vma, &mapping->i_mmap);
	flush_dcache_mmap_unlock(mapping);
}
```

### anon_name attaches a name to an anonymous mapping

Under `CONFIG_ANON_VMA_NAME`, an anonymous mapping can carry a user-assigned name for reporting in `/proc/PID/maps`. The field points at a kref-counted, dynamically sized string object:

```c
/* include/linux/mm_types.h:728 */
struct anon_vma_name {
	struct kref kref;
	/* The name needs to be at the end because it is dynamically sized. */
	char name[];
};
```

According to the field comment, [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) is "Serialized by mmap_lock. Use anon_vma_name to access", and the accessor asserts that the caller has the VMA stabilised before handing out the pointer:

```c
/* mm/madvise.c:110 */
struct anon_vma_name *anon_vma_name(struct vm_area_struct *vma)
{
	vma_assert_stabilised(vma);
	return vma->anon_name;
}
```

The writer is `madvise(MADV_SET_ANON_NAME)`; [`madvise_update_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/madvise.c#L150) calls [`replace_anon_vma_name()`](https://elixir.bootlin.com/linux/v7.0/source/mm/madvise.c#L117) at [`mm/madvise.c:179`](https://elixir.bootlin.com/linux/v7.0/source/mm/madvise.c#L179), which swaps the refcounted string:

```c
/* mm/madvise.c:116 */
/* mmap_lock should be write-locked */
static int replace_anon_vma_name(struct vm_area_struct *vma,
				 struct anon_vma_name *anon_name)
{
	struct anon_vma_name *orig_name = anon_vma_name(vma);

	if (!anon_name) {
		vma->anon_name = NULL;
		anon_vma_name_put(orig_name);
		return 0;
	}

	if (anon_vma_name_eq(orig_name, anon_name))
		return 0;

	vma->anon_name = anon_vma_name_reuse(anon_name);
	anon_vma_name_put(orig_name);

	return 0;
}
```

On duplication, [`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121) takes a fresh reference on the shared string via [`dup_anon_vma_name()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L408), and [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) drops it via [`free_anon_vma_name()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_inline.h#L417).

### vm_userfaultfd_ctx and pfnmap_track_ctx attach optional per-VMA state

The final two members attach optional per-VMA subsystems. The userfaultfd context is embedded by value and collapses to an empty struct when userfaultfd is not built in:

```c
/* include/linux/mm_types.h:718 */
#ifdef CONFIG_USERFAULTFD
#define NULL_VM_UFFD_CTX ((struct vm_userfaultfd_ctx) { NULL, })
struct vm_userfaultfd_ctx {
	struct userfaultfd_ctx *ctx;
};
#else /* CONFIG_USERFAULTFD */
#define NULL_VM_UFFD_CTX ((struct vm_userfaultfd_ctx) {})
struct vm_userfaultfd_ctx {};
#endif /* CONFIG_USERFAULTFD */
```

[`userfaultfd_set_ctx()`](https://elixir.bootlin.com/linux/v7.0/source/mm/userfaultfd.c#L1956) is the writer; it write-locks the VMA, assigns the wrapped pointer, and reruns the flag update shown earlier:

```c
/* mm/userfaultfd.c:1956 */
static void userfaultfd_set_ctx(struct vm_area_struct *vma,
				struct userfaultfd_ctx *ctx,
				vm_flags_t vm_flags)
{
	vma_start_write(vma);
	vma->vm_userfaultfd_ctx = (struct vm_userfaultfd_ctx){ctx};
	userfaultfd_set_vm_flags(vma,
				 (vma->vm_flags & ~__VM_UFFD_FLAGS) | vm_flags);
}
```

Its callers are [`userfaultfd_register_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/userfaultfd.c#L2007), which stamps the context onto every VMA in the registered range at [`mm/userfaultfd.c:2054`](https://elixir.bootlin.com/linux/v7.0/source/mm/userfaultfd.c#L2054), and [`userfaultfd_reset_ctx()`](https://elixir.bootlin.com/linux/v7.0/source/mm/userfaultfd.c#L1966), which clears it by passing NULL. The PFN-tracking pointer exists only under [`__HAVE_PFNMAP_TRACKING`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L528), which the x86 headers define ("Indicate that x86 has its own track and untrack pfn vma functions"), and records a kref-counted PFN range whose memory-type reservation (PAT) must be released when the last VMA sharing it goes away:

```c
/* include/linux/mm_types.h:804 */
#ifdef __HAVE_PFNMAP_TRACKING
struct pfnmap_track_ctx {
	struct kref kref;
	unsigned long pfn;
	unsigned long size;	/* in bytes */
};
#endif
```

The writer is [`remap_pfn_range_track()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3058), which allocates a tracking context only when the remap covers the whole VMA:

```c
/* mm/memory.c:3058 */
static int remap_pfn_range_track(struct vm_area_struct *vma, unsigned long addr,
		unsigned long pfn, unsigned long size, pgprot_t prot)
{
	struct pfnmap_track_ctx *ctx = NULL;
	int err;

	size = PAGE_ALIGN(size);

	/*
	 * If we cover the full VMA, we'll perform actual tracking, and
	 * remember to untrack when the last reference to our tracking
	 * context from a VMA goes away. We'll keep tracking the whole pfn
	 * range even during VMA splits and partial unmapping.
	 *
	 * If we only cover parts of the VMA, we'll only setup the cachemode
	 * in the pgprot for the pfn range.
	 */
	if (addr == vma->vm_start && addr + size == vma->vm_end) {
		if (vma->pfnmap_track_ctx)
			return -EINVAL;
		ctx = pfnmap_track_ctx_alloc(pfn, size, &prot);
		if (IS_ERR(ctx))
			return PTR_ERR(ctx);
	} else if (pfnmap_setup_cachemode(pfn, size, &prot)) {
		return -EINVAL;
	}

	err = remap_pfn_range_notrack(vma, addr, pfn, size, prot);
	if (ctx) {
		if (err)
			kref_put(&ctx->kref, pfnmap_track_ctx_release);
		else
			vma->pfnmap_track_ctx = ctx;
	}
	return err;
}
```

According to the comment, the context keeps "tracking the whole pfn range even during VMA splits and partial unmapping", which is why the field is reference-counted rather than owned. On duplication, [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41) clears the clone's pointer and [`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121) takes the extra kref through [`vma_pfnmap_track_ctx_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L81); on destruction, [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) drops the reference through [`vma_pfnmap_track_ctx_release()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L100).

### vm_area_alloc takes a VMA from the vm_area_cachep slab

The public constructor allocates one object from the slab and initializes it:

```c
/* mm/vma_init.c:28 */
struct vm_area_struct *vm_area_alloc(struct mm_struct *mm)
{
	struct vm_area_struct *vma;

	vma = kmem_cache_alloc(vm_area_cachep, GFP_KERNEL);
	if (!vma)
		return NULL;

	vma_init(vma, mm);

	return vma;
}
```

[`vm_area_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28) is the entry point every fresh mapping uses. [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) calls it for a new `mmap` mapping (shown below), [`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866) for a brk extension that cannot reuse the existing VMA, and [`__install_special_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1451) for the vdso-style special mappings (shown earlier). The matching destructor returns a detached VMA to the same slab after releasing its per-feature state:

```c
/* mm/vma_init.c:144 */
void vm_area_free(struct vm_area_struct *vma)
{
	/* The vma should be detached while being destroyed. */
	vma_assert_detached(vma);
	vma_numab_state_free(vma);
	free_anon_vma_name(vma);
	vma_pfnmap_track_ctx_release(vma);
	kmem_cache_free(vm_area_cachep, vma);
}
```

[`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) asserts the VMA is already detached (its [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) has reached 0) via [`vma_assert_detached()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L438), frees the lazily allocated [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989), drops the [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) reference, releases the [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054), and returns the object to [`vm_area_cachep`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L12), where the `SLAB_TYPESAFE_BY_RCU` grace period keeps the memory readable by a concurrent lockless reader until it is safe to recycle. Its caller for a live mapping is [`remove_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L463), which first releases the references the VMA's own fields hold:

```c
/* mm/vma.c:460 */
/*
 * Close a vm structure and free it.
 */
void remove_vma(struct vm_area_struct *vma)
{
	might_sleep();
	vma_close(vma);
	if (vma->vm_file)
		fput(vma->vm_file);
	mpol_put(vma_policy(vma));
	vm_area_free(vma);
}
```

[`remove_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L463) runs from the two unmap paths shown earlier, the `munmap` completion in [`vms_complete_munmap_vmas()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1311) (which first decrements [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) by the number of removed VMAs, then frees each one from the detached tree at [`mm/vma.c:1342`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1342)) and the process-exit sweep in [`tear_down_vmas()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1252).

### vm_area_init_from copies every member during duplication

The `fork`, split, and `mremap` paths duplicate a VMA rather than re-derive it, and the routine that copies it member by member is the one the type comment warns about:

```c
/* mm/vma_init.c:41 */
static void vm_area_init_from(const struct vm_area_struct *src,
			      struct vm_area_struct *dest)
{
	dest->vm_mm = src->vm_mm;
	dest->vm_ops = src->vm_ops;
	dest->vm_start = src->vm_start;
	dest->vm_end = src->vm_end;
	dest->anon_vma = src->anon_vma;
	dest->vm_pgoff = src->vm_pgoff;
	dest->vm_file = src->vm_file;
	dest->vm_private_data = src->vm_private_data;
	vm_flags_init(dest, src->vm_flags);
	memcpy(&dest->vm_page_prot, &src->vm_page_prot,
	       sizeof(dest->vm_page_prot));
	/*
	 * src->shared.rb may be modified concurrently when called from
	 * dup_mmap(), but the clone will reinitialize it.
	 */
	data_race(memcpy(&dest->shared, &src->shared, sizeof(dest->shared)));
	memcpy(&dest->vm_userfaultfd_ctx, &src->vm_userfaultfd_ctx,
	       sizeof(dest->vm_userfaultfd_ctx));
#ifdef CONFIG_ANON_VMA_NAME
	dest->anon_name = src->anon_name;
#endif
#ifdef CONFIG_SWAP
	memcpy(&dest->swap_readahead_info, &src->swap_readahead_info,
	       sizeof(dest->swap_readahead_info));
#endif
#ifndef CONFIG_MMU
	dest->vm_region = src->vm_region;
#endif
#ifdef CONFIG_NUMA
	dest->vm_policy = src->vm_policy;
#endif
#ifdef __HAVE_PFNMAP_TRACKING
	dest->pfnmap_track_ctx = NULL;
#endif
}
```

Every member named in the catalog table appears here except the lock fields, and this is exactly the list the WARNING comment on the struct requires a new member to be added to. The [`shared`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) block is copied under `data_race()` because, according to the comment "src->shared.rb may be modified concurrently when called from dup_mmap(), but the clone will reinitialize it", the copy is a throwaway that the caller overwrites. The [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054) is set to NULL rather than shared. The lock and reverse-map fields are re-initialized by the public wrapper instead:

```c
/* mm/vma_init.c:121 */
struct vm_area_struct *vm_area_dup(struct vm_area_struct *orig)
{
	struct vm_area_struct *new = kmem_cache_alloc(vm_area_cachep, GFP_KERNEL);

	if (!new)
		return NULL;

	ASSERT_EXCLUSIVE_WRITER(orig->vm_flags);
	ASSERT_EXCLUSIVE_WRITER(orig->vm_file);
	vm_area_init_from(orig, new);

	if (vma_pfnmap_track_ctx_dup(orig, new)) {
		kmem_cache_free(vm_area_cachep, new);
		return NULL;
	}
	vma_lock_init(new, true);
	INIT_LIST_HEAD(&new->anon_vma_chain);
	vma_numab_state_init(new);
	dup_anon_vma_name(orig, new);

	return new;
}
```

[`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121) runs [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41), then takes a fresh reference on any [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054), re-initializes the per-VMA lock with [`vma_lock_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L150) (with `reset_refcnt` true, so the clone starts detached), re-initializes the empty [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list, resets [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989), and takes a reference on the [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) string. Three callers use it for three different reasons. [`dup_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1732) clones every parent VMA into the child during `fork` (the loop shown in the [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) section, invoked from `dup_mm()` at [`kernel/fork.c:1531`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1531)), [`__split_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L497) clones a VMA so one mapping can become two (shown in the [`vma_set_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620) section), and [`copy_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1844) clones a VMA to its `mremap` destination:

```c
/* mm/vma.c:1904 */
		new_vma = vm_area_dup(vma);
		if (!new_vma)
			goto out;
		vma_set_range(new_vma, addr, addr + len, pgoff);
		if (vma_dup_policy(vma, new_vma))
			goto out_free_vma;
		if (anon_vma_clone(new_vma, vma, VMA_OP_REMAP))
			goto out_free_mempol;
```

### __mmap_region orchestrates allocation, field fill, and insertion

Everything above comes together in the mapping path. [`do_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L335) calls [`mmap_region()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2818) at [`mm/mmap.c:559`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L559), which validates the flags and then hands over to the orchestrator:

```c
/* mm/vma.c:2818 */
unsigned long mmap_region(struct file *file, unsigned long addr,
			  unsigned long len, vm_flags_t vm_flags, unsigned long pgoff,
			  struct list_head *uf)
{
	unsigned long ret;
	bool writable_file_mapping = false;

	mmap_assert_write_locked(current->mm);

	/* Check to see if MDWE is applicable. */
	if (map_deny_write_exec(vm_flags, vm_flags))
		return -EACCES;

	/* Allow architectures to sanity-check the vm_flags. */
	if (!arch_validate_flags(vm_flags))
		return -EINVAL;

	/* Map writable and ensure this isn't a sealed memfd. */
	if (file && is_shared_maywrite_vm_flags(vm_flags)) {
		int error = mapping_map_writable(file->f_mapping);

		if (error)
			return error;
		writable_file_mapping = true;
	}

	ret = __mmap_region(file, addr, len, vm_flags, pgoff, uf);

	/* Clear our write mapping regardless of error. */
	if (writable_file_mapping)
		mapping_unmap_writable(file->f_mapping);

	validate_mm(current->mm);
	return ret;
}
```

[`__mmap_region()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2720) builds the mapping state and a [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880) on the stack, runs the `mmap_prepare` hook if the file has one, attempts a merge with the neighbors, and only allocates a fresh VMA when the merge fails:

```c
/* mm/vma.c:2720 */
static unsigned long __mmap_region(struct file *file, unsigned long addr,
		unsigned long len, vm_flags_t vm_flags, unsigned long pgoff,
		struct list_head *uf)
{
	struct mm_struct *mm = current->mm;
	struct vm_area_struct *vma = NULL;
	bool have_mmap_prepare = file && file->f_op->mmap_prepare;
	VMA_ITERATOR(vmi, mm, addr);
	MMAP_STATE(map, mm, &vmi, addr, len, pgoff, vm_flags, file);
	struct vm_area_desc desc = {
		.mm = mm,
		.file = file,
		.action = {
			.type = MMAP_NOTHING, /* Default to no further action. */
		},
	};
	bool allocated_new = false;
	int error;

	map.check_ksm_early = can_set_ksm_flags_early(&map);

	error = __mmap_setup(&map, &desc, uf);
	if (!error && have_mmap_prepare)
		error = call_mmap_prepare(&map, &desc);
	if (error)
		goto abort_munmap;

	if (map.check_ksm_early)
		update_ksm_flags(&map);

	/* Attempt to merge with adjacent VMAs... */
	if (map.prev || map.next) {
		VMG_MMAP_STATE(vmg, &map, /* vma = */ NULL);

		vma = vma_merge_new_range(&vmg);
	}

	/* ...but if we can't, allocate a new VMA. */
	if (!vma) {
		error = __mmap_new_vma(&map, &vma);
		if (error)
			goto unacct_error;
		allocated_new = true;
	}

	if (have_mmap_prepare)
		set_vma_user_defined_fields(vma, &map);

	__mmap_complete(&map, vma);

	if (have_mmap_prepare && allocated_new) {
		error = call_action_complete(&map, &desc, vma);

		if (error)
			return error;
	}

	return addr;
	...
}
```

The new-VMA leg is [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506), which performs the field writes this page has catalogued in order, allocation, range and offset, flags, protection, backing store, then attachment and linkage:

```c
/* mm/vma.c:2506 */
static int __mmap_new_vma(struct mmap_state *map, struct vm_area_struct **vmap)
{
	struct vma_iterator *vmi = map->vmi;
	int error = 0;
	struct vm_area_struct *vma;

	/*
	 * Determine the object being mapped and call the appropriate
	 * specific mapper. the address has already been validated, but
	 * not unmapped, but the maps are removed from the list.
	 */
	vma = vm_area_alloc(map->mm);
	if (!vma)
		return -ENOMEM;

	vma_iter_config(vmi, map->addr, map->end);
	vma_set_range(vma, map->addr, map->end, map->pgoff);
	vm_flags_init(vma, map->vm_flags);
	vma->vm_page_prot = map->page_prot;

	if (vma_iter_prealloc(vmi, vma)) {
		error = -ENOMEM;
		goto free_vma;
	}

	if (map->file)
		error = __mmap_new_file_vma(map, vma);
	else if (map->vm_flags & VM_SHARED)
		error = shmem_zero_setup(vma);
	else
		vma_set_anonymous(vma);

	if (error)
		goto free_iter_vma;

	if (!map->check_ksm_early) {
		update_ksm_flags(map);
		vm_flags_init(vma, map->vm_flags);
	}

#ifdef CONFIG_SPARC64
	/* TODO: Fix SPARC ADI! */
	WARN_ON_ONCE(!arch_validate_flags(map->vm_flags));
#endif

	/* Lock the VMA since it is modified after insertion into VMA tree */
	vma_start_write(vma);
	vma_iter_store_new(vmi, vma);
	map->mm->map_count++;
	vma_link_file(vma, map->hold_file_rmap_lock);

	/*
	 * vma_merge_new_range() calls khugepaged_enter_vma() too, the below
	 * call covers the non-merge case.
	 */
	if (!vma_is_anonymous(vma))
		khugepaged_enter_vma(vma, map->vm_flags);
	*vmap = vma;
	return 0;

free_iter_vma:
	vma_iter_free(vmi);
free_vma:
	vm_area_free(vma);
	return error;
}
```

The three-way branch is where the mapping kinds diverge at the [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) and [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) fields. A file mapping goes through [`__mmap_new_file_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2455), a shared anonymous mapping gets a shmem file from [`shmem_zero_setup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/shmem.c#L5932), and a private anonymous mapping is stamped with [`vma_set_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230). The file leg assigns [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976), takes the file reference, and invokes the filesystem's legacy `mmap` operation through [`mmap_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L165):

```c
/* mm/vma.c:2455 */
static int __mmap_new_file_vma(struct mmap_state *map,
			       struct vm_area_struct *vma)
{
	struct vma_iterator *vmi = map->vmi;
	int error;

	vma->vm_file = map->file;
	if (!map->file_doesnt_need_get)
		get_file(map->file);

	if (!map->file->f_op->mmap)
		return 0;

	error = mmap_file(vma->vm_file, vma);
	if (error) {
		UNMAP_STATE(unmap, vmi, vma, vma->vm_start, vma->vm_end,
			    map->prev, map->next);
		fput(vma->vm_file);
		vma->vm_file = NULL;

		vma_iter_set(vmi, vma->vm_end);
		/* Undo any partial mapping done by a device driver. */
		unmap_region(&unmap);
		return error;
	}

	/* Drivers cannot alter the address of the VMA. */
	WARN_ON_ONCE(map->addr != vma->vm_start);
	/*
	 * Drivers should not permit writability when previously it was
	 * disallowed.
	 */
	VM_WARN_ON_ONCE(map->vm_flags != vma->vm_flags &&
			!(map->vm_flags & VM_MAYWRITE) &&
			(vma->vm_flags & VM_MAYWRITE));

	map->file = vma->vm_file;
	map->vm_flags = vma->vm_flags;

	return 0;
}
```

The driver's `mmap` handler is what installs [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971), and the WARN after the call enforces that a driver may change flags and file but never [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919). The generic page-cache handler is the plain-filesystem case:

```c
/* mm/filemap.c:3982 */
const struct vm_operations_struct generic_file_vm_ops = {
	.fault		= filemap_fault,
	.map_pages	= filemap_map_pages,
	.page_mkwrite	= filemap_page_mkwrite,
};

/* This is used for a general mmap of a disk file */

int generic_file_mmap(struct file *file, struct vm_area_struct *vma)
{
	struct address_space *mapping = file->f_mapping;

	if (!mapping->a_ops->read_folio)
		return -ENOEXEC;
	file_accessed(file);
	vma->vm_ops = &generic_file_vm_ops;
	return 0;
}
```

[`generic_file_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L3990) sets `vma->vm_ops = &generic_file_vm_ops`, wiring the range's faults to the page-cache fault handler.

### struct vm_area_desc carries the mmap_prepare view of a VMA

The newer `mmap_prepare` file operation reaches the same field values without ever letting the filesystem touch the VMA. The hook receives a [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880), a stack-allocated description that partitions the same information into immutable, mutable, and write-only groups:

```c
/* include/linux/mm_types.h:873 */
/*
 * Describes a VMA that is about to be mmap()'ed. Drivers may choose to
 * manipulate mutable fields which will cause those fields to be updated in the
 * resultant VMA.
 *
 * Helper functions are not required for manipulating any field.
 */
struct vm_area_desc {
	/* Immutable state. */
	const struct mm_struct *const mm;
	struct file *const file; /* May vary from vm_file in stacked callers. */
	unsigned long start;
	unsigned long end;

	/* Mutable fields. Populated with initial state. */
	pgoff_t pgoff;
	struct file *vm_file;
	vma_flags_t vma_flags;
	pgprot_t page_prot;

	/* Write-only fields. */
	const struct vm_operations_struct *vm_ops;
	void *private_data;

	/* Take further action? */
	struct mmap_action action;
};
```

The trailing [`struct mmap_action`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L823) lets the hook request a follow-up the core performs on its behalf, selected by [`enum mmap_action_type`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L813):

```c
/* include/linux/mm_types.h:812 */
/* What action should be taken after an .mmap_prepare call is complete? */
enum mmap_action_type {
	MMAP_NOTHING,		/* Mapping is complete, no further action. */
	MMAP_REMAP_PFN,		/* Remap PFN range. */
	MMAP_IO_REMAP_PFN,	/* I/O remap PFN range. */
};

/*
 * Describes an action an mmap_prepare hook can instruct to be taken to complete
 * the mapping of a VMA. Specified in vm_area_desc.
 */
struct mmap_action {
	union {
		/* Remap range. */
		struct {
			unsigned long start;
			unsigned long start_pfn;
			unsigned long size;
			pgprot_t pgprot;
		} remap;
	};
	enum mmap_action_type type;
	...
	int (*success_hook)(const struct vm_area_struct *vma);
	...
	int (*error_hook)(int err);

	/*
	 * This should be set in rare instances where the operation required
	 * that the rmap should not be able to access the VMA until
	 * completely set up.
	 */
	bool hide_from_rmap_until_complete :1;
};
```

The descriptor's mutable fields are seeded from the mapping state by [`set_desc_from_map()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2367) inside [`__mmap_setup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2393), the hook is invoked through [`vfs_mmap_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L2073), and [`call_mmap_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2638) copies the results back:

```c
/* include/linux/fs.h:2073 */
static inline int vfs_mmap_prepare(struct file *file, struct vm_area_desc *desc)
{
	return file->f_op->mmap_prepare(desc);
}
...
/* mm/vma.c:2638 */
static int call_mmap_prepare(struct mmap_state *map,
		struct vm_area_desc *desc)
{
	int err;

	/* Invoke the hook. */
	err = vfs_mmap_prepare(map->file, desc);
	if (err)
		return err;

	call_action_prepare(map, desc);

	/* Update fields permitted to be changed. */
	map->pgoff = desc->pgoff;
	if (desc->vm_file != map->file) {
		map->file_doesnt_need_get = true;
		map->file = desc->vm_file;
	}
	map->vma_flags = desc->vma_flags;
	map->page_prot = desc->page_prot;
	/* User-defined fields. */
	map->vm_ops = desc->vm_ops;
	map->vm_private_data = desc->private_data;

	return 0;
}
```

After the merge-or-allocate step, [`set_vma_user_defined_fields()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2665) stamps the two write-only values onto the real VMA:

```c
/* mm/vma.c:2665 */
static void set_vma_user_defined_fields(struct vm_area_struct *vma,
		struct mmap_state *map)
{
	if (map->vm_ops)
		vma->vm_ops = map->vm_ops;
	vma->vm_private_data = map->vm_private_data;
}
```

A filesystem-side hook fills the descriptor exactly the way [`generic_file_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L3990) fills the VMA; [`generic_file_mmap_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L4001) writes `desc->vm_ops` instead of `vma->vm_ops`, and ramfs (an in-tree memory filesystem) wires it into its file operations at [`fs/ramfs/file-mmu.c:44`](https://elixir.bootlin.com/linux/v7.0/source/fs/ramfs/file-mmu.c#L44):

```c
/* mm/filemap.c:4001 */
int generic_file_mmap_prepare(struct vm_area_desc *desc)
{
	struct file *file = desc->file;
	struct address_space *mapping = file->f_mapping;

	if (!mapping->a_ops->read_folio)
		return -ENOEXEC;
	file_accessed(file);
	desc->vm_ops = &generic_file_vm_ops;
	return 0;
}
```

### sysctl_max_map_count bounds how many VMAs one address space may hold

Each [`struct vm_area_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L913) counts against a per-address-space limit. The owner's [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) tracks the running count (incremented by [`vma_link()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1824) and [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506), decremented by [`vms_complete_munmap_vmas()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1311)), and [`sysctl_max_map_count`](https://elixir.bootlin.com/linux/v7.0/source/mm/util.c#L755) is the ceiling it is compared against:

```c
/* include/linux/mm.h:194 */
/*
 * Default maximum number of active map areas, this limits the number of vmas
 * per mm struct. Users can overwrite this number by sysctl but there is a
 * problem.
 *
 * When a program's coredump is generated as ELF format, a section is created
 * per a vma. In ELF, the number of sections is represented in unsigned short.
 * This means the number of sections should be smaller than 65535 at coredump.
 * Because the kernel adds some informative sections to a image of program at
 * generating coredump, we need some margin. The number of extra sections is
 * 1-3 now and depends on arch. We use "5" as safe margin, here.
 *
 * ELF extended numbering allows more than 65535 sections, so 16-bit bound is
 * not a hard limit any more. Although some userspace tools can be surprised by
 * that.
 */
#define MAPCOUNT_ELF_CORE_MARGIN	(5)
#define DEFAULT_MAX_MAP_COUNT	(USHRT_MAX - MAPCOUNT_ELF_CORE_MARGIN)

extern int sysctl_max_map_count;
...
/* mm/util.c:755 */
int sysctl_max_map_count __read_mostly = DEFAULT_MAX_MAP_COUNT;
```

[`DEFAULT_MAX_MAP_COUNT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L209) is `USHRT_MAX - 5` = 65530, where the [`MAPCOUNT_ELF_CORE_MARGIN`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L208) of 5 reserves headroom for the extra ELF sections a coredump adds. The value is runtime-tunable as `vm.max_map_count` through the sysctl table registered by [`mmap_init()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1568):

```c
/* mm/mmap.c:1520 */
static const struct ctl_table mmap_table[] = {
		{
				.procname       = "max_map_count",
				.data           = &sysctl_max_map_count,
				.maxlen         = sizeof(sysctl_max_map_count),
				.mode           = 0644,
				.proc_handler   = proc_dointvec_minmax,
				.extra1         = SYSCTL_ZERO,
		},
```

Five paths enforce the ceiling, each at the point where it would create VMAs. [`do_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L335) refuses a new mapping, and [`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866) refuses a brk extension, when the count is already above the limit:

```c
/* mm/mmap.c:377 */
	/* Too many mappings? */
	if (mm->map_count > sysctl_max_map_count)
		return -ENOMEM;
...
/* mm/vma.c:2880 */
	if (mm->map_count > sysctl_max_map_count)
		return -ENOMEM;
```

[`split_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L590) refuses a split that would add a VMA at the limit, while its inner [`__split_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L497) skips the check for callers that already performed it (according to the comment above it, "__split_vma() bypasses sysctl_max_map_count checking. We use this where it has already been checked or doesn't make sense to fail"):

```c
/* mm/vma.c:586 */
/*
 * Split a vma into two pieces at address 'addr', a new vma is allocated
 * either for the first part or the tail.
 */
static int split_vma(struct vma_iterator *vmi, struct vm_area_struct *vma,
		     unsigned long addr, int new_below)
{
	if (vma->vm_mm->map_count >= sysctl_max_map_count)
		return -ENOMEM;

	return __split_vma(vmi, vma, addr, new_below);
}
```

[`vms_gather_munmap_vmas()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1379) applies the same bound to the split that a partial `munmap` needs, but only when both ends of the range split (according to the comment, it will "let map_count go just above its limit temporarily, to help free resources as expected"):

```c
/* mm/vma.c:1391 */
		/*
		 * Make sure that map_count on return from munmap() will
		 * not exceed its limit; but let map_count go just above
		 * its limit temporarily, to help free resources as expected.
		 */
		if (vms->end < vms->vma->vm_end &&
		    vms->vma->vm_mm->map_count >= sysctl_max_map_count) {
			error = -ENOMEM;
			goto map_count_exceeded;
		}
```

The `mremap` paths pre-check with margins because one move can split VMAs at both the source and the destination; [`mm/mremap.c:1047`](https://elixir.bootlin.com/linux/v7.0/source/mm/mremap.c#L1047) requires `map_count < sysctl_max_map_count - 3` before a move that "may split one vma into three", and [`mm/mremap.c:1820`](https://elixir.bootlin.com/linux/v7.0/source/mm/mremap.c#L1820) requires `map_count + 2 < sysctl_max_map_count - 3` for the worst case where both the old and new ranges split in three:

```c
/* mm/mremap.c:1043 */
	/*
	 * We'd prefer to avoid failure later on in do_munmap:
	 * which may split one vma into three before unmapping.
	 */
	if (current->mm->map_count >= sysctl_max_map_count - 3)
		return -ENOMEM;
...
/* mm/mremap.c:1820 */
	if ((current->mm->map_count + 2) >= sysctl_max_map_count - 3)
		return -ENOMEM;
```

### Field-keyed predicates classify a VMA without extra state

A family of small helpers derives a VMA's identity purely from the fields this page has catalogued, so no dedicated "kind" member exists. The heap and stack tests compare the range against the owner's brk and stack markers:

```c
/* include/linux/mm.h:1240 */
/*
 * Indicate if the VMA is a heap for the given task; for
 * /proc/PID/maps that is the heap of the main task.
 */
static inline bool vma_is_initial_heap(const struct vm_area_struct *vma)
{
	return vma->vm_start < vma->vm_mm->brk &&
		vma->vm_end > vma->vm_mm->start_brk;
}

/*
 * Indicate if the VMA is a stack for the given task; for
 * /proc/PID/maps that is the stack of the main task.
 */
static inline bool vma_is_initial_stack(const struct vm_area_struct *vma)
{
	/*
	 * We make no effort to guess what a given thread considers to be
	 * its "stack".  It's not even well-defined for programs written
	 * languages like Go.
	 */
	return vma->vm_start <= vma->vm_mm->start_stack &&
		vma->vm_end >= vma->vm_mm->start_stack;
}
```

Both feed [`get_vma_name()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L381) in the `/proc/PID/maps` code, which prints `[heap]` and `[stack]` from them:

```c
/* fs/proc/task_mmu.c:425 */
	if (vma_is_initial_heap(vma)) {
		*name = "[heap]";
		return;
	}

	if (vma_is_initial_stack(vma)) {
		*name = "[stack]";
		return;
	}
```

[`vma_is_temporary_stack()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1265) recognizes the transient stack that `execve` builds before relocating it, from the growth flags plus the `VM_STACK_INCOMPLETE_SETUP` marker bits:

```c
/* include/linux/mm.h:1265 */
static inline bool vma_is_temporary_stack(const struct vm_area_struct *vma)
{
	int maybe_stack = vma->vm_flags & (VM_GROWSDOWN | VM_GROWSUP);

	if (!maybe_stack)
		return false;

	if ((vma->vm_flags & VM_STACK_INCOMPLETE_SETUP) ==
						VM_STACK_INCOMPLETE_SETUP)
		return true;

	return false;
}
```

The rmap walker uses it as its skip test when migrating stack pages during `execve`, through [`invalid_migration_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L2365):

```c
/* mm/rmap.c:2365 */
static bool invalid_migration_vma(struct vm_area_struct *vma, void *arg)
{
	return vma_is_temporary_stack(vma);
}
```

[`vma_is_foreign()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1279) compares [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) against the current task:

```c
/* include/linux/mm.h:1279 */
static inline bool vma_is_foreign(const struct vm_area_struct *vma)
{
	if (!current->mm)
		return true;

	if (current->mm != vma->vm_mm)
		return true;

	return false;
}
```

The x86-64 protection-key check [`arch_vma_access_permitted()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L267) uses it to bypass pkey enforcement for a VMA that belongs to another process, since PKRU is a per-thread register that only governs the current task's own address space:

```c
/* arch/x86/include/asm/mmu_context.h:267 */
static inline bool arch_vma_access_permitted(struct vm_area_struct *vma,
		bool write, bool execute, bool foreign)
{
	/* pkeys never affect instruction fetches */
	if (execute)
		return true;
	/* allow access if the VMA is not one from this process */
	if (foreign || vma_is_foreign(vma))
		return true;
	return __pkru_allows_pkey(vma_pkey(vma), write);
}
```

[`vma_is_accessible()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1290) tests the [`VM_ACCESS_FLAGS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L545) mask (`VM_READ | VM_WRITE | VM_EXEC`), and its NUMA-scan usage appears in the [`task_numa_work()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3363) excerpt above, where a `PROT_NONE` range is skipped:

```c
/* include/linux/mm.h:1290 */
static inline bool vma_is_accessible(const struct vm_area_struct *vma)
{
	return vma->vm_flags & VM_ACCESS_FLAGS;
}
```

Together with [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235) (keyed on [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971)), [`vma_is_shared_maywrite()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1306) (keyed on two flag bits), and [`vma_is_special_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1489) (keyed on [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) plus [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971)), these predicates make the struct's fields the single source of truth for what kind of mapping a VMA is.

### mm_mt owns every VMA and mmap_lock plus vm_refcnt serialize access

A VMA does not stand alone; its owner is the [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) maple tree in the [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) that [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) points back at. The tree type is a three-member root whose RCU-friendly node store enables the lockless lookup in [`lock_vma_under_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296):

```c
/* include/linux/maple_tree.h:222 */
struct maple_tree {
	union {
		spinlock_t		ma_lock;
#ifdef CONFIG_LOCKDEP
		struct lockdep_map	*ma_external_lock;
#endif
	};
	unsigned int	ma_flags;
	void __rcu      *ma_root;
};
```

The tree stores each VMA under its `[vm_start, vm_end)` range, so a lookup by address returns the covering VMA, and insertion is done by [`vma_iter_store_new()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610) while the VMA is write-locked. The lifetime rules that follow from this ownership are compact. A VMA is created by [`vm_area_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28) from `vm_area_cachep`, published into [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) under the owner's [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) held for write (its [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) going 0 to 1 in [`vma_mark_attached()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L443)), counted in [`map_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1179) against [`sysctl_max_map_count`](https://elixir.bootlin.com/linux/v7.0/source/mm/util.c#L755), and freed by [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) after it is removed from the tree, detached by [`vma_mark_detached()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L452), released by [`remove_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L463), and left for an RCU grace period by the `SLAB_TYPESAFE_BY_RCU` cache. Two locks serialize access. The [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) reader-writer semaphore covers structural changes to the whole tree (a writer holds it to insert, split, merge, or remove VMAs; a reader holds it to walk them), and the per-VMA [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) plus [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) pair lets a fault take a read lock on one VMA under RCU through [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) without the shared semaphore. A VMA field that a lockless reader may observe is one of the three the type comment marks RCU-readable ([`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958), [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030)); every other field requires the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) or a stable per-VMA reference obtained through the read lock.







