# Known limits

This project is a portfolio demo, not a production system.

## Synthetic data

The data are synthetic, so the numbers should not be read as real customer behaviour. The value is in the workflow: raw tables, mart, segmentation, offer analysis, dashboard, and safety boundary.

## Segmentation

The five customer groups are useful for explanation, but I would not fix the number of segments without checking stability over time and getting business feedback.

## Offer analysis

The treatment-control lift is simulated. In real data I would check whether assignment was random. If not, I would use adjustment methods and show uncertainty intervals.

## Advice boundary

The dashboard uses terms such as education, reminder, and service route. It does not make personal investment recommendations.

## Dashboard

The current dashboard is a self-contained HTML file. In a real team I would connect it to a managed reporting tool and a tested data pipeline.

## Next changes I would make

- Add data validation tests for missing values and outliers.
- Add confidence intervals for offer lift.
- Add segment stability checks by month.
- Add a small Power BI-style mockup or Streamlit version.
- Add more SQL examples for stakeholder questions.
