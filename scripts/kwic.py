#!/usr/bin/env python3
"""
kwic.py — keyword-in-context retrieval of evidence passages (Stage 2).

Every element in `extractions.json` carries 1–3 short example passages, and the Stage 5 tests are
scored against that evidence. Pulling it out of a large corpus with `grep` does not work: source
text arrives with paragraphs on single lines thousands of characters long, so a match returns the
whole paragraph, and matches that straddle a line break are missed entirely.

This normalises whitespace first, then returns a fixed-width window around each hit — the shape
evidence actually needs. `--json` emits straight into the `evidence` field of an extraction.

Usage:
    # one pattern across the cluster directory
    python3 kwic.py clusters/ "dizziness of freedom"

    # alternation, wider left context, first 3 hits per file
    python3 kwic.py clusters/ "levell?ing|the public is" --before 300 --after 900 --max 3

    # straight into an extraction's evidence field
    python3 kwic.py clusters/ "opposite of sin" --json evidence.json

    # which clusters mention this at all — the ≥2-cluster check for a projectible regularity
    python3 kwic.py clusters/ "single individual" --count

PATTERN IS A PYTHON REGEX, NOT A SHELL ONE. Alternation is `a|b`. Writing `a\\|b` — the habit from
grep and sed — matches a literal pipe and silently returns nothing, which reads exactly like a
corpus that lacks the passage. If a search comes back empty on a term you are confident is there,
check this before concluding anything about the corpus.
"""

import argparse
import json
import os
import re
import sys

WS = re.compile(r"\s+")


def iter_files(path):
    if os.path.isfile(path):
        yield path
        return
    for root, _, names in os.walk(path):
        for n in sorted(names):
            if n.endswith((".txt", ".md")):
                yield os.path.join(root, n)


def main():
    ap = argparse.ArgumentParser(
        description="Keyword-in-context evidence retrieval (Stage 2).",
        epilog="PATTERN is a Python regex: use a|b for alternation, never a\\|b.")
    ap.add_argument("path", help="text file or directory of .txt/.md files")
    ap.add_argument("pattern", help="Python regex")
    ap.add_argument("--before", type=int, default=250, help="chars of left context (default 250)")
    ap.add_argument("--after", type=int, default=900, help="chars of right context (default 900)")
    ap.add_argument("--max", type=int, default=2, help="max hits per file (default 2)")
    ap.add_argument("--case-sensitive", action="store_true")
    ap.add_argument("--count", action="store_true",
                    help="hit counts per file only — the ≥2-cluster corroboration check")
    ap.add_argument("--json", help="write hits here, shaped for an extraction's evidence field")
    args = ap.parse_args()

    if r"\|" in args.pattern:
        print(r"warning: pattern contains \| — in a Python regex that is a LITERAL pipe.",
              file=sys.stderr)
        print(r"         For alternation write a|b. Continuing as given.", file=sys.stderr)

    try:
        rx = re.compile(args.pattern, 0 if args.case_sensitive else re.I)
    except re.error as exc:
        sys.exit(f"bad regex: {exc}")

    files = list(iter_files(args.path))
    if not files:
        sys.exit(f"no .txt/.md files under {args.path}")

    out = []
    clusters_hit = 0
    total = 0

    for p in files:
        text = WS.sub(" ", open(p, encoding="utf-8", errors="replace").read())
        hits = list(rx.finditer(text))
        if hits:
            clusters_hit += 1
            total += len(hits)

        if args.count:
            if hits:
                print(f"{os.path.basename(p):44s}{len(hits):6d}")
            continue

        if not hits:
            continue

        print(f"\n=== {os.path.basename(p)}  ({len(hits)} hit{'s' if len(hits) != 1 else ''})")
        for m in hits[:args.max]:
            left = max(0, m.start() - args.before)
            right = min(len(text), m.end() + args.after)
            window = text[left:right]
            print(f"…{window}…\n")
            out.append({"file": os.path.basename(p), "offset": m.start(),
                        "match": m.group(0), "window": window})

    print(f"\n{total} hit(s) in {clusters_hit} of {len(files)} file(s).")
    if clusters_hit < 2:
        print("Fewer than 2 files contain this. A projectible regularity needs ≥2 independent")
        print("clusters — as evidence for one, this is a single-cluster observation at best.")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"pattern": args.pattern, "n_files_hit": clusters_hit,
                       "n_hits": total, "hits": out}, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.json}")
        print("Trim each window to the shortest span that carries the point before it goes into")
        print("extractions.json — evidence is for scoring, not for pasting into the core.")


if __name__ == "__main__":
    main()
