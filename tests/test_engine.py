import pytest
import pandas as pd
import os
from src.engine import run_macro_engine

def test_engine_output_creation(tmp_path):
    # Setup mock data environment
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Create a dummy CSV to simulate the Process Data stage
    mock_data = pd.DataFrame({
        "Date": ["2004-01-01"],
        "Q1": [5.5],
        "Q2": [5.4]
    })
    mock_data.to_csv(os.path.join(data_dir, "tealbook_unemployment.csv"), index=False)

    # Run engine logic (ensure results dir exists)
    os.makedirs("results", exist_ok=True)
    run_macro_engine()

    # Assertions
    assert os.path.exists("results/forecast_summary.csv")
    summary = pd.read_csv("results/forecast_summary.csv")
    assert not summary.empty
    assert "mean_unemployment_forecast" in summary.columns