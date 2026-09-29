# Infinite: agent sessions until the plan runs out

**Status for 0.47.0: withdrawn.** See [ERRATA.md](../ERRATA.md).

**Question.** On the same questions about the same files, how many tokens does a coding agent
spend with Archis available, compared with the agent alone, and does the answer stay as good?

**Design.** Two arms on the same model and plan type: `control` (the agent's own tools, no MCP
servers, no user configuration) and `chi_additive` (the same, plus Archis's MCP server). A ladder
of 23 levels from 1 to 320 files of one repository (prometheus v0.54.1, Go), each level a nested
prefix of a seeded shuffle. At each level the agent is asked, for every file, its line count, its
top-level symbols and its imports, plus cross-file questions.

**Grading.** Deterministic, no model judge. Questions and answers come from ctags and a text
scan, never from Archis. `score = 0.25·present + 0.25·lines_exact + 0.25·mean(symbol_F1, import_F1)
+ 0.25·answer_accuracy`; ×0.9 if the answer names a file that was not asked about. A session
succeeds at score ≥ 0.95 with every file present.

**Tokens.** From the agent CLI's final usage record: `billed_in = input + cache_read + cache_creation`.

**Savings.** `100 · (control − archis) / control` over levels both arms attempted, withheld unless
Archis's quality is within 0.02 of control.

**Configuration of the Archis arm.** A headline figure from this benchmark must come from an
arm that uses only released, documented settings of the Archis MCP server, so that anyone can
run the same arm with the shipped binary. The exact configuration is published with the harness.

**n.** One repetition per level per pass; levels are nested, so they are correlated.

**Limits.** See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md#infinite).
