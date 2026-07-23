# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] — 2026-07-23

Initial public release.

### Added

- **`SKILL.md`** — the core skill: a five-stage pipeline (ingest & segment → multi-granularity
  extraction → multi-probe curation & deletion → assemble → fidelity verification) for
  distilling one person's corpus into an embodiment-ready persona skill.
- **Family-resemblance framing** — recognition treated as redundant, overlapping probes rather
  than a clean partition of the person; corroboration across probes is retained rather than
  deduplicated away.
- **Hard-signal prioritisation** — cost-bearing refusals, patterns of variation, and
  interactional moves weighted above easily-counted surface style.
- **Five-probe scoring composite** — projectibility (0.30), cost/refusal signal (0.25),
  expressive match (0.20), interactional visibility (0.15), preoccupation (0.10).
- **Deletion rule** — hard cut below 0.55 composite, plus unconditional cuts for generic
  language, forced meta-commentary, or conflict with a higher-scoring voice feature.
- **Elevation rule** — survivors ranked by class priority before composite, capping pure style
  averages at ~20% of the core so abundant style metrics cannot crowd out sparse fingerprints.
- **Pre-assembly gates** — projection gate and cost gate run *before* Stage 4 and feed back into
  curation as control signals, making the pipeline a loop rather than a straight line.
- **The honesty split** — no disclaimers or meta framing inside the embodiment artifact;
  coverage gaps, citations, and confidence relocated to `references/` and the user-facing
  coverage report.
- **`references/pipeline.md`** — Stage 1 mechanics, extraction routing by file type, coverage
  map schema.
- **`references/extraction.md`** — Stage 2 expression-DNA taxonomy, projectible-regularity
  verification, cost-bearing and interactional catalogue.
- **`references/scoring.md`** — Stage 3 probes in depth, worked scoring examples, deletion rule,
  audit-log format.
- **`references/output-template.md`** — Stage 4 core template and references-package layout,
  with a filled example.
- **`references/fidelity-tests.md`** — Stage 5 projection, cost, and style-match procedures,
  thresholds, and reporting.
- **`scripts/style_metrics.py`** — countable expression features (sentence-length distribution,
  hedge/booster rates, punctuation rhythm, lexical diversity, person-reference ratios, top
  content terms and bigrams). Standard library only.
- **`scripts/holdout_split.py`** — reproducible seeded split of passages into keep/masked sets
  for the held-out projection test.
- **Operating modes** — full distillation (default), analyze-only, and fold-in/update against an
  existing persona.
- **Scope statement** — perspective and thinking-style work only; explicit refusal of deceptive
  impersonation and forged attribution.

[Unreleased]: https://github.com/ariel-lee-1023/persona-distiller/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ariel-lee-1023/persona-distiller/releases/tag/v1.0.0
