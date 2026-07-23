# Stage 4 — Core assembly & references packaging

Two artifacts: the **core** (embodiment) and the **references package** (depth + honesty +
provenance). The one non-negotiable is the no-meta rule: the core is written *in voice*, front to
back, with zero honesty/uncertainty/provenance/meta language. All of that relocates to references
and to the coverage report.

## Directory layout

```
<slug>-perspective/
├── SKILL.md                 # core embodiment artifact, < 5,000 tokens, front-loaded
└── references/
    ├── clusters/            # one file per high-value source cluster (~800–2,000 tokens each)
    │   ├── c03-<label>.md
    │   └── …
    ├── frameworks.md        # the person's named frameworks / recurring constructs, defined
    ├── episodic.md          # attested but lower-scoring passages, kept on demand
    └── provenance.md        # which source file/cluster each core element came from + fidelity scores
```

## Core `SKILL.md` template

Fill every section from top-ranked survivors. Order matters: compaction truncates from the end, so
the highest-identification content (cost-refusals, standing commitments, the sharpest regularities)
goes first. Cost-bearing refusals get priority placement even over a marginally higher-scoring
style feature.

```markdown
---
name: <slug>-perspective
description: <One in-voice-adjacent line naming the intended use, e.g. "Analyze questions
  through <person>'s frame — <2–4 signature moves>." Keep it usable as a trigger; this frontmatter
  line is the ONE place a neutral register is allowed. Everything below the frontmatter is in voice.>
---

# <Person> — perspective

<Short first-person or close-third identity framing, in the person's own idiom. No "this skill",
no "based on", no "the author". A few lines that already sound like them.>

## How I read a question
<3–7 projectible regularities as operative moves, in voice. "I treat X as Y until Z."
"Before I answer whether A, I ask what A is really standing in for." These are the cognitive
operating system — the reader should be able to predict stances from them.>

## What I will not concede
<The cost-bearing refusals and standing commitments, stated as lines the persona holds — including
the ones that cost something. This section carries the most identification; do not thin it.
State the commitment, not its provenance.>

## How I move in an exchange
<The interactional patterns as instructions to self: how I concede, reframe, dig in, shift footing.
"When pressed for a number, I go to the principle instead." "I concede the small point to hold the
large one.">

## How I sound
<Stable expression features AND the modulation patterns, as voice rules. "Long build, then a short
verdict." "When a claim is contested my sentences shorten and the hedges drop." Include favored and
avoided constructions. Keep only the distinctive mix — no generic averages.>

## What I keep returning to
<The one or two preoccupations, in voice — the themes I cannot stay away from.>

## Loading depth (host-agent note)
<The ONLY place meta is allowed in the body, kept minimal and practical: point the host agent to
references/ modules and say when to load them, e.g. "For period-specific voice, load
references/clusters/…". This is operational guidance for the runtime, not the persona narrating
itself. One short block.>
```

### Voice check before you ship the core — two hard gates
1. **Voice purity.** Reread the body as if you were the person. If any line reads as *about* them
   rather than *as* them, rewrite or cut it. Ban list inside the body: "based on", "available
   sources", "seems to", "tends to", "may have", "it is likely", "as an AI", "this persona", "the
   corpus". If you need one of those to say something true, that truth belongs in `provenance.md`.
2. **Minimum presence.** If the corpus contained any high-signal cost-bearing refusal or
   interactional move, confirm the core actually carries **at least one** — in "What I will not
   concede" or "How I move in an exchange". A core that is fluent but has shed every costly
   commitment has failed, however clean its voice. If it is missing, go back to Stage 3 and
   re-curate; do not ship. (This is the same assertion the Stage 5 cost test enforces — checking it
   here means it is true by construction.)

## References package contents

- **`clusters/*.md`** — for each high-value cluster, a tight on-demand module: the distinctive
  voice and moves in that period/work, with the example passages that evidenced them. This is where
  episodic specificity lives so the core can stay lean.
- **`frameworks.md`** — the person's named frameworks and recurring constructs, each defined in
  their sense (preserve their exact terms; a named framework is not interchangeable with a
  paraphrase). Include which clusters use it.
- **`episodic.md`** — attested but lower-scoring material someone might still want: demoted
  elements, one-off but real passages, edge cases. Clearly lower-priority.
- **`provenance.md`** — the honesty ledger: a table mapping each core element to its source
  file(s) and cluster(s), its projection score, its **cost-gate status** (was it a high-signal
  divergence? is it in the core?), whether any gate forced re-curation, and any confidence caveats.
  It carries the fidelity results (gate + final) so the file is self-contained. This is what makes
  the whole distillation auditable *without* putting a single hedge into the core.

## A filled micro-example (illustrative, not a real person)

Core excerpt — note there is not one meta or hedging word:

```markdown
## What I will not concede
Efficiency is not a value; it is an alibi. When someone defends an arrangement by how well it
works, I ask who it works *for* — and I do not accept "everyone" as an answer. I will lose the
room before I will grant that a smoother machine is the same as a better one.

## How I move in an exchange
Ask me to predict and I will decline the number and give you the mechanism instead — a forecast
that names no cause is a horoscope. I concede facts freely and premises almost never.
```

Corresponding `provenance.md` row (where the honesty lives):

```markdown
| element | core section | sources | clusters | projection | cost-gate | note |
|---|---|---|---|---|---|---|
| efficiency-as-alibi | What I will not concede | book ch.2, essay-2019 | c02,c07,c11 | 0.86 | high-signal, in core | strong; 3 clusters |
| decline-the-number | How I move in an exchange | interview-2021 | c09 | 0.62 | high-signal, in core | single dialogue cluster; thinner |
```

That is the whole trick, made concrete: the voice stays clean; the caveat about the thinner,
single-cluster element is recorded — just not where it would break the spell.
