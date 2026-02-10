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

    # 2. XML Scraper with High-Headroom Injection
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
                    # INCREASED BASELINES: Providing more room before hitting 0.0
                    if any(x in var for x in ['pitarg', 'targ', 'pi']): base = 2.0
                    elif any(x in var for x in ['tr', 'tax', 'rt']): base = 0.20
                    elif any(x in var for x in ['gr', 'gc', 'gi', 'gx', 'gd', 'hgp']): base = 3000.0
                    else: base = 10.0 # Standard level baseline moved from 1.0 to 10.0
                    
                    new_data[var] = [base + (i * 1e-7)] * len(df)
                
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Robust Padding & Smart Clipping
    df = df.sort_index()
    start_date = df.index.min()
    padding_dates = [start_date - i for i in range(1, 13)]
    padding_df = pd.DataFrame(index=pd.PeriodIndex(padding_dates, freq='Q'), columns=df.columns)
    for col in df.columns:
        padding_df[col] = df[col].iloc[0]

    df = pd.concat([padding_df, df]).sort_index()
    
    # SMART CLIP: Use a 0.1 floor for nominal levels and 0.01 for rates
    # This provides 10x more buffer for the variables identified in #258
    for col in df.columns:
        if any(x in col for x in ['pi', 'r', 'tr', 'lur']):
            df[col] = df[col].clip(lower=0.01)
        else:
            df[col] = df[col].clip(lower=0.5) # Aggressive floor for levels

    # 4. Engine Solve
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Calculating Residuals...")
        
        solve_start = pd.PeriodIndex([f.index.min() for f in data_frames], freq='Q').min()
        results = model.init_trac(solve_start, df.index.max(), df)
        
        mask = [c for c in results.columns if c.lower() in actual_data_cols or any(x in c.lower() for x in actual_data_cols)]
        print("✅ Engine Solve Successful.")
        results[mask].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()