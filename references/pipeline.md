# Pipeline mechanics — ingestion, segmentation, coverage map

Read this before running Stage 1 the first time. It covers how to get clean text out of mixed
formats, how to cut the corpus into clusters, and the internal artifacts the later stages depend on.

## Working directories

**Create the work directory before anything else.** Default to `persona_work/` under the current
working directory; use a host-provided scratch or temp location instead when one exists. Every
later stage reads and writes here, so resolve the path once and reuse it.

```
<work-dir>/                # default: ./persona_work/
├── raw/                   # extracted plain text, one file per source
├── clusters/              # segmented clusters, one file per cluster, with a manifest
├── coverage_map.json      # domains, dialogue ratio, decision density, temporal spread
├── extractions.json       # Stage 2 output: every candidate element with evidence
├── scores.json            # Stage 3 output: composite scores + keep/cut + reason
└── fidelity.json          # gate results + Stage 5 results
```

Keep these artifacts for the whole run — do not clean up between stages. Three things depend on it:
the control flow is a **loop** (a failed gate sends you back to re-curate, which needs
`extractions.json` and the previous `scores.json`); the hard deletion rule is only defensible
because `scores.json` logs every keep/cut with its reason; and the honesty split relocates all
caveats into the coverage report and `provenance.md`, which are built from `coverage_map.json` and
`fidelity.json`.

Only the finished persona directory is delivered to the user, at the persona-out location resolved
at the start of the run. The work dir is your scratchpad and stays behind.

**If the work dir sits inside a git repository, confirm it is ignored before writing.** `raw/` holds
the extracted full text of the source corpus; committing it would republish the sources.

Shapes for every JSON artifact above: [`schemas/`](schemas/) — authoritative and validatable. The
snippets in this file are illustrative and some carry `//` comments for readability, so they will
not parse if copied verbatim.

## Extraction routing by file type

Preserve structure — headings, speaker turns, timestamps — because segmentation and the
interactional pass depend on it.

Each row below gives a **preferred** route and a **fallback**. If your host offers a
document-reading tool or companion skill for a format, prefer it; otherwise take the fallback,
which needs only common libraries or a standard CLI. Never fail a run because a preferred tool is
absent — fall back and note any resulting quality loss in the coverage report.

| Format | Preferred | Fallback | Keep |
|---|---|---|---|
| TXT / MD | read directly | — | headings, lists, quotes |
| HTML | host HTML reader | strip tags, keep heading levels and blockquotes | headings, lists, quotes |
| PDF | host PDF-reading tool (essential for scanned or complex layouts) | `pdftotext -layout`, else `pypdf` | page breaks, headings |
| EPUB | `ebooklib` | unzip and read spine XHTML in document order | chapter boundaries |
| DOCX | host DOCX tool | `python-docx` | headings, styles |
| Transcripts | read directly | — | who-said-what, turn order |

Sanity-check every extraction: if a file yields near-empty or garbled text (common with scanned
PDFs), flag it and either OCR it or note it as unusable in the coverage report — do not silently
distill from noise.

## Segmentation into clusters

A **cluster** is a coherent unit that can carry independent evidence. Good cluster boundaries:

- **By work / chapter** for books and long essays.
- **By session** for interviews, talks, podcasts (one cluster per interview).
- **By decision** for decision records / project write-ups (one cluster per documented choice).
- **By time period** when you have a long span and want to track evolution (e.g. pre-2015 vs post).
- **By register** when the same person writes very differently in different venues (scholarly vs
  social) — split so the modulation is visible rather than averaged away.

The reason clusters matter: the projectibility probe requires a regularity to appear in **≥2
independent clusters**. If everything is one blob, nothing can be corroborated, and you will
over-trust one-off remarks. Err toward more clusters, but keep each large enough to be meaningful
(a two-sentence "cluster" corroborates nothing).

Write a `clusters/manifest.json`:

```json
{
  "clusters": [
    {"id": "c01", "label": "Book: <title> ch.3", "source": "raw/book.txt",
     "kind": "monologue", "period": "2018", "tokens": 4200}
  ]
}
```

`kind` is one of `monologue | dialogue | decision_record`. It drives auto-weighting in Stage 3.

## Coverage map

After segmentation, compute `coverage_map.json`. This is the backbone of the honest coverage
report and of several auto-weighting defaults.

```json
{
  "total_tokens": 128000,
  "n_clusters": 14,
  "domains": ["political philosophy", "religion", "economics"],
  "dialogue_ratio": 0.35,            // dialogue+decision tokens / total
  "decision_density": 0.12,          // decision-record tokens / total
  "temporal_spread": {"earliest": "2006", "latest": "2024", "gaps": ["2011-2014"]},
  "thin_domains": ["foreign policy"],   // present but under-attested
  "notes": "Heavy on monologic prose; little live dialogue."
}
```

Use it to:
- **Auto-weight** — high `dialogue_ratio` → raise the interactional pass and probe weight; low
  → lean on projectible-regularity extraction.
- **Set expectations** — `thin_domains` and `temporal gaps` become explicit caveats in the
  coverage report handed to the user (never in the persona).
- **Bound scope** — if `total_tokens` is very low or `domains` is one narrow slice, plan for a
  reduced-scope core up front.

## Handoff to Stage 2

Stage 2 reads `clusters/` + `coverage_map.json` and writes `extractions.json`. Every candidate
element carries: a stable `id`, its `type` (expression feature / projectible regularity /
cost-refusal / interactional move / preoccupation), the `clusters` it appears in, 1–3 short
**example passages** (for evidence, not for verbatim reproduction in the core), and any measured
metrics from `style_metrics.py`. That evidence is what Stage 3 scores and what Stage 5 tests
against, so capture it faithfully now.
