# Known limitations

Where each published benchmark falls short, from an internal review of the harnesses. A figure
affected by a limitation that changes its meaning is kept out of the README headline or
withdrawn ([ERRATA.md](ERRATA.md)); the rest are stated here so the numbers can be read with them.

## Corpus

- Some repositories are not pinned and follow their default branch; [CORPUS.md](CORPUS.md) lists
  them. Two runs may not have measured the same tree for those.
- Fase B uses its own per-cohort repository lists, which do not always match the manifest's
  cohorts one to one.

## Fase A

- **One sample per repository** for every timing. Cold index times have no variance estimate
  and are evidence only.
- "Cold" is declared, not enforced: the operating system's page cache is not purged.
- Incremental equivalence probes one file per repository in four steps. Languages without a probe
  snippet (JavaScript, Rust, C, C++, CSS, HTML, TOML, Haskell, R, PHP, XML) report `null`, not a pass.

## Fase B

- **Lenient recall is lenient.** It counts a symbol as found when its name appears anywhere in the
  repository, so common names (`init`, `main`, `get`) match regardless of where they live. The
  headline uses strict recall for that reason.
- universal-ctags filtering approximates, but does not mirror, the files Archis ignores.
- **Heritage recall** matches `(child name, parent last segment)` without the file, so homonymous
  types collapse. For TypeScript, JavaScript, Java, C#, Kotlin, PHP and Rust the heritage oracle is
  a regular expression, not a parser. Python has none; Go is excluded.
- **CALLS recall** comes from a lexical `name(` scan per file, not a parser.
- **Precision is not a lower bound.** Its checks look for the target in the source text near the
  edge, and comments, strings and whole-file windows can confirm an edge that is not there. Symbol
  precision (the name appears in its own span) is close to tautological. Published as evidence only.
- Fabricated-name negatives treat a failed search as "not invented".

## CLI speed

- Three passes; no page-cache purge for "cold".
- `index (one file changed)` writes the same bytes on every pass, so only the first pass is a real
  change and the median measures the unchanged-content path. **Withdrawn for 0.47.0.**

## Infinite

- **The answer keys for three levels grade the wrong files** in 0.47.0: the whole run is withdrawn.
- One repository, one language, one model family; one repetition per level per pass; levels are
  nested prefixes, so they are correlated rather than independent samples.
- Savings are a ratio of means over attempted levels; runs that ended for infrastructure reasons
  (plan exhausted, rate limit, timeout) are counted with score 0 rather than excluded.
- Arms run sequentially, at different times, on different plan accounts.
- At the top of the ladder a perfect answer is larger than the model's output limit, so the output
  ceiling binds before the context one.
- No confidence intervals or significance tests yet.

## Across all benchmarks

- Nothing runs in CI yet: every figure comes from a campaign run by hand on one machine.
- Harness code is published one or two releases after the results it produced
  ([REPRODUCING.md](REPRODUCING.md)).
