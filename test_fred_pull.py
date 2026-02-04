import os
import polars as pl
import pyfredapi as pf  # Use the standardized import
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("FRED_API_KEY")

def test_ingestion(series_id="FEDFUNDS"):
    print(f"--- Ingesting {series_id} ---")
    
    # 1. In 2026, pyfredapi can return Polars directly!
    # This avoids the Pandas ambiguity error entirely.
    df = pf.get_series(series_id=series_id, api_key=api_key, return_format="polars")
    
    # 2. Check if we actually got data
    if df.height == 0:
        print("Error: No data returned. Check your API key or Series ID.")
        return

    print(df.head())
    
    # 3. Save as Parquet
    os.makedirs("data/raw", exist_ok=True)
    output_path = f"data/raw/{series_id}.parquet"
    df.write_parquet(output_path)
    
    print(f"Successfully saved {df.height} rows to {output_path}")

if __name__ == "__main__":
    test_ingestion()
