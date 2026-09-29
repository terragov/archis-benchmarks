# archis-benchmarks

Public benchmark results for Archis, and the harness that measures them.

> **Not yet populated.** The first results arrive with the `run/0.47.0` export. Until then this
> repository holds only its scaffolding and the checks every export must pass.

## How results get here

Results are never pushed here directly. Each benchmark run is recorded internally first, then
exported as a pull request that contains only the public tier: allowlisted paths, sanitized
paths and identities. The checks in `.github/workflows/checks.yml` run again on every pull
request, independently of the exporter. A merged export is tagged `run/<version>`, and tags
are never rewritten; corrections go in `ERRATA.md` or arrive as a new run.

## Licences

- Data (results, reports, method cards): [CC BY 4.0](LICENSE)
- Code (scripts, harness): [MIT](LICENSE-CODE)
