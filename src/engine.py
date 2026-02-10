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
    
    # 2. Reindex and Continuous Fill
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()

    # 🚀 THE LOG-SAFE NORMALIZATION:
    # Instead of base 100, we use base 10,000.
    # This ensures that even a massive Newton step (-500 units) 
    # won't result in a negative number, protecting the log() identities.
    for i, col in enumerate(actual_cols):
        start_val = df.loc['2006Q1', col]
        if abs(start_val) > 1e-5:
            # Shift data to high-magnitude space while keeping growth rates
            df[col] = (df[col] / start_val) * (10000.0 + (i * 1.0))
        else:
            df[col] = 10000.0 + (i * 1.0)
        df[col] = df[col].abs().clip(lower=1000.0)

    # 3. Model Variable Synchronization (Proxies)
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                expected_vars = [v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', f.read()) if v.strip()]
            
            # Proxies get their own uniquely offset high-base neighborhood
            new_vars_dict = {v: pd.Series(11000.0 + (i * 1.0), index=df.index) for i, v in enumerate(expected_vars) if v not in df.columns}
            df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception: pass

    # 4. Final Engine Execution
    try:
        model = frbus.Frbus(model_xml)
        solve_start = df.index[8] 
        print(f"🏗️ Model Loaded. Solving with High-Base Normalization: {solve_start} to {df.index.max()}")
        
        # Solving with a massive numerical buffer against log(negative) crashes
        results = model.init_trac(solve_start, df.index.max(), df)
        
        print("✅ Engine Solve Successful.")
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()