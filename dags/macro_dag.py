from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'zach',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'macro_forecast_engine',
    default_args=default_args,
    schedule_interval='@weekly', 
    start_date=datetime(2026, 2, 1),
    catchup=False,
) as dag:

    # Task 1: Fetch from FRED
    ingest = DockerOperator(
        task_id='ingest_fred',
        image='macro-pipeline-engine-macro-engine:latest',
        command='python scripts/fred_ingestion.py',
        network_mode='macro-platform_default', # Check your folder name prefix!
        auto_remove=True
    )

    # Task 2: dbt Transformation
    transform = DockerOperator(
        task_id='dbt_transform',
        image='macro-pipeline-engine-macro-engine:latest',
        command='sh -c "cd dbt_macro && dbt run --profiles-dir ."',
        network_mode='macro-platform_default',
        auto_remove=True
    )

    # Task 3: BVAR Model
    model = DockerOperator(
        task_id='fit_bvar',
        image='macro-pipeline-engine-macro-engine:latest',
        command='python scripts/bvar_ultra.py',
        network_mode='macro-platform_default',
        environment={'MLFLOW_TRACKING_URI': 'http://mlflow:5000'},
        auto_remove=True
    )

    ingest >> transform >> model
