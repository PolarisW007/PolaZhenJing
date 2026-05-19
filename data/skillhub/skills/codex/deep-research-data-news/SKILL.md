---
name: deep-research-data-news
description: Use when the user gives a research topic, company, person, lab, industry, paper set, screenshot, article direction, or vague question and wants an Agent-driven deep research workflow that forms an analytical framework, crawls or imports large public datasets, cleans data, builds reproducible CSV/JSON tables, generates charts, and drafts a data-rich long-form article. Especially useful for AI company research, paper/news datasets, coauthor or organization networks, timeline analysis, topic clustering, and "zero hand coding" data journalism.
metadata:
  short-description: Deep research data journalism workflow
---

# Deep Research Data News

This skill turns a loose research direction into a reproducible data-news package: question framing, data collection, cleaning, analysis, charts, and a long-form article. It is distilled from the `deepseek_papers_open` case package, but must generalize beyond DeepSeek.

## Start Here

When this skill triggers, do not jump straight to writing. Run the workflow in phases:

1. **Frame**: convert the user's topic into 3-6 research questions and explicit measurement definitions.
2. **Source**: identify data sources, access method, legal/robots constraints, and expected fields.
3. **Ingest**: crawl, download, import, or parse raw data into `raw/` snapshots.
4. **Clean**: normalize names, entities, dates, categories, duplicates, roles, and quality notes.
5. **Analyze**: create reproducible `output/*.csv` tables before charts.
6. **Visualize**: build demo charts first, then final PNG/SVG charts with footnotes.
7. **Write**: draft the article from verified tables and charts, with caveats and methodology.
8. **Package**: leave scripts, data, figures, and method notes so the result is auditable.

If the user gives only a topic, make reasonable assumptions and begin with Phase 1. Ask only for blockers such as login-only data, paid APIs, or legal constraints.

## Required Project Shape

Create or reuse a project folder with this shape:

```text
research_slug/
  README.md
  METHOD_WORKFLOW.md
  requirements.txt
  raw/
  output/
  figures/
  scripts/
  templates/
  article/
```

Use `scripts/init_research_project.py` to scaffold this structure when starting a new project.

## Core Rules

- First make tables, then charts, then prose.
- Every chart must answer a named question.
- Every key number in the article must trace to a CSV/JSON file.
- Preserve raw snapshots. Do not overwrite raw data with cleaned data.
- Keep a `data_quality_notes.csv` for caveats, manual fixes, and unresolved ambiguities.
- Save exploratory charts with versioned names; final packages may keep only formal chart versions.
- Never describe inferred networks as real org charts, reporting lines, contribution rankings, or employee counts unless the data source directly proves that.
- Make human decisions explicit: topic taxonomy, entity merge rules, filtering criteria, and chart inclusion criteria.
- For web sources, respect robots, rate limits, copyright, and access restrictions. Prefer official APIs, public datasets, RSS, sitemaps, GitHub APIs, arXiv/OpenAlex/Semantic Scholar, SEC/registry filings, and documented endpoints.

## Phase Details

### 1. Frame

Produce a short research brief:

- Topic and target audience.
- Main claim candidates.
- 3-6 research questions.
- Data needed for each question.
- Proposed charts.
- Risks and likely caveats.

For examples and reusable question patterns, read `references/research_blueprint.md`.

### 2. Source

For each source, define:

- URL/API/dataset location.
- Access method: API, static HTML, PDF, CSV, GitHub, manual upload, screenshot OCR.
- Fields to collect.
- Refresh strategy.
- Known limitations.

If the user provides screenshots, inspect them as evidence and extract structure, claims, visible chart types, captions, and article flow. Treat screenshots as a starting brief, not authoritative data, unless the text is fully legible.

### 3. Ingest

Write scripts that save raw data into `raw/` before any transformation. Common scripts:

- `scripts/01_fetch_sources.py`
- `scripts/02_parse_raw.py`
- `scripts/03_clean_data.py`

Use structured parsers and APIs over brittle string scraping. Keep IDs stable.

### 4. Clean

Produce long tables that preserve provenance. Typical outputs:

- `output/items_clean.csv`
- `output/entities_clean.csv`
- `output/entity_alias_map.csv`
- `output/item_entity_edges.csv`
- `output/data_quality_notes.csv`

For author/company/person datasets, include raw name, clean name, source, source URL, confidence, and manual note fields.

### 5. Analyze

Generate analysis tables before plots:

- Timeline counts.
- Top entities.
- Category/topic matrix.
- Retention/cohort tables.
- Relationship edges and nodes.
- Cluster/community summaries.
- Outlier and quality checks.

For network edge weights, use fractional weighting when large group items would otherwise dominate:

```text
w(i,j)=sum over shared item p of 1/(N_p-1)
```

### 6. Visualize

Create demo charts first. Inspect them and revise data definitions before formal styling.

Prefer a small set of charts:

- Timeline or release map.
- Top entity/frequency chart.
- Cross-topic matrix.
- Relationship/network chart.
- Module/evolution map.
- Summary card or infographic.

Export final charts as PNG and SVG, with direct chart data saved next to the image.

### 7. Write

Draft with this structure:

- Hook from the central surprise.
- Method disclosure: what was crawled, cleaned, and counted.
- 3-5 findings, each grounded in a chart and CSV.
- Caveats before overclaiming.
- Closing section about what the data suggests and what it cannot prove.
- Appendix/method note with reproducibility commands.

## When Reusing The DeepSeek Case

If the task resembles paper/company research, read `references/deepseek_case_patterns.md` for the distilled file structure, scripts, metrics, and caution language from the case.

Do not copy DeepSeek-specific constants into a new domain unless the user's topic is DeepSeek. Generalize them into configurable taxonomies and source schemas.

