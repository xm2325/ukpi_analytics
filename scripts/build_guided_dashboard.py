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

GUIDED_PATH = DOCS / "guided_dashboard.html"
INDEX_PATH = DOCS / "index.html"
DASHBOARD_VERSION = "Evidence-led v2.2"


def img_data_uri(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def pp(x: float) -> str:
    return f"{100 * x:.1f} pp"


def require_columns(df: pd.DataFrame, table_name: str, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(
            f"{table_name} is missing required columns {missing}. "
            f"Available columns: {df.columns.tolist()}"
        )


def table_html(df: pd.DataFrame, n: int | None = None) -> str:
    shown = df.head(n) if n is not None else df
    return shown.to_html(index=False, classes="mini", border=0, escape=True)


def main() -> None:
    segments = pd.read_csv(TABLES / "customer_segments.csv")
    profile = pd.read_csv(TABLES / "segment_profile_summary.csv")
    evidence = pd.read_csv(TABLES / "offer_uplift_with_uncertainty.csv")
    quality = pd.read_csv(TABLES / "data_quality_summary.csv")
    diagnostics = pd.read_csv(TABLES / "cluster_diagnostics.csv")
    stability = pd.read_csv(TABLES / "segment_stability.csv")

    require_columns(segments, "customer_segments.csv", ["segment", "customer_id"])
    require_columns(
        profile,
        "segment_profile_summary.csv",
        ["segment", "cash_ratio_mean", "active_days_6m_mean"],
    )
    require_columns(
        evidence,
        "offer_uplift_with_uncertainty.csv",
        [
            "segment",
            "offer_type",
            "n_treatment",
            "n_control",
            "treatment_conversion_rate",
            "control_conversion_rate",
            "absolute_uplift",
            "ci_95_lower",
            "ci_95_upper",
            "evidence_label",
        ],
    )
    require_columns(quality, "data_quality_summary.csv", ["metric", "value", "unit", "status"])
    require_columns(diagnostics, "cluster_diagnostics.csv", ["n_clusters", "silhouette_score", "inertia", "selected"])
    require_columns(stability, "segment_stability.csv", ["comparison_seed", "adjusted_rand_index"])

    n_customers = len(segments)
    n_segments = int(segments["segment"].nunique())
    best = evidence.sort_values("absolute_uplift", ascending=False).iloc[0]
    best_lift = float(best["absolute_uplift"])
    best_lower = float(best["ci_95_lower"])
    best_upper = float(best["ci_95_upper"])
    review_checks = int((quality["status"] != "PASS").sum())

    selected_k = diagnostics.loc[diagnostics["selected"].astype(bool)].iloc[0]
    best_silhouette = diagnostics.sort_values("silhouette_score", ascending=False).iloc[0]
    mean_ari = float(stability["adjusted_rand_index"].mean())
    min_ari = float(stability["adjusted_rand_index"].min())

    segment_size = (
        segments["segment"]
        .value_counts()
        .rename_axis("Segment")
        .reset_index(name="Customers")
    )
    segment_size["Share"] = (segment_size["Customers"] / n_customers).map(pct)

    high_cash = profile.sort_values("cash_ratio_mean", ascending=False).iloc[0]
    low_activity = profile.sort_values("active_days_6m_mean", ascending=True).iloc[0]

    best_by_segment = (
        evidence.sort_values("absolute_uplift", ascending=False)
        .groupby("segment", as_index=False)
        .head(1)
        .copy()
    )
    best_display = best_by_segment[
        [
            "segment",
            "offer_type",
            "n_treatment",
            "n_control",
            "absolute_uplift",
            "ci_95_lower",
            "ci_95_upper",
            "evidence_label",
        ]
    ].copy()
    best_display["offer_type"] = best_display["offer_type"].str.replace("_", " ", regex=False)
    best_display["absolute_uplift"] = best_display["absolute_uplift"].map(pp)
    best_display["95% interval"] = best_by_segment.apply(
        lambda row: f"{pp(float(row['ci_95_lower']))} to {pp(float(row['ci_95_upper']))}",
        axis=1,
    )
    best_display = best_display.drop(columns=["ci_95_lower", "ci_95_upper"])
    best_display = best_display.rename(
        columns={
            "segment": "Segment",
            "offer_type": "Strongest route",
            "n_treatment": "Treatment n",
            "n_control": "Control n",
            "absolute_uplift": "Simulated uplift",
            "evidence_label": "Evidence reading",
        }
    )

    quality_display = quality.copy()
    quality_display["metric"] = quality_display["metric"].str.replace("_", " ", regex=False)
    quality_display["value"] = quality_display.apply(
        lambda row: pct(float(row["value"])) if row["unit"] == "proportion" else f"{float(row['value']):,.0f}",
        axis=1,
    )
    quality_display = quality_display[["metric", "value", "status"]].rename(
        columns={"metric": "Check", "value": "Result", "status": "Status"}
    )

    diagnostics_display = diagnostics.copy()
    diagnostics_display["silhouette_score"] = diagnostics_display["silhouette_score"].map(lambda x: f"{x:.3f}")
    diagnostics_display["inertia"] = diagnostics_display["inertia"].map(lambda x: f"{x:,.0f}")
    diagnostics_display["selected"] = diagnostics_display["selected"].map(lambda x: "Selected" if bool(x) else "")
    diagnostics_display = diagnostics_display.rename(
        columns={
            "n_clusters": "k",
            "silhouette_score": "Silhouette",
            "inertia": "Inertia",
            "selected": "Decision",
        }
    )

    stability_display = stability.copy()
    stability_display["adjusted_rand_index"] = stability_display["adjusted_rand_index"].map(lambda x: f"{x:.3f}")
    stability_display = stability_display[["comparison_seed", "adjusted_rand_index"]].rename(
        columns={"comparison_seed": "Alternative seed", "adjusted_rand_index": "Adjusted Rand index"}
    )

    fig_map = {
        "Segment size": FIGS / "01_segment_size_journal_palette.png",
        "Need map": FIGS / "02_segment_need_map.png",
        "Recommended offer lift": FIGS / "03_recommended_offer_lift.png",
        "Offer uplift heatmap": FIGS / "04_offer_uplift_heatmap.png",
        "Treatment-control conversion": FIGS / "05_treatment_control_conversion.png",
        "Segment profile comparison": FIGS / "06_segment_profile_comparison.png",
        "Offer uncertainty": FIGS / "07_recommended_offer_uncertainty.png",
        "Cluster diagnostic": FIGS / "08_cluster_count_diagnostic.png",
    }
    missing_figures = [str(path) for path in fig_map.values() if not path.exists()]
    if missing_figures:
        raise FileNotFoundError("Missing figure files: " + ", ".join(missing_figures))

    css = """
    :root{--ink:#111827;--muted:#4B5563;--line:#E5E7EB;--bg:#F8FAFC;--card:#FFFFFF;--blue:#0072B2;--orange:#D55E00;--green:#009E73;--purple:#CC79A7}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.55}
    header{background:#fff;border-bottom:1px solid var(--line);padding:34px 44px 24px}main{max-width:1180px;margin:auto;padding:24px}
    h1{margin:0 0 8px;font-size:30px}h2{margin:0 0 12px;font-size:22px}h3{margin:8px 0;font-size:17px}.subtitle{color:var(--muted);max-width:920px}
    .version{display:inline-block;margin-top:10px;padding:4px 9px;border-radius:999px;background:#111827;color:#fff;font-size:12px;font-weight:700}
    .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px;margin:18px 0;box-shadow:0 1px 2px rgba(0,0,0,.035)}
    .answer{border-left:6px solid var(--blue)}.safe{border-left:6px solid var(--green);background:#F0FDF4}.warn{border-left:6px solid var(--orange);background:#FFF7ED}
    .grid4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
    .kpi{background:#fff;border:1px solid var(--line);border-radius:12px;padding:15px}.label{font-size:13px;color:var(--muted)}.value{font-size:24px;font-weight:700;margin-top:4px}.subvalue{font-size:12px;color:var(--muted);margin-top:5px}
    .step{display:inline-block;background:#EFF6FF;color:#1D4ED8;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:700;margin-bottom:8px}
    .flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.flow div{background:#F9FAFB;border:1px solid var(--line);border-radius:10px;padding:12px;font-size:13px}.flow b{display:block;margin-bottom:4px}
    figure{margin:0}.chart{width:100%;border:1px solid var(--line);border-radius:12px;background:white;padding:10px}.chart img{width:100%;display:block}
    .explain{background:#F9FAFB;border:1px solid var(--line);border-radius:12px;padding:14px}.explain ul{margin:8px 0 0 20px;padding:0}.explain li{margin:5px 0}
    .mini{width:100%;border-collapse:collapse;font-size:12.5px}.mini th,.mini td{border-bottom:1px solid var(--line);padding:7px;text-align:left;vertical-align:top}.mini th{background:#F9FAFB;position:sticky;top:0}
    .table-wrap{overflow-x:auto}.muted{color:var(--muted)}.callout{background:#FFF7ED;border-left:5px solid var(--orange);padding:12px 14px;border-radius:8px}
    @media(max-width:900px){.grid2,.grid4,.flow{grid-template-columns:1fr}header{padding:28px 22px}main{padding:16px}}
    """

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UKPI Analytics — Evidence-led Dashboard</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>UKPI client segmentation and offer analytics</h1>
  <p class="subtitle">Synthetic-data portfolio dashboard. The page moves from the business question to the evidence, uncertainty, operational interpretation, and limits.</p>
  <span class="version">{DASHBOARD_VERSION}</span>
</header>
<main>
  <section class="card answer">
    <span class="step">Answer first</span>
    <h2>One communication plan is not enough for the simulated investor book.</h2>
    <p>The workflow separates <b>{n_customers:,}</b> synthetic customers into <b>{n_segments}</b> interpretable segments. The strongest simulated treatment-control result is <b>{pp(best_lift)}</b> for <b>{str(best['offer_type']).replace('_', ' ')}</b> in <b>{best['segment']}</b>.</p>
    <p class="muted">Its approximate 95% interval is <b>{pp(best_lower)} to {pp(best_upper)}</b>. This is a synthetic experiment result, not evidence of real customer impact.</p>
  </section>

  <section class="grid4">
    <div class="kpi"><div class="label">Synthetic customers</div><div class="value">{n_customers:,}</div><div class="subvalue">One customer-level feature mart</div></div>
    <div class="kpi"><div class="label">Segments retained</div><div class="value">{n_segments}</div><div class="subvalue">Interpretability trade-off</div></div>
    <div class="kpi"><div class="label">Mean stability ARI</div><div class="value">{mean_ari:.3f}</div><div class="subvalue">Minimum {min_ari:.3f} across five seeds</div></div>
    <div class="kpi"><div class="label">Quality checks needing review</div><div class="value">{review_checks}</div><div class="subvalue">Out of {len(quality)} automated checks</div></div>
  </section>

  <section class="card">
    <span class="step">Decision path</span>
    <div class="flow">
      <div><b>1. Who is in the book?</b>Size and profile the customer segments.</div>
      <div><b>2. Why five groups?</b>Compare cluster separation and multi-seed stability.</div>
      <div><b>3. What appears to work?</b>Estimate treatment-control uplift by segment and route.</div>
      <div><b>4. How certain is it?</b>Show sample sizes, uncertainty intervals, quality checks, and limits.</div>
    </div>
  </section>

  <section class="card">
    <span class="step">Model choice</span><h2>Why retain five segments?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Cluster-count diagnostic" src="{img_data_uri(fig_map['Cluster diagnostic'])}"></figure>
      <div class="explain">
        <h3>Honest interpretation</h3>
        <p>The highest silhouette score is at <b>k={int(best_silhouette['n_clusters'])}</b> ({float(best_silhouette['silhouette_score']):.3f}), while the retained five-cluster solution has a lower score of <b>{float(selected_k['silhouette_score']):.3f}</b>.</p>
        <p class="callout"><b>Therefore k=5 is not presented as mathematically optimal.</b> It is retained as a business-facing trade-off: more useful service groups than k=2, while remaining highly stable across alternative random seeds.</p>
        <p>Mean adjusted Rand index: <b>{mean_ari:.3f}</b>; minimum: <b>{min_ari:.3f}</b>.</p>
      </div>
    </div>
    <div class="grid2">
      <div class="table-wrap">{table_html(diagnostics_display)}</div>
      <div class="table-wrap">{table_html(stability_display)}</div>
    </div>
  </section>

  <section class="card">
    <span class="step">1</span><h2>How many customers are in each segment?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Segment size chart" src="{img_data_uri(fig_map['Segment size'])}"></figure>
      <div class="explain"><h3>Read this first</h3><ul><li>Segment size sets the operational scale.</li><li>High uplift in a small group may have less total impact than moderate uplift in a large group.</li><li>The table gives both count and share.</li></ul><div class="table-wrap">{table_html(segment_size)}</div></div>
    </div>
  </section>

  <section class="card">
    <span class="step">2</span><h2>What makes the segments meaningfully different?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Segment need map" src="{img_data_uri(fig_map['Need map'])}"></figure>
      <div class="explain"><h3>Current interpretation</h3><p><b>Highest cash-ratio segment:</b> {high_cash['segment']} ({pct(float(high_cash['cash_ratio_mean']))}).</p><p><b>Lowest digital-activity segment:</b> {low_activity['segment']} ({float(low_activity['active_days_6m_mean']):.1f} active days over six months).</p><ul><li>Bubble size reflects mean AUM.</li><li>Position reflects service needs, not suitability or risk advice.</li></ul></div>
    </div>
  </section>

  <section class="card">
    <span class="step">3</span><h2>Which communication route appears strongest by segment?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Recommended offer lift" src="{img_data_uri(fig_map['Recommended offer lift'])}"></figure>
      <div class="explain"><h3>What this chart can support</h3><ul><li>Prioritising which education or reminder route to test further.</li><li>Comparing segment-level response rather than applying one message to everyone.</li><li>It cannot support a personal product recommendation.</li></ul></div>
    </div>
  </section>

  <section class="card">
    <span class="step">4</span><h2>How uncertain are the apparent best results?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Offer uplift uncertainty" src="{img_data_uri(fig_map['Offer uncertainty'])}"></figure>
      <div class="explain"><h3>How to read it</h3><ul><li>Dots are simulated uplift estimates.</li><li>Horizontal intervals show approximate 95% uncertainty.</li><li>Intervals crossing zero should be treated as directional rather than conclusive.</li><li>Each label also shows the combined treatment and control sample size.</li></ul></div>
    </div>
    <div class="table-wrap">{table_html(best_display)}</div>
  </section>

  <section class="card">
    <span class="step">5</span><h2>Why not use the same route for every segment?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Offer uplift heatmap" src="{img_data_uri(fig_map['Offer uplift heatmap'])}"></figure>
      <div class="explain"><h3>Interpretation</h3><ul><li>Rows show that segment response patterns differ.</li><li>Columns show that no route dominates in every group.</li><li>The heatmap is a prioritisation aid; the uncertainty view above is needed before making stronger claims.</li></ul></div>
    </div>
  </section>

  <section class="card">
    <span class="step">6</span><h2>Is the result based on a visible treatment-control comparison?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Treatment-control conversion" src="{img_data_uri(fig_map['Treatment-control conversion'])}"></figure>
      <div class="explain"><h3>Why this matters</h3><ul><li>It separates baseline conversion from the treatment result.</li><li>The evidence table records treatment and control counts, conversions, rates, uplift, and intervals.</li><li>With real data, further checks would include randomisation integrity, pre-period balance, and multiple-testing control.</li></ul></div>
    </div>
  </section>

  <section class="card">
    <span class="step">7</span><h2>Do the segment names match measurable profiles?</h2>
    <div class="grid2">
      <figure class="chart"><img alt="Segment profile comparison" src="{img_data_uri(fig_map['Segment profile comparison'])}"></figure>
      <div class="explain"><h3>Interpretation</h3><ul><li>Profile measures anchor the segment names in observed synthetic features.</li><li>This guards against labels that sound plausible but are not supported by the data.</li><li>A production version would also test stability across time, not only across random seeds.</li></ul></div>
    </div>
  </section>

  <section class="card">
    <span class="step">Automated checks</span><h2>Was the generated dataset and experiment output internally consistent?</h2>
    <p class="muted">These checks run from code and are saved to <code>outputs/tables/data_quality_summary.csv</code>.</p>
    <div class="table-wrap">{table_html(quality_display)}</div>
  </section>

  <section class="card safe">
    <span class="step">Boundary</span><h2>What I would and would not claim</h2>
    <p><b>I would claim:</b> the repository demonstrates a reproducible workflow connecting synthetic customer data, segmentation diagnostics, campaign comparisons, uncertainty, SQL checks, automated validation, and stakeholder reporting.</p>
    <p><b>I would not claim:</b> that the simulated uplift represents real customer behaviour, that k=5 is uniquely optimal, that the segments establish suitability, or that the dashboard gives regulated financial advice.</p>
  </section>

  <section class="card warn">
    <span class="step">Production upgrades</span><h2>What I would add with real data</h2>
    <p>Time-based segment stability, pre-treatment balance, multiple-testing adjustment, robust experimental design, dashboard freshness monitoring, privacy controls, and documented human approval before campaign use.</p>
  </section>
</main>
</body>
</html>
"""

    GUIDED_PATH.write_text(html, encoding="utf-8")
    INDEX_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {GUIDED_PATH}")
    print(f"Wrote {INDEX_PATH}")


if __name__ == "__main__":
    main()
