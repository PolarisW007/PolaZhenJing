# DeepSeek Case Patterns

This reference distills the `案例/deepseek_papers_open` package into reusable patterns.

## What The Case Contains

The package is a reproducible data-news archive around 27 DeepSeek papers/technical reports. Its value is the workflow, not only the final images.

Important folders:

- `raw/`: Hugging Face API JSON snapshots, ar5iv HTML, PDFs, role snippets.
- `output/`: cleaned tables and intermediate statistics.
- `figures/`: final PNG/SVG charts and direct plot data.
- `scripts/`: 15 Python scripts for cleaning, role splitting, analysis, and plotting.
- `METHOD_WORKFLOW.md`: how the data-news work was designed from zero.
- `TUTORIAL.md`: how to reproduce charts from the package.

## Core Data Tables

Reusable table pattern:

- `papers_clean.csv`: item master table.
- `paper_authors_source_raw.csv`: raw item-entity rows.
- `paper_authors_clean.csv`: cleaned item-entity rows.
- `name_canonicalization_map.csv`: alias/canonical mapping.
- `data_quality_notes.csv`: caveats and manual interventions.
- `main_model_authors_with_roles.csv`: role-enriched entity rows.
- `main_model_role_summary.csv`: role counts and recommended comparable counts.
- `chart*_*.csv`: chart-specific data extracts.

The package uses raw snapshots first, then creates clean long tables, then derives chart tables.

## Metrics And Definitions

Key definitions from the case:

- Total signature authors are not employee or researcher counts.
- Research author pool filters large reports to Research & Engineering roles.
- V4 total signature count and V4 R&E count are separate denominators.
- Cross-direction means an author appears in papers across multiple coarse topics; it is not job change.
- Coauthorship networks come from shared signatures; they are not organization charts.

## Chart Set

The case uses six chart families:

1. Timeline and per-paper author scale.
2. Top high-frequency research authors.
3. Cross-direction author participation.
4. All research author coauthorship network.
5. Research matrix / hub network.
6. Technical module evolution map.

These generalize to:

- timeline,
- top recurring entities,
- cross-category span,
- relationship network,
- hub/bridge map,
- evolution or lineage map.

## Script Roles

Use this script taxonomy in new projects:

- `clean_data`: parse raw sources, normalize entities, create clean tables.
- `build_roles`: split or enrich roles/classes from appendices or special sources.
- `make_timeline`: chart time and scale.
- `make_top_entities`: chart recurring actors.
- `make_cross_category`: chart span across topics.
- `make_network`: build weighted edges, nodes, communities, and plot.
- `make_evolution`: encode technical/product lineage into a structured table and figure.

## Network Weighting

For shared membership networks, reduce large-list inflation:

```text
w(i,j)=sum 1/(N_p-1)
```

where `N_p` is the number of unique entities in shared item `p`.

## Caution Language

Use precise language:

- "public-paper signature sample"
- "research author pool under this filtering rule"
- "coauthorship network"
- "algorithmically detected clusters"
- "topic coverage"
- "public signals suggest"

Avoid:

- "employee count"
- "department"
- "org chart"
- "contribution ranking"
- "reporting relationship"
- "proof of internal strategy"

## Screenshot Reading Pattern

The provided long screenshot shows a finished article shape:

- opening claim about Agent-assisted research;
- method disclosure;
- several numbered findings;
- embedded charts after each claim;
- caveats around public paper data;
- concluding reflection about Agent workflows.

When given similar screenshots, extract:

- article section order;
- chart types and captions;
- visible claims and numbers;
- methodology language;
- caveats;
- visual style requirements.

Then rebuild the underlying reproducible workflow rather than only imitating the prose.

