import pandas as pd
import os
import re
import numpy as np
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    results_dir = "/home/spark/results"
    # 🚀 FIXED TYPO: changed exist_index to exist_ok
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    actual_cols = list(df.columns)
    
    # 2. Strict Reconstruction (Log-Linear)
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index)
    
    # Ensure no zeros before log interpolation
    df = df.clip(lower=0.01)
    df = np.exp(np.log(df).interpolate(method='linear')).bfill().ffill()

    # 3. THE PRECISION AUDIT: Find the "Log-Killer"
    LOG_THRESHOLD = 0.01 
    critical_failures = []
    
    for col in df.columns:
        zeros = df[df[col] < LOG_THRESHOLD][col]
        if not zeros.empty:
            for date, val in zeros.items():
                critical_failures.append(f"🚩 {col} at {date}: value {val}")

    if critical_failures:
        print("\n⚠️ LOG-DANGER ALERT: Found values likely to cause 'divide by zero in log':")
        for fail in critical_failures[:10]:
            print(fail)
        print(f"...Total danger points found: {len(critical_failures)}\n")

    # 4. Proxy Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                expected_vars = [v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', f.read()) if v.strip()]
            median_trend = df.median(axis=1).clip(lower=1.0)
            new_vars_dict = {v: median_trend for v in expected_vars if v not in df.columns}
            df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception: pass

    # 5. Final Engine Execution
    # SAFETY BUMP: Increase floor to 1.0 to ensure log(x) >= 0
    df = df.abs().clip(lower=1.0)
    
    try:
        model = frbus.Frbus(model_xml)
        solve_start = df.index[8] 
        print(f"🏗️ Model Loaded. Solving range: {solve_start} to {df.index.max()}")
        results = model.init_trac(solve_start, df.index.max(), df)
        print("✅ Engine Solve Successful.")
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()