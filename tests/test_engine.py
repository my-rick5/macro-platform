import pytest
import numpy as np
import os
import pandas as pd
from src.engine import run_backtest_chunk, solve_system

def test_solve_system_returns_tuple():
    """
    Verify that the solve_system function (wrapped by the timer decorator)
    returns both the result vector and the time duration.
    """
    from scipy.sparse import eye
    
    # Create a simple 10x10 identity matrix
    size = 10
    A = eye(size).tocsc()
    b = np.ones(size)
    
    result, duration = solve_system(A, b)
    
    assert len(result) == size
    assert isinstance(duration, float)
    assert duration > 0
    assert np.allclose(result, b)

def test_scaled_solver_output_integrity():
    """
    Verify that the 1000x1000 system produces a valid, finite result
    and saves the correct metadata to the CSV.
    """
    # Run for Task 0 (Year 2004)
    run_backtest_chunk(0)
    
    results_path = "results/backtest_2004.csv"
    assert os.path.exists(results_path), "Engine failed to create CSV output."
    
    df = pd.read_csv(results_path)
    
    # Verify metadata captured in CSV
    assert df['matrix_size'].iloc[0] == 1000
    assert not np.isnan(df['result_mean'].iloc[0])
    assert df['solve_time_sec'].iloc[0] > 0
    assert df['year'].iloc[0] == 2004

def test_solver_stability_large_scale():
    """
    Ensure the solver handles the 1% density sparse matrix without
    crashing or producing NaNs.
    """
    from scipy.sparse import csc_matrix, random
    
    size = 500 # Smaller scale for quick unit test
    A = random(size, size, density=0.01, format='csc', dtype=float)
    A += csc_matrix((np.ones(size), (np.arange(size), np.arange(size))), shape=(size, size))
    b = np.full(size, 1.0, dtype=float)
    
    # solve_system returns (x, duration)
    x, _ = solve_system(A, b)
    
    assert x.shape == (size,)
    assert np.all(np.isfinite(x)), "Solver produced non-finite values."

def test_directory_isolation(tmp_path, monkeypatch):
    """
    Verify that the engine correctly handles directory creation 
    in an isolated environment.
    """
    # Use pytest's tmp_path to ensure we aren't writing to the actual workspace
    monkeypatch.chdir(tmp_path)
    
    run_backtest_chunk(20) # Year 2024
    
    expected_file = tmp_path / "results" / "backtest_2024.csv"
    assert expected_file.exists()