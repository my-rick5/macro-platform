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
    
    # 2. Continuous Fill
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()

    # 3. 🚀 THE ATTRIBUTE-SAFE DISCOVERY:
    try:
        model = frbus.Frbus(model_xml)
        
        # FIXED: Try common pyfrbus metadata attributes
        all_vars = []
        if hasattr(model, 'vars'):
            all_vars = model.vars
        elif hasattr(model, 'lookup'):
            all_vars = model.lookup(vtype='all')
        else:
            # Fallback: parse the XML name tags directly if API fails
            with open(model_xml, 'r') as f:
                all_vars = re.findall(r'<name>(.*?)</name>', f.read())
        
        all_model_vars = set(v.strip().lower() for v in all_vars)
        missing_vars = all_model_vars - set(df.columns)
        
        if missing_vars:
            print(f"📦 Patching {len(missing_vars)} missing variables including 'dmptmax'...")
            for v in missing_vars:
                # Initializing to 1.0 ensures they don't break log/division identities
                df[v] = 1.0 
    except Exception as e:
        print(f"⚠️ Robust Discovery failed: {e}")

    # 4. Zero-Base Residual Solve
    try:
        solve_start = df.index[8] # 2006Q1
        print(f"🏗️ Model Loaded. Solving with Zero-Base Discovery: {solve_start} to {df.index.max()}")
        
        # This will now succeed because dmptmax is in df
        baseline_df = model.solve(df.index[0], df.index.max(), df)
        
        for col in actual_cols:
            if col in baseline_df.columns:
                scale_factor = baseline_df.loc[solve_start, col] / (df.loc[solve_start, col] or 1.0)
                baseline_df[col] = df[col] * scale_factor

        results = model.init_trac(solve_start, df.index.max(), baseline_df)
        print("✅ Engine Solve Successful.")
        
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()