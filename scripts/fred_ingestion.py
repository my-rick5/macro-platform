import os
import io
import pandas as pd
from fredapi import Fred
from google.cloud import storage

# --- Configuration ---
FRED_API_KEY = os.environ.get('FRED_API_KEY')
GCS_BUCKET_NAME = 'macroflow-warehouse-2026'

# The list of series we want to track
SERIES_LIST = [
    'FEDFUNDS', 'CPIAUCSL', 'UNRATE', 
    'GDPC1', 'VIXCLS', 'WALCL'
]

def ingest_to_gcs():
    # 1. Initialize Clients
    fred = Fred(api_key=FRED_API_KEY)
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)

    print(f"Starting ingestion to bucket: {GCS_BUCKET_NAME}")

    for series_id in SERIES_LIST:
        try:
            # 2. Fetch from FRED
            print(f"Fetching {series_id}...")
            data = fred.get_series(series_id)
            
            # 3. Process into DataFrame
            df = pd.DataFrame(data, columns=['value'])
            df.index.name = 'date'
            df = df.reset_index()

            # 4. Convert to Parquet in-memory
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            buffer.seek(0)

            # 5. Upload to GCS
            blob_path = f"raw/{series_id}.parquet"
            blob = bucket.blob(blob_path)
            blob.upload_from_file(buffer, content_type='application/octet-stream')
            
            print(f"✅ Success: {blob_path}")

        except Exception as e:
            print(f"❌ Failed to ingest {series_id}: {e}")

if __name__ == "__main__":
    ingest_to_gcs()