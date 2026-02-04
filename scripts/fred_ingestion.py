import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

FRED_API_KEY = os.getenv('FRED_API_KEY')
# Use PROJECT_ROOT to build an absolute path
PROJECT_ROOT = os.getenv('PROJECT_ROOT', os.getcwd())
raw_path = os.path.join(PROJECT_ROOT, 'data', 'raw')

fred = Fred(api_key=FRED_API_KEY)

indicators = {
    'FEDFUNDS': 'fed_funds_rate',
    'CPIAUCSL': 'cpi',
    'GDPC1': 'real_gdp',
    'UNRATE': 'unemployment_rate',
    'WALCL': 'fed_balance_sheet',
    'VIXCLS': 'vix'
}

def ingest_macro_data():
    os.makedirs(raw_path, exist_ok=True)
    
    for series_id, clean_name in indicators.items():
        print(f"Fetching {series_id}...")
        try:
            data = fred.get_series(series_id)
            df = data.to_frame(name='value')
            df.index.name = 'date'
            df.reset_index(inplace=True)
            # Save using the robust path
            df.to_parquet(os.path.join(raw_path, f"{series_id}.parquet"))
        except Exception as e:
            print(f"Error {series_id}: {e}")

if __name__ == "__main__":
    ingest_macro_data()