# Reproducing

## Today

- **Every figure in the README can be recomputed from the files here.** `python3 scripts/validate.py`
  recomputes each registered claim; `python3 scripts/build_readme.py --check` regenerates the
  README and fails if it differs.
- The corpus is public: [CORPUS.md](CORPUS.md) has each repository's URL and pin.
- The method cards in [methods/](methods/) give each benchmark's procedure and formula.

## Coming: the harness

The harness that produced these results is published one or two releases after the results
themselves, so it only ever describes behaviour that has shipped. What will be published:

- the independent oracles and graders for Fase B, and the grader and answer-key builder for Infinite;
- the drivers for Fase A, Fase B, CLI speed and Infinite, written against a small tool interface
  (`index(repo)`, `dump_symbols()`, `run_session(arm)`), with a reference adapter;
- the JSON schemas, which are already here.

Each run's `run.json` records whether the harness that produced it is public yet.
