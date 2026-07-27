# Corpus acquisition — remote sources, container separation, attribution

Read this **before Stage 1** whenever the corpus is anything other than local files already on
disk. Acquisition is not a stage — the five stages start at ingestion, and this is the step that
produces something for them to ingest.

The failure this file exists to prevent is silent. Hand an agent a repository or a wiki and it will
happily read everything it finds, distil the README, the build config, and the navigation pages
along with the writing, and deliver a fluent persona **of the container** rather than of the person.
The second failure is quieter still: most online knowledge bases are somebody's notes *about* a
thinker, and distilling those yields a persona of the note-taker's summarising prose. Both are
addressed below, and both are addressed by *classifying before extracting*, never after.

## 1. Resolve the source type

Ask what you were handed before you fetch anything. Four types, and they behave differently:

| Source | What it is | What to do |
|---|---|---|
| **Local path or directory** | Files already on disk — current behaviour, unchanged | Go straight to Stage 1. Nothing here applies except attribution classification if the files came from someone else's collection. |
| **Git repository URL** | A repo of notes, essays, posts, or a published digital garden | Clone it. Record the commit SHA. |
| **Plain file URL** | One document — a PDF, an essay page, a transcript | Download it into the work dir. |
| **Docs site, wiki, or published note collection** | A rendered site: MkDocs, Docusaurus, Obsidian Publish, a wiki, a blog archive | Crawl **within the given path prefix only**. |

If the user gives you a bare domain and no path, ask which section holds the person's material.
Do not decide for them and do not take the whole domain.

## 2. Acquire

Everything lands under the work directory resolved at the start of the run. `.gitignore` already
covers it, which matters more here than for local corpora — you are now writing other people's
published text onto disk inside a repository.

- **Git** — shallow clone is fine (`--depth 1`); you want the text, not the history. Clone into
  `<work-dir>/src/<repo-name>/`. **Record the commit SHA.** Remote content changes; without the SHA
  a re-run is not the same run and the coverage report is claiming more than it knows.
- **File URL** — download into `<work-dir>/raw/`. Stage 1's extraction routing then runs over it in
  place, exactly as it would for an uploaded file.
- **Site or wiki** — crawl the given path prefix and stop there. Not the parent, not the domain, not
  outbound links. Save pages under `<work-dir>/src/<site>/` mirroring the URL path, so the mapping
  from file back to URL stays recoverable. Record the retrieval date.

Write an acquisition record for each source as you go — type, location, retrieval date, revision.
These become `sources[]` in `coverage_map.json`
(see [`schemas/coverage-map.schema.json`](schemas/coverage-map.schema.json)).

## 3. Separate corpus from container — do this before extracting anything

A repository or a site is a **container**. Some of what it holds is the person's writing; the rest
is the machinery that publishes it. Inventory everything you acquired and classify each path:

**Scaffolding — not corpus.** READMEs describing the collection · build and CI config · templates
and boilerplate · navigation, index, and tag pages · table-of-contents and sidebar files · licence
and contributing files · anything written by someone other than the subject.

**Corpus — the person's material.** Essays, chapters, posts, transcripts, notes they wrote,
correspondence, decision records. Commit messages count when the subject authored the commits.

Judgement calls belong to the user, not to you. **Show the classification and get confirmation
before Stage 1.** A short two-column list — path, corpus or scaffolding — is enough. Do not proceed
on a guess, and do not proceed on silence. A container is exactly the kind of thing that looks
uniform from the outside and is not.

## 4. Classify attribution — per acquired unit, carried onto every cluster

This is the substantive addition, and it is what makes a remote corpus safe to distil. Every unit
you acquired is one of four:

- **`firsthand`** — the person's own words. Their book, essay, transcript turns, posts, commit
  messages.
- **`secondhand`** — someone writing *about* the person. Summaries, study notes, paraphrase,
  reading notes, analysis, lecture notes on their work.
- **`mixed`** — quotation embedded in another author's commentary. Real words of theirs, in
  somebody else's prose, in proportions you cannot cleanly separate.
- **`unknown`** — authorship undeterminable. Say so; do not round it up to `firsthand` because the
  page is filed under the person's name.

Carry the label onto every cluster the unit produces: `attribution` is a **required** field in
[`schemas/clusters-manifest.schema.json`](schemas/clusters-manifest.schema.json). It is required
because the three rules below depend on it and a missing label defaults, in practice, to the
optimistic reading.

Why this matters more than it sounds: a well-organised knowledge base of someone's notes on a
thinker is *more* attractive to distil than the thinker's actual books — it is cleaner, better
segmented, and already thematic. It is also the wrong person. You would produce a persona of a
diligent summariser.

### Three hard rules

**Hard rule 1 — expression and modulation extraction runs on `firsthand` clusters only.** Never run
`style_metrics.py` on `secondhand` text. It measures sentence rhythm, hedge rates, and punctuation
of whoever typed the page, and those numbers then flow into the expressive-match probe as if they
were the subject's. This is not a preference. For `mixed` clusters, either isolate the quoted spans
and measure only those, or exclude the cluster from Pass A entirely — measuring the blend is worse
than measuring nothing.

**Hard rule 2 — a projectible regularity requires at least one `firsthand` cluster.** The ≥2-cluster
corroboration rule stands unchanged; this adds to it. Secondhand clusters may corroborate a
regularity, and often corroborate it well — a good summariser noticed a real pattern. They cannot
carry one alone. Two secondhand clusters agreeing tells you two note-takers read the same book.

**Hard rule 3 — cost-bearing refusals and interactional moves sourced only from secondhand material
are flagged `unverified`, and an unverified element cannot satisfy the Stage 5 cost/presence
assertion.** This is the highest-value class of signal and the easiest to get wrong at second hand:
paraphrase reliably flattens the divergence between the convenient move and the characteristic one,
which is the entire signal. Keep unverified elements — record them, score them, note what would
confirm them — but the assertion in `fidelity-tests.md` needs a firsthand one.

## 5. Independence is about source, not file

The ≥2-cluster corroboration rule assumes clusters are **independent evidence**. Remote sources
break that assumption in a way local uploads rarely do. Two pages of one knowledge base that both
derive from the same underlying work are **one** source, however different their filenames, folders,
or headings.

So before scoring, **collapse them**. Trace each cluster to the work it derives from; where two
clusters share an origin, merge them or mark one as non-corroborating. A regularity attested in
"notes/chapter-3.md" and "summaries/ch3-key-points.md" has been attested once. Left uncollapsed,
a single source silently satisfies a rule designed to require two, and the projectibility probe
starts scoring an echo.

## 6. Chunking wikis and note collections

Wiki and note-collection pages are usually far too small to be clusters on their own, and the
existing rule still binds: a two-sentence cluster corroborates nothing. Group before you segment:

- **By underlying source work** — every page derived from the same book or essay becomes one
  cluster. This is the default, because it is also what makes rule 5 above enforceable.
- **By topic** — where pages are original notes rather than derivations, group thematically until
  each cluster is large enough to carry evidence.
- **Deduplicate first.** Knowledge bases repeat themselves: the same definition on the concept page,
  the index page, and three notes that link to it. Repetition inside one base is not recurrence
  across clusters, and if you skip this step it will read as a preoccupation that does not exist.

Keep the per-page URL on each cluster (`source_url`) even after grouping, so provenance survives the
merge.

## 7. Honest degradation

If the host has no network access, or no `git`, **say so and ask the user to supply the material
locally** — a clone they make themselves, an export, a directory of downloaded files. That is a
complete answer and an easy one for the user to act on.

What you must not do: fill the gap from memory. Never substitute your own training-data recollection
of the person for retrieved text, and never fabricate a passage, a source, or a retrieval you did not
perform. The whole skill is bounded by "works only from the corpus"; an unreachable corpus is a
smaller corpus, not a licence to reconstruct one. If acquisition partly succeeded, distil what you
got, and record in the coverage report exactly what failed and why.

## 8. Rights

The scope statement in `SKILL.md` governs — public material the user has the right to use,
perspective work only, no forged attribution. Acquisition adds three specifics:

- **Respect `robots.txt`** and any stated crawl policy on the site.
- **Do not bypass paywalls or authentication.** If material sits behind either, ask the user to
  supply it from their own access.
- **A knowledge base's own licence is binding.** Someone else's notes are someone else's work, even
  when they are notes about your subject. Honour the terms they published under, and record the
  licence in the acquisition record.

## Handoff to Stage 1

Stage 1 starts with acquired material on disk, the corpus/scaffolding split confirmed by the user,
and an attribution label attached to every unit. It carries `attribution`, and where applicable
`source_url`, `retrieved`, and `revision`, into `clusters/manifest.json`; and the `sources[]` records
plus `firsthand_ratio` (firsthand tokens over total) into `coverage_map.json`. A low
`firsthand_ratio` is a coverage-report caveat, not a blocker — but it is one the user needs to see,
because it is the number that says how much of this persona came from the person.
