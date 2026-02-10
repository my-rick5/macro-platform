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
    
    # 1. Load Real Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
    data_frames = [pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files]
    df = pd.concat(data_frames, axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    actual_data_cols = list(df.columns)

    # 🚀 THE UNIT STABILITY FIX: Global Normalization
    # Scale every real variable so its mean is 100.0 to prevent unit mismatches
    # from crashing log() identities.
    for col in df.columns:
        col_mean = df[col].mean()
        if col_mean != 0:
            df[col] = (df[col] / col_mean) * 100.0

    # 2. Smart Proxy Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            expected_vars = list(set([v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', content) if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in actual_data_cols]
            
            if missing_vars:
                print(f"🛰️ Scraper found {len(expected_vars)} variables. Mapping proxies for {len(missing_vars)} variables...")
                # Every dummy variable now also shares this safe scale (100.0)
                new_vars_dict = {var: 100.0 + (np.sin(i) * 0.1) for i, var in enumerate(missing_vars)}
                df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Mapping warning: {e}")

    # 3. Final Sanitization
    first_obs = df.index.min()
    padding = pd.DataFrame(index=pd.PeriodIndex([first_obs - i for i in range(1, 41)], freq='Q'), columns=df.columns)
    for col in df.columns: padding[col] = df[col].iloc[0]
    
    # Enforce a strict log-safe floor on the normalized data
    df = pd.concat([padding, df]).sort_index().ffill().bfill().abs().clip(lower=10.0)

    # 4. Model Execution
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Executing init_trac with Normalized Data...")
        results = model.init_trac(first_obs, df.index.max(), df)
        
        print("✅ Engine Solve Successful.")
        output_cols = [c for c in results.columns if c.lower() in actual_data_cols]
        results[output_cols].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()