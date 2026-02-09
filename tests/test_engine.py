import pytest
import pandas as pd
import os
from src.engine import run_macro_engine

def test_engine_processing(tmp_path):
    # 1. Setup: Create a fake data directory and mock Excel-converted CSV
    data_dir = tmp_path / "data"
    results_dir = tmp_path / "results"
    data_dir.mkdir()
    
    # Mock data: Date column + 3 quarters of unemployment forecasts
    mock_data = {
        'Date': [20040128, 20040215],
        'Q1': [5.1, 5.0],
        'Q2': [5.2, 5.1],
        'Q3': [5.3, 5.2]
    }
    df = pd.DataFrame(mock_data)
    input_file = data_dir / "tealbook_unemployment.csv"
    df.to_csv(input_file, index=False)

    # 2. Execute: Point the engine to our temp paths
    # (We temporarily change working directory or mock the paths)
    os.chdir(tmp_path)
    run_macro_engine()

    # 3. Verify: Check if the summary was created correctly
    output_file = results_dir / "forecast_summary.csv"
    assert output_file.exists()
    
    result_df = pd.read_csv(output_file)
    # Mean of [5.0, 5.1, 5.2] is 5.1
    assert result_df.iloc[0]['mean_unemployment_forecast'] == 5.1
    assert str(result_df.iloc[0]['vintage_date']) == "20040215"

if __name__ == "__main__":
    pytest.main([__file__])