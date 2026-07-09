# struct vm_area_struct

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

[`struct vm_area_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L913) (the VMA) is the kernel's record of one contiguous range of a process address space that shares a single set of properties, the half-open interval `[vm_start, vm_end)` together with its permissions, its backing store, and the operations that service its page faults. According to the comment on the type, "A VM area is any part of the process virtual memory space that has a special rule for the page-fault handlers (ie a shared library, the executable area etc)". Every VMA belongs to exactly one address space, reached through its [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) back-pointer to the owning [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123), and that address space stores every one of its VMAs as a slot in the [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) maple tree keyed by the address range. A file-backed VMA names the mapped file in [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) and the file offset in [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974), and it links itself into that file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) interval tree through the [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) node; an anonymous VMA has a NULL [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) and instead links to a [`struct anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) through [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) and [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) for reverse mapping. The [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) pointer selects the [`struct vm_operations_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L749) that handles faults for the range, and a NULL [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) is the marker for an anonymous mapping.

Access to a VMA is governed by two locks. The [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) reader-writer semaphore on the owning [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) serializes the whole tree, while the per-VMA [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) reference count (paired with the [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) sequence stamp) lets a page fault take a lightweight read lock on a single VMA under RCU without touching the shared semaphore. According to the comment on the type, "Only explicitly marked struct members may be accessed by RCU readers before getting a stable reference", and only [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958), and [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) carry that marking.

```
    struct vm_area_struct: the VMA and its outward pointers
    ────────────────────────────────────────────────────────

    struct mm_struct  (the owner)
    ┌────────────────────────────┐
    │ mm_mt : maple tree of VMAs │
    └─────────────┬──────────────┘
                  │ one slot per VMA, keyed by [vm_start, vm_end)
                  ▼
    ┌─────────────┬────────────────────┐
    │ struct vm_area_struct            │
    │   vm_start .. vm_end    (range)  │
    │   vm_flags / flags      (bitmap) │
    │   vm_page_prot          (PTE)    │
    │   vm_refcnt vm_lock_seq (locks)  │
    │                                  │
    │   vm_mm ─────────────────────────┼──▶ struct mm_struct  (owner)
    │   vm_ops ────────────────────────┼──▶ struct vm_operations_struct
    │   anon_vma ──────────────────────┼──▶ struct anon_vma
    │   vm_file ───────────────────────┼──▶ struct file
    │   shared.rb ─────────────────────┼──▶ address_space.i_mmap (rb)
    │   vm_private_data ───────────────┼──▶ driver-owned state
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
               after the last per-VMA reference and detach
```

## SUMMARY

A VMA is allocated from the `vm_area_cachep` slab by [`vm_area_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28), which runs [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) to zero the object, set [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), point [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) at the shared [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20), and initialize the [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list. The mapping path fills in the range and file offset with [`vma_set_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620), sets the flag bitmap with [`vm_flags_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L919), and for a file mapping assigns [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) and lets the file's `mmap` or `mmap_prepare` operation install [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971), as [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) does inside [`mmap_region()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2818). The finished VMA is inserted into the owner's [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) with [`vma_iter_store_new()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610) and, when file-backed, linked into the file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree with [`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810). A duplicate for `fork` is produced by [`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121), which copies each member through [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41); the type comment warns that this copy list is the reason new members must be added there.

The flag bitmap is read through the [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) view and changed only through the [`vm_flags_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L958), [`vm_flags_clear()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L965), and [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987) accessors, which take the per-VMA write lock before writing. Whether a VMA is anonymous is derived from [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) by [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235), and [`vma_set_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230) writes the NULL marker. A page fault reaches a VMA without the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) through [`lock_vma_under_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296), whose core is [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212): it reads [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958), takes a bounded increment on [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030), and re-checks [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), the three members the type comment marks RCU-readable. The [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) pointer is populated lazily by [`__anon_vma_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185) on the first anonymous fault into the range, driven from [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217). A VMA is released by [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) back to the slab once it is detached and its last per-VMA reference is gone.

## SPECIFICATIONS

(none; [`struct vm_area_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L913) is a Linux kernel internal construct)

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

### Referenced types

- [`'\<struct mm_struct\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123): the owning address space reached through [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) and holding the [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) tree
- [`'\<struct vm_operations_struct\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L749): the function pointer struct selected by [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971)
- [`'\<struct anon_vma\>':'include/linux/rmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) / [`'\<struct anon_vma_chain\>':'include/linux/rmap.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83): the reverse-mapping root and the chain node linking a VMA to it
- [`'\<struct file\>':'include/linux/fs.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1259) / [`'\<struct address_space\>':'include/linux/fs.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L470): the mapped file and its page cache, whose [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree holds the [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) node
- [`'\<struct mempolicy\>':'include/linux/mempolicy.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mempolicy.h#L47): the NUMA policy pointed at by [`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986)
- [`'\<pgprot_t\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293): the x86-64 protection-bit type held in [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930)
- [`'\<struct maple_tree\>':'include/linux/maple_tree.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/maple_tree.h#L222): the range-keyed store that [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) is an instance of

### Allocation, init, and free (vma_init.c)

- [`'\<vma_state_init\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L14): creates the `vm_area_cachep` slab with the [`vm_freeptr`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L922) free-pointer offset
- [`'\<vm_area_alloc\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28): allocates one VMA and runs [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909)
- [`'\<vm_area_dup\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121): duplicates a VMA for `fork` through [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41)
- [`'\<vm_area_init_from\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41): member-by-member copy the type comment warns must track new members
- [`'\<vm_area_free\>':'mm/vma_init.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144): returns a detached VMA to the slab
- [`'\<vma_init\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909): zeroes a VMA and points [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) at [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20)
- [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20): the empty operations struct a fresh non-anonymous VMA points at

### Field accessors (mm.h, internal.h, mmap_lock.c)

- [`'\<vma_set_range\>':'mm/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620): writes [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919), [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920), and [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) together
- [`'\<vm_flags_init\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L919): overwrites the flag bitmap without locking (pre-tree use)
- [`'\<vm_flags_set\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L958) / [`'\<vm_flags_clear\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L965) / [`'\<vm_flags_mod\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987): OR, AND-NOT, and combined flag edits under the per-VMA write lock
- [`'\<vm_flags_reset\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L932): full overwrite that asserts the write lock is already held
- [`'\<vma_flags_overwrite_word\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1070) / [`'\<vma_flags_set_word\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1091) / [`'\<vma_flags_clear_word\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1099): the low-level bitmap writers the accessors call
- [`'\<vma_is_anonymous\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235) / [`'\<vma_set_anonymous\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230): read and write the NULL-[`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) anonymous marker
- [`'\<vma_start_read\>':'mm/mmap_lock.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) / [`'\<lock_vma_under_rcu\>':'mm/mmap_lock.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296): take a per-VMA read lock under RCU for the fault path
- [`'\<vma_start_write\>':'include/linux/mmap_lock.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L298): mark a VMA write-locked before its fields change

### Setters in the mapping path (vma.c, rmap.c, filemap.c)

- [`'\<mmap_region\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2818) / [`'\<__mmap_region\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2720): create a mapping, allocating or merging a VMA
- [`'\<__mmap_new_vma\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) / [`'\<__mmap_new_file_vma\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2455): fill a freshly allocated VMA and drive the file `mmap` operation
- [`'\<call_mmap_prepare\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2638) / [`'\<set_vma_user_defined_fields\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2665): the `mmap_prepare` path that copies [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) and [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) onto the VMA
- [`'\<generic_file_mmap\>':'mm/filemap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L3990) / [`'\<generic_file_mmap_prepare\>':'mm/filemap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L4001): a filesystem `mmap`/`mmap_prepare` that installs the page-cache [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971)
- [`'\<vma_link_file\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810) / [`'\<__vma_link_file\>':'mm/vma.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L227): insert the [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) node into the file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree
- [`'\<vma_interval_tree_insert\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3786): the interval-tree primitive keyed on [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974)
- [`'\<__anon_vma_prepare\>':'mm/rmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185): allocate or reuse an [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) and attach it to the VMA
- [`'\<do_anonymous_page\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217) / [`'\<__vmf_anon_prepare\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3723): the anonymous fault that triggers [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) attachment
- [`'\<vma_set_page_prot\>':'mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L81): recompute [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) from the current flags
- [`'\<vma_replace_policy\>':'mm/mempolicy.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L1009) / [`'\<vma_dup_policy\>':'mm/mempolicy.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L2802): set and duplicate [`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986)
- [`'\<task_numa_work\>':'kernel/sched/fair.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3363): lazily allocates [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989) during a NUMA scan
- [`'\<swap_update_readahead\>':'mm/swap_state.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/swap_state.c#L440): updates the [`swap_readahead_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L980) window on swap-in

### Hard limits and layout markers

- [`VM_REFCNT_EXCLUDE_READERS_BIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L764) / [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765): bit 30 of [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) that excludes new readers, value `1U << 30`
- [`VM_REFCNT_LIMIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L766): the ceiling `VM_REFCNT_EXCLUDE_READERS_FLAG - 1` a reader increment may not cross
- [`NUM_VMA_FLAG_BITS`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L866): width of the [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L940) bitmap, `BITS_PER_LONG` (64 on x86-64)

## KERNEL DOCUMENTATION

- [`Documentation/mm/process_addrs.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/process_addrs.rst): the address-space locking model, the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196), and per-VMA locking over the VMA tree
- [`Documentation/core-api/maple_tree.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/core-api/maple_tree.rst): the maple tree that [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) uses to store every VMA by range

## OTHER SOURCES

- [commit d4af56c5c7c6 ("mm: start tracking VMAs with maple tree")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=d4af56c5c7c6781ca6ca8075e2cf5bc119ed33d1)
- [commit 5e31275cc997 ("mm: add per-VMA lock and helper functions to control it")](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=5e31275cc997f8ec5d9e8d65fe9840ebed89db19)

## DETAILS

### struct vm_area_struct is defined in mm_types.h with config-gated regions

The full definition is a single structure whose members are ordered by how a page fault reaches them, opening with the address range that the maple tree keys on and closing with optional per-feature pointers, the whole thing wrapped in `__randomize_layout`:

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

On an x86-64 build with `CONFIG_MMU` and `CONFIG_PER_VMA_LOCK` on, the `#ifndef CONFIG_MMU` member [`vm_region`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L983) is compiled out, and the `CONFIG_PER_VMA_LOCK`, `CONFIG_SWAP`, `CONFIG_NUMA`, `CONFIG_NUMA_BALANCING`, `CONFIG_ANON_VMA_NAME`, and `__HAVE_PFNMAP_TRACKING` members are all present. The [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) member carries `____cacheline_aligned_in_smp`, so it starts a fresh cache line and the reader-increment path does not contend with the range and flag fields above it, which are read far more than written. The type comment states two rules a reader has to honor. According to the comment "Only explicitly marked struct members may be accessed by RCU readers before getting a stable reference", only the three members annotated in the definition, [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) ("Unstable RCU readers are allowed to read this."), [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) ("Can be read unreliably (using READ_ONCE()) ... while holding nothing (except RCU ...)"), and [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) ("NOTE: Unstable RCU readers are allowed to read this."), may be touched by a lockless reader before it has pinned the VMA; every other member requires either the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) or a stable per-VMA reference. According to the comment "WARNING: when adding new members, please update vm_area_init_from() to copy them during vm_area_struct content duplication", the duplication routine [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41) is the maintenance point that pairs with the field list here.

The members group by role, and this catalog names each field, its type, and what it records:

| Field | Type | Role |
|---|---|---|
| [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919) / [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920) (union with [`vm_freeptr`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L922)) | `unsigned long` / `freeptr_t` | the half-open range `[vm_start, vm_end)`; while free in the slab the same bytes hold the SLUB free pointer |
| [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) | `struct mm_struct *` | back-pointer to the owning address space (RCU-readable) |
| [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) | `pgprot_t` | the PTE protection bits applied to pages faulted into the range |
| [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) / [`flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L940) (union) | `const vm_flags_t` / `vma_flags_t` | the VMA property bitmap (`VM_READ`, `VM_WRITE`, `VM_SHARED`, ...), read through the const view and written through helpers |
| [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) | `unsigned int` | the owner write-lock generation this VMA was last write-locked at (RCU-readable) |
| [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) | `refcount_t` | attachment state plus per-VMA read-lock count (RCU-readable) |
| [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) | `struct list_head` | list of [`struct anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83) links to every `anon_vma` this VMA belongs to |
| [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) | `struct anon_vma *` | the reverse-map root for anonymous pages, attached lazily |
| [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) | `const struct vm_operations_struct *` | the fault/open/close operations; NULL marks an anonymous VMA |
| [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) | `unsigned long` | offset into [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) in `PAGE_SIZE` units (or the PFN for an anonymous VMA) |
| [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) | `struct file *` | the mapped file, NULL for anonymous, stack, and brk VMAs |
| [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) | `void *` | per-mapping state owned by the driver or filesystem behind [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) |
| [`swap_readahead_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L980) | `atomic_long_t` | the per-VMA swap readahead window (last fault address, window, hits) |
| [`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986) | `struct mempolicy *` | the NUMA allocation policy for pages in the range |
| [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989) | `struct vma_numab_state *` | NUMA-balancing scan bookkeeping, allocated on first scan |
| [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) | `struct rb_node` (+ `rb_subtree_last`) | interval-tree node linking a file VMA into `address_space->i_mmap` |
| [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) | `struct anon_vma_name *` | the name assigned to an anonymous mapping, or NULL |
| [`vm_userfaultfd_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1052) | `struct vm_userfaultfd_ctx` | the userfaultfd context registered on the range, if any |
| [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054) | `struct pfnmap_track_ctx *` | refcounted tracking of a PFN-mapped range's cache attributes |

### The vm_start and vm_end union overlaps a slab free pointer

The first member is a union between the address range and a single free-list pointer:

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
```

While the VMA is live, [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919) and [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920) are the inclusive start and exclusive end of the mapped range, and the whole VMA occupies the maple-tree slot spanning exactly `[vm_start, vm_end)`. When the VMA is freed back to its slab, the same bytes are reused by SLUB as the free-list pointer [`vm_freeptr`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L922). This overlap is possible because [`vma_state_init()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L14) creates the slab with the free-pointer offset pinned to this union, so a freed object stores its free pointer where a live object stores its range:

```c
/* mm/vma_init.c:14 */
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

The `SLAB_TYPESAFE_BY_RCU` flag on this cache keeps lockless VMA lookup sound: a freed VMA object can be handed out again immediately, but the memory itself is not returned to the page allocator until an RCU grace period passes, so a reader that found a VMA under `rcu_read_lock()` can safely read the RCU-marked fields even if the VMA was concurrently freed and recycled, and then detects the recycle through the [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) and [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) re-checks in [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212).

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

[`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) is set once, at allocation, by [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909), and never changes for the life of the VMA. Fault, unmap, and reverse-map code all reach the owning [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) through it (for the page-table root, the resident-set counters, and the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196)). Because it is RCU-readable, [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) re-reads it after taking a reference and bails out if `vma->vm_mm != mm`, which is how the fault path detects a VMA that was freed and reattached to a different address space under it.

### vm_page_prot caches the page-table protection bits for the range

[`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) holds the [`pgprot_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293) protection bits (the `_PAGE_*` flags on x86-64) that the fault handlers stamp into every PTE they create for pages in this range. It is a cache derived from the VMA flags, recomputed by [`vma_set_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L81) whenever the flags change so that the fault path can install a PTE without re-deriving the protection each time:

```c
/* mm/mmap.c:81 */
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

According to the comment "remove_protection_ptes reads vma->vm_page_prot without mmap_lock", the write is a `WRITE_ONCE()` because a reader can observe [`vm_page_prot`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L930) without the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). When [`vma_wants_writenotify()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2085) reports that the VMA needs write-notification (for dirty tracking on a shared writable file mapping), the shared bit is dropped from the cached protection so that the first write faults and takes the `page_mkwrite` path.

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

Reading `vma->vm_flags` yields a `const` [`vm_flags_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L691) (an `unsigned long`), so code can test bits like `vma->vm_flags & VM_WRITE` directly but cannot assign to the field. Writes go through the accessor family named in the comment, which operate on the [`vma_flags_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L867) bitmap view. That bitmap type is declared next to the struct and is `BITS_PER_LONG` wide on x86-64:

```c
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

### vm_lock_seq stamps the VMA with the mm write-lock generation

The per-VMA lock is built from a sequence stamp and a reference count. The stamp records the owner's write-lock generation at which this VMA was last write-locked, and its access rules are spelled out in the field comment reproduced in the struct above. The value is compared against the owner's `mm_lock_seq`: a VMA is considered write-locked exactly when its [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) equals the current `mm->mm_lock_seq`, which is why write-locking a VMA is a single stamp assignment and why a bump of the owner's sequence at [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) write-unlock instantly marks every VMA unlocked at once. According to the comment, the counter "is explicitly allowed to overflow; sequence counter reuse can only lead to occasional unnecessary use of the slowpath", so the design tolerates wraparound by paying an occasional false-locked result that only costs a retry. A lockless reader is allowed to read this field, but only with `READ_ONCE()` and only as a pessimistic early check.

### vm_refcnt counts per-VMA read locks and encodes attachment state

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

[`VM_REFCNT_EXCLUDE_READERS_BIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L764) is bit 30, so [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765) is `1U << 30` and [`VM_REFCNT_LIMIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L766) is that value minus one. A reader increment in [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) is bounded by [`VM_REFCNT_LIMIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L766), so once a writer sets the exclude flag (pushing the count to or above `1U << 30`) the bounded increment fails and no new reader can join, which is how a writer guarantees it eventually sees the reader count drop to a state it can proceed from. This field carries `____cacheline_aligned_in_smp` in the definition so the atomic reader traffic stays off the first cache line.

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

[`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) points at the [`struct anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) that owns the interval tree of VMAs mapping the same anonymous pages, and [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) is the list head threading the [`struct anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83) links that connect this VMA to every `anon_vma` it participates in (its own and, after `fork`, its ancestors'). According to the comment, a private file VMA can appear in both the [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree and an `anon_vma` list once a copy-on-write has produced a private page, a shared VMA appears only in the [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree, and an anonymous, stack, or brk VMA appears only in an `anon_vma` list. The [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list is initialized empty by [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) and stays empty until the first anonymous fault attaches an `anon_vma`.

### vm_ops points at the operations struct for the mapping

The behavior of a VMA under a page fault is selected by its operations pointer:

```c
/* include/linux/mm_types.h:970 */
	/* Function pointers to deal with this struct. */
	const struct vm_operations_struct *vm_ops;
```

[`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) selects a [`struct vm_operations_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L749), whose function pointers the core mm calls to service the range:

```c
/* include/linux/mm.h:749 */
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
	...
	vm_fault_t (*fault)(struct vm_fault *vmf);
	vm_fault_t (*huge_fault)(struct vm_fault *vmf, unsigned int order);
	vm_fault_t (*map_pages)(struct vm_fault *vmf,
			pgoff_t start_pgoff, pgoff_t end_pgoff);
	...
};
```

The `fault` handler is invoked when a page in the range is accessed and no PTE resolves it, `map_pages` pre-populates PTEs around a fault, and `open`/`close` run when the VMA is split, merged, or torn down. A NULL [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) is the sole marker that a VMA is anonymous, so the core mm handles its faults with the built-in anonymous path rather than a driver callback. A freshly allocated VMA does not have a NULL pointer here; [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) points it at [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20), and the mapping path either replaces it with a real operations struct (file mapping) or explicitly clears it to NULL (anonymous mapping).

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

[`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) is the mapped [`struct file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L1259), and [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) is the offset (in page units) into that file at which the range starts, so the file page backing a virtual address `addr` is `vm_pgoff + ((addr - vm_start) >> PAGE_SHIFT)`. For an anonymous VMA [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) is NULL and [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) holds the starting PFN of the range instead (used by the anon-vma interval tree). Both are set together with the range by [`vma_set_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620), and [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) additionally takes a counted reference on the file that [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) (via the unmap path) later drops.

### vm_private_data carries per-mapping driver state

The third backing-store member is opaque to the core mm. [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) is a `void *` that the driver or filesystem behind [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) uses to hang per-mapping state, and its comment "was vm_pte (shared mem)" records that the slot was once used by System V shared memory. The core mm never dereferences it; it copies it on duplication and lets the owning subsystem interpret it. A `mmap_prepare` hook fills it through the [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880) it is handed, and [`set_vma_user_defined_fields()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2665) copies both it and [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) onto the finished VMA.

### swap_readahead_info records the per-VMA swap readahead window

Under `CONFIG_SWAP`, each VMA remembers how well swap readahead has been predicting its access pattern:

```c
/* include/linux/mm_types.h:979 */
#ifdef CONFIG_SWAP
	atomic_long_t swap_readahead_info;
#endif
```

[`swap_readahead_info`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L980) packs the last faulting address, the current readahead window size, and a hit counter into one `atomic_long_t`. On a swap-in, [`swap_update_readahead()`](https://elixir.bootlin.com/linux/v7.0/source/mm/swap_state.c#L440) recomputes the window and stores it back atomically:

```c
/* mm/swap_state.c:462 */
		atomic_long_set(&vma->swap_readahead_info,
				SWAP_RA_VAL(addr, win, hits));
```

The packed value is read by the VMA-based swap readahead code to decide how many neighboring swap slots to prefetch, growing the window on hits and shrinking it on misses. Because it is a single `atomic_long_t`, updates need no lock and the field is not protected by the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196).

### vm_policy holds the NUMA memory policy for the range

Under `CONFIG_NUMA`, a VMA can carry a memory policy that overrides the task default for allocations in its range:

```c
/* include/linux/mm_types.h:985 */
#ifdef CONFIG_NUMA
	struct mempolicy *vm_policy;	/* NUMA policy for the VMA */
#endif
```

[`vm_policy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L986) points at a [`struct mempolicy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mempolicy.h#L47) that `mbind()` installs. It is written by [`vma_replace_policy()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L1009), which asserts the write lock, offers the change to a driver `set_policy` hook, and then swaps the pointer under the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196):

```c
/* mm/mempolicy.c:1022 */
	if (vma->vm_ops && vma->vm_ops->set_policy) {
		err = vma->vm_ops->set_policy(vma, new);
		if (err)
			goto err_out;
	}

	old = vma->vm_policy;
	WRITE_ONCE(vma->vm_policy, new); /* protected by mmap_lock */
	mpol_put(old);
```

According to the comment "protected by mmap_lock", the swap is a `WRITE_ONCE()` under the write lock, and the old policy's reference is dropped afterward. On `fork`, [`vma_dup_policy()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mempolicy.c#L2802) deep-copies the policy into the child VMA so the two do not share a mutable [`struct mempolicy`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mempolicy.h#L47).

### numab_state tracks NUMA balancing scan progress

Under `CONFIG_NUMA_BALANCING`, the scheduler's NUMA scanner keeps per-VMA state so it can decide which ranges to sample:

```c
/* include/linux/mm_types.h:988 */
#ifdef CONFIG_NUMA_BALANCING
	struct vma_numab_state *numab_state;	/* NUMA Balancing state */
#endif
```

[`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989) points at a [`struct vma_numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L768) recording when the VMA should next be scanned and which PIDs recently faulted in it. It is NULL until the first scan, then allocated by [`task_numa_work()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/fair.c#L3363) with a `cmpxchg` so concurrent scanners install it exactly once:

```c
/* kernel/sched/fair.c:3484 */
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
```

The scan sequence fields let the balancer skip a VMA that was already scanned in the current pass, and the freed pointer is released when the VMA is destroyed.

### The shared.rb node links a file VMA into the i_mmap interval tree

A file-backed VMA is a member of two trees at once, the owner's [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) and the file's [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480). The embedded node for the second is the `shared` sub-struct:

```c
/* include/linux/mm_types.h:1035 */
	/*
	 * For areas with an address space and backing store,
	 * linkage into the address_space->i_mmap interval tree.
	 *
	 */
	struct {
		struct rb_node rb;
		unsigned long rb_subtree_last;
	} shared;
```

The [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) node makes the VMA an entry in the [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) interval tree of the mapped file's [`struct address_space`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L470), keyed by the file-offset interval `[vm_pgoff, vm_pgoff + pages)`, and `rb_subtree_last` is the augmented interval-tree bookkeeping. That tree is how the kernel finds every VMA mapping a given file range when the file is truncated or a shared page is unmapped, the file-backed counterpart to the `anon_vma` interval tree for anonymous pages. Insertion happens through [`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810), detailed below.

### anon_name attaches a name to an anonymous mapping

Under `CONFIG_ANON_VMA_NAME`, an anonymous mapping can carry a user-assigned name for reporting in `/proc/PID/maps`:

```c
/* include/linux/mm_types.h:1044 */
#ifdef CONFIG_ANON_VMA_NAME
	/*
	 * For private and shared anonymous mappings, a pointer to a null
	 * terminated string containing the name given to the vma, or NULL if
	 * unnamed. Serialized by mmap_lock. Use anon_vma_name to access.
	 */
	struct anon_vma_name *anon_name;
#endif
```

[`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) points at a refcounted [`struct anon_vma_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L728) set by `madvise(MADV_SET_ANON_NAME)`. According to the comment, it is "Serialized by mmap_lock" and must be reached through the `anon_vma_name()` accessor rather than dereferenced directly, because that accessor takes the reference the caller needs to keep the string alive after the lock is dropped.

### vm_userfaultfd_ctx and pfnmap_track_ctx attach optional per-VMA state

The final two members attach optional per-VMA subsystems:

```c
/* include/linux/mm_types.h:1052 */
	struct vm_userfaultfd_ctx vm_userfaultfd_ctx;
#ifdef __HAVE_PFNMAP_TRACKING
	struct pfnmap_track_ctx *pfnmap_track_ctx;
#endif
```

[`vm_userfaultfd_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1052) is an embedded [`struct vm_userfaultfd_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L720) that, under `CONFIG_USERFAULTFD`, wraps a pointer to the userfaultfd context registered on the range, and is an empty struct when userfaultfd is not built in. [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054) points at a refcounted [`struct pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L805) recording the PFN range and cache attributes for a `VM_PFNMAP` mapping, so the tracked memory-type reservation is released when the last VMA sharing it goes away. On duplication, [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41) copies the userfaultfd context by value but clears the child's [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054) so the reference is taken separately by [`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121).

### vma_init resets a VMA and points vm_ops at vma_dummy_vm_ops

Every VMA passes through one initializer that establishes the invariants the rest of the code relies on:

```c
/* include/linux/mm.h:909 */
static inline void vma_init(struct vm_area_struct *vma, struct mm_struct *mm)
{
	memset(vma, 0, sizeof(*vma));
	vma->vm_mm = mm;
	vma->vm_ops = &vma_dummy_vm_ops;
	INIT_LIST_HEAD(&vma->anon_vma_chain);
	vma_lock_init(vma, false);
}
```

[`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) zeroes the whole object, sets the owner [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), initializes the empty [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list, and initializes the per-VMA lock with [`vma_lock_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L150). It points [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) at the shared placeholder [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20), a single zero-initialized operations struct declared with the definition:

```c
/* mm/init-mm.c:20 */
const struct vm_operations_struct vma_dummy_vm_ops;
```

Pointing a fresh VMA at [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20) rather than leaving [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) NULL keeps [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235) from reporting a partially built VMA as anonymous before the mapping path has decided what it is. The extern declaration in the header pairs with this single definition:

```c
/* include/linux/mm.h:907 */
extern const struct vm_operations_struct vma_dummy_vm_ops;
```

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

[`vm_area_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28) is the entry point the mapping path uses. [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) calls it for a new mapping, and [`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866) calls it for a brk-style anonymous extension; both then fill the range and flags before inserting the VMA into [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140). The matching destructor returns a detached VMA to the same slab after releasing its per-feature state:

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

[`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) asserts the VMA is already detached (its [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) has reached the detached state), frees the lazily allocated [`numab_state`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L989), drops the [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) reference, releases the [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054), and returns the object to `vm_area_cachep`, where the `SLAB_TYPESAFE_BY_RCU` grace period keeps the memory readable by a concurrent lockless reader until it is safe to recycle.

### vm_area_init_from copies every member during duplication

The `fork` path duplicates a VMA rather than re-parsing the mapping, and the routine that copies it member by member is the one the type comment warns about:

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

Every member named in the catalog table appears here except the ones a clone must not share, and this is exactly the list the WARNING comment on the struct requires a new member to be added to. The [`shared`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) block is copied under `data_race()` because, according to the comment "src->shared.rb may be modified concurrently when called from dup_mmap(), but the clone will reinitialize it", the copy is a throwaway that the caller overwrites. The [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054) is set to NULL rather than shared. The lock and reverse-map fields are deliberately not copied here; the public wrapper re-initializes them:

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

[`vm_area_dup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L121) runs [`vm_area_init_from()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L41), then takes a fresh reference on any [`pfnmap_track_ctx`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1054), re-initializes the per-VMA lock with [`vma_lock_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L150) (resetting [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) for the detached clone), re-initializes the empty [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list, and takes a reference on the [`anon_name`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1050) string.

### vma_set_range writes the address range and file offset together

The three fields that place a VMA in both trees are written by one helper so they cannot drift apart:

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

[`vma_set_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1620) writes [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919), [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920), and [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) in one call, keeping the maple-tree key and the file-offset key consistent. Seven call sites in [`mm/vma.c`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c) use it, covering VMA merge and split, the `mremap` copy, the new mapping created by [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506), and the brk extension in [`do_brk_flags()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2866). Every path that resizes a VMA goes through it, so no code adjusts [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919) without also fixing the file offset the interval trees are keyed on.

### The vm_flags accessors mediate every flag change

Because [`vm_flags`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L939) is `const`, the flag bitmap is edited only through the accessor family. The unlocked initializer is used before the VMA is visible in the tree:

```c
/* include/linux/mm.h:919 */
static inline void vm_flags_init(struct vm_area_struct *vma,
				 vm_flags_t flags)
{
	VM_WARN_ON_ONCE(!pgtable_supports_soft_dirty() && (flags & VM_SOFTDIRTY));
	vma_flags_clear_all(&vma->flags);
	vma_flags_overwrite_word(&vma->flags, flags);
}
```

[`vm_flags_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L919) clears the bitmap and writes the word without any lock, which is why its comment restricts it to a VMA that is "not part of the VMA tree and needs no locking". Once a VMA is published, edits must take the per-VMA write lock, and the set/clear/mod trio does:

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

[`vm_flags_set()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L958) ORs bits in and [`vm_flags_clear()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L965) masks them out, each calling [`vma_start_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L298) first so a concurrent lockless reader sees the VMA write-locked. The combined form [`vm_flags_mod()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L987) applies a set and a clear in one locked section, and [`vm_flags_reset()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L932) overwrites the whole word after asserting the caller already holds the write lock. All of these delegate to the low-level bitmap writers [`vma_flags_set_word()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1091), [`vma_flags_clear_word()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1099), and [`vma_flags_overwrite_word()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1070). Around 111 call sites across `mm/`, `fs/`, and the arch code change VMA flags this way, for example [`__mmap_complete()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2580) setting `VM_SOFTDIRTY` on a new mapping.

### vma_is_anonymous and vma_set_anonymous read and write the vm_ops sentinel

The anonymous marker is derived from [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) rather than stored as a flag:

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

[`vma_set_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230) writes the NULL marker, and [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235) reports true when [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) is NULL. This is why [`vma_init()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L909) points a fresh VMA at [`vma_dummy_vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L20) (a non-NULL, empty struct) rather than NULL, so an unfinished VMA does not read as anonymous. Around 39 call sites in `mm/` and `fs/` branch on [`vma_is_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1235), including the fault dispatcher that routes an anonymous fault to [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217).

### vma_start_read takes a per-VMA read lock under RCU

The point of the per-VMA lock is to let a page fault proceed without the address-space-wide [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196). The core is [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212), which reads only the three RCU-marked members:

```c
/* mm/mmap_lock.c:212 */
static inline struct vm_area_struct *vma_start_read(struct mm_struct *mm,
						    struct vm_area_struct *vma)
{
	struct mm_struct *other_mm;
	int oldcnt;

	RCU_LOCKDEP_WARN(!rcu_read_lock_held(), "no rcu lock held");
	/*
	 * Check before locking. A race might cause false locked result.
	 * ...
	 */
	if (READ_ONCE(vma->vm_lock_seq) == READ_ONCE(mm->mm_lock_seq.sequence)) {
		vma = NULL;
		goto err;
	}

	/*
	 * If VM_REFCNT_EXCLUDE_READERS_FLAG is set,
	 * __refcount_inc_not_zero_limited_acquire() will fail because
	 * VM_REFCNT_LIMIT is less than VM_REFCNT_EXCLUDE_READERS_FLAG.
	 * ...
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
	...
}
```

The function first reads [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) with `READ_ONCE()` and bails out (returning NULL) if it equals the owner's current write-lock generation, the pessimistic early check the field comment sanctions. It then takes a bounded increment on [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) capped at [`VM_REFCNT_LIMIT`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L766); a detached VMA (count 0) or one whose writer set [`VM_REFCNT_EXCLUDE_READERS_FLAG`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L765) fails the increment. Finally it re-reads [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) to detect a VMA that was recycled onto a different address space. All three reads are of RCU-marked members, which keeps the lock safe against the `SLAB_TYPESAFE_BY_RCU` recycling of the VMA. The public entry point [`lock_vma_under_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296) is the caller that pairs the maple-tree lookup with this read lock:

```c
/* mm/mmap_lock.c:296 */
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

[`lock_vma_under_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L296) looks up the covering VMA in [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) with `mas_walk()` under `rcu_read_lock()`, hands it to [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212), and retries the whole lookup on `-EAGAIN` (the VMA was isolated under it). According to the comment "From here on, we can access the VMA without worrying about which fields are accessible for RCU readers", once the read lock is held the caller may touch any field, not just the three RCU-marked ones, and it then confirms the address still falls inside [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919) to [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920) before returning. The page-fault handler falls back to taking the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) when this returns NULL.

### mmap installs vm_file, vm_pgoff, and vm_ops for a file mapping

A file mapping's driver-facing fields are set in the new-VMA path of [`mmap_region()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2818). The allocation and the range/flag/offset writes happen first:

```c
/* mm/vma.c:2506 */
static int __mmap_new_vma(struct mmap_state *map, struct vm_area_struct **vmap)
{
	struct vma_iterator *vmi = map->vmi;
	int error = 0;
	struct vm_area_struct *vma;

	...
	vma = vm_area_alloc(map->mm);
	if (!vma)
		return -ENOMEM;

	vma_iter_config(vmi, map->addr, map->end);
	vma_set_range(vma, map->addr, map->end, map->pgoff);
	vm_flags_init(vma, map->vm_flags);
	vma->vm_page_prot = map->page_prot;
	...
	if (map->file)
		error = __mmap_new_file_vma(map, vma);
	else if (map->vm_flags & VM_SHARED)
		error = shmem_zero_setup(vma);
	else
		vma_set_anonymous(vma);
```

For a file mapping the branch calls [`__mmap_new_file_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2455), which assigns [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976), takes a file reference, and invokes the filesystem's legacy `mmap` operation:

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
	...
	/* Drivers cannot alter the address of the VMA. */
	WARN_ON_ONCE(map->addr != vma->vm_start);
	...
}
```

The driver's `mmap` handler is what installs [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971). The generic page-cache handler is the common case:

```c
/* mm/filemap.c:3990 */
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

[`generic_file_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L3990) sets `vma->vm_ops = &generic_file_vm_ops`, wiring the range's faults to the page-cache fault handler. The newer `mmap_prepare` interface reaches the same result without letting the driver touch the VMA directly. A filesystem fills a [`struct vm_area_desc`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L880), as [`generic_file_mmap_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/filemap.c#L4001) does with `desc->vm_ops = &generic_file_vm_ops`, and the core copies the whitelisted fields off the descriptor:

```c
/* mm/vma.c:2650 */
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
```

[`call_mmap_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2638) copies [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) and [`vm_private_data`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L977) from the descriptor into the mapping state, and [`set_vma_user_defined_fields()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2665) later stamps them onto the VMA:

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

The anonymous branch of [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) instead calls [`vma_set_anonymous()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1230) to clear [`vm_ops`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L971) to NULL, so the two mapping kinds diverge exactly at this pointer.

### do_anonymous_page attaches an anon_vma on the first anonymous fault

An anonymous VMA starts with a NULL [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968); the reverse-map root is attached only when a page is first faulted into the range. The anonymous fault handler prepares it before allocating the page:

```c
/* mm/memory.c:5261 */
	/* Allocate our own private page. */
	ret = vmf_anon_prepare(vmf);
	if (ret)
		return ret;
	/* Returns NULL on OOM or ERR_PTR(-EAGAIN) if we must retry the fault */
	folio = alloc_anon_folio(vmf);
```

[`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217) calls [`vmf_anon_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L500), whose non-inline half [`__vmf_anon_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3723) returns early when [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) already exists and otherwise, if the fault holds only the per-VMA lock, upgrades to the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) before calling [`__anon_vma_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185). According to its comment, "__anon_vma_prepare() will look at adjacent VMAs to determine if this VMA can share its anon_vma, and that's not safe to do with only the per-VMA lock held for this VMA". The attach itself installs the pointer under the page-table lock:

```c
/* mm/rmap.c:208 */
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
```

[`__anon_vma_prepare()`](https://elixir.bootlin.com/linux/v7.0/source/mm/rmap.c#L185) either reuses an adjacent mergeable [`struct anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L32) or allocates a new one, then sets the VMA's [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) pointer, links a [`struct anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/rmap.h#L83) onto the VMA's [`anon_vma_chain`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L966) list, and inserts that chain node into the `anon_vma`'s interval tree. The write is guarded by the page-table lock, which is the serialization the [`anon_vma`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L968) field comment names.

### vma_link_file inserts the shared.rb node into i_mmap

A file-backed VMA is added to its file's interval tree at map time by [`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810):

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
```

When [`vm_file`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L976) is set, it takes the file mapping's `i_mmap_rwsem` for write and calls [`__vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L227), which inserts the [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) node:

```c
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

[`vma_interval_tree_insert()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L3786) adds the VMA to `mapping->i_mmap`, the [`i_mmap`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L480) tree of the [`struct address_space`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/fs.h#L470), keyed on the [`vm_pgoff`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L974) interval and using the embedded [`shared.rb`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1043) node. This is what lets truncation and reverse mapping find every VMA that maps a given file page. [`vma_link_file()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1810) is called from [`__mmap_new_vma()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L2506) for a new mapping and from [`vma_link()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.c#L1824) for other insertions, always after [`vma_start_write()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L298) has write-locked the VMA and [`vma_iter_store_new()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610) has placed it in [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140).

### mm_mt owns every VMA and mmap_lock plus vm_refcnt serialize access

A VMA does not stand alone; its owner is the [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) maple tree in the [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) that [`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929) points back at. The tree stores each VMA under its [`vm_start`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L919) to [`vm_end`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L920) range, so a lookup by address returns the covering VMA, and insertion is done by [`vma_iter_store_new()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L610) while the VMA is write-locked. The lifetime and locking rules that follow from this ownership are compact. A VMA is created by [`vm_area_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L28) from `vm_area_cachep`, published into [`mm_mt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1140) under the owner's [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) held for write, and freed by [`vm_area_free()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma_init.c#L144) after it is removed from the tree, detached (its [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) driven to the detached state), and left for an RCU grace period by the `SLAB_TYPESAFE_BY_RCU` cache. Two locks serialize access: the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) reader-writer semaphore covers structural changes to the whole tree (a writer holds it to insert, split, merge, or remove VMAs; a reader holds it to walk them), and the per-VMA [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030) plus [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958) pair lets a fault take a read lock on one VMA under RCU through [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) without the shared semaphore. A VMA field that a lockless reader may observe is one of the three the type comment marks RCU-readable ([`vm_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L929), [`vm_lock_seq`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L958), [`vm_refcnt`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1030)); every other field requires the [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) or a stable per-VMA reference obtained through the read lock.
