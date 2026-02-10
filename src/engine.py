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
    
    # 2. Strict Continuous Fill
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()

    # 3. 🚀 THE "ZERO-BASE" SOLVE: 
    # Use the model's baseline to populate the dataframe first. 
    # This ensures every variable (including proxies) is in perfect balance.
    try:
        model = frbus.Frbus(model_xml)
        solve_start = df.index[8] # 2006Q1
        
        print(f"🏗️ Model Loaded. Solving with Zero-Base Residuals: {solve_start} to {df.index.max()}")
        
        # Step A: Get a mathematically perfect baseline for the whole range
        baseline_df = model.solve(df.index[0], df.index.max(), df)
        
        # Step B: Overlay your real-world data onto the baseline.
        # We preserve the model's scale for variables we don't have.
        for col in actual_cols:
            if col in baseline_df.columns:
                # Scale your data to match the baseline's starting magnitude
                scale_factor = baseline_df.loc[solve_start, col] / df.loc[solve_start, col]
                baseline_df[col] = df[col] * scale_factor

        # 4. Final Tracking Solve
        results = model.init_trac(solve_start, df.index.max(), baseline_df)
        
        print("✅ Engine Solve Successful.")
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()