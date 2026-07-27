# persona-distiller

**Turn one person's public record into a persona another agent can *embody*.**

`persona-distiller` is an [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that takes a corpus of one person's material — books, essays, transcripts, interviews, decision records — and distills it into a compact, embodiment-ready perspective skill: a lean core `SKILL.md` plus a modular `references/` package.

Not a biography. Not a summary. Not a quote database. The output is optimized so that a reader familiar with the person's record cannot easily tell its output apart from the real thing, on public topics the corpus actually covers.

---

## What makes it different

Most voice-cloning prompts reach for what is easy to count — sentence length, favourite punctuation, hedge-word frequency. Those features are cheap to measure and almost everyone's are somewhat generic. This skill deliberately spends its budget elsewhere:

| Signal | Why it individuates |
|---|---|
| **Cost-bearing refusals** | Positions the person held *against* their own incentive |
| **Patterns of variation** | How their register shifts under pressure, audience, or stakes |
| **Interactional moves** | How they concede, reframe, dig in, or shift footing in exchange |
| **Projectible regularities** | Thought-moves that actually predict stance on held-out material |

Two design commitments follow from that:

1. **Recognition is a family resemblance.** Identity shows up redundantly, at different grains, through overlapping probes. The skill does *not* partition a person into tidy mutually-exclusive buckets, and does *not* dedupe a trait away just because it surfaced in three passes. Redundant corroboration across probes is strength.

2. **Delete without mercy.** A tight ~4k-token core that nails the fingerprints beats a comprehensive 15k-token one that reads like everyone. Anything scoring below threshold, reading as generic, or conflicting with a higher-scoring voice feature gets cut — not softened, not averaged in.

### The honesty split

The generated persona contains **no uncertainty disclaimers, no provenance hedging, no meta framing**. Those move a reader out of the voice and destroy identification.

Honesty does not disappear — it **relocates**. Coverage gaps, source citations, confidence levels, and limitations live in the `references/` package and in a coverage report handed to the user, never inside the embodiment artifact. You keep full auditability; the persona keeps its voice. This split is the whole trick.

---

## Installation

### Claude Code

```bash
git clone https://github.com/ariel-lee-1023/persona-distiller.git ~/.claude/skills/persona-distiller
```

Or, to install for a single project instead of globally:

```bash
git clone https://github.com/ariel-lee-1023/persona-distiller.git .claude/skills/persona-distiller
```

Restart Claude Code (or start a new session) and the skill will be discoverable.

### Claude.ai / Claude Desktop

Zip the repository contents so that `SKILL.md` sits at the root of the archive, then upload it under **Settings → Capabilities → Skills**.

```bash
cd persona-distiller && zip -r persona-distiller.zip SKILL.md references scripts
```

### Requirements

Python 3.8+ for the two helper scripts. **No third-party dependencies** — both are standard library only.

---

## Usage

The skill is model-invoked; it fires on natural phrasing. Upload the corpus, then say something like:

> Distill these into a perspective skill I can load.

> Build a persona skill from this author's collected essays.

> I want an agent that thinks like the person who wrote these transcripts.

You don't have to say the word "skill" for it to trigger.

### Modes

| Mode | How to ask | What happens |
|---|---|---|
| **Full distillation** *(default)* | Just upload and ask | Runs all five stages, delivers the persona directory + coverage report |
| **Analyze only** | "analyze only" / "let me review first" | Runs Stages 1–3, hands you the ranked extraction and scoring log, then stops |
| **Fold-in / update** | Point it at an existing persona | Re-curates against the new corpus instead of blindly overwriting |

### Optional focus statement

Narrow the distillation by naming a facet — *"decision style in public controversies"*, *"overall voice for analysis tasks"*. Scoring re-weights toward the requested facet and prunes off-focus probes. Omit it for overall identification.

### Accepted input

PDF, EPUB, DOCX, TXT, Markdown, HTML, and transcripts. Mixed formats are fine.

---

## The pipeline

Five stages, run in order — with a **loop**, not a straight line, at its centre.

**Stage 1 — Ingest & segment.** Extract text with structure preserved (headings, speaker turns, timestamps). Segment into coherent clusters and build a coverage map: domains, dialogue-vs-monologue ratio, decision density, temporal spread.

**Stage 2 — Multi-granularity extraction.** Three passes: fine-grained expression (measured by `style_metrics.py`, not guessed), coarse-grained projectible regularities, and the interactional / cost-bearing pass. Every point where the *convenient* response diverges from the person's *attested* response gets flagged. Those flags are gold.

**Stage 3 — Multi-probe curation & deletion.** Every element scored 0–1 on a weighted composite:

| Probe | Weight |
|---|---|
| Projectibility | **0.30** |
| Cost / refusal signal | **0.25** |
| Expressive match | 0.20 |
| Interactional visibility | 0.15 |
| Preoccupation / gravitational weight | 0.10 |

Hard deletion rule below 0.55 composite. Hard elevation rule ranks survivors by *class priority first* — because style metrics are abundant and cost-refusals are sparse, raw ranking would let volume crowd the fingerprints out. Pure style averages may fill at most ~20% of the core.

**Gate before Stage 4.** Assembly is downstream of passing two gates: a **projection gate** (held-out prediction) and a **cost gate** (every high-signal divergence accounted for). Gate results are *control signals*, not reports — failing one sends you back to re-curate, never forward to the template.

**Stage 4 — Assemble.** Core `SKILL.md` plus the `references/` package, following a fixed template, obeying the no-meta rule absolutely.

**Stage 5 — Final fidelity verification.** Projection re-check, cost/presence assertion, and style-match test. The hard minimum: *if the corpus contains any high-signal cost-bearing refusal, the core must contain at least one.* Failing this blocks delivery — it is the most common way a core ends up articulate but generic.

---

## Output

A directory named `<slug>-perspective` containing:

- **`SKILL.md`** — the core embodiment artifact, targeted under 5,000 tokens, front-loaded (compaction truncates from the end, so the highest-value fingerprints come first).
- **`references/`** — modular files sized for on-demand loading (~800–2,000 tokens each): one per high-value source cluster, a glossary of the person's named frameworks, episodic and lower-scoring attested passages, and a provenance index mapping each module to its source.

Plus a short **coverage report** delivered in conversation: what the corpus covered well, where it was thin, the fidelity-test scores, and any domain where the persona should be trusted less.

Output quality is strictly bounded by corpus coverage, diversity, and signal density. A thin corpus yields a smaller, honestly-scoped core — never fabricated probes padding it out to hit a size target.

---

## Repository layout

```
.
├── SKILL.md                        # the skill itself — pipeline, rules, judgment calls
├── references/
│   ├── pipeline.md                 # Stage 1 mechanics, extraction routing, coverage map schema
│   ├── extraction.md               # Stage 2 taxonomy and cost-bearing catalogue
│   ├── scoring.md                  # Stage 3 probes, worked examples, audit-log format
│   ├── output-template.md          # Stage 4 core template + package layout
│   ├── fidelity-tests.md           # Stage 5 procedures, thresholds, reporting
│   └── schemas/                    # JSON Schema for every intermediate artifact
│       ├── clusters-manifest.schema.json
│       ├── coverage-map.schema.json
│       ├── extractions.schema.json
│       ├── scores.schema.json
│       ├── fidelity.schema.json
│       └── passages.schema.json
├── scripts/
│   ├── style_metrics.py            # countable expression features (stdlib only)
│   └── holdout_split.py            # reproducible seeded keep/masked split
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
└── README.md
```

### Host requirements

The skill is written to run under **any** agent host, not a particular one. It needs a filesystem it
can write to and Python 3 for the two scripts; both are standard-library-only, with no install step.

Three locations are host-dependent and resolved once at the start of a run: where the corpus is read
from, where the work directory is created (default `persona_work/`), and where the finished persona
is delivered. Anything else the pipeline suggests — a PDF reader, a DOCX converter, a companion
document skill — is a preference with a named stdlib fallback, so a missing tool degrades quality
rather than failing the run.

### Scripts

Both run standalone, no install required.

```bash
# Measure expression features across a corpus (or a single file)
python scripts/style_metrics.py path/to/corpus/

# Produce a reproducible seeded split for the held-out projection test.
# Takes a JSON list of passage IDs — {"passages": ["p001", ...]} or a bare array — not a corpus path.
python scripts/holdout_split.py passages.json --seed 42 --frac 0.12 --out split.json

# …or pass the IDs inline
python scripts/holdout_split.py --ids p001 p002 p003 p004 --seed 42
```

`style_metrics.py` reports sentence-length distribution, hedge and booster rates, punctuation rhythm, lexical diversity, person-reference ratios, and top content terms and bigrams.

### Artifact schemas

The pipeline writes five intermediate JSON artifacts to its work directory (default `persona_work/`) — `clusters/manifest.json`, `coverage_map.json`, `extractions.json`, `scores.json`, `fidelity.json` — plus the `passages.json` that `holdout_split.py` reads. These are **runtime outputs for a specific corpus, not files this repository ships**. There is no universal `extractions.json`; it is the extraction of one particular person's material. They are kept for the whole run rather than cleaned up between stages, because the gates can send curation backwards and because the audit log and coverage report are built from them. `.gitignore` keeps them out of version control.

What the repository does ship is their shape: [`references/schemas/`](references/schemas/) holds a JSON Schema (draft 2020-12) for each, with worked examples. The snippets embedded in the prose references are illustrative and some carry `//` comments, so they will not parse if copied verbatim — the schemas are the authoritative, validatable version. A few of the skill's hard rules are encoded structurally there too (the ≥2-cluster corroboration rule, the required `convenient_move` on cost-refusal elements, 0–1 score bounds). See [`references/schemas/README.md`](references/schemas/README.md) for the index and what is deliberately left unencoded.

---

## Scope and intended use

This skill operates only on public material the user has the right to use, and produces a **perspective / thinking-style tool** — for analysis, study, and ideation in the person's documented frame.

It is **not** for deceptive impersonation, forged attribution, or passing off invented statements as a person's real words. The skill is written to say so and to reshape such requests toward legitimate perspective work.

Distilling a living person's voice carries obvious dual-use weight. Use the coverage report. Label outputs as perspective work. Don't put words in anyone's mouth.

---

## Contributing

Issues and pull requests welcome. The parts that carry the real value are Stage 3 (scoring, elevation, deletion) and the fidelity tests — improvements there are worth more than broader extraction coverage.

---

MIT © 2026 Ariel Lee. [See LICENSE](LICENSE).

This license covers the original text in this repository. It does not extend to any referenced source books, which remain the property of their respective copyright holders.
