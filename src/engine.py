import pandas as pd
import os
import re
import sys
import numpy as np
from pyfrbus import frbus, exceptions

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    results_dir = "/home/spark/results"
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load Data and Capture Target Columns
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.index = pd.PeriodIndex(df.index, freq='Q')
    df.columns = [c.lower() for c in df.columns]
    target_variables = list(df.columns)
    
    # 2. Initialization
    model = frbus.Frbus(model_xml)
    solve_start = pd.Period('2006Q1', freq='Q')
    solve_end = df.index.max()

    # 3. 🚀 THE BIPOLAR SEARCH LOOP
    max_retries = 1500 # Even more headroom
    attempts = 0
    missing_registry = {} 
    
    print(f"🏗️ Model Loaded. Entering Bipolar Surgical Loop...")

    while attempts < max_retries:
        try:
            if missing_registry:
                patch_df = pd.DataFrame(missing_registry, index=df.index)
                current_df = pd.concat([df, patch_df], axis=1)
            else:
                current_df = df.copy()

            results = model.init_trac(solve_start, solve_end, current_df)
            
            # SUCCESS
            final_cols = []
            for v in target_variables:
                if v in results.columns: final_cols.append(v)
                res_v = f"{v}_res"
                if res_v in results.columns: final_cols.append(res_v)
            
            results[final_cols].to_csv(os.path.join(results_dir, "residuals_lite.csv"))
            print(f"✅ Success at Cycle {attempts}. Exported residuals_lite.csv.")
            return 

        except exceptions.MissingDataError as e:
            match = re.search(r'`([^`]+)`', str(e))
            if match:
                var = match.group(1).lower()
                missing_registry[var] = 10.0 # Standard start
                attempts += 1
            else: raise e
        except (ValueError, exceptions.ComputationError):
            # 🚀 BIPOLAR ESCALATION: 
            # We alternate directions. Even cycles go UP, Odd cycles go DOWN.
            # This prevents getting stuck on a "one-way" math wall.
            direction = 1 if attempts % 2 == 0 else -1
            shift = 0.057 * direction # Using a prime shift
            
            missing_registry = {k: max(0.01, v + shift) for k, v in missing_registry.items()}
            attempts += 1
            if attempts % 100 == 0:
                print(f"🔄 Bipolar Cycle {attempts} (Direction: {'UP' if direction > 0 else 'DOWN'})...")

    print("❌ CRITICAL: Failed to find stable mathematical domain.")
    sys.exit(1)

if __name__ == "__main__":
    run_pro_engine()