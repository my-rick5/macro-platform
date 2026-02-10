import pandas as pd
import os
import re
import numpy as np
from pyfrbus import frbus

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    results_dir = "/home/spark/results"
    os.makedirs(results_dir, exist_index=True)
    
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

    # DYNAMIC SCALING: Calculate the average magnitude of your real data
    # We will use this as the baseline for all injected dummies
    real_mean_magnitude = df[actual_data_cols].mean().mean()
    print(f"📊 Mirroring scale magnitude: {real_mean_magnitude:.2f}")

    # 2. Scraper with Mirror-Scale Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            found_vars = re.findall(r'<name>(.*?)</name>', content)
            expected_vars = list(set([v.strip().lower() for v in found_vars if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in actual_data_cols]
            
            if missing_vars:
                print(f"🛰️ Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} dummies...")
                t = np.arange(len(df))
                new_data = {}
                for i, var in enumerate(missing_vars):
                    # Use the mirrored mean for levels, keep rates around 2%
                    if any(x in var for x in ['pitarg', 'targ', 'pi', 'r', 'lur']): 
                        base = 2.0
                    else: 
                        base = real_mean_magnitude
                    
                    # Trend ensures no divide-by-zero, jitter ensures unique Jacobian columns
                    new_data[var] = base + (t * 1e-6) + (i * 1e-8)
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Buffer and Floor
    df = df.sort_index()
    first_obs = df.index.min()
    padding_df = pd.DataFrame(index=pd.PeriodIndex([first_obs - i for i in range(1, 25)], freq='Q'), columns=df.columns)
    for col in df.columns: padding_df[col] = df[col].iloc[0]
    
    df = pd.concat([padding_df, df]).sort_index()
    df = df.ffill().bfill().clip(lower=0.1).copy()

    # 4. Engine Solve
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Calculating Residuals...")
        results = model.init_trac(first_obs, df.index.max(), df)
        
        mask = [c for c in results.columns if c.lower() in actual_data_cols or any(x in c.lower() for x in actual_data_cols)]
        print("✅ Engine Solve Successful.")
        results[mask].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        # Identify variables that are out of scale with the new mirrored mean
        outliers = (df.iloc[-1] / real_mean_magnitude).nlargest(3).to_dict()
        print(f"🔍 Scale Outliers: {outliers}")
        raise

if __name__ == "__main__":
    run_pro_engine()