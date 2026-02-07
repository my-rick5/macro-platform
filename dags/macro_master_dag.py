from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime, timedelta
from airflow.models import Variable
from docker.types import Mount
from airflow.providers.google.cloud.operators.cloud_run import CloudRunExecuteJobOperator
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator

# Unified arguments
default_args = {
    'owner': 'zach',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# --- MOUNTS ---
# Shared data folder (DuckDB + Local CSVs)
data_mount = Mount(
    source='/Users/zacharymyrick/macro-platform/data',
    target='/app/data',
    type='bind'
)

# GCloud Credentials (The missing link for GCS access)
gcloud_mount = Mount(
    source='/Users/zacharymyrick/.config/gcloud',
    target='/root/.config/gcloud',
    type='bind',
    read_only=True
)

# Shared environment variables for Cloud Auth
cloud_env = {
    'GOOGLE_APPLICATION_CREDENTIALS': '/root/.config/gcloud/application_default_credentials.json',
    'GOOGLE_CLOUD_PROJECT': 'macroflow-486515' # Updated to your actual project ID
}

with DAG(
    'macro_forecast_system',
    default_args=default_args,
    description='End-to-end Macro Pipeline: FRED -> dbt -> BVAR',
    schedule_interval='@weekly', 
    start_date=datetime(2026, 2, 1),
    catchup=False,
) as dag:

# Task 1: Fetch from FRED & Upload to GCS
    ingest = DockerOperator(
        task_id='ingest_fred',
        image='macro-pipeline-engine-macro-engine:latest',
        # Sets the working directory to where scripts/ lives
        working_dir='/app', 
        command='python scripts/fred_ingestion.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='macro-platform_default',
        environment={
            'FRED_API_KEY': Variable.get('fred_api_key'),
            **cloud_env
        },
        mounts=[data_mount, gcloud_mount],
        mount_tmp_dir=False,
        auto_remove=True
    )

# Task 2: dbt Transformation (GCS -> DuckDB)
    transform = DockerOperator(
        task_id='dbt_transform',
        image='macro-pipeline-engine-macro-engine:latest',
        # Points exactly to the folder containing dbt_project.yml
        working_dir='/app/dbt_macro', 
        # --profiles-dir . tells dbt to look in /app/dbt_macro for profiles.yml
        command='dbt run --profiles-dir . --vars \'{"raw_data_path": "gs://macro-engine-warehouse-macroflow-486515/raw"}\'', 
        docker_url='unix://var/run/docker.sock',
        network_mode='macro-platform_default',
        environment=cloud_env,
        mounts=[data_mount, gcloud_mount],
        mount_tmp_dir=False,
        auto_remove=True
    )

    upload_warehouse = LocalFilesystemToGCSOperator(
        task_id="upload_warehouse_to_gcs",
        # CHANGE THIS from /app/data/ to /opt/airflow/data/
        src="/opt/airflow/data/macro_warehouse.duckdb", 
        dst="data/macro_warehouse.duckdb",
        bucket="macro-engine-warehouse-macroflow-486515",
        gcp_conn_id='google_cloud_default',
    )

    run_bvar_model = CloudRunExecuteJobOperator(
        task_id="run_bvar_model_job",
        project_id="macroflow-486515",
        region="us-central1",
        job_name="macro-forecast-job",
        dag=dag,
    )

    # The Chain
    ingest >> transform >> upload_warehouse >> run_bvar_model