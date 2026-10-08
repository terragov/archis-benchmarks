#!/usr/bin/env python3
"""Check every result file against its schema, and every claim against the data.

- Every .json and .csv under runs/, plus MANIFEST.json, corpus.json and claims.json, must
  match a schema in schemas/. A result file with no schema is an error: a new kind of file
  needs its schema in the same pull request.
- Every claim in claims.json is recomputed from the file and field it names, and must be
  within its tolerance of the stated value.

Standard library only. The validator implements the part of JSON Schema the schemas here
use: type, required, properties, additionalProperties, items, enum, pattern, minimum,
maximum, minItems.
"""

from __future__ import annotations

import csv
import fnmatch
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCHEMA_FOR = [
    ("MANIFEST.json", "manifest"),
    ("corpus.json", "corpus"),
    ("claims.json", "claims"),
    ("runs/*/run.json", "run"),
    ("runs/*/environment.json", "environment"),
    ("runs/*/fase_a/cohort5_languages.json", "fase_a_languages"),
    ("runs/*/fase_a/cohort*.json", "fase_a_summary"),
    ("runs/*/fase_b/recall.json", "fase_b_recall"),
    ("runs/*/fase_b/precision.json", "fase_b_precision"),
    ("runs/*/fase_b/relations.json", "fase_b_relations"),
    ("runs/*/cli_speed.json", "cli_speed"),
    ("runs/*/conformance/support_matrix.json", "support_matrix"),
    ("runs/*/infinite/levels.csv", "infinite_levels"),
    ("runs/*/infinite/runs.csv", "infinite_runs"),
]

TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "number": (int, float), "integer": int, "null": type(None),
}


def is_type(v, t: str) -> bool:
    if t in ("number", "integer") and isinstance(v, bool):
        return False
    return isinstance(v, TYPES[t])


def check(v, s: dict, where: str, errs: list[str]) -> None:
    if len(errs) > 50:
        return
    if "type" in s:
        ts = s["type"] if isinstance(s["type"], list) else [s["type"]]
        if not any(is_type(v, t) for t in ts):
            errs.append(f"{where}: expected {'/'.join(ts)}, got {type(v).__name__}")
            return
    if "enum" in s and v not in s["enum"]:
        errs.append(f"{where}: {v!r} not in {s['enum']}")
    if isinstance(v, str) and "pattern" in s and not re.search(s["pattern"], v):
        errs.append(f"{where}: {v!r} does not match {s['pattern']}")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if "minimum" in s and v < s["minimum"]:
            errs.append(f"{where}: {v} < {s['minimum']}")
        if "maximum" in s and v > s["maximum"]:
            errs.append(f"{where}: {v} > {s['maximum']}")
    if isinstance(v, dict):
        for k in s.get("required", []):
            if k not in v:
                errs.append(f"{where}: missing '{k}'")
        props = s.get("properties", {})
        for k, x in v.items():
            if k in props:
                check(x, props[k], f"{where}.{k}", errs)
            elif s.get("additionalProperties") is False:
                errs.append(f"{where}: unexpected '{k}'")
            elif isinstance(s.get("additionalProperties"), dict):
                check(x, s["additionalProperties"], f"{where}.{k}", errs)
    if isinstance(v, list):
        if len(v) < s.get("minItems", 0):
            errs.append(f"{where}: fewer than {s['minItems']} items")
        if "items" in s:
            for i, x in enumerate(v):
                check(x, s["items"], f"{where}[{i}]", errs)


def read(p: Path):
    if p.suffix == ".csv":
        return list(csv.DictReader(p.open()))
    return json.loads(p.read_text())


def schema_name(rel: str) -> str | None:
    for pat, name in SCHEMA_FOR:
        if fnmatch.fnmatch(rel, pat):
            return name
    return None


def validate_files(root: Path) -> list[str]:
    errs: list[str] = []
    targets = [p for p in (root / "runs").rglob("*") if p.suffix in (".json", ".csv")] if (root / "runs").exists() else []
    targets += [root / n for n in ("MANIFEST.json", "corpus.json", "claims.json") if (root / n).exists()]
    for p in sorted(targets):
        rel = p.relative_to(root).as_posix()
        name = schema_name(rel)
        if name is None:
            errs.append(f"{rel}: no schema covers this file (add one to schemas/ and SCHEMA_FOR)")
            continue
        sp = root / "schemas" / f"{name}.schema.json"
        if not sp.exists():
            errs.append(f"{rel}: schema {sp.name} is missing")
            continue
        try:
            data = read(p)
        except (json.JSONDecodeError, csv.Error) as e:
            errs.append(f"{rel}: unreadable ({e})")
            continue
        check(data, json.loads(sp.read_text()), rel, errs)
    return errs


# ---- claims ---------------------------------------------------------------------------

def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


AGGREGATES = {
    "mean": lambda xs: statistics.fmean([x for x in xs if _num(x)]),
    "median": lambda xs: statistics.median([x for x in xs if _num(x)]),
    "min": lambda xs: min(x for x in xs if _num(x)),
    "max": lambda xs: max(x for x in xs if _num(x)),
    "sum": lambda xs: sum(x for x in xs if _num(x)),
    "count": lambda xs: len(xs),
    "count_true": lambda xs: sum(1 for x in xs if x is True),
    "count_false": lambda xs: sum(1 for x in xs if x is False),
    "value": lambda xs: xs[0] if len(xs) == 1 else None,
}


def pick(rows, field: str):
    """field is a dotted path; rows is a list of objects, or one object."""
    items = rows if isinstance(rows, list) else [rows]
    out = []
    for r in items:
        v = r
        for part in field.split("."):
            v = v.get(part) if isinstance(v, dict) else None
        out.append(v)
    return out


def evaluate_claims(claims: dict, root: Path):
    results = []
    for c in claims.get("claims", []):
        p = root / c["file"]
        if not p.exists():
            results.append((c, None, False))
            continue
        rows = read(p)
        where = c.get("where") or {}
        if isinstance(rows, list) and where:
            rows = [r for r in rows if all(r.get(k) == v for k, v in where.items())]
        try:
            measured = AGGREGATES[c["aggregate"]](pick(rows, c["field"]))
        except (ValueError, statistics.StatisticsError, KeyError):
            measured = None
        ok = measured is not None and abs(measured - c["value"]) <= c.get("tolerance", 0)
        results.append((c, measured, ok))
    return results


def fmt(x, style: str | None) -> str:
    if x is None:
        return "—"
    if style == "pct0":
        return f"{100 * x:.0f}%"
    if style == "pct1":
        return f"{100 * x:.1f}%"
    if style == "int":
        return f"{int(round(x)):,}"
    if style == "s":
        return f"{x:.3f} s"
    return f"{x:g}" if isinstance(x, float) else str(x)


def main() -> int:
    errs = validate_files(ROOT)
    claims = json.loads((ROOT / "claims.json").read_text()) if (ROOT / "claims.json").exists() else {}
    for c, measured, ok in evaluate_claims(claims, ROOT):
        if not ok:
            errs.append(f"claim {c['id']}: states {fmt(c['value'], c.get('format'))}, "
                        f"data gives {fmt(measured, c.get('format'))} ({c['file']} · {c['field']})")
    errata = (ROOT / "ERRATA.md").read_text() if (ROOT / "ERRATA.md").exists() else ""
    for rp in sorted((ROOT / "runs").glob("*/run.json")) if (ROOT / "runs").exists() else []:
        run = json.loads(rp.read_text())
        for c in run.get("corrections", []):
            if not any(line.startswith(f"| {run['version']} |") and c["file"] in line for line in errata.splitlines()):
                errs.append(f"{rp.relative_to(ROOT)}: correction to {c['file']} has no row in ERRATA.md")
    for e in errs:
        print(e)
    print(f"validate: {len(errs)} problem(s)", file=sys.stderr)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
