#!/usr/bin/env python3
"""Generate README.md from the data in this repository.

Every figure in the README is computed here from a file under runs/, and the section
that shows it names that file. Nothing is typed by hand: `--check` fails when the README
does not match the data, and CI runs it on every pull request.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import validate  # noqa: E402  (claims are evaluated by the same code CI uses)

STATUS_WORD = {"headline": "headline", "evidence": "evidence only", "withdrawn": "**withdrawn**"}


def load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def pct(x, digits=1) -> str:
    return "—" if x is None else f"{100 * x:.{digits}f}%"


def mean(xs):
    xs = [x for x in xs if isinstance(x, (int, float)) and not isinstance(x, bool)]
    return statistics.fmean(xs) if xs else None


def median(xs):
    xs = [x for x in xs if isinstance(x, (int, float)) and not isinstance(x, bool)]
    return statistics.median(xs) if xs else None


def frac(rows, key) -> str:
    vals = [r.get(key) for r in rows if isinstance(r.get(key), bool)]
    return f"{sum(vals)}/{len(vals)}" if vals else "—"


def section_runs(manifest) -> list[str]:
    out = ["## Runs", "",
           "One directory per run under `runs/<version>/`, and one tag per run. A run is never",
           "rewritten after it is merged: corrections are listed in [ERRATA.md](ERRATA.md) or arrive",
           "as a new run.", "",
           "| version | date | tag | files | status per family |", "|---|---|---|--:|---|"]
    for r in manifest["runs"]:
        fams = " · ".join(f"{k}: {STATUS_WORD.get(v, v)}" for k, v in r["families"].items())
        out.append(f"| [{r['version']}](runs/{r['version']}/run.json) | {r['date'][:10]} | "
                   f"`{r['tag']}` | {r['files']} | {fams} |")
    return out + [""]


def section_fase_a(run_dir: Path, run) -> list[str]:
    fam = run["families"].get("fase_a")
    if not fam:
        return []
    out = ["## Fase A: does indexing hold up?", "",
           "Two indexes of the same tree must produce the same canonical graph hash; an incremental",
           "re-index after edits must converge on what a clean rebuild writes; and `reduction` is how",
           "much smaller Archis's representation is than the source, in tokens. Method:",
           f"[{fam['method']}]({fam['method']}).", "",
           "| cohort | repos | hash deterministic | incremental == rebuild | median reduction | file |",
           "|---|--:|--:|--:|--:|---|"]
    for rel in fam["files"]:
        if not rel.startswith("fase_a/cohort") or rel.endswith("_languages.json"):
            continue
        rows = load(run_dir / rel)
        name = Path(rel).stem
        out.append(f"| {name} | {len(rows)} | {frac(rows, 'hash_stable')} | "
                   f"{frac(rows, 'incremental_equiv')} | {pct(median(r.get('reduction') for r in rows))} | "
                   f"[`{rel}`](runs/{run['version']}/{rel}) |")
    out += ["", "Cold index times (`cold_index_s`) are in the same files. They are one sample per",
            "repository, so they are evidence, not a headline figure.", ""]
    return out


def section_fase_b(run_dir: Path, run) -> list[str]:
    fam = run["families"].get("fase_b")
    if not fam:
        return []
    rec = load(run_dir / "fase_b/recall.json") or []
    rel = load(run_dir / "fase_b/relations.json") or []
    by_lang = defaultdict(list)
    for r in rec:
        by_lang[r["language"]].append(r)
    calls_by_lang = defaultdict(list)
    for r in rel:
        calls_by_lang[r["language"]].append(r.get("calls_recall"))
    v = run["version"]
    out = ["## Fase B: is the graph right?", "",
           "Archis's symbols and relations graded against an independent parser for each language",
           "(universal-ctags, or the language's own compiler front end), never against Archis's own",
           f"output. Method: [{fam['method']}]({fam['method']}).", "",
           "**Strict recall** counts a symbol as found only when Archis has it under the same name *and*",
           "the same file. **Lenient recall** also accepts the name anywhere in the repository; it is the",
           "figure earlier reports led with, and it is shown for comparison only.", "",
           f"Symbol recall across {len(rec)} repositories in {len(by_lang)} languages, and relations across",
           f"{len(rel)} repositories in {len(calls_by_lang)} languages, measured with chi {v}. A language with",
           "relation rows but no symbol-recall rows for this binary shows — in the recall columns.", "",
           "| measure | mean over repositories | file |", "|---|--:|---|",
           f"| symbol recall, strict | {pct(mean(r.get('recall_strict_path') for r in rec))} | "
           f"[`fase_b/recall.json`](runs/{v}/fase_b/recall.json) |",
           f"| symbol recall, lenient | {pct(mean(r.get('recall') for r in rec))} | same |",
           f"| structural recall | {pct(mean(r.get('recall_structural') for r in rec))} | same |",
           f"| CALLS recall | {pct(mean(r.get('calls_recall') for r in rel))} | "
           f"[`fase_b/relations.json`](runs/{v}/fase_b/relations.json) |",
           f"| heritage recall | {pct(mean(r.get('heritage_recall') for r in rel))} | same |",
           "",
           "| language | repos | strict recall | lenient recall | CALLS recall |",
           "|---|--:|--:|--:|--:|"]
    for lang in sorted(set(by_lang) | set(calls_by_lang)):
        rows = by_lang.get(lang, [])
        n = len(rows) or len(calls_by_lang[lang])
        out.append(f"| `{lang}` | {n} | {pct(mean(r.get('recall_strict_path') for r in rows))} | "
                   f"{pct(mean(r.get('recall') for r in rows))} | {pct(mean(calls_by_lang.get(lang, [])))} |")
    out += ["", f"Precision by sampling is in [`fase_b/precision.json`](runs/{v}/fase_b/precision.json) as",
            "evidence; [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) explains why it is not a headline.", ""]
    return out


def section_cli_speed(run_dir: Path, run) -> list[str]:
    fam = run["families"].get("cli_speed")
    if not fam:
        return []
    data = load(run_dir / "cli_speed.json")
    withdrawn = fam.get("withdrawn_commands", {})
    shown = ["index --full (cold)", "index (no change)", "index (one file changed)", "status",
             "context", "search", "callers <symbol>", "impact <symbol>", "source <symbol>"]
    repos = data["repos"]
    v = run["version"]
    env = load(run_dir / "environment.json") or {}
    machine = f" on {env['cpu']} ({env.get('cores', '?')} cores, {env.get('ram_mb', 0) // 1024} GB)" if env.get("cpu") else ""
    out = ["## CLI speed", "",
           f"Wall time of `chi` commands in seconds{machine}: the median of the passes, with the number",
           "of passes next to it.",
           f"Full table, every command: [`cli_speed.json`](runs/{v}/cli_speed.json). Method: [{fam['method']}]({fam['method']}).", "",
           "| command | " + " | ".join(f"{r['name']} ({r['files']:,} files)" for r in repos) + " |",
           "|---|" + "--:|" * len(repos)]
    for cmd in shown:
        if cmd in withdrawn:
            out.append(f"| `{cmd}` | " + " | ".join("withdrawn¹" for _ in repos) + " |")
            continue
        cells = []
        for r in repos:
            res = r["results"].get(cmd)
            cells.append("—" if not res else f"{res['median_s']:.3f} (n={len(res['runs'])})")
        out.append(f"| `{cmd}` | " + " | ".join(cells) + " |")
    for i, (cmd, why) in enumerate(withdrawn.items(), 1):
        out += ["", f"¹ `{cmd}`: {why}"]
    return out + [""]


def section_languages(run_dir: Path, run) -> list[str]:
    fam = run["families"].get("conformance")
    if not fam:
        return []
    rows = load(run_dir / "conformance/support_matrix.json")
    v = run["version"]
    out = ["## Language support", "",
           "The support level of each language and its score on the capability matrix, which runs on",
           "small fixtures: a ceiling, not what is seen at scale (Fase B above is that). Method:",
           f"[{fam['method']}]({fam['method']}). File: [`conformance/support_matrix.json`](runs/{v}/conformance/support_matrix.json).", "",
           "| language | level | matrix score |", "|---|---|--:|"]
    for r in sorted(rows, key=lambda r: (-(r.get("measured_score") or 0), r["language"])):
        out.append(f"| `{r['language']}` | {r.get('support_level')} | {pct(r.get('measured_score'), 0)} |")
    return out + [""]


def section_withdrawn(run) -> list[str]:
    out = []
    for name, fam in run["families"].items():
        if fam["status"] == "withdrawn":
            out += [f"### {name}: withdrawn", "", fam.get("reason", ""), "",
                    f"The raw rows are kept under `runs/{run['version']}/{name}/` so the withdrawal can be",
                    f"checked. Method: [{fam['method']}]({fam['method']}).", ""]
    return (["## Withdrawn", ""] + out) if out else []


def section_claims(claims_path: Path) -> list[str]:
    claims = load(claims_path) or {"claims": []}
    results = validate.evaluate_claims(claims, ROOT)
    out = ["## Claims", "",
           "Every figure Archis states publicly, and the file and field that back it. CI recomputes each",
           "one from the data on every pull request and fails if a claim and its data disagree.", ""]
    if not results:
        return out + ["No claims are registered yet.", ""]
    out += ["| claim | stated | measured | source |", "|---|--:|--:|---|"]
    for c, measured, ok in results:
        mark = "" if ok else " ✗"
        out.append(f"| {c['claim']} | {validate.fmt(c['value'], c.get('format'))} | "
                   f"{validate.fmt(measured, c.get('format'))}{mark} | `{c['file']}` · `{c['field']}` ({c['aggregate']}) |")
    return out + [""]


def build() -> str:
    manifest = load(ROOT / "MANIFEST.json")
    lines = ["# archis-benchmarks", "",
             "Public benchmark results for Archis: what it claims, how each figure was measured, and",
             "what is known to be weak. Results come from the internal campaign for each release and are",
             "exported here by pull request, filtered and sanitized; see [How results get here](#how-results-get-here).", "",
             "> Generated by `scripts/build_readme.py` from the files in this repository. Do not edit by hand.", ""]
    if not manifest or not manifest.get("runs"):
        return "\n".join(lines + ["No runs have been exported yet.", ""])
    latest = manifest["runs"][0]
    run_dir = ROOT / "runs" / latest["version"]
    run = load(run_dir / "run.json")
    lines += [f"**Latest run: chi {latest['version']}**, {latest['date'][:10]}, tag `{latest['tag']}`. "
              f"Record: [`runs/{latest['version']}/run.json`](runs/{latest['version']}/run.json).", ""]
    for sect in (section_fase_a(run_dir, run), section_fase_b(run_dir, run), section_cli_speed(run_dir, run),
                 section_languages(run_dir, run), section_withdrawn(run), section_claims(ROOT / "claims.json"),
                 section_runs(manifest)):
        lines += sect
    lines += ["## How results get here", "",
              "Each release's benchmark campaign is recorded internally first. A run reaches this",
              "repository only as a pull request that an export script opens: it copies an allowlisted set",
              "of result files, keeps only rows measured with that run's binary, replaces machine paths",
              "and account identities, and runs the same checks CI runs again here",
              "([`scripts/check_public.py`](scripts/check_public.py), [`scripts/validate.py`](scripts/validate.py)).",
              "Merging a pull request tags it.", "",
              "## Reading further", "",
              "- [methods/](methods/): one card per benchmark: what it measures, the formula, n, limits",
              "- [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md): where each benchmark falls short",
              "- [ERRATA.md](ERRATA.md): figures withdrawn or corrected after publication",
              "- [CORPUS.md](CORPUS.md): every repository measured, its pin and licence",
              "- [schemas/](schemas/): JSON Schema for every result file",
              "- [REPRODUCING.md](REPRODUCING.md): what you can re-run today, and what is coming", "",
              "## Licences", "",
              "Data: [CC BY 4.0](LICENSE). Code: [MIT](LICENSE-CODE).", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if README.md is not what the data gives")
    args = ap.parse_args()
    text = build()
    readme = ROOT / "README.md"
    if args.check:
        if readme.read_text() != text:
            print("README.md does not match the data; run scripts/build_readme.py", file=sys.stderr)
            return 1
        return 0
    readme.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
