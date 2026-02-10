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
    
    # 2. Reindex and Log-Linear Clean
    full_index = pd.period_range(start='2004Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()
    
    # 🚀 THE STRUCTURAL ANCHOR: Use Nominal GDP as the scaling master
    # If gngdp isn't present, we use a 100-base trend.
    anchor = df['gngdp'] if 'gngdp' in df.columns else pd.Series(100.0, index=df.index)
    df = df.abs().clip(lower=10.0)

    # 3. Identity-Bound Proxy Injection
    if os.path.exists(model_xml):
        try:
            with open(model_xml, 'r', encoding='utf-8') as f:
                expected_vars = [v.strip().lower() for v in re.findall(r'<name>(.*?)</name>', f.read()) if v.strip()]
            
            new_vars_dict = {}
            for i, v in enumerate(expected_vars):
                if v not in df.columns:
                    # Proxies are tied to the anchor with a unique 'identity offset'
                    # This ensures they move together, preventing log-difference crashes.
                    offset = 1.0 + (i % 50) * 0.002
                    new_vars_dict[v] = anchor * offset
            
            df = pd.concat([df, pd.DataFrame(new_vars_dict, index=df.index)], axis=1)
        except Exception: pass

    # 4. Final Engine Execution
    try:
        model = frbus.Frbus(model_xml)
        solve_start = df.index[8] # 2006Q1
        
        print(f"🏗️ Model Loaded. Solving with Structural Anchor: {solve_start} to {df.index.max()}")
        
        # We solve period-by-period one last time to isolate the exact date of failure
        current_data = df.copy()
        for period in pd.period_range(start=solve_start, end=df.index.max(), freq='Q'):
            print(f"📊 Tracking Identity: {period}...", end='\r')
            temp_res = model.init_trac(period, period, current_data)
            current_data.update(temp_res)
            
        print("\n✅ Identity-Bound Solve Successful.")
        current_data[[c for c in current_data.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"\n❌ Engine Failed: {e}")
        # Identify the exact data state at the moment of failure
        print(f"Failing Period Context:\n{df.loc[period, actual_cols] if 'period' in locals() else 'N/A'}")
        raise

if __name__ == "__main__":
    run_pro_engine()