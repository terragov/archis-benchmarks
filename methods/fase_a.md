# Fase A: ingestion gates

**Question.** Does indexing a real repository work, is it stable, and does an incremental
re-index end where a clean rebuild would?

**What runs, per repository**
1. Index the tree twice into separate stores and compare the **canonical graph hash**: a hash
   over symbol and relation names (not internal ids), so two indexes of the same tree must agree
   byte for byte. `hash_stable` is that comparison. The very first index is excluded because it
   writes the ignore file; its difference is recorded separately.
2. **Incremental equivalence**: on a copy of the tree, pick the largest source file between
   200 B and 40 KB; a no-op re-index must keep the hash; then append a function, rename, delete
   and recreate the file, re-indexing after each step, and compare the final hash with a clean
   rebuild in a separate store. `incremental_equiv` is that comparison.
3. **Reduction**: `chi measure` over the tree, `reduction = 1 − tokens(Archis representation) /
   tokens(source)`, tokenizer `o200k_base`.
4. **Cold index time**: wall time of the first full index (`cold_index_s`).

**Formula.** A cohort's gate is the count of repositories where each check is true, over the
repositories where it ran (`null` means it did not run, e.g. no probe snippet exists for that
language). The headline reduction is the median over repositories.

**n.** One pass per repository. The hash and the equivalence checks are deterministic, so one
pass settles them; `cold_index_s` is a single sample and is evidence only.

**Limits.** See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md#fase-a).
