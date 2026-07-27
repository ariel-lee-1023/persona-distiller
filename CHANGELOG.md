# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] — 2026-07-27

Host portability + artifact schemas. The skill previously assumed the filesystem layout of one
specific agent host; it now runs anywhere. Intermediate artifacts gain canonical JSON Schemas.

### Added

- **`SKILL.md` — "Host environment" section** — the three host-dependent locations (corpus in, work
  directory, persona out) are now named explicitly and resolved once at the start of a run, instead
  of being hardcoded. States that suggested tools are preferences with fallbacks, and that both
  scripts are standard-library-only under any Python 3.
- **Explicit work-directory creation** — `references/pipeline.md` now instructs the agent to create
  the work directory before Stage 1 and explains why the artifacts must survive the whole run: the
  control flow is a loop, the deletion rule is only defensible with the audit log intact, and the
  coverage report and `provenance.md` are built from those files.
- **`.gitignore`** — blocks the work directory, generated `*-perspective/` personas, stray
  intermediate artifacts, and source-corpus formats (`*.pdf`, `*.epub`, `*.mobi`, `*.azw`,
  `*.docx`, and corpus directories). This last group protects the claim in `NOTICE.md`: a single
  careless `git add -A` on a corpus directory would republish the source works. Shipped schemas are
  explicitly re-included so no JSON rule can shadow them.
- **`references/schemas/`** — JSON Schema (draft 2020-12) for every intermediate artifact the
  pipeline writes, each with a worked example: `clusters-manifest.schema.json`,
  `coverage-map.schema.json`, `extractions.schema.json`, `scores.schema.json`,
  `fidelity.schema.json`, and `passages.schema.json` (the input `holdout_split.py` reads).
  Previously these shapes existed only as illustrative snippets across four reference files,
  two of which carry `//` comments and so do not parse as JSON if copied verbatim.
- **Structurally encoded rules** — the schemas express several of the skill's hard constraints
  rather than only field types: a `regularity` element requires ≥2 corroborating clusters, a
  `cost_refusal` or `interactional` element requires `convenient_move`, a `core` decision requires
  a `rank`, and all probe scores and composites are bounded to 0–1.
- **`references/schemas/README.md`** — artifact-to-stage-to-schema index, and an explicit note on
  the two rules deliberately left unencoded (the 0.55 deletion threshold, which valid `cut` records
  fall below, and weights summing to 1.0, which JSON Schema cannot express).

### Changed

- **Work directory is now relative** — `persona_work/` under the current working directory, or a
  host-provided scratch location, replacing the hardcoded `/home/claude/persona_work/`.
- **Corpus input and persona output locations are resolved from the host** rather than fixed to
  `/mnt/user-data/uploads/` and `/mnt/user-data/outputs/`. Those paths remain documented as one
  host's convention, not as the contract.
- **Extraction routing table restructured into preferred / fallback columns** — every format has a
  named stdlib or common-CLI fallback, so a host lacking a document-reading tool degrades output
  quality and logs it in the coverage report rather than failing the run.

### Fixed

- **`README.md` script usage** — the `holdout_split.py` example passed a corpus directory, which
  the script cannot read; it requires a JSON list of passage IDs or inline `--ids`. Corrected, and
  the `--ids` form added.
- **`SKILL.md` script description** — now states that `holdout_split.py` takes a JSON passage-ID
  list rather than a corpus path.

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

[Unreleased]: https://github.com/ariel-lee-1023/persona-distiller/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/ariel-lee-1023/persona-distiller/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/ariel-lee-1023/persona-distiller/releases/tag/v1.0.0
