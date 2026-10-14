"""
Weekly Airflow DAG: wait for the swim log -> parse, validate, load -> trends.

Point SWIM_PROJECT_DIR at this repo and SWIM_LOG at your log CSV
(both can be set as Airflow Variables or environment variables).
"""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor

PROJECT_DIR = Variable.get("SWIM_PROJECT_DIR",
                           default_var=os.environ.get("SWIM_PROJECT_DIR", "/opt/swim"))
SWIM_LOG = Variable.get("SWIM_LOG",
                        default_var=f"{PROJECT_DIR}/sample_data/swim_log_sample.csv")
DB = f"{PROJECT_DIR}/data/swim.db"

default_args = {
    "owner": "hitashi",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="swim_performance_pipeline",
    description="Ingest swim splits and compute pace trends",
    start_date=datetime(2026, 4, 1),
    schedule="0 8 * * 1",  # Monday mornings
    catchup=False,
    default_args=default_args,
    tags=["personal", "analytics"],
) as dag:

    wait_for_log = FileSensor(
        task_id="wait_for_swim_log",
        filepath=SWIM_LOG,
        poke_interval=300,
        timeout=60 * 60,
        mode="reschedule",
    )

    ingest = BashOperator(
        task_id="parse_validate_load",
        bash_command=(
            f"cd {PROJECT_DIR} && python ingest/parse_splits.py "
            f"--in {SWIM_LOG} --db {DB} --rejects data/rejects.csv"
        ),
    )

    trends = BashOperator(
        task_id="compute_pace_trends",
        bash_command=(
            f"cd {PROJECT_DIR} && python analysis/pace_trends.py "
            f"--db {DB} --out data/pace_trends.csv"
        ),
    )

    wait_for_log >> ingest >> trends
