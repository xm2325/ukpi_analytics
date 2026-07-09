# UKPI Client Segmentation and Offer Analytics

Synthetic-data portfolio project for a UK Personal Investor (UKPI) retail-investment analytics role. The project shows how SQL/Python-style data work can support client segmentation, offer analysis, dashboard reporting, and customer-level service design without making personal investment advice.

## What this project demonstrates

- Five customer segments based on assets, cash ratio, pension/ISA ownership, contribution behaviour, and digital engagement.
- Segment-level offer analysis for ISA reminders, SIPP contribution reminders, cash-to-invest education, and managed-service education.
- Chart-first reporting using a colourblind-safe journal-style palette rather than a single blue colour.
- A dynamic HTML customer dashboard where selecting a customer changes the segment, needs, recommended communication route, and comparison charts.
- A safe boundary: outputs are communication and education analytics, not fund recommendations, suitability decisions, or regulated financial advice.

## Run locally

```bash
pip install -r requirements.txt
python ukpi_analytics_demo.py
```

The script creates:

```text
outputs/figures/
outputs/tables/
outputs/ukpi_dashboard.html
reports/analysis_report.md
```

## Why it matches the role

The project mirrors a UKPI data analyst workflow: generate and clean customer-level data, build an analytics feature table, create business-ready segments, test campaign uplift, produce visual dashboards, and explain results to technical and non-technical stakeholders.

All data are synthetic. No Vanguard data or real customer data are used.
