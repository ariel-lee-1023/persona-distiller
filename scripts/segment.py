#!/usr/bin/env python3
"""
segment.py — cut extracted text into clusters and emit a schema-valid manifest (Stage 1).

`pipeline.md` requires the corpus be segmented into clusters and indexed in
`clusters/manifest.json`, because the projectibility probe needs a regularity to appear in ≥2
independent clusters. Cutting a multi-work volume by hand is where two errors get made, and both
are silent:

  * BOUNDARY DRIFT — a slice that runs past the end of one work into the next, so a "cluster"
    mixes two registers and every per-cluster metric averages across them.
  * EDITORIAL BLEED — front matter, historical introductions, translator's notes, endnotes and
    indexes captured as if they were the subject's own words, which quietly lowers the firsthand
    ratio the whole run is scored against.

You supply a spec naming each cluster and where it starts and stops. This slices it, strips the
running headers that repeat on every page of a scanned book, counts tokens, and writes a manifest
that validates against `references/schemas/clusters-manifest.schema.json`.

Boundaries may be given as line numbers or as regexes matched against the source. Regexes survive
re-extraction of the same source; line numbers do not, so prefer `start`/`end` over
`start_line`/`end_line` when the text has usable headings.

Spec (JSON):

    {
      "source_root": "raw",
      "strip_running_headers": ["^\\\\s*\\\\*?(Supplement|Historical Introduction)\\\\*?\\\\s*\\\\d*\\\\s*$"],
      "clusters": [
        {"id": "c01", "label": "Book: Either/Or I — Diapsalmata", "file": "either_or.txt",
         "start": "^# 1 DIAPSALMATA", "end": "^# PART TWO",
         "kind": "monologue", "period": "1843", "attribution": "firsthand"},
        {"id": "c02", "label": "Journals 1846", "file": "journals.txt",
         "start_line": 916, "end_line": 1580,
         "kind": "decision_record", "period": "1846", "attribution": "mixed"}
      ]
    }

`end` is exclusive — it is the marker that begins the *next* thing. Omit it to run to end of file.

Usage:
    python3 segment.py spec.json --out persona_work/
    python3 segment.py spec.json --out persona_work/ --dry-run     # boundaries only, writes nothing
"""

import argparse
import json
import os
import re
import sys

VALID_KIND = {"monologue", "dialogue", "decision_record"}
VALID_ATTR = {"firsthand", "secondhand", "mixed", "unknown"}


def find_marker(lines, pattern, start_at=0):
    rx = re.compile(pattern)
    for i in range(start_at, len(lines)):
        if rx.search(lines[i]):
            return i
    return None


def resolve_bounds(spec, lines):
    """Return (start_idx, end_idx) as 0-based, end exclusive."""
    if "start_line" in spec:
        start = spec["start_line"] - 1
    elif "start" in spec:
        start = find_marker(lines, spec["start"])
        if start is None:
            raise LookupError(f"start marker not found: {spec['start']!r}")
    else:
        start = 0

    if "end_line" in spec:
        end = spec["end_line"]
    elif "end" in spec:
        end = find_marker(lines, spec["end"], start + 1)
        if end is None:
            raise LookupError(f"end marker not found after start: {spec['end']!r}")
    else:
        end = len(lines)

    if end <= start:
        raise ValueError(f"end ({end}) is not after start ({start})")
    return start, end


def main():
    ap = argparse.ArgumentParser(description="Segment a corpus into clusters (Stage 1).")
    ap.add_argument("spec", help="JSON spec (see module docstring)")
    ap.add_argument("--out", required=True, help="work dir; writes <out>/clusters/")
    ap.add_argument("--dry-run", action="store_true", help="report boundaries, write nothing")
    args = ap.parse_args()

    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)

    root = spec.get("source_root", "")
    strippers = [re.compile(p) for p in spec.get("strip_running_headers", [])]
    outdir = os.path.join(args.out, "clusters")

    cache = {}
    manifest = []
    problems = []
    total = 0

    print(f"{'id':6s}{'label':44s}{'lines':>14s}{'words':>9s}{'kind':>16s}{'attr':>11s}")
    print("-" * 100)

    for c in spec["clusters"]:
        for key in ("id", "label", "file", "kind", "attribution"):
            if key not in c:
                sys.exit(f"cluster {c.get('id','?')}: missing required field {key!r}")
        if c["kind"] not in VALID_KIND:
            sys.exit(f"cluster {c['id']}: kind must be one of {sorted(VALID_KIND)}")
        if c["attribution"] not in VALID_ATTR:
            sys.exit(f"cluster {c['id']}: attribution must be one of {sorted(VALID_ATTR)}")
        if not re.fullmatch(r"c[0-9]{2,}", c["id"]):
            sys.exit(f"cluster {c['id']}: id must match ^c[0-9]{{2,}}$")

        path = os.path.join(root, c["file"]) if root else c["file"]
        if path not in cache:
            if not os.path.exists(path):
                sys.exit(f"cluster {c['id']}: source not found: {path}")
            cache[path] = open(path, encoding="utf-8", errors="replace").read().split("\n")
        lines = cache[path]

        try:
            start, end = resolve_bounds(c, lines)
        except (LookupError, ValueError) as exc:
            problems.append(f"{c['id']}: {exc}")
            print(f"{c['id']:6s}{c['label'][:42]:44s}{'FAILED':>14s}")
            continue

        chunk = [ln for ln in lines[start:end] if not any(rx.match(ln) for rx in strippers)]
        text = "\n".join(chunk)
        words = len(text.split())
        tokens = int(words * 1.33)  # rough English word→token ratio; refine if your host counts
        total += words

        if words < 400:
            problems.append(f"{c['id']}: only {words} words — a cluster this small corroborates "
                            f"nothing and cannot satisfy the ≥2-cluster rule meaningfully")

        rel = f"clusters/{c['id']}_{re.sub(r'[^a-z0-9]+', '_', c['label'].lower()).strip('_')[:40]}.txt"
        entry = {"id": c["id"], "label": c["label"], "source": rel,
                 "kind": c["kind"], "tokens": tokens, "attribution": c["attribution"]}
        for opt in ("period", "source_url", "retrieved", "revision"):
            if opt in c:
                entry[opt] = c[opt]
        manifest.append(entry)

        print(f"{c['id']:6s}{c['label'][:42]:44s}{f'{start+1}-{end}':>14s}"
              f"{words:9d}{c['kind']:>16s}{c['attribution']:>11s}")

        if not args.dry_run:
            os.makedirs(outdir, exist_ok=True)
            with open(os.path.join(args.out, rel), "w", encoding="utf-8") as fh:
                fh.write(text)

    fh_words = sum(len(open(os.path.join(args.out, m["source"]), encoding="utf-8").read().split())
                   for m in manifest if m["attribution"] == "firsthand") if not args.dry_run else None

    print(f"\n{len(manifest)} cluster(s), {total:,} words.")
    if fh_words is not None and total:
        print(f"firsthand_ratio ≈ {fh_words / total:.2f}  "
              f"(< 0.50 caps the core budget at 4,000 — see scoring.md)")
    if len(manifest) < 4:
        print("Fewer than 4 clusters: the corpus ceiling drops to 4,000 tokens, and cross-cluster "
              "corroboration gets thin. Consider splitting by chapter, session, or period.")

    if problems:
        print("\nProblems:")
        for p in problems:
            print(f"  - {p}")

    if not args.dry_run:
        with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump({"clusters": manifest}, fh, indent=2, ensure_ascii=False)
        print(f"\nwrote {outdir}/manifest.json")
        print("Run corpus_clean.py over the slices before style_metrics.py — segmenting damaged "
              "text just distributes the damage.")
    else:
        print("\nDry run — nothing written.")

    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
