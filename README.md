# Swim Performance Analytics

I started learning to swim in spring 2026 and wanted to know whether I was actually getting faster or just feeling like it. This is an Airflow-scheduled pipeline that takes my practice log, cleans and validates it, loads it into SQLite, and tracks pace trends by stroke and distance.

## Pipeline

```
swim log CSV
     |
     v
[wait_for_swim_log]       FileSensor, waits for the log to exist
     |
     v
[parse_validate_load]     ingest/parse_splits.py
                          - "1:12.80" -> 72.8s, stroke aliases (free/back)
                          - pace per 100m so 25s, 50s and 100s compare
                          - bad rows go to data/rejects.csv with a reason
                          - full refresh into SQLite
     |
     v
[compute_pace_trends]     sql/pace_trends.sql + analysis/pace_trends.py
                          - best and average pace per month
                          - % change vs last month and since the first month
                          - summary CSV and a chart
```

Runs every Monday morning, with retries.

## Why best pace, not average

Practice logs mix easy laps with hard efforts. Averaging them hides progress, so the trend uses each month's best swim per stroke and distance. Average pace is still in the output for context.

## Run it

```bash
pip install -r requirements.txt

python ingest/parse_splits.py --in sample_data/swim_log_sample.csv
python analysis/pace_trends.py

pytest
```

Outputs land in `data/`: `swim.db`, `pace_trends.csv`, `pace_trends_summary.csv`, `pace_trends.png`, and `rejects.csv` if anything failed validation.

To run it in Airflow, copy `dags/swim_pipeline_dag.py` into your DAGs folder and set the `SWIM_PROJECT_DIR` and `SWIM_LOG` Airflow Variables.

## Log format

```
date,stroke,distance_m,time,pool_length_m
2026-04-06,freestyle,25,23.99,25
2026-04-06,freestyle,50,51.43,25
```

`sample_data/swim_log_sample.csv` is generated sample data in this format (with two deliberately bad rows to show the rejects path). Swap in your own log to get real numbers.

## Repo layout

```
dags/          Airflow DAG
ingest/        parsing, validation, load
sql/           table schema and trend query
analysis/      runs the trend query, writes CSV and chart
sample_data/   example log
tests/         unit tests for parsing and validation
```
