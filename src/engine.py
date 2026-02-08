import os
import datetime
import numpy as np
import pandas as pd
from scikits.umfpack import spsolve
from scipy.sparse import csc_matrix, eye

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time
    import time
    return wrapper

@timer_decorator
def solve_system(A, b):
    return spsolve(A, b)

def run_backtest_chunk(task_index):
    start_year = 2004
    current_year = start_year + task_index
    
    print(f"🚀 [Task {task_index}] Running Simulation for Year: {current_year}")

    # --- LOAD REAL TEALBOOK DATA ---
    data_path = "/home/spark/data/tealbook_unemployment.csv"
    
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        # Filter for the Tealbook published in Q1 of the target year
        # Note: Phil Fed format often uses 'DATE' as the publication date
        year_data = df[df['DATE'].astype(str).str.contains(str(current_year))].head(1)
        
        if not year_data.empty:
            # 'H0' or 'F0' are common column names for the 'Nowcast' in Phil Fed sets
            # We'll try to grab the first available forecast column
            target_unemployment = year_data.iloc[0, 2] # Usually the 3rd column is the first forecast
            print(f"📊 Tealbook Target Unemployment for {current_year}: {target_unemployment}%")
        else:
            target_unemployment = 5.0 # Fallback
            print(f"⚠️ No Tealbook data for {current_year}, using fallback: 5.0%")
    else:
        target_unemployment = 5.0
        print(f"⚠️ data/tealbook_unemployment.csv not found, using fallback: 5.0%")

    # --- MACRO SOLVER LOGIC ---
    # We'll create a 1000x1000 identity matrix representing the 'LONGBASE' steady state
    size = 1000
    A = eye(size).tocsc()
    
    # b is the 'exogenous' vector. We'll set the first element to our 
    # Tealbook unemployment target to simulate a policy shock.
    b = np.zeros(size)
    b[0] = target_unemployment 
    
    # Solve for the new equilibrium
    x, solve_duration = solve_system(A, b)
    
    # result_mean represents our 'Aggregate Economic Index' for this year
    result_mean = np.mean(x)
    print(f"✅ Solve complete in {solve_duration:.4f}s. Index: {result_mean:.4f}")
    
    # --- SAVE RESULTS ---
    output_dir = "/home/spark/results"
    os.makedirs(output_dir, exist_ok=True)
    
    results_df = pd.DataFrame({
        'year': [current_year],
        'target_unemployment': [target_unemployment],
        'solve_time_sec': [solve_duration],
        'agg_index': [result_mean],
        'timestamp': [datetime.datetime.now()]
    })
    
    filepath = os.path.join(output_dir, f"backtest_{current_year}.csv")
    results_df.to_csv(filepath, index=False)
    print(f"🏁 Results archived to {filepath}")

if __name__ == "__main__":
    idx = int(os.getenv("CLOUD_RUN_TASK_INDEX", 0))
    run_backtest_chunk(idx)