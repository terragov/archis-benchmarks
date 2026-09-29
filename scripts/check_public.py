#!/usr/bin/env python3
"""Fail if anything in the tree should not be public.

Runs on every pull request, independently of the exporter that produced it:
an export that slips past its own filters still stops here.

Checks:
  - private paths: result families that stay in the private tier;
  - file size: nothing over MAX_BYTES;
  - personal data: e-mail addresses, home directories, local volumes, UUID-style ids
    next to account/org/session keys;
  - internal terms: names of unreleased commands and flags. The list itself is not
    public, so it comes from the INTERNAL_TERMS environment variable (one term per
    line), set from a repository secret. Without it the check is reported as skipped,
    and --require-internal-terms turns that into a failure.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_BYTES = 1_000_000

SKIP_DIRS = {".git"}
# The checker and its workflow have to name the patterns they look for.
SELF = {"scripts/check_public.py", ".github/workflows/checks.yml"}

PRIVATE_PATHS = [
    "context_policy/*",
    "cavs/*",
    "artifacts/*",
    "session_economics/*",
    "v2/*", "v2_1/*", "v3/*", "v3_*/*",
    "recon/*",
    "*fase_c*",
    "*fase_d*",
    "*fase_j*",
    "*_stale*",
    "*_discarded*",
    "*TRUNCATED*",
    "*.log",
    "*stderr.txt",
    "*events.jsonl",
]

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
EMAIL_OK = re.compile(r"(@users\.noreply\.github\.com|@example\.(com|org)|^noreply@)$", re.I)
# Words that look like addresses in source code but are not (e.g. Package@swift-5.9.swift).
EMAIL_FALSE = re.compile(r"\.(swift|js|ts|py|go|rs|json|md)$", re.I)
HOME = re.compile(r"(/Users/(?!Shared\b)[A-Za-z0-9._-]+|/home/(?!runner\b)[A-Za-z0-9._-]+|/Volumes/[A-Za-z0-9._-]+|[A-Z]:\\\\Users\\\\[A-Za-z0-9._-]+)")
ACCOUNT_ID = re.compile(
    r"\"(org_id|organization_id|account_id|account_uuid|session_id|user_id|account_identity)\"\s*:\s*\"[^\"]+\"",
    re.I,
)


def tracked_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*"):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
            out.append(p)
    return sorted(out)


def load_terms() -> list[str]:
    raw = os.environ.get("INTERNAL_TERMS", "")
    return [t.strip() for t in raw.splitlines() if t.strip() and not t.startswith("#")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-internal-terms", action="store_true",
                    help="fail when INTERNAL_TERMS is not set")
    args = ap.parse_args()

    problems: list[str] = []
    terms = load_terms()

    for path in tracked_files():
        rel = path.relative_to(ROOT).as_posix()

        if any(fnmatch.fnmatch(rel, pat) for pat in PRIVATE_PATHS):
            problems.append(f"{rel}: private-tier path")
            continue

        size = path.stat().st_size
        if size > MAX_BYTES:
            problems.append(f"{rel}: {size:,} bytes (limit {MAX_BYTES:,})")

        if rel in SELF:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary; size already checked

        for n, line in enumerate(text.splitlines(), 1):
            for m in EMAIL.finditer(line):
                addr = m.group(0)
                if not EMAIL_OK.search(addr) and not EMAIL_FALSE.search(addr):
                    problems.append(f"{rel}:{n}: e-mail address")
            if HOME.search(line):
                problems.append(f"{rel}:{n}: local path ({HOME.search(line).group(0).split('/')[1]}/…)")
            if ACCOUNT_ID.search(line):
                problems.append(f"{rel}:{n}: account/session identifier")
            for t in terms:
                if t in line:
                    # never echo the term: the log of a public repo is public too
                    problems.append(f"{rel}:{n}: internal term #{terms.index(t) + 1}")

    if not terms:
        msg = "internal-terms check skipped: INTERNAL_TERMS is not set"
        if args.require_internal_terms:
            problems.append(msg)
        else:
            print(f"warning: {msg}", file=sys.stderr)

    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s) in {len(tracked_files())} file(s)", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
