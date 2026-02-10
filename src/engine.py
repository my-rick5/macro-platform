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
    
    # 1. Load and Normalize
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return

    data_frames = []
    for f in files:
        tmp = pd.read_csv(os.path.join(data_path, f))
        tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
        data_frames.append(tmp.set_index('date'))
    
    df = pd.concat(data_frames, axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    actual_data_cols = list(df.columns)

    # 2. Log-Neutral Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            found_vars = re.findall(r'<name>(.*?)</name>', content)
            expected_vars = list(set([v.strip().lower() for v in found_vars if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in actual_data_cols]
            
            if missing_vars:
                print(f"🛰️ Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} dummies...")
                new_data = {}
                for i, var in enumerate(missing_vars):
                    # NEUTRALITY FIX: 
                    # Rates and price indices stay at 1.0 (log-neutral)
                    # We add a micro-jitter to prevent singular matrices
                    base = 1.0 
                    new_data[var] = base + (np.arange(len(df)) * 1e-8) + (i * 1e-10)
                
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Buffer and Final Solve
    df = df.sort_index()
    first_obs = df.index.min()
    # 32-quarter buffer to ensure even the longest expectations (t+30) have data
    padding_df = pd.DataFrame(index=pd.PeriodIndex([first_obs - i for i in range(1, 33)], freq='Q'), columns=df.columns)
    for col in df.columns: padding_df[col] = df[col].iloc[0]
    
    df = pd.concat([padding_df, df]).sort_index()
    # Floor of 0.1 remains to prevent absolute zero logs
    df = df.ffill().bfill().clip(lower=0.1).copy()

    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Calculating Residuals...")
        
        # Use solve_start with a deep lookback buffer
        results = model.init_trac(first_obs, df.index.max(), df)
        
        mask = [c for c in results.columns if c.lower() in actual_data_cols or any(x in c.lower() for x in actual_data_cols)]
        print("✅ Engine Solve Successful.")
        results[mask].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        # Identify the exact column causing the log-floor strike
        min_series = df.min().idxmin()
        print(f"🔍 Diagnostic: Minimum value strike on variable `{min_series}`")
        raise

if __name__ == "__main__":
    run_pro_engine()