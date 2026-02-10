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

    # 2. XML-Aware Scraper with "Safe" Nominal Baselines
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            
            found_vars = re.findall(r'<name>(.*?)</name>', content)
            expected_vars = list(set([v.strip().lower() for v in found_vars if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in df.columns]
            
            if missing_vars:
                print(f"🛰️  Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} series...")
                new_data = {}
                for var in missing_vars:
                    # Logic: Use 100.0 for things that look like indices (p = price, x = nominal)
                    # Use 2.0 for rates, 1.0 for the rest. Never 0.0.
                    if any(p in var for p in ['p', 'x', 'y']): val = 100.0
                    elif any(r in var for r in ['mpt', 'lur', 'pi', 'r']): val = 2.0
                    else: val = 1.0
                    new_data[var] = [val] * len(df)
                
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Deep Lag Padding (8 Quarters) & Value Clamping
    df = df.sort_index()
    start_date = df.index.min()
    padding_dates = [start_date - i for i in range(1, 9)]
    # Start padding with 100.0 as a safe default for the buffer
    padding_df = pd.DataFrame(100.0, index=pd.PeriodIndex(padding_dates, freq='Q'), columns=df.columns)
    
    df = pd.concat([padding_df, df]).sort_index()
    
    # CRITICAL: Clamp values to a minimum of 0.0001 to prevent log(0)
    # FRB/US equations often fail if values are exactly 0.
    df = df.ffill().bfill().clip(lower=0.0001)
    df = df.copy() 

    df.to_csv(os.path.join(results_dir, "master_input_matrix.csv"))
    print(f"📊 Matrix Clamped & Saved. Range: {df.index.min()} to {df.index.max()}")

    # 4. Engine Solve
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️  Model Loaded. Calculating Residuals...")
        # Note: We still calculate from start_date to ignore the padding in the results
        results = model.init_trac(start_date, df.index.max(), df)
        print("✅ Engine Solve Successful.")
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()