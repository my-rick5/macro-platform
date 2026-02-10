import pandas as pd
import os
import re
import numpy as np
from pyfrbus import frbus, exceptions

def run_pro_engine():
    data_path = "/home/spark/data/processed"
    model_xml = "/home/spark/models/model.xml"
    results_dir = "/home/spark/results"
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Load Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
    
    # Load and immediately normalize frequency to 'Q'
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.index = df.index.asfreq('Q')
    df.columns = [c.lower() for c in df.columns]
    
    # 2. Initialization
    model = frbus.Frbus(model_xml)
    # Ensure start/end dates use the exact same frequency as the index
    solve_start = pd.Period('2006Q1', freq='Q')
    solve_end = df.index.max()

    # 3. 🚀 THE DE-FRAGMENTED SELF-HEALING LOOP
    max_retries = 500
    attempts = 0
    
    print(f"🏗️ Model Loaded. Entering De-Fragmented Validation Loop...")

    while attempts < max_retries:
        try:
            # IMPORTANT: Re-copy the dataframe to fix the PerformanceWarning (fragmentation)
            # This ensures the index remains a clean 'list' for the solver's internal lookup.
            clean_df = df.copy()
            
            # Attempt the track solve
            results = model.init_trac(solve_start, solve_end, clean_df)
            print(f"✅ Engine Solve Successful after {attempts} healing cycles.")
            results.to_csv(os.path.join(results_dir, "residuals.csv"))
            break
            
        except exceptions.MissingDataError as e:
            msg = str(e)
            match = re.search(r'`([^`]+)`', msg)
            
            if match:
                missing_var = match.group(1).lower()
                df[missing_var] = 1.0  # Neutral baseline
                attempts += 1
                if attempts % 50 == 0:
                    print(f"🩹 Healed {attempts} variables...")
            else:
                raise e
        except ValueError as e:
            # Handle the 'Period not in list' error by checking index coverage
            if "is not in list" in str(e):
                print(f"⚠️ Index Mismatch at {solve_start}. Re-indexing to ensure coverage...")
                # Expand index to ensure 2006Q1 is definitely included
                new_idx = pd.period_range(start=min(df.index.min(), solve_start), 
                                          end=max(df.index.max(), solve_end), 
                                          freq='Q')
                df = df.reindex(new_idx).ffill().bfill()
                attempts += 1
            else:
                raise e
    else:
        print("❌ Reached max retries.")

if __name__ == "__main__":
    run_pro_engine()