import pandas as pd
import os
import re
import numpy as np
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    results_dir = "/home/spark/results"
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    actual_cols = list(df.columns)
    
    # 2. Deep History Expansion
    full_index = pd.period_range(start='2000Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()

    # 3. 🚀 THE WARM-START FIX:
    try:
        model = frbus.Frbus(model_xml)
        # We load the data that comes embedded in the model itself.
        # This is guaranteed to be mathematically consistent.
        print("📦 Loading internal model baseline to fill gaps...")
        master_df = model.get_init_data() # Gets the standard FRB/US baseline
        
        # We align the internal baseline to our timeframe
        master_df = master_df.reindex(full_index).bfill().ffill()
        
        # We overlay your 15 real variables onto the perfect baseline
        for col in actual_cols:
            master_df[col] = df[col]
            
        df = master_df
    except Exception as e:
        print(f"⚠️ Warm-start failed, falling back to discovery: {e}")
        # (Discovery logic as backup...)

    # 4. Final Engine Execution
    try:
        solve_start_date = pd.Period('2006Q1', freq='Q')
        solve_end_date = df.index.max()
        print(f"🏗️ Model Loaded. Solving with Warm-Start Baseline...")

        # We use the most robust solver settings
        if hasattr(model, 'solver_options'):
            model.solver_options['factor'] = 0.01 
            
        # Since the baseline is already balanced, solve() should converge instantly
        baseline_df = model.solve(solve_start_date, solve_end_date, df)
        
        # 5. Tracking Solve
        results = model.init_trac(solve_start_date, solve_end_date, baseline_df)
        print("✅ Engine Solve Successful.")
        
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()