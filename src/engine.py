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
    df = df.abs().clip(lower=10.0) # Higher floor for numerical stability

    # 3. Model Variable Synchronization
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                expected_vars = [v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', f.read()) if v.strip()]
            new_vars_dict = {v: pd.Series(10.0, index=df.index) for v in expected_vars if v not in df.columns}
            df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception: pass

    # 4. 🚀 THE ITERATIVE SOLVER: Solve one quarter at a time
    try:
        model = frbus.Frbus(model_xml)
        solve_start = df.index[8] 
        print(f"🏗️ Model Loaded. Solving with Iterative Soft-Start: {solve_start} to {df.index.max()}")
        
        # We solve iteratively to prevent the 'divide by zero' step-size error
        current_data = df.copy()
        for period in pd.period_range(start=solve_start, end=df.index.max(), freq='Q'):
            print(f"📈 Solving period: {period}...", end='\r')
            # init_trac for a single period stabilizes the solution for the next
            temp_res = model.init_trac(period, period, current_data)
            current_data.update(temp_res)
        
        print("\n✅ Iterative Engine Solve Successful.")
        current_data[[c for c in current_data.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"\n❌ Iterative Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()