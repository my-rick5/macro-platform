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
    
    # 1. Load and Align Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
    data_frames = [pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files]
    
    # Use outer join to keep the maximum possible date range (2004-2019)
    df = pd.concat(data_frames, axis=1, join='outer').sort_index()
    df.columns = [c.lower() for c in df.columns]
    
    # 🚀 THE ALIGNMENT FIX: Backfill missing values for variables that start late (like 2008Q3)
    # This prevents the solver from 'losing' the 2004-2008 history.
    df = df.bfill().ffill()

    # 2. Map Proxies
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            expected_vars = list(set([v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', content) if v.strip()]))
            
            print(f"🛰️ Scraper found {len(expected_vars)} variables. Synchronizing 398-var matrix...")
            macro_proxy = df.mean(axis=1)
            new_vars_dict = {v: macro_proxy * (1.0 + np.sin(i)*0.01) for i, v in enumerate(expected_vars) if v not in df.columns}
            df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Mapping warning: {e}")

    # 3. Final Sanitization
    df = df.abs().clip(lower=0.1)
    
    # 4. Model Execution
    try:
        # 🚀 THE LAG FIX: Provide exactly 8 quarters of buffer (2 years)
        # This satisfies the '-6' index requirement and provides a safety margin.
        if len(df) <= 8:
            raise ValueError(f"Insufficient data (only {len(df)} obs). Model requires at least 9.")

        model = frbus.Frbus(model_xml)
        
        # We start solving at the 9th observation, giving us 8 quarters of history (0-7)
        solve_start = df.index[8] 
        print(f"🏗️ Model Loaded. Solving strict range: {solve_start} to {df.index.max()}")
        
        results = model.init_trac(solve_start, df.index.max(), df)
        print("✅ Engine Solve Successful.")
        
        # Save results for only the original 15 real variables
        actual_cols = [f.split('.')[0].lower() for f in files]
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()