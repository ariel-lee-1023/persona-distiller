# Stage 2 — Multi-granularity extraction

Three passes, run over the segmented clusters. The output is `extractions.json`: a flat list of
candidate elements, each with evidence, ready for Stage 3 scoring. The central discipline of this
stage is to **spend effort in proportion to diagnostic value, not ease of measurement** — the easy
pass (fine-grained) is necessary but cheap; the two hard passes are where identification is won.

---

## Pass A — Fine-grained expression (every cluster)

Countable style features **and their modulation**. Run `scripts/style_metrics.py` on the whole
corpus and per cluster so you have real numbers, then read the *shifts*, not just the averages.
For a Chinese corpus run `scripts/zh_metrics.py` instead — same feature classes, measured in 汉字,
with Chinese hedge/booster sets; the Latin-tokenising script reports zeros and will quietly cost
you the entire expression pass. Track the subject's own vocabulary with its `--terms` flag.

Measure:
- **Sentence-length distribution** — mean, median, spread, and the shape (does the person mix long
  periodic sentences with abrupt short ones? that mix is more individuating than any average).
- **Hedging vs. boosting** — rates of "perhaps/it seems/arguably" vs "obviously/clearly/in fact".
- **Punctuation rhythm** — em-dashes, semicolons, colons, parentheticals, rhetorical questions.
- **Lexical fingerprint** — high-frequency content words and bigrams; and, harder, **conspicuously
  absent** common words the person avoids (compute by comparing their content-word set against a
  generic baseline — an avoided word can be as diagnostic as a favored one).
- **Person reference** — first / second / third-person ratios; do they address the reader?
- **Analogy / metaphor density** and their source domains (nautical? legal? biological?).
- **Rhythm markers** — anaphora, tricolon, sentence-initial conjunctions, one-line paragraphs.

**Modulation is the point.** For each feature, note how it moves across `kind` (dialogue vs
monologue), audience (expert vs lay), and stakes (calm exposition vs contested point). Record e.g.
"sentence length halves and boosters spike when challenged" — that *pattern of variation* is a
high-value element, whereas the bare average is low-value and probably generic.

Emit each stable feature and each modulation pattern as separate candidate elements.

Run this pass on **firsthand clusters only**. Secondhand paraphrase carries the paraphraser's
sentence rhythm, not the subject's, and averaging the two produces a voice belonging to neither.

> Caution: it is tempting to fill the persona with this pass because it is easy and produces tidy
> numbers. Resist. Most raw style metrics score low on identification once you account for how
> generic they are. Keep the *distinctive mix* and the *modulation*; discard the rest.

What survives this pass has two destinations, and the split happens in Stage 3: the few most
identifying features go to the core's "How I sound" (capped at ~20% of it), and everything else
that survived the deletion rule goes to **`references/voice.md`** — the standing expressive-system
module. So extract the full picture here rather than pre-trimming to what a core could hold; in
particular, the **conspicuously absent** words and the per-register numbers have a home now, and
they are among the most useful things this pass produces.

---

## Pass B — Coarse-grained projectible regularities (across clusters)

These are the person's recurring **thought-moves** and **decision heuristics** — the cognitive
operating system. A candidate is only recorded if it passes all three gates (adapted from the
triple-verification standard):

1. **Cross-cluster recurrence** — appears in **≥2 independent clusters**, not a one-off line.
2. **Predictive power** — from the remaining evidence you can infer the person's stance on a
   question they did *not* explicitly address in the masked passage. If it can only reproduce known
   statements, it is a quote, not a regularity.
3. **Exclusivity** — not something any thoughtful person would say. If it is generic wisdom, it does
   not individuate and does not belong. ("Think before you act" fails; a specific characteristic
   inversion they habitually perform passes.)

Write each as an operative rule in the person's own logic — "When facing X, reframes it as Y
before evaluating", "Treats institutional claims as suspect until Z" — with the clusters it appears
in and 1–2 example passages. State it as a *move the persona makes*, not as a description of the
person ("does X when Y", never "the author tends to").

Adversarial / critical sources, if present in the corpus, are especially useful here: the places
where critics push back reveal where the person's real decision boundaries are. Distilling only
flattering material yields hagiography, not a decision architecture.

---

## Pass C — Interactional & cost-bearing (prioritize dialogue + decision records)

This pass extracts the single highest-value class of signal. Two overlapping catalogues:

### Cost-bearing refusals & standing commitments
Hunt for every place where the person's **characteristic** response **diverges from the convenient
or generic** one — where they paid, or risked, something to hold a line:
- positions maintained against their own audience, tribe, or interest;
- questions they refuse to answer, or reframe rather than accept;
- concessions they will not make even under pressure;
- lines that recur as non-negotiable across clusters.

For each, record **both** sides explicitly: the convenient/expected move *and* the attested
characteristic move. That divergence pair is what the Stage 5 cost test checks, and it is the
fingerprint most responsible for expert-level identification. Flag these prominently.

### Interactional moves
In any exchange (interview, debate, Q&A, correspondence), catalogue *how* the person handles a
turn — the repeated shape of their engagement:
- **concede** — what they give ground on, and how gracefully;
- **reframe** — how they redraw the question before answering;
- **dig in** — where and how they refuse to move;
- **shift footing** — changing register, stance, or level (e.g. from particular to principle) mid-exchange.

Record the *pattern* ("when asked for a concrete prediction, shifts to the principle at stake
rather than naming a number"), the clusters, and an example. These moves are invisible in
monologic summary but decisive for embodiment, which is why dialogue-rich corpora get up-weighted.

---

## Output of Stage 2

`extractions.json` — a flat list; each element:

```json
{
  "id": "e017",
  "type": "cost_refusal",          // expression | modulation | regularity | cost_refusal | interactional | preoccupation
  "statement": "Holds that <line> even when <audience> expects the opposite.",
  "convenient_move": "…",           // for cost_refusal / interactional only
  "clusters": ["c03", "c09", "c11"],
  "evidence": ["short passage 1", "short passage 2"],
  "metrics": {}                     // for expression/modulation, from style_metrics.py
}
```

Keep evidence passages short and treat them as *evidence*, not as text to paste into the core —
the core is written in the persona's voice from these regularities, not stitched from quotations.
Hand the full list to Stage 3.
