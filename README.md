# UKPI Client Segmentation and Offer Analytics

This repository contains a synthetic-data analytics workflow for a UK retail-investment platform use case. It turns customer, account, holding, transaction, web/app, and campaign data into a customer-level feature mart, interpretable segments, treatment-control evidence, SQL outputs, and stakeholder-facing dashboards.

The data are synthetic. They are not Vanguard data and not real customer data.

## Questions the project answers

1. What customer groups appear in the data?
2. Why was a five-segment solution retained?
3. Which education or reminder route appears strongest for each segment?
4. How uncertain are the apparent treatment-control differences?
5. Did the generated data and outputs pass basic quality checks?
6. How can the analysis support service design without becoming personal investment advice?

## Project flow

```text
synthetic customer and campaign data
        ↓
customer-level feature mart
        ↓
segmentation
  k=2–8 diagnostics + multi-seed stability checks
        ↓
offer analysis
  treatment/control rates + uplift + 95% intervals + sample sizes
        ↓
validation
  data-quality checks + SQL questions + generated snapshot
        ↓
evidence-led HTML dashboard
  answer first → evidence → uncertainty → interpretation → limits
```

## Run locally

```bash
pip install -r requirements.txt
python ukpi_analytics_demo.py
python scripts/evaluate_segmentation.py
python scripts/build_evidence_layer.py
python scripts/run_sql_checks.py
python scripts/export_generated_snapshot.py
python scripts/build_guided_dashboard.py
```

## Main generated outputs

```text
docs/index.html                              default evidence-led dashboard
docs/guided_dashboard.html                   same evidence-led dashboard under an explicit name
docs/ukpi_dashboard.html                     original interactive customer dashboard

outputs/figures/01_segment_size_journal_palette.png
outputs/figures/02_segment_need_map.png
outputs/figures/03_recommended_offer_lift.png
outputs/figures/04_offer_uplift_heatmap.png
outputs/figures/05_treatment_control_conversion.png
outputs/figures/06_segment_profile_comparison.png
outputs/figures/07_recommended_offer_uncertainty.png
outputs/figures/08_cluster_count_diagnostic.png

outputs/tables/offer_uplift_with_uncertainty.csv
outputs/tables/data_quality_summary.csv
outputs/tables/cluster_diagnostics.csv
outputs/tables/segment_stability.csv
outputs/tables/sql_checks/*.csv

reports/analysis_report.md
reports/evidence_report.md
reports/segmentation_diagnostics.md
reports/sql_check_report.md

data/generated_snapshot/
```

## Current synthetic result

The generated customer book contains 2,500 customers and is presented as five interpretable groups:

- high-value engaged investors;
- cash-heavy cautious investors;
- emerging monthly investors;
- pension builders approaching retirement;
- low-engagement or dormant investors.

The strongest simulated treatment-control difference is reported together with treatment and control sample sizes and an approximate 95% interval. The dashboard distinguishes an estimated signal from evidence that remains directional or uncertain.

## Repository map

```text
ukpi_analytics_demo.py               synthetic data, segmentation, campaign simulation, base figures
scripts/evaluate_segmentation.py     k diagnostics and multi-seed adjusted Rand stability
scripts/build_evidence_layer.py      uncertainty, sample sizes, quality checks, evidence figure
scripts/run_sql_checks.py            SQLite execution of stakeholder-style SQL questions
scripts/export_generated_snapshot.py copies a frozen generated run into the repository
scripts/build_guided_dashboard.py    builds the evidence-led default dashboard
sql/ad_hoc_business_questions.sql    reusable business-facing SQL queries
docs/project_story.md                project rationale
docs/data_dictionary.md              generated field definitions
docs/known_limits.md                 claims intentionally excluded from the demo
```

## Reproducibility

GitHub Actions regenerates the synthetic data, figures, tables, reports, SQL results, and dashboards. It then commits a frozen generated snapshot back to the repository. The workflow now fails visibly if the generated commit cannot be pushed, rather than silently leaving an old HTML file in the repository.

## Safety boundary

This project does not recommend a fund, portfolio, risk level, or personal investment action. It demonstrates service analytics, experimental reporting, and dashboard design using synthetic data.
