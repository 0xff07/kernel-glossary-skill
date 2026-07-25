# x86-64 page-table entries

> CAUTION: AI-GENERATED CONTENT
>
> STRICTLY DO NOT SUBMIT THIS UPSTREAM UNLESS YOU ARE AN EXPERT INTIMATELY FAMILIAR WITH THIS SUBSYSTEM.

An x86-64 hardware page-table entry is one 64-bit word that the kernel wraps in the single-member structs [`pte_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L21), [`pmd_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L22), [`pud_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L368), [`p4d_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L342), and [`pgd_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L295) so that entries from different levels cannot be mixed up by the type checker. Bits 11:0 and 63:52 hold flags defined as [`_PAGE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L51) through [`_PAGE_NX`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L122) from the bit positions [`_PAGE_BIT_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L10) through [`_PAGE_BIT_NX`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L30), the bits in between hold the physical page-frame number extracted by [`PTE_PFN_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L285), and every read, test, construction, and mutation goes through the helpers in [`arch/x86/include/asm/pgtable.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h) such as [`pte_present()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L967), [`pte_pfn()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L264), [`pfn_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738), [`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453), and [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409).

```
    x86-64 4-KiB leaf PTE (the 64-bit word inside pte_t)
    ─────────────────────────────────────────────────────
    (schematic; M = MAXPHYADDR, 36 to 52 depending on CPU)

     63   62      59 58   57   56    52 51     M M-1        12 11     0
    ┌────┬──────────┬────┬────┬─────────┬────────┬─────────────┬────────┐
    │ XD │   PKEY   │SW5 │SW4 │ ignored │ resvd  │ page frame  │ flags  │
    │(63)│ (62:59)  │(58)│(57)│ (56:52) │ (51:M) │  (M-1:12)   │ (11:0) │
    └────┴──────────┴────┴────┴─────────┴────────┴─────────────┴────────┘

    XD   = _PAGE_NX          (_PAGE_BIT_NX, execute-disable)
    PKEY = _PAGE_PKEY_BIT0..3 (_PAGE_BIT_PKEY_BIT0..3, protection key)
    SW5  = _PAGE_SOFTW5      (_PAGE_SAVED_DIRTY on leaves,
                              _PAGE_NOPTISHADOW on root PGDs)
    SW4  = _PAGE_SOFTW4      (software, unused by any owner at v7.0)
    ignored 56:52, reserved 51:M read as 0 (hardware faults if set)
    page frame = physical address >> 12, masked by PTE_PFN_MASK

    flags bits 11:0 expanded (to scale)
    ────────────────────────────────────
    bit    1 1
           1 0 9 8 7 6 5 4 3 2 1 0
          ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐
          │3│2│1│G│F│D│A│C│T│U│W│P│
          └─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘
           │ │ │ │ │ │ │ │ │ │ │ │
    SW3 ───┘ │ │ │ │ │ │ │ │ │ │ │
    SW2 ─────┘ │ │ │ │ │ │ │ │ │ │
    SW1 ───────┘ │ │ │ │ │ │ │ │ │
    G   ─────────┘ │ │ │ │ │ │ │ │
    PAT ───────────┘ │ │ │ │ │ │ │
    D   ─────────────┘ │ │ │ │ │ │
    A   ───────────────┘ │ │ │ │ │
    PCD ─────────────────┘ │ │ │ │
    PWT ───────────────────┘ │ │ │
    U/S ─────────────────────┘ │ │
    R/W ───────────────────────┘ │
    P   ─────────────────────────┘

    P   = _PAGE_PRESENT   (_PAGE_BIT_PRESENT   0)
    R/W = _PAGE_RW        (_PAGE_BIT_RW        1)
    U/S = _PAGE_USER      (_PAGE_BIT_USER      2)
    PWT = _PAGE_PWT       (_PAGE_BIT_PWT       3)
    PCD = _PAGE_PCD       (_PAGE_BIT_PCD       4)
    A   = _PAGE_ACCESSED  (_PAGE_BIT_ACCESSED  5)
    D   = _PAGE_DIRTY     (_PAGE_BIT_DIRTY     6)
    PAT = _PAGE_PAT       (_PAGE_BIT_PAT       7; _PAGE_BIT_PSE on
                           PMD/PUD leaves, where PAT moves to bit 12)
    G   = _PAGE_GLOBAL    (_PAGE_BIT_GLOBAL    8; reused as
                           _PAGE_PROTNONE when P is 0)
    SW1 = _PAGE_SOFTW1    (_PAGE_BIT_SOFTW1    9; _PAGE_SPECIAL)
    SW2 = _PAGE_SOFTW2    (_PAGE_BIT_SOFTW2   10; _PAGE_UFFD_WP)
    SW3 = _PAGE_SOFTW3    (_PAGE_BIT_SOFTW3   11; _PAGE_SOFT_DIRTY
                           or _PAGE_KERNEL_4K on kernel mappings)
```

## SUMMARY

The wrapper types and their raw-value typedefs [`pteval_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L14), [`pmdval_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L15), [`pudval_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L16), [`p4dval_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L17), [`pgdval_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L18), and [`pgprotval_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L19) are all `unsigned long` on x86-64, and the conversion between the wrapper and the raw word is the [`native_pte_val()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L474)/[`native_make_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L469) pair, reached through the [`pte_val()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L117) and [`__pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L118) macros directly on bare metal and through [`pv_ops`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/paravirt.h#L341) indirection under CONFIG_PARAVIRT_XXL. [`pte_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L479) splits the word at [`PTE_FLAGS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L291), the complement of the PFN field bounded by [`__PHYSICAL_MASK_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L50) (52) and narrowed at runtime by [`physical_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L11) when memory encryption steals address bits.

Bits 0 through 8 are hardware-defined (present, writable, user, the PWT/PCD/PAT cache-mode selectors, accessed, dirty, the [`_PAGE_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L58) leaf marker, global), bit 63 is execute-disable, and bits 62:59 carry the memory-protection key under CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS. The software bits are 9, 10, 11, 57, and 58, assigned at v7.0 to [`_PAGE_SPECIAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L65), [`_PAGE_UFFD_WP`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L114), [`_PAGE_SOFT_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L92), [`_PAGE_SOFTW4`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L123) (free), and [`_PAGE_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L137)/[`_PAGE_NOPTISHADOW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L143). A not-present entry reuses the global bit as [`_PAGE_PROTNONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L141), which is why [`pte_present()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L967) tests `_PAGE_PRESENT | _PAGE_PROTNONE` and [`pte_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1001) demands PROTNONE set with PRESENT clear.

The mutators come in three layers. Pure value transforms ([`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453), [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409), [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779)) build a new value from an old one, and on shadow-stack hardware (X86_FEATURE_SHSTK, CONFIG_X86_USER_SHADOW_STACK) they juggle the dirty bit through [`_PAGE_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L137) so that a read-only entry never carries Write=0,Dirty=1, the hardware encoding of shadow-stack memory. In-place stores go through [`set_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L68) down to [`native_set_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L61) (a `WRITE_ONCE()`), and atomic read-modify-write helpers ([`ptep_get_and_clear()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1251), [`ptep_set_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1279)) use `xchg()`/`try_cmpxchg()` because the CPU sets the accessed and dirty bits asynchronously. [`vm_get_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L35) turns a VMA's VM_ flags into the [`pgprot_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293) that constructors like [`pfn_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738) merge with a page-frame number.

Geometry is fixed at 512 entries of 8 bytes per table ([`PTRS_PER_PGD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L51), [`PTRS_PER_PUD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L68), [`PTRS_PER_PMD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L75), [`PTRS_PER_PTE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L80), all 512), and CONFIG_PGTABLE_LEVELS is [5 on x86-64](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L428) with the fifth level folded at runtime when [`pgtable_l5_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L36) reports the CPU booted without CR4.LA57, in which case [`pgdir_shift`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/head64.c#L56) stays 39 and [`ptrs_per_p4d`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/head64.c#L59) stays 1. This page covers the encoding of present entries plus the PROTNONE special case; the software payload encodings of non-present entries (swap, migration, and marker entries) and the allocation and locking of page-table pages are outside its scope.

## SPECIFICATIONS

- Intel 64 and IA-32 Architectures Software Developer's Manual, Volume 3A: paging chapter (4-KByte, 2-MByte, and 1-GByte page-table entry formats, access rights, accessed and dirty flags, protection keys, PAT, and CET shadow-stack pages). Kernel comments in this area cite the manual generically, so no sub-section numbers are reproduced here.
- Intel 64 and IA-32 Architectures Software Developer's Manual, Volume 3, section 4.10.4.3, bullet 3 (Optional Invalidation): the one paging sub-section named exactly in the tree, by the comment above [`spurious_kernel_fault()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L980) in [`arch/x86/mm/fault.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L976).
- AMD64 Architecture Programmer's Manual, Volume 2: System Programming, page-translation chapter. arch/x86 comments reference "the AMD APM" without naming paging section numbers, so none are cited here.

## LINUX KERNEL

### Wrapper types and raw-value accessors (pgtable_64_types.h, pgtable_types.h)

- [`'\<pteval_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L14) / [`'\<pmdval_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L15) / [`'\<pudval_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L16) / [`'\<p4dval_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L17) / [`'\<pgdval_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L18) / [`'\<pgprotval_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L19): raw 64-bit entry values, all `unsigned long`
- [`'\<pte_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L21) / [`'\<pmd_t\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L22): single-member struct wrappers for the two leaf-capable low levels
- [`'\<pud_t\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L368) / [`'\<p4d_t\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L342) / [`'\<pgd_t\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L295) / [`'\<pgprot_t\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293): upper-level wrappers and the protection-bits carrier
- [`'\<native_make_pte\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L469) / [`'\<native_pte_val\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L474): wrap and unwrap the raw word
- [`'\<native_make_pgd\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L326) / [`'\<native_pgd_val\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L331): PGD variants that mask with [`PGD_ALLOWED_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L323) (`~0ULL` on x86-64)
- [`'\<pte_flags\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L479) / [`'\<pmd_flags\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L464) / [`'\<pgd_flags\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L336): extract the non-PFN bits ([`pud_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L446) is the PUD sibling)
- [`'\<pmd_pfn_mask\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L451) / [`'\<pud_pfn_mask\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L433) / [`'\<p4d_pfn_mask\>':'arch/x86/include/asm/pgtable_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L417): per-entry PFN masks that widen when [`_PAGE_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L58) marks a leaf
- [`pte_val`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L117) / [`__pte`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L118) and the sibling `set_pte`/`pgd_val` macros at [`arch/x86/include/asm/pgtable.h:68-118`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L68): alias the native helpers when CONFIG_PARAVIRT_XXL is off; [`'\<pte_val\>':'arch/x86/include/asm/paravirt.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/paravirt.h#L341) routes through [`pv_ops`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/paravirt.h#L341) when it is on

### Hardware flag bits (pgtable_types.h)

- [`_PAGE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L51): bit 0 ([`_PAGE_BIT_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L10)), entry participates in translation
- [`_PAGE_RW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L52): bit 1 ([`_PAGE_BIT_RW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L11)), write permission
- [`_PAGE_USER`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L53): bit 2 ([`_PAGE_BIT_USER`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L12)), CPL 3 may access
- [`_PAGE_PWT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L54) / [`_PAGE_PCD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L55): bits 3 and 4 ([`_PAGE_BIT_PWT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L13), [`_PAGE_BIT_PCD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L14)), low PAT-index bits
- [`_PAGE_ACCESSED`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L56): bit 5 ([`_PAGE_BIT_ACCESSED`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L15)), raised by the CPU on first use
- [`_PAGE_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L57): bit 6 ([`_PAGE_BIT_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L16)), raised by the CPU on first write
- [`_PAGE_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L58): bit 7 ([`_PAGE_BIT_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L17)), 2 MiB/1 GiB leaf at PMD/PUD level; the same bit is [`_PAGE_PAT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L63) ([`_PAGE_BIT_PAT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L18)) on 4 KiB PTEs
- [`_PAGE_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L59): bit 8 ([`_PAGE_BIT_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L19)), TLB entry survives CR3 switches
- [`_PAGE_PAT_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L64): bit 12 ([`_PAGE_BIT_PAT_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L23)), the PAT bit on 2 MiB/1 GiB leaves
- [`_PAGE_NX`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L122): bit 63 ([`_PAGE_BIT_NX`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L30)), execute-disable, masked off by [`x86_configure_nx()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/setup.c#L847) when the CPU lacks X86_FEATURE_NX
- [`_PAGE_PKEY_BIT0`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L69) through `_PAGE_PKEY_BIT3` and [`_PAGE_PKEY_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L80): bits 59-62 ([`_PAGE_BIT_PKEY_BIT0`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L26)), the 4-bit protection key, compiled to 0 without CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS
- [`enum page_cache_mode`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L167): the six software cache modes encoded into PWT/PCD/PAT by [`cachemode2protval()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L493)

### Software flag bits (pgtable_types.h)

- [`_PAGE_SPECIAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L65): bit 9 ([`_PAGE_BIT_SPECIAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L32) = [`_PAGE_BIT_SOFTW1`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L20)), "no struct page behind this PFN", tested by [`vm_normal_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L764)
- [`_PAGE_UFFD_WP`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L114): bit 10 ([`_PAGE_BIT_UFFD_WP`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L34)), userfaultfd write-protect marker under CONFIG_HAVE_ARCH_USERFAULTFD_WP (X86_64 && USERFAULTFD)
- [`_PAGE_SOFT_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L92): bit 11 ([`_PAGE_BIT_SOFT_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L35)), CRIU dirty tracking under CONFIG_MEM_SOFT_DIRTY; the same bit is [`_PAGE_KERNEL_4K`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L67) ([`_PAGE_BIT_KERNEL_4K`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L36)) on kernel mappings that must never be collapsed into large pages
- [`_PAGE_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L137): bit 58 ([`_PAGE_BIT_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L39) = [`_PAGE_BIT_SOFTW5`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L25)), parks the hardware dirty bit while an entry is write-protected so it cannot read as shadow stack
- [`_PAGE_DIRTY_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L139): `_PAGE_DIRTY | _PAGE_SAVED_DIRTY`, the mask every dirty predicate and cleaner uses
- [`_PAGE_PROTNONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L141): bit 8 ([`_PAGE_BIT_PROTNONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L49) = [`_PAGE_BIT_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L19)), marks a PROT_NONE or NUMA-hinting entry while `_PAGE_PRESENT` is clear
- [`_PAGE_NOPTISHADOW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L143): bit 58 on root PGDs ([`_PAGE_BIT_NOPTISHADOW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L40)), tells [`__pti_set_user_pgtbl()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pti.c#L131) not to mirror an entry into the user PTI table
- [`_PAGE_KNL_ERRATUM_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L86): `_PAGE_DIRTY | _PAGE_ACCESSED`, the bits Knights Landing can set spuriously on not-present entries, ignored by [`pte_none()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L948) and [`pmd_none()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1014)
- [`_PAGE_CHG_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L155) / [`_HPAGE_CHG_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L156) / [`_COMMON_PAGE_CHG_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L151): the bits [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) and [`pmd_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L812) preserve across a protection change

### PFN field masks (page_types.h, page_64_types.h)

- [`__PHYSICAL_MASK_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L50): 52, the architectural ceiling on physical-address bits; [`MAX_POSSIBLE_PHYSMEM_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L62) repeats the 52
- [`__PHYSICAL_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_types.h#L48): resolves to the runtime variable [`physical_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L11) under CONFIG_DYNAMIC_PHYSICAL_MASK (selected by CONFIG_X86_MEM_ENCRYPT), which [`sme_enable()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/boot/startup/sme.c#L489) shrinks by the SME encryption bit
- [`PHYSICAL_PAGE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_types.h#L16) / [`PHYSICAL_PMD_PAGE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_types.h#L17) / [`PHYSICAL_PUD_PAGE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_types.h#L18): page-, 2 MiB-, and 1 GiB-aligned physical masks
- [`PTE_PFN_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L285) / [`PTE_FLAGS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L291): the PFN field of a 4 KiB entry and its complement

### Table geometry and the 5-level switch (pgtable_64_types.h, head64.c)

- [`PTRS_PER_PGD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L51) / [`PTRS_PER_P4D`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L58) / [`PTRS_PER_PUD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L68) / [`PTRS_PER_PMD`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L75) / [`PTRS_PER_PTE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L80): 512 entries at every level (PTRS_PER_P4D is the variable [`ptrs_per_p4d`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/head64.c#L59), 1 or 512, bounded by [`MAX_PTRS_PER_P4D`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L57) = 512)
- [`PGDIR_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L50) (the variable [`pgdir_shift`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/head64.c#L56), 39 or 48) / [`P4D_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L56) 39 / [`PUD_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L67) 30 / [`PMD_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L74) 21: virtual-address slice positions
- [`'\<pgtable_l5_enabled\>':'arch/x86/include/asm/pgtable_64_types.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L36): `cpu_feature_enabled(X86_FEATURE_LA57)`, or the [`__pgtable_l5_enabled`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/head64.c#L54) variable in early-boot code compiled with `USE_EARLY_PGTABLE_L5`
- [`'\<check_la57_support\>':'arch/x86/boot/startup/map_kernel.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/boot/startup/map_kernel.c#L17): flips the three geometry variables when CR4.LA57 was set during decompression
- [`'\<p4d_offset\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1136) / [`'\<pgd_present\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1117): fold the fifth level by treating the PGD entry as the P4D when [`pgtable_l5_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L36) is false
- [`pgd_index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L71) / [`'\<p4d_index\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1111): slice a virtual address into 9-bit table indexes; [`pud_index()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L62), [`pmd_index()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L54), and [`pte_index()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L48) follow the same shape

### Predicates (pgtable.h)

- [`'\<pte_present\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L967) / [`'\<pmd_present\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L985): PRESENT or PROTNONE (plus PSE for the PMD, for split THP)
- [`'\<pte_protnone\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1001) / [`'\<pmd_protnone\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1007): PROTNONE set and PRESENT clear, under CONFIG_NUMA_BALANCING
- [`'\<pte_none\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L948) / [`'\<pmd_none\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1014) / [`'\<pte_same\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L954): emptiness modulo the KNL erratum bits, and exact equality
- [`'\<pte_accessible\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L973): PRESENT, or PROTNONE while a TLB flush is pending
- [`'\<pte_write\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L213) / [`'\<pmd_write\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L223): `_PAGE_RW` or a shadow-stack encoding
- [`'\<pte_dirty\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L156) / [`'\<pte_young\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L167): `_PAGE_DIRTY_BITS` and `_PAGE_ACCESSED` tests
- [`'\<pte_shstk\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L161) / [`'\<pmd_shstk\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L183): Write=0,Dirty=1 shadow-stack detectors, gated on X86_FEATURE_SHSTK
- [`'\<pte_special\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L253): `_PAGE_SPECIAL` test
- [`'\<pmd_leaf\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L299) / [`'\<pud_leaf\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1067) / [`'\<pmd_trans_huge\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L305) / [`'\<pud_trans_huge\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L311): `_PAGE_PSE` leaf tests (the trans-huge pair exists under CONFIG_TRANSPARENT_HUGEPAGE)
- [`'\<pte_soft_dirty\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L660) / [`'\<pte_uffd_wp\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L422): software-bit tests
- [`'\<pte_flags_pkey\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1594) / [`'\<__pte_access_permitted\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1621) / [`'\<pte_access_permitted\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1640): pkey extraction and the PRESENT/USER/RW plus PKRU gate

### Constructors and flag mutators (pgtable.h, arch/x86/mm/pgtable.c)

- [`'\<pte_set_flags\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L348) / [`'\<pte_clear_flags\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L355): OR in or mask out flag bits on a value
- [`'\<pte_mkdirty\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453) / [`'\<pte_mkclean\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L438) / [`'\<pte_mkyoung\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L467) / [`'\<pte_mkold\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L443) / [`'\<pte_mkspecial\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L501): A/D and special-bit transitions
- [`'\<pte_wrprotect\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409) / [`'\<pmd_wrprotect\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L524): clear RW and park Dirty in SavedDirty
- [`'\<pte_mkwrite\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802) / [`'\<pmd_mkwrite\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L812): VMA-aware writable transition, routing VM_SHADOW_STACK to [`'\<pte_mkwrite_shstk\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L460) and everything else to [`'\<pte_mkwrite_novma\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L472)
- [`'\<mksaveddirty_shift\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L373) / [`'\<clear_saveddirty_shift\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L383) / [`'\<pte_mksaveddirty\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L393) / [`'\<pte_clear_saveddirty\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L401): branchless Dirty-to-SavedDirty shifting conditioned on the RW bit
- [`'\<pte_mkuffd_wp\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L427) / [`'\<pte_clear_uffd_wp\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L432) / [`'\<pte_clear_soft_dirty\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L690): software-bit transitions
- [`'\<pmd_mkdirty\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L563) / [`'\<pmd_mkyoung\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L582) / [`'\<pmd_mkold\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L553): PMD-level A/D transitions
- [`'\<pte_pfn\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L264) / [`'\<pfn_pte\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738) / [`'\<pfn_pmd\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L749): PFN extraction and entry construction through the PROT_NONE inversion
- [`'\<mk_pte\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L2268) / [`'\<folio_mk_pte\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L2283): page- and folio-based [`pfn_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738) wrappers
- [`'\<pte_modify\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) / [`'\<pmd_modify\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L812): replace protection bits, keep `_PAGE_CHG_MASK` bits
- [`'\<pmd_mkinvalid\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L765): strip PRESENT and PROTNONE for the THP invalidate protocol
- [`'\<pte_advance_pfn\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L959): step the PFN field, inverted-entry aware
- [`'\<massage_pgprot\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L711) / [`'\<check_pgprot\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L721): clamp a pgprot to [`__supported_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L107), warning under CONFIG_DEBUG_VM
- [`'\<maybe_mkwrite\>':'include/linux/mm.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1690): apply [`pte_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802) only when the VMA has VM_WRITE

### PROT_NONE inversion (pgtable-invert.h)

- [`'\<__pte_needs_invert\>':'arch/x86/include/asm/pgtable-invert.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L16): any non-zero, non-present value stores its PFN inverted (L1TF defense)
- [`'\<protnone_mask\>':'arch/x86/include/asm/pgtable-invert.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L22): `~0ull` or 0, XORed into every PFN extraction and construction
- [`'\<flip_protnone_guard\>':'arch/x86/include/asm/pgtable-invert.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L27): flips the PFN field when [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) crosses the present/PROTNONE boundary

### pgprot construction (arch/x86/mm/pgprot.c, pgtable_types.h)

- [`'\<protection_map\>':'arch/x86/mm/pgprot.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L8): 16-entry table from `VM_READ|VM_WRITE|VM_EXEC|VM_SHARED` to a base pgprot
- [`'\<vm_get_page_prot\>':'arch/x86/mm/pgprot.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L35): indexes the map, merges the four `VM_PKEY_BIT*` flags, applies SME and [`__supported_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L107)
- [`'\<add_encrypt_protection_map\>':'arch/x86/mm/pgprot.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L27): folds the SME C-bit into all 16 entries at boot
- [`PAGE_NONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L205) / [`PAGE_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L206) / [`PAGE_COPY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L210) / [`PAGE_READONLY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L211): the user pgprot building blocks (PAGE_NONE is accessed+global with no present bit)
- [`__pgprot_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L245) and [`PAGE_KERNEL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L247): kernel pgprots filtered through [`__default_kernel_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L109)
- [`'\<x86_configure_nx\>':'arch/x86/kernel/setup.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/setup.c#L847) / [`'\<probe_page_size_mask\>':'arch/x86/mm/init.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init.c#L224): trim `_PAGE_NX` and `_PAGE_GLOBAL` out of [`__supported_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L107) per CPU feature
- [`'\<pgprot_modify\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L863) / [`'\<vm_pgprot_modify\>':'mm/vma.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L483) / [`'\<vma_set_page_prot\>':'mm/mmap.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L81): refresh `vma->vm_page_prot` while preserving PAT and encryption bits

### In-place entry updates (pgtable_64.h, pgtable.h, arch/x86/mm/pgtable.c)

- [`'\<native_set_pte\>':'arch/x86/include/asm/pgtable_64.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L61) / [`'\<native_set_pmd\>':'arch/x86/include/asm/pgtable_64.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L77) / [`'\<native_set_pud\>':'arch/x86/include/asm/pgtable_64.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L113) / [`'\<native_pte_clear\>':'arch/x86/include/asm/pgtable_64.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L66): `WRITE_ONCE()` stores of a whole entry
- [`'\<native_set_p4d\>':'arch/x86/include/asm/pgtable_64.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L138) / [`'\<native_set_pgd\>':'arch/x86/include/asm/pgtable_64.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L158): top-level stores that route through [`'\<pti_set_user_pgtbl\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L920) under CONFIG_MITIGATION_PAGE_TABLE_ISOLATION
- [`'\<__pti_set_user_pgtbl\>':'arch/x86/mm/pti.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pti.c#L131): mirrors userspace PGD halves into the PTI user table unless `_PAGE_NOPTISHADOW` says not to
- [`'\<native_ptep_get_and_clear\>':'arch/x86/include/asm/pgtable_64.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L87) / [`'\<ptep_get_and_clear\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1251): atomic `xchg()` with 0 so concurrent hardware A/D updates are not lost
- [`'\<ptep_set_wrprotect\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1279) / [`'\<pmdp_set_wrprotect\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1339): `try_cmpxchg()` loops around [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409)
- [`'\<wrprotect_ptes\>':'include/linux/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L1058): generic loop over [`ptep_set_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1279) for a folio batch
- [`'\<ptep_set_access_flags\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L391) / [`'\<pmdp_set_access_flags\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L404): write the entry only for dirty upgrades, no TLB flush
- [`'\<ptep_test_and_clear_young\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L446): atomic `test_and_clear_bit()` on `_PAGE_BIT_ACCESSED`
- [`'\<pmdp_establish\>':'arch/x86/include/asm/pgtable.h'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1357) / [`'\<pmdp_invalidate_ad\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L520): `xchg()` replacement of a huge PMD, and the invalidate that freezes its A/D bits
- [`'\<arch_check_zapped_pte\>':'arch/x86/mm/pgtable.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L822): warns if a zap removes a shadow-stack entry from a non-shadow-stack VMA
- [`'\<ptep_clear_flush\>':'mm/pgtable-generic.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/pgtable-generic.c#L96): clear plus TLB flush, skipping the flush when [`pte_accessible()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L973) says the TLB cannot hold it

### Fault, NUMA, fork, and mprotect users (mm/, arch/x86/mm/fault.c)

- [`'\<handle_pte_fault\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6273) / [`'\<do_pte_missing\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4472): dispatch on [`pte_none()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L948)/[`pte_present()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L967)/[`pte_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1001), then the [`pte_mkyoung()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L467)/[`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453) tail
- [`'\<do_anonymous_page\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217) / [`'\<wp_page_reuse\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3664) / [`'\<do_wp_page\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4149): entry construction on first touch and write-fault reuse
- [`'\<__copy_present_ptes\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1095) / [`'\<copy_huge_pmd\>':'mm/huge_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L1849): fork write-protects both copies of a COW mapping
- [`'\<zap_present_folio_ptes\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1633): unmap path that harvests [`pte_young()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L167) and runs [`arch_check_zapped_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L822)
- [`'\<do_numa_page\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6048) / [`'\<numa_rebuild_single_mapping\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5994): resolve a PROTNONE NUMA-hinting fault with [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779)
- [`'\<change_pte_range\>':'mm/mprotect.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L214) / [`'\<prot_commit_flush_ptes\>':'mm/mprotect.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L120) / [`'\<change_huge_pmd\>':'mm/huge_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L2558): mprotect and NUMA-hinting rewrites at PTE and PMD level
- [`'\<maybe_change_pte_writable\>':'mm/mprotect.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L41) / [`'\<can_change_shared_pte_writable\>':'mm/mprotect.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L79) / [`'\<can_change_pte_writable\>':'mm/mprotect.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L97): decide whether mprotect may set RW immediately
- [`'\<touch_pmd\>':'mm/huge_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L1776) / [`'\<huge_pmd_set_accessed\>':'mm/huge_memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L2018): PMD-level accessed/dirty refresh
- [`'\<gup_fast_pte_range\>':'mm/gup.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/gup.c#L2829): lockless GUP filtering on [`pte_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1001), [`pte_access_permitted()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1640), and [`pte_special()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L253)
- [`'\<vm_normal_page\>':'mm/memory.c'`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L764): decodes [`pte_special()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L253) into "no struct page"
- [`'\<clear_soft_dirty\>':'fs/proc/task_mmu.c'`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L1616) / [`'\<pte_needs_soft_dirty_wp\>':'mm/internal.h'`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1652): the soft-dirty clear and re-protect cycle
- [`'\<userfaultfd_pte_wp\>':'include/linux/userfaultfd_k.h'`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/userfaultfd_k.h#L194): combines VMA state with [`pte_uffd_wp()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L422)
- [`'\<spurious_kernel_fault\>':'arch/x86/mm/fault.c'`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L980): walks all five levels with the presence predicates after a lazy permission upgrade

## KERNEL DOCUMENTATION

- [`Documentation/arch/x86/x86_64/mm.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/x86/x86_64/mm.rst): the complete 4-level and 5-level virtual memory maps
- [`Documentation/arch/x86/x86_64/5level-paging.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/x86/x86_64/5level-paging.rst): LA57 enablement and the user-space opt-in for addresses above 47 bits
- [`Documentation/mm/page_tables.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/mm/page_tables.rst): the generic pgd/p4d/pud/pmd/pte naming and folding scheme
- [`Documentation/arch/x86/shstk.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/x86/shstk.rst): CET shadow stacks, the Write=0,Dirty=1 encoding's consumer
- [`Documentation/core-api/protection-keys.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/core-api/protection-keys.rst): memory protection keys stored in PTE bits 62:59
- [`Documentation/arch/x86/pti.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/arch/x86/pti.rst): page-table isolation, the consumer of the PGD-level `_PAGE_NOPTISHADOW` bit
- [`Documentation/admin-guide/mm/soft-dirty.rst`](https://elixir.bootlin.com/linux/v7.0/source/Documentation/admin-guide/mm/soft-dirty.rst): the soft-dirty tracking ABI behind `_PAGE_SOFT_DIRTY`

## OTHER SOURCES

- [x86/mm: Introduce _PAGE_SAVED_DIRTY (lore, Rick Edgecombe, June 2023)](https://lore.kernel.org/all/20230613001108.3040476-11-rick.p.edgecombe%40intel.com)
- [x86/mm: Update ptep/pmdp_set_wrprotect() for _PAGE_SAVED_DIRTY (lore, Rick Edgecombe, June 2023)](https://lore.kernel.org/all/20230613001108.3040476-12-rick.p.edgecombe%40intel.com)
- [x86/mm: Warn if create Write=0,Dirty=1 with raw prot (lore, Rick Edgecombe, June 2023)](https://lore.kernel.org/all/20230613001108.3040476-19-rick.p.edgecombe%40intel.com)
- [x86/mm: Add _PAGE_NOPTISHADOW bit to avoid updating userspace page tables (lore, David Woodhouse, December 2024)](https://lore.kernel.org/r/412c90a4df7aef077141d9f68d19cbe5602d6c6d.camel@infradead.org)
- [mm: remove devmap related functions and page table bits (lore, Alistair Popple, June 2025)](https://lkml.kernel.org/r/6389398c32cc9daa3dfcaa9f79c7972525d310ce.1750323463.git-series.apopple@nvidia.com)

## DETAILS

### The wrapper structs make each level a distinct type over the same 64-bit word

Every level of the x86-64 page-table tree stores 512 eight-byte entries per 4096-byte table page, and every entry is an `unsigned long`. The typedefs in [`arch/x86/include/asm/pgtable_64_types.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L11) give the raw value one name per level, and [`pte_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L21) and [`pmd_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L22) wrap the two lowest levels there. According to the comment "These are used to make use of C type-checking..", the only purpose of the wrapping is that passing a [`pmd_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L22) where a [`pte_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L21) is expected becomes a compile error even though both are one `unsigned long`.

```c
/* arch/x86/include/asm/pgtable_64_types.h:11 */
/*
 * These are used to make use of C type-checking..
 */
typedef unsigned long	pteval_t;
typedef unsigned long	pmdval_t;
typedef unsigned long	pudval_t;
typedef unsigned long	p4dval_t;
typedef unsigned long	pgdval_t;
typedef unsigned long	pgprotval_t;

typedef struct { pteval_t pte; } pte_t;
typedef struct { pmdval_t pmd; } pmd_t;
```

[`pgprot_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293) and [`pgd_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L295) are defined in [`arch/x86/include/asm/pgtable_types.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L293), and [`p4d_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L342) and [`pud_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L368) follow behind `CONFIG_PGTABLE_LEVELS` guards that are both true on x86-64, where [`CONFIG_PGTABLE_LEVELS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L428) is 5.

```c
/* arch/x86/include/asm/pgtable_types.h:293 */
typedef struct pgprot { pgprotval_t pgprot; } pgprot_t;

typedef struct { pgdval_t pgd; } pgd_t;
```

```c
/* arch/x86/include/asm/pgtable_types.h:341 */
#if CONFIG_PGTABLE_LEVELS > 4
typedef struct { p4dval_t p4d; } p4d_t;

static inline p4d_t native_make_p4d(pudval_t val)
{
	return (p4d_t) { val };
}

static inline p4dval_t native_p4d_val(p4d_t p4d)
{
	return p4d.p4d;
}
```

```c
/* arch/x86/include/asm/pgtable_types.h:367 */
#if CONFIG_PGTABLE_LEVELS > 3
typedef struct { pudval_t pud; } pud_t;

static inline pud_t native_make_pud(pmdval_t val)
{
	return (pud_t) { val };
}

static inline pudval_t native_pud_val(pud_t pud)
{
	return pud.pud;
}
```

The wrap/unwrap pair for the PTE level also defines [`pte_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L479), which masks the value with [`PTE_FLAGS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L291) so that every flag predicate on this page operates on the non-PFN bits only.

```c
/* arch/x86/include/asm/pgtable_types.h:469 */
static inline pte_t native_make_pte(pteval_t val)
{
	return (pte_t) { .pte = val };
}

static inline pteval_t native_pte_val(pte_t pte)
{
	return pte.pte;
}

static inline pteval_t pte_flags(pte_t pte)
{
	return native_pte_val(pte) & PTE_FLAGS_MASK;
}
```

The PGD variants mask the value with [`PGD_ALLOWED_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L323). That mask exists for 32-bit PAE, where most PGD bits are reserved; on x86-64 (no `CONFIG_X86_PAE`) it is `~0ULL`, so [`native_make_pgd()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L326) and [`native_pgd_val()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L331) pass the word through unchanged, and [`pgd_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L336) applies the same [`PTE_FLAGS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L291) split as the PTE level.

```c
/* arch/x86/include/asm/pgtable_types.h:321 */
#else
/* No need to mask any bits for !PAE */
#define PGD_ALLOWED_BITS	(~0ULL)
#endif

static inline pgd_t native_make_pgd(pgdval_t val)
{
	return (pgd_t) { val & PGD_ALLOWED_BITS };
}

static inline pgdval_t native_pgd_val(pgd_t pgd)
{
	return pgd.pgd & PGD_ALLOWED_BITS;
}

static inline pgdval_t pgd_flags(pgd_t pgd)
{
	return native_pgd_val(pgd) & PTE_FLAGS_MASK;
}
```

Kernel code never calls the `native_*` conversion helpers directly. It uses [`pte_val()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L117), [`__pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L118), [`set_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L68), and their per-level siblings, which [`arch/x86/include/asm/pgtable.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L65) defines as straight aliases when `CONFIG_PARAVIRT_XXL` is off.

```c
/* arch/x86/include/asm/pgtable.h:68 */
#define set_pte(ptep, pte)		native_set_pte(ptep, pte)
...
#define set_pmd(pmdp, pmd)		native_set_pmd(pmdp, pmd)

#ifndef __PAGETABLE_P4D_FOLDED
#define set_pgd(pgdp, pgd)		native_set_pgd(pgdp, pgd)
#define pgd_clear(pgd)			(pgtable_l5_enabled() ? native_pgd_clear(pgd) : 0)
#endif

#ifndef set_p4d
# define set_p4d(p4dp, p4d)		native_set_p4d(p4dp, p4d)
#endif
...
#ifndef set_pud
# define set_pud(pudp, pud)		native_set_pud(pudp, pud)
#endif
...
#define pte_clear(mm, addr, ptep)	native_pte_clear(mm, addr, ptep)
#define pmd_clear(pmd)			native_pmd_clear(pmd)

#define pgd_val(x)	native_pgd_val(x)
#define __pgd(x)	native_make_pgd(x)
...
#define pte_val(x)	native_pte_val(x)
#define __pte(x)	native_make_pte(x)
```

With `CONFIG_PARAVIRT_XXL` (a Xen PV kernel), the same names become [`pv_ops`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/paravirt.h#L341) calls, patched back to a register move on bare metal by the `ALT_NOT_XEN` alternative. The indirection exists because a Xen PV guest stores machine frame numbers in its page tables and must translate on every wrap and unwrap.

```c
/* arch/x86/include/asm/paravirt.h:335 */
static inline pte_t __pte(pteval_t val)
{
	return (pte_t) { PVOP_ALT_CALLEE1(pteval_t, pv_ops, mmu.make_pte, val,
					  "mov %%rdi, %%rax", ALT_NOT_XEN) };
}

static inline pteval_t pte_val(pte_t pte)
{
	return PVOP_ALT_CALLEE1(pteval_t, pv_ops, mmu.pte_val, pte.pte,
				"mov %%rdi, %%rax", ALT_NOT_XEN);
}
```

### PTE_PFN_MASK bounds the physical-address field at 52 bits

[`__PHYSICAL_MASK_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L50) is 52 in [`arch/x86/include/asm/page_64_types.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L50), the architectural maximum for MAXPHYADDR, and [`MAX_POSSIBLE_PHYSMEM_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L62) states the same 52 in [`arch/x86/include/asm/pgtable_64_types.h:62`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L62). The next line also fixes [`__VIRTUAL_MASK_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_64_types.h#L51) at 56 or 47 depending on [`pgtable_l5_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L36).

```c
/* arch/x86/include/asm/page_64_types.h:50 */
#define __PHYSICAL_MASK_SHIFT	52
#define __VIRTUAL_MASK_SHIFT	(pgtable_l5_enabled() ? 56 : 47)
```

[`__PHYSICAL_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_types.h#L48) is that many one-bits, but under `CONFIG_DYNAMIC_PHYSICAL_MASK` (selected by [`CONFIG_X86_MEM_ENCRYPT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L1500)) it resolves to the runtime variable [`physical_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L11), because SME and TDX repurpose the top implemented physical-address bit as an encryption marker that must never be treated as part of the PFN.

```c
/* arch/x86/include/asm/page_types.h:46 */
#ifdef CONFIG_DYNAMIC_PHYSICAL_MASK
extern phys_addr_t physical_mask;
#define __PHYSICAL_MASK		physical_mask
#else
#define __PHYSICAL_MASK		((phys_addr_t)((1ULL << __PHYSICAL_MASK_SHIFT) - 1))
#endif
```

```c
/* arch/x86/mm/pgtable.c:11 */
phys_addr_t physical_mask __ro_after_init = (1ULL << __PHYSICAL_MASK_SHIFT) - 1;
```

[`sme_enable()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/boot/startup/sme.c#L489) removes the AMD SME C-bit from the mask during early boot, at the same time it publishes the bit as [`sme_me_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mem_encrypt_amd.c#L42) (the value behind the [`_PAGE_ENC`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L180) and [`_PAGE_CC`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L179) pgprot components).

```c
/* arch/x86/boot/startup/sme.c:564 */
	sme_me_mask	= me_mask;
	physical_mask	&= ~me_mask;
	cc_vendor	= CC_VENDOR_AMD;
	cc_set_mask(me_mask);
}
```

[`PHYSICAL_PAGE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_types.h#L16) intersects the physical mask with the 4 KiB [`PAGE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/include/vdso/page.h#L28) (page size is 4096, [`PAGE_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/include/vdso/page.h#L13) = `CONFIG_PAGE_SHIFT` = 12 on x86-64), producing the bits M-1:12; the PMD and PUD versions align at 2 MiB and 1 GiB for leaf entries.

```c
/* arch/x86/include/asm/page_types.h:13 */
/* Cast P*D_MASK to a signed type so that it is sign-extended if
   virtual addresses are 32-bits but physical addresses are larger
   (ie, 32-bit PAE). */
#define PHYSICAL_PAGE_MASK	(((signed long)PAGE_MASK) & __PHYSICAL_MASK)
#define PHYSICAL_PMD_PAGE_MASK	(((signed long)PMD_MASK) & __PHYSICAL_MASK)
#define PHYSICAL_PUD_PAGE_MASK	(((signed long)PUD_MASK) & __PHYSICAL_MASK)
```

[`PTE_PFN_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L285) casts that to [`pteval_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L14) and [`PTE_FLAGS_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L291) is its complement, so the flags side includes the protection-key bits by construction.

```c
/* arch/x86/include/asm/pgtable_types.h:284 */
/* Extracts the PFN from a (pte|pmd|pud|pgd)val_t of a 4KB page */
#define PTE_PFN_MASK		((pteval_t)PHYSICAL_PAGE_MASK)

/*
 *  Extracts the flags from a (pte|pmd|pud|pgd)val_t
 *  This includes the protection key value.
 */
#define PTE_FLAGS_MASK		(~PTE_PFN_MASK)
```

At the PMD, PUD, and P4D levels the boundary between PFN and flags depends on whether the entry is a leaf. [`pmd_pfn_mask()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L451) returns the 2 MiB-aligned mask when [`_PAGE_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L58) is set (a leaf maps a 2 MiB frame, and bit 12 becomes [`_PAGE_PAT_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L64) rather than an address bit) and the 4 KiB mask when the entry points at a page table. [`pud_pfn_mask()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L433) does the same at 1 GiB, and [`p4d_pfn_mask()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L417) has no leaf case because, per its comment, there are no 512 GiB huge pages.

```c
/* arch/x86/include/asm/pgtable_types.h:451 */
static inline pmdval_t pmd_pfn_mask(pmd_t pmd)
{
	if (native_pmd_val(pmd) & _PAGE_PSE)
		return PHYSICAL_PMD_PAGE_MASK;
	else
		return PTE_PFN_MASK;
}

static inline pmdval_t pmd_flags_mask(pmd_t pmd)
{
	return ~pmd_pfn_mask(pmd);
}

static inline pmdval_t pmd_flags(pmd_t pmd)
{
	return native_pmd_val(pmd) & pmd_flags_mask(pmd);
}
```

```c
/* arch/x86/include/asm/pgtable_types.h:417 */
static inline p4dval_t p4d_pfn_mask(p4d_t p4d)
{
	/* No 512 GiB huge pages yet */
	return PTE_PFN_MASK;
}

static inline p4dval_t p4d_flags_mask(p4d_t p4d)
{
	return ~p4d_pfn_mask(p4d);
}

static inline p4dval_t p4d_flags(p4d_t p4d)
{
	return native_p4d_val(p4d) & p4d_flags_mask(p4d);
}
```

```c
/* arch/x86/include/asm/pgtable_types.h:433 */
static inline pudval_t pud_pfn_mask(pud_t pud)
{
	if (native_pud_val(pud) & _PAGE_PSE)
		return PHYSICAL_PUD_PAGE_MASK;
	else
		return PTE_PFN_MASK;
}

static inline pudval_t pud_flags_mask(pud_t pud)
{
	return ~pud_pfn_mask(pud);
}

static inline pudval_t pud_flags(pud_t pud)
{
	return native_pud_val(pud) & pud_flags_mask(pud);
}
```

### The bit-position constants assign nine hardware bits, five software bits, and one alias

All bit positions are defined once at the top of [`arch/x86/include/asm/pgtable_types.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L10). Bits 0 through 8 are hardware semantics, bits 9 through 11 are ignored by hardware and free for the kernel ([`_PAGE_BIT_SOFTW1`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L20) to [`_PAGE_BIT_SOFTW3`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L22)), bit 7 doubles as [`_PAGE_BIT_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L17) on PMD/PUD entries and [`_PAGE_BIT_PAT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L18) on 4 KiB PTEs, and the high software bits occupy 57 and 58 inside the 62:52 region the hardware ignores. The software-bit owners are declared immediately below as aliases, including the [`_PAGE_BIT_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L39)/[`_PAGE_BIT_NOPTISHADOW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L40) pair, which share bit 58 without conflict because the former only appears on leaf entries and the latter only on root PGD entries.

```c
/* arch/x86/include/asm/pgtable_types.h:10 */
#define _PAGE_BIT_PRESENT	0	/* is present */
#define _PAGE_BIT_RW		1	/* writeable */
#define _PAGE_BIT_USER		2	/* userspace addressable */
#define _PAGE_BIT_PWT		3	/* page write through */
#define _PAGE_BIT_PCD		4	/* page cache disabled */
#define _PAGE_BIT_ACCESSED	5	/* was accessed (raised by CPU) */
#define _PAGE_BIT_DIRTY		6	/* was written to (raised by CPU) */
#define _PAGE_BIT_PSE		7	/* 4 MB (or 2MB) page */
#define _PAGE_BIT_PAT		7	/* on 4KB pages */
#define _PAGE_BIT_GLOBAL	8	/* Global TLB entry PPro+ */
#define _PAGE_BIT_SOFTW1	9	/* available for programmer */
#define _PAGE_BIT_SOFTW2	10	/* " */
#define _PAGE_BIT_SOFTW3	11	/* " */
#define _PAGE_BIT_PAT_LARGE	12	/* On 2MB or 1GB pages */
#define _PAGE_BIT_SOFTW4	57	/* available for programmer */
#define _PAGE_BIT_SOFTW5	58	/* available for programmer */
#define _PAGE_BIT_PKEY_BIT0	59	/* Protection Keys, bit 1/4 */
#define _PAGE_BIT_PKEY_BIT1	60	/* Protection Keys, bit 2/4 */
#define _PAGE_BIT_PKEY_BIT2	61	/* Protection Keys, bit 3/4 */
#define _PAGE_BIT_PKEY_BIT3	62	/* Protection Keys, bit 4/4 */
#define _PAGE_BIT_NX		63	/* No execute: only valid after cpuid check */

#define _PAGE_BIT_SPECIAL	_PAGE_BIT_SOFTW1
#define _PAGE_BIT_CPA_TEST	_PAGE_BIT_SOFTW1
#define _PAGE_BIT_UFFD_WP	_PAGE_BIT_SOFTW2 /* userfaultfd wrprotected */
#define _PAGE_BIT_SOFT_DIRTY	_PAGE_BIT_SOFTW3 /* software dirty tracking */
#define _PAGE_BIT_KERNEL_4K	_PAGE_BIT_SOFTW3 /* page must not be converted to large */

#ifdef CONFIG_X86_64
#define _PAGE_BIT_SAVED_DIRTY	_PAGE_BIT_SOFTW5 /* Saved Dirty bit (leaf) */
#define _PAGE_BIT_NOPTISHADOW	_PAGE_BIT_SOFTW5 /* No PTI shadow (root PGD) */
#else
/* Shared with _PAGE_BIT_UFFD_WP which is not supported on 32 bit */
#define _PAGE_BIT_SAVED_DIRTY	_PAGE_BIT_SOFTW2 /* Saved Dirty bit (leaf) */
#define _PAGE_BIT_NOPTISHADOW	_PAGE_BIT_SOFTW2 /* No PTI shadow (root PGD) */
#endif

/* If _PAGE_BIT_PRESENT is clear, we use these: */
/* - if the user mapped it with PROT_NONE; pte_present gives true */
#define _PAGE_BIT_PROTNONE	_PAGE_BIT_GLOBAL
```

Bit 9 carries two aliases. [`_PAGE_BIT_SPECIAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L32) marks user PTEs whose PFN has no [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L79) that the mm may touch, and [`_PAGE_BIT_CPA_TEST`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L33) is a self-test marker for the change-page-attribute code (CONFIG_CPA_DEBUG); the two never meet because the first appears only on user mappings and the second only on kernel mappings. Bit 11 likewise serves as [`_PAGE_BIT_SOFT_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L35) on user PTEs and as [`_PAGE_BIT_KERNEL_4K`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L36) on kernel PTEs that must stay 4 KiB.

The value macros shift a 1 to each position with the `_AT(pteval_t, 1)` typed-constant helper, and the protection-key bits compile to 0 when `CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS` is off.

```c
/* arch/x86/include/asm/pgtable_types.h:51 */
#define _PAGE_PRESENT	(_AT(pteval_t, 1) << _PAGE_BIT_PRESENT)
#define _PAGE_RW	(_AT(pteval_t, 1) << _PAGE_BIT_RW)
#define _PAGE_USER	(_AT(pteval_t, 1) << _PAGE_BIT_USER)
#define _PAGE_PWT	(_AT(pteval_t, 1) << _PAGE_BIT_PWT)
#define _PAGE_PCD	(_AT(pteval_t, 1) << _PAGE_BIT_PCD)
#define _PAGE_ACCESSED	(_AT(pteval_t, 1) << _PAGE_BIT_ACCESSED)
#define _PAGE_DIRTY	(_AT(pteval_t, 1) << _PAGE_BIT_DIRTY)
#define _PAGE_PSE	(_AT(pteval_t, 1) << _PAGE_BIT_PSE)
#define _PAGE_GLOBAL	(_AT(pteval_t, 1) << _PAGE_BIT_GLOBAL)
#define _PAGE_SOFTW1	(_AT(pteval_t, 1) << _PAGE_BIT_SOFTW1)
#define _PAGE_SOFTW2	(_AT(pteval_t, 1) << _PAGE_BIT_SOFTW2)
#define _PAGE_SOFTW3	(_AT(pteval_t, 1) << _PAGE_BIT_SOFTW3)
#define _PAGE_PAT	(_AT(pteval_t, 1) << _PAGE_BIT_PAT)
#define _PAGE_PAT_LARGE (_AT(pteval_t, 1) << _PAGE_BIT_PAT_LARGE)
#define _PAGE_SPECIAL	(_AT(pteval_t, 1) << _PAGE_BIT_SPECIAL)
#define _PAGE_CPA_TEST	(_AT(pteval_t, 1) << _PAGE_BIT_CPA_TEST)
#define _PAGE_KERNEL_4K	(_AT(pteval_t, 1) << _PAGE_BIT_KERNEL_4K)
#ifdef CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS
#define _PAGE_PKEY_BIT0	(_AT(pteval_t, 1) << _PAGE_BIT_PKEY_BIT0)
#define _PAGE_PKEY_BIT1	(_AT(pteval_t, 1) << _PAGE_BIT_PKEY_BIT1)
#define _PAGE_PKEY_BIT2	(_AT(pteval_t, 1) << _PAGE_BIT_PKEY_BIT2)
#define _PAGE_PKEY_BIT3	(_AT(pteval_t, 1) << _PAGE_BIT_PKEY_BIT3)
#else
#define _PAGE_PKEY_BIT0	(_AT(pteval_t, 0))
#define _PAGE_PKEY_BIT1	(_AT(pteval_t, 0))
#define _PAGE_PKEY_BIT2	(_AT(pteval_t, 0))
#define _PAGE_PKEY_BIT3	(_AT(pteval_t, 0))
#endif

#define _PAGE_PKEY_MASK (_PAGE_PKEY_BIT0 | \
			 _PAGE_PKEY_BIT1 | \
			 _PAGE_PKEY_BIT2 | \
			 _PAGE_PKEY_BIT3)
```

The four protection-key bits 62:59 select one of 16 keys whose read/write disables are held in the per-thread PKRU register, and [`vm_get_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L35) copies them into the entry from the VMA's [`VM_PKEY_BIT0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L452) group of flags. [`CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L1806) is default-on for 64-bit builds on Intel and AMD CPUs.

Directly after the pkey block comes the Knights Landing erratum mask. On that CPU (and only with `CONFIG_X86_64` or `CONFIG_X86_PAE`) the page walker can plant stray Accessed and Dirty bits in entries whose present bit is clear, so emptiness tests must ignore exactly those two bits.

```c
/* arch/x86/include/asm/pgtable_types.h:85 */
#if defined(CONFIG_X86_64) || defined(CONFIG_X86_PAE)
#define _PAGE_KNL_ERRATUM_MASK (_PAGE_DIRTY | _PAGE_ACCESSED)
#else
#define _PAGE_KNL_ERRATUM_MASK 0
#endif

#ifdef CONFIG_MEM_SOFT_DIRTY
#define _PAGE_SOFT_DIRTY	(_AT(pteval_t, 1) << _PAGE_BIT_SOFT_DIRTY)
#else
#define _PAGE_SOFT_DIRTY	(_AT(pteval_t, 0))
#endif
```

[`_PAGE_UFFD_WP`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L114) exists under `CONFIG_HAVE_ARCH_USERFAULTFD_WP`, which [`arch/x86/Kconfig`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L212) selects for `X86_64 && USERFAULTFD`, and [`_PAGE_NX`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L122) and [`_PAGE_SOFTW4`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L123) are real bits only on 64-bit or PAE builds. No code owns [`_PAGE_SOFTW4`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L123) at v7.0 (its previous owner, the devmap bit, was removed by commit d438d2734170, "mm: remove devmap related functions and page table bits"); it appears only in the software-bits mask of [`pte_flags_need_flush()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/tlbflush.h#L360).

```c
/* arch/x86/include/asm/pgtable_types.h:113 */
#ifdef CONFIG_HAVE_ARCH_USERFAULTFD_WP
#define _PAGE_UFFD_WP		(_AT(pteval_t, 1) << _PAGE_BIT_UFFD_WP)
#define _PAGE_SWP_UFFD_WP	_PAGE_USER
#else
#define _PAGE_UFFD_WP		(_AT(pteval_t, 0))
#define _PAGE_SWP_UFFD_WP	(_AT(pteval_t, 0))
#endif

#if defined(CONFIG_X86_64) || defined(CONFIG_X86_PAE)
#define _PAGE_NX	(_AT(pteval_t, 1) << _PAGE_BIT_NX)
#define _PAGE_SOFTW4	(_AT(pteval_t, 1) << _PAGE_BIT_SOFTW4)
#else
#define _PAGE_NX	(_AT(pteval_t, 0))
#define _PAGE_SOFTW4	(_AT(pteval_t, 0))
#endif
```

The saved-dirty definition follows with the comment that motivates everything in the shadow-stack section below, then [`_PAGE_DIRTY_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L139) (the union both dirtiness predicates test), [`_PAGE_PROTNONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L141), [`_PAGE_NOPTISHADOW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L143), and the three change masks that [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) preserves.

```c
/* arch/x86/include/asm/pgtable_types.h:129 */
/*
 * The hardware requires shadow stack to be Write=0,Dirty=1. However,
 * there are valid cases where the kernel might create read-only PTEs that
 * are dirty (e.g., fork(), mprotect(), uffd-wp(), soft-dirty tracking). In
 * this case, the _PAGE_SAVED_DIRTY bit is used instead of the HW-dirty bit,
 * to avoid creating a wrong "shadow stack" PTEs. Such PTEs have
 * (Write=0,SavedDirty=1,Dirty=0) set.
 */
#define _PAGE_SAVED_DIRTY	(_AT(pteval_t, 1) << _PAGE_BIT_SAVED_DIRTY)

#define _PAGE_DIRTY_BITS (_PAGE_DIRTY | _PAGE_SAVED_DIRTY)

#define _PAGE_PROTNONE	(_AT(pteval_t, 1) << _PAGE_BIT_PROTNONE)

#define _PAGE_NOPTISHADOW (_AT(pteval_t, 1) << _PAGE_BIT_NOPTISHADOW)

/*
 * Set of bits not changed in pte_modify.  The pte's
 * protection key is treated like _PAGE_RW, for
 * instance, and is *not* included in this mask since
 * pte_modify() does modify it.
 */
#define _COMMON_PAGE_CHG_MASK	(PTE_PFN_MASK | _PAGE_PCD | _PAGE_PWT |	\
				 _PAGE_SPECIAL | _PAGE_ACCESSED |	\
				 _PAGE_DIRTY_BITS | _PAGE_SOFT_DIRTY |	\
				 _PAGE_CC | _PAGE_UFFD_WP)
#define _PAGE_CHG_MASK	(_COMMON_PAGE_CHG_MASK | _PAGE_PAT)
#define _HPAGE_CHG_MASK (_COMMON_PAGE_CHG_MASK | _PAGE_PSE | _PAGE_PAT_LARGE)
```

The TLB-flush filter in [`pte_flags_need_flush()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/tlbflush.h#L360) is a compact statement of how every one of these bits behaves. Clearing Present, Dirty, or Accessed needs a flush, changing any hardware permission or cache bit needs a flush, and the five software bits plus [`_PAGE_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L137) never need one because the TLB does not cache them.

```c
/* arch/x86/include/asm/tlbflush.h:360 */
static inline bool pte_flags_need_flush(unsigned long oldflags,
					unsigned long newflags,
					bool ignore_access)
{
	/*
	 * Flags that require a flush when cleared but not when they are set.
	 * Only include flags that would not trigger spurious page-faults.
	 * Non-present entries are not cached. Hardware would set the
	 * dirty/access bit if needed without a fault.
	 */
	const pteval_t flush_on_clear = _PAGE_DIRTY | _PAGE_PRESENT |
					_PAGE_ACCESSED;
	const pteval_t software_flags = _PAGE_SOFTW1 | _PAGE_SOFTW2 |
					_PAGE_SOFTW3 | _PAGE_SOFTW4 |
					_PAGE_SAVED_DIRTY;
	const pteval_t flush_on_change = _PAGE_RW | _PAGE_USER | _PAGE_PWT |
			  _PAGE_PCD | _PAGE_PSE | _PAGE_GLOBAL | _PAGE_PAT |
			  _PAGE_PAT_LARGE | _PAGE_PKEY_BIT0 | _PAGE_PKEY_BIT1 |
			  _PAGE_PKEY_BIT2 | _PAGE_PKEY_BIT3 | _PAGE_NX;
	unsigned long diff = oldflags ^ newflags;
```

The [`_PAGE_KERNEL_4K`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L67) consumer illustrates a software bit gating a hard rule. [`collapse_pmd_page()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pat/set_memory.c#L1245) in the change-page-attribute code refuses to merge 512 PTEs back into one 2 MiB mapping when the first entry carries the bit.

```c
/* arch/x86/mm/pat/set_memory.c:1266 */
	/* The page is 4k intentionally */
	if (pte_flags(first) & _PAGE_KERNEL_4K)
		return 0;
```

### The PAT bit changes position between 4 KiB and large-page entries

The three cache-mode bits select an entry of the Page Attribute Table. On a 4 KiB PTE they are PWT (bit 3), PCD (bit 4), and PAT (bit 7); on a 2 MiB or 1 GiB leaf, bit 7 is occupied by [`_PAGE_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L58), so the PAT bit moves to bit 12 as [`_PAGE_PAT_LARGE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L64). The kernel names the six modes it uses in [`enum page_cache_mode`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L167) and keeps the WB mode at index 0 so that all-bits-clear means write-back.

```c
/* arch/x86/include/asm/pgtable_types.h:166 */
#ifndef __ASSEMBLER__
enum page_cache_mode {
	_PAGE_CACHE_MODE_WB       = 0,
	_PAGE_CACHE_MODE_WC       = 1,
	_PAGE_CACHE_MODE_UC_MINUS = 2,
	_PAGE_CACHE_MODE_UC       = 3,
	_PAGE_CACHE_MODE_WT       = 4,
	_PAGE_CACHE_MODE_WP       = 5,

	_PAGE_CACHE_MODE_NUM      = 8
};
#endif
```

[`__pte2cm_idx()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L484) and [`__cm_idx2pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L488) convert between a 3-bit PAT index and the scattered PWT/PCD/PAT bit positions, [`cachemode2protval()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L493) maps a cache mode through the boot-time PAT programming, and [`protval_4k_2_large()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L495)/[`protval_large_2_4k()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L504) slide the PAT bit between position 7 and position 12 when the change-page-attribute code splits or merges large mappings.

```c
/* arch/x86/include/asm/pgtable_types.h:484 */
#define __pte2cm_idx(cb)				\
	((((cb) >> (_PAGE_BIT_PAT - 2)) & 4) |		\
	 (((cb) >> (_PAGE_BIT_PCD - 1)) & 2) |		\
	 (((cb) >> _PAGE_BIT_PWT) & 1))
#define __cm_idx2pte(i)					\
	((((i) & 4) << (_PAGE_BIT_PAT - 2)) |		\
	 (((i) & 2) << (_PAGE_BIT_PCD - 1)) |		\
	 (((i) & 1) << _PAGE_BIT_PWT))

unsigned long cachemode2protval(enum page_cache_mode pcm);

static inline pgprotval_t protval_4k_2_large(pgprotval_t val)
{
	return (val & ~(_PAGE_PAT | _PAGE_PAT_LARGE)) |
		((val & _PAGE_PAT) << (_PAGE_BIT_PAT_LARGE - _PAGE_BIT_PAT));
}
```

### Every table holds 512 entries, and LA57 adds the fifth level at boot

The shifts and per-table entry counts are fixed in [`arch/x86/include/asm/pgtable_64_types.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L47). Each level consumes 9 bits of virtual address (512 entries), the page offset consumes 12, and the only variable pieces are [`PGDIR_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L50) and [`PTRS_PER_P4D`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L58), which are runtime variables because the same kernel image boots with 4-level and 5-level paging.

```c
/* arch/x86/include/asm/pgtable_64_types.h:47 */
/*
 * PGDIR_SHIFT determines what a top-level page table entry can map
 */
#define PGDIR_SHIFT	pgdir_shift
#define PTRS_PER_PGD	512

/*
 * 4th level page in 5-level paging case
 */
#define P4D_SHIFT		39
#define MAX_PTRS_PER_P4D	512
#define PTRS_PER_P4D		ptrs_per_p4d
#define P4D_SIZE		(_AC(1, UL) << P4D_SHIFT)
#define P4D_MASK		(~(P4D_SIZE - 1))

#define MAX_POSSIBLE_PHYSMEM_BITS	52

/*
 * 3rd level page
 */
#define PUD_SHIFT	30
#define PTRS_PER_PUD	512

/*
 * PMD_SHIFT determines the size of the area a middle-level
 * page table can map
 */
#define PMD_SHIFT	21
#define PTRS_PER_PMD	512

/*
 * entries per page directory level
 */
#define PTRS_PER_PTE	512
```

```
    Virtual-address decomposition into table indexes
    ─────────────────────────────────────────────────

    4-level (LA57 clear): pgdir_shift = 39, ptrs_per_p4d = 1
     47       39 38       30 29       21 20       12 11        0
    ┌───────────┬───────────┬───────────┬───────────┬───────────┐
    │ pgd_index │ pud_index │ pmd_index │ pte_index │ page offs │
    │  (47:39)  │  (38:30)  │  (29:21)  │  (20:12)  │  (11:0)   │
    └───────────┴───────────┴───────────┴───────────┴───────────┘

    5-level (LA57 set): pgdir_shift = 48, ptrs_per_p4d = 512
     56     48 47     39 38     30 29     21 20     12 11      0
    ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
    │pgd_index│p4d_index│pud_index│pmd_index│pte_index│page offs│
    │ (56:48) │ (47:39) │ (38:30) │ (29:21) │ (20:12) │ (11:0)  │
    └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘

    each index selects one of 512 8-byte entries in one 4096-byte
    table page; bits above the top index are the sign extension
```

[`pgtable_l5_enabled()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L36) is the single switch. In normal kernel code it compiles to `cpu_feature_enabled(X86_FEATURE_LA57)` (a static-key test of [`X86_FEATURE_LA57`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/cpufeatures.h#L404)); files compiled before the CPU feature machinery works define `USE_EARLY_PGTABLE_L5` and read the [`__pgtable_l5_enabled`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/head64.c#L54) variable instead.

```c
/* arch/x86/include/asm/pgtable_64_types.h:24 */
extern unsigned int __pgtable_l5_enabled;

#ifdef USE_EARLY_PGTABLE_L5
/*
 * cpu_feature_enabled() is not available in early boot code.
 * Use variable instead.
 */
static inline bool pgtable_l5_enabled(void)
{
	return __pgtable_l5_enabled;
}
#else
#define pgtable_l5_enabled() cpu_feature_enabled(X86_FEATURE_LA57)
#endif /* USE_EARLY_PGTABLE_L5 */
```

The three geometry variables default to the 4-level values in [`arch/x86/kernel/head64.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/head64.c#L54).

```c
/* arch/x86/kernel/head64.c:54 */
unsigned int __pgtable_l5_enabled __ro_after_init;
SYM_PIC_ALIAS(__pgtable_l5_enabled);
unsigned int pgdir_shift __ro_after_init = 39;
EXPORT_SYMBOL(pgdir_shift);
SYM_PIC_ALIAS(pgdir_shift);
unsigned int ptrs_per_p4d __ro_after_init = 1;
EXPORT_SYMBOL(ptrs_per_p4d);
SYM_PIC_ALIAS(ptrs_per_p4d);
```

The decompression stub decides whether to enable LA57 and sets CR4 before the kernel proper runs, so [`check_la57_support()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/boot/startup/map_kernel.c#L17) only has to read CR4 back and flip the variables to 48, 512, and 1. [`__startup_64()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/boot/startup/map_kernel.c#L87) calls it as its first act while building the identity mapping for the kernel image.

```c
/* arch/x86/boot/startup/map_kernel.c:17 */
static inline bool check_la57_support(void)
{
	/*
	 * 5-level paging is detected and enabled at kernel decompression
	 * stage. Only check if it has been enabled there.
	 */
	if (!(native_read_cr4() & X86_CR4_LA57))
		return false;

	__pgtable_l5_enabled	= 1;
	pgdir_shift		= 48;
	ptrs_per_p4d		= 512;

	return true;
}
```

```c
/* arch/x86/boot/startup/map_kernel.c:98 */
	pmdval_t *pmd, pmd_entry;
	bool la57;
	int i;

	la57 = check_la57_support();
```

The index helpers in [`include/linux/pgtable.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L48) slice a virtual address with those shifts. [`pgd_index`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L71) picks up the runtime [`PGDIR_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L50) automatically, and x86 supplies its own [`p4d_index()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1111) over the variable [`PTRS_PER_P4D`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64_types.h#L58).

```c
/* include/linux/pgtable.h:48 */
static inline unsigned long pte_index(unsigned long address)
{
	return (address >> PAGE_SHIFT) & (PTRS_PER_PTE - 1);
}

#ifndef pmd_index
static inline unsigned long pmd_index(unsigned long address)
{
	return (address >> PMD_SHIFT) & (PTRS_PER_PMD - 1);
}
#define pmd_index pmd_index
#endif

#ifndef pud_index
static inline unsigned long pud_index(unsigned long address)
{
	return (address >> PUD_SHIFT) & (PTRS_PER_PUD - 1);
}
#define pud_index pud_index
#endif

#ifndef pgd_index
/* Must be a compile-time constant, so implement it as a macro */
#define pgd_index(a)  (((a) >> PGDIR_SHIFT) & (PTRS_PER_PGD - 1))
#endif
```

```c
/* arch/x86/include/asm/pgtable.h:1111 */
static inline unsigned long p4d_index(unsigned long address)
{
	return (address >> P4D_SHIFT) & (PTRS_PER_P4D - 1);
}
```

Folding happens inside the PGD-level helpers rather than in the walkers. With 4-level paging, [`p4d_offset()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1136) returns the PGD slot pointer itself cast to [`p4d_t`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L342) `*`, and [`pgd_present()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1117)/[`pgd_none()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1156) report a fixed present/not-none answer so a generic five-level walk falls straight through to the P4D level, where the real bits are examined.

```c
/* arch/x86/include/asm/pgtable.h:1117 */
static inline int pgd_present(pgd_t pgd)
{
	if (!pgtable_l5_enabled())
		return 1;
	return pgd_flags(pgd) & _PAGE_PRESENT;
}
...
/* to find an entry in a page-table-directory. */
static inline p4d_t *p4d_offset(pgd_t *pgd, unsigned long address)
{
	if (!pgtable_l5_enabled())
		return (p4d_t *)pgd;
	return (p4d_t *)pgd_page_vaddr(*pgd) + p4d_index(address);
}
```

```c
/* arch/x86/include/asm/pgtable.h:1156 */
static inline int pgd_none(pgd_t pgd)
{
	if (!pgtable_l5_enabled())
		return 0;
	/*
	 * There is no need to do a workaround for the KNL stray
	 * A/D bit erratum here.  PGDs only point to page tables
	 * except on 32-bit non-PAE which is not supported on
	 * KNL.
	 */
	return !native_pgd_val(pgd);
}
```

A full five-level walk using these helpers, and the presence predicates of every level, is [`spurious_kernel_fault()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L980) in [`arch/x86/mm/fault.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L980). The kernel-address fault handler [`do_kern_addr_fault()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L1134) calls it because x86 upgrades kernel-mapping permissions lazily, without a cross-CPU TLB flush, and the comment above the function cites Intel SDM Vol 3 section 4.10.4.3 bullet 3 for why a stale-TLB fault is legal and self-healing.

```c
/* arch/x86/mm/fault.c:1002 */
	pgd = init_mm.pgd + pgd_index(address);
	if (!pgd_present(*pgd))
		return 0;

	p4d = p4d_offset(pgd, address);
	if (!p4d_present(*p4d))
		return 0;

	if (p4d_leaf(*p4d))
		return spurious_kernel_fault_check(error_code, (pte_t *) p4d);

	pud = pud_offset(p4d, address);
	if (!pud_present(*pud))
		return 0;

	if (pud_leaf(*pud))
		return spurious_kernel_fault_check(error_code, (pte_t *) pud);

	pmd = pmd_offset(pud, address);
	if (!pmd_present(*pmd))
		return 0;

	if (pmd_leaf(*pmd))
		return spurious_kernel_fault_check(error_code, (pte_t *) pmd);

	pte = pte_offset_kernel(pmd, address);
	if (!pte_present(*pte))
		return 0;
```

```c
/* arch/x86/mm/fault.c:1178 */
	/* Was the fault spurious, caused by lazy TLB invalidation? */
	if (spurious_kernel_fault(hw_error_code, address))
		return;
```

### pte_present() also accepts PROTNONE, because a PROT_NONE entry is logically mapped

[`_PAGE_BIT_PROTNONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L49) is [`_PAGE_BIT_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L19). The overload is safe because the global bit only means "keep the TLB entry across CR3 writes" while the present bit is set; on a not-present entry the hardware ignores bit 8, so the kernel stores "this range is mapped but with no access rights" there. `mmap(PROT_NONE)` regions and NUMA-hinting entries both use it. A PROTNONE entry still carries its PFN and its other flags, so from the mm's point of view the page is present (rmap sees it, unmap must free it); it just faults on any user access. That is exactly what [`pte_present()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L967) encodes.

```c
/* arch/x86/include/asm/pgtable.h:967 */
static inline int pte_present(pte_t a)
{
	return pte_flags(a) & (_PAGE_PRESENT | _PAGE_PROTNONE);
}

#define pte_accessible pte_accessible
static inline bool pte_accessible(struct mm_struct *mm, pte_t a)
{
	if (pte_flags(a) & _PAGE_PRESENT)
		return true;

	if ((pte_flags(a) & _PAGE_PROTNONE) &&
			atomic_read(&mm->tlb_flush_pending))
		return true;

	return false;
}
```

[`pte_accessible()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L973) answers the narrower question "can the TLB hold this entry". A PROTNONE entry cannot be in the TLB, except during the window in which [`change_pte_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L214) has already written PROTNONE entries but not yet flushed, which the `mm->tlb_flush_pending` counter marks. The generic [`ptep_clear_flush()`](https://elixir.bootlin.com/linux/v7.0/source/mm/pgtable-generic.c#L96) uses it to skip the TLB flush for entries the TLB cannot hold; [`wp_page_copy()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3758) reaches it when replacing a COW page.

```c
/* mm/pgtable-generic.c:96 */
pte_t ptep_clear_flush(struct vm_area_struct *vma, unsigned long address,
		       pte_t *ptep)
{
	struct mm_struct *mm = (vma)->vm_mm;
	pte_t pte;
	pte = ptep_get_and_clear(mm, address, ptep);
	if (pte_accessible(mm, pte))
		flush_tlb_page(vma, address);
	return pte;
}
```

```c
/* mm/memory.c:3840 */
		 * Clear the pte entry and flush it first, before updating the
		 * pte with the new entry, to keep TLBs on different CPUs in
		 * sync. This code used to set the new PTE then flush TLBs, but
		 * that left a window where the new PTE could be loaded into
		 * some TLBs while the old PTE remains in others.
		 */
		ptep_clear_flush(vma, vmf->address, vmf->pte);
```

[`pte_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1001) and [`pmd_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1007) exist under `CONFIG_NUMA_BALANCING` and require PROTNONE set with PRESENT clear, so a present global kernel mapping never matches.

```c
/* arch/x86/include/asm/pgtable.h:996 */
#ifdef CONFIG_NUMA_BALANCING
/*
 * These work without NUMA balancing but the kernel does not care. See the
 * comment in include/linux/pgtable.h
 */
static inline int pte_protnone(pte_t pte)
{
	return (pte_flags(pte) & (_PAGE_PROTNONE | _PAGE_PRESENT))
		== _PAGE_PROTNONE;
}

static inline int pmd_protnone(pmd_t pmd)
{
	return (pmd_flags(pmd) & (_PAGE_PROTNONE | _PAGE_PRESENT))
		== _PAGE_PROTNONE;
}
#endif /* CONFIG_NUMA_BALANCING */
```

[`pmd_present()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L985) adds a third accepted bit, [`_PAGE_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L58), because [`__split_huge_pmd_locked()`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L2988) clears the present bit of a huge PMD for the duration of the split while PSE stays set.

```c
/* arch/x86/include/asm/pgtable.h:985 */
static inline int pmd_present(pmd_t pmd)
{
	/*
	 * Checking for _PAGE_PSE is needed too because
	 * split_huge_page will temporarily clear the present bit (but
	 * the _PAGE_PSE flag will remain set at all times while the
	 * _PAGE_PRESENT bit is clear).
	 */
	return pmd_flags(pmd) & (_PAGE_PRESENT | _PAGE_PROTNONE | _PAGE_PSE);
}
```

Emptiness and equality complete the set. [`pte_none()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L948) masks out [`_PAGE_KNL_ERRATUM_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L86) so a stray Accessed or Dirty bit planted by the Knights Landing erratum does not make a cleared slot look occupied, [`pte_same()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L954) compares raw words, and [`pte_advance_pfn()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L959) steps the PFN field forward, subtracting instead of adding when the entry stores an inverted PFN (next section).

```c
/* arch/x86/include/asm/pgtable.h:948 */
static inline int pte_none(pte_t pte)
{
	return !(pte.pte & ~(_PAGE_KNL_ERRATUM_MASK));
}

#define __HAVE_ARCH_PTE_SAME
static inline int pte_same(pte_t a, pte_t b)
{
	return a.pte == b.pte;
}

static inline pte_t pte_advance_pfn(pte_t pte, unsigned long nr)
{
	if (__pte_needs_invert(pte_val(pte)))
		return __pte(pte_val(pte) - (nr << PFN_PTE_SHIFT));
	return __pte(pte_val(pte) + (nr << PFN_PTE_SHIFT));
}
```

```c
/* arch/x86/include/asm/pgtable.h:1014 */
static inline int pmd_none(pmd_t pmd)
{
	/* Only check low word on 32-bit platforms, since it might be
	   out of sync with upper half. */
	unsigned long val = native_pmd_val(pmd);
	return (val & ~_PAGE_KNL_ERRATUM_MASK) == 0;
}
```

### The flag predicates read one bit each, except the write and dirty tests

The single-flag predicates are defined together in [`arch/x86/include/asm/pgtable.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L152), under a comment that restricts them to present entries. [`pte_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L156) tests both dirty bits at once through [`_PAGE_DIRTY_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L139), so an entry whose hardware dirty bit was parked in [`_PAGE_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L137) by [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409) still reads as dirty. [`pte_shstk()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L161) recognizes the shadow-stack encoding, gated on [`X86_FEATURE_SHSTK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/cpufeatures.h#L396) so pre-CET hardware that (rarely) produced Write=0,Dirty=1 entries is not misread.

```c
/* arch/x86/include/asm/pgtable.h:152 */
/*
 * The following only work if pte_present() is true.
 * Undefined behaviour if not..
 */
static inline bool pte_dirty(pte_t pte)
{
	return pte_flags(pte) & _PAGE_DIRTY_BITS;
}

static inline bool pte_shstk(pte_t pte)
{
	return cpu_feature_enabled(X86_FEATURE_SHSTK) &&
	       (pte_flags(pte) & (_PAGE_RW | _PAGE_DIRTY)) == _PAGE_DIRTY;
}

static inline int pte_young(pte_t pte)
{
	return pte_flags(pte) & _PAGE_ACCESSED;
}
```

```c
/* arch/x86/include/asm/pgtable.h:183 */
static inline bool pmd_shstk(pmd_t pmd)
{
	return cpu_feature_enabled(X86_FEATURE_SHSTK) &&
	       (pmd_flags(pmd) & (_PAGE_RW | _PAGE_DIRTY | _PAGE_PSE)) ==
	       (_PAGE_DIRTY | _PAGE_PSE);
}
```

[`pte_write()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L213) answers "may userspace write here", which is true for [`_PAGE_RW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L52) entries and also for shadow-stack entries, which the CET WRSS/CALL instructions write even though RW is 0.

```c
/* arch/x86/include/asm/pgtable.h:213 */
static inline int pte_write(pte_t pte)
{
	/*
	 * Shadow stack pages are logically writable, but do not have
	 * _PAGE_RW.  Check for them separately from _PAGE_RW itself.
	 */
	return (pte_flags(pte) & _PAGE_RW) || pte_shstk(pte);
}

#define pmd_write pmd_write
static inline int pmd_write(pmd_t pmd)
{
	/*
	 * Shadow stack pages are logically writable, but do not have
	 * _PAGE_RW.  Check for them separately from _PAGE_RW itself.
	 */
	return (pmd_flags(pmd) & _PAGE_RW) || pmd_shstk(pmd);
}
```

The remaining one-bit tests are [`pte_huge()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L238) (PSE), [`pte_global()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L243), [`pte_exec()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L248) (negated NX), and [`pte_special()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L253).

```c
/* arch/x86/include/asm/pgtable.h:238 */
static inline int pte_huge(pte_t pte)
{
	return pte_flags(pte) & _PAGE_PSE;
}

static inline int pte_global(pte_t pte)
{
	return pte_flags(pte) & _PAGE_GLOBAL;
}

static inline int pte_exec(pte_t pte)
{
	return !(pte_flags(pte) & _PAGE_NX);
}

static inline int pte_special(pte_t pte)
{
	return pte_flags(pte) & _PAGE_SPECIAL;
}
```

[`vm_normal_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L764) is the consumer that gives [`pte_special()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L253) its meaning. It feeds the bit into [`__vm_normal_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L696), which returns NULL for special mappings so no code path tries to manipulate a [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L79) for a raw PFN (a VM_PFNMAP BAR mapping, the zero page).

```c
/* mm/memory.c:764 */
struct page *vm_normal_page(struct vm_area_struct *vma, unsigned long addr,
			    pte_t pte)
{
	return __vm_normal_page(vma, addr, pte_pfn(pte), pte_special(pte),
				pte_val(pte), PGTABLE_LEVEL_PTE);
}
```

The leaf tests at PMD and PUD level read [`_PAGE_PSE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L58). [`pmd_leaf()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L299) and [`pud_leaf()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1067) answer "does this entry map memory directly", and the `CONFIG_TRANSPARENT_HUGEPAGE`-only [`pmd_trans_huge()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L305)/[`pud_trans_huge()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L311) are the same bit test written as an exact comparison.

```c
/* arch/x86/include/asm/pgtable.h:298 */
#define pmd_leaf pmd_leaf
static inline bool pmd_leaf(pmd_t pte)
{
	return pmd_flags(pte) & _PAGE_PSE;
}

#ifdef CONFIG_TRANSPARENT_HUGEPAGE
static inline int pmd_trans_huge(pmd_t pmd)
{
	return (pmd_val(pmd) & _PAGE_PSE) == _PAGE_PSE;
}

#ifdef CONFIG_HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD
static inline int pud_trans_huge(pud_t pud)
{
	return (pud_val(pud) & _PAGE_PSE) == _PAGE_PSE;
}
#endif
```

```c
/* arch/x86/include/asm/pgtable.h:1066 */
#define pud_leaf pud_leaf
static inline bool pud_leaf(pud_t pud)
{
	return pud_val(pud) & _PAGE_PSE;
}
```

The `CONFIG_PAGE_TABLE_CHECK` helpers combine the leaf test with the present and user bits; they are the in-header users of [`pmd_leaf()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L299) and [`pud_leaf()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1067) that the page-table checker calls on every entry store.

```c
/* arch/x86/include/asm/pgtable.h:1688 */
static inline bool pmd_user_accessible_page(pmd_t pmd, unsigned long addr)
{
	return pmd_leaf(pmd) && (pmd_val(pmd) & _PAGE_PRESENT) && (pmd_val(pmd) & _PAGE_USER);
}

static inline bool pud_user_accessible_page(pud_t pud, unsigned long addr)
{
	return pud_leaf(pud) && (pud_val(pud) & _PAGE_PRESENT) && (pud_val(pud) & _PAGE_USER);
}
```

The software-bit predicates and their mutators come in config-gated triples. Soft-dirty (under `CONFIG_HAVE_ARCH_SOFT_DIRTY`, always selected by [`arch/x86/Kconfig`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/Kconfig#L32), effective with `CONFIG_MEM_SOFT_DIRTY`):

```c
/* arch/x86/include/asm/pgtable.h:659 */
#ifdef CONFIG_HAVE_ARCH_SOFT_DIRTY
static inline int pte_soft_dirty(pte_t pte)
{
	return pte_flags(pte) & _PAGE_SOFT_DIRTY;
}
...
static inline pte_t pte_mksoft_dirty(pte_t pte)
{
	return pte_set_flags(pte, _PAGE_SOFT_DIRTY);
}
...
static inline pte_t pte_clear_soft_dirty(pte_t pte)
{
	return pte_clear_flags(pte, _PAGE_SOFT_DIRTY);
}
```

[`pte_needs_soft_dirty_wp()`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1652) in [`mm/internal.h`](https://elixir.bootlin.com/linux/v7.0/source/mm/internal.h#L1652) shows the predicate in use; mprotect consults it before making an entry writable, because a clean-tracked page must keep faulting on write so the tracker sees the write.

```c
/* mm/internal.h:1652 */
static inline bool pte_needs_soft_dirty_wp(struct vm_area_struct *vma, pte_t pte)
{
	return vma_soft_dirty_enabled(vma) && !pte_soft_dirty(pte);
}
```

The userfaultfd write-protect triple wraps [`_PAGE_UFFD_WP`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L114), and [`pte_mkuffd_wp()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L427) also write-protects, since the bit's entire point is to keep the entry read-only until userspace resolves the fault.

```c
/* arch/x86/include/asm/pgtable.h:421 */
#ifdef CONFIG_HAVE_ARCH_USERFAULTFD_WP
static inline int pte_uffd_wp(pte_t pte)
{
	return pte_flags(pte) & _PAGE_UFFD_WP;
}

static inline pte_t pte_mkuffd_wp(pte_t pte)
{
	return pte_wrprotect(pte_set_flags(pte, _PAGE_UFFD_WP));
}

static inline pte_t pte_clear_uffd_wp(pte_t pte)
{
	return pte_clear_flags(pte, _PAGE_UFFD_WP);
}
#endif /* CONFIG_HAVE_ARCH_USERFAULTFD_WP */
```

```c
/* include/linux/userfaultfd_k.h:194 */
static inline bool userfaultfd_pte_wp(struct vm_area_struct *vma,
				      pte_t pte)
{
	return userfaultfd_wp(vma) && pte_uffd_wp(pte);
}
```

The protection-key gate combines three hardware bits with the PKRU register. [`pte_flags_pkey()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1594) extracts bits 62:59 as a key number, and [`__pte_access_permitted()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1621) demands PRESENT and USER (plus RW for writes), then asks PKRU whether the key permits the access. The comment notes that the RW requirement also rejects shadow-stack entries. The same helper backs [`pte_access_permitted()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1640), [`pmd_access_permitted()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1646), and [`pud_access_permitted()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1652) because PRESENT, USER, and RW occupy the same positions at every level.

```c
/* arch/x86/include/asm/pgtable.h:1594 */
static inline u16 pte_flags_pkey(unsigned long pte_flags)
{
#ifdef CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS
	/* ifdef to avoid doing 59-bit shift on 32-bit values */
	return (pte_flags & _PAGE_PKEY_MASK) >> _PAGE_BIT_PKEY_BIT0;
#else
	return 0;
#endif
}
```

```c
/* arch/x86/include/asm/pgtable.h:1616 */
/*
 * 'pteval' can come from a PTE, PMD or PUD.  We only check
 * _PAGE_PRESENT, _PAGE_USER, and _PAGE_RW in here which are the
 * same value on all 3 types.
 */
static inline bool __pte_access_permitted(unsigned long pteval, bool write)
{
	unsigned long need_pte_bits = _PAGE_PRESENT|_PAGE_USER;

	/*
	 * Write=0,Dirty=1 PTEs are shadow stack, which the kernel
	 * shouldn't generally allow access to, but since they
	 * are already Write=0, the below logic covers both cases.
	 */
	if (write)
		need_pte_bits |= _PAGE_RW;

	if ((pteval & need_pte_bits) != need_pte_bits)
		return 0;

	return __pkru_allows_pkey(pte_flags_pkey(pteval), write);
}

#define pte_access_permitted pte_access_permitted
static inline bool pte_access_permitted(pte_t pte, bool write)
{
	return __pte_access_permitted(pte_val(pte), write);
}
```

The lockless GUP fast path runs three of these predicates back to back on every candidate entry. [`gup_fast_pte_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/gup.c#L2829) (called per PMD by [`gup_fast_pmd_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/gup.c#L3011)) bails to the slow path on PROTNONE entries, on entries the pkey or permission bits forbid, and on special entries with no [`struct page`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm_types.h#L79).

```c
/* mm/gup.c:2840 */
		pte_t pte = ptep_get_lockless(ptep);
		struct page *page;
		struct folio *folio;

		/*
		 * Always fallback to ordinary GUP on PROT_NONE-mapped pages:
		 * pte_access_permitted() better should reject these pages
		 * either way: otherwise, GUP-fast might succeed in
		 * cases where ordinary GUP would fail due to VMA access
		 * permissions.
		 */
		if (pte_protnone(pte))
			goto pte_unmap;

		if (!pte_access_permitted(pte, flags & FOLL_WRITE))
			goto pte_unmap;

		if (pte_special(pte))
			goto pte_unmap;
```

```c
/* mm/gup.c:3035 */
		} else if (!gup_fast_pte_range(pmd, pmdp, addr, next, flags,
					       pages, nr))
			return 0;
```

### pte_set_flags() and pte_clear_flags() implement every one-bit mutator

All the `pte_mk*` helpers are value transforms; none touches memory. They funnel through one OR and one AND-NOT on the raw word, bypassing [`pte_val()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L117) in favor of the direct [`native_pte_val()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L474)/[`native_make_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L469) pair, because flag flips do not change the PFN and so need no paravirt translation. [`pmd_set_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L124), [`pmd_clear_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L131), [`pud_set_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L138), and [`pud_clear_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L145) repeat the pattern per level.

```c
/* arch/x86/include/asm/pgtable.h:348 */
static inline pte_t pte_set_flags(pte_t pte, pteval_t set)
{
	pteval_t v = native_pte_val(pte);

	return native_make_pte(v | set);
}

static inline pte_t pte_clear_flags(pte_t pte, pteval_t clear)
{
	pteval_t v = native_pte_val(pte);

	return native_make_pte(v & ~clear);
}
```

The accessed/dirty/special transitions are one call each. [`pte_mkclean()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L438) clears both dirty bits at once via [`_PAGE_DIRTY_BITS`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L139), and [`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453) sets the software soft-dirty bit together with the hardware one so CRIU-style tracking never misses a kernel-initiated dirtying (its [`pte_mksaveddirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L393) tail is covered in the shadow-stack section).

```c
/* arch/x86/include/asm/pgtable.h:438 */
static inline pte_t pte_mkclean(pte_t pte)
{
	return pte_clear_flags(pte, _PAGE_DIRTY_BITS);
}

static inline pte_t pte_mkold(pte_t pte)
{
	return pte_clear_flags(pte, _PAGE_ACCESSED);
}

static inline pte_t pte_mkexec(pte_t pte)
{
	return pte_clear_flags(pte, _PAGE_NX);
}

static inline pte_t pte_mkdirty(pte_t pte)
{
	pte = pte_set_flags(pte, _PAGE_DIRTY | _PAGE_SOFT_DIRTY);

	return pte_mksaveddirty(pte);
}
```

```c
/* arch/x86/include/asm/pgtable.h:467 */
static inline pte_t pte_mkyoung(pte_t pte)
{
	return pte_set_flags(pte, _PAGE_ACCESSED);
}

static inline pte_t pte_mkwrite_novma(pte_t pte)
{
	return pte_set_flags(pte, _PAGE_RW);
}
```

```c
/* arch/x86/include/asm/pgtable.h:501 */
static inline pte_t pte_mkspecial(pte_t pte)
{
	return pte_set_flags(pte, _PAGE_SPECIAL);
}
```

The PMD level repeats the same transitions for transparent huge pages; [`pmd_mkold()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L553), [`pmd_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L563), and [`pmd_mkyoung()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L582) are the ones the fault paths below exercise.

```c
/* arch/x86/include/asm/pgtable.h:553 */
static inline pmd_t pmd_mkold(pmd_t pmd)
{
	return pmd_clear_flags(pmd, _PAGE_ACCESSED);
}
...
static inline pmd_t pmd_mkdirty(pmd_t pmd)
{
	pmd = pmd_set_flags(pmd, _PAGE_DIRTY | _PAGE_SOFT_DIRTY);

	return pmd_mksaveddirty(pmd);
}
...
static inline pmd_t pmd_mkyoung(pmd_t pmd)
{
	return pmd_set_flags(pmd, _PAGE_ACCESSED);
}
```

### pfn_pte() XORs the PFN through protnone_mask() to blunt L1TF

Since the L1 Terminal Fault CPU bug, x86-64 never stores a real PFN in a not-present entry, because the L1TF speculation reads the PFN field of a not-present entry straight from the L1 cache. Every entry that is non-zero but lacks [`_PAGE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L51) (a PROTNONE entry included) keeps its PFN field bit-inverted, which points speculation at the top of physical address space where nothing is mapped. The three helpers in [`arch/x86/include/asm/pgtable-invert.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L16) implement the scheme, and the comment above [`__pte_needs_invert()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L16) records that an all-zero value stays uninverted because even [`PAGE_NONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L205) carries `_PAGE_PROTNONE | _PAGE_ACCESSED`.

```c
/* arch/x86/include/asm/pgtable-invert.h:7 */
/*
 * A clear pte value is special, and doesn't get inverted.
 *
 * Note that even users that only pass a pgprot_t (rather
 * than a full pte) won't trigger the special zero case,
 * because even PAGE_NONE has _PAGE_PROTNONE | _PAGE_ACCESSED
 * set. So the all zero case really is limited to just the
 * cleared page table entry case.
 */
static inline bool __pte_needs_invert(u64 val)
{
	return val && !(val & _PAGE_PRESENT);
}

/* Get a mask to xor with the page table entry to get the correct pfn. */
static inline u64 protnone_mask(u64 val)
{
	return __pte_needs_invert(val) ?  ~0ull : 0;
}

static inline u64 flip_protnone_guard(u64 oldval, u64 val, u64 mask)
{
	/*
	 * When a PTE transitions from NONE to !NONE or vice-versa
	 * invert the PFN part to stop speculation.
	 * pte_pfn undoes this when needed.
	 */
	if (__pte_needs_invert(oldval) != __pte_needs_invert(val))
		val = (val & ~mask) | (~val & mask);
	return val;
}
```

[`pte_pfn()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L264) undoes the inversion transparently. It XORs the raw value with [`protnone_mask()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L22) of itself (all-ones for an inverted entry, zero otherwise), masks with [`PTE_PFN_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L285), and shifts by [`PAGE_SHIFT`](https://elixir.bootlin.com/linux/v7.0/source/include/vdso/page.h#L13). [`pmd_pfn()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L271) and [`pud_pfn()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L279) do the same through the PSE-aware masks.

```c
/* arch/x86/include/asm/pgtable.h:258 */
/* Entries that were set to PROT_NONE are inverted */

static inline u64 protnone_mask(u64 val);

#define PFN_PTE_SHIFT	PAGE_SHIFT

static inline unsigned long pte_pfn(pte_t pte)
{
	phys_addr_t pfn = pte_val(pte);
	pfn ^= protnone_mask(pfn);
	return (pfn & PTE_PFN_MASK) >> PAGE_SHIFT;
}

static inline unsigned long pmd_pfn(pmd_t pmd)
{
	phys_addr_t pfn = pmd_val(pmd);
	pfn ^= protnone_mask(pfn);
	return (pfn & pmd_pfn_mask(pmd)) >> PAGE_SHIFT;
}

#define pud_pfn pud_pfn
static inline unsigned long pud_pfn(pud_t pud)
{
	phys_addr_t pfn = pud_val(pud);
	pfn ^= protnone_mask(pfn);
	return (pfn & pud_pfn_mask(pud)) >> PAGE_SHIFT;
}
```

[`pfn_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738) is the constructor. It applies the same XOR based on the pgprot (a PROT_NONE pgprot produces an inverted PFN from the start), validates the pgprot through [`check_pgprot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L721), and warns if the caller hands it the raw shadow-stack combination Dirty=1,Write=0, the guard added by the commit "x86/mm: Warn if create Write=0,Dirty=1 with raw prot".

```c
/* arch/x86/include/asm/pgtable.h:738 */
static inline pte_t pfn_pte(unsigned long page_nr, pgprot_t pgprot)
{
	phys_addr_t pfn = (phys_addr_t)page_nr << PAGE_SHIFT;
	/* This bit combination is used to mark shadow stacks */
	WARN_ON_ONCE((pgprot_val(pgprot) & (_PAGE_DIRTY | _PAGE_RW)) ==
			_PAGE_DIRTY);
	pfn ^= protnone_mask(pgprot_val(pgprot));
	pfn &= PTE_PFN_MASK;
	return __pte(pfn | check_pgprot(pgprot));
}

static inline pmd_t pfn_pmd(unsigned long page_nr, pgprot_t pgprot)
{
	phys_addr_t pfn = (phys_addr_t)page_nr << PAGE_SHIFT;
	pfn ^= protnone_mask(pgprot_val(pgprot));
	pfn &= PHYSICAL_PMD_PAGE_MASK;
	return __pmd(pfn | check_pgprot(pgprot));
}
```

[`massage_pgprot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L711) strips bits the running CPU does not support (NX on non-NX hardware, GLOBAL without PGE) but only from present pgprots, since non-present encodings own those bit positions for other purposes; [`check_pgprot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L721) is the same plus a one-time warning under `CONFIG_DEBUG_VM`.

```c
/* arch/x86/include/asm/pgtable.h:707 */
/*
 * Mask out unsupported bits in a present pgprot.  Non-present pgprots
 * can use those bits for other purposes, so leave them be.
 */
static inline pgprotval_t massage_pgprot(pgprot_t pgprot)
{
	pgprotval_t protval = pgprot_val(pgprot);

	if (protval & _PAGE_PRESENT)
		protval &= __supported_pte_mask;

	return protval;
}

static inline pgprotval_t check_pgprot(pgprot_t pgprot)
{
	pgprotval_t massaged_val = massage_pgprot(pgprot);

	/* mmdebug.h can not be included here because of dependencies */
#ifdef CONFIG_DEBUG_VM
	WARN_ONCE(pgprot_val(pgprot) != massaged_val,
		  "attempted to set unsupported pgprot: %016llx "
		  "bits: %016llx supported: %016llx\n",
		  (u64)pgprot_val(pgprot),
		  (u64)pgprot_val(pgprot) ^ massaged_val,
		  (u64)__supported_pte_mask);
#endif

	return massaged_val;
}
```

Generic mm code reaches [`pfn_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738) through [`mk_pte()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L2268) and [`folio_mk_pte()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L2283) in [`include/linux/mm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L2268).

```c
/* include/linux/mm.h:2268 */
static inline pte_t mk_pte(const struct page *page, pgprot_t pgprot)
{
	return pfn_pte(page_to_pfn(page), pgprot);
}
...
static inline pte_t folio_mk_pte(const struct folio *folio, pgprot_t pgprot)
{
	return pfn_pte(folio_pfn(folio), pgprot);
}
```

[`restore_exclusive_pte()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L881) shows the page-based form, rebuilding a device-exclusive entry as old so the first touch refreshes the accessed bit.

```c
/* mm/memory.c:889 */
	pte = pte_mkold(mk_pte(page, READ_ONCE(vma->vm_page_prot)));
```

A construction that uses [`pfn_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738) and [`pte_mkspecial()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L501) together is the read-fault branch of [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217), which maps the shared zero page read-only and marks it special so nothing ever treats the zero page as an ordinary anonymous page.

```c
/* mm/memory.c:5237 */
	/* Use the zero-page for reads */
	if (!(vmf->flags & FAULT_FLAG_WRITE) &&
			!mm_forbids_zeropage(vma->vm_mm)) {
		entry = pte_mkspecial(pfn_pte(my_zero_pfn(vmf->address),
						vma->vm_page_prot));
```

### pte_modify() replaces the protection bits and keeps _PAGE_CHG_MASK

mprotect and NUMA hinting change an entry's protections without touching its PFN, its A/D state, or its software payload. [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) keeps exactly the [`_PAGE_CHG_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L155) bits (PFN, PCD/PWT/PAT, SPECIAL, ACCESSED, both dirty bits, SOFT_DIRTY, the encryption bit, UFFD_WP), merges everything else from the new pgprot (which is how RW, USER, NX, GLOBAL/PROTNONE, and the pkey change), runs [`flip_protnone_guard()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L27) to re-invert the PFN when the change crosses the present/PROTNONE boundary, and finishes with the saved-dirty shuffle keyed on the old RW bit.

```c
/* arch/x86/include/asm/pgtable.h:779 */
static inline pte_t pte_modify(pte_t pte, pgprot_t newprot)
{
	pteval_t val = pte_val(pte), oldval = val;
	pte_t pte_result;

	/*
	 * Chop off the NX bit (if present), and add the NX portion of
	 * the newprot (if present):
	 */
	val &= _PAGE_CHG_MASK;
	val |= check_pgprot(newprot) & ~_PAGE_CHG_MASK;
	val = flip_protnone_guard(oldval, val, PTE_PFN_MASK);

	pte_result = __pte(val);

	/*
	 * To avoid creating Write=0,Dirty=1 PTEs, pte_modify() needs to avoid:
	 *  1. Marking Write=0 PTEs Dirty=1
	 *  2. Marking Dirty=1 PTEs Write=0
	 *
	 * The first case cannot happen because the _PAGE_CHG_MASK will filter
	 * out any Dirty bit passed in newprot. Handle the second case by
	 * going through the mksaveddirty exercise. Only do this if the old
	 * value was Write=1 to avoid doing this on Shadow Stack PTEs.
	 */
	if (oldval & _PAGE_RW)
		pte_result = pte_mksaveddirty(pte_result);
	else
		pte_result = pte_clear_saveddirty(pte_result);

	return pte_result;
}
```

[`pmd_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L812) is the THP twin over [`_HPAGE_CHG_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L156) (which adds PSE and PAT_LARGE) and [`PHYSICAL_PMD_PAGE_MASK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/page_types.h#L17); [`pud_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L835) completes the set.

```c
/* arch/x86/include/asm/pgtable.h:812 */
static inline pmd_t pmd_modify(pmd_t pmd, pgprot_t newprot)
{
	pmdval_t val = pmd_val(pmd), oldval = val;
	pmd_t pmd_result;

	val &= (_HPAGE_CHG_MASK & ~_PAGE_DIRTY);
	val |= check_pgprot(newprot) & ~_HPAGE_CHG_MASK;
	val = flip_protnone_guard(oldval, val, PHYSICAL_PMD_PAGE_MASK);

	pmd_result = __pmd(val);

	/*
	 * Avoid creating shadow stack PMD by accident.  See comment in
	 * pte_modify().
	 */
	if (oldval & _PAGE_RW)
		pmd_result = pmd_mksaveddirty(pmd_result);
	else
		pmd_result = pmd_clear_saveddirty(pmd_result);

	return pmd_result;
}
```

[`pmd_mkinvalid()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L765) strips both PRESENT and PROTNONE (rebuilding the value through [`pfn_pmd()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L749), which re-inverts the PFN) to produce the frozen state the THP invalidate protocol stores while it edits a huge mapping.

```c
/* arch/x86/include/asm/pgtable.h:765 */
static inline pmd_t pmd_mkinvalid(pmd_t pmd)
{
	return pfn_pmd(pmd_pfn(pmd),
		      __pgprot(pmd_flags(pmd) & ~(_PAGE_PRESENT|_PAGE_PROTNONE)));
}
```

The pgprot-level analog of [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) is [`pgprot_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L863), the x86 override of the generic helper, which mprotect uses so a fresh [`vm_get_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L35) result does not wipe the PAT and encryption bits a driver put into `vma->vm_page_prot`.

```c
/* arch/x86/include/asm/pgtable.h:858 */
/*
 * mprotect needs to preserve PAT and encryption bits when updating
 * vm_page_prot
 */
#define pgprot_modify pgprot_modify
static inline pgprot_t pgprot_modify(pgprot_t oldprot, pgprot_t newprot)
{
	pgprotval_t preservebits = pgprot_val(oldprot) & _PAGE_CHG_MASK;
	pgprotval_t addbits = pgprot_val(newprot) & ~_PAGE_CHG_MASK;
	return __pgprot(preservebits | addbits);
}
```

### vm_get_page_prot() maps four VM_ flags through a 16-entry table

The pgprots an entry is built from start as combinations of eight single-letter aliases defined in [`arch/x86/include/asm/pgtable_types.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L188). [`PAGE_NONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L205) is accessed plus global with no present bit, and because bit 8 on a non-present entry is [`_PAGE_PROTNONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L141), a PROT_NONE mapping is born PROTNONE. [`PAGE_COPY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L210) (the private-writable case) is identical to [`PAGE_READONLY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L211), so a private writable mapping starts read-only and gains its write bit only from a fault or from mprotect's immediate-upgrade path, the mechanism copy-on-write is built on.

```c
/* arch/x86/include/asm/pgtable_types.h:188 */
#define __PP _PAGE_PRESENT
#define __RW _PAGE_RW
#define _USR _PAGE_USER
#define ___A _PAGE_ACCESSED
#define ___D _PAGE_DIRTY
#define ___G _PAGE_GLOBAL
#define __NX _PAGE_NX

#define _ENC _PAGE_ENC
#define __WP _PAGE_CACHE_WP
#define __NC _PAGE_NOCACHE
#define _PSE _PAGE_PSE

#define pgprot_val(x)		((x).pgprot)
#define __pgprot(x)		((pgprot_t) { (x) } )
#define __pg(x)			__pgprot(x)

#define PAGE_NONE	     __pg(   0|   0|   0|___A|   0|   0|   0|___G)
#define PAGE_SHARED	     __pg(__PP|__RW|_USR|___A|__NX|   0|   0|   0)
#define PAGE_SHARED_EXEC     __pg(__PP|__RW|_USR|___A|   0|   0|   0|   0)
#define PAGE_COPY_NOEXEC     __pg(__PP|   0|_USR|___A|__NX|   0|   0|   0)
#define PAGE_COPY_EXEC	     __pg(__PP|   0|_USR|___A|   0|   0|   0|   0)
#define PAGE_COPY	     __pg(__PP|   0|_USR|___A|__NX|   0|   0|   0)
#define PAGE_READONLY	     __pg(__PP|   0|_USR|___A|__NX|   0|   0|   0)
#define PAGE_READONLY_EXEC   __pg(__PP|   0|_USR|___A|   0|   0|   0|   0)
```

Kernel-space pgprots go through [`__pgprot_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L245), which filters with [`__default_kernel_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L109) so, for example, [`PAGE_KERNEL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L247) loses [`_PAGE_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L59) on PTI systems.

```c
/* arch/x86/include/asm/pgtable_types.h:245 */
#define __pgprot_mask(x)	__pgprot((x) & __default_kernel_pte_mask)

#define PAGE_KERNEL		__pgprot_mask(__PAGE_KERNEL            | _ENC)
```

[`protection_map`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L8) in [`arch/x86/mm/pgprot.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L8) indexes those pgprots by the low four VM_ flags (16 combinations). Private write maps to [`PAGE_COPY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L210), shared write to [`PAGE_SHARED`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L206), and both no-access rows to [`PAGE_NONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L205).

```c
/* arch/x86/mm/pgprot.c:8 */
static pgprot_t protection_map[16] __ro_after_init = {
	[VM_NONE]					= PAGE_NONE,
	[VM_READ]					= PAGE_READONLY,
	[VM_WRITE]					= PAGE_COPY,
	[VM_WRITE | VM_READ]				= PAGE_COPY,
	[VM_EXEC]					= PAGE_READONLY_EXEC,
	[VM_EXEC | VM_READ]				= PAGE_READONLY_EXEC,
	[VM_EXEC | VM_WRITE]				= PAGE_COPY_EXEC,
	[VM_EXEC | VM_WRITE | VM_READ]			= PAGE_COPY_EXEC,
	[VM_SHARED]					= PAGE_NONE,
	[VM_SHARED | VM_READ]				= PAGE_READONLY,
	[VM_SHARED | VM_WRITE]				= PAGE_SHARED,
	[VM_SHARED | VM_WRITE | VM_READ]		= PAGE_SHARED,
	[VM_SHARED | VM_EXEC]				= PAGE_READONLY_EXEC,
	[VM_SHARED | VM_EXEC | VM_READ]			= PAGE_READONLY_EXEC,
	[VM_SHARED | VM_EXEC | VM_WRITE]		= PAGE_SHARED_EXEC,
	[VM_SHARED | VM_EXEC | VM_WRITE | VM_READ]	= PAGE_SHARED_EXEC
};
```

[`vm_get_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L35) is the exported x86 override of the generic helper. It indexes the map, translates the four [`VM_PKEY_BIT0`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L452)..3 VMA flags into the four [`_PAGE_PKEY_BIT0`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L69)..3 entry bits, ORs in the SME C-bit with `__sme_set()`, and clamps present protections to [`__supported_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L107).

```c
/* arch/x86/mm/pgprot.c:35 */
pgprot_t vm_get_page_prot(vm_flags_t vm_flags)
{
	unsigned long val = pgprot_val(protection_map[vm_flags &
				      (VM_READ|VM_WRITE|VM_EXEC|VM_SHARED)]);

#ifdef CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS
	/*
	 * Take the 4 protection key bits out of the vma->vm_flags value and
	 * turn them in to the bits that we can put in to a pte.
	 *
	 * Only override these if Protection Keys are available (which is only
	 * on 64-bit).
	 */
	if (vm_flags & VM_PKEY_BIT0)
		val |= _PAGE_PKEY_BIT0;
	if (vm_flags & VM_PKEY_BIT1)
		val |= _PAGE_PKEY_BIT1;
	if (vm_flags & VM_PKEY_BIT2)
		val |= _PAGE_PKEY_BIT2;
	if (vm_flags & VM_PKEY_BIT3)
		val |= _PAGE_PKEY_BIT3;
#endif

	val = __sme_set(val);
	if (val & _PAGE_PRESENT)
		val &= __supported_pte_mask;
	return __pgprot(val);
}
EXPORT_SYMBOL(vm_get_page_prot);
```

[`add_encrypt_protection_map()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L27) rewrites all 16 rows once at boot when SME is active; [`sme_early_init()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/mem_encrypt_amd.c#L477) calls it right after widening [`__supported_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L107) by the C-bit.

```c
/* arch/x86/mm/pgprot.c:27 */
void add_encrypt_protection_map(void)
{
	unsigned int i;

	for (i = 0; i < ARRAY_SIZE(protection_map); i++)
		protection_map[i] = pgprot_encrypted(protection_map[i]);
}
```

```c
/* arch/x86/mm/mem_encrypt_amd.c:484 */
	__supported_pte_mask = __sme_set(__supported_pte_mask);

	/* Update the protection map with memory encryption mask */
	add_encrypt_protection_map();
```

[`__supported_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L107) itself starts as all ones in [`arch/x86/mm/init_64.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L106) and is trimmed at boot. [`x86_configure_nx()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/kernel/setup.c#L847) removes [`_PAGE_NX`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L122) on hardware without the feature (matching the "only valid after cpuid check" warning on [`_PAGE_BIT_NX`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L30)), and [`probe_page_size_mask()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init.c#L224) settles [`_PAGE_GLOBAL`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L59), keeping it out of [`__default_kernel_pte_mask`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/init_64.c#L109) on PTI systems so user-visible kernel mappings can be flushed per-process.

```c
/* arch/x86/mm/init_64.c:106 */
/* Bits supported by the hardware: */
pteval_t __supported_pte_mask __read_mostly = ~0;
/* Bits allowed in normal kernel mappings: */
pteval_t __default_kernel_pte_mask __read_mostly = ~0;
EXPORT_SYMBOL_GPL(__supported_pte_mask);
/* Used in PAGE_KERNEL_* macros which are reasonably used out-of-tree: */
EXPORT_SYMBOL(__default_kernel_pte_mask);
```

```c
/* arch/x86/kernel/setup.c:847 */
void x86_configure_nx(void)
{
	if (boot_cpu_has(X86_FEATURE_NX))
		__supported_pte_mask |= _PAGE_NX;
	else
		__supported_pte_mask &= ~_PAGE_NX;
}
```

```c
/* arch/x86/kernel/setup.c:970 */
	/*
	 * x86_configure_nx() is called before parse_early_param() to detect
	 * whether hardware doesn't support NX (so that the early EHCI debug
	 * console setup can safely call set_fixmap()).
	 */
	x86_configure_nx();
```

```c
/* arch/x86/mm/init.c:240 */
	/* Enable PGE if available */
	__supported_pte_mask &= ~_PAGE_GLOBAL;
	if (boot_cpu_has(X86_FEATURE_PGE)) {
		cr4_set_bits_and_update_boot(X86_CR4_PGE);
		__supported_pte_mask |= _PAGE_GLOBAL;
	}

	/* By the default is everything supported: */
	__default_kernel_pte_mask = __supported_pte_mask;
	/* Except when with PTI where the kernel is mostly non-Global: */
	if (cpu_feature_enabled(X86_FEATURE_PTI))
		__default_kernel_pte_mask &= ~_PAGE_GLOBAL;
```

```c
/* arch/x86/mm/init.c:763 */
	probe_page_size_mask();
```

The VMA caches the result in `vma->vm_page_prot`. [`vma_set_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mmap.c#L81) recomputes it through [`vm_pgprot_modify()`](https://elixir.bootlin.com/linux/v7.0/source/mm/vma.h#L483) (which is [`pgprot_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L863) over a fresh [`vm_get_page_prot()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgprot.c#L35)), downgrading to the non-shared row when the file needs write notification; [`mprotect_fixup()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L695) invokes it after changing `vma->vm_flags`.

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

```c
/* mm/vma.h:483 */
static inline pgprot_t vm_pgprot_modify(pgprot_t oldprot, vm_flags_t vm_flags)
{
	return pgprot_modify(oldprot, vm_get_page_prot(vm_flags));
}
```

```c
/* mm/mprotect.c:768 */
	vma_start_write(vma);
	vm_flags_reset_once(vma, newflags);
	if (vma_wants_manual_pte_write_upgrade(vma))
		mm_cp_flags |= MM_CP_TRY_CHANGE_WRITABLE;
	vma_set_page_prot(vma);
```

### Shadow stack claims Write=0,Dirty=1, and SavedDirty keeps read-only entries out of it

With CET shadow stacks (CONFIG_X86_USER_SHADOW_STACK, hardware [`X86_FEATURE_SHSTK`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/cpufeatures.h#L396)), the CPU defines a shadow-stack page as one whose leaf entry has Write=0 and Dirty=1. Ordinary kernel operations create exactly that combination on ordinary pages, because fork, mprotect, uffd-wp, and soft-dirty all clear RW on entries whose hardware dirty bit is set. The resolution at v7.0 is the [`_PAGE_SAVED_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L137) bit (bit 58). Whenever a transform would leave Dirty=1 on a Write=0 entry, the dirty bit moves to SavedDirty; whenever RW returns, SavedDirty moves back. Both dirty bits mean "dirty" to [`pte_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L156), so the accounting survives the round trip.

```
    Write/Dirty/SavedDirty states of a present leaf entry
    ──────────────────────────────────────────────────────────────────
    (X86_FEATURE_SHSTK hardware; SavedDirty is bit 58. Each node is the
     RW/D/SD triple the entry carries; only the labelled edges are
     drawn, and the two clean states have no transition of their own.)

       ┌────────────────────────┐        ┌────────────────────────┐
       │ writable, clean        │        │ read-only, clean       │
       │  RW 1   D 0   SD 0     │        │  RW 0   D 0   SD 0     │
       └────────────────────────┘        └────────────────────────┘

       ┌────────────────────────┐
    ┌─▶│ writable, dirty        │
    │  │  RW 1   D 1   SD 0     │
    │  └───────────┬────────────┘
    │              │ pte_wrprotect()
    │              │ RW 1 to 0, and D parks in SD
    │              ▼
    │  ┌────────────────────────┐
    │  │ read-only, dirty       │
    │  │  RW 0   D 0   SD 1     │
    │  └───────────┬────────────┘
    └──────────────┘ pte_mkwrite(vma)
                     RW 0 to 1, and SD returns to D

       ┌────────────────────────┐   reached only by pte_mkwrite_shstk,
       │ shadow stack           │   which drives RW to 0 and D to 1,
       │  RW 0   D 1   SD 0     │   and only on a VM_SHADOW_STACK vma
       └────────────────────────┘

    pte_dirty() reads Dirty and SavedDirty as one mask, so the
    read-only-dirty node and the writable-dirty node both report dirty
```

The shifting core is branchless. [`mksaveddirty_shift()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L373) computes a condition bit from inverted RW, copies Dirty into SavedDirty under that condition, and clears Dirty; [`clear_saveddirty_shift()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L383) is the mirror image keyed on RW being set. According to the comment above them, the shifting is done only when needed, Dirty-to-SavedDirty when the entry is Write=0 and SavedDirty-to-Dirty when it is Write=1.

```c
/* arch/x86/include/asm/pgtable.h:362 */
/*
 * Write protection operations can result in Dirty=1,Write=0 PTEs. But in the
 * case of X86_FEATURE_USER_SHSTK, these PTEs denote shadow stack memory. So
 * when creating dirty, write-protected memory, a software bit is used:
 * _PAGE_BIT_SAVED_DIRTY. The following functions take a PTE and transition the
 * Dirty bit to SavedDirty, and vice-vesra.
 *
 * This shifting is only done if needed. In the case of shifting
 * Dirty->SavedDirty, the condition is if the PTE is Write=0. In the case of
 * shifting SavedDirty->Dirty, the condition is Write=1.
 */
static inline pgprotval_t mksaveddirty_shift(pgprotval_t v)
{
	pgprotval_t cond = (~v >> _PAGE_BIT_RW) & 1;

	v |= ((v >> _PAGE_BIT_DIRTY) & cond) << _PAGE_BIT_SAVED_DIRTY;
	v &= ~(cond << _PAGE_BIT_DIRTY);

	return v;
}

static inline pgprotval_t clear_saveddirty_shift(pgprotval_t v)
{
	pgprotval_t cond = (v >> _PAGE_BIT_RW) & 1;

	v |= ((v >> _PAGE_BIT_SAVED_DIRTY) & cond) << _PAGE_BIT_DIRTY;
	v &= ~(cond << _PAGE_BIT_SAVED_DIRTY);

	return v;
}

static inline pte_t pte_mksaveddirty(pte_t pte)
{
	pteval_t v = native_pte_val(pte);

	v = mksaveddirty_shift(v);
	return native_make_pte(v);
}

static inline pte_t pte_clear_saveddirty(pte_t pte)
{
	pteval_t v = native_pte_val(pte);

	v = clear_saveddirty_shift(v);
	return native_make_pte(v);
}
```

[`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409) is therefore two steps, clear RW and then park any dirty bit; [`pmd_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L524) and [`pud_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L623) repeat it per level.

```c
/* arch/x86/include/asm/pgtable.h:409 */
static inline pte_t pte_wrprotect(pte_t pte)
{
	pte = pte_clear_flags(pte, _PAGE_RW);

	/*
	 * Blindly clearing _PAGE_RW might accidentally create
	 * a shadow stack PTE (Write=0,Dirty=1). Move the hardware
	 * dirty value to the software bit, if present.
	 */
	return pte_mksaveddirty(pte);
}
```

```c
/* arch/x86/include/asm/pgtable.h:524 */
static inline pmd_t pmd_wrprotect(pmd_t pmd)
{
	pmd = pmd_clear_flags(pmd, _PAGE_RW);

	/*
	 * Blindly clearing _PAGE_RW might accidentally create
	 * a shadow stack PMD (RW=0, Dirty=1). Move the hardware
	 * dirty value to the software bit.
	 */
	return pmd_mksaveddirty(pmd);
}
```

The writable transition is VMA-aware because a shadow-stack VMA must come out of it as Write=0,Dirty=1 rather than RW=1. [`pte_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802) is an out-of-line function in [`arch/x86/mm/pgtable.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802) that dispatches on `VM_SHADOW_STACK`, sending shadow-stack VMAs to [`pte_mkwrite_shstk()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L460) and everything else to [`pte_mkwrite_novma()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L472) followed by the SavedDirty-to-Dirty restore.

```c
/* arch/x86/mm/pgtable.c:802 */
pte_t pte_mkwrite(pte_t pte, struct vm_area_struct *vma)
{
	if (vma->vm_flags & VM_SHADOW_STACK)
		return pte_mkwrite_shstk(pte);

	pte = pte_mkwrite_novma(pte);

	return pte_clear_saveddirty(pte);
}

pmd_t pmd_mkwrite(pmd_t pmd, struct vm_area_struct *vma)
{
	if (vma->vm_flags & VM_SHADOW_STACK)
		return pmd_mkwrite_shstk(pmd);

	pmd = pmd_mkwrite_novma(pmd);

	return pmd_clear_saveddirty(pmd);
}
```

```c
/* arch/x86/include/asm/pgtable.h:460 */
static inline pte_t pte_mkwrite_shstk(pte_t pte)
{
	pte = pte_clear_flags(pte, _PAGE_RW);

	return pte_set_flags(pte, _PAGE_DIRTY);
}
```

[`maybe_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1690) in [`include/linux/mm.h`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1690) is the guard most fault paths use, applying [`pte_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802) only when the VMA has VM_WRITE.

```c
/* include/linux/mm.h:1690 */
static inline pte_t maybe_mkwrite(pte_t pte, struct vm_area_struct *vma)
{
	if (likely(vma->vm_flags & VM_WRITE))
		pte = pte_mkwrite(pte, vma);
	return pte;
}
```

Value transforms are not enough for entries already installed in the page tables, because the CPU can set Dirty=1 in the same instant the kernel clears RW, recreating the shadow-stack encoding despite the SavedDirty dance. [`ptep_set_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1279) therefore loops [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409) inside a `try_cmpxchg()` so the transform always operates on the value the hardware last wrote; [`pmdp_set_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1339) does the same for huge PMDs. The lore thread "x86/mm: Update ptep/pmdp_set_wrprotect() for _PAGE_SAVED_DIRTY" (OTHER SOURCES) introduced exactly this pair.

```c
/* arch/x86/include/asm/pgtable.h:1278 */
#define __HAVE_ARCH_PTEP_SET_WRPROTECT
static inline void ptep_set_wrprotect(struct mm_struct *mm,
				      unsigned long addr, pte_t *ptep)
{
	/*
	 * Avoid accidentally creating shadow stack PTEs
	 * (Write=0,Dirty=1).  Use cmpxchg() to prevent races with
	 * the hardware setting Dirty=1.
	 */
	pte_t old_pte, new_pte;

	old_pte = READ_ONCE(*ptep);
	do {
		new_pte = pte_wrprotect(old_pte);
	} while (!try_cmpxchg((long *)&ptep->pte, (long *)&old_pte, *(long *)&new_pte));
}
```

```c
/* arch/x86/include/asm/pgtable.h:1338 */
#define __HAVE_ARCH_PMDP_SET_WRPROTECT
static inline void pmdp_set_wrprotect(struct mm_struct *mm,
				      unsigned long addr, pmd_t *pmdp)
{
	/*
	 * Avoid accidentally creating shadow stack PTEs
	 * (Write=0,Dirty=1).  Use cmpxchg() to prevent races with
	 * the hardware setting Dirty=1.
	 */
	pmd_t old_pmd, new_pmd;

	old_pmd = READ_ONCE(*pmdp);
	do {
		new_pmd = pmd_wrprotect(old_pmd);
	} while (!try_cmpxchg((long *)pmdp, (long *)&old_pmd, *(long *)&new_pmd));
}
```

fork runs that path over every present entry of every COW mapping. [`wrprotect_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L1058), the generic batch helper, loops [`ptep_set_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1279) over a folio's worth of entries, and [`__copy_present_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1095) applies it to the parent side of every COW mapping while building the child's entry from the same value with [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409), then [`pte_mkclean()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L438) for shared mappings and [`pte_mkold()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L443) unconditionally, so the child starts not-young and re-faults for its accessed bit. [`copy_present_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1126) invokes it at its `copy_pte` tail.

```c
/* include/linux/pgtable.h:1058 */
static inline void wrprotect_ptes(struct mm_struct *mm, unsigned long addr,
		pte_t *ptep, unsigned int nr)
{
	for (;;) {
		ptep_set_wrprotect(mm, addr, ptep);
		if (--nr == 0)
			break;
		ptep++;
		addr += PAGE_SIZE;
	}
}
```

```c
/* mm/memory.c:1095 */
static __always_inline void __copy_present_ptes(struct vm_area_struct *dst_vma,
		struct vm_area_struct *src_vma, pte_t *dst_pte, pte_t *src_pte,
		pte_t pte, unsigned long addr, int nr)
{
	struct mm_struct *src_mm = src_vma->vm_mm;

	/* If it's a COW mapping, write protect it both processes. */
	if (is_cow_mapping(src_vma->vm_flags) && pte_write(pte)) {
		wrprotect_ptes(src_mm, addr, src_pte, nr);
		pte = pte_wrprotect(pte);
	}

	/* If it's a shared mapping, mark it clean in the child. */
	if (src_vma->vm_flags & VM_SHARED)
		pte = pte_mkclean(pte);
	pte = pte_mkold(pte);

	if (!userfaultfd_wp(dst_vma))
		pte = pte_clear_uffd_wp(pte);

	set_ptes(dst_vma->vm_mm, addr, dst_pte, pte, nr);
}
```

```c
/* mm/memory.c:1193 */
copy_pte:
	__copy_present_ptes(dst_vma, src_vma, dst_pte, src_pte, pte, addr, 1);
	return 1;
}
```

[`copy_huge_pmd()`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L1849) (called from [`copy_pmd_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1376) when [`pmd_is_huge()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/huge_mm.h#L436) matches) is the THP equivalent, running [`pmdp_set_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1339) on the parent and [`pmd_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L524) plus [`pmd_mkold()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L553) on the value it stores in the child.

```c
/* mm/huge_memory.c:1936 */
out_zero_page:
	mm_inc_nr_ptes(dst_mm);
	pgtable_trans_huge_deposit(dst_mm, dst_pmd, pgtable);
	pmdp_set_wrprotect(src_mm, addr, src_pmd);
	if (!userfaultfd_wp(dst_vma))
		pmd = pmd_clear_uffd_wp(pmd);
	pmd = pmd_wrprotect(pmd);
set_pmd:
	pmd = pmd_mkold(pmd);
	set_pmd_at(dst_mm, addr, dst_pmd, pmd);
```

```c
/* mm/memory.c:1391 */
		if (pmd_is_huge(*src_pmd)) {
			int err;

			VM_BUG_ON_VMA(next-addr != HPAGE_PMD_SIZE, src_vma);
			err = copy_huge_pmd(dst_mm, src_mm, dst_pmd, src_pmd,
					    addr, dst_vma, src_vma);
```

The unmap path polices the invariant. [`arch_check_zapped_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L822) warns (under `CONFIG_DEBUG_VM`) when a zap pulls a shadow-stack-encoded entry out of a VMA without `VM_SHADOW_STACK`, and its comment records why the check is keyed on [`pte_shstk()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L161), which is false on pre-shadow-stack hardware where stray Write=0,Dirty=1 entries were legal. [`zap_present_folio_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1633) runs it once per batch, right where it also harvests [`pte_young()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L167) into folio state; [`zap_present_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L1684) is its caller.

```c
/* arch/x86/mm/pgtable.c:822 */
void arch_check_zapped_pte(struct vm_area_struct *vma, pte_t pte)
{
	/*
	 * Hardware before shadow stack can (rarely) set Dirty=1
	 * on a Write=0 PTE. So the below condition
	 * only indicates a software bug when shadow stack is
	 * supported by the HW. This checking is covered in
	 * pte_shstk().
	 */
	VM_WARN_ON_ONCE(!(vma->vm_flags & VM_SHADOW_STACK) &&
			pte_shstk(pte));
}
```

```c
/* mm/memory.c:1651 */
		if (pte_young(ptent) && likely(vma_has_recency(vma)))
			folio_mark_accessed(folio);
		rss[mm_counter(folio)] -= nr;
	} else {
		/* We don't need up-to-date accessed/dirty bits. */
		clear_full_ptes(mm, addr, pte, nr, tlb->fullmm);
		rss[MM_ANONPAGES] -= nr;
	}
	/* Checking a single PTE in a batch is sufficient. */
	arch_check_zapped_pte(vma, ptent);
```

```c
/* mm/memory.c:1718 */
	if (unlikely(folio_test_large(folio) && max_nr != 1)) {
		nr = folio_pte_batch(folio, pte, ptent, max_nr);
		zap_present_folio_ptes(tlb, vma, folio, page, pte, ptent, nr,
				       addr, details, rss, force_flush,
				       force_break, any_skipped);
```

### Hardware raises Accessed and Dirty, and the kernel writes them back through race-safe helpers

The CPU sets [`_PAGE_ACCESSED`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L56) on the first translation through an entry and [`_PAGE_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L57) on the first write, both as locked memory transactions performed by the page walker. The kernel's job is the reverse direction, pre-setting the bits when it constructs entries (every base pgprot above carries `___A`, and [`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453) runs before installing a written-to page) so the hardware never needs its slow assist, and clearing them for reclaim and dirty tracking.

[`ptep_set_access_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L391) is the x86 implementation of the generic "make the entry more permissive after a fault" hook. According to the comment above it, x86 tracks accessed and dirty in hardware, so the function only writes when the caller both changed the entry and asked for a dirty upgrade; a young-only refresh of an unchanged entry is a no-op that returns 0. The store is a plain [`set_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L68) with no TLB flush, because the only stale TLB entry possible here is less permissive, and the comments in the PMD/PUD variants record that a #PF is architecturally guaranteed to resolve that (the same Optional Invalidation rule [`spurious_kernel_fault()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/fault.c#L980) relies on).

```c
/* arch/x86/mm/pgtable.c:384 */
/*
 * Used to set accessed or dirty bits in the page table entries
 * on other architectures. On x86, the accessed and dirty bits
 * are tracked by hardware. However, do_wp_page calls this function
 * to also make the pte writeable at the same time the dirty bit is
 * set. In that case we do actually need to write the PTE.
 */
int ptep_set_access_flags(struct vm_area_struct *vma,
			  unsigned long address, pte_t *ptep,
			  pte_t entry, int dirty)
{
	int changed = !pte_same(*ptep, entry);

	if (changed && dirty)
		set_pte(ptep, entry);

	return changed;
}
```

```c
/* arch/x86/mm/pgtable.c:404 */
int pmdp_set_access_flags(struct vm_area_struct *vma,
			  unsigned long address, pmd_t *pmdp,
			  pmd_t entry, int dirty)
{
	int changed = !pmd_same(*pmdp, entry);

	VM_BUG_ON(address & ~HPAGE_PMD_MASK);

	if (changed && dirty) {
		set_pmd(pmdp, entry);
		/*
		 * We had a write-protection fault here and changed the pmd
		 * to to more permissive. No need to flush the TLB for that,
		 * #PF is architecturally guaranteed to do that and in the
		 * worst-case we'll generate a spurious fault.
		 */
	}

	return changed;
}
```

The consumer that motivates the comment is the tail of [`handle_pte_fault()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6273). After the dispatch (missing entry to [`do_pte_missing()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4472), non-present to [`do_swap_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4706), PROTNONE to [`do_numa_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6048), write fault on a read-only entry to [`do_wp_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4149)), what remains is a fault on an entry that is present and adequate, meaning the TLB was stale or the hardware wanted A/D assistance. The tail rebuilds the entry with [`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453) (write faults) and [`pte_mkyoung()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L467), then hands it to [`ptep_set_access_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L391) with `dirty` set only for write faults.

```c
/* mm/memory.c:6316 */
	if (!vmf->pte)
		return do_pte_missing(vmf);

	if (!pte_present(vmf->orig_pte))
		return do_swap_page(vmf);

	if (pte_protnone(vmf->orig_pte) && vma_is_accessible(vmf->vma))
		return do_numa_page(vmf);

	spin_lock(vmf->ptl);
	entry = vmf->orig_pte;
	if (unlikely(!pte_same(ptep_get(vmf->pte), entry))) {
		update_mmu_tlb(vmf->vma, vmf->address, vmf->pte);
		goto unlock;
	}
	if (vmf->flags & (FAULT_FLAG_WRITE|FAULT_FLAG_UNSHARE)) {
		if (!pte_write(entry))
			return do_wp_page(vmf);
		else if (likely(vmf->flags & FAULT_FLAG_WRITE))
			entry = pte_mkdirty(entry);
	}
	entry = pte_mkyoung(entry);
	if (ptep_set_access_flags(vmf->vma, vmf->address, vmf->pte, entry,
				vmf->flags & FAULT_FLAG_WRITE))
		update_mmu_cache_range(vmf, vmf->vma, vmf->address,
				vmf->pte, 1);
	else
		fix_spurious_fault(vmf, PGTABLE_LEVEL_PTE);
unlock:
	pte_unmap_unlock(vmf->pte, vmf->ptl);
	return 0;
}
```

[`__handle_mm_fault()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6355) is the caller; its PMD stage shows the same predicates one level up, dispatching huge entries by [`pmd_present()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L985), [`pmd_trans_huge()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L305), [`pmd_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1007), and [`pmd_write()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L223), and falling through to [`handle_pte_fault()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6273) otherwise. The PUD stage above it runs the analogous [`pud_trans_huge()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L311)/[`pud_write()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L233) checks.

```c
/* mm/memory.c:6390 */
		if (pud_trans_huge(orig_pud)) {

			/*
			 * TODO once we support anonymous PUDs: NUMA case and
			 * FAULT_FLAG_UNSHARE handling.
			 */
			if ((flags & FAULT_FLAG_WRITE) && !pud_write(orig_pud)) {
				ret = wp_huge_pud(&vmf, orig_pud);
				if (!(ret & VM_FAULT_FALLBACK))
					return ret;
			} else {
				huge_pud_set_accessed(&vmf, orig_pud);
				return 0;
			}
		}
```

```c
/* mm/memory.c:6424 */
	vmf.orig_pmd = pmdp_get_lockless(vmf.pmd);
	if (pmd_none(vmf.orig_pmd))
		goto fallback;
...
	if (pmd_trans_huge(vmf.orig_pmd)) {
		if (pmd_protnone(vmf.orig_pmd) && vma_is_accessible(vma))
			return do_huge_pmd_numa_page(&vmf);

		if ((flags & (FAULT_FLAG_WRITE|FAULT_FLAG_UNSHARE)) &&
		    !pmd_write(vmf.orig_pmd)) {
			ret = wp_huge_pmd(&vmf);
			if (!(ret & VM_FAULT_FALLBACK))
				return ret;
		} else {
			vmf.ptl = pmd_lock(mm, vmf.pmd);
			if (!huge_pmd_set_accessed(&vmf))
				fix_spurious_fault(&vmf, PGTABLE_LEVEL_PMD);
			spin_unlock(vmf.ptl);
			return 0;
		}
	}
...
fallback:
	return handle_pte_fault(&vmf);
}
```

```c
/* mm/memory.c:4472 */
static vm_fault_t do_pte_missing(struct vm_fault *vmf)
{
	if (vma_is_anonymous(vmf->vma))
		return do_anonymous_page(vmf);
	else
		return do_fault(vmf);
}
```

[`wp_page_reuse()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L3664) resolves a COW fault on a page the faulting process may keep (an exclusive anonymous page). It reconstructs the entry from `vmf->orig_pte` with [`pte_mkyoung()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L467), [`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453), and [`maybe_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L1690), and commits with `dirty=1`, which is the exact case [`ptep_set_access_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L391) actually writes. [`do_wp_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L4149) calls it on the anonymous-reuse branch.

```c
/* mm/memory.c:3684 */
	flush_cache_page(vma, vmf->address, pte_pfn(vmf->orig_pte));
	entry = pte_mkyoung(vmf->orig_pte);
	entry = maybe_mkwrite(pte_mkdirty(entry), vma);
	if (ptep_set_access_flags(vma, vmf->address, vmf->pte, entry, 1))
		update_mmu_cache_range(vmf, vma, vmf->address, vmf->pte, 1);
	pte_unmap_unlock(vmf->pte, vmf->ptl);
	count_vm_event(PGREUSE);
}
```

```c
/* mm/memory.c:4223 */
		if (unlikely(unshare)) {
			pte_unmap_unlock(vmf->pte, vmf->ptl);
			return 0;
		}
		wp_page_reuse(vmf, folio);
		return 0;
	}
```

The write branch of [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217) shows the same three constructors at first touch, on an entry built by [`folio_mk_pte()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L2283) from the VMA's cached pgprot.

```c
/* mm/memory.c:5282 */
	entry = folio_mk_pte(folio, vma->vm_page_prot);
	entry = pte_sw_mkyoung(entry);
	if (vma->vm_flags & VM_WRITE)
		entry = pte_mkwrite(pte_mkdirty(entry), vma);
```

[`touch_pmd()`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L1776) is the THP copy of the tail, invoked by [`huge_pmd_set_accessed()`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L2018) from the [`__handle_mm_fault()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6355) dispatch, pairing [`pmd_mkyoung()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L582)/[`pmd_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L563) with [`pmdp_set_access_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L404).

```c
/* mm/huge_memory.c:1776 */
bool touch_pmd(struct vm_area_struct *vma, unsigned long addr,
	       pmd_t *pmd, bool write)
{
	pmd_t entry;

	entry = pmd_mkyoung(*pmd);
	if (write)
		entry = pmd_mkdirty(entry);
	if (pmdp_set_access_flags(vma, addr & HPAGE_PMD_MASK,
				  pmd, entry, write)) {
		update_mmu_cache_pmd(vma, addr, pmd);
		return true;
	}

	return false;
}
```

```c
/* mm/huge_memory.c:2018 */
bool huge_pmd_set_accessed(struct vm_fault *vmf)
{
	bool write = vmf->flags & FAULT_FLAG_WRITE;

	if (unlikely(!pmd_same(*vmf->pmd, vmf->orig_pmd)))
		return false;

	return touch_pmd(vmf->vma, vmf->address, vmf->pmd, write);
}
```

Clearing the accessed bit runs in the opposite direction, from reclaim toward the hardware. [`ptep_test_and_clear_young()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L446) uses an atomic `test_and_clear_bit()` on [`_PAGE_BIT_ACCESSED`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L15) directly on the installed entry, and [`ptep_clear_flush_young()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L486) deliberately skips the TLB flush the generic version would do; according to its comment, a stale accessed bit costs at most a mistaken page-age decision, and the flush would cost an IPI storm on every reclaim scan.

```c
/* arch/x86/mm/pgtable.c:446 */
int ptep_test_and_clear_young(struct vm_area_struct *vma,
			      unsigned long addr, pte_t *ptep)
{
	int ret = 0;

	if (pte_young(*ptep))
		ret = test_and_clear_bit(_PAGE_BIT_ACCESSED,
					 (unsigned long *) &ptep->pte);

	return ret;
}
```

```c
/* arch/x86/mm/pgtable.c:486 */
int ptep_clear_flush_young(struct vm_area_struct *vma,
			   unsigned long address, pte_t *ptep)
{
	/*
	 * On x86 CPUs, clearing the accessed bit without a TLB flush
	 * doesn't cause data corruption. [ It could cause incorrect
	 * page aging and the (mistaken) reclaim of hot pages, but the
	 * chance of that should be relatively low. ]
	 *
	 * So as a performance optimization don't flush the TLB when
	 * clearing the accessed bit, it will eventually be flushed by
	 * a context switch or a VM operation anyway. [ In the rare
	 * event of it not getting flushed for a long time the delay
	 * shouldn't really matter because there's no real memory
	 * pressure for swapout to react to. ]
	 */
	return ptep_test_and_clear_young(vma, address, ptep);
}
```

Whole-entry removal must also be atomic against the walker. [`ptep_get_and_clear()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1251) wraps [`native_ptep_get_and_clear()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L87), whose SMP flavor is an `xchg()` with zero, so a dirty bit the CPU sets concurrently lands in the returned value instead of being lost; the returned entry is what reclaim uses to decide whether the page needs writeback.

```c
/* arch/x86/include/asm/pgtable_64.h:87 */
static inline pte_t native_ptep_get_and_clear(pte_t *xp)
{
#ifdef CONFIG_SMP
	return native_make_pte(xchg(&xp->pte, 0));
#else
	/* native_local_ptep_get_and_clear,
	   but duplicated because of cyclic dependency */
	pte_t ret = *xp;
	native_pte_clear(NULL, 0, xp);
	return ret;
#endif
}
```

```c
/* arch/x86/include/asm/pgtable.h:1250 */
#define __HAVE_ARCH_PTEP_GET_AND_CLEAR
static inline pte_t ptep_get_and_clear(struct mm_struct *mm, unsigned long addr,
				       pte_t *ptep)
{
	pte_t pte = native_ptep_get_and_clear(ptep);
	page_table_check_pte_clear(mm, addr, pte);
	return pte;
}
```

At the PMD level the equivalent replacement primitive is [`pmdp_establish()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1357), an `xchg()` of the whole huge entry, and [`pmdp_invalidate_ad()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L520) uses it to swap in the [`pmd_mkinvalid()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L765) value. According to its comment, once the invalid entry is established the walker can no longer set A/D on it, so the returned old value holds the final truth; the THP protection changer depends on that below.

```c
/* arch/x86/include/asm/pgtable.h:1355 */
#ifndef pmdp_establish
#define pmdp_establish pmdp_establish
static inline pmd_t pmdp_establish(struct vm_area_struct *vma,
		unsigned long address, pmd_t *pmdp, pmd_t pmd)
{
	page_table_check_pmd_set(vma->vm_mm, address, pmdp, pmd);
	if (IS_ENABLED(CONFIG_SMP)) {
		return xchg(pmdp, pmd);
	} else {
		pmd_t old = *pmdp;
		WRITE_ONCE(*pmdp, pmd);
		return old;
	}
}
#endif
```

```c
/* arch/x86/mm/pgtable.c:520 */
pmd_t pmdp_invalidate_ad(struct vm_area_struct *vma, unsigned long address,
			 pmd_t *pmdp)
{
	VM_WARN_ON_ONCE(!pmd_present(*pmdp));

	/*
	 * No flush is necessary. Once an invalid PTE is established, the PTE's
	 * access and dirty bits cannot be updated.
	 */
	return pmdp_establish(vma, address, pmdp, pmd_mkinvalid(*pmdp));
}
```

### change_pte_range() writes PROTNONE entries and do_numa_page() takes them back

NUMA balancing turns present entries into PROTNONE hinting entries so the next touch faults and reveals which node is using the page. The writer is [`change_pte_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L214), called by [`change_pmd_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L451) for both mprotect and the `MM_CP_PROT_NUMA` scans; in the NUMA case `newprot` is [`PAGE_NONE`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L205), so [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) clears [`_PAGE_PRESENT`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L51) and sets bit 8, and [`flip_protnone_guard()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable-invert.h#L27) inverts the PFN on the way. Entries already PROTNONE are skipped by [`pte_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1001), the uffd-wp cases run [`pte_mkuffd_wp()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L427)/[`pte_clear_uffd_wp()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L432) on the modified value, and the `else if` leg over [`pte_none()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L948) entries installs uffd-wp markers only.

```c
/* mm/mprotect.c:237 */
	do {
		nr_ptes = 1;
		oldpte = ptep_get(pte);
		if (pte_present(oldpte)) {
			const fpb_t flags = FPB_RESPECT_SOFT_DIRTY | FPB_RESPECT_WRITE;
			int max_nr_ptes = (end - addr) >> PAGE_SHIFT;
			struct folio *folio = NULL;
			struct page *page;
			pte_t ptent;

			/* Already in the desired state. */
			if (prot_numa && pte_protnone(oldpte))
				continue;

			page = vm_normal_page(vma, addr, oldpte);
			if (page)
				folio = page_folio(page);
```

```c
/* mm/mprotect.c:269 */
			nr_ptes = mprotect_folio_pte_batch(folio, pte, oldpte, max_nr_ptes, flags);

			oldpte = modify_prot_start_ptes(vma, addr, pte, nr_ptes);
			ptent = pte_modify(oldpte, newprot);

			if (uffd_wp)
				ptent = pte_mkuffd_wp(ptent);
			else if (uffd_wp_resolve)
				ptent = pte_clear_uffd_wp(ptent);

			/*
			 * In some writable, shared mappings, we might want
			 * to catch actual write access -- see
			 * vma_wants_writenotify().
			 *
			 * In all writable, private mappings, we have to
			 * properly handle COW.
			 *
			 * In both cases, we can sometimes still change PTEs
			 * writable and avoid the write-fault handler, for
			 * example, if a PTE is already dirty and no other
			 * COW or special handling is required.
			 */
			if ((cp_flags & MM_CP_TRY_CHANGE_WRITABLE) &&
			     !pte_write(ptent))
				set_write_prot_commit_flush_ptes(vma, folio, page,
				addr, pte, oldpte, ptent, nr_ptes, tlb);
			else
				prot_commit_flush_ptes(vma, addr, pte, oldpte, ptent,
					nr_ptes, /* idx = */ 0, /* set_write = */ false, tlb);
			pages += nr_ptes;
		} else if (pte_none(oldpte)) {
```

```c
/* mm/mprotect.c:507 */
		ret = change_pte_range(tlb, vma, pmd, addr, next, newprot,
				       cp_flags);
```

The commit helper [`prot_commit_flush_ptes()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L120) advances through the batch with [`pte_advance_pfn()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L959) (which is why that helper is inversion-aware), applies [`pte_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802) when the caller decided the entries may become writable immediately, and consults [`pte_needs_flush()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/tlbflush.h#L416) (the [`pte_flags_need_flush()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/tlbflush.h#L360) wrapper) to batch TLB work.

```c
/* mm/mprotect.c:119 */
/* Set nr_ptes number of ptes, starting from idx */
static void prot_commit_flush_ptes(struct vm_area_struct *vma, unsigned long addr,
		pte_t *ptep, pte_t oldpte, pte_t ptent, int nr_ptes,
		int idx, bool set_write, struct mmu_gather *tlb)
{
	/*
	 * Advance the position in the batch by idx; note that if idx > 0,
	 * then the nr_ptes passed here is <= batch size - idx.
	 */
	addr += idx * PAGE_SIZE;
	ptep += idx;
	oldpte = pte_advance_pfn(oldpte, idx);
	ptent = pte_advance_pfn(ptent, idx);

	if (set_write)
		ptent = pte_mkwrite(ptent, vma);

	modify_prot_commit_ptes(vma, addr, ptep, oldpte, ptent, nr_ptes);
	if (pte_needs_flush(oldpte, ptent))
		tlb_flush_pte_range(tlb, addr, nr_ptes * PAGE_SIZE);
}
```

Whether mprotect may set RW at once (skipping a later COW or writenotify fault) is decided by the [`can_change_pte_writable()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L97) family. [`maybe_change_pte_writable()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L41) refuses PROTNONE entries outright (they are not even readable), then defers to soft-dirty and uffd-wp tracking; the shared-mapping case additionally requires [`pte_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L156), treating a dirty entry as proof that writenotify already fired. [`do_numa_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6048) calls the same predicate when rebuilding.

```c
/* mm/mprotect.c:41 */
static bool maybe_change_pte_writable(struct vm_area_struct *vma, pte_t pte)
{
	if (WARN_ON_ONCE(!(vma->vm_flags & VM_WRITE)))
		return false;

	/* Don't touch entries that are not even readable. */
	if (pte_protnone(pte))
		return false;

	/* Do we need write faults for softdirty tracking? */
	if (pte_needs_soft_dirty_wp(vma, pte))
		return false;

	/* Do we need write faults for uffd-wp tracking? */
	if (userfaultfd_pte_wp(vma, pte))
		return false;

	return true;
}
```

```c
/* mm/mprotect.c:79 */
static bool can_change_shared_pte_writable(struct vm_area_struct *vma,
					   pte_t pte)
{
	if (!maybe_change_pte_writable(vma, pte))
		return false;

	VM_WARN_ON_ONCE(is_zero_pfn(pte_pfn(pte)) && pte_dirty(pte));

	/*
	 * Writable MAP_SHARED mapping: "clean" might indicate that the FS still
	 * needs a real write-fault for writenotify
	 * (see vma_wants_writenotify()). If "dirty", the assumption is that the
	 * FS was already notified and we can simply mark the PTE writable
	 * just like the write-fault handler would do.
	 */
	return pte_dirty(pte);
}

bool can_change_pte_writable(struct vm_area_struct *vma, unsigned long addr,
			     pte_t pte)
{
	if (!(vma->vm_flags & VM_SHARED))
		return can_change_private_pte_writable(vma, addr, pte);

	return can_change_shared_pte_writable(vma, pte);
}
```

The reader side is [`do_numa_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6048), reached from the [`pte_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1001) dispatch in [`handle_pte_fault()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6273). Under the PTL it recomputes the present view of the entry with [`pte_modify(old_pte, vma->vm_page_prot)`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779), probes writability, and passes the PFN to [`vm_normal_folio()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L783) to find the folio for the migration decision.

```c
/* mm/memory.c:6064 */
	spin_lock(vmf->ptl);
	/* Read the live PTE from the page tables: */
	old_pte = ptep_get(vmf->pte);

	if (unlikely(!pte_same(old_pte, vmf->orig_pte))) {
		pte_unmap_unlock(vmf->pte, vmf->ptl);
		return 0;
	}

	pte = pte_modify(old_pte, vma->vm_page_prot);

	/*
	 * Detect now whether the PTE could be writable; this information
	 * is only valid while holding the PT lock.
	 */
	writable = pte_write(pte);
	if (!writable && pte_write_upgrade &&
	    can_change_pte_writable(vma, vmf->address, pte))
		writable = true;

	folio = vm_normal_folio(vma, vmf->address, pte);
	if (!folio || folio_is_zone_device(folio))
		goto out_map;
```

Whether the page migrates or not, the entry must become present again, which [`numa_rebuild_single_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5994) does through the [`ptep_modify_prot_start()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L1530)/[`ptep_modify_prot_commit()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/pgtable.h#L1543) transaction around [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779), [`pte_mkyoung()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L467), and an optional [`pte_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802). The `out_map` tail of [`do_numa_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6048) calls it for the single-page case and [`numa_rebuild_large_mapping()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L6009) for large folios.

```c
/* mm/memory.c:5994 */
static void numa_rebuild_single_mapping(struct vm_fault *vmf, struct vm_area_struct *vma,
					unsigned long fault_addr, pte_t *fault_pte,
					bool writable)
{
	pte_t pte, old_pte;

	old_pte = ptep_modify_prot_start(vma, fault_addr, fault_pte);
	pte = pte_modify(old_pte, vma->vm_page_prot);
	pte = pte_mkyoung(pte);
	if (writable)
		pte = pte_mkwrite(pte, vma);
	ptep_modify_prot_commit(vma, fault_addr, fault_pte, old_pte, pte);
	update_mmu_cache_range(vmf, vma, fault_addr, fault_pte, 1);
}
```

```c
/* mm/memory.c:6121 */
out_map:
	/*
	 * Make it present again, depending on how arch implements
	 * non-accessible ptes, some can allow access by kernel mode.
	 */
	if (folio && folio_test_large(folio))
		numa_rebuild_large_mapping(vmf, vma, folio, pte, ignore_writable,
					   pte_write_upgrade);
	else
		numa_rebuild_single_mapping(vmf, vma, vmf->address, vmf->pte,
					    writable);
	pte_unmap_unlock(vmf->pte, vmf->ptl);
```

The THP mirror is [`change_huge_pmd()`](https://elixir.bootlin.com/linux/v7.0/source/mm/huge_memory.c#L2558), which [`change_pmd_range()`](https://elixir.bootlin.com/linux/v7.0/source/mm/mprotect.c#L451) calls for huge entries. It skips already-PROTNONE entries with [`pmd_protnone()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1007), freezes the entry with [`pmdp_invalidate_ad()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L520) (the comment explains the MADV_DONTNEED race that forbids a transient clear), rewrites it with [`pmd_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L812), and applies the same uffd-wp and immediate-write logic as the PTE path, [`pmd_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L812) included.

```c
/* mm/huge_memory.c:2595 */
		if (pmd_protnone(*pmd))
			goto unlock;
...
	oldpmd = pmdp_invalidate_ad(vma, addr, pmd);

	entry = pmd_modify(oldpmd, newprot);
	if (uffd_wp)
		entry = pmd_mkuffd_wp(entry);
	else if (uffd_wp_resolve)
		/*
		 * Leave the write bit to be handled by PF interrupt
		 * handler, then things like COW could be properly
		 * handled.
		 */
		entry = pmd_clear_uffd_wp(entry);

	/* See change_pte_range(). */
	if ((cp_flags & MM_CP_TRY_CHANGE_WRITABLE) && !pmd_write(entry) &&
	    can_change_pmd_writable(vma, addr, entry))
		entry = pmd_mkwrite(entry, vma);
```

```c
/* mm/mprotect.c:491 */
			} else {
				ret = change_huge_pmd(tlb, vma, pmd,
						addr, newprot, cp_flags);
```

### clear_soft_dirty() write-protects the entry so the tracker sees the next write

Soft-dirty tracking (CONFIG_MEM_SOFT_DIRTY) is a full lifecycle over one software bit. [`pte_mkdirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L453) sets [`_PAGE_SOFT_DIRTY`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L92) alongside the hardware bit on every kernel-initiated dirtying, hardware writes reach it through the write fault that follows a clear, and the pagemap interface reports it to userspace. The reset step is [`clear_soft_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L1616), run by [`clear_refs_pte_range()`](https://elixir.bootlin.com/linux/v7.0/source/fs/proc/task_mmu.c#L1680) for every entry when `4` is written to `/proc/pid/clear_refs`. For a present entry it combines [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409) with [`pte_clear_soft_dirty()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L690) inside a modify_prot transaction, because clearing the bit without removing write permission would let the next write go unrecorded. This is one of the paths that manufactures read-only-but-dirty values, and the SavedDirty machinery above is what keeps those values from reading as shadow stack.

```c
/* fs/proc/task_mmu.c:1616 */
static inline void clear_soft_dirty(struct vm_area_struct *vma,
		unsigned long addr, pte_t *pte)
{
	if (!pgtable_supports_soft_dirty())
		return;
	/*
	 * The soft-dirty tracker uses #PF-s to catch writes
	 * to pages, so write-protect the pte as well. See the
	 * Documentation/admin-guide/mm/soft-dirty.rst for full description
	 * of how soft-dirty works.
	 */
	pte_t ptent = ptep_get(pte);

	if (pte_none(ptent))
		return;

	if (pte_present(ptent)) {
		pte_t old_pte;

		if (pte_is_pinned(vma, addr, ptent))
			return;
		old_pte = ptep_modify_prot_start(vma, addr, pte);
		ptent = pte_wrprotect(old_pte);
		ptent = pte_clear_soft_dirty(ptent);
		ptep_modify_prot_commit(vma, addr, pte, old_pte, ptent);
	} else {
		ptent = pte_swp_clear_soft_dirty(ptent);
		set_pte_at(vma->vm_mm, addr, pte, ptent);
	}
}
```

```c
/* fs/proc/task_mmu.c:1715 */
	for (; addr != end; pte++, addr += PAGE_SIZE) {
		ptent = ptep_get(pte);

		if (cp->type == CLEAR_REFS_SOFT_DIRTY) {
			clear_soft_dirty(vma, addr, pte);
			continue;
		}
```

### The native store layer writes whole entries with WRITE_ONCE, and the PGD level detours through PTI

Every in-place store bottoms out in [`arch/x86/include/asm/pgtable_64.h`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L61). A 64-bit entry is stored with one `WRITE_ONCE()`, which is atomic on x86-64, so a concurrently walking CPU sees either the old or the new value, never a torn word; clearing is storing zero.

```c
/* arch/x86/include/asm/pgtable_64.h:61 */
static inline void native_set_pte(pte_t *ptep, pte_t pte)
{
	WRITE_ONCE(*ptep, pte);
}

static inline void native_pte_clear(struct mm_struct *mm, unsigned long addr,
				    pte_t *ptep)
{
	native_set_pte(ptep, native_make_pte(0));
}

static inline void native_set_pte_atomic(pte_t *ptep, pte_t pte)
{
	native_set_pte(ptep, pte);
}

static inline void native_set_pmd(pmd_t *pmdp, pmd_t pmd)
{
	WRITE_ONCE(*pmdp, pmd);
}
```

```c
/* arch/x86/include/asm/pgtable_64.h:113 */
static inline void native_set_pud(pud_t *pudp, pud_t pud)
{
	WRITE_ONCE(*pudp, pud);
}
```

The two top levels add the PTI detour. Under CONFIG_MITIGATION_PAGE_TABLE_ISOLATION each process has a second, user-visible PGD page, and a store to a userspace slot of the kernel PGD must be mirrored there. [`native_set_pgd()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L158) routes every value through [`pti_set_user_pgtbl()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L920); [`native_set_p4d()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_64.h#L138) does the same when 4-level paging makes the P4D the real top level, converting through [`native_make_pgd()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L326)/[`native_pgd_val()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L331) because the folded levels share one storage slot.

```c
/* arch/x86/include/asm/pgtable_64.h:138 */
static inline void native_set_p4d(p4d_t *p4dp, p4d_t p4d)
{
	pgd_t pgd;

	if (pgtable_l5_enabled() ||
	    !IS_ENABLED(CONFIG_MITIGATION_PAGE_TABLE_ISOLATION)) {
		WRITE_ONCE(*p4dp, p4d);
		return;
	}

	pgd = native_make_pgd(native_p4d_val(p4d));
	pgd = pti_set_user_pgtbl((pgd_t *)p4dp, pgd);
	WRITE_ONCE(*p4dp, native_make_p4d(native_pgd_val(pgd)));
}

static inline void native_p4d_clear(p4d_t *p4d)
{
	native_set_p4d(p4d, native_make_p4d(0));
}

static inline void native_set_pgd(pgd_t *pgdp, pgd_t pgd)
{
	WRITE_ONCE(*pgdp, pti_set_user_pgtbl(pgdp, pgd));
}
```

[`pti_set_user_pgtbl()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L920) is a static-key no-op on non-PTI systems and otherwise calls into [`__pti_set_user_pgtbl()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pti.c#L131), which copies the value into the user PGD page unless the slot maps kernel space or the entry carries [`_PAGE_NOPTISHADOW`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable_types.h#L143), the bit the identity-mapping builders in [`arch/x86/mm/ident_map.c`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/ident_map.c#L172) set on entries that must never leak into the user half.

```c
/* arch/x86/include/asm/pgtable.h:912 */
#ifdef CONFIG_MITIGATION_PAGE_TABLE_ISOLATION
pgd_t __pti_set_user_pgtbl(pgd_t *pgdp, pgd_t pgd);

/*
 * Take a PGD location (pgdp) and a pgd value that needs to be set there.
 * Populates the user and returns the resulting PGD that must be set in
 * the kernel copy of the page tables.
 */
static inline pgd_t pti_set_user_pgtbl(pgd_t *pgdp, pgd_t pgd)
{
	if (!static_cpu_has(X86_FEATURE_PTI))
		return pgd;
	return __pti_set_user_pgtbl(pgdp, pgd);
}
```

```c
/* arch/x86/mm/pti.c:131 */
pgd_t __pti_set_user_pgtbl(pgd_t *pgdp, pgd_t pgd)
{
	/*
	 * Changes to the high (kernel) portion of the kernelmode page
	 * tables are not automatically propagated to the usermode tables.
	 *
	 * Users should keep in mind that, unlike the kernelmode tables,
	 * there is no vmalloc_fault equivalent for the usermode tables.
	 * Top-level entries added to init_mm's usermode pgd after boot
	 * will not be automatically propagated to other mms.
	 */
	if (!pgdp_maps_userspace(pgdp) || (pgd.pgd & _PAGE_NOPTISHADOW))
		return pgd;

	/*
	 * The user page tables get the full PGD, accessible from
	 * userspace:
	 */
	kernel_to_user_pgdp(pgdp)->pgd = pgd.pgd;
```

The state transitions this page has covered, gathered in one place. Construction produces a present entry from a PFN and a pgprot ([`pfn_pte()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L738) via [`folio_mk_pte()`](https://elixir.bootlin.com/linux/v7.0/source/include/linux/mm.h#L2283) in [`do_anonymous_page()`](https://elixir.bootlin.com/linux/v7.0/source/mm/memory.c#L5217)), young and, for writes, dirty and writable from birth. Hardware moves clean-to-dirty and old-to-young on its own; the kernel moves the other directions with [`pte_mkclean()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L438), [`pte_mkold()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L443), and [`ptep_test_and_clear_young()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L446), and re-drives the hardware directions after faults through [`ptep_set_access_flags()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L391). Writable-to-read-only is [`pte_wrprotect()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L409) under `try_cmpxchg()` (fork, soft-dirty reset, uffd-wp), the reverse is [`pte_mkwrite()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/mm/pgtable.c#L802) (write faults, mprotect immediate upgrade), and on shadow-stack hardware both directions carry the Dirty/SavedDirty exchange. Present-to-PROTNONE and back is the NUMA cycle through [`pte_modify()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L779) with the PFN inversion flipping at each crossing, and present-to-cleared is [`ptep_get_and_clear()`](https://elixir.bootlin.com/linux/v7.0/source/arch/x86/include/asm/pgtable.h#L1251) returning the final A/D truth to the unmapper. Everything past that cleared state, the swap, migration, and marker payloads a non-present slot may hold next, is outside this page.
