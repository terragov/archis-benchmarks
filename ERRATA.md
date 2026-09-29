# Errata

Figures withdrawn or corrected after they were measured. An entry is never deleted; a
correction adds a line with the run that supersedes it.

| run | figure | status | reason |
|---|---|---|---|
| 0.47.0 | Infinite: session savings, success rates and reach, every level | withdrawn | The answer keys for the first, second and fourth levels of the ladder grade files other than the ones the prompt asked about: a rename of the shuffle seed reshuffled every level, and the answer-key cache was keyed on the grader and oracle versions but not on the seed or the file list, so three stale keys were served. Pending a re-grade with rebuilt keys. |
| 0.47.0 | CLI speed: `index (one file changed)` | withdrawn | The harness writes the same bytes on every pass, so the median of three measures the unchanged-content path. |
| 0.47.0 | Fase A, cohort 5: incremental == rebuild for `sql-server-samples` (`fase_a/cohort5.json`) | corrected: pass → fail | The cohort summary recorded a pass; the repository's own Fase A record has the incremental and clean-rebuild hashes different. The summary had been restored from an earlier pass after a re-measure. Corrected at export, with the evidence checked; see `corrections` in `runs/0.47.0/run.json`. |
