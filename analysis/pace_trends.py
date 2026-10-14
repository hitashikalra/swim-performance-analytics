"""
Run the pace trend query and write the results to CSV, plus a chart of
best pace per month for each stroke/distance.

Usage:
  python analysis/pace_trends.py --db data/swim.db --out data/pace_trends.csv
"""

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

SQL = Path(__file__).resolve().parent.parent / "sql" / "pace_trends.sql"


def compute(db_path: str) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(SQL.read_text(), conn)


def summary(trends: pd.DataFrame) -> pd.DataFrame:
    """First vs latest month for every stroke/distance."""
    first = trends.groupby(["stroke", "distance_m"]).first()
    last = trends.groupby(["stroke", "distance_m"]).last()
    return pd.DataFrame({
        "first_month": first["month"],
        "first_best_pace": first["best_pace"],
        "latest_month": last["month"],
        "latest_best_pace": last["best_pace"],
        "pct_change": last["pct_change_since_start"],
    }).reset_index()


def plot(trends: pd.DataFrame, out_png: str):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping chart")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    for (stroke, dist), grp in trends.groupby(["stroke", "distance_m"]):
        ax.plot(grp["month"], grp["best_pace"], marker="o",
                label=f"{dist}m {stroke}")
    ax.set_ylabel("Best pace (sec / 100m), lower is faster")
    ax.set_xlabel("Month")
    ax.set_title("Pace trend by stroke and distance")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/swim.db")
    parser.add_argument("--out", default="data/pace_trends.csv")
    args = parser.parse_args()

    trends = compute(args.db)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    trends.to_csv(args.out, index=False)

    summ = summary(trends)
    summ.to_csv(args.out.replace(".csv", "_summary.csv"), index=False)
    plot(trends, args.out.replace(".csv", ".png"))

    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
