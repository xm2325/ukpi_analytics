from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

OUT = Path("outputs")
FIG = OUT / "figures"
TAB = OUT / "tables"
REP = Path("reports")
DOCS = Path("docs")
for d in (FIG, TAB, REP, DOCS):
    d.mkdir(parents=True, exist_ok=True)

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
GRID = "#E5E7EB"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#374151", "axes.labelcolor": "#111827", "xtick.color": "#374151", "ytick.color": "#374151"})


def gbp(x: float) -> str:
    return f"£{x:,.0f}"


def pc(x: float) -> str:
    return f"{100*x:.1f}%"


def pp(x: float) -> str:
    return f"{100*x:.1f} pp"


def clean_outputs() -> None:
    for p in FIG.glob("*.png"):
        p.unlink()
    for p in [OUT / "ukpi_dashboard.html", OUT / "customer_dashboard.html", DOCS / "index.html"]:
        if p.exists():
            p.unlink()


def save(path: Path) -> Path:
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    return path


def img64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


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
    contribution = np.clip(rng.gamma(2.4, 1150, n) * (0.5 + digital) * (0.7 + has_isa + 0.6 * has_sipp), 0, None)
    active_days = np.clip(rng.normal(18 + 34 * digital, 8, n), 0, 120)
    region = rng.choice(["North West", "London", "South East", "Scotland", "Wales", "East Midlands", "Yorkshire"], n)
    return pd.DataFrame({
        "customer_id": [f"C{i:06d}" for i in range(1, n + 1)],
        "age": age, "region": region, "digital_score": digital, "risk_appetite_proxy": risk,
        "has_isa": has_isa, "has_sipp": has_sipp, "has_gia": has_gia,
        "aum": aum.round(2), "cash_ratio": cash_ratio, "cash_balance": (aum * cash_ratio).round(2),
        "contribution_18m": contribution.round(2), "active_days_6m": active_days.round(0),
    })


def add_segments(df: pd.DataFrame) -> pd.DataFrame:
    x = df[["age", "aum", "cash_ratio", "contribution_18m", "active_days_6m", "has_sipp"]].copy()
    x["aum"] = np.log1p(x["aum"])
    x["contribution_18m"] = np.log1p(x["contribution_18m"])
    out = df.copy()
    out["cluster"] = KMeans(n_clusters=5, random_state=20260709, n_init=25).fit_predict(StandardScaler().fit_transform(x))
    prof = out.groupby("cluster").agg(age=("age", "mean"), aum=("aum", "mean"), cash=("cash_ratio", "mean"), contribution=("contribution_18m", "mean"))
    names: dict[int, str] = {}
    names[int(prof["aum"].idxmax())] = "High-value engaged investors"
    names[int(prof.drop(index=list(names))["cash"].idxmax())] = "Cash-heavy cautious investors"
    names[int(prof.drop(index=list(names))["age"].idxmax())] = "Pension builders approaching retirement"
    names[int(prof.drop(index=list(names))["contribution"].idxmax())] = "Emerging monthly investors"
    for c in prof.index:
        names.setdefault(int(c), "Low-engagement or dormant investors")
    out["segment"] = out["cluster"].map(names)
    return out


def simulate_campaigns(df: pd.DataFrame, seed: int = 20260710) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    offers = list(OFFER_COLORS)
    aum_q65 = df.aum.quantile(0.65)
    for r in df.itertuples(index=False):
        for offer in rng.choice(offers, size=rng.integers(1, 4), replace=False):
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
                fit += 0.30 * (r.aum > aum_q65) + 0.25 * (r.digital_score < 0.55)
            prob = 1 / (1 + np.exp(-(base + fit + treatment * (0.45 + 0.25 * fit))))
            rows.append({"customer_id": r.customer_id, "segment": r.segment, "offer_type": offer, "assigned_group": "treatment" if treatment else "control", "converted": int(rng.binomial(1, min(prob, 0.75)))})
    return pd.DataFrame(rows)


def analyse(df: pd.DataFrame, camp: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = df.groupby("segment").agg(n_customers=("customer_id", "size"), age_mean=("age", "mean"), aum_mean=("aum", "mean"), cash_ratio_mean=("cash_ratio", "mean"), contribution_18m_mean=("contribution_18m", "mean"), active_days_6m_mean=("active_days_6m", "mean"), has_isa_mean=("has_isa", "mean"), has_sipp_mean=("has_sipp", "mean")).reset_index()
    rows = []
    for (segment, offer), g in camp.groupby(["segment", "offer_type"]):
        t = g.loc[g.assigned_group == "treatment", "converted"].mean()
        c = g.loc[g.assigned_group == "control", "converted"].mean()
        rows.append({"segment": segment, "offer_type": offer, "treatment_conversion_rate": t, "control_conversion_rate": c, "absolute_uplift": t - c})
    uplift = pd.DataFrame(rows)
    recs = uplift.sort_values("absolute_uplift", ascending=False).groupby("segment").head(1).rename(columns={"offer_type": "recommended_offer", "absolute_uplift": "expected_absolute_lift"})
    messages = {"ISA_ALLOWANCE_REMINDER": "Remind eligible ISA holders about contribution deadlines and provide neutral education on allowance use.", "SIPP_CONTRIBUTION_REMINDER": "Prompt eligible SIPP customers to review pension contributions without presenting personal advice.", "CASH_TO_INVEST_EDUCATION": "Give customers with high cash balances educational content on risk, time horizon, and investment options.", "MANAGED_SERVICE_EDUCATION": "Explain managed service features without recommending a product as personal advice."}
    recs["safe_business_message"] = recs.recommended_offer.map(messages)
    recs["reason"] = np.where(recs.recommended_offer.eq("CASH_TO_INVEST_EDUCATION"), "high cash or education fit", "segment-specific conversion lift")
    return summary, uplift, recs[["segment", "recommended_offer", "expected_absolute_lift", "reason", "safe_business_message"]]


def figures(summary: pd.DataFrame, uplift: pd.DataFrame, recs: pd.DataFrame, camp: pd.DataFrame) -> list[Path]:
    paths: list[Path] = []
    s = summary.sort_values("n_customers")
    plt.figure(figsize=(10.6, 5.6)); ax = plt.gca(); ax.barh(s.segment, s.n_customers, color=[SEGMENT_COLORS[x] for x in s.segment]); ax.set_xlabel("Customers"); ax.set_title("Five client segments explain different analytics and communication needs"); ax.grid(axis="x", color=GRID)
    for i, v in enumerate(s.n_customers): ax.text(v + max(s.n_customers) * 0.015, i, f"{v:,.0f}", va="center")
    paths.append(save(FIG / "01_segment_size_journal_palette.png"))

    plt.figure(figsize=(9.8, 6.2)); ax = plt.gca()
    for r in summary.itertuples(index=False):
        ax.scatter(r.active_days_6m_mean, r.cash_ratio_mean, s=150 + 900 * r.aum_mean / summary.aum_mean.max(), color=SEGMENT_COLORS[r.segment], edgecolor="white", linewidth=1.4, alpha=0.88)
        ax.annotate(r.segment.replace(" investors", ""), (r.active_days_6m_mean, r.cash_ratio_mean), xytext=(7, 5), textcoords="offset points", fontsize=8.5)
    ax.set_xlabel("Mean active web/app days in last 6 months"); ax.set_ylabel("Mean cash ratio"); ax.yaxis.set_major_formatter(PercentFormatter(1)); ax.set_title("Different segments need different communication design"); ax.grid(color=GRID)
    paths.append(save(FIG / "02_segment_need_map.png"))

    r = recs.sort_values("expected_absolute_lift"); plt.figure(figsize=(10.8, 5.8)); ax = plt.gca(); ax.barh(r.segment, r.expected_absolute_lift, color=[OFFER_COLORS[x] for x in r.recommended_offer]); ax.set_xlabel("Expected treatment-control conversion lift"); ax.xaxis.set_major_formatter(PercentFormatter(1)); ax.set_title("Recommended communications differ by segment"); ax.grid(axis="x", color=GRID)
    for i, v in enumerate(r.expected_absolute_lift): ax.text(v + 0.003, i, pp(v), va="center")
    paths.append(save(FIG / "03_recommended_offer_lift.png"))

    heat = uplift.pivot(index="segment", columns="offer_type", values="absolute_uplift").loc[summary.sort_values("n_customers", ascending=False).segment]
    plt.figure(figsize=(11.5, 5.8)); ax = plt.gca(); im = ax.imshow(heat.fillna(0), cmap="PuOr", aspect="auto", vmin=-0.08, vmax=0.18); ax.set_xticks(np.arange(len(heat.columns))); ax.set_xticklabels([x.replace("_", "\n") for x in heat.columns], fontsize=8); ax.set_yticks(np.arange(len(heat.index))); ax.set_yticklabels(heat.index, fontsize=9)
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]): ax.text(j, i, f"{100*heat.iloc[i, j]:.1f}", ha="center", va="center", fontsize=8)
    plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02).set_label("percentage points"); ax.set_title("Offer uplift is segment-specific, so one message should not fit all clients")
    paths.append(save(FIG / "04_offer_uplift_heatmap.png"))

    conv = camp.groupby(["offer_type", "assigned_group"]).converted.mean().reset_index().pivot(index="offer_type", columns="assigned_group", values="converted").reindex(list(OFFER_COLORS)); x = np.arange(len(conv.index)); width = 0.36
    plt.figure(figsize=(11.5, 5.5)); ax = plt.gca(); ax.bar(x - width / 2, conv["control"], width, label="Control", color="#8D99AE"); ax.bar(x + width / 2, conv["treatment"], width, label="Treatment", color="#2A9D8F"); ax.set_xticks(x); ax.set_xticklabels([i.replace("_", "\n") for i in conv.index], fontsize=8); ax.set_ylabel("Conversion rate"); ax.yaxis.set_major_formatter(PercentFormatter(1)); ax.set_title("Campaign measurement uses treatment-control comparison"); ax.grid(axis="y", color=GRID); ax.legend(frameon=False)
    paths.append(save(FIG / "05_treatment_control_conversion.png"))

    x = np.arange(len(summary.segment)); width = 0.24; plt.figure(figsize=(12.8, 6.2)); ax = plt.gca()
    for k, (col, name, color) in enumerate([("cash_ratio_mean", "Cash ratio", "#0072B2"), ("has_isa_mean", "ISA ownership", "#009E73"), ("has_sipp_mean", "SIPP ownership", "#CC79A7")]): ax.bar(x + (k - 1) * width, summary[col], width, label=name, color=color)
    ax.set_xticks(x); ax.set_xticklabels([s.replace(" investors", "") for s in summary.segment], rotation=20, ha="right"); ax.set_ylabel("Share or ratio"); ax.yaxis.set_major_formatter(PercentFormatter(1)); ax.set_title("Segment profiles show why product and communication needs differ"); ax.grid(axis="y", color=GRID); ax.legend(frameon=False, ncol=3)
    paths.append(save(FIG / "06_segment_profile_comparison.png"))
    return paths


def customer_payload(df: pd.DataFrame, summary: pd.DataFrame, recs: pd.DataFrame, uplift: pd.DataFrame) -> dict[str, object]:
    sample = df.sort_values("aum", ascending=False).groupby("segment", as_index=False).head(3).reset_index(drop=True)
    rec_map = recs.set_index("segment").to_dict("index"); seg_map = summary.set_index("segment").to_dict("index")
    pop = {"aum": float(df.aum.mean()), "cash_ratio": float(df.cash_ratio.mean()), "active_days_6m": float(df.active_days_6m.mean()), "contribution_18m": float(df.contribution_18m.mean())}
    rows = []
    for r in sample.itertuples(index=False):
        needs = []
        if r.cash_ratio >= 0.28: needs.append("cash education")
        if r.active_days_6m < 15: needs.append("low digital engagement")
        if r.has_sipp and r.age >= 48: needs.append("pension review prompt")
        if r.has_isa: needs.append("ISA allowance reminder")
        if r.aum >= df.aum.quantile(0.80): needs.append("high-value client")
        rec = rec_map[r.segment]; seg = seg_map[r.segment]
        rows.append({"customer_id": r.customer_id, "segment": r.segment, "age": int(r.age), "region": r.region, "aum": float(r.aum), "cash_ratio": float(r.cash_ratio), "active_days_6m": float(r.active_days_6m), "contribution_18m": float(r.contribution_18m), "has_isa": int(r.has_isa), "has_sipp": int(r.has_sipp), "has_gia": int(r.has_gia), "needs": needs or ["general education"], "recommended_offer": rec["recommended_offer"], "expected_lift": float(rec["expected_absolute_lift"]), "reason": rec["reason"], "safe_business_message": rec["safe_business_message"], "segment_mean": {"aum": float(seg["aum_mean"]), "cash_ratio": float(seg["cash_ratio_mean"]), "active_days_6m": float(seg["active_days_6m_mean"]), "contribution_18m": float(seg["contribution_18m_mean"])}})
    return {"customers": rows, "population_mean": pop, "offer_uplift": uplift.to_dict("records")}


def make_dashboard(df: pd.DataFrame, summary: pd.DataFrame, uplift: pd.DataFrame, recs: pd.DataFrame, paths: list[Path]) -> str:
    fig_html = "\n".join(f'<figure><img src="data:image/png;base64,{img64(p)}" alt="{p.stem}"><figcaption>{p.stem.replace("_", " ").title()}</figcaption></figure>' for p in paths)
    payload = json.dumps(customer_payload(df, summary, recs, uplift), ensure_ascii=False)
    best = float(recs.expected_absolute_lift.max())
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>UKPI Analytics Dashboard</title><style>:root{{--ink:#111827;--muted:#4B5563;--line:#E5E7EB;--bg:#F9FAFB;--card:#FFFFFF;--blue:#0072B2;--orange:#D55E00;--green:#009E73;--purple:#CC79A7;--yellow:#E69F00}}body{{font-family:Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--ink)}}header{{padding:36px 44px 22px;background:white;border-bottom:1px solid var(--line)}}main{{max-width:1240px;margin:auto;padding:24px}}.card{{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;margin:18px 0;box-shadow:0 1px 2px rgba(0,0,0,.04)}}.answer{{border-left:6px solid var(--blue)}}.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.chart-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.kpi{{padding:16px;border-radius:12px;border:1px solid var(--line);background:white}}.kpi .label{{color:var(--muted);font-size:13px}}.kpi .value{{font-size:24px;font-weight:700;margin-top:6px}}figure{{margin:0;background:white;border:1px solid var(--line);border-radius:12px;padding:12px}}figure img{{width:100%;display:block}}figcaption{{color:var(--muted);font-size:13px;padding:8px 4px 2px}}select{{padding:9px 10px;border:1px solid #CBD5E1;border-radius:8px;min-width:360px;font-size:14px}}.pill{{display:inline-block;padding:4px 9px;border-radius:999px;background:#EEF2FF;color:#3730A3;margin:3px;font-size:12px}}.note{{background:#FFF7ED;border-left:5px solid var(--orange);padding:12px 14px;border-radius:8px;color:#7C2D12}}.safe{{background:#ECFDF5;border-left:5px solid var(--green);padding:12px 14px;border-radius:8px;color:#064E3B}}.bar-row{{display:grid;grid-template-columns:190px 1fr 78px;align-items:center;gap:10px;margin:9px 0}}.bar-bg{{height:13px;background:#E5E7EB;border-radius:999px;overflow:hidden}}.bar-fill{{height:13px;border-radius:999px}}.small{{color:var(--muted);font-size:13px;line-height:1.5}}.mini-table{{width:100%;border-collapse:collapse;font-size:14px}}.mini-table th,.mini-table td{{border-bottom:1px solid var(--line);padding:8px;text-align:left}}@media(max-width:900px){{.grid2,.grid3,.chart-grid{{grid-template-columns:1fr}}select{{min-width:100%}}}}</style></head><body><header><h1>UKPI Client Segmentation and Offer Analytics</h1><p>Synthetic data demo. Charts first, then customer-level service view. The output is not personal investment advice.</p></header><main><section class="card answer"><h2>Answer first</h2><p><b>The simulated UKPI book is not one customer group.</b> It separates into five actionable segments. The strongest simulated offer lift is <b>{100*best:.1f} percentage points</b>. The safe action is to route customers to neutral education, ISA or pension reminders, and product information based on segment-level evidence.</p></section><section class="grid3"><div class="kpi"><div class="label">Synthetic customers</div><div class="value">{len(df):,}</div></div><div class="kpi"><div class="label">Client segments</div><div class="value">5</div></div><div class="kpi"><div class="label">Best offer lift</div><div class="value">{100*best:.1f} pp</div></div></section><section class="card"><h2>1. Visual evidence</h2><div class="chart-grid">{fig_html}</div></section><section class="card"><h2>2. Dynamic customer dashboard</h2><p class="small">Select a synthetic customer. The dashboard changes the segment, needs, suggested communication route, and comparison bars.</p><select id="customerSelect"></select><div id="customerPanel" class="grid2"></div><div id="customerBars" class="card"></div><div id="offerBars" class="card"></div></section><section class="safe"><b>Safety boundary:</b> all records are synthetic. The outputs support service design and education routing, not personal fund recommendations, regulated advice, or suitability decisions.</section></main><script>const DATA={payload};const SEG_COLORS={json.dumps(SEGMENT_COLORS)};const OFFER_COLORS={json.dumps(OFFER_COLORS)};function gbp(x){{return '£'+Math.round(x).toLocaleString('en-GB')}}function pct(x){{return(100*x).toFixed(1)+'%'}}function pp(x){{return(100*x).toFixed(1)+' pp'}}function bar(label,value,maxValue,color,formatter){{const w=Math.max(2,Math.min(100,100*value/maxValue));return `<div class="bar-row"><div>${{label}}</div><div class="bar-bg"><div class="bar-fill" style="width:${{w}}%;background:${{color}}"></div></div><div>${{formatter(value)}}</div></div>`}}function renderCustomer(id){{const c=DATA.customers.find(x=>String(x.customer_id)===String(id));const color=SEG_COLORS[c.segment]||'#4B5563';document.getElementById('customerPanel').innerHTML=`<div class="card" style="border-left:6px solid ${{color}}"><h3>Customer ${{c.customer_id}}</h3><table class="mini-table"><tr><th>Segment</th><td>${{c.segment}}</td></tr><tr><th>Age and region</th><td>${{c.age}}, ${{c.region}}</td></tr><tr><th>AUM</th><td>${{gbp(c.aum)}}</td></tr><tr><th>Cash ratio</th><td>${{pct(c.cash_ratio)}}</td></tr><tr><th>Active days, 6m</th><td>${{c.active_days_6m.toFixed(0)}}</td></tr></table></div><div class="card"><h3>Suggested communication route</h3><p><b>${{c.recommended_offer.replaceAll('_',' ')}}</b></p><p>${{c.safe_business_message}}</p><p class="small">Reason: ${{c.reason}}. Expected segment-level lift: <b>${{pp(c.expected_lift)}}</b>.</p><div>${{c.needs.map(n=>`<span class="pill">${{n}}</span>`).join('')}}</div><p class="note">Service and communication view only. It should not recommend a fund, risk level, or personal investment action.</p></div>`;const maxA=Math.max(c.aum,c.segment_mean.aum,DATA.population_mean.aum)*1.08;const maxAct=Math.max(c.active_days_6m,c.segment_mean.active_days_6m,DATA.population_mean.active_days_6m)*1.08;const maxCon=Math.max(c.contribution_18m,c.segment_mean.contribution_18m,DATA.population_mean.contribution_18m)*1.08;document.getElementById('customerBars').innerHTML=`<h3>Customer versus segment and population</h3><div class="grid2"><div><h4>AUM</h4>${{bar('Customer',c.aum,maxA,color,gbp)}}${{bar('Segment mean',c.segment_mean.aum,maxA,'#8D99AE',gbp)}}${{bar('Population mean',DATA.population_mean.aum,maxA,'#9CA3AF',gbp)}}</div><div><h4>Cash ratio</h4>${{bar('Customer',c.cash_ratio,.65,color,pct)}}${{bar('Segment mean',c.segment_mean.cash_ratio,.65,'#8D99AE',pct)}}${{bar('Population mean',DATA.population_mean.cash_ratio,.65,'#9CA3AF',pct)}}</div><div><h4>Active days</h4>${{bar('Customer',c.active_days_6m,maxAct,color,x=>x.toFixed(0))}}${{bar('Segment mean',c.segment_mean.active_days_6m,maxAct,'#8D99AE',x=>x.toFixed(0))}}</div><div><h4>18m contributions</h4>${{bar('Customer',c.contribution_18m,maxCon,color,gbp)}}${{bar('Segment mean',c.segment_mean.contribution_18m,maxCon,'#8D99AE',gbp)}}</div></div>`;const offers=DATA.offer_uplift.filter(x=>x.segment===c.segment).sort((a,b)=>b.absolute_uplift-a.absolute_uplift);const maxLift=Math.max(.01,...offers.map(x=>Math.max(0,x.absolute_uplift)));document.getElementById('offerBars').innerHTML=`<h3>Offer evidence for this segment</h3>${{offers.map(o=>bar(o.offer_type.replaceAll('_',' '),Math.max(0,o.absolute_uplift),maxLift,OFFER_COLORS[o.offer_type]||'#4B5563',pp)).join('')}}`}}const sel=document.getElementById('customerSelect');DATA.customers.forEach(c=>{{const opt=document.createElement('option');opt.value=c.customer_id;opt.textContent=`Customer ${{c.customer_id}} — ${{c.segment}} — cash ${{pct(c.cash_ratio)}} — AUM ${{gbp(c.aum)}}`;sel.appendChild(opt)}});sel.addEventListener('change',e=>renderCustomer(e.target.value));renderCustomer(DATA.customers[0].customer_id);</script></body></html>'''


def verify_dashboard_sync(html_path: Path, paths: list[Path]) -> None:
    html = html_path.read_text(encoding="utf-8")
    embedded = re.findall(r"data:image/png;base64,([A-Za-z0-9+/=]+)", html)
    file_hashes = [hashlib.md5(p.read_bytes()).hexdigest() for p in paths]
    embedded_hashes = [hashlib.md5(base64.b64decode(b)).hexdigest() for b in embedded]
    if embedded_hashes != file_hashes:
        raise RuntimeError("Dashboard images are not synchronized with outputs/figures.")
    if (FIG / "01_segment_size.png").exists():
        raise RuntimeError("Old single-colour figure name still exists.")


def main() -> None:
    clean_outputs()
    df = add_segments(make_data())
    camp = simulate_campaigns(df)
    summary, uplift, recs = analyse(df, camp)
    df.to_csv(TAB / "customer_segments.csv", index=False)
    camp.to_csv(TAB / "campaign_events_with_segments.csv", index=False)
    summary.to_csv(TAB / "segment_profile_summary.csv", index=False)
    uplift.to_csv(TAB / "offer_uplift_by_segment.csv", index=False)
    recs.to_csv(TAB / "segment_offer_recommendations.csv", index=False)
    paths = figures(summary, uplift, recs, camp)
    html = make_dashboard(df, summary, uplift, recs, paths)
    for out in [OUT / "ukpi_dashboard.html", OUT / "customer_dashboard.html", DOCS / "index.html"]:
        out.write_text(html, encoding="utf-8")
    verify_dashboard_sync(OUT / "ukpi_dashboard.html", paths)
    report = f"# Analysis report\n\nGenerated {len(paths)} journal-palette figures and a chart-first dashboard for {len(df):,} synthetic customers. The dashboard images are embedded from the current outputs/figures directory and are verified by MD5 hash. The strongest simulated offer lift is {pp(float(recs.expected_absolute_lift.max()))}.\n"
    (REP / "analysis_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
