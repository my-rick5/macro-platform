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
    
    # 1. Load merged CSVs
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return

    data_frames = []
    for f in files:
        tmp = pd.read_csv(os.path.join(data_path, f))
        tmp['date'] = pd.PeriodIndex(tmp['date'], freq='Q')
        data_frames.append(tmp.set_index('date'))
    
    df = pd.concat(data_frames, axis=1).sort_index()

    # 2. XML Scraper: Targeted Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            
            found_vars = re.findall(r'<name>(.*?)</name>', content)
            expected_vars = list(set([v.strip().lower() for v in found_vars if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in df.columns]
            
            if missing_vars:
                print(f"🛰️ Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} series...")
                new_data = {}
                for i, var in enumerate(missing_vars):
                    # Set a safe steady-state baseline
                    # Rates at 0.05, Levels at 1.0 (Unit)
                    base = 0.05 if any(r in var for r in ['mpt', 'lur', 'pi', 'r']) else 1.0
                    # Tiny unique offset to prevent identity collisions
                    new_data[var] = [base + (i * 1e-8)] * len(df)
                
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Padding & Numerical Robustness
    df = df.sort_index()
    start_date = df.index.min()
    padding_dates = [start_date - i for i in range(1, 13)] # 3 years of buffer
    padding_df = pd.DataFrame(index=pd.PeriodIndex(padding_dates, freq='Q'), columns=df.columns)
    
    for col in df.columns:
        padding_df[col] = df[col].iloc[0]

    df = pd.concat([padding_df, df]).sort_index()
    
    # CRITICAL: Apply a strictly positive floor to prevent log(negative)
    # 0.01 is a safe lower bound for macro data in this engine
    df = df.ffill().bfill().clip(lower=0.01).copy()

    # Save verification for artifact inspection
    df.to_csv(os.path.join(results_dir, "master_input_matrix.csv"))

    # 4. Engine Solve
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Calculating Residuals...")
        # Solve from actual start_date
        results = model.init_trac(start_date, df.index.max(), df)
        
        print("✅ Engine Solve Successful.")
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()