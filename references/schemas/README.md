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
| `clusters/manifest.json` | 1 — segment | [`clusters-manifest.schema.json`](clusters-manifest.schema.json) | [pipeline.md](../pipeline.md), [acquisition.md](../acquisition.md) |
| `coverage_map.json` | 1 — coverage map | [`coverage-map.schema.json`](coverage-map.schema.json) | [pipeline.md](../pipeline.md), [acquisition.md](../acquisition.md) |
| `extractions.json` | 2 — extraction | [`extractions.schema.json`](extractions.schema.json) | [extraction.md](../extraction.md) |
| `scores.json` | 3 — curation audit log | [`scores.schema.json`](scores.schema.json) | [scoring.md](../scoring.md) |
| `fidelity.json` | gate + 5 — verification | [`fidelity.schema.json`](fidelity.schema.json) | [fidelity-tests.md](../fidelity-tests.md) |
| `passages.json` | 5 — projection test input | [`passages.schema.json`](passages.schema.json) | script docstring |

`passages.json` is the one artifact you hand *to* a script rather than receive from the pipeline —
`scripts/holdout_split.py` reads it. The script's own output (`split.json`) has no schema here; the
script is its source of truth.

The two Stage 1 schemas also carry the results of **corpus acquisition**, which runs before Stage 1
when the source is remote: `attribution` plus the optional `source_url` / `retrieved` / `revision`
on each cluster, and the `sources[]` records plus `firsthand_ratio` on the coverage map. See
[acquisition.md](../acquisition.md).

## Constraints the schemas encode

Beyond field types, a few of the skill's hard rules are expressed structurally:

- A cluster requires an **`attribution`** label — `firsthand | secondhand | mixed | unknown`. It is
  required rather than optional because three hard rules read it (expression and modulation
  extraction runs on firsthand clusters only; a projectible regularity needs at least one firsthand
  cluster; cost-refusals and interactional moves attested only secondhand are flagged unverified and
  cannot satisfy the Stage 5 presence assertion), and an absent label defaults in practice to the
  optimistic reading. Making it required means a manifest cannot stay silent about whose words these
  are.
- A `regularity` element requires **≥2 clusters** — the corroboration rule from Stage 2.
- A `cost_refusal` or `interactional` element requires `convenient_move`, since the divergence
  between the convenient response and the attested one *is* the signal.
- A `core` decision requires a `rank`, because core entries are ordered by class priority before
  composite and the ordering has to be recoverable.
- `scores.json` requires **`core_budget`** with its supply term, ceiling row, clamp result, and the
  class counts that produced it. The core's size is computed per run rather than fixed, so an
  unlogged size is an unreproducible one; the ceiling is enumerated to `4000 | 5500 | 6500` so a
  budget cannot quietly exceed what the corpus supports.
- All probe scores and composites are bounded to 0–1.

Two rules are deliberately **not** encoded, because valid records violate them:

- The **0.55 deletion threshold** — cut entries legitimately score below it, and entries above it
  are still cut when they read generic or conflict with a higher-scoring voice feature.
- **Weights summing to 1.0** — auto-weighting renormalises, but JSON Schema cannot express the sum.
  Check it yourself when you adjust weights.
- **The 3,000-token core floor** — `budget` is not bounded below by it, because a reduced-scope core
  shipped against a genuinely thin pool is a valid outcome, not a malformed record. What the schema
  does insist on is that the shortfall be *visible*: `floor_triggered` is required.
- **The firsthand requirement on regularities** — the label lives in the manifest and the rule binds
  in `extractions.json`, and no schema can follow a cluster id across files. The enum makes the fact
  recordable; enforcing it is on you.

## Validating

Optional, and no dependency is added to this repo:

```bash
pip install check-jsonschema
check-jsonschema --schemafile references/schemas/scores.schema.json path/to/scores.json
```
