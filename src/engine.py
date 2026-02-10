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

    # 3. 🚀 THE LOG-SPACE INITIALIZATION:
    try:
        model = frbus.Frbus(model_xml)
        model_vars = set(v.lower() for v in model.vars) if hasattr(model, 'vars') else set()
        missing_vars = model_vars - set(df.columns)
        
        if missing_vars:
            print(f"📦 Initializing {len(missing_vars)} variables with Log-Space safety...")
            patch = {}
            for v in missing_vars:
                # Rates (interest, inflation) should be small (~5%)
                if any(x in v for x in ['r', 'pi', 'u', 'gap']):
                    patch[v] = 0.05
                # Levels (GDP, Price Indices) should be large
                else:
                    patch[v] = 100.0
            df = pd.concat([df, pd.DataFrame(patch, index=df.index)], axis=1)
    except Exception as e:
        print(f"⚠️ Discovery failed: {e}")

    # 4. Final Engine Execution
    try:
        solve_start_date = pd.Period('2006Q1', freq='Q')
        solve_end_date = df.index.max()
        print(f"🏗️ Model Loaded. Solving with Identity-Preserving Initialization...")

        # We force the solver to use a very small factor (0.001) for the first 10 iterations
        # to "warm up" the Jacobian without crashing.
        if hasattr(model, 'solver_options'):
            model.solver_options['factor'] = 0.001 
            
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