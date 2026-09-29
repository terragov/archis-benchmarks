# Language support matrix

**Question.** For each language, which capabilities (symbols, calls, types, heritage, overrides,
imports, exports, tests) does Archis extract, and how well, on fixtures written to exercise them?

**What runs.** A fixture set per language, with the expected symbols and relations written by
hand, indexed with the release binary.

**Formula.** `measured_score` is the share of expected facts Archis produces. `support_level` is
the graduation state of the language (STABLE or PREVIEW).

**Reading it.** The matrix is a ceiling: fixtures are small and cover what they were written for.
What Archis sees on real repositories is Fase B.

**n.** One pass; deterministic.
