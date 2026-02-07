import os
import polars as pl
import numpy as np
import duckdb
import matplotlib          # <--- Add this first
matplotlib.use('Agg')     # <--- Then set the backend
import matplotlib.pyplot as plt
import mlflow
import mlflow.statsmodels
import datetime  # Added for timestamping
from statsmodels.tsa.vector_ar.var_model import VAR
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

def get_gcs_client():
    """Returns a GCS client if a bucket is configured."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if bucket_name:
        return storage.Client(), bucket_name
    return None, None

def download_warehouse_from_gcs():
    """Downloads the DuckDB file from GCS to /tmp for stateless execution."""
    client, bucket_name = get_gcs_client()
    if not client:
        print("No GCS_BUCKET_NAME found, using local path.")
        return os.getenv('DB_PATH', "./data/macro_warehouse.duckdb")

    source_blob_name = "data/macro_warehouse.duckdb"
    destination_file_name = "/tmp/macro_warehouse.duckdb"

    print(f"☁️ Cloud Mode: Downloading {source_blob_name}...")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    return destination_file_name

def upload_to_gcs(local_path, remote_path):
    """Uploads a local file to GCS."""
    client, bucket_name = get_gcs_client()
    if client:
        print(f"📤 Uploading {local_path} to gs://{bucket_name}/{remote_path}...")
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(local_path)

def run_ultra_model():
    # 1. PATH & MLFLOW INITIALIZATION
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    is_mlflow_available = False

    if tracking_uri and "localhost" not in tracking_uri:
        try:
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment("Macro_Forecast_Engine")
            is_mlflow_available = True
            print(f"📡 MLflow initialized at {tracking_uri}")
        except Exception as e:
            print(f"⚠️ MLflow connection failed: {e}. Running without tracking.")
    else:
        print("ℹ️ No remote MLflow URI found. Skipping experiment tracking.")

    # Detect if we are in Docker or Local
    project_root = "/app" if os.path.exists("/app") else os.getcwd()
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Use a dummy context manager if MLflow is disabled
    run_context = mlflow.start_run() if is_mlflow_available else pl.Config() 

    with run_context:
        db_path = download_warehouse_from_gcs()
        
        # 2. DATA FETCH
        query = """
            WITH filled_data AS (
                SELECT 
                    date, vix,
                    LAST_VALUE(fed_funds_rate IGNORE NULLS) OVER (ORDER BY date) as fed_funds_rate,
                    LAST_VALUE(unemployment_rate IGNORE NULLS) OVER (ORDER BY date) as unemployment_rate,
                    LAST_VALUE(real_gdp IGNORE NULLS) OVER (ORDER BY date) as real_gdp,
                    LAST_VALUE(fed_assets IGNORE NULLS) OVER (ORDER BY date) as fed_assets
                FROM stg_fred_indicators
            )
            SELECT * FROM filled_data WHERE vix IS NOT NULL AND real_gdp IS NOT NULL ORDER BY date ASC
        """

        with duckdb.connect(db_path) as con:
            raw_df = con.execute(query).pl()

        # 3. TRANSFORMATIONS
        last_actuals = raw_df.tail(1).to_dicts()[0]
        df = raw_df.with_columns([  
            pl.col("real_gdp").log().diff().alias("gdp_growth"),
            pl.col("fed_assets").log().diff().alias("assets_growth"),
            pl.col("fed_funds_rate").diff().alias("d_fed_funds"),
            pl.col("unemployment_rate").diff().alias("d_unemployment"),
            pl.col("vix") 
        ]).drop_nulls()

        model_vars = ['d_fed_funds', 'd_unemployment', 'vix', 'gdp_growth', 'assets_growth']
        pd_df = df.select(['date'] + model_vars).to_pandas().set_index('date')
        
        # 4. MODEL FITTING
        lags = 6
        results = VAR(pd_df).fit(lags, trend='c')
        
        # 5. FORECAST & RECONSTRUCTION
        forecast_steps = 6
        forecast_array = results.forecast(pd_df.values[-lags:], forecast_steps)
        forecast_diffs = pl.DataFrame(forecast_array, schema=model_vars)
        
        recon_data = []
        curr_gdp, curr_assets, curr_ffr = last_actuals['real_gdp'], last_actuals['fed_assets'], last_actuals['fed_funds_rate']
        
        for i in range(forecast_steps):
            row = forecast_diffs.row(i, named=True)
            curr_gdp *= np.exp(row['gdp_growth'])
            curr_assets *= np.exp(row['assets_growth'])
            curr_ffr += row['d_fed_funds']
            recon_data.append({"step": i+1, "gdp": curr_gdp, "assets": curr_assets, "ffr": curr_ffr, "vix": row['vix']})

        levels_df = pl.DataFrame(recon_data)
        
        # 6. SAVE & UPLOAD ARTIFACTS (With Historical Archiving)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        
        # --- CSV Section ---
        dated_csv = f"forecast_{timestamp}.csv"
        csv_path = os.path.join(output_dir, dated_csv)
        levels_df.write_csv(csv_path)
        upload_to_gcs(csv_path, f"results/archive/{dated_csv}") # Archived
        upload_to_gcs(csv_path, "results/forecast_latest.csv")  # Latest for UI

        # --- Parquet Section (Spark Ready) ---
        dated_parquet = f"forecast_{timestamp}.parquet"
        parquet_path = os.path.join(output_dir, dated_parquet)
        levels_df.write_parquet(parquet_path)
        upload_to_gcs(parquet_path, f"results/archive/{dated_parquet}")
        upload_to_gcs(parquet_path, "results/forecast_latest.parquet")
        
        if is_mlflow_available:
            mlflow.log_artifact(csv_path)

        # --- Plot Section ---
        irf = results.irf(12)
        fig = irf.plot(impulse='vix', response='d_fed_funds', orth=True)
        dated_img = f"vix_shock_{timestamp}.png"
        img_path = os.path.join(output_dir, dated_img)
        plt.savefig(img_path)
        upload_to_gcs(img_path, f"results/archive/{dated_img}")
        upload_to_gcs(img_path, "results/vix_shock_latest.png")
        
        if is_mlflow_available:
            mlflow.log_artifact(img_path)
            print(f"✅ Success! Run ID: {mlflow.active_run().info.run_id}")
        else:
            print("✅ Success! (No MLflow tracking)")

if __name__ == "__main__":
    run_ultra_model()