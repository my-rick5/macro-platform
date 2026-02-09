import pytest
import os
import pandas as pd
from unittest.mock import patch
from src.engine import run_backtest_chunk

@pytest.fixture
def mock_tealbook_data():
    return pd.DataFrame({
        'DATE': ['2004-01-01', '2005-01-01'],
        'RUC': [5.5, 5.2] # Mocked unemployment values
    })

@patch('src.engine.pd.read_csv')
@patch('src.engine.os.path.exists')
def test_engine_uses_tealbook_value(mock_exists, mock_read_csv, mock_tealbook_data):
    mock_exists.return_value = True
    mock_read_csv.return_value = mock_tealbook_data
    
    # Run for 2004 (Task 0)
    run_backtest_chunk(0)
    
    output_file = "/home/spark/results/backtest_2004.csv"
    assert os.path.exists(output_file)
    
    res = pd.read_csv(output_file)
    assert res['RUC'].iloc[0] == 5.5

@patch('src.engine.os.path.exists')
def test_engine_fallback(mock_exists):
    mock_exists.return_value = False
    run_backtest_chunk(1) # 2005
    res = pd.read_csv("/home/spark/results/backtest_2005.csv")
    assert res['RUC'].iloc[0] == 5.0