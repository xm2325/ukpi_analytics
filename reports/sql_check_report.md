# SQL check report

Loaded tables:

- `customer_segments`: 2,500 rows
- `campaign_events_with_segments`: 5,015 rows
- `segment_profile_summary`: 5 rows
- `offer_uplift_by_segment`: 20 rows
- `segment_offer_recommendations`: 5 rows
- `executive_metrics`: AUM p90 = £175,725

## Query 1

Rows returned: 5
Output: `outputs/tables/sql_checks/query_01_select_segment_count_as_n_customers_avg.csv`

| segment                                 |   n_customers |   mean_cash_ratio |   mean_aum |
|:----------------------------------------|--------------:|------------------:|-----------:|
| Cash-heavy cautious investors           |           407 |          0.526664 |    68723.6 |
| High-value engaged investors            |           457 |          0.316495 |   121841   |
| Pension builders approaching retirement |           471 |          0.235368 |   113277   |
| Emerging monthly investors              |           614 |          0.214433 |    61583.5 |
| Low-engagement or dormant investors     |           551 |          0.205421 |    52942.7 |

## Query 2

Rows returned: 1
Output: `outputs/tables/sql_checks/query_02_select_customer_id_segment_aum_cash_ratio_active_days_6m.csv`

| customer_id   | segment                                 |    aum |   cash_ratio |   active_days_6m |
|:--------------|:----------------------------------------|-------:|-------------:|-----------------:|
| C002362       | Pension builders approaching retirement | 321710 |      0.14517 |                1 |

## Query 3

Rows returned: 5
Output: `outputs/tables/sql_checks/query_03_with_ranked_as_select_segment_offer_type.csv`

| segment                                 | offer_type                |   treatment_conversion_rate |   control_conversion_rate |   absolute_uplift |   rn |
|:----------------------------------------|:--------------------------|----------------------------:|--------------------------:|------------------:|-----:|
| Cash-heavy cautious investors           | CASH_TO_INVEST_EDUCATION  |                    0.447154 |                 0.195876  |          0.251278 |    1 |
| Pension builders approaching retirement | MANAGED_SERVICE_EDUCATION |                    0.241071 |                 0.0982143 |          0.142857 |    1 |
| High-value engaged investors            | CASH_TO_INVEST_EDUCATION  |                    0.316667 |                 0.192982  |          0.123684 |    1 |
| Emerging monthly investors              | CASH_TO_INVEST_EDUCATION  |                    0.236842 |                 0.120253  |          0.116589 |    1 |
| Low-engagement or dormant investors     | ISA_ALLOWANCE_REMINDER    |                    0.231343 |                 0.119403  |          0.11194  |    1 |

## Query 4

Rows returned: 100
Output: `outputs/tables/sql_checks/query_04_select_customer_id_segment_aum_cash_balance_cash_ratio.csv`

| customer_id   | segment                                 |    aum |   cash_balance |   cash_ratio |   active_days_6m |
|:--------------|:----------------------------------------|-------:|---------------:|-------------:|-----------------:|
| C000936       | High-value engaged investors            | 467036 |         347112 |     0.743222 |               35 |
| C000408       | High-value engaged investors            | 581301 |         282532 |     0.486034 |               50 |
| C001813       | Pension builders approaching retirement | 617344 |         265064 |     0.429363 |               26 |
| C000768       | Cash-heavy cautious investors           | 406812 |         263466 |     0.647637 |               39 |
| C000403       | Cash-heavy cautious investors           | 436097 |         230094 |     0.527622 |               40 |

## Query 5

Rows returned: 6
Output: `outputs/tables/sql_checks/query_05_select_customer_id_segment_age_aum_contribution_18m.csv`

| customer_id   | segment                                 |   age |      aum |   contribution_18m |   active_days_6m |
|:--------------|:----------------------------------------|------:|---------:|-------------------:|-----------------:|
| C000550       | Pension builders approaching retirement |    75 | 181683   |             476.65 |               37 |
| C001541       | Pension builders approaching retirement |    74 | 171019   |             428.57 |               16 |
| C001557       | Pension builders approaching retirement |    71 | 103426   |             232.75 |               12 |
| C000333       | Pension builders approaching retirement |    67 |  26661.2 |             480.35 |               42 |
| C002178       | Pension builders approaching retirement |    55 |  83132   |             450.46 |               29 |

## Query 6

Rows returned: 8
Output: `outputs/tables/sql_checks/query_06_select_offer_type_assigned_group_count_as_n_events.csv`

| offer_type                | assigned_group   |   n_events |   conversion_rate |
|:--------------------------|:-----------------|-----------:|------------------:|
| CASH_TO_INVEST_EDUCATION  | control          |        624 |          0.149038 |
| CASH_TO_INVEST_EDUCATION  | treatment        |        668 |          0.261976 |
| ISA_ALLOWANCE_REMINDER    | control          |        613 |          0.14845  |
| ISA_ALLOWANCE_REMINDER    | treatment        |        631 |          0.247227 |
| MANAGED_SERVICE_EDUCATION | control          |        604 |          0.114238 |
