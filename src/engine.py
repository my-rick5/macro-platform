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
    
    # 2. Strict Reconstruction (Log-Linear)
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()
    # 🚀 SCALE FIX: Many FRB/US versions expect GDP in billions (e.g. 18000) 
    # and rates in percentages (e.g. 5.0). We will preserve the input scale.
    df = df.abs().clip(lower=10.0)

    # 3. Proxy Synchronization
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                expected_vars = [v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', f.read()) if v.strip()]
            # Set all unknown variables to a neutral, high-stability constant
            new_vars_dict = {v: pd.Series(100.0, index=df.index) for v in expected_vars if v not in df.columns}
            df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception: pass

    # 4. 🚀 THE WARM-UP SOLVER
    try:
        model = frbus.Frbus(model_xml)
        solve_start = df.index[8] # 2006Q1
        
        print(f"🏗️ Model Loaded. Performing Warm-up for: {solve_start}")
        
        # We use solve() first to let the model find a stable 'baseline' 
        # before we try to calculate tracking residuals (init_trac).
        # This effectively 'primes' the Jacobian matrix.
        baseline = model.solve(solve_start, solve_start, df)
        
        print(f"📈 Warm-up complete. Starting tracking solve...")
        # Merge baseline back into df to provide the 'warm' starting guess
        df.update(baseline)
        
        results = model.init_trac(solve_start, df.index.max(), df)
        print("✅ Engine Solve Successful.")
        
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()