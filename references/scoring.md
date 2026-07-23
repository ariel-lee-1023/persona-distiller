# Stage 3 — Multi-probe curation & deletion

This is where the value is. The job is to score every candidate from `extractions.json` on five
probes, combine them into one identification score, and then **delete aggressively**. Get this
right before you polish anything else.

## The composite

```
identification = 0.30·projectibility
               + 0.25·cost_refusal
               + 0.20·expressive_match
               + 0.15·interactional
               + 0.10·preoccupation
```

Each sub-score is 0–1. The weights are defaults — tunable, but keep the ordering: the two hardest,
most diagnostic probes (projectibility, cost/refusal) together outweigh everything else. This
ordering *is* the correction against the natural bias toward easily-measured surface style. If you
ever find the core filling with tidy style facts, the weighting is doing its job and you should let
it cut them.

## Scoring each probe (0–1 rubrics)

**Projectibility (0.30)** — does it predict held-out stances?
- 1.0 — from this element alone you can correctly infer the person's position on questions they
  never explicitly addressed; confirmed in the Stage 5 projection test.
- 0.5 — recurs and generalizes somewhat, but predictions are shaky or under-tested.
- 0.0 — reproduces a specific known statement only; no reach beyond it.

**Cost / refusal (0.25)** — does it sit on an incentive-vs-characteristic divergence?
- 1.0 — a documented line the person held against their own audience/interest, with both the
  convenient move and the characteristic move attested.
- 0.5 — a standing commitment that recurs but carried little visible cost.
- 0.0 — no divergence; agrees with what anyone in their position would conveniently say.

**Expressive match (0.20)** — alignment with the *measured* style distribution, including variation.
- 1.0 — a distinctive feature or a modulation *pattern* well outside the generic baseline.
- 0.5 — present but only mildly distinctive.
- 0.0 — a bare average indistinguishable from generic prose. (Most raw metrics land here — that is
  correct, and why this probe is capped at 0.20.)

**Interactional visibility (0.15)** — observable as a move in exchange.
- 1.0 — a repeated, recognizable concede/reframe/dig-in/shift-footing pattern across dialogues.
- 0.5 — appears in exchange but inconsistently.
- 0.0 — never observable interactionally (pure monologue artifact).

**Preoccupation / gravitational weight (0.10)** — the theme they keep returning to.
- 1.0 — surfaces across several *unrelated* clusters; the person cannot stay away from it.
- 0.5 — a recurring interest within one domain.
- 0.0 — mentioned once or twice.

## The deletion rule (hard)

After scoring, cut an element if **any** of these is true:

1. Composite **< 0.55**.
2. It introduces **generic language** — phrasing that would fit a thousand people.
3. It **forces meta-commentary** — you cannot include it without the persona narrating itself,
   hedging, or citing sources.
4. It **conflicts with a higher-scoring** core voice feature — keep the stronger one; drop the
   weaker rather than averaging them into a muddle.

Do not smooth, blend, or "partially include" low-value material. A deleted element that was merely
low-scoring (not generic/meta/conflicting) can still be **demoted to references** if it is attested
and someone might want it on demand — but it does not touch the core.

## Elevation & retention (hard) — why weights alone are not enough

The weights tilt toward the diagnostic signals, but ranking purely by composite still lets *volume*
defeat them: a corpus yields dozens of moderate style features and only a handful of cost-refusals,
so a flat top-N sort can fill the core with tidy generic style while the fingerprints spill into
references. The elevation rules below prevent that. They are not optional flavor — they are the
mechanism that makes the whole design work.

**1. Class priority in ranking.** Do not sort survivors by composite alone. Sort by **class first**,
then by composite within class:

```
cost_refusal  ≈  projectible_regularity   >   interactional   >   variation/modulation
                                                            >   preoccupation   >   stable_style
```

**2. Reserved claim.** Cost-bearing refusals, standing commitments, and variation/modulation
patterns get *first claim* on core space. Fill them in before any stable style feature, then fill
remaining budget down the priority ladder.

**3. Style-metric cap.** Pure style averages (stable_style class) may occupy **at most ~20%** of the
core's elements. If you are over the cap, the surplus style features go to references regardless of
their composite — the core is a fingerprint, not a stylometry report.

**4. Sparsity protection.** A high-signal cost-refusal or variation pattern that clears the ≥2-cluster
bar is retained even if it is rarer than, and outscored on the composite by, an abundant style class.
Count never demotes a scarce diagnostic below a plentiful generic one.

**5. Minimum presence.** If the corpus contains *any* high-signal cost-refusal or interactional move,
the core must carry **at least one**. This is asserted again at the Stage 5 presence check; enforce
it here so it is true by construction, not by luck.

Fill the core to the ~5k-token budget under these rules (see `output-template.md` for the section
layout); everything else attested goes to references.

## Gate before assembly

Scoring does not flow straight into Stage 4. Before assembly, run the **projection gate** and **cost
gate** in `fidelity-tests.md`; a failing projection score means you re-curate (down-weight over-fit
elements, promote better-generalizing ones) or narrow scope and re-score, and a cost-gate miss means
you re-include or elevate the missing divergence. Record both outcomes in the persona's
`provenance.md`, and note any weight change they triggered. Only a set that clears both gates gets
assembled.

## Auto-weighting hooks

- Dialogue-rich corpus (`coverage_map.dialogue_ratio` high) → nudge the interactional weight up
  (e.g. 0.15 → 0.20) and renormalize; monologic corpus → nudge it down toward projectibility.
- Narrow user focus → raise the weight of the requested facet and drop off-focus elements even if
  they score well, since they are out of scope for this persona.
- Record any weight change and why, at the top of the audit log, so the run stays reproducible.

## Audit log (`scores.json`)

Every decision is logged with its scores and a one-line reason, so the whole curation is
inspectable and defensible.

```json
{
  "weights": {"projectibility":0.30,"cost_refusal":0.25,"expressive_match":0.20,
              "interactional":0.15,"preoccupation":0.10},
  "weight_notes": "dialogue_ratio 0.35 → interactional 0.15 (unchanged)",
  "decisions": [
    {"id":"e017","type":"cost_refusal",
     "scores":{"projectibility":0.9,"cost_refusal":1.0,"expressive_match":0.4,
               "interactional":0.8,"preoccupation":0.7},
     "composite":0.80,"decision":"core","rank":2,
     "reason":"incentive-vs-characteristic divergence attested in 3 clusters; predicts well"},
    {"id":"e041","type":"expression",
     "scores":{"projectibility":0.1,"cost_refusal":0.0,"expressive_match":0.5,
               "interactional":0.0,"preoccupation":0.0},
     "composite":0.10,"decision":"cut",
     "reason":"bare sentence-length average; generic; below threshold"}
  ]
}
```

## Two worked examples

**Kept.** A candidate `cost_refusal`: the person repeatedly argues *against* a position their own
readership favors, taking the unpopular side on principle, attested in three clusters, and from it
you can correctly predict their stance on a fresh case. Scores: projectibility 0.9, cost 1.0,
expressive 0.4, interactional 0.8, preoccupation 0.7 → composite **0.80** → **core**, high rank.
This is the kind of element that earns identification.

**Cut.** A candidate `expression`: "uses moderately long sentences, average 22 words." Scores:
projectibility 0.1, cost 0.0, expressive 0.5, interactional 0.0, preoccupation 0.0 → composite
**0.10** → **cut**. Generic and below threshold; a persona built on this reads like anyone. If a
*modulation* version existed ("sentences collapse to clipped fragments the moment a claim is
contested"), that would score far higher on expressive match and interactional and might reach the
core — the pattern individuates where the average does not.
