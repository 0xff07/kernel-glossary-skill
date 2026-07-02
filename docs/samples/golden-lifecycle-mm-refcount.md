# mm_struct reference counting

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

Every [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) carries two reference counters with two different meanings. [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) counts users of the address space contents (the VMAs, the user page tables, the mapped pages), is moved by [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131), [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136), and [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193), and its 1 to 0 edge fires [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167), which dismantles the address space through [`exit_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1275). [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) counts references to the [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) object itself (including the page-global directory it points to), is moved by [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) and [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47), and its 1 to 0 edge fires [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718), which frees the pgd and returns the struct to [`mm_cachep`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L479). The whole nonzero [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) population collectively owns exactly one [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference, which the last [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) releases at the end of [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167). On x86-64 the scheduler's lazy-TLB borrowing (a kernel thread running on a user task's page tables through [`task_struct.active_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h)) takes real [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) references through [`mmgrab_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88) and [`mmdrop_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L94), because [`CONFIG_MMU_LAZY_TLB_REFCOUNT`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L553) is `def_bool y` and x86 leaves [`CONFIG_MMU_LAZY_TLB_SHOOTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L568) unselected. This page covers the counters, every get/put variant, the caller populations, and the [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) borrowing story including [`kthread_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615); the internal ordering of the [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) teardown callees is covered at call-name level only, and their deep internals fall outside this page.

```
    Two counters, four edges: what each transition fires
    ─────────────────────────────────────────────────────
    (mm_init() starts both counters at 1; the whole nonzero
     mm_users population owns exactly one mm_count reference)

      mm_users event                 transition    action at the edge
      ┌────────────────────────────┬─────────────┬─────────────────────────┐
      │ mmget / get_task_mm        │  n ─▶ n+1   │ none (pure pin)         │
      │ mmget_not_zero, mm live    │  n ─▶ n+1   │ none (pure pin)         │
      │ mmget_not_zero, mm dead    │  0 ─▶ 0     │ returns false           │
      │ mmput, other users left    │  n ─▶ n-1   │ skip (n-1 > 0)          │
      │ mmput, last user           │  1 ─▶ 0     │ __mmput(): exit_mmap()  │
      │                            │             │ etc., then mmdrop()     │
      │ mmput_async, last user     │  1 ─▶ 0     │ schedule_work ─▶        │
      │                            │             │ __mmput() on a kworker  │
      └────────────────────────────┴─────────────┴─────────────────────────┘

      mm_count event                 transition    action at the edge
      ┌────────────────────────────┬─────────────┬─────────────────────────┐
      │ mmgrab                     │  n ─▶ n+1   │ none (pure pin)         │
      │ mmgrab_lazy_tlb (x86-64)   │  n ─▶ n+1   │ none (REFCOUNT=y)       │
      │ mmdrop, references left    │  n ─▶ n-1   │ skip (n-1 > 0)          │
      │ mmdrop, last reference     │  1 ─▶ 0     │ __mmdrop(): free pgd,   │
      │                            │             │ ids, cid; free_mm()     │
      │ mmdrop_sched, last (RT)    │  1 ─▶ 0     │ call_rcu ─▶ __mmdrop()  │
      │ mmdrop_async, last         │  1 ─▶ 0     │ schedule_work ─▶        │
      │                            │             │ __mmdrop() on a kworker │
      └────────────────────────────┴─────────────┴─────────────────────────┘

      the mm_users 1 ─▶ 0 edge releases the population's single mm_count
      reference, so the last mmput() runs __mmput() and then mmdrop();
      a lazy-TLB borrower or an mmgrab() holder keeps the struct (and the
      pgd) alive past that point, as a "zombie" address space
```

## SUMMARY

The two counters are [`atomic_t`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/types.h#L188) fields of [`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123). [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) is defined alone in a [`____cacheline_aligned_in_smp`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cache.h#L65) anonymous struct at the top of the object, under the comment "Fields which are often written to are placed in a separate cache line.", because every context switch into or out of a kernel thread writes it on x86-64; its kerneldoc reads "The number of references to &struct mm_struct (@mm_users count as 1)." and "When this drops to 0, the &struct mm_struct is freed." [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) carries the kerneldoc "The number of users including userspace." and states the coupling rule between the counters, "When this drops to 0 (i.e. when the task exits and there are no other temporary reference holders), we also release a reference on @mm_count (which may then free the &struct mm_struct if @mm_count also drops to 0)." [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) starts both counters at 1 ([`kernel/fork.c:1077`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1077)), while the static [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) is born with [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) 2 and [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) 1 ([`mm/init-mm.c:35`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L35)) and is never freed; [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) opens with [`BUG_ON(mm == &init_mm)`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L720).

The API is split accordingly. [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35)/[`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) pin and release the struct for "a longer/unbounded amount of time" (the kerneldoc's words) without keeping the address space contents alive; [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131)/[`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136)/[`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) pin and release the contents, and the kerneldoc forbids holding them "for an unbounded/indefinite amount of time". [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) and the fork-internal [`mmdrop_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749) push the respective 1 to 0 work onto the system workqueue through the [`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333) field, so atomic and lock-nested contexts can drop their last reference; [`mmdrop_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L74) defers [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) through [`call_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/rcu/tree.c#L3249) on [`CONFIG_PREEMPT_RT`](https://elixir.bootlin.com/linux/v7.0/source/kernel/Kconfig.preempt#L92) kernels via the [`delayed_drop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1328) rcu_head. At v7.0 there are 108 functions calling [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193), 57 calling [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136), 46 calling [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35), and 49 calling [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47), enumerated in DETAILS with representative excerpts.

The borrowing model separates [`task_struct.mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L114) (the address space a task owns; NULL for every kernel thread) from [`task_struct.active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) (the address space whose page tables the CPU is running on). [`context_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5239) hands the outgoing task's [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) to an incoming kernel thread and takes a lazy reference with [`mmgrab_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88) only on the user-to-kernel edge, and [`finish_task_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112) pays that reference back with [`mmdrop_lazy_tlb_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L107) on the kernel-to-user edge. On x86-64 [`enter_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L987) leaves CR3 untouched and only marks the CPU lazy in [`cpu_tlbstate_shared.is_lazy`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/tlbflush.h). [`exit_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L550) converts a dying task into a lazy borrower of its own former mm, [`exec_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L837) swaps a new mm in at execve and settles either an [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) or an [`mmdrop_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L94), and [`kthread_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615)/[`kthread_unuse_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1662) let a kernel thread adopt a user mm outright, a facility used at v7.0 by vhost, VFIO, iommufd, the USB gadget function filesystem, amdkfd, and others (16 callers).

## SPECIFICATIONS

## LINUX KERNEL

### Counter storage (mm_types.h, init-mm.c, fork.c)

- [`'\<struct mm_struct\>':'include/linux/mm_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123): the address-space descriptor holding both counters
- [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137): references to the struct itself; isolated in its own cache line
- [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171): users of the address space contents; counts as one [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137)
- [`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333): work_struct reused by [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) and [`mmdrop_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749)
- [`delayed_drop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1328): rcu_head for the [`CONFIG_PREEMPT_RT`](https://elixir.bootlin.com/linux/v7.0/source/kernel/Kconfig.preempt#L92) [`mmdrop_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L74) path
- [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32): static kernel mm; [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) 2, [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) 1, never freed
- [`mm_cachep`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L479): the `"mm_struct"` slab cache created by [`mm_cache_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L3002)
- [`allocate_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L649) / [`free_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L650): the alloc/free macros over [`mm_cachep`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L479)
- [`'\<mm_init\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072): sets both counters to 1 and builds every subsystem hook of a fresh mm
- [`'\<mm_alloc\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1154): [`allocate_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L649) + zero + [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) for execve and KUnit

### mm_count API (include/linux/sched/mm.h, kernel/fork.c)

- [`'\<mmgrab\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35): [`atomic_inc(&mm->mm_count)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L37); the long-term struct pin
- [`'\<mmdrop\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47): [`atomic_dec_and_test()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-instrumented.h#L1380); fires [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) at 0 and doubles as a membarrier full barrier
- [`'\<__mmdrop\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718): frees pgd, mm ID, LDT context, notifier subscriptions, CID, rss counters, then [`free_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L650)
- [`'\<mmdrop_sched\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L74): RT variant deferring the last drop to [`call_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/rcu/tree.c#L3249)
- [`'\<__mmdrop_delayed\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L63): the RCU callback running [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718)
- [`'\<mmdrop_async\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749): workqueue variant used for [`signal_struct.oom_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/signal.h)
- [`'\<mmdrop_async_fn\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L741): the work function behind it
- [`'\<cleanup_lazy_tlbs\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L670): shoots down lazy users before the free; a no-op under [`CONFIG_MMU_LAZY_TLB_REFCOUNT`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L553)

### Lazy-TLB reference API (include/linux/sched/mm.h, arch/Kconfig)

- [`'\<mmgrab_lazy_tlb\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88): [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) when lazy references are counted (x86-64), else nothing
- [`'\<mmdrop_lazy_tlb\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L94): [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) or a bare [`smp_mb()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/barrier.h#L99) preserving the membarrier barrier
- [`'\<mmdrop_lazy_tlb_sched\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L107): the [`finish_task_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112) flavor routing to [`mmdrop_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L74)
- [`MMU_LAZY_TLB_REFCOUNT`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L553): `def_bool y` unless shootdown is selected; y on x86-64
- [`MMU_LAZY_TLB_SHOOTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L568): IPI-based alternative; selected only by powerpc [`PPC_BOOK3S_64`](https://elixir.bootlin.com/linux/v7.0/source/arch/powerpc/platforms/Kconfig.cputype#L83) at v7.0

### mm_users API (include/linux/sched/mm.h, kernel/fork.c)

- [`'\<mmget\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131): [`atomic_inc(&mm->mm_users)`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L133); requires an already-held user reference
- [`'\<mmget_not_zero\>':'include/linux/sched/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136): [`atomic_inc_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-instrumented.h#L1533); the revive-if-alive entry for observers
- [`'\<mmput\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193): [`might_sleep()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/kernel.h#L90); fires [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) at 0
- [`'\<__mmput\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167): tears down aio, ksm, khugepaged, mappings, mmlist, binfmt, MGLRU, futex hash, then [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47)
- [`'\<mmput_async\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211): defers a last-user [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) to the system workqueue; callable from atomic context
- [`'\<mmput_async_fn\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1203): the work function behind it
- [`'\<get_task_mm\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1366): task_lock-protected [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131) of another task's mm; refuses kthreads
- [`'\<mm_access\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1393): [`get_task_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1366) gated by ptrace permission under [`exec_update_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/signal.h#L250)
- [`'\<copy_mm\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1556): fork-time [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131) for [`CLONE_VM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/sched.h#L11) or [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) otherwise
- [`'\<dup_mm\>':'kernel/fork.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515): allocates and copies an mm for a fork without [`CLONE_VM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/sched.h#L11)

### Scheduler and lifecycle transitions (core.c, exit.c, exec.c, cpu.c, tlb.c)

- [`'\<context_switch\>':'kernel/sched/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5239): the four-case mm hand-over at every switch
- [`'\<finish_task_switch\>':'kernel/sched/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112): pays back the deferred lazy reference via [`rq->prev_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/sched.h#L1207)
- [`'\<enter_lazy_tlb\>':'arch/x86/mm/tlb.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L987): x86-64 lazy-mode marker; leaves CR3 loaded
- [`'\<exit_mm\>':'kernel/exit.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L550): converts the dying task into a lazy borrower, then [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193)
- [`'\<exec_mmap\>':'fs/exec.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L837): installs the new execve mm and releases the old one
- [`'\<sched_force_init_mm\>':'kernel/sched/core.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L8067): hotplug-out switch of the hotplug thread to [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32)
- [`'\<finish_cpu\>':'kernel/cpu.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/cpu.c#L908): drops the dead CPU idle task's [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) lazy reference

### kthread borrowing (kernel/kthread.c)

- [`'\<kthread_use_mm\>':'kernel/kthread.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615): a kthread adopts a user mm; [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) plus [`mmdrop_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L94) of the old borrow
- [`'\<kthread_unuse_mm\>':'kernel/kthread.c'`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1662): the reverse; [`mmgrab_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88) plus [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47)

### Pinning-user patterns shown on this page (proc, oom, khugepaged)

- [`'\<proc_mem_open\>':'fs/proc/base.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L837): [`mm_access()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1393) then [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35)+[`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193), keeping only the struct pinned
- [`'\<mem_rw\>':'fs/proc/base.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L899): per-I/O [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) revival for /proc/PID/mem
- [`'\<mem_release\>':'fs/proc/base.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L984): the matching [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) at file close
- [`'\<mark_oom_victim\>':'mm/oom_kill.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L767): pins the victim mm as [`signal_struct.oom_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/signal.h) with [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35)
- [`'\<hpage_collapse_test_exit\>':'mm/khugepaged.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/khugepaged.c#L390): reads [`mm_users == 0`](https://elixir.bootlin.com/linux/v7.0/source/mm/khugepaged.c#L392) as the exit signal for a struct-pinned mm

## KERNEL DOCUMENTATION

- [`Documentation/mm/active_mm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/active_mm.rst): Linus Torvalds' 1999 explanation of [`mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958) versus [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) and of [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) versus [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137), prefixed with the modern [`CONFIG_MMU_LAZY_TLB_REFCOUNT`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L553) caveat; quoted in DETAILS

## OTHER SOURCES

- [mm: add new mmgrab() helper](http://lkml.kernel.org/r/20161218123229.22952-1-vegard.nossum@oracle.com)
- [mm: add new mmget() helper](http://lkml.kernel.org/r/20161218123229.22952-2-vegard.nossum@oracle.com)
- [kernel: move use_mm/unuse_mm to kthread.c](http://lkml.kernel.org/r/20200404094101.672954-5-hch@lst.de)
- [mm: fix kthread_use_mm() vs TLB invalidate](http://lkml.kernel.org/r/20200721154106.GE10769@hirez.programming.kicks-ass.net)
- [lazy tlb: introduce lazy tlb mm refcount helper functions](https://lkml.kernel.org/r/20230203071837.1136453-3-npiggin@gmail.com)
- [lazy tlb: allow lazy tlb mm refcounting to be configurable](https://lkml.kernel.org/r/20230203071837.1136453-4-npiggin@gmail.com)
- [lazy tlb: shoot lazies, non-refcounting lazy tlb mm reference handling scheme](https://lkml.kernel.org/r/20230203071837.1136453-5-npiggin@gmail.com)
- [mm: move mm_count into its own cache line](https://lkml.kernel.org/r/20230515143536.114960-1-mathieu.desnoyers@efficios.com)
- [futex: Use RCU-based per-CPU reference counting instead of rcuref_t](https://lore.kernel.org/r/20250710110011.384614-3-bigeasy@linutronix.de)

## DETAILS

### mm_users and mm_count split one object into two lifetimes

[`struct mm_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1123) opens with [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) wrapped in an anonymous struct that is [`____cacheline_aligned_in_smp`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cache.h#L65), so the counter that every kernel-thread context switch writes shares no cache line with the read-mostly fields around it.

```c
/* include/linux/mm_types.h:1123 */
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

		struct maple_tree mm_mt;
	...
```

[`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) is defined further down, next to the fields that the page-fault and mmap paths touch, and its kerneldoc states the rule that couples the two counters. The whole population of address-space users holds one single [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference, and the [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) 1 to 0 edge releases it.

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

Two more fields exist purely for the deferred-release paths. [`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333) is the work_struct that both [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) and [`mmdrop_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749) initialize on demand, and [`delayed_drop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1328) is the rcu_head that the [`CONFIG_PREEMPT_RT`](https://elixir.bootlin.com/linux/v7.0/source/kernel/Kconfig.preempt#L92) build of [`mmdrop_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L74) hands to [`call_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/rcu/tree.c#L3249). The two work users never overlap because a work item is queued only on a counter's final decrement, [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) queues on the [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) edge while the mm still holds its [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference, and [`mmdrop_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749) queues on the [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) edge after which nothing else touches the struct.

```c
/* include/linux/mm_types.h:1327 */
#ifdef CONFIG_PREEMPT_RT
		struct rcu_head delayed_drop;
#endif
#ifdef CONFIG_HUGETLB_PAGE
		atomic_long_t hugetlb_usage;
#endif
		struct work_struct async_put_work;
```

[`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) gives every dynamically created mm its initial counter values. Both start at 1, meaning one address-space user (the task being created or the execve in progress) and the one struct reference that the user population owns.

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
	...
	if (mm_alloc_pgd(mm))
		goto fail_nopgd;
	...
```

The statically built [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) starts at [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) 2 and [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) 1 (values carried unchanged since the 2009 consolidation of the per-arch definitions into [`mm/init-mm.c`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c)). Neither counter of [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) may ever reach zero; [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) enforces that with a [`BUG_ON`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/bug.h#L81), and the surplus initial [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) guarantees no [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) can trigger [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) on it.

```c
/* mm/init-mm.c:32 */
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
	...
};
```

### mm_cachep backs allocate_mm and free_mm

The struct is held in the `"mm_struct"` slab cache. [`mm_cachep`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L479) is file-static in [`kernel/fork.c`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c), and the [`allocate_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L649)/[`free_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L650) macros are its only entry points, so every allocation and every final free of an mm funnels through this one cache.

```c
/* kernel/fork.c:478 */
/* SLAB cache for mm_struct structures (tsk->mm) */
static struct kmem_cache *mm_cachep;
```

```c
/* kernel/fork.c:649 */
#define allocate_mm()	(kmem_cache_alloc(mm_cachep, GFP_KERNEL))
#define free_mm(mm)	(kmem_cache_free(mm_cachep, (mm)))
```

[`mm_cache_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L3002) creates the cache at boot. The object size adds the dynamically sized [`mm_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1432) bitmap and the per-CPU CID storage behind the fixed struct, and the usercopy window whitelists only [`saved_auxv`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1259) for direct copies to userspace.

```c
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

[`mm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1154) is the fresh-mm constructor for paths that build an address space from nothing (execve and KUnit tests), combining [`allocate_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L649), a full zeroing, and [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072).

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
```

[`bprm_mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L256) in the execve path is a caller worth reading because of its error leg. A brand-new mm whose address space never received user content is released with a bare [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) ([`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) 1 to 0, straight to [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718)), skipping the [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) teardown entirely; a bprm mm that survives initialization is later released with [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) by [`free_bprm()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L1372) or handed to the task by [`exec_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L837).

```c
/* fs/exec.c:256 */
static int bprm_mm_init(struct linux_binprm *bprm)
{
	int err;
	struct mm_struct *mm = NULL;

	bprm->mm = mm = mm_alloc();
	err = -ENOMEM;
	if (!mm)
		goto err;
	...
err:
	if (mm) {
		bprm->mm = NULL;
		mmdrop(mm);
	}

	return err;
}
```

### mmgrab and mmdrop move mm_count

[`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) is a plain atomic increment. Its kerneldoc draws the line between the two counters. According to the comment, "Make sure that @mm will not get freed even after the owning task exits. This doesn't guarantee that the associated address space will still exist later on and mmget_not_zero() has to be used before accessing it.", and it names itself "a preferred way to pin @mm for a longer/unbounded amount of time".

```c
/* include/linux/sched/mm.h:18 */
/**
 * mmgrab() - Pin a &struct mm_struct.
 * @mm: The &struct mm_struct to pin.
 *
 * Make sure that @mm will not get freed even after the owning task
 * exits. This doesn't guarantee that the associated address space
 * will still exist later on and mmget_not_zero() has to be used before
 * accessing it.
 *
 * This is a preferred way to pin @mm for a longer/unbounded amount
 * of time.
 *
 * Use mmdrop() to release the reference acquired by mmgrab().
 *
 * See also <Documentation/mm/active_mm.rst> for an in-depth explanation
 * of &mm_struct.mm_count vs &mm_struct.mm_users.
 */
static inline void mmgrab(struct mm_struct *mm)
{
	atomic_inc(&mm->mm_count);
}

static inline void smp_mb__after_mmgrab(void)
{
	smp_mb__after_atomic();
}
```

The adjacent [`smp_mb__after_mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L40) upgrades the increment to a full barrier for ordering-sensitive callers; a tree-wide grep at v7.0 finds zero in-tree callers, so it exists only as API surface.

[`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) decrements and fires [`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) on the 1 to 0 edge. According to the comment, the full barrier that [`atomic_dec_and_test()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-instrumented.h#L1380) implies "is required by the membarrier system call before returning to user-space, after storing to rq->curr", which is why the scheduler may substitute a bare [`smp_mb()`](https://elixir.bootlin.com/linux/v7.0/source/include/asm-generic/barrier.h#L99) when the decrement itself is compiled out (see the lazy-TLB section below).

```c
/* include/linux/sched/mm.h:45 */
extern void __mmdrop(struct mm_struct *mm);

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

### __mmdrop frees the page directory and the struct at mm_count 0

[`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) is the terminal state of the object. Its opening assertions double as the debugging story for [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) bugs. [`BUG_ON(mm == &init_mm)`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L720) catches a refcount underflow on the never-freed kernel mm, [`WARN_ON_ONCE(mm == current->mm)`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L721) catches a task dropping the struct it still owns as its address space, and (after the lazy shootdown hook) [`WARN_ON_ONCE(mm == current->active_mm)`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L726) catches a CPU freeing the page tables it is still running on.

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
EXPORT_SYMBOL_GPL(__mmdrop);
```

The teardown sequence runs at call-name level as follows. [`mm_free_pgd()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L583) returns the page-global directory through [`pgd_free()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c), [`mm_free_id()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L606) releases the [`mm_id`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1372) used for folio owner tracking, [`destroy_context()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L175) frees the x86 LDT via [`destroy_context_ldt()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L61), [`mmu_notifier_subscriptions_destroy()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmu_notifier.h#L488) frees the notifier subscription block, [`check_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L622) reports leaked rss counters and nonzero [`pgtables_bytes`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1177) to dmesg, [`put_user_ns()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/user_namespace.h#L187) drops the user namespace, [`mm_pasid_drop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/iommu.h#L1631) releases the IOMMU PASID, [`mm_destroy_cid()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1553) tears down the concurrency-ID state, [`percpu_counter_destroy_many()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/percpu_counter.h#L49) frees the rss percpu counters, and [`free_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L650) returns the object to [`mm_cachep`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L479).

[`cleanup_lazy_tlbs()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L670) is a no-op on x86-64. According to its comment, with refcounted lazy mms "lazy tlb mms are refounted and would not reach __mmdrop until all CPUs have switched away and mmdrop()ed", so only the [`CONFIG_MMU_LAZY_TLB_SHOOTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L568) configuration (powerpc [`PPC_BOOK3S_64`](https://elixir.bootlin.com/linux/v7.0/source/arch/powerpc/platforms/Kconfig.cputype#L83) at v7.0, [`arch/powerpc/Kconfig:310`](https://elixir.bootlin.com/linux/v7.0/source/arch/powerpc/Kconfig#L310)) sends IPIs through [`do_shoot_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L659) to evict remaining borrowers onto [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32).

```c
/* kernel/fork.c:652 */
static void do_check_lazy_tlb(void *arg)
{
	struct mm_struct *mm = arg;

	WARN_ON_ONCE(current->active_mm == mm);
}

static void do_shoot_lazy_tlb(void *arg)
{
	struct mm_struct *mm = arg;

	if (current->active_mm == mm) {
		WARN_ON_ONCE(current->mm);
		current->active_mm = &init_mm;
		switch_mm(mm, &init_mm, current);
	}
}

static void cleanup_lazy_tlbs(struct mm_struct *mm)
{
	if (!IS_ENABLED(CONFIG_MMU_LAZY_TLB_SHOOTDOWN)) {
		/*
		 * In this case, lazy tlb mms are refounted and would not reach
		 * __mmdrop until all CPUs have switched away and mmdrop()ed.
		 */
		return;
	}
	...
	on_each_cpu_mask(mm_cpumask(mm), do_shoot_lazy_tlb, (void *)mm, 1);
	if (IS_ENABLED(CONFIG_DEBUG_VM_SHOOT_LAZIES))
		on_each_cpu(do_check_lazy_tlb, (void *)mm, 1);
}
```

### mmdrop_sched defers __mmdrop through RCU on PREEMPT_RT

[`__mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L718) frees page tables and percpu counters, which is too much work under the scheduler's tail on an RT kernel, so [`finish_task_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112) reaches [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) only through the `_sched` wrappers. On [`CONFIG_PREEMPT_RT`](https://elixir.bootlin.com/linux/v7.0/source/kernel/Kconfig.preempt#L92) the last decrement hands the free to [`call_rcu()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/rcu/tree.c#L3249) via the [`delayed_drop`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1328) head; according to the comment, this is "Not strictly RCU, but call_rcu() is by far the least expensive way to do that". Without RT the wrapper collapses to plain [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47). The x86-64 defconfig runs without [`CONFIG_PREEMPT_RT`](https://elixir.bootlin.com/linux/v7.0/source/kernel/Kconfig.preempt#L92), so the alias branch applies there.

```c
/* include/linux/sched/mm.h:58 */
#ifdef CONFIG_PREEMPT_RT
/*
 * RCU callback for delayed mm drop. Not strictly RCU, but call_rcu() is
 * by far the least expensive way to do that.
 */
static inline void __mmdrop_delayed(struct rcu_head *rhp)
{
	struct mm_struct *mm = container_of(rhp, struct mm_struct, delayed_drop);

	__mmdrop(mm);
}

/*
 * Invoked from finish_task_switch(). Delegates the heavy lifting on RT
 * kernels via RCU.
 */
static inline void mmdrop_sched(struct mm_struct *mm)
{
	/* Provides a full memory barrier. See mmdrop() */
	if (atomic_dec_and_test(&mm->mm_count))
		call_rcu(&mm->delayed_drop, __mmdrop_delayed);
}
#else
static inline void mmdrop_sched(struct mm_struct *mm)
{
	mmdrop(mm);
}
#endif
```

### mmdrop_async moves the final drop out of softirq context

[`free_signal_struct()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L757) can run from the RCU softirq when the last [`put_task_struct()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/task.h) of an OOM victim's group arrives there, and it may hold the last [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference through [`signal_struct.oom_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/signal.h). According to the comment, "__mmdrop is not safe to call from softirq context on x86 due to pgd_dtor so postpone it to the async context" ([`pgd_dtor()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L95) takes the spinlock protecting the x86 [`pgd_list`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L172)), so the drop goes through [`mmdrop_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L749), which queues [`mmdrop_async_fn()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L741) on the system workqueue through the same [`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333) field that [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) uses.

```c
/* kernel/fork.c:741 */
static void mmdrop_async_fn(struct work_struct *work)
{
	struct mm_struct *mm;

	mm = container_of(work, struct mm_struct, async_put_work);
	__mmdrop(mm);
}

static void mmdrop_async(struct mm_struct *mm)
{
	if (unlikely(atomic_dec_and_test(&mm->mm_count))) {
		INIT_WORK(&mm->async_put_work, mmdrop_async_fn);
		schedule_work(&mm->async_put_work);
	}
}

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

The [`oom_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/signal.h#L241) pin itself is taken by [`mark_oom_victim()`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L767) with [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35), exactly once per signal_struct via [`cmpxchg`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-instrumented.h#L4783). This pin is what lets the OOM reaper thread walk and unmap the victim's address space from [`oom_reap_task()`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L619) even after the victim's [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) has reached zero, retrying [`oom_reap_task_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L578) up to [`MAX_OOM_REAP_RETRIES`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L618) (10, [`mm/oom_kill.c:618`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L618)) times with a [`schedule_timeout_idle(HZ/10)`](https://elixir.bootlin.com/linux/v7.0/source/kernel/time/sleep_timeout.c#L172) pause between attempts, synchronized against [`exit_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1275) by [`MMF_OOM_SKIP`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1894) under [`mmap_read_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L589).

```c
/* mm/oom_kill.c:777 */
	/* oom_mm is bound to the signal struct life time. */
	if (!cmpxchg(&tsk->signal->oom_mm, NULL, mm))
		mmgrab(tsk->signal->oom_mm);
```

### mmget, mmget_not_zero, and mmput move mm_users

[`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131) is the increment for callers that already hold a user reference, and its kerneldoc bounds the hold time. According to the comment, "Never use this function to pin this address space for an unbounded/indefinite amount of time", because a pinned [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) keeps every mapped page and page table of the process allocated. [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) is the speculative variant for observers holding only an [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) pin (or a [`task_struct`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L820) pin); it refuses to resurrect an address space whose teardown has begun, returning false once [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) reached 0.

```c
/* include/linux/sched/mm.h:115 */
/**
 * mmget() - Pin the address space associated with a &struct mm_struct.
 * @mm: The address space to pin.
 *
 * Make sure that the address space of the given &struct mm_struct doesn't
 * go away. This does not protect against parts of the address space being
 * modified or freed, however.
 *
 * Never use this function to pin this address space for an
 * unbounded/indefinite amount of time.
 *
 * Use mmput() to release the reference acquired by mmget().
 *
 * See also <Documentation/mm/active_mm.rst> for an in-depth explanation
 * of &mm_struct.mm_count vs &mm_struct.mm_users.
 */
static inline void mmget(struct mm_struct *mm)
{
	atomic_inc(&mm->mm_users);
}

static inline bool mmget_not_zero(struct mm_struct *mm)
{
	return atomic_inc_not_zero(&mm->mm_users);
}
```

[`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) asserts a sleepable context up front because the 1 to 0 edge runs the full address-space teardown synchronously.

```c
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
EXPORT_SYMBOL_GPL(mmput);
```

Two helpers wrap the increment for cross-task access. [`get_task_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1366) takes [`task_lock()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/task.h#L216) so the read of [`task->mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1374) and the [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131) are atomic against [`exit_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L550) and [`exec_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L837) clearing or replacing the pointer, and it returns NULL for [`PF_KTHREAD`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L1774) tasks so a kthread that temporarily adopted a user mm through [`kthread_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615) is never mistaken for its owner. [`mm_access()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1393) adds the ptrace permission check under [`exec_update_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/signal.h#L250) and is the entry point for /proc and [`process_vm_readv()`](https://elixir.bootlin.com/linux/v7.0/source/mm/process_vm_access.c#L292)-style remote access.

```c
/* kernel/fork.c:1356 */
/**
 * get_task_mm - acquire a reference to the task's mm
 * @task: The task.
 *
 * Returns %NULL if the task has no mm.  Checks PF_KTHREAD (meaning
 * this kernel workthread has transiently adopted a user mm with kthread_use_mm,
 * to do its AIO) is not set and if so returns a reference to it, after
 * bumping up the use count.  User must release the mm via mmput()
 * after use.  Typically used by /proc and ptrace.
 */
struct mm_struct *get_task_mm(struct task_struct *task)
{
	struct mm_struct *mm;

	if (task->flags & PF_KTHREAD)
		return NULL;

	task_lock(task);
	mm = task->mm;
	if (mm)
		mmget(mm);
	task_unlock(task);
	return mm;
}
EXPORT_SYMBOL_GPL(get_task_mm);
```

```c
/* kernel/fork.c:1393 */
struct mm_struct *mm_access(struct task_struct *task, unsigned int mode)
{
	struct mm_struct *mm;
	int err;

	err =  down_read_killable(&task->signal->exec_update_lock);
	if (err)
		return ERR_PTR(err);

	mm = get_task_mm(task);
	if (!mm) {
		mm = ERR_PTR(-ESRCH);
	} else if (!may_access_mm(mm, task, mode)) {
		mmput(mm);
		mm = ERR_PTR(-EACCES);
	}
	up_read(&task->signal->exec_update_lock);

	return mm;
}
```

### copy_mm shares or duplicates the mm at fork

[`copy_process()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1964) calls [`copy_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1556) at [`kernel/fork.c:2223`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L2223), and [`copy_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1556) produces the child's [`mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958) and [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) in one of three ways. A kernel thread (no [`current->mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1575)) gets NULL for both, a [`CLONE_VM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/sched.h#L11) thread shares the parent's mm and takes one [`mmget()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L131) user reference, and a plain fork gets a full copy from [`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515), which arrives from [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) already holding [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) 1 and [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) 1 for the child.

```c
/* kernel/fork.c:1556 */
static int copy_mm(u64 clone_flags, struct task_struct *tsk)
{
	struct mm_struct *mm, *oldmm;
	...
	tsk->mm = NULL;
	tsk->active_mm = NULL;

	/*
	 * Are we cloning a kernel thread?
	 *
	 * We need to steal a active VM for that..
	 */
	oldmm = current->mm;
	if (!oldmm)
		return 0;

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

[`dup_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1515) releases a half-built copy with [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) on failure, matching the reference that [`mm_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1072) created; the comment at [`mm_release()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1460) (Eric Biederman, 1998) records that this ordering, "we mmput the new mm_struct before restoring the old one", is why [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) and [`mm_release()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1460) stay separate functions.

```c
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
	...
free_pt:
	/* don't put binfmt in mmput, we haven't got module yet */
	mm->binfmt = NULL;
	mm_init_owner(mm, NULL);
	mmput(mm);
	...
```

### __mmput dismantles the address space at mm_users 0

[`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) runs once, on the final [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) or on a kworker for [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211), and asserts [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) is exactly zero on entry.

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
```

At call-name level the sequence is as follows, and the internals of each callee fall outside this page. [`uprobe_clear_state()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/events/uprobes.c#L1820) frees the uprobes XOL area, [`exit_aio()`](https://elixir.bootlin.com/linux/v7.0/source/fs/aio.c#L891) kills the remaining aio contexts and waits for them, [`ksm_exit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/ksm.h#L77) and [`khugepaged_exit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/khugepaged.h#L29) detach the mm from the two scanners (the comment pins khugepaged before the unmap), [`exit_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1275) unmaps every VMA and frees the user page tables, [`mm_put_huge_zero_folio()`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L270) returns the huge zero folio reference, [`set_mm_exe_file()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1234) drops the executable file pin, the [`mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198) block unlinks the mm from the swap-visibility list under [`mmlist_lock`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c), [`module_put()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/module.h) releases the binfmt module, [`lru_gen_del_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2930) removes the mm from the MGLRU walker list, and [`futex_hash_free()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1731) frees the private futex hash. The closing [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) releases the one [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference that the user population owned, which is the concrete implementation of the coupling rule in the [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) kerneldoc.

After [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) the struct may live on under remaining [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) references as an empty shell whose [`pgd`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1150) still exists but maps no user pages, which is exactly the "zombie" state that [`Documentation/mm/active_mm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/active_mm.rst) describes for lazy borrowers, and the state in which [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) returns false forever after.

### mmput_async defers __mmput to the system workqueue

[`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) performs the same decrement as [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) but, on the 1 to 0 edge, initializes [`async_put_work`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1333) with [`mmput_async_fn()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1203) and queues it with [`schedule_work()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/workqueue.h), so [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) runs later on a kworker. The declaration comment in [`include/linux/sched/mm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L144) states the purpose, "same as above but performs the slow path from the async context. Can be called from the atomic context as well". The function exists because [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) sleeps (it takes [`mmap_write_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mmap_lock.h#L533) inside [`exit_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1275) and can flush I/O), so any caller that might hold the last user reference while in atomic context, while holding locks that rank below [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196), or while inside reclaim needs the deferred variant.

```c
/* include/linux/sched/mm.h:141 */
/* mmput gets rid of the mappings and all user-space */
extern void mmput(struct mm_struct *);
#if defined(CONFIG_MMU) || defined(CONFIG_FUTEX_PRIVATE_HASH)
/* same as above but performs the slow path from the async context. Can
 * be called from the atomic context as well
 */
void mmput_async(struct mm_struct *);
#endif
```

```c
/* kernel/fork.c:1202 */
#if defined(CONFIG_MMU) || defined(CONFIG_FUTEX_PRIVATE_HASH)
static void mmput_async_fn(struct work_struct *work)
{
	struct mm_struct *mm = container_of(work, struct mm_struct,
					    async_put_work);

	__mmput(mm);
}

void mmput_async(struct mm_struct *mm)
{
	if (atomic_dec_and_test(&mm->mm_users)) {
		INIT_WORK(&mm->async_put_work, mmput_async_fn);
		schedule_work(&mm->async_put_work);
	}
}
EXPORT_SYMBOL_GPL(mmput_async);
#endif
```

The `#if` condition gained its second leg in commit `56180dd20c19` ("futex: Use RCU-based per-CPU reference counting instead of rcuref_t"), because [`__futex_ref_atomic_end()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1566) drops the private-hash reference on [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) from an RCU callback, an atomic context that exists even on [`!CONFIG_MMU`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1202) builds with [`CONFIG_FUTEX_PRIVATE_HASH`](https://elixir.bootlin.com/linux/v7.0/source/init/Kconfig).

A tree-wide grep at v7.0 finds 13 [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) call sites in 12 C functions, plus the Rust binder abstraction in [`rust/kernel/mm/mmput_async.rs`](https://elixir.bootlin.com/linux/v7.0/source/rust/kernel/mm/mmput_async.rs). The callers are [`sgx_encl_cpumask()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/cpu/sgx/encl.c#L926), [`sgx_encl_get_mem_cgroup()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/cpu/sgx/encl.c#L1001), [`sgx_zap_enclave_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/cpu/sgx/encl.c#L1200), and [`sgx_reclaimer_age()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/cpu/sgx/main.c#L113) in the x86 SGX driver, [`binder_install_single_page()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/android/binder_alloc.c#L312) and [`binder_alloc_free_page()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/android/binder_alloc.c#L1134) (two sites) in binder, [`iterate_mm_list()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L3043) in the MGLRU page-table walker, [`__futex_ref_atomic_end()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/futex/core.c#L1566), [`ib_umem_odp_map_dma_and_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/infiniband/core/umem_odp.c#L324), [`svm_range_deferred_list_work()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpu/drm/amd/amdkfd/kfd_svm.c#L2403), [`drm_pagemap_evict_to_ram()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpu/drm/drm_pagemap.c#L943), and [`aie2_sched_notify()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/accel/amdxdna/aie2_ctx.c#L162).

Binder (the Android IPC driver in [`drivers/android/binder_alloc.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/android/binder_alloc.c), with substantive commits through 2026 including the KUnit scaffolding series) shows the shape of these callers. [`binder_install_single_page()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/android/binder_alloc.c#L312) revives the target address space with [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) and releases it with [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211), so a binder thread that happens to hold the last user reference never runs the full address-space teardown inside a binder allocation path.

```c
/* drivers/android/binder_alloc.c:312 */
static int binder_install_single_page(struct binder_alloc *alloc,
				      unsigned long index,
				      unsigned long addr)
{
	struct page *page;
	int ret;

	if (!mmget_not_zero(alloc->mm))
		return -ESRCH;
	...
out:
	mmput_async(alloc->mm);
	return ret;
}
```

SGX (the x86-64 enclave driver in [`arch/x86/kernel/cpu/sgx/`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/cpu/sgx/)) iterates every mm that ever mapped an enclave while holding the enclave SRCU lock, and drops each revived reference with [`mmput_async()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1211) so the ETRACK IPI path never executes [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) inline.

```c
/* arch/x86/kernel/cpu/sgx/encl.c:926 */
const cpumask_t *sgx_encl_cpumask(struct sgx_encl *encl)
{
	cpumask_t *cpumask = &encl->cpumask;
	struct sgx_encl_mm *encl_mm;
	int idx;

	cpumask_clear(cpumask);

	idx = srcu_read_lock(&encl->srcu);

	list_for_each_entry_rcu(encl_mm, &encl->mm_list, list) {
		if (!mmget_not_zero(encl_mm->mm))
			continue;

		cpumask_or(cpumask, cpumask, mm_cpumask(encl_mm->mm));

		mmput_async(encl_mm->mm);
	}

	srcu_read_unlock(&encl->srcu, idx);
	...
```

[`iterate_mm_list()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L3043) makes the reclaim case concrete. The MGLRU walker pins each mm with [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) inside [`get_next_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2885) and releases the previous one with [`mmput_async(*iter)`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L3100); running [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) synchronously here would re-enter memory management from inside reclaim.

```c
/* mm/vmscan.c:2885 */
static struct mm_struct *get_next_mm(struct lru_gen_mm_walk *walk)
{
	int key;
	struct mm_struct *mm;
	struct pglist_data *pgdat = lruvec_pgdat(walk->lruvec);
	struct lru_gen_mm_state *mm_state = get_mm_state(walk->lruvec);

	mm = list_entry(mm_state->head, struct mm_struct, lru_gen.list);
	key = pgdat->node_id % BITS_PER_TYPE(mm->lru_gen.bitmap);

	if (!walk->force_scan && !test_bit(key, &mm->lru_gen.bitmap))
		return NULL;

	clear_bit(key, &mm->lru_gen.bitmap);

	return mmget_not_zero(mm) ? mm : NULL;
}
```

### The mmgrab population pins the struct for long-lived observers

semcode's caller index at v7.0 lists 46 functions calling [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) directly (including the [`mmgrab_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88) wrapper and the Rust helper). The population divides into a few shapes. Long-lived subsystem attachments pin the struct for as long as their bookkeeping references it, as in [`kvm_create_vm()`](https://elixir.bootlin.com/linux/v7.0/source/virt/kvm/kvm_main.c#L1105) (paired with [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) in [`kvm_destroy_vm()`](https://elixir.bootlin.com/linux/v7.0/source/virt/kvm/kvm_main.c#L1261)), [`__mmu_notifier_register()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmu_notifier.c#L596), [`__ksm_enter()`](https://elixir.bootlin.com/linux/v7.0/source/mm/ksm.c#L3015), [`__khugepaged_enter()`](https://elixir.bootlin.com/linux/v7.0/source/mm/khugepaged.c#L425), [`__binder_alloc_init()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/android/binder_alloc.c#L1232), [`user_event_mm_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/trace/trace_events_user.c#L705), [`vfio_dma_do_map()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/vfio/vfio_iommu_type1.c#L1681), and [`iommu_sva_domain_alloc()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/iommu/iommu-sva.c#L309). Short critical sections use it to keep a pointer comparison or a field read safe after dropping [`task_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/task.h#L216), as in [`__oom_kill_process()`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L928) and [`vma_start_read()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap_lock.c#L212) (which pins the struct across an RCU-mode per-VMA lock acquisition). The scheduler-adjacent secondary-CPU bring-up code of several architectures grabs [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) for the new idle thread; on x86-64 that role is played by [`sched_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L8599) and the hotplug pair described below.

io_uring pins the submitter's struct purely for accounting. [`io_uring_create()`](https://elixir.bootlin.com/linux/v7.0/source/io_uring/io_uring.c#L2934) explains itself in a comment worth quoting because it names the ordering hazard that makes [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) (rather than [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171)) the right counter for the job, the mm is torn down before the file table at process exit, so an [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) pin held by a file would keep a dead process's address space alive.

```c
/* io_uring/io_uring.c:3000 */
	/*
	 * This is just grabbed for accounting purposes. When a process exits,
	 * the mm is exited and dropped before the files, hence we need to hang
	 * on to this mm purely for the purposes of being able to unaccount
	 * memory (locked/pinned vm). It's not used for anything else.
	 */
	mmgrab(current->mm);
	ctx->mm_account = current->mm;
```

```c
/* io_uring/io_uring.c:2170 */
	if (ctx->mm_account) {
		mmdrop(ctx->mm_account);
		ctx->mm_account = NULL;
	}
```

The /proc/PID/mem implementation is the reference pattern for a long-lived observer. [`proc_mem_open()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L837) converts the temporary user reference from [`mm_access()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1393) into a struct-only pin by pairing [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) with an immediate [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193), so an open file descriptor never holds the target's memory hostage.

```c
/* fs/proc/base.c:830 */
/*
 * proc_mem_open() can return errno, NULL or mm_struct*.
 *
 *   - Returns NULL if the task has no mm (PF_KTHREAD or PF_EXITING)
 *   - Returns mm_struct* on success
 *   - Returns error code on failure
 */
struct mm_struct *proc_mem_open(struct inode *inode, unsigned int mode)
{
	struct task_struct *task = get_proc_task(inode);
	struct mm_struct *mm;

	if (!task)
		return ERR_PTR(-ESRCH);

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

static int __mem_open(struct inode *inode, struct file *file, unsigned int mode)
{
	struct mm_struct *mm = proc_mem_open(inode, mode);

	if (IS_ERR_OR_NULL(mm))
		return mm ? PTR_ERR(mm) : -ESRCH;

	file->private_data = mm;
	return 0;
}
```

Each actual read or write then revives the address space only for the duration of the I/O with [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136), and returns 0 bytes once the target has exited; [`mem_release()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L984) pays the struct pin back with [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) at close.

```c
/* fs/proc/base.c:899 */
static ssize_t mem_rw(struct file *file, char __user *buf,
			size_t count, loff_t *ppos, int write)
{
	struct mm_struct *mm = file->private_data;
	unsigned long addr = *ppos;
	ssize_t copied;
	char *page;
	unsigned int flags;

	if (!mm)
		return 0;

	page = (char *)__get_free_page(GFP_KERNEL);
	if (!page)
		return -ENOMEM;

	copied = 0;
	if (!mmget_not_zero(mm))
		goto free;
	...
```

```c
/* fs/proc/base.c:962 */
static ssize_t mem_write(struct file *file, const char __user *buf,
			 size_t count, loff_t *ppos)
{
	return mem_rw(file, (char __user*)buf, count, ppos, 1);
}
```

```c
/* fs/proc/base.c:984 */
static int mem_release(struct inode *inode, struct file *file)
{
	struct mm_struct *mm = file->private_data;
	if (mm)
		mmdrop(mm);
	return 0;
}

static const struct file_operations proc_mem_operations = {
	.llseek		= mem_lseek,
	.read		= mem_read,
	.write		= mem_write,
	.open		= mem_open,
	.release	= mem_release,
	.fop_flags	= FOP_UNSIGNED_OFFSET,
};
```

[`__oom_kill_process()`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L928) shows the short-lived struct pin. The comment states the purpose, a stable pointer for comparison after [`task_unlock()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/task.h#L222), and the function also calls [`mark_oom_victim()`](https://elixir.bootlin.com/linux/v7.0/source/mm/oom_kill.c#L767) (the [`oom_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/signal.h#L241) pin shown earlier) before paying its own pin back.

```c
/* mm/oom_kill.c:946 */
	/* Get a reference to safely compare mm after task_unlock(victim) */
	mm = victim->mm;
	mmgrab(mm);
	...
	do_send_sig_info(SIGKILL, SEND_SIG_PRIV, victim, PIDTYPE_TGID);
	mark_oom_victim(victim);
	...
	if (can_oom_reap)
		queue_oom_reaper(victim);

	mmdrop(mm);
	put_task_struct(victim);
}
```

### The mmget_not_zero population revives the address space for bounded work

semcode lists 57 direct callers of [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136) at v7.0. They cluster into /proc readers ([`mem_rw()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L899), [`environ_read()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/base.c#L1006), [`m_start()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L275) for the maps files, [`do_procmap_query()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L654)), remote-GUP users that must fault pages into another process ([`async_pf_execute()`](https://elixir.bootlin.com/linux/v7.0/source/virt/kvm/async_pf.c#L45) for KVM async page faults, [`pfn_reader_user_pin()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/iommu/iommufd/pages.c#L876) for iommufd, [`ib_umem_odp_map_dma_and_lock()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/infiniband/core/umem_odp.c#L324) for on-demand-paging RDMA, [`vfio_pin_page_external()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/vfio/vfio_iommu_type1.c#L840)), scanners that iterate mms they only hold struct pins or list membership on ([`get_next_mm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vmscan.c#L2885) in MGLRU, [`try_to_unuse()`](https://elixir.bootlin.com/linux/v7.0/source/mm/swapfile.c#L2399) walking [`mmlist`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1198) at swapoff, [`sgx_reclaimer_age()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/cpu/sgx/main.c#L113)), and GPU/accelerator SVM fault handlers ([`nouveau_svm_fault()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpu/drm/nouveau/nouveau_svm.c#L717), [`svm_migrate_to_ram()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpu/drm/amd/amdkfd/kfd_migrate.c#L941), [`drm_gpusvm_range_find_or_insert()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/gpu/drm/drm_gpusvm.c#L1014)). khugepaged is deliberately absent from this population, as its section below explains.

The KVM async page-fault worker demonstrates both the idiom and its justification in one comment. The VM object holds the struct alive with the [`kvm_create_vm()`](https://elixir.bootlin.com/linux/v7.0/source/virt/kvm/kvm_main.c#L1105) grab, and each worker revives the contents only if the process still runs.

```c
/* virt/kvm/async_pf.c:45 */
static void async_pf_execute(struct work_struct *work)
{
	struct kvm_async_pf *apf =
		container_of(work, struct kvm_async_pf, work);
	struct kvm_vcpu *vcpu = apf->vcpu;
	struct mm_struct *mm = vcpu->kvm->mm;
	unsigned long addr = apf->addr;
	gpa_t cr2_or_gpa = apf->cr2_or_gpa;
	int locked = 1;
	bool first;

	might_sleep();

	/*
	 * Attempt to pin the VM's host address space, and simply skip gup() if
	 * acquiring a pin fail, i.e. if the process is exiting.  Note, KVM
	 * holds a reference to its associated mm_struct until the very end of
	 * kvm_destroy_vm(), i.e. the struct itself won't be freed before this
	 * work item is fully processed.
	 */
	if (mmget_not_zero(mm)) {
		mmap_read_lock(mm);
		get_user_pages_remote(mm, addr, 1, FOLL_WRITE, NULL, &locked);
		if (locked)
			mmap_read_unlock(mm);
		mmput(mm);
	}
	...
```

### The mmput population returns every temporary use

semcode lists 108 direct callers of [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) at v7.0, the union of everything above plus the lifecycle sites. The three references every process lifecycle exercises are [`exit_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L550) (the task's own reference at exit), [`exec_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L837) (the old image's reference at execve), and the fork error path in [`copy_process()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1964) ([`bad_fork_cleanup_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L2499) puts [`p->mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958) at [`kernel/fork.c:2502`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L2502)). The remote-access family pairs it with [`get_task_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1366)/[`mm_access()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1393), as in [`ptrace_access_vm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/ptrace.c#L44), [`access_process_vm()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L7059), [`process_vm_rw_core()`](https://elixir.bootlin.com/linux/v7.0/source/mm/process_vm_access.c#L151), [`get_cmdline()`](https://elixir.bootlin.com/linux/v7.0/source/mm/util.c#L986), the /proc statm/status/stat printers ([`proc_pid_statm()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/array.c#L677), [`do_task_stat()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/array.c#L466)), the uprobes registration walk ([`register_for_each_vma()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/events/uprobes.c#L1272)), the BPF task-VMA iterator ([`task_vma_seq_get_next()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/bpf/task_iter.c#L426)), cpuset's mm migration ([`cpuset_migrate_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/cgroup/cpuset.c#L2535)), and DAMON's virtual-address monitors ([`damon_va_check_accesses()`](https://elixir.bootlin.com/linux/v7.0/source/mm/damon/vaddr.c#L565)).

### task->mm and task->active_mm separate ownership from occupancy

[`Documentation/mm/active_mm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/active_mm.rst) reproduces Linus Torvalds' 1999 mail defining the model, prefixed at v7.0 with a note tying it to the lazy-TLB config. The passages below are the load-bearing ones for this page.

```
Documentation/mm/active_mm.rst:5

Note, the mm_count refcount may no longer include the "lazy" users
(running tasks with ->active_mm == mm && ->mm == NULL) on kernels
with CONFIG_MMU_LAZY_TLB_REFCOUNT=n. Taking and releasing these lazy
references must be done with mmgrab_lazy_tlb() and mmdrop_lazy_tlb()
helpers, which abstract this config option.
```

```
Documentation/mm/active_mm.rst:28

 Basically, the new setup is:

  - we have "real address spaces" and "anonymous address spaces". The
    difference is that an anonymous address space doesn't care about the
    user-level page tables at all, so when we do a context switch into an
    anonymous address space we just leave the previous address space
    active.
...
  - "tsk->mm" points to the "real address space". For an anonymous process,
    tsk->mm will be NULL, for the logical reason that an anonymous process
    really doesn't _have_ a real address space at all.

  - however, we obviously need to keep track of which address space we
    "stole" for such an anonymous user. For that, we have "tsk->active_mm",
    which shows what the currently active address space is.

    The rule is that for a process with a real address space (ie tsk->mm is
    non-NULL) the active_mm obviously always has to be the same as the real
    one.
```

```
Documentation/mm/active_mm.rst:61

 To support all that, the "struct mm_struct" now has two counters: a
 "mm_users" counter that is how many "real address space users" there are,
 and a "mm_count" counter that is the number of "lazy" users (ie anonymous
 users) plus one if there are any real users.

 Usually there is at least one real user, but it could be that the real
 user exited on another CPU while a lazy user was still active, so you do
 actually get cases where you have a address space that is _only_ used by
 lazy users. That is often a short-lived state, because once that thread
 gets scheduled away in favour of a real thread, the "zombie" mm gets
 released because "mm_count" becomes zero.
```

The mail also establishes the [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) rule, "_nobody_ ever has 'init_mm' as a real MM any more. 'init_mm' should be considered just a 'lazy context when no other context is available'", which is why the kernel-thread test is [`!current->mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1575) everywhere rather than a comparison against [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32). The boot thread starts in exactly that state; [`init_task`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L96) is statically born a lazy borrower of the kernel address space.

```c
/* init/init_task.c:114 */
	.mm		= NULL,
	.active_mm	= &init_mm,
```

[`sched_init()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L8599) makes the boot thread's static borrow a counted one before the first context switch can pay it back.

```c
/* kernel/sched/core.c:8761 */
	/*
	 * The boot idle thread does lazy MMU switching as well:
	 */
	mmgrab_lazy_tlb(&init_mm);
	enter_lazy_tlb(&init_mm, current);
```

### context_switch borrows and returns the mm at every kernel-thread boundary

[`context_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5239) is called from [`__schedule()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L6764) at [`kernel/sched/core.c:6911`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L6911) and encodes the whole borrowing protocol in one if/else with a four-row summary comment. Switching to a kernel thread ([`!next->mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5259)) transfers the previous [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) without touching hardware state beyond [`enter_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L987); the reference is taken only when the previous task was a user task ([`prev->mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5263) set), because a kernel-to-kernel switch moves an already-counted borrow from one task to the next and clears [`prev->active_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5266) with no counter movement. Switching to a user task runs [`switch_mm_irqs_off()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c) and, when the previous task was a kernel thread, parks the borrowed mm in [`rq->prev_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/sched.h#L1207) instead of dropping it immediately.

```c
/* kernel/sched/core.c:5252 */
	/*
	 * kernel -> kernel   lazy + transfer active
	 *   user -> kernel   lazy + mmgrab_lazy_tlb() active
	 *
	 * kernel ->   user   switch + mmdrop_lazy_tlb() active
	 *   user ->   user   switch
	 */
	if (!next->mm) {				// to kernel
		enter_lazy_tlb(prev->active_mm, next);

		next->active_mm = prev->active_mm;
		if (prev->mm)				// from user
			mmgrab_lazy_tlb(prev->active_mm);
		else
			prev->active_mm = NULL;
	} else {					// to user
		membarrier_switch_mm(rq, prev->active_mm, next->mm);
		/*
		 * sys_membarrier() requires an smp_mb() between setting
		 * rq->curr / membarrier_switch_mm() and returning to userspace.
		 *
		 * The below provides this either through switch_mm(), or in
		 * case 'prev->active_mm == next->mm' through
		 * finish_task_switch()'s mmdrop().
		 */
		switch_mm_irqs_off(prev->active_mm, next->mm, next);
		lru_gen_use_mm(next->mm);

		if (!prev->mm) {			// from kernel
			/* will mmdrop_lazy_tlb() in finish_task_switch(). */
			rq->prev_mm = prev->active_mm;
			prev->active_mm = NULL;
		}
	}
```

The parked reference is dropped after the stack switch, in [`finish_task_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112), outside the runqueue lock. According to the function comment, "we may have delayed dropping an mm in context_switch(). If so, we finish that here outside of the runqueue lock. (Doing it with the lock held can cause deadlocks; see schedule() for details.)". The drop goes through [`mmdrop_lazy_tlb_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L107), whose full barrier the membarrier system call depends on when a CPU schedules user, kernel, user without ever passing through [`switch_mm_irqs_off()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c).

```c
/* kernel/sched/core.c:5166 */
	fire_sched_in_preempt_notifiers(current);
	/*
	 * When switching through a kernel thread, the loop in
	 * membarrier_{private,global}_expedited() may have observed that
	 * kernel thread and not issued an IPI. It is therefore possible to
	 * schedule between user->kernel->user threads without passing though
	 * switch_mm(). Membarrier requires a barrier after storing to
	 * rq->curr, before returning to userspace, so provide them here:
	 *
	 * - a full memory barrier for {PRIVATE,GLOBAL}_EXPEDITED, implicitly
	 *   provided by mmdrop_lazy_tlb(),
	 * - a sync_core for SYNC_CORE.
	 */
	if (mm) {
		membarrier_mm_sync_core_before_usermode(mm);
		mmdrop_lazy_tlb_sched(mm);
	}
```

The same function also finishes a dying task. [`prev_state == TASK_DEAD`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5183) triggers the final [`put_task_struct_rcu_user()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c), and the dead task's remaining lazy borrow of its own former mm is exactly the [`rq->prev_mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/sched.h#L1207) (next is a user task) or transferred [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) (next is a kernel thread) handled by the code above, so a dead task's last counter movement runs on the CPU that switched away from it.

```c
/* kernel/sched/core.c:6909 */
		/* Also unlocks the rq: */
		rq = context_switch(rq, prev, next, &rf);
```

### enter_lazy_tlb on x86-64 marks the CPU lazy and leaves CR3 loaded

x86 opts out of the generic no-op by defining [`enter_lazy_tlb`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L139) in [`arch/x86/include/asm/mmu_context.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h#L139) and implementing it in [`arch/x86/mm/tlb.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L987). The implementation writes one percpu flag. The borrowed page tables stay loaded in CR3, and the TLB-flush IPI path consults [`cpu_tlbstate_shared.is_lazy`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/tlbflush.h) to skip flushing lazy CPUs and instead force them onto fresh page tables at their next real switch, which is why the lazy borrow needs no TLB work here and why the [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference is the only thing keeping the borrowed pgd valid.

```c
/* arch/x86/mm/tlb.c:974 */
/*
 * Please ignore the name of this function.  It should be called
 * switch_to_kernel_thread().
 *
 * enter_lazy_tlb() is a hint from the scheduler that we are entering a
 * kernel thread or other context without an mm.  Acceptable implementations
 * include doing nothing whatsoever, switching to init_mm, or various clever
 * lazy tricks to try to minimize TLB flushes.
 *
 * The scheduler reserves the right to call enter_lazy_tlb() several times
 * in a row.  It will notify us that we're going back to a real mm by
 * calling switch_mm_irqs_off().
 */
void enter_lazy_tlb(struct mm_struct *mm, struct task_struct *tsk)
{
	if (this_cpu_read(cpu_tlbstate.loaded_mm) == &init_mm)
		return;

	this_cpu_write(cpu_tlbstate_shared.is_lazy, true);
}
```

### CONFIG_MMU_LAZY_TLB_REFCOUNT keeps lazy borrowing refcounted on x86-64

The `_lazy_tlb` helpers exist so that architectures can choose whether a lazy borrow costs an atomic on [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137). [`CONFIG_MMU_LAZY_TLB_REFCOUNT`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L553) defaults to y and turns off only where [`CONFIG_MMU_LAZY_TLB_SHOOTDOWN`](https://elixir.bootlin.com/linux/v7.0/source/arch/Kconfig#L568) is selected; at v7.0 the only selector is powerpc's [`PPC_BOOK3S_64`](https://elixir.bootlin.com/linux/v7.0/source/arch/powerpc/platforms/Kconfig.cputype#L83) ([`arch/powerpc/Kconfig:310`](https://elixir.bootlin.com/linux/v7.0/source/arch/powerpc/Kconfig#L310)), so every x86-64 kernel counts lazy references for real and [`cleanup_lazy_tlbs()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L670) never sends shootdown IPIs there.

```
# arch/Kconfig:539
# Use normal mm refcounting for MMU_LAZY_TLB kernel thread references.
# MMU_LAZY_TLB_REFCOUNT=n can improve the scalability of context switching
# to/from kernel threads when the same mm is running on a lot of CPUs (a large
# multi-threaded application), by reducing contention on the mm refcount.
#
# This can be disabled if the architecture ensures no CPUs are using an mm as a
# "lazy tlb" beyond its final refcount (i.e., by the time __mmdrop frees the mm
# or its kernel page tables). This could be arranged by arch_exit_mmap(), or
# final exit(2) TLB flush, for example.
#
# To implement this, an arch *must*:
# Ensure the _lazy_tlb variants of mmgrab/mmdrop are used when manipulating
# the lazy tlb reference of a kthread's ->active_mm (non-arch code has been
# converted already).
config MMU_LAZY_TLB_REFCOUNT
	def_bool y
	depends on !MMU_LAZY_TLB_SHOOTDOWN
```

On x86-64 the three wrappers therefore compile to [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35), [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47), and [`mmdrop_sched()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L74); the `else` branches document that a shootdown build must still emit the full memory barrier that [`finish_task_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112)'s membarrier comment relies on, because that barrier otherwise comes free with [`atomic_dec_and_test()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/atomic/atomic-instrumented.h#L1380).

```c
/* include/linux/sched/mm.h:87 */
/* Helpers for lazy TLB mm refcounting */
static inline void mmgrab_lazy_tlb(struct mm_struct *mm)
{
	if (IS_ENABLED(CONFIG_MMU_LAZY_TLB_REFCOUNT))
		mmgrab(mm);
}

static inline void mmdrop_lazy_tlb(struct mm_struct *mm)
{
	if (IS_ENABLED(CONFIG_MMU_LAZY_TLB_REFCOUNT)) {
		mmdrop(mm);
	} else {
		/*
		 * mmdrop_lazy_tlb must provide a full memory barrier, see the
		 * membarrier comment finish_task_switch which relies on this.
		 */
		smp_mb();
	}
}

static inline void mmdrop_lazy_tlb_sched(struct mm_struct *mm)
{
	if (IS_ENABLED(CONFIG_MMU_LAZY_TLB_REFCOUNT))
		mmdrop_sched(mm);
	else
		smp_mb(); /* see mmdrop_lazy_tlb() above */
}
```

### exit_mm turns the dying task into a lazy borrower of its own mm

[`do_exit()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L896) calls [`exit_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L550) at [`kernel/exit.c:964`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L964), and the function's own comment states the transformation, "Turn us into a lazy TLB process if we aren't already". The order of operations is the whole point. First [`mmgrab_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88) takes the lazy reference that [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) will keep holding, then [`current->mm`](https://elixir.bootlin.com/linux/v7.0/source/kernel/exit.c#L574) is cleared under [`task_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/task.h#L216) with interrupts off (so a concurrent [`get_task_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1366) either sees the mm and gets a reference or sees NULL), then [`enter_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L987) marks the CPU lazy, and only then does [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) drop the task's user reference, possibly running the entire [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) teardown while the task still runs on the (now zombie) page tables that the lazy [`mm_count`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1137) reference keeps allocated. The final lazy reference is paid back by [`finish_task_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112) or transferred onward after the task's last [`__schedule()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L6764), as the context-switch section above showed.

```c
/* kernel/exit.c:546 */
/*
 * Turn us into a lazy TLB process if we
 * aren't already..
 */
static void exit_mm(void)
{
	struct mm_struct *mm = current->mm;

	exit_mm_release(current, mm);
	if (!mm)
		return;
	mmap_read_lock(mm);
	mmgrab_lazy_tlb(mm);
	BUG_ON(mm != current->active_mm);
	/* more a memory barrier than a real lock */
	task_lock(current);
	/*
	 * When a thread stops operating on an address space, the loop
	 * in membarrier_private_expedited() may not observe that
	 * tsk->mm, and the loop in membarrier_global_expedited() may
	 * not observe a MEMBARRIER_STATE_GLOBAL_EXPEDITED
	 * rq->membarrier_state, so those would not issue an IPI.
	 * Membarrier requires a memory barrier after accessing
	 * user-space memory, before clearing tsk->mm or the
	 * rq->membarrier_state.
	 */
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
	if (test_thread_flag(TIF_MEMDIE))
		exit_oom_victim();
}
```

[`exit_mm_release()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1493) at the top runs the futex and [`mm_release()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1460) bookkeeping (clearing [`clear_child_tid`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L1102) in the still-mapped address space and completing vfork), which is why it must run before [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) can drop.

### exec_mmap swaps in the new mm and settles the old reference

[`begin_new_exec()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L1091) installs the bprm mm at [`fs/exec.c:1148`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L1148) through [`exec_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/fs/exec.c#L837). The function sets both [`tsk->mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958) and [`tsk->active_mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L959) to the new mm under [`task_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/task.h#L216) with interrupts disabled (the comment explains that this shuts out the lazy-TLB counting in concurrent context switches while the two fields disagree), activates the new page tables with [`activate_mm()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/mmu_context.h), and then settles the old reference by kind. A previous user image is released with [`mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1193) (a user reference), while a kernel-thread-style caller that only borrowed its [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) (execve from a task whose mm was already gone) pays with [`mmdrop_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L94) (a lazy struct reference).

```c
/* fs/exec.c:837 */
static int exec_mmap(struct mm_struct *mm)
{
	struct task_struct *tsk;
	struct mm_struct *old_mm, *active_mm;
	int ret;

	/* Notify parent that we're no longer interested in the old VM */
	tsk = current;
	old_mm = current->mm;
	exec_mm_release(tsk, old_mm);
	...
	task_lock(tsk);
	membarrier_exec_mmap(mm);

	local_irq_disable();
	active_mm = tsk->active_mm;
	tsk->active_mm = mm;
	tsk->mm = mm;
	mm_init_cid(mm, tsk);
	/*
	 * This prevents preemption while active_mm is being loaded and
	 * it and mm are being updated, which could cause problems for
	 * lazy tlb mm refcounting when these are updated by context
	 * switches. Not all architectures can handle irqs off over
	 * activate_mm yet.
	 */
	if (!IS_ENABLED(CONFIG_ARCH_WANT_IRQS_OFF_ACTIVATE_MM))
		local_irq_enable();
	activate_mm(active_mm, mm);
	if (IS_ENABLED(CONFIG_ARCH_WANT_IRQS_OFF_ACTIVATE_MM))
		local_irq_enable();
	lru_gen_add_mm(mm);
	task_unlock(tsk);
	lru_gen_use_mm(mm);
	if (old_mm) {
		mmap_read_unlock(old_mm);
		BUG_ON(active_mm != old_mm);
		setmax_mm_hiwater_rss(&tsk->signal->maxrss, old_mm);
		mm_update_next_owner(old_mm);
		mmput(old_mm);
		return 0;
	}
	mmdrop_lazy_tlb(active_mm);
	return 0;
}
```

### CPU hotplug hands the idle task's lazy reference back through finish_cpu

An offlining CPU must leave no lazy borrow behind. [`sched_cpu_wait_empty()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L8473) calls [`sched_force_init_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L8067) on the outgoing CPU, which retargets the hotplug thread's borrow onto [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) (grab the new borrow, switch, drop the old borrow), so whatever user mm the CPU was idling on gets released before the CPU dies.

```c
/* kernel/sched/core.c:8057 */
/*
 * Invoked on the outgoing CPU in context of the CPU hotplug thread
 * after ensuring that there are no user space tasks left on the CPU.
 *
 * If there is a lazy mm in use on the hotplug thread, drop it and
 * switch to init_mm.
 *
 * The reference count on init_mm is dropped in finish_cpu().
 */
static void sched_force_init_mm(void)
{
	struct mm_struct *mm = current->active_mm;

	if (mm != &init_mm) {
		mmgrab_lazy_tlb(&init_mm);
		local_irq_disable();
		current->active_mm = &init_mm;
		switch_mm_irqs_off(mm, &init_mm, current);
		local_irq_enable();
		finish_arch_post_lock_switch();
		mmdrop_lazy_tlb(mm);
	}

	/* finish_cpu(), as ran on the BP, will clean up the active_mm state */
}
```

After the CPU is fully dead, the control processor runs [`finish_cpu()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/cpu.c#L908) as the [`teardown.single`](https://elixir.bootlin.com/linux/v7.0/source/kernel/cpu.c#L136) callback of the [`CPUHP_BRINGUP_CPU`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/cpuhotplug.h#L126) state in [`cpuhp_hp_states`](https://elixir.bootlin.com/linux/v7.0/source/kernel/cpu.c#L2046) ([`kernel/cpu.c:2117`](https://elixir.bootlin.com/linux/v7.0/source/kernel/cpu.c#L2117)), clearing the dead idle task's [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) and dropping the [`init_mm`](https://elixir.bootlin.com/linux/v7.0/source/mm/init-mm.c#L32) lazy reference that [`sched_force_init_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L8067) (or boot) left in place.

```c
/* kernel/cpu.c:908 */
static int finish_cpu(unsigned int cpu)
{
	struct task_struct *idle = idle_thread_get(cpu);
	struct mm_struct *mm = idle->active_mm;

	/*
	 * sched_force_init_mm() ensured the use of &init_mm,
	 * drop that refcount now that the CPU has stopped.
	 */
	WARN_ON(mm != &init_mm);
	idle->active_mm = NULL;
	mmdrop_lazy_tlb(mm);

	return 0;
}
```

```c
/* kernel/cpu.c:2114 */
	[CPUHP_BRINGUP_CPU] = {
		.name			= "cpu:bringup",
		.startup.single		= cpuhp_bringup_ap,
		.teardown.single	= finish_cpu,
		.cant_stop		= true,
	},
```

### kthread_use_mm adopts a user mm and kthread_unuse_mm returns it

[`kthread_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615) lets a [`PF_KTHREAD`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L1774) task become a full user of somebody's address space, turning [`tsk->mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958) non-NULL so that [`copy_to_user()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uaccess.h#L228)/[`copy_from_user()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uaccess.h#L216) and GUP operate on the borrowed mm. The counter choreography is asymmetric on purpose. Entry takes a real [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) on the new mm (the kthread is now a non-lazy occupant) and pays back the lazy reference on whatever mm the kthread had been borrowing with [`mmdrop_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L94). According to the comment, "It is possible for mm to be the same as tsk->active_mm, but we must still mmgrab(mm) and mmdrop_lazy_tlb(active_mm), because these references are not equivalent."

```c
/* kernel/kthread.c:1611 */
/**
 * kthread_use_mm - make the calling kthread operate on an address space
 * @mm: address space to operate on
 */
void kthread_use_mm(struct mm_struct *mm)
{
	struct mm_struct *active_mm;
	struct task_struct *tsk = current;

	WARN_ON_ONCE(!(tsk->flags & PF_KTHREAD));
	WARN_ON_ONCE(tsk->mm);
	WARN_ON_ONCE(!mm->user_ns);

	/*
	 * It is possible for mm to be the same as tsk->active_mm, but
	 * we must still mmgrab(mm) and mmdrop_lazy_tlb(active_mm),
	 * because these references are not equivalent.
	 */
	mmgrab(mm);

	task_lock(tsk);
	/* Hold off tlb flush IPIs while switching mm's */
	local_irq_disable();
	active_mm = tsk->active_mm;
	tsk->active_mm = mm;
	tsk->mm = mm;
	membarrier_update_current_mm(mm);
	switch_mm_irqs_off(active_mm, mm, tsk);
	local_irq_enable();
	task_unlock(tsk);
#ifdef finish_arch_post_lock_switch
	finish_arch_post_lock_switch();
#endif

	/*
	 * When a kthread starts operating on an address space, the loop
	 * in membarrier_{private,global}_expedited() may not observe
	 * that tsk->mm, and not issue an IPI. Membarrier requires a
	 * memory barrier after storing to tsk->mm, before accessing
	 * user-space memory. A full memory barrier for membarrier
	 * {PRIVATE,GLOBAL}_EXPEDITED is implicitly provided by
	 * mmdrop_lazy_tlb().
	 */
	mmdrop_lazy_tlb(active_mm);
}
EXPORT_SYMBOL_GPL(kthread_use_mm);
```

[`kthread_unuse_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1662) mirrors it. The kthread clears [`tsk->mm`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched.h#L958), converts its occupancy back into a lazy borrow with [`mmgrab_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L88) before dropping the real reference with [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47), and calls [`enter_lazy_tlb()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/tlb.c#L987) while [`active_mm`](https://elixir.bootlin.com/linux/v7.0/source/init/init_task.c#L115) still points at the borrowed mm (the comment marks that state). The CPU therefore keeps running on the user's page tables as an ordinary lazy borrower until the next context switch to a user task pays the lazy reference back through [`finish_task_switch()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/sched/core.c#L5112).

```c
/* kernel/kthread.c:1658 */
/**
 * kthread_unuse_mm - reverse the effect of kthread_use_mm()
 * @mm: address space to operate on
 */
void kthread_unuse_mm(struct mm_struct *mm)
{
	struct task_struct *tsk = current;

	WARN_ON_ONCE(!(tsk->flags & PF_KTHREAD));
	WARN_ON_ONCE(!tsk->mm);

	task_lock(tsk);
	/*
	 * When a kthread stops operating on an address space, the loop
	 * in membarrier_{private,global}_expedited() may not observe
	 * that tsk->mm, and not issue an IPI. Membarrier requires a
	 * memory barrier after accessing user-space memory, before
	 * clearing tsk->mm.
	 */
	smp_mb__after_spinlock();
	local_irq_disable();
	tsk->mm = NULL;
	membarrier_update_current_mm(NULL);
	mmgrab_lazy_tlb(mm);
	/* active_mm is still 'mm' */
	enter_lazy_tlb(mm, tsk);
	local_irq_enable();
	task_unlock(tsk);

	mmdrop(mm);
}
EXPORT_SYMBOL_GPL(kthread_unuse_mm);
```

Neither function touches [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171); a caller that needs the address space contents alive across the borrow must hold its own user reference, which every production caller below does.

```
    A vhost kthread borrows the owner's mm (CONFIG_MMU_LAZY_TLB_REFCOUNT=y)
    ────────────────────────────────────────────────────────────────────────
    (u = borrowed mm's mm_users, c = its mm_count; time runs downward)

    owner task (QEMU ioctl)          │ vhost worker kthread
    ─────────────────────────────────┼──────────────────────────────────────
    VHOST_SET_OWNER                  │
      vhost_attach_mm()              │
       = get_task_mm(current)  u+1   │
                                     │ vhost_run_work_kthread_list()
                                     │  kthread_use_mm(dev->mm)
                                     │    mmgrab(mm)                  c+1
                                     │    tsk->mm = mm
                                     │    active_mm = mm
                                     │    switch_mm_irqs_off()
                                     │    mmdrop_lazy_tlb(old)    old c-1
                                     │  copy_to_user()/copy_from_user()
                                     │  ... work loop ...
                                     │  kthread_unuse_mm(dev->mm)
                                     │    tsk->mm = NULL
                                     │    mmgrab_lazy_tlb(mm)         c+1
                                     │    enter_lazy_tlb()
                                     │    mmdrop(mm)                  c-1
                                     │ (CPU stays lazy on mm; the next
                                     │  switch to a user task drops the
                                     │  lazy c reference)              c-1
    VHOST_RESET_OWNER / release      │
      vhost_detach_mm()              │
       = mmput(mm)             u-1   │
```

### vhost, VFIO, and the USB gadget filesystem borrow user mms in production

semcode counts 16 callers of [`kthread_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615) and 15 of [`kthread_unuse_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1662) at v7.0, spread over vhost, VFIO, iommufd, the USB gadget function filesystem and legacy inode gadget, the Intel idxd DMA driver, vdpa_sim, amdkfd and xe GPU workers, arm64 EFI, and KUnit. io_uring stopped using it when io-wq moved to [`CLONE_VM`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/sched.h#L11) worker threads in v5.12, and at v7.0 [`io_uring/`](https://elixir.bootlin.com/linux/v7.0/source/io_uring/) contains no [`kthread_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615) call (its only mm reference is the [`mm_account`](https://elixir.bootlin.com/linux/v7.0/source/io_uring/io_uring.c#L3007) grab shown earlier); usbip contains none either. Three actively maintained users follow, each verified by `git log` on its file.

vhost (the virtio host-side driver in [`drivers/vhost/vhost.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/vhost/vhost.c), substantive commits through 2025 including "vhost: Fix kthread worker cgroup failure handling") captures the owner at [`VHOST_SET_OWNER`](https://elixir.bootlin.com/linux/v7.0/source/include/uapi/linux/vhost.h#L32) time inside [`vhost_dev_set_owner()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/vhost/vhost.c#L1093), and its [`vhost_attach_mm()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/vhost/vhost.c#L680) distinguishes the two counters explicitly. The kthread-worker mode takes a user reference with [`get_task_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1366) because the worker will dereference user memory, while the vDPA mode pins only the struct with [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35); according to the comment, holding a user reference there would risk "deadlock in the case of mmap() which may hold the refcnt of the file and depends on release method to remove vma."

```c
/* drivers/vhost/vhost.c:680 */
static void vhost_attach_mm(struct vhost_dev *dev)
{
	/* No owner, become one */
	if (dev->use_worker) {
		dev->mm = get_task_mm(current);
	} else {
		/* vDPA device does not use worker thread, so there's
		 * no need to hold the address space for mm. This helps
		 * to avoid deadlock in the case of mmap() which may
		 * hold the refcnt of the file and depends on release
		 * method to remove vma.
		 */
		dev->mm = current->mm;
		mmgrab(dev->mm);
	}
}

static void vhost_detach_mm(struct vhost_dev *dev)
{
	if (!dev->mm)
		return;

	if (dev->use_worker)
		mmput(dev->mm);
	else
		mmdrop(dev->mm);
	...
```

```c
/* drivers/vhost/vhost.c:1098 */
	/* Is there an owner already? */
	if (vhost_dev_has_owner(dev)) {
		err = -EBUSY;
		goto err_mm;
	}

	vhost_attach_mm(dev);
```

The legacy kthread worker adopts the owner mm for its whole lifetime rather than per work item.

```c
/* drivers/vhost/vhost.c:400 */
static int vhost_run_work_kthread_list(void *data)
{
	struct vhost_worker *worker = data;
	struct vhost_work *work, *work_next;
	struct vhost_dev *dev = worker->dev;
	struct llist_node *node;

	kthread_use_mm(dev->mm);
	...
```

VFIO's type-1 IOMMU backend (in [`drivers/vfio/vfio_iommu_type1.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/vfio/vfio_iommu_type1.c), substantive commits through 2025 including "vfio/type1: handle DMA map/unmap up to the addressable limit") shows the per-operation borrow with the full three-step choreography, revive the contents with [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136), adopt with [`kthread_use_mm()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/kthread.c#L1615) only when the caller is a kthread ([`current->mm == NULL`](https://elixir.bootlin.com/linux/v7.0/source/drivers/vfio/vfio_iommu_type1.c#L3147)), do the [`copy_to_user()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uaccess.h#L228)/[`copy_from_user()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/uaccess.h#L216), then unwind both.

```c
/* drivers/vfio/vfio_iommu_type1.c:3139 */
static int vfio_iommu_type1_dma_rw_chunk(struct vfio_iommu *iommu,
					 dma_addr_t user_iova, void *data,
					 size_t count, bool write,
					 size_t *copied)
{
	struct mm_struct *mm;
	unsigned long vaddr;
	struct vfio_dma *dma;
	bool kthread = current->mm == NULL;
	size_t offset;

	*copied = 0;

	dma = vfio_find_dma(iommu, user_iova, 1);
	if (!dma)
		return -EINVAL;

	if ((write && !(dma->prot & IOMMU_WRITE)) ||
			!(dma->prot & IOMMU_READ))
		return -EPERM;

	mm = dma->mm;
	if (!mmget_not_zero(mm))
		return -EPERM;

	if (kthread)
		kthread_use_mm(mm);
	else if (current->mm != mm)
		goto out;
	...
	if (kthread)
		kthread_unuse_mm(mm);
out:
	mmput(mm);
	return *copied ? 0 : -EFAULT;
}
```

The USB gadget function filesystem (in [`drivers/usb/gadget/function/f_fs.c`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/gadget/function/f_fs.c), substantive commits through 2026 including the DMA-BUF queue fixes) records the submitter's mm at AIO submission time in [`ffs_epfile_read_iter()`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/gadget/function/f_fs.c#L1277) ([`p->mm = current->mm`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/gadget/function/f_fs.c#L1304), [`drivers/usb/gadget/function/f_fs.c:1304`](https://elixir.bootlin.com/linux/v7.0/source/drivers/usb/gadget/function/f_fs.c#L1304)) and has its completion worker adopt it just long enough to copy the received data into the user's buffers; the AIO framework keeps the mm alive across the request because [`exit_aio()`](https://elixir.bootlin.com/linux/v7.0/source/fs/aio.c#L891) in [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) drains outstanding requests before the address space is torn down.

```c
/* drivers/usb/gadget/function/f_fs.c:859 */
static void ffs_user_copy_worker(struct work_struct *work)
{
	struct ffs_io_data *io_data = container_of(work, struct ffs_io_data,
						   work);
	int ret = io_data->status;
	bool kiocb_has_eventfd = io_data->kiocb->ki_flags & IOCB_EVENTFD;

	if (io_data->read && ret > 0) {
		kthread_use_mm(io_data->mm);
		ret = ffs_copy_to_iter(io_data->buf, ret, &io_data->data);
		kthread_unuse_mm(io_data->mm);
	}

	io_data->kiocb->ki_complete(io_data->kiocb, ret);
	...
```

### khugepaged pins registered mms with mm_count and detects exit through mm_users

khugepaged is the reference user of the "struct pin plus liveness probe" idiom. [`__khugepaged_enter()`](https://elixir.bootlin.com/linux/v7.0/source/mm/khugepaged.c#L425) registers an mm in its scan list with an [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35), so the slot's mm pointer stays dereferenceable regardless of process exit, without keeping any user memory alive.

```c
/* mm/khugepaged.c:425 */
void __khugepaged_enter(struct mm_struct *mm)
{
	struct mm_slot *slot;
	int wakeup;

	/* __khugepaged_exit() must not run from under us */
	VM_BUG_ON_MM(hpage_collapse_test_exit(mm), mm);
	if (unlikely(mm_flags_test_and_set(MMF_VM_HUGEPAGE, mm)))
		return;
	...
	mmgrab(mm);
	if (wakeup)
		wake_up_interruptible(&khugepaged_wait);
}
```

Instead of reviving the address space with [`mmget_not_zero()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L136), the daemon reads [`mm_users`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1171) as a pure liveness probe; [`khugepaged_exit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/khugepaged.h#L29) runs from [`__mmput()`](https://elixir.bootlin.com/linux/v7.0/source/kernel/fork.c#L1167) before [`exit_mmap()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L1275), so a zero reading means the address space is being (or has been) dismantled and the slot must be abandoned. The daemon holds [`mmap_lock`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L1196) while it works, which keeps a nonzero reading meaningful for the duration of a scan.

```c
/* mm/khugepaged.c:390 */
static inline int hpage_collapse_test_exit(struct mm_struct *mm)
{
	return atomic_read(&mm->mm_users) == 0;
}
```

[`collect_mm_slot()`](https://elixir.bootlin.com/linux/v7.0/source/mm/khugepaged.c#L1403) then frees the slot and pays the struct pin back with [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47) once the probe reports exit.

```c
/* mm/khugepaged.c:1403 */
static void collect_mm_slot(struct mm_slot *slot)
{
	struct mm_struct *mm = slot->mm;

	lockdep_assert_held(&khugepaged_mm_lock);

	if (hpage_collapse_test_exit(mm)) {
		/* free mm_slot */
		hash_del(&slot->hash);
		list_del(&slot->mm_node);

		/*
		 * Not strictly needed because the mm exited already.
		 *
		 * mm_flags_clear(MMF_VM_HUGEPAGE, mm);
		 */

		/* khugepaged_mm_lock actually not necessary for the below */
		mm_slot_free(mm_slot_cache, slot);
		mmdrop(mm);
	}
}
```

KSM implements the same idiom with [`__ksm_enter()`](https://elixir.bootlin.com/linux/v7.0/source/mm/ksm.c#L3015) taking the [`mmgrab()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L35) and [`__ksm_exit()`](https://elixir.bootlin.com/linux/v7.0/source/mm/ksm.c#L3058) plus [`scan_get_next_rmap_item()`](https://elixir.bootlin.com/linux/v7.0/source/mm/ksm.c#L2574) paying it back with [`mmdrop()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/sched/mm.h#L47), so the two per-mm scanners age out dead registrations identically.
