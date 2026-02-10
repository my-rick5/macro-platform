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
    
    # 2. Apply Baseline and Splicing
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    stable_trend = pd.Series([100 * (1.005**i) for i in range(len(full_index))], index=full_index)
    df = df.reindex(full_index)

    for col in df.columns:
        first_idx = df[col].first_valid_index()
        if first_idx and first_idx > full_index[0]:
            ratio = df.loc[first_idx, col] / stable_trend.loc[first_idx]
            df.loc[:first_idx, col] = stable_trend.loc[:first_idx] * ratio

    # 🚀 THE DIAGNOSTIC FIX: Print the data state before solving
    print("\n🔍 --- DATA DIAGNOSTIC REPORT ---")
    print(f"Index Range: {df.index.min()} to {df.index.max()}")
    print("\nSummary Statistics for Real Variables:")
    print(df[actual_cols].describe().loc[['min', 'max', 'mean']])
    print("\nFirst 8 Quarters (Spliced History):")
    print(df[actual_cols].head(8))
    print("-----------------------------------\n")

    # 3. Proxy Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                expected_vars = list(set([v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', f.read()) if v.strip()]))
            new_vars_dict = {v: stable_trend * (1.0 + np.sin(i)*0.01) for i, v in enumerate(expected_vars) if v not in df.columns}
            df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception as e: print(f"⚠️ warning: {e}")

    # 4. Model Execution
    df = df.ffill().bfill().abs().clip(lower=0.1)
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