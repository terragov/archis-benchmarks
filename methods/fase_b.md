# Fase B: graph fidelity against independent oracles

**Question.** Are the symbols and relations in Archis's graph the ones the source code has?

**Principle.** Archis is graded against a *different extraction path*, never against its own
output. A language whose oracle is not installed is reported as skipped, not as recall 0.

| language | oracle |
|---|---|
| Ruby · Elixir · Swift · Scala · Groovy · Zig · Haskell · R · HCL | Prism · `Code.string_to_quoted` · swift-syntax · Scalameta · Groovy compiler · `std.zig.Ast` · GHC parser · `parse()` · hashicorp/hcl |
| GraphQL · YAML · Dockerfile · Bash · TOML · CSS · HTML · Proto | graphql-core · PyYAML + bashlex · dockerfile-parse + bashlex · `shfmt --tojson` · tomllib · tinycss2 · html5lib + tinycss2 + acorn · protoc (relations only) |
| C · C++ · Objective-C | ctags (C declarations) and libclang (relations) |
| Lua | luaparser |
| everything else | universal-ctags |

**Symbol recall** (`recall.json`). The oracle yields `(name, file, kind)` rows; Archis's graph
yields its symbols for the same language after `chi index`.
- `recall_strict_path = |oracle ∩ archis| / |oracle|` matching on `(name, file)`, deduplicated.
  **This is the headline.**
- `recall` (lenient) also counts a row as found when the name appears anywhere in the repository,
  or its last dotted segment matches in the same file. Shown for comparison with earlier reports.
- `recall_structural`: the same, restricted to structural kinds (types, functions, methods).

**Relation recall** (`relations.json`). Heritage: `(child, parent)` pairs from the oracle found in
Archis's EXTENDS/IMPLEMENTS edges. CALLS: call sites found by a lexical `name(` scan per file,
counted as found when Archis has a CALLS edge from the enclosing symbol.

**Precision** (`precision.json`, evidence). A deterministic stride sample of up to 400 edges per
kind, each checked against the source text around it; plus five fabricated names that search
must not return.

**Formula.** Headline figures are the mean over repositories of the per-repository ratio.

**n.** One pass; extraction is deterministic. Each row carries the binary that produced it in
its `chi` field, and a run exports only its own binary's rows.

**Limits.** See [KNOWN_LIMITATIONS.md](../KNOWN_LIMITATIONS.md#fase-b).
