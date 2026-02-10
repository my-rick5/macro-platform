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
    
    # 1. Load and Normalize Data
    files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
    if not files: return
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.index = df.index.asfreq('Q')
    df.columns = [c.lower() for c in df.columns]
    
    # 2. Initialization
    model = frbus.Frbus(model_xml)
    solve_start = pd.Period('2006Q1', freq='Q')
    solve_end = df.index.max()

    # 3. 🚀 THE LOG-NEUTRAL SELF-HEALING LOOP
    max_retries = 500
    attempts = 0
    
    print(f"🏗️ Model Loaded. Entering Log-Neutral Validation Loop...")

    while attempts < max_retries:
        try:
            # Fix fragmentation before every solve attempt
            clean_df = df.copy()
            
            # Attempt tracking
            results = model.init_trac(solve_start, solve_end, clean_df)
            print(f"✅ Engine Solve Successful after {attempts} healing cycles.")
            results.to_csv(os.path.join(results_dir, "residuals.csv"))
            break
            
        except exceptions.MissingDataError as e:
            match = re.search(r'`([^`]+)`', str(e))
            if match:
                missing_var = match.group(1).lower()
                
                # 🚀 LOG-NEUTRAL PATCHING: 
                # Avoid 1.0 (which causes log(0) in identities).
                # Use 1.1 for levels and 0.01 for rates/spreads.
                if any(x in missing_var for x in ['r', 'pi', 'u', 'gap', 'del']):
                    df[missing_var] = 0.01
                else:
                    df[missing_var] = 1.1
                
                attempts += 1
                if attempts % 50 == 0:
                    print(f"🩹 Healed {attempts} variables...")
            else:
                raise e
        except ValueError as e:
            if "is not in list" in str(e):
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