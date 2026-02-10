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
    
    # 1. Load and Align Real Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files:
        print("⚠️ No processed data files found.")
        return
        
    data_frames = [pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files]
    df = pd.concat(data_frames, axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    actual_data_cols = list(df.columns)

    # 2. Inject Stable Dummies (397 variables)
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                content = f.read()
            expected_vars = list(set([v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', content) if v.strip()]))
            missing_vars = [v for v in expected_vars if v not in actual_data_cols]
            
            if missing_vars:
                print(f"🛰️ Scraper found {len(expected_vars)} variables. Injecting {len(missing_vars)} stable dummies...")
                t = np.arange(len(df))
                new_data = {}
                rng = np.random.default_rng(320) # Updated for Build #320
                
                for var in missing_vars:
                    base_level = 100.0 + rng.uniform(0, 50)
                    growth = 1.0001 + rng.uniform(0, 0.0001)
                    new_data[var] = base_level * (growth ** t)
                
                df = pd.concat([df, pd.DataFrame(new_data, index=df.index)], axis=1)
        except Exception as e:
            print(f"⚠️ Scraper warning: {e}")

    # 3. Final Sanitization
    first_obs = df.index.min()
    padding = pd.DataFrame(index=pd.PeriodIndex([first_obs - i for i in range(1, 41)], freq='Q'), columns=df.columns)
    for col in df.columns: padding[col] = df[col].iloc[0]
    df = pd.concat([padding, df]).sort_index().ffill().bfill().abs().clip(lower=10.0)

    # 4. Model Loading & Flattened Solver Execution
    try:
        model = frbus.Frbus(model_xml)
        print("🏗️ Model Loaded. Executing init_trac with flattened solver options...")
        
        # 🚀 API FIX: Pass options as direct keyword arguments to avoid TypeError
        results = model.init_trac(
            first_obs, 
            df.index.max(), 
            df, 
            eps=1e-6,           # Perturbation step
            tol=1e-7,           # Tolerance
            maxit=100,          # Max iterations
            linesearch=True     # Safety seatbelt for log transforms
        )
        
        print("✅ Engine Solve Successful.")
        
        # 5. Output filtered results
        output_cols = [c for c in results.columns if c.lower() in actual_data_cols]
        results[output_cols].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()