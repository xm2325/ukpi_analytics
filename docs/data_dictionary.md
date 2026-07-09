# Data dictionary

All tables are synthetic. The fields are designed to look like the type of data a retail investment analytics team might use.

## `customers.csv`

| Field | Meaning | Why I used it |
|---|---|---|
| `customer_id` | Synthetic customer key | Joins all tables |
| `age` | Customer age | Helps separate younger monthly investors from pension builders |
| `region` | UK region label | Useful for basic reporting and dashboard filters |
| `acquisition_channel` | Source channel | Useful for growth and campaign analysis |
| `tenure_months` | Customer tenure | Helps separate new and mature customers |
| `digital_score` | Synthetic web/app engagement score | Used to model digital behaviour |
| `risk_appetite_proxy` | Synthetic risk proxy | Kept as a proxy only; not a suitability score |

## `accounts.csv`

| Field | Meaning | Why I used it |
|---|---|---|
| `account_id` | Synthetic account key | Joins accounts to holdings and transactions |
| `customer_id` | Customer key | Links accounts to the customer view |
| `account_type` | ISA, SIPP, or GIA | Supports ISA and SIPP reminder use cases |
| `opened_date` | Synthetic account open date | Useful for tenure and lifecycle questions |

## `holdings.csv`

| Field | Meaning | Why I used it |
|---|---|---|
| `asset_class` | Cash, equity, bond, mixed fund, or other class | Used to calculate broad allocation features |
| `market_value` | Synthetic holding value | Used for AUM and cash ratio |
| `valuation_date` | Snapshot date | Keeps the holding snapshot explicit |

## `transactions.csv`

| Field | Meaning | Why I used it |
|---|---|---|
| `transaction_type` | Contribution or withdrawal | Builds customer contribution behaviour |
| `amount` | Synthetic transaction value | Used for 18-month contribution metrics |
| `transaction_date` | Synthetic transaction date | Used for recent activity features |

## `web_events.csv`

| Field | Meaning | Why I used it |
|---|---|---|
| `event_type` | Login, view, education, account action, or support event | Measures digital activity |
| `event_date` | Synthetic event date | Used for active days over six months |

## `campaign_events.csv`

| Field | Meaning | Why I used it |
|---|---|---|
| `offer_type` | ISA reminder, SIPP reminder, cash education, managed-service education | Tests segment-specific communication routes |
| `assigned_group` | Treatment or control | Allows treatment-control lift calculation |
| `converted` | Synthetic conversion flag | Outcome for offer analysis |

## Feature mart fields

| Field | Meaning |
|---|---|
| `aum` | Sum of customer holding values |
| `cash_balance` | Sum of cash holdings |
| `cash_ratio` | Cash balance divided by AUM |
| `contribution_18m` | Contributions over 18 months |
| `active_days_6m` | Number of active web/app days over six months |
| `has_isa` | Whether customer has an ISA account |
| `has_sipp` | Whether customer has a SIPP account |
| `has_gia` | Whether customer has a GIA account |

## Notes

The project treats these fields as service analytics features. They should not be read as a full suitability or advice framework.
