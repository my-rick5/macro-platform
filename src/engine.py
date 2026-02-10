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
    
    # 2. Deep History Expansion (24-quarter buffer)
    full_index = pd.period_range(start='2000Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()

    # 3. 🚀 THE BRUTE-FORCE INITIALIZATION:
    try:
        model = frbus.Frbus(model_xml)
        
        # We manually extract the required variables from the model object
        model_vars = set()
        if hasattr(model, 'vars'):
            model_vars = set(v.lower() for v in model.vars)
        else:
            # Fallback to direct XML inspection if property is missing
            with open(model_xml, 'r') as f:
                model_vars = set(re.findall(r'<name>(.*?)</name>', f.read().lower()))

        missing_vars = model_vars - set(df.columns)
        
        if missing_vars:
            print(f"📦 Manually initializing {len(missing_vars)} variables (including 'dmptmax')...")
            # We use 1.0 as a neutral baseline to avoid log(0) errors
            patch = {v: 1.0 for v in missing_vars}
            df = pd.concat([df, pd.DataFrame(patch, index=df.index)], axis=1)
            
    except Exception as e:
        print(f"⚠️ Metadata extraction failed: {e}")

    # 4. Final Engine Execution
    try:
        solve_start_date = pd.Period('2006Q1', freq='Q')
        solve_end_date = df.index.max()
        print(f"🏗️ Model Loaded. Solving with Explicit Initialization...")

        # Since we are using 1.0, we use a very conservative damping factor
        # to prevent the Newton solver from crashing on the first step.
        if hasattr(model, 'solver_options'):
            model.solver_options['factor'] = 0.01 
            
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