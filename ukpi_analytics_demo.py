from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

OUT = Path("outputs")
FIG = OUT / "figures"
TAB = OUT / "tables"
REP = Path("reports")
for p in [FIG, TAB, REP]:
    p.mkdir(parents=True, exist_ok=True)

SEGMENT_COLORS = {
    "High-value engaged investors": "#0072B2",
    "Cash-heavy cautious investors": "#D55E00",
    "Emerging monthly investors": "#009E73",
    "Pension builders approaching retirement": "#CC79A7",
    "Low-engagement or dormant investors": "#E69F00",
}
OFFER_COLORS = {
    "ISA_ALLOWANCE_REMINDER": "#0072B2",
    "SIPP_CONTRIBUTION_REMINDER": "#CC79A7",
    "CASH_TO_INVEST_EDUCATION": "#009E73",
    "MANAGED_SERVICE_EDUCATION": "#D55E00",
}
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})


def money(x: float) -> str:
    return f"£{x:,.0f}"


def pct(x: float) -> str:
    return f"{100*x:.1f}%"


def save_fig(name: str) -> Path:
    path = FIG / name
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    return path


def make_data(n: int = 2500, seed: int = 20260709) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    age = rng.integers(22, 76, n)
    digital = rng.beta(2.2, 2.0, n)
    risk = rng.beta(2.0, 2.2, n)
    has_isa = rng.binomial(1, 0.78, n)
    has_sipp = rng.binomial(1, np.clip((age - 25) / 65, 0.12, 0.78))
    has_gia = rng.binomial(1, 0.36, n)
    aum = rng.lognormal(10.55, 0.85, n) * (1 + 0.9 * has_sipp + 0.45 * has_gia)
    cash_ratio = np.clip(rng.beta(2.0, 6.0, n) + rng.binomial(1, 0.18, n) * rng.uniform(0.12, 0.30, n), 0.02, 0.82)
    contrib = np.clip(rng.gamma(2.4, 1150, n) * (0.5 + digital) * (0.7 + has_isa + 0.6 * has_sipp), 0, None)
    active = np.clip(rng.normal(18 + 34 * digital, 8, n), 0, 120)
    regions = rng.choice(["North West", "London", "South East", "Scotland", "Wales", "East Midlands", "Yorkshire"], n)
    df = pd.DataFrame({
        "customer_id": [f"C{i:06d}" for i in range(1, n + 1)],
        "age": age,
        "region": regions,
        "digital_score": digital,
        "risk_appetite_proxy": risk,
        "has_isa": has_isa,
        "has_sipp": has_sipp,
        "has_gia": has_gia,
        "aum": aum.round(2),
        "cash_ratio": cash_ratio,
        "cash_balance": (aum * cash_ratio).round(2),
        "contribution_18m": contrib.round(2),
        "active_days_6m": active.round(0),
    })
    return df


def segment(df: pd.DataFrame) -> pd.DataFrame:
    features = df[["age", "aum", "cash_ratio", "contribution_18m", "active_days_6m", "has_sipp"]].copy()
    features["aum"] = np.log1p(features["aum"])
    features["contribution_18m"] = np.log1p(features["contribution_18m"])
    x = StandardScaler().fit_transform(features)
    df = df.copy()
    df["cluster"] = KMeans(n_clusters=5, random_state=20260709, n_init=25).fit_predict(x)
    prof = df.groupby("cluster").agg(
        age=("age", "mean"),
        aum=("aum", "mean"),
        cash=("cash_ratio", "mean"),
        contribution_18m=("contribution_18m", "mean"),
        active=("active_days_6m", "mean"),
        sipp=("has_sipp", "mean"),
        n=("customer_id", "size"),
    )
    names = {}
    names[prof["aum"].idxmax()] = "High-value engaged investors"
    names[prof.drop(index=list(names.keys()))["cash"].idxmax()] = "Cash-heavy cautious investors"
    names[prof.drop(index=list(names.keys()))["age"].idxmax()] = "Pension builders approaching retirement"
    names[prof.drop(index=list(names.keys()))["contribution_18m"].idxmax()] = "Emerging monthly investors"
    for c in prof.index:
        names.setdefault(c, "Low-engagement or dormant investors")
    df["segment"] = df["cluster"].map(names)
    return df


def simulate_campaigns(df: pd.DataFrame, seed: int = 20260710) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    offers = list(OFFER_COLORS)
    rows = []
    for _, r in df.iterrows():
        chosen = rng.choice(offers, size=rng.integers(1, 4), replace=False)
        for offer in chosen:
            treatment = rng.binomial(1, 0.52)
            base = -3.1 + 0.9 * r.digital_score + 0.35 * np.log1p(r.aum) / 12
            fit = 0.0
            if offer == "ISA_ALLOWANCE_REMINDER":
                fit += 0.55 * r.has_isa + 0.25 * (r.cash_ratio > 0.20)
            if offer == "SIPP_CONTRIBUTION_REMINDER":
                fit += 0.70 * r.has_sipp + 0.35 * (r.age > 45)
            if offer == "CASH_TO_INVEST_EDUCATION":
                fit += 1.10 * (r.cash_ratio > 0.30)
            if offer == "MANAGED_SERVICE_EDUCATION":
                fit += 0.30 * (r.aum > df.aum.quantile(0.65)) + 0.25 * (r.digital_score < 0.55)
            prob = 1 / (1 + np.exp(-(base + fit + treatment * (0.45 + 0.25 * fit))))
            converted = rng.binomial(1, min(prob, 0.75))
            rows.append({
                "customer_id": r.customer_id,
                "segment": r.segment,
                "offer_type": offer,
                "assigned_group": "treatment" if treatment else "control",
                "converted": converted,
            })
    return pd.DataFrame(rows)


def analyse(df: pd.DataFrame, camp: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = df.groupby("segment").agg(
        n_customers=("customer_id", "size"),
        age_mean=("age", "mean"),
        aum_mean=("aum", "mean"),
        cash_ratio_mean=("cash_ratio", "mean"),
        contribution_18m_mean=("contribution_18m", "mean"),
        active_days_6m_mean=("active_days_6m", "mean"),
        has_isa_mean=("has_isa", "mean"),
        has_sipp_mean=("has_sipp", "mean"),
    ).reset_index()
    rows = []
    for (seg, offer), g in camp.groupby(["segment", "offer_type"]):
        t = g[g.assigned_group == "treatment"].converted.mean()
        c = g[g.assigned_group == "control"].converted.mean()
        rows.append({
            "segment": seg,
            "offer_type": offer,
            "treatment_conversion_rate": t,
            "control_conversion_rate": c,
            "absolute_uplift": t - c,
        })
    uplift = pd.DataFrame(rows)
    recs = uplift.sort_values("absolute_uplift", ascending=False).groupby("segment").head(1).copy()
    msg = {
        "ISA_ALLOWANCE_REMINDER": "Remind eligible ISA holders about contribution deadlines and provide neutral education on allowance use.",
        "SIPP_CONTRIBUTION_REMINDER": "Prompt eligible SIPP customers to review pension contributions without presenting personal advice.",
        "CASH_TO_INVEST_EDUCATION": "Give customers with high cash balances educational content on risk, time horizon, and investment options.",
        "MANAGED_SERVICE_EDUCATION": "Explain managed service features without recommending a product as personal advice.",
    }
    recs["safe_business_message"] = recs.offer_type.map(msg)
    return summary, uplift, recs


def figures(summary: pd.DataFrame, uplift: pd.DataFrame, camp: pd.DataFrame) -> list[Path]:
    paths = []
    for old in FIG.glob("*.png"):
        old.unlink()
    s = summary.sort_values("n_customers")
    plt.figure(figsize=(10, 5.4))
    ax = plt.gca()
    ax.barh(s.segment, s.n_customers, color=[SEGMENT_COLORS[x] for x in s.segment])
    ax.set_xlabel("Customers")
    ax.set_title("Client segment size")
    ax.grid(axis="x", color="#E5E7EB")
    paths.append(save_fig("01_segment_size.png"))

    plt.figure(figsize=(9, 5.6))
    ax = plt.gca()
    for _, r in summary.iterrows():
        ax.scatter(
            r.active_days_6m_mean,
            r.cash_ratio_mean,
            s=180 + 850 * r.aum_mean / summary.aum_mean.max(),
            color=SEGMENT_COLORS[r.segment],
            edgecolor="white",
            linewidth=1.3,
        )
        ax.annotate(r.segment.replace(" investors", ""), (r.active_days_6m_mean, r.cash_ratio_mean), xytext=(7, 4), textcoords="offset points", fontsize=8.5)
    ax.set_xlabel("Mean active days, 6m")
    ax.set_ylabel("Mean cash ratio")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(color="#E5E7EB")
    ax.set_title("Different client groups need different communication design")
    paths.append(save_fig("02_segment_need_map.png"))

    r = uplift.sort_values("absolute_uplift", ascending=False).groupby("segment").head(1).sort_values("absolute_uplift")
    plt.figure(figsize=(10, 5.4))
    ax = plt.gca()
    ax.barh(r.segment, r.absolute_uplift, color=[OFFER_COLORS[x] for x in r.offer_type])
    ax.set_xlabel("Treatment-control conversion lift")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(axis="x", color="#E5E7EB")
    ax.set_title("Recommended offer lift by segment")
    paths.append(save_fig("03_recommended_offer_lift.png"))

    heat = uplift.pivot(index="segment", columns="offer_type", values="absolute_uplift").loc[summary.segment]
    plt.figure(figsize=(11, 5.4))
    ax = plt.gca()
    im = ax.imshow(heat, cmap="PuOr", aspect="auto", vmin=-0.08, vmax=0.18)
    ax.set_xticks(range(len(heat.columns)))
    ax.set_xticklabels([c.replace("_", "\n") for c in heat.columns], fontsize=8)
    ax.set_yticks(range(len(heat.index)))
    ax.set_yticklabels(heat.index, fontsize=9)
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            ax.text(j, i, f"{100*heat.iloc[i, j]:.1f}", ha="center", va="center", fontsize=8)
    plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02).set_label("percentage points")
    ax.set_title("Offer uplift is segment-specific")
    paths.append(save_fig("04_offer_uplift_heatmap.png"))
    return paths


def img64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def make_dashboard(df: pd.DataFrame, summary: pd.DataFrame, uplift: pd.DataFrame, recs: pd.DataFrame, paths: list[Path]) -> None:
    sample = df.sort_values("aum", ascending=False).groupby("segment", as_index=False).head(2).reset_index(drop=True)
    rec_map = recs.set_index("segment").to_dict("index")
    seg_map = summary.set_index("segment").to_dict("index")
    pop = {
        "aum": float(df.aum.mean()),
        "cash_ratio": float(df.cash_ratio.mean()),
        "active_days_6m": float(df.active_days_6m.mean()),
        "contribution_18m": float(df.contribution_18m.mean()),
    }
    cards = []
    for _, r in sample.iterrows():
        rec = rec_map[r.segment]
        seg = seg_map[r.segment]
        needs = []
        if r.cash_ratio > 0.30:
            needs.append("cash education")
        if r.active_days_6m < 20:
            needs.append("low digital engagement")
        if r.has_isa:
            needs.append("ISA reminder")
        if r.has_sipp and r.age > 45:
            needs.append("pension prompt")
        cards.append({
            "customer_id": r.customer_id,
            "segment": r.segment,
            "age": int(r.age),
            "region": r.region,
            "aum": float(r.aum),
            "cash_ratio": float(r.cash_ratio),
            "active_days_6m": float(r.active_days_6m),
            "contribution_18m": float(r.contribution_18m),
            "has_isa": int(r.has_isa),
            "has_sipp": int(r.has_sipp),
            "recommended_offer": rec["offer_type"],
            "expected_lift": float(rec["absolute_uplift"]),
            "safe_message": rec["safe_business_message"],
            "needs": needs or ["general education"],
            "segment_mean": {
                "aum": float(seg["aum_mean"]),
                "cash_ratio": float(seg["cash_ratio_mean"]),
                "active_days_6m": float(seg["active_days_6m_mean"]),
                "contribution_18m": float(seg["contribution_18m_mean"]),
            },
        })
    figs = "\n".join([f'<figure><img src="data:image/png;base64,{img64(p)}"><figcaption>{p.stem}</figcaption></figure>' for p in paths])
    payload = json.dumps({"customers": cards, "population_mean": pop, "offer_uplift": uplift.to_dict("records")})
    html = f'''<!doctype html><html><head><meta charset="utf-8"><title>UKPI Analytics Dashboard</title><style>
body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:#F9FAFB;color:#111827}}header{{background:white;padding:34px 44px;border-bottom:1px solid #E5E7EB}}main{{max-width:1180px;margin:auto;padding:24px}}.card{{background:white;border:1px solid #E5E7EB;border-radius:14px;padding:18px;margin:16px 0}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}.kpi{{font-size:26px;font-weight:700}}figure{{background:white;border:1px solid #E5E7EB;border-radius:12px;padding:10px;margin:0}}img{{width:100%}}select{{padding:9px;border:1px solid #CBD5E1;border-radius:8px;min-width:360px}}.pill{{display:inline-block;background:#EEF2FF;padding:4px 8px;border-radius:999px;margin:3px;font-size:12px}}.barrow{{display:grid;grid-template-columns:160px 1fr 70px;gap:8px;align-items:center;margin:8px 0}}.bg{{height:12px;background:#E5E7EB;border-radius:999px;overflow:hidden}}.fill{{height:12px;border-radius:999px}}@media(max-width:850px){{.grid{{grid-template-columns:1fr}}select{{min-width:100%}}}}
</style></head><body><header><h1>UKPI Client Segmentation and Offer Analytics</h1><p>Answer first: use segment-specific education and reminder routes, not one message for all clients. This is synthetic data and not personal advice.</p></header><main>
<section class="card"><h2>Executive answer</h2><div class="grid"><div><div>Customers</div><div class="kpi">{len(df):,}</div></div><div><div>Best offer lift</div><div class="kpi">{100*uplift.absolute_uplift.max():.1f} pp</div></div></div></section>
<section class="grid">{figs}</section><section class="card"><h2>Dynamic customer dashboard</h2><select id="sel"></select><div id="panel"></div><div id="bars"></div></section>
<section class="card"><b>Safety boundary:</b> Outputs support service design and education routing. They do not recommend a fund, portfolio, risk level, or personal investment action.</section></main><script>
const DATA={payload}; const COLORS={json.dumps(SEGMENT_COLORS)};
function gbp(x){{return '£'+Math.round(x).toLocaleString('en-GB')}} function pc(x){{return (100*x).toFixed(1)+'%'}} function pp(x){{return (100*x).toFixed(1)+' pp'}}
function bar(label,v,max,c,fmt){{let w=Math.max(2,100*v/max); return `<div class="barrow"><div>${{label}}</div><div class="bg"><div class="fill" style="width:${{w}}%;background:${{c}}"></div></div><div>${{fmt(v)}}</div></div>`}}
function render(id){{let c=DATA.customers.find(x=>x.customer_id===id); let col=COLORS[c.segment]||'#4B5563'; document.getElementById('panel').innerHTML=`<div class="card" style="border-left:6px solid ${{col}}"><h3>${{c.customer_id}} — ${{c.segment}}</h3><p>Age ${{c.age}}, ${{c.region}}. AUM ${{gbp(c.aum)}}. Cash ratio ${{pc(c.cash_ratio)}}. Active days ${{c.active_days_6m}}.</p><p><b>Suggested communication:</b> ${{c.recommended_offer.replaceAll('_',' ')}}. Expected segment lift ${{pp(c.expected_lift)}}.</p><p>${{c.safe_message}}</p>${{c.needs.map(n=>`<span class="pill">${{n}}</span>`).join('')}}</div>`; let maxA=Math.max(c.aum,c.segment_mean.aum,DATA.population_mean.aum)*1.05; document.getElementById('bars').innerHTML=`<div class="card"><h3>Customer versus segment and population</h3>${{bar('Customer AUM',c.aum,maxA,col,gbp)}}${{bar('Segment AUM',c.segment_mean.aum,maxA,'#8D99AE',gbp)}}${{bar('Population AUM',DATA.population_mean.aum,maxA,'#9CA3AF',gbp)}}${{bar('Customer cash',c.cash_ratio,0.7,col,pc)}}${{bar('Segment cash',c.segment_mean.cash_ratio,0.7,'#8D99AE',pc)}}${{bar('Population cash',DATA.population_mean.cash_ratio,0.7,'#9CA3AF',pc)}}</div>`}}
let s=document.getElementById('sel'); DATA.customers.forEach(c=>{{let o=document.createElement('option'); o.value=c.customer_id; o.textContent=`${{c.customer_id}} — ${{c.segment}} — cash ${{pc(c.cash_ratio)}}`; s.appendChild(o)}}); s.onchange=e=>render(e.target.value); render(DATA.customers[0].customer_id);
</script></body></html>'''
    (OUT / "ukpi_dashboard.html").write_text(html, encoding="utf-8")


def main() -> None:
    df = segment(make_data())
    camp = simulate_campaigns(df)
    summary, uplift, recs = analyse(df, camp)
    df.to_csv(TAB / "customer_segments.csv", index=False)
    camp.to_csv(TAB / "campaign_events_with_segments.csv", index=False)
    summary.to_csv(TAB / "segment_profile_summary.csv", index=False)
    uplift.to_csv(TAB / "offer_uplift_by_segment.csv", index=False)
    recs.to_csv(TAB / "segment_offer_recommendations.csv", index=False)
    paths = figures(summary, uplift, camp)
    make_dashboard(df, summary, uplift, recs, paths)
    report = f"# Analysis report\n\nThe synthetic book has {len(df):,} customers and five segments. The largest simulated treatment-control lift is {100*uplift.absolute_uplift.max():.1f} percentage points. The HTML dashboard uses charts first and includes a dynamic customer selector. All records are synthetic and the output is not personal financial advice.\n"
    (REP / "analysis_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
