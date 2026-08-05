#!/usr/bin/env python3
"""
zh_metrics.py — countable expression features for Chinese-language corpora.

The companion `style_metrics.py` tokenises on `[A-Za-z]` and counts English hedges and boosters,
so on a CJK corpus it returns zeros for every feature that matters. This computes the same
*classes* of feature over Chinese text, in the units Chinese prose is actually measured in:
sentence length in 汉字, hedge/booster rates, punctuation rhythm, person-reference ratios,
proper-name density, and a character-n-gram lexical fingerprint.

Feeds the same two places `style_metrics.py` does — the expressive-match probe (Stage 3) and the
style-match fidelity test (Stage 5) — and supplies the measured baseline written into
`references/voice.md`.

Standard library only; no installation required.

Usage:
    python3 zh_metrics.py <file-or-directory> [--json out.json] [--per-file] [--top N]
                          [--terms 秩序,封建,费拉]        # or --terms terms.txt (one per line)

Notes:
- Averages are mostly generic. What individuates a Chinese writer is the **modulation across
  registers** — spoken lecture vs. written essay vs. classical-Chinese note. Run --per-file, or run
  the tool once per register group, and read the *gaps*, not the means.
- `--terms` is how you track a person's own vocabulary. The tool ships with no term list on
  purpose: a distiller's script must not carry one subject's jargon.
- Segmentation is deliberately dependency-free: sentences split on 。！？…, and the lexical
  fingerprint uses character n-grams rather than a word segmenter. Robust-enough signal, not
  linguistic ground truth.
"""

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter

HAN = re.compile(r"[一-鿿]")
SENT_END = re.compile(r"[。！？!?…]+")
CLAUSE_END = re.compile(r"[。！？!?…；;]+")

# hedges and boosters, simplified + traditional
HEDGES = ["也许", "也許", "或许", "或許", "可能", "大概", "似乎", "恐怕", "我觉得", "我覺得",
          "我认为", "我認為", "个人认为", "個人認為", "在我看来", "在我看來", "差不多",
          "基本上", "多半", "大体", "大體", "一般来说", "一般來說", "某种程度", "某種程度"]
BOOSTERS = ["一定", "必然", "肯定", "绝对", "絕對", "根本", "完全", "毫无疑问", "毫無疑問",
            "当然", "當然", "显然", "顯然", "无非", "無非", "从来", "從來", "永远", "永遠",
            "只能", "必定"]

# discourse scaffolding that a distinctive writer may conspicuously avoid; its ABSENCE is the
# signal, so this list is checked, never assumed (feeds voice.md's "What I never write")
SCAFFOLDING = ["首先", "其次", "综上所述", "綜上所述", "总而言之", "總而言之", "总的来说",
               "總的來說", "值得注意的是", "众所周知", "眾所周知", "不可否认", "不可否認",
               "笔者", "筆者", "本文", "客观地说", "客觀地說", "坦率地说", "坦率地說",
               "从某种意义上说", "從某種意義上說", "需要指出的是", "换句话说", "換句話說",
               "也就是说", "也就是說", "实际上", "實際上", "事实上", "事實上"]

FIRST = ["我们", "我們", "我", "咱们", "咱們"]
SECOND = ["你们", "你們", "你", "您"]
THIRD = ["他们", "他們", "她们", "她們", "它们", "它們", "他", "她", "它"]

# characters too common to carry fingerprint information; n-grams containing one are dropped
STOP_CHARS = set(
    "的了是在和就都而及与與著或一个個这這那有也不没沒被把对對于於上下中你我他们們之其所以为"
    "為要会會能很只从從到但如果因所什么麼样樣时時候可就是还還并並且然后後最更又再"
)


def read_texts(path):
    out = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for f in sorted(files):
                if f.lower().endswith((".md", ".markdown", ".txt")):
                    fp = os.path.join(root, f)
                    with open(fp, encoding="utf-8", errors="replace") as fh:
                        out.append((fp, fh.read()))
    else:
        with open(path, encoding="utf-8", errors="replace") as fh:
            out.append((path, fh.read()))
    return out


def strip_markup(t):
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)   # frontmatter
    t = re.sub(r"```.*?```", "", t, flags=re.S)          # code fences
    t = re.sub(r"^\s*#{1,6}\s.*$", "", t, flags=re.M)    # headings
    t = re.sub(r"^\s*>\s?", "", t, flags=re.M)           # blockquote marks
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)       # bullets
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)       # links
    t = t.replace("|", " ")                              # table pipes
    return t


def dist(xs):
    if not xs:
        return {}
    s = sorted(xs)
    return {
        "n": len(xs),
        "mean": round(statistics.mean(xs), 1),
        "median": statistics.median(xs),
        "stdev": round(statistics.pstdev(xs), 1),
        "p10": s[max(0, int(0.10 * len(s)) - 1)],
        "p90": s[min(len(s) - 1, int(0.90 * len(s)))],
        "max": s[-1],
    }


def ngrams(text, n, top):
    seq = HAN.findall(text)
    c = Counter()
    for i in range(len(seq) - n + 1):
        g = "".join(seq[i:i + n])
        if any(ch in STOP_CHARS for ch in g):
            continue
        c[g] += 1
    return c.most_common(top)


def analyze(raw, top=25, terms=None):
    t = strip_markup(raw)
    n_han = len(HAN.findall(t))
    if n_han == 0:
        return None
    per_10k = lambda k: round(10000.0 * k / n_han, 2)

    sents = [s for s in SENT_END.split(t) if HAN.search(s)]
    slens = [x for x in (len(HAN.findall(s)) for s in sents) if x > 0]
    clauses = [len(HAN.findall(c)) for c in CLAUSE_END.split(t) if HAN.search(c)]

    hedge = sum(t.count(w) for w in HEDGES)
    boost = sum(t.count(w) for w in BOOSTERS)
    first = sum(t.count(w) for w in FIRST)
    second = sum(t.count(w) for w in SECOND)
    third = sum(t.count(w) for w in THIRD)
    pr_total = first + second + third or 1

    out = {
        "han_chars": n_han,
        "sentence_length_han": dist(slens),
        "pct_sentences_over_40han": round(100.0 * sum(1 for x in slens if x > 40) / len(slens), 1) if slens else 0.0,
        "pct_sentences_under_12han": round(100.0 * sum(1 for x in slens if x < 12) / len(slens), 1) if slens else 0.0,
        "clause_length_han": dist(clauses),
        "hedges_per_10k": per_10k(hedge),
        "boosters_per_10k": per_10k(boost),
        "hedge_booster_ratio": round(hedge / boost, 2) if boost else None,
        "punctuation_per_10k": {
            "question": per_10k(t.count("？") + t.count("?")),
            "exclamation": per_10k(t.count("！") + t.count("!")),
            "dash": per_10k(t.count("——")),
            "semicolon": per_10k(t.count("；") + t.count(";")),
            "parenthetical": per_10k(t.count("（") + t.count("(")),
            "quote": per_10k(t.count("“") + t.count("「")),
            "book_title": per_10k(t.count("《")),
            "interpunct": per_10k(t.count("·")),   # marks transliterated foreign proper names
        },
        "person_reference_pct": {
            "first": round(100 * first / pr_total, 1),
            "second": round(100 * second / pr_total, 1),
            "third": round(100 * third / pr_total, 1),
        },
        "scaffolding_per_10k": {w: per_10k(t.count(w)) for w in SCAFFOLDING},
        "conspicuously_absent_scaffolding": [w for w in SCAFFOLDING if per_10k(t.count(w)) < 0.05],
        "top_2gram": ngrams(t, 2, top),
        "top_3gram": ngrams(t, 3, top),
        "top_4gram": ngrams(t, 4, min(top, 15)),
    }
    if terms:
        out["tracked_terms_per_10k"] = {w: per_10k(t.count(w)) for w in terms}
        out["tracked_terms_total_per_10k"] = per_10k(sum(t.count(w) for w in terms))
    return out


def load_terms(arg):
    if not arg:
        return None
    if os.path.exists(arg):
        with open(arg, encoding="utf-8") as fh:
            return [ln.strip() for ln in fh if ln.strip()]
    return [w.strip() for w in arg.split(",") if w.strip()]


def main():
    ap = argparse.ArgumentParser(description="Countable expression features for Chinese corpora.")
    ap.add_argument("path", help="text file or directory of .md/.txt files")
    ap.add_argument("--json", help="write full JSON here")
    ap.add_argument("--per-file", action="store_true", help="also emit per-file metrics (see modulation)")
    ap.add_argument("--top", type=int, default=25, help="how many n-grams to report")
    ap.add_argument("--terms", help="comma-separated terms, or a file with one per line, to track")
    a = ap.parse_args()

    if not os.path.exists(a.path):
        sys.exit(f"path not found: {a.path}")
    texts = read_texts(a.path)
    if not texts:
        sys.exit("no .md/.txt text found at that path")

    terms = load_terms(a.terms)
    combined = "\n\n".join(x for _, x in texts)
    agg = analyze(combined, a.top, terms)
    if agg is None:
        sys.exit("no CJK characters found — this is the Chinese tool; use style_metrics.py instead")
    result = {"aggregate": agg}
    if a.per_file and len(texts) > 1:
        per = {os.path.basename(p): analyze(x, a.top, terms) for p, x in texts}
        result["per_file"] = {k: v for k, v in per.items() if v}

    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1, ensure_ascii=False)
        print(f"wrote {a.json}")

    sl = agg["sentence_length_han"]
    p = agg["punctuation_per_10k"]
    print("\n=== aggregate zh style metrics ===")
    print(f"汉字 {agg['han_chars']}   sentences {sl.get('n')}")
    print(f"sentence length (汉字): mean {sl.get('mean')} / median {sl.get('median')} "
          f"(p10 {sl.get('p10')}, p90 {sl.get('p90')})   >40字 {agg['pct_sentences_over_40han']}%   "
          f"<12字 {agg['pct_sentences_under_12han']}%")
    print(f"hedges/10k {agg['hedges_per_10k']}   boosters/10k {agg['boosters_per_10k']}   "
          f"hedge:booster {agg['hedge_booster_ratio']}")
    print(f"question/10k {p['question']}   dash/10k {p['dash']}   《》/10k {p['book_title']}   "
          f"·/10k {p['interpunct']}")
    print(f"person ref %: {agg['person_reference_pct']}")
    if terms:
        print(f"tracked terms/10k (total {agg['tracked_terms_total_per_10k']}): "
              f"{agg['tracked_terms_per_10k']}")
    print(f"top 3-grams: {', '.join(w for w, _ in agg['top_3gram'][:12])}")
    absent = agg["conspicuously_absent_scaffolding"]
    if absent:
        print(f"conspicuously absent scaffolding: {', '.join(absent)}")
    print("\nReminder: the means are mostly generic. Run --per-file, or once per register group,")
    print("and read the *gaps* — spoken vs. written vs. classical is where the person shows up.")


if __name__ == "__main__":
    main()
