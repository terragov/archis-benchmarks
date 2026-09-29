# CLI speed

**Question.** How long does each `chi` command take on small, medium and large repositories?

**What runs.** Each command in the table runs three times per repository (once for heavy
commands above 8,000 files) in an isolated state directory, on the bench machine with nothing
else scheduled. A failing command is marked and still timed. "Cold" deletes the repository's
index before the pass.

**Formula.** Median and minimum of the passes; every pass is kept in `runs`.

**n.** 3 per command, as stated next to each figure.

**Limits.** See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md#cli-speed). One command is
withdrawn for 0.47.0; see [ERRATA.md](../ERRATA.md).
