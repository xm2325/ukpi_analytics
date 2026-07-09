from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
SQL_PATH = ROOT / "sql" / "ad_hoc_business_questions.sql"
REPORT_PATH = ROOT / "reports" / "sql_check_report.md"
OUT_DIR = ROOT / "outputs" / "tables" / "sql_checks"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

TABLE_FILES = {
    "customer_segments": "customer_segments.csv",
    "campaign_events_with_segments": "campaign_events_with_segments.csv",
    "segment_profile_summary": "segment_profile_summary.csv",
    "offer_uplift_by_segment": "offer_uplift_by_segment.csv",
    "segment_offer_recommendations": "segment_offer_recommendations.csv",
}


def split_sql(sql_text: str) -> list[str]:
    cleaned_lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]
    return statements


def safe_name(statement: str, index: int) -> str:
    text = re.sub(r"\s+", " ", statement).strip().lower()
    words = re.findall(r"[a-z0-9_]+", text)[:6]
    return f"query_{index:02d}_" + "_".join(words) + ".csv"


def main() -> None:
    con = sqlite3.connect(":memory:")
    loaded = []
    for table, file_name in TABLE_FILES.items():
        path = TABLE_DIR / file_name
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}. Run python ukpi_analytics_demo.py first.")
        df = pd.read_csv(path)
        df.to_sql(table, con, index=False, if_exists="replace")
        loaded.append((table, len(df)))

    customer = pd.read_sql_query("SELECT aum FROM customer_segments", con)
    p90 = float(np.percentile(customer["aum"], 90))
    pd.DataFrame([{"metric": "aum", "percentile_90": p90}]).to_sql("executive_metrics", con, index=False, if_exists="replace")

    statements = split_sql(SQL_PATH.read_text(encoding="utf-8"))
    report_lines = ["# SQL check report", "", "Loaded tables:", ""]
    for table, n in loaded:
        report_lines.append(f"- `{table}`: {n:,} rows")
    report_lines.append(f"- `executive_metrics`: AUM p90 = £{p90:,.0f}")
    report_lines.append("")

    for i, statement in enumerate(statements, 1):
        df = pd.read_sql_query(statement, con)
        out_path = OUT_DIR / safe_name(statement, i)
        df.to_csv(out_path, index=False)
        report_lines.append(f"## Query {i}")
        report_lines.append("")
        report_lines.append(f"Rows returned: {len(df):,}")
        report_lines.append(f"Output: `{out_path.relative_to(ROOT)}`")
        report_lines.append("")
        if len(df) > 0:
            report_lines.append(df.head(5).to_markdown(index=False))
            report_lines.append("")

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Executed {len(statements)} SQL statements.")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
