# Project story

I made this project to mirror the kind of analysis a UK personal investor data team might need when the business is launching new offers, improving reporting, and trying to use customer data in a careful way.

The starting point is a common business problem: the platform has many customers, but the customers do not behave in the same way. Some have high assets and log in often. Some have a high cash balance and may need education before they make any change. Some are younger monthly investors. Some are older and more likely to have a pension account. Some are quiet and may need a lighter communication route.

I built synthetic data for those patterns. The raw data are split into customers, accounts, holdings, transactions, web events, and campaign events. I then build a customer-level mart, because most dashboard and segmentation questions need one row per customer with the key features already prepared.

The main features are assets under administration, cash ratio, account types, contribution behaviour, and recent digital activity. These features are not meant to give personal advice. They are used to understand broad service needs and communication routes.

After building the feature mart, I run a five-segment clustering model. I then rename the clusters using the segment profiles rather than leaving them as cluster 0, cluster 1, and so on. The segment names are meant to be readable by a business user:

- high-value engaged investors;
- cash-heavy cautious investors;
- emerging monthly investors;
- pension builders approaching retirement;
- low-engagement or dormant investors.

The next part is offer analysis. I simulate treatment and control groups for neutral education and reminder routes, such as ISA allowance reminders, SIPP contribution reminders, cash-to-invest education, and managed-service education. For each segment and offer, I calculate treatment conversion, control conversion, and absolute lift.

The dashboard is built around the answer first. It does not start with tables. It starts by saying that one communication plan is not enough, then shows the figures that support the point. The customer-level selector is included to show how the same mart can support a different view: not only a segment report, but also a profile page for a single customer.

The most important design rule is the safety boundary. The project can say that a customer group may be suitable for neutral education or a reminder. It should not say that a customer should buy a fund, change risk level, or move cash into investments. That is why the project uses language such as education, reminder, and service route rather than recommendation.
