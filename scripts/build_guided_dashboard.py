from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TABLES = OUT / "tables"
FIGS = OUT / "figures"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

DASHBOARD_PATH = DOCS / "guided_dashboard.html"


def img_data_uri(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def money(x: float) -> str:
    return f"£{x:,.0f}"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def pp(x: float) -> str:
    return f"{100 * x:.1f} pp"


def top_rows_html(df: pd.DataFrame, n: int = 5) -> str:
    return df.head(n).to_html(index=False, classes="mini", border=0)


def main() -> None:
    segments = pd.read_csv(TABLES / "customer_segments.csv")
    recs = pd.read_csv(TABLES / "segment_offer_recommendations.csv")
    uplift = pd.read_csv(TABLES / "offer_uplift_by_segment.csv")
    profile = pd.read_csv(TABLES / "segment_profile_summary.csv")

    n_customers = len(segments)
    n_segments = segments["segment"].nunique()
    best = uplift.sort_values("absolute_uplift", ascending=False).iloc[0]
    best_segment = best["segment"]
    best_offer = best["offer_type"]
    best_lift = float(best["absolute_uplift"])

    segment_size = segments["segment"].value_counts().rename_axis("segment").reset_index(name="customers")
    segment_size["share"] = segment_size["customers"] / n_customers

    high_cash = profile.sort_values("mean_cash_ratio", ascending=False).iloc[0]
    low_activity = profile.sort_values("mean_active_days_6m", ascending=True).iloc[0]

    fig_map = {
        "Segment size": FIGS / "01_segment_size_journal_palette.png",
        "Need map": FIGS / "02_segment_need_map.png",
        "Recommended offer lift": FIGS / "03_recommended_offer_lift.png",
        "Offer uplift heatmap": FIGS / "04_offer_uplift_heatmap.png",
        "Treatment-control conversion": FIGS / "05_treatment_control_conversion.png",
        "Segment profile comparison": FIGS / "06_segment_profile_comparison.png",
    }

    missing = [str(p) for p in fig_map.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing figure files: " + ", ".join(missing))

    css = """
    :root{--ink:#111827;--muted:#4B5563;--line:#E5E7EB;--bg:#F8FAFC;--card:#FFFFFF;--blue:#0072B2;--orange:#D55E00;--green:#009E73;--purple:#CC79A7;--yellow:#E69F00}
    body{margin:0;background:var(--bg);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.55}
    header{background:#fff;border-bottom:1px solid var(--line);padding:34px 44px 24px}
    main{max-width:1180px;margin:auto;padding:24px}
    h1{margin:0 0 8px;font-size:30px} h2{margin:0 0 12px;font-size:22px} h3{margin:8px 0 8px;font-size:17px}
    .subtitle{color:var(--muted);max-width:900px}
    .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px;margin:18px 0;box-shadow:0 1px 2px rgba(0,0,0,.035)}
    .answer{border-left:6px solid var(--blue)} .safe{border-left:6px solid var(--green);background:#F0FDF4}.warn{border-left:6px solid var(--orange);background:#FFF7ED}
    .grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
    .kpi{background:#fff;border:1px solid var(--line);border-radius:12px;padding:15px}.label{font-size:13px;color:var(--muted)}.value{font-size:25px;font-weight:700;margin-top:4px}
    .step{display:inline-block;background:#EFF6FF;color:#1D4ED8;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:700;margin-bottom:8px}
    figure{margin:0}.chart{width:100%;border:1px solid var(--line);border-radius:12px;background:white;padding:10px;box-sizing:border-box}.chart img{width:100%;display:block}
    .explain{background:#F9FAFB;border:1px solid var(--line);border-radius:12px;padding:14px}.explain ul{margin:8px 0 0 20px;padding:0}.explain li{margin:5px 0}
    .mini{width:100%;border-collapse:collapse;font-size:13px}.mini th,.mini td{border-bottom:1px solid var(--line);padding:7px;text-align:left}.mini th{background:#F9FAFB}
    .pill{display:inline-block;border-radius:999px;padding:4px 9px;margin:3px;background:#EEF2FF;color:#3730A3;font-size:12px}.muted{color:var(--muted)}
    @media(max-width:900px){.grid2,.grid3{grid-template-columns:1fr}header{padding:28px 22px}main{padding:16px}}
    """

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>Guided UKPI Analytics Dashboard</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>UKPI client segmentation and offer analytics</h1>
  <p class=\"subtitle\">Synthetic-data portfolio dashboard. The page is designed to make the analysis easy to inspect: each section states the business question, the evidence, how to read the figure, and what the output should not be used for.</p>
</header>
<main>
  <section class=\"card answer\">
    <span class=\"step\">Answer first</span>
    <h2>One communication plan is not enough for the simulated investor book.</h2>
    <p>The workflow creates <b>{n_segments}</b> interpretable customer segments from <b>{n_customers:,}</b> synthetic customers. The strongest simulated segment-offer result is <b>{pp(best_lift)}</b> for <b>{best_offer}</b> in <b>{best_segment}</b>.</p>
    <p class=\"muted\">The output supports service design and education routing. It does not recommend a fund, portfolio, risk level, or personal investment action.</p>
  </section>

  <section class=\"grid3\">
    <div class=\"kpi\"><div class=\"label\">Synthetic customers</div><div class=\"value\">{n_customers:,}</div></div>
    <div class=\"kpi\"><div class=\"label\">Interpretable segments</div><div class=\"value\">{n_segments}</div></div>
    <div class=\"kpi\"><div class=\"label\">Best simulated lift</div><div class=\"value\">{pp(best_lift)}</div></div>
  </section>

  <section class=\"card\">
    <span class=\"step\">1</span>
    <h2>Business question: how many customers are in each segment?</h2>
    <div class=\"grid2\">
      <figure class=\"chart\"><img alt=\"Segment size chart\" src=\"{img_data_uri(fig_map['Segment size'])}\"></figure>
      <div class=\"explain\">
        <h3>How to read it</h3>
        <ul>
          <li>Start with segment size before interpreting offer performance.</li>
          <li>A small segment can show high lift but still have limited operational impact.</li>
          <li>A large segment with moderate lift may be more useful for a scaled campaign.</li>
        </ul>
        <h3>Current snapshot</h3>
        {top_rows_html(segment_size, 5)}
      </div>
    </div>
  </section>

  <section class=\"card\">
    <span class=\"step\">2</span>
    <h2>Business question: which segments have different needs?</h2>
    <div class=\"grid2\">
      <figure class=\"chart\"><img alt=\"Segment need map\" src=\"{img_data_uri(fig_map['Need map'])}\"></figure>
      <div class=\"explain\">
        <h3>How to read it</h3>
        <ul>
          <li>The x-axis separates more and less digitally active customers.</li>
          <li>The y-axis separates higher and lower cash-ratio groups.</li>
          <li>This makes the segment story visible before looking at campaigns.</li>
        </ul>
        <h3>Current snapshot</h3>
        <p><b>Highest cash-ratio segment:</b> {high_cash['segment']} ({pct(float(high_cash['mean_cash_ratio']))}).</p>
        <p><b>Lowest digital-activity segment:</b> {low_activity['segment']} ({float(low_activity['mean_active_days_6m']):.1f} active days over six months).</p>
      </div>
    </div>
  </section>

  <section class=\"card\">
    <span class=\"step\">3</span>
    <h2>Business question: which communication route appears strongest by segment?</h2>
    <div class=\"grid2\">
      <figure class=\"chart\"><img alt=\"Recommended offer lift\" src=\"{img_data_uri(fig_map['Recommended offer lift'])}\"></figure>
      <div class=\"explain\">
        <h3>How to read it</h3>
        <ul>
          <li>Each bar is the strongest simulated offer route for one segment.</li>
          <li>The output is segment-level evidence, not a personal recommendation.</li>
          <li>This is the chart I would show first when discussing campaign prioritisation.</li>
        </ul>
        {top_rows_html(recs.sort_values('absolute_uplift', ascending=False)[['segment','recommended_offer','absolute_uplift']], 5)}
      </div>
    </div>
  </section>

  <section class=\"card\">
    <span class=\"step\">4</span>
    <h2>Business question: why not use the same offer for everyone?</h2>
    <div class=\"grid2\">
      <figure class=\"chart\"><img alt=\"Offer uplift heatmap\" src=\"{img_data_uri(fig_map['Offer uplift heatmap'])}\"></figure>
      <div class=\"explain\">
        <h3>How to read it</h3>
        <ul>
          <li>Compare rows to see that segments respond differently.</li>
          <li>Compare columns to see that one offer does not dominate everywhere.</li>
          <li>This figure supports targeted communication rather than one-size-fits-all messaging.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class=\"card\">
    <span class=\"step\">5</span>
    <h2>Business question: is the uplift coming from a treatment-control comparison?</h2>
    <div class=\"grid2\">
      <figure class=\"chart\"><img alt=\"Treatment-control conversion\" src=\"{img_data_uri(fig_map['Treatment-control conversion'])}\"></figure>
      <div class=\"explain\">
        <h3>How to read it</h3>
        <ul>
          <li>The chart separates treatment and control conversion rates.</li>
          <li>It makes the simulated experiment logic visible to a non-technical reviewer.</li>
          <li>In real data, I would add confidence intervals and check assignment bias.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class=\"card\">
    <span class=\"step\">6</span>
    <h2>Business question: what makes the segments different?</h2>
    <div class=\"grid2\">
      <figure class=\"chart\"><img alt=\"Segment profile comparison\" src=\"{img_data_uri(fig_map['Segment profile comparison'])}\"></figure>
      <div class=\"explain\">
        <h3>How to read it</h3>
        <ul>
          <li>This chart links the segment labels back to measurable features.</li>
          <li>It helps explain why a segment is described as cash-heavy, engaged, or dormant.</li>
          <li>It is a check against creating labels that sound plausible but do not match the data.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class=\"card safe\">
    <span class=\"step\">Boundary</span>
    <h2>What I would and would not claim</h2>
    <p><b>I would claim:</b> the workflow shows how customer-level features, segmentation, offer lift analysis, SQL checks, and a dashboard can support service analytics.</p>
    <p><b>I would not claim:</b> that this is real customer behaviour, regulated financial advice, or a production campaign decisioning system.</p>
  </section>

  <section class=\"card warn\">
    <span class=\"step\">Next production checks</span>
    <h2>What I would add with real data</h2>
    <p><span class=\"pill\">data quality checks</span><span class=\"pill\">confidence intervals</span><span class=\"pill\">segment stability</span><span class=\"pill\">assignment-bias checks</span><span class=\"pill\">dashboard freshness checks</span></p>
  </section>
</main>
</body>
</html>
"""
    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
