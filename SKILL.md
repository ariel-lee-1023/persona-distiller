---
name: persona-distiller
description: >-
  Distills one person's uploaded public record (books, essays, transcripts, interviews,
  decision records) into a compact, embodiment-ready persona skill — a core SKILL.md tuned
  for maximum identification plus a modular references package. Extracts the hard, diagnostic
  signals (cost-bearing refusals, patterns of variation, interactional moves) rather than
  just countable surface style, curates ruthlessly by a multi-probe identification score,
  deletes anything generic or voice-diluting, and verifies fidelity with held-out projection,
  cost, and style-match tests. Use this whenever someone uploads a corpus of one person's
  material and wants to "distill", "channel", "think like", "write as", "build a persona/
  perspective/voice skill of", or "make a system prompt that embodies" that person — even if
  they don't say the word "skill". Also use to turn a thinker's collected work into a reusable
  perspective a host agent can load. Works only from the uploaded corpus; never invents material.
---

# Persona Distiller

Turn a corpus of one person's public material into a persona another agent can *embody* —
not a biography, not a summary, not a quote database. The output is a lean core `SKILL.md`
optimized so that a reader familiar with the person's record cannot easily tell its output
apart from the real thing on public topics the corpus covers.

## Governing idea: recognition is a family resemblance

You are not building a clean taxonomy of the person. Recognition in text is a
family-resemblance practice: the *same* identity shows up redundantly, at different grains,
through overlapping probes — a sentence rhythm here, a refusal there, a recurring move when
cornered, a theme they keep circling back to. No single probe is definitive; the overlap is
the signal. So do **not** try to partition the person into mutually-exclusive buckets, and do
**not** dedupe away a trait just because it surfaces in three different probes. Redundant
corroboration across probes is *strength*, and it is exactly what you keep.

Two consequences shape everything below:

1. **Fight the pull toward easily-measured style.** Sentence length, hedge-word frequency,
   and favorite punctuation are trivial to count — and almost everyone's are somewhat generic.
   The signals that actually individuate a person are *harder* to extract and *higher* value:
   **cost-bearing refusals** (positions they held against their own incentive), **patterns of
   variation** (how their register shifts under pressure, audience, or stakes), and
   **interactional moves** (how they concede, reframe, dig in, or shift footing in exchange).
   The scoring weights below deliberately elevate these. When in doubt, spend your budget on the
   hard signals, not the easy ones.

2. **Delete without mercy.** The core is an embodiment artifact, and every low-value line
   dilutes voice and adds distance. Anything that scores below threshold, reads as generic,
   forces meta-commentary, or conflicts with a higher-scoring voice feature gets **cut** — not
   softened, not averaged in. A tight 4k-token core that nails the fingerprints beats a
   comprehensive 15k-token one that reads like everyone.

## The hard rule about the OUTPUT (read this twice)

The generated persona `SKILL.md` contains **no honesty language, no uncertainty disclaimers,
no provenance hedging, and no meta framing** — no "based on available sources", no "the person
seems to", no "as an AI embodying". Those move the reader out of the voice and destroy
identification. This is a deliberate departure from provenance-forward distillers.

Honesty does not disappear — it **relocates**. Coverage gaps, source citations, confidence, and
limitations live in the *references package* and in the *coverage report you hand the user*,
never inside the embodiment artifact. You keep full auditability; the persona keeps its voice.
(This split is the whole trick — do not collapse it.)

---

## Inputs

**Required:** the person's public record, as any of four source types — **local files or a
directory**; a **git repository URL**; a **plain file URL**; or a **docs site, wiki, or published
note collection**. Formats: PDF, EPUB, DOCX, TXT, Markdown, HTML, or transcripts; mixed is fine.
Where the corpus lives depends on the host (see **Host environment** below); if the location is not
given, ask for it rather than guessing. Anything remote is fetched and classified before Stage 1 —
procedure in `references/acquisition.md`, and skipping it is how you end up distilling a
repository's scaffolding, or someone's notes *about* the person, instead of the person.

**Optional:** a focus statement, e.g. "decision style in public controversies" or "overall
voice for analysis tasks". If omitted, default to overall identification.

Output quality is strictly bounded by corpus coverage, diversity, and signal density. If the
corpus is thin, you produce a smaller, honestly-scoped core — you never fabricate probes to
fill it out.

---

## Host environment

This skill makes no assumption about which agent runs it or what the filesystem looks like. Three
locations are host-dependent; resolve each **once, at the start of the run**, and reuse the
resolved paths throughout.

| What | How to resolve |
|---|---|
| **Corpus in** | Whatever the user points you at — and it may be **remote**, not a local path. Some hosts stage uploads in a fixed directory (on claude.ai, `/mnt/user-data/uploads/`); others expect a path or a working-tree location. If unstated, ask. Network access and `git` are host capabilities: **check them, never assume them**, and if either is missing say so and ask for the material locally (`references/acquisition.md`). |
| **Work dir** | Create one. Default to `persona_work/` under the current working directory. Prefer a host-provided scratch or temp location when one exists. Create it before Stage 1 — nothing later works without it. |
| **Persona out** | Wherever the host delivers artifacts to the user (on claude.ai, `/mnt/user-data/outputs/`); otherwise the current working directory, unless the user says otherwise. |

Two further portability rules:

- **Tools are optional, never assumed.** Where a stage suggests a document-reading tool, a
  converter, or a companion skill, treat it as a preference. If the host does not have it, fall
  back to the stdlib route named alongside it. Both scripts in `scripts/` are standard-library-only
  and run under any Python 3.
- **If the work dir lands inside a git repository**, ensure it is ignored before writing to it.
  It fills with extracted full text of the source corpus, which must not be committed. This
  repository's own `.gitignore` covers the default name.

---

## Pipeline (five stages, run in order)

Each stage has a detailed reference file. Read the reference before executing that stage the
first time; the summaries below are orientation, not the full procedure.

**Acquisition precedes Stage 1.** If the corpus is remote, fetch it, separate the person's material
from the container's scaffolding with the user's confirmation, and label every unit `firsthand` /
`secondhand` / `mixed` / `unknown` before ingesting anything → `references/acquisition.md`.

### Stage 1 — Ingest & segment
Read the corpus. Extract text with structure preserved (headings, speaker turns, timestamps).
Segment into coherent **clusters** — per work/chapter, per interview, per decision record, per
time period. Build an internal **coverage map**: domains covered, dialogue-vs-monologue ratio,
decision density, temporal spread. This map drives later auto-weighting and the honest coverage
report. → See `references/pipeline.md` (Stage 1) for extraction routing by file type, and
`references/schemas/` for the validatable shape of every intermediate JSON artifact.

### Stage 2 — Multi-granularity extraction
Run three passes over the segmented corpus:
- **Fine-grained expression pass** — countable features *and their modulation* across registers.
  Run `scripts/style_metrics.py` on the corpus (and per-cluster) so these are measured, not
  guessed. Capture how features shift, not just their averages.
- **Coarse-grained projectible-regularity pass** — recurring thought-moves and decision
  heuristics. A regularity qualifies only if it (a) appears in ≥2 independent clusters and
  (b) predicts stance on held-out questions from the same corpus. Store with source clusters and
  example passages.
- **Interactional & cost-bearing pass** (prioritize dialogue and decision records) — standing
  commitments, refusals, and moves (concede / reframe / dig in / shift footing). Flag every case
  where the *convenient or generic* response diverges from the person's *attested characteristic*
  response. These flags are gold.
→ Full taxonomy and what-to-look-for: `references/extraction.md`.

### Stage 3 — Multi-probe curation & deletion *(the main differentiator — do this carefully)*
Score every extracted element 0–1 on a weighted composite:

| Probe | Weight | What it measures |
|---|---|---|
| Projectibility | **0.30** | held-out prediction performance within the corpus |
| Cost / refusal signal | **0.25** | sits on a documented divergence between incentive and characteristic move |
| Expressive match | 0.20 | alignment with the person's *measured* style distribution, including variation |
| Interactional visibility | 0.15 | observable in dialogue or exchange |
| Preoccupation / gravitational weight | 0.10 | the theme they keep returning to across unrelated clusters |

**Deletion rule (hard):** cut any element scoring below **0.55** composite, *and* cut any element
— regardless of score — that introduces generic language, forces meta-commentary, or conflicts
with a higher-scoring core voice feature. No smoothing, no averaging across low-value material.
Log every keep/cut with its probe scores and a one-line reason so the decision is auditable.

**Elevation rule (hard):** the weights alone are not enough — style metrics are abundant and
cost-refusals are sparse, so raw ranking lets volume crowd the fingerprints out. So rank survivors
by **class priority first** (cost-refusal ≈ projectible regularity > interactional > variation >
preoccupation > stable style), then by composite *within* class. Cost-bearing refusals, standing
commitments, and variation/modulation patterns get first claim on core space and are retained even
when sparser than style metrics; pure style averages may fill **at most ~20%** of the core.
Everything else attested goes to references.

**Core budget (computed, not fixed):** size the core to the diagnostic material that survived,
bounded by what the corpus supports — `supply = 2,200 + 250·min(n_cost_refusal,6) +
180·min(n_projectible,7) + 140·min(n_interactional,5) + 120·min(n_variation,4)`, clamped between a
**3,000 floor** and a `coverage_map`-derived ceiling (**4,000** thin or `firsthand_ratio` < 0.50 /
**5,500** mid / **6,500** large and multi-period). Preoccupation and style contribute nothing to
supply. Landing under the floor means the pool is too thin, not that the core needs filler: revisit
the 0.45–0.55 cut band for diagnostic classes only, then ship reduced-scope and say so. → The
formula, the floor procedure, worked scoring examples, weight-tuning, and the log format:
`references/scoring.md`.

### Gate before Stage 4 — mandatory, and it feeds back *(do not skip)*
Assembly is downstream of passing two gates. Their results are logged to the persona's
`provenance.md` and are **used to adjust inclusion and weighting** — they are control signals, not
just reports:
- **Projection gate** — run the held-out projection test (procedure in `fidelity-tests.md`) on the
  top-ranked projectible regularities *now, before assembly*. If it misses threshold, re-curate:
  down-weight the over-fit elements, promote better-generalizing ones, or narrow the persona's
  claimed scope — then re-score. Loop until it passes or you commit to a documented reduced scope.
- **Cost gate** — inventory every attested incentive-vs-characteristic divergence from Stage 2 and
  confirm the high-signal ones survived curation and are slated for the core. Any missing one is
  re-included or elevated *before* assembly, not after.

This loop is what stops a style-heavy, low-projectibility set from reaching the (structurally
correct) template and inheriting its bias. → `references/fidelity-tests.md`.

### Stage 4 — Assemble core + package references
Write the core `SKILL.md` (embodiment artifact) and the `references/` package (depth + episodic
content + provenance). The core follows a fixed template and obeys the no-meta rule absolutely.
Episodic content and lower-scoring-but-attested passages live in references, never the core.

Two reference modules are **standing and co-equal**: `frameworks.md` (what the person thinks with)
and `voice.md` (how the person sounds). The 20% style cap keeps the core a fingerprint, but a
fingerprint is not enough to *write* as someone at length, so the rest of the expressive system —
favored and **avoided** constructions, modulation rules, register range, lexical fingerprint, the
measured `style_metrics.py` baseline, and anti-drift pairs — is written to `voice.md` from firsthand
clusters only, and the core's loading block tells the host to load it before any sustained prose.
The cap routes surplus style there; it does not discard it. Material cut under the 0.55 rule stays
cut — `voice.md` takes the demoted, never the deleted.
→ Exact templates, the `voice.md` spec, and directory layout: `references/output-template.md`.

### Stage 5 — Final fidelity verification *(the gates already ran at 3.5; this confirms the assembled core)*
- **Projection re-check** — confirm the assembled persona's reasoning still predicts the masked
  held-out passages (`scripts/holdout_split.py` gives the reproducible seeded split); record the
  score in `provenance.md`.
- **Cost / presence assertion** — re-confirm every high-signal divergence landed in the core, and
  assert the hard minimum: **if the corpus contains any high-signal cost-bearing refusal or
  interactional move, the core must contain at least one.** Failing this blocks delivery — go
  re-curate; it is the most common way a core ends up articulate but generic.
- **Style-match test** — generate sample passages under the core's expression rules **plus
  `voice.md`** (that pair is the sustained-prose configuration, so that is what gets tested),
  including one contested prompt and one long enough to drift; re-run `style_metrics.py`; compare
  feature distributions *and modulation* against held-out originals; and confirm nothing on the
  avoid-list appears.

Log all three results to `provenance.md` and the coverage report. If a check falls below threshold,
emit a **reduced-scope** core with the gap logged, or surface it to the user for corpus improvement
— never paper over it. → Procedures, thresholds, and reporting: `references/fidelity-tests.md`.

---

## Output

A directory containing:
- **`SKILL.md`** — the core embodiment artifact, sized to the **computed budget** (typically
  3,000–5,500 tokens; floor 3,000, ceiling 4,000–6,500 by corpus), front-loaded (compaction
  truncates from the end, so highest-value fingerprints come first).
- **`references/`** — modular files sized for on-demand loading. Two are **standing, cross-corpus
  modules of equal status**: `frameworks.md` (the person's named constructs, defined in their sense)
  and `voice.md` (the measured expressive system — favored and *avoided* constructions, modulation
  rules, register range, lexical fingerprint, the `style_metrics.py` baseline, and anti-drift
  pairs). The rest are per-source or residual: one module per high-value source cluster,
  `episodic.md` for demoted attested material, and `provenance.md` mapping each core element to its
  source. Sizes: cluster modules ~1,500–4,000 tokens each (hard ceiling 6,000 — split rather than
  trim), `frameworks.md` / `voice.md` / `episodic.md` soft ~4,000, `provenance.md` uncapped since it
  is an audit file.

Name the output directory with a user-supplied or auto-generated slug + `-perspective`
(e.g. `deneen-perspective`), and write it to the persona-out location resolved at the start of the
run. If a persona of that name already exists, offer incremental **fold-in** of the new corpus with
re-curation rather than a blind overwrite.

Then hand the user a short **coverage report** (this is where honesty lives): what the corpus
covered well, where it was thin, the fidelity-test scores, and any domains where the persona
should be trusted less. Keep this report *out* of the core `SKILL.md`.

---

## Scope, defaults, and judgment

- **Small or low-diversity corpus** → smaller core + explicit coverage report. Never hallucinate
  missing probes to hit a size target.
- **Heavily dialogue vs. heavily monologic corpus** → auto-raise the interactional pass weight for
  dialogue-rich corpora; lean harder on projectible-regularity extraction for monologic ones.
- **Contradictory signals across time periods** → treat as documented evolution/tension *only if*
  projectibility stays high; otherwise drop the weaker signal rather than blending them into mush.
- **Narrow user focus** (e.g. "only decision style") → re-weight scoring toward the requested
  facet and prune off-focus probes.
- **Modes:** default is full distillation. If the user says "analyze only" or "let me review
  first", run Stages 1–3 and hand them the ranked extraction + scoring log, then stop. If they
  point you at an existing persona, run in fold-in/update mode.

This skill operates only on public material the user has the right to use, and produces a
perspective/thinking-style tool — for analysis, study, and ideation in the person's documented
frame. It is not for deceptive impersonation, forged attribution, or passing off invented
statements as the person's real words. If a request bends that way, say so and reshape it toward
legitimate perspective work.

## Suggested execution order for the engineer inside this skill
Because Stage 3 (scoring + elevation + deletion) and the tests encode the real value, get them
right first, before polishing extraction breadth. And note the control flow is a **loop, not a
straight line**: score → gate (projection + cost) → re-curate / re-weight → assemble → final
verify. Assembly is always downstream of passing the gates; if the gates fail, you go back to
curation, never forward to the template. The remaining stages can reuse familiar modular-skill
patterns (lean front-loaded core, on-demand reference files, tight token budgets).

## Reference files
- `references/acquisition.md` — before Stage 1: resolving remote source types, fetching, separating
  corpus from container, the attribution classification and its three hard rules, source
  independence, wiki chunking, and honest degradation when the host has no network.
- `references/pipeline.md` — Stage 1 & full-pipeline mechanics, extraction routing by file type,
  the coverage map schema.
- `references/extraction.md` — Stage 2: the expression-DNA taxonomy, projectible-regularity
  verification, and the cost-bearing / interactional catalogue.
- `references/scoring.md` — Stage 3: the five probes in depth, worked scoring examples, the
  deletion rule, and the audit-log format.
- `references/output-template.md` — Stage 4: exact core `SKILL.md` template + references package
  layout, with a filled example.
- `references/fidelity-tests.md` — Stage 5: projection / cost / style-match procedures, thresholds,
  and reporting.
- `references/schemas/` — JSON Schema (draft 2020-12) for every intermediate artifact
  (`clusters/manifest.json`, `coverage_map.json`, `extractions.json`, `scores.json`,
  `fidelity.json`, and the `passages.json` input to `holdout_split.py`). The snippets in the prose
  references are illustrative and some carry `//` comments; these schemas are authoritative and
  parseable. Consult one before writing the corresponding artifact.

## Scripts
- `scripts/style_metrics.py` — computes countable expression features (sentence-length
  distribution, hedge/booster rates, punctuation rhythm, lexical diversity, person-reference
  ratios, top content terms/bigrams) for a text file or directory. Stdlib only; no install.
- `scripts/holdout_split.py` — reproducible seeded split of passages into keep/masked sets for
  the held-out projection test. Takes a JSON list of passage IDs (see
  `references/schemas/passages.schema.json`) or `--ids` on the command line — not a corpus path.
