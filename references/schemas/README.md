# Artifact schemas

Machine-readable [JSON Schema](https://json-schema.org/) (draft 2020-12) definitions for the
intermediate artifacts the pipeline writes to its work directory.

**None of these files are produced by this repository.** They describe artifacts the distiller
generates at runtime, in its work directory (default `persona_work/` — see
[pipeline.md](../pipeline.md)), for one specific corpus. There is no universal `extractions.json`;
shipping one would mean shipping some particular person's extraction output as if it were a
template.

What the repository ships is their *shape*. The schemas exist so those artifacts have one
canonical, validatable form rather than five illustrative snippets scattered across the reference
docs — several of which carry `//` comments for readability and are therefore not parseable as
JSON if copied verbatim.

Each schema carries a worked `examples` block. Where a schema and a prose snippet disagree, the
schema is authoritative.

## Index

| Artifact | Stage | Schema | Prose |
|---|---|---|---|
| `clusters/manifest.json` | 1 — segment | [`clusters-manifest.schema.json`](clusters-manifest.schema.json) | [pipeline.md](../pipeline.md) |
| `coverage_map.json` | 1 — coverage map | [`coverage-map.schema.json`](coverage-map.schema.json) | [pipeline.md](../pipeline.md) |
| `extractions.json` | 2 — extraction | [`extractions.schema.json`](extractions.schema.json) | [extraction.md](../extraction.md) |
| `scores.json` | 3 — curation audit log | [`scores.schema.json`](scores.schema.json) | [scoring.md](../scoring.md) |
| `fidelity.json` | gate + 5 — verification | [`fidelity.schema.json`](fidelity.schema.json) | [fidelity-tests.md](../fidelity-tests.md) |
| `passages.json` | 5 — projection test input | [`passages.schema.json`](passages.schema.json) | script docstring |

`passages.json` is the one artifact you hand *to* a script rather than receive from the pipeline —
`scripts/holdout_split.py` reads it. The script's own output (`split.json`) has no schema here; the
script is its source of truth.

## Constraints the schemas encode

Beyond field types, a few of the skill's hard rules are expressed structurally:

- A `regularity` element requires **≥2 clusters** — the corroboration rule from Stage 2.
- A `cost_refusal` or `interactional` element requires `convenient_move`, since the divergence
  between the convenient response and the attested one *is* the signal.
- A `core` decision requires a `rank`, because core entries are ordered by class priority before
  composite and the ordering has to be recoverable.
- All probe scores and composites are bounded to 0–1.

Two rules are deliberately **not** encoded, because valid records violate them:

- The **0.55 deletion threshold** — cut entries legitimately score below it, and entries above it
  are still cut when they read generic or conflict with a higher-scoring voice feature.
- **Weights summing to 1.0** — auto-weighting renormalises, but JSON Schema cannot express the sum.
  Check it yourself when you adjust weights.

## Validating

Optional, and no dependency is added to this repo:

```bash
pip install check-jsonschema
check-jsonschema --schemafile references/schemas/scores.schema.json path/to/scores.json
```
