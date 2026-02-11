import pandas as pd
import os
import sys
import numpy as np

def run_pro_engine():
    print("🚀 Heartbeat: Entropy-Calibrated Macro Engine (Build #548)")
    
    # 1. Environment & Path Setup
    working_dir = os.getcwd()
    data_path = os.path.join(working_dir, "data/processed")
    model_xml = os.path.join(working_dir, "models/model.xml")
    results_dir = os.path.join(working_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    try:
        from pyfrbus import frbus
        print("✅ FRB/US Solver Dependencies Loaded.")
    except Exception as e:
        print(f"❌ FATAL: Dependency Load Error: {e}")
        sys.exit(1)

    # 2. Data Loading (Build #547 Stable Path)
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("❌ ERROR: No data files found.")
        return

    df = pd.concat([
        pd.read_csv(os.path.join(data_path, f))
        .assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q'))
        .set_index('date') for f in files
    ], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]

    # 3. Model Solver with Entropy Cycles
    model = frbus.Frbus(model_xml)
    solve_start = df.index.min() + 1
    solve_end = df.index.max()
    
    # --- Entropy Configuration ---
    max_entropy_cycles = 5
    entropy_threshold = 1e-6
    current_df = df.copy()
    
    print(f"📈 Initializing calibration solve: {solve_start} to {solve_end}")
    
    for cycle in range(1, max_entropy_cycles + 1):
        print(f"🔄 Entropy Cycle {cycle}/{max_entropy_cycles}...")
        
        # Core Solver Call
        results = model.init_trac(solve_start, solve_end, current_df)
        
        # Calculate Calibration Error (Mean Squared Residuals as Entropy Proxy)
        # We focus on the delta between the solve and the target data
        entropy_score = np.mean(np.square(results.values))
        print(f"📊 Current Entropy Score: {entropy_score:.8f}")
        
        if entropy_score < entropy_threshold:
            print("✨ Calibration achieved. Breaking cycles.")
            break
            
        # If entropy is too high, update current_df with a portion of the residuals 
        # to "nudge" the calibration for the next cycle
        current_df = current_df.add(results * 0.1, fill_value=0)
        
    final_results = results

    # 4. Final Exports
    # --- Full Export ---
    full_path = os.path.join(results_dir, "residuals.csv")
    final_results.to_csv(full_path)
    
    # --- Lite Export ---
    lite_path = os.path.join(results_dir, "residuals_lite.csv")
    lite_vars = ['cve', 'y', 'pit', 'unr', 'rff'] 
    available_vars = [v for v in lite_vars if v in final_results.columns]
    final_results[available_vars].to_csv(lite_path)
    
    print(f"✅ SUCCESS: Exported residuals.csv and residuals_lite.csv")

if __name__ == "__main__":
    run_pro_engine()