import os
import datetime
import numpy as np
import pandas as pd  # Added for CSV export
from scikits.umfpack import spsolve
from scipy.sparse import csc_matrix

def run_backtest_chunk(task_index):
    # 1. Map the task index to a specific year
    start_year = 2004
    current_year = start_year + task_index
    
    print(f"🚀 [Task {task_index}] Starting Backtest for Year: {current_year}")
    
    # 2. Math Logic
    # Simulate a UMFPACK calculation for this specific year
    A = csc_matrix([[1, 2], [3, 4]], dtype=float)
    b = np.array([task_index, current_year], dtype=float)
    x = spsolve(A, b)
    
    print(f"✅ [Task {task_index}] Calculation complete for {current_year}. Result: {x}")
    
    # 3. Create Results Directory (for the Data Volume)
    output_dir = "results"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 4. Save to CSV (This will appear on your laptop via the Jenkins volume mount)
    results_df = pd.DataFrame({
        'task_index': [task_index],
        'year': [current_year],
        'result_x0': [x[0]],
        'result_x1': [x[1]],
        'timestamp': [datetime.datetime.now()]
    })
    
    filename = f"backtest_{current_year}.csv"
    filepath = os.path.join(output_dir, filename)
    results_df.to_csv(filepath, index=False)
    
    print(f"🏁 [Task {task_index}] Finished. Results saved to {filepath}")

if __name__ == "__main__":
    # Get the task index from the environment (defaults to 0 for local testing)
    idx = int(os.getenv("CLOUD_RUN_TASK_INDEX", 0))
    run_backtest_chunk(idx)