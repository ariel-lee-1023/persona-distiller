#!/usr/bin/env python3
"""
style_metrics.py — countable expression features for the Persona Distiller.

Feeds the "expressive match" probe (Stage 3) and the style-match fidelity test (Stage 5).
Standard library only; no installation required.

Usage:
    python3 style_metrics.py <file-or-directory> [--json out.json] [--per-file]

Notes:
- These numbers are inputs to judgment, not the judgment itself. Most raw averages are generic;
  the distiller cares more about the *distinctive mix* and the *modulation* across files than
  about any single average. Run --per-file to see how features move across clusters/registers.
- Sentence and word tokenization are deliberately simple and dependency-free. Treat the outputs
  as robust-enough signal, not linguistic ground truth.
"""

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter

HEDGES = {
    "perhaps", "maybe", "possibly", "arguably", "seemingly", "apparently", "roughly",
    "somewhat", "fairly", "rather", "quite", "presumably", "supposedly", "probably",
    "likely", "seems", "seem", "seemed", "suggests", "suggest", "tends", "tend",
    "might", "could", "may", "conceivably", "ostensibly", "sort", "kind",  # "sort of"/"kind of"
}
BOOSTERS = {
    "obviously", "clearly", "certainly", "undoubtedly", "definitely", "surely",
    "plainly", "evidently", "indeed", "absolutely", "always", "never", "must",
    "unquestionably", "manifestly", "of course", "in fact", "without doubt",
}
STOPWORDS = set("""
the a an and or but if then else when while of to in on at by for with without from into onto
is are was were be been being am do does did doing have has had having i you he she it we they
me him her us them my your his its our their this that these those as so than too very just also
not no nor which who whom whose what where why how all any both each few more most other some such
only own same can will would should could may might must here there over under again further once
about against between through during before after above below up down out off because until about
""".split())

# very common content words; conspicuous absence relative to size can itself be diagnostic
COMMON_CONTENT = [
    "people", "time", "way", "world", "life", "work", "thing", "part", "point", "fact",
    "problem", "question", "reason", "idea", "system", "power", "order", "sense", "state",
    "good", "great", "important", "different", "possible", "human", "social", "political",
]

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
# sentence split on ., !, ? followed by space+capital / EOL, with light abbreviation guard
ABBREV = {"mr", "mrs", "ms", "dr", "prof", "vs", "etc", "e.g", "i.e", "st", "no", "fig"}


def read_text(path):
    texts = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in sorted(files):
                if f.lower().endswith((".txt", ".md", ".markdown")):
                    fp = os.path.join(root, f)
                    with open(fp, encoding="utf-8", errors="replace") as fh:
                        texts.append((fp, fh.read()))
    else:
        with open(path, encoding="utf-8", errors="replace") as fh:
            texts.append((path, fh.read()))
    return texts


def split_sentences(text):
    # collapse whitespace, then split on terminal punctuation heuristically
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'(A-Z0-9])", text.strip())
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # merge obvious abbreviation over-splits
        tail = p.rsplit(" ", 1)[-1].lower().strip(".")
        if out and tail in ABBREV:
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return out


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def analyze(text):
    words = [w.lower() for w in WORD_RE.findall(text)]
    n_words = len(words)
    sents = split_sentences(text)
    slens = [len(WORD_RE.findall(s)) for s in sents if WORD_RE.findall(s)]
    paras = paragraphs(text)
    plens = [len(WORD_RE.findall(p)) for p in paras if WORD_RE.findall(p)]

    def per_1k(count):
        return round(1000.0 * count / n_words, 2) if n_words else 0.0

    def dist(xs):
        if not xs:
            return {}
        xs_sorted = sorted(xs)
        return {
            "n": len(xs),
            "mean": round(statistics.mean(xs), 2),
            "median": statistics.median(xs),
            "stdev": round(statistics.pstdev(xs), 2),
            "p10": xs_sorted[max(0, int(0.10 * len(xs)) - 1)],
            "p90": xs_sorted[min(len(xs) - 1, int(0.90 * len(xs)))],
            "min": xs_sorted[0],
            "max": xs_sorted[-1],
        }

    wc = Counter(words)
    content = [w for w in words if w not in STOPWORDS and len(w) > 2]
    content_counts = Counter(content)
    bigrams = Counter(zip(content, content[1:]))

    # moving-average type-token ratio (window 500) — less length-sensitive than raw TTR
    win = 500
    if n_words >= win:
        ratios = []
        for i in range(0, n_words - win + 1, win):
            chunk = words[i:i + win]
            ratios.append(len(set(chunk)) / win)
        mattr = round(statistics.mean(ratios), 3)
    else:
        mattr = round(len(set(words)) / n_words, 3) if n_words else 0.0

    hedge_ct = sum(wc[h] for h in HEDGES)
    boost_ct = sum(wc[b] for b in BOOSTERS)

    first = sum(wc[p] for p in ("i", "me", "my", "we", "us", "our"))
    second = sum(wc[p] for p in ("you", "your", "yours"))
    third = sum(wc[p] for p in ("he", "she", "they", "him", "her", "them", "his", "their"))
    pr_total = first + second + third or 1

    avoided = [w for w in COMMON_CONTENT if per_1k(wc[w]) < 0.2]

    return {
        "counts": {"words": n_words, "sentences": len(slens), "paragraphs": len(plens)},
        "sentence_length": dist(slens),
        "paragraph_length": dist(plens),
        "lexical_diversity_mattr500": mattr,
        "hedges_per_1k": per_1k(hedge_ct),
        "boosters_per_1k": per_1k(boost_ct),
        "hedge_booster_ratio": round(hedge_ct / boost_ct, 2) if boost_ct else None,
        "punctuation_per_1k": {
            "em_dash": per_1k(text.count("—") + text.count("--")),
            "semicolon": per_1k(text.count(";")),
            "colon": per_1k(text.count(":")),
            "question": per_1k(text.count("?")),
            "exclamation": per_1k(text.count("!")),
            "parenthetical": per_1k(text.count("(")),
        },
        "person_reference_pct": {
            "first": round(100 * first / pr_total, 1),
            "second": round(100 * second / pr_total, 1),
            "third": round(100 * third / pr_total, 1),
        },
        "top_content_words": content_counts.most_common(25),
        "top_bigrams": [(" ".join(b), c) for b, c in bigrams.most_common(15)],
        "conspicuously_absent_common_words": avoided,
    }


def main():
    ap = argparse.ArgumentParser(description="Countable expression features for persona distillation.")
    ap.add_argument("path", help="text file or directory of .txt/.md files")
    ap.add_argument("--json", help="write full JSON here")
    ap.add_argument("--per-file", action="store_true", help="also emit per-file metrics (see modulation)")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        sys.exit(f"path not found: {args.path}")

    texts = read_text(args.path)
    if not texts:
        sys.exit("no .txt/.md text found at that path")

    combined = "\n\n".join(t for _, t in texts)
    result = {"aggregate": analyze(combined)}
    if args.per_file and len(texts) > 1:
        result["per_file"] = {os.path.basename(p): analyze(t) for p, t in texts}

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.json}")

    agg = result["aggregate"]
    print("\n=== aggregate style metrics ===")
    print(f"words: {agg['counts']['words']}  sentences: {agg['counts']['sentences']}")
    sl = agg["sentence_length"]
    if sl:
        print(f"sentence length: mean {sl['mean']} / median {sl['median']} / stdev {sl['stdev']} "
              f"(p10 {sl['p10']}, p90 {sl['p90']})")
    print(f"lexical diversity (MATTR-500): {agg['lexical_diversity_mattr500']}")
    print(f"hedges/1k: {agg['hedges_per_1k']}   boosters/1k: {agg['boosters_per_1k']}   "
          f"hedge:booster {agg['hedge_booster_ratio']}")
    print(f"person ref %: {agg['person_reference_pct']}")
    print(f"top content: {', '.join(w for w, _ in agg['top_content_words'][:10])}")
    if agg["conspicuously_absent_common_words"]:
        print(f"conspicuously absent common words: {', '.join(agg['conspicuously_absent_common_words'])}")
    print("\nReminder: averages are mostly generic — read the per-file *shifts* (modulation) and the")
    print("distinctive mix, not the means, when scoring expressive match.")


if __name__ == "__main__":
    main()
