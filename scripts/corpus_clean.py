#!/usr/bin/env python3
"""
corpus_clean.py — extraction-damage census and repair for Stage 1 (ingest).

`pipeline.md` says to sanity-check every extraction and flag anything garbled. This is the check.
Converted corpora carry three kinds of damage that are easy to miss by eye and that corrupt the
expression pass *silently* — which is the dangerous shape, because the run still produces tidy
numbers:

  1. LIGATURE LOSS  — PDF/EPUB extraction drops fi/fl/ff/ffi, so "first" arrives as "rst",
     "difference" as "dierence", "reflective" as "reective". Poisons the lexical fingerprint and
     the conspicuously-absent-words list, and makes quoted evidence unusable.
  2. SOFT HYPHENATION — text set with justified columns wraps words across lines: "transporta-
     tion". Extraction preserves the hyphen and the break, so one word is counted as two. Inflates
     word counts and sentence-length means by 1–2% and litters the top-terms list with fragments.
  3. MARKUP RESIDUE — EPUB anchors and page-position tokens (`epub-spine-…`, `filepos…`) survive
     conversion and enter the corpus as high-frequency "content words".

Detection is deliberately two-stage for ligatures: an f-frequency screen flags a file, and a
suspect-token census confirms it. The screen alone false-positives on short files, so a low
f-rate with no suspect tokens is not damage — it is a small sample. Both are reported.

Report by default; nothing is written unless you pass --fix.

Usage:
    # census only — always run this first
    python3 corpus_clean.py raw/

    # repair in place (writes .orig backups unless --no-backup)
    python3 corpus_clean.py raw/ --fix

    # repair into a separate tree, and extend the ligature map for this corpus
    python3 corpus_clean.py raw/ --fix --out clean/ --lexicon my_ligatures.json

--lexicon takes {"broken": "repaired", ...} and is merged over the built-in map, so a corpus with
its own vocabulary ("conation" -> "conflation") can be handled without editing this file.
"""

import argparse
import json
import os
import re
import sys

# --- markup residue ----------------------------------------------------------------------------

MARKUP = [
    (re.compile(r'<a id="[^"]*"></a>'), ""),
    (re.compile(r"\bepub-spine-\S*"), ""),
    (re.compile(r"\bfilepos\d+\b"), ""),
    (re.compile(r"\bsic\d{4,}\b"), ""),
    (re.compile(r"\bkindle:\S+"), ""),
    (re.compile(r"\bcalibre_[a-z0-9_]+\b"), ""),
]

# --- soft hyphenation --------------------------------------------------------------------------
# "transporta- tion" / "transporta-\ntion" -> "transportation".
#
# The hyphen MUST be followed by whitespace. That single requirement is what separates a wrapped
# word from a real compound: justified typesetting leaves "transporta-" at the end of a line, while
# "self-love" and "well-known" are written closed up. Without it this rule silently welds every
# hyphenated compound in the corpus into one token, which is worse damage than it repairs.
SOFT_HYPHEN = re.compile(r"([a-z]{2,})-\s+([a-z]{2,})")

# Suspended compounds — "pre- and post-war" — look identical to a wrapped word. Do not join when
# the right-hand side is one of these.
NOT_A_CONTINUATION = {"and", "or", "but", "nor", "the", "a", "an", "to", "of", "in", "for"}

# --- ligature loss -----------------------------------------------------------------------------
# Built-in map. Keys are the damaged forms as they actually appear after fi/fl/ff/ffi loss.
LIGATURES = {
    # fi
    "rst": "first", "rstly": "firstly", "nd": "find", "nds": "finds", "nding": "finding",
    "nally": "finally", "nal": "final", "ne": "fine", "nite": "finite", "nitude": "finitude",
    "innite": "infinite", "innitely": "infinitely", "rm": "firm", "rmly": "firmly",
    "eld": "field", "erce": "fierce", "fty": "fifty", "fth": "fifth", "ction": "fiction",
    "ctitious": "fictitious", "delity": "fidelity", "ance": "fiance", "gure": "figure",
    "gures": "figures", "lled": "filled", "lls": "fills", "ll": "fill", "lth": "filth",
    "conrm": "confirm", "conrmed": "confirmed", "conned": "confined", "condence": "confidence",
    "condent": "confident", "satised": "satisfied", "signicance": "significance",
    "signicant": "significant", "signies": "signifies", "signied": "signified",
    "justied": "justified", "identied": "identified", "specic": "specific",
    "sacrice": "sacrifice", "sacriced": "sacrificed", "veried": "verified",
    "denite": "definite", "denition": "definition", "dened": "defined", "dene": "define",
    "denitely": "definitely", "magnicent": "magnificent", "benet": "benefit",
    "benecial": "beneficial", "prot": "profit", "proted": "profited",
    "certicate": "certificate", "inrmity": "infirmity", "unication": "unification",
    "edies": "edifies", "edied": "edified", "classication": "classification",
    "qualication": "qualification", "modication": "modification",
    # fl
    "reection": "reflection", "reections": "reflections", "reective": "reflective",
    "reect": "reflect", "reects": "reflects", "reected": "reflected", "ight": "flight",
    "oor": "floor", "ow": "flow", "ows": "flows", "inuence": "influence",
    "conict": "conflict", "conicts": "conflict", "ourish": "flourish", "uid": "fluid",
    "briey": "briefly", "ame": "flame", "esh": "flesh", "eeting": "fleeting",
    "ourishing": "flourishing", "uctuation": "fluctuation", "trie": "trifle",
    "tries": "trifles", "ock": "flock", "ank": "flank",
    # ff / ffi
    "suces": "suffices", "sucient": "sufficient", "suciently": "sufficiently",
    "dicult": "difficult", "diculty": "difficulty", "diculties": "difficulties",
    "dierent": "different", "dierence": "difference", "dierences": "differences",
    "dier": "differ", "dierently": "differently", "indierence": "indifference",
    "indierent": "indifferent", "eect": "effect", "eects": "effects",
    "eective": "effective", "aect": "affect", "aects": "affects", "aection": "affection",
    "oer": "offer", "oers": "offers", "oered": "offered", "oering": "offering",
    "suer": "suffer", "suers": "suffers", "suered": "suffered", "suering": "suffering",
    "suerings": "sufferings", "eort": "effort", "eorts": "efforts", "aair": "affair",
    "aairs": "affairs", "oense": "offense", "oence": "offence", "ecacy": "efficacy",
    "ecient": "efficient", "oce": "office", "ocial": "official", "ocially": "officially",
    "aord": "afford", "aorded": "afforded", "sti": "stiff", "sta": "staff",
    "condant": "confidant", "condante": "confidante",
}

# Tokens that also occur as ordinary English words, or as OCR junk and Roman numerals. Repairing
# these blind creates new errors — "tries" is a real word and is not "trifles" — so they are
# excluded from the damage verdict and only repaired with --aggressive.
AMBIGUOUS = {"nd", "ne", "ow", "ame", "ock", "ank", "sti", "sta", "ance", "gure",
             "ll", "tries", "trie", "nal", "ction", "eld", "ne", "erce"}

F_RATE_FLOOR = 2.00     # % of letters; below this, screen the file for ligature loss
LIG_RATE_FLAG = 10.0    # unambiguous hits per 10k words; damaged corpora run 50–100×, clean <2


def f_rate(text):
    letters = re.findall(r"[a-z]", text.lower())
    if not letters:
        return None
    return 100.0 * letters.count("f") / len(letters)


def census(text, ligmap):
    low = text.lower()
    suspects = {}
    for bad in ligmap:
        n = len(re.findall(r"\b" + re.escape(bad) + r"\b", low))
        if n:
            suspects[bad] = n
    markup = sum(len(rx.findall(text)) for rx, _ in MARKUP)
    hyphens = sum(1 for a, b in SOFT_HYPHEN.findall(text) if b not in NOT_A_CONTINUATION)
    return suspects, markup, hyphens


def repair(text, ligmap, aggressive):
    for rx, rep in MARKUP:
        text = rx.sub(rep, text)
    text = SOFT_HYPHEN.sub(
        lambda m: m.group(0) if m.group(2) in NOT_A_CONTINUATION else m.group(1) + m.group(2),
        text)
    usable = {k: v for k, v in ligmap.items() if aggressive or k not in AMBIGUOUS}
    if usable:
        pattern = re.compile(
            r"\b(" + "|".join(sorted(map(re.escape, usable), key=len, reverse=True)) + r")\b"
        )
        text = pattern.sub(lambda m: usable[m.group(1)], text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def iter_files(path):
    if os.path.isfile(path):
        yield path
        return
    for root, _, names in os.walk(path):
        for n in sorted(names):
            if n.endswith((".txt", ".md")):
                yield os.path.join(root, n)


def main():
    ap = argparse.ArgumentParser(description="Extraction-damage census and repair (Stage 1).")
    ap.add_argument("path", help="text file or directory of .txt/.md files")
    ap.add_argument("--fix", action="store_true", help="write repairs (default: report only)")
    ap.add_argument("--out", help="write repaired files here instead of in place")
    ap.add_argument("--no-backup", action="store_true", help="skip .orig backups when fixing in place")
    ap.add_argument("--lexicon", help='JSON {"broken":"repaired"} merged over the built-in map')
    ap.add_argument("--aggressive", action="store_true",
                    help="also repair tokens that are real English words (see AMBIGUOUS)")
    ap.add_argument("--json", help="write the census here")
    args = ap.parse_args()

    ligmap = dict(LIGATURES)
    if args.lexicon:
        with open(args.lexicon, encoding="utf-8") as fh:
            ligmap.update(json.load(fh))

    files = list(iter_files(args.path))
    if not files:
        sys.exit(f"no .txt/.md files under {args.path}")

    report = {}
    damaged = 0
    print(f"{'file':38s}{'f%':>7s}{"lig/10k":>10s}{'markup':>8s}{'hyphen':>8s}  verdict")
    print("-" * 88)
    for p in files:
        text = open(p, encoding="utf-8", errors="replace").read()
        suspects, markup, hyphens = census(text, ligmap)
        fr = f_rate(text)
        words = max(1, len(text.split()))
        unambig = sum(v for k, v in suspects.items() if k not in AMBIGUOUS)
        lig_rate = 10000.0 * unambig / words

        flags = []
        if lig_rate >= LIG_RATE_FLAG:
            flags.append("LIGATURE")
        elif fr is not None and fr < F_RATE_FLOOR:
            flags.append("f-low(screen only)")
        if markup:
            flags.append("MARKUP")
        if 10000.0 * hyphens / words >= 20:
            flags.append("HYPHEN")
        verdict = ", ".join(flags) if flags else "clean"
        if any(f in verdict for f in ("LIGATURE", "MARKUP", "HYPHEN")):
            damaged += 1

        print(f"{os.path.basename(p)[:36]:38s}{fr if fr else 0:7.2f}{lig_rate:10.1f}"
              f"{markup:8d}{hyphens:8d}  {verdict}")
        report[p] = {"f_rate": fr, "words": words,
                     "ligature_unambiguous": unambig, "ligature_per_10k": round(lig_rate, 1),
                     "markup_hits": markup, "hyphen_splits": hyphens,
                     "top_suspects": dict(sorted(suspects.items(), key=lambda kv: -kv[1])[:12]),
                     "verdict": verdict}

        if args.fix:
            fixed = repair(text, ligmap, args.aggressive)
            if args.out:
                dest = os.path.join(args.out, os.path.relpath(p, args.path)
                                    if os.path.isdir(args.path) else os.path.basename(p))
                os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            else:
                dest = p
                if not args.no_backup:
                    with open(p + ".orig", "w", encoding="utf-8") as fh:
                        fh.write(text)
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(fixed)

    print(f"\n{len(files)} file(s), {damaged} showing damage.")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.json}")

    if not args.fix and damaged:
        print("\nReport only — nothing written. Re-run with --fix once the census looks right.")
        print("Review 'top_suspects' first: an unfamiliar corpus may need --lexicon additions,")
        print("and a low f% with zero ligature hits is a short file, not damage.")
    if args.fix:
        print("\nRepaired. Re-run style_metrics.py AFTER this — a baseline measured over damaged")
        print("text is not a baseline, and every downstream expressive-match score inherits it.")


if __name__ == "__main__":
    main()
