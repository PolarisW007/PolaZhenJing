# Research Blueprint

Use this reference to turn a loose topic into a data-news plan.

## Minimal User Input

The user may only provide:

- a topic, e.g. "研究某 AI 公司的人才流动";
- a direction, e.g. "想看这家公司到底靠什么技术路线起家";
- a screenshot/article;
- a folder of partial data.

Turn that into:

```text
Research brief
- Working title:
- Why it matters:
- Core question:
- Subquestions:
- Candidate datasets:
- Tables to build:
- Charts to build:
- Caveats:
- First command/script to run:
```

## Reusable Question Families

### Paper / Research Output

- What did the organization publish, and when?
- Which topics or technical modules are repeated?
- Who appears repeatedly across work?
- Which people bridge multiple topics?
- What collaboration clusters appear in coauthorship data?
- Which claims are supported by papers versus outside interpretation?

### Company / Product / Market

- What products or releases shipped over time?
- Which features/pricing/markets changed?
- Which customers, partners, or regions recur?
- What signals show momentum: hiring, repos, papers, funding, traffic, app ranks?
- Which competitors occupy adjacent positions?

### People / Talent / Organization

- Who appears in public outputs?
- Which roles are explicit versus inferred?
- Who bridges teams/topics?
- What cannot be concluded from public data?

### Open Source / Developer Ecosystem

- How do stars, forks, contributors, issues, releases, and dependency graphs evolve?
- Which maintainers are central?
- Which modules receive most activity?
- What is driven by one-off bursts versus sustained work?

## Data Source Menu

Prefer sources in this order:

1. Official APIs or public datasets.
2. Public static pages with stable IDs.
3. GitHub/GitLab APIs.
4. arXiv/OpenAlex/Semantic Scholar/Crossref for papers.
5. SEC/registry/filing databases for companies.
6. RSS/sitemaps for articles and announcements.
7. PDFs as verification sources.
8. Screenshots as weak evidence or style/reference inputs.

## Standard Tables

Use these as defaults and adapt field names:

```text
raw/source_index.json
output/items_clean.csv
output/entities_clean.csv
output/entity_alias_map.csv
output/item_entity_edges.csv
output/category_matrix.csv
output/timeline_counts.csv
output/network_nodes.csv
output/network_edges.csv
output/data_quality_notes.csv
```

## Chart Acceptance Checklist

Before using a chart in the article:

- Does the title answer one question?
- Can the reader understand the denominator?
- Are categories defined?
- Are filters visible in a subtitle or footnote?
- Is each number reproducible from a CSV?
- Could this chart be misread as ranking, hierarchy, or causality?
- Does it work in a mobile article viewport?

## Article Claim Checklist

For each major sentence:

- Is it directly observed, calculated, or inferred?
- Which table supports it?
- Is the time period explicit?
- Are limitations stated nearby?
- Did we avoid turning public signals into private facts?

