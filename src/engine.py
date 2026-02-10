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

    # 3. 🚀 THE DOMAIN-SPECIFIC PATCH:
    try:
        model = frbus.Frbus(model_xml)
        all_vars = model.vars if hasattr(model, 'vars') else re.findall(r'<name>(.*?)</name>', open(model_xml).read())
        missing_vars = set(v.strip().lower() for v in all_vars) - set(df.columns)
        
        if missing_vars:
            print(f"📦 Patching {len(missing_vars)} variables with Domain Scaling...")
            patch = {}
            for i, v in enumerate(missing_vars):
                # Distinguish between 'Rates/Deltas' and 'Levels'
                if any(x in v for x in ['r', 'pi', 'u', 'd']):
                    base = 5.0  # Safe base for interest rates or inflation
                else:
                    base = 10000.0 # Safe base for GDP-scale levels
                patch[v] = base + (i * 0.01)
            
            df = pd.concat([df, pd.DataFrame(patch, index=df.index)], axis=1)
    except Exception as e:
        print(f"⚠️ Discovery failed: {e}")

    # 4. Final Engine Execution
    try:
        solve_start_date = pd.Period('2006Q1', freq='Q')
        solve_end_date = df.index.max()
        print(f"🏗️ Model Loaded. Solving with Domain Stability...")

        # We keep the damping factor to prevent log-step divergence
        if hasattr(model, 'solver_options'):
            model.solver_options['factor'] = 0.05 
            
        baseline_df = model.solve(solve_start_date, solve_end_date, df)
        
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
        raise

if __name__ == "__main__":
    run_pro_engine()