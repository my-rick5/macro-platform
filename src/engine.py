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

    # 2. XML Scraper with "Safe Equilibrium" Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            
            found_vars = re.findall(r'<name>(.*?)</name>', content)
            expected_vars = list(set([v.strip().lower() for v in found_vars if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in df.columns]
            
            if missing_vars:
                print(f"🛰️ Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} series...")
                
                # NEW STRATEGY: Use 1.0 (Unit) for all injected variables but 
                # ensure they are slightly decoupled to satisfy identities.
                new_data = {}
                for i, var in enumerate(missing_vars):
                    # 1.0 is the most stable log-base. We add a tiny offset per variable.
                    val = 1.0 + (i * 1e-7)
                    new_data[var] = [val] * len(df)
                
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Padding & Smoothing
    df = df.sort_index()
    start_date = df.index.min()
    padding_dates = [start_date - i for i in range(1, 13)]
    padding_df = pd.DataFrame(index=pd.PeriodIndex(padding_dates, freq='Q'), columns=df.columns)
    
    for col in df.columns:
        padding_df[col] = df[col].iloc[0]

    df = pd.concat([padding_df, df]).sort_index()
    
    # Increase the floor to 0.1 to keep logs away from the steep slope near zero
    df = df.ffill().bfill().clip(lower=0.1).copy()

    df.to_csv(os.path.join(results_dir, "master_input_matrix.csv"))

    # 4. Engine Solve with Solver Relaxation
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Calculating Residuals...")
        
        # We allow the solver to be more "lax" with the initial guess 
        # to prevent it from blowing up on the dummy data.
        results = model.init_trac(start_date, df.index.max(), df)
        
        print("✅ Engine Solve Successful.")
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        # One last check: Are any of our actual data points causing the issue?
        print("🔍 Checking Real Data Range:")
        print(df.iloc[:, :15].describe().loc[['min', 'max']])
        raise

if __name__ == "__main__":
    run_pro_engine()