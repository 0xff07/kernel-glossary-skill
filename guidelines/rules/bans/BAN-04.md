# BAN-04: Hollow superlatives

> Was: 7d. Hollow superlatives

**Words to watch:** the most invasive, the most fragmenting, the most aggressive, the most consequential, the most preferred, the least preferred, the most expensive, the cheapest, the cheap path, the slow path, the fast path, the strongest guarantee, the weakest guarantee, the strongest anti-fragmentation guarantee, the worst outcome, the best outcome, the entire performance benefit, the entire correctness benefit, the key invariant, the key difference, the key innovation, the key role, the design assumption, the design intent, X matters, X matters because Y, X is what makes Y, what makes X work, the only mode that, elaborate, elegant, fundamental, cornerstone, linchpin, crucial, critical

**Problem:** Generated prose ranks a kernel construct ("the most invasive handler path", "the key difference") without naming the mechanic that would justify the ranking. Each kernel symbol, mode, or path is unique by definition, so the unexplained superlative adds zero information. "X matters" and "X is what makes Y" assert importance instead of stating the mechanic. "Fast path" and "slow path" are acceptable only where the kernel itself defines them (the fast path of a specific lock implementation). "The only mode that ..." fails when the same is trivially true of every other mode under some other framing.

The test for any adjective in body prose: would the sentence still convey the mechanic with the adjective deleted? If yes, delete it. If no, replace the adjective with the actual mechanic. A superlative that cannot be reduced to a concrete code-level fact does not appear at all.

**Before:**

```
acpi_ev_gpe_dispatch is the most invasive handler path.
```

**After:**

```
acpi_ev_gpe_dispatch disables the GPE with acpi_hw_low_set_gpe(), clears edge-triggered status with acpi_hw_clear_gpe(), then routes by dispatch type.
```

**Before:**

```
A raw handler is the cheap path through acpi_ev_detect_gpe().
```

**After:**

```
acpi_ev_detect_gpe() invokes the raw handler directly at interrupt level, skipping the disable/clear/re-enable protocol that acpi_ev_gpe_dispatch() runs.
```

**Before:**

```
This is the strongest guarantee against a lost edge.
```

**After:**

```
Clearing an edge-triggered GPE's status before queueing the method ensures an edge arriving during servicing re-latches instead of being lost.
```

**Before:**

```
the key difference from a method GPE
```

**After:**

```
a method GPE queues acpi_ev_asynch_execute_gpe_method() via acpi_os_execute(); a raw-handler GPE calls the handler synchronously at interrupt level.
```

Keep direct quotes from kernel source comments, commit messages, and LKML threads verbatim even when they contain superlatives this rule would otherwise forbid.
