# UKPI Client Segmentation and Offer Analytics

I built this as a small portfolio project for a UK retail investment platform data analyst role. The point is simple: take customer, account, holding, transaction, web/app, and campaign data, build one customer-level view, then use it for segmentation, offer analysis, and dashboard reporting.

The data are synthetic. They are not Vanguard data and not real customer data.

## What I wanted to check

A UK personal investor platform should not treat all customers as one group. Some customers hold a lot of cash, some are building pensions, some invest monthly, some are active online, and some barely use the platform. I wanted the project to answer four practical questions:

1. What customer groups appear in the data?
2. Which education or reminder route fits each group better?
3. What should a stakeholder dashboard show first?
4. How can the analysis support service design without becoming personal investment advice?

## Project flow

```text
raw synthetic tables
  customers, accounts, holdings, transactions, web_events, campaign_events
        ↓
customer feature mart
  one row per customer
        ↓
segmentation and offer analysis
  five customer groups + treatment/control offer lift
        ↓
chart-first dashboard
  business answer, figures, customer selector, safe wording
```

## Run locally

```bash
pip install -r requirements.txt
python ukpi_analytics_demo.py
```

The compact GitHub version recreates the outputs from scratch:

```text
outputs/figures/01_segment_size_journal_palette.png
outputs/figures/02_segment_need_map.png
outputs/figures/03_recommended_offer_lift.png
outputs/figures/04_offer_uplift_heatmap.png
outputs/figures/05_treatment_control_conversion.png
outputs/figures/06_segment_profile_comparison.png
outputs/ukpi_dashboard.html
outputs/customer_dashboard.html
docs/index.html
reports/analysis_report.md
```

## Main result

The synthetic book separates into five customer groups:

- high-value engaged investors;
- cash-heavy cautious investors;
- emerging monthly investors;
- pension builders approaching retirement;
- low-engagement or dormant investors.

The recommended action is not to recommend products. The safer action is to route customers to neutral education, ISA or SIPP reminders, and service information based on segment-level evidence.

## Notes added for review

I added a few plain project notes so the repo is easier to discuss in an interview:

- `docs/project_story.md`: why I built it and how the pieces fit together;
- `docs/data_dictionary.md`: field meanings and why the fields were used;
- `docs/interview_talk_track.md`: 60-second and 3-minute explanations;
- `docs/known_limits.md`: what I would not claim from this demo;
- `sql/ad_hoc_business_questions.sql`: stakeholder-style SQL questions.

## Safety note

This project does not recommend a fund, portfolio, risk level, or personal investment action. It is a service analytics and dashboard project using synthetic data.
