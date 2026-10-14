"""
Parse raw swim logs into a clean table and load them into SQLite.

Input CSV columns (one row per timed swim):
  date, stroke, distance_m, time, [pool_length_m], [notes]

  time can be "38.42", "1:12.80", or "2:41"

Rows that fail validation are written to a rejects file with the reason,
so a typo in the log never silently disappears.
"""

import argparse
import re
import sqlite3
from pathlib import Path

import pandas as pd

VALID_STROKES = {"freestyle", "backstroke"}
STROKE_ALIASES = {"free": "freestyle", "fr": "freestyle",
                  "back": "backstroke", "bk": "backstroke"}
TIME_RE = re.compile(r"^(?:(\d+):)?(\d{1,2}(?:\.\d{1,2})?)$")


def time_to_seconds(value) -> float | None:
    """'1:12.80' -> 72.8, '38.42' -> 38.42. Returns None if unparseable."""
    if pd.isna(value):
        return None
    match = TIME_RE.match(str(value).strip())
    if not match:
        return None
    minutes = int(match.group(1) or 0)
    seconds = float(match.group(2))
    if match.group(1) and seconds >= 60:
        return None
    return minutes * 60 + seconds


def normalize_stroke(value) -> str | None:
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    return STROKE_ALIASES.get(s, s)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = raw.copy()
    df["swim_date"] = pd.to_datetime(df["date"], errors="coerce")
    df["stroke"] = df["stroke"].map(normalize_stroke)
    df["distance_m"] = pd.to_numeric(df["distance_m"], errors="coerce")
    df["time_sec"] = df["time"].map(time_to_seconds)
    if "pool_length_m" not in df:
        df["pool_length_m"] = 25

    reasons = pd.Series("", index=df.index)
    reasons[df["swim_date"].isna()] += "bad date;"
    reasons[~df["stroke"].isin(VALID_STROKES)] += "unknown stroke;"
    reasons[df["distance_m"].isna() | (df["distance_m"] <= 0)] += "bad distance;"
    reasons[df["time_sec"].isna()] += "bad time;"

    # Sanity bound: anything faster than 40s/100m is almost certainly a typo
    pace = df["time_sec"] / df["distance_m"] * 100
    reasons[(reasons == "") & (pace < 40)] += "implausibly fast;"

    rejects = df[reasons != ""].assign(reject_reason=reasons[reasons != ""])
    good = df[reasons == ""].copy()

    good["pace_per_100m"] = (good["time_sec"] / good["distance_m"] * 100).round(2)
    good["swim_date"] = good["swim_date"].dt.date.astype(str)
    good = good[["swim_date", "stroke", "distance_m", "time_sec",
                 "pace_per_100m", "pool_length_m"]]
    good = good.drop_duplicates()
    return good, rejects


def load(df: pd.DataFrame, db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    schema = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema.read_text())
        # Full refresh: the CSV log is the source of truth
        conn.execute("DELETE FROM swims")
        df.to_sql("swims", conn, if_exists="append", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="inp", required=True)
    parser.add_argument("--db", default="data/swim.db")
    parser.add_argument("--rejects", default="data/rejects.csv")
    args = parser.parse_args()

    raw = pd.read_csv(args.inp)
    good, rejects = clean(raw)
    load(good, args.db)

    if len(rejects):
        Path(args.rejects).parent.mkdir(parents=True, exist_ok=True)
        rejects.to_csv(args.rejects, index=False)
    print(f"loaded {len(good)} swims, rejected {len(rejects)}")


if __name__ == "__main__":
    main()
