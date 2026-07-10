from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
REPORTS = ROOT / "reports"
FIGURES.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

SEGMENT_COLORS = {
    "High-value engaged investors": "#0072B2",
    "Cash-heavy cautious investors": "#D55E00",
    "Emerging monthly investors": "#009E73",
    "Pension builders approaching retirement": "#CC79A7",
    "Low-engagement or dormant investors": "#E69F00",
}


def require_columns(df: pd.DataFrame, table: str, columns: list[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(
            f"{table} is missing required columns {missing}. "
            f"Available columns: {df.columns.tolist()}"
        )


def build_uncertainty(campaigns: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (segment, offer), group in campaigns.groupby(["segment", "offer_type"]):
        treatment = group.loc[group["assigned_group"].eq("treatment"), "converted"]
        control = group.loc[group["assigned_group"].eq("control"), "converted"]
        n_treatment = int(treatment.size)
        n_control = int(control.size)
        if n_treatment == 0 or n_control == 0:
            raise ValueError(f"Empty treatment or control group for {segment} / {offer}")

        treatment_rate = float(treatment.mean())
        control_rate = float(control.mean())
        uplift = treatment_rate - control_rate
        standard_error = float(
            np.sqrt(
                treatment_rate * (1 - treatment_rate) / n_treatment
                + control_rate * (1 - control_rate) / n_control
            )
        )
        ci_lower = max(-1.0, uplift - 1.96 * standard_error)
        ci_upper = min(1.0, uplift + 1.96 * standard_error)
        min_group_size = min(n_treatment, n_control)

        if ci_lower > 0 and min_group_size >= 100:
            evidence_label = "positive simulated signal"
        elif ci_upper < 0 and min_group_size >= 100:
            evidence_label = "negative simulated signal"
        else:
            evidence_label = "directional / uncertain"

        rows.append(
            {
                "segment": segment,
                "offer_type": offer,
                "n_treatment": n_treatment,
                "treatment_conversions": int(treatment.sum()),
                "treatment_conversion_rate": treatment_rate,
                "n_control": n_control,
                "control_conversions": int(control.sum()),
                "control_conversion_rate": control_rate,
                "absolute_uplift": uplift,
                "standard_error": standard_error,
                "ci_95_lower": ci_lower,
                "ci_95_upper": ci_upper,
                "min_group_size": min_group_size,
                "evidence_label": evidence_label,
            }
        )

    return pd.DataFrame(rows).sort_values(["segment", "absolute_uplift"], ascending=[True, False])


def build_quality(customers: pd.DataFrame, campaigns: pd.DataFrame, evidence: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("customer_rows", int(len(customers)), "count", "PASS"),
        ("unique_customer_ids", int(customers["customer_id"].nunique()), "count", "PASS"),
        (
            "duplicate_customer_ids",
            int(customers["customer_id"].duplicated().sum()),
            "count",
            "PASS" if not customers["customer_id"].duplicated().any() else "REVIEW",
        ),
        (
            "missing_customer_cells",
            int(customers.isna().sum().sum()),
            "count",
            "PASS" if not customers.isna().any().any() else "REVIEW",
        ),
        (
            "cash_ratio_out_of_range",
            int((~customers["cash_ratio"].between(0, 1)).sum()),
            "count",
            "PASS" if customers["cash_ratio"].between(0, 1).all() else "FAIL",
        ),
        (
            "negative_aum_rows",
            int((customers["aum"] < 0).sum()),
            "count",
            "PASS" if (customers["aum"] >= 0).all() else "FAIL",
        ),
        ("campaign_rows", int(len(campaigns)), "count", "PASS"),
        (
            "duplicate_customer_offer_rows",
            int(campaigns.duplicated(["customer_id", "offer_type"]).sum()),
            "count",
            "PASS" if not campaigns.duplicated(["customer_id", "offer_type"]).any() else "REVIEW",
        ),
        (
            "treatment_assignment_share",
            float(campaigns["assigned_group"].eq("treatment").mean()),
            "proportion",
            "PASS" if 0.45 <= campaigns["assigned_group"].eq("treatment").mean() <= 0.59 else "REVIEW",
        ),
        (
            "minimum_treatment_or_control_group",
            int(evidence["min_group_size"].min()),
            "count",
            "PASS" if evidence["min_group_size"].min() >= 100 else "REVIEW",
        ),
        (
            "segment_offer_cells",
            int(len(evidence)),
            "count",
            "PASS",
        ),
    ]
    return pd.DataFrame(checks, columns=["metric", "value", "unit", "status"])


def make_uncertainty_figure(evidence: pd.DataFrame) -> Path:
    best = (
        evidence.sort_values("absolute_uplift", ascending=False)
        .groupby("segment", as_index=False)
        .head(1)
        .sort_values("absolute_uplift")
        .reset_index(drop=True)
    )
    y = np.arange(len(best))
    lower_error = best["absolute_uplift"] - best["ci_95_lower"]
    upper_error = best["ci_95_upper"] - best["absolute_uplift"]

    plt.figure(figsize=(11.4, 6.2))
    ax = plt.gca()
    for i, row in best.iterrows():
        ax.errorbar(
            row["absolute_uplift"],
            i,
            xerr=np.array([[lower_error.iloc[i]], [upper_error.iloc[i]]]),
            fmt="o",
            markersize=8,
            capsize=4,
            linewidth=1.8,
            color=SEGMENT_COLORS.get(row["segment"], "#4B5563"),
        )
    ax.axvline(0, color="#6B7280", linewidth=1)
    ax.set_yticks(y)
    ax.set_yticklabels(best["segment"])
    ax.set_xlabel("Treatment-control conversion uplift (95% interval)")
    ax.set_title("Best simulated offer by segment, with uncertainty and group sizes")
    ax.grid(axis="x", color="#E5E7EB")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for i, row in best.iterrows():
        ax.text(
            row["ci_95_upper"] + 0.006,
            i,
            f"{100 * row['absolute_uplift']:.1f} pp; n={row['n_treatment'] + row['n_control']}",
            va="center",
            fontsize=8.5,
        )
    plt.tight_layout()
    path = FIGURES / "07_recommended_offer_uncertainty.png"
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    return path


def main() -> None:
    customers = pd.read_csv(TABLES / "customer_segments.csv")
    campaigns = pd.read_csv(TABLES / "campaign_events_with_segments.csv")
    require_columns(customers, "customer_segments.csv", ["customer_id", "aum", "cash_ratio"])
    require_columns(
        campaigns,
        "campaign_events_with_segments.csv",
        ["customer_id", "segment", "offer_type", "assigned_group", "converted"],
    )

    evidence = build_uncertainty(campaigns)
    quality = build_quality(customers, campaigns, evidence)
    evidence.to_csv(TABLES / "offer_uplift_with_uncertainty.csv", index=False)
    quality.to_csv(TABLES / "data_quality_summary.csv", index=False)
    figure_path = make_uncertainty_figure(evidence)

    best = evidence.sort_values("absolute_uplift", ascending=False).iloc[0]
    report = f"""# Evidence and data-quality report

- Customer rows: {len(customers):,}
- Campaign rows: {len(campaigns):,}
- Segment-offer cells: {len(evidence)}
- Minimum treatment/control group size: {int(evidence['min_group_size'].min())}
- Strongest simulated uplift: {100 * float(best['absolute_uplift']):.1f} percentage points
- 95% interval for strongest simulated uplift: {100 * float(best['ci_95_lower']):.1f} to {100 * float(best['ci_95_upper']):.1f} percentage points
- Data-quality checks requiring review or failure: {int((quality['status'] != 'PASS').sum())}
- Uncertainty figure: `{figure_path.relative_to(ROOT)}`

These intervals describe uncertainty in the synthetic treatment-control comparison. They are not evidence of real customer impact.
"""
    (REPORTS / "evidence_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
