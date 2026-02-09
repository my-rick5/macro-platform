import pytest
import pandas as pd
import os
from src.engine import run_macro_engine

def test_engine_logic():
    # Create mock directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # Create a mock Excel file with the expected sheet name
    mock_df = pd.DataFrame({
        "Vintage": ["2024-Q1"],
        "F1": [4.0],
        "F2": [4.2]
    })
    
    with pd.ExcelWriter("data/tealbook_raw.xlsx") as writer:
        mock_df.to_excel(writer, sheet_name='UNEMP', index=False)

    # Run the engine (in test mode, paths should resolve locally)
    # Note: If running inside Docker, ensure pathing logic matches
    try:
        run_macro_engine()
        assert os.path.exists("results/forecast_summary.csv")
        res = pd.read_csv("results/forecast_summary.csv")
        assert res["mean_unemployment_forecast"].iloc[0] == 4.1
    finally:
        # Cleanup
        if os.path.exists("results/forecast_summary.csv"):
            os.remove("results/forecast_summary.csv")