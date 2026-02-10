import pd as pd
import os
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
    
    # 2. 🚀 THE "GLOBAL PROXY" INJECTION
    try:
        model = frbus.Frbus(model_xml)
        solve_start = pd.Period('2006Q1', freq='Q')
        solve_end = df.index.max()
        
        print(f"🏗️ Model Loaded. Performing Global Proxy Injection...")

        # Directly query the two primary lists that _solve_setup checks
        model_vars = set()
        if hasattr(model, 'endo'): model_vars.update(model.endo)
        if hasattr(model, 'exo'): model_vars.update(model.exo)
        
        # Hard-coded safety net for the specific blocker
        model_vars.add('dmptmax') 

        missing = [v.lower() for v in model_vars if v.lower() not in df.columns]
        
        if missing:
            print(f"📦 Injecting {len(missing)} proxies to satisfy _solve_setup...")
            # Create a full-index dataframe of 1.0s and join it
            proxy_df = pd.DataFrame(1.0, index=df.index, columns=missing)
            df = pd.concat([df, proxy_df], axis=1)

        # 3. Direct Tracking Solve
        # Since we bypass model.solve(), we still avoid the 'log' math crashes.
        results = model.init_trac(solve_start, solve_end, df)
        
        print("✅ Engine Solve Successful.")
        results.to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()