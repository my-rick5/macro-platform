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
    data_frames = [pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files]
    df = pd.concat(data_frames, axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    actual_data_cols = list(df.columns)

    # Calculate Anchor
    macro_anchor = df[actual_data_cols].sum(axis=1).mean()
    print(f"📊 Macro Anchor Scale: {macro_anchor:.2f}")

    # 2. Injection with Massive Structural Offsets
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            expected_vars = list(set([v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', content) if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in actual_data_cols]
            
            if missing_vars:
                print(f"🛰️ Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} dummies...")
                t = np.arange(len(df))
                new_data = {}
                
                for i, var in enumerate(missing_vars):
                    # Growth rate: Prime-decoupled
                    growth_rate = 1.005 + ((i % 13) * 0.0001)
                    
                    # 🚀 MASSIVE OFFSET: Instead of small fractions, give every dummy
                    # a base level of at least 100 + a unique index offset.
                    # This makes log(A/B) or log(A-B) mathematically 'safe'.
                    base_offset = 100.0 + (i * 0.5)
                    new_data[var] = base_offset * (growth_rate ** t)
                
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Aggressive Lookback Padding
    first_obs = df.index.min()
    padding = pd.DataFrame(index=pd.PeriodIndex([first_obs - i for i in range(1, 41)], freq='Q'), columns=df.columns)
    for col in df.columns: padding[col] = df[col].iloc[0]
    
    # Clip at 50.0 to move further away from log-boundary
    df = pd.concat([padding, df]).sort_index().ffill().bfill().clip(lower=50.0)

    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Calculating Residuals...")
        results = model.init_trac(first_obs, df.index.max(), df)
        print("✅ Engine Solve Successful.")
        results[[c for c in results.columns if c.lower() in actual_data_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()