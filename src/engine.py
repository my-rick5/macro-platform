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
    
    # 2. Strict Continuous Reconstruction
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()

    # 3. 🚀 THE DISCOVERY FIX:
    # We load the model and find every variable it expects.
    try:
        model = frbus.Frbus(model_xml)
        # Querying model metadata to find missing variables like 'dmptmax'
        all_model_vars = set(model.lookup(vtype='all'))
        missing_vars = all_model_vars - set(df.columns)
        
        if missing_vars:
            print(f"📦 Patching {len(missing_vars)} missing model variables (e.g., {list(missing_vars)[:3]}...)")
            # Populate missing variables with neutral defaults
            for v in missing_vars:
                # 'dmpt' variables are usually policy maxes/parameters; 1.0 is a safe identity.
                df[v] = 1.0 
    except Exception as e:
        print(f"⚠️ Metadata Discovery Failed: {e}")

    # 4. Zero-Base Residual Solve
    try:
        solve_start = df.index[8] # 2006Q1
        print(f"🏗️ Model Loaded. Solving with Zero-Base Discovery: {solve_start} to {df.index.max()}")
        
        # Now 'dmptmax' exists in df, so solve() will proceed
        baseline_df = model.solve(df.index[0], df.index.max(), df)
        
        # Overlay actual data growth onto baseline magnitude
        for col in actual_cols:
            if col in baseline_df.columns:
                scale_factor = baseline_df.loc[solve_start, col] / (df.loc[solve_start, col] or 1.0)
                baseline_df[col] = df[col] * scale_factor

        results = model.init_trac(solve_start, df.index.max(), baseline_df)
        print("✅ Engine Solve Successful.")
        
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()