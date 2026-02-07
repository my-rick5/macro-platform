import os
import polars as pl
import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

def get_gcs_client():
    """Returns a GCS client if a bucket is configured."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if bucket_name:
        return storage.Client(), bucket_name
    return None, None

def download_archive_from_gcs(timestamp):
    """Downloads a specific archived forecast from GCS to /tmp."""
    client, bucket_name = get_gcs_client()
    if not client:
        print("⚠️ GCS client not configured. Check your .env file.")
        return None

    remote_path = f"results/archive/forecast_{timestamp}.parquet"
    local_path = f"/tmp/forecast_{timestamp}.parquet"
    
    print(f"📥 Fetching archived forecast from GCS: {remote_path}")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(remote_path)
    
    if not blob.exists():
        print(f"❌ Archive not found in GCS: {remote_path}")
        return None
        
    blob.download_to_filename(local_path)
    return local_path

def run_evaluation(forecast_timestamp):
    # 1. Load the Forecast from GCS
    local_parquet = download_archive_from_gcs(forecast_timestamp)
    if not local_parquet: 
        return
    
    forecast_df = pl.read_parquet(local_parquet)
    
    # 2. Connect to Warehouse (Adaptive Pathing)
    project_root = "/app" if os.path.exists("/app") else os.getcwd()
    db_path = os.getenv('DB_PATH', os.path.join(project_root, "data/macro_warehouse.duckdb"))

    if not os.path.exists(db_path):
        print(f"❌ Error: Database not found at {db_path}")
        return

    # Backtest Query: Pulls the 6 most recent months of ACTUAL data
    query = """
        SELECT 
            fed_funds_rate as ffr_actual, 
            vix as vix_actual,
            real_gdp as gdp_actual
        FROM stg_fred_indicators
        WHERE fed_funds_rate IS NOT NULL
        ORDER BY date DESC
        LIMIT 6
    """
    
    print(f"📂 Connecting to warehouse at: {db_path}")
    with duckdb.connect(db_path) as con:
        # Reverse because 'ORDER BY date DESC' gives newest first, 
        # but forecast steps are 1 -> 6 (chronological)
        actuals_df = con.execute(query).pl().reverse() 

    # 3. Join and Calculate Error Metrics
    # Horizontal concat aligns Step 1 (Forecast) with the oldest of the last 6 months (Actual)
    eval_df = pl.concat([forecast_df, actuals_df], how="horizontal")
    
    eval_df = eval_df.with_columns([
        (pl.col("ffr") - pl.col("ffr_actual")).abs().alias("ffr_error"),
        (pl.col("vix") - pl.col("vix_actual")).abs().alias("vix_error")
    ])

    # 4. Statistical Summary (MAE)
    ffr_mae = eval_df["ffr_error"].mean()
    vix_mae = eval_df["vix_error"].mean()

    print("\n--- 📊 Performance Report ---")
    print(eval_df.select(["ffr", "ffr_actual", "ffr_error"]))
    
    print(f"\n📈 Mean Absolute Error (FFR): {ffr_mae:.4f}")
    print(f"📈 Mean Absolute Error (VIX): {vix_mae:.4f}")
    
    # 5. Plot Comparison & Save
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    plt.subplot(2, 1, 1)
    plt.plot(eval_df["ffr"], label="Predicted FFR", marker='o', linestyle='--')
    plt.plot(eval_df["ffr_actual"], label="Actual FFR", marker='x', color='orange')
    plt.title(f"Backtest Analysis: {forecast_timestamp}")
    plt.ylabel("Fed Funds Rate")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.subplot(2, 1, 2)
    plt.plot(eval_df["vix"], label="Predicted VIX", marker='o', linestyle='--', color='green')
    plt.plot(eval_df["vix_actual"], label="Actual VIX", marker='x', color='red')
    plt.ylabel("VIX Index")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, f"eval_{forecast_timestamp}.png")
    plt.savefig(output_path)
    print(f"\n✅ Evaluation plot saved to: {output_path}")

if __name__ == "__main__":
    # If a timestamp is passed as an argument, use it. 
    # Otherwise, look for the most recent file in the archive.
    import sys
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        # Auto-detect latest timestamp from GCS
        client, bucket_name = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix="results/archive/forecast_"))
        
        if blobs:
            # Sort by name to get the latest timestamped file
            latest_blob = sorted(blobs, key=lambda x: x.name)[-1]
            # Extract timestamp from 'results/archive/forecast_20260206_1603.parquet'
            target = latest_blob.name.split('_')[-2] + "_" + latest_blob.name.split('_')[-1].split('.')[0]
        else:
            target = "20260206_1603" # Fallback

    run_evaluation(target)