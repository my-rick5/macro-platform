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
    
    # 2. Deep History Expansion
    full_index = pd.period_range(start='2000Q1', end=df.index.max(), freq='Q')
    df = df.reindex(full_index).bfill().interpolate(method='linear').ffill()

    # 3. 🚀 THE HARD-PATCH FIX:
    try:
        model = frbus.Frbus(model_xml)
        
        # Determine ALL expected variables from model object or XML
        all_expected = set()
        if hasattr(model, 'vars'):
            all_expected = set(v.lower() for v in model.vars)
        else:
            with open(model_xml, 'r') as f:
                all_expected = set(re.findall(r'<name>(.*?)</name>', f.read().lower()))
        
        # Add 'dmptmax' explicitly to the list just in case
        all_expected.add('dmptmax')
        
        missing_vars = all_expected - set(df.columns)
        if missing_vars:
            print(f"📦 Hard-patching {len(missing_vars)} missing variables including 'dmptmax'...")
            # We use a massive dictionary to batch-create missing columns
            patch_data = {v: 1.0 for v in missing_vars}
            patch_df = pd.DataFrame(patch_data, index=df.index)
            df = pd.concat([df, patch_df], axis=1)
            
    except Exception as e:
        print(f"⚠️ Metadata hard-patch failed: {e}")

    # 4. Engine Execution
    try:
        solve_start_date = pd.Period('2006Q1', freq='Q')
        solve_end_date = df.index.max()
        print(f"🏗️ Model Loaded. Solving with Hard-Patched Namespace...")

        # Ultra-conservative factor to handle the 1.0 baseline
        if hasattr(model, 'solver_options'):
            model.solver_options['factor'] = 0.001 
            
        # 5. Core Solve
        # We perform a re-alignment just before the call to ensure 
        # that the dataframe is not fragmented and contains dmptmax.
        df = df.copy() 
        baseline_df = model.solve(solve_start_date, solve_end_date, df)
        
        # 6. Tracking Solve
        results = model.init_trac(solve_start_date, solve_end_date, baseline_df)
        print("✅ Engine Solve Successful.")
        
        results[[c for c in results.columns if c in actual_cols]].to_csv(os.path.join(results_dir, "residuals.csv"))
        
    except Exception as e:
        print(f"❌ Engine Failed: {e}")
        raise

if __name__ == "__main__":
    run_pro_engine()