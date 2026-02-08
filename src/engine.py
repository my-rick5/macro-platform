import os
import datetime
import numpy as np
from scikits.umfpack import spsolve
from scipy.sparse import csc_matrix

def run_backtest_chunk(task_index):
    # Map the task index to a specific year
    # Example: Task 0 = 2004, Task 1 = 2005, ..., Task 20 = 2024
    start_year = 2004
    current_year = start_year + task_index
    
    print(f"🚀 [Task {task_index}] Starting Backtest for Year: {current_year}")
    
    # --- YOUR MATH LOGIC HERE ---
    # Placeholder: Simulate a UMFPACK calculation for this specific year
    A = csc_matrix([[1, 2], [3, 4]], dtype=float)
    b = np.array([task_index, current_year], dtype=float)
    x = spsolve(A, b)
    
    print(f"✅ [Task {task_index}] Calculation complete for {current_year}. Result: {x}")
    
    # --- SAVE TO GCS ---
    # In a real scenario, you'd save your results to a bucket here:
    # results_df.to_parquet(f"gs://your-bucket/backtests/{current_year}.parquet")
    print(f"🏁 [Task {task_index}] Finished and saved.")

if __name__ == "__main__":
    # Get the task index from the environment (defaults to 0 for local testing)
    idx = int(os.getenv("CLOUD_RUN_TASK_INDEX", 0))
    run_backtest_chunk(idx)
