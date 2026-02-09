import os
import datetime
import numpy as np
import pandas as pd
from scikits.umfpack import spsolve
from scipy.sparse import eye

def solve_system(A, b):
    import time
    start = time.perf_counter()
    return spsolve(A, b), time.perf_counter() - start

def run_backtest_chunk(task_index):
    current_year = 2004 + task_index
    data_path = "/home/spark/data/tealbook_unemployment.csv"
    target_unemployment = 5.0 # Default fallback
    
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        # Match current year in the DATE column (format: YYYY-MM-DD)
        year_match = df[df['DATE'].astype(str).str.contains(str(current_year))]
        if not year_match.empty:
            # Phil Fed RUC sheet: 1st col is DATE, 2nd col (index 1) is the forecast
            target_unemployment = year_match.iloc[0, 1]
    
    print(f"🚀 Year {current_year} | Target RUC: {target_unemployment}%")

    # Simple 1000x1000 equilibrium model
    A = eye(1000).tocsc()
    b = np.zeros(1000)
    b[0] = target_unemployment 
    
    x, duration = solve_system(A, b)
    
    # Save results
    os.makedirs("/home/spark/results", exist_ok=True)
    results_df = pd.DataFrame({
        'year': [current_year],
        'target_unemployment': [target_unemployment],
        'solve_time': [duration],
        'agg_index': [np.mean(x)]
    })
    results_df.to_csv(f"/home/spark/results/backtest_{current_year}.csv", index=False)

if __name__ == "__main__":
    idx = int(os.getenv("CLOUD_RUN_TASK_INDEX", 0))
    run_backtest_chunk(idx)