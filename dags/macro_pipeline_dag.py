from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'macro_forecast_pipeline',
    default_args=default_args,
    description='End-to-end Macro Pipeline: FRED -> dbt -> BVAR',
    schedule_interval='@weekly', # Runs once a week
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:

    # 1. Ingest Data from FRED
    ingest_fred = DockerOperator(
        task_id='ingest_fred',
        image='macro-pipeline-engine-macro-engine:latest',
        command='python scripts/fred_ingestion.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='macro-pipeline-engine_default',
        environment={'FRED_API_KEY': '{{ var.value.fred_api_key }}'}
    )

    # 2. Transform with dbt
    transform_dbt = DockerOperator(
        task_id='transform_dbt',
        image='macro-pipeline-engine-macro-engine:latest',
        command='sh -c "cd dbt_macro && dbt run --profiles-dir ."',
        docker_url='unix://var/run/docker.sock',
        network_mode='macro-pipeline-engine_default'
    )

    # 3. Fit BVAR Model & Log to MLflow
    fit_bvar = DockerOperator(
        task_id='fit_bvar',
        image='macro-pipeline-engine-macro-engine:latest',
        command='python scripts/bvar_ultra.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='macro-pipeline-engine_default',
        environment={
            'MLFLOW_TRACKING_URI': 'http://mlflow:5000'
        }
    )

    # Define the Dependency Chain
    ingest_fred >> transform_dbt >> fit_bvar
