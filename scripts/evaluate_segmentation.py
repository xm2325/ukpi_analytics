from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
REPORTS = ROOT / "reports"
FIGURES.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

FEATURES = ["age", "aum", "cash_ratio", "contribution_18m", "active_days_6m", "has_sipp"]
REFERENCE_SEED = 20260709


def feature_matrix(customers: pd.DataFrame) -> np.ndarray:
    missing = [column for column in FEATURES if column not in customers.columns]
    if missing:
        raise ValueError(f"customer_segments.csv is missing clustering features: {missing}")
    x = customers[FEATURES].copy()
    x["aum"] = np.log1p(x["aum"])
    x["contribution_18m"] = np.log1p(x["contribution_18m"])
    return StandardScaler().fit_transform(x)


def main() -> None:
    customers = pd.read_csv(TABLES / "customer_segments.csv")
    x = feature_matrix(customers)

    diagnostics: list[dict[str, float | int]] = []
    labels_by_k: dict[int, np.ndarray] = {}
    for k in range(2, 9):
        model = KMeans(n_clusters=k, random_state=REFERENCE_SEED, n_init=25)
        labels = model.fit_predict(x)
        labels_by_k[k] = labels
        diagnostics.append(
            {
                "n_clusters": k,
                "silhouette_score": float(silhouette_score(x, labels)),
                "inertia": float(model.inertia_),
            }
        )

    diagnostics_df = pd.DataFrame(diagnostics)
    diagnostics_df["selected"] = diagnostics_df["n_clusters"].eq(5)
    diagnostics_df.to_csv(TABLES / "cluster_diagnostics.csv", index=False)

    reference = labels_by_k[5]
    stability_rows: list[dict[str, float | int]] = []
    for seed in [20260710, 20260711, 20260712, 20260713, 20260714]:
        labels = KMeans(n_clusters=5, random_state=seed, n_init=25).fit_predict(x)
        stability_rows.append(
            {
                "reference_seed": REFERENCE_SEED,
                "comparison_seed": seed,
                "adjusted_rand_index": float(adjusted_rand_score(reference, labels)),
            }
        )
    stability = pd.DataFrame(stability_rows)
    stability.to_csv(TABLES / "segment_stability.csv", index=False)

    plt.figure(figsize=(9.8, 5.8))
    ax = plt.gca()
    ax.plot(
        diagnostics_df["n_clusters"],
        diagnostics_df["silhouette_score"],
        marker="o",
        linewidth=2,
    )
    selected = diagnostics_df.loc[diagnostics_df["n_clusters"].eq(5)].iloc[0]
    ax.scatter([5], [selected["silhouette_score"]], s=120, zorder=3)
    ax.annotate(
        f"Selected k=5\nSilhouette {selected['silhouette_score']:.3f}",
        (5, selected["silhouette_score"]),
        xytext=(12, 14),
        textcoords="offset points",
    )
    ax.set_xticks(range(2, 9))
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel("Silhouette score")
    ax.set_title("Cluster-count diagnostic: separation across candidate k values")
    ax.grid(color="#E5E7EB")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    figure_path = FIGURES / "08_cluster_count_diagnostic.png"
    plt.savefig(figure_path, dpi=220, bbox_inches="tight")
    plt.close()

    selected_silhouette = float(selected["silhouette_score"])
    mean_ari = float(stability["adjusted_rand_index"].mean())
    min_ari = float(stability["adjusted_rand_index"].min())
    report = f"""# Segmentation diagnostics

- Candidate cluster counts evaluated: 2 to 8
- Selected cluster count: 5
- Silhouette score at k=5: {selected_silhouette:.3f}
- Mean adjusted Rand index across five alternative random seeds: {mean_ari:.3f}
- Minimum adjusted Rand index across alternative seeds: {min_ari:.3f}
- Diagnostic figure: `{figure_path.relative_to(ROOT)}`

The five-cluster solution is retained for interpretability and service-design coverage. The diagnostic tables make the trade-off visible rather than claiming that k=5 is uniquely optimal.
"""
    (REPORTS / "segmentation_diagnostics.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
