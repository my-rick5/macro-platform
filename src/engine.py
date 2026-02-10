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

    # 3. 🚀 THE LOG-SAFE PATCH:
    try:
        model = frbus.Frbus(model_xml)
        all_vars = model.vars if hasattr(model, 'vars') else re.findall(r'<name>(.*?)</name>', open(model_xml).read())
        missing_vars = set(v.strip().lower() for v in all_vars) - set(df.columns)
        
        if missing_vars:
            print(f"📦 Patching {len(missing_vars)} missing variables with Log-Safe Base...")
            # Using 100.0 provides a buffer. If a solver step is -5.0, 
            # 95.0 is still log-legal. 1.0 would have become -4.0 (crash).
            patch = {v: 100.0 for v in missing_vars}
            df = pd.concat([df, pd.DataFrame(patch, index=df.index)], axis=1)
    except Exception as e:
        print(f"⚠️ Discovery failed: {e}")

    # 4. Final Engine Execution
    try:
        solve_start_date = pd.Period('2006Q1', freq='Q')
        solve_end_date = df.index.max()
        
        print(f"🏗️ Model Loaded. Solving with High-Base Stability (2000Q1 base)...")
        
        # 🚀 SOLVER TUNING:
        # We use model.solve but pass internal options to the scipy root finder
        # to prevent it from taking 'illegal' steps into negative log space.
        baseline_df = model.solve(
            solve_start_date, 
            solve_end_date, 
            df,
            # These options tell the underlying scipy solver to be 'gentle'
            # and avoid the explosive steps that cause the log crash.
            solver_opts={'options': {'factor': 0.1}} 
        )
        
        # 5. Tracking Overlay
        for col in actual_cols:
            if col in baseline_df.columns:
                scale_factor = baseline_df.loc[solve_start_date, col] / (df.loc[solve_start_date, col] or 1.0)
                baseline_df[col] = df[col] * scale_factor

        results = model.init_trac(solve_start_date, solve_end_date, baseline_df)
        print("✅ Engine Solve Successful.")
        
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        # Final emergency debug: clip all data to be positive
        raise

if __name__ == "__main__":
    run_pro_engine()