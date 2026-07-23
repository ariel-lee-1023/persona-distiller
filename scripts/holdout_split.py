#!/usr/bin/env python3
"""
holdout_split.py — reproducible masked split for the held-out projection test (Stage 5).

Given a list of qualifying passage IDs, deterministically selects ~10–15% to mask, using a fixed
seed so the split is auditable and repeatable. The distiller then predicts the persona's
stance/move on the masked IDs using only the un-masked evidence, and scores alignment.

Usage:
    # from a JSON file: {"passages": ["p001", "p002", ...]}
    python3 holdout_split.py passages.json --seed 42 --frac 0.12 --out split.json

    # or pass IDs directly
    python3 holdout_split.py --ids p001 p002 p003 ... --seed 42
"""

import argparse
import json
import math
import random
import sys


def load_ids(args):
    if args.ids:
        return list(args.ids)
    if args.infile:
        with open(args.infile, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "passages" in data:
            return list(data["passages"])
        if isinstance(data, list):
            return list(data)
        sys.exit('JSON must be a list of IDs or {"passages": [...]}')
    sys.exit("provide a JSON file or --ids")


def main():
    ap = argparse.ArgumentParser(description="Reproducible held-out split for the projection test.")
    ap.add_argument("infile", nargs="?", help='JSON: {"passages":[...]} or a bare list')
    ap.add_argument("--ids", nargs="+", help="pass passage IDs directly")
    ap.add_argument("--seed", type=int, default=42, help="fixed seed for reproducibility")
    ap.add_argument("--frac", type=float, default=0.12, help="fraction to mask (0.10–0.15 typical)")
    ap.add_argument("--out", help="write split JSON here")
    args = ap.parse_args()

    ids = load_ids(args)
    n = len(ids)
    if n < 4:
        sys.exit(f"need at least 4 qualifying passages to hold out a meaningful set (got {n})")

    k = max(1, math.ceil(args.frac * n))
    rng = random.Random(args.seed)
    masked = sorted(rng.sample(ids, k))
    kept = [i for i in ids if i not in set(masked)]

    result = {"seed": args.seed, "frac": args.frac, "n_total": n,
              "n_masked": k, "masked": masked, "kept": kept}

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.out}")

    print(f"total {n}  masked {k} (seed {args.seed}, frac {args.frac})")
    print("masked:", ", ".join(masked))
    print("\nPredict the persona's stance/move on each masked ID using ONLY the kept evidence,")
    print("then score alignment against the true masked passage (2=stance+reasoning, 1=direction, 0=miss).")


if __name__ == "__main__":
    main()
