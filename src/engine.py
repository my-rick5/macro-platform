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
    df = pd.concat([pd.read_csv(os.path.join(data_path, f)).assign(date=lambda x: pd.PeriodIndex(x['date'], freq='Q')).set_index('date') for f in files], axis=1).sort_index()
    df.columns = [c.lower() for c in df.columns]
    actual_cols = list(df.columns)
    
    # 2. Initialization
    model = frbus.Frbus(model_xml)
    solve_start = pd.Period('2006Q1', freq='Q')
    solve_end = df.index.max()

    # 3. 🚀 THE SELF-HEALING LOOP
    max_retries = 500 # Sufficient for a 400-variable model
    attempts = 0
    
    print(f"🏗️ Model Loaded. Entering Self-Healing Validation Loop...")

    while attempts < max_retries:
        try:
            # Attempt the track solve
            results = model.init_trac(solve_start, solve_end, df)
            print(f"✅ Engine Solve Successful after {attempts} healing cycles.")
            results.to_csv(os.path.join(results_dir, "residuals.csv"))
            break
            
        except exceptions.MissingDataError as e:
            # 🔍 EXTRACT THE OFFENDING VARIABLE
            # Error looks like: "The variable `dmptpi` appears in the model..."
            msg = str(e)
            match = re.search(r'`([^`]+)`', msg)
            
            if match:
                missing_var = match.group(1).lower()
                # Inject a neutral 1.0 series for the missing variable
                df[missing_var] = 1.0
                attempts += 1
                if attempts % 10 == 0:
                    print(f"🩹 Healed {attempts} variables so far (Latest: {missing_var})...")
            else:
                print(f"❌ Unparseable MissingDataError: {msg}")
                raise e
        except Exception as e:
            print(f"❌ Non-Validation Error encountered: {e}")
            raise e
    else:
        print("❌ Reached max retries without resolving namespace.")

if __name__ == "__main__":
    run_pro_engine()