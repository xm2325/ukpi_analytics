# Interview talk track

## 60 seconds

I built a synthetic UK personal investor analytics project. The goal was to turn customer, account, holdings, transaction, web, and campaign data into a customer-level feature mart, then use it for segmentation, offer analysis, and dashboard reporting.

The output is a chart-first dashboard and a customer-level selector. It shows that a retail investment platform should not use the same communication plan for all customers. For example, cash-heavy customers may need neutral cash education, while pension builders may be more relevant for SIPP reminders.

I kept a clear boundary: this is not a fund recommendation or personal advice project. It supports service design, reporting, and communication routing.

## 3 minutes

I started by creating synthetic raw tables: customers, accounts, holdings, transactions, web events, and campaign events. I then built a customer-level feature table with one row per customer. The key features were AUM, cash ratio, ISA/SIPP/GIA ownership, contribution behaviour, and active web/app days.

I used clustering to form five customer groups and then renamed them based on their profile. The point was not to build the most complex model; it was to create groups a business stakeholder can understand and act on.

After segmentation, I looked at simulated treatment and control groups for different communication routes. For each segment and offer type, I calculated conversion lift. That gave a practical answer to the question: which route appears to work better for each group?

The dashboard uses figures before tables. It starts with the main answer, then shows segment size, segment needs, offer lift, treatment-control conversion, and segment profiles. The dynamic customer view shows how the same mart can be used for a single-customer service view.

## Questions I expect

### Why synthetic data?

Because I wanted to show the workflow without using private customer data. The synthetic data also lets me design realistic patterns, such as high cash, low engagement, pension ownership, and monthly investing.

### Why KMeans?

It is a simple baseline that is easy to explain. For this type of role, interpretability and stakeholder communication matter. A more complex model would only help if it improved stability or business use.

### How would I improve it in production?

I would add proper data quality checks, dashboard freshness checks, confidence intervals for offer lift, monitoring for segment drift, and tests for campaign assignment bias.

### What is the advice boundary?

The project can support neutral education and service routing. It should not recommend a fund, risk level, or personal investment decision.
